from __future__ import annotations
"""
API client for the user frontend.

All HTTP calls to the backend REST API go through this module.
Raises ``APIError`` on any non-2xx response so callers can handle
errors uniformly with a single except block.

Usage
-----
    from app.utils.api_client import APIClient, APIError
    api = APIClient()
    try:
        data = api.login("user@example.com", "password")
    except APIError as e:
        flash(e.message)
"""
import requests
from flask import current_app


class APIError(Exception):
    """Raised when the backend returns a non-2xx response."""

    def __init__(self, status_code: int, code: str, message: str, details: list = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


class APIClient:
    """Thin wrapper around ``requests`` that targets the backend API."""

    # ------------------------------------------------------------------
    # Auth endpoints
    # ------------------------------------------------------------------

    def register(self, full_name: str, email: str, password: str) -> dict:
        """
        POST /api/v1/auth/register

        Returns the ``data`` dict:
            {"user": {...}, "access_token": "...", "refresh_token": "..."}
        """
        return self._post("/auth/register", {
            "full_name": full_name,
            "email": email,
            "password": password,
        })

    def login(self, email: str, password: str) -> dict:
        """
        POST /api/v1/auth/login

        Returns the ``data`` dict:
            {"access_token": "...", "refresh_token": "..."}
        """
        return self._post("/auth/login", {"email": email, "password": password})

    def logout(self, access_token: str, refresh_token: str) -> None:
        """
        POST /api/v1/auth/logout  (requires Bearer access token)
        POST /api/v1/auth/refresh is NOT called here — we just discard
        the refresh token on the client side.
        """
        self._post("/auth/logout", {}, access_token=access_token)

    def refresh_tokens(self, refresh_token: str) -> dict:
        """
        POST /api/v1/auth/refresh  (requires Bearer refresh token)

        Returns:
            {"access_token": "...", "refresh_token": "..."}
        """
        return self._post("/auth/refresh", {}, access_token=refresh_token)

    def forgot_password(self, email: str) -> dict:
        """POST /api/v1/auth/forgot-password"""
        return self._post("/auth/forgot-password", {"email": email})

    def reset_password(self, token: str, new_password: str) -> dict:
        """POST /api/v1/auth/reset-password"""
        return self._post("/auth/reset-password", {
            "token": token,
            "new_password": new_password,
        })

    # ------------------------------------------------------------------
    # Jobs endpoints
    # ------------------------------------------------------------------

    def get_jobs(self, access_token: str | None = None, **params) -> dict:
        """GET /api/v1/jobs — paginated + filtered job list."""
        return self._get("/jobs", access_token=access_token, params=params or None)

    def get_job(self, slug: str, access_token: str | None = None) -> dict:
        """GET /api/v1/jobs/<slug> — job detail."""
        return self._get(f"/jobs/{slug}", access_token=access_token)

    # ------------------------------------------------------------------
    # User / profile endpoints
    # ------------------------------------------------------------------

    def get_profile(self, access_token: str) -> dict:
        """GET /api/v1/users/profile"""
        return self._get("/users/profile", access_token=access_token)

    def update_profile(self, access_token: str, payload: dict) -> dict:
        """PUT /api/v1/users/profile"""
        return self._put("/users/profile", payload, access_token=access_token)

    def get_applications(self, access_token: str, page: int = 1) -> dict:
        """GET /api/v1/users/applications"""
        return self._get("/users/applications", access_token=access_token, params={"page": page})

    def apply_to_job(self, access_token: str, job_id: str) -> dict:
        """POST /api/v1/users/applications"""
        return self._post("/users/applications", {"job_id": job_id}, access_token=access_token)

    def withdraw_application(self, access_token: str, application_id: str) -> dict:
        """DELETE /api/v1/users/applications/<id>"""
        return self._delete(f"/users/applications/{application_id}", access_token=access_token)

    # ------------------------------------------------------------------
    # Notifications endpoints
    # ------------------------------------------------------------------

    def get_notifications(self, access_token: str, page: int = 1) -> dict:
        """GET /api/v1/notifications"""
        return self._get("/notifications", access_token=access_token, params={"page": page})

    def get_notification_count(self, access_token: str) -> dict:
        """GET /api/v1/notifications/count"""
        return self._get("/notifications/count", access_token=access_token)

    def mark_notification_read(self, access_token: str, notification_id: str) -> dict:
        """PUT /api/v1/notifications/<id>/read"""
        return self._put(f"/notifications/{notification_id}/read", {}, access_token=access_token)

    def mark_all_read(self, access_token: str) -> dict:
        """PUT /api/v1/notifications/read-all"""
        return self._put("/notifications/read-all", {}, access_token=access_token)

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
            raise APIError(504, "GATEWAY_TIMEOUT", "The server took too long to respond. Please try again.")
        
        # Check for token rotation header before handling response
        self._check_token_rotation(resp)
        
        return self._handle_response(resp)
    
    def _check_token_rotation(self, resp: requests.Response) -> None:
        """
        Check if backend rotated the access token (X-New-Access-Token header).
        If present, update the session automatically.
        """
        new_token = resp.headers.get('X-New-Access-Token')
        if new_token:
            try:
                from flask import session
                if 'access_token' in session:
                    session['access_token'] = new_token
                    current_app.logger.info("Access token automatically rotated")
            except RuntimeError:
                # Not in request context (e.g., background task)
                pass

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
        """
        Parse the JSON response. On success returns ``response["data"]``.
        On error raises ``APIError`` with the backend error details.
        """
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
