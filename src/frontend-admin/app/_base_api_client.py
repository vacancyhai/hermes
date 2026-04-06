"""Shared base ApiClient — provides HTTP methods wrapping requests.Session."""

import uuid

import requests


class BaseApiClient:
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
        return self.session.get(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            params=params,
            timeout=10,
        )

    def post(self, path: str, token: str | None = None, json: dict | None = None):
        """POST request to backend API."""
        return self.session.post(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            json=json,
            timeout=10,
        )

    def put(self, path: str, token: str | None = None, json: dict | None = None):
        """PUT request to backend API."""
        return self.session.put(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            json=json,
            timeout=10,
        )

    def delete(self, path: str, token: str | None = None):
        """DELETE request to backend API."""
        return self.session.delete(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            timeout=10,
        )

    def patch(self, path: str, token: str | None = None, json: dict | None = None):
        """PATCH request to backend API."""
        return self.session.patch(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            json=json,
            timeout=10,
        )

    def post_file(self, path: str, token: str | None = None, files: dict | None = None):
        """Multipart file POST to backend API."""
        headers = {"X-Request-ID": str(uuid.uuid4())}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self.session.post(
            f"{self.base_url}{path}",
            headers=headers,
            files=files,
            timeout=60,
        )
