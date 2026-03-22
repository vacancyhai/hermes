# Hermes — System Briefing

You are continuing work on **Hermes**, a Government Job Vacancy Portal (India-focused). This briefing gives you everything you need. Do NOT re-discover what's already documented here.

## Repo & Location
- Workspace: `/home/sumant/workspace/hermes`
- Remote: `git@github.com:SumanKr7/hermes.git`, branch `main`
- GitHub Issues: #114–#143 (30 issues, 9 phases). Phases 1–7 are CLOSED. Phase 8 (#139–#141) is next.

## Architecture
```
Browser → Nginx (80/443)
         ├── /api/*       → Backend  (FastAPI, port 8000)
         ├── /*           → Frontend (Flask,   port 8080)
         └── admin.*      → Admin FE (Flask,   port 8081)
```

## Tech Stack
**Backend** (`src/backend/`): Python 3.12, FastAPI + Uvicorn, SQLAlchemy 2.0 async (asyncpg), Pydantic v2 (`pydantic_settings`), python-jose JWT (HS256), passlib+bcrypt, Celery 5.4 + Redis 7, SlowAPI, PgBouncer (transaction mode, scram-sha-256).
**Frontend** (`src/frontend/`): Flask 3.1 + Jinja2 + HTMX 2.0 + Alpine.js 3.14.
**Admin Frontend** (`src/frontend-admin/`): Flask 3.1 + Jinja2 + HTMX 2.0 — dashboard, job/user management, audit logs.
**Database**: PostgreSQL 16, 8 tables: `users`, `admin_users`, `user_profiles`, `job_vacancies`, `user_job_applications`, `notifications`, `admin_logs`, `alembic_version`. Has tsvector/GIN full-text search.

## Docker (8 services)
`src/backend/docker-compose.yml` — 7 services: postgresql (16-alpine), redis (7-alpine), pgbouncer, backend, celery_worker, celery_beat, mailpit (dev email).
`src/frontend/docker-compose.yml` — 1 service: hermes_frontend (port 8080), connected via `src_backend_network`.

### Critical Docker/DB Notes
- asyncpg + PgBouncer requires `connect_args={"prepared_statement_cache_size": 0}`
- Alembic migrations BYPASS PgBouncer — `env.py` rewrites URL to connect directly to `postgresql:5432`
- Backend volume mount: `./app:/app/app` only. Changes outside `app/` (like `migrations/`, `requirements.txt`) need `docker compose up -d --build`
- Celery uses explicit `include` in `celery_app.py` (NOT autodiscover — autodiscover was unreliable)
- Celery tasks use a **sync** engine (`psycopg2-binary`) via `app.database.sync_engine` because Celery workers are synchronous

## Key Commands
```bash
# Migrations
docker exec -w /app -e PYTHONPATH=/app hermes_backend alembic upgrade head

# Rebuild backend + workers (for requirements.txt or migration changes)
cd src/backend && docker compose up -d --build backend celery_worker celery_beat

# Restart backend only (hot-reload for app/ code changes)
docker restart hermes_backend

# Restart Celery (after task code changes)
docker restart hermes_celery_worker

# Frontend
cd src/frontend && docker compose up -d --build
```

## Project Structure
```
src/backend/
  app/
    main.py              # FastAPI app factory, lifespan, router registration
    config.py            # pydantic_settings Settings (extra="ignore"), singleton
    database.py          # async engine + async_session + sync_engine
    dependencies.py      # get_db, get_redis, get_current_user, get_current_admin, require_admin, require_operator
    celery_app.py        # Celery config, explicit include, beat_schedule
    logging_config.py
    models/              # SQLAlchemy 2.0 Mapped models
      base.py            # DeclarativeBase
      user.py, admin_user.py, user_profile.py, job_vacancy.py, application.py, notification.py, admin_log.py
    routers/
      auth.py            # /api/v1/auth/* — user + admin login/register/logout/refresh/password-reset
      jobs.py            # /api/v1/jobs/* — public listing (FTS), recommended, detail by slug
      users.py           # /api/v1/users/* + /api/v1/organizations/* — profile CRUD, org follow
      admin.py           # /api/v1/admin/* — job CRUD, approve, user mgmt, dashboard, audit logs
      applications.py    # /api/v1/applications/* — full CRUD (track, list, get, update, delete, stats)
      notifications.py   # /api/v1/notifications/* — list, count, read, read-all, delete
      health.py          # /api/v1/health
    schemas/
      auth.py, jobs.py, users.py, applications.py, notifications.py  # Pydantic v2 schemas
    services/
      matching.py        # Job scoring engine (state +3, category +3, education +2, recency +1)
      pdf_extractor.py   # PDF text extraction (pdfplumber)
      ai_extractor.py    # AI structured extraction (Anthropic Claude)
    tasks/
      notifications.py   # send_deadline_reminders, send_new_job_notifications, send_email_notification, send_push_notification
      cleanup.py         # Purge expired records
      jobs.py            # close_expired_job_listings, extract_job_from_pdf
      seo.py             # generate_sitemap
    templates/email/     # Jinja2 email templates (base, welcome, verification, password_reset, deadline_reminder, new_job_alert)
  migrations/versions/
    0001_initial_schema.py
    0002_separate_admin_users.py
    0003_profile_preferences.py
    0004_fcm_tokens.py
    0005_add_fee_columns.py
    0006_add_source_pdf_path.py

src/frontend/app/
  __init__.py            # Flask app factory with routes (/, /jobs, /jobs/<slug>, /dashboard, /notifications/*, /offline, /login, /logout)
  api_client.py          # requests wrapper for backend API (get, post, put, delete, patch)
  static/                # PWA assets (manifest.json, sw.js, icons)
  templates/             # base.html (notification bell, PWA), index.html, _job_cards.html, job_detail.html, dashboard.html, _application_rows.html, notifications.html, offline.html, login.html, 404.html
```

## Auth Design
- `users` table = regular users (no role). `admin_users` table = admin/operator (role, department, permissions JSONB).
- JWT has `user_type` claim: `"user"` or `"admin"` for scope isolation.
- Redis keys: `blocklist:{jti}`, `reset:{token}`, `verify:{token}`, `csrf:{token}`
- Access token: 15 min. Refresh: 7 days. JTI blocklisted on logout/refresh rotation.

## Test Accounts (in the DB)
| Role     | Email                     | Password      | Notes                                            |
|----------|---------------------------|---------------|--------------------------------------------------|
| User     | user1@test.com            | UserPass123   | Has prefs: graduate, Delhi, general/obc, follows UPSC |
| Admin    | admin@hermes.gov.in       | AdminPass123  | role=admin, dept=IT Department                   |
| Operator | operator@hermes.gov.in    | OperPass123   | role=operator, dept=Content Team                 |
| User     | test@example.com          | NewPass456    | Old test user from Phase 1                       |

## Phase Status
- **Phase 1** (#114–#120) ✅: Alembic migration, all auth endpoints (register, login, logout, refresh, password reset, email verify, admin login/register)
- **Phase 2** (#121–#124) ✅: Job CRUD + FTS search, admin approve flow + audit logging, user profile endpoints, frontend job listing (HTMX)
- **Phase 3** (#125–#126) ✅: Job matching/recommendations, org follow/unfollow, Celery notification on approve
- **Phase 4** (#127–#129) ✅: Application tracking CRUD, deadline reminders, user dashboard + login
- **Phase 5** (#130–#132) ✅: In-app notification endpoints, email via SMTP (Mailpit dev), FCM push, notification preferences, frontend bell
- **Phase 6** (#133–#135) ✅: Admin frontend (dashboard, job/user mgmt, audit logs), SEO (sitemap, meta tags, JSON-LD), fee display by category, share buttons
- **Phase 7** (#136–#138) ✅: PDF upload + AI extraction (Anthropic Claude), draft review/approve workflow, PWA (manifest, service worker, offline)
- **Phase 8–9**: Tests, security audit, production deployment, mobile app

## Docs
- `docs/API.md` — complete endpoint reference with examples
- `docs/hermes.postman_collection.json` — Postman v2.1 collection (auto-saves tokens)
- `docs/DESIGN.md` — architecture, DB schema, API design
- `docs/WORKFLOW_DIAGRAMS.md` — Mermaid architecture diagrams
- `docs/hermes_project_context.md` — this same context in a repo file

---

## My Coding Style — Follow These Conventions

### General
- **Be direct and execute.** I give brief commands like "do Phase 4" or "update docs". Don't ask for clarification — infer intent and go.
- **End-to-end implementation.** When I say "do Phase X", that means: write the code, run migrations, test with curl, fix bugs, commit, push, and close the GitHub issues. All in one go.
- **No over-engineering.** Don't add features I didn't ask for. Don't refactor working code. Don't add docstrings to code you didn't write.
- **Test with curl inside Docker.** After implementing, verify endpoints work by running curl against `localhost:8000` from inside the backend container or from the host.

### Python / Backend
- **Module docstrings**: Every `.py` file starts with a `"""..."""` docstring listing the endpoints or purpose (see `routers/jobs.py`, `routers/admin.py` as examples).
- **No function docstrings** unless the logic is non-obvious. One-liner docstrings only when present.
- **Type hints**: Use Python 3.12 `str | None` syntax (not `Optional[str]`). Use `Mapped[type]` for SQLAlchemy columns.
- **Imports**: stdlib → third-party → `app.*` local imports. One blank line between groups. Alphabetical within groups.
- **Router pattern**: `router = APIRouter(prefix="/api/v1/...", tags=["..."])`. Exception: `users.py` uses full paths (no prefix) because it mixes `/api/v1/users/*` and `/api/v1/organizations/*`.
- **Response pattern**: Return plain dicts, not Pydantic models directly. Use `ModelClass.model_validate(obj).model_dump()` to serialize.
- **Pagination pattern**: Return `{"data": [...], "pagination": {"limit", "offset", "total", "has_more"}}`.
- **Error pattern**: `raise HTTPException(status_code=status.HTTP_4XX_..., detail="message")`. Import status codes from `fastapi.status`.
- **Auth unpacking**: `user, _ = current_user` (the dependency returns a tuple of user + token payload).
- **DB queries**: Use `select()` + `.where()` pattern with SQLAlchemy 2.0 style. `result.scalar_one_or_none()` or `result.scalars().all()`.
- **Schemas**: Flat Pydantic models. `CreateRequest`, `UpdateRequest` (all optional fields), `Response` (with `model_config = {"from_attributes": True}`). No inheritance hierarchies.
- **Models**: `Mapped[type]` annotations, `mapped_column(...)`, UUID primary keys (`default=uuid.uuid4`), `created_at`/`updated_at` with `server_default=func.now()`.
- **Migrations**: Numbered `0001_`, `0002_`, etc. Descriptive revision name. Use `op.add_column` / `op.create_table` directly.
- **Celery tasks**: Sync functions using `sync_engine` + `Session(sync_engine)` + raw SQL via `text()`. Named as `"app.tasks.module.function_name"`.
- **Constants**: Module-level `UPPER_SNAKE_CASE`. E.g., `MAX_FOLLOWED_ORGS = 50`, `STATE_MATCH = 3`.
- **Slugify**: Done in the admin router via `_slugify()` helper, not in the model.

### Frontend
- **Flask factory pattern**: `create_app()` with routes defined inside.
- **HTMX partials**: Route returns just the HTML fragment (e.g., `_job_cards.html`), full page routes return the complete template.
- **Templates**: Jinja2 with `base.html` layout. HTMX attributes in HTML. Alpine.js for client-side state.

### Git
- **Commit format**: `type: description (#issue_numbers)`. Types: `feat`, `fix`, `refactor`, `docs`, `chore`.
- **Multi-line commit body**: Bullet list of what changed, preceded by a blank line.
- **Auto-close issues**: Use `(#NNN)` in commit message subject.
- **Push to main directly** (no PRs for solo work).

### Docs
- After each phase, update: `README.md` (status, roadmap, tree), `docs/API.md` (new endpoints), `docs/hermes.postman_collection.json` (new requests).
- **Postman collection**: Folders per domain, auto-save tokens via test scripts, include all request bodies.

---

---

## Implementation Workflow — How I Execute Each Phase

When the user says "do next phase" or "do Phase N", follow this exact workflow:

### Step 1: Plan — Create a Todo List
Break the phase into a todo list of 5–7 actionable items. Always include these standard steps:

```
1. Read phase issues & existing code          (in-progress)
2. #NNN: [First issue — core backend work]    (not-started)
3. #NNN: [Second issue — supporting feature]  (not-started)
4. #NNN: [Third issue — frontend/UI]          (not-started)
5. Test all endpoints with curl                (not-started)
6. Update docs (README, API.md, Postman)       (not-started)
7. Commit, push, close issues                  (not-started)
```

**Example — Phase 4 todo list:**
```
1. Read Phase 4 issues & existing code         ✅
2. #127: Application tracking CRUD endpoints   ✅
3. #128: Deadline reminders Celery task         ✅
4. #129: Frontend application dashboard         ✅
5. Test all endpoints with curl                 ✅
6. Update docs (README, API.md, Postman)        ✅
7. Commit, push, close issues                   ✅
```

### Step 2: Research — Read Before Writing
- Read every file you plan to modify (models, routers, schemas, tasks, frontend).
- Check DB constraints (`\d table_name` in psql) — they dictate valid status values and column limits.
- Read the existing skeleton/placeholder code — routers like `applications.py` and `notifications.py` were created as stubs in Phase 1.
- Check `celery_app.py` for the Beat schedule and `include` list.

### Step 3: Implement — One Issue at a Time
- Mark one todo as `in-progress`, implement it, mark `completed`, move to next.
- Backend first (models → schemas → router → tasks), frontend last.
- If a new migration is needed: write it, rebuild backend, run it.
- If a new schema file is needed: create it, import in the router.
- If Celery tasks change: restart `hermes_celery_worker`.

### Step 4: Test — Run Tests Inside Docker
- Get a user token: login via `/auth/login` and capture `access_token`.
- Get a test resource ID (e.g., job_id from `/jobs?limit=1`).
- Run a comprehensive test script inside `hermes_backend` container using `urllib` (not `requests` — it's not installed in the container).
- Test: happy path, duplicates (409), not found (404), invalid input (400), auth required (401/403), delete + verify gone.
- Check Celery task registration: `celery -A app.celery_app inspect registered`.

### Step 5: Update Docs
After all tests pass:
- `README.md` — Update status line ("Phases 1–N complete"), roadmap table (Phase N → Done), project tree (new files).
- `docs/API.md` — Add new endpoint tables, query params, request/response examples.
- `docs/hermes.postman_collection.json` — Add new folder with requests, auto-save variables in test scripts.

### Step 6: Commit & Push
- `git add -A && git status` — review staged files.
- Commit with format: `feat: Phase N — description (#issue1, #issue2, #issue3)` + bullet list body.
- `git push origin main` — auto-closes issues via `(#NNN)` in subject.
- Update memory file (`/memories/repo/hermes_project_context.md`) with new commit hash and phase status.

### Bugs & Fixes During Implementation
When something breaks (and it will):
- **500 error**: Check `docker logs hermes_backend --tail 30` for traceback.
- **DB constraint violation**: Run `\d table_name` in psql to find exact check constraint values — match them in code.
- **Celery tasks not found**: Restart worker after code changes. Verify with `inspect registered`.
- **Route conflict** (`/{id}` catching `/stats`): Place specific routes BEFORE parameterized routes in the router.
- **PgBouncer issues**: Migrations bypass it; ensure `prepared_statement_cache_size=0` for asyncpg.

---

## How Each Phase Was Implemented

### Phase 1 — Database Schema + Auth (commit `2af60a5` → `277ffa5`)
- Created Alembic migration 0001 with 6 core tables (users, user_profiles, job_vacancies, user_job_applications, notifications, admin_logs). Each table has UUID PKs, JSONB columns, check constraints, and targeted indexes (GIN for JSONB/FTS, B-tree for lookups).
- `search_vector` is a PostgreSQL GENERATED COLUMN (tsvector) combining weighted fields A=job_title, B=organization, C=description with a GIN index.
- Migration 0002 split auth: created `admin_users` table, migrated admin rows, updated FKs on admin_logs and job_vacancies, dropped `role` column from `users`.
- Auth router with 11 endpoints across `/auth/*` and `/auth/admin/*`. JWT tokens carry `user_type` claim for scope isolation. Token revocation via Redis `blocklist:{jti}` keys.
- Dependencies module: `get_current_user` and `get_current_admin` decode JWT → check blocklist → look up DB → return (model, payload) tuple.
- Docker stack: 6 services. Fixed PgBouncer + asyncpg compatibility (`prepared_statement_cache_size=0`). Alembic env.py rewrites URL to bypass PgBouncer.

### Phase 2 — Job CRUD + Search + Frontend (commit `774c270` → `75aab18`)
- Admin router: full CRUD with `_slugify()` helper (unique slug enforcement with counter suffix), approve flow (draft → active + triggers Celery notification), audit logging via `_log_action()` that captures old→new changes as JSONB.
- Jobs router: FTS via `plainto_tsquery('english', q)` matched against `search_vector`, ranked by `ts_rank()`. 8 query filters (q, job_type, qualification_level, organization, department, is_featured, is_urgent, status). Default active-only.
- Users router: profile GET/PUT with `model_dump(exclude_unset=True)` for partial updates, phone update endpoint.
- Schemas: flat Pydantic models — CreateRequest, UpdateRequest (all optional), Response (from_attributes). No inheritance.
- Frontend: Flask factory with 4 routes (/, /jobs HTMX partial, /jobs/<slug>, health). ApiClient class for backend HTTP calls. Jinja2 templates with HTMX 2.0 load-more and Alpine.js.

### Phase 3 — Matching + Org Follow + Notifications (commit `d89474d` → `d836581`)
- Migration 0003 added 3 JSONB columns to user_profiles: preferred_states, preferred_categories, followed_organizations.
- Matching engine (`services/matching.py`): scores each active job against user profile — state (+3), category (+3), education rank (+2, using hierarchy 10th→phd), recency <7d (+1). Fallback to newest if no preferences.
- `/jobs/recommended` endpoint placed before `/{slug}` in router to avoid route conflict.
- Org follow: JSONB array in user_profiles, max 50, case-insensitive, idempotent follow.
- Celery task `send_new_job_notifications`: triggered on admin approve, queries JSONB followers via `jsonb_array_elements_text()`, creates in-app notifications.
- Fixed Celery autodiscover → explicit `include` list. Added `psycopg2-binary` + `sync_engine` for Celery sync DB access.

### Phase 4 — Application Tracking + Dashboard (commit `89e9f7b`)
- Application CRUD: 6 endpoints (list, stats, create, get, update, delete). Create validates job exists + prevents duplicates (409) + increments `applications_count`. Delete decrements count. Update validates status against DB check constraint: applied, admit_card_released, exam_completed, result_pending, selected, rejected, waiting_list.
- `/applications/stats` placed before `/{id}` to avoid route conflict. Enriches list/detail responses with job info (title, slug, org, deadline).
- Deadline reminders: implemented `send_deadline_reminders()` Celery Beat task (daily 08:00 UTC). Checks T-7, T-3, T-1 days. Joins applications with jobs, skips rejected/selected/waiting_list, deduplicates per (user, job, interval). Priority: high (1d, 3d), medium (7d).
- Frontend: `/dashboard` (stats grid + status filter tabs + HTMX load-more), `/login` (form → POST → store JWT in Flask session), `/logout`. Nav bar updated with Dashboard/Login/Logout links.

### Phase 5 — Email, Push & In-App Notifications (commit `2c00666`)
- In-app notification endpoints: GET /notifications (paginated, filterable), GET /notifications/count, PUT /notifications/{id}/read, PUT /notifications/read-all, DELETE /notifications/{id}. Route order: `/count` and `/read-all` before `/{id}` to avoid conflicts.
- Email: `send_email_notification` Celery task using sync `smtplib` with 3x retry + exponential backoff. 6 Jinja2 HTML templates in `app/templates/email/`. Mailpit in Docker for dev (`1025` SMTP, `8025` web UI). `MAIL_ENABLED` toggle in config.
- Push: `send_push_notification` Celery task with `firebase-admin`. Graceful no-op if `FIREBASE_CREDENTIALS_PATH` not set. Checks `notification_preferences.push`. Cleans invalid tokens on `NotRegistered`.
- FCM endpoints: POST/DELETE `/users/me/fcm-token` (max 10 devices), PUT `/users/me/notification-preferences`.
- Migration 0004: `fcm_tokens` JSONB column on `user_profiles`.
- Email + push wired into `send_deadline_reminders` and `send_new_job_notifications` — checks user prefs before sending.
- Frontend: notification bell (🔔) in nav with HTMX polling every 30s, notifications page with mark-read/delete/read-all, HTMX load-more.

### Phase 6 — Admin Frontend + SEO + Fee Display (commit TBD)
- Enhanced `/admin/stats` endpoint: added `applications.total` and `users.new_this_week` counts.
- Built full admin frontend (`src/frontend-admin/`): login, dashboard with stat cards (HTMX auto-refresh 60s), job management table (status filter, approve draft), user management table (search, suspend/activate), audit log viewer. All with HTMX load-more pagination.
- Admin frontend connected to backend via `src_backend_network` Docker network.
- Implemented `generate_sitemap` Celery task: queries active jobs, writes valid XML sitemap with `lastmod`, `changefreq`, `priority`. Served via Nginx at `/sitemap.xml`.
- Added SEO meta tags to job detail pages: `<title>`, `<meta description>`, `<meta keywords>`, Open Graph (`og:title`, `og:description`, `og:url`, `og:type`, `og:site_name`).
- Added JobPosting JSON-LD structured data (`<script type="application/ld+json">`) on job detail pages: title, description, datePosted, validThrough, hiringOrganization, jobLocation, employmentType, educationRequirements, baseSalary.
- Migration 0005: added 5 nullable integer columns to `job_vacancies`: `fee_general`, `fee_obc`, `fee_sc_st`, `fee_ews`, `fee_female`.
- Fee fields added to model, all schemas (create, update, response, list), and admin create_job endpoint.
- Fee table rendered on job detail page (category-wise breakdown, shows "Free" if 0, hides row if null).
- Share buttons on job detail and job cards: WhatsApp, Telegram, Copy Link (clipboard API).

---

### Phase 7 — PDF Upload + AI Extraction + PWA (commit TBD)
- Added `pdfplumber` and `anthropic` to requirements. Migration 0006: `source_pdf_path` column on `job_vacancies`.
- `services/pdf_extractor.py`: extracts text from PDF pages using pdfplumber.
- `services/ai_extractor.py`: sends PDF text to Anthropic Claude API with a detailed extraction prompt for Indian government job fields. Returns structured JSON. Graceful no-op if API key not set.
- `tasks/jobs.py`: fully implemented `close_expired_job_listings` (daily 02:30 UTC) and new `extract_job_from_pdf` task (PDF text → AI extraction → create draft job in DB with fallback).
- `POST /admin/jobs/upload-pdf` endpoint: accepts multipart PDF, validates type/size, saves to upload dir, triggers Celery extraction task, returns 202 with task_id.
- Docker: shared `uploads_data` volume between backend and celery_worker. Config: `PDF_UPLOAD_DIR`, `PDF_MAX_SIZE_MB`, `ANTHROPIC_API_KEY`, `AI_MODEL`.
- Admin frontend: PDF upload page (`/jobs/upload`), draft review page (`/jobs/<id>/review`) with editable fields for all extracted data + Save Draft / Approve & Publish buttons. "Upload PDF" button on jobs list. "Review" button on draft rows.
- PWA: `manifest.json` (standalone, portrait, Hermes branding), `sw.js` (network-first for navigation, offline fallback), `offline.html` page, 192+512 PNG icons. `base.html` updated with manifest link, theme-color meta, apple-touch-icon, service worker registration.

**Next up**: Phase 8 (#139–#141) — Testing, security audit, production deployment.
