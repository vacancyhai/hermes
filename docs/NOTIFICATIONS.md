# Notifications

Hermes sends transactional emails and multi-channel notifications (in-app, FCM push, email, WhatsApp).

---

## Email Templates

All templates are in `src/backend/app/templates/email/` and extend `base.html`.

### Active Templates (currently called by code)

| Template | Caller | Trigger | Variables |
|----------|--------|---------|-----------|
| `otp.html` | `auth.py` (sync SMTP via `asyncio.to_thread`) | User requests email OTP during registration or resend-verification | `otp` |
| `welcome.html` | `auth.py` (via Celery `send_email_notification`) | Email/password registration (complete-registration) OR Google OAuth first login (provider != "password") | `name`, `base_url` |
| `phone_added.html` | `users.py` (via Celery) | User updates phone number (`PUT /users/profile/phone`) | `name`, `email`, `phone`, `timestamp`, `base_url` |
| `phone_verified.html` | `users.py` (via Celery) | User verifies phone via Firebase token | `name`, `phone`, `timestamp`, `base_url` |
| `password_set.html` | `users.py` (via Celery) | Google user sets a password (`POST /users/me/set-password`) | `name`, `email`, `timestamp`, `original_method`, `base_url` |
| `password_changed.html` | `users.py` (via Celery) | User changes existing password (`POST /users/me/change-password`) | `name`, `email`, `timestamp`, `base_url` |
| `email_linked.html` | `users.py` (via Celery) | Phone-only user links email+password (`POST /users/me/link-email-password`) | `name`, `email`, `phone`, `timestamp`, `base_url` |
| `deadline_reminder.html` | `tasks/notifications.py` (via Celery `smart_notify`) | 7/3/1 day deadline reminder for tracked jobs/admissions | `title`, `message`, `job_title`, `organization`, `slug`, `deadline` |
| `new_job_alert.html` | `tasks/notifications.py` (via Celery `smart_notify`) | New job posted by an organization a user follows | `job_title`, `organization`, `url` |

> **Note:** Context variables listed are what the calling code passes. Each template may use additional variables from the Jinja2 `base.html` defaults (e.g. `base_url` is always defaulted in `_render_email`).

### Templates Present But Not the Primary Send Path

| Template | Status |
|----------|--------|
| `verification.html` | Not currently called — Firebase manages email verification links |
| `password_reset.html` | Not currently called — Firebase manages password reset links |

---

## OTP Email Flow

OTP emails for registration are sent **synchronously** (not via Celery), using direct SMTP via `asyncio.to_thread(_smtp_send_otp)` inside the `send_email_otp` and `resend_verification` endpoints.

- OTP is a 6-digit cryptographically random number (`secrets.randbelow(1000000)`)
- Stored in Redis as `hermes:email_otp:{email}` with a **5-minute TTL** (`setex 300`)
- Registration data (`full_name`, optional `phone`) stored separately as `hermes:email_otp_data:{email}` (also 5-minute TTL)
- After successful verification (`POST /auth/verify-email-otp`), the OTP is deleted (one-time use)
- A short-lived JWT `verification_token` is returned (5 min, `purpose="email_verified"`)
- `POST /auth/complete-registration` validates this token, retrieves registration data from Redis, creates Firebase user server-side, returns a Firebase `custom_token` for client sign-in

---

## All Other Email and Notification Events

All other notifications are sent asynchronously via Celery using `smart_notify.delay(...)` or `send_email_notification.delay(...)`.

### User Action Emails

| Action | Email Template | Notes |
|--------|---------------|-------|
| Complete registration (email/password) | `welcome.html` | Sent after `complete-registration` |
| Google OAuth first login | `welcome.html` | Only when provider != `"password"` |
| Request email OTP / resend | `otp.html` | Sent synchronously; rate-limited 3/min |
| Set password (Google → email+pass) | `password_set.html` | Via `POST /users/me/set-password` |
| Change existing password | `password_changed.html` | Via `POST /users/me/change-password` |
| Add/update phone number | `phone_added.html` | Via `PUT /users/profile/phone`; marks phone unverified |
| Verify phone | `phone_verified.html` | Via `POST /users/me/verify-phone-otp` |
| Link email to phone-only account | `email_linked.html` | Via `POST /users/me/link-email-password` |

### System Notifications (Celery beat / event-triggered)

| Trigger | Template | Priority | Mode |
|---------|----------|----------|------|
| 7 days before `application_end` (tracked job) | `deadline_reminder.html` | `medium` | staggered |
| 3 days before `application_end` (tracked job) | `deadline_reminder.html` | `high` | staggered |
| 1 day before `application_end` (tracked job) | `deadline_reminder.html` | `high` | staggered |
| 7 days before `application_end` (tracked admission) | `deadline_reminder.html` | `medium` | staggered |
| 3 days before `application_end` (tracked admission) | `deadline_reminder.html` | `high` | staggered |
| 1 day before `application_end` (tracked admission) | `deadline_reminder.html` | `high` | staggered |
| Job/admission updated to `active` (tracked item) | None (in-app + push only) | `medium` | staggered |
| New job from followed organization | `new_job_alert.html` | `medium` | staggered |

**Admin panel actions do not trigger email notifications to affected users.**

---

## Smart Notify — Celery Task Entry Point

All system notifications go through `smart_notify` task → `NotificationService.send()`.

```python
smart_notify.delay(
    user_id="uuid-string",
    title="...",
    message="...",
    notification_type="deadline_reminder_3d",
    priority="high",               # "low" | "medium" | "high"
    entity_type="job",             # optional
    entity_id="uuid-string",       # optional
    action_url="/jobs/ssc-cgl-2026",
    email_template="deadline_reminder.html",  # optional
    email_context={...},           # optional
    delivery_mode="staggered",     # "instant" | "staggered"
)
```

### Delivery Modes

| Mode | In-app | Push | Email | WhatsApp |
|------|--------|------|-------|----------|
| `instant` | T+0 | T+0 | T+0 | T+0 |
| `staggered` | T+0 | T+0 | T+`NOTIFY_EMAIL_DELAY` (default 900s = 15 min) | T+`NOTIFY_WHATSAPP_DELAY` (default 3600s = 1 hr) |

Staggered delayed delivery uses separate Celery tasks `deliver_delayed_email` and `deliver_delayed_whatsapp`.

### Channel Logic

| Channel | Condition | Notes |
|---------|-----------|-------|
| In-app | Always | Inserted into `notifications` table |
| Push | `prefs.get("push") is not False` | Reads from `user_devices` table (active devices with `fcm_token`); de-duplicated by `device_fingerprint`; requires `FIREBASE_CREDENTIALS_PATH` |
| Email | `prefs.get("email") is not False` AND `email_template` provided | Subject to 2700/day OCI soft cap tracked in Redis; reads email from `users` table |
| WhatsApp | `prefs.get("whatsapp") is not False` | Reads phone from `user_profiles.notification_preferences.whatsapp.phone` or `users.phone`; **currently a no-op placeholder** — always returns `False` |

Every channel attempt is logged in `notification_delivery_log` with status: `pending`, `sent`, `delivered`, `failed`, `queued`, `skipped`.

---

## Deadline Reminder Task

`send_deadline_reminders` runs daily at **08:00 UTC** via Celery beat.

For each of T-7, T-3, T-1 days:
1. Queries all tracked jobs where `application_end = today + N`
2. Queries all tracked admissions where `application_end = today + N`
3. De-duplicates by checking `notifications` table for existing `(user_id, entity_id, type)` row
4. Dispatches `smart_notify.delay(...)` for each user

Job status filter: `status = 'active'`. Admission status filter: `status != 'closed'`.

---

## Configuration

Email settings (via `.env`):

```env
MAIL_ENABLED=true/false
MAIL_SERVER=smtp.email.ap-mumbai-1.oci.oraclecloud.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=<OCI SMTP username>
MAIL_PASSWORD=<OCI SMTP auth token>
MAIL_DEFAULT_SENDER=noreply@hermes.com
```

Notification delay settings (seconds):
```env
NOTIFY_EMAIL_DELAY=900      # 15 minutes (staggered email delay)
NOTIFY_WHATSAPP_DELAY=3600  # 1 hour (staggered WhatsApp delay)
```

If `MAIL_ENABLED=false`, all SMTP sends are skipped silently.

---

## Rate Limiting on Auth Email Endpoints

| Endpoint | Limit |
|----------|-------|
| `POST /auth/send-email-otp` | 3/minute per IP |
| `POST /auth/resend-verification` | 3/minute per IP |
| `POST /auth/verify-email-otp` | 5/minute per IP |
