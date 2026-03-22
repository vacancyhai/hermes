# Hermes — System Briefing

You are continuing work on **Hermes**, a Government Job Vacancy Portal (India-focused). This briefing gives you everything you need. Do NOT re-discover what's already documented here.

## Repo & Location
- Workspace: `/home/sumant/workspace/hermes`
- Remote: `git@github.com:SumanKr7/hermes.git`, branch `main`
- GitHub Issues: #114–#143 (30 issues, 9 phases). Phases 1–3 are CLOSED. Phase 4 (#127–#129) is next.

## Architecture
```
Browser → Nginx (80/443)
         ├── /api/*       → Backend  (FastAPI, port 8000)
         ├── /*           → Frontend (Flask,   port 8080)
         └── admin.*      → Admin FE (Flask,   port 8081 — skeleton only)
```

## Tech Stack
**Backend** (`src/backend/`): Python 3.12, FastAPI + Uvicorn, SQLAlchemy 2.0 async (asyncpg), Pydantic v2 (`pydantic_settings`), python-jose JWT (HS256), passlib+bcrypt, Celery 5.4 + Redis 7, SlowAPI, PgBouncer (transaction mode, scram-sha-256).
**Frontend** (`src/frontend/`): Flask 3.1 + Jinja2 + HTMX 2.0 + Alpine.js 3.14.
**Admin Frontend** (`src/frontend-admin/`): Flask 3.1 — skeleton only, not implemented yet.
**Database**: PostgreSQL 16, 8 tables: `users`, `admin_users`, `user_profiles`, `job_vacancies`, `user_job_applications`, `notifications`, `admin_logs`, `alembic_version`. Has tsvector/GIN full-text search.

## Docker (7 services)
`src/backend/docker-compose.yml` — 6 services: postgresql (16-alpine), redis (7-alpine), pgbouncer, backend, celery_worker, celery_beat.
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
      applications.py    # /api/v1/applications/* — skeleton/placeholder
      notifications.py   # /api/v1/notifications/* — user notification endpoints
      health.py          # /api/v1/health
    schemas/
      auth.py, jobs.py, users.py  # Pydantic v2 request/response schemas
    services/
      matching.py        # Job scoring engine (state +3, category +3, education +2, recency +1)
    tasks/
      notifications.py   # send_deadline_reminders (TODO), send_new_job_notifications (done)
      cleanup.py, jobs.py, seo.py  # Scheduled Celery tasks (mostly stubs)
  migrations/versions/
    0001_initial_schema.py
    0002_separate_admin_users.py
    0003_profile_preferences.py

src/frontend/app/
  __init__.py            # Flask app factory with routes (/, /jobs HTMX partial, /jobs/<slug>)
  api_client.py          # requests wrapper for backend API
  templates/             # base.html, index.html, _job_cards.html, job_detail.html, 404.html
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
- **Phase 4** (#127–#129) ⬜: Application tracking, deadline reminders, application dashboard
- **Phase 5** (#130–#132) ⬜: Email, push, in-app notifications
- **Phase 6–9**: Admin dashboard, SEO, PDF ingestion, tests, security, deployment, mobile app

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

**Next up**: Phase 4 (#127–#129) — Application tracking CRUD, deadline reminders Celery task, frontend application dashboard.
