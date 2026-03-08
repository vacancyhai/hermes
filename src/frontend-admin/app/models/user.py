"""
User model for Flask-Login — Admin Frontend.

Same session-backed proxy as the user frontend. The admin frontend
additionally enforces that role must be 'admin' or 'operator' before
the session is saved (enforced in auth_middleware.py).
"""
from flask_login import UserMixin


class User(UserMixin):
    """Represents the currently-logged-in admin/operator user."""

    ALLOWED_ROLES = ('admin', 'operator')

    def __init__(self, user_id: str, email: str, full_name: str, role: str):
        self.id = user_id
        self.email = email
        self.full_name = full_name
        self.role = role

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_operator(self) -> bool:
        return self.role == 'operator'

    @staticmethod
    def from_session(data: dict) -> "User":
        return User(
            user_id=data["user_id"],
            email=data["email"],
            full_name=data.get("full_name", ""),
            role=data["role"],
        )
