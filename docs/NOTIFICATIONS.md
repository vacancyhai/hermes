# Notifications

Hermes sends transactional emails and multi-channel notifications (in-app, FCM push, email, Telegram). This document covers email templates and the notification system.

## Email Templates

All templates are in `src/backend/app/templates/email/` and extend `base.html`.

### Active Templates

| Template | Caller | Trigger | Variables |
|----------|--------|---------|-----------|
| `welcome.html` | `auth.py` | User completes email/password registration OR Google OAuth first login | `name`, `base_url` |
| `otp.html` | `auth.py` (sync SMTP, not Celery) | User requests email OTP during registration | `otp` |
| `email_linked.html` | `auth.py` | Phone-only user links email+password to account | `name`, `email`, `phone`, `timestamp`, `base_url` |
| `phone_added.html` | `users.py` | User adds/updates phone number | `name`, `phone`, `timestamp`, `base_url` |
| `phone_verified.html` | `users.py` | User successfully verifies phone number with OTP | `name`, `phone`, `timestamp`, `base_url` |
| `password_changed.html` | `users.py` | User changes their password | `name`, `timestamp`, `base_url` |
| `deadline_reminder.html` | `tasks/notifications.py` | 7/3/1 day deadline reminder for watched jobs/exams | `name`, `title`, `deadline`, `url` |
| `new_job_alert.html` | `tasks/notifications.py` | New job matching user's org follows or preferences | `name`, `job_title`, `organization`, `url` |

### Standby Templates (Firebase handles these flows)

| Template | Purpose |
|----------|---------|
| `verification.html` | Email verification link — Firebase currently manages this |
| `password_reset.html` | Password reset link — Firebase currently manages this |
| `password_set.html` | Password set confirmation — Firebase currently manages this |

> These templates are kept for potential future custom flows. They are not currently called by any router.

---

## OTP Email Flow

OTP emails for registration are sent **synchronously** (not via Celery) using direct SMTP:

```python
# In auth.py — /auth/send-email-otp
await asyncio.to_thread(_smtp_send_otp, body.email, otp)
```

OTP is stored in Redis with a **5-minute TTL** (`setex(otp_key, 300, otp)`). After successful verification (`/auth/verify-email-otp`), a short-lived JWT verification token (5 min) is returned for use in `/auth/complete-registration`.

---

## Job Alert / Deadline Email Flow

All other emails are sent asynchronously via Celery:

```python
from app.tasks.notifications import send_email_notification

send_email_notification.delay(
    email_address,
    subject,
    template_path,
    context_vars
)
```

---

## Configuration

Email settings in `.env`:

```env
MAIL_ENABLED=true
MAIL_SERVER=mailpit           # Use mailpit for development
MAIL_PORT=1025
MAIL_USE_TLS=false
MAIL_DEFAULT_SENDER=noreply@hermes.example.com
```

- **Development:** Emails captured by Mailpit (web UI at `http://localhost:8025`)
- **Production:** OCI Email Delivery (SMTP port 587, TLS enabled)

---

## Password Requirements

Enforced on all password operations (user and admin):
- **Minimum 8 characters**
- **At least 1 uppercase letter**
- **At least 1 special character** (`!@#$%^&*(),.?":{}|<>`)

Validated server-side via Pydantic schema.

---

## Email Notification Events

### User Actions

| Action | Email Sent | Notes |
|--------|------------|-------|
| Complete registration (email/password) | `welcome.html` | OTP verified before registration |
| Google OAuth first login | `welcome.html` | Only on first login (provider != "password") |
| Request email OTP | `otp.html` | OTP stored 5 min in Redis; rate-limited 3/min |
| Change password | `password_changed.html` | Security notification |
| Add/update phone number | `phone_added.html` | Marks phone as unverified |
| Verify phone with OTP | `phone_verified.html` | Sets `is_phone_verified = true` |
| Link email to phone account | `email_linked.html` | Sets Firebase email provider |
| 7/3/1 day before `application_end` | `deadline_reminder.html` | Sent to all watchers of the job/exam |
| New job from followed organization | `new_job_alert.html` | **Not yet triggered** — `send_new_job_notifications` is a registered Celery task but is a no-op stub (`pass` body). Template exists for future use. |

### Admin Actions

Admin panel actions do not trigger email notifications to affected users (to prevent spam from bulk operations).

---

## Rate Limiting

| Mechanism | Limit |
|-----------|-------|
| `/auth/send-email-otp` endpoint | 3 requests/minute per IP |
| `/auth/verify-email-otp` endpoint | 5 requests/minute per IP |
| OTP validity | 5 minutes (Redis TTL) |
| Celery task queuing | Prevents email server overload |

---

## Testing

1. **Mailpit UI:** `http://localhost:8025` — view all captured emails in dev
2. **Unit tests:** Mock `send_email_notification.delay()` in tests
3. **Integration tests:** Use test database; emails dispatched but not actually sent (`MAIL_ENABLED=false` in `.env.test`)
