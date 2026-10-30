"""
HoneyChain Dashboard Routes (Blueprint: dashboard)
Serves the unified multi-device operational telemetry and overview.
"""
from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import database

dashboard_bp = Blueprint("dashboard_routes", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access the HoneyChain dashboard.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    """
    HoneyChain Telemetry Dashboard:
    - Responsive layout with Sidebar (Desktop/Laptop) and Hamburger Drawer (Tablet/Mobile)
    - 6 Live MSME Metric Cards
    - 4-Stage Supply Chain Pipeline Flow
    - Quick Action Buttons & Real-time Batch Register
    """
    from services.batch_service import BatchService
    from services.blockchain_service import BlockchainService
    from services.qr_service import QRService

    bs = BatchService(
        blockchain_service=BlockchainService(),
        qr_service=QRService()
    )
    stats = bs.get_dashboard_counts()
    all_batches = database.get_all_batches()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        stats=stats,
        batches=all_batches
    )
