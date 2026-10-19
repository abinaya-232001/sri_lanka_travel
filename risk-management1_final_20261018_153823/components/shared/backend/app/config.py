import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)
load_dotenv(override=False)


class Config:
    """Unified Tour Ceylon + SOS configuration (MVC Model layer uses this)."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    # Long-lived for local/college demos; override with JWT_EXPIRE_HOURS in .env
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=float(os.getenv("JWT_EXPIRE_HOURS", "168")))

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:password@localhost:5432/travel_app",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "15")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "25")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "15")),
        "connect_args": {"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5"))},
    }

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    LKR_TO_USD_RATE = float(os.getenv("LKR_TO_USD_RATE", "300"))

    DEFAULT_FOOD_PCT = float(os.getenv("DEFAULT_FOOD_PCT", "25"))
    DEFAULT_ACCOMMODATION_PCT = float(os.getenv("DEFAULT_ACCOMMODATION_PCT", "35"))
    DEFAULT_SHOPPING_PCT = float(os.getenv("DEFAULT_SHOPPING_PCT", "15"))
    DEFAULT_TRANSPORT_PCT = float(os.getenv("DEFAULT_TRANSPORT_PCT", "25"))
    DEFAULT_GUIDE_PCT = float(os.getenv("DEFAULT_GUIDE_PCT", "10"))

    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://localhost:5175,"
            "http://localhost:5176,http://localhost:5180,http://localhost:5181,"
            "http://localhost:5182,"
            "http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,"
            "http://127.0.0.1:5176,http://127.0.0.1:5180,http://127.0.0.1:5181,"
            "http://127.0.0.1:5182",
        ).split(",")
        if o.strip()
    ]

    FERNET_KEY = os.getenv("FERNET_KEY", "")
    NOTIFY_MODE = os.getenv("NOTIFY_MODE", "console")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    NOTIFY_FROM_EMAIL = os.getenv("NOTIFY_FROM_EMAIL", "noreply@tour-ceylon.local")

    # Same-process monolith: bridge uses local User model (kept for compatibility)
    TRAVEL_API_URL = os.getenv("TRAVEL_API_URL", "http://127.0.0.1:5002/api").rstrip("/")

    # Wellness matcher admin (demo-grade shared password, same as the standalone component)
    WELLNESS_ADMIN_PASSWORD = os.getenv("WELLNESS_ADMIN_PASSWORD", "tourceylon2026")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_PATH = "/"
