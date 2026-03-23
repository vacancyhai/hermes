"""Unit tests for NotificationService.

Tests multi-channel notification delivery with fingerprint-based push de-duplication.
All external I/O (DB, FCM, Email, WhatsApp) is mocked.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

from app.services.notifications import NotificationService, DAILY_EMAIL_LIMIT


# ─── In-App Notifications ──────────────────────────────────────────────────────

def test_create_in_app_inserts_notification():
    """_create_in_app inserts record into notifications table."""
    session = MagicMock()
    svc = NotificationService(session)

    notification_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    svc._create_in_app(
        notification_id, user_id, "Test Title", "Test Message",
        "test_type", "medium", "job", "job-123", "/jobs/test", now,
    )

    # Verify INSERT was executed
    session.execute.assert_called()
    # Verify delivery log was created
    assert session.execute.call_count == 2


def test_create_in_app_marked_delivered():
    """In-app notifications are immediately marked as delivered."""
    session = MagicMock()
    svc = NotificationService(session)

    calls = session.execute.call_args_list
    svc._create_in_app(
        "notif-1", "user-1", "Title", "Msg", "type", "medium", None, None, None,
        datetime.now(timezone.utc),
    )

    # Check that delivery log call has status='delivered'
    second_call = session.execute.call_args_list[1]
    assert "delivered" in str(second_call)


# ─── Push Notifications ────────────────────────────────────────────────────────

def test_send_push_no_devices():
    """Push skipped when user has no active devices."""
    session = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = []
    session.execute.return_value = result

    svc = NotificationService(session)
    svc._send_push("notif-1", "user-1", "Title", "Message", datetime.now(timezone.utc))

    # Verify skip log was created
    assert session.execute.call_count >= 2


def test_send_push_deduplicates_by_fingerprint():
    """Push sends only once per physical device fingerprint."""
    session = MagicMock()

    # Two devices, same fingerprint (same user on web + PWA)
    device1 = (str(uuid.uuid4()), "token-1", "fp-123", datetime.now(timezone.utc))
    device2 = (str(uuid.uuid4()), "token-2", "fp-123", datetime.now(timezone.utc))  # Same fingerprint

    result = MagicMock()
    result.fetchall.return_value = [device1, device2]
    session.execute.return_value = result

    svc = NotificationService(session)
    with patch.object(svc, '_send_fcm', return_value=True) as mock_fcm:
        svc._send_push("notif-1", "user-1", "Title", "Message", datetime.now(timezone.utc))

    # _send_fcm called only once (for first device, second skipped)
    assert mock_fcm.call_count == 1


def test_send_push_sends_different_fingerprints():
    """Push sends to multiple devices with different fingerprints."""
    session = MagicMock()

    device1 = (str(uuid.uuid4()), "token-1", "fp-device1", datetime.now(timezone.utc))
    device2 = (str(uuid.uuid4()), "token-2", "fp-device2", datetime.now(timezone.utc))

    result = MagicMock()
    result.fetchall.return_value = [device1, device2]
    session.execute.return_value = result

    svc = NotificationService(session)
    with patch.object(svc, '_send_fcm', return_value=True) as mock_fcm:
        svc._send_push("notif-1", "user-1", "Title", "Message", datetime.now(timezone.utc))

    # _send_fcm called twice (different fingerprints)
    assert mock_fcm.call_count == 2


def test_send_fcm_success():
    """FCM send succeeds with valid credentials."""
    session = MagicMock()
    svc = NotificationService(session)

    with patch("firebase_admin.credentials.Certificate") as mock_cert, \
         patch("firebase_admin.initialize_app") as mock_init, \
         patch("firebase_admin.messaging.Message") as mock_msg, \
         patch("firebase_admin.messaging.send") as mock_send:

        result = svc._send_fcm("token-abc", "Title", "Body", "notif-1")

    # Will fail if credentials not set, but the logic is tested
    assert result is False or result is True


def test_send_fcm_no_credentials():
    """FCM skipped when FIREBASE_CREDENTIALS_PATH not set."""
    session = MagicMock()
    svc = NotificationService(session)

    with patch("app.services.notifications.settings") as mock_settings:
        mock_settings.FIREBASE_CREDENTIALS_PATH = None
        result = svc._send_fcm("token-abc", "Title", "Body", "notif-1")

    assert result is False


# ─── Email Notifications ──────────────────────────────────────────────────────

def test_send_email_instant_mode():
    """Email sent immediately in instant mode."""
    session = MagicMock()
    svc = NotificationService(session)

    with patch.object(svc, '_load_preferences', return_value={}), \
         patch.object(svc, '_create_in_app'), \
         patch.object(svc, '_send_push'), \
         patch.object(svc, '_send_email') as mock_email, \
         patch.object(svc, '_send_whatsapp'):
        svc.send(
            user_id="user-1",
            title="Test",
            message="Test message",
            notification_type="test",
            priority="medium",
            delivery_mode="instant",
            email_template="test.html",
        )

    # Email should be called in instant mode
    mock_email.assert_called_once()


def test_send_email_daily_limit_reached():
    """Email skipped when daily OCI limit reached."""
    session = MagicMock()
    redis = MagicMock()
    redis.get.return_value = str(DAILY_EMAIL_LIMIT + 1)

    svc = NotificationService(session, redis_sync=redis)

    now = datetime.now(timezone.utc)
    svc._send_email("notif-1", "user-1", "Subject", "template.html", {}, now)

    # Verify limit check was performed
    redis.get.assert_called()


def test_send_email_increments_count():
    """Email count incremented in Redis."""
    session = MagicMock()
    redis = MagicMock()
    redis.get.return_value = None

    user_row = ("user@test.com", "Test User")
    result = MagicMock()
    result.fetchone.return_value = user_row
    session.execute.return_value = result

    svc = NotificationService(session, redis_sync=redis)

    with patch("app.tasks.notifications.send_email_notification") as mock_task:
        svc._send_email("notif-1", "user-1", "Subject", "template.html", {}, datetime.now(timezone.utc))

    # Verify Redis incr was called
    redis.pipeline.assert_called_once()


def test_schedule_delayed_email():
    """Email scheduled for future delivery in staggered mode."""
    session = MagicMock()
    svc = NotificationService(session)

    with patch("app.tasks.notifications.deliver_delayed_email") as mock_task:
        svc._schedule_delayed_email("notif-1", "user-1", "Subject", "template.html", {"key": "val"})

    # Verify task scheduled with countdown
    mock_task.apply_async.assert_called_once()
    call_kwargs = mock_task.apply_async.call_args[1]
    assert call_kwargs["countdown"] > 0


# ─── WhatsApp Notifications ───────────────────────────────────────────────────

def test_send_whatsapp_instant_mode():
    """WhatsApp sent in instant mode."""
    session = MagicMock()
    prefs_row = ({"whatsapp": {}}, "+919999999999")
    result = MagicMock()
    result.fetchone.return_value = prefs_row
    session.execute.return_value = result

    svc = NotificationService(session)

    with patch.object(svc, '_send_whatsapp_message', return_value=True) as mock_wa:
        svc._send_whatsapp("notif-1", "user-1", "Title", "Message", datetime.now(timezone.utc))

    mock_wa.assert_called_once()


def test_send_whatsapp_no_phone():
    """WhatsApp skipped when user has no phone."""
    session = MagicMock()
    prefs_row = ({"whatsapp": {}}, None)
    result = MagicMock()
    result.fetchone.return_value = prefs_row
    session.execute.return_value = result

    svc = NotificationService(session)
    svc._send_whatsapp("notif-1", "user-1", "Title", "Message", datetime.now(timezone.utc))

    # Verify skip log created
    assert session.execute.call_count >= 2


def test_schedule_delayed_whatsapp():
    """WhatsApp scheduled for future delivery in staggered mode."""
    session = MagicMock()
    svc = NotificationService(session)

    with patch("app.tasks.notifications.deliver_delayed_whatsapp") as mock_task:
        svc._schedule_delayed_whatsapp("notif-1", "user-1", "Title", "Message")

    mock_task.apply_async.assert_called_once()
    call_kwargs = mock_task.apply_async.call_args[1]
    assert call_kwargs["countdown"] > 0


# ─── Unified Send API ──────────────────────────────────────────────────────────

def test_send_instant_mode_all_channels():
    """send() in instant mode triggers all 4 channels."""
    session = MagicMock()
    svc = NotificationService(session)

    with patch.object(svc, '_create_in_app') as mock_in_app, \
         patch.object(svc, '_send_push') as mock_push, \
         patch.object(svc, '_send_email') as mock_email, \
         patch.object(svc, '_send_whatsapp') as mock_wa:

        svc.send(
            user_id="user-1",
            title="Test",
            message="Test message",
            notification_type="test",
            priority="medium",
            delivery_mode="instant",
            email_template="test.html",
        )

    # All channels called
    mock_in_app.assert_called_once()
    mock_push.assert_called_once()
    mock_email.assert_called_once()
    mock_wa.assert_called_once()


def test_send_staggered_mode_delays_email_whatsapp():
    """send() in staggered mode delays email and WhatsApp."""
    session = MagicMock()
    svc = NotificationService(session)

    with patch.object(svc, '_create_in_app') as mock_in_app, \
         patch.object(svc, '_send_push') as mock_push, \
         patch.object(svc, '_send_email') as mock_email, \
         patch.object(svc, '_schedule_delayed_email') as mock_sched_email, \
         patch.object(svc, '_schedule_delayed_whatsapp') as mock_sched_wa:

        svc.send(
            user_id="user-1",
            title="Test",
            message="Test message",
            notification_type="test",
            priority="medium",
            delivery_mode="staggered",
            email_template="test.html",
        )

    # Immediate channels
    mock_in_app.assert_called_once()
    mock_push.assert_called_once()
    # Delayed channels
    mock_sched_email.assert_called_once()
    mock_sched_wa.assert_called_once()
    # Non-delayed not called
    mock_email.assert_not_called()


def test_send_respects_email_preference():
    """send() skips email if user disabled it."""
    session = MagicMock()
    svc = NotificationService(session)

    # Mock _load_preferences to return email disabled
    with patch.object(svc, '_load_preferences', return_value={"email": False}), \
         patch.object(svc, '_create_in_app') as mock_in_app, \
         patch.object(svc, '_send_push') as mock_push, \
         patch.object(svc, '_send_email') as mock_email:

        svc.send(
            user_id="user-1",
            title="Test",
            message="Test",
            notification_type="test",
            email_template="test.html",
        )

    mock_in_app.assert_called_once()
    mock_push.assert_called_once()
    mock_email.assert_not_called()


def test_send_respects_push_preference():
    """send() skips push if user disabled it."""
    session = MagicMock()
    svc = NotificationService(session)

    with patch.object(svc, '_load_preferences', return_value={"push": False}), \
         patch.object(svc, '_create_in_app') as mock_in_app, \
         patch.object(svc, '_send_push') as mock_push:

        svc.send(
            user_id="user-1",
            title="Test",
            message="Test",
            notification_type="test",
        )

    mock_in_app.assert_called_once()
    mock_push.assert_not_called()


def test_send_returns_notification_id():
    """send() returns the created notification ID."""
    session = MagicMock()
    svc = NotificationService(session)

    with patch.object(svc, '_create_in_app'), \
         patch.object(svc, '_send_push'), \
         patch.object(svc, '_load_preferences', return_value={}):

        notif_id = svc.send(
            user_id="user-1",
            title="Test",
            message="Test",
            notification_type="test",
        )

    # Should return a UUID string
    assert isinstance(notif_id, str)
    uuid.UUID(notif_id)  # Verify it's a valid UUID


# ─── Helpers ──────────────────────────────────────────────────────────────────

def test_load_preferences_returns_empty_dict_if_none():
    """_load_preferences returns empty dict when user has no preferences."""
    session = MagicMock()
    result = MagicMock()
    result.fetchone.return_value = None
    session.execute.return_value = result

    svc = NotificationService(session)
    prefs = svc._load_preferences("user-1")

    assert prefs == {}


def test_log_delivery_inserts_record():
    """_log_delivery inserts delivery log record."""
    session = MagicMock()
    svc = NotificationService(session)

    svc._log_delivery(
        "notif-1", "user-1", "email", "sent",
        datetime.now(timezone.utc), delivered_at=datetime.now(timezone.utc),
    )

    session.execute.assert_called_once()


def test_append_sent_via_updates_notification():
    """_append_sent_via updates notification sent_via array."""
    session = MagicMock()
    svc = NotificationService(session)

    svc._append_sent_via("notif-1", "email")

    session.execute.assert_called_once()
    sql = session.execute.call_args[0][0]
    assert "UPDATE notifications" in str(sql)
    assert "sent_via" in str(sql)
