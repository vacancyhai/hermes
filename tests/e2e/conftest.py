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
        "email": os.getenv("E2E_ADMIN_EMAIL", "admin@ci.local"),
        "password": os.getenv("E2E_ADMIN_PASSWORD", "AdminCI123"),
    }
