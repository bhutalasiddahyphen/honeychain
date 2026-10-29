# HoneyChain REST API Documentation

HoneyChain provides lightweight JSON REST endpoints for external auditing, mobile scanner integration, and automated consortium reporting.

---

## 1. Get Blockchain Ledger
Retrieves the entire active chain including Block 0 and all mined stage blocks.

* **Endpoint**: `GET /api/chain`
* **Access**: Public / Consortium Clients
* **Response `200 OK`**:
```json
{
  "success": true,
  "length": 1,
  "chain": [
    {
      "index": 0,
      "block_type": "Block 0: Genesis Block",
      "timestamp": "2026-10-28 16:15:00 UTC",
      "previous_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "hash": "004a192ac85d50a401c1932372ff2ed3b984836a65f2412e9162eae38072a051",
      "nonce": 42,
      "data": {
        "event": "GENESIS_BLOCK",
        "lifecycle_stage": "Block 0: Genesis Block",
        "protocol": "HoneyChain-PoW-v2.0"
      }
    }
  ]
}
```

---

## 2. Verify Cryptographic Integrity
Runs automated SHA-256 hash recalculation and Proof-of-Work target verification across all blocks.

* **Endpoint**: `GET /api/verify-chain`
* **Access**: Public / Consortium Clients
* **Response `200 OK`**:
```json
{
  "success": true,
  "is_valid": true,
  "chain_length": 1,
  "message": "Blockchain integrity verified. All cryptographic proofs match 100%."
}
```

---

## 3. Trace Honey Batch
Returns the current database record and all associated blockchain blocks for a given Batch ID.

* **Endpoint**: `GET /api/trace/<batch_id>`
* **Access**: Public / Consumers / Retailers
* **Parameters**: `batch_id` (e.g. `HC-2026-8812`)
* **Response `200 OK`**:
```json
{
  "success": true,
  "batch": {
    "batch_id": "HC-2026-8812",
    "product_name": "Organic Alpine Raw Honey",
    "floral_source": "Wild Alpine Blossom",
    "apiary_name": "Valais Meadow Apiary",
    "beekeeper_name": "Master Beekeeper",
    "current_stage": "Block 2: Laboratory Test Recorded",
    "stage_num": 2,
    "purity_score": 99.8,
    "moisture_content": 16.4
  },
  "blockchain_blocks": [
    {
      "index": 1,
      "block_type": "Block 1: Honey Batch Registered",
      "hash": "007f...",
      "timestamp": "2026-10-28 10:00:00 UTC"
    },
    {
      "index": 2,
      "block_type": "Block 2: Laboratory Test Recorded",
      "hash": "003c...",
      "timestamp": "2026-10-28 14:00:00 UTC"
    }
  ]
}
```
* **Response `404 Not Found`**:
```json
{
  "success": false,
  "error": "Batch 'HC-UNKNOWN' not found"
}
```

---

## 4. Consortium Network Info
Returns local and network IP addresses, active port, and hostname for smartphone Wi-Fi scanning.

* **Endpoint**: `GET /api/network-info`
* **Access**: Public
* **Response `200 OK`**:
```json
{
  "success": true,
  "hostname": "LAPTOP-HOST",
  "lan_ip": "10.31.30.29",
  "local_url": "http://127.0.0.1:5000",
  "network_url": "http://10.31.30.29:5000",
  "port": 5000,
  "status": "online"
}
```

