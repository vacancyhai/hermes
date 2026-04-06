"""Playwright E2E test configuration.

All three services must be running before these tests execute.
In CI, the e2e job starts all services via docker-compose before running pytest-playwright.

Service URLs are read from environment variables with sensible CI defaults:
  FRONTEND_URL       — user frontend  (default: http://localhost:8080)
  ADMIN_URL          — admin frontend (default: http://localhost:8081)
  BACKEND_URL        — backend API    (default: http://localhost:8000)
"""

import os

import pytest


@pytest.fixture(scope="session")
def frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def admin_url() -> str:
    return os.getenv("ADMIN_URL", "http://localhost:8081")


@pytest.fixture(scope="session")
def backend_url() -> str:
    return os.getenv("BACKEND_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def admin_credentials() -> dict:
    return {
        "email": os.getenv("E2E_ADMIN_EMAIL", "admin@ci-test.com"),
        "password": os.getenv("E2E_ADMIN_PASSWORD", "AdminCI123"),
    }


@pytest.fixture(scope="session")
def user_api_token() -> str:
    """Pre-minted user JWT injected by the CI seed step via E2E_USER_TOKEN.

    In CI: the seed step creates a regular User in the DB and prints the JWT,
    which is captured and exported as E2E_USER_TOKEN before pytest runs.
    Locally: set E2E_USER_TOKEN in your environment before running.
    """
    token = os.getenv("E2E_USER_TOKEN", "")
    if not token:
        pytest.skip("E2E_USER_TOKEN not set — skipping user-scoped watch tests")
    return token
