# Testing

## Run Tests

```bash
# Backend — all tests with coverage
docker exec -w /app hermes_backend pytest tests/ --cov=app --cov-report=term-missing -q

# Backend — unit tests only
docker exec -w /app hermes_backend pytest tests/unit/ -q

# Backend — integration tests only
docker exec -w /app hermes_backend pytest tests/integration/ -q

# User frontend
docker exec -w /app hermes_frontend python -m pytest tests/ --cov=app --cov-report=term-missing -q

# Admin frontend
docker exec -w /app hermes_frontend_admin python -m pytest tests/ --cov=app --cov-report=term-missing -q
```

## Manual Firebase Test Credentials

These phone numbers are configured in **Firebase Console → Authentication → Phone numbers for testing** and bypass real SMS.

| Phone | OTP | Use |
|-------|-----|-----|
| +917777777777 | 123456 | Phone OTP login on `/login` page |

For email/password and Google login, use the accounts in `src/backend/app/data/seed.py` or create a new account via the `/login` page.

---

## Backend — 93% (313 tests)

| Module | Coverage | Notes |
|--------|----------|-------|
| `routers/notifications.py` | 100% | |
| `routers/applications.py` | 97% | IntegrityError rollback path |
| `routers/jobs.py` | 100% | |
| `routers/users.py` | 98% | |
| `routers/admin.py` | 93% | PDF file-write + Celery dispatch path |
| `routers/auth.py` | 92% | Firebase `verify_id_token` uncovered paths; token refresh edge cases |
| `firebase.py` | 69% | Real Firebase token verify path requires live credentials |
| `services/notifications.py` | 89% | Firebase FCM send requires credentials |
| `services/matching.py` | 99% | |
| `services/ai_extractor.py` | 100% | |
| `services/pdf_extractor.py` | 100% | |
| `tasks/notifications.py` | 77% | Firebase push requires credentials |
| `tasks/cleanup.py` | 100% | |
| `tasks/jobs.py` | 89% | |
| `tasks/seo.py` | 100% | |
| `models/*` / `schemas/*` | 100% | |

### Backend Test Files

| File | Tests | Covers |
|------|-------|--------|
| `unit/test_route_admin.py` | 34 | Dashboard stats, jobs CRUD, user mgmt, audit logs |
| `unit/test_route_applications.py` | 17 | Track/list/update/remove applications |
| `unit/test_route_notifications.py` | 15 | List, mark read/all, delete, has_more pagination |
| `unit/test_route_users.py` | 18 | Profile, phone, follow orgs, FCM tokens |
| `unit/test_route_jobs.py` | 7 | Listing filters, recommended, detail |
| `unit/test_matching.py` | 14 | Job recommendation scoring |
| `unit/test_services.py` | 10 | PDF extraction, AI parsing |
| `unit/test_tasks.py` | 12 | Cleanup, sitemap, job extraction |
| `unit/test_notification_tasks.py` | 29 | Email, push, deadline reminders, smart_notify, delayed delivery |
| `unit/test_notification_service.py` | 22 | NotificationService: all 4 channels, prefs, dedup, email limits |
| `integration/test_auth.py` | 19 | Firebase verify-token (new/existing/migrate/suspended/deleted/phone-only), logout, refresh, admin login/logout/refresh, RBAC |
| `integration/test_admin.py` | ~40 | Admin API, analytics, RBAC |
| `integration/test_jobs.py` | ~25 | Public job listing and search |
| `integration/test_users.py` | ~30 | User profile API |
| `integration/test_notifications.py` | ~25 | Notification API |
| `integration/test_applications.py` | ~25 | Application tracking API |
| `security/test_security.py` | 17 | JWT structure (HS256/exp/iat/jti), RBAC, token revocation, admin bcrypt, file upload safety, XSS, SQLi, CORS |
| `e2e/test_user_flow.py` | 4 | Full user + admin lifecycle flows (Firebase verify-token) |

### Backend Unit Test Strategy

Route handlers are called **directly as async functions** with `AsyncMock` db sessions, bypassing HTTP/ASGI entirely. This avoids SQLAlchemy's internal greenlet switches that cause `coverage.py` to lose trace context after `await db.execute()` calls.

`NotificationService` tests mock the synchronous SQLAlchemy `Session` and all external I/O (FCM, SMTP, Redis) so they run without any live services.

Tasks that use **lazy imports** (e.g. `smart_notify`, `deliver_delayed_email`, `deliver_delayed_whatsapp`) are tested by patching `app.services.notifications.NotificationService` at its source module rather than on the tasks module (since the class is imported inside the function body at call-time).

Firebase tests mock `app.firebase.verify_id_token` via `unittest.mock.patch` so they run without live Firebase credentials. The `user_token` fixture now uses `create_access_token()` directly instead of calling the removed `/auth/login` endpoint.

### Why Some Backend Lines Are Uncovered

- **`auth.py`** — blocklisted token check + `user.status != "active"` branch in `/refresh` require state that only arises after logout; covered at integration level.
- **`firebase.py`** — real `verify_id_token()` call requires a live Firebase project; the init guard (`firebase_admin._apps`) is covered by unit tests.
- **`admin.py:231–235, 338–351`** — PDF file-write + Celery dispatch block; validation paths (wrong extension/MIME) are covered.
- **`tasks/notifications.py:328–387`** — Firebase legacy push code requires `FIREBASE_CREDENTIALS_PATH`, absent in the test environment.
- **`services/notifications.py:190–191, 221–222`** — FCM `_send_fcm` happy path requires Firebase credentials; no-credentials path is covered.

---

## User Frontend — 91% (80 tests)

| Module | Coverage | Notes |
|--------|----------|-------|
| `app/__init__.py` | 90% | Firebase JS-handled routes (email-verify deep-link, account-link) not exercised |
| `app/api_client.py` | 100% | All HTTP methods covered |

### Frontend Test Files

| File | Tests | Covers |
|------|-------|--------|
| `unit/test_api_client.py` | 17 | `__init__`, `_headers`, `get`, `post`, `put`, `delete`, `patch` |
| `integration/test_routes.py` | 63 | All routes: index, job listing, job detail, dashboard, notifications, login (GET), `/auth/firebase-callback`, logout, profile, org follow/unfollow, recommended jobs, application track/update/delete |

### Frontend Test Strategy

Flask `test_client()` with `app.api_client` replaced by a `MagicMock`. No real backend or Firebase calls are made. Auth-required routes are tested both with and without a session token. The `/auth/firebase-callback` endpoint is tested by posting JSON directly (as the Firebase JS SDK would); no CSRF is needed since it's a JSON API endpoint. Register/forgot-password/reset-password pages are removed — Firebase JS SDK handles these flows entirely client-side.

---

## Admin Frontend — 97% (88 tests)

| Module | Coverage | Notes |
|--------|----------|-------|
| `app/__init__.py` | 97% | All routes covered; `patch()` in api_client unused |
| `app/api_client.py` | 94% | `patch()` method not used by any admin route |

### Admin Frontend Test Files

| File | Tests | Covers |
|------|-------|--------|
| `unit/test_api_client.py` | 18 | All methods including `post_file` (timeout, headers, files) |
| `integration/test_routes.py` | 70 | All routes: dashboard (analytics for admin vs operator), jobs, new job, job delete, PDF upload, draft review, users, user detail, role management, logs |

### Why Some Admin Frontend Lines Are Uncovered

- **`api_client.py:63–69`** — `patch()` method exists for completeness but no admin frontend route currently calls it.
