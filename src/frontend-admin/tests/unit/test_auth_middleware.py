"""
Unit tests for app/middleware/auth_middleware.py  (admin frontend)

Tests run inside an active Flask request context so session / url_for work.
The decorated view functions are light stubs — we only care about whether
the middleware allows through or redirects/aborts.
"""
import pytest
from unittest.mock import patch
from flask import session

from app.middleware.auth_middleware import login_required, role_required


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stub_view(*args, **kwargs):
    """Minimal view function used as the decorated target."""
    return "OK", 200


def _set_session(client, role: str, access_token: str = "tok"):
    """Directly write auth keys into the test client session."""
    with client.session_transaction() as sess:
        sess["access_token"] = access_token
        sess["user_id"] = "uid-1"
        sess["email"] = "a@a.com"
        sess["full_name"] = ""
        sess["role"] = role


# ---------------------------------------------------------------------------
# login_required
# ---------------------------------------------------------------------------

class TestLoginRequired:
    def test_redirects_when_no_session(self, app, client):
        """Unauthenticated request must redirect to auth.login."""
        with app.test_request_context("/some-page"):
            from flask import session as req_sess
            resp = login_required(_stub_view)()
        # login_required returns a redirect response
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_redirects_when_role_is_user(self, app):
        """A plain 'user' role must be rejected even with a valid token."""
        with app.test_request_context("/some-page"):
            from flask import session as req_sess
            req_sess["access_token"] = "tok"
            req_sess["user_id"] = "uid-u"
            req_sess["email"] = "u@e.com"
            req_sess["full_name"] = ""
            req_sess["role"] = "user"
            resp = login_required(_stub_view)()
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_passes_when_role_is_admin(self, app):
        """Admin role must be allowed through."""
        with app.test_request_context("/some-page"):
            from flask import session as req_sess
            req_sess["access_token"] = "tok"
            req_sess["user_id"] = "uid-a"
            req_sess["email"] = "a@a.com"
            req_sess["full_name"] = ""
            req_sess["role"] = "admin"
            result = login_required(_stub_view)()
        assert result == ("OK", 200)

    def test_passes_when_role_is_operator(self, app):
        """Operator role must also be allowed through."""
        with app.test_request_context("/some-page"):
            from flask import session as req_sess
            req_sess["access_token"] = "tok"
            req_sess["user_id"] = "uid-op"
            req_sess["email"] = "op@a.com"
            req_sess["full_name"] = ""
            req_sess["role"] = "operator"
            result = login_required(_stub_view)()
        assert result == ("OK", 200)


# ---------------------------------------------------------------------------
# role_required
# ---------------------------------------------------------------------------

class TestRoleRequired:
    def test_redirects_to_login_when_not_authenticated(self, app):
        with app.test_request_context("/restricted"):
            resp = role_required("admin")(_stub_view)()
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_redirects_to_dashboard_when_wrong_role(self, app):
        """Operator trying to access an admin-only route → redirect to dashboard."""
        with app.test_request_context("/admin-only"):
            from flask import session as req_sess
            req_sess["access_token"] = "tok"
            req_sess["user_id"] = "uid-op"
            req_sess["email"] = "op@a.com"
            req_sess["full_name"] = ""
            req_sess["role"] = "operator"
            resp = role_required("admin")(_stub_view)()
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_allows_matching_role(self, app):
        """Admin accessing admin-only route → passes."""
        with app.test_request_context("/admin-only"):
            from flask import session as req_sess
            req_sess["access_token"] = "tok"
            req_sess["user_id"] = "uid-a"
            req_sess["email"] = "a@a.com"
            req_sess["full_name"] = ""
            req_sess["role"] = "admin"
            result = role_required("admin")(_stub_view)()
        assert result == ("OK", 200)

    def test_allows_multiple_roles(self, app):
        """role_required('admin', 'operator') should allow both."""
        for role in ("admin", "operator"):
            with app.test_request_context("/shared"):
                from flask import session as req_sess
                req_sess["access_token"] = "tok"
                req_sess["user_id"] = "uid-x"
                req_sess["email"] = "x@a.com"
                req_sess["full_name"] = ""
                req_sess["role"] = role
                result = role_required("admin", "operator")(_stub_view)()
            assert result == ("OK", 200), f"Failed for role '{role}'"
