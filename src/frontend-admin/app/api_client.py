"""HTTP client for Backend API communication.

Shared between both frontends — identical implementation.
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
        resp = self.session.get(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            params=params,
            timeout=10,
        )
        return resp

    def post(self, path: str, token: str | None = None, json: dict | None = None):
        resp = self.session.post(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            json=json,
            timeout=10,
        )
        return resp

    def put(self, path: str, token: str | None = None, json: dict | None = None):
        resp = self.session.put(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            json=json,
            timeout=10,
        )
        return resp

    def delete(self, path: str, token: str | None = None):
        resp = self.session.delete(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            timeout=10,
        )
        return resp

    def patch(self, path: str, token: str | None = None, json: dict | None = None):
        resp = self.session.patch(
            f"{self.base_url}{path}",
            headers=self._headers(token),
            json=json,
            timeout=10,
        )
        return resp

    def post_file(self, path: str, token: str | None = None, files: dict | None = None):
        headers = {"X-Request-ID": str(uuid.uuid4())}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = self.session.post(
            f"{self.base_url}{path}",
            headers=headers,
            files=files,
            timeout=60,
        )
        return resp
