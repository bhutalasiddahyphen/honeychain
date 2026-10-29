"""
HoneyChain QR Code Service
"""
import os
import qrcode
from utils.helpers import get_lan_ip


class QRService:
    """Handles QR code generation and resolution for customer honey traceability."""

    def __init__(self, output_dir=None, base_url=None):
        if output_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(project_root, "static", "qrcodes")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.base_url = base_url

    def get_effective_base_url(self):
        """Resolves base URL prioritizing environment variable, fallback to LAN IP."""
        if self.base_url:
            return self.base_url.rstrip("/")
        env_url = (os.environ.get("PUBLIC_BASE_URL") or os.environ.get("BASE_URL") or "").strip().rstrip("/")
        if env_url:
            return env_url
        port = int(os.environ.get("PORT", 5000))
        lan_ip = get_lan_ip()
        return f"http://{lan_ip}:{port}"

    def generate_batch_qr(self, batch_id, custom_base_url=None):
        """
        Generates high-contrast QR code pointing directly to public traceability endpoint /trace/<batch_id>.
        Returns the filename (e.g. HC-2026-1001.png).
        """
        clean_id = (batch_id or "").strip()
        base = (custom_base_url or self.get_effective_base_url()).rstrip("/")
        trace_url = f"{base}/trace/{clean_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=3,
        )
        qr.add_data(trace_url)
        qr.make(fit=True)

        # Brand color dark honey-brown (#4A2C16) fill, white background (#ffffff)
        img = qr.make_image(fill_color="#4A2C16", back_color="#ffffff")
        file_name = f"{clean_id}.png"
        file_path = os.path.join(self.output_dir, file_name)
        img.save(file_path)
        return file_name

    def get_qr_path(self, batch_id):
        """Returns disk path if exists, else None."""
        file_name = f"{batch_id.strip()}.png"
        file_path = os.path.join(self.output_dir, file_name)
        return file_path if os.path.exists(file_path) else None

