# Hermes Project — Complete Context (as of March 22, 2026)

## What It Is
A **Government Job Vacancy Portal** (India-focused). Users register, browse jobs, get personalized recommendations, follow organizations, track applications, receive deadline reminders. Admins manage jobs, users, and content.

## Repo
- Path: `/home/sumant/workspace/hermes`
- Remote: `git@github.com:SumanKr7/hermes.git`
- Branch: `main` at commit `d836581`

---

## Architecture

```
Browser → Nginx (80/443)
             ├──/api/*       → Backend API (port 8000)
             ├──/*           → User Frontend (port 8080)
             └──admin.*      → Admin Frontend (port 8081)
```

## Backend Tech Stack (`src/backend/`)
- Python 3.12, FastAPI + Uvicorn (port 8000)
- SQLAlchemy 2.0 async + asyncpg (+ psycopg2-binary for Celery sync access)
- Pydantic v2 (Settings with `extra="ignore"`)
- python-jose HS256 JWT (15-min access + 7-day refresh)
- passlib + bcrypt for passwords
- Celery 5.4 + Redis 7 (broker + result backend)
- SlowAPI rate limiting
- PgBouncer (transaction mode, scram-sha-256)

## Frontend Tech Stack (`src/frontend/`)
- Flask 3.1 + Jinja2 + HTMX 2.0 + Alpine.js 3.14
- Job listing with HTMX load-more pagination, search, filters
- Job detail page, 404 page
- Connected to backend via `src_backend_network` Docker network

## Docker Stack (`src/backend/docker-compose.yml`)
6 backend services: postgresql (16-alpine), redis (7-alpine), pgbouncer (edoburu/pgbouncer:latest), backend, celery_worker, celery_beat.
1 frontend service: hermes_frontend (port 8080).

### Critical Config
- PgBouncer: `AUTH_TYPE: scram-sha-256`, pool_mode=transaction, internal port 5432, external 6432
- asyncpg + PgBouncer: requires `connect_args={"prepared_statement_cache_size": 0}` in engine
- Alembic migrations BYPASS PgBouncer — `env.py` uses `MIGRATION_DATABASE_URL` replacing `pgbouncer:5432` → `postgresql:5432`
- Backend volume mount: `./app:/app/app` (only `app/` dir, NOT `migrations/`). Must rebuild image for changes outside `app/`.
- Run migrations: `docker exec -w /app -e PYTHONPATH=/app hermes_backend alembic upgrade head`
- Celery tasks use explicit `include` (not autodiscover) for reliable registration
- Celery sync_engine (psycopg2) in `app/database.py` for sync DB access in tasks

## Database
PostgreSQL 16 with 8 tables: users, admin_users, user_profiles, job_vacancies, user_job_applications, notifications, admin_logs, alembic_version. Full-text search (tsvector + GIN).

### Migrations
- `0001_initial_schema.py` — 6 core tables + FTS
- `0002_separate_admin_users.py` — Split users/admin_users
- `0003_profile_preferences.py` — preferred_states, preferred_categories, followed_organizations

## Docs
- docs/API.md — full API endpoint reference (incl. Phase 3 endpoints)
- docs/hermes.postman_collection.json — Postman v2.1 collection (auto-saves tokens)
- docs/DESIGN.md — architecture, DB schema, API design
- docs/WORKFLOW_DIAGRAMS.md — Mermaid architecture diagrams

## Auth System (all tested & working)
- Redis keys: `blocklist:{jti}`, `reset:{token}`, `verify:{token}`, `csrf:{token}`
- JWT: access (15min) + refresh (7day), JTI in Redis blocklist on logout/refresh rotation
- Separate user/admin auth: /auth/login (users), /auth/admin/login (admins)
- JWT `user_type` claim: "user" or "admin" for scope isolation
- Dependencies: get_current_user (users), get_current_admin (admin/operator), require_admin, require_operator

## Phase 2 — Job CRUD + Frontend
- `app/routers/jobs.py` — public job listing with FTS, filters, pagination; detail by slug
- `app/routers/admin.py` — full job CRUD, approve flow, audit logging, user management, dashboard stats
- `app/routers/users.py` — profile get/update, phone update, org follow/unfollow/list
- `src/frontend/` — Flask + HTMX job listing, search bar, job_type/qualification filters, job detail, 404 page

## Phase 3 — Matching + Org Follow + Notifications
- `app/services/matching.py` — scoring engine: state (+3), category (+3), education (+2), recency (+1)
- `GET /api/v1/jobs/recommended` — personalized recommendations (requires user JWT)
- `POST/DELETE /api/v1/organizations/{name}/follow` — follow/unfollow (max 50, idempotent)
- `GET /api/v1/users/me/following` — list followed orgs
- `app/tasks/notifications.py` — `send_new_job_notifications` Celery task (triggered on job approve, queries JSONB followers, creates in-app notifications)
- user_profiles new columns: `preferred_states`, `preferred_categories`, `followed_organizations` (all JSONB)

## GitHub Issues
- 30 issues (#114-#143) across 9 phases
- Phase 1 (#114-#120): CLOSED — migration + auth endpoints
- Phase 2 (#121-#124): CLOSED — Job CRUD, search, user profile, frontend job listing
- Phase 3 (#125-#126): CLOSED — Job matching + org follow + Celery notifications
- Phase 4 (#127-#129): OPEN — Application tracking, deadline reminders, dashboard
- Phase 5 (#130-#132): OPEN — Email, push, in-app notifications
- Phase 6 (#133-#135): OPEN — Admin dashboard, SEO, fee display
- Phase 7 (#136-#138): OPEN — PDF ingestion, review workflow, PWA
- Phase 8 (#139-#141): OPEN — Tests, security audit, deployment
- Phase 9 (#142-#143): OPEN — React Native mobile app
- 34 labels total (9 story labels + component/type/size/priority labels)

## Test Accounts
- User: user1@test.com / UserPass123 (regular user, has prefs: graduate, Delhi, general/obc)
- Admin: admin@hermes.gov.in / AdminPass123 (role=admin, dept=IT Department)
- Operator: operator@hermes.gov.in / OperPass123 (role=operator, dept=Content Team)
- Old user: test@example.com / NewPass456 (from Phase 1 testing)

## DB Split
- `users` table: regular users only (no role column)
- `admin_users` table: admin/operator with role, department, permissions (JSONB)

## Key Commands
- Run migrations: `docker exec -w /app -e PYTHONPATH=/app hermes_backend alembic upgrade head`
- Rebuild backend: `cd src/backend && docker compose up -d --build backend`
- Restart backend (hot-reload app/ only): `docker restart hermes_backend`
- Rebuild all backend services: `cd src/backend && docker compose up -d --build backend celery_worker celery_beat`
- Start frontend: `cd src/frontend && docker compose up -d --build`
