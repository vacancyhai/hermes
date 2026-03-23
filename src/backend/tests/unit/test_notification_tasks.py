"""Unit tests for notification Celery tasks.

All external I/O (DB, SMTP, Firebase) is mocked. Tasks run synchronously via .run().
"""

import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, call


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

    with patch("app.tasks.notifications.settings") as s, \
         patch("smtplib.SMTP", return_value=mock_server):
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

    with patch("app.tasks.notifications.settings") as s, \
         patch("smtplib.SMTP", return_value=mock_server):
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
    with patch("app.tasks.notifications.settings") as s, \
         patch("smtplib.SMTP", side_effect=ConnectionRefusedError("refused")):
        s.MAIL_ENABLED = True
        s.MAIL_USE_TLS = False
        s.MAIL_SERVER = "bad-server"
        s.MAIL_PORT = 25
        s.MAIL_USERNAME = None
        s.MAIL_DEFAULT_SENDER = "noreply@example.com"

        from app.tasks.notifications import _send_smtp
        import pytest
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
    with patch("app.tasks.notifications._render_email", return_value="<h1>Hi</h1>") as mock_render, \
         patch("app.tasks.notifications._send_smtp", return_value=True) as mock_smtp:
        from app.tasks.notifications import send_email_notification
        send_email_notification.run("user@test.com", "Test", "welcome.html", {"name": "Bob"})

    mock_render.assert_called_once_with("welcome.html", {"name": "Bob"})
    mock_smtp.assert_called_once_with("user@test.com", "Test", "<h1>Hi</h1>")


# ─── send_new_job_notifications ───────────────────────────────────────────────

def _session_ctx_for_notifications(job_row=None, profiles=None):
    """Create mock Session context manager with configurable query results."""
    session = MagicMock()
    results = []

    if job_row:
        r1 = MagicMock()
        r1.fetchone.return_value = job_row
        results.append(r1)
    else:
        r1 = MagicMock()
        r1.fetchone.return_value = None
        results.append(r1)

    if profiles is not None:
        r2 = MagicMock()
        r2.fetchall.return_value = profiles
        results.append(r2)

    result_iter = iter(results)
    session.execute.side_effect = lambda *a, **kw: next(result_iter)

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx, session


def test_send_new_job_notifications_job_not_found():
    """Exits early when job doesn't exist."""
    ctx, session = _session_ctx_for_notifications(job_row=None)
    with patch("app.tasks.notifications.Session", return_value=ctx):
        from app.tasks.notifications import send_new_job_notifications
        send_new_job_notifications("non-existent-job-id")
    session.commit.assert_not_called()


def test_send_new_job_notifications_no_followers():
    """Exits early when no followers of the org."""
    job_row = ("job-id", "Test Job", "test-job-slug", "UPSC", None)
    ctx, session = _session_ctx_for_notifications(job_row=job_row, profiles=[])
    with patch("app.tasks.notifications.Session", return_value=ctx):
        from app.tasks.notifications import send_new_job_notifications
        send_new_job_notifications("job-id")
    session.commit.assert_not_called()


def test_send_new_job_notifications_with_followers():
    """Queues notifications for followers when a new job is posted."""
    job_row = ("job-id", "UPSC IAS 2024", "upsc-ias-2024", "UPSC", None)
    user_id = str(uuid.uuid4())
    profiles = [(user_id,)]

    session = MagicMock()
    job_result = MagicMock()
    job_result.fetchone.return_value = job_row
    profiles_result = MagicMock()
    profiles_result.fetchall.return_value = profiles

    side_effects = [job_result, profiles_result]
    session.execute.side_effect = side_effects

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications.smart_notify") as mock_notify:
        mock_notify.delay = MagicMock()
        from app.tasks.notifications import send_new_job_notifications
        send_new_job_notifications("job-id")

    # Should queue smart_notify for each follower
    mock_notify.delay.assert_called_once()


# ─── notify_priority_subscribers ──────────────────────────────────────────────

def test_notify_priority_subscribers_job_not_found():
    """Exits early when job doesn't exist."""
    session = MagicMock()
    result = MagicMock()
    result.fetchone.return_value = None
    session.execute.return_value = result

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx):
        from app.tasks.notifications import notify_priority_subscribers
        notify_priority_subscribers("bad-job-id")

    session.commit.assert_not_called()


def test_notify_priority_subscribers_no_apps():
    """Exits early when no priority trackers."""
    session = MagicMock()
    job_result = MagicMock()
    job_result.fetchone.return_value = ("job-id", "SSC CGL", "ssc-cgl", "SSC")
    apps_result = MagicMock()
    apps_result.fetchall.return_value = []

    session.execute.side_effect = [job_result, apps_result]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx):
        from app.tasks.notifications import notify_priority_subscribers
        notify_priority_subscribers("job-id")

    session.commit.assert_not_called()


def test_notify_priority_subscribers_with_trackers():
    """Queues notifications for priority trackers."""
    user_id = str(uuid.uuid4())
    session = MagicMock()
    job_result = MagicMock()
    job_result.fetchone.return_value = ("job-id", "SSC CGL", "ssc-cgl", "SSC")
    apps_result = MagicMock()
    apps_result.fetchall.return_value = [(user_id,)]

    session.execute.side_effect = [job_result, apps_result]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications.smart_notify") as mock_notify:
        mock_notify.delay = MagicMock()
        from app.tasks.notifications import notify_priority_subscribers
        notify_priority_subscribers("job-id")

    # Should queue smart_notify for each priority tracker
    mock_notify.delay.assert_called_once()


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
    user_pref_result = MagicMock()
    user_pref_result.fetchone.return_value = ("user@test.com", "Test User", {})

    empty_result = MagicMock()
    empty_result.fetchall.return_value = []

    # 3 REMINDER_DAYS: first call returns apps, rest empty
    call_sequence = [
        apps_result,         # T-7 apps
        notif_check_result,  # check if already notified
        MagicMock(),         # insert notification
        user_pref_result,    # _queue_email_for_user
        empty_result,        # T-3 apps
        empty_result,        # T-1 apps
    ]
    session.execute.side_effect = call_sequence

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications.send_email_notification") as mock_email:
        mock_email.delay = MagicMock()
        from app.tasks.notifications import send_deadline_reminders
        send_deadline_reminders()

    # Notification was inserted
    assert session.execute.call_count >= 4


# ─── _queue_email_for_user ─────────────────────────────────────────────────────

def test_queue_email_for_user_user_not_found():
    """Does nothing when user doesn't exist."""
    session = MagicMock()
    result = MagicMock()
    result.fetchone.return_value = None
    session.execute.return_value = result

    with patch("app.tasks.notifications.send_email_notification") as mock_email:
        mock_email.delay = MagicMock()
        from app.tasks.notifications import _queue_email_for_user
        _queue_email_for_user(session, str(uuid.uuid4()), "Subject", "template.html", {})

    mock_email.delay.assert_not_called()


def test_queue_email_for_user_email_disabled():
    """Does nothing when user has email notifications disabled."""
    session = MagicMock()
    result = MagicMock()
    result.fetchone.return_value = ("user@test.com", "Test User", {"email": False})
    session.execute.return_value = result

    with patch("app.tasks.notifications.send_email_notification") as mock_email:
        mock_email.delay = MagicMock()
        from app.tasks.notifications import _queue_email_for_user
        _queue_email_for_user(session, str(uuid.uuid4()), "Subject", "template.html", {})

    mock_email.delay.assert_not_called()


def test_queue_email_for_user_email_enabled():
    """Queues email task when user has email notifications enabled (default)."""
    session = MagicMock()
    result = MagicMock()
    result.fetchone.return_value = ("user@test.com", "Test User", {})  # No explicit disable
    session.execute.return_value = result

    with patch("app.tasks.notifications.send_email_notification") as mock_email:
        mock_email.delay = MagicMock()
        from app.tasks.notifications import _queue_email_for_user
        _queue_email_for_user(session, str(uuid.uuid4()), "Subject", "template.html", {"key": "val"})

    mock_email.delay.assert_called_once()


def test_queue_email_for_user_explicit_email_enabled():
    """Queues email when user explicitly set email=True in preferences."""
    session = MagicMock()
    result = MagicMock()
    result.fetchone.return_value = ("user@test.com", "Test User", {"email": True})
    session.execute.return_value = result

    with patch("app.tasks.notifications.send_email_notification") as mock_email:
        mock_email.delay = MagicMock()
        from app.tasks.notifications import _queue_email_for_user
        _queue_email_for_user(session, str(uuid.uuid4()), "Subject", "template.html", {})

    mock_email.delay.assert_called_once()


# ─── send_push_notification task ──────────────────────────────────────────────

def test_send_push_notification_no_firebase_config():
    """Exits early when FIREBASE_CREDENTIALS_PATH is not set."""
    with patch("app.tasks.notifications.settings") as s:
        s.FIREBASE_CREDENTIALS_PATH = None
        from app.tasks.notifications import send_push_notification
        # Should return without error
        send_push_notification.run("user-id", "Title", "Body", {})


# ─── smart_notify task ────────────────────────────────────────────────────────

def test_smart_notify_calls_service_send():
    """smart_notify delegates to NotificationService.send and returns notification_id."""
    user_id = str(uuid.uuid4())
    mock_notif_id = str(uuid.uuid4())

    mock_svc = MagicMock()
    mock_svc.send.return_value = mock_notif_id

    session = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications._get_sync_redis", return_value=MagicMock()), \
         patch("app.tasks.notifications.NotificationService", return_value=mock_svc):
        from app.tasks.notifications import smart_notify
        smart_notify(
            user_id=user_id,
            title="New Job Alert",
            message="A job was posted",
            notification_type="new_job_from_followed_org",
        )

    mock_svc.send.assert_called_once()
    call_kwargs = mock_svc.send.call_args[1]
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["title"] == "New Job Alert"


def test_smart_notify_staggered_mode():
    """smart_notify passes delivery_mode='staggered' to NotificationService.send."""
    mock_svc = MagicMock()
    mock_svc.send.return_value = str(uuid.uuid4())

    session = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications._get_sync_redis", return_value=MagicMock()), \
         patch("app.tasks.notifications.NotificationService", return_value=mock_svc):
        from app.tasks.notifications import smart_notify
        smart_notify(
            user_id=str(uuid.uuid4()),
            title="Test",
            message="msg",
            notification_type="system",
            delivery_mode="staggered",
        )

    call_kwargs = mock_svc.send.call_args[1]
    assert call_kwargs["delivery_mode"] == "staggered"


# ─── deliver_delayed_email task ───────────────────────────────────────────────

def test_deliver_delayed_email_calls_send_email():
    """deliver_delayed_email calls NotificationService._send_email then commits."""
    mock_svc = MagicMock()

    session = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications._get_sync_redis", return_value=MagicMock()), \
         patch("app.tasks.notifications.NotificationService", return_value=mock_svc):
        from app.tasks.notifications import deliver_delayed_email
        deliver_delayed_email(
            notification_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            subject="Job Alert",
            template_name="new_job_alert.html",
            context={"job_title": "SSC CGL"},
        )

    mock_svc._send_email.assert_called_once()
    session.commit.assert_called_once()


# ─── deliver_delayed_whatsapp task ────────────────────────────────────────────

def test_deliver_delayed_whatsapp_calls_send_whatsapp():
    """deliver_delayed_whatsapp calls NotificationService._send_whatsapp then commits."""
    mock_svc = MagicMock()

    session = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications._get_sync_redis", return_value=MagicMock()), \
         patch("app.tasks.notifications.NotificationService", return_value=mock_svc):
        from app.tasks.notifications import deliver_delayed_whatsapp
        deliver_delayed_whatsapp(
            notification_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            title="New Job",
            message="A job was posted for you.",
        )

    mock_svc._send_whatsapp.assert_called_once()
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
    app_row = (str(_uuid.uuid4()), user_id, job_id, "Test Job", "test-job", "UPSC", deadline)

    session = MagicMock()
    apps_result = MagicMock()
    apps_result.fetchall.return_value = [app_row]
    existing_result = MagicMock()
    existing_result.fetchone.return_value = (1,)  # Already notified!
    empty_result = MagicMock()
    empty_result.fetchall.return_value = []

    session.execute.side_effect = [apps_result, existing_result, empty_result, empty_result]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications.smart_notify") as mock_notify:
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
    app_row = (str(_uuid.uuid4()), user_id, job_id, "Test Job", "test-job", "UPSC", deadline)

    session = MagicMock()
    empty_result = MagicMock()
    empty_result.fetchall.return_value = []
    apps_result = MagicMock()
    apps_result.fetchall.return_value = [app_row]
    no_existing = MagicMock()
    no_existing.fetchone.return_value = None

    # T-7: empty, T-3: empty, T-1: matches
    session.execute.side_effect = [empty_result, empty_result, apps_result, no_existing]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications.smart_notify") as mock_notify:
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
    app_row = (str(_uuid.uuid4()), user_id, job_id, "Test Job", "test-job", "SSC", deadline)

    session = MagicMock()
    empty_result = MagicMock()
    empty_result.fetchall.return_value = []
    apps_result = MagicMock()
    apps_result.fetchall.return_value = [app_row]
    no_existing = MagicMock()
    no_existing.fetchone.return_value = None

    # T-7: empty, T-3: matches, T-1: empty
    session.execute.side_effect = [empty_result, apps_result, no_existing, empty_result]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.notifications.Session", return_value=ctx), \
         patch("app.tasks.notifications.smart_notify") as mock_notify:
        mock_notify.delay = MagicMock()
        from app.tasks.notifications import send_deadline_reminders
        send_deadline_reminders()

    mock_notify.delay.assert_called_once()
    kwargs = mock_notify.delay.call_args[1]
    assert kwargs["priority"] == "high"
    assert "3 days" in kwargs["title"]
