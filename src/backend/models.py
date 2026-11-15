"""
MindVault Database Core Models & Unified Schema
Enforces strict type validation and referential integrity across the Knowledge Bus.
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
    relation_type: str  # e.g., 'DEPENDS_ON', 'DERIVED_FROM', 'CONTRADICTS'
    weight: float = 1.0
    metadata_json: Optional[str] = None
    created_at: str = Field(default_factory=utc_now)
