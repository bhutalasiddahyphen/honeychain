"""
HoneyChain Blockchain Block Model
"""
import json
from datetime import datetime, timezone


class BlockModel:
    """Model wrapper for persistent blockchain blocks."""

    def __init__(self, index, timestamp, data, previous_hash, nonce=0, hash_val="", block_type=""):
        self.index = int(index)
        self.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.data = data if isinstance(data, dict) else (json.loads(data) if data else {})
        self.previous_hash = previous_hash
        self.nonce = int(nonce)
        self.hash = hash_val
        self.block_type = block_type

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "block_type": self.block_type,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            index=row["block_index"],
            timestamp=row["timestamp"],
            data=row["data_json"],
            previous_hash=row["previous_hash"],
            nonce=row["nonce"],
            hash_val=row["hash"],
            block_type=row["block_type"] if "block_type" in row.keys() else "",
        )

