# Testing

## Feature Development Workflow

Every new feature, fix, or chore follows this sequence:

```bash
# 1. Create a branch
git checkout -b feature/your-feature-name   # or fix/ chore/

# 2. One-time setup per machine
pre-commit install

# 3. Write code + tests, then run locally
docker exec hermes_backend python -m pytest tests/unit/ -q
docker exec hermes_frontend python -m pytest tests/ -q
docker exec hermes_frontend_admin python -m pytest tests/ -q

# 4. Commit — hooks fire automatically (black, isort, flake8, detect-secrets)
git add .
git commit -m "feat: describe what you did"

# 5. Push and open a PR targeting main
git push origin feature/your-feature-name

# 6. CI runs all 5 jobs — all must pass before merge
# 7. Squash merge via GitHub, delete the branch
```

**Commit message prefixes:** `feat:` `fix:` `chore:` `docs:` `style:` `refactor:` `test:`

> Full workflow detail with branch protection rules and commit conventions: [`docs/DESIGN.md → Feature Development Workflow`](DESIGN.md#feature-development-workflow)

---

## Run Tests Locally

```bash
# Backend — unit tests only (coverage XML written to /app/coverage.xml automatically via pytest.ini)
docker exec hermes_backend python -m pytest tests/unit/ -q

# Backend — all tests (unit + integration)
docker exec hermes_backend python -m pytest tests/ -q

# Backend — integration tests only
docker exec hermes_backend python -m pytest tests/integration/ -q

# User frontend (container must be running)
docker exec hermes_frontend python -m pytest tests/ --cov=app --cov-report=term-missing -q

# Admin frontend (container must be running)
docker exec hermes_frontend_admin python -m pytest tests/ --cov=app --cov-report=term-missing -q

# E2E (requires all 3 services running via docker compose up)
pytest tests/e2e/ -q
```

> **Coverage is automatic for backend:** `src/backend/pytest.ini` sets `addopts = --cov=app --cov-report=xml:/app/coverage.xml --cov-report=term-missing`.

---

## CI Pipeline (GitHub Actions)

The workflow at `.github/workflows/build.yml` runs on every push to `main` and every pull request.
Jobs 1–3 run **in parallel**; job 4 (E2E) waits for all three; job 5 (SonarCloud) waits for all four.

```
push / PR
  ├─► job 1: test                — docker-compose.test.yml up (PG+Redis+PgBouncer+backend)
  │                                  → alembic upgrade head
  │                                  → docker exec test_backend pytest tests/unit/ tests/integration/
  │                                  → coverage artifact: coverage/backend/coverage.xml
  │
  ├─► job 2: test-frontend       — docker build hermes_frontend_ci
  │                                  → docker run (--env-file config/test/.env.frontend, volume-mounted /app/coverage)
  │                                  → pytest tests/ --cov=app
  │                                  → coverage artifact: coverage/frontend/coverage.xml
  │
  ├─► job 3: test-frontend-admin — docker build hermes_frontend_admin_ci
  │                                  → docker run (--env-file config/test/.env.frontend-admin, volume-mounted /app/coverage)
  │                                  → pytest tests/ --cov=app
  │                                  → coverage artifact: coverage/frontend-admin/coverage.xml
  │
  ├─► job 4: test-e2e            — needs [1, 2, 3]
  │     (ubuntu-latest)              → docker-compose.test.yml up --wait (all services)
  │                                  → alembic upgrade head
  │                                  → seed CI admin + user; capture user JWT → E2E_USER_TOKEN
  │                                  → pip install tests/e2e/requirements.txt
  │                                  → pytest tests/e2e/
  │
  └─► job 5: sonarcloud          — needs [1, 2, 3, 4]
        (ubuntu-latest)              → download all 3 coverage artifacts
                                     → SonarCloud scan (sonar-project.properties)
```

| Job | Service | Infra needed | Coverage artifact |
|-----|---------|-------------|-------------------|
| `test` | Backend (FastAPI) | PostgreSQL + Redis + PgBouncer via `docker-compose.test.yml` | `coverage/backend/coverage.xml` |
| `test-frontend` | User frontend (Flask) | None — Flask test client + MagicMock | `coverage/frontend/coverage.xml` |
| `test-frontend-admin` | Admin frontend (Flask) | None — Flask test client + MagicMock | `coverage/frontend-admin/coverage.xml` |
| `test-e2e` | Cross-service | All 3 services via `docker-compose.test.yml` | None |
| `sonarcloud` | — | Needs all 4 jobs | Merges all 3 XMLs |

**Key details:**
- `docker-compose.test.yml` has no `hermes-worker`, `hermes-scheduler`, or `mailpit` — those are dev-only.
- Backend test image bakes `app/` in at build time; `tests/` and `pytest.ini` are volume-mounted so they can be updated without rebuilding.
- Frontend/admin test images run as standalone `docker run` containers with a host-mounted `coverage/` directory to extract the XML.
- E2E tests use the `requests` library for HTTP calls — no browser automation.
- All CI `.env` values come from `config/test/.env.*` files committed to the repo (no production secrets).

---

## Pre-commit Hooks

Hooks run automatically before every `git commit` (installed via `pre-commit install`):

| Hook | Purpose |
|------|---------|
| `trailing-whitespace`, `end-of-file-fixer` | File hygiene |
| `check-yaml`, `check-json`, `check-toml` | Config syntax |
| `check-merge-conflict`, `debug-statements` | Common accidents |
| `black` | Auto-format Python in `src/backend/` |
| `isort` (`--profile=black`) | Sort imports |
| `flake8` + bugbear | Lint `src/backend/app/` only (120-char limit) |
| `detect-secrets` | Block credential leaks (baseline: `.secrets.baseline`) |

```bash
# Run all hooks manually across the full repo:
pre-commit run --all-files
```

---

> **Firebase test credentials** (test phone numbers, OTP bypass) are documented in [DESIGN.md → Authentication & RBAC](DESIGN.md#authentication--rbac).

---

## Backend Tests (`src/backend/tests/`)

**16 unit files + 10 integration files.**

| Module | Coverage | Notes |
|--------|----------|---------|
| `routers/notifications.py` | 100% | |
| `routers/watches.py` | 100% | |
| `routers/jobs.py` | 100% | |
| `routers/users.py` | 73% | Phone/password flows and some profile update paths covered at integration level |
| `routers/admin.py` | 73% | PDF file-write + bulk role/status/log-query paths covered at integration level |
| `routers/content.py` | 96% | |
| `routers/admissions.py` | 97% | |
| `routers/auth.py` | 79% | Firebase-dependent OAuth paths require live credentials |
| `dependencies.py` | 85% | JWT decode, blocklist, RBAC fully covered; async dep wiring uncovered |
| `firebase.py` | 75% | Real Firebase token verify path requires live credentials |
| `services/notifications.py` | 77% | FCM happy path and WhatsApp/Telegram delivery require live credentials |
| `services/matching.py` | 80% | with-prefs scoring paths covered; no-prefs pagination covered |
| `services/ai_extractor.py` | 100% | |
| `services/pdf_extractor.py` | 100% | |
| `tasks/notifications.py` | 67% | Firebase FCM send in `smart_notify` requires credentials; stub tasks uncovered |
| `tasks/cleanup.py` | 100% | |
| `tasks/jobs.py` | 57% | AI-extraction and PDF-parse paths require live Anthropic API |
| `tasks/seo.py` | 100% | |
| `models/*` / `schemas/*` | 100% | |

### Backend Test Files

**Unit (`src/backend/tests/unit/`):**

| File | Covers |
|------|--------|
| `test_route_admin.py` | Dashboard stats, jobs CRUD, user mgmt, audit logs |
| `test_route_notifications.py` | List, mark read/all, delete, has_more pagination |
| `test_route_users.py` | Profile, phone, FCM tokens |
| `test_route_jobs.py` | Listing filters (active-only default), recommended, detail |
| `test_route_content.py` | Admit cards, answer keys, results — public list/detail + admin CRUD; `_validate_document_parent` |
| `test_route_admissions.py` | Public list (filters, pagination, search) + detail; admin list/get/create (slug collision)/update/delete |
| `test_route_watches.py` | Watch/unwatch jobs & admissions (limit enforcement, duplicate guard); list_watched (empty, job-only, admission-only, mixed) |
| `test_route_health.py` | Health check endpoint |
| `test_dependencies.py` | `_decode_and_validate_token` (valid, expired, wrong type, blocklist, scope); `get_current_user/admin`; `require_admin/operator` |
| `test_matching.py` | Job recommendation scoring (state, category, education, age, recency) |
| `test_matching_admissions.py` | Admission recommendation scoring |
| `test_services.py` | PDF extraction, AI parsing |
| `test_tasks.py` | Cleanup, close_expired_job_listings, job extraction |
| `test_notification_tasks.py` | Deadline reminders (7/3/1 day), smart_notify, delayed delivery |
| `test_notification_service.py` | NotificationService: all channels (`_send_push`, fingerprint dedup, `_send_fcm`), prefs, email limits |
| `test_route_jobs.py` | Listing filters, recommended tab, detail by slug |

**Integration (`src/backend/tests/integration/`):**

| File | Covers |
|------|--------|
| `test_auth.py` | Firebase verify-token (new/existing/migrate/suspended/deleted/phone-only), logout (blocklist), refresh, admin login/logout/refresh, RBAC |
| `test_auth_extended.py` | Email OTP registration, password validation, set/change, phone verification, email linking |
| `test_admin.py` | Admin API, stats, RBAC |
| `test_content.py` | Admit cards, answer keys, results — real DB round-trips |
| `test_admissions.py` | Admission CRUD via HTTP + real DB |
| `test_jobs.py` | Public job listing and search (active-only filter) |
| `test_notifications.py` | Notification API |
| `test_security.py` | JWT structure (HS256/exp/iat/jti), RBAC, token revocation, admin bcrypt, XSS, SQLi, CORS |
| `test_users.py` | User profile API |
| `test_watches.py` | Watch/unwatch jobs & admissions via HTTP + real DB |

### Backend Test Strategy

Route **unit tests** call handler functions **directly as async functions** with `AsyncMock` db sessions, bypassing HTTP/ASGI entirely. This avoids SQLAlchemy greenlet switches that cause `coverage.py` to lose trace context after `await db.execute()` calls.

**Integration tests** use `httpx.AsyncClient` with `ASGITransport` against the real FastAPI app, wired to a live PostgreSQL + Redis via the test `conftest.py`. A session-scoped `truncate_all_tables` autouse fixture clears all 14 tables before the test session.

`NotificationService` tests mock all external I/O (FCM, SMTP, Redis) so they run without live services.

Firebase tests mock `app.firebase.verify_id_token` via `unittest.mock.patch` — no live Firebase credentials needed. The `user_token` fixture uses `create_access_token()` directly.

### Why Some Backend Lines Are Uncovered

- **`routers/auth.py`** — Firebase-dependent paths covered at integration level; OAuth flows require live credentials.
- **`routers/watches.py`** — IntegrityError rollback path covered at integration level.
- **`routers/content.py`** — Rarely-reached branches (e.g. both-job-and-exam parent edge cases).
- **`firebase.py`** — Real `verify_id_token()` requires a live Firebase project.
- **`routers/admin.py`** — PDF file-write + Celery dispatch block; covered at integration level.
- **`tasks/notifications.py`** — Firebase FCM send in `smart_notify` requires `FIREBASE_CREDENTIALS_PATH`.
- **`services/notifications.py`** — `_send_fcm_with_status` happy path requires Firebase credentials.
- **`services/ai_extractor.py`** — Requires live Anthropic API credentials.
- **`tasks/seo.py`** — Sitemap file-write path requires filesystem setup.

---

## User Frontend Tests (`src/frontend/tests/`)

**1 unit file + 1 integration file.**

| Module | Coverage | Notes |
|--------|----------|-------|
| `app/__init__.py` | 85% | Firebase JS-handled routes (email-verify deep-link, account-link) not exercised |
| `app/api_client.py` | 100% | All HTTP methods covered |

| File | Covers |
|------|--------|
| `unit/test_api_client.py` | `__init__`, `_headers`, `get`, `post`, `put`, `delete`, `patch` — all methods |
| `integration/test_routes.py` | All routes: index, job listing, job detail, dashboard, notifications, login, `/auth/firebase-callback`, logout, profile, org follow/unfollow, recommended jobs |

### Frontend Test Strategy

Flask `test_client()` with `app.api_client` replaced by a `MagicMock`. No real backend or Firebase calls are made. Auth-required routes are tested both with and without a session token.

All POST form tests include `csrf_token` in the form data. The `/auth/firebase-callback` endpoint is exempt from CSRF validation.

---

## Admin Frontend Tests (`src/frontend-admin/tests/`)

**1 unit file + 1 integration file.**

| Module | Coverage | Notes |
|--------|----------|-------|
| `app/__init__.py` | 82% | Admission and some user-management routes not fully exercised |
| `app/api_client.py` | 96% | All HTTP methods including `post_file` covered |

| File | Covers |
|------|--------|
| `unit/test_api_client.py` | All methods including `post_file` (timeout, headers, files) |
| `integration/test_routes.py` | All routes: dashboard (admin vs operator analytics), jobs, new job, job delete, PDF extraction, draft review, users, user detail, role management, logs |

### Why Some Admin Frontend Lines Are Uncovered

- **`app/__init__.py`** — Admission admin routes and some bulk-action paths not exercised in test suite.

---

## E2E Tests (`tests/e2e/`)

Cross-service HTTP tests using the `requests` library. All three services must be running.

| File | Covers |
|------|--------|
| `test_health.py` | Smoke-tests all 3 service `/health` endpoints |
| `test_full_flow.py` | Job lifecycle (draft → approve → visible on frontend → delete); admin frontend login/navigate/logout; watch job flow (watch → list → unwatch); admission lifecycle |

In CI (job 4), services are started via `docker-compose.test.yml`, an admin and regular user are seeded, the user JWT is captured as `E2E_USER_TOKEN`, then `pytest tests/e2e/` runs on the host runner.
