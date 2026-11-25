import pytest
import os
from src.backend.models import (
    KnowledgeNodeModel,
    NodeType,
    ClaimModel,
    ClaimModality,
    VerificationStatus,
)
from src.backend.database import DatabaseEngine
from src.backend.external_verification import ExternalVerificationEngine

TEST_DB_PATH = "data/test_verification_vault.db"

@pytest.fixture
async def setup_verification():
    for p in (TEST_DB_PATH,):
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass

    db = DatabaseEngine(db_path=TEST_DB_PATH)
    await db.initialize()
    engine = ExternalVerificationEngine(db_engine=db)

    yield db, engine

    for p in (TEST_DB_PATH,):
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass

def test_external_verification_supported(setup_verification):
    _, engine = setup_verification
    claim = ClaimModel(
        node_id="node-test-1",
        subject="Python",
        predicate="is",
        object="programming language",
        modality=ClaimModality.FACT
    )
    mock_wiki = {
        "source": "Wikipedia",
        "title": "Python (programming language)",
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "extract": "Python is a high-level, general-purpose programming language.",
        "description": "Programming language"
    }
    rec = engine.evaluate_claim(claim, external_evidence=mock_wiki)
    assert rec.status == VerificationStatus.VERIFIED_SUPPORTED
    assert "Corroborated by Wikipedia" in rec.explanation

def test_external_verification_contradicted(setup_verification):
    _, engine = setup_verification
    claim = ClaimModel(
        node_id="node-test-2",
        subject="Python",
        predicate="is not",
        object="programming language",
        is_negated=True,
        modality=ClaimModality.FACT
    )
    mock_wiki = {
        "source": "Wikipedia",
        "title": "Python (programming language)",
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "extract": "Python is a high-level, general-purpose programming language.",
        "description": "Programming language"
    }
    rec = engine.evaluate_claim(claim, external_evidence=mock_wiki)
    assert rec.status == VerificationStatus.CONTRADICTED_BY_EVIDENCE
    assert "negates relation" in rec.explanation

def test_external_verification_outdated_scope(setup_verification):
    _, engine = setup_verification
    claim = ClaimModel(
        node_id="node-test-3",
        subject="Federal Reserve interest rate",
        predicate="stands at",
        object="0.25%",
        temporal_scope="in 2020",
        modality=ClaimModality.FACT
    )
    mock_wiki = {
        "source": "Wikipedia",
        "title": "Federal Reserve",
        "extract": "The Federal Reserve set target rates between 5.25% and 5.50% in recent actions."
    }
    rec = engine.evaluate_claim(claim, external_evidence=mock_wiki)
    assert rec.status == VerificationStatus.OUTDATED_INFORMATION

@pytest.mark.asyncio
async def test_external_verification_db_persistence(setup_verification):
    db, engine = setup_verification
    node = KnowledgeNodeModel(node_type=NodeType.NOTE, title="Test Node", content="Test")
    await db.insert_node(node)
    claim = ClaimModel(
        node_id=node.id,
        subject="Rust",
        predicate="provides",
        object="memory safety",
        modality=ClaimModality.FACT
    )
    await db.insert_claim(claim)
    mock_evidence = {
        "source": "Official Docs",
        "extract": "Rust is a systems programming language that provides memory safety without garbage collection."
    }
    rec = await engine.verify_and_record(claim, mock_evidence)
    assert rec.status == VerificationStatus.VERIFIED_SUPPORTED
    assert rec.claim_id == claim.id
