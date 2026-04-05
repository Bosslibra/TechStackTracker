"""Class-based Flask app configuration."""

import os
from datetime import timedelta
from os import environ, path
from dotenv import load_dotenv

BASE_DIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASE_DIR, ".env"))


def _is_truthy(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration loaded from environment variables."""

    # General
    ENVIRONMENT = environ.get("ENVIRONMENT", "production")

    # Flask Core
    SECRET_KEY = environ.get("TRACK_SECRET_KEY", os.urandom(32).hex())
    FLASK_DEBUG = _is_truthy(environ.get("FLASK_DEBUG"), False)
    FLASK_APP = "wsgi.py"

    # Static / Templates
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"

    # Session & Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    SESSION_COOKIE_SECURE = _is_truthy(environ.get("TRACK_COOKIE_SECURE"), True)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Request limits
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB

    # Security Headers (custom block)
    SECURITY_HEADERS = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "same-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cache-Control": "no-store",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' https://cdnjs.cloudflare.com; "
            "style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
    }