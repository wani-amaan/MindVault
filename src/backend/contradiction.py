"""
MindVault Contradiction Detection & Logic Engine
Multi-stage hybrid contradiction detection:
Stage 1: High-recall candidate filtering via subject alignment & predicate analysis.
Stage 2: Temporal & Contextual Filter (prevents false positives from date shifts or scope divergence).
Stage 3: Numerical Discrepancy Gate (compares values when temporal and contextual scopes overlap).
Stage 4: Direct Mutual Exclusion & Negation Gate (antonyms, explicit negations).
Stage 5: Persistent SQLite conflict registry.
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
    "invalidates": "validates",
    "expanded": "contracted",
    "contracted": "expanded",
    "rose": "fell",
    "fell": "rose",
    "grew": "shrank",
    "shrank": "grew",
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
        """Determines if two predicates are semantic opposites or negated."""
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

    def check_temporal_divergence(self, claim_a: ClaimModel, claim_b: ClaimModel) -> bool:
        """
        Determines if claims explicitly refer to different temporal scopes.
        If dates differ (e.g. 2022 vs 2024), it is temporal evolution, not a logical contradiction.
        """
        t_a = (claim_a.temporal_scope or "").strip().lower()
        t_b = (claim_b.temporal_scope or "").strip().lower()
        if t_a and t_b and t_a != t_b:
            return True
        return False

    def evaluate_pair(self, claim_a: ClaimModel, claim_b: ClaimModel) -> Optional[ContradictionModel]:
        """
        Analyzes two atomic claims using a multi-stage epistemic filter:
        1. Subject Alignment
        2. Temporal Evolution Gate (prevents date-shift false positives)
        3. Numerical Discrepancy Gate
        4. Direct Mutual Exclusion & Polarity Gate
        """
        if claim_a.id == claim_b.id:
            return None

        # Stage 1: Both claims must align on the core subject
        if not self.check_subject_alignment(claim_a, claim_b):
            return None

        # Stage 2: Temporal Evolution Filter
        # If both claims specify different years or dates, classify as temporal evolution rather than conflict
        if self.check_temporal_divergence(claim_a, claim_b):
            return ContradictionModel(
                claim_a_id=claim_a.id,
                claim_b_id=claim_b.id,
                severity=ContradictionSeverity.TEMPORAL_EVOLUTION,
                explanation=(
                    f"Temporal divergence observed: Claim A references '{claim_a.temporal_scope}' "
                    f"while Claim B references '{claim_b.temporal_scope}'. This represents factual evolution, not direct conflict."
                ),
                resolution_status="RESOLVED_TEMPORAL"
            )

        # Stage 3: Numerical Discrepancy check (same subject and predicate, different numbers in object)
        nums_a = extract_numbers(claim_a.object)
        nums_b = extract_numbers(claim_b.object)
        has_numerical_mismatch = False
        if nums_a and nums_b and nums_a != nums_b and (claim_a.predicate.lower().strip() == claim_b.predicate.lower().strip()):
            has_numerical_mismatch = True

        # Stage 4: Check direct mutual exclusion and negation flags
        is_opposing = self.check_predicate_opposition(claim_a.predicate, claim_b.predicate)
        negation_clash = (claim_a.is_negated != claim_b.is_negated) and (claim_a.predicate.lower().strip() == claim_b.predicate.lower().strip())

        oa = claim_a.object.lower().strip()
        ob = claim_b.object.lower().strip()
        objects_align = (oa == ob) or (oa in ob) or (ob in oa)

        if (is_opposing or negation_clash) and objects_align:
            explanation = (
                f"Direct conflict detected: Claim A asserts '{claim_a.subject}' {claim_a.predicate} '{claim_a.object}' "
                f"(negated={claim_a.is_negated}), whereas Claim B asserts '{claim_b.subject}' {claim_b.predicate} '{claim_b.object}' "
                f"(negated={claim_b.is_negated})."
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
                f"whereas Claim B reports values {nums_b} within the same temporal window."
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
                INSERT OR REPLACE INTO contradictions (id, claim_a_id, claim_b_id, severity, explanation, resolution_status, detected_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contradiction.id,
                    contradiction.claim_a_id,
                    contradiction.claim_b_id,
                    contradiction.severity.value if hasattr(contradiction.severity, "value") else str(contradiction.severity),
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

    async def get_active_contradictions(self) -> List[Dict[str, Any]]:
        """Retrieves all open contradictions persisted in the database with claim details."""
        async with aiosqlite.connect(self.db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                """
                SELECT c.id, c.claim_a_id, c.claim_b_id, c.severity, c.explanation, c.resolution_status, c.detected_at,
                       ca.subject as subj_a, ca.predicate as pred_a, ca.object as obj_a,
                       cb.subject as subj_b, cb.predicate as pred_b, cb.object as obj_b
                FROM contradictions c
                JOIN claims ca ON c.claim_a_id = ca.id
                JOIN claims cb ON c.claim_b_id = cb.id
                WHERE c.resolution_status = 'OPEN'
                ORDER BY c.detected_at DESC
                """
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
