"""
HoneyChain Laboratory Stage Routes (Blueprint: laboratory)
Stage 2: Scientific Quality Analysis, Purity Testing, and Assay Verification.
"""
import random
import hmac
import hashlib
from datetime import datetime, timezone
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database
from blockchain import Blockchain

laboratory_bp = Blueprint("laboratory_routes", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def generate_lab_digital_signature(batch_id, cert_no, purity, moisture, hmf, secret="EUROFINS_CONSORTIUM_RSA_KEY_2026"):
    payload = f"{batch_id}|{cert_no}|{purity}|{moisture}|{hmf}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"SIG-SHA256:{sig[:28].upper()}"


@laboratory_bp.route("/laboratory", methods=["GET", "POST"])
@login_required
def laboratory():
    """
    Stage 2 - Laboratory Testing:
    Records purity score, moisture, HMF level, NMR profile, certificate number,
    and mines Block 2 on the blockchain with a cryptographic digital signature.
    """
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

        # 1. Mine Block 2
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
        from app import honey_blockchain
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


@laboratory_bp.route("/stages/laboratory", methods=["GET", "POST"])
@login_required
def stages_laboratory():
    """Alternative enterprise lab stage route."""
    from services.batch_service import BatchService
    from services.blockchain_service import BlockchainService
    from services.qr_service import QRService

    bs = BatchService(
        blockchain_service=BlockchainService(),
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
