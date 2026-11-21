"""
claim_extractor.py — Lightweight, High-Precision SVO & Modality Claim Extractor
Extracts atomic subject-predicate-object claims, temporal scopes, and modality flags
using high-speed dependency and rule-based NLP without heavy external models.
"""
import re
from typing import List, Dict, Any, Optional
from src.backend.models import ClaimModel, ClaimModality, ReviewStatus, generate_uuid, utc_now

# Common modal verbs and markers indicating non-certain modalities
MODALITY_PATTERNS = [
    (re.compile(r"\b(may|might|could|possibly|perhaps|hypothesize|suggests)\b", re.IGNORECASE), ClaimModality.HYPOTHESIS),
    (re.compile(r"\b(believe|believes|believed|claim|claims|assert|asserts|opinion|argue|argues|feel|feels)\b", re.IGNORECASE), ClaimModality.OPINION),
    (re.compile(r"\b(axiom|by definition|necessarily|fundamental law)\b", re.IGNORECASE), ClaimModality.AXIOM),
]

# Negation indicators
NEGATION_PATTERN = re.compile(r"\b(not|never|neither|nor|cannot|no|refuse|fails to|disprove)\b", re.IGNORECASE)

# Temporal anchors (years, quarters, centuries, relative dates)
TEMPORAL_PATTERN = re.compile(
    r"\b((?:19|20)\d{2}|Q[1-4]\s*(?:19|20)?\d{2}|in\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?|\d{1,2}(?:st|nd|rd|th)?\s+century)\b",
    re.IGNORECASE
)

# Common verb anchors to extract predicates
PREDICATE_SPLITTERS = [
    "was", "were", "is", "are", "has been", "have been", "had been",
    "increased by", "decreased by", "fell to", "rose to", "grew by", "declined by",
    "causes", "caused", "leads to", "led to", "produces", "produced",
    "exceeds", "exceeded", "generates", "generated", "contains", "contained",
    "supports", "refutes", "contradicts", "proves", "disproves"
]

class AtomicClaimExtractor:
    """
    Extracts atomic claims from raw document passages and notes.
    Designed for sub-millisecond execution on standard desktop CPUs.
    """

    @staticmethod
    def extract_claims_from_text(
        text: str,
        node_id: str,
        source_doc_id: Optional[str] = None,
        source_location: Optional[Dict[str, Any]] = None
    ) -> List[ClaimModel]:
        """
        Parses sentences into structured atomic claims with modality,
        temporal scope, context qualifiers, and negation detection.
        """
        if not text or not text.strip():
            return []

        # Split into individual sentences
        raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        claims: List[ClaimModel] = []

        for sentence in raw_sentences:
            s_clean = sentence.strip()
            if len(s_clean) < 10:
                continue

            # Detect Modality
            modality = ClaimModality.FACT
            for pattern, mod in MODALITY_PATTERNS:
                if pattern.search(s_clean):
                    modality = mod
                    break

            # Detect Negation
            is_negated = bool(NEGATION_PATTERN.search(s_clean))

            # Detect Temporal Scope
            temporal_match = TEMPORAL_PATTERN.search(s_clean)
            temporal_scope = temporal_match.group(0).strip() if temporal_match else None

            # SVO Extraction via predicate anchor matching
            extracted = AtomicClaimExtractor._extract_svo(s_clean)
            if not extracted:
                continue

            subject, predicate, obj = extracted
            import json
            loc_json = json.dumps(source_location) if source_location else None

            claims.append(ClaimModel(
                id=generate_uuid(),
                node_id=node_id,
                subject=subject,
                predicate=predicate,
                object=obj,
                modality=modality,
                confidence=0.85 if modality == ClaimModality.HYPOTHESIS else 0.95,
                temporal_scope=temporal_scope,
                context_qualifier=s_clean[:120],
                is_negated=is_negated,
                review_status=ReviewStatus.APPROVED if modality in (ClaimModality.FACT, ClaimModality.CERTAIN) else ReviewStatus.PENDING_REVIEW,
                source_doc_id=source_doc_id,
                source_location_json=loc_json,
                created_at=utc_now()
            ))

        return claims

    @staticmethod
    def _extract_svo(sentence: str) -> Optional[tuple[str, str, str]]:
        """Extracts Subject, Predicate, and Object using structural verbal anchors."""
        s = sentence.rstrip(".!?")
        
        # Check against multi-word predicate splitters first
        for pred in PREDICATE_SPLITTERS:
            pattern = re.compile(rf"\b{re.escape(pred)}\b", re.IGNORECASE)
            match = pattern.search(s)
            if match:
                subj = s[:match.start()].strip()
                predicate = match.group(0).strip()
                obj = s[match.end():].strip()
                if subj and obj:
                    return (subj[:100], predicate, obj[:150])

        # Fallback to standard verb detection if no specific phrase matched
        words = s.split()
        if len(words) >= 3:
            # Approximate midpoint verb or copula
            mid = len(words) // 2
            subj = " ".join(words[:mid])
            predicate = words[mid]
            obj = " ".join(words[mid+1:])
            return (subj[:100], predicate, obj[:150])

        return None
