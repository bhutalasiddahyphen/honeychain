"""
HoneyChain Responsive Routes & Blueprint Integration Tests
Validates all Section 8 endpoints, templates, and 4-stage pipeline.
"""
import pytest
from app import app
import database


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "responsive-test-key-9988"
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_client(client):
    """Client with an authenticated session."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Dr. Certified Tester"
        sess["user_role"] = "admin"
        sess["user_email"] = "admin@honeychain.local"
    return client


def test_landing_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"HONEY" in res.data


def test_login_page_responsive(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert b"Sign in with Google" in res.data
    assert b"Remember me" in res.data


def test_dashboard_authenticated(auth_client):
    res = auth_client.get("/dashboard")
    assert res.status_code == 200
    assert b"Dashboard" in res.data
    assert b"HONEY CHAIN" in res.data


def test_beekeeper_stage(auth_client):
    res = auth_client.get("/beekeeper")
    assert res.status_code == 200
    assert b"Beekeeper" in res.data


def test_laboratory_stage(auth_client):
    res = auth_client.get("/laboratory")
    assert res.status_code == 200
    assert b"Laboratory" in res.data


def test_packer_stage(auth_client):
    res = auth_client.get("/packer")
    assert res.status_code == 200
    assert b"Packer" in res.data


def test_seller_stage(auth_client):
    res = auth_client.get("/seller")
    assert res.status_code == 200
    assert b"Seller" in res.data


def test_blockchain_records(auth_client):
    res = auth_client.get("/blockchain")
    assert res.status_code == 200
    assert b"Blockchain Records" in res.data


def test_qr_code_hub_page(auth_client):
    res = auth_client.get("/qr-code")
    assert res.status_code == 200
    assert b"QR Code" in res.data
    assert b"Camera" in res.data


def test_traceability_page(auth_client):
    res = auth_client.get("/traceability")
    assert res.status_code == 200
    assert b"Traceability" in res.data
    assert b"Beekeeper" in res.data


def test_public_trace_endpoint(client):
    res = client.get("/trace/HONEY2026001")
    assert res.status_code == 200
    assert b"HONEY CHAIN" in res.data
