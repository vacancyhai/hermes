from __future__ import annotations
"""
API client for the admin frontend.

Identical HTTP machinery as the user frontend APIClient. Kept as a
separate file so admin-specific endpoints (job management, user
management, etc.) can be added here in Stories 3 and 4 without
touching the user frontend.
"""
import requests
from flask import current_app


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: list = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


class APIClient:
    """Thin wrapper around ``requests`` targeting the backend API."""

    # ------------------------------------------------------------------
    # Auth endpoints
    # ------------------------------------------------------------------

    def login(self, email: str, password: str) -> dict:
        """POST /api/v1/auth/login → {"access_token": ..., "refresh_token": ...}"""
        return self._post("/auth/login", {"email": email, "password": password})

    def logout(self, access_token: str, refresh_token: str) -> None:
        self._post("/auth/logout", {}, access_token=access_token)

    def refresh_tokens(self, refresh_token: str) -> dict:
        return self._post("/auth/refresh", {}, access_token=refresh_token)

    # ------------------------------------------------------------------
    # Private HTTP helpers
    # ------------------------------------------------------------------

    def _base_url(self) -> str:
        return current_app.config["BACKEND_API_URL"].rstrip("/")

    def _headers(self, access_token: str | None = None) -> dict:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if access_token:
            h["Authorization"] = f"Bearer {access_token}"
        return h

    def _post(self, path: str, payload: dict, access_token: str | None = None) -> dict:
        url = f"{self._base_url()}{path}"
        try:
            resp = requests.post(url, json=payload, headers=self._headers(access_token), timeout=10)
        except requests.exceptions.ConnectionError:
            raise APIError(503, "SERVICE_UNAVAILABLE", "Cannot reach the server. Please try again later.")
        except requests.exceptions.Timeout:
            raise APIError(504, "GATEWAY_TIMEOUT", "The server took too long to respond.")
        return self._handle_response(resp)

    def _get(self, path: str, access_token: str | None = None, params: dict | None = None) -> dict:
        url = f"{self._base_url()}{path}"
        try:
            resp = requests.get(url, params=params, headers=self._headers(access_token), timeout=10)
        except requests.exceptions.ConnectionError:
            raise APIError(503, "SERVICE_UNAVAILABLE", "Cannot reach the server. Please try again later.")
        except requests.exceptions.Timeout:
            raise APIError(504, "GATEWAY_TIMEOUT", "The server took too long to respond.")
        return self._handle_response(resp)

    def _put(self, path: str, payload: dict, access_token: str | None = None) -> dict:
        url = f"{self._base_url()}{path}"
        try:
            resp = requests.put(url, json=payload, headers=self._headers(access_token), timeout=10)
        except requests.exceptions.ConnectionError:
            raise APIError(503, "SERVICE_UNAVAILABLE", "Cannot reach the server. Please try again later.")
        except requests.exceptions.Timeout:
            raise APIError(504, "GATEWAY_TIMEOUT", "The server took too long to respond.")
        return self._handle_response(resp)

    def _delete(self, path: str, access_token: str | None = None) -> dict:
        url = f"{self._base_url()}{path}"
        try:
            resp = requests.delete(url, headers=self._headers(access_token), timeout=10)
        except requests.exceptions.ConnectionError:
            raise APIError(503, "SERVICE_UNAVAILABLE", "Cannot reach the server. Please try again later.")
        except requests.exceptions.Timeout:
            raise APIError(504, "GATEWAY_TIMEOUT", "The server took too long to respond.")
        return self._handle_response(resp)

    @staticmethod
    def _handle_response(resp: requests.Response) -> dict:
        try:
            body = resp.json()
        except ValueError:
            raise APIError(resp.status_code, "INVALID_RESPONSE", "Unexpected response from the server.")

        if resp.ok:
            return body.get("data", {})

        error = body.get("error", {})
        raise APIError(
            status_code=resp.status_code,
            code=error.get("code", "UNKNOWN_ERROR"),
            message=error.get("message", "An unexpected error occurred."),
            details=error.get("details", []),
        )
