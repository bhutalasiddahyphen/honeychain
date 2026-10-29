"""
HoneyChain QR Code & Public Traceability Unit Tests
"""
import os
import pytest
from app import app
from services.qr_service import QRService


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_qr_generation():
    qr_svc = QRService()
    test_id = "HC-TEST-QR-99"
    filename = qr_svc.generate_batch_qr(test_id, custom_base_url="https://honeychain.org")
    assert filename == f"{test_id}.png"

    path = qr_svc.get_qr_path(test_id)
    assert path is not None
    assert os.path.exists(path)


def test_public_trace_endpoint_unauthenticated(client):
    """Customer public traceability endpoint MUST be accessible without logging in."""
    res = client.get("/trace/HC-2026-9842")
    # Even if batch doesn't exist, it should render 200 without redirecting to login!
    assert res.status_code == 200
    assert b"HONEY CHAIN" in res.data


def test_public_trace_root_unauthenticated(client):
    res = client.get("/trace")
    assert res.status_code == 200
    assert b"HONEY CHAIN" in res.data

