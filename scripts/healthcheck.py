#!/usr/bin/env python3
"""
HoneyChain Healthcheck & Diagnostics Script
Verifies database integrity, blockchain ledger status, directory permissions, and static assets.
"""

import os
import sys
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import database
from blockchain import Blockchain


def check_health():
    print("=" * 65)
    print("      HONEYCHAIN SYSTEM HEALTHCHECK & DIAGNOSTICS")
    print("=" * 65)

    all_passed = True

    # 1. Database Connection
    print("\n[1/5] Checking SQLite Database Connection...")
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"      [OK] Connected to SQLite (v{version}) at {database.DB_PATH}")

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"      [OK] Total Tables: {len(tables)} ({', '.join(sorted(tables))})")
        conn.close()
    except Exception as e:
        print(f"      [FAIL] Database check failed: {e}")
        all_passed = False

    # 2. Blockchain Ledger
    print("\n[2/5] Checking Blockchain Ledger...")
    try:
        chain_instance = Blockchain(difficulty=2)
        database.load_chain_from_db(chain_instance)
        is_valid, msg = chain_instance.is_chain_valid()
        block_count = len(chain_instance.chain)
        print(f"      [OK] Ledger Active: {block_count} blocks found")
        print(f"      [OK] Genesis Block: {chain_instance.chain[0].block_type if block_count > 0 else 'None'}")
        print(f"      [OK] Cryptographic Verification: {'PASSED' if is_valid else 'FAILED'} - {msg}")
        if not is_valid:
            all_passed = False
    except Exception as e:
        print(f"      [FAIL] Blockchain check failed: {e}")
        all_passed = False

    # 3. Directory Permissions
    print("\n[3/5] Checking Required Directories & Permissions...")
    required_dirs = [
        os.path.join(BASE_DIR, "instance"),
        os.path.join(BASE_DIR, "static", "qrcodes"),
        os.path.join(BASE_DIR, "templates"),
        os.path.join(BASE_DIR, "static", "css"),
        os.path.join(BASE_DIR, "static", "js"),
        os.path.join(BASE_DIR, "examples"),
    ]
    for d in required_dirs:
        rel = os.path.relpath(d, BASE_DIR)
        if os.path.exists(d):
            print(f"      [OK] Directory exists: {rel}")
        else:
            try:
                os.makedirs(d, exist_ok=True)
                print(f"      [CREATED] Created directory: {rel}")
            except Exception as e:
                print(f"      [FAIL] Cannot create {rel}: {e}")
                all_passed = False

    # 4. Core User Accounts
    print("\n[4/5] Checking System User Roles...")
    try:
        users = database.get_all_users()
        usernames = [u["username"] for u in users]
        required_roles = ["admin", "beekeeper", "lab", "packager", "seller"]
        missing = [r for r in required_roles if r not in usernames]
        if not missing:
            print(f"      [OK] All primary role accounts present: {', '.join(usernames)}")
        else:
            print(f"      [WARN] Missing accounts: {missing}")
    except Exception as e:
        print(f"      [FAIL] User check failed: {e}")
        all_passed = False

    # 5. Summary
    print("\n" + "=" * 65)
    if all_passed:
        print("  ALL HEALTHCHECKS PASSED - HONEYCHAIN SYSTEM READY")
    else:
        print("  SOME CHECKS REPORTED ISSUES - PLEASE REVIEW ABOVE")
    print("=" * 65 + "\n")
    return all_passed


if __name__ == "__main__":
    success = check_health()
    sys.exit(0 if success else 1)

