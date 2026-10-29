"""
HoneyChain Blockchain Unit Tests
"""
import pytest
from blockchain import Blockchain, Block


def test_genesis_block():
    bc = Blockchain(difficulty=2)
    genesis = bc.create_genesis_block()
    assert genesis.index == 0
    assert genesis.previous_hash == "0" * 64
    assert genesis.hash.startswith("00")


def test_proof_of_work_mining():
    block = Block(
        index=1,
        timestamp="2026-10-29 12:00:00 UTC",
        data={"event": "TEST_EVENT", "batch_id": "HC-TEST-001"},
        previous_hash="0" * 64
    )
    block.mine_block(difficulty=2)
    assert block.hash.startswith("00")
    assert block.nonce >= 0


def test_blockchain_linkage_and_integrity():
    bc = Blockchain(difficulty=2)
    genesis = bc.create_genesis_block()
    bc.chain.append(genesis)

    b1 = bc.add_block({"event": "HONEY_BATCH_REGISTERED", "batch_id": "HC-001"}, block_type="Block 1")
    assert b1.index == 1
    assert b1.previous_hash == genesis.hash
    assert b1.hash.startswith("00")

    b2 = bc.add_block({"event": "LAB_TEST_RECORDED", "batch_id": "HC-001"}, block_type="Block 2")
    assert b2.index == 2
    assert b2.previous_hash == b1.hash

    is_valid, msg = bc.is_chain_valid()
    assert is_valid is True


def test_tamper_detection():
    bc = Blockchain(difficulty=2)
    genesis = bc.create_genesis_block()
    bc.chain.append(genesis)
    b1 = bc.add_block({"event": "ORIGIN", "amount": 100}, block_type="Block 1")

    # Deliberate tampering: mutate data without recalculating hash
    b1.data["amount"] = 999999

    is_valid, msg = bc.is_chain_valid()
    assert is_valid is False
    assert "tampered" in msg.lower() or "invalid" in msg.lower()

