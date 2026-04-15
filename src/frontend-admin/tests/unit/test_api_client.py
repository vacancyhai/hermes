"""Unit tests for the admin frontend ApiClient (includes post_file)."""

from unittest.mock import MagicMock

from app.api_client import ApiClient


def _client():
    c = ApiClient("http://backend:8000/api/v1")
    c.session = MagicMock()
    return c


# ─── __init__ ─────────────────────────────────────────────────────────────────

def test_init_strips_trailing_slash():
    c = ApiClient("http://backend:8000/api/v1/")
    assert c.base_url == "http://backend:8000/api/v1"


# ─── _headers ─────────────────────────────────────────────────────────────────

def test_headers_no_token():
    c = _client()
    h = c._headers()
    assert h["Content-Type"] == "application/json"
    assert "Authorization" not in h


def test_headers_with_token():
    c = _client()
    h = c._headers(token="abc")
    assert h["Authorization"] == "Bearer abc"


def test_headers_unique_request_id():
    c = _client()
    assert c._headers()["X-Request-ID"] != c._headers()["X-Request-ID"]


# ─── get ──────────────────────────────────────────────────────────────────────

def test_get_url():
    c = _client()
    c.get("/admin/jobs")
    assert c.session.get.call_args[0][0] == "http://backend:8000/api/v1/admin/jobs"


def test_get_params():
    c = _client()
    c.get("/admin/jobs", params={"status": "active"})
    assert c.session.get.call_args[1]["params"] == {"status": "active"}


def test_get_with_token():
    c = _client()
    c.get("/admin/stats", token="tok")
    assert "Bearer tok" in c.session.get.call_args[1]["headers"]["Authorization"]


# ─── post ─────────────────────────────────────────────────────────────────────

def test_post_url():
    c = _client()
    c.post("/auth/admin/login", json={"email": "a@b.com"})
    assert c.session.post.call_args[0][0] == "http://backend:8000/api/v1/auth/admin/login"


def test_post_json():
    c = _client()
    body = {"email": "a@b.com", "password": "p"}
    c.post("/auth/admin/login", json=body)
    assert c.session.post.call_args[1]["json"] == body


# ─── put ──────────────────────────────────────────────────────────────────────

def test_put_url():
    c = _client()
    c.put("/admin/jobs/123")
    assert c.session.put.call_args[0][0] == "http://backend:8000/api/v1/admin/jobs/123"


def test_put_with_json():
    c = _client()
    c.put("/admin/users/1/status", json={"status": "suspended"})
    assert c.session.put.call_args[1]["json"] == {"status": "suspended"}


# ─── delete ───────────────────────────────────────────────────────────────────

def test_delete_url():
    c = _client()
    c.delete("/admin/jobs/123")
    assert c.session.delete.call_args[0][0] == "http://backend:8000/api/v1/admin/jobs/123"


# ─── post_file ────────────────────────────────────────────────────────────────

def test_post_file_url():
    c = _client()
    c.post_file("/admin/jobs/upload-pdf", token="tok", files={"file": b"data"})
    assert c.session.post.call_args[0][0] == "http://backend:8000/api/v1/admin/jobs/upload-pdf"


def test_post_file_no_content_type():
    """post_file should NOT set Content-Type (multipart handled by requests)."""
    c = _client()
    c.post_file("/admin/jobs/upload-pdf")
    headers = c.session.post.call_args[1]["headers"]
    assert "Content-Type" not in headers


def test_post_file_sets_auth_header():
    c = _client()
    c.post_file("/admin/jobs/upload-pdf", token="mytoken")
    headers = c.session.post.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer mytoken"


def test_post_file_without_token_no_auth():
    c = _client()
    c.post_file("/admin/jobs/upload-pdf")
    headers = c.session.post.call_args[1]["headers"]
    assert "Authorization" not in headers


def test_post_file_has_longer_timeout():
    c = _client()
    c.post_file("/admin/jobs/upload-pdf")
    assert c.session.post.call_args[1]["timeout"] == 60


def test_post_file_passes_files():
    c = _client()
    files = {"file": ("test.pdf", b"content", "application/pdf")}
    c.post_file("/admin/jobs/upload-pdf", files=files)
    assert c.session.post.call_args[1]["files"] == files
