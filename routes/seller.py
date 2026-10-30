"""
HoneyChain Seller Stage Routes (Blueprint: seller)
Stage 4: Retail Shelf Authenticity, Store Location, Pricing, and Final Distribution.
"""
from datetime import datetime, timezone
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database

seller_bp = Blueprint("seller_routes", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@seller_bp.route("/seller", methods=["GET", "POST"])
@login_required
def seller():
    """
    Stage 4 - Seller Management:
    Records retailer boutique name, store location, license number, shelf arrival date,
    and sale price; mines Block 4 completing the supply-chain lifecycle.
    """
    if request.method == "POST":
        batch_id = request.form.get("batch_id", "").strip().upper()
        seller_name = request.form.get("seller_name", "").strip()
        store_location = request.form.get("store_location", "").strip()
        license_no = request.form.get("license_no", "").strip()
        sale_price = request.form.get("sale_price", "$48.00").strip()
        shelf_arrival_date = request.form.get("shelf_arrival_date", "").strip()

        # 1. Mine Block 4
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
        from app import honey_blockchain
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


@seller_bp.route("/stages/seller", methods=["GET", "POST"])
@login_required
def stages_seller():
    """Alternative enterprise seller stage route."""
    from services.batch_service import BatchService
    from services.blockchain_service import BlockchainService
    from services.qr_service import QRService

    bs = BatchService(
        blockchain_service=BlockchainService(),
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
