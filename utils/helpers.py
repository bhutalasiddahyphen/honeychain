"""
HoneyChain General Helper Utilities
"""
import socket
import hmac
import hashlib
import json
import random
from datetime import datetime, timezone


def get_lan_ip():
    """Detects primary local LAN IPv4 address for multi-device network testing."""
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


def format_datetime(dt=None):
    """Returns ISO UTC timestamp string."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def generate_digital_signature(batch_id, cert_no, purity, moisture, hmf, secret="EUROFINS_CONSORTIUM_RSA_KEY_2026"):
    """Generates deterministic HMAC SHA-256 digital signature for lab assay."""
    payload = f"{batch_id}|{cert_no}|{purity}|{moisture}|{hmf}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"SIG-SHA256:{sig[:28].upper()}"


def safe_json_parse(json_str, default=None):
    """Safely parses JSON string or returns default."""
    if default is None:
        default = {}
    if not json_str:
        return default
    if isinstance(json_str, (dict, list)):
        return json_str
    try:
        return json.loads(json_str)
    except Exception:
        return default


def generate_batch_id():
    """Generates human-readable batch code: HC-YYYY-XXXX."""
    year = datetime.now().year
    rand_num = random.randint(1000, 9999)
    return f"HC-{year}-{rand_num}"

