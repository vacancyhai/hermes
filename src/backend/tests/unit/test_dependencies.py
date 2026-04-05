"""Unit tests for FastAPI dependencies (JWT auth, RBAC)."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.config import settings
from app.utils import ALGORITHM


# ── helpers ───────────────────────────────────────────────────────────────────


def _build_token(overrides=None):
    """Create a signed JWT with sensible defaults, optionally overriding fields."""
    payload = {
        "sub": str(uuid.uuid4()),
        "user_type": "user",
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "iat": datetime.now(timezone.utc),
    }
    if overrides:
        payload.update(overrides)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def _creds(token: str) -> HTTPAuthorizationCredentials:
    c = MagicMock(spec=HTTPAuthorizationCredentials)
    c.credentials = token
    return c


def _redis(blocklisted=False):
    r = AsyncMock()
    r.get = AsyncMock(return_value=b"1" if blocklisted else None)
    return r


def _db_with_user(user):
    res = MagicMock()
    res.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute = AsyncMock(return_value=res)
    return db


# ═══════════════════════════════════════════════════════════════
# _decode_and_validate_token
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_decode_valid_user_token():
    from app.dependencies import _decode_and_validate_token
    token = _build_token({"user_type": "user"})
    payload = await _decode_and_validate_token(_creds(token), _redis(), "user")
    assert payload["user_type"] == "user"
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_decode_valid_admin_token():
    from app.dependencies import _decode_and_validate_token
    token = _build_token({"user_type": "admin"})
    payload = await _decode_and_validate_token(_creds(token), _redis(), "admin")
    assert payload["user_type"] == "admin"


@pytest.mark.asyncio
async def test_decode_malformed_token_raises_401():
    from app.dependencies import _decode_and_validate_token
    with pytest.raises(HTTPException) as exc:
        await _decode_and_validate_token(_creds("not.a.valid.jwt"), _redis(), "user")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token"


@pytest.mark.asyncio
async def test_decode_wrong_secret_raises_401():
    from app.dependencies import _decode_and_validate_token
    bad_token = jwt.encode(
        {"sub": str(uuid.uuid4()), "user_type": "user", "type": "access", "jti": str(uuid.uuid4())},
        "wrong-secret",
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc:
        await _decode_and_validate_token(_creds(bad_token), _redis(), "user")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_decode_refresh_token_type_raises_401():
    from app.dependencies import _decode_and_validate_token
    token = _build_token({"type": "refresh"})
    with pytest.raises(HTTPException) as exc:
        await _decode_and_validate_token(_creds(token), _redis(), "user")
    assert exc.value.status_code == 401
    assert "type" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_decode_wrong_user_type_raises_403():
    from app.dependencies import _decode_and_validate_token
    token = _build_token({"user_type": "admin"})
    with pytest.raises(HTTPException) as exc:
        await _decode_and_validate_token(_creds(token), _redis(), "user")
    assert exc.value.status_code == 403
    assert "scope" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_decode_blocklisted_jti_raises_401():
    from app.dependencies import _decode_and_validate_token
    token = _build_token({"user_type": "user"})
    with pytest.raises(HTTPException) as exc:
        await _decode_and_validate_token(_creds(token), _redis(blocklisted=True), "user")
    assert exc.value.status_code == 401
    assert "revoked" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_decode_missing_sub_raises_401():
    from app.dependencies import _decode_and_validate_token
    token = _build_token({"sub": ""})
    with pytest.raises(HTTPException) as exc:
        await _decode_and_validate_token(_creds(token), _redis(), "user")
    assert exc.value.status_code == 401


# ═══════════════════════════════════════════════════════════════
# get_current_user
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_current_user_valid_returns_tuple():
    from app.dependencies import get_current_user
    user_id = uuid.uuid4()
    token = _build_token({"sub": str(user_id), "user_type": "user"})

    user = MagicMock()
    user.id = user_id
    user.status = "active"

    result_user, payload = await get_current_user(
        credentials=_creds(token),
        db=_db_with_user(user),
        redis=_redis(),
    )
    assert result_user is user
    assert payload["user_type"] == "user"


@pytest.mark.asyncio
async def test_get_current_user_not_found_raises_401():
    from app.dependencies import get_current_user
    token = _build_token({"user_type": "user"})
    with pytest.raises(HTTPException) as exc:
        await get_current_user(
            credentials=_creds(token),
            db=_db_with_user(None),
            redis=_redis(),
        )
    assert exc.value.status_code == 401
    assert "not found" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_get_current_user_suspended_raises_401():
    from app.dependencies import get_current_user
    token = _build_token({"user_type": "user"})

    user = MagicMock()
    user.status = "suspended"

    with pytest.raises(HTTPException) as exc:
        await get_current_user(
            credentials=_creds(token),
            db=_db_with_user(user),
            redis=_redis(),
        )
    assert exc.value.status_code == 401
    assert "inactive" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_get_current_user_invalid_token_raises_401():
    from app.dependencies import get_current_user
    with pytest.raises(HTTPException) as exc:
        await get_current_user(
            credentials=_creds("garbage"),
            db=_db_with_user(None),
            redis=_redis(),
        )
    assert exc.value.status_code == 401


# ═══════════════════════════════════════════════════════════════
# get_current_admin
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_current_admin_valid_returns_tuple():
    from app.dependencies import get_current_admin
    admin_id = uuid.uuid4()
    token = _build_token({"sub": str(admin_id), "user_type": "admin"})

    admin = MagicMock()
    admin.id = admin_id
    admin.status = "active"

    result_admin, payload = await get_current_admin(
        credentials=_creds(token),
        db=_db_with_user(admin),
        redis=_redis(),
    )
    assert result_admin is admin
    assert payload["user_type"] == "admin"


@pytest.mark.asyncio
async def test_get_current_admin_not_found_raises_401():
    from app.dependencies import get_current_admin
    token = _build_token({"user_type": "admin"})
    with pytest.raises(HTTPException) as exc:
        await get_current_admin(
            credentials=_creds(token),
            db=_db_with_user(None),
            redis=_redis(),
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_admin_inactive_raises_401():
    from app.dependencies import get_current_admin
    token = _build_token({"user_type": "admin"})

    admin = MagicMock()
    admin.status = "inactive"

    with pytest.raises(HTTPException) as exc:
        await get_current_admin(
            credentials=_creds(token),
            db=_db_with_user(admin),
            redis=_redis(),
        )
    assert exc.value.status_code == 401
    assert "inactive" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_get_current_admin_wrong_token_scope_raises_403():
    from app.dependencies import get_current_admin
    # user-scoped token used for admin endpoint
    token = _build_token({"user_type": "user"})
    with pytest.raises(HTTPException) as exc:
        await get_current_admin(
            credentials=_creds(token),
            db=_db_with_user(None),
            redis=_redis(),
        )
    assert exc.value.status_code == 403


# ═══════════════════════════════════════════════════════════════
# require_admin
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_require_admin_with_admin_role_passes():
    from app.dependencies import require_admin
    admin = MagicMock()
    admin.role = "admin"
    result = await require_admin(current_admin=(admin, {}))
    assert result is admin


@pytest.mark.asyncio
async def test_require_admin_with_operator_role_raises_403():
    from app.dependencies import require_admin
    admin = MagicMock()
    admin.role = "operator"
    with pytest.raises(HTTPException) as exc:
        await require_admin(current_admin=(admin, {}))
    assert exc.value.status_code == 403
    assert "admin" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_require_admin_with_viewer_role_raises_403():
    from app.dependencies import require_admin
    admin = MagicMock()
    admin.role = "viewer"
    with pytest.raises(HTTPException) as exc:
        await require_admin(current_admin=(admin, {}))
    assert exc.value.status_code == 403


# ═══════════════════════════════════════════════════════════════
# require_operator
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_require_operator_with_admin_role_passes():
    from app.dependencies import require_operator
    admin = MagicMock()
    admin.role = "admin"
    result = await require_operator(current_admin=(admin, {}))
    assert result is admin


@pytest.mark.asyncio
async def test_require_operator_with_operator_role_passes():
    from app.dependencies import require_operator
    admin = MagicMock()
    admin.role = "operator"
    result = await require_operator(current_admin=(admin, {}))
    assert result is admin


@pytest.mark.asyncio
async def test_require_operator_with_viewer_role_raises_403():
    from app.dependencies import require_operator
    admin = MagicMock()
    admin.role = "viewer"
    with pytest.raises(HTTPException) as exc:
        await require_operator(current_admin=(admin, {}))
    assert exc.value.status_code == 403
    assert "operator" in exc.value.detail.lower()
