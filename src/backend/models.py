"""
MindVault Database Core Models & Unified Schema
Enforces strict type validation, epistemic state tracking, and referential integrity.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid
from pydantic import BaseModel, Field

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class NodeType(str, Enum):
    NOTE = "NOTE"
    CONCEPT = "CONCEPT"
    CLAIM = "CLAIM"
    ASSUMPTION = "ASSUMPTION"
    HYPOTHESIS = "HYPOTHESIS"
    QUESTION = "QUESTION"
    CONCLUSION = "CONCLUSION"
    EVIDENCE = "EVIDENCE"

class NodeStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    VERIFIED = "VERIFIED"
    CHALLENGED = "CHALLENGED"
    DEPRECATED = "DEPRECATED"

class ClaimModality(str, Enum):
    CERTAIN = "CERTAIN"
    PROBABLE = "PROBABLE"
    POSSIBLE = "POSSIBLE"
    SPECULATIVE = "SPECULATIVE"
    FACT = "FACT"
    HYPOTHESIS = "HYPOTHESIS"
    OPINION = "OPINION"
    AXIOM = "AXIOM"

class ReviewStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"

class VerificationStatus(str, Enum):
    VERIFIED_SUPPORTED = "VERIFIED_SUPPORTED"
    STRONGLY_SUPPORTED = "STRONGLY_SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED_BY_EVIDENCE = "CONTRADICTED_BY_EVIDENCE"
    OUTDATED_INFORMATION = "OUTDATED_INFORMATION"
    MISLEADING_OR_MISSING_CONTEXT = "MISLEADING_OR_MISSING_CONTEXT"
    CONFLICTING_EXTERNAL_SOURCES = "CONFLICTING_EXTERNAL_SOURCES"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_EXTERNALLY_VERIFIABLE = "NOT_EXTERNALLY_VERIFIABLE"
    PENDING_REVIEW = "PENDING_REVIEW"

class EvidencePolarity(str, Enum):
    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    QUALIFIES = "QUALIFIES"

class ReliabilityTier(str, Enum):
    PEER_REVIEWED = "PEER_REVIEWED"
    OFFICIAL_REPORT = "OFFICIAL_REPORT"
    EXPERT_OPINION = "EXPERT_OPINION"
    UNVERIFIED = "UNVERIFIED"
    ANECDOTAL = "ANECDOTAL"

class ContradictionSeverity(str, Enum):
    DIRECT_MUTUAL_EXCLUSION = "DIRECT_MUTUAL_EXCLUSION"
    NUMERICAL_DISCREPANCY = "NUMERICAL_DISCREPANCY"
    CONTEXTUAL_TENSION = "CONTEXTUAL_TENSION"
    TEMPORAL_EVOLUTION = "TEMPORAL_EVOLUTION"

# Base Pydantic Models for Application Layer
class DocumentModel(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    title: str
    file_path: str
    file_hash_sha256: str
    mime_type: str = "application/pdf"
    page_count: int = 1
    metadata_json: Optional[str] = None
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)

class KnowledgeNodeModel(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    node_type: NodeType
    title: str
    content: str
    status: NodeStatus = NodeStatus.ACTIVE
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)

class ClaimModel(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    node_id: str
    subject: str
    predicate: str
    object: str
    modality: ClaimModality = ClaimModality.CERTAIN
    source_doc_id: Optional[str] = None
    source_location_json: Optional[str] = None
    confidence: float = 1.0
    temporal_scope: Optional[str] = None
    context_qualifier: Optional[str] = None
    is_negated: bool = False
    review_status: ReviewStatus = ReviewStatus.APPROVED
    canonical_claim_id: Optional[str] = None
    created_at: str = Field(default_factory=utc_now)

class CanonicalClaimModel(BaseModel):
    """Represents a normalized canonical proposition that multiple raw document assertions point to."""
    id: str = Field(default_factory=generate_uuid)
    canonical_text: str
    subject: str
    predicate: str
    object: str
    temporal_scope: Optional[str] = None
    aggregate_confidence: float = 1.0
    verification_status: VerificationStatus = VerificationStatus.PENDING_REVIEW
    created_at: str = Field(default_factory=utc_now)

class EvidenceModel(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    claim_id: str
    source_doc_id: Optional[str] = None
    polarity: EvidencePolarity
    excerpt: str
    reliability_tier: ReliabilityTier = ReliabilityTier.UNVERIFIED
    notes: Optional[str] = None
    created_at: str = Field(default_factory=utc_now)

class ContradictionModel(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    claim_a_id: str
    claim_b_id: str
    severity: ContradictionSeverity
    explanation: str
    resolution_status: str = "OPEN"
    detected_at: str = Field(default_factory=utc_now)
    resolved_at: Optional[str] = None

class GraphEdgeModel(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    source_node_id: str
    target_node_id: str
    relation_type: str  # e.g., 'SUPPORTS', 'CONTRADICTS', 'DERIVES_FROM', 'ASSUMES', 'EXTENDS'
    weight: float = 1.0
    metadata_json: Optional[str] = None
    created_at: str = Field(default_factory=utc_now)

class ExternalVerificationRecordModel(BaseModel):
    """Stores factual verification against external ground-truth sources."""
    id: str = Field(default_factory=generate_uuid)
    claim_id: str
    external_source_name: str  # e.g., 'Wikipedia', 'PTI', 'Official'
    external_source_url: Optional[str] = None
    external_excerpt: str
    status: VerificationStatus
    explanation: str
    retrieved_at: str = Field(default_factory=utc_now)
