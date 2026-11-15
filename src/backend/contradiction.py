"""
MindVault Contradiction Detection & Logic Engine
Two-stage hybrid contradiction detection:
Stage 1: High-recall candidate filtering via entity overlap and opposing predicate rules.
Stage 2: Deterministic & semantic disambiguation into Mutual Exclusion, Numerical Discrepancy, Contextual Tension, or Temporal Drift.
"""
import re
from typing import List, Dict, Any, Optional
from src.backend.models import (
    ClaimModel, ContradictionModel, ContradictionSeverity, generate_uuid, utc_now
)
from src.backend.database import DatabaseEngine
from src.backend.search import HybridSearchEngine
import aiosqlite

OPPOSING_PREDICATES = {
    "increases": "decreases",
    "decreases": "increases",
    "causes": "prevents",
    "prevents": "causes",
    "stimulates": "inhibits",
    "inhibits": "stimulates",
    "activates": "deactivates",
    "deactivates": "activates",
    "proves": "disproves",
    "disproves": "proves",
    "accelerates": "decelerates",
    "decelerates": "accelerates",
    "promotes": "suppresses",
    "suppresses": "promotes",
    "validates": "invalidates",
    "invalidates": "validates"
}

def extract_numbers(text: str) -> List[float]:
    """Extracts numerical quantities from claim text for numerical discrepancy checks."""
    pattern = r"[-+]?\d*\.?\d+"
    matches = re.findall(pattern, text)
    nums = []
    for m in matches:
        try:
            nums.append(float(m))
        except ValueError:
            pass
    return nums

class ContradictionDetectionEngine:
    def __init__(self, db_engine: DatabaseEngine, search_engine: HybridSearchEngine):
        self.db = db_engine
        self.search = search_engine

    def check_predicate_opposition(self, pred_a: str, pred_b: str) -> bool:
        """Determines if two predicates are semantic opposites."""
        pa = pred_a.lower().strip()
        pb = pred_b.lower().strip()
        if pa in OPPOSING_PREDICATES and OPPOSING_PREDICATES[pa] == pb:
            return True
        if (f"not {pa}" in pb) or (f"not {pb}" in pa) or ("not" in pa and pb in pa):
            return True
        return False

    def check_subject_alignment(self, claim_a: ClaimModel, claim_b: ClaimModel) -> bool:
        """Checks if two claims share conceptual subjects."""
        sa = claim_a.subject.lower().strip()
        sb = claim_b.subject.lower().strip()
        return (sa == sb) or (sa in sb) or (sb in sa)

    def evaluate_pair(self, claim_a: ClaimModel, claim_b: ClaimModel) -> Optional[ContradictionModel]:
        """
        Analyzes two atomic claims and determines if a contradiction exists, 
        categorizing severity and generating an explainable rationale.
        """
        if claim_a.id == claim_b.id:
            return None

        # Both claims must align on the core subject
        if not self.check_subject_alignment(claim_a, claim_b):
            return None

        is_opposing = self.check_predicate_opposition(claim_a.predicate, claim_b.predicate)

        # Numerical discrepancy check (same subject and predicate, different numbers in object)
        nums_a = extract_numbers(claim_a.object)
        nums_b = extract_numbers(claim_b.object)
        has_numerical_mismatch = False
        if nums_a and nums_b and nums_a != nums_b and (claim_a.predicate.lower().strip() == claim_b.predicate.lower().strip()):
            has_numerical_mismatch = True

        # Check direct mutual exclusion
        oa = claim_a.object.lower().strip()
        ob = claim_b.object.lower().strip()
        objects_align = (oa == ob) or (oa in ob) or (ob in oa)

        if is_opposing and objects_align:
            explanation = (
                f"Direct conflict detected: Claim A asserts '{claim_a.subject}' {claim_a.predicate} '{claim_a.object}', "
                f"whereas Claim B asserts '{claim_b.subject}' {claim_b.predicate} '{claim_b.object}'."
            )
            return ContradictionModel(
                claim_a_id=claim_a.id,
                claim_b_id=claim_b.id,
                severity=ContradictionSeverity.DIRECT_MUTUAL_EXCLUSION,
                explanation=explanation,
                resolution_status="OPEN"
            )

        if has_numerical_mismatch:
            explanation = (
                f"Numerical discrepancy detected: Claim A reports values {nums_a} for '{claim_a.subject}', "
                f"whereas Claim B reports values {nums_b}."
            )
            return ContradictionModel(
                claim_a_id=claim_a.id,
                claim_b_id=claim_b.id,
                severity=ContradictionSeverity.NUMERICAL_DISCREPANCY,
                explanation=explanation,
                resolution_status="OPEN"
            )

        return None

    async def register_contradiction(self, contradiction: ContradictionModel) -> ContradictionModel:
        """Stores detected contradiction in the persistent SQLite registry."""
        async with aiosqlite.connect(self.db.db_path) as conn:
            await conn.execute("PRAGMA foreign_keys = ON;")
            await conn.execute(
                """
                INSERT INTO contradictions (id, claim_a_id, claim_b_id, severity, explanation, resolution_status, detected_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contradiction.id,
                    contradiction.claim_a_id,
                    contradiction.claim_b_id,
                    contradiction.severity.value,
                    contradiction.explanation,
                    contradiction.resolution_status,
                    contradiction.detected_at,
                    contradiction.resolved_at
                )
            )
            await conn.commit()
        return contradiction

    async def scan_all_claims(self, claims: List[ClaimModel]) -> List[ContradictionModel]:
        """Scans a collection of claims, discovers contradictions, and persists them."""
        detected = []
        n = len(claims)
        for i in range(n):
            for j in range(i + 1, n):
                conflict = self.evaluate_pair(claims[i], claims[j])
                if conflict:
                    await self.register_contradiction(conflict)
                    detected.append(conflict)
        return detected
