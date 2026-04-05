# Testing

## Run Tests

```bash
# Backend — unit tests only (coverage XML written to /app/coverage.xml automatically)
docker exec hermes_backend python -m pytest tests/unit/ -q

# Backend — all tests (unit + integration + security + e2e)
docker exec hermes_backend python -m pytest tests/ -q

# Backend — integration tests only
docker exec hermes_backend python -m pytest tests/integration/ -q

# User frontend
docker exec -w /app hermes_frontend python -m pytest tests/ --cov=app --cov-report=term-missing -q

# Admin frontend
docker exec -w /app hermes_frontend_admin python -m pytest tests/ --cov=app --cov-report=term-missing -q
```

> **Coverage is automatic:** `src/backend/pytest.ini` sets `addopts = --cov=app --cov-report=xml:/app/coverage.xml --cov-report=term-missing`.
> The XML report at `/app/coverage.xml` is what SonarCloud ingests in CI.

## CI Pipeline (GitHub Actions)

The workflow at `.github/workflows/build.yml` runs on every push to `main` and every pull request.

```
push / PR
  └─► job: test          — builds Docker stack, runs pytest --cov, uploads coverage.xml
        └─► job: sonarcloud  — downloads coverage.xml, runs SonarCloud scan
```

- **Tests must pass** before SonarCloud runs (`needs: test`).
- **Branch protection** on `main` requires both jobs to pass before a PR can merge.
- The CI `.env` is written inline in the workflow — no production secrets in CI.

## Pre-commit Hooks

Hooks run automatically before every `git commit` (installed via `pre-commit install`):

| Hook | Purpose |
|------|---------|
| `trailing-whitespace`, `end-of-file-fixer` | File hygiene |
| `check-yaml`, `check-json`, `check-toml` | Config syntax |
| `check-merge-conflict`, `debug-statements` | Common accidents |
| `black` | Auto-format Python in `src/backend/` |
| `isort` (`--profile=black`) | Sort imports |
| `flake8` + bugbear | Lint (100-char line limit) |
| `mypy` | Type checking (`--ignore-missing-imports`) |
| `detect-secrets` | Block credential leaks |

```bash
# Run all hooks manually across the full repo:
pre-commit run --all-files
```

## Manual Firebase Test Credentials

These phone numbers are configured in **Firebase Console → Authentication → Phone numbers for testing** and bypass real SMS.

| Phone | OTP | Use |
|-------|-----|-----|
| +917777777777 | 123456 | Phone OTP login on `/login` page |

For email/password and Google login, create a new account via the `/login` page or use the Firebase Console to create a test user. Admin accounts are created via `POST /api/v1/admin/admin-users` (after the first admin is seeded directly into the DB — see README.md Quick Start).

---

## Backend — 77% (250 unit tests)

Test suite updated: removed all `UserJobApplication`, `platform_analytics`, `update_user_role`, org-following, `send_new_job_notifications`, and `notify_priority_subscribers` tests (premature features reverted). Added `test_matching_entrance_exams.py` (14 tests) and new coverage-improvement test files for `content.py`, `entrance_exams.py`, `watches.py`, and `dependencies.py`.

| Module | Coverage | Notes |
|--------|----------|-------|
| `routers/notifications.py` | 93% | |
| `routers/watches.py` | 47% | IntegrityError rollback path covered at integration level |
| `routers/jobs.py` | 93% | |
| `routers/users.py` | 100% | |
| `routers/admin.py` | 0% | PDF file-write + Celery dispatch path; covered at integration level |
| `routers/content.py` | 19% | List/get/CRUD public+admin endpoints covered; detail views with parent enrichment covered |
| `routers/entrance_exams.py` | 96% | |
| `routers/auth.py` | 66% | Covered at integration level (Firebase mocking) |
| `dependencies.py` | 97% | JWT decode, blocklist, RBAC fully covered |
| `firebase.py` | 75% | Real Firebase token verify path requires live credentials |
| `services/notifications.py` | 80% | FCM `_send_push` uses `user_devices` table; `_send_fcm_with_status` happy path requires credentials |
| `services/matching.py` | 80% | with-prefs scoring paths covered; no-prefs pagination covered |
| `services/ai_extractor.py` | 0% | Requires live Anthropic API |
| `services/pdf_extractor.py` | 77% | |
| `tasks/notifications.py` | 57% | Firebase FCM send in `smart_notify` requires credentials |
| `tasks/cleanup.py` | 100% | |
| `tasks/jobs.py` | 100% | |
| `tasks/seo.py` | 68% | |
| `models/*` / `schemas/*` | 100% | |

### Backend Test Files

| File | Tests | Covers |
|------|-------|--------|
| `unit/test_route_admin.py` | 26 | Dashboard stats, jobs CRUD, user mgmt, audit logs |
| `unit/test_route_notifications.py` | 17 | List, mark read/all, delete, has_more pagination |
| `unit/test_route_users.py` | 12 | Profile, phone, FCM tokens |
| `unit/test_route_jobs.py` | 7 | Listing filters (active-only default), recommended, detail |
| `unit/test_route_content.py` | 44 | Admit cards, answer keys, results — public list/detail + admin CRUD; `_validate_document_parent` |
| `unit/test_route_entrance_exams.py` | 28 | Public list (filters, pagination, search) + detail; admin list/get/create (slug collision, published_at)/update/delete |
| `unit/test_route_watches.py` | 17 | Watch/unwatch jobs & exams (limit enforcement, duplicate guard); list_watched (empty, job-only, exam-only, mixed) |
| `unit/test_dependencies.py` | 27 | `_decode_and_validate_token` (valid, expired, wrong type, blocklist, scope); `get_current_user/admin`; `require_admin/operator` |
| `unit/test_matching.py` | 14 | Job recommendation scoring (state, category, education, age, recency) |
| `unit/test_matching_entrance_exams.py` | 14 | Entrance exam recommendation scoring |
| `unit/test_services.py` | 10 | PDF extraction, AI parsing |
| `unit/test_tasks.py` | 9 | Cleanup, close_expired_job_listings, job extraction |
| `unit/test_notification_tasks.py` | 16 | Deadline reminders (7/3/1 day), smart_notify, delayed delivery |
| `unit/test_notification_service.py` | 22 | NotificationService: all channels (`_send_push` via `user_devices`, fingerprint dedup, `_send_fcm`), prefs, email limits |
| `integration/test_auth.py` | 20 | Firebase verify-token (new/existing/migrate/suspended/deleted/phone-only), logout (blocklist check via `/notifications`), refresh, admin login/logout/refresh, RBAC |
| `integration/test_auth_extended.py` | 21 | Email OTP registration, password validation, password set/change, phone verification, email linking |
| `integration/test_admin.py` | 14 | Admin API, stats, RBAC |
| `integration/test_jobs.py` | 17 | Public job listing and search (active-only filter) |
| `integration/test_users.py` | 18 | User profile API |
| `integration/test_notifications.py` | 20 | Notification API |
| `security/test_security.py` | 14 | JWT structure (HS256/exp/iat/jti), RBAC, token revocation, admin bcrypt, XSS, SQLi, CORS |
| `e2e/test_user_flow.py` | 3 | Admin job lifecycle, user management, RBAC operator-vs-admin |

### Backend Unit Test Strategy

Route handlers are called **directly as async functions** with `AsyncMock` db sessions, bypassing HTTP/ASGI entirely. This avoids SQLAlchemy's internal greenlet switches that cause `coverage.py` to lose trace context after `await db.execute()` calls.

`NotificationService` tests mock the synchronous SQLAlchemy `Session` and all external I/O (FCM, SMTP, Redis) so they run without any live services.

Tasks that use **lazy imports** (e.g. `smart_notify`, `deliver_delayed_email`, `deliver_delayed_whatsapp`) are tested by patching `app.services.notifications.NotificationService` at its source module rather than on the tasks module (since the class is imported inside the function body at call-time).

Firebase tests mock `app.firebase.verify_id_token` via `unittest.mock.patch` so they run without live Firebase credentials. The `user_token` fixture now uses `create_access_token()` directly instead of calling the removed `/auth/login` endpoint.

### Why Some Backend Lines Are Uncovered

- **`routers/auth.py`** — Firebase-dependent paths covered at integration level; OAuth and OTP flows require live credentials.
- **`routers/watches.py`** — IntegrityError rollback and ordering-by-creation-date reassembly paths covered at integration level.
- **`routers/content.py`** — Recommend endpoints and some detail enrichment paths are covered; remaining uncovered lines are in rarely-reached branches (e.g. both-job-and-exam parent edge cases).
- **`firebase.py`** — real `verify_id_token()` call requires a live Firebase project; the init guard (`firebase_admin._apps`) is covered by unit tests.
- **`routers/admin.py`** — PDF file-write + Celery dispatch block; covered at integration level.
- **`tasks/notifications.py`** — Firebase FCM send in `smart_notify` requires `FIREBASE_CREDENTIALS_PATH`, absent in the test environment. Stubs `send_new_job_notifications` and `notify_priority_subscribers` are no-ops.
- **`services/notifications.py`** — `_send_fcm_with_status` happy path and the new `_send_push` (reads `user_devices` with fingerprint dedup) require Firebase credentials for the FCM leg; `_send_fcm` wrapper and no-credentials path are covered.
- **`services/ai_extractor.py`** — requires live Anthropic API credentials.
- **`tasks/seo.py`** — sitemap file-write path requires filesystem setup.

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

Flask `test_client()` with `app.api_client` replaced by a `MagicMock`. No real backend or Firebase calls are made. Auth-required routes are tested both with and without a session token.

All POST form tests must include `csrf_token` in the form data (or set it in `session` before the request). The `/auth/firebase-callback` endpoint is exempt from CSRF validation (it receives a JSON body authenticated by the Firebase ID token).

The `conftest.py` includes a session-scoped `truncate_all_tables` autouse fixture that truncates all tables before the test session starts, preventing stale data from prior runs from causing test failures. The truncation list covers all 13 tables: `notification_delivery_log`, `notifications`, `user_watches`, `user_devices`, `admin_logs`, `admit_cards`, `answer_keys`, `results`, `jobs`, `entrance_exams`, `user_profiles`, `users`, `admin_users`.

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
| `integration/test_routes.py` | 70 | All routes: dashboard (analytics for admin vs operator), jobs, new job, job delete, PDF extraction, draft review, users, user detail, role management, logs |

### Why Some Admin Frontend Lines Are Uncovered

- **`api_client.py:63–69`** — `patch()` method exists for completeness but no admin frontend route currently calls it.
