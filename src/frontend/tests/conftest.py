"""
Shared pytest fixtures for user frontend tests.

No real backend is needed — APIClient calls are mocked in each test.
Flask-Login's load_user is satisfied by the session_manager fixtures.
"""
import pytest
from unittest.mock import patch


@pytest.fixture
def app():
    """Minimal Flask app using the real create_app factory."""
    from app import create_app
    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY='test-secret-key-32-chars-minimum!!',
        WTF_CSRF_ENABLED=False,
        BACKEND_API_URL='http://test-backend/api/v1',
    )
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_ctx(app):
    """Push an application context so session/url_for work in unit tests."""
    with app.app_context():
        yield app


@pytest.fixture
def fake_login_data():
    """Simulates api_data from a successful login (no user field)."""
    # JWT payload: {"sub": "uid-123", "role": "user", "email": "u@e.com"}
    # base64url(header).base64url(payload).sig
    import base64, json
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": "uid-123", "role": "user", "email": "u@example.com"}).encode()
    ).rstrip(b"=").decode()
    token = f"eyJhbGciOiJIUzI1NiJ9.{payload}.fakesig"
    return {
        "access_token": token,
        "refresh_token": "refresh.token.here",
    }


@pytest.fixture
def fake_register_data(fake_login_data):
    """Simulates api_data from a successful register (has user field)."""
    return {
        "user": {
            "id": "uid-456",
            "email": "new@example.com",
            "full_name": "New User",
            "role": "user",
        },
        "access_token": fake_login_data["access_token"],
        "refresh_token": fake_login_data["refresh_token"],
    }
