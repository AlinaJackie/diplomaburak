import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _get_secret_key():
    value = (os.environ.get("SECRET_KEY") or "").strip()
    if value:
        return value
    return secrets.token_hex(32)


class Config:
    SECRET_KEY = _get_secret_key()

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'foodgo.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        os.environ.get("MAIL_USERNAME"),
    )
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")
    PASSWORD_RESET_TOKEN_HOURS = int(
        os.environ.get("PASSWORD_RESET_TOKEN_HOURS", 1)
    )

    GOOGLE_MAPS_API_KEY = (os.environ.get("GOOGLE_MAPS_API_KEY") or "").strip()

    DELIVERY_BASE_FEE = int(os.environ.get("DELIVERY_BASE_FEE", 40))
    DELIVERY_FREE_FROM = int(os.environ.get("DELIVERY_FREE_FROM", 700))
    DELIVERY_PRICE_PER_KM = float(os.environ.get("DELIVERY_PRICE_PER_KM", 12))
    DELIVERY_MAX_DISTANCE_KM = float(
        os.environ.get("DELIVERY_MAX_DISTANCE_KM", 15)
    )
    DELIVERY_FALLBACK_DISTANCE_KM = float(
        os.environ.get("DELIVERY_FALLBACK_DISTANCE_KM", 4)
    )
    DELIVERY_FALLBACK_ETA_MINUTES = int(
        os.environ.get("DELIVERY_FALLBACK_ETA_MINUTES", 35)
    )