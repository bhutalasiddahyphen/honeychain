"""
HoneyChain Packer Stage Routes (Blueprint: packer)
Stage 3: Bottling, Packaging Specifications, Tamper-Evident Seals, and Lot Numbering.
"""
import random
from datetime import datetime, timezone
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database

packer_bp = Blueprint("packer_routes", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@packer_bp.route("/packer", methods=["GET", "POST"])
@login_required
def packer():
    """
    Stage 3 - Packer Management:
    Records packaging facility, supervisor, jar type, net weight, tamper seal ID,
    lot number, and packaging date; mines Block 3 onto the blockchain.
    """
    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        packaging_plant = request.form.get("packaging_plant", "").strip()
        packaging_supervisor = request.form.get("packaging_supervisor", "").strip()
        jar_format = request.form.get("jar_format", "").strip()
        net_weight = request.form.get("net_weight", "").strip()
        tamper_seal_id = request.form.get("tamper_seal_id", "").strip()
        lot_number = request.form.get("lot_number", "").strip()
        packaging_date = request.form.get("packaging_date", "").strip()

        # 1. Mine Block 3
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
        from app import honey_blockchain
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


@packer_bp.route("/stages/packer", methods=["GET", "POST"])
@login_required
def stages_packer():
    """Alternative enterprise packer stage route."""
    from services.batch_service import BatchService
    from services.blockchain_service import BlockchainService
    from services.qr_service import QRService

    bs = BatchService(
        blockchain_service=BlockchainService(),
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
