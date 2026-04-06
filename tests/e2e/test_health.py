"""E2E smoke tests — verify all three services are reachable and healthy."""

import pytest
import requests


def test_backend_health(backend_url):
    """Backend /health returns 200 with status ok."""
    resp = requests.get(f"{backend_url}/api/v1/health", timeout=10)
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_frontend_health(frontend_url):
    """User frontend /health returns 200 with status ok."""
    resp = requests.get(f"{frontend_url}/health", timeout=10)
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_admin_health(admin_url):
    """Admin frontend /health returns 200 with status ok."""
    resp = requests.get(f"{admin_url}/health", timeout=10)
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"
