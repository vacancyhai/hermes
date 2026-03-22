"""Unit tests for the frontend ApiClient."""

from unittest.mock import MagicMock, patch

from app.api_client import ApiClient


def _client():
    c = ApiClient("http://backend:8000/api/v1")
    c.session = MagicMock()
    return c


# ─── __init__ ─────────────────────────────────────────────────────────────────

def test_init_strips_trailing_slash():
    c = ApiClient("http://backend:8000/api/v1/")
    assert c.base_url == "http://backend:8000/api/v1"


def test_init_no_slash():
    c = ApiClient("http://backend:8000/api/v1")
    assert c.base_url == "http://backend:8000/api/v1"


# ─── _headers ─────────────────────────────────────────────────────────────────

def test_headers_without_token():
    c = _client()
    h = c._headers()
    assert h["Content-Type"] == "application/json"
    assert "X-Request-ID" in h
    assert "Authorization" not in h


def test_headers_with_token():
    c = _client()
    h = c._headers(token="mytoken")
    assert h["Authorization"] == "Bearer mytoken"


def test_headers_request_id_is_uuid():
    import uuid
    c = _client()
    h = c._headers()
    uuid.UUID(h["X-Request-ID"])  # raises if not valid UUID


def test_headers_different_each_call():
    c = _client()
    assert c._headers()["X-Request-ID"] != c._headers()["X-Request-ID"]


# ─── get ──────────────────────────────────────────────────────────────────────

def test_get_builds_correct_url():
    c = _client()
    c.get("/jobs")
    c.session.get.assert_called_once()
    call_args = c.session.get.call_args
    assert call_args[0][0] == "http://backend:8000/api/v1/jobs"


def test_get_passes_params():
    c = _client()
    c.get("/jobs", params={"limit": 20})
    call_kwargs = c.session.get.call_args[1]
    assert call_kwargs["params"] == {"limit": 20}


def test_get_with_token():
    c = _client()
    c.get("/jobs", token="tok")
    headers = c.session.get.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer tok"


def test_get_timeout():
    c = _client()
    c.get("/jobs")
    assert c.session.get.call_args[1]["timeout"] == 10


# ─── post ─────────────────────────────────────────────────────────────────────

def test_post_builds_correct_url():
    c = _client()
    c.post("/auth/login", json={"email": "a@b.com"})
    assert c.session.post.call_args[0][0] == "http://backend:8000/api/v1/auth/login"


def test_post_passes_json():
    c = _client()
    c.post("/auth/login", json={"email": "a@b.com", "password": "pass"})
    assert c.session.post.call_args[1]["json"] == {"email": "a@b.com", "password": "pass"}


# ─── put ──────────────────────────────────────────────────────────────────────

def test_put_builds_correct_url():
    c = _client()
    c.put("/notifications/123/read")
    assert c.session.put.call_args[0][0] == "http://backend:8000/api/v1/notifications/123/read"


def test_put_with_json():
    c = _client()
    c.put("/users/me/phone", json={"phone": "9999"})
    assert c.session.put.call_args[1]["json"] == {"phone": "9999"}


# ─── delete ───────────────────────────────────────────────────────────────────

def test_delete_builds_correct_url():
    c = _client()
    c.delete("/notifications/abc")
    assert c.session.delete.call_args[0][0] == "http://backend:8000/api/v1/notifications/abc"


def test_delete_timeout():
    c = _client()
    c.delete("/notifications/abc")
    assert c.session.delete.call_args[1]["timeout"] == 10


# ─── patch ────────────────────────────────────────────────────────────────────

def test_patch_builds_correct_url():
    c = _client()
    c.patch("/users/me")
    assert c.session.patch.call_args[0][0] == "http://backend:8000/api/v1/users/me"
