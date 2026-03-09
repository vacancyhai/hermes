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
    # Jobs endpoints
    # ------------------------------------------------------------------

    def get_jobs(self, access_token: str, **params) -> dict:
        """GET /api/v1/jobs — paginated job list."""
        return self._get("/jobs", access_token=access_token, params=params or None)

    def get_job(self, slug: str, access_token: str) -> dict:
        """GET /api/v1/jobs/<slug>"""
        return self._get(f"/jobs/{slug}", access_token=access_token)

    def create_job(self, access_token: str, payload: dict) -> dict:
        """POST /api/v1/jobs"""
        return self._post("/jobs", payload, access_token=access_token)

    def update_job(self, access_token: str, job_id: str, payload: dict) -> dict:
        """PUT /api/v1/jobs/<id>"""
        return self._put(f"/jobs/{job_id}", payload, access_token=access_token)

    def delete_job(self, access_token: str, job_id: str) -> dict:
        """DELETE /api/v1/jobs/<id>"""
        return self._delete(f"/jobs/{job_id}", access_token=access_token)

    # ------------------------------------------------------------------
    # Users endpoints (admin)
    # ------------------------------------------------------------------

    def get_users(self, access_token: str, page: int = 1, **params) -> dict:
        """GET /api/v1/users — list all users (admin)."""
        p = {'page': page, **params}
        return self._get("/users", access_token=access_token, params=p)

    def update_user_status(self, access_token: str, user_id: str, status: str) -> dict:
        """PUT /api/v1/users/<id>/status"""
        return self._put(f"/users/{user_id}/status", {"status": status}, access_token=access_token)

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

    def _request(
        self,
        method: str,
        path: str,
        access_token: str | None = None,
        payload: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        url = f"{self._base_url()}{path}"
        kwargs: dict = {"headers": self._headers(access_token), "timeout": 10}
        if payload is not None:
            kwargs["json"] = payload
        if params is not None:
            kwargs["params"] = params
        try:
            resp = requests.request(method, url, **kwargs)
        except requests.exceptions.ConnectionError:
            raise APIError(503, "SERVICE_UNAVAILABLE", "Cannot reach the server. Please try again later.")
        except requests.exceptions.Timeout:
            raise APIError(504, "GATEWAY_TIMEOUT", "The server took too long to respond.")
        return self._handle_response(resp)

    def _post(self, path: str, payload: dict, access_token: str | None = None) -> dict:
        return self._request("POST", path, access_token=access_token, payload=payload)

    def _get(self, path: str, access_token: str | None = None, params: dict | None = None) -> dict:
        return self._request("GET", path, access_token=access_token, params=params)

    def _put(self, path: str, payload: dict, access_token: str | None = None) -> dict:
        return self._request("PUT", path, access_token=access_token, payload=payload)

    def _delete(self, path: str, access_token: str | None = None) -> dict:
        return self._request("DELETE", path, access_token=access_token)

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
