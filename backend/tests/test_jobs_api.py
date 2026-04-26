import json

from app.services import jobs as jobs_service


def _login_and_get_csrf(client):
    resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert resp.status_code == 200
    return resp.get_json()["csrfToken"]


def test_get_jobs_returns_empty_list_when_file_missing(client, monkeypatch, tmp_path):
    monkeypatch.setattr(jobs_service, "DATA_FILE", tmp_path / "jobs.json")

    resp = client.get("/api/jobs")

    assert resp.status_code == 200
    assert resp.get_json() == []


def test_get_jobs_returns_list_from_storage(client, monkeypatch, tmp_path):
    data_file = tmp_path / "jobs.json"
    data_file.write_text(
        json.dumps([{"id": 1, "title": "Backend Dev"}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(jobs_service, "DATA_FILE", data_file)

    resp = client.get("/api/jobs")

    assert resp.status_code == 200
    assert resp.get_json() == [{"id": 1, "title": "Backend Dev"}]


def test_post_jobs_requires_auth(client, monkeypatch, tmp_path):
    monkeypatch.setattr(jobs_service, "DATA_FILE", tmp_path / "jobs.json")

    resp = client.post("/api/jobs", json=[])

    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Authentication required"


def test_post_jobs_requires_csrf(client, monkeypatch, tmp_path):
    monkeypatch.setattr(jobs_service, "DATA_FILE", tmp_path / "jobs.json")
    _login_and_get_csrf(client)

    resp = client.post("/api/jobs", json=[])

    assert resp.status_code == 403
    assert resp.get_json()["error"] == "Invalid CSRF token"


def test_post_jobs_rejects_non_array_payload(client, monkeypatch, tmp_path):
    monkeypatch.setattr(jobs_service, "DATA_FILE", tmp_path / "jobs.json")
    token = _login_and_get_csrf(client)

    resp = client.post(
        "/api/jobs",
        json={"id": 1},
        headers={"X-CSRF-Token": token},
    )

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Expected a JSON array"


def test_post_jobs_persists_payload_and_returns_204(client, monkeypatch, tmp_path):
    data_file = tmp_path / "jobs.json"
    monkeypatch.setattr(jobs_service, "DATA_FILE", data_file)
    token = _login_and_get_csrf(client)
    payload = [
        {"id": 1, "title": "Backend Dev", "status": "Applied"},
        {"id": 2, "title": "ML Engineer", "status": "Interview"},
    ]

    post_resp = client.post(
        "/api/jobs",
        json=payload,
        headers={"X-CSRF-Token": token},
    )
    get_resp = client.get("/api/jobs")

    assert post_resp.status_code == 204
    assert post_resp.data == b""
    assert get_resp.status_code == 200
    assert get_resp.get_json() == payload
