"""
HoneyChain Blockchain Service
"""
import json
from datetime import datetime, timezone
import database
from blockchain import Blockchain, Block


class BlockchainService:
    """Handles blockchain operations, proof-of-work mining, and ledger auditing."""

    def __init__(self, blockchain_instance=None):
        if blockchain_instance is None:
            self.blockchain = Blockchain(difficulty=2)
            database.load_chain_from_db(self.blockchain)
        else:
            self.blockchain = blockchain_instance

    def get_chain(self):
        """Returns the full in-memory blockchain list."""
        return self.blockchain.chain

    def get_block_by_index(self, index):
        """Fetches block by its sequence index."""
        for block in self.blockchain.chain:
            if block.index == index:
                return block
        return None

    def add_batch_block(self, batch_id, stage_name, event_type, details):
        """
        Mines and commits a new block for a batch stage transition.
        """
        payload = {
            "event": event_type,
            "lifecycle_stage": stage_name,
            "batch_id": batch_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            **details,
        }
        new_block = self.blockchain.add_block(payload, block_type=stage_name)
        database.save_block_to_db(new_block)
        return new_block

    def verify_ledger_integrity(self):
        """
        Audits cryptographic hash continuity and proof-of-work across all blocks.
        Returns (is_valid: bool, issues: list).
        """
        return self.blockchain.is_chain_valid()

    def get_summary_stats(self):
        """Returns statistics for dashboard cards."""
        chain = self.blockchain.chain
        is_valid, _ = self.verify_ledger_integrity()
        return {
            "total_blocks": len(chain),
            "latest_block_index": chain[-1].index if chain else 0,
            "latest_hash": chain[-1].hash if chain else "0" * 64,
            "difficulty": self.blockchain.difficulty,
            "is_valid": is_valid,
        }

