"""
HoneyChain Traceability Routes (Blueprint: traceability)
Public & Member Traceability: Full 5-Stage Provenance and SHA-256 Blockchain Verification.
"""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import database

traceability_bp = Blueprint("traceability_routes", __name__)


@traceability_bp.route("/traceability")
def traceability():
    """
    Dedicated Responsive Traceability Page (Section 6 & 8):
    Displays complete honey supply-chain process:
    Beekeeper -> Laboratory -> Packer -> Seller -> Customer
    With live cryptographic blockchain verification status.
    """
    all_batches = database.get_all_batches()
    batch_id = request.args.get("batch_id", "").strip().upper().lstrip("#")
    if not batch_id and all_batches:
        batch_id = all_batches[0]["batch_id"]

    batch = database.get_batch(batch_id) if batch_id else None

    # Retrieve blockchain verification status for this batch
    from app import honey_blockchain
    blocks_for_batch = [b for b in honey_blockchain.chain if b.data.get("batch_id") == batch_id]
    is_valid, validation_msg = honey_blockchain.is_chain_valid()

    return render_template(
        "traceability.html",
        active_page="track_honey",
        batch=batch,
        active_batch_id=batch_id,
        batches=all_batches,
        blocks=blocks_for_batch,
        is_chain_valid=is_valid,
        validation_msg=validation_msg
    )


@traceability_bp.route("/track-honey")
def track_honey():
    """Alias for honey supply-chain journey tracking."""
    return traceability()


@traceability_bp.route("/verification")
def verification():
    """Product verification view for scanned consumer jars."""
    batch_id = request.args.get("batch_id", "").strip().upper().lstrip("#")
    batch = database.get_batch(batch_id) if batch_id else None
    return render_template(
        "verification.html",
        active_page="verification",
        query_batch_id=batch_id,
        batch=batch
    )


@traceability_bp.route("/trace")
@traceability_bp.route("/trace/<batch_id>")
def trace_route(batch_id=None):
    """
    Public customer honey traceability endpoint.
    Accessible without authentication on mobile phones, tablets, and desktops.
    """
    clean_id = (batch_id or request.args.get("batch_id", "")).strip().upper().lstrip("#")
    batch = database.get_batch(clean_id) if clean_id else None
    return render_template(
        "public/trace.html",
        batch=batch,
        searched_id=clean_id
    )


@traceability_bp.route("/api/trace/<batch_id>", methods=["GET"])
def api_trace_batch(batch_id):
    """REST API endpoint returning complete batch provenance & cryptographic hash."""
    clean_id = (batch_id or "").strip().upper().lstrip("#")
    batch = database.get_batch(clean_id)
    if not batch:
        return jsonify({"success": False, "error": f"Batch '{clean_id}' not found."}), 404

    from app import honey_blockchain
    blocks = [b.to_dict() for b in honey_blockchain.chain if b.data.get("batch_id") == clean_id]
    is_valid, _ = honey_blockchain.is_chain_valid()

    return jsonify({
        "success": True,
        "batch_id": clean_id,
        "product_name": batch.get("product_name"),
        "current_stage": batch.get("current_stage"),
        "stage_num": batch.get("stage_num"),
        "blockchain_verified": is_valid,
        "block_count": len(blocks),
        "blocks": blocks,
        "details": batch
    })
