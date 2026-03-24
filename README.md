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
> decoupled from `job_vacancies`; polymorphic document tables (`job_admit_cards`, `job_answer_keys`, `job_results`) now
> support both jobs and entrance exams via `job_id`/`exam_id` FK; 5-section frontend navigation
> (Jobs / Admit Cards / Answer Keys / Results / Admissions); type-aware gradient detail pages with shared
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
- **Multi-Channel Notifications** — In-app, FCM push (tokens stored in `user_profiles.fcm_tokens`), email (OCI Email Delivery), WhatsApp (placeholder), and **Telegram** (Bot API `sendMessage`; activated when `TELEGRAM_BOT_TOKEN` is set, user stores their chat_id via preferences API); instant mode for OTP/auth, staggered mode for job alerts with configurable delays per channel
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
- **Polymorphic Document Tables** — `job_admit_cards`, `job_answer_keys`, `job_results` link to
  either a job (`job_id`) or entrance exam (`exam_id`) via DB CHECK constraint; 32 phase docs seeded
- **5-Section Navigation** — Jobs, Admit Cards, Answer Keys, Results, Admissions — each with its own
  section page, search, and type-matching gradient hero color
- **Unified Detail Pages** — Type-aware gradient heroes (navy/blue/amber/green/purple per section);
  structured sections for eligibility, selection process, exam pattern, vacancy breakdown, fee table;
  Web Share API button (with clipboard fallback) replacing WhatsApp/Telegram links
- **HTMX Doc Tabs** — Per-phase admit cards, answer keys, and results loaded on-demand in tabbed
  panels on both job detail and admission detail pages
- **Social Share** — Single Share button (Web Share API + clipboard fallback) on every card and detail page
- **Fee by Category** — Shows personalised application fee (₹0 for SC/ST/EWS,
  reduced for OBC) based on the logged-in user's category

## Documentation

| Document | Description |
| -------- | ----------- |
| [docs/DESIGN.md](docs/DESIGN.md) | Full system design: architecture, database schema, API endpoints, Docker environments, security, deployment |
| [docs/DIAGRAMS.md](docs/DIAGRAMS.md) | ASCII workflow diagrams for all major user and system flows |
| [docs/API.md](docs/API.md) | Complete API endpoint reference with request/response examples |
| [docs/hermes.postman_collection.json](docs/hermes.postman_collection.json) | Postman collection for all API endpoints |
| [docs/CONTEXT.md](docs/CONTEXT.md) | Unified session context — load at start of every new AI session |
| [docs/TESTING.md](docs/TESTING.md) | Test coverage report for all three services |

## Development Quick Start

```bash
# 1. Copy development env files and fill in secrets
cp config/development/.env.backend.development       src/backend/.env
cp config/development/.env.frontend.development      src/frontend/.env
cp config/development/.env.frontend-admin.development src/frontend-admin/.env
# Edit src/backend/.env — set FIREBASE_WEB_API_KEY, FIREBASE_AUTH_DOMAIN,
# FIREBASE_PROJECT_ID, and FIREBASE_CREDENTIALS_PATH for your Firebase project.

# 2. Start backend (PostgreSQL, Redis, PgBouncer, FastAPI, Celery)
cd src/backend && docker compose up -d --build

# 3. Run database migrations (creates all 14 tables)
docker exec -w /app -e PYTHONPATH=/app hermes_backend alembic upgrade head
# Migrations: 0001 (initial schema), 0002 (telegram channel), 0003 (job document tables),
#             0004 (entrance_exams + polymorphic doc FK)

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

# 6. (Optional) Start Nginx reverse proxy
cd ../nginx && docker compose up -d

# 7. Run tests
docker exec -w /app -e PYTHONPATH=/app hermes_backend python -m pytest tests/ -v

# Access:
#   Backend API:    http://localhost:8000/api/v1/health
#   API Docs:       http://localhost:8000/api/v1/docs
#   User Frontend:  http://localhost:8080
#   Admin Frontend: http://localhost:8081  (login: admin@example.com / ChangeMe123!)
```

Or use the deploy script: `./scripts/deployment/deploy_all.sh development`

## Project Structure

```
hermes/
├── src/
│   ├── backend/                          # Backend API (port 8000)
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml            # PostgreSQL, Redis, PgBouncer, Backend, Celery
│   │   ├── requirements.txt
│   │   ├── alembic.ini
│   │   ├── app/
│   │   │   ├── main.py                   # FastAPI app entry point
│   │   │   ├── config.py                 # Settings from .env (pydantic-settings)
│   │   │   ├── database.py               # SQLAlchemy async engine + session
│   │   │   ├── celery_app.py             # Celery config + Beat schedule
│   │   │   ├── firebase.py               # Firebase Admin SDK — shared init (Auth + FCM)
│   │   │   ├── logging_config.py         # structlog JSON logging setup
│   │   │   ├── dependencies.py           # FastAPI deps (auth, db session)
│   │   │   ├── routers/                  # FastAPI route modules
│   │   │   │   ├── health.py             # GET /api/v1/health
│   │   │   │   ├── auth.py               # /api/v1/auth/* (verify-token, logout, refresh, admin/*)
│   │   │   │   ├── users.py              # /api/v1/users/*
│   │   │   │   ├── jobs.py               # /api/v1/jobs/*
│   │   │   │   ├── applications.py       # /api/v1/applications/*
│   │   │   │   ├── notifications.py      # /api/v1/notifications/*
│   │   │   │   ├── admin.py              # /api/v1/admin/*
│   │   │   │   ├── job_documents.py      # /api/v1/jobs/{id}/admit-cards|answer-keys|results (public+admin)
│   │   │   │   └── entrance_exams.py     # /api/v1/exams/* (public) + /api/v1/admin/exams/* (admin CRUD)
│   │   │   ├── models/                   # SQLAlchemy models (14 tables)
│   │   │   │   ├── base.py               # DeclarativeBase
│   │   │   │   ├── user.py               # Regular users (no role column)
│   │   │   │   ├── admin_user.py          # Admin/operator accounts
│   │   │   │   ├── user_profile.py
│   │   │   │   ├── job_vacancy.py
│   │   │   │   ├── application.py
│   │   │   │   ├── notification.py
│   │   │   │   ├── user_device.py         # Device registry (FCM, fingerprint, type)
│   │   │   │   ├── notification_delivery_log.py  # Per-channel delivery tracking
│   │   │   │   ├── admin_log.py
│   │   │   │   ├── job_admit_card.py      # Per-phase admit cards (job_id OR exam_id)
│   │   │   │   ├── job_answer_key.py      # Per-phase answer keys (provisional/final)
│   │   │   │   ├── job_result.py          # Per-phase results (shortlist/cutoff/merit_list/final)
│   │   │   │   └── entrance_exam.py       # Entrance/admission exams (NEET, JEE, CLAT, CAT, GATE…)
│   │   │   ├── schemas/                  # Pydantic request/response models
│   │   │   │   ├── auth.py
│   │   │   │   ├── jobs.py               # Includes AdmitCard/AnswerKey/Result schemas
│   │   │   │   ├── users.py
│   │   │   │   ├── applications.py
│   │   │   │   ├── notifications.py
│   │   │   │   └── entrance_exams.py     # EntranceExam create/update/response/list schemas
│   │   │   ├── services/                 # Business logic
│   │   │   │   ├── matching.py           # Job recommendation scoring engine
│   │   │   │   ├── notifications.py      # NotificationService — smart multi-channel routing
│   │   │   │   ├── pdf_extractor.py      # PDF text extraction (pdfplumber)
│   │   │   │   └── ai_extractor.py       # AI structured extraction (Anthropic Claude)
│   │   │   └── tasks/                    # Celery tasks
│   │   │       ├── notifications.py      # smart_notify, deadline reminders, job alerts
│   │   │       ├── cleanup.py            # Purge expired records
│   │   │       ├── jobs.py               # Close expired listings, PDF extraction
│   │   │       └── seo.py                # Generate sitemap
│   │   ├── migrations/                   # Alembic migrations
│   │   │   ├── env.py                    # Async migration runner
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │       ├── 0001_initial_schema.py  # Complete base schema (all core tables)
│   │   │       ├── 0002_add_telegram_channel.py  # Adds telegram to delivery_channel constraint
│   │   │       ├── 0003_job_documents_tables.py  # job_admit_cards, job_answer_keys, job_results
│   │   │       └── 0004_entrance_exams.py  # entrance_exams table + exam_id FK on doc tables
│   │   ├── tests/                               # pytest test suite (313 tests)
│   │   │   ├── conftest.py                      # Async fixtures (DB, client, tokens)
│   │   │   ├── unit/                            # Pure logic tests (no DB/Redis)
│   │   │   ├── integration/                     # API endpoint tests (real DB + Redis)
│   │   │   │   ├── test_auth.py                 # Auth: Firebase verify-token, logout, refresh, admin login
│   │   │   │   ├── test_jobs.py                 # Jobs: CRUD, search, slug, pagination
│   │   │   │   ├── test_applications.py         # Applications: track, update, delete
│   │   │   │   └── test_admin.py                # Admin: stats, user mgmt, RBAC
│   │   │   ├── security/                        # OWASP + auth security tests
│   │   │   │   └── test_security.py             # JWT, uploads, XSS, SQL injection
│   │   │   └── e2e/                             # Multi-step end-to-end flows
│   │   │       └── test_user_flow.py            # Full user + admin lifecycle flows
│   │   └── pytest.ini
│   ├── frontend/                         # User Frontend (port 8080)
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── requirements.txt
│   │   ├── tests/                        # pytest test suite (80 tests)
│   │   │   ├── unit/                     # API client tests
│   │   │   ├── integration/              # Route + template tests
│   │   │   └── e2e/
│   │   └── app/
│   │       ├── __init__.py               # Flask app factory + /auth/firebase-callback relay
│   │       ├── api_client.py             # HTTP client for backend API
│   │       ├── static/
│   │       │   ├── manifest.json         # PWA web app manifest
│   │       │   ├── sw.js                 # Service worker (offline fallback)
│   │       │   ├── icon-192.png          # PWA icon 192x192
│   │       │   └── icon-512.png          # PWA icon 512x512
│   │       └── templates/
│   │           ├── base.html             # Base layout (HTMX + Alpine.js + PWA + shared CSS system)
│   │           ├── index.html            # Jobs section (hero, search, filters, cards)
│   │           ├── admit_cards.html      # Admit Cards section page
│   │           ├── answer_keys.html      # Answer Keys section page
│   │           ├── results.html          # Results section page
│   │           ├── admissions.html       # Admissions & Entrance Exams section page
│   │           ├── _job_cards.html       # HTMX partial — all card types + Share button
│   │           ├── job_detail.html       # Job/admit card/answer key/result detail (type-aware hero)
│   │           ├── admission_detail.html # Entrance exam detail (purple hero, exam pattern, doc tabs)
│   │           ├── _admit_cards_panel.html    # HTMX partial — per-phase admit card docs
│   │           ├── _answer_keys_panel.html    # HTMX partial — per-phase answer key docs
│   │           ├── _results_panel.html        # HTMX partial — per-phase result docs
│   │           ├── dashboard.html        # Application tracking dashboard
│   │           ├── _application_rows.html # HTMX partial (load more apps)
│   │           ├── notifications.html    # Notification center
│   │           ├── login.html            # Firebase JS SDK auth (email, Google, phone OTP)
│   │           ├── profile.html          # User profile + preferences
│   │           ├── offline.html          # PWA offline fallback
│   │           └── 404.html
│   ├── frontend-admin/                   # Admin Frontend (port 8081)
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── requirements.txt
│   │   ├── tests/                        # pytest test suite (88 tests)
│   │   │   ├── unit/                     # API client tests
│   │   │   ├── integration/              # Route + template tests
│   │   │   └── e2e/
│   │   └── app/
│   │       ├── __init__.py               # Flask routes (dashboard, jobs, upload, review, users, logs)
│   │       ├── api_client.py
│   │       └── templates/
│   │           ├── base.html             # Admin layout (nav, styling)
│   │           ├── login.html            # Admin login form
│   │           ├── dashboard.html        # Stats cards + quick actions
│   │           ├── jobs.html             # Job management table
│   │           ├── _job_rows.html        # HTMX partial (job rows)
│   │           ├── job_upload.html       # PDF upload form
│   │           ├── job_review.html       # Draft review/edit + approve
│   │           ├── users.html            # User management table
│   │           ├── _user_rows.html       # HTMX partial (user rows)
│   │           ├── logs.html             # Audit log viewer
│   │           └── _log_rows.html        # HTMX partial (log rows)
│   ├── mobile-app/                       # React Native mobile app (Phase 9 — planned)
│   │   ├── google-services.json          # Android Firebase SDK config (com.hermes.app)
│   │   ├── GoogleService-Info.plist      # iOS Firebase SDK config (com.hermes.app)
│   │   └── README.md                     # Setup instructions + test credentials
│   └── nginx/                            # Reverse Proxy (port 80)
│       ├── docker-compose.yml
│       ├── nginx.conf                    # Rate limiting, routing, security headers
│       └── static/                       # Sitemap served here
├── config/
│   ├── development/                      # Dev env templates
│   │   ├── .env.backend.development
│   │   ├── .env.frontend.development
│   │   └── .env.frontend-admin.development
│   └── production/                       # Prod env templates
│       ├── .env.backend.production
│       ├── .env.frontend.production
│       └── .env.frontend-admin.production
├── scripts/
│   ├── backup/
│   │   ├── backup_db.sh                  # pg_dump daily backup
│   │   └── restore_db.sh                 # Restore from dump
│   └── deployment/
│       ├── deploy_all.sh                 # Copy envs + start all services
│       └── stop_all.sh                   # Stop all services
├── docs/
│   ├── DESIGN.md
│   ├── DIAGRAMS.md
│   ├── API.md
│   ├── hermes.postman_collection.json
│   ├── CONTEXT.md
│   ├── TESTING.md
├── .gitignore
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

