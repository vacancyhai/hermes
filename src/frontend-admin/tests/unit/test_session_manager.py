"""
Unit tests for app/utils/session_manager.py  (admin frontend)

Identical coverage to the user frontend — kept separate so admin-specific
session fields added in future stories can be tested here.
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
    permanent = False


def _make_jwt(payload: dict) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{body}.fakesig"


def _admin_login_data(role="admin", email="admin@example.com", user_id="uid-a"):
    token = _make_jwt({"sub": user_id, "role": role, "email": email})
    return {"access_token": token, "refresh_token": "refresh.tok"}


# ---------------------------------------------------------------------------
# _decode_jwt_payload
# ---------------------------------------------------------------------------

class TestDecodeJwtPayload:
    def test_decodes_valid_jwt(self):
        token = _make_jwt({"sub": "uid-a", "role": "admin"})
        claims = _decode_jwt_payload(token)
        assert claims["sub"] == "uid-a"
        assert claims["role"] == "admin"

    def test_raises_on_malformed_jwt(self):
        with pytest.raises(ValueError, match="Malformed JWT"):
            _decode_jwt_payload("a.b.c.d")

    def test_raises_on_single_segment(self):
        with pytest.raises(ValueError):
            _decode_jwt_payload("justonething")

    def test_handles_unpadded_base64(self):
        raw = base64.urlsafe_b64encode(json.dumps({"sub": "x"}).encode()).decode().rstrip("=")
        token = f"hdr.{raw}.sig"
        assert _decode_jwt_payload(token)["sub"] == "x"


# ---------------------------------------------------------------------------
# save_login_session
# ---------------------------------------------------------------------------

class TestSaveLoginSession:
    def test_saves_tokens(self):
        sess = MockSession()
        save_login_session(sess, _admin_login_data())
        assert sess["access_token"] is not None
        assert sess["refresh_token"] == "refresh.tok"

    def test_decodes_role_admin(self):
        sess = MockSession()
        save_login_session(sess, _admin_login_data(role="admin"))
        assert sess["role"] == "admin"

    def test_decodes_role_operator(self):
        sess = MockSession()
        save_login_session(sess, _admin_login_data(role="operator"))
        assert sess["role"] == "operator"

    def test_decodes_user_id(self):
        sess = MockSession()
        save_login_session(sess, _admin_login_data(user_id="uid-xyz"))
        assert sess["user_id"] == "uid-xyz"

    def test_marks_permanent(self):
        sess = MockSession()
        save_login_session(sess, _admin_login_data())
        assert sess.permanent is True


# ---------------------------------------------------------------------------
# update_tokens
# ---------------------------------------------------------------------------

class TestUpdateTokens:
    def test_replaces_both_tokens(self):
        sess = MockSession({"access_token": "old", "refresh_token": "old_r"})
        update_tokens(sess, "new_a", "new_r")
        assert sess["access_token"] == "new_a"
        assert sess["refresh_token"] == "new_r"


# ---------------------------------------------------------------------------
# clear_session
# ---------------------------------------------------------------------------

class TestClearSession:
    def test_removes_all_keys(self):
        sess = MockSession()
        save_login_session(sess, _admin_login_data())
        clear_session(sess)
        for key in ("access_token", "refresh_token", "user_id", "email", "full_name", "role"):
            assert key not in sess

    def test_safe_on_empty_session(self):
        clear_session(MockSession())


# ---------------------------------------------------------------------------
# is_authenticated
# ---------------------------------------------------------------------------

class TestIsAuthenticated:
    def test_false_when_empty(self):
        assert is_authenticated(MockSession()) is False

    def test_true_when_token_present(self):
        assert is_authenticated(MockSession({"access_token": "tok"})) is True

    def test_false_after_clear(self):
        sess = MockSession()
        save_login_session(sess, _admin_login_data())
        clear_session(sess)
        assert is_authenticated(sess) is False


# ---------------------------------------------------------------------------
# get_access_token / get_refresh_token
# ---------------------------------------------------------------------------

class TestGetTokens:
    def test_access_none_when_empty(self):
        assert get_access_token(MockSession()) is None

    def test_refresh_none_when_empty(self):
        assert get_refresh_token(MockSession()) is None

    def test_access_returns_value(self):
        sess = MockSession()
        save_login_session(sess, _admin_login_data())
        assert get_access_token(sess) == sess["access_token"]


# ---------------------------------------------------------------------------
# get_user_data
# ---------------------------------------------------------------------------

class TestGetUserData:
    def test_returns_none_when_not_authenticated(self):
        assert get_user_data(MockSession()) is None

    def test_returns_dict(self):
        sess = MockSession()
        save_login_session(sess, _admin_login_data(user_id="uid-a", role="admin", email="a@a.com"))
        data = get_user_data(sess)
        assert data["user_id"] == "uid-a"
        assert data["role"] == "admin"
        assert data["email"] == "a@a.com"
