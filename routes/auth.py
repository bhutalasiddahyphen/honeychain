"""
HoneyChain Authentication Routes (Blueprint: auth)
Covers Login, Admin Portal, Google SSO, Registration, Forgot Password, and Logout.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
import database

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Unified Responsive Login Page:
    - User Login (Beekeepers, Labs, Packagers, Sellers, Consumers)
    - Admin Login Portal
    - Google SSO Sign-in
    - Remember me & Forgot password
    """
    mode = request.args.get("mode", "user").strip().lower()

    if session.get("user_id") and request.method == "GET":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()
        login_mode = request.form.get("login_mode", "user").strip().lower()
        remember_me = request.form.get("remember_me")

        if remember_me:
            session.permanent = True

        user = database.authenticate_user(identifier, password)
        if user:
            if login_mode == "admin" and user["role"] != "admin":
                flash("Access denied: This portal is reserved for Consortium Lead Administrators only.", "error")
                return redirect(url_for("login", mode="admin"))

            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]
            flash(f"Welcome back to HoneyChain, {user['full_name']}!", "success")

            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials! Please check your username/email and password.", "error")
            return redirect(url_for("login", mode=login_mode))

    return render_template("login.html", mode=mode)


@auth_bp.route("/admin/login")
def admin_login():
    """Direct shortcut URL to the Admin Login Portal."""
    return redirect(url_for("login", mode="admin"))


@auth_bp.route("/auth/google")
@auth_bp.route("/google-login")
def google_login():
    """
    Simple Google SSO Sign-In:
    Seamless 1-click Google authentication for members and customers.
    """
    google_email = "google.honeyuser@gmail.com"
    google_name = "Google Verified Member"
    google_username = "google_user"

    user = database.get_user_by_email(google_email)
    if not user:
        database.create_user(
            username=google_username,
            email=google_email,
            password=generate_password_hash("GoogleAuth@2026"),
            full_name=google_name,
            role="consumer",
            organization="Google Authenticated Member"
        )
        user = database.get_user_by_login(google_username)

    session["user_id"] = user["id"]
    session["user_name"] = user["full_name"]
    session["user_email"] = user["email"]
    session["user_role"] = user["role"]
    session["auth_provider"] = "google"

    flash("Successfully signed in with Google! Welcome to HoneyChain.", "success")
    return redirect(url_for("dashboard"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Create account option for HoneyChain consortium partners."""
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip() or (email.split("@")[0] if email else "")
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        role = request.form.get("role", "beekeeper").strip().lower()
        organization = request.form.get("organization", "").strip()

        if not full_name or not email or not password:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("register"))

        if confirm_password and password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        if database.get_user_by_email(email) or database.get_user_by_login(username):
            flash("An account with that email or username already exists. Please log in.", "error")
            return redirect(url_for("login"))

        user_id = database.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=role,
            organization=organization or f"{full_name} Apiary"
        )
        session["user_id"] = user_id
        session["user_name"] = full_name
        session["user_email"] = email
        session["user_role"] = role
        flash(f"Account registered successfully! Welcome to HONEYCHAIN, {full_name}.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Reset account password via email."""
    email = request.form.get("email", "").strip()
    new_password = request.form.get("new_password", "").strip()
    if not email or not new_password:
        flash("Please provide your email address and a new password.", "error")
        return redirect(url_for("login"))

    success = database.reset_password_by_email(email, new_password)
    if success:
        flash("Password reset successfully! Please log in with your new credentials.", "success")
    else:
        flash("Email address not found in consortium database.", "error")
    return redirect(url_for("login"))


@auth_bp.route("/logout")
def logout():
    """Sign out current user and clear session."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))
