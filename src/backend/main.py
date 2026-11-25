"""
main.py — MindVault FastAPI Gateway (v0.8.0-alpha)

All backend modules are wired to REST endpoints here.

Run with:
    uvicorn src.backend.main:app --reload --port 8765

Interactive docs: http://localhost:8765/docs

Route groups
------------
  GET  /                              Health check
  POST /nodes                         Create a knowledge node
  GET  /nodes                         List all nodes (paginated)
  GET  /nodes/{node_id}               Get single node
  POST /ingest                        Ingest a document file (PDF/TXT)
  GET  /search                        Hybrid search
  GET  /contradictions                List all detected contradictions
  POST /contradictions/scan           Trigger contradiction scan
  GET  /graph                         Full graph serialised for frontend
  GET  /graph/impact/{node_id}        Impact cascade from a node
  GET  /critical-thinking/{node_id}   Fallacy/reasoning analysis of a node
  GET  /timeline/{entity_id}          Belief audit timeline for an entity
  POST /assistant/ask                 Grounded AI Q&A
  GET  /simulation/nodes              List nodes available to simulate
  POST /simulation/run                What-if scenario execution
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Backend modules ──────────────────────────────────────────────────────────
from src.backend.database import DatabaseEngine
from src.backend.ingestion import DocumentIngestionEngine
from src.backend.search import HybridSearchEngine
from src.backend.contradiction import ContradictionDetectionEngine
from src.backend.graph import KnowledgeGraphEngine
from src.backend.critical_thinking import CriticalThinkingEngine
from src.backend.timeline import TimelineEngine
from src.backend.ai_assistant import AIResearchAssistant
from src.backend.simulation import SimulationLab
from src.backend.external_verification import ExternalVerificationEngine
from src.backend.models import KnowledgeNodeModel

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MindVault API",
    description="Personal Knowledge Intelligence System — backend gateway",
    version="0.8.0-alpha",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tauri frontend on localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared singletons ────────────────────────────────────────────────────────
DB_PATH = str(Path(os.getenv("MINDVAULT_DB", "data/mindvault.db")))
_db: DatabaseEngine | None = None
_search: HybridSearchEngine | None = None
_graph: KnowledgeGraphEngine | None = None


async def _get_db() -> DatabaseEngine:
    global _db
    if _db is None:
        _db = DatabaseEngine(DB_PATH)
        await _db.initialize()
    return _db


async def _get_search() -> HybridSearchEngine:
    global _search
    if _search is None:
        db = await _get_db()
        _search = HybridSearchEngine(db)
    return _search


async def _get_graph() -> KnowledgeGraphEngine:
    global _graph
    if _graph is None:
        db = await _get_db()
        _graph = KnowledgeGraphEngine(db)
        await _graph.build_from_db()
    return _graph


def _invalidate_graph() -> None:
    global _graph
    _graph = None


# ── Request / Response models ────────────────────────────────────────────────

class NodeCreate(BaseModel):
    title: str
    content: str
    node_type: str = "CONCEPT"   # Must match NodeType enum values
    confidence_score: float = 1.0


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class SimulationRequest(BaseModel):
    toggled_node_ids: list[str]
    scenario_label: str = "What-If Scenario"


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.8.0-alpha", "app": "MindVault"}


# ── Nodes ────────────────────────────────────────────────────────────────────

@app.post("/nodes", tags=["Nodes"], status_code=201)
async def create_node(payload: NodeCreate) -> dict[str, Any]:
    db = await _get_db()
    from src.backend.models import NodeType
    node = KnowledgeNodeModel(
        node_type=NodeType(payload.node_type),
        title=payload.title,
        content=payload.content,
        confidence_score=payload.confidence_score,
    )
    created = await db.insert_node(node)
    _invalidate_graph()
    return {"node_id": created.id, "title": created.title}


@app.get("/nodes", tags=["Nodes"])
async def list_nodes(
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    db = await _get_db()
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            """
            SELECT id, node_type, title, content, status, confidence_score, created_at, updated_at
            FROM knowledge_nodes
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ) as cursor:
            rows = [dict(r) for r in await cursor.fetchall()]
    return {"nodes": rows, "limit": limit, "offset": offset}


@app.get("/nodes/{node_id}", tags=["Nodes"])
async def get_node(node_id: str) -> dict[str, Any]:
    db = await _get_db()
    node = await db.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return node


# ── Ingestion ────────────────────────────────────────────────────────────────

@app.post("/ingest", tags=["Ingestion"])
async def ingest_document(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload a PDF or TXT file; MindVault ingests it and returns a summary."""
    allowed = {".pdf", ".txt"}
    suffix = Path(file.filename or "upload.txt").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix}'. Use .pdf or .txt."
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        engine = DocumentIngestionEngine()
        doc_model, blocks = engine.process_file(tmp_path)
        _invalidate_graph()
        return {
            "document_id": doc_model.document_id,
            "title": doc_model.title,
            "blocks_extracted": len(blocks),
            "sha256": doc_model.sha256_hash,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── Search ───────────────────────────────────────────────────────────────────

@app.get("/search", tags=["Search"])
async def search(
    q: Annotated[str, Query(min_length=1)],
    top_k: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict[str, Any]:
    engine = await _get_search()
    results = await engine.hybrid_search(query=q, limit=top_k)
    return {"query": q, "results": results}


# ── Contradictions ───────────────────────────────────────────────────────────

@app.get("/contradictions", tags=["Contradictions"])
async def list_contradictions() -> dict[str, Any]:
    db = await _get_db()
    search_engine = await _get_search()
    engine = ContradictionDetectionEngine(db, search_engine)
    conflicts = await engine.get_active_contradictions()
    return {"contradictions": conflicts, "count": len(conflicts)}


@app.post("/contradictions/scan", tags=["Contradictions"])
async def scan_contradictions() -> dict[str, Any]:
    db = await _get_db()
    search_engine = await _get_search()
    engine = ContradictionDetectionEngine(db, search_engine)
    # We need claims — fetch via FTS wildcard and build ClaimModel objects
    from src.backend.models import ClaimModel
    rows = await db.search_fts("*", limit=500)
    claims = [
        ClaimModel(
            node_id=r.get("node_id", r.get("id", "")),
            subject=r.get("title", r.get("label", "")),
            predicate="is",
            object=r.get("content", "")[:200],
        )
        for r in rows
    ]
    conflicts = await engine.scan_all_claims(claims)
    return {"new_conflicts_found": len(conflicts), "conflicts": [c.dict() for c in conflicts]}


# ── Graph ────────────────────────────────────────────────────────────────────

@app.get("/graph", tags=["Graph"])
async def get_graph() -> dict[str, Any]:
    g = await _get_graph()
    return g.serialize_for_frontend()


@app.get("/graph/impact/{node_id}", tags=["Graph"])
async def get_impact(node_id: str) -> dict[str, Any]:
    g = await _get_graph()
    cascade = g.compute_impact_cascade(node_id)
    if cascade is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not in graph")
    return {"node_id": node_id, "cascade": cascade}


# ── Critical Thinking ────────────────────────────────────────────────────────

@app.get("/critical-thinking/{node_id}", tags=["Critical Thinking"])
async def analyse_node(node_id: str) -> dict[str, Any]:
    db = await _get_db()
    node_dict = await db.get_node(node_id)
    if node_dict is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    g = await _get_graph()
    scanner = CriticalThinkingEngine(g)
    node = KnowledgeNodeModel(
        node_type=node_dict.get("node_type", "CONCEPT"),
        title=node_dict.get("title", node_dict.get("label", "")),
        content=node_dict.get("content", ""),
        confidence_score=node_dict.get("confidence_score", 1.0),
    )
    findings = scanner.scan_node(node)
    return {"node_id": node_id, "findings": [f.to_dict() for f in findings]}


# ── Timeline ─────────────────────────────────────────────────────────────────

@app.get("/timeline/{entity_id}", tags=["Timeline"])
async def get_timeline(entity_id: str) -> dict[str, Any]:
    db = await _get_db()
    ledger = TimelineEngine(db)
    events = await ledger.get_entity_history(entity_id)
    return {"entity_id": entity_id, "events": events}


# ── AI Assistant ─────────────────────────────────────────────────────────────

@app.post("/assistant/ask", tags=["AI Assistant"])
async def ask_assistant(payload: AskRequest) -> dict[str, Any]:
    db = await _get_db()
    search_engine = await _get_search()
    assistant = AIResearchAssistant(db, search_engine)
    return await assistant.answer(question=payload.question, top_k=payload.top_k)


# ── Simulation ───────────────────────────────────────────────────────────────

@app.get("/simulation/nodes", tags=["Simulation"])
async def simulation_nodes() -> dict[str, Any]:
    g = await _get_graph()
    lab = SimulationLab(g.graph)
    return {"nodes": lab.list_nodes()}


@app.post("/simulation/run", tags=["Simulation"])
async def run_simulation(payload: SimulationRequest) -> dict[str, Any]:
    g = await _get_graph()
    lab = SimulationLab(g.graph)
    report = lab.run_scenario(
        toggled_node_ids=payload.toggled_node_ids,
        scenario_label=payload.scenario_label,
    )
    return report.to_dict()


# ── External Factual Verification ──────────────────────────────────────────

@app.post("/verify/claim/{claim_id}", tags=["Verification"])
async def verify_claim(claim_id: str) -> dict[str, Any]:
    db = await _get_db()
    # Look up claim from database
    claim = await db.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found")
    verifier = ExternalVerificationEngine(db)
    rec = await verifier.verify_and_record(claim)
    return rec.model_dump()


@app.get("/verify/reports", tags=["Verification"])
async def get_verification_reports(limit: int = 50) -> dict[str, Any]:
    db = await _get_db()
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            """
            SELECT id, claim_id, external_source_name, external_source_url, external_excerpt, status, explanation, retrieved_at
            FROM external_verifications
            ORDER BY retrieved_at DESC LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return {"reports": [dict(r) for r in rows]}


