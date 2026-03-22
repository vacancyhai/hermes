# Hermes — Government Job Vacancy Portal

A web application that notifies Indian users about government job vacancies
matched to their education, age, category, and preferences. Includes user
authentication, profile-based job matching, application tracking, multi-channel
notifications, and an admin panel.

> **Status:** Phases 1–6 complete. Auth system, job CRUD, full-text search,
> user profiles, job matching & recommendations, org follow with Celery
> notifications, application tracking with deadline reminders, user dashboard,
> email notifications (Mailpit in dev), FCM push notifications, in-app
> notification endpoints, notification preferences, full admin frontend
> (dashboard, job/user management, audit logs), SEO (sitemap, meta tags,
> JSON-LD structured data), application fee display by category, and
> WhatsApp/Telegram share buttons — all implemented and tested.

## Tech Stack

| Layer              | Technology                                  |
| ------------------ | ------------------------------------------- |
| Backend API        | Python FastAPI, Uvicorn                     |
| Database           | PostgreSQL 16                               |
| ORM                | SQLAlchemy 2.0 (async) + Alembic            |
| Async DB Driver    | asyncpg                                     |
| Auth               | python-jose (JWT + Redis blocklist)          |
| Validation         | Pydantic v2 (FastAPI native)                |
| Task Queue         | Celery 5.4 + Redis 7 broker                |
| Email              | OCI Email Delivery (3,000/day free)         |
| Push Notifications | Firebase Cloud Messaging                    |
| Telegram (future) | Telegram Bot API                             |
| WhatsApp (future) | WhatsApp Cloud API                           |
| User Frontend      | Flask + Jinja2 + HTMX (port 8080)           |
| Admin Frontend     | Flask + Jinja2 + HTMX (port 8081)           |
| Reverse Proxy      | Nginx (behind OCI Load Balancer)            |
| CDN / DDoS         | Cloudflare (free tier)                      |
| Connection Pooling | PgBouncer                                   |
| Logging            | structlog (JSON) → OCI Logging              |
| Image Registry     | OCI Container Registry (500 MB free)        |
| Containerization   | Docker + Docker Compose                     |
| Hosting            | OCI ARM VM (4 OCPU, 24 GB RAM — Always Free)|

## Architecture

All services run on a single OCI ARM instance (Always Free) via Docker Compose.
Traffic enters through an OCI Load Balancer (free 10 Mbps, SSL termination).

```
Browser → Cloudflare (CDN + DDoS) → OCI Load Balancer (SSL) → Nginx
            ├── /api/*        → Backend API  (port 8000)
            ├── /*            → User Frontend (port 8080)
            └── admin.*       → Admin Frontend (port 8081)

Backend containers: PostgreSQL, Redis, FastAPI (Uvicorn), Celery Worker, Celery Beat
```

Frontends communicate with the backend exclusively via REST API
(`BACKEND_API_URL`). They cannot access the database or Redis directly.
PostgreSQL and Redis are isolated inside Docker networks — never exposed to the internet.

## Planned Features

- **Job Matching** — Automatically match jobs to users by education level,
  stream, age, and category
- **Multi-Channel Notifications** — Email, push (FCM), in-app alerts, and
  future Telegram + WhatsApp integration for job alerts and reminders
- **Application Tracker** — Users save jobs, set priority, add notes, and get
  deadline reminders
- **Smart Reminders** — Automatic alerts at 7, 3, and 1 day before deadlines
- **Dynamic UI** — HTMX for live search, infinite scroll, and real-time
  updates without JavaScript frameworks
- **Full-Text Search** — PostgreSQL tsvector-based ranked search on job titles,
  organizations, and descriptions (no Elasticsearch needed)
- **SEO Optimized** — Dynamic sitemap, meta tags, and Google JobPosting
  structured data for organic traffic
- **PDF Job Ingestion** — Upload government notification PDFs, AI extracts
  structured data, operator reviews and publishes
- **PWA Support** — Add-to-home-screen, offline caching, and web push
  notifications before a full mobile app
- **Admin Dashboard** — Job CRUD, user management, analytics
- **Three-Role RBAC** — User, Operator, Admin with scoped permissions
- **Organization Follow** — Follow SSC, UPSC, Railway, etc. to get notified
  on every new job from that org
- **Social Share** — WhatsApp and Telegram share buttons on every job page
- **Fee by Category** — Show "Your application fee: ₹0" based on user's
  category (General/OBC/SC/ST/EWS)

## Documentation

| Document | Description |
| -------- | ----------- |
| [docs/DESIGN.md](docs/DESIGN.md) | Full system design: architecture, database schema, API endpoints, Docker environments, security, deployment |
| [docs/WORKFLOW_DIAGRAMS.md](docs/WORKFLOW_DIAGRAMS.md) | ASCII workflow diagrams for all major user and system flows |
| [docs/API.md](docs/API.md) | Complete API endpoint reference with request/response examples |
| [docs/hermes.postman_collection.json](docs/hermes.postman_collection.json) | Postman collection for all API endpoints |
| [docs/hermes_project_context.md](docs/hermes_project_context.md) | Full project context reference |
| [docs/SYSTEM_BRIEFING.md](docs/SYSTEM_BRIEFING.md) | AI assistant system briefing |

## Development Quick Start

```bash
# 1. Copy development env files
cp config/development/.env.backend.development       src/backend/.env
cp config/development/.env.frontend.development      src/frontend/.env
cp config/development/.env.frontend-admin.development src/frontend-admin/.env

# 2. Start backend (PostgreSQL, Redis, PgBouncer, FastAPI, Celery)
cd src/backend && docker compose up -d --build

# 3. Run database migrations
docker compose exec backend alembic upgrade head

# 4. Start frontends
cd ../frontend       && docker compose up -d --build
cd ../frontend-admin && docker compose up -d --build

# 5. (Optional) Start Nginx reverse proxy
cd ../nginx && docker compose up -d

# Access:
#   Backend API:    http://localhost:8000/api/v1/health
#   API Docs:       http://localhost:8000/api/v1/docs
#   User Frontend:  http://localhost:8080
#   Admin Frontend: http://localhost:8081
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
│   │   │   ├── logging_config.py         # structlog JSON logging setup
│   │   │   ├── dependencies.py           # FastAPI deps (auth, db session)
│   │   │   ├── routers/                  # FastAPI route modules
│   │   │   │   ├── health.py             # GET /api/v1/health
│   │   │   │   ├── auth.py               # /api/v1/auth/*
│   │   │   │   ├── users.py              # /api/v1/users/*
│   │   │   │   ├── jobs.py               # /api/v1/jobs/*
│   │   │   │   ├── applications.py       # /api/v1/applications/*
│   │   │   │   ├── notifications.py      # /api/v1/notifications/*
│   │   │   │   └── admin.py              # /api/v1/admin/*
│   │   │   ├── models/                   # SQLAlchemy models (7 core tables)
│   │   │   │   ├── base.py               # DeclarativeBase
│   │   │   │   ├── user.py               # Regular users (no role column)
│   │   │   │   ├── admin_user.py          # Admin/operator accounts
│   │   │   │   ├── user_profile.py
│   │   │   │   ├── job_vacancy.py
│   │   │   │   ├── application.py
│   │   │   │   ├── notification.py
│   │   │   │   └── admin_log.py
│   │   │   ├── schemas/                  # Pydantic request/response models
│   │   │   │   ├── auth.py
│   │   │   │   ├── jobs.py
│   │   │   │   ├── users.py
│   │   │   │   ├── applications.py
│   │   │   │   └── notifications.py
│   │   │   ├── services/                 # Business logic
│   │   │   │   └── matching.py           # Job recommendation scoring engine
│   │   │   └── tasks/                    # Celery tasks
│   │   │       ├── notifications.py      # Deadline reminders, job alerts
│   │   │       ├── cleanup.py            # Purge expired records
│   │   │       ├── jobs.py               # Close expired listings
│   │   │       └── seo.py                # Generate sitemap
│   │   ├── migrations/                   # Alembic migrations
│   │   │   ├── env.py                    # Async migration runner
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │       ├── 0001_initial_schema.py  # 6 core tables + FTS
│   │   │       ├── 0002_separate_admin_users.py  # Split users/admin_users
│   │   │       ├── 0003_profile_preferences.py   # Matching prefs + org follows
│   │   │       ├── 0004_fcm_tokens.py            # FCM tokens for push notifications
│   │   │       └── 0005_add_fee_columns.py       # Application fee by category
│   │   └── tests/
│   ├── frontend/                         # User Frontend (port 8080)
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── __init__.py               # Flask app factory
│   │       ├── api_client.py             # HTTP client for backend API
│   │       └── templates/
│   │           ├── base.html             # Base layout (HTMX + Alpine.js)
│   │           ├── index.html            # Job listing + search + filters
│   │           ├── _job_cards.html       # HTMX partial (load more)
│   │           ├── job_detail.html       # Job detail page
│   │           ├── dashboard.html       # Application tracking dashboard
│   │           ├── _application_rows.html # HTMX partial (load more apps)│   │           ├── notifications.html   # Notification center│   │           ├── login.html           # Login form
│   │           └── 404.html
│   ├── frontend-admin/                   # Admin Frontend (port 8081)
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── __init__.py               # Flask routes (dashboard, jobs, users, logs)
│   │       ├── api_client.py
│   │       └── templates/
│   │           ├── base.html             # Admin layout (nav, styling)
│   │           ├── login.html            # Admin login form
│   │           ├── dashboard.html        # Stats cards + quick actions
│   │           ├── jobs.html             # Job management table
│   │           ├── _job_rows.html        # HTMX partial (job rows)
│   │           ├── users.html            # User management table
│   │           ├── _user_rows.html       # HTMX partial (user rows)
│   │           ├── logs.html             # Audit log viewer
│   │           └── _log_rows.html        # HTMX partial (log rows)
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
│   ├── WORKFLOW_DIAGRAMS.md
│   ├── API.md
│   ├── hermes.postman_collection.json
│   ├── hermes_project_context.md
│   └── SYSTEM_BRIEFING.md
├── .gitignore
└── README.md
```

## Development Roadmap

| Phase | Scope | Status |
| ----- | ----- | ------ |
| 1     | Database schema, user auth (register, login, JWT, logout, refresh, password reset, email verify, CSRF) | Done |
| 2     | Job vacancy CRUD, full-text search, user profile, admin dashboard, frontend job listing | Done |
| 3     | Job matching algorithm, recommendations, org follow + alerts | Done |
| 4     | Application tracking, deadline reminders, user dashboard | Done |
| 5     | Notification engine (email, push, in-app, future: Telegram + WhatsApp) | Done |
| 6     | Admin frontend (dashboard, job/user mgmt, logs), SEO (sitemap, meta, JSON-LD), fee display, share buttons | Done |
| 7     | PDF ingestion (AI extraction + operator review), PWA | Open |
| 8     | Testing, security audit, production deployment | Open |
| 9     | React Native mobile app (Android + iOS) — same API | Open |

## License

MIT

