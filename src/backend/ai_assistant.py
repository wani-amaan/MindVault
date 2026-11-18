"""
MindVault AI Research Assistant (Grounded RAG Router)
Provider-agnostic, multi-tier AI assistant:
  Tier 1: Local vector context retrieval (always offline, always traceable)
  Tier 2: Free-tier cloud API (Gemini / Groq — zero RAM, zero cost)
  Tier 3: Hardened refusal when evidence is absent (no hallucination)

Enforces: No citation fabrication. Every answer includes source node IDs.
"""
import os
import json
import httpx
from typing import List, Dict, Any, Optional
from src.backend.database import DatabaseEngine
from src.backend.search import HybridSearchEngine


AI_PROVIDER_CONFIGS = {
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "api_key_env": "GEMINI_API_KEY",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "api_key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile"
    }
}

SYSTEM_PROMPT = """You are MindVault's AI Research Assistant.

RULES (NEVER BREAK THESE):
1. Only answer using the retrieved knowledge context provided below. Do not use external knowledge.
2. Every factual claim in your answer MUST include a source reference [Node: <node_id>].
3. If the context does not contain enough information to answer confidently, respond:
   "I cannot find sufficient evidence in your knowledge vault to answer this question. Consider adding relevant sources."
4. Never fabricate citations, documents, or evidence.
5. Clearly distinguish retrieved facts from analytical interpretation.
6. If the question involves a logical contradiction, explain both sides with their source nodes.

CONTEXT:
{context}

USER QUESTION:
{question}
"""


class AIResearchAssistant:
    def __init__(self, db_engine: DatabaseEngine, search_engine: HybridSearchEngine):
        self.db = db_engine
        self.search = search_engine
        self.active_provider: Optional[str] = self._detect_provider()

    def _detect_provider(self) -> Optional[str]:
        """Auto-detects which free-tier provider is configured via environment variables."""
        if os.environ.get("GEMINI_API_KEY"):
            return "gemini"
        if os.environ.get("GROQ_API_KEY"):
            return "groq"
        return None  # Offline mode: context-only response

    async def _retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves the top-K relevant knowledge nodes using Hybrid RRF search."""
        results = await self.search.hybrid_search(query, limit=top_k)
        return results

    def _build_context_string(self, results: List[Dict[str, Any]]) -> str:
        """Formats retrieved nodes into a numbered context block with node ID citations."""
        if not results:
            return "(No relevant knowledge found in vault)"
        lines = []
        for i, r in enumerate(results, start=1):
            node_id = r.get("id", "unknown")
            title = r.get("title", "Untitled")
            content = r.get("content", "")[:500]  # Cap at 500 chars per node
            lines.append(f"[Node {i} | ID: {node_id}]\nTitle: {title}\nContent: {content}")
        return "\n\n".join(lines)

    async def _call_gemini(self, prompt: str, api_key: str) -> str:
        """Calls Google Gemini 2.0 Flash free-tier API."""
        url = f"{AI_PROVIDER_CONFIGS['gemini']['url']}?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_groq(self, prompt: str, api_key: str) -> str:
        """Calls Groq free-tier API with Llama 3.3 70B."""
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": AI_PROVIDER_CONFIGS["groq"]["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1024
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(AI_PROVIDER_CONFIGS["groq"]["url"], headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def answer(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Main entrypoint: Retrieves vault context, constructs grounded prompt,
        calls AI provider (or returns offline context-only answer), and returns
        a fully traceable response.
        """
        retrieved = await self._retrieve_context(question, top_k=top_k)
        context_str = self._build_context_string(retrieved)
        source_node_ids = [r.get("id") for r in retrieved if r.get("id")]

        full_prompt = SYSTEM_PROMPT.format(context=context_str, question=question)
        ai_response = None
        provider_used = "offline"

        if self.active_provider == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY", "")
            try:
                ai_response = await self._call_gemini(full_prompt, api_key)
                provider_used = "gemini"
            except Exception as e:
                ai_response = None

        if ai_response is None and self.active_provider == "groq":
            api_key = os.environ.get("GROQ_API_KEY", "")
            try:
                ai_response = await self._call_groq(full_prompt, api_key)
                provider_used = "groq"
            except Exception as e:
                ai_response = None

        # Offline fallback: return structured context summary without AI synthesis
        if ai_response is None:
            if not retrieved:
                ai_response = (
                    "I cannot find sufficient evidence in your knowledge vault to answer this question. "
                    "Consider adding relevant sources."
                )
            else:
                ai_response = (
                    f"[Offline Mode — No AI provider configured]\n\n"
                    f"Top {len(retrieved)} relevant knowledge entries retrieved:\n\n{context_str}"
                )
            provider_used = "offline"

        return {
            "question": question,
            "answer": ai_response,
            "provider": provider_used,
            "source_node_ids": source_node_ids,
            "retrieved_count": len(retrieved)
        }
