"""
Phase 7 Critical Thinking, Timeline & AI Assistant Unit Tests
"""
import pytest
import os
from src.backend.models import (
    KnowledgeNodeModel, NodeType, NodeStatus, GraphEdgeModel
)
from src.backend.database import DatabaseEngine
from src.backend.graph import KnowledgeGraphEngine
from src.backend.search import HybridSearchEngine
from src.backend.critical_thinking import CriticalThinkingEngine
from src.backend.timeline import TimelineEngine
from src.backend.ai_assistant import AIResearchAssistant

TEST_DB_PATH = "data/test_phase7_vault.db"
TEST_VECTOR_PATH = "data/test_vectors_phase7.json"

@pytest.fixture
async def setup_phase7():
    for p in (TEST_DB_PATH, TEST_VECTOR_PATH):
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass

    db = DatabaseEngine(db_path=TEST_DB_PATH)
    await db.initialize()
    search = HybridSearchEngine(db_engine=db, vector_cache_path=TEST_VECTOR_PATH)
    graph_engine = KnowledgeGraphEngine(db_engine=db)
    ct_engine = CriticalThinkingEngine(graph_engine=graph_engine)
    timeline = TimelineEngine(db_engine=db)
    assistant = AIResearchAssistant(db_engine=db, search_engine=search)

    yield db, graph_engine, ct_engine, timeline, assistant, search

    for p in (TEST_DB_PATH, TEST_VECTOR_PATH):
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass

# --- Critical Thinking Tests ---

@pytest.mark.asyncio
async def test_correlation_causation_flag(setup_phase7):
    """Ensure node with both correlation AND causation language is flagged."""
    db, graph, ct, timeline, assistant, search = setup_phase7

    node = KnowledgeNodeModel(
        node_type=NodeType.CLAIM,
        title="Ice Cream Drowning",
        content="Ice cream sales are associated with drowning rates, therefore ice cream causes drowning."
    )
    await db.insert_node(node)

    issues = ct.scan_node(node)
    types = [i.issue_type for i in issues]
    assert "CORRELATION_CAUSATION_CONFUSION" in types

@pytest.mark.asyncio
async def test_unsupported_leap_flag(setup_phase7):
    """Ensure nodes with 'therefore' or 'thus' without evidence are flagged."""
    db, graph, ct, timeline, assistant, search = setup_phase7

    node = KnowledgeNodeModel(
        node_type=NodeType.CLAIM,
        title="Logical Leap Example",
        content="The patient recovered. Therefore, the treatment was effective."
    )
    await db.insert_node(node)

    issues = ct.scan_node(node)
    types = [i.issue_type for i in issues]
    assert "UNSUPPORTED_LOGICAL_LEAP" in types

@pytest.mark.asyncio
async def test_circular_dependency_detection(setup_phase7):
    """Ensure a circular epistemic chain A -> B -> A is detected."""
    db, graph, ct, timeline, assistant, search = setup_phase7

    node_a = KnowledgeNodeModel(node_type=NodeType.CLAIM, title="Claim A", content="A is true because B.")
    node_b = KnowledgeNodeModel(node_type=NodeType.CLAIM, title="Claim B", content="B is true because A.")
    await db.insert_node(node_a)
    await db.insert_node(node_b)

    edge_ab = GraphEdgeModel(source_node_id=node_a.id, target_node_id=node_b.id, relation_type="DEPENDS_ON")
    edge_ba = GraphEdgeModel(source_node_id=node_b.id, target_node_id=node_a.id, relation_type="DEPENDS_ON")
    await graph.add_edge(edge_ab)
    await graph.add_edge(edge_ba)
    await graph.build_from_db()

    issues = ct.detect_circular_dependencies()
    types = [i.issue_type for i in issues]
    assert "CIRCULAR_DEPENDENCY" in types

# --- Timeline Tests ---

@pytest.mark.asyncio
async def test_timeline_record_and_retrieve(setup_phase7):
    """Verify timeline records events and retrieves full history for an entity."""
    db, graph, ct, timeline, assistant, search = setup_phase7

    node = KnowledgeNodeModel(node_type=NodeType.CLAIM, title="Evolving Claim", content="Initial content.")
    await db.insert_node(node)

    await timeline.record(
        entity_id=node.id,
        event_type="CLAIM_CREATED",
        new_state={"title": node.title, "content": node.content},
        reason="Initial knowledge entry"
    )
    await timeline.record(
        entity_id=node.id,
        event_type="CONFIDENCE_ADJUSTED",
        previous_state={"confidence_score": 1.0},
        new_state={"confidence_score": 0.7},
        reason="New contradicting evidence found"
    )

    history = await timeline.get_entity_history(node.id)
    assert len(history) == 2
    assert history[0]["event_type"] == "CLAIM_CREATED"
    assert history[1]["event_type"] == "CONFIDENCE_ADJUSTED"

@pytest.mark.asyncio
async def test_timeline_fingerprint_integrity(setup_phase7):
    """Verify each timeline event gets a unique non-empty integrity fingerprint."""
    db, graph, ct, timeline, assistant, search = setup_phase7

    from src.backend.timeline import TimelineEvent
    event = TimelineEvent(entity_id="test-entity-id", event_type="TEST_EVENT")
    assert event.fingerprint is not None
    assert len(event.fingerprint) == 16

# --- AI Assistant Tests ---

@pytest.mark.asyncio
async def test_assistant_offline_no_vault(setup_phase7):
    """Offline assistant with empty vault returns a knowledge-gap response."""
    db, graph, ct, timeline, assistant, search = setup_phase7

    result = await assistant.answer("What is quantum entanglement?")
    assert result["provider"] == "offline"
    assert result["question"] == "What is quantum entanglement?"
    assert isinstance(result["answer"], str)

@pytest.mark.asyncio
async def test_assistant_offline_with_vault_context(setup_phase7):
    """Offline assistant retrieves and returns relevant vault nodes as context."""
    db, graph, ct, timeline, assistant, search = setup_phase7

    node = KnowledgeNodeModel(
        node_type=NodeType.NOTE,
        title="Photosynthesis",
        content="Plants convert sunlight, water and CO2 into glucose and oxygen via photosynthesis."
    )
    await db.insert_node(node)
    search.index_node(node.id, f"{node.title} {node.content}")

    result = await assistant.answer("How do plants make food from sunlight?")
    assert result["provider"] == "offline"
    assert result["retrieved_count"] >= 1
    assert len(result["source_node_ids"]) >= 1
