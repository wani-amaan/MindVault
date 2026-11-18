"""
MindVault Asynchronous SQLite Engine with WAL & FTS5
Provides atomic, high-performance database operations and full-text search.
"""
import os
import aiosqlite
from typing import Optional, List, Dict, Any
from src.backend.models import (
    DocumentModel, KnowledgeNodeModel, ClaimModel,
    EvidenceModel, ContradictionModel, GraphEdgeModel
)

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash_sha256 TEXT NOT NULL UNIQUE,
    mime_type TEXT NOT NULL,
    page_count INTEGER DEFAULT 1,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    modality TEXT NOT NULL,
    source_doc_id TEXT REFERENCES documents(id) ON DELETE SET NULL,
    source_location_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    source_doc_id TEXT REFERENCES documents(id) ON DELETE RESTRICT,
    polarity TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    reliability_tier TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contradictions (
    id TEXT PRIMARY KEY,
    claim_a_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    claim_b_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    severity TEXT NOT NULL,
    explanation TEXT NOT NULL,
    resolution_status TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS graph_edges (
    id TEXT PRIMARY KEY,
    source_node_id TEXT NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_node_id TEXT NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);


-- 7. Audit and Belief Evolution Timeline
CREATE TABLE IF NOT EXISTS timeline_events (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    previous_state_json TEXT,
    new_state_json TEXT,
    reason TEXT,
    created_at TEXT NOT NULL
);

-- Full-Text Search (FTS5) for instant sub-millisecond keyword lookup
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    node_id UNINDEXED,
    title,
    content,
    tokenize = 'porter unicode61'
);
"""

class DatabaseEngine:
    def __init__(self, db_path: str = "data/mindvault.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    async def initialize(self):
        """Initializes tables, indexes, and enables WAL mode."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA_SQL)
            await db.commit()

    async def insert_node(self, node: KnowledgeNodeModel) -> KnowledgeNodeModel:
        """Inserts a knowledge node and updates the FTS5 search index."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute(
                """
                INSERT INTO knowledge_nodes (id, node_type, title, content, status, confidence_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (node.id, node.node_type.value, node.title, node.content, node.status.value, node.confidence_score, node.created_at, node.updated_at)
            )
            # Synchronize FTS5 virtual index
            await db.execute(
                """
                INSERT INTO knowledge_fts (node_id, title, content)
                VALUES (?, ?, ?)
                """,
                (node.id, node.title, node.content)
            )
            await db.commit()
            return node

    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single knowledge node by its UUID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM knowledge_nodes WHERE id = ?", (node_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def search_fts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Executes a BM25 ranked full-text search against the FTS5 index."""
        # Sanitize query for FTS5 syntax
        sanitized = "".join(c for c in query if c.isalnum() or c in (" ", "-", "_", "*")).strip()
        if not sanitized:
            return []

        # Tokenize query into words and search with OR to support natural language questions
        words = [w for w in sanitized.split() if len(w) > 1]
        fts_match = " OR ".join(f'"{w}"*' for w in words) if words else f'"{sanitized}"*'

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            try:
                async with db.execute(
                    """
                    SELECT 
                        n.id, n.node_type, n.title, n.content, n.status, n.confidence_score,
                        bm25(knowledge_fts) as rank
                    FROM knowledge_fts fts
                    JOIN knowledge_nodes n ON fts.node_id = n.id
                    WHERE knowledge_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_match, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in rows]
            except Exception:
                return []

    async def insert_claim(self, claim: ClaimModel) -> ClaimModel:
        """Inserts an atomic claim linked to a knowledge node."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute(
                """
                INSERT INTO claims (id, node_id, subject, predicate, object, modality, source_doc_id, source_location_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (claim.id, claim.node_id, claim.subject, claim.predicate, claim.object, claim.modality.value, claim.source_doc_id, claim.source_location_json, claim.created_at)
            )
            await db.commit()
            return claim

    async def insert_edge(self, edge: GraphEdgeModel) -> GraphEdgeModel:
        """Inserts an ontological or causal directed edge."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute(
                """
                INSERT INTO graph_edges (id, source_node_id, target_node_id, relation_type, weight, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (edge.id, edge.source_node_id, edge.target_node_id, edge.relation_type, edge.weight, edge.metadata_json, edge.created_at)
            )
            await db.commit()
            return edge

