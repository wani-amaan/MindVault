import pytest
from src.backend.claim_extractor import AtomicClaimExtractor
from src.backend.models import ClaimModality, ReviewStatus

def test_atomic_claim_extraction_svo():
    text = "Atmospheric carbon increases global temperature. Solar output was stable in 2024."
    claims = AtomicClaimExtractor.extract_claims_from_text(text, node_id="test_node_1")
    assert len(claims) >= 1
    c1 = claims[0]
    assert "Atmospheric carbon" in c1.subject or "temperature" in c1.object
    assert c1.node_id == "test_node_1"

def test_claim_modality_detection():
    fact_text = "The speed of light is 299792458 meters per second."
    hypo_text = "Dark energy might decay into phantom radiation over time."
    opinion_text = "Analysts believe inflation will fall sharply."

    c_fact = AtomicClaimExtractor.extract_claims_from_text(fact_text, "n1")[0]
    c_hypo = AtomicClaimExtractor.extract_claims_from_text(hypo_text, "n2")[0]
    c_opinion = AtomicClaimExtractor.extract_claims_from_text(opinion_text, "n3")[0]

    assert c_fact.modality in (ClaimModality.FACT, ClaimModality.CERTAIN)
    assert c_fact.review_status == ReviewStatus.APPROVED

    assert c_hypo.modality == ClaimModality.HYPOTHESIS
    assert c_hypo.review_status == ReviewStatus.PENDING_REVIEW

    assert c_opinion.modality == ClaimModality.OPINION

def test_temporal_scope_and_negation():
    text = "Company revenue was not profitable in 2023."
    claims = AtomicClaimExtractor.extract_claims_from_text(text, "n4")
    assert len(claims) == 1
    c = claims[0]
    assert c.is_negated is True
    assert c.temporal_scope == "2023"
