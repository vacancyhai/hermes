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
│   └── DOCKER_ENVIRONMENTS.md        ✅
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
├── tests/                             📁  empty (e2e tests not started)
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
    │   │   │   ├── auth.py            🟡  blueprint at /api/v1/auth — no endpoints yet
    │   │   │   ├── jobs.py            🟡  blueprint at /api/v1/jobs — no endpoints yet
    │   │   │   ├── users.py           🟡  blueprint at /api/v1/users — no endpoints yet
    │   │   │   ├── notifications.py   🟡  blueprint at /api/v1/notifications — no endpoints yet
    │   │   │   └── admin.py           🟡  blueprint at /api/v1/admin — no endpoints yet
    │   │   │
    │   │   ├── services/              🟡  __init__.py only — modules to be added
    │   │   │   ├── __init__.py
    │   │   │   ├── auth_service.py    ❌  register, login, JWT issue/refresh, password reset
    │   │   │   ├── job_service.py     ❌  job CRUD, search, filtering, matching algorithm
    │   │   │   ├── user_service.py    ❌  profile read/update, preferences
    │   │   │   ├── notification_service.py  ❌  create, deliver, and mark notifications
    │   │   │   └── email_service.py   ❌  SMTP send via Flask-Mail (welcome, alerts, OTP)
    │   │   │
    │   │   ├── tasks/
    │   │   │   ├── __init__.py        ✅
    │   │   │   ├── celery_app.py      ✅  Celery instance, broker/backend, serialisation config
    │   │   │   ├── notification_tasks.py  ❌  async send email + push notifications
    │   │   │   ├── reminder_tasks.py  ❌  cron — application deadline reminders
    │   │   │   └── cleanup_tasks.py   ❌  cron — purge stale sessions, old logs
    │   │   │
    │   │   ├── utils/                 🟡  __init__.py only — modules to be added
    │   │   │   ├── __init__.py
    │   │   │   ├── helpers.py         ❌  shared helper functions (pagination, date fmt, etc.)
    │   │   │   ├── decorators.py      ❌  custom decorators (e.g. @admin_required)
    │   │   │   └── constants.py       ❌  app-wide constants (roles, statuses, limits)
    │   │   │
    │   │   ├── validators/            🟡  __init__.py only — modules to be added
    │   │   │   ├── __init__.py
    │   │   │   ├── auth_validator.py  ❌  Marshmallow schemas for register/login payloads
    │   │   │   ├── user_validator.py  ❌  Marshmallow schemas for profile update payloads
    │   │   │   └── job_validator.py   ❌  Marshmallow schemas for job create/update payloads
    │   │   │
    │   │   └── middleware/
    │   │       ├── __init__.py        ✅
    │   │       ├── error_handler.py   ✅  JSON error handlers for 400/401/403/404/500
    │   │       ├── auth_middleware.py ❌  JWT verification, token rotation, @jwt_required wrapper
    │   │       ├── rate_limiter.py    ❌  IP-level + user-level rate limiting (flask-limiter)
    │   │       ├── request_id.py      ❌  inject X-Request-ID header for distributed tracing
    │   │       └── rbac.py            ❌  role-based access control (@require_role decorator)
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
    │   └── tests/
    │       ├── unit/                  📁  empty
    │       └── integration/           📁  empty
    │
    ├── frontend/                      ✅  Docker container starts and runs
    │   ├── docker-compose.yml         ✅  single frontend container, port 8080
    │   ├── Dockerfile                 ✅  python:3.11-slim → gunicorn (2 workers)
    │   ├── requirements.txt           ✅
    │   ├── run.py                     ✅
    │   ├── .env / .env.example        ✅
    │   ├── .dockerignore              ✅
    │   │
    │   ├── app/
    │   │   ├── __init__.py            ✅  app factory: LoginManager, all blueprints registered
    │   │   │
    │   │   ├── routes/
    │   │   │   ├── __init__.py        ✅
    │   │   │   ├── main.py            ✅  GET /health + GET / → JSON responses
    │   │   │   ├── errors.py          ✅  404 + 500 JSON error handlers
    │   │   │   ├── auth.py            🟡  blueprint at /auth — no routes yet
    │   │   │   ├── jobs.py            🟡  blueprint at /jobs — no routes yet
    │   │   │   ├── profile.py         🟡  blueprint at /profile — no routes yet
    │   │   │   └── admin.py           🟡  blueprint at /admin — no routes yet
    │   │   │
    │   │   ├── utils/                 🟡  __init__.py only — modules to be added
    │   │   │   ├── __init__.py
    │   │   │   ├── api_client.py      ❌  HTTP client wrapping requests to BACKEND_API_URL
    │   │   │   ├── session_manager.py ❌  helpers to read/write flask-login session data
    │   │   │   └── helpers.py         ❌  Jinja2 template helpers, date formatters, etc.
    │   │   │
    │   │   └── middleware/            🟡  __init__.py only — modules to be added
    │   │       ├── __init__.py
    │   │       ├── auth_middleware.py ❌  @login_required decorator + redirect to /login
    │   │       └── error_handler.py   ❌  render error templates for 404/500 pages
    │   │
    │   ├── config/
    │   │   └── settings.py            ✅  BACKEND_API_URL, session config, pagination
    │   │
    │   ├── templates/                 📁  directories exist, no .html files yet
    │   │   ├── layouts/
    │   │   │   ├── base.html          ❌  main layout with nav, footer, flash messages
    │   │   │   ├── admin.html         ❌  admin layout with sidebar navigation
    │   │   │   └── minimal.html       ❌  minimal layout for auth/error pages
    │   │   ├── components/
    │   │   │   ├── navbar.html        ❌  top navigation bar partial
    │   │   │   ├── footer.html        ❌  page footer partial
    │   │   │   ├── sidebar.html       ❌  admin sidebar partial
    │   │   │   ├── job_card.html      ❌  reusable job listing card
    │   │   │   └── pagination.html    ❌  pagination controls partial
    │   │   └── pages/
    │   │       ├── auth/
    │   │       │   ├── login.html     ❌  login form page
    │   │       │   ├── register.html  ❌  registration form page
    │   │       │   └── forgot_password.html  ❌  password reset request page
    │   │       ├── jobs/
    │   │       │   ├── list.html      ❌  paginated job listings
    │   │       │   ├── detail.html    ❌  single job detail + apply button
    │   │       │   └── apply.html     ❌  job application form
    │   │       ├── profile/
    │   │       │   ├── index.html     ❌  user profile view
    │   │       │   └── settings.html  ❌  profile and preferences edit form
    │   │       └── admin/
    │   │           ├── dashboard.html ❌  admin stats overview
    │   │           ├── users.html     ❌  user management table
    │   │           └── jobs.html      ❌  job management table
    │   │
    │   └── static/                    📁  directories exist, no asset files yet
    │       ├── css/
    │       │   ├── main.css           ❌  global styles and variables
    │       │   ├── auth.css           ❌  login/register page styles
    │       │   ├── jobs.css           ❌  job listing and detail styles
    │       │   └── admin.css          ❌  admin dashboard styles
    │       ├── js/
    │       │   ├── main.js            ❌  global scripts (flash dismiss, nav)
    │       │   ├── jobs.js            ❌  job search filters and apply form
    │       │   ├── notifications.js   ❌  real-time notification polling
    │       │   └── admin.js           ❌  admin table interactions
    │       ├── images/                📁  logo, favicon, placeholders
    │       └── fonts/                 📁  custom web fonts
    │
    └── nginx/                         ✅  fully configured
        ├── docker-compose.yml         ✅  external network references to backend + frontend
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
Only `health.py` has a live endpoint (`GET /api/v1/health`). All other route files are registered blueprints with no endpoints yet — add route functions directly to each file.

### `app/services/`
Business logic layer — keeps route handlers thin. Five modules planned:
- `auth_service.py` — register, login, JWT issue/refresh, password reset
- `job_service.py` — job CRUD, search filtering, user-to-job matching
- `user_service.py` — profile read/update, notification preferences
- `notification_service.py` — create, store, and deliver notifications
- `email_service.py` — SMTP email via Flask-Mail (welcome, OTP, alerts)

### `app/tasks/`
`celery_app.py` has the Celery instance wired to Redis. Three task modules planned:
- `notification_tasks.py` — async send email + push notifications (HIGH priority queue)
- `reminder_tasks.py` — cron: application deadline reminders (MEDIUM priority)
- `cleanup_tasks.py` — cron: purge stale sessions and old analytics rows (LOW priority)

### `app/middleware/`
`error_handler.py` is implemented. Four more modules planned:
- `auth_middleware.py` — JWT verification, token rotation, `@jwt_required` wrapper
- `rate_limiter.py` — IP-level + user-level limiting via flask-limiter
- `request_id.py` — injects `X-Request-ID` header for distributed tracing
- `rbac.py` — `@require_role('admin')` decorator using `RolePermission` model

### `app/utils/`
Three modules planned:
- `helpers.py` — pagination helper, date formatters, slug generator
- `decorators.py` — custom decorators (e.g. `@admin_required`, `@rate_limit`)
- `constants.py` — app-wide constants: roles, job statuses, notification types

### `app/validators/`
Marshmallow schema modules — three planned:
- `auth_validator.py` — register and login payload schemas
- `user_validator.py` — profile and preferences update schemas
- `job_validator.py` — job create and update schemas

### `config/settings.py`
Full `Config` class: SQLAlchemy connection pooling, JWT expiry, Redis URL, Celery broker/backend, CORS origins, rate limits, mail settings. Includes a startup guard that aborts if required vars are missing or insecure in production.

### `migrations/`
Alembic wired up. `0001_initial_schema.py` contains full DDL for all tables. Run `flask db upgrade` inside the container after changes.

---

## Frontend (`src/frontend/`)

Runs a single Gunicorn container on port 8080.

### `app/routes/`
`main.py` serves `GET /` and `GET /health` (JSON only — no template rendered yet). `errors.py` handles 404/500. All other blueprints are registered but have no routes.

### `app/utils/`
Three modules planned:
- `api_client.py` — wraps `requests` calls to `BACKEND_API_URL`; handles token passing and error propagation
- `session_manager.py` — helpers to read/write flask-login session data and JWT tokens
- `helpers.py` — Jinja2 template helpers, date formatters, URL builders

### `app/middleware/`
Two modules planned:
- `auth_middleware.py` — `@login_required` decorator redirecting unauthenticated users to `/login`
- `error_handler.py` — renders HTML error templates (404.html, 500.html) instead of JSON

### `templates/`
Directory scaffolding exists. Templates follow a three-tier layout:
- `layouts/` — `base.html` (main), `admin.html` (sidebar), `minimal.html` (auth/error)
- `components/` — reusable partials: navbar, footer, sidebar, job card, pagination
- `pages/` — one subfolder per section; see tree above for planned filenames

### `static/`
Directories exist. Assets planned:
- `css/` — `main.css`, `auth.css`, `jobs.css`, `admin.css`
- `js/` — `main.js`, `jobs.js`, `notifications.js`, `admin.js`
- `images/` — logo, favicon, placeholder
- `fonts/` — custom web fonts

### `config/settings.py`
`BACKEND_API_URL`, session options (`SESSION_TIMEOUT`, `SESSION_COOKIE_SECURE`, etc.), `ITEMS_PER_PAGE`, Flask `SECRET_KEY`.

---

## What works right now

- Full Docker stack (`make all-up`) starts cleanly.
- `GET /api/v1/health` (backend) and `GET /health` (frontend) are live.
- Database schema is fully defined — run `flask db upgrade` to apply it.
- All SQLAlchemy models are wired and ready for use.

## What's next

| Priority | Work |
|---|---|
| High | `backend/middleware/auth_middleware.py` — JWT verify + token rotation |
| High | `backend/routes/auth.py` — register, login, logout, refresh endpoints |
| High | `backend/services/auth_service.py` — authentication business logic |
| High | `frontend/app/utils/api_client.py` — HTTP client to backend API |
| High | `frontend/app/middleware/auth_middleware.py` — `@login_required` decorator |
| Medium | `backend/routes/jobs.py`, `users.py`, `notifications.py` — add endpoints |
| Medium | `backend/services/` — job, user, notification, email service modules |
| Medium | `frontend/routes/` — auth, jobs, profile, admin page routes + templates |
| Medium | `backend/middleware/rate_limiter.py` + `rbac.py` + `request_id.py` |
| Low | `backend/validators/` — Marshmallow schemas for all resources |
| Low | `backend/utils/` — helpers, decorators, constants |
| Low | `backend/tasks/` — notification, reminder, cleanup task functions |
| Low | Test files in `tests/unit/` and `tests/integration/` |

---

**Last Updated**: March 2026
**Version**: 2.0