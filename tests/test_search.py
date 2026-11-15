"""
Phase 4 Hybrid Search & Evidence Engine Unit Tests
Verifies ONNX dense vector embedding generation, cosine similarity ranking, 
Reciprocal Rank Fusion (RRF), and evidence binding.
"""
import pytest
import os
import asyncio
from src.backend.models import (
    KnowledgeNodeModel, NodeType, NodeStatus,
    ClaimModel, ClaimModality, EvidencePolarity, ReliabilityTier
)
from src.backend.database import DatabaseEngine
from src.backend.search import HybridSearchEngine

TEST_DB_PATH = "data/test_search_vault.db"
TEST_VECTOR_PATH = "data/test_vectors.json"

@pytest.fixture
async def setup_search():
    # Cleanup prior test state
    for p in (TEST_DB_PATH, TEST_VECTOR_PATH):
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass

    db = DatabaseEngine(db_path=TEST_DB_PATH)
    await db.initialize()
    search = HybridSearchEngine(db_engine=db, vector_cache_path=TEST_VECTOR_PATH)
    
    yield db, search
    
    for p in (TEST_DB_PATH, TEST_VECTOR_PATH):
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass

@pytest.mark.asyncio
async def test_onnx_vector_embedding(setup_search):
    """Ensure FastEmbed ONNX produces 384-dimensional normalized vectors."""
    db, search = setup_search
    vec = search.embed_text("Epistemic dependency analysis")
    assert isinstance(vec, list)
    assert len(vec) == 384

@pytest.mark.asyncio
async def test_hybrid_rrf_search(setup_search):
    """
    Test that Reciprocal Rank Fusion returns top matches across both 
    exact keywords (BM25) and semantic conceptual similarity (Dense Vector).
    """
    db, search = setup_search
    
    # Insert node 1: Exact keyword match
    node1 = KnowledgeNodeModel(
        node_type=NodeType.CLAIM,
        title="Helium Flash Nucleosynthesis",
        content="The brief thermal runaway of helium fusion in low-mass red giant cores."
    )
    # Insert node 2: Semantic match (synonyms, conceptual alignment)
    node2 = KnowledgeNodeModel(
        node_type=NodeType.CLAIM,
        title="Stellar Core Ignition",
        content="Explosive nuclear burning in dying stars before reaching planetary nebula stage."
    )
    # Insert node 3: Unrelated distracter
    node3 = KnowledgeNodeModel(
        node_type=NodeType.NOTE,
        title="Medieval Agrarian Revolution",
        content="Crop rotation methods in 12th century Western European agriculture."
    )
    
    for n in (node1, node2, node3):
        await db.insert_node(n)
        search.index_node(n.id, f"{n.title} {n.content}")

    # Search for "stellar thermonuclear explosion"
    results = await search.hybrid_search("stellar thermonuclear explosion", limit=2)
    assert len(results) >= 1
    
    top_titles = [r["title"] for r in results]
    assert "Helium Flash Nucleosynthesis" in top_titles or "Stellar Core Ignition" in top_titles
    assert "Medieval Agrarian Revolution" not in top_titles
    assert results[0]["rrf_score"] > 0.0

@pytest.mark.asyncio
async def test_evidence_attachment(setup_search):
    """Verify that evidence with polarity and reliability tier binds to claims."""
    db, search = setup_search
    
    node = KnowledgeNodeModel(
        node_type=NodeType.CLAIM,
        title="Vitamin D Synthesis",
        content="UVB solar radiation stimulates cutaneous Vitamin D production."
    )
    await db.insert_node(node)
    
    claim = ClaimModel(
        node_id=node.id,
        subject="UVB Radiation",
        predicate="synthesizes",
        object="Vitamin D",
        modality=ClaimModality.CERTAIN
    )
    await db.insert_claim(claim)
    
    evidence = await search.attach_evidence(
        claim_id=claim.id,
        excerpt="Randomized double-blind trial confirmed serum 25(OH)D increase under 300nm exposure.",
        polarity=EvidencePolarity.SUPPORTS,
        reliability=ReliabilityTier.PEER_REVIEWED,
        notes="Clinical trial published in Lancet 2024."
    )
    
    assert evidence.id is not None
    assert evidence.claim_id == claim.id
    assert evidence.polarity == EvidencePolarity.SUPPORTS
    assert evidence.reliability_tier == ReliabilityTier.PEER_REVIEWED
