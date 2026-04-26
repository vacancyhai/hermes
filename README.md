# Hermes — Government Job Vacancy Portal

A web application that notifies Indian users about government job vacancies
matched to their education, age, category, and preferences. Includes user
authentication, profile-based job matching, track-based deadline reminders,
multi-channel notifications, and an admin panel.

> **Status:** Phases 1–7 + 10 + 11 + UI/Content phase complete.
> Auth (Firebase — Email/Password, Google OAuth, Phone OTP), job CRUD, full-text search, user profiles,
> per-job/admission eligibility checking (pre-computed via Celery), org follow, track-based deadline reminders (user_tracks),
> user dashboard, smart multi-channel notifications (in-app + FCM push + email + WhatsApp placeholder),
> full admin frontend (dashboard, job/user management, audit logs), SEO (sitemap, meta, JSON-LD),
> CSRF protection,
> PWA (manifest, service worker, offline fallback), security audit.
>
> **Latest additions:** Separate `admissions` table for admissions (NEET, JEE, CLAT, CAT, GATE, CUET etc.)
> decoupled from `jobs`; polymorphic document tables (`admit_cards`, `answer_keys`, `results`) now
> support both jobs and admissions via `job_id`/`admission_id` FK; 5-section frontend navigation
> (Jobs / Admit Cards / Answer Keys / Results / Admissions); type-aware gradient detail pages with shared
> CSS design system; single Web Share API button replacing third-party share links; 9 admission seed
> entries with full metadata and 32 linked phase documents; fixed frontend detail pages to correctly render
> nested JSON fields (`admission_details`, `eligibility`, `seats_info`, `vacancy_breakdown`, `selection_process`);
> removed standalone admit-cards/answer-keys/results management pages from admin frontend — all phase
> document management is now consolidated within the parent job/admission edit pages.

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
| Email              | OCI Email Delivery (SMTP, port 587 STARTTLS) |
| Push Notifications | Firebase Cloud Messaging                    |
| WhatsApp (future) | WhatsApp Cloud API                           |
| User Frontend      | React 18 + Vite + TailwindCSS (port 3000)   |
| Admin Frontend     | React 18 + Vite + TailwindCSS (port 4000)   |
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
            ├── /*            → User Frontend (port 3000)
            └── admin.*       → Admin Frontend (port 4000)

Backend containers: PostgreSQL, Redis, FastAPI (Uvicorn), hermes-worker, hermes-scheduler
```

Frontends communicate with the backend exclusively via REST API
(`BACKEND_API_URL`). They cannot access the database or Redis directly.
PostgreSQL and Redis are isolated inside Docker networks — never exposed to the internet.

## Features

- **Eligibility Matching** — Determines if a user is eligible for a job/admission based on education, age (with category-specific relaxation), category (from vacancy_breakdown), and domicile. Results are pre-computed asynchronously by Celery tasks (`recompute_eligibility_for_user/job/admission`) into `job_eligibility` and `admission_eligibility` tables. Eligibility endpoints read from cache first, fall back to live compute if no cached row exists.
- **Track Jobs & Admissions** — Users track specific jobs or admissions (`user_tracks` table, max 100 per user) to receive automatic deadline reminders and update notifications.
- **Multi-Channel Notifications** — In-app, FCM push (reads from `user_devices` table; registration API stores to `user_profiles.fcm_tokens`), email (OCI Email Delivery), and **WhatsApp** (infrastructure ready, pending `WHATSAPP_API_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` — currently a no-op placeholder); instant mode for OTP/auth, staggered mode for job alerts with configurable delays per channel.
- **Deadline Reminders** — Celery task `send_deadline_reminders` fires automatic alerts at T-7, T-3, and T-1 days before `application_end` for all trackers of a job or admission. Scheduled daily at 08:00 UTC via `hermes-scheduler` (`celery_app.py` beat_schedule).
- **Full-Text Search** — PostgreSQL tsvector/GIN-indexed ranked search on job titles, organisations, and descriptions (no Elasticsearch needed).
- **SEO Optimized** — Dynamic sitemap, meta tags, and Google JobPosting JSON-LD structured data for organic traffic.
- **PWA Support** — Add-to-home-screen, offline fallback page, and web push notifications via service worker.
- **Admin Panel** — Job CRUD, admission management, user management, and audit log viewer on a separate React+Vite frontend (port 4000).
- **Firebase Auth** — Email/password (OTP-verified), Google OAuth (popup), and Phone OTP login via Firebase JS SDK; backend verifies Firebase ID tokens and issues internal JWTs; auto-links existing accounts by email; supports legacy user migration. On logout, both the access token and (if provided) the refresh token are revoked in Redis so neither can be reused.
- **Admin Account Management** — New admin/operator accounts are created via `POST /api/v1/admin/admin-users` (admin role only). The first admin must be seeded directly in the DB (see Development Quick Start below).
- **Two-Tier RBAC** — Regular users (`users` table, user frontend port 3000) and Operator/Admin (`admin_users` table with role column, admin frontend port 4000); JWT `user_type` claim (`"user"` | `"admin"`) enforces strict scope isolation — admin tokens are rejected by user endpoints and vice versa.
- **Organisation Follow** — Follow SSC, UPSC, Railway, etc. via dedicated endpoints (`POST/DELETE/GET /api/v1/organizations/{org_id}/track`). Follows stored in `user_tracks` with `entity_type='organization'`. When a new active job is posted, followers are notified via `send_new_job_notifications`. The `user_profiles.followed_organizations` JSONB field is deprecated.
- **Admissions** — Separate `admissions` table for NEET, JEE, CLAT, CAT, CUET, GATE etc.; distinct from government job vacancies with exam-specific fields: `stream`, `admission_type`, `counselling_body`, `seats_info`, eligibility, exam pattern.
- **Polymorphic Document Tables** — `admit_cards`, `answer_keys`, `results` each link to either a job (`job_id`) or admission (`admission_id`) via DB CHECK constraint — exactly one parent per row.
- **5-Section Navigation** — Jobs, Admit Cards, Answer Keys, Results, Admissions — each with its own section page, search, and type-matching gradient hero color.
- **Unified Detail Pages** — Type-aware gradient heroes (navy/blue/amber/green/purple per section); structured sections for eligibility, selection process, admission pattern, vacancy breakdown, fee table; Web Share API button (with clipboard fallback).
- **Phase Document Tabs** — Per-phase admit cards, answer keys, and results rendered in tabbed panels on both job detail and admission detail pages, loaded via REST API calls.
- **Social Share** — Single Share button (Web Share API + clipboard fallback) on every card and detail page.

## Documentation

| Document | Description |
| -------- | ----------- |
| [docs/DESIGN.md](docs/DESIGN.md) | System design: architecture, auth, Celery tasks, SEO, notifications, security, deployment |
| [docs/DATABASE.md](docs/DATABASE.md) | Full database schema: ERD, all 16 tables, column definitions, indexes, CHECK constraints |
| [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md) | Email templates, notification channels, OTP flow, delivery modes |
| [docs/API.md](docs/API.md) | Complete API endpoint reference with request/response examples |
| [docs/DIAGRAMS.md](docs/DIAGRAMS.md) | ASCII workflow diagrams for all major user and system flows |
| [docs/MATCHING.md](docs/MATCHING.md) | Eligibility matching engine: criteria, age relaxation, pre-computation tasks |
| [docs/hermes.postman_collection.json](docs/hermes.postman_collection.json) | Postman collection for all API endpoints |

## Development Quick Start

```bash
# 1. Fill in secrets in the development env files
# Edit config/development/.env.backend — required: POSTGRES_PASSWORD, JWT_SECRET_KEY,
# FIREBASE_WEB_API_KEY, FIREBASE_AUTH_DOMAIN, FIREBASE_PROJECT_ID,
# FIREBASE_CREDENTIALS_PATH for your Firebase project.
# (docker-compose.yml reads config/development/.env.* directly — no copying needed)

# 2. Start all services (PostgreSQL, Redis, PgBouncer, FastAPI, hermes-worker, hermes-scheduler, Frontends)
docker compose up -d --build

# 3. Run database migrations
docker exec hermes_backend alembic -c /app/alembic.ini upgrade head
# Migrations: 0001_initial (all core tables), 0002_user_eligibility_tables

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
    \"\"\"), {\"id\": str(uuid.uuid4()), \"email\": \"admin@hermes.com\",
             \"pw\": ctx.hash(\"Admin@123\"), \"name\": \"Admin\"})
    conn.commit()
"
# After the first admin is created, additional accounts can be created via:
# POST /api/v1/admin/admin-users  (admin role only)

# Access:
#   Backend API:    http://localhost:8000/api/v1/health
#   API Docs:       http://localhost:8000/api/v1/docs
#   User Frontend:  http://localhost:3000
#   Admin Frontend: http://localhost:4000  (login: admin@hermes.com / Admin@123)
```

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
- Require status checks: **SonarCloud Scan**
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
│                                 #   hermes-worker, hermes-scheduler, Frontend, Admin Frontend)
├── alembic.ini                   # Alembic config (URL overridden by env.py at runtime)
├── migrations/                   # Alembic migrations (0001_initial — consolidated)
├── src/
│   ├── backend/                  # FastAPI REST API (port 8000)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
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
│   │   │   │   ├── tracks.py        # /api/v1/jobs/{id}/track, /api/v1/admissions/{id}/track
│   │   │   │   ├── notifications.py  # /api/v1/notifications/*
│   │   │   │   ├── admin.py          # /api/v1/admin/*
│   │   │   │   ├── content.py        # /api/v1/admit-cards, /answer-keys, /results
│   │   │   │   ├── admissions.py # /api/v1/admissions/* + /api/v1/admin/admissions/*
│   │   │   │   └── health.py         # /api/v1/health
│   │   │   ├── models/           # SQLAlchemy 2.0 Mapped models (16 tables, see DATABASE.md)
│   │   │   ├── schemas/          # Pydantic v2 request/response models
│   │   │   ├── services/
│   │   │   │   ├── matching.py       # Eligibility engine: check_job_eligibility, check_admission_eligibility
│   │   │   │   └── notifications.py  # NotificationService — 4-channel smart routing (in-app, push, email, WhatsApp)
│   │   │   └── tasks/            # Celery tasks
│   │   │       ├── notifications.py  # smart_notify, deadline reminders, org-follow alerts
│   │   │       ├── eligibility.py    # recompute_eligibility_for_user/job/admission
│   │   │       ├── cleanup.py        # Purge expired notifications + logs
│   │   │       ├── jobs.py           # Close expired listings, admission status update
│   │   │       └── seo.py            # Generate sitemap.xml
│   ├── frontend/                 # User Frontend (React 18 + Vite + TailwindCSS, port 3000)
│   │   ├── Dockerfile            # Multi-stage: dev (Vite HMR) + prod (nginx)
│   │   ├── package.json
│   │   ├── vite.config.js        # Proxy /api/v1/* → backend:8000
│   │   ├── public/               # PWA: manifest.json, sw.js, icons, offline.html
│   │   └── src/
│   │       ├── api/client.js     # Axios + JWT interceptor + auto-refresh
│   │       ├── contexts/         # AuthContext (token, login, logout)
│   │       ├── lib/firebase.js   # Firebase JS SDK init
│   │       ├── components/       # Layout (nav, footer)
│   │       └── pages/            # Dashboard, Jobs, JobDetail, Admissions, AdmissionDetail,
│   │                             # AdmitCards, AnswerKeys, Results, Profile, Notifications, Login
│   ├── frontend-admin/           # Admin Frontend (React 18 + Vite + TailwindCSS, port 4000)
│   │   ├── Dockerfile            # Multi-stage: dev (Vite HMR) + prod (nginx)
│   │   ├── package.json
│   │   ├── vite.config.js        # Proxy /api/v1/* → backend:8000
│   │   └── src/
│   │       ├── api/client.js     # Axios + admin JWT interceptor + auto-refresh
│   │       ├── contexts/         # AuthContext (admin_token, admin_name, admin_role)
│   │       ├── components/       # Layout (sidebar nav, role badge)
│   │       └── pages/            # Login, Dashboard, Jobs+JobForm, Admissions+AdmissionForm,
│   │                             # Users+UserDetail, Organizations+OrgForm, AuditLogs
│   └── nginx/                    # Reverse Proxy (port 80/443)
│       ├── nginx.conf            # Rate limiting, routing, security headers
│       └── static/               # Serves sitemap.xml
├── config/
│   ├── development/              # .env.backend, .env.frontend, .env.frontend-admin (gitignored)
│   ├── staging/                  # .env.backend, .env.frontend, .env.frontend-admin (committed placeholders)
│   └── production/               # .env.backend, .env.frontend, .env.frontend-admin (committed placeholders)
├── scripts/
│   ├── seed_jobs.py              # Seed: 10 jobs + 9 admissions + 32 phase docs (run manually)
│   └── seed_creds.py             # Seed: admin + test user accounts
├── sonar-project.properties      # SonarCloud config (3 source roots)
├── .pre-commit-config.yaml       # Pre-commit hooks (black, isort, flake8, mypy, detect-secrets)
├── .secrets.baseline             # detect-secrets baseline (empty — no secrets in repo)
├── docs/                         # See Documentation table above
└── README.md
```

## License

MIT
