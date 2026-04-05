"""Direct unit tests for notification route handlers with mocked dependencies."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_current_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    return user, {"user_type": "user"}


def _make_notif(user_id=None, is_read=False):
    n = MagicMock()
    n.id = uuid.uuid4()
    n.user_id = user_id or uuid.uuid4()
    n.type = "system"
    n.title = "Test"
    n.message = "Body"
    n.is_read = is_read
    n.priority = "medium"
    n.sent_via = ["in_app"]
    n.action_url = None
    n.entity_type = None
    n.entity_id = None
    n.read_at = None
    n.created_at = datetime.now(timezone.utc)
    n.expires_at = datetime.now(timezone.utc)
    return n


# ─── list_notifications ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_notifications_empty():
    from app.routers.notifications import list_notifications

    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_notifications(
        limit=20,
        offset=0,
        type=None,
        is_read=None,
        current_user=_make_current_user(),
        db=db,
    )
    assert output["pagination"]["total"] == 0
    assert output["data"] == []


@pytest.mark.asyncio
async def test_list_notifications_with_data():
    from app.routers.notifications import list_notifications

    user, _ = _make_current_user()
    n = _make_notif(user_id=user.id)

    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = [n]
    db.execute.side_effect = [count_result, data_result]

    output = await list_notifications(
        limit=20,
        offset=0,
        type=None,
        is_read=None,
        current_user=(user, {}),
        db=db,
    )
    assert output["pagination"]["total"] == 1
    assert len(output["data"]) == 1


@pytest.mark.asyncio
async def test_list_notifications_with_type_filter():
    from app.routers.notifications import list_notifications

    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_notifications(
        limit=20,
        offset=0,
        type="deadline_reminder",
        is_read=None,
        current_user=_make_current_user(),
        db=db,
    )
    assert output["data"] == []


@pytest.mark.asyncio
async def test_list_notifications_with_is_read_filter():
    from app.routers.notifications import list_notifications

    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_notifications(
        limit=20,
        offset=0,
        type=None,
        is_read=False,
        current_user=_make_current_user(),
        db=db,
    )
    assert output["pagination"]["has_more"] is False


# ─── unread_count ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unread_count_zero():
    from app.routers.notifications import unread_count

    db = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = 0
    db.execute.return_value = result

    output = await unread_count(current_user=_make_current_user(), db=db)
    assert output["count"] == 0


@pytest.mark.asyncio
async def test_unread_count_with_unreads():
    from app.routers.notifications import unread_count

    db = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = 3
    db.execute.return_value = result

    output = await unread_count(current_user=_make_current_user(), db=db)
    assert output["count"] == 3


# ─── mark_all_read ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mark_all_read_zero():
    from app.routers.notifications import mark_all_read

    db = AsyncMock()
    result = MagicMock()
    result.rowcount = 0
    db.execute.return_value = result

    output = await mark_all_read(current_user=_make_current_user(), db=db)
    assert output["updated"] == 0


@pytest.mark.asyncio
async def test_mark_all_read_some():
    from app.routers.notifications import mark_all_read

    db = AsyncMock()
    result = MagicMock()
    result.rowcount = 5
    db.execute.return_value = result

    output = await mark_all_read(current_user=_make_current_user(), db=db)
    assert output["updated"] == 5
    assert "5" in output["message"]


# ─── mark_read ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mark_read_not_found():
    from app.routers.notifications import mark_read
    from fastapi import HTTPException

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await mark_read(
            notification_id=uuid.uuid4(),
            current_user=_make_current_user(),
            db=db,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_mark_read_wrong_user():
    from app.routers.notifications import mark_read
    from fastapi import HTTPException

    user, _ = _make_current_user()
    n = _make_notif(user_id=uuid.uuid4())  # different user_id

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = n
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await mark_read(
            notification_id=n.id,
            current_user=(user, {}),
            db=db,
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_mark_read_success():
    from app.routers.notifications import mark_read

    user, _ = _make_current_user()
    n = _make_notif(user_id=user.id, is_read=False)

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = n
    db.execute.return_value = result

    output = await mark_read(
        notification_id=n.id,
        current_user=(user, {}),
        db=db,
    )
    assert n.is_read is True


@pytest.mark.asyncio
async def test_mark_read_already_read():
    """Already read notification: no change to read_at, still returns 200."""
    from app.routers.notifications import mark_read

    user, _ = _make_current_user()
    n = _make_notif(user_id=user.id, is_read=True)
    original_read_at = n.read_at

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = n
    db.execute.return_value = result

    await mark_read(notification_id=n.id, current_user=(user, {}), db=db)
    # already read, so read_at shouldn't be updated
    assert n.read_at == original_read_at


# ─── delete_notification ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_notification_not_found():
    from app.routers.notifications import delete_notification
    from fastapi import HTTPException

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await delete_notification(
            notification_id=uuid.uuid4(),
            current_user=_make_current_user(),
            db=db,
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_notification_wrong_user():
    from app.routers.notifications import delete_notification
    from fastapi import HTTPException

    user, _ = _make_current_user()
    n = _make_notif(user_id=uuid.uuid4())

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = n
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await delete_notification(
            notification_id=n.id,
            current_user=(user, {}),
            db=db,
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_notification_success():
    from app.routers.notifications import delete_notification

    user, _ = _make_current_user()
    n = _make_notif(user_id=user.id)

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = n
    db.execute.return_value = result
    db.delete = AsyncMock()

    await delete_notification(
        notification_id=n.id,
        current_user=(user, {}),
        db=db,
    )
    db.delete.assert_called_once_with(n)


# ─── has_more pagination edge case ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_notifications_has_more_true():
    """has_more is True when total > offset + limit."""
    from app.routers.notifications import list_notifications

    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 50  # total=50
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_notifications(
        limit=20,
        offset=0,
        type=None,
        is_read=None,
        current_user=_make_current_user(),
        db=db,
    )
    # offset(0) + limit(20) = 20 < total(50) → has_more = True
    assert output["pagination"]["has_more"] is True


@pytest.mark.asyncio
async def test_list_notifications_has_more_false_when_last_page():
    """has_more is False on the last page."""
    from app.routers.notifications import list_notifications

    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 5  # total=5
    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []
    db.execute.side_effect = [count_result, data_result]

    output = await list_notifications(
        limit=20,
        offset=0,
        type=None,
        is_read=None,
        current_user=_make_current_user(),
        db=db,
    )
    # offset(0) + limit(20) = 20 >= total(5) → has_more = False
    assert output["pagination"]["has_more"] is False
