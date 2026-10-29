"""
HoneyChain Input Validators
"""
import re
from datetime import datetime


def validate_email(email):
    """Validates standard email address format."""
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


def validate_batch_id(batch_id):
    """Validates batch ID syntax (e.g. HC-2026-1001 or alphanumeric)."""
    if not batch_id or not isinstance(batch_id, str):
        return False
    cleaned = batch_id.strip()
    return bool(re.match(r"^[A-Za-z0-9\-_]{4,32}$", cleaned))


def validate_purity(purity_val):
    """Validates honey purity score (0.0 to 100.0%)."""
    try:
        val = float(purity_val)
        return 0.0 <= val <= 100.0
    except (TypeError, ValueError):
        return False


def validate_moisture(moisture_val):
    """Validates moisture percentage (standard table honey max 20.0%)."""
    try:
        val = float(moisture_val)
        return 5.0 <= val <= 35.0
    except (TypeError, ValueError):
        return False


def validate_hmf(hmf_val):
    """Validates Hydroxymethylfurfural (HMF) level in mg/kg."""
    try:
        val = float(hmf_val)
        return 0.0 <= val <= 200.0
    except (TypeError, ValueError):
        return False


def validate_harvest_date(date_str):
    """Validates date format YYYY-MM-DD and ensures it is a valid date."""
    if not date_str:
        return False
    try:
        d = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_password_strength(password):
    """Checks password meets minimum complexity requirements (at least 6 characters)."""
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""

