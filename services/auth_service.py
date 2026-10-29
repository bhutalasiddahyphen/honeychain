"""
HoneyChain Authentication Service
"""
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import database
from models.user import User
from utils.validators import validate_email, validate_password_strength


class AuthService:
    """Manages authentication, session authorization, and user registration."""

    @staticmethod
    def authenticate(identifier, password, ip_address="127.0.0.1", user_agent=""):
        """
        Authenticates user with email or username.
        Logs admin login attempts to admin_login_history.
        """
        if not identifier or not password:
            return None, "Email or username and password are required."

        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = ? OR username = ? COLLATE NOCASE",
            (identifier.strip(), identifier.strip()),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None, "Invalid credentials. Please verify your email/username and password."

        user = User.from_row(row)
        if not user.verify_password(password):
            conn.close()
            return None, "Invalid credentials. Please verify your email/username and password."

        # If user is admin, record login audit history
        if user.role.lower() == "admin":
            try:
                cursor.execute(
                    """
                    INSERT INTO admin_login_history (admin_id, username, email, ip_address, user_agent, timestamp, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user.id,
                        user.username,
                        user.email,
                        ip_address,
                        user_agent,
                        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "SUCCESS",
                    ),
                )
                conn.commit()
            except Exception:
                pass

        conn.close()
        return user, None

    @staticmethod
    def register_user(full_name, email, password, confirm_password, role="beekeeper", organization="", phone="", allow_admin=False):
        """
        Registers a new user with validation and secure password hashing.
        """
        full_name = (full_name or "").strip()
        email = (email or "").strip().lower()
        role = (role or "beekeeper").strip().lower()
        organization = (organization or "").strip()
        phone = (phone or "").strip()

        if not full_name:
            return None, "Full name is required."
        if not email or not validate_email(email):
            return None, "A valid email address is required."
        if not password:
            return None, "Password is required."
        if password != confirm_password:
            return None, "Passwords do not match."

        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            return None, msg

        if role == "admin" and not allow_admin:
            role = "beekeeper"

        username = email.split("@")[0]

        conn = database.get_db_connection()
        cursor = conn.cursor()

        # Check existing user
        cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
        if cursor.fetchone():
            conn.close()
            return None, f"An account with email '{email}' already exists."

        hashed_pw = generate_password_hash(password)
        cursor.execute(
            """
            INSERT INTO users (username, email, password, full_name, role, organization)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, email, hashed_pw, full_name, role, organization),
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        user = User(
            id=user_id,
            username=username,
            email=email,
            password=hashed_pw,
            full_name=full_name,
            role=role,
            organization=organization,
            phone=phone,
        )
        return user, None

    @staticmethod
    def get_user_by_id(user_id):
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return User.from_row(row) if row else None

    @staticmethod
    def seed_default_admin(email="admin@honeychain.local", password="Admin@123"):
        """
        Seeds default demonstration administrator if not already present.
        """
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE email = ? COLLATE NOCASE", (email.lower(),))
        existing_by_email = cursor.fetchone()
        hashed_pw = generate_password_hash(password)

        if existing_by_email:
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, existing_by_email["id"]))
            conn.commit()
        else:
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            admin_row = cursor.fetchone()
            if admin_row:
                cursor.execute(
                    "UPDATE users SET email = ?, password = ?, full_name = ? WHERE id = ?",
                    (email.lower(), hashed_pw, "HoneyChain Administrator", admin_row["id"])
                )
                conn.commit()
            else:
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password, full_name, role, organization)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("admin", email.lower(), hashed_pw, "HoneyChain Administrator", "admin", "HoneyChain Consortium"),
                )
                conn.commit()
        conn.close()
