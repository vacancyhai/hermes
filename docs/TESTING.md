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

---

## Backend — 88% (309 tests)

| Module | Coverage | Notes |
|--------|----------|-------|
| `routers/applications.py` | 96% | |
| `routers/jobs.py` | 100% | |
| `routers/notifications.py` | 100% | |
| `routers/users.py` | 97% | |
| `routers/admin.py` | 92% | PDF file-write + Celery dispatch path |
| `routers/auth.py` | 60% | Token refresh/verify require live Redis |
| `tasks/notifications.py` | 62% | Firebase push, delayed email/WhatsApp |
| `tasks/cleanup.py` | 100% | |
| `tasks/jobs.py` | 89% | |
| `tasks/seo.py` | 100% | |
| `services/matching.py` | 99% | |
| `services/notifications.py` | 82% | FCM fallback, WhatsApp placeholder |
| `services/pdf_extractor.py` | 100% | |
| `services/ai_extractor.py` | 100% | |
| `models/*` / `schemas/*` | 100% | |

### Backend Test Files

| File | Tests | Covers |
|------|-------|--------|
| `unit/test_route_admin.py` | 34 | Dashboard stats, jobs CRUD, user mgmt, audit logs |
| `unit/test_route_applications.py` | 18 | Track/list/update/remove applications |
| `unit/test_route_notifications.py` | 13 | List, mark read/all, delete |
| `unit/test_route_users.py` | 18 | Profile, phone, follow orgs, FCM tokens |
| `unit/test_route_jobs.py` | 7 | Listing filters, recommended, detail |
| `unit/test_matching.py` | 12 | Job recommendation scoring |
| `unit/test_services.py` | 7 | PDF extraction, AI parsing |
| `unit/test_tasks.py` | 12 | Cleanup, sitemap, job extraction |
| `unit/test_notification_tasks.py` | 22 | Email, push, deadline reminders, new job notifications |
| `unit/test_notification_service.py` | **22** | **Multi-channel delivery, FCM de-duplication, email/WhatsApp scheduling** |
| `integration/test_auth.py` | ~30 | Login, register, password reset, email verify |
| `integration/test_admin.py` | ~40 | Admin API, analytics, RBAC |
| `integration/test_jobs.py` | ~25 | Public job listing and search |
| `integration/test_users.py` | ~30 | User profile API |
| `integration/test_notifications.py` | ~25 | Notification API |
| `integration/test_applications.py` | ~25 | Application tracking API |
| `security/test_security.py` | 18 | JWT, RBAC, XSS, SQLi, CORS, file upload |
| `e2e/test_user_flow.py` | 4 | Full user + admin lifecycle flows |

### Backend Unit Test Strategy

Route handlers are called **directly as async functions** with `AsyncMock` db sessions, bypassing HTTP/ASGI entirely. This avoids SQLAlchemy's internal greenlet switches that cause `coverage.py` to lose trace context after `await db.execute()` calls.

### Why Some Backend Lines Are Uncovered

- **`auth.py`** — email verify + password reset endpoints depend on pre-seeded Redis tokens; covered at integration level but not unit.
- **`admin.py`** — PDF file-write + Celery dispatch paths; validation paths (wrong extension/MIME) are covered.
- **`tasks/notifications.py`** — Delayed email/WhatsApp scheduling and legacy FCM code; core multi-channel logic tested via NotificationService unit tests.
- **`services/notifications.py`** — Firebase credentials fallback (82% covered); WhatsApp placeholder returns False; unit tests cover all main code paths.

---

## User Frontend — 100% (96 tests)

| Module | Coverage | Notes |
|--------|----------|-------|
| `app/__init__.py` | 100% | All routes covered |
| `app/api_client.py` | 100% | All HTTP methods covered |

### Frontend Test Files

| File | Tests | Covers |
|------|-------|--------|
| `unit/test_api_client.py` | 17 | `__init__`, `_headers`, `get`, `post`, `put`, `delete`, `patch` |
| `integration/test_routes.py` | 79 | All routes: index, job listing, job detail, dashboard, notifications, login/logout, register, forgot/reset password, verify email, profile, org follow/unfollow, recommended jobs, application track/update/delete |

### Frontend Test Strategy

Flask `test_client()` with `app.api_client` replaced by a `MagicMock`. No real backend calls are made. Auth-required routes are tested both with and without a session token. CSRF-protected routes use `_set_csrf()` helper to pre-populate session token before POSTs.

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
