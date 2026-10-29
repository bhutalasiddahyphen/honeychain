#!/usr/bin/env python3
"""
HoneyChain 5-Stage Supply Chain Pipeline Example
Demonstrates programmatically executing all 5 provenance lifecycle stages:
  Block 0: Genesis Block
  Block 1: Honey Batch Registered (Apiary Harvest)
  Block 2: Laboratory Test Recorded (Quality & Purity Assay)
  Block 3: Honey Packaging Recorded (Bottling & Tamper Seal)
  Block 4: Seller Information Recorded (Retail Shelf Authentication)
"""

import os
import sys
from datetime import datetime, timezone

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from blockchain import Blockchain
import database


def run_pipeline_example():
    print("=" * 70)
    print("   HONEYCHAIN 5-STAGE BLOCKCHAIN SUPPLY CHAIN PIPELINE DEMO")
    print("=" * 70)

    # 1. Initialize Blockchain
    ledger = Blockchain(difficulty=2)
    genesis = ledger.create_genesis_block()
    print(f"\n[Block 0] Genesis Block Created:")
    print(f"  * Hash:      {genesis.hash}")
    print(f"  * Nonce:     {genesis.nonce}")
    print(f"  * Message:   {genesis.data.get('message')}")

    # 2. Block 1: Apiary Harvest Registration
    batch_id = "HC-EX-2026-001"
    b1_data = {
        "event": "HONEY_BATCH_REGISTERED",
        "lifecycle_stage": "Block 1: Honey Batch Registered",
        "batch_id": batch_id,
        "product_name": "Organic Alpine Raw Honey",
        "floral_source": "Wild Alpine Flora & Rhododendron",
        "apiary_name": "Alpine Crest Apiary",
        "beekeeper_name": "Hans Gruber",
        "origin_location": "Swiss Alps, Elevation 1,500m",
        "harvest_date": "2026-10-28",
        "comb_type": "Pure Capped Organic Comb",
        "extraction_method": "Unheated Cold Centrifugation",
        "quantity_kg": 250.0
    }
    b1 = ledger.add_block(b1_data, block_type="Block 1: Honey Batch Registered")
    print(f"\n[Block 1] Apiary Harvest Minted:")
    print(f"  * Batch ID:  {batch_id}")
    print(f"  * Hash:      {b1.hash}")
    print(f"  * PrevHash:  {b1.previous_hash}")
    print(f"  * Nonce:     {b1.nonce}")

    # 3. Block 2: Laboratory Test Recorded
    b2_data = {
        "event": "LAB_TEST_RECORDED",
        "lifecycle_stage": "Block 2: Laboratory Test Recorded",
        "batch_id": batch_id,
        "lab_name": "Swiss Food Safety Laboratory",
        "inspector_name": "Dr. Beatrice Keller",
        "certificate_no": "CH-FOOD-CERT-2026-9901",
        "purity_score": 99.8,
        "moisture_content": 16.2,
        "nmr_profile": "100% Pure Floral Nectar - No Exogenous Sugars",
        "hmf_level": 3.8,
        "lab_test_date": "2026-10-29",
        "digital_signature": "SIG-SHA256:77F1AA9082C09BE"
    }
    b2 = ledger.add_block(b2_data, block_type="Block 2: Laboratory Test Recorded")
    print(f"\n[Block 2] Laboratory Test Minted:")
    print(f"  * Lab:       {b2_data['lab_name']} ({b2_data['purity_score']}% Pure)")
    print(f"  * Hash:      {b2.hash}")
    print(f"  * PrevHash:  {b2.previous_hash}")
    print(f"  * Nonce:     {b2.nonce}")

    # 4. Block 3: Honey Packaging Recorded
    b3_data = {
        "event": "PACKAGING_RECORDED",
        "lifecycle_stage": "Block 3: Honey Packaging Recorded",
        "batch_id": batch_id,
        "packaging_plant": "Helvetia Artisan Bottlers Ltd.",
        "packaging_supervisor": "Lukas Meier",
        "jar_format": "500g Hexagonal Embossed Glass Jar",
        "net_weight": "500g (± 2g)",
        "tamper_seal_id": "SEAL-CH-2026-001",
        "lot_number": "LOT-2026-CH-01",
        "packaging_date": "2026-10-30"
    }
    b3 = ledger.add_block(b3_data, block_type="Block 3: Honey Packaging Recorded")
    print(f"\n[Block 3] Bottling & Tamper Seal Minted:")
    print(f"  * Plant:     {b3_data['packaging_plant']} (Seal: {b3_data['tamper_seal_id']})")
    print(f"  * Hash:      {b3.hash}")
    print(f"  * PrevHash:  {b3.previous_hash}")
    print(f"  * Nonce:     {b3.nonce}")

    # 5. Block 4: Seller Recorded
    b4_data = {
        "event": "SELLER_RECORDED",
        "lifecycle_stage": "Block 4: Seller Information Recorded",
        "batch_id": batch_id,
        "seller_name": "AlpenGourmet Flagship Boutique",
        "store_location": "Bahnhofstrasse 42, Zurich",
        "license_no": "ZH-FOOD-88120",
        "shelf_arrival_date": "2026-11-01",
        "sale_price": "CHF 48.00",
        "retail_status": "On Shelf & Authenticated"
    }
    b4 = ledger.add_block(b4_data, block_type="Block 4: Seller Information Recorded")
    print(f"\n[Block 4] Retail Arrival Minted:")
    print(f"  * Retailer:  {b4_data['seller_name']} at {b4_data['store_location']}")
    print(f"  * Hash:      {b4.hash}")
    print(f"  * PrevHash:  {b4.previous_hash}")
    print(f"  * Nonce:     {b4.nonce}")

    # 6. Verify Ledger Integrity
    print("\n" + "-" * 70)
    print("[Verification] Checking cryptographic chain validity...")
    is_valid, msg = ledger.is_chain_valid()
    print(f"  * Chain Valid: {is_valid}")
    print(f"  * Status:      {msg}")
    print(f"  * Length:      {len(ledger.chain)} blocks")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline_example()

