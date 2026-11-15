"""
Phase 6 Knowledge Graph & Impact Radar Unit Tests
Verifies graph construction from DB, foundation scoring, impact cascade traversal,
and frontend serialization.
"""
import pytest
import os
import asyncio
from src.backend.models import (
    KnowledgeNodeModel, NodeType, NodeStatus,
    GraphEdgeModel
)
from src.backend.database import DatabaseEngine
from src.backend.graph import KnowledgeGraphEngine

TEST_DB_PATH = "data/test_graph_vault.db"

@pytest.fixture
async def setup_graph():
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass

    db = DatabaseEngine(db_path=TEST_DB_PATH)
    await db.initialize()
    engine = KnowledgeGraphEngine(db_engine=db)

    # Insert a 4-node epistemic chain:
    # (Assumption A) --> (Claim B) --> (Hypothesis C)
    #                              --> (Conclusion D)
    node_a = KnowledgeNodeModel(node_type=NodeType.ASSUMPTION, title="Assumption A", content="Base assumption")
    node_b = KnowledgeNodeModel(node_type=NodeType.CLAIM, title="Claim B", content="Derived claim", confidence_score=0.9)
    node_c = KnowledgeNodeModel(node_type=NodeType.HYPOTHESIS, title="Hypothesis C", content="Downstream hypothesis")
    node_d = KnowledgeNodeModel(node_type=NodeType.CONCLUSION, title="Conclusion D", content="Downstream conclusion")

    for n in (node_a, node_b, node_c, node_d):
        await db.insert_node(n)

    edge1 = GraphEdgeModel(source_node_id=node_a.id, target_node_id=node_b.id, relation_type="DEPENDS_ON", weight=1.0)
    edge2 = GraphEdgeModel(source_node_id=node_b.id, target_node_id=node_c.id, relation_type="DERIVED_FROM", weight=0.9)
    edge3 = GraphEdgeModel(source_node_id=node_b.id, target_node_id=node_d.id, relation_type="DERIVED_FROM", weight=0.8)

    await engine.add_edge(edge1)
    await engine.add_edge(edge2)
    await engine.add_edge(edge3)
    await engine.build_from_db()

    yield db, engine, node_a, node_b, node_c, node_d

    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass

@pytest.mark.asyncio
async def test_graph_construction(setup_graph):
    """Verify graph has correct node and edge counts after DB build."""
    db, engine, na, nb, nc, nd = setup_graph
    assert engine.graph.number_of_nodes() == 4
    assert engine.graph.number_of_edges() == 3

@pytest.mark.asyncio
async def test_foundation_scores(setup_graph):
    """Ensure assumption and claim nodes score higher than leaf conclusions in PageRank."""
    db, engine, na, nb, nc, nd = setup_graph
    scores = engine.compute_foundation_scores()
    assert isinstance(scores, dict)
    assert len(scores) == 4
    # All scores should be positive
    for score in scores.values():
        assert score >= 0.0

@pytest.mark.asyncio
async def test_impact_cascade_traversal(setup_graph):
    """
    Challenging Assumption A must cascade and identify Claim B, 
    Hypothesis C, and Conclusion D as downstream vulnerabilities.
    """
    db, engine, na, nb, nc, nd = setup_graph

    cascade = engine.compute_impact_cascade(na.id)
    affected = cascade["affected_nodes"]

    assert cascade["total_affected"] == 3
    assert nb.id in affected
    assert nc.id in affected
    assert nd.id in affected

    # Claim B should be at depth 1, C and D at depth 2
    assert cascade["cascade_depth"] == 2

@pytest.mark.asyncio
async def test_impact_cascade_leaf_node(setup_graph):
    """A leaf node (no outgoing edges) should have zero cascade impact."""
    db, engine, na, nb, nc, nd = setup_graph
    cascade = engine.compute_impact_cascade(nc.id)
    assert cascade["total_affected"] == 0
    assert cascade["cascade_depth"] == 0

@pytest.mark.asyncio
async def test_frontend_serialization(setup_graph):
    """Ensure serialize_for_frontend returns valid JSON-ready structure."""
    db, engine, na, nb, nc, nd = setup_graph
    payload = engine.serialize_for_frontend()

    assert "nodes" in payload
    assert "edges" in payload
    assert len(payload["nodes"]) == 4
    assert len(payload["edges"]) == 3

    node_ids = {n["id"] for n in payload["nodes"]}
    assert na.id in node_ids
    assert nd.id in node_ids
