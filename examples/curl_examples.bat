@echo off
REM HoneyChain REST API cURL Examples (Windows)
set BASE_URL=http://127.0.0.1:5000

echo === 1. Network Status ===
curl -s -X GET %BASE_URL%/api/network-info
echo.

echo === 2. Blockchain Integrity Check ===
curl -s -X GET %BASE_URL%/api/verify-chain
echo.

echo === 3. Inspect Blockchain Ledger ===
curl -s -X GET %BASE_URL%/api/chain
echo.

echo === 4. Trace Batch by ID ===
curl -s -X GET %BASE_URL%/api/trace/HC-2026-EXAMPLE1
echo.
pause

