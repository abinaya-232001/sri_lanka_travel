import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-to-a-long-random-string-32+")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_HOURS", "24")))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'tour_ceylon_sos.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB per photo / voice note
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Voice -> English. With an OpenAI key, Whisper translates any spoken language
    # straight to English. Without it, the browser's speech-to-text is used and
    # the text is translated to English.
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # WhatsApp to family. "console" = print only (development); "twilio" = send.
    WHATSAPP_MODE = os.getenv("WHATSAPP_MODE", "console")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
    TWILIO_WHATSAPP_CONTENT_SID = os.getenv("TWILIO_WHATSAPP_CONTENT_SID")

    # Separate immigration API. The police desk reads visa dates from here.
    IMMIGRATION_API_URL = os.getenv("IMMIGRATION_API_URL", "http://127.0.0.1:5055")
    IMMIGRATION_API_KEY = os.getenv("IMMIGRATION_API_KEY", "demo-immigration-key")
