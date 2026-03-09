from __future__ import annotations
"""
Session manager for the admin frontend.

Identical structure to the user frontend session_manager; kept as a
separate module so future admin-specific session keys can be added
without coupling the two frontends.
"""
import base64
import json

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
    admin login.

    Login response: {"user": {...}, "access_token": "...", "refresh_token": "..."}
    """
    access_token = api_data["access_token"]
    refresh_token = api_data["refresh_token"]

    if "user" in api_data:
        user = api_data["user"]
        user_id = user["id"]
        email = user["email"]
        full_name = user.get("full_name", "")
        role = user["role"]
    else:
        claims = _decode_jwt_payload(access_token)
        user_id = claims["sub"]
        email = claims.get("email", "")
        full_name = ""
        role = claims.get("role", "")

    flask_session["user_id"] = user_id
    flask_session["email"] = email
    flask_session["full_name"] = full_name
    flask_session["role"] = role
    flask_session["access_token"] = access_token
    flask_session["refresh_token"] = refresh_token
    flask_session.permanent = True


def update_tokens(flask_session, access_token: str, refresh_token: str) -> None:
    flask_session["access_token"] = access_token
    flask_session["refresh_token"] = refresh_token


def clear_session(flask_session) -> None:
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
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed JWT")
    payload = parts[1]
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += "=" * padding
    return json.loads(base64.urlsafe_b64decode(payload))
