# Hermes — Complete Session Context

> **Load this file at the start of every new session.**
> It replaces `docs/SYSTEM_BRIEFING.md` and `docs/hermes_project_context.md`.
> Do NOT re-discover what is already documented here.

---

## What It Is

A **Government Job Vacancy Portal** (India-focused). Users register, browse jobs, get personalized recommendations, follow organizations, track applications, and receive deadline reminders. Admins manage jobs, users, and content via a separate admin frontend.

---

## Repo

- **Path**: `/home/sumant/workspace/hermes`
- **Remote**: `git@github.com:SumanKr7/hermes.git`, branch `main`
- **Latest commit**: `1836397` — feat: Phase 10 + 11 — complete user and admin frontend
- **GitHub Issues**: #114–#154 (41 issues, 11 phases)
  - Phases 1–7 + Testing (#139–#140) + Phase 10–11 (#144–#154): **CLOSED**
  - Phase 8 (#141, OCI deployment): **OPEN — deferred to future**
  - Phase 9 (#142–#143, React Native): **OPEN — deferred to future**

---

## Architecture

```
Browser → Nginx (80/443)
         ├── /api/*    → Backend API   (FastAPI,  port 8000)
         ├── /*        → User Frontend (Flask,    port 8080)
         └── admin.*   → Admin Frontend(Flask,    port 8081)
```

---

## Tech Stack

| Layer | Stack |
|-------|-------|
| **Backend** | Python 3.12, FastAPI + Uvicorn, SQLAlchemy 2.0 async (asyncpg), Pydantic v2, python-jose HS256 JWT, passlib+bcrypt, Celery 5.4 + Redis 7, SlowAPI, PgBouncer (transaction mode, scram-sha-256) |
| **User Frontend** | Flask 3.1 + Jinja2 + HTMX 2.0 + Alpine.js 3.14 |
| **Admin Frontend** | Flask 3.1 + Jinja2 + HTMX 2.0 |
| **Database** | PostgreSQL 16 — 8 tables, tsvector/GIN full-text search |
| **Celery sync** | psycopg2-binary via `app.database.sync_engine` (Celery workers are synchronous) |

---

## Docker Services

`src/backend/docker-compose.yml` — 7 services:
- `hermes_postgresql` — PostgreSQL 16-alpine
- `hermes_redis` — Redis 7-alpine
- `hermes_pgbouncer` — edoburu/pgbouncer, transaction mode, scram-sha-256
- `hermes_backend` — FastAPI + Uvicorn (port 8000, hot-reload on `app/`)
- `hermes_celery_worker` — Celery worker (concurrency=2)
- `hermes_celery_beat` — Celery Beat scheduler
- `hermes_mailpit` — Dev email (SMTP 1025, Web UI 8025)

`src/frontend/docker-compose.yml` — `hermes_frontend` (port 8080)
`src/frontend-admin/docker-compose.yml` — `hermes_frontend_admin` (port 8081)

### Critical Docker/DB Notes

- asyncpg + PgBouncer: `connect_args={"prepared_statement_cache_size": 0}` required
- Alembic bypasses PgBouncer: `env.py` rewrites URL `pgbouncer:5432` → `postgresql:5432`
- Backend volume: `./app:/app/app` only — changes outside `app/` (migrations, requirements.txt) need `--build`
- Celery: explicit `include` list in `celery_app.py`, NOT `autodiscover_tasks`

---

## Database

PostgreSQL 16 with 8 tables:

| Table | Purpose |
|-------|---------|
| `users` | Regular users (no role column) |
| `admin_users` | Admin/operator with role, department, permissions JSONB |
| `user_profiles` | Extended user data + JSONB arrays (preferences, FCM tokens, followed orgs) |
| `job_vacancies` | 30+ columns, JSONB fields, tsvector GENERATED column for FTS |
| `user_job_applications` | Application tracking with status, notes, reminders JSONB |
| `notifications` | In-app notifications with expiry (90 days) |
| `admin_logs` | Audit trail with expiry (30 days) |
| `alembic_version` | Migration state |

### Migrations

- `0001_initial_schema.py` — 6 core tables + FTS (tsvector GIN index)
- `0002_separate_admin_users.py` — Split users/admin_users, update FKs
- `0003_profile_preferences.py` — `preferred_states`, `preferred_categories`, `followed_organizations` on user_profiles
- `0004_fcm_tokens.py` — `fcm_tokens` JSONB on user_profiles
- `0005_add_fee_columns.py` — `fee_general`, `fee_obc`, `fee_sc_st`, `fee_ews`, `fee_female` on job_vacancies
- `0006_add_source_pdf_path.py` — `source_pdf_path` (Text, nullable) on job_vacancies

### Key DB Constraints

- `ck_applications_status`: applied, admit_card_released, exam_completed, result_pending, selected, rejected, waiting_list
- `ck_notifications_priority`: low, medium, high
- `ck_profiles_gender`: Male, Female, Other (capitalized)
- `ck_profiles_category`: General, OBC, SC, ST, EWS

---

## Project Structure

```
src/backend/
  app/
    main.py              # FastAPI app factory, lifespan, router registration
    config.py            # pydantic_settings Settings (extra="ignore"), singleton
    database.py          # async engine + async_session + sync_engine (psycopg2)
    dependencies.py      # get_db, get_redis, get_current_user, get_current_admin, require_admin, require_operator
    celery_app.py        # Celery config, explicit include list, beat_schedule
    rate_limit.py        # SlowAPI limiter singleton
    models/              # SQLAlchemy 2.0 Mapped models
      base.py, user.py, admin_user.py, user_profile.py, job_vacancy.py,
      application.py, notification.py, admin_log.py
    routers/
      auth.py            # /api/v1/auth/* — user + admin login/register/logout/refresh/reset
      jobs.py            # /api/v1/jobs/* — public listing (FTS), recommended, detail by slug
      users.py           # /api/v1/users/* + /api/v1/organizations/* — profile CRUD, org follow
      admin.py           # /api/v1/admin/* — job CRUD, approve, user mgmt, dashboard, analytics, logs
      applications.py    # /api/v1/applications/* — full CRUD (stats, list, track, get, update, delete)
      notifications.py   # /api/v1/notifications/* — list, count, read, read-all, delete
      health.py          # /api/v1/health
    schemas/
      auth.py, jobs.py, users.py, applications.py, notifications.py
    services/
      matching.py        # Job scoring: state +3, category +3, education +2, recency +1; CANDIDATE_LIMIT=500 caps DB fetch
      pdf_extractor.py   # PDF text extraction (pdfplumber)
      ai_extractor.py    # AI structured extraction (Anthropic Claude API)
    tasks/
      notifications.py   # send_deadline_reminders, send_new_job_notifications,
                         # send_email_notification, send_push_notification, notify_priority_subscribers
      cleanup.py         # purge_expired_notifications, purge_expired_admin_logs, purge_soft_deleted_jobs
      jobs.py            # close_expired_job_listings (bind, max_retries=3), extract_job_from_pdf (deletes PDF after use)
      seo.py             # generate_sitemap
    templates/email/     # Jinja2: base, welcome, verification, password_reset, deadline_reminder, new_job_alert
  tests/                 # 292 tests — 91% coverage
    conftest.py          # Async fixtures: engine-per-test, AsyncClient, auth tokens, test jobs
    unit/                # Direct function tests — no DB/Redis, uses AsyncMock
      test_route_admin.py (34), test_route_applications.py (17),
      test_route_notifications.py (13), test_route_users.py (18),
      test_route_jobs.py (7), test_matching.py (12),
      test_services.py (7), test_tasks.py (12), test_notification_tasks.py (20)
    integration/         # API tests against real DB + Redis
      test_auth.py (~30), test_jobs.py (~25), test_applications.py (~25),
      test_admin.py (~40), test_users.py (~30), test_notifications.py (~25)
    security/
      test_security.py (18)   # JWT, RBAC, XSS, SQLi, CORS, file upload
    e2e/
      test_user_flow.py (4)   # Full lifecycle flows
  .coveragerc              # concurrency = thread,greenlet

src/frontend/
  app/
    __init__.py          # Routes: /, /jobs, /jobs/<slug>, /dashboard, /dashboard/track,
                         # /dashboard/applications/<id>/update, /dashboard/applications/<id>/delete,
                         # /dashboard/applications (HTMX partial), /notifications/*, /profile,
                         # /profile/follow, /profile/unfollow, /register, /forgot-password,
                         # /reset-password, /verify-email/<token>, /login (CSRF), /logout, /offline
                         # _try_refresh() on 401
    api_client.py        # requests wrapper: get, post, put, delete, patch (10s timeout)
    static/              # PWA: manifest.json, sw.js, icons
    templates/           # base.html, index.html, _job_cards.html, job_detail.html,
                         # dashboard.html, _application_rows.html, notifications.html,
                         # profile.html, register.html, forgot_password.html, reset_password.html,
                         # login.html, offline.html, 404.html
  tests/                 # 96 tests — 100% coverage
    conftest.py
    unit/test_api_client.py (17)
    integration/test_routes.py (79)

src/frontend-admin/
  app/
    __init__.py          # Routes: /, /login (CSRF), /logout, /jobs, /jobs/list, /jobs/new,
                         # /jobs/<id>/approve, /jobs/<id>/delete, /jobs/upload, /jobs/<id>/review,
                         # /users, /users/list, /users/<id>, /users/<id>/suspend, /users/<id>/role,
                         # /logs, /logs/list; _try_refresh() on 401; JWT role decoded from token payload
    api_client.py        # Same as frontend + post_file() for PDF uploads (60s timeout)
    templates/           # login.html, dashboard.html (analytics for admin role), jobs.html,
                         # job_new.html, job_upload.html, job_review.html (delete button for admin),
                         # users.html, user_detail.html, logs.html,
                         # _job_rows.html, _user_rows.html (View link), _log_rows.html
  tests/                 # 88 tests — 97% coverage
    conftest.py
    unit/test_api_client.py (18)
    integration/test_routes.py (70)

migrations/versions/     # 0001–0006 Alembic migration files
docs/
  API.md                 # Complete endpoint reference
  DESIGN.md              # Architecture + DB schema
  TESTING.md             # Coverage report for all 3 services
  WORKFLOW_DIAGRAMS.md   # Mermaid diagrams
  CONTEXT.md             # This file — load at session start
```

---

## Auth Design

- `users` table — regular users only (no role)
- `admin_users` table — admin/operator (role, department, permissions JSONB)
- JWT `user_type` claim: `"user"` | `"admin"` for scope isolation
- Redis keys: `hermes:blocklist:{jti}`, `hermes:reset:{token}`, `hermes:verify:{token}`, `hermes:csrf:{token}` (prefix from `REDIS_KEY_PREFIX` setting)
- Access token: 15 min. Refresh: 7 days. JTI blocklisted on logout + refresh rotation.
- Frontends store `refresh_token` in session; auto-refresh on 401 via `_try_refresh()` helper.
- Dependency tuple: `get_current_user()` → `(User, payload_dict)`, `get_current_admin()` → `(AdminUser, payload_dict)`

---

## Test Accounts

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| User | user@test.com | User1234 | active, email verified |
| Admin | admin@test.com | Admin1234 | role=admin, dept=IT Department |
| Operator | operator@test.com | Operator1234 | role=operator, dept=Content Team |

---

## Test Coverage Summary

| Service | Tests | Coverage | Command |
|---------|-------|----------|---------|
| Backend | 292 | 91% | `docker exec -w /app hermes_backend pytest tests/ --cov=app -q` |
| User Frontend | 96 | 100% | `docker exec -w /app hermes_frontend python -m pytest tests/ --cov=app -q` |
| Admin Frontend | 88 | 97% | `docker exec -w /app hermes_frontend_admin python -m pytest tests/ --cov=app -q` |

See `docs/TESTING.md` for per-file breakdown and notes on uncovered lines.

---

## Key Commands

```bash
# Migrations
docker exec -w /app -e PYTHONPATH=/app hermes_backend alembic upgrade head

# Rebuild backend (requirements.txt or migration changes)
cd src/backend && docker compose up -d --build backend celery_worker celery_beat

# Restart backend only (hot-reload app/ code changes)
docker restart hermes_backend

# Restart Celery worker (after task code changes)
docker restart hermes_celery_worker

# Run backend tests + coverage
docker exec -w /app hermes_backend pytest tests/ --cov=app --cov-report=term-missing -q

# Run frontend tests
docker exec -w /app hermes_frontend python -m pytest tests/ --cov=app -q
docker exec -w /app hermes_frontend_admin python -m pytest tests/ --cov=app -q

# Rebuild frontends
cd src/frontend && docker compose up -d --build
cd src/frontend-admin && docker compose up -d --build

# Check Celery task registration
docker exec hermes_celery_worker celery -A app.celery_app inspect registered
```

---

## Phase History

| Phase | Issues | Status | What Was Built |
|-------|--------|--------|----------------|
| 1 | #114–#120 | ✅ | Alembic migrations (0001–0002), all auth endpoints, JWT + Redis blocklist, PgBouncer setup |
| 2 | #121–#124 | ✅ | Job CRUD + FTS search, admin approve + audit logging, user profile endpoints, frontend job listing (HTMX) |
| 3 | #125–#126 | ✅ | Job matching/recommendations engine, org follow/unfollow, Celery new-job notifications |
| 4 | #127–#129 | ✅ | Application tracking CRUD, deadline reminder Celery task, user dashboard + login |
| 5 | #130–#132 | ✅ | In-app notifications, email (Mailpit dev), FCM push, notification preferences, frontend bell |
| 6 | #133–#135 | ✅ | Admin frontend, SEO (sitemap, meta, JSON-LD), fee display by category, share buttons |
| 7 | #136–#138 | ✅ | PDF upload + AI extraction (Anthropic Claude), draft review workflow, PWA |
| Testing | #139–#140 | ✅ | 406 tests (291 backend + 52 frontend + 62 admin), 91/100/97% coverage, security audit |
| 10 | #144–#148 | ✅ | Complete user frontend: register, forgot/reset password, verify email, profile, org follow/unfollow, recommended jobs tab, application tracking inline edit |
| 11 | #149–#154 | ✅ | Complete admin frontend: analytics dashboard, new job form, job delete, user detail, role management; 476 tests (292 backend + 96 frontend + 88 admin) |
| 8 | #141 | ⏳ Deferred | Production deployment to OCI ARM VM — planned for future |
| 9 | #142–#143 | ⏳ Deferred | React Native mobile app + push notifications — planned for future |

---

## Coding Conventions

### General
- **Be direct and execute.** Brief commands like "do Phase 8" mean: write code, test, commit, push, close issues — all in one go.
- **No over-engineering.** Don't add features not asked for. Don't refactor working code. Don't add docstrings to untouched files.
- **Verify with curl inside Docker** after implementing backend endpoints.

### Python / Backend
- **Module docstrings**: Every `.py` file starts with `"""..."""` listing endpoints or purpose.
- **No function docstrings** unless logic is non-obvious.
- **Type hints**: `str | None` (not `Optional[str]`). `Mapped[type]` for SQLAlchemy columns.
- **Imports**: stdlib → third-party → `app.*`. Alphabetical within groups.
- **Router prefix**: `APIRouter(prefix="/api/v1/...", tags=["..."])`. Exception: `users.py` uses full paths (mixes `/users/*` and `/organizations/*`).
- **Response**: Return plain dicts. `ModelClass.model_validate(obj).model_dump()` to serialize.
- **Pagination**: `{"data": [...], "pagination": {"limit", "offset", "total", "has_more"}}`.
- **Errors**: `raise HTTPException(status_code=status.HTTP_4XX_..., detail="message")`.
- **Auth**: `user, _ = current_user` (dependency returns tuple).
- **DB queries**: `select()` + `.where()`. `result.scalar_one_or_none()` or `result.scalars().all()`.
- **Schemas**: Flat Pydantic models — `CreateRequest`, `UpdateRequest` (all optional), `Response` (from_attributes). No inheritance.
- **Models**: `Mapped[type]`, `mapped_column(...)`, UUID PKs (`default=uuid.uuid4`), `server_default=func.now()`.
- **Migrations**: Numbered `0001_`, `0002_`. Use `op.add_column` / `op.create_table` directly.
- **Celery tasks**: Sync, using `sync_engine` + `Session(sync_engine)` + `text()` for raw SQL.
- **Constants**: `UPPER_SNAKE_CASE` at module level.
- **Route order**: Specific routes (`/stats`, `/count`) BEFORE parameterized routes (`/{id}`) to avoid conflicts.

### Frontend (Flask)
- **Factory pattern**: `create_app()` with routes defined inside the function.
- **HTMX partials**: Return only the HTML fragment. Full page routes return complete template.
- **ApiClient**: `app.api_client` set on the Flask `app` object in `create_app()`. Mocked in tests via `app.api_client = MagicMock()`.
- **Tests**: Flask `test_client()` + `MagicMock` for `api_client`. No real backend calls.

### Git
- **Format**: `type: description (#issue_numbers)` + blank line + bullet body.
- **Types**: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`.
- **Auto-close**: `(#NNN)` in subject closes the issue on push to main.
- **Push to main directly** — no PRs for solo work.

### Docs
- After each phase update: `README.md`, `docs/API.md`, `docs/hermes.postman_collection.json`.
- After test changes update: `docs/TESTING.md`.
- After any structural change update: this file (`docs/CONTEXT.md`).

---

## Implementation Workflow (for each phase)

### Step 1 — Plan
Create a 5–7 item todo list:
```
1. Read phase issues & existing code      (in-progress)
2. #NNN: core backend work                (not-started)
3. #NNN: supporting feature               (not-started)
4. #NNN: frontend/UI                      (not-started)
5. Test endpoints with curl               (not-started)
6. Update docs (README, API.md, Postman)  (not-started)
7. Commit, push, close issues             (not-started)
```

### Step 2 — Research
- Read every file to modify before writing.
- Check DB check constraints (`\d table_name` in psql) before using status values.
- Check `celery_app.py` beat_schedule and include list before adding tasks.

### Step 3 — Implement
- One todo at a time: in-progress → completed → next.
- Backend first (models → schemas → router → tasks), frontend last.
- New migration needed? Write → rebuild → run. New requirements? Rebuild image.

### Step 4 — Test
- Curl happy path, duplicates (409), not found (404), invalid input (400), auth required (401/403), delete + verify gone.
- Check Celery task registration after task changes.

### Step 5 — Update Docs
- `README.md`: status line, roadmap table, project tree.
- `docs/API.md`: new endpoint tables with examples.
- `docs/TESTING.md`: if test counts or coverage changed.
- `docs/CONTEXT.md`: update phase table + latest commit hash.

### Step 6 — Commit & Push
```bash
git add <files>
git commit -m "feat: Phase N — description (#NNN, #NNN)"
git push origin main
```

### Common Bug Patterns
- **500 error** → `docker logs hermes_backend --tail 30`
- **DB constraint violation** → `\d table_name` to find exact allowed values
- **Celery task not found** → restart worker, verify with `inspect registered`
- **Route conflict** → specific routes must come before `/{id}` in the router file
- **PgBouncer issue** → migrations bypass it; check `prepared_statement_cache_size=0`
- **Coverage gaps in async routes** → write direct unit tests calling handler functions with `AsyncMock`, not via HTTP client

---

## Docs Reference

| File | Purpose |
|------|---------|
| `docs/CONTEXT.md` | **This file** — load at session start |
| `docs/API.md` | Complete endpoint reference with request/response examples |
| `docs/DESIGN.md` | Architecture, DB schema, API design decisions |
| `docs/TESTING.md` | Coverage report for backend + frontend + admin |
| `docs/WORKFLOW_DIAGRAMS.md` | Mermaid architecture diagrams |
| `docs/hermes.postman_collection.json` | Postman v2.1 collection (auto-saves tokens) |
