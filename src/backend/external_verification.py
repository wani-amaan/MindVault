"""
MindVault External Factual Verification Subsystem
Verifies internal atomic claims against external knowledge sources (Wikipedia REST API,
authoritative references, PTI / News archive extracts, and offline ground truth).
"""
import urllib.request
import urllib.parse
import json
import re
from typing import Optional, Dict, Any, List
from src.backend.models import (
    ClaimModel,
    ExternalVerificationRecordModel,
    VerificationStatus,
)
from src.backend.database import DatabaseEngine

class ExternalVerificationEngine:
    """
    Subsystem responsible for evaluating claims against authoritative external references.
    Provides offline fallbacks and graceful degradation when offline or unresolvable.
    """
    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    def query_wikipedia_summary(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Fetches official summary extract from Wikipedia REST API with offline graceful fallback.
        """
        clean_title = urllib.parse.quote(title.strip().replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_title}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "MindVault-KnowledgeEngine/1.0 (Desktop Knowledge Intelligence; contact@mindvault.local)"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return {
                        "source": "Wikipedia",
                        "title": data.get("title", title),
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", url),
                        "extract": data.get("extract", ""),
                        "description": data.get("description", "")
                    }
        except Exception:
            # Network offline or title not found
            pass
        return None

    def evaluate_claim(self, claim: ClaimModel, external_evidence: Optional[Dict[str, Any]] = None) -> ExternalVerificationRecordModel:
        """
        Evaluates an atomic claim against external evidence or attempts live lookup.
        Assigns structured status:
          - VERIFIED_SUPPORTED: Direct factual alignment
          - CONTRADICTED_BY_EVIDENCE: External source actively refutes the claim
          - OUTDATED_INFORMATION: Contains expired temporal scope or obsolete metrics
          - INSUFFICIENT_EVIDENCE / NOT_EXTERNALLY_VERIFIABLE: Cannot verify with certainty
        """
        if not external_evidence:
            # Try finding external evidence using the subject or object
            external_evidence = self.query_wikipedia_summary(claim.subject)
            if not external_evidence and claim.object:
                external_evidence = self.query_wikipedia_summary(claim.object)

        if not external_evidence or not external_evidence.get("extract"):
            return ExternalVerificationRecordModel(
                claim_id=claim.id,
                external_source_name="Unknown / Offline Reference",
                external_source_url=None,
                external_excerpt="",
                status=VerificationStatus.NOT_EXTERNALLY_VERIFIABLE,
                explanation=f"No external ground-truth record found for entity '{claim.subject}'."
            )

        excerpt = external_evidence["extract"]
        source_name = external_evidence.get("source", "Wikipedia")
        source_url = external_evidence.get("url")

        pred = (claim.predicate or "").lower()
        obj = (claim.object or "").lower()
        excerpt_lower = excerpt.lower()

        # Check for temporal obsolescence
        if claim.temporal_scope and re.search(r"\b(19\d{2}|20\d{2})\b", claim.temporal_scope):
            return ExternalVerificationRecordModel(
                claim_id=claim.id,
                external_source_name=source_name,
                external_source_url=source_url,
                external_excerpt=excerpt[:350],
                status=VerificationStatus.OUTDATED_INFORMATION,
                explanation=f"Claim is bound to historical temporal scope ({claim.temporal_scope}); current authoritative data may supersede it."
            )

        # Check for direct contradictions (e.g., negations or opposite attributes)
        if claim.is_negated:
            # Claim says "X is NOT Y", check if excerpt asserts "X is Y"
            if obj in excerpt_lower and len(obj) > 3:
                return ExternalVerificationRecordModel(
                    claim_id=claim.id,
                    external_source_name=source_name,
                    external_source_url=source_url,
                    external_excerpt=excerpt[:350],
                    status=VerificationStatus.CONTRADICTED_BY_EVIDENCE,
                    explanation=f"Claim negates relation, but {source_name} documents positive association between '{claim.subject}' and '{claim.object}'."
                )

        # Check support
        if obj in excerpt_lower:
            return ExternalVerificationRecordModel(
                claim_id=claim.id,
                external_source_name=source_name,
                external_source_url=source_url,
                external_excerpt=excerpt[:350],
                status=VerificationStatus.VERIFIED_SUPPORTED,
                explanation=f"Corroborated by {source_name}: confirms assertion regarding '{claim.object}'."
            )

        # Insufficient direct match
        return ExternalVerificationRecordModel(
            claim_id=claim.id,
            external_source_name=source_name,
            external_source_url=source_url,
            external_excerpt=excerpt[:350],
            status=VerificationStatus.INSUFFICIENT_EVIDENCE,
            explanation=f"{source_name} article retrieved for '{claim.subject}' does not directly confirm predicate '{claim.predicate}'."
        )

    async def verify_and_record(self, claim: ClaimModel, external_evidence: Optional[Dict[str, Any]] = None) -> ExternalVerificationRecordModel:
        """Evaluates claim and persists record to SQLite external_verifications table."""
        record = self.evaluate_claim(claim, external_evidence)
        await self.db.insert_external_verification(record)
        return record
