# Hermes — Government Job Vacancy Portal

A web application that notifies Indian users about government job vacancies
matched to their education, age, category, and preferences. Includes user
authentication, profile-based job matching, application tracking, multi-channel
notifications, and an admin panel.

> **Status:** Phases 1–7 + Testing + 10 + 11 + UI/Content phase complete.
> Auth (Firebase — Email/Password, Google OAuth, Phone OTP), job CRUD, full-text search, user profiles,
> job matching & recommendations, org follow + Celery notifications, application tracking with deadline reminders,
> user dashboard, smart multi-channel notifications (in-app + FCM push + email + WhatsApp placeholder + Telegram),
> full admin frontend (dashboard, job/user management, audit logs), SEO (sitemap, meta, JSON-LD),
> PDF upload with AI extraction (Anthropic Claude), draft review & approve workflow, CSRF protection,
> PWA (manifest, service worker, offline fallback), comprehensive test suite, security audit.
>
> **Latest additions:** Separate `entrance_exams` table for admission/entrance exams (NEET, JEE, CLAT, CAT, GATE, CUET etc.)
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

Backend containers: PostgreSQL, Redis, FastAPI (Uvicorn), Celery Worker, Celery Beat
```

Frontends communicate with the backend exclusively via REST API
(`BACKEND_API_URL`). They cannot access the database or Redis directly.
PostgreSQL and Redis are isolated inside Docker networks — never exposed to the internet.

## Features

- **Job Matching** — Scores jobs against user profile: reservation category eligibility (+4), state preference (+3), preferred categories (+2), education level (+2), age eligibility vs. `age_min`/`age_max` in job eligibility (+2), and recency bonus (+1); scoring engine in `services/matching.py`. The candidate pool is capped at the 500 most-recent active jobs (a known trade-off documented in the code).
- **Multi-Channel Notifications** — In-app, FCM push (tokens stored in `user_profiles.fcm_tokens`), email (OCI Email Delivery), **WhatsApp** (infrastructure ready, pending API key configuration in `WHATSAPP_API_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID`), and **Telegram** (Bot API `sendMessage`; activated when `TELEGRAM_BOT_TOKEN` is set, user stores their chat_id via preferences API); instant mode for OTP/auth, staggered mode for job alerts with configurable delays per channel
- **Application Tracker** — Users save jobs, set priority, add notes, and get
  deadline reminders
- **Smart Reminders** — Celery Beat tasks fire automatic alerts at 7, 3, and
  1 day before application deadlines
- **Dynamic UI** — HTMX for live search, infinite scroll, and real-time
  updates without JavaScript frameworks
- **Full-Text Search** — PostgreSQL tsvector/GIN-indexed ranked search on job
  titles, organisations, and descriptions (no Elasticsearch needed)
- **SEO Optimized** — Dynamic sitemap, meta tags, and Google JobPosting
  JSON-LD structured data for organic traffic
- **PDF Job Ingestion** — Upload government notification PDFs; AI (Claude)
  extracts structured data; operator reviews, edits, and publishes
- **PWA Support** — Add-to-home-screen, offline fallback page, and web push
  notifications via service worker
- **Admin Panel** — Job CRUD, draft/approve workflow, user management, and
  audit log viewer on a separate frontend (port 8081)
- **Firebase Auth** — Email/password, Google OAuth (popup), and Phone OTP login via Firebase JS SDK; backend verifies Firebase ID tokens and issues internal JWTs; auto-links existing accounts by email; supports legacy user migration. On logout, both the access token and (if provided) the refresh token are revoked in Redis so neither can be reused.
- **Admin Account Management** — New admin/operator accounts are created via `POST /api/v1/admin/admin-users` (admin role only). The first admin must be seeded directly in the DB (see Development Quick Start below).
- **CSRF Protection** — All user frontend POST forms include a session-bound CSRF token validated on the server. The Firebase callback endpoint is exempt (authenticated by Firebase ID token).
- **Two-Tier RBAC** — Regular users (`users` table, user frontend port 8080)
  and Operator/Admin (`admin_users` table with role column, admin frontend
  port 8081); JWT `user_type` claim (`"user"` | `"admin"`) enforces strict
  scope isolation — admin tokens are rejected by user endpoints and vice versa
- **Organisation Follow** — Follow SSC, UPSC, Railway, etc. to get notified
  on every new vacancy from that organisation
- **Entrance Exam Admissions** — Separate `entrance_exams` table for NEET, JEE, CLAT, CAT, CUET, GATE etc.;
  distinct from government job vacancies with exam-specific fields: `stream`, `exam_type`, `counselling_body`,
  `seats_info`, eligibility, exam pattern — 9 exams seeded with full metadata
- **Polymorphic Document Tables** — `admit_cards`, `answer_keys`, `results` link to
  either a job (`job_id`) or entrance exam (`exam_id`) via DB CHECK constraint; 32 phase docs seeded
- **5-Section Navigation** — Jobs, Admit Cards, Answer Keys, Results, Entrance Exams — each with its own
  section page, search, and type-matching gradient hero color
- **Unified Detail Pages** — Type-aware gradient heroes (navy/blue/amber/green/purple per section);
  structured sections for eligibility, selection process, exam pattern, vacancy breakdown, fee table;
  Web Share API button (with clipboard fallback) replacing WhatsApp/Telegram links
- **HTMX Doc Tabs** — Per-phase admit cards, answer keys, and results loaded on-demand in tabbed
  panels on both job detail and entrance exam detail pages
- **Social Share** — Single Share button (Web Share API + clipboard fallback) on every card and detail page
- **Fee by Category** — Shows personalised application fee (₹0 for SC/ST/EWS,
  reduced for OBC) based on the logged-in user's category

## Documentation

| Document | Description |
| -------- | ----------- |
| [docs/DESIGN.md](docs/DESIGN.md) | System design: architecture, auth, Celery tasks, SEO, notifications, CI/CD, security, deployment |
| [docs/DATABASE.md](docs/DATABASE.md) | Full database schema: ERD, all 13 tables, column definitions, indexes, CHECK constraints |
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
#
# Alternatively, use the pre-filled environment templates:
# cp config/development/.env.backend.development       src/backend/.env
# cp config/development/.env.frontend.development      src/frontend/.env
# cp config/development/.env.frontend-admin.development src/frontend-admin/.env

# 2. Start backend (PostgreSQL, Redis, PgBouncer, FastAPI, Celery)
cd src/backend && docker compose up -d --build

# 3. Run database migrations (creates all 13 tables)
docker exec -w /app -e PYTHONPATH=/app hermes_backend alembic upgrade head
# Migrations: 0001 (initial schema), 0002 (add followed_organizations)

# 4. Create the first admin account (required — no self-registration for admins)
docker compose exec backend python -c "
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
import os, uuid
ctx = CryptContext(schemes=['bcrypt'])
engine = create_engine(os.environ['DATABASE_URL'].replace('+asyncpg', ''))
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

# 5. Start frontends
cd ../frontend       && docker compose up -d --build
cd ../frontend-admin && docker compose up -d --build

# 6. Start Nginx reverse proxy (must be last — joins all three Docker networks)
cd ../nginx && docker compose up -d

# 7. Run tests (coverage XML written to /app/coverage.xml automatically)
docker exec hermes_backend python -m pytest tests/unit/ -q

# Access:
#   Backend API:    http://localhost:8000/api/v1/health
#   API Docs:       http://localhost:8000/api/v1/docs
#   User Frontend:  http://localhost:8080
#   Admin Frontend: http://localhost:8081  (login: admin@example.com / ChangeMe123!)
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
- Require status checks: **Unit Tests (pytest + coverage)** and **SonarCloud Scan**
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
├── src/
│   ├── backend/                  # FastAPI REST API (port 8000)
│   │   ├── docker-compose.yml    # PostgreSQL, Redis, PgBouncer, Backend, Celery Worker, Celery Beat
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI app factory, lifespan, router registration
│   │   │   ├── config.py         # pydantic-settings (extra="ignore"), singleton
│   │   │   ├── database.py       # async engine + async_session + sync_engine (Celery)
│   │   │   ├── celery_app.py     # Celery config, explicit include list, beat_schedule
│   │   │   ├── firebase.py       # Firebase Admin SDK — shared init (Auth + FCM)
│   │   │   ├── dependencies.py   # get_db, get_redis, get_current_user, get_current_admin
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
│   │   └── tests/                # 313 tests — 93% coverage (unit, integration, security, e2e)
│   ├── frontend/                 # User Frontend (Flask + HTMX + Alpine.js, port 8080)
│   │   ├── app/
│   │   │   ├── __init__.py       # All routes: /, /admit-cards, /answer-keys, /results,
│   │   │   │                     # /entrance-exams, /entrance-exams/<slug>, /jobs/<slug>,
│   │   │   │                     # /partials/*, /dashboard, /notifications, /profile, /login
│   │   │   ├── api_client.py     # HTTP client for backend API (10s timeout)
│   │   │   ├── static/           # PWA: manifest.json, sw.js, icons
│   │   │   └── templates/        # 20+ Jinja2 templates + HTMX partials
│   │   └── tests/                # 80 tests — 91% coverage
│   ├── frontend-admin/           # Admin Frontend (Flask + HTMX, port 8081)
│   │   ├── app/
│   │   │   ├── __init__.py       # Routes: dashboard, jobs CRUD, entrance exams CRUD, users, logs
│   │   │   ├── api_client.py     # Same as frontend + post_file() for PDF uploads
│   │   │   └── templates/        # 15+ templates including entrance exam edit, job review
│   │   └── tests/                # 88 tests — 97% coverage
│   ├── mobile-app/               # React Native pre-work (Phase 9 — planned)
│   │   ├── google-services.json  # Android Firebase config (com.hermes.app)
│   │   └── GoogleService-Info.plist  # iOS Firebase config
│   └── nginx/                    # Reverse Proxy (port 80/443)
│       ├── nginx.conf            # Rate limiting, routing, security headers
│       └── static/               # Serves sitemap.xml
├── config/
│   ├── development/              # .env.backend/frontend/frontend-admin templates
│   ├── staging/                  # Staging .env templates
│   └── production/               # Production .env templates
├── scripts/
│   ├── backup/                   # backup_db.sh + restore_db.sh
│   └── deployment/               # deploy_all.sh + stop_all.sh + check_config.sh
├── .pre-commit-config.yaml       # Pre-commit hooks (black, isort, flake8, mypy, detect-secrets)
├── .secrets.baseline             # detect-secrets baseline (empty — no secrets in repo)
├── docs/                         # See Documentation table above
└── README.md
```

## Development Roadmap

| Phase | Scope | Status |
| ----- | ----- | ------ |
| 1     | Database schema, user auth (JWT, logout, refresh, Redis blocklist, admin bcrypt login), PgBouncer setup | Done |
| 2     | Job vacancy CRUD, full-text search, user profile, admin dashboard, frontend job listing | Done |
| 3     | Job matching algorithm, recommendations, org follow + alerts | Done |
| 4     | Application tracking, deadline reminders, user dashboard | Done |
| 5     | Notification engine (in-app, FCM push, email, WhatsApp placeholder, Telegram) | Done |
| 6     | Admin frontend (dashboard, job/user mgmt, logs), SEO (sitemap, meta, JSON-LD), fee display | Done |
| 7     | PDF ingestion (AI extraction + operator review), PWA | Done |
| 7.5   | Testing (481 tests — 93/91/97% coverage), security audit (JWT, RBAC, OWASP) | Done |
| 10    | Complete user frontend: profile, org follow, recommended tab, application tracking inline edit | Done |
| 11    | Complete admin frontend: analytics, new job form, job delete, user detail, role management | Done |
| 12    | Job document tables (admit cards / answer keys / results), 5-section nav, entrance_exams DB design, 9 exams seeded, type-aware UI redesign | Done |
| 8     | Production deployment to OCI ARM VM | Deferred — future |
| 9     | React Native mobile app (Android + iOS) | Deferred — future |

## License

MIT
