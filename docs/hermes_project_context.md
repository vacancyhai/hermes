# Hermes Project — Complete Context (as of March 22, 2026, Phase 7 complete)

## What It Is
A **Government Job Vacancy Portal** (India-focused). Users register, browse jobs, get personalized recommendations, follow organizations, track applications, receive deadline reminders. Admins manage jobs, users, and content.

## Repo
- Path: `/home/sumant/workspace/hermes`
- Remote: `git@github.com:SumanKr7/hermes.git`
- Branch: `main` (Phase 7 complete)

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
- Job detail page, application dashboard, login/logout
- Connected to backend via `src_backend_network` Docker network

## Docker Stack (`src/backend/docker-compose.yml`)
7 backend services: postgresql (16-alpine), redis (7-alpine), pgbouncer (edoburu/pgbouncer:latest), backend, celery_worker, celery_beat, mailpit (dev email: SMTP 1025, Web UI 8025).
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
- `0004_fcm_tokens.py` — fcm_tokens JSONB column on user_profiles
- `0005_add_fee_columns.py` — fee_general, fee_obc, fee_sc_st, fee_ews, fee_female on job_vacancies
- `0006_add_source_pdf_path.py` — source_pdf_path (Text, nullable) on job_vacancies

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

## Phase-by-Phase Implementation Details

### Phase 1 — Database Schema + Auth (#114–#120) ✅

**Commit:** `2af60a5` → `277ffa5`

**What was built:**

1. **Migration 0001 — Initial Schema (6 tables):**
   - `users` — id (UUID PK), email (unique), password_hash, full_name, phone, role, status, is_verified, is_email_verified, last_login, timestamps. Indexes on email + status. Check constraints on role, status.
   - `user_profiles` — id, user_id (FK→users CASCADE, unique), date_of_birth, gender, category, is_pwd, is_ex_serviceman, state, city, pincode, highest_qualification, education (JSONB), notification_preferences (JSONB). GIN indexes on JSONB columns. Check constraints on gender, category.
   - `job_vacancies` — 30+ columns including JSONB (vacancy_breakdown, eligibility, application_details, documents, exam_details, salary, selection_process), date fields (notification_date through result_date), `search_vector` (tsvector GENERATED COLUMN weighted: A=job_title, B=organization, C=description). GIN index on search_vector. Check constraints on job_type, employment_type, status, source.
   - `user_job_applications` — id, user_id, job_id, application_number, is_priority, applied_on, status, notes, reminders (JSONB), result_info (JSONB). Unique(user_id, job_id). Check constraint `ck_applications_status` with values: applied, admit_card_released, exam_completed, result_pending, selected, rejected, waiting_list.
   - `notifications` — id, user_id, entity_type, entity_id, type, title, message, action_url, is_read, sent_via (ARRAY), priority, created_at, read_at, expires_at (NOW()+90 days). Indexes on user+read, user+created, expires.
   - `admin_logs` — id, admin_id, action, resource_type, resource_id, details, changes (JSONB), ip_address (INET), user_agent, timestamp, expires_at (NOW()+30 days).

2. **Migration 0002 — Separate Admin Users:**
   - Created `admin_users` table (parallel to users): id, email, password_hash, full_name, phone, role (admin/operator), department, permissions (JSONB), status, timestamps.
   - Migrated admin/operator rows from `users` → `admin_users`.
   - Updated FKs: `admin_logs.admin_id` and `job_vacancies.created_by` now point to `admin_users`.
   - Dropped `role` column from `users` (all remaining are regular users).

3. **Auth Router (`app/routers/auth.py`):**
   - User: register (creates user + linked profile), login, logout (JTI → Redis blocklist), refresh (token rotation), forgot-password (Redis token), reset-password, verify-email, csrf-token.
   - Admin: login, logout, refresh (separate /auth/admin/* paths).
   - JWT claims: `sub` (UUID), `user_type` ("user"|"admin"), `type` ("access"|"refresh"), `jti` (UUID for blocklist), `role` (admin tokens only), `exp`, `iat`.
   - Token creation via `_create_token()`, `create_access_token()`, `create_refresh_token()`.
   - Password hashing: passlib bcrypt via `pwd_context`.

4. **Dependencies (`app/dependencies.py`):**
   - `get_redis()` — Lazy singleton aioredis pool.
   - `get_db()` — AsyncSession with auto-commit/rollback.
   - `_decode_and_validate_token()` — Decodes JWT, checks blocklist:{jti}, validates user_type.
   - `get_current_user()` → (User, payload_dict) — User auth dependency.
   - `get_current_admin()` → (AdminUser, payload_dict) — Admin auth dependency.
   - `require_admin()` — Role check (admin only).
   - `require_operator()` — Role check (operator or admin).

5. **Docker Stack:**
   - 6 backend services: postgresql (16-alpine), redis (7-alpine), pgbouncer (edoburu/pgbouncer:latest, transaction mode), backend (uvicorn --reload), celery_worker (concurrency=2), celery_beat.
   - PgBouncer: scram-sha-256, pool_mode=transaction, 20 default/100 max connections.
   - Fixed: asyncpg + PgBouncer requires `prepared_statement_cache_size=0`.
   - Fixed: Alembic migrations bypass PgBouncer (env.py rewrites URL).

**Issues closed:** #114, #115, #116, #117, #118, #119, #120

---

### Phase 2 — Job CRUD + Search + Frontend (#121–#124) ✅

**Commit:** `774c270` → `75aab18`

**What was built:**

1. **Admin Router (`app/routers/admin.py`):**
   - `GET /admin/stats` — Dashboard counts (total jobs, active, draft, total users, active users).
   - `POST /admin/jobs` — Create job (auto-slugifies title via `_slugify()`, enforces unique slug with counter suffix, defaults to draft).
   - `PUT /admin/jobs/{id}` — Update job (tracks changes as JSONB).
   - `PUT /admin/jobs/{id}/approve` — Approve draft → active, sets published_at, triggers `send_new_job_notifications.delay()`.
   - `DELETE /admin/jobs/{id}` — Soft-delete (status → cancelled, admin-only).
   - `GET /admin/users` — List users (searchable by name/email via ILIKE).
   - `GET /admin/users/{id}` — User detail with profile.
   - `PUT /admin/users/{id}/status` — Suspend/activate (admin-only).
   - `GET /admin/logs` — Audit trail with pagination.
   - Audit logging via `_log_action()` — tracks admin_id, action, resource, changes (old→new dict), IP, user-agent. Auto-expires 30 days.

2. **Jobs Router (`app/routers/jobs.py`):**
   - `GET /jobs` — Public listing with FTS: `search_vector @@ plainto_tsquery('english', q)`, ranked by `ts_rank()`. Filters: q, job_type, qualification_level, organization (ILIKE), department (ILIKE), is_featured, is_urgent, status (default: active). Pagination with limit/offset.
   - `GET /jobs/{slug}` — Detail by slug, increments views counter.
   - Response format: `{"data": [...], "pagination": {"limit", "offset", "total", "has_more"}}`.

3. **Users Router (`app/routers/users.py`):**
   - `GET /users/profile` — Returns user data + profile joined.
   - `PUT /users/profile` — Update profile fields via `model_dump(exclude_unset=True)`.
   - `PUT /users/profile/phone` — Update phone on user record.

4. **Schemas:**
   - `auth.py`: RegisterRequest/Response, LoginRequest, TokenResponse, RefreshRequest, ForgotPasswordRequest, ResetPasswordRequest, MessageResponse, UserResponse, AdminLoginRequest, AdminUserResponse.
   - `jobs.py`: JobCreateRequest, JobUpdateRequest, JobResponse (full), JobListItem (summary).
   - `users.py`: ProfileResponse (from_attributes), ProfileUpdateRequest, PhoneUpdateRequest.

5. **Frontend (`src/frontend/`):**
   - Flask factory `create_app()` with routes inside.
   - `GET /` — Full page: search bar + job_type/qualification_level dropdowns + HTMX job cards.
   - `GET /jobs` — HTMX partial: `_job_cards.html` with load-more button.
   - `GET /jobs/<slug>` — Job detail page.
   - `ApiClient` class wrapping urllib for backend communication.
   - Templates: `base.html` (nav, HTMX 2.0 + Alpine.js 3.14 CDN), `index.html`, `_job_cards.html`, `job_detail.html`, `404.html`.
   - Connected to backend network via `src_backend_network` (external Docker network).

**Issues closed:** #121, #122, #123, #124

---

### Phase 3 — Job Matching + Org Follow + Notifications (#125–#126) ✅

**Commit:** `d89474d` → `d836581`

**What was built:**

1. **Migration 0003 — Profile Preferences:**
   - Added to `user_profiles`: `preferred_states` (JSONB, default []), `preferred_categories` (JSONB, default []), `followed_organizations` (JSONB, default []).

2. **Matching Engine (`app/services/matching.py`):**
   - `get_recommended_jobs(user_id, db, limit, offset)` → (jobs, total).
   - Scoring: state match (+3 from eligibility.states or vacancy_breakdown), category match (+3 from vacancy_breakdown keys), education rank match (+2 if user_edu >= job_edu), recency <7d (+1).
   - Education hierarchy: 10th < 12th < diploma < graduate < postgraduate < phd.
   - Fallback: if user has no preferences, returns latest active jobs.
   - Sort: score DESC, then application_end ASC (None deadlines last).

3. **Recommendations Endpoint:**
   - `GET /jobs/recommended` (placed before `/{slug}` to avoid route conflict) — requires user JWT, calls `get_recommended_jobs()`, returns paginated response.

4. **Organization Follow (`app/routers/users.py`):**
   - `POST /organizations/{name}/follow` — Idempotent, case-insensitive, max 50 orgs (`MAX_FOLLOWED_ORGS`).
   - `DELETE /organizations/{name}/follow` — 404 if not following.
   - `GET /users/me/following` — Returns followed_organizations array + count.
   - Storage: JSONB array in `user_profiles.followed_organizations`.

5. **New Job Notifications (`app/tasks/notifications.py`):**
   - `send_new_job_notifications(job_id)` — Celery task triggered by admin approve endpoint.
   - Queries `user_profiles.followed_organizations` via JSONB array search (case-insensitive).
   - Creates `new_job_from_followed_org` notification for each follower.
   - Uses sync_engine + Session + raw SQL via `text()`.

6. **Celery Configuration Fix:**
   - Switched from `autodiscover_tasks` (unreliable) to explicit `include` list in `celery_app.py`.
   - Added `psycopg2-binary` to requirements.txt.
   - Added `sync_engine` in `database.py` (converts asyncpg URL → psycopg2).

**Issues closed:** #125, #126

---

### Phase 4 — Application Tracking + Dashboard (#127–#129) ✅

**Commit:** `89e9f7b`

**What was built:**

1. **Application CRUD (`app/routers/applications.py`):**
   - `GET /applications/stats` — Counts grouped by status (`SELECT status, count(*) GROUP BY status`).
   - `GET /applications` — List own tracked applications. Filters: status, is_priority. Enriched with job info (job_title, slug, organization, application_end). Paginated.
   - `POST /applications` — Track a job. Validates job exists, prevents duplicates (409), increments `job_vacancies.applications_count`.
   - `GET /applications/{id}` — Single application detail with job enrichment.
   - `PUT /applications/{id}` — Update status, notes, priority, application_number. Validates against DB check constraint: applied, admit_card_released, exam_completed, result_pending, selected, rejected, waiting_list.
   - `DELETE /applications/{id}` — Remove from tracker (204), decrements applications_count on job.

2. **Application Schemas (`app/schemas/applications.py`):**
   - `ApplicationCreateRequest` — job_id, application_number, is_priority (default False), notes, status (default "applied").
   - `ApplicationUpdateRequest` — all fields optional.
   - `ApplicationResponse` — full model with from_attributes.

3. **Deadline Reminders (`app/tasks/notifications.py`):**
   - `send_deadline_reminders()` — Celery Beat task, daily 08:00 UTC.
   - Checks T-7, T-3, T-1 days before `application_end`.
   - Joins `user_job_applications` with `job_vacancies` for active jobs.
   - Skips rejected/selected/waiting_list applications.
   - Deduplicates: checks if `deadline_reminder_{N}d` notification already exists for (user, job).
   - Creates notifications with priority: high (1d, 3d), medium (7d).

4. **Frontend Dashboard (`src/frontend/app/__init__.py`):**
   - `GET /dashboard` — Stats grid (total, applied, shortlisted, selected) + status filter tabs + application cards with HTMX load-more. Requires login (redirects to `/login` if no session token).
   - `GET /dashboard/applications` — HTMX partial for load-more.
   - `GET /login` — Login form.
   - `POST /login` — Calls `/auth/login`, stores access_token + user_name in Flask session, redirects.
   - `GET /logout` — Clears session, redirects to `/`.
   - Nav bar updated: Jobs, Dashboard, Login/Logout links.
   - New templates: `dashboard.html` (stats grid, filter tabs, app cards), `_application_rows.html` (HTMX partial), `login.html` (sign-in form).

**Issues closed:** #127, #128, #129

---

## Docs
- docs/API.md — full API endpoint reference (all phases)
- docs/hermes.postman_collection.json — Postman v2.1 collection (auto-saves tokens)
- docs/DESIGN.md — architecture, DB schema, API design
- docs/WORKFLOW_DIAGRAMS.md — Mermaid architecture diagrams
- docs/hermes_project_context.md — this file
- docs/SYSTEM_BRIEFING.md — AI assistant system briefing with coding conventions

## Auth System (all tested & working)
- Redis keys: `blocklist:{jti}`, `reset:{token}`, `verify:{token}`, `csrf:{token}`
- JWT: access (15min) + refresh (7day), JTI in Redis blocklist on logout/refresh rotation
- Separate user/admin auth: /auth/login (users), /auth/admin/login (admins)
- JWT `user_type` claim: "user" or "admin" for scope isolation
- Dependencies: get_current_user (users), get_current_admin (admin/operator), require_admin, require_operator

## GitHub Issues
- 30 issues (#114-#143) across 9 phases
- Phase 1 (#114-#120): CLOSED — migration + auth endpoints
- Phase 2 (#121-#124): CLOSED — Job CRUD, search, user profile, frontend job listing
- Phase 3 (#125-#126): CLOSED — Job matching + org follow + Celery notifications
- Phase 4 (#127-#129): CLOSED — Application tracking, deadline reminders, user dashboard
- Phase 5 (#130-#132): CLOSED — In-app notification endpoints, email (Mailpit dev), FCM push, notification preferences, frontend bell
- Phase 6 (#133-#135): CLOSED — Admin frontend (dashboard, job/user mgmt, logs), SEO (sitemap, meta, JSON-LD), fee display, share buttons
- Phase 7 (#136-#138): CLOSED — PDF upload + AI extraction, draft review/approve, PWA
- Phase 8 (#139-#141): OPEN — Tests, security audit, deployment
- Phase 9 (#142-#143): OPEN — React Native mobile app
- 34 labels total (9 story labels + component/type/size/priority labels)

## Test Accounts
- User: user1@test.com / UserPass123 (regular user, has prefs: graduate, Delhi, general/obc, follows UPSC)
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

---

## Phase 5 — Email, Push & In-App Notifications (#130–#132) ✅

**Commit:** `2c00666`

**What was built:**

1. **In-App Notification Endpoints (`app/routers/notifications.py`):**
   - `GET /notifications` — Paginated, filterable by type/is_read. Returns `{data, pagination}`.
   - `GET /notifications/count` — Unread count `{count: N}`.
   - `PUT /notifications/{id}/read` — Mark single as read (is_read=true, read_at=now). Ownership check.
   - `PUT /notifications/read-all` — Mark all unread → read for user.
   - `DELETE /notifications/{id}` — Delete notification (204). Ownership check.
   - Route order: `/count` and `/read-all` before `/{id}` to avoid conflicts.
   - Schema: `NotificationResponse` in `app/schemas/notifications.py`.

2. **Email Notifications (`app/tasks/notifications.py`):**
   - `send_email_notification(to, subject, template_name, context)` — Celery task using sync `smtplib` + `email.mime`. 3x retry with exponential backoff.
   - Jinja2 templates in `app/templates/email/`: base.html, welcome.html, verification.html, password_reset.html, deadline_reminder.html, new_job_alert.html.
   - `MAIL_ENABLED` toggle in config.py (default: False). Dev uses MailHog.
   - MailHog added to docker-compose.yml: SMTP 1025, Web UI 8025.
   - Email wired into `send_deadline_reminders` and `send_new_job_notifications` via `_queue_email_for_user()` helper (checks `notification_preferences.email`).

3. **Push Notifications (FCM):**
   - `send_push_notification(user_id, title, body, data)` — Celery task using `firebase-admin`. Graceful no-op if `FIREBASE_CREDENTIALS_PATH` not set.
   - Invalid token cleanup: removes tokens with `NotRegistered` errors.
   - Checks `notification_preferences.push` before sending.
   - `firebase-admin==6.5.0` added to requirements.txt.

4. **FCM Token Endpoints (`app/routers/users.py`):**
   - `POST /users/me/fcm-token` — Register device token (max 10, deduplication).
   - `DELETE /users/me/fcm-token` — Unregister token.
   - `PUT /users/me/notification-preferences` — Update email/push/in_app toggles.
   - Schemas: `FCMTokenRequest`, `FCMTokenDeleteRequest`, `NotificationPreferencesRequest`.

5. **Migration 0004 — FCM Tokens:**
   - Added `fcm_tokens` (JSONB, default []) to `user_profiles`.

6. **Frontend:**
   - Notification bell (🔔) in nav with HTMX polling every 30s (`hx-get="/notifications/unread-count" hx-trigger="every 30s"`).
   - Notifications page: list with read/unread styling, mark-read, delete, read-all, HTMX load-more.
   - 6 Flask routes: /notifications, /notifications/list (HTMX partial), /notifications/unread-count (badge), /notifications/{id}/read, /notifications/read-all, /notifications/{id}/delete.
   - `patch()` method added to `ApiClient`.

**Issues closed:** #130, #131, #132

---

### Phase 6 — Admin Frontend + SEO + Fee Display (#133–#135) ✅

**What was built:**

1. **Enhanced Admin Stats (`app/routers/admin.py`):**
   - Added `applications.total` count and `users.new_this_week` (past 7 days) to `/admin/stats`.

2. **Admin Frontend (`src/frontend-admin/`):**
   - Full Flask app with login, dashboard, job management, user management, audit log viewer.
   - Dashboard: stat cards (HTMX auto-refresh 60s), quick action links, system info.
   - Job management: table with status filter, approve draft button, HTMX load-more.
   - User management: table with search, status filter, suspend/activate buttons.
   - Audit logs: table with timestamp, action, resource, details, IP.
   - Connected to backend via `src_backend_network`.

3. **SEO — Sitemap (`app/tasks/seo.py`):**
   - `generate_sitemap()` Celery task: queries active jobs, writes XML sitemap with `lastmod`, `changefreq`, `priority`.
   - Served via Nginx at `/sitemap.xml`.

4. **SEO — Meta Tags & JSON-LD (`src/frontend/app/templates/job_detail.html`):**
   - `<title>`: `{title} | {org} | Hermes`.
   - `<meta description>`, `<meta keywords>`, Open Graph tags.
   - JobPosting JSON-LD: title, description, datePosted, validThrough, hiringOrganization, jobLocation, employmentType, educationRequirements, baseSalary.

5. **Migration 0005 — Fee Columns:**
   - Added `fee_general`, `fee_obc`, `fee_sc_st`, `fee_ews`, `fee_female` (nullable int) to `job_vacancies`.
   - Updated model, create/update/response/list schemas, admin create_job endpoint.

6. **Fee Display (`job_detail.html`):**
   - Category-wise fee table: General, OBC, SC/ST, EWS, Female. Shows "Free" if 0, hides row if null.

7. **Share Buttons:**
   - Job detail: WhatsApp, Telegram, Copy Link (clipboard API).
   - Job cards: WhatsApp, Telegram links.

**Issues closed:** #133, #134, #135

---

### Phase 7 — PDF Upload + AI Extraction + PWA (#136–#138) ✅

**What was built:**

1. **PDF Upload + AI Data Extraction (#136):**
   - Added `pdfplumber==0.11.4` and `anthropic==0.42.0` to requirements.
   - `app/config.py`: `PDF_UPLOAD_DIR`, `PDF_MAX_SIZE_MB`, `ANTHROPIC_API_KEY`, `AI_MODEL` settings.
   - Migration 0006: `source_pdf_path` (Text, nullable) on `job_vacancies`.
   - `app/services/pdf_extractor.py`: extracts all text from PDF pages using pdfplumber.
   - `app/services/ai_extractor.py`: sends text to Anthropic Claude with detailed extraction prompt for Indian government job fields. Returns structured JSON. Graceful no-op if API key not set.
   - `app/tasks/jobs.py`: `extract_job_from_pdf` Celery task (bind=True, max_retries=2). Extracts PDF → AI → creates draft job. Fallback: raw text as description if AI fails. Also implemented `close_expired_job_listings` (was stub).
   - `POST /admin/jobs/upload-pdf`: accepts multipart PDF, validates type + size (10MB), saves to upload dir, triggers Celery task, returns 202.
   - Docker: shared `uploads_data` volume between backend and celery_worker.

2. **Draft Review + Approve Workflow (#137):**
   - Admin frontend `/jobs/upload`: PDF upload form with file validation and progress indicator.
   - Admin frontend `/jobs/<id>/review`: full-page form with all extractable fields organized into sections (Basic Info, Description, Dates, Fees, Salary, Source). Save Draft and Approve & Publish buttons.
   - "Upload PDF" button on jobs list page. "Review" button on draft job rows.
   - `api_client.py`: added `post_file()` method for multipart uploads.

3. **PWA — Progressive Web App (#138):**
   - `src/frontend/app/static/manifest.json`: standalone display, portrait orientation, Hermes branding, 192+512 icons.
   - `src/frontend/app/static/sw.js`: service worker with precaching (homepage + offline page), network-first strategy for navigation, offline fallback.
   - `src/frontend/app/templates/offline.html`: user-friendly offline page with retry button.
   - Placeholder icons (192x192 and 512x512 PNG).
   - `base.html`: manifest link, theme-color meta, apple-touch-icon, service worker registration.
   - Flask route `/offline` added.

**Issues closed:** #136, #137, #138
