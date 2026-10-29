import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "honeychain-cryptographic-secret-key-super-secure-2026")
    DATABASE_PATH = os.environ.get("DATABASE_PATH") or os.path.join(BASE_DIR, "instance", "honeychain.db")
    BLOCKCHAIN_DATA_DIR = os.environ.get("BLOCKCHAIN_DATA_DIR") or os.path.join(BASE_DIR, "blockchain_data")
    QR_DIR = os.environ.get("QR_DIR") or os.path.join(BASE_DIR, "static", "qrcodes")
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:5000")
    BLOCKCHAIN_DIFFICULTY = int(os.environ.get("BLOCKCHAIN_DIFFICULTY", 2))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    DATABASE_PATH = os.path.join(BASE_DIR, "instance", "test_honeychain.db")
    BLOCKCHAIN_DIFFICULTY = 1  # Fast PoW for tests


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

