import pytest
from werkzeug.security import generate_password_hash

from tech_stack_tracker import create_app
from tech_stack_tracker.app.services import auth as auth_service


@pytest.fixture(autouse=True)
def auth_isolation(monkeypatch):
    """Ensure each test has isolated auth configuration and state."""
    monkeypatch.setenv("TRACK_ADMIN_USERNAME", "admin")
    monkeypatch.setenv(
        "TRACK_ADMIN_PASSWORD_HASH",
        generate_password_hash("password123"),
    )

    auth_service._admin_hash.cache_clear()
    auth_service._FAILED_ATTEMPTS.clear()

    yield

    auth_service._admin_hash.cache_clear()
    auth_service._FAILED_ATTEMPTS.clear()


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SECRET_KEY="test_secret_key"  # <--- needed for session / login_user()
    )
    return app


@pytest.fixture
def client(app):
    return app.test_client()
