# Hermes — Development Roadmap

> **Last updated**: 2026-03-10 (Stories 2–11 complete + Production Readiness improvements)
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
| `app/routes/health.py` | ✅ 4 endpoints: /health (basic), /health/full (comprehensive), /health/ready (K8s), /health/live (K8s) |
| `app/routes/jobs.py` | ✅ 5 endpoints: GET list, GET /<slug>, POST create, PUT update, DELETE soft-delete |
| `app/routes/users.py` | ✅ 7 endpoints: GET/PUT profile, GET/POST/DELETE applications, GET users (admin), PUT status (admin) |
| `app/routes/notifications.py` | ✅ 5 endpoints: GET list, GET count, PUT /:id/read, PUT /read-all, DELETE /:id |
- `app/routes/admin.py` — ✅ Dashboard stats endpoint (GET /stats)
- `app/routes/admin_auth.py` — ✅ Admin authentication (login, logout, refresh, change-password, me)
- `app/routes/admin_users.py` — ✅ Admin user management (CRUD, permissions, role updates)
- `app/routes/admin_audit.py` — ✅ Audit logs (action logs, access logs)
| `app/services/auth_service.py` | ✅ Register, login, logout, token refresh, password reset, email verification |
| `app/services/job_service.py` | ✅ get_jobs, get_job_by_slug, get_job_by_id, create_job, update_job, delete_job |
| `app/services/user_service.py` | ✅ get_profile, update_profile, get_applications, apply_to_job, withdraw_application, get_all_users, update_user_status |
| `app/services/notification_service.py` | ✅ create, mark read, mark all read, delete, match_job_to_users |
| `app/services/email_service.py` | ✅ Flask-Mail wrapper: verification, reset, job alert, deadline reminder |
| `app/middleware/auth_middleware.py` | ✅ JWT decode, role check, token rotation |
| `app/middleware/error_handler.py` | ✅ JSON error handlers (400, 401, 403, 404, 500); reads g.request_id |
| `app/middleware/rate_limiter.py` | ✅ Shared Flask-Limiter instance; JWT-aware key (user:<id> vs IP); init_limiter() |
| `app/middleware/request_id.py` | ✅ before_request assigns g.request_id; after_request echoes X-Request-ID header |
| `app/middleware/security.py` | ✅ HTTPS enforcement, security headers (HSTS, CSP, X-Frame-Options, etc.) |
| `app/utils/logging_config.py` | ✅ JSON logging with request_id injection, environment-aware formatting |
| `app/utils/sentry_config.py` | ✅ Sentry error tracking, Flask/Celery/Redis/SQLAlchemy integrations |
| `app/validators/auth_validator.py` | ✅ RegisterSchema, LoginSchema, PasswordResetRequestSchema, PasswordResetSchema |
| `app/validators/user_validator.py` | ✅ UpdateProfileSchema, UpdatePhoneSchema |
| `app/validators/job_validator.py` | ✅ CreateJobSchema, UpdateJobSchema, JobSearchSchema |
| `app/utils/constants.py` | ✅ UserRole, UserStatus, JobStatus, JobType, ApplicationStatus, NotificationType, QualificationLevel, ErrorCode |
| `app/utils/helpers.py` | ✅ paginate(), success_response(), slugify() |
| `app/utils/decorators.py` | ✅ @admin_required, @operator_required |
| `app/tasks/celery_app.py` | ✅ Celery configured |
| `app/tasks/notification_tasks.py` | ✅ send_verification_email_task, send_password_reset_email_task, send_new_job_notifications, deliver_notification_email |
| `app/tasks/reminder_tasks.py` | ✅ deadline reminders at T-7, T-3, T-1 days |
| `app/tasks/cleanup_tasks.py` | ✅ purge notifications, admin logs, soft-deleted jobs, expired listings |

**Tests**: 324 passing — unit tests cover validators, helpers, services, rate_limiter, request_id, all Celery tasks (notification, reminder, views-flush, cleanup); integration tests cover auth + jobs + users + notification routes.

**VERIFIED IMPLEMENTATIONS** (2026-03-10 audit):
- ✅ **CSRF Protection**: Fully implemented in `src/frontend/app/utils/csrf.py` and `src/frontend-admin/app/utils/csrf.py` with session-based tokens
- ✅ **Views Counter**: Complete implementation in `app/services/job_service.py` (Redis increment) + `app/tasks/views_flush_task.py` (flush to DB with distributed locking) + Celery Beat schedule (every 5 minutes)
- ✅ **Database Indexes**: Exist in `migrations/versions/0001_initial_schema.py` including idx_users_email, idx_users_status, idx_jobs_status_created, idx_jobs_qual_level, idx_jobs_application_end, GIN indexes on JSONB fields
- ✅ **Soft Delete Filtering**: Enforced in `job_service.py` line 67 - public API only returns JobStatus.ACTIVE jobs
- ✅ **Admin Frontend Routes**: Implemented (dashboard.py, jobs.py with full CRUD, users.py with list + status update)
- ✅ **Celery Beat Scheduling**: Configured in `celery_app.py` with 6 scheduled tasks (deadline reminders, cleanup tasks, views flush)

### User Frontend — Stories 2 + 6 Complete ✅
- Docker runs on port 8080, health check at `/health` passes
- Root `/` renders homepage with featured jobs
- `app/routes/errors.py` — renders HTML error templates (404, 500)
- `app/routes/main.py` — renders `pages/index.html` with featured jobs
- `app/routes/jobs.py` — ✅ 3 endpoints: list, detail, apply
- `app/routes/profile.py` — ✅ 4 endpoints: index, edit, applications, withdraw
- `app/routes/admin.py` — empty stub (not in scope)

**Story 2 additions**:
| File | Status |
|---|---|
| `app/models/user.py` | ✅ Flask-Login `UserMixin` proxy (session-backed, no DB) |
| `app/utils/api_client.py` | ✅ `requests` wrapper; raises `APIError` on non-2xx; covers auth + jobs + profile + notifications endpoints |
| `app/utils/session_manager.py` | ✅ Save/read/clear tokens + user info; decodes JWT payload for user_id/role |
| `app/middleware/auth_middleware.py` | ✅ `@login_required` decorator |
| `app/__init__.py` | ✅ `load_user()` wired to session via `session_manager`; explicit `template_folder` + `static_folder` |
| `app/routes/auth.py` | ✅ login, register, logout, forgot-password, reset-password (GET+POST) |

**Story 6 additions**:
| File | Status |
|---|---|
| `app/routes/jobs.py` | ✅ list_jobs, job_detail, apply |
| `app/routes/profile.py` | ✅ index, edit (GET+POST), applications, withdraw |
| `app/routes/main.py` | ✅ homepage renders `pages/index.html` with featured jobs |
| `app/routes/errors.py` | ✅ renders `errors/404.html` and `errors/500.html` |
| `templates/pages/index.html` | ✅ hero section + featured jobs grid |
| `templates/pages/jobs/list.html` | ✅ filter bar, job grid, pagination |
| `templates/pages/jobs/detail.html` | ✅ full job detail, apply CTA, eligibility |
| `templates/pages/profile/index.html` | ✅ profile view with sidebar nav |
| `templates/pages/profile/edit.html` | ✅ edit form (personal info, location, education) |
| `templates/pages/profile/applications.html` | ✅ applications list with withdraw + pagination |
| `templates/errors/404.html` | ✅ branded error page |
| `templates/errors/500.html` | ✅ branded error page |
| `static/css/main.css` | ✅ added hero, error-page, application-card, form-fieldset classes |

**Tests**: 102 passing (unit + integration; 40 new route tests added in Story 6)

### Admin Frontend — Stories 2 + 6 Complete ✅
- Docker runs on port 8081, health check at `/health` passes
- Root `/` redirects to `/dashboard/`
- `app/routes/errors.py` — renders error pages
- `app/routes/main.py` — health + root only
- `app/routes/dashboard.py` — ✅ recent jobs + users summary
- `app/routes/jobs.py` — ✅ full CRUD: list, create, edit, delete
- `app/routes/users.py` — ✅ list + status update

**Story 2 additions**:
| File | Status |
|---|---|
| `app/models/user.py` | ✅ Flask-Login `UserMixin` proxy; adds `is_admin()` / `is_operator()` helpers |
| `app/utils/api_client.py` | ✅ Covers auth + jobs CRUD + user management endpoints |
| `app/utils/session_manager.py` | ✅ Same as user frontend |
| `app/middleware/auth_middleware.py` | ✅ `@login_required` + `@role_required(*roles)`; enforces admin/operator on every protected route |
| `app/__init__.py` | ✅ `load_user()` wired to session; explicit `template_folder` + `static_folder` |
| `app/routes/auth.py` | ✅ login + logout; role decoded from JWT before session save — regular users are rejected and their token is blocklisted |
| `.env` | ✅ Created (was missing) |

**Story 6 additions**:
| File | Status |
|---|---|
| `app/routes/dashboard.py` | ✅ recent jobs + users; renders `pages/dashboard/index.html` |
| `app/routes/jobs.py` | ✅ list, create (GET+POST), edit (GET+POST), delete; `@role_required` guards |
| `app/routes/users.py` | ✅ list + POST status update; admin-only via `@role_required('admin')` |
| `templates/pages/dashboard/index.html` | ✅ stats grid with recent jobs + users |
| `templates/pages/jobs/list.html` | ✅ filter table, pagination, delete buttons |
| `templates/pages/jobs/create.html` | ✅ full job creation form |
| `templates/pages/jobs/edit.html` | ✅ pre-filled job edit form |
| `templates/pages/jobs/_job_form.html` | ✅ shared form partial (create + edit) |
| `templates/pages/users/list.html` | ✅ user table with inline status update forms |
| `static/css/admin.css` | ✅ added dashboard-grid, data-table, filter-form, btn--xs classes |

**Tests**: 95 passing (unit + integration; 46 new route tests added in Story 6)

---

## GitHub Issues

| Issue | Story | Priority | Area | Status |
|---|---|---|---|---|
| #100 | Story 2: Frontend Auth & API Client | HIGH | User Frontend + Admin Frontend | ✅ **Done** |
| #101 | Story 3: Backend Job APIs | MEDIUM | Backend | ✅ **Done** |
| #102 | Story 4: Backend User Profile APIs | MEDIUM | Backend | ✅ **Done** |
| #103 | Story 5: Backend Notification APIs | MEDIUM | Backend | ✅ **Done** |
| #104 | Story 6: Frontend Page Routes & Jinja2 Templates | MEDIUM | User Frontend | ✅ **Done** |
| #105 | Story 7: Backend Security Middleware | MEDIUM | Backend | ✅ **Done** |
| #106 | Story 8: Marshmallow Input Validators | LOW | Backend | ✅ **Done** |
| #107 | Story 9: Backend Utilities | LOW | Backend | ✅ **Done** |
| #108 | Story 10: Celery Background Tasks | LOW | Backend + Celery | ✅ **Done** |
| #109 | Story 11: Test Suite Expansion | LOW | Backend tests | ✅ **Done** |
| — | Admin Authentication System (2-role) | HIGH | Backend + Admin Frontend | ✅ **Done** (March 10, 2026) |

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

**Story 9** — Backend Utilities (Issue #107) ✅ **DONE**
- `app/utils/constants.py` — UserRole, UserStatus, JobStatus, JobType, ApplicationStatus, NotificationType, QualificationLevel, ErrorCode
- `app/utils/helpers.py` — paginate(), success_response(), slugify()
- `app/utils/decorators.py` — @admin_required, @operator_required

**Story 8** — Marshmallow Input Validators (Issue #106) ✅ **DONE**
- `app/validators/user_validator.py` — UpdateProfileSchema (all optional, enum/regex constraints), UpdatePhoneSchema
- `app/validators/job_validator.py` — CreateJobSchema (cross-field date+salary validation, slug rejected), UpdateJobSchema, JobSearchSchema

---

### Phase 2 — Backend Security + Core APIs

**Story 7** — Backend Security Middleware (Issue #105) ✅ **DONE**
- `app/middleware/rate_limiter.py` — shared Limiter singleton; JWT-aware key function (user:<id> for authed, IP for anonymous); init_limiter() forwards REDIS_URL as storage
- `app/middleware/request_id.py` — before_request assigns g.request_id (header or UUID4); after_request echoes X-Request-ID
- `app/routes/auth.py` — now imports shared limiter (local Limiter instance removed)
- `app/__init__.py` — calls init_limiter(app) + register_request_id(app)
- `app/middleware/error_handler.py` — reads g.request_id instead of raw header

**Story 3** — Backend Job APIs (Issue #101) ✅ **DONE**
- `app/services/job_service.py` — get_jobs (paginated + filtered), get_job_by_slug (+views increment), get_job_by_id, create_job (auto-slug), update_job, delete_job (soft)
- `app/routes/jobs.py` — 5 endpoints:
  - `GET /api/v1/jobs` — list with pagination + filters (type, qualification, org, status, q)
  - `GET /api/v1/jobs/<slug>` — detail + views increment
  - `POST /api/v1/jobs` — create (operator/admin, JWT required)
  - `PUT /api/v1/jobs/<id>` — update (operator/admin, JWT required)
  - `DELETE /api/v1/jobs/<id>` — soft delete → archived (admin only)

**Story 4** — Backend User Profile APIs (Issue #102) ✅ **DONE**
- `app/services/user_service.py` — get_profile, update_profile, get_applications, apply_to_job (+count), withdraw_application (-count), get_all_users, update_user_status
- `app/routes/users.py` — 7 endpoints:
  - `GET /api/v1/users/profile` — get own profile (JWT required)
  - `PUT /api/v1/users/profile` — update own profile (JWT required)
  - `GET /api/v1/users/applications` — list own applications (JWT required, paginated)
  - `POST /api/v1/users/applications` — apply to job (JWT required)
  - `DELETE /api/v1/users/applications/<id>` — withdraw (JWT required)
  - `GET /api/v1/users` — list all users (admin only, paginated)
  - `PUT /api/v1/users/<id>/status` — change user status (admin only)

---

### Phase 3 — Notifications + Frontend Pages

**Story 5** — Backend Notification APIs (Issue #103) ✅ **DONE**
- `app/services/notification_service.py` — create, mark read, mark all read, delete; match_job_to_users() eligibility logic
- `app/services/email_service.py` — Flask-Mail wrapper: verification, reset, job alert, deadline reminder
- `app/routes/notifications.py` — 5 endpoints:
  - `GET /api/v1/notifications` — list (JWT required, paginated, per_page capped at 100)
  - `GET /api/v1/notifications/count` — unread count → `{"unread_count": int}`
  - `PUT /api/v1/notifications/<id>/read` — mark single read (404 on wrong owner)
  - `PUT /api/v1/notifications/read-all` — bulk mark read → `{"updated": int}`
  - `DELETE /api/v1/notifications/<id>` — hard delete (404 on wrong owner)
- `app/routes/auth.py` — wired `send_verification_email_task.delay()` and `send_password_reset_email_task.delay()` (replaced TODO comments)
- Tests: `tests/unit/test_notification_service.py` (20), `tests/integration/test_notification_routes.py` (20) — all passing

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

**Story 10** — Celery Background Tasks (Issue #108) ✅ **DONE**

Implemented:
- `app/routes/jobs.py` — `create_job` now calls `send_new_job_notifications.delay(job_id)` when a new job is published as `active`
- `app/services/job_service.py` — `get_job_by_slug` now buffers view increments in Redis (`job:views:<id>`) with DB fallback on Redis unavailability
- `app/tasks/views_flush_task.py` — `flush_job_views()` reads all `job:views:*` keys with `GETDEL`, commits view-count deltas to PostgreSQL in bulk, rolls back on failure
- `app/tasks/celery_app.py` — added `flush-job-views-every-5-minutes` entry to `beat_schedule` (every 300s)
- `app/services/email_service.py` — fixed Python 3.9 compatibility (`from __future__ import annotations`)
- Tests: `tests/unit/test_notification_tasks.py` (10), `tests/unit/test_reminder_tasks.py` (8), `tests/unit/test_views_flush_task.py` (8) — 26 new tests, all passing

**Story 11** — Test Suite Expansion (Issue #109) ✅ **DONE**
- Added `pytest-cov` configuration: `.coveragerc` (source=app, omit migrations/celery_app) + `--cov=app --cov-report=term-missing` in `pytest.ini`
- Added `pytest-cov==7.0.0` to `requirements.txt`
- Added `db_session` fixture in `tests/conftest.py` — yields a rolled-back SQLAlchemy session for DB-backed integration tests
- Filled coverage gaps:
  - `tests/unit/test_cleanup_tasks.py` — 11 new tests for all 4 cleanup tasks (`purge_expired_notifications`, `purge_expired_admin_logs`, `purge_soft_deleted_jobs`, `close_expired_job_listings`)
  - `tests/unit/test_notification_tasks.py` — 8 new tests for `send_verification_email_task` and `send_password_reset_email_task`
- Total: **324 backend tests**, all passing

---

## Summary Table

| Order | Story | Issue | Status | Blocker for |
|---|---|---|---|---|
| 1 (parallel) | Story 2: Frontend Auth & API Client | #100 | ✅ **Done** | Story 6 |
| 1 (parallel) | Story 9: Backend Utilities | #107 | ✅ **Done** | Stories 3, 4, 5, 7 |
| 1 (parallel) | Story 8: Marshmallow Validators | #106 | ✅ **Done** | Stories 3, 4 |
| 2 | Story 7: Backend Security Middleware | #105 | ✅ **Done** | Stories 3, 4, 5 |
| 3 | Story 3: Backend Job APIs | #101 | ✅ **Done** | Stories 5, 6, 10 |
| 3 | Story 4: Backend User Profile APIs | #102 | ✅ **Done** | Stories 5, 6, 10 |
| 4 | Story 5: Backend Notification APIs | #103 | ✅ **Done** | Story 10 |
| 4 | Story 6: Frontend Page Routes + Templates | #104 | ✅ **Done** | — |
| 5 | Story 10: Celery Background Tasks | #108 | ✅ **Done** | — |
| 6 | Story 11: Test Suite Expansion | #109 | ✅ **Done** | — |

---

## Production Readiness Improvements (March 10, 2026)

**Completed:**
1. ✅ **Structured JSON Logging** — `app/utils/logging_config.py` with CustomJsonFormatter, request_id injection
2. ✅ **Sentry Error Tracking** — `app/utils/sentry_config.py` integrated in all 3 services (backend + both frontends)
3. ✅ **Enhanced Health Checks** — Expanded `app/routes/health.py` to 4 endpoints with DB/Redis/Celery verification
4. ✅ **Redis-Backed Sessions** — Both frontends now use Flask-Session with Redis (24h user, 12h admin)
5. ✅ **Token Rotation Handling** — Frontends now read X-New-Access-Token header and auto-update
6. ✅ **CORS Validation** — Backend `config/settings.py` validates CORS_ORIGINS with production safeguards
7. ✅ **HTTPS Enforcement + Security Headers** — `app/middleware/security.py` with HSTS, CSP, X-Frame-Options, etc.

**Files Added:**
- `src/backend/app/utils/logging_config.py` (100+ lines)
- `src/backend/app/utils/sentry_config.py` (120+ lines)
- `src/backend/app/middleware/security.py` (70+ lines)

**Files Modified:**
- Backend: `app/__init__.py`, `config/settings.py`, `requirements.txt`, `app/routes/health.py`
- User Frontend: `app/__init__.py`, `config/settings.py`, `requirements.txt`, `app/utils/api_client.py`
- Admin Frontend: `app/__init__.py`, `config/settings.py`, `requirements.txt`

**Overall Grade:** B+ → A- (production-ready, critical blockers resolved)

---

## What Remains To Be Done (Production-Ready Gaps)

**High Priority:**
1. **Backend Admin Analytics Endpoints** — `routes/admin.py` is empty stub; add stats/audit-log endpoints
2. **CI/CD Pipeline** — No `.github/workflows/` exists; deployments are manual

**Medium Priority:**
1. **E2E Tests** — Only unit + integration tests exist; need Playwright for full user flows
2. **Load Testing** — No performance baseline; add Locust/k6 tests
3. **API Documentation** — No Swagger/OpenAPI spec; would help frontend developers
4. **Deployment Verification** — Scripts start containers but don't verify migrations/health

**Low Priority:**
1. **Linting Config** — No .flake8/.pylintrc; code style varies

**See**: `docs/KNOWN_ISSUES_AND_GAPS.md` for full details on remaining gaps (updated March 10, 2026).

---

## What Is NOT In Scope (Future Work)

These items appear in the README and workflow diagrams but have no corresponding GitHub issue yet:

- Firebase FCM push notification integration (partially mentioned in Story 10)
- Admin frontend analytics dashboard (charts, stats)
- Nginx admin frontend proxying (currently admin is accessed directly on port 8081)
- Production deployment to Hostinger VPS (documented in README but no issue)
- SSL certificate provisioning (Let's Encrypt)
- CI/CD pipeline (no `.github/workflows/` exists)

These will need separate issues before work begins.
