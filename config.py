"""Class-based Flask app configuration."""

import os
from datetime import timedelta
from os import environ, path
from dotenv import load_dotenv
import yaml

BASE_DIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASE_DIR, ".env"))

# Load YAML configuration
with open(path.join(BASE_DIR, "config.yaml"), "r") as f:
    _yaml_config = yaml.safe_load(f) or {}


def _is_truthy(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration loaded from environment variables."""

    # General
    ENVIRONMENT = environ.get("ENVIRONMENT", "production")

    # Flask Core
    SECRET_KEY = environ.get("TRACK_SECRET_KEY")
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

    # Authentication & Rate Limiting
    _auth_config = _yaml_config.get("authentication", {}).get("rate_limiting", {})
    MAX_LOGIN_ATTEMPTS = _auth_config.get("max_attempts", 3)
    LOGIN_ATTEMPT_WINDOW_SECONDS = _auth_config.get("window_seconds", 600)
    LOGIN_LOCKOUT_SECONDS = _auth_config.get("lockout_seconds", 900)

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