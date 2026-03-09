# Hermes - Project Structure

> **Status legend:** ✅ implemented · 🟡 stub (file exists, no logic yet) · ❌ file not created yet · 📁 empty directory

## Folder Structure

```
hermes/
│
├── README.md                          ✅
├── Makefile                           ✅  all make targets working
├── .gitignore                         ✅
│
├── docs/                              ✅
│   ├── PROJECT_STRUCTURE.md           ✅  this file
│   ├── PROJECT_SUMMARY.md             ✅
│   ├── WORKFLOW_DIAGRAMS.md           ✅
│   └── DOCKER_ENVIRONMENTS.md        ✅  Docker environments, networks, Celery Beat schedule
│
├── config/                            ✅  env templates (copy to src/*/. env)
│   ├── README.md
│   ├── development/
│   │   ├── .env.backend.development   ✅
│   │   └── .env.frontend.development  ✅
│   ├── staging/
│   │   ├── .env.backend.staging       ✅
│   │   └── .env.frontend.staging      ✅
│   └── production/
│       ├── .env.backend.production    ✅
│       └── .env.frontend.production   ✅
│
├── postman/
│   └── hermes-api.postman_collection.json  ✅
│
├── scripts/
│   ├── README.md                      ✅
│   ├── deployment/
│   │   ├── deploy_all.sh              ✅
│   │   ├── deploy_backend.sh          ✅
│   │   └── deploy_frontend.sh         ✅
│   ├── backup/
│   │   ├── backup_db.sh               ✅
│   │   └── restore_db.sh              ✅
│   └── migration/                     📁  empty
│
├── tests/                             ✅  e2e structure: conftest.py, e2e/test_auth_flow.py, e2e/test_job_browsing.py
│
└── src/
    ├── backend/                       ✅  Docker stack starts and runs
    │   ├── docker-compose.yml         ✅  PostgreSQL + Redis + API + Celery Worker + Beat
    │   ├── Dockerfile                 ✅  python:3.11-slim → migrations → gunicorn (4 workers)
    │   ├── requirements.txt           ✅
    │   ├── run.py                     ✅
    │   ├── .env / .env.example        ✅
    │   ├── .dockerignore              ✅
    │   │
    │   ├── app/
    │   │   ├── __init__.py            ✅  app factory: db, migrate, CORS, JWT, blueprints, error handlers
    │   │   ├── extensions.py          ✅  db + migrate instances (SQLAlchemy, Flask-Migrate)
    │   │   │
    │   │   ├── models/                ✅  all models fully defined
    │   │   │   ├── __init__.py        ✅  imports all models for Flask-Migrate detection
    │   │   │   ├── user.py            ✅  User + UserProfile (UUID PKs, JSONB, relationships)
    │   │   │   ├── admin.py           ✅  AdminLog + RolePermission + AccessAuditLog
    │   │   │   ├── job.py             ✅  JobVacancy + UserJobApplication (JSONB eligibility)
    │   │   │   ├── notification.py    ✅  Notification
    │   │   │   ├── analytics.py       ✅  Category + PageView + SearchLog
    │   │   │   └── content.py         ✅  Result, AdmitCard, AnswerKey, Admission, Yojana, BoardResult
    │   │   │
    │   │   ├── routes/
    │   │   │   ├── __init__.py        ✅
    │   │   │   ├── health.py          ✅  GET /api/v1/health → {"status":"healthy"}
    │   │   │   ├── auth.py            ✅  register, login, logout, refresh, forgot/reset password, verify-email
    │   │   │   ├── jobs.py            ✅  5 endpoints: GET list, GET /<slug>, POST create, PUT update, DELETE soft-delete
    │   │   │   ├── users.py           ✅  7 endpoints: GET/PUT profile, GET/POST/DELETE applications, GET admin list, PUT admin status
    │   │   ├── notifications.py   ✅  5 endpoints: GET list, GET count, PUT /:id/read, PUT /read-all, DELETE /:id
    │   │   │   └── admin.py           🟡  blueprint at /api/v1/admin — no endpoints yet
    │   │   │
    │   │   ├── services/              ✅
    │   │   │   ├── __init__.py
    │   │   │   ├── auth_service.py    ✅  register, login, logout, refresh, request/reset password, verify email
    │   │   │   ├── job_service.py     ✅  get_jobs (filtered/paginated), get_job_by_slug, create_job, update_job, delete_job
    │   │   │   ├── user_service.py    ✅  get_profile, update_profile, get_applications, apply_to_job, withdraw_application, admin ops
    │   │   ├── notification_service.py  ✅  create, mark read, mark all read, delete, match_job_to_users()
    │   │   └── email_service.py   ✅  Flask-Mail: verification, reset, job alert, deadline reminder
    │   │   │
    │   │   ├── tasks/
    │   │   │   ├── __init__.py        ✅
    │   │   │   ├── celery_app.py      ✅  Celery instance, broker/backend, serialisation config
    │   │   ├── notification_tasks.py  ✅  send_verification_email_task, send_password_reset_email_task, send_new_job_notifications, deliver_notification_email
    │   │   ├── reminder_tasks.py  ✅  cron — deadline reminders at T-7, T-3, T-1 days
    │   │   └── cleanup_tasks.py   ✅  cron — purge notifications, admin logs, soft-deleted jobs, close expired listings
    │   │   │
    │   │   ├── utils/                 ✅
    │   │   │   ├── __init__.py
    │   │   │   ├── helpers.py         ✅  paginate(), success_response(), slugify()
    │   │   │   ├── decorators.py      ✅  @admin_required, @operator_required (stack beneath @jwt_required)
    │   │   │   └── constants.py       ✅  UserRole, UserStatus, JobStatus, JobType, ApplicationStatus, NotificationType, QualificationLevel, ErrorCode
    │   │   │
    │   │   ├── validators/            ✅
    │   │   │   ├── __init__.py
    │   │   │   ├── auth_validator.py  ✅  RegisterSchema, LoginSchema, PasswordReset schemas (marshmallow)
    │   │   │   ├── user_validator.py  ✅  UpdateProfileSchema, UpdatePhoneSchema (marshmallow, unknown=RAISE)
    │   │   │   └── job_validator.py   ✅  CreateJobSchema, UpdateJobSchema, JobSearchSchema (cross-field validation)
    │   │   │
    │   │   └── middleware/
    │   │       ├── __init__.py        ✅
    │   │       ├── error_handler.py   ✅  JSON error handlers for 400/401/403/404/500, includes request_id in response
    │   │       ├── auth_middleware.py ✅  require_role decorator, get_current_user, JWT error handlers, token rotation
    │   │       ├── rate_limiter.py    ✅  shared Limiter singleton with JWT-aware key function; init_limiter(app)
    │   │       ├── request_id.py      ✅  injects/echoes X-Request-ID header (UUID4 fallback) via before/after_request
    │   │       └── rbac.py            ❌  superseded by utils/decorators.py (@admin_required, @operator_required)
    │   │
    │   ├── config/
    │   │   ├── __init__.py            ✅
    │   │   └── settings.py            ✅  Config class: SQLAlchemy pooling, JWT, Redis, Celery,
    │   │                                  rate limits, mail; production env guard on startup
    │   │
    │   ├── migrations/                ✅
    │   │   ├── alembic.ini            ✅
    │   │   ├── env.py                 ✅
    │   │   ├── script.py.mako         ✅
    │   │   └── versions/
    │   │       └── 0001_initial_schema.py  ✅  full DDL for all tables
    │   │
    │   ├── logs/                      📁  populated at runtime
    │   ├── pytest.ini                 ✅  addopts: --cov=app --cov-report=term-missing
    │   ├── .coveragerc                ✅  source=app; omits celery_app.py + migrations; show_missing=True
    │   └── tests/
    │       ├── conftest.py            ✅  shared fixtures: fake_redis, app, client, token factories, db_session; registers jobs_bp + users_bp
    │       ├── unit/
    │       │   ├── test_auth_validator.py      ✅  22 tests — RegisterSchema, LoginSchema, PasswordReset schemas
    │       │   ├── test_auth_service.py        ✅  19 tests — register, login, logout, refresh, password reset, verify email
    │       │   ├── test_helpers.py             ✅  22 tests — slugify (12), success_response (5), paginate (5)
    │       │   ├── test_user_validator.py      ✅  22 tests — UpdateProfileSchema (16), UpdatePhoneSchema (6)
    │       │   ├── test_user_service.py        ✅  15 tests — DB mocked via unittest.mock
    │       │   ├── test_job_validator.py       ✅  34 tests — CreateJobSchema (22), UpdateJobSchema (5), JobSearchSchema (7)
    │       │   ├── test_job_service.py         ✅  14 tests — DB mocked via unittest.mock
    │       │   ├── test_notification_service.py ✅  20 tests — create, mark read, match_job_to_users
    │       │   ├── test_notification_tasks.py  ✅  18 tests — send_new_job_notifications, deliver_notification_email, send_verification_email_task, send_password_reset_email_task
    │       │   ├── test_reminder_tasks.py      ✅  8 tests — send_deadline_reminders (T-7, T-3, T-1)
    │       │   ├── test_views_flush_task.py    ✅  8 tests — flush_job_views, Redis GETDEL, DB rollback
    │       │   ├── test_cleanup_tasks.py       ✅  11 tests — purge_expired_notifications, purge_expired_admin_logs, purge_soft_deleted_jobs, close_expired_job_listings
    │       │   ├── test_rate_limiter.py        ✅  8 tests — singleton, _rate_limit_key JWT/IP fallback, init_limiter
    │       │   └── test_request_id.py          ✅  8 tests — header preservation, UUID gen, g access, 404
    │       └── integration/
    │           ├── test_auth_routes.py         ✅  33 tests — all 7 auth endpoints + JWT error handlers
    │           ├── test_job_routes.py          ✅  17 tests — job endpoints, service layer fully mocked
    │           ├── test_notification_routes.py ✅  20 tests — list, count, mark read, mark all read, delete
    │           └── test_user_routes.py         ✅  25 tests — user endpoints, service layer fully mocked
    │
    ├── frontend/                      ✅  Docker container starts and runs
    │   ├── docker-compose.yml         ✅  single frontend container, port 8080
    │   ├── Dockerfile                 ✅  python:3.11-slim → gunicorn (2 workers)
    │   ├── requirements.txt           ✅
    │   ├── pytest.ini                 ✅  testpaths = tests, pythonpath = .
    │   ├── run.py                     ✅
    │   ├── .env / .env.example        ✅
    │   ├── .dockerignore              ✅
    │   │
    │   ├── app/
    │   │   ├── __init__.py            ✅  app factory: LoginManager, load_user wired to session_manager
    │   │   │
    │   │   ├── models/                ✅  session-backed, no DB
    │   │   │   ├── __init__.py        ✅
    │   │   │   └── user.py            ✅  Flask-Login UserMixin proxy; User.from_session(data)
    │   │   │
    │   │   ├── routes/
    │   │   │   ├── __init__.py        ✅
    │   │   │   ├── main.py            ✅  GET /health + GET / → renders pages/index.html with featured jobs
    │   │   │   ├── errors.py          ✅  renders errors/404.html and errors/500.html
    │   │   │   ├── auth.py            ✅  login, register, logout, forgot-password, reset-password
    │   │   │   ├── jobs.py            ✅  list_jobs, job_detail, apply (3 endpoints)
    │   │   │   ├── profile.py         ✅  index, edit, applications, withdraw (4 endpoints)
    │   │   │   └── admin.py           🟡  blueprint at /admin — not in scope
    │   │   │
    │   │   ├── utils/                 ✅
    │   │   │   ├── __init__.py
    │   │   │   ├── api_client.py      ✅  HTTP client wrapping requests to BACKEND_API_URL
    │   │   │   ├── session_manager.py ✅  helpers to read/write flask-login session data
    │   │   │   └── helpers.py         ✅  Jinja2 filters: format_date, time_ago, days_remaining, format_salary, etc.
    │   │   │
    │   │   └── middleware/            ✅
    │   │       ├── __init__.py
    │   │       ├── auth_middleware.py ✅  @login_required decorator + redirect to /login
    │   │       └── error_handler.py   ✅  renders HTML error templates (404.html, 500.html)
    │   │
    │   ├── config/
    │   │   └── settings.py            ✅  BACKEND_API_URL, session config, pagination
    │   │
    │   ├── templates/
    │   │   ├── layouts/
    │   │   │   ├── base.html          ✅  main layout: navbar, flash messages, footer
    │   │   │   └── minimal.html       ✅  minimal auth layout (no nav)
    │   │   ├── components/
    │   │   │   ├── navbar.html        ✅  top navigation bar partial
    │   │   │   ├── footer.html        ✅  page footer partial
    │   │   │   ├── job_card.html      ✅  reusable job listing card with badges and filters
    │   │   │   └── pagination.html    ✅  pagination controls with prev/next/ellipsis
    │   │   ├── errors/
    │   │   │   ├── 404.html           ✅  branded 404 error page
    │   │   │   └── 500.html           ✅  branded 500 error page
    │   │   └── pages/
    │   │       ├── index.html              ✅  homepage: hero section + featured jobs grid
    │   │       ├── auth/
    │   │       │   ├── login.html          ✅  login form page
    │   │       │   ├── register.html       ✅  registration form page
    │   │       │   ├── forgot_password.html ✅  password reset request page
    │   │       │   └── reset_password.html  ✅  password reset form (token-gated)
    │   │       ├── jobs/
    │   │       │   ├── list.html      ✅  filter bar, job grid, pagination
    │   │       │   └── detail.html    ✅  full job detail with apply CTA, eligibility, dates
    │   │       └── profile/
    │   │           ├── index.html     ✅  profile view with sidebar nav
    │   │           ├── edit.html      ✅  edit form (personal info, location, education)
    │   │           ├── applications.html  ✅  applications list with withdraw + pagination
    │   │           └── settings.html  ✅  profile preferences form
    │   │
    │   └── static/
    │       ├── css/
    │       │   ├── main.css           ✅  global styles + hero, error-page, application-card, form-fieldset
    │       │   ├── auth.css           ✅  login/register gradient background + auth-card
    │       │   └── jobs.css           ✅  filter bar, job-grid, job-card BEM, job-detail, pagination
    │       ├── js/
    │       │   ├── main.js            ✅  navbar mobile toggle, flash auto-dismiss, active nav-link
    │       │   ├── jobs.js            ✅  filter auto-submit (debounced), apply confirmation, track btn
    │       │   └── notifications.js   ✅  polling /notifications/count every 60 s, badge update
    │       ├── images/                📁  logo, favicon, placeholders
    │       └── fonts/                 📁  custom web fonts
    │
    │   └── tests/
    │       ├── conftest.py                ✅  shared fixtures: app, client, authenticated session helpers
    │       ├── unit/
    │       │   ├── test_api_client.py          ✅  API client unit tests
    │       │   ├── test_auth_middleware.py     ✅  @login_required decorator tests
    │       │   ├── test_session_manager.py     ✅  session read/write helpers tests
    │       │   └── test_helpers.py             ✅  Jinja2 filter function tests
    │       └── integration/
    │           ├── test_auth_routes.py         ✅  22 tests — login, register, forgot-password, logout
    │           ├── test_job_routes.py          ✅  20 tests — list, detail, apply; auth guards
    │           └── test_profile_routes.py      ✅  20 tests — index, edit, applications, withdraw
    │
    ├── frontend-admin/                ✅  Docker container starts and runs
    │   ├── docker-compose.yml         ✅  single admin-frontend container, port 8081
    │   ├── Dockerfile                 ✅  python:3.11-slim → gunicorn (2 workers)
    │   ├── requirements.txt           ✅
    │   ├── pytest.ini                 ✅  testpaths = tests, pythonpath = .
    │   ├── run.py                     ✅
    │   ├── .env                       ✅  BACKEND_API_URL=http://hermes_api:5000/api/v1 (created Story 2)
    │   ├── .env.example               ✅
    │   ├── .dockerignore              ✅
    │   │
    │   ├── app/
    │   │   ├── __init__.py            ✅  app factory: LoginManager, admin blueprints registered; explicit template_folder/static_folder
    │   │   │
    │   │   ├── routes/
    │   │   │   ├── __init__.py        ✅
    │   │   │   ├── main.py            ✅  GET /health + GET / → redirect to /dashboard/
    │   │   │   ├── errors.py          ✅  404 + 500 error handlers
    │   │   │   ├── auth.py            ✅  login + logout; role check; plain-user tokens blocklisted
    │   │   │   ├── dashboard.py       ✅  GET /dashboard/ → recent jobs + users summary
    │   │   │   ├── users.py           ✅  GET /users/ (list) + POST /users/<id>/status; admin-only
    │   │   │   └── jobs.py            ✅  list, create, edit, delete; operator+ for write, admin for delete
    │   │   │
    │   │   ├── utils/                 ✅
    │   │   │   ├── __init__.py
    │   │   │   ├── api_client.py      ✅  HTTP client: auth + jobs CRUD + user management endpoints
    │   │   │   └── session_manager.py ✅  read/write tokens + user info; get_user_data()
    │   │   │
    │   │   └── middleware/            ✅
    │   │       ├── __init__.py
    │   │       ├── auth_middleware.py ✅  @login_required + @role_required(*roles); enforces admin/operator
    │   │       └── error_handler.py   ✅  404 + 500 error handlers
    │   │
    │   ├── config/
    │   │   └── settings.py            ✅  BACKEND_API_URL, session config, port 8081
    │   │
    │   ├── templates/
    │   │   ├── layouts/
    │   │   │   ├── base.html          ✅  sidebar admin layout (topbar, sidebar nav, flash, content)
    │   │   │   └── minimal.html       ✅  minimal layout for auth pages
    │   │   ├── components/            ✅  partials added in Story 6
    │   │   └── pages/
    │   │       ├── auth/
    │   │       │   └── login.html        ✅  admin/operator login form (role-gated)
    │   │       ├── dashboard/
    │   │       │   └── index.html        ✅  stats grid with recent jobs + users
    │   │       ├── users/
    │   │       │   └── list.html         ✅  user table with inline status update
    │   │       └── jobs/
    │   │           ├── list.html         ✅  job table with filters, pagination, delete
    │   │           ├── create.html       ✅  job creation form
    │   │           ├── edit.html         ✅  pre-filled job edit form
    │   │           └── _job_form.html    ✅  shared form partial (used by create + edit)
    │   │
    │   ├── static/
    │   │   ├── css/
    │   │   │   └── admin.css          ✅  sidebar layout, stat cards, forms, badges, auth screen
    │   │   ├── js/
    │   │   │   └── admin.js           ✅  sidebar mobile toggle, flash dismiss, confirm dialogs
    │   │   └── images/                📁
    │   │
    │   └── tests/
    │       ├── conftest.py            ✅  shared fixtures: app, client, admin/operator session helpers
    │       ├── unit/
    │       │   ├── test_api_client.py      ✅  9 tests
    │       │   ├── test_auth_middleware.py ✅  8 tests
    │       │   └── test_session_manager.py ✅  20 tests
    │       └── integration/
    │           ├── test_auth_routes.py     ✅  12 tests — login, role rejection, logout
    │           ├── test_dashboard_routes.py ✅  8 tests — GET /dashboard/ with mocked API
    │           ├── test_job_routes.py      ✅  25 tests — CRUD routes, role guards
    │           └── test_user_routes.py     ✅  13 tests — list + status update, admin-only guards
    │
    └── nginx/                         ✅  fully configured
        ├── docker-compose.yml         ✅  external network references to backend + frontend + frontend-admin
        ├── nginx.conf                 ✅  routing, gzip, rate limiting, security headers
        │                                  HTTPS block present but commented out (production)
        ├── .env / .env.example        ✅
        ├── README.md                  ✅
        └── ssl/                       📁  empty — add certs here for production HTTPS
```

---

## Backend (`src/backend/`)

Runs 5 containers via `docker-compose.yml`: PostgreSQL, Redis, the Flask API, a Celery worker, and Celery Beat.

### `app/extensions.py`
`db` (SQLAlchemy) and `migrate` (Flask-Migrate) instances. Imported by models and the app factory to avoid circular imports.

### `app/models/`
All models are fully implemented with UUID PKs, JSONB columns, and SQLAlchemy relationships. See the tree above for which classes live in each file.

### `app/routes/`
`health.py`, `auth.py`, `jobs.py`, `users.py`, and `notifications.py` are fully implemented. `admin.py` is a registered blueprint with no endpoints yet.

### `app/services/`
Business logic layer — keeps route handlers thin.
- `auth_service.py` — ✅ register, login, logout, refresh, password reset, email verify
- `job_service.py` — ✅ get_jobs (filtered/paginated), get_job_by_slug, get_job_by_id, create_job (auto-slug), update_job, delete_job (soft)
- `user_service.py` — ✅ get_profile, update_profile, get_applications, apply_to_job, withdraw_application, get_all_users, update_user_status
- `notification_service.py` — ✅ create, store, deliver, mark read; `match_job_to_users()` for eligibility-based matching
- `email_service.py` — ✅ Flask-Mail wrapper: `send_verification_email()`, `send_password_reset_email()`, `send_welcome_email()`, `send_job_notification_email()`, `send_deadline_reminder_email()`

### `app/tasks/`
All task modules implemented:
- `notification_tasks.py` — ✅ `send_verification_email_task`, `send_password_reset_email_task`, `send_new_job_notifications`, `deliver_notification_email`
- `reminder_tasks.py` — ✅ cron: application deadline reminders at T-7, T-3, T-1 (MEDIUM priority)
- `cleanup_tasks.py` — ✅ cron: purge stale notifications, admin logs, soft-deleted jobs, close expired listings (LOW priority)

### `app/middleware/`
- `error_handler.py` — ✅ JSON 400/401/403/404/500 handlers; echoes `request_id` in error body
- `auth_middleware.py` — ✅ `@require_role(*roles)`, `get_current_user()`, JWT error handlers, token rotation (`X-New-Access-Token`)
- `rate_limiter.py` — ✅ shared `Limiter` singleton with JWT-aware key function; `init_limiter(app)` wired in factory
- `request_id.py` — ✅ `register_request_id(app)` injects / echoes `X-Request-ID` (UUID4 fallback) via before/after_request hooks
- `rbac.py` — ❌ superseded; RBAC covered by `@admin_required` / `@operator_required` in `utils/decorators.py`

### `app/utils/`
All three modules implemented:
- `helpers.py` — ✅ `paginate(query, page, per_page)` (caps at 100, reads `request.args`), `success_response(data, status_code, meta)`, `slugify(text)` (NFKD → ASCII → lowercase)
- `decorators.py` — ✅ `@admin_required`, `@operator_required` (stack beneath `@jwt_required()`)
- `constants.py` — ✅ `UserRole`, `UserStatus`, `JobStatus`, `JobType`, `ApplicationStatus`, `NotificationType`, `QualificationLevel`, `ErrorCode`

### `app/validators/`
- `auth_validator.py` — ✅ RegisterSchema, LoginSchema, PasswordResetRequestSchema, PasswordResetSchema (marshmallow 3.x, `unknown = RAISE`)
- `user_validator.py` — ✅ `UpdateProfileSchema` (all-optional fields: gender, category, pincode, state, city, highest_qualification, dicts), `UpdatePhoneSchema` (E.164 regex)
- `job_validator.py` — ✅ `CreateJobSchema` (required: job_title, organization, job_type, eligibility; cross-field date/salary validation), `UpdateJobSchema` (all-optional), `JobSearchSchema` (query params)

### `config/settings.py`
Full `Config` class: SQLAlchemy connection pooling, JWT expiry, Redis URL, Celery broker/backend, CORS origins, rate limits, mail settings. Includes a startup guard that aborts if required vars are missing or insecure in production.

### `migrations/`
Alembic wired up. `0001_initial_schema.py` contains full DDL for all tables. Run `flask db upgrade` inside the container after changes.

---

## User Frontend (`src/frontend/`)

Serves public users: registration, login, job browsing, profile. Runs a single Gunicorn container on port 8080.

### `app/models/`
`user.py` — Flask-Login `UserMixin` proxy populated from the server-side session (no database access). Provides `get_id()`, `is_authenticated`, and `User.from_session(data)` factory method.

### `app/routes/`
`main.py` serves `GET /` (homepage with featured jobs) and `GET /health`. `errors.py` renders HTML error templates. `auth.py` handles login/register/logout/password reset. `jobs.py` has list, detail, and apply endpoints. `profile.py` has index, edit, applications, and withdraw endpoints.

### `app/utils/`
- `api_client.py` — wraps `requests` calls to `BACKEND_API_URL`; covers auth + jobs + profile + notification endpoints
- `session_manager.py` — helpers to read/write flask-login session data and JWT tokens
- `helpers.py` — Jinja2 template filters: format_date, time_ago, days_remaining, format_salary, etc.

### `app/middleware/`
- `auth_middleware.py` — `@login_required` decorator redirecting unauthenticated users to `/auth/login`
- `error_handler.py` — renders HTML error templates (404.html, 500.html)

### `templates/`
All templates implemented:
- `layouts/` — `base.html`, `minimal.html`
- `components/` — navbar, footer, job_card, pagination
- `errors/` — 404.html, 500.html
- `pages/` — index; auth (login, register, forgot/reset password); jobs (list, detail); profile (index, edit, applications)

### `static/`
- `css/` — `main.css` (with hero, error-page, application-card classes), `auth.css`, `jobs.css`
- `js/` — `main.js`, `jobs.js`, `notifications.js`

### `config/settings.py`
`BACKEND_API_URL`, session options, `ITEMS_PER_PAGE`, Flask `SECRET_KEY`.

---

## Admin Frontend (`src/frontend-admin/`)

Serves admin and operator users only: login, dashboard, job management, user management. Completely separate Docker container on port 8081.

### `app/routes/`
`auth.py` handles admin/operator login and logout; plain-user tokens are blocklisted on rejection. `dashboard.py` renders a summary of recent jobs and users. `jobs.py` handles full CRUD with role guards (operator+ for create/edit, admin-only for delete). `users.py` handles user listing and status updates (admin-only).

### `app/utils/`
- `api_client.py` — covers auth + jobs CRUD + user management endpoints
- `session_manager.py` — same structure as user frontend; adds `get_user_data()`

### `app/middleware/`
- `auth_middleware.py` — `@login_required` (checks admin/operator role) + `@role_required(*roles)`
- `error_handler.py` — 404 + 500 handlers

### `config/settings.py`
Same structure as user frontend `settings.py` but defaults to port 8081.

---

## What works right now

- Full Docker stack (`make all-up`) starts cleanly.
- `GET /api/v1/health` (backend), `GET /health` (frontend), and `GET /health` (frontend-admin) are live.
- Backend auth is fully implemented: register, login, logout, refresh, password reset, email verify.
- Backend job APIs fully implemented: list/search, get by slug, create, update, soft-delete.
- Backend user APIs fully implemented: profile read/update, job applications (apply/withdraw), admin user management.
- Security middleware in place: JWT-aware rate limiting (flask-limiter) + X-Request-ID tracing on all requests.
- All utils and validators implemented: constants, helpers (paginate, slugify), decorators, marshmallow schemas.
- Database schema is fully defined — run `flask db upgrade` to apply it.
- All SQLAlchemy models are wired and ready for use.
- Backend notification APIs fully implemented: list, unread count, mark read, mark all read, delete.
- Celery task modules implemented: notification_tasks, reminder_tasks, cleanup_tasks.
- Auth routes wired with Celery email tasks (verification + password reset).
- **User frontend fully implemented**: homepage, auth (login/register/reset), job list/detail/apply, profile view/edit/applications.
- **Admin frontend fully implemented**: login (role-gated), dashboard, job CRUD, user list + status management.
- **521 tests passing**: backend 324 (229 unit + 95 integration), user frontend 102, admin frontend 95.
- `create_job` wires `send_new_job_notifications.delay()` for active jobs; views counted via Redis INCR + Celery Beat flush every 5 min.
- Test suite expanded (Story 11): `.coveragerc` + pytest-cov configured; `db_session` fixture added; all Celery tasks covered.

## What's next

All planned stories (Stories 2–11) are complete. Potential future work (no GitHub issues yet):

| Priority | Work |
|---|---|
| Medium | Firebase FCM push notification integration |
| Medium | Admin frontend analytics dashboard (charts, stats) |
| Low | Nginx admin frontend proxying (currently accessed directly on port 8081) |
| Low | CI/CD pipeline (`.github/workflows/`) |
| Low | Production deployment to Hostinger VPS + SSL (Let's Encrypt) |

---

## Design Issues — All Fixed

All issues identified during code review have been resolved. What changed and where:

| # | Issue | Fixed in |
|---|-------|----------|
| 1 | Celery had no Flask app context — tasks using `db.session` would crash | `app/tasks/celery_app.py` — added `init_celery(app)` factory; called from `app/__init__.py` |
| 2 | `role_permissions` table never seeded — every request returned 403 | `migrations/versions/0001_initial_schema.py` — seed data added to `upgrade()` |
| 3 | JWT logout had no token revocation | `app/__init__.py` — Redis-backed `@jwt.token_in_blocklist_loader` registered; logout route must `setex(f"blocklist:{jti}", ttl, "1")` |
| 4 | Error handler format didn't match README spec | `app/middleware/error_handler.py` — returns `{"success": false, "error": {"code", "message", "details", "timestamp", "request_id"}}` |
| 5 | `job_vacancies` missing `correction_start`, `correction_end`, `exam_city_release` | `app/models/job.py` + `migrations/versions/0001_initial_schema.py` |
| 6 | `pydantic` in requirements but Marshmallow planned for validators | `requirements.txt` — replaced `pydantic` with `marshmallow==3.21.0` |
| 7 | `flask-limiter` missing from requirements | `requirements.txt` — added `Flask-Limiter==3.5.0` |
| 8 | CORS allowed all origins (`*`) | `config/settings.py` — added `CORS_ORIGINS`; `app/__init__.py` — passes it to `CORS(app, origins=...)` |
| 9 | `updated_at` not auto-updated on direct SQL writes | `migrations/versions/0001_initial_schema.py` — `_set_updated_at()` trigger function + `BEFORE UPDATE` triggers on all 11 affected tables |
| 10 | `views` counter causes row-level lock contention at scale | `job_service.py` — Redis `INCR` on view; `views_flush_task.py` — Celery Beat flushes Redis → DB every 5 min |

---

**Last Updated**: 2026-03-08 (Stories 2–11 all complete)
**Version**: 3.2
