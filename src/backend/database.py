"""
MindVault Database Core Engine (SQLite WAL + FTS5)
Handles thread-safe asynchronous operations, relational integrity, migrations, and semantic queries.
"""
import os
import aiosqlite
from typing import Optional, Dict, Any, List
from src.backend.models import (
    KnowledgeNodeModel,
    ClaimModel,
    CanonicalClaimModel,
    GraphEdgeModel,
    EvidenceModel,
    ContradictionModel,
    ExternalVerificationRecordModel,
    ReviewStatus,
    VerificationStatus,
)

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;

-- 1. Ingested raw documents
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash_sha256 TEXT NOT NULL UNIQUE,
    mime_type TEXT NOT NULL,
    page_count INTEGER NOT NULL,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 2. Knowledge nodes (concepts, premises, facts, conclusions)
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

-- 3. Normalized Canonical Claims (shared target for multiple source assertions)
CREATE TABLE IF NOT EXISTS canonical_claims (
    id TEXT PRIMARY KEY,
    canonical_text TEXT NOT NULL,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    temporal_scope TEXT,
    aggregate_confidence REAL DEFAULT 1.0,
    verification_status TEXT DEFAULT 'PENDING_REVIEW',
    created_at TEXT NOT NULL
);

-- 4. Atomic assertions extracted from documents or nodes
CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    canonical_claim_id TEXT REFERENCES canonical_claims(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    modality TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    temporal_scope TEXT,
    context_qualifier TEXT,
    is_negated INTEGER DEFAULT 0,
    review_status TEXT DEFAULT 'APPROVED',
    source_doc_id TEXT REFERENCES documents(id) ON DELETE SET NULL,
    source_location_json TEXT,
    created_at TEXT NOT NULL
);

-- 5. Evidence linkages
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

-- 6. Contradictions Registry
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

-- 7. External Factual Verification Records
CREATE TABLE IF NOT EXISTS external_verifications (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    external_source_name TEXT NOT NULL,
    external_source_url TEXT,
    external_excerpt TEXT NOT NULL,
    status TEXT NOT NULL,
    explanation TEXT NOT NULL,
    retrieved_at TEXT NOT NULL
);

-- 8. Directed Graph Edges
CREATE TABLE IF NOT EXISTS graph_edges (
    id TEXT PRIMARY KEY,
    source_node_id TEXT NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_node_id TEXT NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

-- 9. Audit and Belief Evolution Timeline
CREATE TABLE IF NOT EXISTS timeline_events (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    previous_state_json TEXT,
    new_state_json TEXT,
    reason TEXT,
    created_at TEXT NOT NULL
);

-- 10. Full-Text Search (FTS5) for instant sub-millisecond keyword lookup
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
        """Initializes tables, indexes, migration updates, and enables WAL mode."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA_SQL)
            
            # Non-destructive incremental migrations for existing databases
            existing_cols = []
            async with db.execute("PRAGMA table_info(claims);") as cursor:
                rows = await cursor.fetchall()
                existing_cols = [r[1] for r in rows]

            migrations = [
                ("canonical_claim_id", "TEXT REFERENCES canonical_claims(id) ON DELETE SET NULL"),
                ("confidence", "REAL DEFAULT 1.0"),
                ("temporal_scope", "TEXT"),
                ("context_qualifier", "TEXT"),
                ("is_negated", "INTEGER DEFAULT 0"),
                ("review_status", "TEXT DEFAULT 'APPROVED'"),
            ]
            for col_name, col_def in migrations:
                if col_name not in existing_cols:
                    await db.execute(f"ALTER TABLE claims ADD COLUMN {col_name} {col_def};")

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
                INSERT INTO claims (
                    id, node_id, canonical_claim_id, subject, predicate, object, modality,
                    confidence, temporal_scope, context_qualifier, is_negated, review_status,
                    source_doc_id, source_location_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim.id,
                    claim.node_id,
                    claim.canonical_claim_id,
                    claim.subject,
                    claim.predicate,
                    claim.object,
                    claim.modality.value if hasattr(claim.modality, "value") else str(claim.modality),
                    claim.confidence,
                    claim.temporal_scope,
                    claim.context_qualifier,
                    1 if claim.is_negated else 0,
                    claim.review_status.value if hasattr(claim.review_status, "value") else str(claim.review_status),
                    claim.source_doc_id,
                    claim.source_location_json,
                    claim.created_at,
                )
            )
            await db.commit()
            return claim

    async def get_claims_by_node(self, node_id: str) -> List[Dict[str, Any]]:
        """Retrieves all atomic claims extracted from a given node."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM claims WHERE node_id = ?", (node_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def insert_canonical_claim(self, canonical: CanonicalClaimModel) -> CanonicalClaimModel:
        """Inserts a normalized canonical proposition."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO canonical_claims (
                    id, canonical_text, subject, predicate, object, temporal_scope, aggregate_confidence, verification_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    canonical.id,
                    canonical.canonical_text,
                    canonical.subject,
                    canonical.predicate,
                    canonical.object,
                    canonical.temporal_scope,
                    canonical.aggregate_confidence,
                    canonical.verification_status.value if hasattr(canonical.verification_status, "value") else str(canonical.verification_status),
                    canonical.created_at,
                )
            )
            await db.commit()
            return canonical

    async def insert_external_verification(self, rec: ExternalVerificationRecordModel) -> ExternalVerificationRecordModel:
        """Records an external factual verification result."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO external_verifications (
                    id, claim_id, external_source_name, external_source_url, external_excerpt, status, explanation, retrieved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.id,
                    rec.claim_id,
                    rec.external_source_name,
                    rec.external_source_url,
                    rec.external_excerpt,
                    rec.status.value if hasattr(rec.status, "value") else str(rec.status),
                    rec.explanation,
                    rec.retrieved_at,
                )
            )
            await db.commit()
            return rec

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
