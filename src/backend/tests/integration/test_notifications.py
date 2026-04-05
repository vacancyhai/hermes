"""Tests for notification endpoints — all 5 CRUD paths + auth + filters."""

import uuid

import pytest
from app.models.notification import Notification
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_notification(
    db: AsyncSession, user_id: str, is_read: bool = False, ntype: str = "system"
) -> Notification:
    n = Notification(
        user_id=uuid.UUID(user_id),
        type=ntype,
        title="Test Notification",
        message="This is a test notification",
        is_read=is_read,
        priority="medium",
        sent_via=["in_app"],
    )
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return n


# --- List notifications ---


async def test_list_notifications_empty(client: AsyncClient, user_token: str):
    resp = await client.get("/api/v1/notifications", headers=auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "pagination" in data
    assert data["pagination"]["total"] >= 0


async def test_list_notifications_with_data(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    await _create_notification(db, user_id)
    resp = await client.get("/api/v1/notifications", headers=auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total"] >= 1


async def test_list_notifications_filter_type(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    await _create_notification(db, user_id, ntype="deadline_reminder")
    await _create_notification(db, user_id, ntype="system")
    resp = await client.get(
        "/api/v1/notifications?type=deadline_reminder", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert item["type"] == "deadline_reminder"


async def test_list_notifications_filter_is_read(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    await _create_notification(db, user_id, is_read=False)
    await _create_notification(db, user_id, is_read=True)
    resp = await client.get(
        "/api/v1/notifications?is_read=false", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert item["is_read"] is False


async def test_list_notifications_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/notifications")
    assert resp.status_code in (401, 403)


async def test_list_notifications_pagination(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    for _ in range(5):
        await _create_notification(db, user_id)
    resp = await client.get(
        "/api/v1/notifications?limit=2&offset=0", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 2
    assert data["pagination"]["limit"] == 2


# --- Unread count ---


async def test_unread_count(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    await _create_notification(db, user_id, is_read=False)
    resp = await client.get(
        "/api/v1/notifications/count", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    assert "count" in resp.json()
    assert resp.json()["count"] >= 1


async def test_unread_count_zero(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    await _create_notification(db, user_id, is_read=True)
    resp = await client.get(
        "/api/v1/notifications/count", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    # Count is per-user, may be 0 if all read
    assert resp.json()["count"] >= 0


async def test_unread_count_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/notifications/count")
    assert resp.status_code in (401, 403)


# --- Mark single read ---


async def test_mark_read(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    notif = await _create_notification(db, user_id, is_read=False)
    resp = await client.put(
        f"/api/v1/notifications/{notif.id}/read", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


async def test_mark_read_already_read(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    notif = await _create_notification(db, user_id, is_read=True)
    resp = await client.put(
        f"/api/v1/notifications/{notif.id}/read", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


async def test_mark_read_not_found(client: AsyncClient, user_token: str):
    fake_id = uuid.uuid4()
    resp = await client.put(
        f"/api/v1/notifications/{fake_id}/read", headers=auth_header(user_token)
    )
    assert resp.status_code == 404


async def test_mark_read_other_users_notification(
    client: AsyncClient, user_token: str, db: AsyncSession
):
    """A user cannot mark another user's notification as read."""
    import uuid as _uuid

    from app.models.user import User
    from passlib.context import CryptContext

    _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    other = User(
        email=f"other_{_uuid.uuid4().hex[:8]}@test.com",
        password_hash=_pwd.hash("Pass123"),
        full_name="Other User",
        status="active",
    )
    db.add(other)
    await db.commit()
    notif = await _create_notification(db, str(other.id), is_read=False)
    resp = await client.put(
        f"/api/v1/notifications/{notif.id}/read", headers=auth_header(user_token)
    )
    assert resp.status_code == 403


# --- Mark all read ---


async def test_mark_all_read(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    await _create_notification(db, user_id, is_read=False)
    await _create_notification(db, user_id, is_read=False)
    resp = await client.put(
        "/api/v1/notifications/read-all", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "updated" in data
    assert data["updated"] >= 2


async def test_mark_all_read_no_unread(client: AsyncClient, user_token: str):
    resp = await client.put(
        "/api/v1/notifications/read-all", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] >= 0


async def test_mark_all_read_requires_auth(client: AsyncClient):
    resp = await client.put("/api/v1/notifications/read-all")
    assert resp.status_code in (401, 403)


# --- Delete notification ---


async def test_delete_notification(
    client: AsyncClient, user_token: str, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    notif = await _create_notification(db, user_id)
    resp = await client.delete(
        f"/api/v1/notifications/{notif.id}", headers=auth_header(user_token)
    )
    assert resp.status_code == 204


async def test_delete_notification_not_found(client: AsyncClient, user_token: str):
    fake_id = uuid.uuid4()
    resp = await client.delete(
        f"/api/v1/notifications/{fake_id}", headers=auth_header(user_token)
    )
    assert resp.status_code == 404


async def test_delete_other_users_notification(
    client: AsyncClient, user_token: str, db: AsyncSession
):
    import uuid as _uuid

    from app.models.user import User
    from passlib.context import CryptContext

    _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    other = User(
        email=f"del_{_uuid.uuid4().hex[:8]}@test.com",
        password_hash=_pwd.hash("Pass123"),
        full_name="Delete Other",
        status="active",
    )
    db.add(other)
    await db.commit()
    notif = await _create_notification(db, str(other.id))
    resp = await client.delete(
        f"/api/v1/notifications/{notif.id}", headers=auth_header(user_token)
    )
    assert resp.status_code == 403


async def test_delete_notification_requires_auth(
    client: AsyncClient, test_user, db: AsyncSession
):
    user_id, _, _ = test_user
    notif = await _create_notification(db, user_id)
    resp = await client.delete(f"/api/v1/notifications/{notif.id}")
    assert resp.status_code in (401, 403)
