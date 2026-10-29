#!/usr/bin/env python3
"""
HoneyChain API Example Client
Demonstrates programmatically verifying blockchain integrity and tracing honey batches.
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:5000"


def fetch_json(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "HoneyChain-ExampleClient/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"[!] Error contacting {url}: {e}")
        return None


def main():
    print("=" * 65)
    print("  HoneyChain Blockchain REST API Inspection Example")
    print("=" * 65)

    # 1. Network Info
    print("\n[1] Fetching Consortium Network Status...")
    net_info = fetch_json("/api/network-info")
    if net_info:
        print(f"    * Hostname:    {net_info.get('hostname')}")
        print(f"    * Status:      {net_info.get('status')}")
        print(f"    * Local URL:   {net_info.get('local_url')}")
        print(f"    * Network URL: {net_info.get('network_url')}")

    # 2. Blockchain Integrity
    print("\n[2] Cryptographic Ledger Integrity Verification...")
    verify_info = fetch_json("/api/verify-chain")
    if verify_info:
        is_valid = verify_info.get("is_valid")
        status_txt = "VALID (CRYPTOGRAPHICALLY SOUND)" if is_valid else "TAMPER DETECTED"
        print(f"    * Chain Status:  {status_txt}")
        print(f"    * Total Blocks:  {verify_info.get('chain_length')}")
        print(f"    * Audit Message: {verify_info.get('message')}")

    # 3. Blockchain Blocks
    print("\n[3] Inspecting Blockchain Ledger (Blocks 0..N)...")
    chain_info = fetch_json("/api/chain")
    if chain_info and chain_info.get("chain"):
        blocks = chain_info.get("chain")
        print(f"    Found {len(blocks)} blocks on ledger:")
        for b in blocks:
            print(f"      - Block #{b['index']} [{b['block_type']}]")
            print(f"        Hash:     {b['hash'][:24]}...")
            print(f"        PrevHash: {b['previous_hash'][:24]}...")
            print(f"        Nonce:    {b['nonce']} | Timestamp: {b['timestamp']}")

    print("\n" + "=" * 65)
    print("  Inspection Complete.")
    print("=" * 65)


if __name__ == "__main__":
    main()

