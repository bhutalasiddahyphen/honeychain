"""
HoneyChain Authentication Unit & Integration Tests
"""
import pytest
from app import app
from services.auth_service import AuthService
from models.user import User


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key-12345"
    with app.test_client() as client:
        yield client


def test_seed_default_admin():
    AuthService.seed_default_admin(email="admin@honeychain.local", password="Admin@123")
    user, err = AuthService.authenticate("admin@honeychain.local", "Admin@123")
    assert err is None
    assert user is not None
    assert user.role == "admin"


def test_auth_invalid_credentials():
    user, err = AuthService.authenticate("admin@honeychain.local", "WrongPassword!")
    assert user is None
    assert "Invalid credentials" in err


def test_user_model_password_hashing():
    u = User(username="testbeekeeper", email="test@beekeeper.local")
    u.set_password("Secret123")
    assert u.password != "Secret123"
    assert u.verify_password("Secret123") is True
    assert u.verify_password("WrongPassword") is False


def test_login_page_renders(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert b"HONEY CHAIN" in res.data
    assert b"Sign in with Google" in res.data
    assert b"User Login" in res.data
    assert b"Admin Portal" in res.data


def test_admin_portal_login_page_renders(client):
    res = client.get("/admin/login", follow_redirects=True)
    assert res.status_code == 200
    assert b"Admin Portal" in res.data
    assert b"Consortium Administrator Gateway" in res.data
    assert b"Switch to User Login" in res.data


def test_google_login_endpoint(client):
    res = client.get("/auth/google", follow_redirects=True)
    assert res.status_code == 200
    assert b"Dashboard" in res.data or b"Google" in res.data


def test_welcome_page_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"HONEY" in res.data
    assert b"From Hive to Home" in res.data


def test_login_flow(client):
    res = client.post("/login", data={
        "identifier": "admin@honeychain.local",
        "password": "Admin@123"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Dashboard" in res.data
