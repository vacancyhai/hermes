"""HTTP client for Backend API communication.

Both frontends use this to call the backend REST API.
Handles JWT tokens, request IDs, and error responses.
"""

import uuid

import requests


class ApiClient:
    """HTTP client for the Hermes backend API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _headers(self, token: str | None = None) -> dict:
        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": str(uuid.uuid4()),
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def get(self, path: str, token: str | None = None, params: dict | None = None):
        """GET request to backend API."""
        resp = self.session.get(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            params=params,
            timeout=10,
        )
        return resp

    def post(self, path: str, token: str | None = None, json: dict | None = None):
        """POST request to backend API."""
        resp = self.session.post(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            json=json,
            timeout=10,
        )
        return resp

    def put(self, path: str, token: str | None = None, json: dict | None = None):
        """PUT request to backend API."""
        resp = self.session.put(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            json=json,
            timeout=10,
        )
        return resp

    def delete(self, path: str, token: str | None = None):
        """DELETE request to backend API."""
        resp = self.session.delete(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            timeout=10,
        )
        return resp
