from __future__ import annotations
"""
Session manager for the user frontend.

Stores JWT tokens and basic user info in Flask's server-side session
(Flask-Session writes to filesystem). No sensitive data is sent to the
browser — the session cookie only contains a session ID.

Keys stored in session
----------------------
user_id         str    UUID of the authenticated user
email           str
full_name       str    May be empty until Story 4 profile endpoint exists
role            str    'user' | 'admin' | 'operator'
access_token    str    Short-lived JWT (used as Bearer on every API call)
refresh_token   str    Long-lived JWT (used only to rotate tokens)
"""
import base64
import json

# All keys this module writes so we can clear them cleanly on logout.
_SESSION_KEYS = (
    "user_id",
    "email",
    "full_name",
    "role",
    "access_token",
    "refresh_token",
)


# ---------------------------------------------------------------------------
# Write / clear
# ---------------------------------------------------------------------------

def save_login_session(flask_session, api_data: dict) -> None:
    """
    Persist tokens and user info into the Flask session after a successful
    login or registration API call.

    ``api_data`` is the ``data`` dict from the backend response:
      - For login:    {"user": {...}, "access_token": "...", "refresh_token": "..."}
      - For register: {"user": {...}, "access_token": "...", "refresh_token": "..."}
    """
    access_token = api_data["access_token"]
    refresh_token = api_data["refresh_token"]

    if "user" in api_data:
        # Registration response includes full user object
        user = api_data["user"]
        user_id = user["id"]
        email = user["email"]
        full_name = user.get("full_name", "")
        role = user["role"]
    else:
        # Login response: decode JWT payload to get claims
        claims = _decode_jwt_payload(access_token)
        user_id = claims["sub"]      # flask_jwt_extended uses 'sub' for identity
        email = claims.get("email", "")
        full_name = ""               # not in JWT; populated by Story 4 profile call
        role = claims.get("role", "user")

    flask_session["user_id"] = user_id
    flask_session["email"] = email
    flask_session["full_name"] = full_name
    flask_session["role"] = role
    flask_session["access_token"] = access_token
    flask_session["refresh_token"] = refresh_token
    flask_session.permanent = True


def update_tokens(flask_session, access_token: str, refresh_token: str) -> None:
    """Replace tokens after a successful /auth/refresh call."""
    flask_session["access_token"] = access_token
    flask_session["refresh_token"] = refresh_token


def clear_session(flask_session) -> None:
    """Remove all auth-related keys from the session (called on logout)."""
    for key in _SESSION_KEYS:
        flask_session.pop(key, None)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def is_authenticated(flask_session) -> bool:
    return bool(flask_session.get("access_token"))


def get_access_token(flask_session) -> str | None:
    return flask_session.get("access_token")


def get_refresh_token(flask_session) -> str | None:
    return flask_session.get("refresh_token")


def get_user_data(flask_session) -> dict | None:
    """
    Return a dict with all stored user fields, or None if not logged in.
    """
    if not is_authenticated(flask_session):
        return None
    return {
        "user_id": flask_session.get("user_id"),
        "email": flask_session.get("email"),
        "full_name": flask_session.get("full_name", ""),
        "role": flask_session.get("role"),
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _decode_jwt_payload(token: str) -> dict:
    """
    Base64url-decode the JWT payload section without verifying the signature.

    This is safe because:
    - The token was just issued by our own backend and has not left our
      control between the API response and this decode.
    - The backend verifies the signature on every subsequent request.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed JWT")

    payload = parts[1]
    # Base64url may omit padding — re-add it.
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += "=" * padding

    return json.loads(base64.urlsafe_b64decode(payload))
