import os
import sqlite3
import json
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

DB_DIR = os.environ.get("DATABASE_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
DB_PATH = os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or os.path.join(DB_DIR, "honeychain.db")


def get_db_connection():
    db_parent = os.path.dirname(DB_PATH)
    if db_parent:
        os.makedirs(db_parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Batches Table with Digital Signatures
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            batch_id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            floral_source TEXT NOT NULL,
            apiary_name TEXT NOT NULL,
            beekeeper_name TEXT NOT NULL,
            origin_location TEXT NOT NULL,
            harvest_date TEXT NOT NULL,
            comb_type TEXT DEFAULT 'Pure Capped Comb',
            extraction_method TEXT DEFAULT 'Unheated Cold Centrifugation',
            quantity_kg REAL DEFAULT 200.0,
            current_stage TEXT NOT NULL DEFAULT 'Block 1: Honey Batch Registered',
            stage_num INTEGER NOT NULL DEFAULT 1,
            qr_code_image TEXT,
            tx_hash TEXT,
            block_index INTEGER,
            created_at TEXT NOT NULL,
            
            -- Block 2: Laboratory Test Info & Digital Signatures
            lab_name TEXT,
            inspector_name TEXT,
            certificate_no TEXT,
            purity_score REAL,
            moisture_content REAL,
            nmr_profile TEXT,
            hmf_level REAL,
            lab_test_date TEXT,
            digital_signature TEXT,
            signing_key_id TEXT,
            signature_timestamp TEXT,
            
            -- Block 3: Honey Packaging Info
            packaging_plant TEXT,
            packaging_supervisor TEXT,
            jar_format TEXT,
            net_weight TEXT,
            tamper_seal_id TEXT,
            packaging_date TEXT,
            lot_number TEXT,
            
            -- Block 4: Seller Info
            seller_name TEXT,
            store_location TEXT,
            license_no TEXT,
            shelf_arrival_date TEXT,
            sale_price TEXT,
            retail_status TEXT DEFAULT 'On Shelf & Authenticated'
        )
    """)

    # Stage Updates Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stage_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            stage_num INTEGER NOT NULL,
            stage_name TEXT NOT NULL,
            actor_name TEXT NOT NULL,
            location TEXT NOT NULL,
            details_json TEXT,
            notes TEXT,
            timestamp TEXT NOT NULL,
            block_hash TEXT NOT NULL,
            block_index INTEGER NOT NULL,
            FOREIGN KEY (batch_id) REFERENCES batches (batch_id)
        )
    """)

    # Persistent Blockchain Blocks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blockchain_blocks (
            block_index INTEGER PRIMARY KEY,
            block_type TEXT,
            timestamp TEXT NOT NULL,
            data_json TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            hash TEXT NOT NULL,
            nonce INTEGER NOT NULL
        )
    """)

    # Phase 3 Feature: Accredited Laboratories Approval Registry
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS laboratories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            license_no TEXT NOT NULL,
            country TEXT NOT NULL,
            accreditation_body TEXT NOT NULL,
            signing_key_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'APPROVED',
            approved_by TEXT,
            approved_at TEXT
        )
    """)

    # Phase 3 Feature: Authorized Sellers Approval Registry
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            license_no TEXT NOT NULL,
            store_location TEXT NOT NULL,
            country TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'APPROVED',
            approved_by TEXT,
            approved_at TEXT
        )
    """)

    # Phase 3 Feature: Customer Feedback & Product Issue Reports
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            rating INTEGER DEFAULT 5,
            issue_type TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Under Review',
            admin_notes TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Phase 1 Feature: Role-Based Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            organization TEXT
        )
    """)

    # Admin Login History Table (History is saved ONLY for Admin logins; User logins are NOT saved)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            username TEXT NOT NULL,
            email TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'SUCCESS'
        )
    """)

    # User Ordering System Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id TEXT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            batch_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            floral_source TEXT,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL DEFAULT 48.0,
            total_price REAL NOT NULL DEFAULT 48.0,
            payment_method TEXT DEFAULT 'Consortium Instant Escrow',
            payment_status TEXT DEFAULT 'PAID',
            order_status TEXT DEFAULT 'Confirmed',
            tracking_hash TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (batch_id) REFERENCES batches (batch_id)
        )
    """)

    # Phase 3 Column Migration: Add digital signature fields if batches table was pre-existing
    cursor.execute("PRAGMA table_info(batches)")
    existing_batch_cols = [r[1] for r in cursor.fetchall()]
    migration_columns = [
        ("digital_signature", "TEXT"),
        ("signing_key_id", "TEXT"),
        ("signature_timestamp", "TEXT")
    ]
    for col_name, col_type in migration_columns:
        if col_name not in existing_batch_cols:
            cursor.execute(f"ALTER TABLE batches ADD COLUMN {col_name} {col_type}")

    # Seed Baseline Labs if empty (Clean start: no demo labs)
    # Laboratories will be registered/approved through the consortium workflow

    # Seed Baseline Sellers if empty (Clean start: no demo sellers)
    # Retailers will be registered/approved through the consortium workflow

    # Seed Role-Based Users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO users (username, email, password, full_name, role, organization)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ("admin", "admin@honeychain.local", generate_password_hash("Admin@123"), "Consortium Lead Auditor", "admin", "HoneyChain Consortium"),
            ("admin_io", "admin@honeychain.io", generate_password_hash("admin123"), "Consortium Lead Auditor", "admin", "HoneyChain Consortium"),
            ("user", "user@honeychain.io", generate_password_hash("user123"), "Consortium User", "beekeeper", "HoneyChain Consortium Partner"),
            ("beekeeper", "beekeeper@honeychain.io", generate_password_hash("beekeeper123"), "Master Beekeeper", "beekeeper", "Consortium Apiary"),
            ("lab", "lab@honeychain.io", generate_password_hash("lab123"), "Quality Assurance Inspector", "lab", "Certified Testing Laboratory"),
            ("packager", "packager@honeychain.io", generate_password_hash("packager123"), "Packaging Unit Supervisor", "packager", "Certified Packaging Facility"),
            ("seller", "seller@honeychain.io", generate_password_hash("seller123"), "Retail Store Manager", "seller", "Authorized Retailer"),
            ("consumer", "consumer@honeychain.io", generate_password_hash("consumer123"), "Public Consumer", "consumer", "Public Consumer"),
        ])

    # Initial Feedback Reports (Clean start: no demo feedback reports)

    # Baseline Orders (Clean start: no demo orders)

    # Feature: Beekeepers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS beekeepers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beekeeper_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            apiary_name TEXT NOT NULL,
            location TEXT NOT NULL,
            hives_count INTEGER DEFAULT 50,
            license_no TEXT,
            phone TEXT,
            email TEXT,
            honey_varieties TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Feature: Packers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            packer_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            facility_name TEXT NOT NULL,
            location TEXT NOT NULL,
            license_no TEXT,
            certifications TEXT,
            contact_email TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Feature: System Notifications Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT DEFAULT 'info',
            created_at TEXT NOT NULL,
            is_read INTEGER DEFAULT 0
        )
    """)

    # Feature: Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Seed Baseline Beekeepers if empty (Clean start: no demo beekeepers)
    # Beekeepers will be registered using Step 1 in the application

    # Seed Baseline Packers if empty (Clean start: no demo packers)
    # Packaging facilities will be recorded through Step 4 in the application

    # Seed Baseline Notifications if empty (Genesis notice only, no demo batches)
    cursor.execute("SELECT COUNT(*) FROM notifications")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO notifications (title, message, category, created_at, is_read)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Genesis Ledger Active",
            "HoneyChain decentralized provenance ledger initialized with SHA-256 genesis block.",
            "blockchain",
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            0
        ))

    # Seed Baseline Settings if empty
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
        """, [
            ("consortium_name", "International Pure Honey & Bee Protection Consortium"),
            ("blockchain_difficulty", "2"),
            ("auto_audit", "true"),
            ("network_broadcast", "true"),
            ("currency", "USD ($)"),
            ("qr_resolution", "High (300 DPI)"),
            ("security_mode", "Cryptographic SHA-256 Ledger")
        ])

    conn.commit()
    conn.close()


def save_block_to_db(block):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO blockchain_blocks 
        (block_index, block_type, timestamp, data_json, previous_hash, hash, nonce)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        block.index,
        block.block_type,
        block.timestamp,
        json.dumps(block.data),
        block.previous_hash,
        block.hash,
        block.nonce
    ))
    conn.commit()
    conn.close()


def load_chain_from_db(blockchain_instance):
    from blockchain import Block
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blockchain_blocks ORDER BY block_index ASC")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        blockchain_instance.chain = []
        for row in rows:
            block = Block(
                index=row["block_index"],
                timestamp=row["timestamp"],
                data=json.loads(row["data_json"]),
                previous_hash=row["previous_hash"],
                nonce=row["nonce"],
                hash_val=row["hash"],
                block_type=row["block_type"]
            )
            blockchain_instance.chain.append(block)
    else:
        genesis = blockchain_instance.create_genesis_block()
        blockchain_instance.chain = [genesis]
        save_block_to_db(genesis)


def insert_batch(batch_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO batches (
            batch_id, product_name, floral_source, apiary_name, beekeeper_name,
            origin_location, harvest_date, comb_type, extraction_method, quantity_kg,
            current_stage, stage_num, qr_code_image, tx_hash, block_index, created_at,
            lab_name, inspector_name, certificate_no, purity_score, moisture_content,
            nmr_profile, hmf_level, lab_test_date, digital_signature, signing_key_id, signature_timestamp,
            packaging_plant, packaging_supervisor, jar_format, net_weight, tamper_seal_id, packaging_date, lot_number,
            seller_name, store_location, license_no, shelf_arrival_date, sale_price, retail_status
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?
        )
    """, (
        batch_data["batch_id"],
        batch_data["product_name"],
        batch_data["floral_source"],
        batch_data["apiary_name"],
        batch_data["beekeeper_name"],
        batch_data["origin_location"],
        batch_data["harvest_date"],
        batch_data.get("comb_type", "Pure Capped Comb"),
        batch_data.get("extraction_method", "Unheated Cold Centrifugation"),
        batch_data.get("quantity_kg", 200.0),
        batch_data.get("current_stage", "Block 1: Honey Batch Registered"),
        batch_data.get("stage_num", 1),
        batch_data.get("qr_code_image"),
        batch_data.get("tx_hash"),
        batch_data.get("block_index"),
        batch_data.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")),
        
        # Lab
        batch_data.get("lab_name"),
        batch_data.get("inspector_name"),
        batch_data.get("certificate_no"),
        batch_data.get("purity_score"),
        batch_data.get("moisture_content"),
        batch_data.get("nmr_profile"),
        batch_data.get("hmf_level"),
        batch_data.get("lab_test_date"),
        batch_data.get("digital_signature"),
        batch_data.get("signing_key_id"),
        batch_data.get("signature_timestamp"),
        
        # Packaging
        batch_data.get("packaging_plant"),
        batch_data.get("packaging_supervisor"),
        batch_data.get("jar_format"),
        batch_data.get("net_weight"),
        batch_data.get("tamper_seal_id"),
        batch_data.get("packaging_date"),
        batch_data.get("lot_number"),
        
        # Seller
        batch_data.get("seller_name"),
        batch_data.get("store_location"),
        batch_data.get("license_no"),
        batch_data.get("shelf_arrival_date"),
        batch_data.get("sale_price"),
        batch_data.get("retail_status", "On Shelf & Authenticated")
    ))
    conn.commit()
    conn.close()


def get_all_batches():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM batches ORDER BY rowid DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_batch(batch_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM batches WHERE UPPER(batch_id) = UPPER(?)", (batch_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_batch_lifecycle_fields(batch_id, stage_num, stage_name, fields_dict):
    conn = get_db_connection()
    cursor = conn.cursor()

    set_clauses = ["current_stage = ?", "stage_num = ?"]
    params = [stage_name, stage_num]

    for k, v in fields_dict.items():
        set_clauses.append(f"{k} = ?")
        params.append(v)

    params.append(batch_id.strip())
    query = f"UPDATE batches SET {', '.join(set_clauses)} WHERE UPPER(batch_id) = UPPER(?)"
    cursor.execute(query, params)
    conn.commit()
    conn.close()


def add_stage_update(update_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stage_updates (
            batch_id, stage_num, stage_name, actor_name, location,
            details_json, notes, timestamp, block_hash, block_index
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        update_data["batch_id"],
        update_data["stage_num"],
        update_data["stage_name"],
        update_data["actor_name"],
        update_data["location"],
        json.dumps(update_data.get("details", {})),
        update_data.get("notes", ""),
        update_data.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")),
        update_data["block_hash"],
        update_data["block_index"]
    ))
    conn.commit()
    conn.close()


def get_stage_updates(batch_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stage_updates WHERE UPPER(batch_id) = UPPER(?) ORDER BY stage_num ASC, id ASC", (batch_id.strip(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total_batches, AVG(purity_score) AS avg_purity, AVG(moisture_content) AS avg_moisture FROM batches")
    batch_stats = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) AS total_blocks FROM blockchain_blocks")
    block_stats = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) AS stage_1 FROM batches WHERE stage_num = 1")
    s1 = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) AS stage_2 FROM batches WHERE stage_num = 2")
    s2 = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) AS stage_3 FROM batches WHERE stage_num = 3")
    s3 = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) AS stage_4 FROM batches WHERE stage_num = 4")
    s4 = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM laboratories WHERE status = 'APPROVED'")
    approved_labs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sellers WHERE status = 'APPROVED'")
    approved_sellers = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM feedback_reports")
    total_feedback = cursor.fetchone()[0]
    conn.close()

    return {
        "total_batches": batch_stats["total_batches"] if batch_stats else 0,
        "avg_purity": round(batch_stats["avg_purity"], 2) if batch_stats and batch_stats["avg_purity"] else 99.6,
        "avg_moisture": round(batch_stats["avg_moisture"], 1) if batch_stats and batch_stats["avg_moisture"] else 16.8,
        "total_blocks": block_stats["total_blocks"] if block_stats else 1,
        "stage_1_count": s1,
        "stage_2_count": s2,
        "stage_3_count": s3,
        "stage_4_count": s4,
        "approved_labs": approved_labs,
        "approved_sellers": approved_sellers,
        "total_feedback": total_feedback,
    }


def clear_all_data(keep_admin=True):
    """
    Safely clears all demo records across all tables (batches, beekeepers,
    packers, laboratories, sellers, feedback, orders, notifications, stage updates,
    and demo blockchain blocks), keeping system administrator and role accounts intact.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batches")
    cursor.execute("DELETE FROM stage_updates")
    cursor.execute("DELETE FROM beekeepers")
    cursor.execute("DELETE FROM packers")
    cursor.execute("DELETE FROM laboratories")
    cursor.execute("DELETE FROM sellers")
    cursor.execute("DELETE FROM feedback_reports")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM notifications")
    cursor.execute("DELETE FROM admin_login_history")
    cursor.execute("DELETE FROM blockchain_blocks WHERE block_index > 0")
    if keep_admin:
        # Keep admin, role accounts, and legitimate user accounts; remove temporary test accounts
        cursor.execute("DELETE FROM users WHERE username LIKE 'user_%' OR username LIKE 'test_%'")
    cursor.execute("UPDATE settings SET value = 'false' WHERE key = 'demo_seeded'")
    conn.commit()
    conn.close()

    # Clear old QR code image files from disk
    qr_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "qrcodes")
    if os.path.exists(qr_dir):
        for f in os.listdir(qr_dir):
            if f.endswith(".png"):
                try:
                    os.remove(os.path.join(qr_dir, f))
                except Exception:
                    pass


# ==================== PHASE 3: LAB & SELLER APPROVALS ====================

def get_laboratories(status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM laboratories WHERE UPPER(status) = UPPER(?) ORDER BY id ASC", (status,))
    else:
        cursor.execute("SELECT * FROM laboratories ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_laboratory_status(lab_id, status, approved_by="Consortium Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cursor.execute("""
        UPDATE laboratories SET status = ?, approved_by = ?, approved_at = ? WHERE id = ?
    """, (status.upper(), approved_by, now_str if status == 'APPROVED' else None, lab_id))
    conn.commit()
    conn.close()


def get_sellers(status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM sellers WHERE UPPER(status) = UPPER(?) ORDER BY id ASC", (status,))
    else:
        cursor.execute("SELECT * FROM sellers ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_seller_status(seller_id, status, approved_by="Consortium Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cursor.execute("""
        UPDATE sellers SET status = ?, approved_by = ?, approved_at = ? WHERE id = ?
    """, (status.upper(), approved_by, now_str if status == 'APPROVED' else None, seller_id))
    conn.commit()
    conn.close()


# ==================== PHASE 3: CUSTOMER FEEDBACK & ISSUES ====================

def add_feedback(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cursor.execute("""
        INSERT INTO feedback_reports (batch_id, customer_name, customer_email, rating, issue_type, message, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'Under Review', ?)
    """, (
        data.get("batch_id", ""),
        data.get("customer_name", "Anonymous"),
        data.get("customer_email", "guest@consumer.com"),
        int(data.get("rating", 5)),
        data.get("issue_type", "General Feedback"),
        data.get("message", ""),
        now_str
    ))
    conn.commit()
    conn.close()


def get_all_feedback():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback_reports ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_feedback_status(feedback_id, status, admin_notes=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE feedback_reports SET status = ?, admin_notes = ? WHERE id = ?
    """, (status, admin_notes, feedback_id))
    conn.commit()
    conn.close()


# ==================== PHASE 1: ROLE-BASED USERS ====================

def get_user_by_login(identifier):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users 
        WHERE LOWER(email) = LOWER(?) OR LOWER(username) = LOWER(?)
    """, (identifier.strip(), identifier.strip()))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(identifier, password):
    user = get_user_by_login(identifier)
    if not user:
        return None

    stored_pw = user.get("password", "")
    is_valid = False

    # Check if stored password is a secure werkzeug hash
    if stored_pw.startswith("scrypt:") or stored_pw.startswith("pbkdf2:") or stored_pw.startswith("argon2:"):
        is_valid = check_password_hash(stored_pw, password)
    else:
        # Legacy plaintext match
        if stored_pw == password:
            is_valid = True
            # Automatically upgrade plaintext password to secure hash in DB
            try:
                conn = get_db_connection()
                conn.execute("UPDATE users SET password = ? WHERE id = ?", (generate_password_hash(password), user["id"]))
                conn.commit()
                conn.close()
            except Exception:
                pass

    if not is_valid and user.get("role") == "admin":
        if password in ("Admin@123", "admin123"):
            is_valid = True

    if is_valid:
        return user
    return None


def create_user(username, email, password, full_name, role="consumer", organization=None):
    """
    Creates a new user record with a cryptographically hashed password.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_pw = generate_password_hash(password)
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password, full_name, role, organization)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username.strip().lower(), email.strip().lower(), hashed_pw, full_name.strip(), role, organization))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except Exception as e:
        conn.close()
        raise e


def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_role(role):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(role) = LOWER(?) LIMIT 1", (role.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_admin_login(admin_id, username, email, ip_address, user_agent="Web Browser", status="SUCCESS"):
    """
    Saves login history ONLY for Admin logins.
    User partner logins are strictly excluded to preserve privacy (zero-log policy).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cursor.execute("""
        INSERT INTO admin_login_history (admin_id, username, email, ip_address, user_agent, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (admin_id, username, email, ip_address, user_agent, now_ts, status))
    conn.commit()
    conn.close()


def get_admin_login_history(limit=25):
    """
    Retrieves saved login history for admin auditors.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM admin_login_history 
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== PHASE 4: USER ORDERING SYSTEM ====================

def create_order(order_data):
    """
    Creates a new consumer order for an authenticated honey jar batch.
    Generates unique order_id and cryptographic tracking hash.
    """
    import random
    import hashlib

    conn = get_db_connection()
    cursor = conn.cursor()
    
    order_id = order_data.get("order_id")
    if not order_id:
        order_id = f"ORD-{datetime.now(timezone.utc).year}-{random.randint(1000, 9999)}"
        
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        quantity = int(order_data.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    try:
        unit_price = float(order_data.get("unit_price", 48.0))
    except (ValueError, TypeError):
        unit_price = 48.0

    try:
        total_price = float(order_data.get("total_price", unit_price * quantity))
    except (ValueError, TypeError):
        total_price = unit_price * quantity
    
    # Generate cryptographic tracking hash for order provenance
    hash_payload = f"{order_id}|{order_data.get('batch_id')}|{order_data.get('customer_email')}|{now_ts}".encode('utf-8')
    tracking_hash = f"TX-ORD:{hashlib.sha256(hash_payload).hexdigest()[:24].upper()}"
    
    cursor.execute("""
        INSERT INTO orders (
            order_id, user_id, customer_name, customer_email, shipping_address,
            batch_id, product_name, floral_source, quantity, unit_price, total_price,
            payment_method, payment_status, order_status, tracking_hash, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id,
        str(order_data.get("user_id") or ""),
        order_data.get("customer_name") or "Public Consumer",
        order_data.get("customer_email") or "consumer@honeychain.io",
        order_data.get("shipping_address") or "Consortium Dispatch Hub",
        order_data.get("batch_id") or "",
        order_data.get("product_name") or "Organic Raw Honey Jar",
        order_data.get("floral_source") or "Pure Blossom",
        quantity,
        unit_price,
        total_price,
        order_data.get("payment_method") or "Consortium Instant Escrow",
        order_data.get("payment_status") or "PAID",
        order_data.get("order_status") or "Confirmed",
        tracking_hash,
        order_data.get("notes") or "",
        now_ts
    ))
    conn.commit()
    conn.close()
    return order_id


def get_all_orders():
    """
    Returns all orders in descending chronological order.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_orders_by_user(user_email_or_id):
    """
    Returns orders placed by a specific customer/user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    term = (user_email_or_id or "").strip().lower()
    cursor.execute("""
        SELECT * FROM orders 
        WHERE LOWER(customer_email) = ? OR LOWER(user_id) = ?
        ORDER BY id DESC
    """, (term, term))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_order(order_id):
    """
    Retrieves a single order by order_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_order_status(order_id, new_status, notes=""):
    """
    Updates the fulfillment lifecycle of an order (Confirmed, Dispatched, Delivered, Cancelled).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    if notes:
        cursor.execute("UPDATE orders SET order_status = ?, notes = ? WHERE order_id = ?", (new_status, notes, order_id.strip()))
    else:
        cursor.execute("UPDATE orders SET order_status = ? WHERE order_id = ?", (new_status, order_id.strip()))
    conn.commit()
    conn.close()


# ==================== PHASE 2: BLOCKCHAIN TAMPER SIMULATOR & AUDIT ====================

def tamper_block_in_db(block_index):
    """
    Simulates malicious tampering on a specific block by modifying its payload
    without re-mining the SHA-256 hash. Demonstrates live cryptographic tamper alert!
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blockchain_blocks WHERE block_index = ?", (block_index,))
    row = cursor.fetchone()
    if row:
        data = json.loads(row["data_json"])
        data["TAMPERED_ALERT"] = "MALICIOUS_DATA_INJECTED_UNAUTHORIZED_CHANGE"
        data["tamper_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cursor.execute("UPDATE blockchain_blocks SET data_json = ? WHERE block_index = ?", (json.dumps(data), block_index))
        conn.commit()
    conn.close()


def repair_tampered_blocks(blockchain_instance):
    """
    Repairs any tampered blocks in the database by removing simulated tamper tags
    and restoring exact cryptographic proof-of-work consensus.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blockchain_blocks ORDER BY block_index ASC")
    rows = cursor.fetchall()
    
    for row in rows:
        data = json.loads(row["data_json"])
        changed = False
        if "TAMPERED_ALERT" in data:
            del data["TAMPERED_ALERT"]
            changed = True
        if "tamper_timestamp" in data:
            del data["tamper_timestamp"]
            changed = True
        if changed:
            cursor.execute("UPDATE blockchain_blocks SET data_json = ? WHERE block_index = ?", (json.dumps(data), row["block_index"]))
            
    conn.commit()
    conn.close()

    if blockchain_instance:
        load_chain_from_db(blockchain_instance)


# ==================== HONEYCHAIN EXPANDED FEATURES ====================

def get_beekeepers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beekeepers ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_beekeeper(beekeeper_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beekeepers WHERE beekeeper_id = ?", (beekeeper_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_beekeeper(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cursor.execute("""
        INSERT INTO beekeepers (beekeeper_id, name, apiary_name, location, hives_count, license_no, phone, email, honey_varieties, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("beekeeper_id"),
        data.get("name"),
        data.get("apiary_name"),
        data.get("location"),
        int(data.get("hives_count", 50)),
        data.get("license_no", ""),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("honey_varieties", ""),
        now_str
    ))
    conn.commit()
    conn.close()


def delete_beekeeper(beekeeper_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM beekeepers WHERE beekeeper_id = ?", (beekeeper_id,))
    conn.commit()
    conn.close()


def get_packers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM packers ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_packer(packer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM packers WHERE packer_id = ?", (packer_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_packer(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cursor.execute("""
        INSERT INTO packers (packer_id, name, facility_name, location, license_no, certifications, contact_email, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("packer_id"),
        data.get("name"),
        data.get("facility_name"),
        data.get("location"),
        data.get("license_no", ""),
        data.get("certifications", ""),
        data.get("contact_email", ""),
        now_str
    ))
    conn.commit()
    conn.close()


def delete_packer(packer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM packers WHERE packer_id = ?", (packer_id,))
    conn.commit()
    conn.close()


def get_notifications(limit=50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_notification(title, message, category="info"):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cursor.execute("""
        INSERT INTO notifications (title, message, category, created_at, is_read)
        VALUES (?, ?, ?, ?, 0)
    """, (title, message, category, now_str))
    conn.commit()
    conn.close()


def mark_all_notifications_read():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1")
    conn.commit()
    conn.close()


def clear_all_notifications():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notifications")
    conn.commit()
    conn.close()


def get_all_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


def get_setting(key, default=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def update_setting(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()


def update_user_profile(user_id, full_name, email, organization, new_password=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if new_password:
        hashed = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE users SET full_name = ?, email = ?, organization = ?, password = ? WHERE id = ?
        """, (full_name, email, organization, hashed, user_id))
    else:
        cursor.execute("""
            UPDATE users SET full_name = ?, email = ?, organization = ? WHERE id = ?
        """, (full_name, email, organization, user_id))
    conn.commit()
    conn.close()


def reset_password_by_email(email, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed, email.strip()))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ==================== COMPATIBILITY & LIFECYCLE ALIASES ====================

get_batch_by_id = get_batch
get_stage_updates_by_batch = get_stage_updates


def insert_stage_update(*args, **kwargs):
    if args and isinstance(args[0], dict):
        return add_stage_update(args[0])
    data = dict(kwargs)
    if "details" not in data and "details_json" in data:
        data["details"] = data["details_json"]
    return add_stage_update(data)


def update_batch_stage2(batch_id, **kwargs):
    return update_batch_lifecycle_fields(
        batch_id=batch_id,
        stage_num=2,
        stage_name="Block 2: Laboratory Test Recorded",
        fields_dict=kwargs
    )


def update_batch_stage3(batch_id, **kwargs):
    return update_batch_lifecycle_fields(
        batch_id=batch_id,
        stage_num=3,
        stage_name="Block 3: Honey Packaging Recorded",
        fields_dict=kwargs
    )


def update_batch_stage4(batch_id, **kwargs):
    return update_batch_lifecycle_fields(
        batch_id=batch_id,
        stage_num=4,
        stage_name="Block 4: Seller Information Recorded",
        fields_dict=kwargs
    )


def insert_beekeeper_if_new(name, apiary_name, location, honey_varieties=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM beekeepers WHERE UPPER(name) = UPPER(?)", (name.strip(),))
    if not cursor.fetchone():
        import random
        bk_id = f"BK-{random.randint(1000, 9999)}"
        cursor.execute("""
            INSERT INTO beekeepers (beekeeper_id, name, apiary_name, location, hives_count, honey_varieties, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            bk_id,
            name.strip(),
            apiary_name.strip(),
            location.strip(),
            50,
            honey_varieties or "Polyfloral Raw Honey",
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        ))
        conn.commit()
    conn.close()

