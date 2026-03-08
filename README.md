# Hermes - Government Job Vacancy Portal

> **🚀 Quick Start**: New to this project? Read [docs/PROJECT_SUMMARY.md](./docs/PROJECT_SUMMARY.md) for a 10-minute deployment guide.

> **📂 Project Structure**: See [docs/PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md) for complete folder structure and architecture.

> **📚 Documentation**: See the `docs/` folder for all available documentation.

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [System Architecture](#system-architecture)
4. [Database Schema](#database-schema-postgresql-tables)
5. [API Endpoints](#api-endpoints)
6. [Key Features](#key-features-implementation)
7. [Deployment Options](#deployment-options)
8. [Project Structure](#project-structure-microservices)
9. [Environment Setup](#environment-variables-env)
10. [Development Workflow](#development-workflow)
11. [Deployment Guides](#hostinger-vps-deployment-guide)
12. [Troubleshooting](#troubleshooting-hostinger-vps)

📖 **Additional Documentation**:
- [Workflow Diagrams](./docs/WORKFLOW_DIAGRAMS.md)
- [Project Structure](./docs/PROJECT_STRUCTURE.md)

## Project Overview

A comprehensive web application that provides users with personalized government job vacancy notifications based on their educational qualifications, preferences, and job priorities. The system includes user authentication, profile management, intelligent notification filtering, and an admin panel for job management.

### Key Capabilities
- 🎯 **Intelligent Job Matching**: Automatically matches jobs based on user's education (10th, 12th, Graduation), stream (Science/Commerce/Arts), age, and category (General/OBC/SC/ST)
- 📧 **Multi-Channel Notifications**: Email (Flask-Mail), Push (Firebase FCM), and In-app notifications
- ⏰ **Smart Reminders**: Automatic deadline reminders at 7 days, 3 days, and 1 day before application closes
- 📊 **Admin Dashboard**: Complete job management with analytics and user tracking
- 🔐 **Secure Authentication**: JWT-based API authentication with session management
- 🐳 **Containerized Deployment**: Docker microservices architecture for easy scaling

## Tech Stack

### Backend (Flask API)
- **Framework**: Python Flask 3.0.0
- **Database**: PostgreSQL 16 (Relational)
- **ORM**: Flask-SQLAlchemy 3.1 + psycopg2-binary
- **Authentication**: Flask-JWT-Extended
- **Task Queue**: Celery 5.3.4 with Redis broker
- **Email Service**: Flask-Mail (SMTP)
- **Push Notifications**: Firebase Cloud Messaging (FCM)
- **Production Server**: Gunicorn 21.2.0

### User Frontend (`src/frontend/`) — port 8080
- **Framework**: Python Flask 3.0.0
- **Template Engine**: Jinja2
- **Session Management**: Flask-Login
- **Static Assets**: HTML5, CSS3, JavaScript
- **API Client**: Python Requests library
- **Production Server**: Gunicorn 21.2.0
- **Audience**: Public users — register, login, browse jobs, manage profile

### Admin Frontend (`src/frontend-admin/`) — port 8081
- **Framework**: Python Flask 3.0.0
- **Template Engine**: Jinja2
- **Session Management**: Flask-Login
- **Static Assets**: HTML5, CSS3, JavaScript
- **API Client**: Python Requests library
- **Production Server**: Gunicorn 21.2.0
- **Audience**: Admin + Operator roles only — dashboard, job management, user management

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx (load balancing, SSL, static files)
- **Cache & Broker**: Redis 7.0
- **Deployment**: Hostinger VPS (Ubuntu 22.04 LTS)

## System Architecture

### Three-Service Architecture (Independent Containers)

```
┌────────────────────────────────────────────────────────────┐
│                    User's Browser                          │
└────────────────┬───────────────────────────────────────────┘
                 │ HTTPS (Port 443)
                 ↓
┌────────────────────────────────────────────────────────────┐
│           Nginx Reverse Proxy Container                    │
│         - SSL Termination (Let's Encrypt)                  │
│         - Load Balancing                                   │
│         - Static File Serving                              │
│         - Rate Limiting                                    │
└────┬─────────────────────────┬──────────────────┬──────────┘
     │                         │                  │
     │ /api/* → backend:5000   │ /* → user:8080   │ admin.* → admin:8081
     ↓                         ↓                  ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Backend Container│  │  User Frontend   │  │  Admin Frontend  │
│ (Flask REST API) │  │  Container       │  │  Container       │
│                  │  │  (Flask+Jinja2)  │  │  (Flask+Jinja2)  │
│ - Auth (✅ done) │◄─│ - Register/Login │  │ - Admin Login    │
│ - Business Logic │  │ - Job browsing   │◄─│ - Dashboard      │
│ - JWT + RBAC     │  │ - User profile   │  │ - Job mgmt       │
│ - Job Matching   │  │ - Notifications  │  │ - User mgmt      │
│ - Notifications  │  │                  │  │                  │
│ Port: 5000       │  │ Port: 8080       │  │ Port: 8081       │
└────────┬─────────┘  └──────────────────┘  └──────────────────┘
         │
         ├──────────────┬──────────────┬─────────────┐
         ↓              ↓              ↓             ↓
┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐
│ PostgreSQL  │  │   Redis     │  │ Celery   │  │ Celery   │
│  Container  │  │  Container  │  │ Worker   │  │  Beat    │
│             │  │             │  │Container │  │Container │
│ - Jobs DB   │  │ - Token     │  │          │  │          │
│ - Users DB  │  │   blocklist │  │ - Emails │  │- Schedule│
│ - Logs      │  │ - Sessions  │  │ - Push   │  │- Cron    │
│             │  │ - Queue     │  │ - Match  │  │          │
│ Port: 5432  │  │ Port: 6379  │  │          │  │          │
└─────────────┘  └─────────────┘  └──────────┘  └──────────┘

  Backend network    User frontend network    Admin frontend network
  (src_backend_      (src_frontend_           (src_frontend_admin_
   network)           network)                 network)
  Each service runs its own docker-compose.yml independently
```

### Core Components

1. **User Management Module** (Backend + User Frontend)
2. **Job Vacancy Module** (Backend + User Frontend)
3. **Notification Engine** (Backend + Celery)
4. **Admin Panel** (Backend + Admin Frontend — `src/frontend-admin/`, port 8081)
5. **Profile Matching System** (Backend + Celery)
6. **Application Tracking System** (Backend + User Frontend)

---

### ⚡ Health Checks & Service Dependencies

**Why Health Checks Matter?** Without them, Nginx might route traffic to crashed containers.

**What the system checks:**
- **PostgreSQL**: Every 10 seconds (must be healthy before Backend starts)
- **Redis**: Every 10 seconds (must be healthy before Celery starts)
- **Backend**: Every 30 seconds at `/api/v1/health`
- **User Frontend**: Every 30 seconds at `/health` (port 8080)
- **Admin Frontend**: Every 30 seconds at `/health` (port 8081)
- **Nginx**: Every 30 seconds at `/health` (monitors reverse proxy health)

**Dependency Chain (ensures ordered startup)**:
1. PostgreSQL starts and becomes healthy
2. Redis starts and becomes healthy
3. Backend waits for PostgreSQL + Redis healthy, then starts
4. User Frontend starts independently (calls backend via `BACKEND_API_URL`)
5. Admin Frontend starts independently (calls backend via `BACKEND_API_URL`)
6. Nginx connects to all three networks and routes traffic

**If a container fails:**
- Docker restarts it automatically (`restart: unless-stopped`)
- Health checks detect unhealthy state
- Nginx stops routing traffic to failed containers
- No cascading failures

**Check container health manually:**
```bash
# All containers
docker compose ps

# Specific container health
docker compose ps backend  # Shows healthy/unhealthy status

# View health check logs
docker compose exec postgresql pg_isready -U hermes_user -d hermes_db
docker compose exec backend curl http://localhost:5000/api/v1/health
```

---


## Database Schema (PostgreSQL Tables)

> **📊 Total Tables**: 15 — fully relational PostgreSQL 16 tables with UUID primary keys, JSONB for flexible metadata, and proper foreign-key constraints

### 1. `users` Table
```sql
CREATE TABLE users (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email               VARCHAR(255) UNIQUE NOT NULL,
  password_hash       VARCHAR(255) NOT NULL,
  full_name           VARCHAR(255) NOT NULL,
  phone               VARCHAR(20),
  role                VARCHAR(20) NOT NULL DEFAULT 'user'
                        CHECK (role IN ('user','admin','operator')),
  status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','suspended','deleted')),
  avatar_url          TEXT,
  is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
  is_email_verified   BOOLEAN NOT NULL DEFAULT FALSE,
  is_mobile_verified  BOOLEAN NOT NULL DEFAULT FALSE,
  last_login          TIMESTAMP WITH TIME ZONE,
  created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email  ON users (email);
CREATE INDEX idx_users_status ON users (status);
```

### 2. `user_profiles` Table (Enhanced)
```sql
-- education and notification_preferences use JSONB for flexible nested structure
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
  -- JSONB: stores 10th/12th/graduation/post-graduation sub-documents
  education                 JSONB NOT NULL DEFAULT '{}',
  -- JSONB: stores height/weight/chest/vision/color_blindness
  physical_details          JSONB NOT NULL DEFAULT '{}',
  -- JSONB: stores quick filter arrays (organizations, job types, locations, salary range)
  quick_filters             JSONB NOT NULL DEFAULT '{}',
  -- JSONB: stores notification channels and frequency preferences
  notification_preferences  JSONB NOT NULL DEFAULT '{}',
  updated_at                TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_user_profiles_user_id ON user_profiles (user_id);
-- GIN index for fast JSONB containment queries
CREATE INDEX idx_user_profiles_education       ON user_profiles USING GIN (education);
CREATE INDEX idx_user_profiles_notif_prefs     ON user_profiles USING GIN (notification_preferences);
```

### 3. `job_vacancies` Table (Significantly Enhanced)
```sql
-- Large nested structures (vacancy_breakdown, eligibility, exam_details, salary, etc.)
-- are stored as JSONB for schema flexibility while keeping core filter columns indexed.
CREATE TABLE job_vacancies (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_title             VARCHAR(500) NOT NULL,
  slug                  VARCHAR(500) UNIQUE NOT NULL,
  organization          VARCHAR(255) NOT NULL,
  department            VARCHAR(255),
  post_code             VARCHAR(100),
  job_type              VARCHAR(50) NOT NULL DEFAULT 'latest_job'
                          CHECK (job_type IN ('latest_job','result','admit_card','answer_key','admission','yojana')),
  employment_type       VARCHAR(50) DEFAULT 'permanent'
                          CHECK (employment_type IN ('permanent','temporary','contract','apprentice')),
  qualification_level   VARCHAR(50),   -- '10th','10+2','graduate','post-graduate','diploma','iti'
  total_vacancies       INTEGER,
  -- JSONB: by_category, by_post, by_state, by_trade breakdowns
  vacancy_breakdown     JSONB NOT NULL DEFAULT '{}',
  description           TEXT,
  short_description     TEXT,
  -- JSONB: age_limit, physical_standards, medical_standards, qualification_details
  eligibility           JSONB NOT NULL DEFAULT '{}',
  -- JSONB: application_link, fee, important_links, payment_mode
  application_details   JSONB NOT NULL DEFAULT '{}',
  -- Individual date columns for indexed range queries
  notification_date     DATE,
  application_start     DATE,
  application_end       DATE,
  last_date_fee         DATE,
  correction_start      DATE,
  correction_end        DATE,
  admit_card_release    DATE,
  exam_city_release     DATE,
  exam_start            DATE,
  exam_end              DATE,
  answer_key_release    DATE,
  result_date           DATE,
  -- JSONB: exam_pattern, phases, syllabus_link
  exam_details          JSONB NOT NULL DEFAULT '{}',
  salary_initial        INTEGER,
  salary_max            INTEGER,
  -- JSONB: pay_scale, pay_level, allowances, other_benefits
  salary                JSONB NOT NULL DEFAULT '{}',
  -- JSONB: selection phases array
  selection_process     JSONB NOT NULL DEFAULT '[]',
  -- JSONB: documents required array
  documents_required    JSONB NOT NULL DEFAULT '[]',
  status                VARCHAR(20) NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active','expired','cancelled','upcoming')),
  is_featured           BOOLEAN NOT NULL DEFAULT FALSE,
  is_urgent             BOOLEAN NOT NULL DEFAULT FALSE,
  is_trending           BOOLEAN NOT NULL DEFAULT FALSE,
  priority              SMALLINT NOT NULL DEFAULT 0,
  meta_title            VARCHAR(500),
  meta_description      TEXT,
  meta_keywords         TEXT[],
  views                 INTEGER NOT NULL DEFAULT 0,
  applications_count    INTEGER NOT NULL DEFAULT 0,
  shares_count          INTEGER NOT NULL DEFAULT 0,
  created_by            UUID REFERENCES users(id),
  published_at          TIMESTAMP WITH TIME ZONE,
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_organization      ON job_vacancies (organization);
CREATE INDEX idx_jobs_status_created    ON job_vacancies (status, created_at DESC);
CREATE INDEX idx_jobs_qual_level        ON job_vacancies (qualification_level);
CREATE INDEX idx_jobs_application_end   ON job_vacancies (application_end);
CREATE INDEX idx_jobs_org_status        ON job_vacancies (organization, status, created_at DESC);
CREATE INDEX idx_jobs_eligibility_gin   ON job_vacancies USING GIN (eligibility);
```

### 4. `user_job_applications` Table
```sql
CREATE TABLE user_job_applications (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  job_id                  UUID NOT NULL REFERENCES job_vacancies(id) ON DELETE CASCADE,
  application_number      VARCHAR(100),
  is_priority             BOOLEAN NOT NULL DEFAULT FALSE,
  applied_on              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  exam_center             VARCHAR(255),
  admit_card_downloaded   BOOLEAN NOT NULL DEFAULT FALSE,
  exam_appeared           BOOLEAN NOT NULL DEFAULT FALSE,
  status                  VARCHAR(50) NOT NULL DEFAULT 'applied'
                            CHECK (status IN (
                              'applied','admit_card_released','exam_completed',
                              'result_pending','selected','rejected','waiting_list'
                            )),
  notes                   TEXT,
  -- JSONB: reminder objects with type, date, notified flag
  reminders               JSONB NOT NULL DEFAULT '[]',
  -- JSONB: marks_obtained, total_marks, rank, cutoff_marks, status
  result_info             JSONB NOT NULL DEFAULT '{}',
  UNIQUE (user_id, job_id)
);

CREATE INDEX idx_applications_user_job      ON user_job_applications (user_id, job_id);
CREATE INDEX idx_applications_user_applied  ON user_job_applications (user_id, applied_on DESC);
```

### 5. `notifications` Table (Enhanced)
```sql
CREATE TABLE notifications (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type VARCHAR(50)  -- 'job','result','admit_card','answer_key','admission','yojana'
                CHECK (entity_type IN ('job','result','admit_card','answer_key','admission','yojana')),
  entity_id   UUID,
  type        VARCHAR(60) NOT NULL,  -- 'new_vacancy','application_reminder','admit_card', etc.
  title       VARCHAR(500) NOT NULL,
  message     TEXT NOT NULL,
  action_url  TEXT,
  is_read     BOOLEAN NOT NULL DEFAULT FALSE,
  sent_via    TEXT[],              -- e.g. ARRAY['email','push','in-app']
  priority    VARCHAR(10) NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low','medium','high')),
  created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  read_at     TIMESTAMP WITH TIME ZONE,
  -- Row-level TTL enforced by a scheduled pg_cron job (90-day retention)
  expires_at  TIMESTAMP WITH TIME ZONE NOT NULL
                DEFAULT (NOW() + INTERVAL '90 days')
);

CREATE INDEX idx_notifications_user_read    ON notifications (user_id, is_read);
CREATE INDEX idx_notifications_user_created ON notifications (user_id, created_at DESC);
CREATE INDEX idx_notifications_expires      ON notifications (expires_at);
```

### 6. `admin_logs` Table
```sql
CREATE TABLE admin_logs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id      UUID NOT NULL REFERENCES users(id),
  action        VARCHAR(100) NOT NULL,   -- 'create_job','update_job','delete_job','approve_user'
  resource_type VARCHAR(100),            -- 'job_vacancy','result','admit_card','user'
  resource_id   UUID,
  details       TEXT,
  -- JSONB: field-level old_value / new_value diff
  changes       JSONB NOT NULL DEFAULT '{}',
  ip_address    INET,
  user_agent    TEXT,
  timestamp     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  -- Row-level TTL: Celery cleanup task deletes rows older than 30 days
  expires_at    TIMESTAMP WITH TIME ZONE NOT NULL
                  DEFAULT (NOW() + INTERVAL '30 days')
);

CREATE INDEX idx_admin_logs_admin_ts ON admin_logs (admin_id, timestamp DESC);
CREATE INDEX idx_admin_logs_expires  ON admin_logs (expires_at);
```

### 7. `results` Table (NEW)
```sql
CREATE TABLE results (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id         UUID REFERENCES job_vacancies(id) ON DELETE SET NULL,
  result_type    VARCHAR(50) NOT NULL,  -- 'written','prelims','mains','interview','final','cutoff','merit_list','psl_list','dv_list','waiting_list'
  result_phase   VARCHAR(100),
  result_title   VARCHAR(500) NOT NULL,
  result_date    DATE,
  -- JSONB: result_pdf, scorecard_link, marks_link, merit_list_link
  result_links   JSONB NOT NULL DEFAULT '{}',
  -- JSONB: category-wise cutoff marks {general: {male, female}, obc: {...}, ...}
  cut_off_marks  JSONB NOT NULL DEFAULT '{}',
  -- JSONB: total_appeared, qualified, selected, highest_marks, lowest_marks
  statistics     JSONB NOT NULL DEFAULT '{}',
  is_final       BOOLEAN NOT NULL DEFAULT FALSE,
  status         VARCHAR(20) NOT NULL DEFAULT 'active'
                   CHECK (status IN ('active','revised','cancelled')),
  created_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_results_job_id ON results (job_id);
```

### 8. `admit_cards` Table (NEW)
```sql
CREATE TABLE admit_cards (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id                    UUID REFERENCES job_vacancies(id) ON DELETE SET NULL,
  exam_name                 VARCHAR(500) NOT NULL,
  exam_phase                VARCHAR(100),
  release_date              DATE,
  exam_date_start           DATE,
  exam_date_end             DATE,
  exam_mode                 VARCHAR(50),
  download_link             TEXT,
  exam_city_link            TEXT,
  mock_test_link            TEXT,
  self_slot_selection_link  TEXT,
  instructions              TEXT,
  reporting_time            VARCHAR(50),
  exam_timing               VARCHAR(100),
  important_documents       TEXT[],
  exam_centers              TEXT[],
  status                    VARCHAR(20) NOT NULL DEFAULT 'active'
                              CHECK (status IN ('active','expired')),
  created_at                TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_admit_cards_job_id ON admit_cards (job_id);
```

### 9. `answer_keys` Table (NEW)
```sql
CREATE TABLE answer_keys (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id                UUID REFERENCES job_vacancies(id) ON DELETE SET NULL,
  exam_name             VARCHAR(500) NOT NULL,
  exam_phase            VARCHAR(100),
  paper_name            VARCHAR(255),
  release_date          DATE,
  -- JSONB: [{set, url}, ...]
  answer_key_links      JSONB NOT NULL DEFAULT '[]',
  -- JSONB: [{subject, url}, ...]
  subject_wise_links    JSONB NOT NULL DEFAULT '[]',
  objection_start       DATE,
  objection_end         DATE,
  objection_fee         INTEGER,
  objection_link        TEXT,
  response_sheet_link   TEXT,
  question_paper_link   TEXT,
  total_questions       INTEGER,
  status                VARCHAR(30) NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active','expired','final_published')),
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_answer_keys_job_id ON answer_keys (job_id);
```

### 10. `admissions` Table (NEW)
```sql
CREATE TABLE admissions (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  title             VARCHAR(300) NOT NULL,
  slug              VARCHAR(320) NOT NULL UNIQUE,
  admission_type    VARCHAR(30)  NOT NULL CHECK (admission_type IN ('ug','pg','diploma','certificate','school','entrance_exam')),
  course_name       VARCHAR(200),
  conducting_body   VARCHAR(200),
  total_seats       INTEGER,
  description       TEXT,
  eligibility       JSONB,        -- {qualification, min_percentage, age_limit, nationality, required_subjects[]}
  application_dates JSONB,        -- {notification_date, start, end, correction_start, correction_end, admit_card_date, exam_date, result_date, counseling_date}
  application_fee   JSONB,        -- {general, sc_st, obc, ews, female, pwd}
  application_link  TEXT,
  notification_pdf  TEXT,
  syllabus_link     TEXT,
  exam_pattern      JSONB,        -- {papers[], mode, duration, total_marks}
  selection_process TEXT,
  status            VARCHAR(20)   NOT NULL DEFAULT 'active' CHECK (status IN ('active','expired','upcoming')),
  is_featured       BOOLEAN       NOT NULL DEFAULT FALSE,
  views             INTEGER       NOT NULL DEFAULT 0,
  created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_admissions_slug        ON admissions (slug);
CREATE INDEX idx_admissions_status      ON admissions (status, created_at DESC);
CREATE INDEX idx_admissions_type        ON admissions (admission_type);
CREATE INDEX idx_admissions_featured    ON admissions (is_featured) WHERE is_featured = TRUE;
CREATE INDEX idx_admissions_eligibility ON admissions USING GIN (eligibility);
```

### 11. `yojanas` (Government Schemes) Table (NEW)
```sql
CREATE TABLE yojanas (
  id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  title               VARCHAR(300) NOT NULL,
  slug                VARCHAR(320) NOT NULL UNIQUE,
  yojana_type         VARCHAR(30)  NOT NULL CHECK (yojana_type IN ('central','state','scholarship','pension','subsidy','insurance','loan')),
  state               VARCHAR(100),
  department          VARCHAR(200),
  short_description   TEXT,
  full_description    TEXT,
  eligibility         TEXT,
  benefits            TEXT,
  benefit_amount      VARCHAR(100),
  installment_details TEXT,
  how_to_apply        TEXT,
  required_documents  TEXT[],
  application_link    TEXT,
  official_website    TEXT,
  guidelines_pdf      TEXT,
  helpline            VARCHAR(50),
  email               VARCHAR(200),
  start_date          DATE,
  last_date           DATE,
  is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
  status              VARCHAR(20)  NOT NULL DEFAULT 'active' CHECK (status IN ('active','expired','upcoming')),
  is_featured         BOOLEAN      NOT NULL DEFAULT FALSE,
  views               INTEGER      NOT NULL DEFAULT 0,
  applicants_count    BIGINT       NOT NULL DEFAULT 0,
  created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_yojanas_slug     ON yojanas (slug);
CREATE INDEX idx_yojanas_type     ON yojanas (yojana_type);
CREATE INDEX idx_yojanas_status   ON yojanas (status, is_active);
CREATE INDEX idx_yojanas_featured ON yojanas (is_featured) WHERE is_featured = TRUE;
```

### 12. `board_results` Table (NEW)
```sql
CREATE TABLE board_results (
  id                      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  board_name              VARCHAR(100) NOT NULL,    -- CBSE/UP Board/Bihar Board/RBSE/etc
  class                   VARCHAR(10)  NOT NULL,    -- 10th/12th/5th/8th
  stream                  VARCHAR(30),              -- Arts/Commerce/Science/All
  exam_year               INTEGER      NOT NULL,
  result_type             VARCHAR(30)  NOT NULL DEFAULT 'regular' CHECK (result_type IN ('regular','supplementary','compartment','improvement')),
  exam_start_date         DATE,
  exam_end_date           DATE,
  result_date             DATE,
  result_time             VARCHAR(20),
  result_link             TEXT,
  marksheet_download_link TEXT,
  topper_list_link        TEXT,
  date_sheet_link         TEXT,
  statistics              JSONB,        -- {total_students, passed_students, pass_percentage, girls_pass_percentage, boys_pass_percentage, distinction_count, first_division_count}
  how_to_check            TEXT,
  alternative_links       TEXT[],
  status                  VARCHAR(20)  NOT NULL DEFAULT 'active' CHECK (status IN ('active','expired')),
  views                   INTEGER      NOT NULL DEFAULT 0,
  created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_board_results_board      ON board_results (board_name);
CREATE INDEX idx_board_results_year       ON board_results (exam_year DESC);
CREATE INDEX idx_board_results_class      ON board_results (class, exam_year DESC);
CREATE INDEX idx_board_results_statistics ON board_results USING GIN (statistics);
```

### 13. `categories` (Organizations) Table (NEW)
```sql
CREATE TABLE categories (
  id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name             VARCHAR(200) NOT NULL,
  slug             VARCHAR(220) NOT NULL UNIQUE,
  parent_id        UUID         REFERENCES categories(id) ON DELETE SET NULL,
  type             VARCHAR(30)  NOT NULL CHECK (type IN ('organization','job_type','department','board')),
  icon             VARCHAR(100),
  description      TEXT,
  display_order    INTEGER      NOT NULL DEFAULT 0,
  is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
  job_count        INTEGER      NOT NULL DEFAULT 0,
  meta_title       VARCHAR(300),
  meta_description TEXT,
  created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_categories_slug   ON categories (slug);
CREATE INDEX idx_categories_type   ON categories (type) WHERE is_active = TRUE;
CREATE INDEX idx_categories_parent ON categories (parent_id);
CREATE INDEX idx_categories_order  ON categories (display_order, type);
```

### 14. `page_views` Table (Analytics - NEW)
```sql
CREATE TABLE page_views (
  id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type         VARCHAR(30)  NOT NULL CHECK (entity_type IN ('job','result','admit_card','admission','yojana','page')),
  entity_id           UUID,
  user_id             UUID         REFERENCES users(id) ON DELETE SET NULL,
  session_id          VARCHAR(100),
  ip_address          INET,
  user_agent          TEXT,
  device_type         VARCHAR(20)  CHECK (device_type IN ('desktop','mobile','tablet')),
  browser             VARCHAR(50),
  os                  VARCHAR(50),
  referrer            TEXT,
  page_url            TEXT,
  time_spent_seconds  INTEGER,
  viewed_at           TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_page_views_entity  ON page_views (entity_type, entity_id);
CREATE INDEX idx_page_views_user    ON page_views (user_id, viewed_at DESC);
CREATE INDEX idx_page_views_session ON page_views (session_id);
CREATE INDEX idx_page_views_date    ON page_views (viewed_at DESC);
```

### 15. `search_logs` Table (Analytics - NEW)
```sql
CREATE TABLE search_logs (
  id                          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                     UUID         REFERENCES users(id) ON DELETE SET NULL,
  session_id                  VARCHAR(100),
  search_query                VARCHAR(500) NOT NULL,
  filters_applied             JSONB,        -- {organization[], qualification[], state[], job_type[]}
  results_count               INTEGER      NOT NULL DEFAULT 0,
  clicked_results             UUID[],       -- array of entity UUIDs clicked
  first_click_position        INTEGER,
  time_to_first_click_seconds INTEGER,
  no_results                  BOOLEAN      NOT NULL DEFAULT FALSE,
  searched_at                 TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_search_logs_user           ON search_logs (user_id, searched_at DESC);
CREATE INDEX idx_search_logs_query          ON search_logs (search_query);
CREATE INDEX idx_search_logs_date           ON search_logs (searched_at DESC);
CREATE INDEX idx_search_logs_filters        ON search_logs USING GIN (filters_applied);
CREATE INDEX idx_search_logs_no_results     ON search_logs (no_results) WHERE no_results = TRUE;
```

### 16. `role_permissions` Table (RBAC Support)
```sql
CREATE TABLE role_permissions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role          VARCHAR(50) NOT NULL CHECK (role IN ('user','operator','admin')),
  resource      VARCHAR(100) NOT NULL,
  -- JSONB: {GET: true/false, POST: true/false, PUT: true/false, DELETE: true/false}
  actions       JSONB NOT NULL DEFAULT '{}',
  -- JSONB: array of field names restricted for this role
  field_restrictions JSONB NOT NULL DEFAULT '[]',
  is_enabled    BOOLEAN NOT NULL DEFAULT TRUE,
  is_restricted BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  UNIQUE (role, resource)
);

CREATE INDEX idx_role_permissions_role     ON role_permissions (role);
CREATE INDEX idx_role_permissions_enabled  ON role_permissions (is_enabled);
```

### 17. `access_audit_logs` Table (RBAC Audit Trail)
```sql
CREATE TABLE access_audit_logs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id      UUID NOT NULL REFERENCES users(id),
  action        VARCHAR(100) NOT NULL,   -- 'permission_changed','role_disabled','role_enabled'
  role          VARCHAR(50),
  resource      VARCHAR(100),
  -- JSONB: tracks what changed {field_name: {from: old_value, to: new_value}}
  changes       JSONB NOT NULL DEFAULT '{}',
  reason        TEXT,
  ip_address    INET,
  timestamp     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_access_audit_logs_admin     ON access_audit_logs (admin_id, timestamp DESC);
CREATE INDEX idx_access_audit_logs_role      ON access_audit_logs (role, timestamp DESC);
CREATE INDEX idx_access_audit_logs_timestamp ON access_audit_logs (timestamp DESC);
```

---

## 📊 Database Design Optimization

### ⚡ Indexing Strategy (CRITICAL for Performance)

**Problem**: Without proper indexes, queries scan entire tables (slow)

**Required Indexes** (create via Alembic migration or `init.sql`):

```sql
-- User queries
CREATE UNIQUE INDEX idx_users_email  ON users (email);
CREATE        INDEX idx_users_status ON users (status);

-- Job search queries (most critical - scanned frequently)
CREATE INDEX idx_jobs_organization ON job_vacancies (organization);
CREATE INDEX idx_jobs_status_date  ON job_vacancies (status, created_at DESC);
CREATE INDEX idx_jobs_app_end      ON job_vacancies (application_end_date);

-- Compound index for filtered + sorted queries
CREATE INDEX idx_jobs_org_status_date ON job_vacancies (organization, status, created_at DESC);

-- GIN indexes for JSONB containment queries
CREATE INDEX idx_jobs_eligibility      ON job_vacancies USING GIN (eligibility);
CREATE INDEX idx_profiles_education    ON user_profiles USING GIN (education);
CREATE INDEX idx_profiles_quick_filter ON user_profiles USING GIN (quick_filters);

-- Application tracking
CREATE UNIQUE INDEX idx_applications_user_job ON user_job_applications (user_id, job_id);
CREATE        INDEX idx_applications_user_date ON user_job_applications (user_id, applied_date DESC);

-- Notifications
CREATE INDEX idx_notif_user_read ON notifications (user_id, is_read);
CREATE INDEX idx_notif_user_date ON notifications (user_id, created_at DESC);

-- Cleanup: partial index for non-expired rows
CREATE INDEX idx_notif_expires  ON notifications (expires_at) WHERE expires_at IS NOT NULL;
```

**Impact**:
- ✅ `GET /api/v1/jobs?org=Railway&status=active` now uses `idx_jobs_org_status_date`
- ✅ Job listing query: 1000ms → 10ms (100x faster)
- ✅ JSONB containment `eligibility @> '{"qualification": "Graduate"}'` uses GIN index
- ✅ Cache hits improve (less database load)

### ⚡ Denormalization Strategy (Optional Optimization)

Some data is cached in `user_profiles` for faster queries:

```python
# Instead of joining user_profiles → job_vacancies just to send a notification,
# store a small cache directly on the profile row:
from app.extensions import db
from app.models import UserProfile

profile = UserProfile.query.filter_by(user_id=user_id).one()
profile.cached_job_matches = [
    {"job_id": str(job.id), "org": job.organization, "title": job.job_title}
    for job in matched_jobs[:20]
]
db.session.commit()
# Refresh this cache every 6 hours via Celery task
```

### Data Lifecycle & TTL

**Auto-Delete Old Data**:
PostgreSQL does not have native TTL indexes. Row expiry is handled via an `expires_at TIMESTAMP` column (set to `NOW() + INTERVAL 'N days'` at insert time) and a scheduled Celery beat task (or `pg_cron`) that runs daily to purge expired rows:

```python
# tasks/cleanup.py
@celery.task
def purge_expired_rows():
    db.session.execute(text("DELETE FROM notifications WHERE expires_at < NOW()"))
    db.session.execute(text("DELETE FROM admin_logs   WHERE expires_at < NOW()"))
    db.session.commit()
```

- Notifications: Delete after 90 days (`expires_at = NOW() + INTERVAL '90 days'`)
- Activity logs: Delete after 30 days (`expires_at = NOW() + INTERVAL '30 days'`)
- Failed email logs: Delete after 14 days

**Reduces**: Storage cost, query time, backup size

---

## API Endpoints

> **⚡ All endpoints use versioning format `/api/v1/`** to allow future compatibility with v2, v3, etc. without breaking existing clients.

### Authentication APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/auth/register` | User registration | Public |
| POST | `/api/v1/auth/login` | User login | Public |
| POST | `/api/v1/auth/logout` | User logout | Authenticated |
| POST | `/api/v1/auth/refresh` | Refresh JWT token | Authenticated |
| POST | `/api/v1/auth/forgot-password` | Password reset request | Public |
| POST | `/api/v1/auth/reset-password` | Reset password | Public |
| GET | `/api/v1/auth/verify-email/:token` | Email verification | Public |

### User Profile APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/users/profile` | Get user profile | User |
| PUT | `/api/v1/users/profile` | Update user profile | User |
| POST | `/api/v1/users/education` | Add education details | User |
| PUT | `/api/v1/users/education/:id` | Update education | User |
| GET | `/api/v1/users/preferences` | Get notification preferences | User |
| PUT | `/api/v1/users/preferences` | Update preferences | User |

### Job Vacancy APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/jobs` | Get all jobs (with filters) | Public |
| GET | `/api/v1/jobs/:id` | Get job details | Public |
| GET | `/api/v1/jobs/recommended` | Get personalized jobs | User |
| POST | `/api/v1/jobs/search` | Advanced job search | Public |
| GET | `/api/v1/jobs/organization/:org` | Jobs by organization | Public |

### Application APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/applications` | Mark job as applied | User |
| GET | `/api/v1/applications` | Get user's applications | User |
| GET | `/api/v1/applications/:id` | Get application details | User |
| PUT | `/api/v1/applications/:id/priority` | Toggle priority | User |
| PUT | `/api/v1/applications/:id/notes` | Update notes | User |
| DELETE | `/api/v1/applications/:id` | Remove application | User |

### Notification APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/notifications` | Get user notifications | User |
| PUT | `/api/v1/notifications/:id/read` | Mark as read | User |
| PUT | `/api/v1/notifications/read-all` | Mark all as read | User |
| DELETE | `/api/v1/notifications/:id` | Delete notification | User |

### Admin APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/admin/jobs` | Create new job | Admin |
| PUT | `/api/v1/admin/jobs/:id` | Update job | Admin |
| DELETE | `/api/v1/admin/jobs/:id` | Delete job | Admin |
| GET | `/api/v1/admin/users` | Get all users | Admin |
| PUT | `/api/admin/users/:id/status` | Update user status | Admin |
| GET | `/api/admin/analytics` | Get platform analytics | Admin |
| GET | `/api/admin/logs` | Get admin activity logs | Admin |

### Admin APIs

| Method | Endpoint | Description | Access | Pagination |
|--------|----------|-------------|--------|-----------|
| POST | `/api/v1/admin/jobs` | Create new job | Admin | N/A |
| PUT | `/api/v1/admin/jobs/:id` | Update job | Admin | N/A |
| DELETE | `/api/v1/admin/jobs/:id` | Delete job | Admin | N/A |
| GET | `/api/v1/admin/jobs` | Get all jobs | Admin | ✅ (limit/offset) |
| GET | `/api/v1/admin/users` | Get all users | Admin | ✅ (limit/offset) |
| GET | `/api/v1/admin/users/:id` | Get user details | Admin | N/A |
| PUT | `/api/v1/admin/users/:id/status` | Update user status | Admin | N/A |
| GET | `/api/v1/admin/analytics` | Get platform analytics | Admin | N/A |
| GET | `/api/v1/admin/logs` | Get admin activity logs | Admin | ✅ (limit/offset) |
| GET | `/api/v1/admin/system-health` | System health metrics | Admin | N/A |

🔔 **All Admin List Endpoints Support**:
```bash
GET /api/v1/admin/users?limit=50&offset=0
GET /api/v1/admin/jobs?limit=100&offset=100
GET /api/v1/admin/logs?limit=50&offset=0&filter=ERROR
```

---

## ⚠️ Standardized Error Codes & Response Format

**All API errors follow this format**:

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

### Authentication Errors (401)
```
AUTH_INVALID_CREDENTIALS        - Wrong email/password
AUTH_TOKEN_EXPIRED              - JWT access token expired, use refresh
AUTH_TOKEN_REVOKED              - Token invalidated (user logout)
AUTH_REFRESH_FAILED             - Refresh token expired, must login again
AUTH_EMAIL_NOT_VERIFIED         - Email verification pending
AUTH_ACCOUNT_SUSPENDED          - User account suspended
AUTH_MFA_REQUIRED               - Multi-factor authentication needed
```

### Validation Errors (400)
```
VALIDATION_EMAIL_EXISTS         - Email already registered
VALIDATION_EMAIL_INVALID        - Email format invalid
VALIDATION_PASSWORD_WEAK        - Password doesn't meet strength requirements
VALIDATION_MISSING_FIELD        - Required field missing
VALIDATION_INVALID_FORMAT       - Data format invalid (JSON, file type, etc.)
VALIDATION_FILE_TOO_LARGE       - Uploaded file exceeds size limit
```

### Authorization Errors (403)
```
FORBIDDEN_PERMISSION_DENIED     - User doesn't have permission
FORBIDDEN_ADMIN_ONLY            - Admin access required
FORBIDDEN_OWN_RESOURCE_ONLY     - Can only access own resources
```

### Resource Errors (404)
```
NOT_FOUND_USER                  - User doesn't exist
NOT_FOUND_JOB                   - Job doesn't exist
NOT_FOUND_APPLICATION           - Application not found
NOT_FOUND_ENDPOINT              - API endpoint doesn't exist
```

### Rate Limiting (429)
```
RATE_LIMIT_EXCEEDED             - Too many requests, retry after X seconds
RATE_LIMIT_LOGIN                - Too many login failures, account locked 5 min
```

### Server Errors (500)
```
SERVER_ERROR                    - Internal server error
SERVER_DATABASE_ERROR           - Database connection failed
SERVER_EXTERNAL_SERVICE_ERROR   - Email/FCM service failed
SERVER_CELERY_ERROR             - Background task failed
```

---

## 🔗 Request ID & Correlation Tracing

**Every request has a unique ID for debugging**:

```
┌──────────────────────────┐
│ Client Browser           │
│ Sends: POST /login       │
│ Header: X-Request-ID: r1 │
└────────────┬─────────────┘
             │ r1
             ↓
┌──────────────────────────┐
│ Nginx (Proxy)            │
│ Generates if missing     │
│ Forwards: X-Request-ID   │
└────────────┬─────────────┘
             │ r1
             ↓
┌──────────────────────────┐
│ Backend Flask            │
│ Adds to logs:            │
│ request_id: r1           │
│ Calls Auth Service       │
└────────────┬─────────────┘
             │ r1
             ↓
┌──────────────────────────┐
│ PostgreSQL               │
│ Stored with request_id   │
│ audit_trail.request_id   │
└──────────────────────────┘
```

**How to use**:
```bash
# Client sends request
curl -X POST http://api.example.com/auth/login \
  -H "X-Request-ID: req_abc123" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# Backend logs
{
  "timestamp": "2026-03-03T10:30:00Z",
  "level": "INFO",
  "message": "User login successful",
  "request_id": "req_abc123",
  "user_id": "123",
  "duration_ms": 245
}

# Search logs by request_id
curl "http://kibana:5601/elasticsearch?q=request_id:req_abc123"
# Shows: Frontend → Backend → Database → Email service flow
```

---

## ⏱️ API Response Time SLAs (Service Level Agreement)

**Target response times (p95 percentile)**:

| Endpoint Type | Target | Max | Category |
|---------------|--------|-----|----------|
| **Authentication** | < 100ms | 200ms | Fast |
| `/api/v1/auth/register` | 80ms | 150ms | User registration |
| `/api/v1/auth/login` | 95ms | 200ms | Login (2 DB queries) |
| `/api/v1/auth/refresh` | 50ms | 100ms | Token refresh |
| **Read Endpoints** | < 200ms | 500ms | Standard |
| `/api/v1/jobs` | 150ms | 400ms | Job listing (1000 docs) |
| `/api/v1/jobs/:id` | 50ms | 100ms | Single job |
| `/api/v1/users/profile` | 80ms | 150ms | User profile |
| `/api/v1/notifications` | 100ms | 200ms | Notifications |
| **Write Endpoints** | < 300ms | 600ms | Standard |
| `/api/v1/users/profile` (PUT) | 120ms | 250ms | Update profile |
| `/api/v1/applications` (POST) | 150ms | 300ms | Create application |
| **Search Endpoints** | < 500ms | 1000ms | Slow (Elasticsearch) |
| `/api/v1/jobs/search` | 300ms | 800ms | Full-text search |
| **Admin Endpoints** | < 1000ms | 2000ms | Heavy queries |
| `/api/v1/admin/analytics` | 500ms | 1500ms | Aggregation needed |
| `/api/v1/admin/users` | 700ms | 1500ms | Large dataset |


---

## 🔄 Graceful Degradation Strategy

**When external services fail, app continues working**:

### Email Service Failure
```
❌ SMTP server down
↓
✅ Queue email in Redis (retry queue)
✅ Respond to user: "Notification queued"
✅ Background job retries 5 times (wait: 1s, 2s, 4s, 8s, 16s)
✅ If still failing after 5 retries: Alert admin, disable email temporarily
✅ User still gets in-app notification
```

### Firebase Push Notification Failure
```
❌ FCM service down
↓
✅ Fall back to in-app notification (stored in PostgreSQL)
✅ Email user as backup
✅ Alert: "Notifications temporarily via email"
✅ Auto-retry FCM when service recovers
```

### Database Slow (> 50ms)
```
❌ PostgreSQL query taking 500ms
↓
✅ Return cached data from Redis (if available)
✅ Add header: "X-Cache: STALE_DATA, from_cache=true"
✅ Alert: "DB performance degraded"
✅ Frontend shows: "Showing cached data (refreshed 5 min ago)"
```

### Celery Down (Background Tasks)
```
❌ Celery worker not responding
↓
✅ Accept job but don't block response
✅ Queue in Redis directly
✅ Respond to user: "Job queued, will process when available"
✅ When Celery recovers: Process queued jobs in order
✅ Alert: "Background processing delayed"
```

### Database Connection Pool Exhausted
```
❌ All 50 connections used, new request waiting
↓
✅ Queue request (max wait: 10 seconds)
✅ If timeout: Return 503 Service Unavailable
✅ User retries after 5 seconds (exponential backoff)
✅ Alert: "DB connection pool exhausted"
```

---

## 💡 API & Communication Standards

### ⚡ Pagination Strategy

**All list endpoints MUST support pagination**:

```bash
# Limit/Offset Pagination (good for small datasets)
GET /api/v1/notifications?limit=20&offset=0
{
  "data": [...20 notifications...],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 500,
    "has_more": true
  }
}

# Cursor-based Pagination (efficient for large datasets)
GET /api/v1/jobs?limit=20&cursor=eyJpZCI6IjYzZjAwYjEyIn0=
{
  "data": [...20 jobs...],
  "pagination": {
    "next_cursor": "eyJpZCI6IjYzZjAwYjEyfSI=",
    "has_more": true
  }
}
```

**Use cursor-based for**: Job listings (50K+ records)  
**Use limit/offset for**: Notifications, applications (< 10K records)

### ⚡ Standardized Error Responses

**All errors MUST follow this format**:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is invalid",
    "details": [
      {"field": "email", "issue": "Invalid email format"}
    ],
    "timestamp": "2026-03-03T10:30:00Z",
    "request_id": "req_123abc456"
  }
}
```

**HTTP Status Codes**:
- 200 OK, 201 Created
- 400 Bad Request (validation error)
- 401 Unauthorized (missing/invalid auth)
- 403 Forbidden (no permission)
- 404 Not Found
- 429 Too Many Requests (rate limit)
- 500 Server Error

### ⚡ Request Timeout & Retry Logic

**Frontend auto-retries** on transient failures:

```python
# Exponential backoff: 2s, 4s, 8s
request_with_retry(
    method="GET",
    endpoint="/jobs",
    max_retries=3,
    timeout=10
)
```

**Benefits**: Network hiccups auto-recover, users don't see "network error"

### ⚡ Notification Retry Strategy

**Failed emails auto-retry** (5 attempts, exponential backoff):

```python
@app.task(base=CallbackTask)
def send_email_notification(user_id, job_id):
    # Celery auto-retries on failure
    # Delays: 1s, 2s, 4s, 8s, 16s
    try:
        mail.send(notification_email)
    except SMTPException as exc:
        raise self.retry(exc=exc)
```

**Prevents**: Email notifications silently failing

---

## Key Features Implementation

---

## 🎯 Database Design & Optimization

### ⚡ Indexing Strategy for PostgreSQL

**B-tree Indexes** (scalar columns):

```sql
CREATE INDEX idx_jobs_posted_date  ON job_vacancies (created_at DESC);
CREATE INDEX idx_jobs_category     ON job_vacancies (category_id);
CREATE INDEX idx_jobs_exam_status  ON job_vacancies (exam_name, status);
```

**GIN Indexes** (JSONB containment queries):

```sql
-- Fast containment queries on flexible nested data
CREATE INDEX idx_jobs_eligibility_gin   ON job_vacancies   USING GIN (eligibility);
CREATE INDEX idx_profiles_education_gin ON user_profiles   USING GIN (education);
CREATE INDEX idx_search_filters_gin     ON search_logs     USING GIN (filters_applied);
```

**Row Cleanup** (PostgreSQL `expires_at` + Celery nightly purge):

```sql
-- expires_at column set at INSERT time; purged nightly by Celery task
ALTER TABLE notifications ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE
  DEFAULT (NOW() + INTERVAL '90 days');
ALTER TABLE admin_logs    ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE
  DEFAULT (NOW() + INTERVAL '30 days');
```

### ⚡ Denormalization Strategy (Optional for Scale)

**Problem**: Querying user profile + all applied jobs requires 2 queries  
**Solution**: Store job summary inside `user_profiles.cached_job_matches` (JSONB):

```python
# SQLAlchemy – store denormalized summary on user_profiles row
profile = UserProfile.query.filter_by(user_id="123").one()
profile.cached_job_matches = [
    {"job_id": "456", "company": "UPSC", "position": "IAS", "status": "applied"}
]
db.session.commit()
```

**When to use**: Only if >1000 queries/minute on user profiles

### ⚡ Data Lifecycle & TTL Management

| Table | Retention | Mechanism |
|-------|-----------|-----------|
| notifications | 90 days | `expires_at` column + nightly Celery purge |
| admin_logs | 30 days | `expires_at` column + nightly Celery purge |
| email_events | 60 days | `expires_at` column + nightly Celery purge |
| audit_trail | 1 year | Manual archive via pg_dump partition |

---


## Key Features Implementation

### 1. Intelligent Job Matching Algorithm

```python
def match_job_with_user(job, user_profile):
    """
    Matches a job vacancy with user profile based on eligibility criteria
    Returns: (is_eligible, match_score)
    """
    score = 0
    
    # Education matching
    if check_education_eligibility(job.eligibility, user_profile.education):
        score += 40
    else:
        return (False, 0)
    
    # Age verification
    if check_age_eligibility(job.eligibility.age_limit, user_profile.personal_info):
        score += 20
    else:
        return (False, 0)
    
    # Category preference
    if user_profile.personal_info.category in job.eligibility.category_wise_vacancies:
        score += 10
    
    # Organization preference
    if job.organization in user_profile.notification_preferences.organizations:
        score += 20
    
    # Location preference
    if job.location in user_profile.notification_preferences.locations:
        score += 10
    
    return (True, score)
```

### 2. Notification Trigger System

**Triggers for Notifications:**

1. **New Job Posted**: When a new job matching user's profile is created
2. **Application Deadline**: 7 days, 3 days, 1 day before deadline
3. **Admit Card Release**: When admit card dates are announced
4. **Exam Date Reminder**: 7 days, 3 days, 1 day before exam
5. **Result Announcement**: When results are declared
6. **Priority Job Updates**: Any update on jobs marked as priority

### 3. Background Job Scheduler (Celery Tasks)

```python
# Daily job matching task
@celery.task
def daily_job_matching():
    """Run daily to match new jobs with users"""
    new_jobs = get_jobs_created_in_last_24_hours()
    users = get_all_active_users()
    
    for job in new_jobs:
        for user in users:
            if match_job_with_user(job, user.profile)[0]:
                send_job_notification(user, job)

# Reminder tasks
@celery.task
def send_deadline_reminders():
    """Check and send reminders for upcoming deadlines"""
    applications = get_applications_with_pending_reminders()
    
    for app in applications:
        check_and_send_reminders(app)
```

### 4. Flask-Mail Email Service

```python
from flask_mail import Mail, Message

mail = Mail(app)

def send_job_notification_email(user, job):
    """Send job notification via Flask-Mail"""
    msg = Message(
        subject=f"New Job Alert: {job.job_title}",
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )
    
    msg.html = render_template(
        'emails/job_notification.html',
        user=user,
        job=job
    )
    
    mail.send(msg)

def send_reminder_email(user, application, reminder_type):
    """Send application reminder via Flask-Mail"""
    msg = Message(
        subject=f"Reminder: {reminder_type} for {application.job.job_title}",
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )
    
    msg.html = render_template(
        'emails/reminder.html',
        user=user,
        application=application,
        reminder_type=reminder_type
    )
    
    mail.send(msg)
```

## Admin Panel Features

> Admin and operator users log in at `http://localhost:8081` (`src/frontend-admin/`), not through the public user frontend.

### Dashboard
- Total users, active jobs, total applications
- Recent activity feed
- Analytics graphs (daily registrations, applications)
- Popular jobs
- User engagement metrics

### Job Management
- Create/Edit/Delete job vacancies
- Bulk upload jobs via CSV/Excel
- Job status management (active/closed/cancelled)
- Clone existing job posting
- Schedule job posting for future date

### User Management
- View all users
- User details and activity
- Ban/Unban users
- Export user data
- View user applications

### Analytics
- User demographics
- Popular organizations
- Application trends
- Notification delivery stats
- Platform usage metrics

### Content Management
- Manage static pages (About, Contact, FAQ)
- Manage email templates
- Notification templates
- Banner/Advertisement management

## 👥 User & Role Management

### Three-Role System

| Role | Type | Can Create Jobs | Can Review Jobs | Logs in via |
|------|------|-----------------|-----------------|-------------|
| **User** | Job Seeker | ❌ | ❌ | `src/frontend/` (port 8080) |
| **Operator** | Content Reviewer | ❌ | ✅ | `src/frontend-admin/` (port 8081) |
| **Admin** | Full Control | ✅ | ✅ | `src/frontend-admin/` (port 8081) |

### Creating Admin (First Time Bootstrap)

**Option A: PostgreSQL Direct Insert (Recommended)**

```bash
# Connect to PostgreSQL
docker compose exec postgresql psql -U hermes_user -d hermes_db

-- Create admin user directly
INSERT INTO users (email, password_hash, full_name, role, is_verified, is_email_verified, status, created_at, last_login)
VALUES (
  'admin@example.com',
  '$2b$12$HASHED_PASSWORD_HERE',  -- Use bcrypt hash
  'Admin User',
  'admin',
  TRUE,
  TRUE,
  'active',
  NOW(),
  NOW()
);

\q
```

**Option B: Register Then Promote**

```bash
# 1. Register via API (creates user with role='user')
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePassword123!",
    "name": "Admin User"
  }'

# 2. Promote to admin (via psql)
docker compose exec postgresql psql -U hermes_user -d hermes_db
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
\q
```

### Creating Operators (Admin-Only)

**API Endpoint:** `PUT /api/v1/admin/users/<user_id>/role`

```bash
# Promotion request (from admin account)
curl -X PUT http://localhost:5000/api/v1/admin/users/USER_ID/role \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_role": "operator"}'
```

**Response:**
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "email": "operator@example.com",
  "role": "operator",
  "updated_at": "2026-03-03T10:30:00Z"
}
```

### Permission Matrix by Endpoint

| Endpoint | User | Operator | Admin |
|----------|------|----------|-------|
| `GET /api/v1/jobs` | ✅ | ✅ | ✅ |
| `POST /api/v1/jobs` | ❌ | ❌ | ✅ |
| `PUT /api/v1/jobs/<id>` | ❌ | ✅ (limited) | ✅ |
| `DELETE /api/v1/jobs/<id>` | ❌ | ❌ | ✅ |
| `GET /api/v1/admin/users` | ❌ | ❌ | ✅ |
| `PUT /api/v1/admin/users/<id>/role` | ❌ | ❌ | ✅ |
| `GET /api/v1/admin/analytics` | ❌ | ❌ | ✅ |

**Note:** Operators have restricted field updates - they can modify `status` and `description` but NOT `salary` or `vacancy_count`.

---

## 🔐 Dynamic Access Management System

### Overview

Admins can **dynamically enable/disable access** for roles without restarting the app. Permissions are stored in PostgreSQL and checked on every API request.

**Example Use Cases:**
- Temporarily disable "Operator" access to sensitive endpoints during maintenance
- Grant "User" role temporary access to download job list (CSV export)
- Restrict "Admin" delete operations for audit compliance
- Enable/disable entire feature sets (like notifications) per role

### Access Control Database Schema

**Tables Created:**

#### 1. `role_permissions` Table

Stores which actions each role can perform:

```sql
CREATE TABLE role_permissions (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  role              VARCHAR(20) NOT NULL CHECK (role IN ('user','operator','admin')),
  resource          VARCHAR(50) NOT NULL,
  actions           JSONB       NOT NULL,       -- {"GET": true, "POST": false, "PUT": true, "DELETE": false}
  field_restrictions TEXT[]     NOT NULL DEFAULT '{}',
  is_enabled        BOOLEAN     NOT NULL DEFAULT TRUE,
  is_restricted     BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  UNIQUE (role, resource)
);
CREATE INDEX idx_role_permissions_role ON role_permissions (role, resource);
```

#### 2. `access_audit_logs` Table

Log every permission change for compliance:

```sql
CREATE TABLE access_audit_logs (
  id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id    UUID         NOT NULL REFERENCES users(id),
  action      VARCHAR(50)  NOT NULL,
  role        VARCHAR(20)  NOT NULL,
  resource    VARCHAR(50),
  changes     JSONB,
  reason      TEXT,
  ip_address  INET,
  timestamp   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_logs_role  ON access_audit_logs (role, timestamp DESC);
CREATE INDEX idx_audit_logs_admin ON access_audit_logs (admin_id, timestamp DESC);
```

### Admin API Endpoints for Access Management

#### 1. Get Current Permissions for a Role

**Endpoint:** `GET /api/v1/admin/permissions?role=operator`

**Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/admin/permissions?role=operator" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
{
  "role": "operator",
  "permissions": [
    {
      "resource": "jobs",
      "actions": {"GET": true, "POST": false, "PUT": true, "DELETE": false},
      "field_restrictions": ["salary_min", "salary_max"]
    },
    {
      "resource": "users",
      "actions": {"GET": true, "POST": false, "PUT": false, "DELETE": false},
      "field_restrictions": ["password", "email"]
    },
    {
      "resource": "admin",
      "actions": {"GET": false, "POST": false, "PUT": false, "DELETE": false}
    }
  ]
}
```

#### 2. Update Permissions for a Role

**Endpoint:** `PUT /api/v1/admin/permissions`

**Request:**
```bash
curl -X PUT http://localhost:5000/api/v1/admin/permissions \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "operator",
    "resource": "jobs",
    "actions": {
      "GET": true,
      "POST": false,
      "PUT": true,
      "DELETE": false
    },
    "field_restrictions": ["salary_min", "salary_max", "vacancy_count"],
    "reason": "Restrict delete operations for compliance"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Permissions updated for operator role",
  "permission_id": "507f1f77bcf86cd799439012",
  "updated_at": "2026-03-03T10:30:00Z"
}
```

#### 3. Disable All Access for a Role (Emergency)

**Endpoint:** `POST /api/v1/admin/permissions/disable-role`

**Request:**
```bash
curl -X POST http://localhost:5000/api/v1/admin/permissions/disable-role \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "operator",
    "reason": "Security breach detected - disabling until investigation complete"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "All permissions disabled for operator role",
  "reason": "Security breach detected - disabling until investigation complete",
  "timestamp": "2026-03-03T10:30:00Z"
}
```

#### 4. View Permission Change History

**Endpoint:** `GET /api/v1/admin/permissions/audit-log?role=operator&limit=50`

**Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/admin/permissions/audit-log?role=operator" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
{
  "audit_logs": [
    {
      "timestamp": "2026-03-03T10:30:00Z",
      "admin_email": "admin@example.com",
      "action": "permission_changed",
      "role": "operator",
      "resource": "jobs",
      "changes": {
        "DELETE": {"from": true, "to": false}
      },
      "reason": "Restrict delete operations for compliance"
    },
    {
      "timestamp": "2026-03-02T15:20:00Z",
      "admin_email": "admin@example.com",
      "action": "role_disabled",
      "role": "operator",
      "reason": "Temporary disable during maintenance"
    }
  ],
  "total": 45,
  "limit": 50
}
```

### Implementation Code

#### 1. Database Model for Permissions

**backend/app/models/permissions.py:**

```python
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY
import uuid
from datetime import datetime

class RolePermission(db.Model):
    """Store role-based permissions in PostgreSQL"""
    __tablename__ = 'role_permissions'

    id                = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role              = db.Column(db.String(20), nullable=False)
    resource          = db.Column(db.String(50), nullable=False)
    actions           = db.Column(JSONB, nullable=False, default=dict)
    field_restrictions = db.Column(ARRAY(db.Text), nullable=False, default=list)
    is_enabled        = db.Column(db.Boolean, nullable=False, default=True)
    is_restricted     = db.Column(db.Boolean, nullable=False, default=False)
    created_at        = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('role', 'resource', name='uq_role_resource'),
    )


class AccessAuditLog(db.Model):
    """Log all permission changes for compliance"""
    __tablename__ = 'access_audit_logs'

    id         = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id   = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    action     = db.Column(db.String(50), nullable=False)
    role       = db.Column(db.String(20), nullable=False)
    resource   = db.Column(db.String(50))
    changes    = db.Column(JSONB)
    reason     = db.Column(db.Text)
    ip_address = db.Column(INET)
    timestamp  = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
```

#### 2. Permission Checking Middleware

**backend/app/middleware/permission_middleware.py:**

```python
from flask import request, abort, g
from functools import wraps
from flask_jwt_extended import get_jwt
from app.models import RolePermission
import logging

logger = logging.getLogger(__name__)

def check_access(resource, required_action='GET'):
    """
    Decorator to check if role has permission for resource/action
    
    Usage:
        @bp.route('/api/v1/jobs', methods=['GET'])
        @check_access('jobs', 'GET')
        def list_jobs():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role', 'user')
            
            # Get permission from cache or database
            permission = get_permission(user_role, resource)
            
            if not permission:
                logger.warning(f"Permission not found: role={user_role}, resource={resource}")
                return {'error': 'FORBIDDEN_NO_PERMISSION'}, 403
            
            # Check if role is disabled
            if not permission.is_enabled:
                logger.warning(f"Role {user_role} is disabled")
                return {'error': 'FORBIDDEN_ROLE_DISABLED'}, 403
            
            # Check if action is allowed
            actions = permission.actions
            if not actions.get(required_action, False):
                logger.warning(f"Action not allowed: {user_role} cannot {required_action} {resource}")
                return {'error': 'FORBIDDEN_ACTION_NOT_ALLOWED'}, 403
            
            # Check field restrictions
            g.field_restrictions = permission.field_restrictions
            
            return fn(*args, **kwargs)
        
        return wrapped
    return decorator

def get_permission(role, resource):
    """Get permission from Redis cache or PostgreSQL"""
    from app import cache

    cache_key = f"perm:{role}:{resource}"

    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Fetch from database
    perm = RolePermission.query.filter_by(role=role, resource=resource).first()

    if perm:
        # Cache for 1 hour
        cache.set(cache_key, perm, 3600)

    return perm

def invalidate_permission_cache(role, resource):
    """Clear cache when permissions change"""
    from app import cache
    cache.delete(f"perm:{role}:{resource}")
```

#### 3. Admin Routes for Permission Management

**backend/app/routes/permissions.py:**

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime
from functools import wraps
from app.models import RolePermission, AccessAuditLog
from app.extensions import db
from app.middleware import invalidate_permission_cache
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('permissions', __name__, url_prefix='/api/v1/admin/permissions')

def require_admin(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return {'error': 'FORBIDDEN_ADMIN_ONLY'}, 403
        return fn(*args, **kwargs)
    return wrapped

@bp.route('', methods=['GET'])
@jwt_required()
@require_admin
def get_permissions():
    """Get all permissions or permissions for specific role"""
    role = request.args.get('role')
    resource = request.args.get('resource')

    query = RolePermission.query

    if role:
        query = query.filter_by(role=role)
    if resource:
        query = query.filter_by(resource=resource)

    permissions = [
        {
            'id': str(p.id),
            'role': p.role,
            'resource': p.resource,
            'actions': p.actions,
            'field_restrictions': p.field_restrictions,
            'is_enabled': p.is_enabled,
            'updated_at': p.updated_at.isoformat()
        }
        for p in query.all()
    ]

    return jsonify({'permissions': permissions}), 200

@bp.route('', methods=['PUT'])
@jwt_required()
@require_admin
def update_permissions():
    """Update permissions for a role"""
    data = request.json
    role = data.get('role')
    resource = data.get('resource')
    actions = data.get('actions', {})
    field_restrictions = data.get('field_restrictions', [])
    reason = data.get('reason', 'No reason provided')
    
    # Validate
    if not role or not resource:
        return {'error': 'VALIDATION_MISSING_FIELD'}, 400

    if role not in ['user', 'operator', 'admin']:
        return {'error': 'VALIDATION_INVALID_ROLE'}, 400

    # Get or create permission
    perm = RolePermission.query.filter_by(role=role, resource=resource).first()

    if perm:
        old_actions = perm.actions
        perm.actions = actions
        perm.field_restrictions = field_restrictions
        perm.updated_at = datetime.utcnow()
        db.session.add(AccessAuditLog(
            admin_id=get_jwt()['sub'],
            action='permission_changed',
            role=role,
            resource=resource,
            changes={'actions': {'from': old_actions, 'to': actions}},
            reason=reason,
            ip_address=request.remote_addr
        ))
    else:
        perm = RolePermission(
            role=role,
            resource=resource,
            actions=actions,
            field_restrictions=field_restrictions
        )
        db.session.add(perm)
        db.session.add(AccessAuditLog(
            admin_id=get_jwt()['sub'],
            action='permission_created',
            role=role,
            resource=resource,
            reason=reason,
            ip_address=request.remote_addr
        ))

    db.session.commit()

    # Invalidate cache
    invalidate_permission_cache(role, resource)

    return {
        'status': 'success',
        'permission_id': str(perm.id),
        'updated_at': perm.updated_at.isoformat()
    }, 200

@bp.route('/disable-role', methods=['POST'])
@jwt_required()
@require_admin
def disable_role():
    """Disable all access for a role (emergency)"""
    data = request.json
    role = data.get('role')
    reason = data.get('reason', 'Emergency disable')
    
    if not role:
        return {'error': 'VALIDATION_MISSING_FIELD'}, 400

    # Disable all permissions for this role
    RolePermission.query.filter_by(role=role).update({'is_enabled': False})
    db.session.add(AccessAuditLog(
        admin_id=get_jwt()['sub'],
        action='role_disabled',
        role=role,
        reason=reason,
        ip_address=request.remote_addr
    ))
    db.session.commit()

    # Clear all caches for this role
    from app import cache
    for resource in ['jobs', 'users', 'applications', 'admin', 'notifications']:
        cache.delete(f"perm:{role}:{resource}")

    logger.critical(f"Role {role} disabled by admin {get_jwt()['sub']}: {reason}")

    return {
        'status': 'success',
        'message': f'All permissions disabled for {role} role'
    }, 200

@bp.route('/enable-role', methods=['POST'])
@jwt_required()
@require_admin
def enable_role():
    """Re-enable access for a disabled role"""
    data = request.json
    role = data.get('role')
    reason = data.get('reason', 'Re-enabling role')
    
    if not role:
        return {'error': 'VALIDATION_MISSING_FIELD'}, 400

    # Enable all permissions for this role
    RolePermission.query.filter_by(role=role).update({'is_enabled': True})
    db.session.add(AccessAuditLog(
        admin_id=get_jwt()['sub'],
        action='role_enabled',
        role=role,
        reason=reason,
        ip_address=request.remote_addr
    ))
    db.session.commit()

    logger.info(f"Role {role} re-enabled by admin {get_jwt()['sub']}")

    return {
        'status': 'success',
        'message': f'All permissions enabled for {role} role'
    }, 200

@bp.route('/audit-log', methods=['GET'])
@jwt_required()
@require_admin
def get_audit_log():
    """Get permission change history"""
    role = request.args.get('role')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    query = AccessAuditLog.query

    if role:
        query = query.filter_by(role=role)

    total = query.count()
    logs  = query.order_by(AccessAuditLog.timestamp.desc()).offset(offset).limit(limit).all()

    return jsonify({
        'audit_logs': [
            {
                'timestamp': log.timestamp.isoformat(),
                'admin_id': str(log.admin_id),
                'action': log.action,
                'role': log.role,
                'resource': log.resource,
                'changes': log.changes,
                'reason': log.reason
            }
            for log in logs
        ],
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200
```

#### 4. Using the Permission Decorator in Routes

**backend/app/routes/jobs.py:**

```python
from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.middleware import check_access

bp = Blueprint('jobs', __name__, url_prefix='/api/v1/jobs')

@bp.route('', methods=['GET'])
@jwt_required()
@check_access('jobs', 'GET')
def list_jobs():
    """List all jobs - permission checked"""
    # Only reaches here if user has GET access to jobs
    return {'jobs': []}, 200

@bp.route('', methods=['POST'])
@jwt_required()
@check_access('jobs', 'POST')
def create_job():
    """Create job - permission checked"""
    # Only admins reach here
    return {'status': 'created'}, 201

@bp.route('/<job_id>', methods=['PUT'])
@jwt_required()
@check_access('jobs', 'PUT')
def update_job(job_id):
    """Update job - permission checked"""
    # Admin or operator with PUT permission reaches here
    return {'status': 'updated'}, 200

@bp.route('/<job_id>', methods=['DELETE'])
@jwt_required()
@check_access('jobs', 'DELETE')
def delete_job(job_id):
    """Delete job - permission checked"""
    # Only admin with DELETE permission
    return {'status': 'deleted'}, 204
```

### Real-World Scenarios

#### Scenario 1: Maintenance Mode

Temporarily disable user access:

```bash
curl -X POST http://localhost:5000/api/v1/admin/permissions/disable-role \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "reason": "System maintenance - disabling user access for 2 hours"
  }'

# After maintenance, re-enable:
curl -X POST http://localhost:5000/api/v1/admin/permissions/enable-role \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "user"}'
```

#### Scenario 2: Restrict Delete Operations

Remove delete access from operators:

```bash
curl -X PUT http://localhost:5000/api/v1/admin/permissions \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "operator",
    "resource": "jobs",
    "actions": {
      "GET": true,
      "POST": false,
      "PUT": true,
      "DELETE": false
    },
    "reason": "Compliance requirement - operators cannot delete jobs"
  }'
```

#### Scenario 3: Audit Permission Changes

```bash
curl -X GET "http://localhost:5000/api/v1/admin/permissions/audit-log?role=operator&limit=100" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Response shows who changed what and when:
# [
#   {"timestamp": "...", "admin_email": "...", "action":  "permission_changed", "changes": {...}},
#   {"timestamp": "...", "admin_email": "...", "action":  "role_disabled", "reason": "..."}
# ]
```

## Security Features

### 🔐 Authentication & Authorization
1. **Password Security**: bcrypt hashing (salted, resistant to rainbow tables)
2. **JWT Authentication**: Token-based API auth (stateless, scalable)
3. **Token Rotation**: Access tokens expire in 15 minutes, refresh tokens in 7 days
   - Compromised tokens only valid for ~15 minutes max
   - Frontend auto-refreshes without user logout
4. **Role-Based Access Control (RBAC)**: User/Admin/Operator roles
   - Admin only: Create/delete jobs, view all users, analytics
   - User only: View own profile, apply for jobs
   - Operator: Update job details, review content
5. **Session Management**: Redis-backed sessions with timeout

### 🌐 API Security
6. **Rate Limiting**: 
   - Nginx: 100 req/min per IP (prevents bots)
   - Backend: 1000 req/min per authenticated user (prevents abuse)
   - Login: 5 attempts per minute (prevents brute force)
7. **CORS Configuration**: Only whitelelist origins can access API
   - Frontend origin must be explicitly allowed
   - Credentials only sent to trusted domains
   - Preflight requests cached (reduces overhead)
8. **Input Validation**: All user inputs sanitized
   - Email validation (RFC 5322)
   - Password requirements enforced (min 12 chars, special chars)
   - Job descriptions escape HTML/JavaScript
9. **API Versioning**: `/api/v1/` allows v2 without breaking v1 clients

### 🔒 Data Protection
10. **PostgreSQL Auth**: Username/password authentication (`pg_hba.conf`, `SQLALCHEMY_DATABASE_URI`)
11. **Redis Auth**: Password protected (requirepass enforced)
12. **HTTPS/SSL**: Let's Encrypt certificates (TLSv1.2+)
    - Automatic renewal (certbot)
    - HSTS headers (force HTTPS)
13. **Secrets Management**:
    - Development: .env file (in .gitignore)
    - Production: HashiCorp Vault / AWS Secrets Manager
    - Never commit secrets to git
14. **Database Indexing**: Prevents data enumeration attacks

### 🛡️ Defensive Headers
15. **X-Frame-Options**: Prevents clickjacking (SAMEORIGIN)
16. **X-Content-Type-Options**: Prevents MIME sniffing (nosniff)
17. **X-XSS-Protection**: Enables browser XSS filter (1; mode=block)
18. **Content-Security-Policy**: Restricts resource loading
19. **Strict-Transport-Security**: Forces HTTPS for 1 year
20. **Referrer-Policy**: Controls referrer information (no-referrer-when-downgrade)


## Deployment Options

### ⭐ Option 1: Docker Microservices (Recommended)

**Containerized Architecture:**
- 🐳 **8 Core Containers**: Nginx Reverse Proxy, User Frontend, Admin Frontend, Backend API, PostgreSQL, Redis, Celery Worker, Celery Beat
- ✅ **10-minute setup** vs 2-hour manual installation
- ✅ **Independent scaling** — Scale each service separately
- ✅ **Zero-downtime updates** — Update services without full restart
- ✅ **Built-in health checks** and auto-restart
- ✅ **Security isolation** — Admin frontend on separate port (can be firewalled)

**Quick Start:**
```bash
git clone https://github.com/SumanKr7/hermes.git
cd hermes

# Start backend (PostgreSQL, Redis, API, Celery)
cd src/backend && cp .env.example .env && docker-compose up -d --build && cd ../..

# Start user frontend (port 8080)
cd src/frontend && cp .env.example .env && docker-compose up -d --build && cd ../..

# Start admin frontend (port 8081)
cd src/frontend-admin && cp .env.example .env && docker-compose up -d --build && cd ../..

# Access
# User site:   http://localhost:8080
# Admin panel: http://localhost:8081
# Backend API: http://localhost:5000/api/v1/health
```

**Each service has its own docker-compose.yml and Docker network. They call each other via `BACKEND_API_URL` environment variable.**

📘 **Complete Docker Guide**: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)

### Option 2: Production Deployment with Let's Encrypt SSL

Same three-service architecture (Backend + User Frontend + Admin Frontend) with SSL certificates from Let's Encrypt.

**Docker-based**: Nginx is included in `src/nginx/docker-compose.yml`. It connects to all three Docker networks (`src_backend_network`, `src_frontend_network`, `src_frontend_admin_network`). Configure SSL in `src/nginx/nginx.conf`.

**Host-based**: Install Nginx on host machine and use certbot for automatic SSL renewal. Proxy `/*` → port 8080, `/api/*` → port 5000, `admin.yourdomain.com/*` → port 8081.

---

## Deployment Architecture

### Docker Microservices Architecture (Recommended)

```
┌───────────────────────────────────────────────────────────────────┐
│                     Hostinger VPS + Docker                        │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              Nginx Container (Port 80/443)                │   │
│  │      - SSL/TLS Termination (Let's Encrypt)                │   │
│  │      - Reverse Proxy & Load Balancing                     │   │
│  │      - Rate Limiting & Security Headers                   │   │
│  └────────┬──────────────────────┬───────────────────┬───────┘   │
│           │                      │                   │            │
│    /api/* │               /*     │   admin.domain/*  │            │
│           ↓                      ↓                   ↓            │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │ Backend        │  │ User Frontend    │  │ Admin Frontend │   │
│  │ Container      │◄─│ Container        │  │ Container      │   │
│  │ (Flask API)    │  │ (Flask+Jinja2)   │◄─│ (Flask+Jinja2) │   │
│  │ Port 5000      │  │ Port 8080        │  │ Port 8081      │   │
│  │ - JWT Auth ✅  │  │ - Public users   │  │ - Admin only   │   │
│  │ - RBAC ✅      │  │ - Register/Login │  │ - Dashboard    │   │
│  │ - Job Matching │  │ - Job browsing   │  │ - Job mgmt     │   │
│  └───────┬────────┘  └──────────────────┘  └────────────────┘   │
│          │                                                        │
│  ┌───────┼─────────────────────────────────────────────────┐    │
│  │  ┌────▼─────┐  ┌──────────┐  ┌──────────┐  ┌──────┐   │    │
│  │  │PostgreSQL│  │  Redis   │  │  Celery  │  │Celery│   │    │
│  │  │ Port5432 │  │ Port6379 │  │  Worker  │  │ Beat │   │    │
│  │  │ hermes_db│  │ blocklist│  │- Emails  │  │-Cron │   │    │
│  │  │ 15 tables│  │ cache    │  │- Notify  │  │Tasks │   │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────┘   │    │
│  │         src_backend_network                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  src_frontend_network       src_frontend_admin_network           │
│  Volumes: postgresql_data, redis_data, backend_logs              │
└───────────────────────────────────────────────────────────────────┘

        Internet ↕️ HTTPS (Port 443)
```

### Traditional VPS Deployment

```
┌─────────────────────────────────────────────────────────┐
│              Hostinger VPS Server                       │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Nginx (Reverse Proxy + SSL)                      │ │
│  │  - Port 80/443                                    │ │
│  │  - SSL Certificate (Let's Encrypt)               │ │
│  └─────────────────┬─────────────────────────────────┘ │
│                    │                                    │
│       ┌────────────┼────────────┐                      │
│       │            │            │                      │
│  ┌────▼────┐  ┌────▼────┐  ┌───▼─────┐               │
│  │ Gunicorn│  │ Gunicorn│  │ Gunicorn│               │
│  │ Worker 1│  │ Worker 2│  │ Worker 3│               │
│  │ (Flask) │  │ (Flask) │  │ (Flask) │               │
│  └────┬────┘  └────┬────┘  └───┬─────┘               │
│       │            │            │                      │
│       └────────────┼────────────┘                      │
│                    │                                    │
│  ┌─────────────────┼─────────────────────────────┐    │
│  │                 │                             │    │
│  │  ┌──────────────▼──────────┐  ┌─────────────┐│    │
│  │  │     PostgreSQL          │  │   Redis     ││    │
│  │  │  - Port 5432            │  │ - Port 6379 ││    │
│  │  │  - Local/RDS            │  │ - Cache     ││    │
│  │  └─────────────────────────┘  │ - Sessions  ││    │
│  │                                │ - Celery    ││    │
│  │                                └─────────────┘│    │
│  │                                                │    │
│  │  ┌─────────────────────────────────────────┐ │    │
│  │  │     Celery Workers (Background)         │ │    │
│  │  │  - Job Matching                         │ │    │
│  │  │  - Email Notifications                  │ │    │
│  │  │  - Reminders                            │ │    │
│  │  └─────────────────────────────────────────┘ │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

        Internet ↕️ HTTPS (Port 443)
```

## Project Structure (Three Independent Services)

> For the full, annotated file tree with ✅/🟡/❌ status per file, see [docs/PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md).

```
hermes/
├── src/
│   ├── backend/                       # Backend API — port 5000
│   │   ├── docker-compose.yml         # PostgreSQL, Redis, API, Celery Worker, Beat
│   │   ├── Dockerfile
│   │   ├── app/
│   │   │   ├── routes/                # REST API (/api/v1/*)
│   │   │   │   ├── auth.py            # ✅ register, login, logout, refresh, reset, verify
│   │   │   │   ├── health.py          # ✅ GET /api/v1/health
│   │   │   │   ├── jobs.py            # 🟡 stub
│   │   │   │   ├── users.py           # 🟡 stub
│   │   │   │   ├── notifications.py   # 🟡 stub
│   │   │   │   └── admin.py           # 🟡 stub
│   │   │   ├── models/                # ✅ 15 tables (User, Job, Notification, …)
│   │   │   ├── services/
│   │   │   │   └── auth_service.py    # ✅ full auth business logic
│   │   │   ├── middleware/
│   │   │   │   ├── auth_middleware.py # ✅ @require_role, get_current_user, token rotation
│   │   │   │   └── error_handler.py   # ✅ JSON 400/401/403/404/500
│   │   │   ├── validators/
│   │   │   │   └── auth_validator.py  # ✅ marshmallow schemas
│   │   │   └── tasks/                 # Celery tasks (stubs)
│   │   ├── migrations/                # ✅ full DDL + seed data
│   │   └── tests/                     # ✅ 74 tests passing
│   │
│   ├── frontend/                      # User Frontend — port 8080
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── app/
│   │   │   ├── routes/                # /, /auth, /jobs, /profile (stubs)
│   │   │   ├── templates/             # Jinja2 HTML (not yet created)
│   │   │   └── static/                # CSS, JS, images (not yet created)
│   │   └── config/settings.py
│   │
│   ├── frontend-admin/                # Admin Frontend — port 8081
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── app/
│   │   │   ├── routes/                # /, /auth, /dashboard, /users, /jobs (stubs)
│   │   │   ├── templates/             # Jinja2 HTML (not yet created)
│   │   │   └── static/                # CSS, JS, images (not yet created)
│   │   └── config/settings.py
│   │
│   └── nginx/                         # Reverse Proxy — ports 80/443
│       ├── docker-compose.yml         # References all three networks
│       └── nginx.conf
│
├── docs/
│   ├── PROJECT_STRUCTURE.md           # Full annotated file tree
│   ├── PROJECT_SUMMARY.md             # Quick start guide
│   └── WORKFLOW_DIAGRAMS.md
├── postman/
│   └── hermes-api.postman_collection.json
├── config/                            # Env templates per environment
├── scripts/
└── README.md
```

## Required Python Packages

```txt
# Flask Framework
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-JWT-Extended==4.5.3
Flask-Mail==0.9.1
Flask-WTF==1.2.1
Flask-Cors==4.0.0

# Database & Caching
psycopg2-binary==2.9.9
alembic==1.13.0
redis==5.0.1

# Background Tasks
celery==5.3.4

# Security
bcrypt==4.1.2

# Utilities
python-dotenv==1.0.0
email-validator==2.1.0
Pillow==10.1.0

# Push Notifications
firebase-admin==6.3.0

# Production Server (Hostinger VPS)
gunicorn==21.2.0
gevent==23.9.1

# Logging
sentry-sdk[flask]==1.39.0
```

## Hostinger VPS Server Requirements

### Minimum Specifications
- **RAM**: 4GB (8GB recommended for production)
- **CPU**: 2 cores (4 cores recommended)
- **Storage**: 40GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Bandwidth**: Unmetered

### Recommended Hostinger Plan
- **VPS Plan**: VPS 2 or higher
- **Monthly Users**: Up to 10,000 active users
- **Concurrent Requests**: ~100-200

### Resource Usage Estimates
- **Flask App (3 Gunicorn workers)**: ~1.5GB RAM
- **PostgreSQL**: Idle ~500MB; Active ~1-4GB RAM
- **Redis**: ~500MB RAM
- **Celery Workers**: ~500MB RAM
- **System & Nginx**: ~500MB RAM

## Environment Variables (.env)

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# PostgreSQL Configuration
SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:your_db_password@localhost:5432/hermes_db
DB_POOL_SIZE=20

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Flask-Mail Email Configuration (SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@hermes.com
MAIL_MAX_EMAILS=100
MAIL_ASCII_ATTACHMENTS=False

# Firebase Configuration (for push notifications)
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Admin Configuration
ADMIN_EMAIL=admin@hermes.com
```

## Development Workflow

### Phase 1: Setup & Core (Week 1-2)
- Project setup and environment configuration
- Database schema design and PostgreSQL setup
- User authentication system
- Basic profile management

### Phase 2: Job Module (Week 3-4)
- Job vacancy CRUD operations
- Job listing and search
- Job details page
- Admin job management

### Phase 3: Matching Engine (Week 5-6)
- Profile-based job matching algorithm
- Eligibility checker
- Recommendation system
- Testing with sample data

### Phase 4: Application Tracking (Week 7-8)
- Application management
- Priority marking
- Notes and reminders
- Application dashboard

### Phase 5: Notification System (Week 9-10)
- Notification engine
- Email integration
- Push notification setup
- Celery task scheduler
- Notification preferences

### Phase 6: Admin Panel (Week 11-12)
- Admin dashboard
- Analytics and reports
- User management
- Content management

### Phase 7: Testing & Deployment (Week 13-14)
- Unit testing
- Integration testing
- Security audit
- Performance optimization
- Production deployment

## Testing Strategy

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test API endpoints
3. **Matching Algorithm Tests**: Verify job-user matching logic
4. **Notification Tests**: Verify notification triggers
5. **Load Testing**: Test with multiple concurrent users
6. **Security Testing**: Penetration testing

## Hostinger VPS Deployment Guide

### Prerequisites
- Hostinger VPS (minimum 4GB RAM, 2 CPU cores)
- Ubuntu 22.04 LTS
- Domain name pointed to VPS IP
- SSH access to server

### Step 1: Initial Server Setup

```bash
# Connect to VPS
ssh root@your-vps-ip

# Update system packages
sudo apt update && sudo apt upgrade -y

# Create application user
sudo adduser hermes
sudo usermod -aG sudo hermes

# Setup firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Step 2: Install Required Software

```bash
# Install Python 3.11 and dependencies
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL 16
sudo apt install -y gnupg curl
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
sudo apt update
sudo apt install -y postgresql-16 postgresql-client-16
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install Redis
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Install Nginx
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx

# Install Supervisor (for process management)
sudo apt install supervisor -y
```

### Step 3: Clone and Setup Application

```bash
# Switch to application user
su - hermes

# Clone repository
cd /home/hermes
git clone https://github.com/SumanKr7/hermes.git
cd hermes

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
nano .env
# Add your environment variables (see .env section)
```

### Step 4: Configure Gunicorn

```bash
# Create gunicorn configuration
nano /home/hermes/hermes/gunicorn_config.py
```

```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
accesslog = "/home/hermes/hermes/logs/gunicorn_access.log"
errorlog = "/home/hermes/hermes/logs/gunicorn_error.log"
loglevel = "info"
```

### Step 5: Configure Supervisor for Flask App

```bash
sudo nano /etc/supervisor/conf.d/hermes.conf
```

```ini
[program:hermes]
command=/home/hermes/hermes/venv/bin/gunicorn -c /home/hermes/hermes/gunicorn_config.py run:app
directory=/home/hermes/hermes
user=hermes
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/hermes/hermes/logs/supervisor_error.log
stdout_logfile=/home/hermes/hermes/logs/supervisor_out.log
```

### Step 6: Configure Supervisor for Celery Workers

```bash
sudo nano /etc/supervisor/conf.d/celery_worker.conf
```

```ini
[program:celery_worker]
command=/home/hermes/hermes/venv/bin/celery -A celery_worker.celery worker --loglevel=info
directory=/home/hermes/hermes
user=hermes
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/hermes/hermes/logs/celery_worker_error.log
stdout_logfile=/home/hermes/hermes/logs/celery_worker.log

[program:celery_beat]
command=/home/hermes/hermes/venv/bin/celery -A celery_worker.celery beat --loglevel=info
directory=/home/hermes/hermes
user=hermes
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/hermes/hermes/logs/celery_beat_error.log
stdout_logfile=/home/hermes/hermes/logs/celery_beat.log
```

```bash
# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status
```

### Step 7: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/hermes
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size limit
    client_max_body_size 10M;

    # Serve static files directly
    location /static {
        alias /home/hermes/hermes/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    # Access and error logs
    access_log /var/log/nginx/hermes_access.log;
    error_log /var/log/nginx/hermes_error.log;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/hermes /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (certbot adds cron job automatically)
sudo certbot renew --dry-run
```

### Step 9: Setup PostgreSQL (Production Configuration)

```bash
# Create database and user
sudo -u postgres psql
```

```sql
CREATE USER hermes_user WITH PASSWORD 'your_strong_password';
CREATE DATABASE hermes_db OWNER hermes_user;
GRANT ALL PRIVILEGES ON DATABASE hermes_db TO hermes_user;
\q
```

```bash
# Restrict remote access (bind to localhost only)
sudo nano /etc/postgresql/16/main/postgresql.conf
# Set: listen_addresses = 'localhost'

# Run Alembic migrations
cd /home/hermes/hermes
source venv/bin/activate
flask db upgrade

# Verify connection
psql -h localhost -U hermes_user -d hermes_db -c "\dt"
```

### Step 10: Environment Variables for Production

```bash
nano /home/hermes/hermes/.env
```

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-production-secret-key-min-32-chars

# PostgreSQL Configuration
SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:your_db_password@localhost:5432/hermes_db
DB_POOL_SIZE=20

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Flask-Mail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=/home/hermes/hermes/firebase-credentials.json

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-different-from-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Admin Configuration
ADMIN_EMAIL=admin@yourdomain.com

# Application URL
APP_URL=https://yourdomain.com
```

### Step 11: Setup Automated Backups

```bash
# Create backup script
nano /home/hermes/backup_postgresql.sh
```

```bash
#!/bin/bash
# PostgreSQL Backup Script

BACKUP_DIR="/home/hermes/backups/postgresql"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="hermes_backup_$DATE.dump"

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump PostgreSQL (custom format – compressed, supports parallel restore)
PGPASSWORD="your_db_password" pg_dump \
  -h localhost -U hermes_user -d hermes_db \
  -F c -f "$BACKUP_DIR/$BACKUP_NAME"

# Delete backups older than 7 days
find $BACKUP_DIR -name "*.dump" -type f -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME"
```

```bash
# Make script executable
chmod +x /home/hermes/backup_postgresql.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add this line:
0 2 * * * /home/hermes/backup_postgresql.sh >> /home/hermes/logs/backup.log 2>&1
```

### Step 12: Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/hermes
```

```
/home/hermes/hermes/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 hermes hermes
    sharedscripts
    postrotate
        supervisorctl restart hermes celery_worker celery_beat
    endscript
}
```

### Deployment Commands

```bash
# Update application
cd /home/hermes/hermes
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo supervisorctl restart all

# View logs
sudo tail -f /home/hermes/hermes/logs/gunicorn_error.log
sudo supervisorctl tail -f hermes stderr

# Check status
sudo supervisorctl status
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server

# Restart services
sudo supervisorctl restart all
sudo systemctl restart nginx
```

## Maintenance

1. **Backup Strategy**: Daily automated PostgreSQL backups via `pg_dump` (retention: 7 days)
2. **Update Schedule**: Weekly security patches, monthly feature updates
3. **Log Management**: Centralized logging with logrotate
4. **Database**: Use `pg_stat_activity`, `EXPLAIN ANALYZE` for query tuning

## Future Enhancements

1. **Mobile Application**: Native iOS and Android apps
2. **AI-Powered Resume Builder**: Help users create job-specific resumes
3. **Mock Test Platform**: Practice tests for various exams
4. **Study Material Section**: Notes and resources
5. **Discussion Forum**: Community for job seekers
6. **Video Tutorials**: Preparation guides
7. **Referral System**: Users can refer friends
8. **Premium Features**: Advanced analytics and priority notifications
9. **Multi-language Support**: Support for regional languages
10. **Interview Preparation**: Tips and common questions

## Success Metrics

1. **User Engagement**: Daily active users, session duration
2. **Job Discovery**: Average jobs viewed per user
3. **Application Rate**: Jobs applied vs jobs viewed
4. **Notification Effectiveness**: Open rate, click-through rate
5. **User Retention**: Monthly active users returning
6. **Platform Growth**: New registrations per month
7. **Job Success Rate**: Users selected in applied jobs

## Troubleshooting (Hostinger VPS)

### Application won't start
```bash
# Check supervisor logs
sudo supervisorctl tail -f hermes stderr

# Check if port is in use
sudo lsof -i :8000

# Restart application
sudo supervisorctl restart hermes
```

### High Memory Usage
```bash
# Check memory usage
free -h
htop

# Reduce Gunicorn workers in gunicorn_config.py
workers = 2  # Instead of 3

# Restart services
sudo supervisorctl restart all
```

### PostgreSQL Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# Test connection
psql -h localhost -U hermes_user -d hermes_db -c "SELECT 1;"
```

### Celery Tasks Not Running
```bash
# Check Celery worker status
sudo supervisorctl status celery_worker celery_beat

# View Celery logs
sudo supervisorctl tail -f celery_worker stderr

# Restart Celery
sudo supervisorctl restart celery_worker celery_beat
```

### SSL Certificate Issues
```bash
# Renew certificate manually
sudo certbot renew --nginx

# Check certificate expiry
sudo certbot certificates
```

### 502 Bad Gateway Error
```bash
# Check if Gunicorn is running
sudo supervisorctl status hermes

# Check Nginx error logs
sudo tail -f /var/log/nginx/hermes_error.log

# Restart services
sudo supervisorctl restart hermes
sudo systemctl restart nginx
```

---

**Project Repository**: https://github.com/SumanKr7/hermes
**License**: MIT License
