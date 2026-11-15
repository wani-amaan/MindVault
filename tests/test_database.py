"""
Phase 2 Database Engine & FTS5 Unit Tests
Verifies schema creation, node inserts, foreign key constraints, and BM25 search.
"""
import pytest
import os
import asyncio
from src.backend.models import (
    KnowledgeNodeModel, NodeType, NodeStatus,
    ClaimModel, ClaimModality, GraphEdgeModel
)
from src.backend.database import DatabaseEngine

TEST_DB_PATH = "data/test_mindvault.db"

@pytest.fixture
async def db():
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass
    engine = DatabaseEngine(db_path=TEST_DB_PATH)
    await engine.initialize()
    yield engine
    # Cleanup after test
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass

@pytest.mark.asyncio
async def test_database_initialization(db):
    """Ensure database initializes without errors."""
    assert os.path.exists(TEST_DB_PATH)

@pytest.mark.asyncio
async def test_node_insertion_and_retrieval(db):
    """Test inserting a knowledge node and fetching it by UUID."""
    node = KnowledgeNodeModel(
        node_type=NodeType.CLAIM,
        title="Epistemic Fallibility Principle",
        content="Any empirical claim is subject to potential contradiction by future evidence.",
        status=NodeStatus.VERIFIED,
        confidence_score=0.95
    )
    inserted = await db.insert_node(node)
    fetched = await db.get_node(inserted.id)
    
    assert fetched is not None
    assert fetched["id"] == node.id
    assert fetched["title"] == "Epistemic Fallibility Principle"
    assert fetched["confidence_score"] == 0.95

@pytest.mark.asyncio
async def test_fts5_full_text_search(db):
    """Verify that SQLite FTS5 indexes and ranks results via BM25."""
    node1 = KnowledgeNodeModel(
        node_type=NodeType.NOTE,
        title="Quantum Decoherence Analysis",
        content="Decoherence explains the transition from quantum probabilities to classical mechanics."
    )
    node2 = KnowledgeNodeModel(
        node_type=NodeType.NOTE,
        title="Cellular Mitosis Stages",
        content="Mitosis divides chromosomes in a cell nucleus during biological division."
    )
    await db.insert_node(node1)
    await db.insert_node(node2)

    # Search for quantum
    results = await db.search_fts("quantum")
    assert len(results) == 1
    assert results[0]["title"] == "Quantum Decoherence Analysis"

    # Search for chromosomes
    results_bio = await db.search_fts("chromosomes")
    assert len(results_bio) == 1
    assert results_bio[0]["title"] == "Cellular Mitosis Stages"

@pytest.mark.asyncio
async def test_claim_foreign_key_constraint(db):
    """Ensure claims correctly link to parent knowledge nodes."""
    node = KnowledgeNodeModel(
        node_type=NodeType.CONCEPT,
        title="General Relativity",
        content="Gravity is spacetime curvature caused by mass and energy."
    )
    await db.insert_node(node)

    claim = ClaimModel(
        node_id=node.id,
        subject="Gravity",
        predicate="causes",
        object="Time dilation",
        modality=ClaimModality.CERTAIN
    )
    inserted_claim = await db.insert_claim(claim)
    assert inserted_claim.id is not None
    assert inserted_claim.node_id == node.id
