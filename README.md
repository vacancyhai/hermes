# Hermes — Government Job Vacancy Portal

A web application that notifies Indian users about government job vacancies
matched to their education, age, category, and preferences. Includes user
authentication, profile-based job matching, watch-based deadline reminders,
multi-channel notifications, and an admin panel.

> **Status:** Phases 1–7 + Testing + 10 + 11 + UI/Content phase complete.
> Auth (Firebase — Email/Password, Google OAuth, Phone OTP), job CRUD, full-text search, user profiles,
> job matching & recommendations, org follow, watch-based deadline reminders (user_watches),
> user dashboard, smart multi-channel notifications (in-app + FCM push + email + WhatsApp placeholder + Telegram),
> full admin frontend (dashboard, job/user management, audit logs), SEO (sitemap, meta, JSON-LD),
> PDF upload with AI extraction (Anthropic Claude), draft review & approve workflow, CSRF protection,
> PWA (manifest, service worker, offline fallback), comprehensive test suite, security audit.
>
> **Latest additions:** Separate `entrance_exams` table for entrance exams (NEET, JEE, CLAT, CAT, GATE, CUET etc.)
> decoupled from `jobs`; polymorphic document tables (`admit_cards`, `answer_keys`, `results`) now
> support both jobs and entrance exams via `job_id`/`exam_id` FK; 5-section frontend navigation
> (Jobs / Admit Cards / Answer Keys / Results / Entrance Exams); type-aware gradient detail pages with shared
> CSS design system; single Web Share API button replacing WhatsApp/Telegram share links; 9 entrance exam seed
> entries with full metadata and 32 linked phase documents.

## Tech Stack

| Layer              | Technology                                  |
| ------------------ | ------------------------------------------- |
| Backend API        | Python FastAPI, Uvicorn                     |
| Database           | PostgreSQL 16                               |
| ORM                | SQLAlchemy 2.0 (async) + Alembic            |
| Async DB Driver    | asyncpg                                     |
| Auth               | Firebase Auth (Email/Password, Google, Phone OTP), firebase-admin SDK, python-jose (internal JWT + Redis blocklist) |
| Validation         | Pydantic v2 (FastAPI native)                |
| Task Queue         | Celery 5.4 + Redis 7 broker                |
| Email              | OCI Email Delivery (prod) / Mailpit (dev)   |
| Push Notifications | Firebase Cloud Messaging                    |
| WhatsApp (future) | WhatsApp Cloud API                           |
| User Frontend      | Flask + Jinja2 + HTMX (port 8080)           |
| Admin Frontend     | Flask + Jinja2 + HTMX (port 8081)           |
| Reverse Proxy      | Nginx (SSL via Let's Encrypt / Certbot)     |
| CDN / DDoS         | Cloudflare (free tier)                      |
| Connection Pooling | PgBouncer                                   |
| Logging            | structlog (JSON)                            |
| Containerization   | Docker + Docker Compose                     |
| Hosting            | OCI ARM VM (4 OCPU, 24 GB RAM, 200 GB storage — Always Free)|

## Architecture

All services run on a single OCI ARM instance (Always Free) via Docker Compose.
Traffic enters directly through Nginx (SSL via Let's Encrypt / Certbot).

```
Browser → Cloudflare (CDN + DDoS) → Nginx (SSL, port 443)
            ├── /api/*        → Backend API  (port 8000)
            ├── /*            → User Frontend (port 8080)
            └── admin.*       → Admin Frontend (port 8081)

Backend containers: PostgreSQL, Redis, FastAPI (Uvicorn), Celery Worker
```

Frontends communicate with the backend exclusively via REST API
(`BACKEND_API_URL`). They cannot access the database or Redis directly.
PostgreSQL and Redis are isolated inside Docker networks — never exposed to the internet.

## Features

- **Job Matching** — Scores jobs against user profile: reservation category eligibility (+4), state preference (+3), preferred categories (+2), education level (+2), age eligibility vs. `age_min`/`age_max` in job eligibility (+2), and recency bonus (+1); scoring engine in `services/matching.py`. The candidate pool is capped at the 500 most-recent active jobs (a known trade-off documented in the code).
- **Watch Jobs & Exams** — Users watch specific jobs or entrance exams (`user_watches` table, max 100 per user) to receive automatic deadline reminders and update notifications.
- **Multi-Channel Notifications** — In-app, FCM push (tokens stored in `user_profiles.fcm_tokens`), email (OCI Email Delivery), **WhatsApp** (infrastructure ready, pending `WHATSAPP_API_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID`), and **Telegram** (Bot API `sendMessage`; activated when `TELEGRAM_BOT_TOKEN` is set, user stores `telegram_chat_id` via preferences API); instant mode for OTP/auth, staggered mode for job alerts with configurable delays per channel.
- **Deadline Reminders** — Celery task `send_deadline_reminders` fires automatic alerts at T-7, T-3, and T-1 days before `application_end` for all watchers of a job or exam. Scheduled daily at 08:00 UTC via `celery_app.py` beat_schedule.
- **Dynamic UI** — HTMX for live search, infinite scroll, and real-time updates without JavaScript frameworks.
- **Full-Text Search** — PostgreSQL tsvector/GIN-indexed ranked search on job titles, organisations, and descriptions (no Elasticsearch needed).
- **SEO Optimized** — Dynamic sitemap, meta tags, and Google JobPosting JSON-LD structured data for organic traffic.
- **PDF Job Ingestion** — Upload government notification PDFs; AI (Claude) extracts structured data; operator reviews, edits, and publishes.
- **PWA Support** — Add-to-home-screen, offline fallback page, and web push notifications via service worker.
- **Admin Panel** — Job CRUD, draft/approve workflow, entrance exam management, user management, and audit log viewer on a separate frontend (port 8081).
- **Firebase Auth** — Email/password (OTP-verified), Google OAuth (popup), and Phone OTP login via Firebase JS SDK; backend verifies Firebase ID tokens and issues internal JWTs; auto-links existing accounts by email; supports legacy user migration. On logout, both the access token and (if provided) the refresh token are revoked in Redis so neither can be reused.
- **Admin Account Management** — New admin/operator accounts are created via `POST /api/v1/admin/admin-users` (admin role only). The first admin must be seeded directly in the DB (see Development Quick Start below).
- **CSRF Protection** — All user frontend POST forms include a session-bound CSRF token validated on the server. The Firebase callback endpoint is exempt (authenticated by Firebase ID token).
- **Two-Tier RBAC** — Regular users (`users` table, user frontend port 8080) and Operator/Admin (`admin_users` table with role column, admin frontend port 8081); JWT `user_type` claim (`"user"` | `"admin"`) enforces strict scope isolation — admin tokens are rejected by user endpoints and vice versa.
- **Organisation Follow** — Follow SSC, UPSC, Railway, etc. (stored in `user_profiles.followed_organizations`) to get notified on every new vacancy from that organisation.
- **Entrance Exams** — Separate `entrance_exams` table for NEET, JEE, CLAT, CAT, CUET, GATE etc.; distinct from government job vacancies with exam-specific fields: `stream`, `exam_type`, `counselling_body`, `seats_info`, eligibility, exam pattern.
- **Polymorphic Document Tables** — `admit_cards`, `answer_keys`, `results` each link to either a job (`job_id`) or entrance exam (`exam_id`) via DB CHECK constraint — exactly one parent per row.
- **5-Section Navigation** — Jobs, Admit Cards, Answer Keys, Results, Entrance Exams — each with its own section page, search, and type-matching gradient hero color.
- **Unified Detail Pages** — Type-aware gradient heroes (navy/blue/amber/green/purple per section); structured sections for eligibility, selection process, exam pattern, vacancy breakdown, fee table; Web Share API button (with clipboard fallback).
- **HTMX Doc Tabs** — Per-phase admit cards, answer keys, and results loaded on-demand in tabbed panels on both job detail and entrance exam detail pages.
- **Social Share** — Single Share button (Web Share API + clipboard fallback) on every card and detail page.
- **Fee by Category** — Shows personalised application fee (₹0 for SC/ST/EWS, reduced for OBC) based on the logged-in user's category.

## Documentation

| Document | Description |
| -------- | ----------- |
| [docs/DESIGN.md](docs/DESIGN.md) | System design: architecture, auth, Celery tasks, SEO, notifications, CI/CD, security, deployment |
| [docs/DATABASE.md](docs/DATABASE.md) | Full database schema: ERD, all 13 tables, column definitions, indexes, CHECK constraints |
| [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md) | Email templates, notification channels, OTP flow, delivery modes |
| [docs/API.md](docs/API.md) | Complete API endpoint reference with request/response examples |
| [docs/DIAGRAMS.md](docs/DIAGRAMS.md) | ASCII workflow diagrams for all major user and system flows |
| [docs/TESTING.md](docs/TESTING.md) | Test commands, CI pipeline, pre-commit hooks, coverage report for all three services |
| [docs/hermes.postman_collection.json](docs/hermes.postman_collection.json) | Postman collection for all API endpoints |

## Development Quick Start

```bash
# 1. Copy env templates for all three services and fill in secrets
cp src/backend/.env.example        src/backend/.env
cp src/frontend/.env.example       src/frontend/.env
cp src/frontend-admin/.env.example src/frontend-admin/.env
# Edit src/backend/.env — required: POSTGRES_PASSWORD, JWT_SECRET_KEY,
# FIREBASE_WEB_API_KEY, FIREBASE_AUTH_DOMAIN, FIREBASE_PROJECT_ID,
# FIREBASE_CREDENTIALS_PATH for your Firebase project.
# Optional: ANTHROPIC_API_KEY (enables AI PDF extraction).

# 2. Start all services (PostgreSQL, Redis, PgBouncer, FastAPI, Celery, Frontends, Mailpit)
docker compose up -d --build

# 3. Run database migrations
docker exec hermes_backend alembic -c /app/alembic.ini upgrade head
# Migrations: 0001 (initial schema), 0002 (add followed_organizations to user_profiles)

# 4. Create the first admin account (required — no self-registration for admins)
docker exec hermes_backend python -c "
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
import os, uuid
ctx = CryptContext(schemes=['bcrypt'])
engine = create_engine(os.environ['DATABASE_URL'].replace('+asyncpg', '+psycopg2'))
with engine.connect() as conn:
    conn.execute(text(\"\"\"
        INSERT INTO admin_users (id, email, password_hash, full_name, role, status, is_email_verified)
        VALUES (:id, :email, :pw, :name, 'admin', 'active', TRUE)
    \"\"\"), {\"id\": str(uuid.uuid4()), \"email\": \"admin@example.com\",
         \"pw\": ctx.hash(\"ChangeMe123!\"), \"name\": \"Admin\"})
    conn.commit()
"
# After the first admin is created, additional accounts can be created via:
# POST /api/v1/admin/admin-users  (admin role only)

# 5. Run tests (backend — coverage XML written to /app/coverage.xml automatically)
docker exec hermes_backend python -m pytest tests/unit/ -q

# Access:
#   Backend API:    http://localhost:8000/api/v1/health
#   API Docs:       http://localhost:8000/api/v1/docs
#   User Frontend:  http://localhost:8080
#   Admin Frontend: http://localhost:8081  (login: admin@example.com / ChangeMe123!)
#   Mailpit UI:     http://localhost:8025
```

Or use the deploy script: `./scripts/deployment/deploy_all.sh development`

## Branching Strategy

All work is done on short-lived branches; `main` is protected and only accepts reviewed PRs.

```
main          ← protected; merges only from reviewed, CI-passing PRs
feature/xxx   ← new features    (e.g. feature/add-whatsapp-notifications)
fix/xxx       ← bug fixes
chore/xxx     ← dependency bumps, config changes
```

**Required GitHub branch protection rules (Settings → Branches → Add rule for `main`):**
- Require pull request before merging
- Require status checks: **Backend Tests**, **User Frontend Tests**, **Admin Frontend Tests**, **E2E Tests**, **SonarCloud Scan**
- Require branches to be up to date before merging

## Pre-commit Hooks

Code quality is enforced locally before every commit. Install once per developer clone:

```bash
sudo apt install pre-commit   # or: pip install pre-commit
pre-commit install            # registers .git/hooks/pre-commit

# Run manually across all files:
pre-commit run --all-files
```

Hooks: `black` (formatting), `isort` (imports), `flake8` (lint), `mypy` (types), `detect-secrets` (credential leak detection), plus standard file-hygiene checks.
See `.pre-commit-config.yaml` for full configuration.

## Project Structure

```
hermes/
├── docker-compose.yml            # Dev: all services (PostgreSQL, Redis, PgBouncer, Backend,
│                                 #   Celery Worker, Frontend, Admin Frontend, Mailpit)
├── docker-compose.test.yml       # CI: same minus celery_worker and mailpit; uses .env.test
├── alembic.ini                   # Alembic config (URL overridden by env.py at runtime)
├── migrations/                   # Alembic migrations (0001 initial, 0002 followed_organizations)
├── src/
│   ├── backend/                  # FastAPI REST API (port 8000)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── pytest.ini            # asyncio_mode=auto; addopts --cov=app
│   │   ├── .env.test             # CI env (committed — no secrets)
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI app factory, lifespan, router registration
│   │   │   ├── config.py         # pydantic-settings (extra="ignore"), singleton
│   │   │   ├── database.py       # async engine + async_session + sync_engine (Celery)
│   │   │   ├── celery_app.py     # Celery config, explicit include list, beat_schedule
│   │   │   ├── firebase.py       # Firebase Admin SDK — shared init (Auth + FCM)
│   │   │   ├── dependencies.py   # get_db, get_redis, get_current_user, get_current_admin, require_admin, require_operator
│   │   │   ├── routers/          # 9 router modules (see API.md for all endpoints)
│   │   │   │   ├── auth.py           # /api/v1/auth/*
│   │   │   │   ├── users.py          # /api/v1/users/*
│   │   │   │   ├── jobs.py           # /api/v1/jobs/*
│   │   │   │   ├── watches.py        # /api/v1/jobs/{id}/watch, /api/v1/entrance-exams/{id}/watch
│   │   │   │   ├── notifications.py  # /api/v1/notifications/*
│   │   │   │   ├── admin.py          # /api/v1/admin/*
│   │   │   │   ├── content.py        # /api/v1/admit-cards, /answer-keys, /results
│   │   │   │   ├── entrance_exams.py # /api/v1/entrance-exams/* + /api/v1/admin/entrance-exams/*
│   │   │   │   └── health.py         # /api/v1/health
│   │   │   ├── models/           # SQLAlchemy 2.0 Mapped models (13 tables, see DATABASE.md)
│   │   │   ├── schemas/          # Pydantic v2 request/response models
│   │   │   ├── services/
│   │   │   │   ├── matching.py       # Job scoring engine (category +4, state +3, education +2…)
│   │   │   │   ├── notifications.py  # NotificationService — 5-channel smart routing
│   │   │   │   ├── pdf_extractor.py  # PDF text extraction (pdfplumber)
│   │   │   │   └── ai_extractor.py   # Structured extraction (Anthropic Claude)
│   │   │   └── tasks/            # Celery tasks
│   │   │       ├── notifications.py  # smart_notify, deadline reminders, job alerts
│   │   │       ├── cleanup.py        # Purge expired notifications + logs
│   │   │       ├── jobs.py           # Close expired listings, PDF extraction, exam status update
│   │   │       └── seo.py            # Generate sitemap.xml
│   │   └── tests/                # unit/ (16 files) + integration/ (10 files)
│   ├── frontend/                 # User Frontend (Flask + HTMX + Alpine.js, port 8080)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.test             # CI env (committed — no secrets)
│   │   ├── app/
│   │   │   ├── __init__.py       # All routes: /, /jobs, /admit-cards, /answer-keys, /results,
│   │   │   │                     # /entrance-exams, /dashboard, /notifications, /profile, /login
│   │   │   ├── _base_api_client.py  # Shared HTTP client base class
│   │   │   ├── api_client.py     # Extends BaseApiClient (10s timeout, X-Request-ID)
│   │   │   ├── static/           # PWA: manifest.json, sw.js, icons
│   │   │   └── templates/        # 20+ Jinja2 templates + HTMX partials
│   │   └── tests/                # unit/test_api_client.py + integration/test_routes.py
│   ├── frontend-admin/           # Admin Frontend (Flask + HTMX, port 8081)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.test             # CI env (committed — no secrets)
│   │   ├── app/
│   │   │   ├── __init__.py       # Routes: dashboard, jobs CRUD, entrance exams CRUD, users, logs
│   │   │   ├── _base_api_client.py  # Shared HTTP client base class
│   │   │   ├── api_client.py     # Extends BaseApiClient + inherits post_file() for PDF uploads
│   │   │   └── templates/        # 15+ templates including entrance exam edit, job review
│   │   └── tests/                # unit/test_api_client.py + integration/test_routes.py
│   ├── mobile-app/               # React Native pre-work (Phase 9 — planned)
│   │   ├── google-services.json  # Android Firebase config (com.hermes.app)
│   │   └── GoogleService-Info.plist  # iOS Firebase config
│   └── nginx/                    # Reverse Proxy (port 80/443)
│       ├── nginx.conf            # Rate limiting, routing, security headers
│       └── static/               # Serves sitemap.xml
├── tests/
│   └── e2e/                      # Cross-service E2E tests (requests library, no browser)
│       ├── conftest.py           # URL + credential fixtures (reads from env vars)
│       ├── requirements.txt      # pytest, pytest-cov, requests
│       ├── test_health.py        # Smoke: all 3 /health endpoints
│       └── test_full_flow.py     # Job lifecycle, admin login flow, watch flow, exam lifecycle
├── config/
│   ├── development/              # .env.backend/frontend/frontend-admin templates
│   ├── staging/                  # Staging .env templates
│   └── production/               # Production .env templates
├── scripts/
│   ├── seed_jobs.py              # Seed: 10 jobs + 9 exams + 32 phase docs (run manually)
│   │                             #   docker cp scripts/seed_jobs.py hermes_backend:/app/seed_jobs.py
│   │                             #   docker exec hermes_backend python seed_jobs.py
│   ├── backup/                   # backup_db.sh + restore_db.sh
│   └── deployment/               # deploy_all.sh + stop_all.sh + check_config.sh
├── sonar-project.properties      # SonarCloud config (3 source roots, 4 test roots, 3 coverage XMLs)
├── .pre-commit-config.yaml       # Pre-commit hooks (black, isort, flake8, mypy, detect-secrets)
├── .secrets.baseline             # detect-secrets baseline (empty — no secrets in repo)
├── docs/                         # See Documentation table above
└── README.md
```

## License

MIT
