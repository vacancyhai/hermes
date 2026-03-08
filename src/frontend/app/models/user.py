"""
User model for Flask-Login.

This is a session-backed proxy — it holds data decoded from the JWT and
stored in the Flask session at login time. There is no database lookup here;
the backend API is the source of truth.
"""
from flask_login import UserMixin


class User(UserMixin):
    """Represents the currently-logged-in user, populated from session data."""

    def __init__(self, user_id: str, email: str, full_name: str, role: str):
        # Flask-Login uses get_id() which returns self.id
        self.id = user_id
        self.email = email
        self.full_name = full_name
        self.role = role

    @staticmethod
    def from_session(data: dict) -> "User":
        """Reconstruct a User from the dict stored in Flask session."""
        return User(
            user_id=data["user_id"],
            email=data["email"],
            full_name=data.get("full_name", ""),
            role=data["role"],
        )
