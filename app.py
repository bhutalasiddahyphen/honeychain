import os
import random
import json
import sys
import hmac
import hashlib
import socket
import io
import csv
from functools import wraps
from datetime import datetime, timezone
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, send_file, send_from_directory, Response
)
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

# Role definitions
ROLES_METADATA = {
    "admin": {
        "title": "Consortium Chief Auditor",
        "badge": "ADMIN AUDITOR",
        "icon": "fa-user-shield",
        "color": "#f43f5e"
    },
    "beekeeper": {
        "title": "Master Beekeeper / Apiary",
        "badge": "APIARY PRODUCER",
        "icon": "fa-seedling",
        "color": "#f59e0b"
    },
    "lab": {
        "title": "Testing Laboratory Inspector",
        "badge": "LAB ANALYST",
        "icon": "fa-flask-vial",
        "color": "#10b981"
    },
    "packager": {
        "title": "Certified Bottling Facility",
        "badge": "BOTTLING FACILITY",
        "icon": "fa-box-open",
        "color": "#3b82f6"
    },
    "seller": {
        "title": "Authorized Retailer / Seller",
        "badge": "AUTHORIZED RETAILER",
        "icon": "fa-store",
        "color": "#8b5cf6"
    },
    "consumer": {
        "title": "Public Consumer / Shopper",
        "badge": "PUBLIC CONSUMER",
        "icon": "fa-user-check",
        "color": "#06b6d4"
    }
}


# ==================== HELPER UTILITIES ====================

def get_local_ip():
    """Returns local LAN/Wi-Fi IPv4 address for multi-device network testing."""
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
    env_url = (os.environ.get("PUBLIC_BASE_URL") or os.environ.get("BASE_URL") or "").strip().rstrip("/")
    if env_url:
        return env_url
    try:
        if request:
            proto = request.headers.get("X-Forwarded-Proto", request.scheme)
            host = request.host
            if host and not host.startswith("127.0.0.1") and not host.startswith("localhost"):
                return f"{proto}://{host}"
    except Exception:
        pass
    port = int(os.environ.get("PORT", 5000))
    lan_ip = get_local_ip()
    return f"http://{lan_ip}:{port}"


def generate_lab_digital_signature(batch_id, cert_no, purity, moisture, hmf, secret="EUROFINS_CONSORTIUM_RSA_KEY_2026"):
    payload = f"{batch_id}|{cert_no}|{purity}|{moisture}|{hmf}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"SIG-SHA256:{sig[:28].upper()}"


def generate_qr(batch_id, base_url=None):
    """Generates high-resolution consumer QR code pointing to product verification."""
    if not base_url or "127.0.0.1" in base_url or "localhost" in base_url:
        base_url = get_public_base_url()
    verify_url = f"{base_url.rstrip('/')}/verification?batch_id={batch_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#24150d", back_color="#ffffff")
    file_name = f"{batch_id}.png"
    file_path = os.path.join(QR_DIR, file_name)
    img.save(file_path)
    return file_name


def refresh_batch_qrcodes():
    try:
        batches = database.get_all_batches()
        port = int(os.environ.get("PORT", 5000))
        lan_url = f"http://{get_local_ip()}:{port}"
        for b in batches:
            generate_qr(b["batch_id"], lan_url)
    except Exception:
        pass


def seed_sample_data_if_needed(force=False):
    """Optional helper for development testing with sample data. Does not run on startup."""
    if not force:
        return

    sample_batches = [
        {
            "batch_id": "HC-2026-9842",
            "product_name": "Organic Alpine Blossom Raw Honey",
            "floral_source": "Wild Alpine Flora & Rhododendron",
            "apiary_name": "Valais High Meadow Apiary",
            "beekeeper_name": "Markus Zenhäusern",
            "origin_location": "Valais Alps, Elevation 1,650m, Switzerland",
            "harvest_date": "2026-08-14",
            "comb_type": "Pure Capped Organic Comb",
            "extraction_method": "Unheated Cold Centrifugation",
            "quantity_kg": 250.0,
            "created_at": "2026-08-14 09:30:00 UTC",
            "lab": {
                "lab_name": "Swiss Agroscope Quality Lab",
                "inspector_name": "Dr. Beatrice Keller",
                "certificate_no": "CH-AGRO-2026-9912",
                "purity_score": 99.8,
                "moisture_content": 16.4,
                "nmr_profile": "100% Pure Raw Honey - No Exogenous Sugars / C4 Negative",
                "hmf_level": 4.2,
                "lab_test_date": "2026-08-20",
                "digital_signature": "SIG-SHA256:88F2A190B3847E99A201DFB892AA",
                "signing_key_id": "KEY-LAB-AGROSCOPE-2026",
                "signature_timestamp": "2026-08-20 14:15:00 UTC"
            },
            "packaging": {
                "packaging_plant": "Helvetia Artisan Bottlers Ltd.",
                "packaging_supervisor": "Lukas Meier",
                "jar_format": "500g Hexagonal Embossed Glass Jar",
                "net_weight": "500g (± 2g)",
                "tamper_seal_id": "SEAL-CH-2026-9842",
                "lot_number": "LOT-2026-CH-09B",
                "packaging_date": "2026-08-25"
            },
            "seller": {
                "seller_name": "AlpenGourmet Flagship Boutique",
                "store_location": "Bahnhofstrasse 42, 8001 Zurich, Switzerland",
                "license_no": "ZH-FOOD-88120",
                "shelf_arrival_date": "2026-09-01",
                "sale_price": "$48.00",
                "retail_status": "On Shelf & Authenticated"
            }
        },
        {
            "batch_id": "HC-2026-7215",
            "product_name": "Authentic Manuka Raw Honey UMF 20+",
            "floral_source": "Manuka (Leptospermum scoparium)",
            "apiary_name": "Canterbury Southern Alps Apiary",
            "beekeeper_name": "Jack & Sarah Wilson",
            "origin_location": "Canterbury High Country, New Zealand",
            "harvest_date": "2026-08-22",
            "comb_type": "Cold Pressed Comb",
            "extraction_method": "Unheated Centrifugation",
            "quantity_kg": 180.0,
            "created_at": "2026-08-22 10:15:00 UTC",
            "lab": {
                "lab_name": "Analytica Laboratories NZ",
                "inspector_name": "Dr. Keith Armstrong",
                "certificate_no": "NZ-ANALYTICA-2026-710",
                "purity_score": 99.6,
                "moisture_content": 17.1,
                "nmr_profile": "Pure Monofloral Manuka - MGO 829mg/kg",
                "hmf_level": 6.8,
                "lab_test_date": "2026-08-28",
                "digital_signature": "SIG-SHA256:7731BA80902FE229B0182C89AA10",
                "signing_key_id": "KEY-LAB-ANALYTICA-NZ-2026",
                "signature_timestamp": "2026-08-28 16:30:00 UTC"
            },
            "packaging": {
                "packaging_plant": "Aotearoa Clean Packaging Facility",
                "packaging_supervisor": "Elena Vance",
                "jar_format": "250g Artisan Glass Hex Jar",
                "net_weight": "250g (± 1g)",
                "tamper_seal_id": "NZ-SEAL-77412",
                "lot_number": "LOT-2026-NZ-08",
                "packaging_date": "2026-09-02"
            }
        },
        {
            "batch_id": "HC-2026-3108",
            "product_name": "Pure Acacia Blossom Golden Reserve",
            "floral_source": "Robinia pseudoacacia (Black Locust)",
            "apiary_name": "Black Forest Artisan Hives",
            "beekeeper_name": "Clara Schmidt",
            "origin_location": "Baden-Württemberg, Germany",
            "harvest_date": "2026-09-15",
            "comb_type": "Natural Comb Frame",
            "extraction_method": "Cold Centrifugation",
            "quantity_kg": 210.0,
            "created_at": "2026-09-15 11:30:00 UTC"
        }
    ]

    for item in sample_batches:
        batch_id = item["batch_id"]

        # Block 1
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
            "notes": "Origin harvest registered on ledger."
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
            "packaging_plant": item.get("packaging", {}).get("packaging_plant"),
            "packaging_supervisor": item.get("packaging", {}).get("packaging_supervisor"),
            "jar_format": item.get("packaging", {}).get("jar_format"),
            "net_weight": item.get("packaging", {}).get("net_weight"),
            "tamper_seal_id": item.get("packaging", {}).get("tamper_seal_id"),
            "lot_number": item.get("packaging", {}).get("lot_number"),
            "packaging_date": item.get("packaging", {}).get("packaging_date"),
            "seller_name": item.get("seller", {}).get("seller_name"),
            "store_location": item.get("seller", {}).get("store_location"),
            "license_no": item.get("seller", {}).get("license_no"),
            "shelf_arrival_date": item.get("seller", {}).get("shelf_arrival_date"),
            "sale_price": item.get("seller", {}).get("sale_price"),
            "retail_status": item.get("seller", {}).get("retail_status", "On Shelf & Authenticated")
        })

        if "lab" in item:
            lab = item["lab"]
            b2_data = {
                "event": "LAB_TEST_RECORDED",
                "lifecycle_stage": "Block 2: Laboratory Test Recorded",
                "batch_id": batch_id,
                "lab_name": lab["lab_name"],
                "inspector_name": lab["inspector_name"],
                "certificate_no": lab["certificate_no"],
                "purity_score": lab["purity_score"],
                "moisture_content": lab["moisture_content"],
                "nmr_profile": lab["nmr_profile"],
                "hmf_level": lab["hmf_level"],
                "lab_test_date": lab["lab_test_date"],
                "digital_signature": lab["digital_signature"]
            }
            b2 = honey_blockchain.add_block(b2_data, block_type="Block 2: Laboratory Test Recorded")
            database.save_block_to_db(b2)

        if "packaging" in item:
            pkg = item["packaging"]
            b3_data = {
                "event": "PACKAGING_RECORDED",
                "lifecycle_stage": "Block 3: Honey Packaging Recorded",
                "batch_id": batch_id,
                "packaging_plant": pkg["packaging_plant"],
                "packaging_supervisor": pkg["packaging_supervisor"],
                "jar_format": pkg["jar_format"],
                "net_weight": pkg["net_weight"],
                "tamper_seal_id": pkg["tamper_seal_id"],
                "lot_number": pkg["lot_number"],
                "packaging_date": pkg["packaging_date"]
            }
            b3 = honey_blockchain.add_block(b3_data, block_type="Block 3: Honey Packaging Recorded")
            database.save_block_to_db(b3)

        if "seller" in item:
            sel = item["seller"]
            b4_data = {
                "event": "SELLER_RECORDED",
                "lifecycle_stage": "Block 4: Seller Information Recorded",
                "batch_id": batch_id,
                "seller_name": sel["seller_name"],
                "store_location": sel["store_location"],
                "license_no": sel["license_no"],
                "shelf_arrival_date": sel["shelf_arrival_date"],
                "sale_price": sel["sale_price"],
                "retail_status": sel["retail_status"]
            }
            b4 = honey_blockchain.add_block(b4_data, block_type="Block 4: Seller Information Recorded")
            database.save_block_to_db(b4)

    database.update_setting("demo_seeded", "true")


# Clean Startup: No automatic seeding of demo data


# ==================== JINJA FILTERS & CONTEXT ====================

@app.template_filter("pretty_json")
def pretty_json(value):
    try:
        if isinstance(value, str):
            value = json.loads(value)
        return json.dumps(value, indent=2, sort_keys=True)
    except Exception:
        return str(value)


# Authentication Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access the HoneyChain dashboard.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


# ==================== 1. FIRST PAGE – WELCOME LANDING PAGE ====================

@app.route("/")
def index():
    """
    First Page — Honey Chain Welcome Page:
    - Honey-yellow and dark-brown color theme.
    - Honey Chain logo.
    - Project name: HONEY CHAIN.
    - Subtitle: Blockchain-Based Honey Traceability.
    - Short description: 'From Hive to Home — Every Drop Has a Story.'
    - Login, Register, and Explore Traceability buttons.
    """
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Dedicated Login Page with User and Admin Portals:
    - User Login (Beekeepers, Labs, Packagers, Sellers, Consumers)
    - Admin Login (Consortium Lead Auditors)
    - Google Sign-In support
    """
    mode = request.args.get("mode", "user").strip().lower()

    if session.get("user_id") and request.method == "GET":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()
        login_mode = request.form.get("login_mode", "user").strip().lower()

        user = database.authenticate_user(identifier, password)
        if user:
            # Enforce admin check if logging in through the Admin Portal
            if login_mode == "admin" and user["role"] != "admin":
                flash("Access denied: This portal is reserved for Consortium Lead Administrators only.", "error")
                return redirect(url_for("login", mode="admin"))

            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]
            flash(f"Welcome to HoneyChain, {user['full_name']}!", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials! Please check your username/email and password.", "error")
            return redirect(url_for("login", mode=login_mode))

    return render_template("login.html", mode=mode)


@app.route("/admin/login")
def admin_login():
    """Direct shortcut URL to the Admin Login Portal."""
    return redirect(url_for("login", mode="admin"))


@app.route("/auth/google")
@app.route("/google-login")
def google_login():
    """
    Simple Google SSO Sign-In:
    Seamless 1-click Google authentication for members and customers.
    """
    google_email = "google.honeyuser@gmail.com"
    google_name = "Google Verified Member"
    google_username = "google_user"

    user = database.get_user_by_email(google_email)
    if not user:
        from werkzeug.security import generate_password_hash
        database.create_user(
            username=google_username,
            email=google_email,
            password=generate_password_hash("GoogleAuth@2026"),
            full_name=google_name,
            role="consumer",
            organization="Google Authenticated Member"
        )
        user = database.get_user_by_login(google_username)

    session["user_id"] = user["id"]
    session["user_name"] = user["full_name"]
    session["user_email"] = user["email"]
    session["user_role"] = user["role"]
    session["auth_provider"] = "google"

    flash("Successfully authenticated with your Google account! Welcome to HoneyChain.", "success")
    return redirect(url_for("dashboard"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Create account option for HoneyChain consortium partners."""
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip() or (email.split("@")[0] if email else "")
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        role = request.form.get("role", "beekeeper").strip().lower()
        organization = request.form.get("organization", "").strip()

        if not full_name or not email or not password:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("register"))

        if confirm_password and password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        if database.get_user_by_email(email) or database.get_user_by_login(username):
            flash("An account with that email or username already exists. Please log in.", "error")
            return redirect(url_for("login"))

        user_id = database.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=role,
            organization=organization or f"{full_name} Apiary"
        )
        session["user_id"] = user_id
        session["user_name"] = full_name
        session["user_email"] = email
        session["user_role"] = role
        flash(f"Account registered successfully! Welcome to HONEYCHAIN, {full_name}.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = request.form.get("email", "").strip()
    new_password = request.form.get("new_password", "").strip()
    if not email or not new_password:
        flash("Please provide your email address and a new password.", "error")
        return redirect(url_for("login"))

    success = database.reset_password_by_email(email, new_password)
    if success:
        flash("Password reset successfully! Please log in with your new credentials.", "success")
    else:
        flash("Email address not found in consortium database.", "error")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))


# ==================== 2. DASHBOARD ====================

@app.route("/dashboard")
@login_required
def dashboard():
    from services.batch_service import BatchService
    from services.blockchain_service import BlockchainService
    from services.qr_service import QRService

    bs = BatchService(
        blockchain_service=BlockchainService(honey_blockchain),
        qr_service=QRService()
    )
    stats = bs.get_dashboard_counts()
    all_batches = database.get_all_batches()
    return render_template(
        "dashboard.html",
        active_page="dashboard",
        stats=stats,
        batches=all_batches
    )


# ==================== 4. SEPARATE FEATURE PAGES ====================

# --- Beekeeper Management (Step 1) ---
@app.route("/beekeeper", methods=["GET", "POST"])
@login_required
def beekeeper():
    if request.method == "POST":
        data = {
            "beekeeper_id": request.form.get("beekeeper_id", "").strip(),
            "name": request.form.get("name", "").strip(),
            "apiary_name": request.form.get("apiary_name", "").strip(),
            "location": request.form.get("location", "").strip(),
            "hives_count": request.form.get("hives_count", 50),
            "license_no": request.form.get("license_no", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "email": request.form.get("email", "").strip(),
            "honey_varieties": request.form.get("honey_varieties", "").strip()
        }
        database.add_beekeeper(data)
        database.add_notification(
            f"Step 1 Complete: Beekeeper Registered ({data['name']})",
            f"Apiary '{data['apiary_name']}' in {data['location']} registered. Ready for Step 2 (Batch Creation).",
            "info"
        )
        flash(f"Step 1 Complete! Beekeeper '{data['name']}' registered. Now proceed to Step 2 to register a honey batch.", "success")
        return redirect(url_for(
            "beekeeper",
            step_completed="1",
            beekeeper_id=data["beekeeper_id"],
            beekeeper_name=data["name"],
            apiary_name=data["apiary_name"],
            location=data["location"]
        ))

    beekeepers = database.get_beekeepers()
    suggested_id = f"BK-{random.randint(100, 999)}"
    return render_template(
        "beekeeper.html",
        active_page="beekeeper",
        beekeepers=beekeepers,
        suggested_id=suggested_id
    )


@app.route("/beekeeper/delete/<beekeeper_id>", methods=["POST"])
@login_required
def delete_beekeeper(beekeeper_id):
    database.delete_beekeeper(beekeeper_id)
    flash(f"Beekeeper {beekeeper_id} removed.", "info")
    return redirect(url_for("beekeeper"))


# --- Honey Batch Management (Step 2: Mints Block 1) ---
@app.route("/batches", methods=["GET", "POST"])
@login_required
def batches():
    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        product_name = request.form.get("product_name", "").strip()
        floral_source = request.form.get("floral_source", "").strip()
        apiary_name = request.form.get("apiary_name", "").strip()
        beekeeper_name = request.form.get("beekeeper_name", "").strip()
        origin_location = request.form.get("origin_location", "").strip()
        harvest_date = request.form.get("harvest_date", "").strip()
        comb_type = request.form.get("comb_type", "Pure Capped Comb").strip()
        extraction_method = request.form.get("extraction_method", "Unheated Cold Centrifugation").strip()
        quantity_kg = float(request.form.get("quantity_kg", 200.0) or 200.0)

        # 1. Mine Block 1 on Blockchain
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
            "timestamp": harvest_date
        }
        b1 = honey_blockchain.add_block(block1_data, block_type="Block 1: Honey Batch Registered")
        database.save_block_to_db(b1)

        # 2. Generate QR Code
        qr_file = generate_qr(batch_id, request.host_url)

        # 3. Store Batch in SQLite
        database.insert_batch({
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
            "qr_code_image": qr_file,
            "tx_hash": b1.hash,
            "block_index": b1.index,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        })

        database.add_notification(
            f"Step 2 Complete: Block 1 Mined ({batch_id})",
            f"{product_name} from {apiary_name} minted into Block 1. Proceed to Step 3 (Laboratory Testing).",
            "blockchain"
        )
        flash(f"Step 2 Complete! Batch {batch_id} registered and Block 1 minted. Now proceed to Step 3 (Laboratory Testing).", "success")
        return redirect(url_for("batches", step_completed="2", batch_id=batch_id))

    all_batches = database.get_all_batches()
    q = request.args.get("q", "").strip().lower()
    selected_stage = request.args.get("stage", "").strip()
    filtered = all_batches
    if q:
        filtered = [
            b for b in filtered
            if q in b.get("batch_id", "").lower()
            or q in b.get("product_name", "").lower()
            or q in b.get("beekeeper_name", "").lower()
            or q in b.get("floral_source", "").lower()
        ]
    if selected_stage:
        try:
            stg = int(selected_stage)
            filtered = [b for b in filtered if b.get("stage_num") == stg]
        except ValueError:
            pass

    return render_template(
        "batches/list.html",
        active_page="batches",
        batches=filtered,
        search_query=q,
        selected_stage=selected_stage
    )


# --- Laboratory Testing (Step 3: Mints Block 2) ---
@app.route("/laboratory", methods=["GET", "POST"])
@login_required
def laboratory():
    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        lab_name = request.form.get("lab_name", "").strip()
        inspector_name = request.form.get("inspector_name", "").strip()
        certificate_no = request.form.get("certificate_no", "").strip()
        purity_score = float(request.form.get("purity_score", 99.8) or 99.8)
        moisture_content = float(request.form.get("moisture_content", 16.4) or 16.4)
        nmr_profile = request.form.get("nmr_profile", "").strip()
        hmf_level = float(request.form.get("hmf_level", 4.2) or 4.2)
        lab_test_date = request.form.get("lab_test_date", "").strip()

        digital_sig = generate_lab_digital_signature(batch_id, certificate_no, purity_score, moisture_content, hmf_level)

        # 1. Mine Block 2 on Blockchain
        block2_data = {
            "event": "LAB_TEST_RECORDED",
            "lifecycle_stage": "Block 2: Laboratory Test Recorded",
            "batch_id": batch_id,
            "lab_name": lab_name,
            "inspector_name": inspector_name,
            "certificate_no": certificate_no,
            "purity_score": purity_score,
            "moisture_content": moisture_content,
            "nmr_profile": nmr_profile,
            "hmf_level": hmf_level,
            "lab_test_date": lab_test_date,
            "digital_signature": digital_sig
        }
        b2 = honey_blockchain.add_block(block2_data, block_type="Block 2: Laboratory Test Recorded")
        database.save_block_to_db(b2)

        # 2. Update Batch in SQLite
        fields = {
            "lab_name": lab_name,
            "inspector_name": inspector_name,
            "certificate_no": certificate_no,
            "purity_score": purity_score,
            "moisture_content": moisture_content,
            "nmr_profile": nmr_profile,
            "hmf_level": hmf_level,
            "lab_test_date": lab_test_date,
            "digital_signature": digital_sig,
            "signing_key_id": "KEY-LAB-AGROSCOPE-2026",
            "signature_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        database.update_batch_lifecycle_fields(batch_id, 2, "Block 2: Laboratory Test Recorded", fields)

        database.add_notification(
            f"Step 3 Complete: Block 2 Mined ({batch_id})",
            f"Batch {batch_id} verified {purity_score}% pure. Proceed to Step 4 (Packer Management).",
            "success"
        )
        flash(f"Step 3 Complete! Laboratory testing recorded and Block 2 mined. Now proceed to Step 4 (Packer Management).", "success")
        return redirect(url_for("laboratory", step_completed="3", batch_id=batch_id))

    all_batches = database.get_all_batches()
    tested_batches = [b for b in all_batches if b.get("purity_score")]
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    selected_batch_id = request.args.get("batch_id", "").strip().upper()
    suggested_cert_num = random.randint(1000, 9999)
    return render_template(
        "laboratory.html",
        active_page="laboratory",
        batches=all_batches,
        tested_batches=tested_batches,
        today_date=today_date,
        selected_batch_id=selected_batch_id,
        suggested_cert_num=suggested_cert_num
    )


# --- Packer Management (Step 4: Mints Block 3) ---
@app.route("/packer", methods=["GET", "POST"])
@login_required
def packer():
    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        packaging_plant = request.form.get("packaging_plant", "").strip()
        packaging_supervisor = request.form.get("packaging_supervisor", "").strip()
        jar_format = request.form.get("jar_format", "").strip()
        net_weight = request.form.get("net_weight", "").strip()
        tamper_seal_id = request.form.get("tamper_seal_id", "").strip()
        lot_number = request.form.get("lot_number", "").strip()
        packaging_date = request.form.get("packaging_date", "").strip()

        # 1. Mine Block 3 on Blockchain
        block3_data = {
            "event": "PACKAGING_RECORDED",
            "lifecycle_stage": "Block 3: Honey Packaging Recorded",
            "batch_id": batch_id,
            "packaging_plant": packaging_plant,
            "packaging_supervisor": packaging_supervisor,
            "jar_format": jar_format,
            "net_weight": net_weight,
            "tamper_seal_id": tamper_seal_id,
            "lot_number": lot_number,
            "packaging_date": packaging_date
        }
        b3 = honey_blockchain.add_block(block3_data, block_type="Block 3: Honey Packaging Recorded")
        database.save_block_to_db(b3)

        # 2. Update Batch in SQLite
        fields = {
            "packaging_plant": packaging_plant,
            "packaging_supervisor": packaging_supervisor,
            "jar_format": jar_format,
            "net_weight": net_weight,
            "tamper_seal_id": tamper_seal_id,
            "lot_number": lot_number,
            "packaging_date": packaging_date
        }
        database.update_batch_lifecycle_fields(batch_id, 3, "Block 3: Honey Packaging Recorded", fields)

        database.add_notification(
            f"Step 4 Complete: Block 3 Mined ({batch_id})",
            f"Batch {batch_id} sealed with tamper seal {tamper_seal_id}. Proceed to Step 5 (Seller Management).",
            "info"
        )
        flash(f"Step 4 Complete! Packaging and tamper seal recorded and Block 3 mined. Now proceed to Step 5 (Seller Management).", "success")
        return redirect(url_for("packer", step_completed="4", batch_id=batch_id))

    all_batches = database.get_all_batches()
    packaged_batches = [b for b in all_batches if b.get("tamper_seal_id")]
    suggested_seal_id = f"SEAL-CH-{datetime.now(timezone.utc).year}-{random.randint(1000, 9999)}"
    suggested_lot_num = random.randint(10, 99)
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    selected_batch_id = request.args.get("batch_id", "").strip().upper()
    return render_template(
        "packer.html",
        active_page="packer",
        batches=all_batches,
        packaged_batches=packaged_batches,
        suggested_seal_id=suggested_seal_id,
        suggested_lot_num=suggested_lot_num,
        today_date=today_date,
        selected_batch_id=selected_batch_id
    )


# --- Seller Management (Step 5: Mints Block 4) ---
@app.route("/seller", methods=["GET", "POST"])
@login_required
def seller():
    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        seller_name = request.form.get("seller_name", "").strip()
        store_location = request.form.get("store_location", "").strip()
        license_no = request.form.get("license_no", "").strip()
        sale_price = request.form.get("sale_price", "$48.00").strip()
        shelf_arrival_date = request.form.get("shelf_arrival_date", "").strip()

        # 1. Mine Block 4 on Blockchain
        block4_data = {
            "event": "SELLER_RECORDED",
            "lifecycle_stage": "Block 4: Seller Information Recorded",
            "batch_id": batch_id,
            "seller_name": seller_name,
            "store_location": store_location,
            "license_no": license_no,
            "shelf_arrival_date": shelf_arrival_date,
            "sale_price": sale_price,
            "retail_status": "On Shelf & Authenticated"
        }
        b4 = honey_blockchain.add_block(block4_data, block_type="Block 4: Seller Information Recorded")
        database.save_block_to_db(b4)

        # 2. Update Batch in SQLite
        fields = {
            "seller_name": seller_name,
            "store_location": store_location,
            "license_no": license_no,
            "shelf_arrival_date": shelf_arrival_date,
            "sale_price": sale_price,
            "retail_status": "On Shelf & Authenticated"
        }
        database.update_batch_lifecycle_fields(batch_id, 4, "Block 4: Seller Information Recorded", fields)

        database.add_notification(
            f"Step 5 Complete: Block 4 Mined ({batch_id})",
            f"Batch {batch_id} authenticated at {seller_name}. Supply chain journey 100% complete!",
            "success"
        )
        flash(f"Step 5 Complete! Batch {batch_id} authenticated on the retail shelf and Block 4 mined! Full supply chain complete.", "success")
        return redirect(url_for("seller", step_completed="5", batch_id=batch_id))

    all_batches = database.get_all_batches()
    seller_batches = [b for b in all_batches if b.get("seller_name")]
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    selected_batch_id = request.args.get("batch_id", "").strip().upper()
    return render_template(
        "seller.html",
        active_page="seller",
        batches=all_batches,
        seller_batches=seller_batches,
        today_date=today_date,
        selected_batch_id=selected_batch_id
    )


# --- Blockchain Records ---
@app.route("/blockchain")
@login_required
def blockchain_records():
    is_valid, validation_msg = honey_blockchain.is_chain_valid()
    return render_template(
        "blockchain.html",
        active_page="blockchain",
        all_blocks=honey_blockchain.chain,
        is_chain_valid=is_valid,
        validation_msg=validation_msg,
        chain_length=len(honey_blockchain.chain)
    )


@app.route("/blockchain/verify", methods=["POST"])
@login_required
def verify_chain_action():
    is_valid, validation_msg = honey_blockchain.is_chain_valid()
    if is_valid:
        flash(f"Verification Passed: {validation_msg}", "success")
    else:
        flash(f"Cryptographic Alert: {validation_msg}", "error")
    return redirect(url_for("blockchain_records"))


# --- QR Code Generator & Label Preview ---
@app.route("/qr-generator")
@app.route("/qr_code")
@app.route("/qr-code")
@login_required
def qr_generator():
    all_batches = database.get_all_batches()
    batch_id = request.args.get("batch_id", "").strip().upper() or request.args.get("custom_id", "").strip().upper()
    if not batch_id and all_batches:
        batch_id = all_batches[0]["batch_id"]

    batch_info = database.get_batch(batch_id) if batch_id else None
    qr_image = None
    if batch_id:
        qr_image = generate_qr(batch_id, request.host_url)

    from services.qr_service import QRService
    qr_svc = QRService()
    base_url = qr_svc.get_effective_base_url()
    trace_url = f"{base_url}/traceability?batch_id={batch_id}" if batch_id else ""

    return render_template(
        "qr_code.html",
        active_page="qr_generator",
        batches=all_batches,
        selected_batch_id=batch_id,
        qr_image=qr_image,
        batch_info=batch_info,
        trace_url=trace_url
    )


# --- Track Honey (5-Stage Supply Chain Traceability) ---
@app.route("/track-honey")
@app.route("/traceability")
def track_honey():
    all_batches = database.get_all_batches()
    batch_id = request.args.get("batch_id", "").strip().upper()
    if not batch_id and all_batches:
        batch_id = all_batches[0]["batch_id"]

    batch = database.get_batch(batch_id) if batch_id else None
    blocks_for_batch = [b for b in honey_blockchain.chain if b.data.get("batch_id") == batch_id]
    is_valid, validation_msg = honey_blockchain.is_chain_valid()

    return render_template(
        "traceability.html",
        active_page="track_honey",
        batch=batch,
        active_batch_id=batch_id,
        batches=all_batches,
        blocks=blocks_for_batch,
        is_chain_valid=is_valid,
        validation_msg=validation_msg
    )


@app.route("/traceability_view")
def traceability():
    return track_honey()


@app.route("/qr_code_hub")
def qr_code_hub():
    return qr_generator()


# --- Product Verification (Publicly accessible!) ---
@app.route("/verification")
def verification():
    batch_id = request.args.get("batch_id", "").strip().upper().lstrip("#")
    batch = database.get_batch(batch_id) if batch_id else None
    return render_template(
        "verification.html",
        active_page="verification",
        query_batch_id=batch_id,
        batch=batch
    )


# --- Reports & Exports ---
@app.route("/reports")
@login_required
def reports():
    all_batches = database.get_all_batches()
    return render_template(
        "reports.html",
        active_page="reports",
        batches=all_batches
    )


@app.route("/reports/export/csv")
@login_required
def export_reports_csv():
    batches = database.get_all_batches()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Batch ID", "Product Name", "Floral Source", "Apiary", "Beekeeper",
        "Location", "Harvest Date", "Quantity (kg)", "Stage Num", "Current Stage",
        "Purity Score (%)", "Moisture (%)", "Tamper Seal ID", "Retailer", "Retail Price"
    ])
    for b in batches:
        writer.writerow([
            b["batch_id"], b["product_name"], b["floral_source"], b["apiary_name"], b["beekeeper_name"],
            b["origin_location"], b["harvest_date"], b["quantity_kg"], b["stage_num"], b["current_stage"],
            b.get("purity_score", ""), b.get("moisture_content", ""), b.get("tamper_seal_id", ""),
            b.get("seller_name", ""), b.get("sale_price", "")
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=honeychain_provenance_report.csv"}
    )


@app.route("/reports/export/json")
@login_required
def export_reports_json():
    chain_data = [b.to_dict() for b in honey_blockchain.chain]
    return Response(
        json.dumps(chain_data, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=honeychain_ledger.json"}
    )


@app.route("/batch/<batch_id>/pdf")
def download_batch_pdf(batch_id):
    """Generates official PDF certificate for a honey batch using reportlab."""
    batch_id = batch_id.strip().upper().lstrip("#")
    pdf_bytes = pdf_generator.generate_provenance_pdf(batch_id)
    if not pdf_bytes:
        flash("Could not generate PDF: Batch record not found.", "error")
        return redirect(url_for("reports"))
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"HoneyChain_Certificate_{batch_id}.pdf"
    )


# --- Notifications ---
@app.route("/notifications")
@login_required
def notifications_page():
    notifications = database.get_notifications(50)
    database.mark_all_notifications_read()
    return render_template(
        "notifications.html",
        active_page="notifications",
        notifications=notifications
    )


@app.route("/notifications/clear", methods=["POST"])
@login_required
def clear_notifications_action():
    database.clear_all_notifications()
    flash("All notifications cleared.", "info")
    return redirect(url_for("notifications_page"))


# --- User Profile ---
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session.get("user_id")
    current_user = database.get_user_by_role(session.get("user_role", "admin"))
    all_users = database.get_all_users()
    for u in all_users:
        if str(u["id"]) == str(user_id) or u["email"] == session.get("user_email"):
            current_user = u
            break

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        organization = request.form.get("organization", "").strip()
        new_password = request.form.get("new_password", "").strip() or None

        if current_user:
            database.update_user_profile(current_user["id"], full_name, email, organization, new_password)
            session["user_name"] = full_name
            session["user_email"] = email
            flash("User profile updated successfully!", "success")
            return redirect(url_for("profile"))

    return render_template(
        "profile.html",
        active_page="profile",
        current_user=current_user or {}
    )


# --- Settings ---
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    if request.method == "POST":
        consortium_name = request.form.get("consortium_name", "").strip()
        blockchain_difficulty = request.form.get("blockchain_difficulty", "2").strip()
        currency = request.form.get("currency", "USD ($)").strip()
        qr_resolution = request.form.get("qr_resolution", "High (300 DPI)").strip()

        database.update_setting("consortium_name", consortium_name)
        database.update_setting("blockchain_difficulty", blockchain_difficulty)
        database.update_setting("currency", currency)
        database.update_setting("qr_resolution", qr_resolution)

        try:
            honey_blockchain.difficulty = int(blockchain_difficulty)
        except Exception:
            pass

        flash("Settings saved successfully!", "success")
        return redirect(url_for("settings_page"))

    settings_dict = database.get_all_settings()
    return render_template(
        "settings.html",
        active_page="settings",
        settings=settings_dict
    )


@app.route("/settings/reset-ledger", methods=["POST"])
@login_required
def reset_ledger_action():
    database.clear_all_data(keep_admin=True)
    honey_blockchain.chain = []
    genesis = honey_blockchain.create_genesis_block()
    honey_blockchain.chain = [genesis]
    database.save_block_to_db(genesis)
    database.update_setting("demo_seeded", "false")

    with_samples = request.form.get("with_samples") == "1"
    if with_samples:
        seed_sample_data_if_needed(force=True)
        flash("Blockchain ledger reset with standard sample demo batches.", "info")
    else:
        flash("Blockchain ledger reset to clean Genesis Block 0. Ready for new step-by-step workflow!", "success")
    return redirect(url_for("settings_page"))


@app.route("/sw.js")
def service_worker():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "sw.js", mimetype="application/javascript")


@app.route("/manifest.json")
def manifest():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "manifest.json", mimetype="application/manifest+json")


# ==================== COMPATIBILITY & API ENDPOINTS ====================

@app.route("/api/chain", methods=["GET"])
def api_chain():
    return jsonify({
        "success": True,
        "length": len(honey_blockchain.chain),
        "chain": [b.to_dict() for b in honey_blockchain.chain]
    })


@app.route("/api/verify-chain", methods=["GET"])
def api_verify_chain():
    is_valid, msg = honey_blockchain.is_chain_valid()
    return jsonify({
        "success": True,
        "is_valid": is_valid,
        "message": msg,
        "chain_length": len(honey_blockchain.chain)
    })


@app.route("/api/trace/<batch_id>", methods=["GET"])
def api_trace_batch(batch_id):
    batch = database.get_batch(batch_id.strip().upper())
    if not batch:
        return jsonify({"success": False, "error": f"Batch '{batch_id}' not found"}), 404
    history = [b.to_dict() for b in honey_blockchain.get_batch_history(batch_id)]
    return jsonify({
        "success": True,
        "batch": dict(batch),
        "blockchain_blocks": history
    })


@app.route("/api/network-info", methods=["GET"])
def api_network_info():
    port = int(os.environ.get("PORT", 5000))
    lan_ip = get_local_ip()
    return jsonify({
        "success": True,
        "lan_ip": lan_ip,
        "port": port,
        "local_url": f"http://127.0.0.1:{port}",
        "network_url": f"http://{lan_ip}:{port}",
        "hostname": socket.gethostname(),
        "status": "online"
    })


# ==================== MODULAR ENTERPRISE / MSME ROUTE MAP ====================

@app.route("/batches/create", methods=["GET", "POST"])
@app.route("/create_batch", methods=["GET", "POST"])
@login_required
def create_batch():
    from services.batch_service import BatchService
    from services.blockchain_service import BlockchainService
    from services.qr_service import QRService

    bs = BatchService(
        blockchain_service=BlockchainService(honey_blockchain),
        qr_service=QRService()
    )

    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        product_name = request.form.get("product_name", "").strip()
        floral_source = request.form.get("floral_source", "").strip()
        apiary_name = request.form.get("apiary_name", "").strip()
        beekeeper_name = request.form.get("beekeeper_name", "").strip()
        origin_location = request.form.get("origin_location", "").strip()
        harvest_date = request.form.get("harvest_date", "").strip()
        comb_type = request.form.get("comb_type", "Pure Capped Comb").strip()
        extraction_method = request.form.get("extraction_method", "Unheated Cold Centrifugation").strip()
        quantity_kg = request.form.get("quantity_kg", 200.0)

        batch, err = bs.create_batch(
            product_name=product_name,
            floral_source=floral_source,
            apiary_name=apiary_name,
            beekeeper_name=beekeeper_name,
            origin_location=origin_location,
            harvest_date=harvest_date,
            quantity_kg=quantity_kg,
            comb_type=comb_type,
            extraction_method=extraction_method,
            batch_id=batch_id
        )

        if err:
            flash(err, "error")
            return redirect(url_for("create_batch"))

        flash(f"Stage 1 Complete! Batch {batch.batch_id} registered and Block 1 mined on blockchain.", "success")
        return redirect(url_for("batch_details", batch_id=batch.batch_id))

    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    suggested_batch_id = f"HC-{datetime.now(timezone.utc).year}-{random.randint(1000, 9999)}"
    return render_template(
        "batches/create.html",
        active_page="batches",
        today_date=today_date,
        suggested_batch_id=suggested_batch_id
    )


@app.route("/batches/<batch_id>")
@app.route("/batch/<batch_id>")
@login_required
def batch_details(batch_id):
    clean_id = (batch_id or "").strip().upper().lstrip("#")
    batch = database.get_batch(clean_id)
    if not batch:
        flash(f"Batch '{clean_id}' not found.", "error")
        return redirect(url_for("batches"))
    return render_template("batches/details.html", active_page="batches", batch=batch)


@app.route("/stages/beekeeper", methods=["GET", "POST"])
@login_required
def stages_beekeeper():
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "add_beekeeper":
            data = {
                "beekeeper_id": f"BK-{random.randint(1000, 9999)}",
                "name": request.form.get("name", "").strip(),
                "apiary_name": request.form.get("apiary_name", "").strip(),
                "location": request.form.get("location", "").strip(),
                "hives_count": request.form.get("hives_count", 50),
                "phone": request.form.get("phone", "").strip(),
                "honey_varieties": request.form.get("honey_varieties", "").strip()
            }
            database.add_beekeeper(data)
            flash(f"Beekeeper '{data['name']}' registered successfully!", "success")
            return redirect(url_for("stages_beekeeper"))

    beekeepers = database.get_beekeepers()
    batches = database.get_all_batches()
    return render_template(
        "stages/beekeeper.html",
        active_page="beekeeper",
        beekeepers=beekeepers,
        batches=batches
    )


@app.route("/stages/laboratory", methods=["GET", "POST"])
@login_required
def stages_laboratory():
    from services.batch_service import BatchService
    from services.blockchain_service import BlockchainService
    from services.qr_service import QRService

    bs = BatchService(
        blockchain_service=BlockchainService(honey_blockchain),
        qr_service=QRService()
    )

    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        lab_name = request.form.get("lab_name", "").strip()
        inspector_name = request.form.get("inspector_name", "").strip()
        certificate_no = request.form.get("certificate_no", "").strip()
        purity_score = request.form.get("purity_score", 99.8)
        moisture_content = request.form.get("moisture_content", 16.4)
        hmf_level = request.form.get("hmf_level", 4.2)
        nmr_profile = request.form.get("nmr_profile", "").strip()
        lab_test_date = request.form.get("lab_test_date", "").strip()

        batch, err = bs.record_laboratory_test(
            batch_id=batch_id,
            lab_name=lab_name,
            inspector_name=inspector_name,
            certificate_no=certificate_no,
            purity_score=purity_score,
            moisture_content=moisture_content,
            hmf_level=hmf_level,
            nmr_profile=nmr_profile,
            lab_test_date=lab_test_date
        )

        if err:
            flash(err, "error")
            return redirect(url_for("stages_laboratory", batch_id=batch_id))

        flash(f"Stage 2 Complete! Lab assay recorded and Block 2 mined for batch {batch_id}.", "success")
        return redirect(url_for("batch_details", batch_id=batch_id))

    all_batches = database.get_all_batches()
    pending = [b for b in all_batches if b.get("stage_num", 1) == 1]
    tested = [b for b in all_batches if b.get("stage_num", 1) >= 2]
    selected_batch_id = request.args.get("batch_id", "").strip().upper()
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return render_template(
        "stages/laboratory.html",
        active_page="laboratory",
        pending_batches=pending,
        tested_batches=tested,
        selected_batch_id=selected_batch_id,
        today_date=today_date
    )


@app.route("/stages/packer", methods=["GET", "POST"])
@login_required
def stages_packer():
    from services.batch_service import BatchService
    from services.blockchain_service import BlockchainService
    from services.qr_service import QRService

    bs = BatchService(
        blockchain_service=BlockchainService(honey_blockchain),
        qr_service=QRService()
    )

    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        packaging_plant = request.form.get("packaging_plant", "").strip()
        packaging_supervisor = request.form.get("packaging_supervisor", "").strip()
        jar_format = request.form.get("jar_format", "500g Hexagonal Glass Jar").strip()
        net_weight = request.form.get("net_weight", "500g").strip()
        tamper_seal_id = request.form.get("tamper_seal_id", "").strip()
        lot_number = request.form.get("lot_number", "").strip()
        packaging_date = request.form.get("packaging_date", "").strip()

        batch, err = bs.record_packaging(
            batch_id=batch_id,
            packaging_plant=packaging_plant,
            packaging_supervisor=packaging_supervisor,
            jar_format=jar_format,
            net_weight=net_weight,
            tamper_seal_id=tamper_seal_id,
            lot_number=lot_number,
            packaging_date=packaging_date
        )

        if err:
            flash(err, "error")
            return redirect(url_for("stages_packer", batch_id=batch_id))

        flash(f"Stage 3 Complete! Packaging recorded and Block 3 mined for batch {batch_id}.", "success")
        return redirect(url_for("batch_details", batch_id=batch_id))

    all_batches = database.get_all_batches()
    pending = [b for b in all_batches if b.get("stage_num") == 2]
    packaged = [b for b in all_batches if b.get("stage_num", 1) >= 3]
    selected_batch_id = request.args.get("batch_id", "").strip().upper()
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return render_template(
        "stages/packer.html",
        active_page="packer",
        pending_batches=pending,
        packaged_batches=packaged,
        selected_batch_id=selected_batch_id,
        today_date=today_date
    )


@app.route("/stages/seller", methods=["GET", "POST"])
@login_required
def stages_seller():
    from services.batch_service import BatchService
    from services.blockchain_service import BlockchainService
    from services.qr_service import QRService

    bs = BatchService(
        blockchain_service=BlockchainService(honey_blockchain),
        qr_service=QRService()
    )

    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        seller_name = request.form.get("seller_name", "").strip()
        store_location = request.form.get("store_location", "").strip()
        license_no = request.form.get("license_no", "").strip()
        sale_price = request.form.get("sale_price", "$0.00").strip()
        shelf_arrival_date = request.form.get("shelf_arrival_date", "").strip()

        batch, err = bs.record_seller(
            batch_id=batch_id,
            seller_name=seller_name,
            store_location=store_location,
            license_no=license_no,
            sale_price=sale_price,
            shelf_arrival_date=shelf_arrival_date
        )

        if err:
            flash(err, "error")
            return redirect(url_for("stages_seller", batch_id=batch_id))

        flash(f"Stage 4 Complete! Retail arrival authenticated and Block 4 mined for batch {batch_id}.", "success")
        return redirect(url_for("batch_details", batch_id=batch_id))

    all_batches = database.get_all_batches()
    pending = [b for b in all_batches if b.get("stage_num") == 3]
    sellers = [b for b in all_batches if b.get("stage_num", 1) >= 4]
    selected_batch_id = request.args.get("batch_id", "").strip().upper()
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return render_template(
        "stages/seller.html",
        active_page="seller",
        pending_batches=pending,
        seller_batches=sellers,
        selected_batch_id=selected_batch_id,
        today_date=today_date
    )


@app.route("/qr/scan")
@login_required
def qr_scan():
    """Browser camera QR scanner with fallback manual batch lookup."""
    return render_template("qr/scan.html", active_page="qr_scan")


@app.route("/qr/generate")
@app.route("/qr/generate/<batch_id>")
@login_required
def qr_generate_page(batch_id=None):
    from services.qr_service import QRService
    qr_svc = QRService()

    all_batches = database.get_all_batches()
    clean_id = (batch_id or request.args.get("batch_id", "")).strip().upper()

    if not clean_id and all_batches:
        clean_id = all_batches[0]["batch_id"]

    batch = database.get_batch(clean_id) if clean_id else None
    if batch and not batch.get("qr_code_image"):
        qr_file = qr_svc.generate_batch_qr(clean_id)
        batch["qr_code_image"] = qr_file

    base_url = qr_svc.get_effective_base_url()
    trace_url = f"{base_url}/trace/{clean_id}" if clean_id else ""

    return render_template(
        "qr/generate.html",
        active_page="qr_generator",
        all_batches=all_batches,
        current_batch=batch,
        trace_url=trace_url
    )


@app.route("/blockchain/block/<int:block_index>")
@login_required
def block_details(block_index):
    from services.blockchain_service import BlockchainService
    bcs = BlockchainService(honey_blockchain)
    block = bcs.get_block_by_index(block_index)
    if not block:
        flash(f"Block #{block_index} does not exist on this ledger.", "error")
        return redirect(url_for("blockchain_records"))
    return render_template("blockchain/block_details.html", active_page="blockchain", block=block)


@app.route("/trace")
@app.route("/trace/<batch_id>")
def trace_route(batch_id=None):
    """
    Public customer honey traceability endpoint.
    No login required!
    """
    clean_id = (batch_id or request.args.get("batch_id", "")).strip().upper().lstrip("#")
    batch = database.get_batch(clean_id) if clean_id else None
    return render_template(
        "public/trace.html",
        batch=batch,
        searched_id=clean_id
    )


@app.route("/trace_batch/<batch_id>")
def trace_batch(batch_id):
    return redirect(url_for("trace_route", batch_id=batch_id))


@app.route("/export/batches/csv")
@login_required
def export_batches_csv():
    return export_reports_csv()


# ==================== ERROR HANDLERS ====================

@app.errorhandler(403)
def forbidden_error(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def not_found_error(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("errors/500.html"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    lan_ip = get_local_ip()
    refresh_batch_qrcodes()
    print("\n" + "=" * 66)
    print("   [HONEYCHAIN] Blockchain Honey Traceability System Online")
    print("   ==============================================================")
    print(f"   * Local Machine:     http://127.0.0.1:{port}")
    print(f"   * Network / Wi-Fi:   http://{lan_ip}:{port}  <-- Any device on Wi-Fi")
    print("   ==============================================================")
    print(f"   Listening on 0.0.0.0:{port}...")
    print("=" * 66 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True)
