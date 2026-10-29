#!/usr/bin/env bash
# HoneyChain REST API cURL Examples

BASE_URL="http://127.0.0.1:5000"

echo "=== 1. Network Status ==="
curl -s -X GET "$BASE_URL/api/network-info" | python -m json.tool

echo -e "\n=== 2. Blockchain Integrity Check ==="
curl -s -X GET "$BASE_URL/api/verify-chain" | python -m json.tool

echo -e "\n=== 3. Inspect Blockchain Ledger ==="
curl -s -X GET "$BASE_URL/api/chain" | python -m json.tool

echo -e "\n=== 4. Trace Batch by ID (replace HC-XXXX with real ID) ==="
curl -s -X GET "$BASE_URL/api/trace/HC-2026-EXAMPLE1" | python -m json.tool

echo -e "\n=== 5. Export Ledger JSON ==="
curl -s -X GET "$BASE_URL/reports/export/json" -o honeychain_ledger_export.json
echo "Saved to honeychain_ledger_export.json"

