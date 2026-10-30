import hashlib
import json
from datetime import datetime, timezone


class Block:
    """
    Represents an immutable block in the HoneyChain blockchain.
    Conforms to the 5-block lifecycle architecture:
    - Block 0: Genesis Block
    - Block 1: Honey Batch Registered
    - Block 2: Laboratory Test Recorded
    - Block 3: Honey Packaging Recorded
    - Block 4: Seller Information Recorded
    """
    def __init__(self, index, timestamp, data, previous_hash, nonce=0, hash_val=None, block_type=None):
        self.index = index
        self.timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.block_type = block_type or self.infer_block_type(data, index)
        self.hash = hash_val or self.calculate_hash()

    @staticmethod
    def infer_block_type(data, index):
        if index == 0:
            return "Block 0: Genesis Block"
        event = data.get("event", "") if isinstance(data, dict) else ""
        if "BATCH" in event or "HARVEST" in event:
            return "Block 1: Honey Batch Registered"
        elif "LAB" in event or "TEST" in event:
            return "Block 2: Laboratory Test Recorded"
        elif "PACKAG" in event or "BOTTL" in event:
            return "Block 3: Honey Packaging Recorded"
        elif "SELLER" in event or "RETAIL" in event:
            return "Block 4: Seller Information Recorded"
        return f"Block {index}: Provenance Update"

    def calculate_hash(self):
        """
        Calculates SHA-256 cryptographic hash of block data.
        """
        payload = (
            str(self.index)
            + str(self.timestamp)
            + str(self.block_type)
            + json.dumps(self.data, sort_keys=True)
            + str(self.previous_hash)
            + str(self.nonce)
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def mine_block(self, difficulty=2):
        """
        Proof of Work mining: Increments nonce until hash meets difficulty target.
        """
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

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
    def from_dict(cls, d):
        return cls(
            index=d["index"],
            timestamp=d["timestamp"],
            data=d["data"],
            previous_hash=d["previous_hash"],
            nonce=d.get("nonce", 0),
            hash_val=d.get("hash"),
            block_type=d.get("block_type"),
        )


class Blockchain:
    """
    Decentralized HoneyChain Ledger implementing the 5-block lifecycle.
    """
    def __init__(self, difficulty=2):
        self.difficulty = difficulty
        self.chain = []

    def create_genesis_block(self):
        """
        Creates Block 0: Genesis Block.
        """
        genesis_data = {
            "event": "GENESIS_BLOCK",
            "lifecycle_stage": "Block 0: Genesis Block",
            "message": "HoneyChain Ledger Initialized - Immutable Provenance Network Active",
            "protocol": "HoneyChain-PoW-v2.0",
            "consortium": "International Pure Honey & Bee Protection Consortium",
        }
        genesis_block = Block(
            index=0,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            data=genesis_data,
            previous_hash="0" * 64,
            nonce=0,
            block_type="Block 0: Genesis Block",
        )
        genesis_block.mine_block(self.difficulty)
        return genesis_block

    def get_latest_block(self):
        if not self.chain:
            return None
        return self.chain[-1]

    def add_block(self, data, block_type=None):
        """
        Mines and links a new block into the chain.
        """
        if not self.chain:
            self.chain.append(self.create_genesis_block())

        latest_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            data=data,
            previous_hash=latest_block.hash,
            block_type=block_type,
        )
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        """
        Validates SHA-256 cryptographic signatures and block linkage.
        """
        if not self.chain:
            return True, "Chain is empty"

        genesis = self.chain[0]
        if genesis.hash != genesis.calculate_hash():
            return False, "Genesis Block 0 hash is invalid or tampered"

        target = "0" * self.difficulty

        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.calculate_hash():
                return False, f"Block #{current.index} ({current.block_type}) hash mismatch! Data tampered."

            if current.previous_hash != previous.hash:
                return False, f"Block #{current.index} previous_hash does not match Block #{previous.index} hash!"

            if not current.hash.startswith(target):
                return False, f"Block #{current.index} does not satisfy difficulty requirement ({self.difficulty} zeros)."

        return True, "Blockchain integrity verified. All cryptographic proofs match 100%."

    def get_batch_history(self, batch_id):
        """
        Retrieves all lifecycle blocks belonging to a given Honey Batch ID.
        """
        history = []
        for block in self.chain:
            if isinstance(block.data, dict) and block.data.get("batch_id") == batch_id:
                history.append(block)
        return history

    def audit_database_blocks(self):
        """
        Audits blocks directly from database rows to detect offline database tampering.
        """
        import database
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blockchain_blocks ORDER BY block_index ASC")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return True, "No blocks in database", []

        tampered_blocks = []
        previous_hash = "0" * 64

        for row in rows:
            idx = row["block_index"]
            stored_hash = row["hash"]
            stored_prev = row["previous_hash"]
            data = json.loads(row["data_json"])
            b_type = row["block_type"]
            nonce = row["nonce"]
            timestamp = row["timestamp"]

            # Re-calculate hash using exactly identical payload logic
            block_obj = Block(idx, timestamp, data, stored_prev, nonce, None, b_type)
            calculated_hash = block_obj.calculate_hash()

            if stored_hash != calculated_hash:
                tampered_blocks.append({
                    "index": idx,
                    "type": b_type,
                    "reason": f"Hash mismatch: stored '{stored_hash[:16]}...' != computed '{calculated_hash[:16]}...'"
                })
            elif idx > 0 and stored_prev != previous_hash:
                tampered_blocks.append({
                    "index": idx,
                    "type": b_type,
                    "reason": f"Chain broken: previous_hash does not point to block #{idx-1}"
                })
            previous_hash = stored_hash

        if tampered_blocks:
            return False, f"CRITICAL: {len(tampered_blocks)} tampered block(s) detected in database!", tampered_blocks
        return True, "All blockchain records cryptographically authentic & untampered.", []
