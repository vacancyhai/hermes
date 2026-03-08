"""
Unit tests for app/utils/session_manager.py

All tests use MockSession — a dict subclass with a .permanent attribute —
because save_login_session sets `flask_session.permanent = True`, which
raises AttributeError on a bare dict.
"""
import base64
import json

import pytest

from app.utils.session_manager import (
    _decode_jwt_payload,
    clear_session,
    get_access_token,
    get_refresh_token,
    get_user_data,
    is_authenticated,
    save_login_session,
    update_tokens,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class MockSession(dict):
    """A plain dict that also accepts .permanent attribute assignment."""
    permanent = False


def _make_jwt(payload: dict) -> str:
    """Build a syntactically valid (but unsigned) JWT from a payload dict."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{body}.fakesig"


def _login_data(role="user", email="u@example.com", user_id="uid-1"):
    """Mimics backend login response (no user field)."""
    token = _make_jwt({"sub": user_id, "role": role, "email": email})
    return {"access_token": token, "refresh_token": "refresh.tok"}


def _register_data():
    """Mimics backend register response (has user field)."""
    return {
        "user": {"id": "uid-2", "email": "reg@example.com", "full_name": "Reg User", "role": "user"},
        "access_token": "access.tok",
        "refresh_token": "refresh.tok",
    }


# ---------------------------------------------------------------------------
# _decode_jwt_payload
# ---------------------------------------------------------------------------

class TestDecodeJwtPayload:
    def test_decodes_valid_jwt(self):
        token = _make_jwt({"sub": "abc", "role": "user"})
        claims = _decode_jwt_payload(token)
        assert claims["sub"] == "abc"
        assert claims["role"] == "user"

    def test_raises_on_malformed_jwt(self):
        with pytest.raises(ValueError, match="Malformed JWT"):
            _decode_jwt_payload("not.a.valid.jwt.with.too.many.parts")

    def test_raises_on_single_segment(self):
        with pytest.raises(ValueError):
            _decode_jwt_payload("onlyone")

    def test_handles_unpadded_base64(self):
        # Real JWTs often have payload without padding — must not raise
        payload = {"sub": "x"}
        raw = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        # strip padding to simulate real JWT
        raw = raw.rstrip("=")
        token = f"hdr.{raw}.sig"
        assert _decode_jwt_payload(token)["sub"] == "x"


# ---------------------------------------------------------------------------
# save_login_session — login path (no user field)
# ---------------------------------------------------------------------------

class TestSaveLoginSession:
    def test_saves_tokens_from_login_response(self):
        sess = MockSession()
        save_login_session(sess, _login_data())
        assert sess["access_token"] is not None
        assert sess["refresh_token"] == "refresh.tok"

    def test_decodes_user_id_from_jwt(self):
        sess = MockSession()
        save_login_session(sess, _login_data(user_id="uid-99"))
        assert sess["user_id"] == "uid-99"

    def test_decodes_role_from_jwt(self):
        sess = MockSession()
        save_login_session(sess, _login_data(role="admin"))
        assert sess["role"] == "admin"

    def test_decodes_email_from_jwt(self):
        sess = MockSession()
        save_login_session(sess, _login_data(email="a@b.com"))
        assert sess["email"] == "a@b.com"

    def test_full_name_empty_for_login(self):
        # Login JWT has no full_name claim — stored as empty string
        sess = MockSession()
        save_login_session(sess, _login_data())
        assert sess["full_name"] == ""

    def test_saves_user_field_from_register_response(self):
        sess = MockSession()
        save_login_session(sess, _register_data())
        assert sess["user_id"] == "uid-2"
        assert sess["email"] == "reg@example.com"
        assert sess["full_name"] == "Reg User"
        assert sess["role"] == "user"

    def test_marks_session_permanent(self):
        sess = MockSession()
        save_login_session(sess, _login_data())
        assert sess.permanent is True  # Flask sets session.permanent attribute


# ---------------------------------------------------------------------------
# update_tokens
# ---------------------------------------------------------------------------

class TestUpdateTokens:
    def test_replaces_both_tokens(self):
        sess = MockSession({"access_token": "old_access", "refresh_token": "old_refresh"})
        update_tokens(sess, "new_access", "new_refresh")
        assert sess["access_token"] == "new_access"
        assert sess["refresh_token"] == "new_refresh"


# ---------------------------------------------------------------------------
# clear_session
# ---------------------------------------------------------------------------

class TestClearSession:
    def test_removes_all_session_keys(self):
        sess = MockSession()
        save_login_session(sess, _login_data())
        assert sess["access_token"]  # sanity
        clear_session(sess)
        for key in ("access_token", "refresh_token", "user_id", "email", "full_name", "role"):
            assert key not in sess

    def test_safe_on_empty_session(self):
        # Should not raise if called on an already-empty session
        clear_session(MockSession())


# ---------------------------------------------------------------------------
# is_authenticated
# ---------------------------------------------------------------------------

class TestIsAuthenticated:
    def test_false_when_session_empty(self):
        assert is_authenticated(MockSession()) is False

    def test_false_when_no_access_token_key(self):
        assert is_authenticated(MockSession({"user_id": "x"})) is False

    def test_true_when_access_token_present(self):
        assert is_authenticated(MockSession({"access_token": "tok"})) is True

    def test_false_after_clear(self):
        sess = MockSession()
        save_login_session(sess, _login_data())
        clear_session(sess)
        assert is_authenticated(sess) is False


# ---------------------------------------------------------------------------
# get_access_token / get_refresh_token
# ---------------------------------------------------------------------------

class TestGetTokens:
    def test_get_access_token_returns_none_when_empty(self):
        assert get_access_token(MockSession()) is None

    def test_get_refresh_token_returns_none_when_empty(self):
        assert get_refresh_token(MockSession()) is None

    def test_get_access_token_returns_value(self):
        sess = MockSession()
        save_login_session(sess, _login_data())
        assert get_access_token(sess) == sess["access_token"]

    def test_get_refresh_token_returns_value(self):
        sess = MockSession()
        save_login_session(sess, _login_data())
        assert get_refresh_token(sess) == "refresh.tok"


# ---------------------------------------------------------------------------
# get_user_data
# ---------------------------------------------------------------------------

class TestGetUserData:
    def test_returns_none_when_not_authenticated(self):
        assert get_user_data(MockSession()) is None

    def test_returns_dict_with_all_fields(self):
        sess = MockSession()
        save_login_session(sess, _login_data(user_id="uid-7", role="user", email="x@y.com"))
        data = get_user_data(sess)
        assert data["user_id"] == "uid-7"
        assert data["role"] == "user"
        assert data["email"] == "x@y.com"
        assert "full_name" in data
