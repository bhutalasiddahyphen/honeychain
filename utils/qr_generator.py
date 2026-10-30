"""
HoneyChain QR Code Generator Utility
"""
import os
import qrcode
from utils.helpers import get_lan_ip


def generate_qr_code(batch_id, base_url=None, output_dir=None):
    """
    Generates a high-contrast consumer QR code pointing to batch traceability.
    Returns the filename of the generated QR code (e.g. HONEY2026001.png).
    """
    clean_id = (batch_id or "").strip()
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "qrcodes")
    os.makedirs(output_dir, exist_ok=True)

    if not base_url:
        env_url = (os.environ.get("PUBLIC_BASE_URL") or os.environ.get("BASE_URL") or "").strip().rstrip("/")
        if env_url:
            base_url = env_url
        else:
            port = int(os.environ.get("PORT", 5000))
            lan_ip = get_lan_ip()
            base_url = f"http://{lan_ip}:{port}"

    trace_url = f"{base_url.rstrip('/')}/traceability?batch_id={clean_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(trace_url)
    qr.make(fit=True)

    # Brand color: Deep Honey Brown (#4A2C16) on White (#FFFFFF)
    img = qr.make_image(fill_color="#4A2C16", back_color="#ffffff")
    filename = f"{clean_id}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    return filename


def get_qr_filepath(batch_id, output_dir=None):
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "qrcodes")
    filepath = os.path.join(output_dir, f"{batch_id.strip()}.png")
    return filepath if os.path.exists(filepath) else None
