# Hermes — System Design Document

> **Status:** Phases 1–7.5 + 10 + 11 + 12 complete. Auth (Firebase — Email/Password with OTP verification, Google OAuth, Phone OTP), job CRUD, full-text search,
> user profiles, job matching, org follow, application tracking, notifications
> (email, push, in-app), admin panel, SEO, PDF AI extraction, PWA,
> security audit + 24 bug fixes, 5-section navigation,
> admissions, polymorphic document tables, email notifications for account actions — all implemented. Phase 8 (OCI deployment) next.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema → DATABASE.md](DATABASE.md)
3. [API Endpoints → API.md](API.md)
4. [Error Response Format](#error-response-format)
5. [Authentication & RBAC](#authentication--rbac)
6. [Background Tasks](#background-tasks)
7. [Job Ingestion Strategy](#job-ingestion-strategy)
8. [SEO Strategy](#seo-strategy)
9. [5-Section Frontend Architecture](#5-section-frontend-architecture)
10. [Docker Environments](#docker-environments)
11. [Security Design](#security-design)
12. [Environment Variables](#environment-variables)
13. [Deployment](#deployment)

---

## System Architecture

### Three-Service Architecture

Backend, User Frontend, and Admin Frontend are independent services defined
in a single root `docker-compose.yml` and sharing one Docker network. They
communicate via HTTP REST API.

```
┌────────────────────────────────────────────────────────────┐
│                    User's Browser                          │
└────────────────┬───────────────────────────────────────────┘
                 │ HTTPS (Port 443)
                 ↓
┌────────────────────────────────────────────────────────────┐
│           Nginx Reverse Proxy Container                    │
│         - SSL Termination (Let's Encrypt)                  │
│         - Rate Limiting                                    │
│         - Security Headers                                 │
└────┬─────────────────────────┬──────────────────┬──────────┘
     │                         │                  │
     │ /api/* → backend:8000   │ /* → user:8080   │ admin.* → admin:8081
     ↓                         ↓                  ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Backend Container│  │  User Frontend   │  │  Admin Frontend  │
│(FastAPI REST API)│  │  (Flask+Jinja2)  │  │  (Flask+Jinja2)  │
│                  │  │                  │  │                  │
│ - JWT Auth       │◄─│ - Register/Login │  │ - Admin Login    │
│ - Business Logic │  │ - Job browsing   │◄─│ - Dashboard      │
│ - Job Matching   │  │ - User profile   │  │ - Job mgmt       │
│ - Notifications  │  │ - Notifications  │  │ - User mgmt      │
│ Port: 8000       │  │ Port: 8080       │  │ Port: 8081       │
└────────┬─────────┘  └──────────────────┘  └──────────────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ↓              ↓              ↓              ↓
┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐
│ PostgreSQL  │  │   Redis     │  │hermes-worker │  │hermes-scheduler│
│  Container  │  │  Container  │  │ (tasks)      │  │ (cron/beat)    │
│ Port: 5432  │  │ Port: 6379  │  │              │  │                │
└─────────────┘  └─────────────┘  └──────────────┘  └────────────────┘
```

### Docker Networks

| Network           | Services                                                                         |
| ----------------- | -------------------------------------------------------------------------------- |
| `hermes_network`  | backend, hermes-worker, hermes-scheduler, postgresql, pgbouncer, redis, frontend, frontend-admin, mailpit |

Frontends **cannot** reach the database or Redis directly — all persistence goes
through the backend REST API via `BACKEND_API_URL`.

### Services

All services are defined in the single root **`docker-compose.yml`**.

| Service          | Image / Build      | Port     | Env file                            |
| ---------------- | ------------------ | -------- | ----------------------------------- |
| `postgresql`     | postgres:16-alpine | `5432`   | shared via compose env vars         |
| `redis`          | redis:7-alpine     | `6379`   | shared via compose env vars         |
| `pgbouncer`      | edoburu/pgbouncer  | `5432`   | shared via compose env vars         |
| `backend`        | local build        | `8000`   | `config/development/.env.backend`        |
| `hermes-worker`  | local build        | —        | `config/development/.env.backend`        |
| `hermes-scheduler`| local build        | —        | `config/development/.env.backend`        |
| `frontend`       | local build        | `8080`   | `config/development/.env.frontend`       |
| `frontend-admin` | local build        | `8081`   | `config/development/.env.frontend-admin` |
| `mailpit`        | axllent/mailpit    | `1025/8025` | — (dev only)                     |


### Health Checks

| Service        | Interval | Endpoint / Command                          |
| -------------- | -------- | ------------------------------------------- |
| PostgreSQL     | 10s      | `pg_isready -U hermes_user -d hermes_db`    |
| PgBouncer      | 10s      | `psql -h postgresql` connection check       |
| Redis          | 10s      | `redis-cli ping`                            |
| Backend        | 30s/15s  | `GET /api/v1/health` (port 8000)            |
| User Frontend  | 30s/15s  | `GET /health` (port 8080)                   |
| Admin Frontend | 30s/15s  | `GET /health` (port 8081)                   |
| Nginx          | 30s      | `GET /health`                               |

**Startup order:** PostgreSQL → Redis → Backend → Frontends → Nginx.
All containers use `restart: unless-stopped`.

### Frontend–Backend Communication

Both frontends are server-rendered Flask+Jinja2 apps enhanced with **HTMX** for
dynamic interactions (live search, infinite scroll, real-time notifications) and
**Alpine.js** for lightweight UI state (dropdowns, modals, toggles). They call
the backend REST API via an `api_client.py` utility using the `BACKEND_API_URL`
env var. No frontend ever connects to PostgreSQL or Redis directly.

#### HTMX Integration

HTMX (~14 KB) replaces the need for a JavaScript framework by making HTML
responses from the server drive UI updates:

| Feature | HTMX Approach | JS Required |
| ------- | ------------- | ----------- |
| Infinite scroll (job listings) | `hx-get="/jobs?page=2" hx-trigger="revealed" hx-swap="afterend"` | None |
| Live search | `hx-get="/jobs/search" hx-trigger="keyup changed delay:300ms"` | None |
| Mark notification read | `hx-put="/notifications/123/read" hx-swap="outerHTML"` | None |
| Delete confirmation modal | Alpine.js `x-show` + `x-on:click` | None |
| Notification badge count | `hx-get="/notifications/count" hx-trigger="every 30s"` | None |
| Deadline countdown on job cards | Jinja2 `{{ (job.application_end - today).days }} days left` + `hx-get` refresh | None |
| Application fee for user's category | Jinja2 reads `eligibility.fee` + user's `category` → shows "Your fee: ₹0" | None |
| Share job / admission / card | `navigator.share({title, url})` (Web Share API); clipboard fallback on desktop | Inline `onclick` |

The backend returns **HTML partials** (Jinja2 fragments) for HTMX requests
(detected via `HX-Request` header) and **full pages** for normal requests.
The FastAPI backend is not involved — HTMX requests go to the Flask frontend
which calls the API and renders the partial.

```
User Browser
    ↓ HTTP
Frontend (port 8080 or 8081)
    ├─ Receives page request
    ├─ Calls Backend via HTTP: GET http://<BACKEND_API_URL>/jobs?limit=20
    │    Headers: Authorization: Bearer <JWT>, X-Request-ID: <uuid>
    │    (Backend runs on port 8000 via Uvicorn)
    ├─ Receives JSON response
    ├─ Renders Jinja2 template with data
    └─ Returns HTML to browser
```

This means any frontend can be replaced (e.g. Flask → React, or a React Native
mobile app) with zero backend changes — only the HTTP client layer changes.

### PWA (Progressive Web App) — Implemented

The Flask user frontend is a full PWA. The following are already in `src/frontend/app/static/`:

- **`manifest.json`** — Add-to-home-screen on Android, app icon, splash screen
- **`sw.js`** — Service worker: caches job pages for offline access, serves `offline.html` fallback
- **`icon-192.png` / `icon-512.png`** — PWA icons

The PWA provides a native-like experience on Android and limited support on iOS Safari.

---

## Database Schema

See **[DATABASE.md](DATABASE.md)** for the complete schema — ERD, all 14 tables, column definitions, indexes, and CHECK constraints.

**4 Alembic migrations (`0001` → `0004`). Tables:**
`users`, `admin_users`, `user_profiles`, `user_devices`, `jobs`,
`notifications`, `notification_delivery_log`, `admin_logs`, `user_watches`,
`admit_cards`, `answer_keys`, `results`, `admissions`.

**Polymorphic document tables:** `admit_cards`, `answer_keys`, `results` each
link to either a `jobs` row (`job_id`) or an `admissions` row (`admission_id`)
via a DB-level `CHECK` constraint — exactly one FK per row, never both, never neither.

---

## API Endpoints

See **[API.md](API.md)** for the complete endpoint reference with request/response examples.

All endpoints versioned under `/api/v1/`. List responses: `{ "data": [...], "pagination": { "limit", "offset", "total", "has_more" } }`.

| Router | Prefix | Description |
|--------|--------|-------------|
| `auth.py` | `/api/v1/auth` | Firebase verify-token, logout, refresh; admin login/logout/refresh; email OTP registration |
| `users.py` | `/api/v1/users` | Profile CRUD, FCM tokens, phone, password management |
| `jobs.py` | `/api/v1/jobs` | Public listing (FTS + filters), recommended, detail by slug |
| `watches.py` | `/api/v1/jobs/{id}/watch`, `/api/v1/admissions/{id}/watch` | Watch/unwatch jobs and admissions; list watched |
| `notifications.py` | `/api/v1/notifications` | List, count, mark read, delete |
| `admin.py` | `/api/v1/admin` | Job CRUD + approve, user mgmt, stats, audit logs, admin-user creation |
| `content.py` | `/api/v1/admit-cards`, `/api/v1/answer-keys`, `/api/v1/results` | Public + admin CRUD for admit cards, answer keys, results |
| `admissions.py` | `/api/v1/admissions`, `/api/v1/admin/admissions` | Public admission listing + detail; admin admission CRUD + per-admission docs |
| `health.py` | `/api/v1/health` | Service health check |

---

## Error Response Format

All errors follow a consistent structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": [{"field": "email", "issue": "Email is invalid"}],
    "timestamp": "2026-03-03T10:30:00Z",
    "request_id": "req_abc123def456"
  }
}
```

### Error Codes

| HTTP | Code                          | Meaning                              |
| ---- | ----------------------------- | ------------------------------------ |
| 400  | `VALIDATION_EMAIL_EXISTS`     | Email already registered             |
| 400  | `VALIDATION_EMAIL_INVALID`    | Bad email format                     |
| 400  | `VALIDATION_PASSWORD_WEAK`    | Doesn't meet strength requirements (min 8 chars, 1 uppercase, 1 special)   |
| 400  | `VALIDATION_MISSING_FIELD`    | Required field missing               |
| 401  | `AUTH_INVALID_CREDENTIALS`    | Wrong email/password                 |
| 401  | `AUTH_TOKEN_EXPIRED`          | Access token expired                 |
| 401  | `AUTH_TOKEN_REVOKED`          | Token blocklisted (logout)           |
| 401  | `AUTH_EMAIL_NOT_VERIFIED`     | Email verification pending           |
| 403  | `FORBIDDEN_PERMISSION_DENIED` | Role lacks permission                |
| 403  | `FORBIDDEN_ADMIN_ONLY`        | Admin access required                |
| 404  | `NOT_FOUND_USER`              | User doesn't exist                   |
| 404  | `NOT_FOUND_JOB`               | Job doesn't exist                    |
| 404  | `NOT_FOUND_ADMISSION`         | Admission not found                  |
| 429  | `RATE_LIMIT_EXCEEDED`         | Too many requests                    |
| 500  | `SERVER_ERROR`                | Internal server error                |

Every request gets an `X-Request-ID` header (generated by Nginx if not sent by
client) that propagates through all services and into logs for tracing.

---

## Authentication & RBAC

### JWT Token Flow

- **Access token:** 15-minute expiry. Sent in `Authorization: Bearer <token>`.
- **Refresh token:** 7-day expiry. Used to obtain a new access token without re-login.
- **Blocklist:** On logout, the token's JTI is stored in Redis (`hermes:blocklist:{jti}`) until expiry. Key prefix is set via `REDIS_KEY_PREFIX` in config.

### Three Roles

| Role     | Description          | Login via              |
| -------- | -------------------- | ---------------------- |
| User     | Job seeker           | User Frontend (8080)   |
| Operator | Content reviewer     | Admin Frontend (8081)  |
| Admin    | Full system control  | Admin Frontend (8081)  |

### Permission Matrix

| Endpoint                           | User | Operator       | Admin |
| ---------------------------------- | ---- | -------------- | ----- |
| `GET /api/v1/jobs`                 | ✅   | ✅             | ✅    |
| `POST /api/v1/admin/jobs`          | ❌   | ✅             | ✅    |
| `PUT /api/v1/admin/jobs/:id`       | ❌   | ✅ (limited)   | ✅    |
| `DELETE /api/v1/admin/jobs/:id`    | ❌   | ❌             | ✅    |
| `GET /api/v1/users/profile`        | ✅   | ✅             | ✅    |
| `GET /api/v1/admin/users`          | ❌   | ✅             | ✅    |
| `PUT /api/v1/admin/users/:id/status` | ❌ | ❌             | ✅    |
| `GET /api/v1/admin/stats`          | ❌   | ✅             | ✅    |
| `GET /api/v1/admin/logs`           | ❌   | ❌             | ✅    |

**Operator restrictions on `PUT /api/v1/admin/jobs/:id`:** Can only modify these fields: `status`, `description`, `short_description`, `notification_date`, `application_start`, `application_end`, `exam_start`, `exam_end`, `result_date`. Cannot modify salary, vacancies, eligibility, or job_type — those require admin role. Operators also cannot delete jobs or access audit logs.

### Initial Admin Setup

No self-registration for admin accounts. Admin auth uses local bcrypt + JWT
(not Firebase). The first admin must be seeded directly in the database:

```bash
docker exec hermes_backend python -c "
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
import os, uuid
ctx = CryptContext(schemes=['bcrypt'])
engine = create_engine(os.environ['DATABASE_URL'].replace('+asyncpg', '+psycopg2'))
with engine.connect() as conn:
    conn.execute(text(\"INSERT INTO admin_users (id, email, password_hash, full_name, role, status, is_email_verified) VALUES (:id, :email, :pw, :name, 'admin', 'active', TRUE)\"),
        {'id': str(uuid.uuid4()), 'email': 'admin@hermes.com', 'pw': ctx.hash('Admin@123'), 'name': 'Admin'})
    conn.commit()
"
```

After the first admin exists, subsequent admin/operator accounts are created via the API:
```
POST /api/v1/admin/admin-users  (admin role only)
{ "email": "operator@hermes.com", "password": "Oper@123", "full_name": "Operator", "role": "operator" }  # pragma: allowlist secret
```

**Password Requirements (enforced for all users and admins):**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 special character (!@#$%^&*(),.?":{}|<>)

User status (suspend/activate) can be changed via `PUT /api/v1/admin/users/:id/status` (admin only).

### Firebase Test Credentials

These phone numbers are configured in **Firebase Console → Authentication → Phone numbers for testing** and bypass real SMS.

| Phone | OTP | Use |
|-------|-----|-----|
| +917777777777 | 123456 | Phone OTP login on `/login` page |

For email/password and Google login, create a test user via the Firebase Console or the `/login` page. Admin accounts are seeded via the DB (see README.md Quick Start).

---

## Background Tasks

### hermes-scheduler (Beat Schedule)

| Task                            | Schedule        | Description                            |
| ------------------------------- | --------------- | -------------------------------------- |
| `send-deadline-reminders`       | Daily 08:00 UTC | T-7, T-3, T-1 reminders → delegates to `smart_notify` |
| `purge-expired-notifications`   | Daily 01:00 UTC | Delete notifications past `expires_at` |
| `purge-expired-admin-logs`      | Daily 01:30 UTC | Delete admin logs past `expires_at`    |
| `purge-soft-deleted-jobs`       | Daily 02:00 UTC | Hard-delete inactive jobs older than 90 days |
| `close-expired-job-listings`    | Daily 02:30 UTC | Set `status='closed'` on jobs past `application_end` |
| `update-admission-statuses`     | Daily 02:35 UTC | Set `status='closed'` on admissions past `admission_date` |
| `generate-sitemap`              | Daily 04:00 UTC | Regenerate `/sitemap.xml` — active jobs, active/upcoming admissions, all 5 section pages |

### hermes-worker (Event-Triggered Tasks)

| Trigger                       | Task                           | Description                            |
| ----------------------------- | ------------------------------ | -------------------------------------- |
| Any notification needed       | `smart_notify`                 | Unified entry — instant or staggered delivery to all 5 channels |
| Job/admission approved or updated  | `notify_watchers_on_update`    | Notify all users watching that job/admission via `smart_notify(staggered)` |
| Staggered email delivery      | `deliver_delayed_email`        | Fires after `NOTIFY_EMAIL_DELAY` — sends the email |
| Staggered WhatsApp            | `deliver_delayed_whatsapp`     | Fires after `NOTIFY_WHATSAPP_DELAY` — sends the WhatsApp |
| Staggered Telegram            | `deliver_delayed_telegram`     | Fires after `NOTIFY_TELEGRAM_DELAY` — sends the Telegram message |

> **Note:** `send_new_job_notifications` (org-follow alerts) and `notify_priority_subscribers` (priority-tracker alerts) are registered Celery tasks but are currently **no-op stubs** (`pass` body). The infrastructure is in place but the matching/dispatch logic is not yet implemented.

---

## Job Ingestion Strategy

Jobs enter the system through two paths:

### Phase 1: Manual Entry (Current)

Admin creates a job via `POST /api/v1/admin/jobs`. The job is created with
`source='manual'` and `status='active'` (published immediately). This is the
only method available in v1.

### Phase 2: PDF Inline Extraction → Form Auto-Fill → Publish (Implemented)

Government job notifications are published as PDF documents. Instead of
manually typing every field, admin/operator can upload a PDF on creation pages
and AI instantly extracts structured data to auto-fill the form.

```
Admin/Operator on creation page (/jobs/new, /admit-cards/new, etc.)
    │
    ▼
┌────────────────────────────────────────┐
│ Upload PDF + Click "Extract Data"       │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│ POST /admin/jobs/extract-pdf             │
│ (Synchronous processing)                 │
│                                          │
│ 1. Parse PDF text (pdfplumber)           │
│ 2. Send text to AI (Anthropic Claude)    │
│ 3. AI returns JSON immediately:          │
│    - job_title, organization, department │
│    - eligibility, dates, vacancies       │
│    - salary, fees, source_url            │
│ 4. Return JSON to frontend               │
│    (no database write)                   │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│ Frontend JavaScript Auto-Fills Form      │
│                                          │
│ All form fields populated with:          │
│   ├─ Job title, org, department          │
│   ├─ Eligibility (age, education, etc.)  │
│   ├─ Dates (application, admission, result)   │
│   ├─ Vacancies, salary, fee              │
│   └─ Source URL                          │
│                                          │
│ Operator/Admin can:                      │
│   ├─ Review all auto-filled data         │
│   ├─ Edit any incorrect field            │
│   ├─ Add missing data                    │
│   └─ Submit → creates content in DB      │
│        (triggers user notifications)     │
└────────────────────────────────────────┘
```

### PDF Extraction Tech Stack

| Component | Technology | Purpose |
| --------- | ---------- | ------- |
| PDF parsing | pdfplumber | Extract raw text from notification PDF |
| AI extraction | Anthropic Claude API | Structured data extraction from text |
| Storage | Temporary files only | Immediate cleanup after extraction |
| Processing | Synchronous (no queue) | Instant response to frontend |

The AI extraction prompt maps PDF text to the `jobs` schema
fields. The creation form shows the extracted data inline, allowing
immediate review and editing before submission.

### API Endpoints for PDF Extraction

| Method | Endpoint                          | Description                    | Access   |
| ------ | --------------------------------- | ------------------------------ | -------- |
| POST   | `/api/v1/admin/jobs/extract-pdf`  | Extract PDF → return JSON      | Operator+ |

---

## SEO Strategy

Government job portals get 80%+ traffic from Google. SEO is critical for
discoverability.

### Dynamic Sitemap

A nightly `hermes-scheduler` task (`generate-sitemap`) regenerates `/sitemap.xml` with all
active job URLs:

```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://hermes.com/jobs/ssc-cgl-2026</loc>
    <lastmod>2026-03-15</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <!-- one <url> per active job -->
</urlset>
```

The sitemap is served as a static file by Nginx. Submit it to Google Search
Console after deployment.

### Meta Tags (per job page)

Each job detail page renders SEO-critical tags in the Jinja2 `<head>`:

```html
<title>{{ job.job_title }} — {{ job.organization }} | Hermes</title>
<meta name="description" content="{{ job.short_description }}">
<link rel="canonical" href="https://hermes.com/jobs/{{ job.slug }}">
<meta property="og:title" content="{{ job.job_title }}">
<meta property="og:description" content="{{ job.short_description }}">
<meta property="og:type" content="website">
```

### Structured Data (JobPosting Schema)

Google's [JobPosting](https://schema.org/JobPosting) structured data makes
jobs appear in Google's job search widget. Added as JSON-LD in each job page:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "{{ job.job_title }}",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "{{ job.organization }}"
  },
  "datePosted": "{{ job.published_at.isoformat() }}",
  "validThrough": "{{ job.application_end.isoformat() }}",
  "employmentType": "{{ job.employment_type | upper }}",
  "description": "{{ job.description }}"
}
</script>
```

This costs zero infrastructure — only Jinja2 template changes.

### Notification Channels

| Channel    | Technology          | Instant Mode (T+0) | Staggered Mode                          | Status      |
| ---------- | ------------------- | ------------------- | --------------------------------------- | ----------- |
| In-app     | PostgreSQL row      | T+0                 | T+0                                     | Implemented |
| Push (FCM) | Firebase FCM        | T+0                 | T+0 (tokens from `user_profiles.fcm_tokens`) | Implemented |
| Email      | OCI Email Delivery  | T+0                 | T+`NOTIFY_EMAIL_DELAY` (default 15min)  | Implemented |
| WhatsApp   | WhatsApp Cloud API  | T+0                 | T+`NOTIFY_WHATSAPP_DELAY` (default 1hr) | Placeholder (API token not yet set) |
| Telegram   | Telegram Bot API    | T+0                 | T+`NOTIFY_TELEGRAM_DELAY` (default 15min) | Implemented |

**Two delivery modes** via `smart_notify(delivery_mode="instant"|"staggered")`:
- **instant** — all 5 channels at T+0 (welcome message, urgent alerts)
- **staggered** — in-app + push at T+0, email + Telegram T+15min, WhatsApp T+1hr

Delays are configurable via env vars (`NOTIFY_EMAIL_DELAY`, `NOTIFY_WHATSAPP_DELAY`, `NOTIFY_TELEGRAM_DELAY`).
All channels always attempt delivery — staggered just adds a time gap to avoid bombarding simultaneously.
User preferences (`notification_preferences` JSONB) control per-channel opt-out.

**Telegram setup** (user-driven):
1. User messages the Hermes bot on Telegram (bot token set via `TELEGRAM_BOT_TOKEN`)
2. User retrieves their `chat_id` (e.g. via `@userinfobot`) and saves it:
   ```
   PUT /api/v1/users/me/notification-preferences
   { "telegram_chat_id": "123456789" }
   ```
3. Bot sends messages via `https://api.telegram.org/bot{token}/sendMessage` with Markdown formatting.
   Free — no per-message cost.

**WhatsApp** uses the WhatsApp Cloud API and remains a placeholder until
`WHATSAPP_API_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` are configured.

Both channels store their config in `notification_preferences`:

```json
{
  "email": true,
  "push": true,
  "telegram": { "enabled": true, "chat_id": "123456789" },
  "whatsapp": { "enabled": true, "phone": "+919876543210" }
}
```

The `sent_via` array on each notification row tracks which channels were used
(e.g., `['email', 'telegram']`).

### Organization Follow

Users can follow specific organizations (SSC, UPSC, Railway, etc.) to get
notified whenever that org posts *any* job — regardless of profile match.

Followed organizations are stored in `user_profiles.followed_organizations` (JSONB array, added by migration 0002).
Users manage this list by updating their profile via `PUT /api/v1/users/profile` — there are no dedicated follow/unfollow endpoints.

> **Note:** Dedicated org-follow endpoints (`/organizations/{name}/follow`) and new-job alert dispatch (`send_new_job_notifications`) are **not yet implemented**. The `followed_organizations` field is stored and displayed, but watcher notifications for new org jobs are a no-op stub.

### Share Button (Web Share API)

Every job card, admit card, answer key, result card, and admission card/detail
page includes a single **Share** button using the Web Share API.

```html
<!-- Single Share button — works on all pages and card types -->
<button
  data-title="{{ item.job_title | e }}"
  data-url="{{ request.url }}"
  onclick="(function(b){
    var u=b.dataset.url, t=b.dataset.title;
    if(navigator.share){
      navigator.share({title:t, url:u});
    } else {
      navigator.clipboard.writeText(u);
      var orig=b.textContent;
      b.textContent='\u2713 Copied';
      setTimeout(function(){b.textContent=orig}, 1800);
    }
  })(this)">
  Share
</button>
```

**Behaviour:**
- **Mobile** (Android/iOS): triggers native OS share sheet (`navigator.share`)
- **Desktop fallback**: copies URL to clipboard, button text changes to `✓ Copied` for 1.8 s
- URL and title passed via `data-*` attributes to avoid Jinja2-inside-JS escaping issues

**WhatsApp and Telegram share links have been removed.** The Web Share API is
more universal — it lets users choose their preferred app (WhatsApp, Telegram,
Copy, SMS, Email, etc.) from the OS-level dialog without the frontend
hard-coding specific platforms.

### Application Fee by Category

Government jobs charge different application fees by category. When a logged-in user views a job,
the frontend reads the fee columns from the job and the user's `category` from their profile,
then displays: **"Your application fee: ₹0"**.

Fees are stored as **top-level integer columns** on the `jobs` table (not inside JSONB):

| Column | Description |
|--------|-------------|
| `fee_general` | Fee for General/UR category (INR) |
| `fee_obc` | Fee for OBC-NCL category (INR) |
| `fee_sc_st` | Fee for SC/ST category (INR) |
| `fee_ews` | Fee for EWS category (INR) |
| `fee_female` | Fee for Female/PwBD candidates (INR) |

`0` = free. `null` = fee not specified (hidden in UI). This is pure Jinja2 template logic — no API changes needed.

---

## 5-Section Frontend Architecture

The user frontend is organized into 5 main sections, each with its own page, search, and visual identity:

| Section | URL Path | Content Type | Hero Color | Data Source |
|---------|----------|--------------|------------|-------------|
| Jobs | `/` | Government job vacancies | Navy → Blue | `jobs` |
| Admit Cards | `/admit-cards` | Exam admit cards | Sky Blue | `admit_cards` |
| Answer Keys | `/answer-keys` | Answer keys | Brown → Amber | `answer_keys` |
| Results | `/results` | Exam results | Dark Green → Green | `results` |
| Admissions | `/admissions` | Admissions | Dark Purple → Purple | `admissions` |

### Type-Aware Design System

Each section uses a gradient hero and consistent card design:

```html
<!-- Section page hero with gradient -->
<div class="section-hero bg-gradient-to-r from-{section-600} to-{section-400}">
  <h1>{Section Title}</h1>
  <!-- Search bar and filters -->
</div>

<!-- Cards with left accent border -->
<div class="card border-l-4 border-{section-500}">
  <!-- Content varies by section type -->
</div>
```

### Polymorphic Document Tables

The three document tables (`admit_cards`, `answer_keys`, `results`) are **polymorphic** — each row links to either:

- A job vacancy via `job_id` (traditional recruitment docs)
- An admission via `admission_id` (admission phase docs)

Database constraint ensures exactly one reference:
```sql
CONSTRAINT ck_doc_source CHECK (
  (job_id IS NOT NULL AND admission_id IS NULL) OR
  (job_id IS NULL AND admission_id IS NOT NULL)
)
```

### Unified Detail Pages

Both jobs and admissions share the same detail page template structure with type-aware heroes:

- **Jobs**: Navy/Blue gradient, employment-focused sections (salary, eligibility, selection process)
- **Admissions**: Purple gradient, education-focused sections (admission pattern, counselling, seats)

### HTMX Document Tabs

Detail pages include dynamic tabbed panels for per-phase documents:

```html
<!-- Admit Cards Tab -->
<div id="admit-cards-panel" hx-get="/jobs/{id}/admit-cards" hx-trigger="load">
  <!-- Loaded via HTMX -->
</div>
```

These work for both jobs and admissions using the same backend endpoints.

---

### Data Retention

Row expiry is handled via an `expires_at` column and nightly `hermes-scheduler` purge tasks.

| Data              | Retention | Mechanism                                  |
| ----------------- | --------- | ------------------------------------------ |
| Notifications     | 90 days   | `expires_at` + `hermes-scheduler` purge    |
| Admin logs        | 30 days   | `expires_at` + `hermes-scheduler` purge    |
| JWT blocklist     | Token TTL | Redis TTL (auto-expires with token) |
| Email OTP         | 5 minutes | Redis TTL (`setex` 300s)      |

> Redis is used only for the JWT blocklist and OTP storage — there is no application-level caching layer.

### PgBouncer (Connection Pooling)

PgBouncer runs as a sidecar container (~10 MB RAM) between the application
and PostgreSQL. The FastAPI backend and `hermes-worker` connect to PgBouncer
on port `5432` (container-internal) instead of PostgreSQL directly.

This matters because:
- PostgreSQL on ARM with limited memory shouldn't hold too many connections
- `hermes-worker` can spike connection counts during task bursts
- PgBouncer multiplexes many app connections over fewer PostgreSQL connections

Configuration: transaction pooling mode, `max_client_conn=100`,
`default_pool_size=20`. Set via environment variables in `docker-compose.yml` (not a mounted ini file).

### Structured JSON Logging

All backend services use `structlog` to emit structured JSON logs with
consistent fields:

```json
{
  "timestamp": "2026-03-15T10:30:00Z",
  "level": "info",
  "event": "job_created",
  "request_id": "req_abc123",
  "user_id": "uuid-...",
  "endpoint": "/api/v1/admin/jobs",
  "duration_ms": 45,
  "job_id": "uuid-..."
}
```

`structlog` is configured once in the FastAPI app startup and works with
Uvicorn, `hermes-worker`, and `hermes-scheduler`.

### Image Deployment

Images are built directly on the OCI ARM VM. The deployment workflow:

1. `git pull origin main` on the VM
2. `docker compose up -d --build` — rebuilds only changed services

This avoids the need for a container registry. The VM has 4 OCPU and 24 GB
RAM so builds are fast enough in production.

---

## Docker Environments

### Development

**Goal:** Fast iteration, debug-friendly, no TLS.

| Aspect   | Value                                                  |
| -------- | ------------------------------------------------------ |
| Config   | `config/development/`                                  |
| `DEBUG`  | `True`                                                 |
| Database | Local PostgreSQL container (Docker volume)              |
| Redis    | Local Redis container, no password (AOF enabled)        |
| Mail     | Mailpit (`MAIL_ENABLED=false` in dev env)             |
| Nginx    | Not required; access services directly on exposed ports|
| TLS      | None                                                   |
| Volumes  | Hot-reload mounts for code                             |

```bash
# All services are in the single root docker-compose.yml
# docker-compose.yml reads config/development/.env.* directly
docker compose up -d --build
```

### Staging

**Goal:** Production-like environment for integration testing.

| Aspect   | Value                                                   |
| -------- | ------------------------------------------------------- |
| Config   | `config/staging/`                                       |
| `DEBUG`  | `False`                                                 |
| Database | Managed PostgreSQL or containerised with password       |
| Redis    | Containerised with password                             |
| Mail     | Real SMTP relay with test accounts                      |
| Nginx    | Deployed; TLS via self-signed or Let's Encrypt staging  |
| TLS      | HTTPS on port 443                                       |
| Volumes  | No hot-reload — rebuild images for code changes         |

### Production (OCI Always Free Tier)

**Goal:** Hardened, monitored deployment on a single OCI ARM instance.

**Infrastructure:** OCI Ampere A1 VM (4 OCPU, 24 GB RAM, 200 GB storage) — Always Free.
All containers run via Docker Compose on this single VM.

| Aspect    | Value                                                           |
| --------- | --------------------------------------------------------------- |
| Config    | `config/production/`                                            |
| `DEBUG`   | `False` (never override)                                        |
| VM        | OCI ARM Ampere A1, 4 OCPU, 24 GB RAM, 200 GB storage (Always Free)             |
| Database  | PostgreSQL 16 in Docker (password-protected, Docker volume)     |
| Redis     | Redis 7 in Docker (password-protected, AOF persistence)         |
| Mail      | OCI Email Delivery (3,000/day free, SPF/DKIM built-in)          |
| TLS       | Nginx + Let's Encrypt (Certbot) — free SSL directly on VM       |
| Nginx     | SSL termination, rate limiting, security headers                |
| Uvicorn   | Workers via `WEB_CONCURRENCY` (default: CPU × 2 + 1)           |
| Networking| OCI VCN — VM in private subnet; ports 80/443/22 via security list|
| Images    | Built directly on VM via `git pull` + `docker compose up --build`|
| CDN       | Cloudflare Free Tier — CDN cache, DDoS protection, analytics   |
| Secrets   | `.env` files (gitignored, managed manually on VM)               |
| Backups   | `pg_dump` daily cron (host cron job, stored on VM disk)          |

**Resource allocation (~3 GB used of 24 GB):**

| Container        | RAM      |
| ---------------- | -------- |
| PostgreSQL 16    | ~1 GB    |
| Redis 7          | ~256 MB  |
| PgBouncer        | ~10 MB   |
| Backend (FastAPI) | ~512 MB  |
| hermes-worker    | ~256 MB  |
| hermes-scheduler | ~128 MB  |
| User Frontend    | ~256 MB  |
| Admin Frontend   | ~256 MB  |
| Nginx            | ~64 MB   |

**Production checklist:**

- [ ] `SECRET_KEY` — minimum 32 random bytes, set in `.env` (gitignored)
- [ ] `POSTGRES_PASSWORD` / `DB_PASSWORD` — strong, unique
- [ ] `REDIS_PASSWORD` — strong, unique
- [ ] `JWT_SECRET_KEY` — separate from `SECRET_KEY`
- [ ] `MAIL_PASSWORD` — OCI Email Delivery SMTP credential
- [ ] Certbot installed + Let's Encrypt certificate obtained for domain
- [ ] Nginx SSL config updated with cert paths + HTTP → HTTPS redirect
- [ ] `CORS_ORIGINS` restricted to production domain(s)
- [ ] VCN security list: ports 80/443 open to `0.0.0.0/0`; SSH (22) from admin IP only
- [ ] Cloudflare DNS configured — domain proxied through Cloudflare
- [ ] Redis AOF persistence enabled (`appendonly yes` in redis.conf)

---

## Security Design

All items below are implemented.

- **User authentication:** Firebase Auth (Email/Password with OTP verification, Google OAuth, Phone OTP) — Email registration requires OTP verification before account creation, backend verifies Firebase ID tokens via `firebase-admin` SDK
- **Admin authentication:** Local bcrypt (salted) password hashing — admin accounts do not use Firebase
- **Password requirements:** All passwords (user & admin) must have minimum 8 characters, 1 uppercase letter, 1 special character
- **Internal JWT with Redis blocklist:** After Firebase verification, backend issues its own JWT — access tokens expire in 15 min, refresh in 7 days
- **Rate limiting:** Nginx (100 req/min per IP, 5/min on `/api/v1/auth/`) + SlowAPI behind proxy using `X-Real-IP` header (1000 req/min per real client, 10/min on verify-token)
- **CORS:** Only whitelisted origins in `CORS_ORIGINS`
- **HTTPS/TLS:** Nginx handles SSL termination via Let's Encrypt (Certbot) — free, auto-renewing certificates directly on the VM
- **Network isolation:** OCI VCN security list — only ports 80/443/22 open; DB and Redis never exposed outside Docker networks
- **Security headers:** X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Content-Security-Policy, Strict-Transport-Security, Referrer-Policy (via Nginx behind LB)
- **Input validation:** Pydantic models on all endpoints (FastAPI native)
- **CSRF protection:** Session-based tokens (admin login form uses `secrets.token_hex`, validated before processing). User frontend POST forms include a session-bound CSRF token generated by `_get_csrf_token()` and validated in `before_request`; the Firebase callback is exempt (authenticated by Firebase ID token).
- **Secrets:** `.env` files in `.gitignore`; never committed to version control
- **Redis persistence:** AOF (append-only file) enabled — prevents JWT blocklist loss on Redis restart. Without AOF, a Redis restart would make previously logged-out tokens valid again.
- **Audit logging — admin actions (DB):** All state-changing admin operations write a row to `admin_logs` (30-day expiry, queryable from admin frontend `/admin/logs`):

  | Event | Action stored |
  |-------|---------------|
  | Admin login | `admin_login` — IP + user-agent |
  | Admin logout | `admin_logout` — IP + user-agent |
  | Admin token refresh | `admin_token_refresh` — IP + user-agent |
  | Create job | `create_job` — job title |
  | Update job | `update_job` — full before/after diff per field |
  | Approve job | `approve_job` — job title |
  | Delete job (soft) | `delete_job` — job title |
  | Extract PDF | `extract_pdf` — filename |
  | Suspend/activate user | `update_user_status` — old → new status |
  | Change admin role | `update_user_role` — old → new role |

- **Audit logging — user events (structlog → stdout):** User actions emit JSON-structured log lines to Docker stdout, collected by the container runtime and available via `docker logs` or any log aggregator configured on the VM.

  | Event | Key fields logged |
  |-------|-------------------|
  | Register | `user_id`, IP |
  | Login success / failure | `user_id`, IP |
  | Logout | `user_id` |
  | Token refresh | `user_id` |
  | Email verified | `user_id` |
  | Password reset requested | `user_id` |
  | Password reset completed | `user_id` |
  | Profile updated | `user_id`, changed fields |
  | Phone updated | `user_id` |
  | Org followed / unfollowed | `user_id`, org name |
  | FCM token registered / removed | `user_id`, device name |
  | Notification preferences updated | `user_id`, channels changed |
  | Notification marked read | `user_id`, `notification_id` |
  | All notifications marked read | `user_id`, count |
  | Notification deleted | `user_id`, `notification_id` |

---

## Environment Variables

Each service has its own `.env` file stored in `config/<environment>/`.

- **Templates (committed):** `config/staging/` and `config/production/` — placeholder values, safe to commit.
- **Dev secrets (gitignored):** `config/development/` — never committed.
- **Reference examples:** `src/backend/.env.example`, `src/frontend/.env.example`, `src/frontend-admin/.env.example` — annotated, safe to commit.

```
config/
├── development/   .env.backend  .env.frontend  .env.frontend-admin  ← gitignored
├── staging/       .env.backend  .env.frontend  .env.frontend-admin  ← committed (placeholders)
└── production/    .env.backend  .env.frontend  .env.frontend-admin  ← committed (placeholders)
```

The actual variable definitions live in the `config/` files. Use the annotated example files as a reference:

- `src/backend/.env.example` — all backend variables with descriptions
- `src/frontend/.env.example` — all frontend variables
- `src/frontend-admin/.env.example` — all admin frontend variables

In production, `BACKEND_API_URL` points to the internal Docker hostname (`http://backend:8000/api/v1`). Each frontend must have a **different** `SECRET_KEY`.

---

## Deployment

### Target: OCI Always Free ARM Instance

The entire stack runs on a single OCI Ampere A1 VM (4 OCPU, 24 GB RAM)
using Docker Compose. Nginx handles SSL termination directly via Let's Encrypt.

```
Internet
    │
    ▼
┌──────────────────────────────────┐
│  Cloudflare (Free CDN + DDoS)    │
│  - CDN cache for static assets   │
│  - DDoS protection               │
│  - Analytics                     │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  OCI ARM VM (4 OCPU, 24 GB RAM, 200 GB storage) — Always Free│
│                                               │
│  Docker Compose                               │
│  ┌─────────────────────────────────────────┐  │
│  │ Nginx (SSL/TLS via Let's Encrypt,       │  │
│  │        rate limiting, security headers) │  │
│  │    ├── backend:8000                     │  │
│  │    ├── frontend:8080                    │  │
│  │    └── frontend-admin:8081              │  │
│  ├─────────────────────────────────────────┤  │
│  │ PostgreSQL 16  │  Redis 7               │  │
│  │ (Docker volume) │ (password protected)  │  │
│  ├─────────────────────────────────────────┤  │
│  │ hermes-worker + hermes-scheduler        │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│  Cron: pg_dump daily                          │
└───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────┐
│  OCI Email Delivery      │  ← 3,000/day free
│  (SMTP for notifications)│
└──────────────────────────┘
```

### OCI Free Services Used

| Service | Purpose | Free Tier Limit |
| ------- | ------- | --------------- |
| ARM VM (Ampere A1) | Runs all Docker containers | 4 OCPU, 24 GB RAM, 200 GB storage |
| Email Delivery | Job notification emails (SPF/DKIM) | 3,000 emails/day |
| VCN + Networking | Subnet isolation + security lists | Unlimited |

**External free services (not OCI):**

| Service | Purpose | Free Tier Limit |
| ------- | ------- | --------------- |
| Cloudflare | CDN, DDoS protection, analytics | Unlimited (free plan) |
| Let's Encrypt (Certbot) | Free SSL/TLS certificates for Nginx | Unlimited |

Cloudflare sits in front of the VM. Its CDN cache handles static asset traffic
(CSS, JS, images) reducing bandwidth load on the VM. Nginx handles SSL
termination directly using Let's Encrypt certificates (auto-renewed by Certbot).

| Resource | Ingress Rules |
| -------- | ------------- |
| VM port 80 | `0.0.0.0/0` (Cloudflare → HTTP, for Certbot challenge + redirect) |
| VM port 443 | `0.0.0.0/0` (Cloudflare → HTTPS) |
| VM port 22 | Admin IP only |

PostgreSQL (5432) and Redis (6379) are accessible only within Docker
networks on the VM — never exposed to any OCI subnet or the internet.

### Local Development

No OCI services needed for local development. Run everything in Docker:

```bash
# docker-compose.yml reads config/development/.env.* directly — no copying needed

# All services in single root docker-compose.yml
docker compose up -d --build
```

### Production Deployment

```bash
# SSH into OCI ARM VM
ssh -i <key> ubuntu@<vm-public-ip>

# Clone and configure
git clone <repo-url> hermes && cd hermes
# Fill in all <placeholder> values in config/production/.env.*

# Deploy all services
docker compose up -d --build
```

### Backup and Restore

**Daily database backup** (host cron via `pg_dump`):

```bash
# crontab -e
0 2 * * * docker exec hermes_postgresql pg_dump -U hermes_user hermes_db > /home/ubuntu/hermes/backups/hermes_db_$(date +%Y%m%d_%H%M%S).dump
```

**Restore:**

```bash
docker exec -i hermes_postgresql psql -U hermes_user hermes_db < <backup_file>
```

---

## Related Documentation

- [Workflow Diagrams](DIAGRAMS.md) — ASCII diagrams for user registration, job creation, watch flow, deadline reminders, admin dashboard, RBAC enforcement, and JWT token flows.
