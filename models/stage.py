"""
HoneyChain Stage Update Model
"""
import json
from datetime import datetime, timezone


class StageUpdate:
    """Represents an audit event updating a batch stage in the supply chain."""

    def __init__(self, id=None, batch_id="", stage_num=1, stage_name="", actor_name="", location="", details_json=None, notes="", timestamp=None, block_hash="", block_index=0):
        self.id = id
        self.batch_id = batch_id
        self.stage_num = int(stage_num)
        self.stage_name = stage_name
        self.actor_name = actor_name
        self.location = location
        self.details = details_json if isinstance(details_json, dict) else (json.loads(details_json) if details_json else {})
        self.notes = notes
        self.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.block_hash = block_hash
        self.block_index = int(block_index)

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "stage_num": self.stage_num,
            "stage_name": self.stage_name,
            "actor_name": self.actor_name,
            "location": self.location,
            "details": self.details,
            "notes": self.notes,
            "timestamp": self.timestamp,
            "block_hash": self.block_hash,
            "block_index": self.block_index,
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            batch_id=row["batch_id"],
            stage_num=row["stage_num"],
            stage_name=row["stage_name"],
            actor_name=row["actor_name"],
            location=row["location"],
            details_json=row["details_json"],
            notes=row["notes"],
            timestamp=row["timestamp"],
            block_hash=row["block_hash"],
            block_index=row["block_index"],
        )

