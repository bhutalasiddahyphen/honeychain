"""
HoneyChain QR Code Routes (Blueprint: qr_code)
Covers QR generation, Jar label downloading/printing, and mobile camera QR scanning.
"""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database
from utils.qr_generator import generate_qr_code

qr_code_bp = Blueprint("qr_code_routes", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@qr_code_bp.route("/qr-code")
@qr_code_bp.route("/qr_code")
@login_required
def qr_code_hub():
    """
    Dedicated Responsive QR Code Hub (Section 7 & 8):
    - Real-time QR Code Generator & Label Print/Download
    - Live Mobile Camera QR Code Scanner with Auto-Detect
    """
    all_batches = database.get_all_batches()
    batch_id = request.args.get("batch_id", "").strip().upper() or request.args.get("custom_id", "").strip().upper()
    if not batch_id and all_batches:
        batch_id = all_batches[0]["batch_id"]

    batch_info = database.get_batch(batch_id) if batch_id else None
    qr_image = None
    if batch_id:
        qr_image = generate_qr_code(batch_id, request.host_url)

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


@qr_code_bp.route("/qr-generator")
@login_required
def qr_generator():
    """QR Code Generator page."""
    return qr_code_hub()


@qr_code_bp.route("/qr/scan")
@login_required
def qr_scan():
    """Browser camera QR scanner with fallback manual batch lookup."""
    return render_template("qr/scan.html", active_page="qr_scan")


@qr_code_bp.route("/qr/generate")
@qr_code_bp.route("/qr/generate/<batch_id>")
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
