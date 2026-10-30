"""
HoneyChain Beekeeper Stage Routes (Blueprint: beekeeper)
Stage 1: Production, Apiary Registration, and Harvest Tracking.
"""
import random
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import database

beekeeper_bp = Blueprint("beekeeper_routes", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access this page.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@beekeeper_bp.route("/beekeeper", methods=["GET", "POST"])
@login_required
def beekeeper():
    """
    Stage 1 - Beekeeper Management:
    Records honey production, apiary location, hives count, and harvest details.
    """
    if request.method == "POST":
        data = {
            "beekeeper_id": request.form.get("beekeeper_id", "").strip(),
            "name": request.form.get("name", "").strip(),
            "apiary_name": request.form.get("apiary_name", "").strip(),
            "location": request.form.get("location", "").strip(),
            "hives_count": request.form.get("hives_count", 50),
            "license_no": request.form.get("license_no", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "email": request.form.get("email", "").strip(),
            "honey_varieties": request.form.get("honey_varieties", "").strip()
        }
        database.add_beekeeper(data)
        database.add_notification(
            f"Step 1 Complete: Beekeeper Registered ({data['name']})",
            f"Apiary '{data['apiary_name']}' in {data['location']} registered. Ready for Step 2 (Batch Creation).",
            "info"
        )
        flash(f"Step 1 Complete! Beekeeper '{data['name']}' registered. Now proceed to Step 2 to register a honey batch.", "success")
        return redirect(url_for(
            "beekeeper",
            step_completed="1",
            beekeeper_id=data["beekeeper_id"],
            beekeeper_name=data["name"],
            apiary_name=data["apiary_name"],
            location=data["location"]
        ))

    beekeepers = database.get_beekeepers()
    suggested_id = f"BK-{random.randint(100, 999)}"
    return render_template(
        "beekeeper.html",
        active_page="beekeeper",
        beekeepers=beekeepers,
        suggested_id=suggested_id
    )


@beekeeper_bp.route("/beekeeper/delete/<beekeeper_id>", methods=["POST"])
@login_required
def delete_beekeeper(beekeeper_id):
    """Delete a beekeeper record."""
    database.delete_beekeeper(beekeeper_id)
    flash(f"Beekeeper {beekeeper_id} removed.", "info")
    return redirect(url_for("beekeeper"))


@beekeeper_bp.route("/stages/beekeeper", methods=["GET", "POST"])
@login_required
def stages_beekeeper():
    """Stage 1: Production & Apiary Overview."""
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "add_beekeeper":
            data = {
                "beekeeper_id": f"BK-{random.randint(1000, 9999)}",
                "name": request.form.get("name", "").strip(),
                "apiary_name": request.form.get("apiary_name", "").strip(),
                "location": request.form.get("location", "").strip(),
                "hives_count": request.form.get("hives_count", 50),
                "phone": request.form.get("phone", "").strip(),
                "honey_varieties": request.form.get("honey_varieties", "").strip()
            }
            database.add_beekeeper(data)
            flash(f"Beekeeper '{data['name']}' registered successfully!", "success")
            return redirect(url_for("stages_beekeeper"))

    beekeepers = database.get_beekeepers()
    batches = database.get_all_batches()
    return render_template(
        "stages/beekeeper.html",
        active_page="beekeeper",
        beekeepers=beekeepers,
        batches=batches
    )
