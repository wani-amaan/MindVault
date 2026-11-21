import pytest
import os
from src.backend.models import (
    KnowledgeNodeModel, NodeType, ClaimModel, ClaimModality,
    ContradictionSeverity
)
from src.backend.database import DatabaseEngine
from src.backend.search import HybridSearchEngine
from src.backend.contradiction import ContradictionDetectionEngine

TEST_DB_PATH = "data/test_contra_pipeline.db"
TEST_VECTOR_PATH = "data/test_vectors_contra_pipe.json"

@pytest.fixture
async def setup_contra_engine():
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
async def test_temporal_divergence_is_not_direct_contradiction(setup_contra_engine):
    """Claims from different years (e.g. 2022 vs 2024) must not be flagged as DIRECT_MUTUAL_EXCLUSION."""
    db, engine = setup_contra_engine

    c2022 = ClaimModel(
        node_id="n_temp",
        subject="US Inflation Rate",
        predicate="rose",
        object="9.1 percent",
        temporal_scope="2022"
    )
    c2024 = ClaimModel(
        node_id="n_temp",
        subject="US Inflation Rate",
        predicate="fell",
        object="3.0 percent",
        temporal_scope="2024"
    )

    conflict = engine.evaluate_pair(c2022, c2024)
    assert conflict is not None
    assert conflict.severity == ContradictionSeverity.TEMPORAL_EVOLUTION
    assert "factual evolution" in conflict.explanation.lower()

@pytest.mark.asyncio
async def test_explicit_negation_flag_triggers_conflict(setup_contra_engine):
    """Opposing negation flags on same predicate and object must trigger DIRECT_MUTUAL_EXCLUSION."""
    db, engine = setup_contra_engine

    c_true = ClaimModel(
        node_id="n_neg",
        subject="Quantum teleportation",
        predicate="allows",
        object="faster than light communication",
        is_negated=False
    )
    c_false = ClaimModel(
        node_id="n_neg",
        subject="Quantum teleportation",
        predicate="allows",
        object="faster than light communication",
        is_negated=True
    )

    conflict = engine.evaluate_pair(c_true, c_false)
    assert conflict is not None
    assert conflict.severity == ContradictionSeverity.DIRECT_MUTUAL_EXCLUSION
    assert "Direct conflict detected" in conflict.explanation
