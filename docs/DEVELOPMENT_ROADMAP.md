# Hermes — Development Roadmap

> **Last updated**: 2026-03-08 (Story 2 complete)
> **Basis**: Actual code state + GitHub issues #100–#109. Nothing is assumed.

---

## Current State (What Is Actually Done)

### Infrastructure — Complete
- Docker Compose for all three services: backend, frontend, frontend-admin
- PostgreSQL 16 container with 15-table schema defined in Alembic migrations
- Redis 7 container (token blocklist + Celery broker)
- Celery Worker + Celery Beat containers (configured, no tasks yet)
- Nginx container (SSL termination, reverse proxy to backend + user frontend)
- All 8 containers start, pass health checks, and communicate on their named Docker networks
- All three services run with Gunicorn (non-root user, `PYTHONUNBUFFERED=1`)

### Backend — Auth Only
| File | Status |
|---|---|
| `app/routes/auth.py` | ✅ All 7 endpoints implemented (register, login, logout, refresh, forgot-password, reset-password, verify-email) |
| `app/routes/health.py` | ✅ `/api/v1/health` returns 200 |
| `app/routes/jobs.py` | 🟡 Empty blueprint stub |
| `app/routes/users.py` | 🟡 Empty blueprint stub |
| `app/routes/notifications.py` | 🟡 Empty blueprint stub |
| `app/routes/admin.py` | 🟡 Empty blueprint stub |
| `app/services/auth_service.py` | ✅ Register, login, logout, token refresh, password reset, email verification |
| `app/services/job_service.py` | ❌ Does not exist |
| `app/services/user_service.py` | ❌ Does not exist |
| `app/services/notification_service.py` | ❌ Does not exist |
| `app/services/email_service.py` | ❌ Does not exist |
| `app/middleware/auth_middleware.py` | ✅ JWT decode, role check, token rotation |
| `app/middleware/error_handler.py` | ✅ JSON error handlers (400, 401, 403, 404, 500) |
| `app/middleware/rate_limiter.py` | ❌ Does not exist |
| `app/middleware/request_id.py` | ❌ Does not exist |
| `app/validators/auth_validator.py` | ✅ RegisterSchema, LoginSchema, PasswordResetRequestSchema, PasswordResetSchema |
| `app/validators/user_validator.py` | ❌ Does not exist |
| `app/validators/job_validator.py` | ❌ Does not exist |
| `app/utils/__init__.py` | 🟡 Empty file only |
| `app/tasks/celery_app.py` | ✅ Celery configured (no tasks defined yet) |

**Tests**: 74 passing — 22 validator unit tests, 19 service unit tests, 33 route integration tests. All cover auth only.

### User Frontend — Auth Plumbing Complete (Story 2 ✅)
- Docker runs on port 8080, health check at `/health` passes
- Root `/` redirects to `auth.login`
- `app/routes/errors.py` — renders error pages
- `app/routes/main.py` — health + root only
- `app/routes/jobs.py` — empty stub
- `app/routes/profile.py` — empty stub
- `app/routes/admin.py` — empty stub

**Story 2 additions**:
| File | Status |
|---|---|
| `app/models/user.py` | ✅ Flask-Login `UserMixin` proxy (session-backed, no DB) |
| `app/utils/api_client.py` | ✅ `requests` wrapper; raises `APIError` on non-2xx; covers all 6 auth endpoints |
| `app/utils/session_manager.py` | ✅ Save/read/clear tokens + user info; decodes JWT payload for user_id/role |
| `app/middleware/auth_middleware.py` | ✅ `@login_required` decorator |
| `app/__init__.py` | ✅ `load_user()` wired to session via `session_manager` |
| `app/routes/auth.py` | ✅ login, register, logout, forgot-password, reset-password (GET+POST) |

**Still missing** (Story 6):
- Templates — `templates/` directory is still empty
- Static files — `static/` directory is still empty

### Admin Frontend — Auth Plumbing Complete (Story 2 ✅)
- Docker runs on port 8081, health check at `/health` passes
- Root `/` redirects to `auth.login`
- `app/routes/errors.py` — renders error pages
- `app/routes/main.py` — health + root only
- `app/routes/dashboard.py` — empty stub
- `app/routes/jobs.py` — empty stub
- `app/routes/users.py` — empty stub

**Story 2 additions**:
| File | Status |
|---|---|
| `app/models/user.py` | ✅ Flask-Login `UserMixin` proxy; adds `is_admin()` / `is_operator()` helpers |
| `app/utils/api_client.py` | ✅ Same as user frontend; admin-specific endpoints added in Stories 3/4 |
| `app/utils/session_manager.py` | ✅ Same as user frontend |
| `app/middleware/auth_middleware.py` | ✅ `@login_required` + `@role_required(*roles)`; enforces admin/operator on every protected route |
| `app/__init__.py` | ✅ `load_user()` wired to session |
| `app/routes/auth.py` | ✅ login + logout; role decoded from JWT before session save — regular users are rejected and their token is blocklisted |
| `.env` | ✅ Created (was missing) |

**Still missing** (Story 6):
- Templates — `templates/` directory is still empty
- Static files — `static/` directory is still empty

---

## GitHub Issues

| Issue | Story | Priority | Area | Status |
|---|---|---|---|---|
| #100 | Story 2: Frontend Auth & API Client | HIGH | User Frontend + Admin Frontend | ✅ **Done** |
| #101 | Story 3: Backend Job APIs | MEDIUM | Backend | 🟡 Open |
| #102 | Story 4: Backend User Profile APIs | MEDIUM | Backend | 🟡 Open |
| #103 | Story 5: Backend Notification APIs | MEDIUM | Backend | 🟡 Open |
| #104 | Story 6: Frontend Page Routes & Jinja2 Templates | MEDIUM | User Frontend | 🟡 Open |
| #105 | Story 7: Backend Security Middleware | MEDIUM | Backend | 🟡 Open |
| #106 | Story 8: Marshmallow Input Validators | LOW | Backend | 🟡 Open |
| #107 | Story 9: Backend Utilities | LOW | Backend | 🟡 Open |
| #108 | Story 10: Celery Background Tasks | LOW | Backend + Celery | 🟡 Open |
| #109 | Story 11: Test Suite Expansion | LOW | Backend tests (partially done) | 🟡 Open |

---

## Dependencies Between Stories

```
Story 9 (utils/helpers/decorators/constants)
  └─► Story 7 (rate_limiter, RBAC decorator, request ID middleware)
        └─► Story 3 (Job APIs — needs RBAC + rate limiting)
        └─► Story 4 (User Profile APIs — needs RBAC + rate limiting)
        └─► Story 5 (Notification APIs — needs RBAC + rate limiting)
              └─► Story 10 (Celery tasks — needs notification + email service)

Story 8 (Marshmallow validators for user + job schemas)
  └─► Story 3 (Job APIs — needs job validator)
  └─► Story 4 (User Profile APIs — needs user validator)

Story 2 (Frontend API client + session manager + login_required)  ← can start NOW
  └─► Story 6 (Frontend page routes + Jinja2 templates)
        └─► (Also needs Story 3 + Story 4 to have useful data to render)

Story 11 (tests) — runs alongside every story, not a blocker
```

**Story 2 is the only HIGH priority item and does not depend on any pending stories.**
~~It can start immediately because the auth backend is complete.~~ **✅ Completed 2026-03-08.**

---

## Recommended Implementation Order

### Phase 1 — Foundation ✅ Partially done

**Story 2** — Frontend Auth & API Client (Issue #100) ✅ **DONE**

Implemented:
- `src/frontend/app/models/user.py` — Flask-Login `UserMixin` proxy (session-backed)
- `src/frontend/app/utils/api_client.py` — `requests` wrapper for all auth endpoints; raises `APIError` on non-2xx
- `src/frontend/app/utils/session_manager.py` — save/read/clear tokens + user info; decodes JWT payload to extract `user_id`/`role`
- `src/frontend/app/middleware/auth_middleware.py` — `@login_required` decorator
- `src/frontend/app/__init__.py` — `load_user()` wired to session
- `src/frontend/app/routes/auth.py` — login, register, logout, forgot-password, reset-password (GET + POST)
- `src/frontend-admin/app/models/user.py` — same pattern; adds `is_admin()` / `is_operator()`
- `src/frontend-admin/app/utils/api_client.py` — same; no register endpoint
- `src/frontend-admin/app/utils/session_manager.py` — same pattern
- `src/frontend-admin/app/middleware/auth_middleware.py` — `@login_required` + `@role_required(*roles)`
- `src/frontend-admin/app/__init__.py` — `load_user()` wired to session
- `src/frontend-admin/app/routes/auth.py` — login + logout; role checked from JWT before session save; regular-user tokens blocklisted immediately
- `src/frontend-admin/.env` — created (was missing)

**Story 9** — Backend Utilities (Issue #107) 🟡 **NEXT**
- `app/utils/helpers.py` — pagination helper, response formatter, slugify
- `app/utils/decorators.py` — `@admin_required`, `@operator_required` (wraps auth_middleware logic)
- `app/utils/constants.py` — job types, role names, status values, error codes
- Foundation code needed by Stories 3, 4, 5, 7

**Story 8** — Marshmallow Input Validators (Issue #106) 🟡 **NEXT**
- `app/validators/user_validator.py` — profile update schema, notification preference schema
- `app/validators/job_validator.py` — job create/update schema, job search/filter schema
- Needed by Stories 3 and 4

---

### Phase 2 — Backend Security + Core APIs

**Story 7** — Backend Security Middleware (Issue #105)
- `app/middleware/rate_limiter.py` — Flask-Limiter config per route (depends on Story 9 for constants)
- `app/middleware/request_id.py` — add `X-Request-ID` header to every request/response
- RBAC decorator (can use Story 9 decorators or extend auth_middleware)
- Needed before exposing any Story 3/4/5 routes in production

**Story 3** — Backend Job APIs (Issue #101)
- `app/services/job_service.py` — create, update, get by ID, list with filters, search by qualification/category/state, views counter increment
- `app/routes/jobs.py` — fill the existing stub with endpoints:
  - `GET /api/v1/jobs` — list with pagination, filters (type, qualification, state, status)
  - `GET /api/v1/jobs/<slug>` — detail + increment views
  - `POST /api/v1/jobs` — create (operator/admin only)
  - `PUT /api/v1/jobs/<id>` — update (operator/admin only)
  - `DELETE /api/v1/jobs/<id>` — soft delete (admin only)
- Uses Story 7 (RBAC), Story 8 (job_validator), Story 9 (pagination, constants)

**Story 4** — Backend User Profile APIs (Issue #102)
- `app/services/user_service.py` — get profile, update profile, get applications, submit application, withdraw application
- `app/routes/users.py` — fill the existing stub:
  - `GET /api/v1/users/profile` — get own profile (JWT required)
  - `PUT /api/v1/users/profile` — update own profile (JWT required)
  - `GET /api/v1/users/applications` — list own applications (JWT required)
  - `POST /api/v1/users/applications` — apply to job (JWT required)
  - `DELETE /api/v1/users/applications/<id>` — withdraw application (JWT required)
  - `GET /api/v1/users` — list all users (admin only)
  - `PUT /api/v1/users/<id>/status` — suspend/activate/delete user (admin only)
- Uses Story 7 (RBAC), Story 8 (user_validator), Story 9 (pagination)

---

### Phase 3 — Notifications + Frontend Pages

**Story 5** — Backend Notification APIs (Issue #103)
- `app/services/notification_service.py` — create, mark read, mark all read, delete; matching logic (user profile vs job eligibility)
- `app/services/email_service.py` — SMTP via Flask-Mail (registration confirm, password reset, exam reminder)
  - Note: password reset + registration email routes exist in `auth.py` but have TODO comments — email is not actually sent yet. Story 5 wires these up.
- `app/routes/notifications.py` — fill the existing stub:
  - `GET /api/v1/notifications` — list (JWT required, paginated)
  - `PUT /api/v1/notifications/<id>/read` — mark single read
  - `PUT /api/v1/notifications/read-all` — mark all read
  - `DELETE /api/v1/notifications/<id>`
- Uses Story 3 (job matching), Story 4 (user profile for eligibility), Story 7 (RBAC)

**Story 6** — Frontend Page Routes & Jinja2 Templates (Issue #104)
- Requires Story 2 (API client + login_required) to be done first
- Useful data only available after Story 3 + Story 4 are done
- User Frontend (`src/frontend/`):
  - `app/routes/auth.py` — login, register, logout, forgot-password pages (HTML forms that call backend via api_client)
  - `app/routes/jobs.py` — job list, job detail, job search pages
  - `app/routes/profile.py` — view/edit profile, applications list
  - `templates/layouts/base.html` — base layout with nav
  - `templates/pages/` — auth pages, job pages, profile pages
  - `static/` — CSS, JS (minimal, no framework required unless specified)
- Admin Frontend (`src/frontend-admin/`):
  - `app/routes/auth.py` — admin login, logout
  - `app/routes/dashboard.py` — stats summary page
  - `app/routes/jobs.py` — job list, create, edit, delete pages
  - `app/routes/users.py` — user list, view, status-change pages
  - `templates/` — admin-specific layouts and pages

---

### Phase 4 — Background Tasks + Tests

**Story 10** — Celery Background Tasks (Issue #108)
- Requires Story 5 (notification + email services) to be done first
- `app/tasks/notification_task.py` — match new jobs to users → create in-app notifications
- `app/tasks/reminder_task.py` — deadline reminders at T-7, T-3, T-1 days via email/push
- `app/tasks/cleanup_task.py` — expire old jobs, purge soft-deleted records
- `app/tasks/views_flush_task.py` — flush Redis view counts to PostgreSQL periodically
- Firebase FCM push notification integration (for reminder_task and notification_task)
- Celery Beat schedule — wire all periodic tasks with correct cron intervals
- Currently `celery_app.py` exists and is configured; only the task files are missing

**Story 11** — Test Suite Expansion (Issue #109, partially done)
- Conftest fixtures done: `app`, `client`, `mock_redis`, `auth_headers`
- Fixture still needed: `db_session` (for integration tests that write to PostgreSQL)
- pytest-cov configuration (`.coveragerc` or `pyproject.toml [tool.pytest.ini_options]`)
- Tests to write per story:
  - Story 3: `tests/unit/test_job_service.py`, `tests/integration/test_job_routes.py`
  - Story 4: `tests/unit/test_user_service.py`, `tests/integration/test_user_routes.py`
  - Story 5: `tests/unit/test_notification_service.py`, `tests/integration/test_notification_routes.py`
  - Story 8: `tests/unit/test_user_validator.py`, `tests/unit/test_job_validator.py`
  - Story 10: `tests/unit/test_notification_task.py`, `tests/unit/test_reminder_task.py`
- Best practice: write tests alongside each story, not all at the end

---

## Summary Table

| Order | Story | Issue | Status | Blocker for |
|---|---|---|---|---|
| 1 (parallel) | Story 2: Frontend Auth & API Client | #100 | ✅ **Done** | Story 6 |
| 1 (parallel) | Story 9: Backend Utilities | #107 | 🟡 Next | Stories 3, 4, 5, 7 |
| 1 (parallel) | Story 8: Marshmallow Validators | #106 | 🟡 Next | Stories 3, 4 |
| 2 | Story 7: Backend Security Middleware | #105 | ⬜ Not started | Stories 3, 4, 5 |
| 3 | Story 3: Backend Job APIs | #101 | ⬜ Not started | Stories 5, 6, 10 |
| 3 | Story 4: Backend User Profile APIs | #102 | ⬜ Not started | Stories 5, 6, 10 |
| 4 | Story 5: Backend Notification APIs | #103 | ⬜ Not started | Story 10 |
| 4 | Story 6: Frontend Page Routes + Templates | #104 | ⬜ Not started | — |
| 5 | Story 10: Celery Background Tasks | #108 | ⬜ Not started | — |
| ongoing | Story 11: Test Suite Expansion | #109 | ⬜ In progress | — |

---

## What Is NOT In Scope (Not in any current issue)

These items appear in the README and workflow diagrams but have no corresponding GitHub issue yet:

- Firebase FCM push notification integration (partially mentioned in Story 10)
- Admin frontend analytics dashboard (charts, stats)
- Nginx admin frontend proxying (currently admin is accessed directly on port 8081)
- Production deployment to Hostinger VPS (documented in README but no issue)
- SSL certificate provisioning (Let's Encrypt)
- CI/CD pipeline (no `.github/workflows/` exists)

These will need separate issues before work begins.
