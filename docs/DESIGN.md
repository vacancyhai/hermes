# Hermes — System Design Document

> **Status:** Phases 1–7.5 complete. Auth, job CRUD, full-text search,
> user profiles, job matching, org follow, application tracking, notifications
> (email, push, in-app), admin panel, SEO, PDF AI extraction, PWA, test suite
> (406 tests — 91/100/97% coverage), and security audit — all implemented. Phase 8 (OCI deployment) next.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Error Response Format](#error-response-format)
5. [Authentication & RBAC](#authentication--rbac)
6. [Background Tasks](#background-tasks)
7. [Job Ingestion Strategy](#job-ingestion-strategy)
8. [SEO Strategy](#seo-strategy)
9. [Docker Environments](#docker-environments)
10. [Security Design](#security-design)
11. [Environment Variables](#environment-variables)
12. [Deployment](#deployment)

---

## System Architecture

### Three-Service Architecture

Backend, User Frontend, and Admin Frontend are independent services with
separate Docker Compose files and Docker networks. They communicate via HTTP
REST API.

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
         ├──────────────┬──────────────┬─────────────┐
         ↓              ↓              ↓             ↓
┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐
│ PostgreSQL  │  │   Redis     │  │ Celery   │  │ Celery   │
│  Container  │  │  Container  │  │ Worker   │  │  Beat    │
│ Port: 5432  │  │ Port: 6379  │  │          │  │          │
└─────────────┘  └─────────────┘  └──────────┘  └──────────┘
```

### Docker Networks

| Network                       | Services                                              |
| ----------------------------- | ----------------------------------------------------- |
| `src_backend_network`         | backend, celery_worker, celery_beat, postgresql, pgbouncer, redis, nginx |
| `src_frontend_network`        | frontend, nginx                                       |
| `src_frontend_admin_network`  | frontend-admin, nginx                                 |

Frontends **cannot** reach the database or Redis directly — all persistence goes
through the backend REST API via `BACKEND_API_URL`.

### Services

| Service          | Image / Build      | Port   | Compose file                            |
| ---------------- | ------------------ | ------ | --------------------------------------- |
| `postgresql`     | postgres:16-alpine | `5432` | `src/backend/docker-compose.yml`        |
| `redis`          | redis:7-alpine     | `6379` | `src/backend/docker-compose.yml`        |
| `pgbouncer`      | edoburu/pgbouncer  | `6432` | `src/backend/docker-compose.yml`        |
| `backend`        | local build        | `8000` | `src/backend/docker-compose.yml`        |
| `celery_worker`  | local build        | —      | `src/backend/docker-compose.yml`        |
| `celery_beat`    | local build        | —      | `src/backend/docker-compose.yml`        |
| `frontend`       | local build        | `8080` | `src/frontend/docker-compose.yml`       |
| `frontend-admin` | local build        | `8081` | `src/frontend-admin/docker-compose.yml` |
| `nginx`          | nginx:alpine       | `80/443` | `src/nginx/docker-compose.yml`        |

### Health Checks

| Service        | Interval | Endpoint / Command                          |
| -------------- | -------- | ------------------------------------------- |
| PostgreSQL     | 10s      | `pg_isready`                                |
| PgBouncer      | 10s      | `PGPASSWORD=$DB_PASS psql -h pgbouncer -p 6432 -U hermes_user -c 'SELECT 1'` |
| Redis          | 10s      | `redis-cli ping`                            |
| Backend        | 30s      | `GET /api/v1/health` (port 8000)            |
| User Frontend  | 30s      | `GET /health`                               |
| Admin Frontend | 30s      | `GET /health`                               |
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
| Share job via WhatsApp/Telegram | `<a href="whatsapp://send?text=...">` / `<a href="https://t.me/share/url?url=...">` | None |

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

### Future: Mobile App (React Native)

The FastAPI backend already serves as a headless REST API. A mobile app would be
an additional client calling the same `/api/v1/*` endpoints:

```
React Native App (Android + iOS)
  ├── Calls same /api/v1/* endpoints via fetch/axios
  ├── JWT auth (same flow — login, refresh, logout)
  ├── Firebase FCM push (already designed, same token registration)
  └── Offline job caching (AsyncStorage / MMKV)
```

**No backend changes required.** The mobile app is just another HTTP client,
exactly like the Flask frontends. React Native is chosen over Flutter for:
- Native JSON consumption (JavaScript)
- Larger developer ecosystem in India
- Expo for simplified builds without Android Studio/Xcode
- Future option: share components with a Next.js web rewrite (Phase 3)

### Future: PWA (Progressive Web App)

Before the React Native app, the Flask frontend can be enhanced as a PWA for a
native-like mobile experience with minimal effort:

- **`manifest.json`** — Add-to-home-screen on Android, app icon, splash screen
- **Service worker** — Cache previously viewed job pages for offline access
- **Web Push API** — Push notifications in the browser (no FCM needed for web)
- **Works on iOS Safari** — Limited but functional (no push, but offline + home screen)

This requires 2–3 files added to the frontend static assets. It does not replace
React Native for a full mobile app, but bridges the gap while phases 1–7 are
being built.

---

## Database Schema

### Core Tables (v1)

Six tables for the initial release.

#### 1. `users` (regular job seekers)

```sql
CREATE TABLE users (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email               VARCHAR(255) UNIQUE NOT NULL,
  password_hash       VARCHAR(255) NOT NULL,
  full_name           VARCHAR(255) NOT NULL,
  phone               VARCHAR(20),
  status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','suspended','deleted')),
  is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
  is_email_verified   BOOLEAN NOT NULL DEFAULT FALSE,
  last_login          TIMESTAMP WITH TIME ZONE,
  created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email  ON users (email);
CREATE INDEX idx_users_status ON users (status);
```

> **Note:** The original design had a `role` column on `users`. Migration 0002
> split admin/operator accounts into a separate `admin_users` table to enforce
> distinct login flows and prevent privilege escalation.

#### 1b. `admin_users` (admins and operators)

```sql
CREATE TABLE admin_users (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email               VARCHAR(255) UNIQUE NOT NULL,
  password_hash       VARCHAR(255) NOT NULL,
  full_name           VARCHAR(255) NOT NULL,
  phone               VARCHAR(20),
  role                VARCHAR(20) NOT NULL DEFAULT 'operator'
                        CHECK (role IN ('admin','operator')),
  department          VARCHAR(255),
  permissions         JSONB NOT NULL DEFAULT '{}',
  status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','suspended','deleted')),
  is_email_verified   BOOLEAN NOT NULL DEFAULT FALSE,
  last_login          TIMESTAMP WITH TIME ZONE,
  created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_admin_users_email ON admin_users (email);
CREATE INDEX idx_admin_users_role  ON admin_users (role);
```

#### 2. `user_profiles`

```sql
CREATE TABLE user_profiles (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date_of_birth             DATE,
  gender                    VARCHAR(20) CHECK (gender IN ('Male','Female','Other')),
  category                  VARCHAR(20) CHECK (category IN ('General','OBC','SC','ST','EWS','EBC')),
  is_pwd                    BOOLEAN NOT NULL DEFAULT FALSE,
  is_ex_serviceman          BOOLEAN NOT NULL DEFAULT FALSE,
  state                     VARCHAR(100),
  city                      VARCHAR(100),
  pincode                   VARCHAR(10),
  highest_qualification     VARCHAR(50),
  education                 JSONB NOT NULL DEFAULT '{}',
  notification_preferences  JSONB NOT NULL DEFAULT '{}',
  preferred_states          JSONB NOT NULL DEFAULT '[]',
  preferred_categories      JSONB NOT NULL DEFAULT '[]',
  followed_organizations    JSONB NOT NULL DEFAULT '[]',
  fcm_tokens                JSONB NOT NULL DEFAULT '[]',
  updated_at                TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_user_profiles_user_id  ON user_profiles (user_id);
CREATE INDEX idx_user_profiles_education       ON user_profiles USING GIN (education);
CREATE INDEX idx_user_profiles_notif_prefs     ON user_profiles USING GIN (notification_preferences);
```

#### 3. `job_vacancies`

```sql
CREATE TABLE job_vacancies (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_title             VARCHAR(500) NOT NULL,
  slug                  VARCHAR(500) UNIQUE NOT NULL,
  organization          VARCHAR(255) NOT NULL,
  department            VARCHAR(255),
  job_type              VARCHAR(50) NOT NULL DEFAULT 'latest_job'
                          CHECK (job_type IN ('latest_job','result','admit_card','answer_key','admission','yojana')),
  employment_type       VARCHAR(50) DEFAULT 'permanent'
                          CHECK (employment_type IN ('permanent','temporary','contract','apprentice')),
  qualification_level   VARCHAR(50),
  total_vacancies       INTEGER,
  vacancy_breakdown     JSONB NOT NULL DEFAULT '{}',
  description           TEXT,
  short_description     TEXT,
  eligibility           JSONB NOT NULL DEFAULT '{}',
  application_details   JSONB NOT NULL DEFAULT '{}',
  documents             JSONB NOT NULL DEFAULT '[]',
  source_url            TEXT,
  notification_date     DATE,
  application_start     DATE,
  application_end       DATE,
  exam_start            DATE,
  exam_end              DATE,
  result_date           DATE,
  exam_details          JSONB NOT NULL DEFAULT '{}',
  salary_initial        INTEGER,
  salary_max            INTEGER,
  salary                JSONB NOT NULL DEFAULT '{}',
  selection_process     JSONB NOT NULL DEFAULT '[]',
  fee_general           INTEGER,
  fee_obc               INTEGER,
  fee_sc_st             INTEGER,
  fee_ews               INTEGER,
  fee_female            INTEGER,
  status                VARCHAR(20) NOT NULL DEFAULT 'active'
                          CHECK (status IN ('draft','active','expired','cancelled','upcoming')),
  is_featured           BOOLEAN NOT NULL DEFAULT FALSE,
  is_urgent             BOOLEAN NOT NULL DEFAULT FALSE,
  views                 INTEGER NOT NULL DEFAULT 0,
  applications_count    INTEGER NOT NULL DEFAULT 0,
  created_by            UUID REFERENCES admin_users(id),
  source                VARCHAR(20) NOT NULL DEFAULT 'manual'
                          CHECK (source IN ('manual','pdf_upload')),
  source_pdf_path       TEXT,
  published_at          TIMESTAMP WITH TIME ZONE,
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_organization    ON job_vacancies (organization);
CREATE INDEX idx_jobs_status_created  ON job_vacancies (status, created_at DESC);
CREATE INDEX idx_jobs_qual_level      ON job_vacancies (qualification_level);
CREATE INDEX idx_jobs_application_end ON job_vacancies (application_end);
CREATE INDEX idx_jobs_org_status      ON job_vacancies (organization, status, created_at DESC);
CREATE INDEX idx_jobs_eligibility_gin ON job_vacancies USING GIN (eligibility);
```

**Full-text search** — a generated `tsvector` column enables ranked search via
PostgreSQL's built-in full-text search (no Elasticsearch needed):

```sql
ALTER TABLE job_vacancies ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(job_title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(organization, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'C')
  ) STORED;

CREATE INDEX idx_jobs_search ON job_vacancies USING GIN (search_vector);
```

The `?q=` filter on `GET /api/v1/jobs` uses `plainto_tsquery` against
`search_vector` and ranks results with `ts_rank`. This gives weighted,
typo-tolerant search with zero additional infrastructure.

**Documents** — the `documents` JSONB column stores links to official PDFs
(notification, syllabus, admit card, answer key). These are URLs to external
government sites, not files stored by Hermes:

```json
[
  {"type": "notification", "title": "Official PDF", "url": "https://ssc.nic.in/..."},
  {"type": "syllabus", "title": "Exam Syllabus", "url": "https://ssc.nic.in/..."}
]
```

Valid `type` values: `notification`, `syllabus`, `admit_card`, `answer_key`, `result`.

#### 4. `user_job_applications`

```sql
CREATE TABLE user_job_applications (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  job_id                  UUID NOT NULL REFERENCES job_vacancies(id) ON DELETE CASCADE,
  application_number      VARCHAR(100),
  is_priority             BOOLEAN NOT NULL DEFAULT FALSE,
  applied_on              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  status                  VARCHAR(50) NOT NULL DEFAULT 'applied'
                            CHECK (status IN (
                              'applied','admit_card_released','exam_completed',
                              'result_pending','selected','rejected','waiting_list'
                            )),
  notes                   TEXT,
  reminders               JSONB NOT NULL DEFAULT '[]',
  result_info             JSONB NOT NULL DEFAULT '{}',
  updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, job_id)
);

CREATE INDEX idx_applications_user_job     ON user_job_applications (user_id, job_id);
CREATE INDEX idx_applications_user_applied ON user_job_applications (user_id, applied_on DESC);
```

#### 5. `notifications`

```sql
CREATE TABLE notifications (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type VARCHAR(50)
                CHECK (entity_type IN ('job','result','admit_card','answer_key','admission','yojana')),
  entity_id   UUID,
  type        VARCHAR(60) NOT NULL,
  title       VARCHAR(500) NOT NULL,
  message     TEXT NOT NULL,
  action_url  TEXT,
  is_read     BOOLEAN NOT NULL DEFAULT FALSE,
  sent_via    TEXT[],
  priority    VARCHAR(10) NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low','medium','high')),
  created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  read_at     TIMESTAMP WITH TIME ZONE,
  expires_at  TIMESTAMP WITH TIME ZONE NOT NULL
                DEFAULT (NOW() + INTERVAL '90 days')
);

CREATE INDEX idx_notifications_user_read    ON notifications (user_id, is_read);
CREATE INDEX idx_notifications_user_created ON notifications (user_id, created_at DESC);
CREATE INDEX idx_notifications_expires      ON notifications (expires_at);
```

#### 6. `admin_logs`

```sql
CREATE TABLE admin_logs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id      UUID NOT NULL REFERENCES admin_users(id),
  action        VARCHAR(100) NOT NULL,
  resource_type VARCHAR(100),
  resource_id   UUID,
  details       TEXT,
  changes       JSONB NOT NULL DEFAULT '{}',
  ip_address    INET,
  user_agent    TEXT,
  timestamp     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  expires_at    TIMESTAMP WITH TIME ZONE NOT NULL
                  DEFAULT (NOW() + INTERVAL '30 days')
);

CREATE INDEX idx_admin_logs_admin_ts ON admin_logs (admin_id, timestamp DESC);
CREATE INDEX idx_admin_logs_expires  ON admin_logs (expires_at);
```

#### 7. `user_devices` (device registry with fingerprint de-duplication)

```sql
CREATE TABLE user_devices (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  fcm_token           VARCHAR(500),
  device_name         VARCHAR(255) NOT NULL DEFAULT 'Unknown',
  device_type         VARCHAR(20) NOT NULL DEFAULT 'web'
                        CHECK (device_type IN ('web', 'pwa', 'android', 'ios')),
  device_fingerprint  VARCHAR(255),
  is_active           BOOLEAN NOT NULL DEFAULT TRUE,
  last_active_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_devices_user_id ON user_devices (user_id);
CREATE UNIQUE INDEX idx_devices_fcm_token ON user_devices (fcm_token) WHERE fcm_token IS NOT NULL;
CREATE INDEX idx_devices_fingerprint ON user_devices (user_id, device_fingerprint);
```

`device_fingerprint` enables push de-duplication: if a user is logged into
Chrome web + Chrome PWA on the same laptop, both share the same fingerprint.
Push is sent once per physical device, not per login.

#### 8. `notification_delivery_log` (per-channel delivery tracking)

```sql
CREATE TABLE notification_delivery_log (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  notification_id   UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
  user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  channel           VARCHAR(20) NOT NULL
                      CHECK (channel IN ('in_app', 'push', 'email', 'whatsapp')),
  status            VARCHAR(20) NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'skipped')),
  device_id         UUID REFERENCES user_devices(id) ON DELETE SET NULL,
  error_message     TEXT,
  attempted_at      TIMESTAMP WITH TIME ZONE,
  delivered_at      TIMESTAMP WITH TIME ZONE,
  created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_delivery_notification ON notification_delivery_log (notification_id);
CREATE INDEX idx_delivery_user_channel ON notification_delivery_log (user_id, channel);
```

### Future Expansion Tables

These tables support features beyond the core job-notification system. They
should be added only when those features are actively being built.

| Table              | Purpose                                          |
| ------------------ | ------------------------------------------------ |
| `results`          | Exam result records linked to `job_vacancies`    |
| `admit_cards`      | Admit card releases linked to `job_vacancies`    |
| `answer_keys`      | Answer key releases linked to `job_vacancies`    |
| `admissions`       | University/college admission listings            |
| `yojanas`          | Government scheme listings                       |
| `board_results`    | Board exam results (CBSE, state boards)          |
| `categories`       | Organization/department taxonomy with hierarchy  |
| `page_views`       | Per-entity view analytics                        |
| `search_logs`      | Search query analytics and click tracking        |
| `user_org_follows` | Many-to-many: users following organizations      |
| `role_permissions` | Dynamic RBAC permission overrides (if needed)    |
| `access_audit_logs`| Audit trail for permission changes               |

---

## API Endpoints

All endpoints are versioned under `/api/v1/`.

### Authentication

| Method | Endpoint                         | Description              | Access |
| ------ | -------------------------------- | ------------------------ | ------ |
| POST   | `/api/v1/auth/register`          | User registration        | Public |
| POST   | `/api/v1/auth/login`             | User login               | Public |
| POST   | `/api/v1/auth/logout`            | Logout (blocklist token) | Auth   |
| POST   | `/api/v1/auth/refresh`           | Refresh JWT token pair   | Auth   |
| POST   | `/api/v1/auth/forgot-password`   | Request password reset   | Public |
| POST   | `/api/v1/auth/reset-password`    | Submit new password      | Public |
| GET    | `/api/v1/auth/verify-email/:token` | Email verification     | Public |
| GET    | `/api/v1/auth/csrf-token`        | Get CSRF token           | Public |

### User Profile

| Method | Endpoint                    | Description                   | Access |
| ------ | --------------------------- | ----------------------------- | ------ |
| GET    | `/api/v1/users/profile`     | Get own profile               | User   |
| PUT    | `/api/v1/users/profile`     | Update own profile            | User   |
| PUT    | `/api/v1/users/profile/phone` | Update phone number         | User   |

### Job Vacancies

| Method | Endpoint                           | Description              | Access         |
| ------ | ---------------------------------- | ------------------------ | -------------- |
| GET    | `/api/v1/jobs`                     | List jobs (filterable, paginated) | Public  |
| GET    | `/api/v1/jobs/:slug`               | Job detail               | Public         |
| GET    | `/api/v1/jobs/recommended`         | Personalized job matches | User           |
| POST   | `/api/v1/jobs`                     | Create job               | Admin          |
| PUT    | `/api/v1/jobs/:id`                 | Update job               | Admin/Operator |
| DELETE | `/api/v1/jobs/:id`                 | Soft delete job          | Admin          |

### Applications

| Method | Endpoint                         | Description            | Access |
| ------ | -------------------------------- | ---------------------- | ------ |
| GET    | `/api/v1/applications`           | List own applications  | User   |
| POST   | `/api/v1/applications`           | Track a job            | User   |
| DELETE | `/api/v1/applications/:id`       | Remove from tracker    | User   |

### Notifications

| Method | Endpoint                            | Description          | Access |
| ------ | ----------------------------------- | -------------------- | ------ |
| GET    | `/api/v1/notifications`             | List notifications   | User   |
| GET    | `/api/v1/notifications/count`       | Unread count         | User   |
| PUT    | `/api/v1/notifications/:id/read`    | Mark as read         | User   |
| PUT    | `/api/v1/notifications/read-all`    | Mark all as read     | User   |
| DELETE | `/api/v1/notifications/:id`         | Delete notification  | User   |

### Admin

| Method | Endpoint                            | Description             | Access |
| ------ | ----------------------------------- | ----------------------- | ------ |
| GET    | `/api/v1/admin/stats`               | Dashboard stats         | Admin  |
| GET    | `/api/v1/admin/analytics`           | Platform analytics      | Admin  |
| GET    | `/api/v1/admin/jobs`                | List all jobs           | Admin  |
| POST   | `/api/v1/admin/jobs`                | Create job              | Admin  |
| PUT    | `/api/v1/admin/jobs/:id`            | Update job              | Admin  |
| DELETE | `/api/v1/admin/jobs/:id`            | Delete job              | Admin  |
| GET    | `/api/v1/admin/users`               | List all users          | Admin  |
| GET    | `/api/v1/admin/users/:id`           | User details            | Admin  |
| PUT    | `/api/v1/admin/users/:id/status`    | Suspend/activate user   | Admin  |
| PUT    | `/api/v1/admin/users/:id/role`      | Change user role        | Admin  |
| GET    | `/api/v1/admin/logs`                | Admin activity logs     | Admin  |

### Health

| Method | Endpoint             | Description    | Access |
| ------ | -------------------- | -------------- | ------ |
| GET    | `/api/v1/health`     | Service health | Public |

**Pagination:** All list endpoints support `?limit=N&offset=M`. Response
includes `{ "data": [...], "pagination": { "limit", "offset", "total", "has_more" } }`.

**Filters on `GET /api/v1/jobs`:** `job_type`, `qualification_level`,
`organization`, `department`, `status`, `is_featured`, `is_urgent`,
`q` (full-text search via `ts_rank` + `plainto_tsquery`).

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
| 400  | `VALIDATION_PASSWORD_WEAK`    | Doesn't meet strength requirements   |
| 400  | `VALIDATION_MISSING_FIELD`    | Required field missing               |
| 401  | `AUTH_INVALID_CREDENTIALS`    | Wrong email/password                 |
| 401  | `AUTH_TOKEN_EXPIRED`          | Access token expired                 |
| 401  | `AUTH_TOKEN_REVOKED`          | Token blocklisted (logout)           |
| 401  | `AUTH_EMAIL_NOT_VERIFIED`     | Email verification pending           |
| 403  | `FORBIDDEN_PERMISSION_DENIED` | Role lacks permission                |
| 403  | `FORBIDDEN_ADMIN_ONLY`        | Admin access required                |
| 404  | `NOT_FOUND_USER`              | User doesn't exist                   |
| 404  | `NOT_FOUND_JOB`               | Job doesn't exist                    |
| 404  | `NOT_FOUND_APPLICATION`       | Application not found                |
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

| Endpoint                         | User | Operator       | Admin |
| -------------------------------- | ---- | -------------- | ----- |
| `GET /api/v1/jobs`               | ✅   | ✅             | ✅    |
| `POST /api/v1/jobs`              | ❌   | ❌             | ✅    |
| `PUT /api/v1/jobs/:id`           | ❌   | ✅ (limited)   | ✅    |
| `DELETE /api/v1/jobs/:id`        | ❌   | ❌             | ✅    |
| `GET /api/v1/users/profile`      | ✅   | ✅             | ✅    |
| `GET /api/v1/admin/users`        | ❌   | ❌             | ✅    |
| `PUT /api/v1/admin/users/:id/role` | ❌ | ❌             | ✅    |
| `GET /api/v1/admin/analytics`    | ❌   | ❌             | ✅    |

**Operator restrictions:** Can only modify `status`, `description`, and
`important_dates` on job records. Cannot modify `salary`, `vacancy_count`, or
delete jobs.

### Initial Admin Setup

No self-registration for admin accounts. The first admin is created via a direct
database insert into the `admin_users` table:

```sql
INSERT INTO admin_users (email, password_hash, full_name, role, department, status)
VALUES ('admin@example.com', '<bcrypt-hash>', 'System Admin', 'admin', 'Engineering', 'active');
```

Subsequent operators are created by inserting into `admin_users` with
`role = 'operator'`. Existing admin/operator roles can be changed via
`PUT /api/v1/admin/users/:id/role` (admin only).

---

## Background Tasks

### Celery Beat Schedule

| Task                            | Schedule        | Description                            |
| ------------------------------- | --------------- | -------------------------------------- |
| `send-deadline-reminders`       | Daily 08:00 UTC | T-7, T-3, T-1 reminders → delegates to `smart_notify` |
| `purge-expired-notifications`   | Daily 01:00 UTC | Delete notifications past `expires_at` |
| `purge-expired-admin-logs`      | Daily 01:30 UTC | Delete admin logs past `expires_at`    |
| `purge-soft-deleted-jobs`       | Daily 02:00 UTC | Hard-delete jobs soft-deleted > 90 days|
| `close-expired-job-listings`    | Daily 02:30 UTC | Auto-close jobs past `application_end` |
| `generate-sitemap`              | Daily 04:00 UTC | Regenerate `/sitemap.xml` with active jobs |

### Event-Triggered Tasks

| Trigger                  | Task                           | Description                            |
| ------------------------ | ------------------------------ | -------------------------------------- |
| Any notification needed  | `smart_notify`                 | Unified entry — instant or staggered delivery to all 4 channels |
| New job created (active) | `send_new_job_notifications`   | Match org followers → `smart_notify(staggered)` per user |
| Admin updates a job      | `notify_priority_subscribers`  | Notify priority trackers → `smart_notify(staggered)` per user |
| Staggered email delivery | `deliver_delayed_email`        | Fires after `NOTIFY_EMAIL_DELAY` — sends the email |
| Staggered WhatsApp       | `deliver_delayed_whatsapp`     | Fires after `NOTIFY_WHATSAPP_DELAY` — sends the WhatsApp |

---

## Job Ingestion Strategy

Jobs enter the system through two paths:

### Phase 1: Manual Entry (Current)

Admin creates a job via `POST /api/v1/admin/jobs`. The job is created with
`source='manual'` and `status='active'` (published immediately). This is the
only method available in v1.

### Phase 2: PDF Upload → AI Extraction → Review → Publish (Implemented)

Government job notifications are published as PDF documents. Instead of
manually typing every field, admin/operator uploads the notification PDF and
AI extracts the structured data for review.

```
Admin/Operator uploads notification PDF
    │
    ▼
┌────────────────────────────────────────┐
│ Celery task: extract_job_from_pdf        │
│                                          │
│ 1. Parse PDF text (PyMuPDF / pdfplumber)  │
│ 2. Send extracted text to AI model        │
│    (structured extraction prompt)         │
│ 3. AI returns JSON:                       │
│    - job_title, organization, department  │
│    - eligibility (age, education, category)│
│    - dates (application, exam, result)    │
│    - vacancies, salary, fee               │
│    - official PDF URL (source_url)        │
│ 4. Create job_vacancies row:              │
│    status = 'draft'                       │
│    source = 'pdf_upload'                  │
│    documents = [{type: "notification",    │
│                   url: <stored PDF>}]     │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ Review Page (Admin Frontend)             │
│                                          │
│ Shows AI-extracted data in an editable   │
│ form pre-filled with all fields:         │
│   ├─ Job title, org, department           │
│   ├─ Eligibility (age, education, etc.)   │
│   ├─ Dates (application, exam, result)    │
│   ├─ Vacancies, salary, fee               │
│   ├─ Original PDF (side-by-side view)     │
│   └─ Confidence indicator per field       │
│                                          │
│ Operator/Admin can:                      │
│   ├─ Edit any incorrect field             │
│   ├─ Add missing data                     │
│   └─ Approve → status='active'            │
│        (triggers user notifications)     │
└────────────────────────────────────────┘
```

### PDF Extraction Tech Stack

| Component | Technology | Purpose |
| --------- | ---------- | ------- |
| PDF parsing | pdfplumber | Extract raw text from notification PDF |
| AI extraction | Anthropic Claude API | Structured data extraction from text |
| Storage | Docker volume (local disk) | Store uploaded PDF files |
| Task queue | Celery (existing) | Async PDF processing |

The AI extraction prompt would map PDF text to the `job_vacancies` schema
fields. The review page shows the extracted data side-by-side with the
original PDF so the operator can verify and correct before publishing.

### API Endpoints for Ingestion

| Method | Endpoint                          | Description                    | Access   |
| ------ | --------------------------------- | ------------------------------ | -------- |
| POST   | `/api/v1/admin/jobs/upload-pdf`   | Upload PDF → trigger extraction | Admin    |
| GET    | `/api/v1/admin/jobs?status=draft` | List draft jobs for review     | Operator |
| GET    | `/api/v1/admin/jobs/:id/review`   | Get draft with AI-extracted data | Operator |
| PUT    | `/api/v1/admin/jobs/:id/approve`  | Approve draft → active         | Operator |

---

## SEO Strategy

Government job portals get 80%+ traffic from Google. SEO is critical for
discoverability.

### Dynamic Sitemap

A nightly Celery task (`generate-sitemap`) regenerates `/sitemap.xml` with all
active job URLs:

```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://hermes.example.com/jobs/ssc-cgl-2026</loc>
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
<link rel="canonical" href="https://hermes.example.com/jobs/{{ job.slug }}">
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

| Channel    | Technology          | Instant Mode (T+0) | Staggered Mode                     | Status      |
| ---------- | ------------------- | ------------------- | ---------------------------------- | ----------- |
| In-app     | PostgreSQL row      | T+0                 | T+0                                | Implemented |
| Push (FCM) | Firebase FCM        | T+0                 | T+0 (fingerprint de-dup)           | Implemented |
| Email      | OCI Email Delivery  | T+0                 | T+`NOTIFY_EMAIL_DELAY` (default 15min) | Implemented |
| WhatsApp   | WhatsApp Cloud API  | T+0                 | T+`NOTIFY_WHATSAPP_DELAY` (default 1hr) | Implemented (API placeholder) |

**Two delivery modes** via `smart_notify(delivery_mode="instant"|"staggered")`:
- **instant** — all 4 channels at T+0 (OTP, password reset, email verification, welcome)
- **staggered** — in-app + push at T+0, email delayed, WhatsApp delayed (job alerts, reminders)

Delays are configurable via env vars (`NOTIFY_EMAIL_DELAY`, `NOTIFY_WHATSAPP_DELAY`).
All channels always deliver — staggered just adds a time gap to avoid bombarding simultaneously.
User preferences (`notification_preferences` JSONB) control per-channel opt-out.

#### Telegram & WhatsApp (Future)

Users will be able to link their Telegram or WhatsApp to receive job alerts
directly on their phone without installing the Hermes app.

- **Telegram**: User links account via `/start` command on the Hermes bot.
  Bot sends job alerts, deadline reminders, and result notifications.
  Free — no per-message cost.
- **WhatsApp**: User opts in by sending a keyword to the Hermes WhatsApp
  Business number. Uses WhatsApp Cloud API (1,000 free conversations/month).
  Template messages for job alerts; session messages for interactive queries.

Both channels store the user's chat ID / phone in `notification_preferences`:

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

### Organization Follow (Future)

Users can follow specific organizations (SSC, UPSC, Railway, etc.) to get
notified whenever that org posts *any* job — regardless of profile match.

Stored in a `user_org_follows` many-to-many table (future expansion table).
The `send_new_job_notifications` Celery task checks both profile matches and
org follows when a job is created.

| Method | Endpoint                              | Description            | Access |
| ------ | ------------------------------------- | ---------------------- | ------ |
| POST   | `/api/v1/users/follow-org`            | Follow an organization | User   |
| DELETE | `/api/v1/users/follow-org/:org_name`  | Unfollow               | User   |
| GET    | `/api/v1/users/followed-orgs`         | List followed orgs     | User   |

### Social Share Buttons

Every job detail page includes WhatsApp and Telegram share links. These are
zero-cost, zero-infrastructure features that drive organic growth — Indian
government job seekers heavily share links in WhatsApp groups.

```html
<!-- WhatsApp share -->
<a href="whatsapp://send?text={{ job.job_title }}%20-%20{{ canonical_url }}"
   target="_blank" rel="noopener">Share on WhatsApp</a>

<!-- Telegram share -->
<a href="https://t.me/share/url?url={{ canonical_url }}&text={{ job.job_title }}"
   target="_blank" rel="noopener">Share on Telegram</a>
```

These are pure HTML links rendered by Jinja2. No API or JavaScript required.

### Application Fee by Category

Government jobs charge different application fees by category (General ₹100,
OBC ₹100, SC/ST ₹0, Female ₹0, etc.). When a logged-in user views a job,
the frontend reads the `eligibility.fee` object from the job and the user's
`category` from their profile, then displays: **"Your application fee: ₹0"**.

This is pure Jinja2 template logic — no API changes needed. The `eligibility`
JSONB already supports storing fee breakdowns:

```json
{
  "fee": {
    "general": 100,
    "obc": 100,
    "sc": 0,
    "st": 0,
    "ews": 0,
    "female": 0,
    "pwd": 0
  }
}
```

### Data Retention

Row expiry is handled via an `expires_at` column and nightly Celery purge tasks.

| Data             | Retention | Mechanism                     |
| ---------------- | --------- | ----------------------------- |
| Notifications    | 90 days   | `expires_at` + Celery purge   |
| Admin logs       | 30 days   | `expires_at` + Celery purge   |
| Redis sessions   | 15 min    | Redis TTL                     |
| Job cache        | 1 hour    | Redis TTL                     |
| Preferences cache| 24 hours  | Redis TTL                     |

### PgBouncer (Connection Pooling)

PgBouncer runs as a sidecar container (~10 MB RAM) between the application
and PostgreSQL. FastAPI backend, Celery workers, and Celery Beat all connect
to PgBouncer on port `6432` instead of PostgreSQL directly on `5432`.

This matters because:
- PostgreSQL on ARM with limited memory shouldn't hold too many connections
- Celery workers can spike connection counts during task bursts
- PgBouncer multiplexes many app connections over fewer PostgreSQL connections

Configuration: transaction pooling mode, `max_client_conn=100`,
`default_pool_size=20`. Set in `pgbouncer.ini` mounted as a Docker volume.

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
Uvicorn and Celery.

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
| Mail     | Mailpit or `MAIL_SUPPRESS_SEND=True`                  |
| Nginx    | Not required; access services directly on exposed ports|
| TLS      | None                                                   |
| Volumes  | Hot-reload mounts for code                             |

```bash
cp config/development/.env.backend.development       src/backend/.env
cp config/development/.env.frontend.development      src/frontend/.env
cp config/development/.env.frontend-admin.development src/frontend-admin/.env

cd src/backend        && docker compose up -d
cd ../frontend        && docker compose up -d
cd ../frontend-admin  && docker compose up -d
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
| Monitoring| OCI Monitoring + Alarms (500M datapoints/month free)            |
| Images    | Built directly on VM via `git pull` + `docker compose up --build`|
| CDN       | Cloudflare Free Tier — CDN cache, DDoS protection, analytics   |
| Secrets   | `.env` files (gitignored, managed manually on VM)               |
| Backups   | `pg_dump` daily cron + OCI block volume snapshots (weekly)      |

**Resource allocation (~3 GB used of 24 GB):**

| Container        | RAM      |
| ---------------- | -------- |
| PostgreSQL 16    | ~1 GB    |
| Redis 7          | ~256 MB  |
| PgBouncer        | ~10 MB   |
| Backend (FastAPI) | ~512 MB  |
| Celery Worker    | ~512 MB  |
| Celery Beat      | ~128 MB  |
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
- [ ] OCI Monitoring alarms set for CPU > 80%, disk > 90%
- [ ] Cloudflare DNS configured — domain proxied through Cloudflare
- [ ] Redis AOF persistence enabled (`appendonly yes` in redis.conf)

---

## Security Design

All items below are implemented.

- **Password hashing:** bcrypt (salted)
- **JWT with Redis blocklist:** access tokens expire in 15 min, refresh in 7 days
- **Rate limiting:** Nginx (100 req/min per IP) + SlowAPI (1000 req/min per user, 5/min on login)
- **CORS:** Only whitelisted origins in `CORS_ORIGINS`
- **HTTPS/TLS:** Nginx handles SSL termination via Let's Encrypt (Certbot) — free, auto-renewing certificates directly on the VM
- **Network isolation:** OCI VCN security list — only ports 80/443/22 open; DB and Redis never exposed outside Docker networks
- **Security headers:** X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Content-Security-Policy, Strict-Transport-Security, Referrer-Policy (via Nginx behind LB)
- **Input validation:** Pydantic models on all endpoints (FastAPI native)
- **CSRF protection:** Redis-backed single-use tokens (1h TTL)
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
  | PDF upload | `upload_pdf` — filename |
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
  | Application tracked | `user_id`, `job_id` |
  | Application updated | `user_id`, changed fields |
  | Application removed | `user_id`, `application_id` |

---

## Environment Variables

Each service has its own `.env` file. Templates live in `config/<environment>/`.

### Backend (`src/backend/.env`)

```env
# App
APP_ENV=development
SECRET_KEY=<random-32-bytes>
BACKEND_PORT=8000

# PostgreSQL (async via asyncpg, through PgBouncer)
DATABASE_URL=postgresql+asyncpg://hermes_user:<password>@pgbouncer:6432/hermes_db
DB_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=<password>

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email — OCI Email Delivery (3,000/day free)
MAIL_SERVER=smtp.email.ap-mumbai-1.oci.oraclecloud.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<OCI-SMTP-credential-OCID>
MAIL_PASSWORD=<OCI-SMTP-credential-password>
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Firebase (push notifications)
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json

# Notification delivery delays (staggered mode, in seconds)
NOTIFY_EMAIL_DELAY=900         # 15 minutes (default)
NOTIFY_WHATSAPP_DELAY=3600     # 1 hour (default)

# JWT
JWT_SECRET_KEY=<separate-random-key>
JWT_ACCESS_TOKEN_EXPIRES=900
```

### User Frontend (`src/frontend/.env`)

```env
BACKEND_API_URL=http://localhost:8000/api/v1
SECRET_KEY=<frontend-secret-key>
FRONTEND_PORT=8080
SESSION_TIMEOUT=3600
```

### Admin Frontend (`src/frontend-admin/.env`)

```env
BACKEND_API_URL=http://localhost:8000/api/v1
SECRET_KEY=<admin-frontend-secret-key>
FRONTEND_ADMIN_PORT=8081
SESSION_TIMEOUT=3600
```

In production, `BACKEND_API_URL` points to the internal Docker hostname
(`http://backend:8000/api/v1`) or the production domain. Each frontend must
have a **different** `SECRET_KEY`.

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
│  │ Celery Worker  │  Celery Beat           │  │
│  └─────────────────────────────────────────┘  │
│                                               │
│  Cron: pg_dump daily + block volume weekly    │
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
| Monitoring + Alarms | CPU, disk, health check alerts | 500M datapoints/month |
| Block Volume | VM storage + backup snapshots | 200 GB total |
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
cp config/development/.env.backend.development       src/backend/.env
cp config/development/.env.frontend.development      src/frontend/.env
cp config/development/.env.frontend-admin.development src/frontend-admin/.env

cd src/backend        && docker compose up -d
cd ../frontend        && docker compose up -d
cd ../frontend-admin  && docker compose up -d
```

### Production Deployment

```bash
# SSH into OCI ARM VM
ssh -i <key> ubuntu@<vm-public-ip>

# Clone and configure
git clone <repo-url> hermes && cd hermes
cp config/production/.env.backend.production       src/backend/.env
cp config/production/.env.frontend.production      src/frontend/.env
cp config/production/.env.frontend-admin.production src/frontend-admin/.env

# Deploy all services
./scripts/deployment/deploy_all.sh production
```

Or start each service individually:

```bash
cd src/backend        && docker compose up -d --build
cd ../frontend        && docker compose up -d --build
cd ../frontend-admin  && docker compose up -d --build
cd ../nginx           && docker compose up -d --build
```

### Backup and Restore

**Daily database backup** (host cron):

```bash
# crontab -e
0 2 * * * /home/ubuntu/hermes/scripts/backup/backup_db.sh
```

**Weekly block volume snapshot** (host cron via OCI CLI):

```bash
# crontab -e
0 3 * * 0 oci bv boot-volume-backup create \
  --boot-volume-id <boot-volume-ocid> \
  --type INCREMENTAL \
  --display-name "hermes-weekly-$(date +\%Y\%m\%d)"
```

**Restore:**

```bash
./scripts/backup/restore_db.sh <file>   # restore from pg_dump
```

---

## Related Documentation

- [Workflow Diagrams](DIAGRAMS.md) — ASCII diagrams for user registration, job creation, matching, application tracking, admin dashboard, RBAC enforcement, and JWT token flows.
