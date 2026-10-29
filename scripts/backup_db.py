#!/usr/bin/env python3
"""
HoneyChain Database Backup Utility
Creates a timestamped snapshot of instance/honeychain.db in the instance/backups directory.
"""

import os
import shutil
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "instance", "honeychain.db")
BACKUP_DIR = os.path.join(BASE_DIR, "instance", "backups")


def create_backup():
    if not os.path.exists(DB_PATH):
        print(f"[!] Database file not found at {DB_PATH}")
        return None

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"honeychain_backup_{timestamp}.db")

    shutil.copy2(DB_PATH, backup_file)
    size_kb = os.path.getsize(backup_file) / 1024
    print(f"[OK] Database backed up successfully:")
    print(f"     Path: {backup_file}")
    print(f"     Size: {size_kb:.2f} KB")
    return backup_file


if __name__ == "__main__":
    create_backup()

