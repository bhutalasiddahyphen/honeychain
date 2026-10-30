"""
HoneyChain Route Blueprints Package
"""
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.beekeeper import beekeeper_bp
from routes.laboratory import laboratory_bp
from routes.packer import packer_bp
from routes.seller import seller_bp
from routes.qr_code import qr_code_bp
from routes.traceability import traceability_bp

__all__ = [
    "auth_bp",
    "dashboard_bp",
    "beekeeper_bp",
    "laboratory_bp",
    "packer_bp",
    "seller_bp",
    "qr_code_bp",
    "traceability_bp",
    "register_blueprints",
]


def register_blueprints(app):
    """Registers all feature blueprints with the Flask application."""
    blueprints = [
        auth_bp,
        dashboard_bp,
        beekeeper_bp,
        laboratory_bp,
        packer_bp,
        seller_bp,
        qr_code_bp,
        traceability_bp,
    ]
    for bp in blueprints:
        app.register_blueprint(bp)
