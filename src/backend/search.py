"""
MindVault Hybrid Search & Evidence Engine
Combines SQLite BM25 keyword matching with dense ONNX vector cosine similarity using Reciprocal Rank Fusion (RRF).
"""
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from fastembed import TextEmbedding
from src.backend.database import DatabaseEngine
from src.backend.models import EvidenceModel, EvidencePolarity, ReliabilityTier

class HybridSearchEngine:
    def __init__(self, db_engine: DatabaseEngine, vector_cache_path: str = "data/vectors.json"):
        self.db = db_engine
        self.vector_cache_path = vector_cache_path
        # Loads ONNX-quantized BAAI/bge-small-en-v1.5 or all-MiniLM-L6-v2 (~80-90MB RAM footprint)
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self._load_vector_cache()

    def _load_vector_cache(self):
        """Loads cached dense embeddings from disk."""
        if os.path.exists(self.vector_cache_path):
            with open(self.vector_cache_path, "r", encoding="utf-8") as f:
                self.vector_cache = json.load(f)
        else:
            self.vector_cache = {}

    def _save_vector_cache(self):
        """Persists vector cache to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(self.vector_cache_path)), exist_ok=True)
        with open(self.vector_cache_path, "w", encoding="utf-8") as f:
            json.dump(self.vector_cache, f)

    def embed_text(self, text: str) -> List[float]:
        """Generates a dense normalized 384-dimensional embedding vector."""
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

    def index_node(self, node_id: str, text: str):
        """Embeds and indexes a node's text in the local vector cache."""
        vector = self.embed_text(text)
        self.vector_cache[node_id] = vector
        self._save_vector_cache()

    def vector_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Computes cosine similarity across all indexed vectors."""
        if not self.vector_cache:
            return []

        query_vec = np.array(self.embed_text(query), dtype=np.float32)
        # Normalize
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm

        results = []
        for node_id, vec in self.vector_cache.items():
            candidate = np.array(vec, dtype=np.float32)
            cand_norm = np.linalg.norm(candidate)
            if cand_norm > 0:
                candidate = candidate / cand_norm
            similarity = float(np.dot(query_vec, candidate))
            results.append({"node_id": node_id, "similarity": similarity})

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    async def hybrid_search(self, query: str, limit: int = 10, rrf_k: int = 60) -> List[Dict[str, Any]]:
        """
        Executes Reciprocal Rank Fusion (RRF) combining:
        1. FTS5 BM25 Keyword Search
        2. FastEmbed Dense Vector Search
        RRF Score = 1 / (k + rank_bm25) + 1 / (k + rank_vector)
        """
        # 1. Fetch BM25 Keyword results
        fts_results = await self.db.search_fts(query, limit=limit * 2)
        # 2. Fetch Vector results
        vec_results = self.vector_search(query, limit=limit * 2)

        rrf_scores: Dict[str, float] = {}
        metadata_map: Dict[str, Dict[str, Any]] = {}

        # Accumulate FTS ranks
        for rank, item in enumerate(fts_results, start=1):
            n_id = item["id"]
            rrf_scores[n_id] = rrf_scores.get(n_id, 0.0) + (1.0 / (rrf_k + rank))
            metadata_map[n_id] = item

        # Accumulate Vector ranks
        for rank, item in enumerate(vec_results, start=1):
            n_id = item["node_id"]
            rrf_scores[n_id] = rrf_scores.get(n_id, 0.0) + (1.0 / (rrf_k + rank))
            if n_id not in metadata_map:
                node_data = await self.db.get_node(n_id)
                if node_data:
                    metadata_map[n_id] = node_data

        # Sort by unified RRF score
        ranked_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        final_results = []
        for n_id, score in ranked_items[:limit]:
            if n_id in metadata_map:
                res = dict(metadata_map[n_id])
                res["rrf_score"] = round(score, 6)
                final_results.append(res)

        return final_results

    async def attach_evidence(
        self,
        claim_id: str,
        excerpt: str,
        polarity: EvidencePolarity,
        source_doc_id: Optional[str] = None,
        reliability: ReliabilityTier = ReliabilityTier.UNVERIFIED,
        notes: Optional[str] = None
    ) -> EvidenceModel:
        """Connects supporting or refuting evidence to a claim."""
        evidence = EvidenceModel(
            claim_id=claim_id,
            source_doc_id=source_doc_id,
            polarity=polarity,
            excerpt=excerpt,
            reliability_tier=reliability,
            notes=notes
        )
        import aiosqlite
        async with aiosqlite.connect(self.db.db_path) as conn:
            await conn.execute("PRAGMA foreign_keys = ON;")
            await conn.execute(
                """
                INSERT INTO evidence (id, claim_id, source_doc_id, polarity, excerpt, reliability_tier, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (evidence.id, evidence.claim_id, evidence.source_doc_id, evidence.polarity.value, evidence.excerpt, evidence.reliability_tier.value, evidence.notes, evidence.created_at)
            )
            await conn.commit()
        return evidence
