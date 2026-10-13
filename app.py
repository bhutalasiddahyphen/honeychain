import os
import random
import json
import sys
import hmac
import hashlib
import socket
import io
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
import qrcode

from blockchain import Blockchain
import database
import pdf_generator

# Windows console encoding safeguard
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Initialize Flask App
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "honeychain-cryptographic-secret-key-super-secure")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
if os.environ.get("FLASK_ENV") == "production" or os.environ.get("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QR_DIR = os.path.join(BASE_DIR, "static", "qrcodes")
os.makedirs(QR_DIR, exist_ok=True)

# Initialize Database and Blockchain
database.init_db()
honey_blockchain = Blockchain(difficulty=2)
database.load_chain_from_db(honey_blockchain)

# Phase 1: Role-Based User Personas & Metadata
ROLES_METADATA = {
    "admin": {
        "title": "Consortium Chief Auditor",
        "badge": "ADMIN AUDITOR",
        "icon": "fa-user-shield",
        "color": "#f43f5e",
        "desc": "Full Consortium oversight: partner approvals, tamper simulator & dispute resolution."
    },
    "beekeeper": {
        "title": "Master Beekeeper / Apiary",
        "badge": "APIARY PRODUCER",
        "icon": "fa-seedling",
        "color": "#f59e0b",
        "desc": "Harvest origin registration (Block 1) and comb extraction telemetry."
    },
    "lab": {
        "title": "Testing Laboratory Inspector",
        "badge": "LAB ANALYST",
        "icon": "fa-flask-vial",
        "color": "#10b981",
        "desc": "Chemical purity assays, NMR verification & digital signature signing (Block 2)."
    },
    "packager": {
        "title": "Certified Bottling Facility",
        "badge": "BOTTLING FACILITY",
        "icon": "fa-box-open",
        "color": "#3b82f6",
        "desc": "Clean room packaging, jar format & tamper-evident holographic seal (Block 3)."
    },
    "seller": {
        "title": "Authorized Retailer / Seller",
        "badge": "AUTHORIZED RETAILER",
        "icon": "fa-store",
        "color": "#8b5cf6",
        "desc": "Store inventory intake, retail shelf verification & pricing (Block 4)."
    },
    "consumer": {
        "title": "Public Consumer / Shopper",
        "badge": "PUBLIC CONSUMER",
        "icon": "fa-user-check",
        "color": "#06b6d4",
        "desc": "100% cryptographic jar trace, PDF certificate download & authenticity feedback."
    }
}

# Lifecycle stages mapping
STAGE_CONFIG = {
    1: {
        "title": "Block 1: Honey Batch Registered",
        "short_title": "Block 1: Batch Registered",
        "event": "HONEY_BATCH_REGISTERED",
        "actor_role": "Apiary / Master Beekeeper",
        "icon": "fa-seedling",
        "color": "#f59e0b"
    },
    2: {
        "title": "Block 2: Laboratory Test Recorded",
        "short_title": "Block 2: Lab Test",
        "event": "LAB_TEST_RECORDED",
        "actor_role": "Accredited Testing Laboratory",
        "icon": "fa-flask-vial",
        "color": "#10b981"
    },
    3: {
        "title": "Block 3: Honey Packaging Recorded",
        "short_title": "Block 3: Packaging",
        "event": "PACKAGING_RECORDED",
        "actor_role": "Certified Packaging Facility",
        "icon": "fa-box-open",
        "color": "#3b82f6"
    },
    4: {
        "title": "Block 4: Seller Information Recorded",
        "short_title": "Block 4: Seller Info",
        "event": "SELLER_RECORDED",
        "actor_role": "Authorized Retailer / Seller",
        "icon": "fa-store",
        "color": "#8b5cf6"
    }
}


def get_local_ip():
    """
    Returns the primary LAN/Wi-Fi IPv4 address of this host.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def get_public_base_url():
    """
    Returns the permanent public base URL for production QR codes and external links.
    1. PUBLIC_BASE_URL or BASE_URL env variable (e.g., https://honeychain.onrender.com)
    2. Reverse proxy public scheme/host if forwarded (Render/Railway HTTPS)
    3. Machine's LAN IP for local testing (http://10.40.247.29:5000)
    4. http://127.0.0.1:port
    """
    env_url = (os.environ.get("PUBLIC_BASE_URL") or os.environ.get("BASE_URL") or "").strip().rstrip("/")
    if env_url:
        return env_url

    try:
        from flask import has_request_context, request
        if has_request_context() and request:
            proto = request.headers.get("X-Forwarded-Proto", request.scheme)
            host = request.host
            if host and not host.startswith("127.0.0.1") and not host.startswith("localhost"):
                return f"{proto}://{host}"
    except Exception:
        pass

    port = int(os.environ.get("PORT", 5000))
    lan_ip = get_local_ip()
    return f"http://{lan_ip}:{port}"


def get_current_role():
    """Helper to return current active session role (default admin)."""
    role = session.get("user_role") or "admin"
    if role not in ROLES_METADATA:
        role = "admin"
    return role


def generate_lab_digital_signature(batch_id, cert_no, purity, moisture, hmf, secret="EUROFINS_CONSORTIUM_RSA_KEY_2026"):
    """
    Phase 3: Cryptographically signs a laboratory report using HMAC-SHA256.
    """
    payload = f"{batch_id}|{cert_no}|{purity}|{moisture}|{hmf}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"SIG-SHA256:{sig[:28].upper()}"


def generate_qr(batch_id, base_url=None):
    """
    Generates high-resolution consumer QR code pointing to batch trace page.
    Automatically resolves to the production public website URL (never localhost in prod)
    so smartphones scanning the QR code can open the trace page from anywhere.
    """
    if not base_url or "127.0.0.1" in base_url or "localhost" in base_url:
        base_url = get_public_base_url()

    trace_url = f"{base_url.rstrip('/')}/?tab=trace&batch_id={batch_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(trace_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    
    file_name = f"{batch_id}.png"
    file_path = os.path.join(QR_DIR, file_name)
    img.save(file_path)
    return file_name


def seed_sample_data_if_needed(force=False):
    """
    Seeds initial realistic batches demonstrating the 5-block lifecycle.
    If force=True, clears and rebuilds the 5 pristine baseline examples.
    """
    if not force and database.get_all_batches():
        return

    if force:
        database.clear_all_data()
        honey_blockchain.chain = []
        genesis = honey_blockchain.create_genesis_block()
        honey_blockchain.chain = [genesis]
        database.save_block_to_db(genesis)

    sample_batches = [
        # Batch 1: Completed all 4 Blocks (Block 0 -> 1 -> 2 -> 3 -> 4)
        {
            "batch_id": "HC-2026-9842",
            "product_name": "Organic Alpine Blossom Raw Honey",
            "floral_source": "Wild Alpine Flora & Rhododendron",
            "apiary_name": "Valais High Meadow Apiary",
            "beekeeper_name": "Markus Zenhäusern",
            "origin_location": "Valais Alpine Valley, Switzerland",
            "harvest_date": "2026-08-14",
            "comb_type": "Virgin Capped Comb",
            "extraction_method": "Unheated Centrifugation (Cold)",
            "quantity_kg": 280.0,
            "created_at": "2026-08-14 09:30:00 UTC",
            
            # Block 2 Data
            "lab": {
                "lab_name": "Swiss Agroscope Quality Lab",
                "inspector_name": "Dr. Beatrice Keller",
                "certificate_no": "CH-AGRO-2026-9912",
                "purity_score": 99.8,
                "moisture_content": 16.4,
                "nmr_profile": "Passed (Pure C3 Flora)",
                "hmf_level": 4.2,
                "lab_test_date": "2026-08-18",
                "location": "Bern, Switzerland",
                "digital_signature": "SIG-SHA256:8F4B92C10E83D71A934E2201",
                "signing_key_id": "KEY-LAB-AGROSCOPE-2026",
                "signature_timestamp": "2026-08-18 14:00:00 UTC",
                "notes": "NMR spectra verified pure unheated honey. HMF 4.2 mg/kg, zero sugar syrups."
            },
            
            # Block 3 Data
            "packaging": {
                "packaging_plant": "Helvetia Artisan Bottlers",
                "packaging_supervisor": "Lukas Meier",
                "jar_format": "500g Amber Glass Jar",
                "net_weight": "500g",
                "tamper_seal_id": "CH-SEAL-882194",
                "packaging_date": "2026-08-22",
                "lot_number": "LOT-2026-VALAIS-01",
                "location": "Thun, Switzerland",
                "notes": "Cold filtered through 200µm mesh. Tamper-evident holographic foil sealed."
            },
            
            # Block 4 Data
            "seller": {
                "seller_name": "AlpenGourmet Flagship Boutique",
                "store_location": "Bahnhofstrasse 42, Zurich, Switzerland",
                "license_no": "ZH-FOOD-88120",
                "shelf_arrival_date": "2026-08-26",
                "sale_price": "CHF 28.50",
                "retail_status": "On Shelf & Authenticated",
                "location": "Zurich, Switzerland",
                "notes": "Stored in temperature-controlled display at 19°C. Verified genuine."
            }
        },

        # Batch 2: Completed through Block 3 (Packaging Recorded)
        {
            "batch_id": "HC-2026-7215",
            "product_name": "Authentic New Zealand Raw Manuka UMF 20+",
            "floral_source": "Leptospermum scoparium (Manuka)",
            "apiary_name": "East Cape Wild Native Reserves",
            "beekeeper_name": "Aroha Te Whata",
            "origin_location": "East Cape, Bay of Plenty, New Zealand",
            "harvest_date": "2026-07-28",
            "comb_type": "Wild Forest Natural Comb",
            "extraction_method": "Raw Cold Press",
            "quantity_kg": 150.0,
            "created_at": "2026-07-28 08:15:00 UTC",
            
            "lab": {
                "lab_name": "Analytica Laboratories NZ",
                "inspector_name": "Dr. Hamish Stewart",
                "certificate_no": "NZ-ANALYTICA-2026-710",
                "purity_score": 99.9,
                "moisture_content": 17.1,
                "nmr_profile": "Passed (High Methylglyoxal)",
                "hmf_level": 6.8,
                "lab_test_date": "2026-08-04",
                "location": "Hamilton, New Zealand",
                "digital_signature": "SIG-SHA256:77D93B52CA0168F993B201AA",
                "signing_key_id": "KEY-LAB-ANALYTICA-NZ-2026",
                "signature_timestamp": "2026-08-04 14:00:00 UTC",
                "notes": "UMF 20+ Certified. Methylglyoxal (MGO) = 830 mg/kg, Leptosperin > 450 mg/kg."
            },
            
            "packaging": {
                "packaging_plant": "Pacific Pure Bottling Plant",
                "packaging_supervisor": "Moana Davis",
                "jar_format": "250g UV-Protected Amber Jar",
                "net_weight": "250g",
                "tamper_seal_id": "NZ-SEAL-77412",
                "packaging_date": "2026-08-10",
                "lot_number": "NZ-LOT-MANUKA-2026",
                "location": "Tauranga, New Zealand",
                "notes": "Nitrogen flushed, induction sealed. Ready for export/seller dispatch."
            }
        },

        # Batch 3: Completed through Block 2 (Laboratory Test Recorded)
        {
            "batch_id": "HC-2026-3108",
            "product_name": "Pure Acacia Blossom Golden Reserve",
            "floral_source": "Robinia pseudoacacia (Black Locust)",
            "apiary_name": "Piedmont Sunlit Groves",
            "beekeeper_name": "Matteo Moretti",
            "origin_location": "Langhe Valley, Piedmont, Italy",
            "harvest_date": "2026-09-02",
            "comb_type": "Monofloral Clean Comb",
            "extraction_method": "Unheated Centrifugation",
            "quantity_kg": 320.0,
            "created_at": "2026-09-02 10:00:00 UTC",
            
            "lab": {
                "lab_name": "Eurofins Scientific Food Testing",
                "inspector_name": "Dott.ssa Chiara Rossi",
                "certificate_no": "IT-EUROFINS-2026-3108",
                "purity_score": 99.4,
                "moisture_content": 16.9,
                "nmr_profile": "Passed (Authentic Acacia)",
                "hmf_level": 3.5,
                "lab_test_date": "2026-09-08",
                "location": "Turin, Italy",
                "digital_signature": "SIG-SHA256:3108E4A9C00281F7883901DC",
                "signing_key_id": "KEY-LAB-EUROFINS-PROD-2026",
                "signature_timestamp": "2026-09-08 14:00:00 UTC",
                "notes": "Low fructose-glucose crystallization tendency verified. Moisture 16.9%."
            }
        },

        # Batch 4: Freshly Registered (Block 1: Honey Batch Registered)
        {
            "batch_id": "HC-2026-1045",
            "product_name": "Black Forest Honeydew Raw Honey",
            "floral_source": "Coniferous Forest Honeydew",
            "apiary_name": "Schwarzwald Apiary",
            "beekeeper_name": "Hans Becker",
            "origin_location": "Baden-Württemberg, Germany",
            "harvest_date": "2026-09-25",
            "comb_type": "Traditional Wooden Frame Comb",
            "extraction_method": "Unheated Centrifugation",
            "quantity_kg": 210.0,
            "created_at": "2026-09-25 11:30:00 UTC"
        }
    ]

    for item in sample_batches:
        batch_id = item["batch_id"]

        # 1. Mine Block 1: Honey Batch Registered
        block1_data = {
            "event": "HONEY_BATCH_REGISTERED",
            "lifecycle_stage": "Block 1: Honey Batch Registered",
            "batch_id": batch_id,
            "product_name": item["product_name"],
            "floral_source": item["floral_source"],
            "apiary_name": item["apiary_name"],
            "beekeeper_name": item["beekeeper_name"],
            "origin_location": item["origin_location"],
            "harvest_date": item["harvest_date"],
            "comb_type": item["comb_type"],
            "extraction_method": item["extraction_method"],
            "quantity_kg": item["quantity_kg"],
            "notes": "Fresh honey harvest logged by certified apiary."
        }
        b1 = honey_blockchain.add_block(block1_data, block_type="Block 1: Honey Batch Registered")
        database.save_block_to_db(b1)

        qr_file = generate_qr(batch_id, "http://127.0.0.1:5000")

        highest_stage = 1
        current_stage_name = "Block 1: Honey Batch Registered"
        if "seller" in item:
            highest_stage = 4
            current_stage_name = "Block 4: Seller Information Recorded"
        elif "packaging" in item:
            highest_stage = 3
            current_stage_name = "Block 3: Honey Packaging Recorded"
        elif "lab" in item:
            highest_stage = 2
            current_stage_name = "Block 2: Laboratory Test Recorded"

        database.insert_batch({
            "batch_id": batch_id,
            "product_name": item["product_name"],
            "floral_source": item["floral_source"],
            "apiary_name": item["apiary_name"],
            "beekeeper_name": item["beekeeper_name"],
            "origin_location": item["origin_location"],
            "harvest_date": item["harvest_date"],
            "comb_type": item["comb_type"],
            "extraction_method": item["extraction_method"],
            "quantity_kg": item["quantity_kg"],
            "current_stage": current_stage_name,
            "stage_num": highest_stage,
            "qr_code_image": qr_file,
            "tx_hash": b1.hash,
            "block_index": b1.index,
            "created_at": item["created_at"],
            
            # Lab
            "lab_name": item.get("lab", {}).get("lab_name"),
            "inspector_name": item.get("lab", {}).get("inspector_name"),
            "certificate_no": item.get("lab", {}).get("certificate_no"),
            "purity_score": item.get("lab", {}).get("purity_score"),
            "moisture_content": item.get("lab", {}).get("moisture_content"),
            "nmr_profile": item.get("lab", {}).get("nmr_profile"),
            "hmf_level": item.get("lab", {}).get("hmf_level"),
            "lab_test_date": item.get("lab", {}).get("lab_test_date"),
            "digital_signature": item.get("lab", {}).get("digital_signature"),
            "signing_key_id": item.get("lab", {}).get("signing_key_id"),
            "signature_timestamp": item.get("lab", {}).get("signature_timestamp"),
            
            # Packaging
            "packaging_plant": item.get("packaging", {}).get("packaging_plant"),
            "packaging_supervisor": item.get("packaging", {}).get("packaging_supervisor"),
            "jar_format": item.get("packaging", {}).get("jar_format"),
            "net_weight": item.get("packaging", {}).get("net_weight"),
            "tamper_seal_id": item.get("packaging", {}).get("tamper_seal_id"),
            "packaging_date": item.get("packaging", {}).get("packaging_date"),
            "lot_number": item.get("packaging", {}).get("lot_number"),
            
            # Seller
            "seller_name": item.get("seller", {}).get("seller_name"),
            "store_location": item.get("seller", {}).get("store_location"),
            "license_no": item.get("seller", {}).get("license_no"),
            "shelf_arrival_date": item.get("seller", {}).get("shelf_arrival_date"),
            "sale_price": item.get("seller", {}).get("sale_price"),
            "retail_status": item.get("seller", {}).get("retail_status", "On Shelf & Authenticated")
        })

        database.add_stage_update({
            "batch_id": batch_id,
            "stage_num": 1,
            "stage_name": "Block 1: Honey Batch Registered",
            "actor_name": item["beekeeper_name"],
            "location": item["origin_location"],
            "details": {"comb_type": item["comb_type"], "quantity_kg": item["quantity_kg"]},
            "notes": "Harvest extracted and cryptographically registered by apiary.",
            "timestamp": item["created_at"],
            "block_hash": b1.hash,
            "block_index": b1.index
        })

        if "lab" in item:
            lab_data = item["lab"]
            block2_data = {
                "event": "LAB_TEST_RECORDED",
                "lifecycle_stage": "Block 2: Laboratory Test Recorded",
                "batch_id": batch_id,
                "lab_name": lab_data["lab_name"],
                "inspector_name": lab_data["inspector_name"],
                "certificate_no": lab_data["certificate_no"],
                "purity_score": lab_data["purity_score"],
                "moisture_content": lab_data["moisture_content"],
                "nmr_profile": lab_data["nmr_profile"],
                "hmf_level": lab_data["hmf_level"],
                "digital_signature": lab_data.get("digital_signature"),
                "signing_key_id": lab_data.get("signing_key_id"),
                "notes": lab_data["notes"]
            }
            b2 = honey_blockchain.add_block(block2_data, block_type="Block 2: Laboratory Test Recorded")
            database.save_block_to_db(b2)
            database.add_stage_update({
                "batch_id": batch_id,
                "stage_num": 2,
                "stage_name": "Block 2: Laboratory Test Recorded",
                "actor_name": f"{lab_data['lab_name']} ({lab_data['inspector_name']})",
                "location": lab_data["location"],
                "details": {
                    "certificate_no": lab_data["certificate_no"],
                    "purity_score": lab_data["purity_score"],
                    "digital_signature": lab_data.get("digital_signature")
                },
                "notes": lab_data["notes"],
                "timestamp": lab_data["lab_test_date"] + " 14:00:00 UTC",
                "block_hash": b2.hash,
                "block_index": b2.index
            })

        if "packaging" in item:
            pkg = item["packaging"]
            block3_data = {
                "event": "PACKAGING_RECORDED",
                "lifecycle_stage": "Block 3: Honey Packaging Recorded",
                "batch_id": batch_id,
                "packaging_plant": pkg["packaging_plant"],
                "packaging_supervisor": pkg["packaging_supervisor"],
                "jar_format": pkg["jar_format"],
                "net_weight": pkg["net_weight"],
                "tamper_seal_id": pkg["tamper_seal_id"],
                "lot_number": pkg["lot_number"],
                "notes": pkg["notes"]
            }
            b3 = honey_blockchain.add_block(block3_data, block_type="Block 3: Honey Packaging Recorded")
            database.save_block_to_db(b3)
            database.add_stage_update({
                "batch_id": batch_id,
                "stage_num": 3,
                "stage_name": "Block 3: Honey Packaging Recorded",
                "actor_name": f"{pkg['packaging_plant']} ({pkg['packaging_supervisor']})",
                "location": pkg["location"],
                "details": {"tamper_seal_id": pkg["tamper_seal_id"], "lot_number": pkg["lot_number"]},
                "notes": pkg["notes"],
                "timestamp": pkg["packaging_date"] + " 11:00:00 UTC",
                "block_hash": b3.hash,
                "block_index": b3.index
            })

        if "seller" in item:
            sel = item["seller"]
            block4_data = {
                "event": "SELLER_RECORDED",
                "lifecycle_stage": "Block 4: Seller Information Recorded",
                "batch_id": batch_id,
                "seller_name": sel["seller_name"],
                "store_location": sel["store_location"],
                "license_no": sel["license_no"],
                "shelf_arrival_date": sel["shelf_arrival_date"],
                "sale_price": sel["sale_price"],
                "retail_status": sel["retail_status"],
                "notes": sel["notes"]
            }
            b4 = honey_blockchain.add_block(block4_data, block_type="Block 4: Seller Information Recorded")
            database.save_block_to_db(b4)
            database.add_stage_update({
                "batch_id": batch_id,
                "stage_num": 4,
                "stage_name": "Block 4: Seller Information Recorded",
                "actor_name": sel["seller_name"],
                "location": sel["location"],
                "details": {"license_no": sel["license_no"], "sale_price": sel["sale_price"]},
                "notes": sel["notes"],
                "timestamp": sel["shelf_arrival_date"] + " 09:00:00 UTC",
                "block_hash": b4.hash,
                "block_index": b4.index
            })


seed_sample_data_if_needed()


def refresh_batch_qrcodes():
    """
    Refreshes all batch QR codes with the reachable network LAN IP
    so mobile phone cameras can scan and trace immediately over Wi-Fi.
    """
    try:
        batches = database.get_all_batches()
        port = int(os.environ.get("PORT", 5000))
        lan_url = f"http://{get_local_ip()}:{port}"
        for b in batches:
            generate_qr(b["batch_id"], lan_url)
    except Exception as e:
        pass


# Network & Deployment Context Processor for all templates
@app.context_processor
def inject_network_context():
    port = int(os.environ.get("PORT", 5000))
    lan_ip = get_local_ip()
    pub_url = get_public_base_url()
    return {
        "lan_ip": lan_ip,
        "network_port": port,
        "local_url": f"http://127.0.0.1:{port}",
        "network_url": f"http://{lan_ip}:{port}",
        "public_url": pub_url,
        "host_machine": socket.gethostname(),
        "roles_metadata": ROLES_METADATA,
        "is_production": bool(os.environ.get("PUBLIC_BASE_URL") or os.environ.get("RENDER"))
    }


# Progressive Web App (PWA) Endpoints
@app.route("/manifest.json")
def pwa_manifest():
    return send_file(os.path.join(BASE_DIR, "static", "manifest.json"), mimetype="application/manifest+json")


@app.route("/sw.js")
def pwa_service_worker():
    response = send_file(os.path.join(BASE_DIR, "static", "sw.js"), mimetype="application/javascript")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/offline")
def pwa_offline():
    return render_template("offline.html")


# Pretty JSON Template Filter
@app.template_filter("pretty_json")
def pretty_json(value):
    try:
        if isinstance(value, str):
            value = json.loads(value)
        return json.dumps(value, indent=2, sort_keys=True)
    except Exception:
        return str(value)


# ==================== MASTER SINGLE-LINK ROUTE ====================

@app.route("/")
def index():
    """
    MASTER SINGLE-LINK PORTAL (http://127.0.0.1:5000/):
    Unifies all features into a single responsive portal:
    - Phase 1: Core features (Batch registration, PoW Ledger, QR generator, Traceability, Role-based login)
    - Phase 2: Advanced features (Dashboard analytics, Batch status tracking, Blockchain alerts & tamper tester, PDF reports)
    - Phase 3: Unique features (Lab Digital signatures, Admin partner approvals, Supply chain timeline, Customer feedback)
    """
    stats = database.get_stats()
    batches = database.get_all_batches()
    is_valid, validation_msg = honey_blockchain.is_chain_valid()
    latest_block = honey_blockchain.get_latest_block()

    # Active batch for the Trace tab
    active_batch_id = request.args.get("batch_id", "").strip().upper().lstrip("#")
    if not active_batch_id:
        active_batch_id = "HC-2026-9842" if batches else ""

    active_batch = database.get_batch(active_batch_id) if active_batch_id else None
    
    # Ensure QR exists
    if active_batch:
        qr_file = active_batch.get("qr_code_image") or f"{active_batch_id}.png"
        qr_path = os.path.join(QR_DIR, qr_file)
        if not os.path.exists(qr_path):
            qr_file = generate_qr(active_batch_id, request.host_url)
        active_batch["qr_code_image"] = qr_file

    active_updates = database.get_stage_updates(active_batch_id) if active_batch_id else []
    active_blocks = honey_blockchain.get_batch_history(active_batch_id) if active_batch_id else []

    suggested_id = f"HC-{datetime.now(timezone.utc).year}-{random.randint(1000, 9999)}"
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    initial_tab = request.args.get("tab", "hub")

    # Specific one-by-one baseline example references (Block 0 to Block 4)
    genesis_block = honey_blockchain.chain[0] if honey_blockchain.chain else None
    example_b1 = database.get_batch("HC-2026-1045") or next((b for b in batches if b["stage_num"] == 1), None)
    example_b2 = database.get_batch("HC-2026-3108") or next((b for b in batches if b["stage_num"] == 2), None)
    example_b3 = database.get_batch("HC-2026-7215") or next((b for b in batches if b["stage_num"] == 3), None)
    example_b4 = database.get_batch("HC-2026-9842") or next((b for b in batches if b["stage_num"] == 4), None)

    # Phase 1: Current active user role
    current_role = get_current_role()
    current_user = database.get_user_by_role(current_role)
    all_users = database.get_all_users()

    # Phase 2: Live Database Blockchain Audit & Tamper Detection
    audit_valid, audit_msg, tampered_blocks = honey_blockchain.audit_database_blocks()

    # Phase 3: Partner Approvals & Customer Feedback
    laboratories = database.get_laboratories()
    approved_labs = database.get_laboratories("APPROVED")
    sellers = database.get_sellers()
    approved_sellers = database.get_sellers("APPROVED")
    all_feedback = database.get_all_feedback()

    return render_template(
        "index.html",
        stats=stats,
        batches=batches,
        is_chain_valid=is_valid,
        validation_msg=validation_msg,
        audit_valid=audit_valid,
        audit_msg=audit_msg,
        tampered_blocks=tampered_blocks,
        latest_block=latest_block,
        stage_config=STAGE_CONFIG,
        active_batch=active_batch,
        active_batch_id=active_batch_id,
        active_updates=active_updates,
        active_blocks=active_blocks,
        all_blocks=honey_blockchain.chain,
        suggested_id=suggested_id,
        today_date=today_date,
        initial_tab=initial_tab,
        genesis_block=genesis_block,
        example_b1=example_b1,
        example_b2=example_b2,
        example_b3=example_b3,
        example_b4=example_b4,
        # Phase 1 & 2 & 3 Context
        current_role=current_role,
        current_user=current_user,
        roles_metadata=ROLES_METADATA,
        all_users=all_users,
        laboratories=laboratories,
        approved_labs=approved_labs,
        sellers=sellers,
        approved_sellers=approved_sellers,
        all_feedback=all_feedback,
    )


# ==================== PHASE 1: ROLE-BASED LOGIN & SESSION ====================

@app.route("/switch-role/<role>")
def switch_role(role):
    """
    1-Click instant role switcher allowing immediate testing of Beekeeper, Lab, Packager, Seller, Consumer, and Admin.
    """
    role = role.lower().strip()
    if role in ROLES_METADATA:
        session["user_role"] = role
        user_info = database.get_user_by_role(role)
        name = user_info["full_name"] if user_info else role.capitalize()
        flash(f"Switched active session to: {ROLES_METADATA[role]['title']} ({name})", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Dedicated Login Page handling authentication and 1-click persona demo logins.
    """
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()

        user = None
        if identifier:
            user = database.authenticate_user(identifier, password)
            if not user:
                # Also allow direct login by email or role preset
                user = database.get_user_by_login(identifier)
        else:
            email = request.form.get("email", "").strip()
            role = request.form.get("role", "admin").strip().lower()
            user = database.get_user_by_email(email) or database.get_user_by_role(role)

        if user:
            session["user_role"] = user["role"]
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            session["user_email"] = user["email"]
            flash(f"Welcome back, {user['full_name']}! Authenticated as {ROLES_METADATA[user['role']]['title']}.", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials! Please enter valid account details or click any 1-click demo persona.", "error")
            return redirect(url_for("index", tab="login"))

    return redirect(url_for("index", tab="login"))


@app.route("/logout")
def logout():
    session.pop("user_role", None)
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    session["user_role"] = "consumer"
    flash("Session signed out. Switched to Public Consumer view.", "info")
    return redirect(url_for("index", tab="hub"))



# ==================== PHASE 2: PDF TRACEABILITY REPORT ====================

@app.route("/batch/<batch_id>/pdf")
def download_batch_pdf(batch_id):
    """
    Generates and serves high-fidelity PDF Certificate of Origin & Provenance.
    """
    batch_id = batch_id.strip().upper().lstrip("#")
    batch = database.get_batch(batch_id)
    if not batch:
        flash(f"Batch {batch_id} not found for PDF report generation.", "error")
        return redirect(url_for("index", tab="hub"))

    updates = database.get_stage_updates(batch_id)
    blocks = honey_blockchain.chain
    qr_filename = batch.get("qr_code_image") or f"{batch_id}.png"
    qr_path = os.path.join(QR_DIR, qr_filename)
    if not os.path.exists(qr_path):
        qr_filename = generate_qr(batch_id, request.host_url)
        qr_path = os.path.join(QR_DIR, qr_filename)

    pdf_buffer = pdf_generator.generate_certificate_pdf(batch, updates, blocks, qr_path)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"{batch_id}_Provenance_Certificate.pdf",
        mimetype="application/pdf"
    )


# ==================== PHASE 2: BLOCKCHAIN VERIFICATION & TAMPER SIMULATOR ====================

@app.route("/admin/tamper-test/<int:block_index>")
def admin_tamper_test(block_index):
    """
    Simulates unauthorized database tampering to demonstrate live cryptographic alert!
    """
    database.tamper_block_in_db(block_index)
    flash(f"⚠️ TAMPER SIMULATED ON BLOCK #{block_index}! An unauthorized edit was injected into the SQLite database. Check the Blockchain Alerts panel!", "error")
    return redirect(url_for("index", tab="explorer"))


@app.route("/admin/repair-chain")
def admin_repair_chain():
    """
    Restores tampered database blocks to matching cryptographic consensus.
    """
    database.repair_tampered_blocks(honey_blockchain)
    flash("🛡️ BLOCKCHAIN REPAIRED & RE-VALIDATED! All records match 100% cryptographic consensus.", "success")
    return redirect(url_for("index", tab="explorer"))


# ==================== PHASE 3: PARTNER APPROVALS ====================

@app.route("/admin/approve-lab/<int:lab_id>/<action>")
def admin_approve_lab(lab_id, action):
    status = "APPROVED" if action == "approve" else ("REJECTED" if action == "reject" else "PENDING")
    database.update_laboratory_status(lab_id, status, "Consortium Lead Auditor")
    flash(f"Testing Laboratory #{lab_id} accreditation status updated to: {status}.", "success")
    return redirect(url_for("index", tab="explorer"))


@app.route("/admin/approve-seller/<int:seller_id>/<action>")
def admin_approve_seller(seller_id, action):
    status = "APPROVED" if action == "approve" else ("REJECTED" if action == "reject" else "PENDING")
    database.update_seller_status(seller_id, status, "Consortium Lead Auditor")
    flash(f"Retailer License #{seller_id} status updated to: {status}.", "success")
    return redirect(url_for("index", tab="explorer"))


# ==================== PHASE 3: CUSTOMER FEEDBACK & DISPUTES ====================

@app.route("/feedback/submit", methods=["POST"])
def submit_feedback():
    batch_id = request.form.get("batch_id", "HC-GENERAL").strip().upper()
    customer_name = request.form.get("customer_name", "Anonymous Consumer").strip()
    customer_email = request.form.get("customer_email", "guest@consumer.com").strip()
    try:
        rating = int(request.form.get("rating", 5))
    except ValueError:
        rating = 5
    issue_type = request.form.get("issue_type", "General Feedback").strip()
    message = request.form.get("message", "").strip()

    database.add_feedback({
        "batch_id": batch_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "rating": rating,
        "issue_type": issue_type,
        "message": message
    })
    flash(f"Thank you, {customer_name}! Your feedback report for batch {batch_id} has been recorded on the HoneyChain ledger.", "success")
    return redirect(url_for("index", tab="trace", batch_id=batch_id))


@app.route("/admin/feedback-status/<int:feedback_id>/<new_status>")
def update_feedback_status(feedback_id, new_status):
    database.update_feedback_status(feedback_id, new_status, f"Audited by Admin on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    flash(f"Customer feedback #{feedback_id} status updated to '{new_status}'.", "success")
    return redirect(url_for("index", tab="explorer"))


# ==================== ACTION ROUTES ====================

@app.route("/reset-examples")
def reset_examples():
    """
    Restores exactly one clean living example of each block (Block 0 to Block 4).
    """
    seed_sample_data_if_needed(force=True)
    flash("Successfully reset to 5 official baseline examples: Block 0 (Genesis), Block 1 (Harvested), Block 2 (Lab Tested), Block 3 (Packaged), and Block 4 (On Shelf)!", "success")
    return redirect(url_for("index", tab="hub"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles Block 1 registration and seamlessly returns to the single link portal.
    """
    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper().lstrip("#")
        if not batch_id:
            batch_id = f"HC-{datetime.now(timezone.utc).year}-{random.randint(1000, 9999)}"

        existing = database.get_batch(batch_id)
        if existing:
            flash(f"Batch ID '{batch_id}' already registered on the blockchain!", "error")
            return redirect(url_for("index", tab="register"))

        product_name = request.form.get("product_name", "Artisan Raw Honey").strip()
        floral_source = request.form.get("floral_source", "Wildflower Flora").strip()
        apiary_name = request.form.get("apiary_name", "").strip()
        beekeeper_name = request.form.get("beekeeper_name", "").strip()
        origin_location = request.form.get("origin_location", "").strip()
        harvest_date = request.form.get("harvest_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        comb_type = request.form.get("comb_type", "Virgin Capped Comb").strip()
        extraction_method = request.form.get("extraction_method", "Unheated Cold Centrifugation").strip()
        
        try:
            quantity_kg = float(request.form.get("quantity_kg", 200.0))
        except ValueError:
            quantity_kg = 200.0

        initial_notes = request.form.get("notes", "Raw honey extraction logged by certified beekeeper.").strip()

        # Mine Block 1
        block1_data = {
            "event": "HONEY_BATCH_REGISTERED",
            "lifecycle_stage": "Block 1: Honey Batch Registered",
            "batch_id": batch_id,
            "product_name": product_name,
            "floral_source": floral_source,
            "apiary_name": apiary_name,
            "beekeeper_name": beekeeper_name,
            "origin_location": origin_location,
            "harvest_date": harvest_date,
            "comb_type": comb_type,
            "extraction_method": extraction_method,
            "quantity_kg": quantity_kg,
            "notes": initial_notes
        }

        mined_block = honey_blockchain.add_block(block1_data, block_type="Block 1: Honey Batch Registered")
        database.save_block_to_db(mined_block)

        qr_filename = generate_qr(batch_id, request.host_url)

        batch_record = {
            "batch_id": batch_id,
            "product_name": product_name,
            "floral_source": floral_source,
            "apiary_name": apiary_name,
            "beekeeper_name": beekeeper_name,
            "origin_location": origin_location,
            "harvest_date": harvest_date,
            "comb_type": comb_type,
            "extraction_method": extraction_method,
            "quantity_kg": quantity_kg,
            "current_stage": "Block 1: Honey Batch Registered",
            "stage_num": 1,
            "qr_code_image": qr_filename,
            "tx_hash": mined_block.hash,
            "block_index": mined_block.index,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        database.insert_batch(batch_record)

        database.add_stage_update({
            "batch_id": batch_id,
            "stage_num": 1,
            "stage_name": "Block 1: Honey Batch Registered",
            "actor_name": beekeeper_name or "Certified Apiary",
            "location": origin_location,
            "details": {"comb_type": comb_type, "quantity_kg": quantity_kg},
            "notes": initial_notes,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "block_hash": mined_block.hash,
            "block_index": mined_block.index
        })

        flash(f"Block 1: Honey Batch #{batch_id} successfully mined into Block #{mined_block.index}!", "success")
        return redirect(url_for("index", tab="trace", batch_id=batch_id))

    return redirect(url_for("index", tab="register"))


@app.route("/trace")
@app.route("/trace/<batch_id>")
def trace_batch(batch_id=None):
    if not batch_id:
        batch_id = request.args.get("batch_id", "").strip().upper().lstrip("#")
    return redirect(url_for("index", tab="trace", batch_id=batch_id if batch_id else "HC-2026-9842"))


@app.route("/dashboard")
def dashboard():
    return redirect(url_for("index", tab="explorer"))


@app.route("/advance-lifecycle/<batch_id>", methods=["POST"])
def advance_lifecycle(batch_id):
    """
    Mines Block 2, Block 3, or Block 4 in the 5-block lifecycle.
    """
    batch_id = batch_id.strip().upper().lstrip("#")
    batch = database.get_batch(batch_id)
    if not batch:
        flash("Batch not found.", "error")
        return redirect(url_for("index", tab="explorer"))

    target_block = int(request.form.get("target_block", 2))

    if target_block == 2:
        # Block 2: Laboratory Test Recorded
        lab_name = request.form.get("lab_name", "Eurofins Scientific Food Testing").strip()
        inspector_name = request.form.get("inspector_name", "Dr. Sandra Meyer").strip()
        certificate_no = request.form.get("certificate_no", f"LAB-CERT-{random.randint(1000, 9999)}").strip()
        try:
            purity_score = float(request.form.get("purity_score", 99.6))
        except ValueError:
            purity_score = 99.6
        try:
            moisture_content = float(request.form.get("moisture_content", 16.8))
        except ValueError:
            moisture_content = 16.8
        nmr_profile = request.form.get("nmr_profile", "Passed (Nuclear Magnetic Resonance Verified)").strip()
        try:
            hmf_level = float(request.form.get("hmf_level", 4.5))
        except ValueError:
            hmf_level = 4.5
        lab_test_date = request.form.get("lab_test_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        location = request.form.get("location", "Zurich Food Testing Center").strip()
        notes = request.form.get("notes", "NMR spectrum confirms pure nectar with zero synthetic sugars.").strip()

        # Phase 3 Feature: Digital Signature Creation
        digital_sig = generate_lab_digital_signature(batch_id, certificate_no, purity_score, moisture_content, hmf_level)
        signing_key_id = f"KEY-LAB-{lab_name[:8].upper().replace(' ', '-')}-2026"
        sig_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        block2_data = {
            "event": "LAB_TEST_RECORDED",
            "lifecycle_stage": "Block 2: Laboratory Test Recorded",
            "batch_id": batch_id,
            "product_name": batch["product_name"],
            "lab_name": lab_name,
            "inspector_name": inspector_name,
            "certificate_no": certificate_no,
            "purity_score": purity_score,
            "moisture_content": moisture_content,
            "nmr_profile": nmr_profile,
            "hmf_level": hmf_level,
            "digital_signature": digital_sig,
            "signing_key_id": signing_key_id,
            "notes": notes,
            "timestamp": sig_timestamp
        }
        new_block = honey_blockchain.add_block(block2_data, block_type="Block 2: Laboratory Test Recorded")
        database.save_block_to_db(new_block)

        database.update_batch_lifecycle_fields(batch_id, 2, "Block 2: Laboratory Test Recorded", {
            "lab_name": lab_name,
            "inspector_name": inspector_name,
            "certificate_no": certificate_no,
            "purity_score": purity_score,
            "moisture_content": moisture_content,
            "nmr_profile": nmr_profile,
            "hmf_level": hmf_level,
            "lab_test_date": lab_test_date,
            "digital_signature": digital_sig,
            "signing_key_id": signing_key_id,
            "signature_timestamp": sig_timestamp
        })

        database.add_stage_update({
            "batch_id": batch_id,
            "stage_num": 2,
            "stage_name": "Block 2: Laboratory Test Recorded",
            "actor_name": f"{lab_name} ({inspector_name})",
            "location": location,
            "details": {
                "certificate_no": certificate_no,
                "purity_score": purity_score,
                "moisture_content": moisture_content,
                "digital_signature": digital_sig
            },
            "notes": notes,
            "timestamp": sig_timestamp,
            "block_hash": new_block.hash,
            "block_index": new_block.index
        })

        flash(f"Block 2: Laboratory Test certified & Digitally Signed ({digital_sig}) into Block #{new_block.index}!", "success")

    elif target_block == 3:
        # Block 3: Honey Packaging Recorded
        packaging_plant = request.form.get("packaging_plant", "Alpine Artisan Bottlers").strip()
        packaging_supervisor = request.form.get("packaging_supervisor", "Thomas Weber").strip()
        jar_format = request.form.get("jar_format", "500g Amber Glass Jar").strip()
        net_weight = request.form.get("net_weight", "500g").strip()
        tamper_seal_id = request.form.get("tamper_seal_id", f"SEAL-{batch_id}-99").strip()
        packaging_date = request.form.get("packaging_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        lot_number = request.form.get("lot_number", f"LOT-{batch_id}").strip()
        location = request.form.get("location", "Lucerne Bottling Facility").strip()
        notes = request.form.get("notes", "Filtered cold through 200µm mesh. Inert nitrogen flush applied.").strip()

        block3_data = {
            "event": "PACKAGING_RECORDED",
            "lifecycle_stage": "Block 3: Honey Packaging Recorded",
            "batch_id": batch_id,
            "product_name": batch["product_name"],
            "packaging_plant": packaging_plant,
            "packaging_supervisor": packaging_supervisor,
            "jar_format": jar_format,
            "net_weight": net_weight,
            "tamper_seal_id": tamper_seal_id,
            "lot_number": lot_number,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        new_block = honey_blockchain.add_block(block3_data, block_type="Block 3: Honey Packaging Recorded")
        database.save_block_to_db(new_block)

        database.update_batch_lifecycle_fields(batch_id, 3, "Block 3: Honey Packaging Recorded", {
            "packaging_plant": packaging_plant,
            "packaging_supervisor": packaging_supervisor,
            "jar_format": jar_format,
            "net_weight": net_weight,
            "tamper_seal_id": tamper_seal_id,
            "packaging_date": packaging_date,
            "lot_number": lot_number
        })

        database.add_stage_update({
            "batch_id": batch_id,
            "stage_num": 3,
            "stage_name": "Block 3: Honey Packaging Recorded",
            "actor_name": f"{packaging_plant} ({packaging_supervisor})",
            "location": location,
            "details": {"tamper_seal_id": tamper_seal_id, "jar_format": jar_format},
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "block_hash": new_block.hash,
            "block_index": new_block.index
        })

        flash(f"Block 3: Honey Packaging recorded with tamper seal #{tamper_seal_id} into Block #{new_block.index}!", "success")

    elif target_block == 4:
        # Block 4: Seller Information Recorded
        seller_name = request.form.get("seller_name", "BioGourmet Flagship Store").strip()
        store_location = request.form.get("store_location", "Limmatquai 18, Zurich").strip()
        license_no = request.form.get("license_no", f"LIC-ZH-881920").strip()
        shelf_arrival_date = request.form.get("shelf_arrival_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        sale_price = request.form.get("sale_price", "$22.50").strip()
        retail_status = request.form.get("retail_status", "On Shelf & Authenticated").strip()
        notes = request.form.get("notes", "Batch accepted into temperature-regulated display. Authenticated genuine.").strip()

        block4_data = {
            "event": "SELLER_RECORDED",
            "lifecycle_stage": "Block 4: Seller Information Recorded",
            "batch_id": batch_id,
            "product_name": batch["product_name"],
            "seller_name": seller_name,
            "store_location": store_location,
            "license_no": license_no,
            "shelf_arrival_date": shelf_arrival_date,
            "sale_price": sale_price,
            "retail_status": retail_status,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        new_block = honey_blockchain.add_block(block4_data, block_type="Block 4: Seller Information Recorded")
        database.save_block_to_db(new_block)

        database.update_batch_lifecycle_fields(batch_id, 4, "Block 4: Seller Information Recorded", {
            "seller_name": seller_name,
            "store_location": store_location,
            "license_no": license_no,
            "shelf_arrival_date": shelf_arrival_date,
            "sale_price": sale_price,
            "retail_status": retail_status
        })

        database.add_stage_update({
            "batch_id": batch_id,
            "stage_num": 4,
            "stage_name": "Block 4: Seller Information Recorded",
            "actor_name": seller_name,
            "location": store_location,
            "details": {"license_no": license_no, "sale_price": sale_price},
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "block_hash": new_block.hash,
            "block_index": new_block.index
        })

        flash(f"Block 4: Seller Information sealed into Block #{new_block.index}! Full 5-Block Provenance Chain Complete!", "success")

    return redirect(url_for("index", tab="trace", batch_id=batch_id))


# ==================== JSON REST APIs ====================

@app.route("/api/chain", methods=["GET"])
def api_get_chain():
    is_valid, message = honey_blockchain.is_chain_valid()
    return jsonify({
        "protocol": "HoneyChain 5-Block Lifecycle Ledger",
        "length": len(honey_blockchain.chain),
        "difficulty": honey_blockchain.difficulty,
        "is_chain_valid": is_valid,
        "validation_message": message,
        "chain": [block.to_dict() for block in honey_blockchain.chain],
    })


@app.route("/api/verify-chain", methods=["GET"])
def api_verify_chain():
    is_valid, message, tampered = honey_blockchain.audit_database_blocks()
    return jsonify({
        "verified": is_valid,
        "message": message,
        "tampered_blocks": tampered,
        "total_blocks": len(honey_blockchain.chain)
    })


@app.route("/api/trace/<batch_id>", methods=["GET"])
def api_trace_batch(batch_id):
    batch = database.get_batch(batch_id)
    if not batch:
        return jsonify({"success": False, "error": "Batch not found"}), 404

    updates = database.get_stage_updates(batch_id)
    blocks = [b.to_dict() for b in honey_blockchain.get_batch_history(batch_id)]
    is_valid, message = honey_blockchain.is_chain_valid()

    return jsonify({
        "success": True,
        "batch": batch,
        "stage_history": updates,
        "blockchain_events": blocks,
        "chain_verified": is_valid,
    })


@app.route("/api/network-qr", methods=["GET"])
def api_network_qr():
    """
    Generates and returns an instant PNG QR code for the LAN Network URL.
    Can be scanned by any smartphone camera on the local Wi-Fi.
    """
    port = int(os.environ.get("PORT", 5000))
    lan_ip = get_local_ip()
    url = f"http://{lan_ip}:{port}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/api/network-info", methods=["GET"])
def api_network_info():
    """
    Returns network IP, ports, hostname, and connectivity instructions.
    """
    port = int(os.environ.get("PORT", 5000))
    lan_ip = get_local_ip()
    return jsonify({
        "success": True,
        "lan_ip": lan_ip,
        "port": port,
        "local_url": f"http://127.0.0.1:{port}",
        "network_url": f"http://{lan_ip}:{port}",
        "hostname": socket.gethostname(),
        "status": "online",
        "tip": "Devices on the same Wi-Fi can open network_url directly or scan /api/network-qr"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    lan_ip = get_local_ip()
    refresh_batch_qrcodes()
    print("\n" + "=" * 66)
    print("   [HONEYCHAIN] Unified Master Blockchain Portal Online")
    print("   ==============================================================")
    print(f"   * Local Machine:     http://127.0.0.1:{port}")
    print(f"   * Network / Wi-Fi:   http://{lan_ip}:{port}  <-- Any device on Wi-Fi")
    print(f"   * Mobile Phone:      Scan Network QR code from top portal bar")
    print("   ==============================================================")
    print(f"   Listening on 0.0.0.0:{port} (All Network Interfaces)...")
    print("=" * 66 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True)

