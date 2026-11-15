"""
Phase 5 Contradiction Detection Unit Tests
Verifies direct mutual exclusion, numerical discrepancies, explainable rationales, 
and contradiction registry persistence.
"""
import pytest
import os
import asyncio
from src.backend.models import (
    KnowledgeNodeModel, NodeType, ClaimModel, ClaimModality,
    ContradictionSeverity
)
from src.backend.database import DatabaseEngine
from src.backend.search import HybridSearchEngine
from src.backend.contradiction import ContradictionDetectionEngine

TEST_DB_PATH = "data/test_contradiction_vault.db"
TEST_VECTOR_PATH = "data/test_vectors_contra.json"

@pytest.fixture
async def setup_engine():
    for p in (TEST_DB_PATH, TEST_VECTOR_PATH):
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass

    db = DatabaseEngine(db_path=TEST_DB_PATH)
    await db.initialize()
    search = HybridSearchEngine(db_engine=db, vector_cache_path=TEST_VECTOR_PATH)
    engine = ContradictionDetectionEngine(db_engine=db, search_engine=search)

    yield db, engine

    for p in (TEST_DB_PATH, TEST_VECTOR_PATH):
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass

@pytest.mark.asyncio
async def test_direct_mutual_exclusion(setup_engine):
    """Ensure opposing predicates (e.g. causes vs prevents) trigger DIRECT_MUTUAL_EXCLUSION."""
    db, engine = setup_engine

    node = KnowledgeNodeModel(
        node_type=NodeType.NOTE,
        title="Dietary Saturated Fat Notes",
        content="Debate regarding saturated fats and cardiovascular markers."
    )
    await db.insert_node(node)

    claim1 = ClaimModel(
        node_id=node.id,
        subject="Saturated fat intake",
        predicate="causes",
        object="Coronary heart disease",
        modality=ClaimModality.CERTAIN
    )
    claim2 = ClaimModel(
        node_id=node.id,
        subject="Saturated fat intake",
        predicate="prevents",
        object="Coronary heart disease",
        modality=ClaimModality.CERTAIN
    )
    await db.insert_claim(claim1)
    await db.insert_claim(claim2)

    conflict = engine.evaluate_pair(claim1, claim2)
    assert conflict is not None
    assert conflict.severity == ContradictionSeverity.DIRECT_MUTUAL_EXCLUSION
    assert "Direct conflict detected" in conflict.explanation
    assert conflict.resolution_status == "OPEN"

@pytest.mark.asyncio
async def test_numerical_discrepancy(setup_engine):
    """Ensure identical entities with differing numerical assertions trigger NUMERICAL_DISCREPANCY."""
    db, engine = setup_engine

    node = KnowledgeNodeModel(
        node_type=NodeType.NOTE,
        title="Economic GDP Forecasts",
        content="Economic growth forecasts for Q3."
    )
    await db.insert_node(node)

    claim1 = ClaimModel(
        node_id=node.id,
        subject="Annual GDP growth",
        predicate="equals",
        object="5.2%",
        modality=ClaimModality.CERTAIN
    )
    claim2 = ClaimModel(
        node_id=node.id,
        subject="Annual GDP growth",
        predicate="equals",
        object="2.8%",
        modality=ClaimModality.CERTAIN
    )
    await db.insert_claim(claim1)
    await db.insert_claim(claim2)

    conflict = engine.evaluate_pair(claim1, claim2)
    assert conflict is not None
    assert conflict.severity == ContradictionSeverity.NUMERICAL_DISCREPANCY
    assert "Numerical discrepancy detected" in conflict.explanation

@pytest.mark.asyncio
async def test_scan_and_registry_persistence(setup_engine):
    """Ensure scan_all_claims stores detected conflicts into the persistent SQLite database."""
    db, engine = setup_engine

    node = KnowledgeNodeModel(
        node_type=NodeType.NOTE,
        title="Oncology Research",
        content="Cell cycle regulators."
    )
    await db.insert_node(node)

    claim_a = ClaimModel(
        node_id=node.id,
        subject="Gene p53",
        predicate="stimulates",
        object="Apoptosis",
        modality=ClaimModality.CERTAIN
    )
    claim_b = ClaimModel(
        node_id=node.id,
        subject="Gene p53",
        predicate="inhibits",
        object="Apoptosis",
        modality=ClaimModality.CERTAIN
    )
    await db.insert_claim(claim_a)
    await db.insert_claim(claim_b)

    conflicts = await engine.scan_all_claims([claim_a, claim_b])
    assert len(conflicts) == 1
    assert conflicts[0].severity == ContradictionSeverity.DIRECT_MUTUAL_EXCLUSION

    # Verify persistent DB record
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM contradictions WHERE id = ?", (conflicts[0].id,)) as cursor:
            row = await cursor.fetchone()
            assert row is not None
            assert row["severity"] == "DIRECT_MUTUAL_EXCLUSION"
            assert row["resolution_status"] == "OPEN"
