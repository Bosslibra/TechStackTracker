from config import Config
from app.api import auth as auth_api


def test_auth_status_unauthenticated(client):
    resp = client.get("/api/auth/status")
    assert resp.status_code == 200
    assert resp.get_json() == {"authenticated": False}


def test_login_success_returns_csrf(client):
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    body = resp.get_json()

    assert resp.status_code == 200
    assert body["authenticated"] is True
    assert isinstance(body["csrfToken"], str)
    assert len(body["csrfToken"]) > 10


def test_login_invalid_credentials_returns_401(client, monkeypatch):
    monkeypatch.setattr(auth_api.time, "sleep", lambda *_: None)
    monkeypatch.setattr(auth_api.secrets, "randbelow", lambda *_: 0)

    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Invalid credentials"


def test_logout_requires_auth(client):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Authentication required"


def test_logout_requires_csrf(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert login.status_code == 200

    resp = client.post("/api/auth/logout")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "Invalid CSRF token"


def test_logout_with_csrf_succeeds(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    token = login.get_json()["csrfToken"]

    resp = client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": token},
    )
    assert resp.status_code == 204


def test_rate_limit_after_too_many_failures(client, monkeypatch):
    monkeypatch.setattr(auth_api.time, "sleep", lambda *_: None)
    monkeypatch.setattr(auth_api.secrets, "randbelow", lambda *_: 0)

    for _ in range(Config.MAX_LOGIN_ATTEMPTS):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert resp.status_code == 401

    locked = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert locked.status_code == 429
    assert "Too many failed attempts" in locked.get_json()["error"]
