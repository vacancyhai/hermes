"""Unit tests for notification Celery tasks.

All external I/O (DB, SMTP, Firebase) is mocked. Tasks run synchronously via .run().
"""

import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, call, patch

# ─── _send_smtp ───────────────────────────────────────────────────────────────


def test_send_smtp_mail_disabled():
    """When MAIL_ENABLED=False, email is skipped and False is returned."""
    with patch("app.tasks.notifications.settings") as s:
        s.MAIL_ENABLED = False
        from app.tasks.notifications import _send_smtp

        result = _send_smtp("user@example.com", "Test Subject", "<h1>Hello</h1>")
    assert result is False


def test_send_smtp_success_with_tls():
    """Successful SMTP send via TLS returns True."""
    mock_server = MagicMock()

    with patch("app.tasks.notifications.settings") as s, patch(
        "smtplib.SMTP", return_value=mock_server
    ):
        s.MAIL_ENABLED = True
        s.MAIL_USE_TLS = True
        s.MAIL_SERVER = "smtp.example.com"
        s.MAIL_PORT = 587
        s.MAIL_USERNAME = "user"
        s.MAIL_PASSWORD = "pass"
        s.MAIL_DEFAULT_SENDER = "noreply@example.com"

        from app.tasks.notifications import _send_smtp

        result = _send_smtp("to@example.com", "Subject", "<p>Body</p>")

    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user", "pass")
    mock_server.sendmail.assert_called_once()
    mock_server.quit.assert_called_once()


def test_send_smtp_success_no_tls():
    """SMTP send without TLS (MAIL_USE_TLS=False)."""
    mock_server = MagicMock()

    with patch("app.tasks.notifications.settings") as s, patch(
        "smtplib.SMTP", return_value=mock_server
    ):
        s.MAIL_ENABLED = True
        s.MAIL_USE_TLS = False
        s.MAIL_SERVER = "smtp.example.com"
        s.MAIL_PORT = 25
        s.MAIL_USERNAME = None
        s.MAIL_DEFAULT_SENDER = "noreply@example.com"

        from app.tasks.notifications import _send_smtp

        result = _send_smtp("to@example.com", "Subject", "<p>Body</p>")

    assert result is True
    mock_server.starttls.assert_not_called()
    mock_server.login.assert_not_called()


def test_send_smtp_exception_reraises():
    """SMTP exception is re-raised after logging."""
    with patch("app.tasks.notifications.settings") as s, patch(
        "smtplib.SMTP", side_effect=ConnectionRefusedError("refused")
    ):
        s.MAIL_ENABLED = True
        s.MAIL_USE_TLS = False
        s.MAIL_SERVER = "bad-server"
        s.MAIL_PORT = 25
        s.MAIL_USERNAME = None
        s.MAIL_DEFAULT_SENDER = "noreply@example.com"

        import pytest
        from app.tasks.notifications import _send_smtp

        with pytest.raises(ConnectionRefusedError):
            _send_smtp("to@example.com", "Subject", "<p>body</p>")


# ─── _render_email ─────────────────────────────────────────────────────────────


def test_render_email():
    """Template rendering returns HTML string."""
    mock_template = MagicMock()
    mock_template.render.return_value = "<h1>Test Email</h1>"

    with patch("app.tasks.notifications._jinja_env") as mock_env:
        mock_env.get_template.return_value = mock_template
        from app.tasks.notifications import _render_email

        result = _render_email("test.html", {"key": "value"})

    assert result == "<h1>Test Email</h1>"
    mock_env.get_template.assert_called_once_with("email/test.html")


def test_render_email_sets_base_url():
    """base_url is added to context if not present."""
    mock_template = MagicMock()
    mock_template.render.return_value = "<p>ok</p>"
    captured_kwargs = {}

    def capture_render(**kwargs):
        captured_kwargs.update(kwargs)
        return "<p>ok</p>"

    mock_template.render.side_effect = capture_render

    with patch("app.tasks.notifications._jinja_env") as mock_env:
        mock_env.get_template.return_value = mock_template
        from app.tasks.notifications import _render_email

        _render_email("test.html", {"name": "Alice"})

    assert "base_url" in captured_kwargs


# ─── send_email_notification task ─────────────────────────────────────────────


def test_send_email_notification_success():
    """Happy path: renders template and sends SMTP."""
    with patch(
        "app.tasks.notifications._render_email", return_value="<h1>Hi</h1>"
    ) as mock_render, patch(
        "app.tasks.notifications._send_smtp", return_value=True
    ) as mock_smtp:
        from app.tasks.notifications import send_email_notification

        send_email_notification.run(
            "user@test.com", "Test", "welcome.html", {"name": "Bob"}
        )

    mock_render.assert_called_once_with("welcome.html", {"name": "Bob"})
    mock_smtp.assert_called_once_with("user@test.com", "Test", "<h1>Hi</h1>")


# ─── send_deadline_reminders ───────────────────────────────────────────────────


def test_send_deadline_reminders_no_upcoming():
    """No apps with upcoming deadlines → no notifications created."""
    session = MagicMock()
    # For each of the 3 reminder days (7, 3, 1), return empty apps
    empty_result = MagicMock()
    empty_result.fetchall.return_value = []
    session.execute.return_value = empty_result

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx):
        from app.tasks.notifications import send_deadline_reminders

        send_deadline_reminders()

    # No inserts or commits expected (beyond session management)


def test_send_deadline_reminders_with_apps():
    """Creates notifications for apps with T-7 deadline."""
    user_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    today = date.today()
    deadline = today + timedelta(days=7)

    app_id = str(uuid.uuid4())
    apps_row = (app_id, user_id, job_id, "Test Job", "test-job", "UPSC", deadline)

    session = MagicMock()
    # First day (T-7): return one app, then empty for T-3 and T-1
    apps_result = MagicMock()
    apps_result.fetchall.return_value = [apps_row]
    notif_check_result = MagicMock()
    notif_check_result.fetchone.return_value = None  # No existing notification

    empty_result = MagicMock()
    empty_result.fetchall.return_value = []

    # 3 REMINDER_DAYS × 2 queries (job watches + admission watches) = 6 base calls
    # T-7: job watches → 1 result; notif check; admission watches → empty
    # T-3, T-1: job watches → empty; admission watches → empty
    call_sequence = [
        apps_result,  # T-7 job watches
        notif_check_result,  # check if already notified
        empty_result,  # T-7 admission watches
        empty_result,  # T-3 job watches
        empty_result,  # T-3 admission watches
        empty_result,  # T-1 job watches
        empty_result,  # T-1 admission watches
    ]
    session.execute.side_effect = call_sequence

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), patch(
        "app.tasks.notifications.send_email_notification"
    ) as mock_email:
        mock_email.delay = MagicMock()
        from app.tasks.notifications import send_deadline_reminders

        send_deadline_reminders()

    # Notification was inserted
    assert session.execute.call_count >= 4


# ─── smart_notify task ────────────────────────────────────────────────────────


def test_smart_notify_calls_service_send():
    """smart_notify delegates to NotificationService.send and returns notification_id."""
    user_id = str(uuid.uuid4())
    mock_notif_id = str(uuid.uuid4())

    mock_svc_instance = MagicMock()
    mock_svc_instance.send.return_value = mock_notif_id
    mock_svc_cls = MagicMock(return_value=mock_svc_instance)

    session = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), patch(
        "app.tasks.notifications._get_sync_redis", return_value=MagicMock()
    ), patch("app.services.notifications.NotificationService", mock_svc_cls):
        from app.tasks.notifications import smart_notify

        smart_notify(
            user_id=user_id,
            title="New Job Alert",
            message="A job was posted",
            notification_type="new_job_from_followed_org",
        )

    mock_svc_instance.send.assert_called_once()
    call_kwargs = mock_svc_instance.send.call_args[1]
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["title"] == "New Job Alert"


def test_smart_notify_staggered_mode():
    """smart_notify passes delivery_mode='staggered' to NotificationService.send."""
    mock_svc_instance = MagicMock()
    mock_svc_instance.send.return_value = str(uuid.uuid4())
    mock_svc_cls = MagicMock(return_value=mock_svc_instance)

    session = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), patch(
        "app.tasks.notifications._get_sync_redis", return_value=MagicMock()
    ), patch("app.services.notifications.NotificationService", mock_svc_cls):
        from app.tasks.notifications import smart_notify

        smart_notify(
            user_id=str(uuid.uuid4()),
            title="Test",
            message="msg",
            notification_type="system",
            delivery_mode="staggered",
        )

    call_kwargs = mock_svc_instance.send.call_args[1]
    assert call_kwargs["delivery_mode"] == "staggered"


# ─── deliver_delayed_email task ───────────────────────────────────────────────


def test_deliver_delayed_email_calls_send_email():
    """deliver_delayed_email calls NotificationService._send_email then commits."""
    mock_svc_instance = MagicMock()
    mock_svc_cls = MagicMock(return_value=mock_svc_instance)

    session = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), patch(
        "app.tasks.notifications._get_sync_redis", return_value=MagicMock()
    ), patch("app.services.notifications.NotificationService", mock_svc_cls):
        from app.tasks.notifications import deliver_delayed_email

        deliver_delayed_email(
            notification_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            subject="Job Alert",
            template_name="new_job_alert.html",
            context={"job_title": "SSC CGL"},
        )

    mock_svc_instance._send_email.assert_called_once()
    session.commit.assert_called_once()


# ─── deliver_delayed_whatsapp task ────────────────────────────────────────────


def test_deliver_delayed_whatsapp_calls_send_whatsapp():
    """deliver_delayed_whatsapp calls NotificationService._send_whatsapp then commits."""
    mock_svc_instance = MagicMock()
    mock_svc_cls = MagicMock(return_value=mock_svc_instance)

    session = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), patch(
        "app.tasks.notifications._get_sync_redis", return_value=MagicMock()
    ), patch("app.services.notifications.NotificationService", mock_svc_cls):
        from app.tasks.notifications import deliver_delayed_whatsapp

        deliver_delayed_whatsapp(
            notification_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            title="New Job",
            message="A job was posted for you.",
        )

    mock_svc_instance._send_whatsapp.assert_called_once()
    session.commit.assert_called_once()


# ─── send_deadline_reminders — edge cases ─────────────────────────────────────


def test_send_deadline_reminders_already_notified_skips():
    """De-duplication: if a reminder notification already exists, skip it."""
    import uuid as _uuid

    user_id = str(_uuid.uuid4())
    job_id = str(_uuid.uuid4())
    from datetime import date, timedelta

    today = date.today()
    deadline = today + timedelta(days=7)
    app_row = (
        str(_uuid.uuid4()),
        user_id,
        job_id,
        "Test Job",
        "test-job",
        "UPSC",
        deadline,
    )

    session = MagicMock()
    apps_result = MagicMock()
    apps_result.fetchall.return_value = [app_row]
    existing_result = MagicMock()
    existing_result.fetchone.return_value = (1,)  # Already notified!
    empty_result = MagicMock()
    empty_result.fetchall.return_value = []

    # T-7: job(1 row→already notified), notif_check, admission(empty); T-3: job(empty), admission(empty); T-1: job(empty), admission(empty)
    session.execute.side_effect = [
        apps_result,  # T-7 job watches
        existing_result,  # notif check → already sent
        empty_result,  # T-7 admission watches
        empty_result,  # T-3 job watches
        empty_result,  # T-3 admission watches
        empty_result,  # T-1 job watches
        empty_result,  # T-1 admission watches
    ]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), patch(
        "app.tasks.notifications.smart_notify"
    ) as mock_notify:
        mock_notify.delay = MagicMock()
        from app.tasks.notifications import send_deadline_reminders

        send_deadline_reminders()

    # smart_notify should NOT be called since reminder was already sent
    mock_notify.delay.assert_not_called()


def test_send_deadline_reminders_1d_uses_high_priority():
    """T-1 reminders use priority=high."""
    import uuid as _uuid
    from datetime import date, timedelta

    user_id = str(_uuid.uuid4())
    job_id = str(_uuid.uuid4())
    today = date.today()
    deadline = today + timedelta(days=1)
    app_row = (
        str(_uuid.uuid4()),
        user_id,
        job_id,
        "Test Job",
        "test-job",
        "UPSC",
        deadline,
    )

    session = MagicMock()
    empty_result = MagicMock()
    empty_result.fetchall.return_value = []
    apps_result = MagicMock()
    apps_result.fetchall.return_value = [app_row]
    no_existing = MagicMock()
    no_existing.fetchone.return_value = None

    # T-7: job(empty), admission(empty); T-3: job(empty), admission(empty); T-1: job(1 row), notif_check, admission(empty)
    session.execute.side_effect = [
        empty_result,  # T-7 job watches
        empty_result,  # T-7 admission watches
        empty_result,  # T-3 job watches
        empty_result,  # T-3 admission watches
        apps_result,  # T-1 job watches
        no_existing,  # notif check
        empty_result,  # T-1 admission watches
    ]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), patch(
        "app.tasks.notifications.smart_notify"
    ) as mock_notify:
        mock_notify.delay = MagicMock()
        from app.tasks.notifications import send_deadline_reminders

        send_deadline_reminders()

    mock_notify.delay.assert_called_once()
    kwargs = mock_notify.delay.call_args[1]
    assert kwargs["priority"] == "high"
    assert "Last day" in kwargs["title"]


def test_send_deadline_reminders_3d_uses_high_priority():
    """T-3 reminders also use priority=high."""
    import uuid as _uuid
    from datetime import date, timedelta

    user_id = str(_uuid.uuid4())
    job_id = str(_uuid.uuid4())
    today = date.today()
    deadline = today + timedelta(days=3)
    app_row = (
        str(_uuid.uuid4()),
        user_id,
        job_id,
        "Test Job",
        "test-job",
        "SSC",
        deadline,
    )

    session = MagicMock()
    empty_result = MagicMock()
    empty_result.fetchall.return_value = []
    apps_result = MagicMock()
    apps_result.fetchall.return_value = [app_row]
    no_existing = MagicMock()
    no_existing.fetchone.return_value = None

    # T-7: job(empty), admission(empty); T-3: job(1 row), notif_check, admission(empty); T-1: job(empty), admission(empty)
    session.execute.side_effect = [
        empty_result,  # T-7 job watches
        empty_result,  # T-7 admission watches
        apps_result,  # T-3 job watches
        no_existing,  # notif check
        empty_result,  # T-3 admission watches
        empty_result,  # T-1 job watches
        empty_result,  # T-1 admission watches
    ]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), patch(
        "app.tasks.notifications.smart_notify"
    ) as mock_notify:
        mock_notify.delay = MagicMock()
        from app.tasks.notifications import send_deadline_reminders

        send_deadline_reminders()

    mock_notify.delay.assert_called_once()
    kwargs = mock_notify.delay.call_args[1]
    assert kwargs["priority"] == "high"
    assert "3 days" in kwargs["title"]
