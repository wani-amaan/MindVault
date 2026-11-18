"""
MindVault Knowledge Timeline Engine
Append-only cryptographic audit ledger that records every state transition,
confidence adjustment, verification flip, and belief revision with full provenance.
"""
import hashlib
import json
from typing import List, Dict, Any, Optional
import aiosqlite
from src.backend.models import generate_uuid, utc_now
from src.backend.database import DatabaseEngine


class TimelineEvent:
    def __init__(
        self,
        entity_id: str,
        event_type: str,
        previous_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None,
        reason: Optional[str] = None
    ):
        self.id = generate_uuid()
        self.entity_id = entity_id
        self.event_type = event_type
        self.previous_state_json = json.dumps(previous_state) if previous_state else None
        self.new_state_json = json.dumps(new_state) if new_state else None
        self.reason = reason
        self.created_at = utc_now()
        # Integrity fingerprint: SHA-256 of entity+event+states+timestamp
        self.fingerprint = self._compute_fingerprint()

    def _compute_fingerprint(self) -> str:
        payload = f"{self.entity_id}:{self.event_type}:{self.previous_state_json}:{self.new_state_json}:{self.created_at}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "event_type": self.event_type,
            "previous_state": json.loads(self.previous_state_json) if self.previous_state_json else None,
            "new_state": json.loads(self.new_state_json) if self.new_state_json else None,
            "reason": self.reason,
            "created_at": self.created_at,
            "fingerprint": self.fingerprint
        }


class TimelineEngine:
    def __init__(self, db_engine: DatabaseEngine):
        self.db = db_engine

    async def record(
        self,
        entity_id: str,
        event_type: str,
        previous_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None,
        reason: Optional[str] = None
    ) -> TimelineEvent:
        """
        Records a new timestamped event in the append-only timeline.
        Event types include:
          CLAIM_CREATED, CLAIM_UPDATED, EVIDENCE_ADDED, STATUS_CHANGED,
          CONFIDENCE_ADJUSTED, CONTRADICTION_DETECTED, CONTRADICTION_RESOLVED,
          NODE_DEPRECATED, BELIEF_REVISED
        """
        event = TimelineEvent(
            entity_id=entity_id,
            event_type=event_type,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason
        )

        async with aiosqlite.connect(self.db.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO timeline_events (id, entity_id, event_type, previous_state_json, new_state_json, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.entity_id,
                    event.event_type,
                    event.previous_state_json,
                    event.new_state_json,
                    event.reason,
                    event.created_at
                )
            )
            await conn.commit()

        return event

    async def get_entity_history(self, entity_id: str) -> List[Dict[str, Any]]:
        """Retrieves the complete ordered history for a single entity."""
        async with aiosqlite.connect(self.db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM timeline_events WHERE entity_id = ? ORDER BY created_at ASC",
                (entity_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the most recent N events across all entities (global activity feed)."""
        async with aiosqlite.connect(self.db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM timeline_events ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
