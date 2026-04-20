# Database Design

This document outlines the PostgreSQL database schema for the Hermes project, using SQLAlchemy models.

## Migrations

Schema is managed with Alembic:

| File | Description |
|------|-------------|
| `migrations/versions/0001_initial.py` | **Complete consolidated schema** — all 14 tables: `fee JSONB` on jobs+admissions, `created_at`+`updated_at` on all tables, `organizations` with `slug`+`org_type`+`updated_at`, `user_tracks` supporting `job`/`admission`/`organization` entity types |

**Apply migrations:**
```bash
docker exec hermes_backend alembic -c /app/alembic.ini upgrade head
```

---

## Entity Relationship Diagram (ERD)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          HERMES — ENTITY RELATIONSHIP DIAGRAM                   │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐   1    ┌──────────────────┐
  │  ADMIN_USERS │───────►│      JOBS        │
  │              │        │ (job listings)   │
  │  id          │        │ id               │
  │  email       │        │ title            │
  │  role        │        │ status           │
  └──────┬───────┘        └────────┬─────────┘
         │ 1                       │ 1
         │                         │
         ▼ *                       ├──────────────────────────────────────┐
  ┌──────────────┐                 │                                      │
  │  ADMIN_LOGS  │                 │                                      │
  │              │                 │                                      │
  │  id          │          ┌──────▼──────────────────────────────────────▼──────────────────────────────────┐
  │  action      │          │              POLYMORPHIC DOCUMENT TABLES                                        │
  │  resource_   │          │                                                                                  │
  │  type/id     │          │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                        │
  └──────────────┘          │  │  ADMIT_CARDS │   │  ANSWER_KEYS │   │   RESULTS    │                        │
                            │  │              │   │              │   │              │                        │
                            │  │ id           │   │ id           │   │ id           │                        │
                            │  │ job_id ──────┼───┼── (FK jobs)  │   │ job_id       │                        │
                            │  │ admission_id─┼───┼── (FK adm.)  │   │ admission_id │                        │
                            │  │ title        │   │ title        │   │ title        │                        │
                            │  │ slug (unique)│   │ slug (unique)│   │ slug (unique)│                        │
                            │  │ links (JSONB)│   │ links (JSONB)│   │ links (JSONB)│                        │
                            │  └──────────────┘   └──────────────┘   └──────────────┘                        │
                            │                                                                                  │
                            │  CHECK: (job_id IS NOT NULL AND admission_id IS NULL)                            │
                            │      OR (job_id IS NULL     AND admission_id IS NOT NULL)                        │
                            └──────────────────────────────────────────────────────────────────────────────────┘
         ▲ *                       ▲ 1
         │                         │
  ┌──────┴───────┐        ┌────────┴─────────┐
  │    JOBS      │        │   ADMISSIONS     │
  │              │        │ (NEET/JEE/CLAT)  │
  │  (see above) │        │ id               │
  └──────────────┘        │ admission_name        │
                          │ conducting_body  │
                          │ stream           │
                          │ status           │
                          └──────────────────┘

  ┌──────────────┐  1     ┌──────────────────┐  *   ┌────────────────────────────┐
  │    USERS     │───────►│  USER_TRACKS     │      │   USER_TRACKS entity       │
  │              │        │                  │      │                            │
  │ id           │        │ id               │      │ entity_type = 'job'        │
  │ email        │        │ user_id ─────────┼─────►│   entity_id → JOBS.id      │
  │ status       │        │ entity_type      │      │                            │
  └──────┬───────┘        │ entity_id        │      │ entity_type = 'admission'  │
         │                └──────────────────┘      │   entity_id → ADMISSIONS   │
         │ 1                                        │                            │
                                                    │ entity_type = 'organization'│
                                                    │   entity_id → ORGANIZATIONS│
                                                    └────────────────────────────┘

  ┌──────────────────┐       organization_id (FK, nullable)
  │  ORGANIZATIONS   │◄──────────────────────────────────────────── JOBS
  │                  │◄──────────────────────────────────────────── ADMISSIONS
  │                  │
  │ id (UUID PK)     │
  │ name (unique)    │
  │ short_name       │
  │ logo_url         │
  │ website_url      │
  └──────────────────┘

         ├──────────────────────┐
         │                      │
         ▼ 0..1                 ▼ *
  ┌──────────────┐     ┌────────────────────┐
  │ USER_PROFILES│     │   NOTIFICATIONS    │
  │              │     │                    │
  │ id           │     │ id                 │
  │ user_id      │     │ user_id            │     ┌────────────────────────────┐
  │ stream       │     │ type               │────►│  NOTIFICATION_DELIVERY_LOG │
  │ category     │     │ title              │  *  │                            │
  │ state        │     │ is_read            │     │ id                         │
  └──────────────┘     └────────────────────┘     │ notification_id            │
                                                   │ device_id                  │
  ┌──────────────┐                                 │ status                     │
  │ USER_DEVICES │────────────────────────────────►│ sent_at                    │
  │              │  *                              └────────────────────────────┘
  │ id           │
  │ user_id      │
  │ fcm_token    │
  └──────────────┘
```

> **Polymorphic constraint:** `admit_cards`, `answer_keys`, and `results` each have a DB-level
> CHECK constraint `(job_id IS NOT NULL AND admission_id IS NULL) OR (job_id IS NULL AND admission_id IS NOT NULL)`
> ensuring exactly one parent reference per row.

---

## Tables (15 total)

### 1. `users`
Core user account table. Integrated with Firebase Auth.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated via `gen_random_uuid()` |
| `email` | String(255) | Yes | User email (unique, indexed) |
| `password_hash` | String(255) | Yes | Legacy/native password hash |
| `full_name` | String(255) | No | Full name |
| `phone` | String(20) | Yes | Contact number |
| `firebase_uid` | String(128) | Yes | Firebase Auth UID (unique, indexed) |
| `migration_status` | String(20) | No | `native` \| `migrated` \| `legacy`; default `native` |
| `status` | String(20) | No | `ck_users_status`: `active` \| `suspended` \| `deleted`; default `active` |
| `is_verified` | Boolean | No | Identity verification status; default `false` |
| `is_email_verified` | Boolean | No | Email OTP verified; default `false` |
| `is_phone_verified` | Boolean | No | Phone OTP verified; default `false` |
| `last_login` | DateTime | Yes | Timestamp of last login |
| `created_at` | DateTime | No | Account creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

**Indexes:** `idx_users_email`, `idx_users_status`, `ix_users_firebase_uid` (unique)

---

### 2. `user_profiles`
Detailed profile information and preferences. One row per user (UNIQUE on `user_id`).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `user_id` | UUID (FK → `users.id`) | No | CASCADE delete; UNIQUE |
| `date_of_birth` | Date | Yes | Birth date |
| `gender` | String(20) | Yes | `ck_profiles_gender`: `Male` \| `Female` \| `Other` |
| `category` | String(20) | Yes | `ck_profiles_category`: `General` \| `OBC` \| `SC` \| `ST` \| `EWS` \| `EBC` |
| `is_pwd` | Boolean | No | Person with Disability; default `false` |
| `is_ex_serviceman` | Boolean | No | Ex-serviceman; default `false` |
| `state` | String(100) | Yes | Current state |
| `city` | String(100) | Yes | Current city |
| `pincode` | String(10) | Yes | Postal code |
| `highest_qualification` | String(50) | Yes | Degree name |
| `education` | JSONB | No | Detailed education history; default `{}` |
| `notification_preferences` | JSONB | No | Channel toggles (`email`, `push`, `in_app`, `whatsapp`); default `{}` |
| `preferred_states` | JSONB | No | States of interest for jobs; default `[]` |
| `preferred_categories` | JSONB | No | Categories of interest; default `[]` |
| `fcm_tokens` | JSONB | No | FCM tokens: `[{"token":"…","device_name":"…","registered_at":"…"}]`; default `[]` |
| `followed_organizations` | JSONB | No | **Deprecated** — legacy org names list; superseded by `user_tracks` with `entity_type='organization'`; default `[]` |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

**Indexes:** GIN on `education`, GIN on `notification_preferences`

---

### 3. `admin_users`
Internal staff accounts (Admin/Operator).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `email` | String(255) | No | Admin email (unique) |
| `password_hash` | String(255) | No | Bcrypt hash |
| `full_name` | String(255) | No | Full name |
| `phone` | String(20) | Yes | Contact number |
| `role` | String(20) | No | `ck_admin_users_role`: `admin` \| `operator`; default `operator` |
| `department` | String(255) | Yes | Internal department |
| `permissions` | JSONB | No | Granular permission flags; default `{}` |
| `status` | String(20) | No | `ck_admin_users_status`: `active` \| `suspended` \| `deleted`; default `active` |
| `is_email_verified` | Boolean | No | Email verified status; default `false` |
| `last_login` | DateTime | Yes | Timestamp of last login |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

**Indexes:** `idx_admin_users_email`, `idx_admin_users_status`

---

### 4. `organizations`
Organization registry — backfilled from `jobs.organization` on migration. Identified by UUID or slug.

| Column | Type | Nullable | Description |
|--------|------|----------|-----------|
| `id` | UUID (PK) | No | Auto-generated |
| `name` | String(255) | No | Full name (unique, indexed) — e.g. "Staff Selection Commission" |
| `short_name` | String(50) | Yes | Abbreviation — e.g. "SSC" |
| `logo_url` | Text | Yes | Logo image URL |
| `website_url` | Text | Yes | Official website |
| `slug` | String(255) | No | URL-friendly identifier (unique, indexed) |
| `org_type` | String(20) | No | `ck_org_type`: `jobs` \| `admissions` \| `both`; default `both` |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

**Indexes:** `idx_organizations_name`, `idx_organizations_slug`

**Public API routes:**
- `GET /api/v1/organizations` — list all orgs (with `job_count` + `admission_count`)
- `GET /api/v1/organizations/tracked` — list orgs the current user follows (auth required)
- `GET /api/v1/organizations/{org_id}` — org detail + recent jobs and admissions
- `POST /api/v1/organizations/{org_id}/track` — follow org (auth required)
- `DELETE /api/v1/organizations/{org_id}/track` — unfollow org (auth required)

---

### 5. `jobs`
Government job vacancies. Document releases (admit cards, answer keys, results) are stored in their own tables and link back via `job_id`.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `job_title` | String(500) | No | Full title of the recruitment |
| `slug` | String(500) | No | URL slug (unique) |
| `organization` | String(255) | No | Hiring authority name (free-text, indexed) — kept for backward compat |
| `organization_id` | UUID (FK → `organizations.id`) | Yes | SET NULL on delete; links to `organizations` table |
| `department` | String(255) | Yes | Specific department |
| `employment_type` | String(50) | Yes | `ck_jobs_employment_type`: `permanent` \| `temporary` \| `contract` \| `apprentice`; default `permanent` |
| `qualification_level` | String(50) | Yes | `10th`, `graduate`, etc., indexed |
| `total_vacancies` | Integer | Yes | Total seat count |
| `vacancy_breakdown` | JSONB | No | Seat distribution by category/state; default `{}` |
| `description` | Text | Yes | Full HTML description |
| `short_description` | Text | Yes | One-liner for listing cards |
| `eligibility` | JSONB | No | Age limits, physical standards, medical; default `{}` |
| `application_details` | JSONB | No | Links, fees, instruction links; default `{}` |
| `documents` | JSONB | No | Required docs (format, size); default `[]` |
| `source_url` | Text | Yes | Official notification URL |
| `notification_date` | Date | Yes | Date of official notice |
| `application_start` | Date | Yes | Start date for applying |
| `application_end` | Date | Yes | Deadline for applying, indexed |
| `exam_start` | Date | Yes | Date of first phase exam |
| `exam_end` | Date | Yes | Date of last phase exam |
| `result_date` | Date | Yes | Expected result date |
| `exam_details` | JSONB | No | Exam pattern, phases; default `{}` |
| `salary_initial` | Integer | Yes | Minimum pay (INR) |
| `salary_max` | Integer | Yes | Maximum pay (INR) |
| `salary` | JSONB | No | Pay scale, level, allowances; default `{}` |
| `selection_process` | JSONB | No | List of selection stages; default `[]` |
| `fee` | JSONB | No | Application fees by category `{general, obc, sc_st, ews, female}` (INR); `0` = Free; default `{}` |
| `status` | String(20) | No | `ck_jobs_status`: `upcoming` \| `active` \| `inactive` \| `closed`; default `active` |
| `created_by` | UUID (FK → `admin_users.id`) | Yes | Admin who created the job |
| `source` | String(20) | No | `ck_jobs_source`: `manual`; default `manual` |
| `source_pdf_path` | Text | Yes | Reserved; not populated |
| `published_at` | DateTime | Yes | When job was approved and published |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |
| `links` | JSONB | No | Important links (application portal, notice PDF, etc.); default `[]` |
| `search_vector` | tsvector | — | GENERATED ALWAYS (job_title A, organization B, description C) — GIN indexed |

**Indexes:** `idx_jobs_organization`, `idx_jobs_status_created`, `idx_jobs_qual_level`, `idx_jobs_application_end`, `idx_jobs_org_status`, GIN on `eligibility`, GIN on `search_vector`

---

### 6. `notifications`
Master records for all system notifications.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `user_id` | UUID (FK → `users.id`) | No | Target user; CASCADE delete |
| `entity_type` | String(50) | Yes | Type of entity that triggered this (`job`, `admission`, etc.) |
| `entity_id` | UUID | Yes | ID of the triggering entity |
| `type` | String(60) | No | Notification type (`job_alert`, `system`, etc.) |
| `title` | String(500) | No | Short title |
| `message` | Text | No | Body content |
| `action_url` | Text | Yes | Click-through link |
| `is_read` | Boolean | No | In-app read status; default `false` |
| `sent_via` | ARRAY(String) | Yes | Channels actually used (e.g. `['push', 'email']`) |
| `priority` | String(10) | No | `ck_notifications_priority`: `low` \| `medium` \| `high`; default `medium` |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |
| `read_at` | DateTime | Yes | When notification was read |
| `expires_at` | DateTime | No | Auto-delete after 90 days; default `NOW() + 90 days` |

**Indexes:** `idx_notifications_user_read`, `idx_notifications_user_created`, `idx_notifications_expires`

---

### 7. `admin_logs`
Audit logs for staff actions. Auto-expire after 30 days.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `admin_id` | UUID (FK → `admin_users.id`) | No | Admin who performed the action |
| `action` | String(100) | No | `create_job`, `suspend_user`, `admin_login`, etc. |
| `resource_type` | String(100) | Yes | `job`, `user`, `admission`, etc. |
| `resource_id` | UUID | Yes | Affected resource ID |
| `details` | Text | Yes | Human-readable summary |
| `changes` | JSONB | No | Before/after snapshot; default `{}` |
| `ip_address` | INET | Yes | Source IP address |
| `user_agent` | Text | Yes | Browser/client user-agent |
| `timestamp` | DateTime | No | When the action occurred; default `NOW()` |
| `expires_at` | DateTime | No | Auto-delete after 30 days; default `NOW() + 30 days` |

**Indexes:** `idx_admin_logs_admin_ts`, `idx_admin_logs_expires`

---

### 8. `user_devices`
Device registry — stores device metadata. **Push notifications read FCM tokens from `user_profiles.fcm_tokens`, not this table.** `user_devices` exists for future use (device-level fingerprint deduplication, device management UI) but is not populated by the current FCM token registration API.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `user_id` | UUID (FK → `users.id`) | No | Device owner; CASCADE delete |
| `fcm_token` | String(500) | Yes | FCM token (nullable; unique partial index where not null) |
| `device_name` | String(255) | No | "Chrome on Windows", "iPhone 13"; default `Unknown` |
| `device_type` | String(20) | No | `ck_devices_device_type`: `web` \| `pwa` \| `android` \| `ios`; default `web` |
| `device_fingerprint` | String(255) | Yes | Browser fingerprint |
| `is_active` | Boolean | No | Token validity; default `true` |
| `last_active_at` | DateTime | No | Last seen timestamp; default `NOW()` |
| `created_at` | DateTime | No | Registration timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

**Indexes:** `idx_devices_user_id`, `idx_devices_fcm_token` (unique partial), `idx_devices_fingerprint`

---

### 9. `notification_delivery_log`
Channel-level delivery tracking per notification attempt.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `notification_id` | UUID (FK → `notifications.id`) | No | Parent notification; CASCADE delete |
| `user_id` | UUID (FK → `users.id`) | No | Target user; CASCADE delete |
| `channel` | String(20) | No | `ck_delivery_channel`: `in_app` \| `push` \| `email` \| `whatsapp` \| `telegram` |
| `status` | String(20) | No | `ck_delivery_status`: `pending` \| `sent` \| `delivered` \| `failed`; default `pending` |
| `device_id` | UUID (FK → `user_devices.id`) | Yes | Targeted device (push only); SET NULL on delete |
| `error_message` | Text | Yes | Failure reason (from OCI/FCM) |
| `attempted_at` | DateTime | Yes | When delivery was attempted |
| `delivered_at` | DateTime | Yes | Verified delivery time |
| `created_at` | DateTime | No | Record creation timestamp |

**Indexes:** `idx_delivery_log_notif`, `idx_delivery_log_user`

---

### 10. `admit_cards`
Per-phase admit card links. Linked to either a **job** or an **admission** (polymorphic).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `job_id` | UUID (FK → `jobs.id`, nullable) | Yes | CASCADE delete |
| `admission_id` | UUID (FK → `admissions.id`, nullable) | Yes | CASCADE delete |
| `title` | String(255) | No | E.g. "SSC CGL Tier-1 2025 Admit Card" |
| `slug` | String(500) | No | URL slug (unique) |
| `links` | JSONB | No | Array of `{label, url}` — download links, notice links; default `[]` |
| `exam_start` | Date | Yes | Exam start date |
| `exam_end` | Date | Yes | Exam end date |
| `published_at` | DateTime | Yes | When this admit card was released |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

> `ck_admit_cards_source`: `(job_id IS NOT NULL AND admission_id IS NULL) OR (job_id IS NULL AND admission_id IS NOT NULL)`

**Indexes:** `idx_admit_cards_job`, `idx_admit_cards_admission`, `idx_admit_cards_pub`, `ix_admit_cards_slug` (unique)

---

### 11. `answer_keys`
Per-phase answer keys. Polymorphic.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `job_id` | UUID (FK → `jobs.id`, nullable) | Yes | CASCADE delete |
| `admission_id` | UUID (FK → `admissions.id`, nullable) | Yes | CASCADE delete |
| `title` | String(255) | No | E.g. "JEE Main Session 1 Provisional Answer Key" |
| `slug` | String(500) | No | URL slug (unique) |
| `links` | JSONB | No | Array of `{label, url}` — answer key files, objection portal; default `[]` |
| `start_date` | Date | Yes | Answer key availability start date |
| `end_date` | Date | Yes | Answer key / objection deadline |
| `published_at` | DateTime | Yes | Release timestamp |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

> `ck_answer_keys_source`: `(job_id IS NOT NULL AND admission_id IS NULL) OR (job_id IS NULL AND admission_id IS NOT NULL)`

**Indexes:** `idx_answer_keys_job`, `idx_answer_keys_admission`, `idx_answer_keys_pub`, `ix_answer_keys_slug` (unique)

---

### 12. `results`
Per-phase results. Polymorphic.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `job_id` | UUID (FK → `jobs.id`, nullable) | Yes | CASCADE delete |
| `admission_id` | UUID (FK → `admissions.id`, nullable) | Yes | CASCADE delete |
| `title` | String(255) | No | E.g. "NEET PG 2026 Result & Score Card" |
| `slug` | String(500) | No | URL slug (unique) |
| `links` | JSONB | No | Array of `{label, url}` — result PDF, scorecard links; default `[]` |
| `start_date` | Date | Yes | Result availability start date |
| `end_date` | Date | Yes | Result / scorecard download deadline |
| `published_at` | DateTime | Yes | Release timestamp |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

> `ck_results_source`: `(job_id IS NOT NULL AND admission_id IS NULL) OR (job_id IS NULL AND admission_id IS NOT NULL)`

**Indexes:** `idx_results_job`, `idx_results_admission`, `idx_results_pub`, `ix_results_slug` (unique)

---

### 13. `admissions`
Admissions (NEET, JEE, CLAT, CAT, GATE, CUET etc.) — separate from `jobs`.
These are educational admissioninations, not government job recruitments.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `slug` | String(500) | No | URL slug (unique) |
| `organization_id` | UUID (FK → `organizations.id`) | Yes | SET NULL on delete; links to `organizations` table |
| `admission_name` | String(500) | No | E.g. "NTA NEET PG 2026 — Medical PG Entrance" |
| `conducting_body` | String(255) | No | E.g. "National Testing Agency" |
| `counselling_body` | String(255) | Yes | E.g. "MCC", "JoSAA", "CLAT Consortium" |
| `admission_type` | String(20) | No | `ck_admission_type`: `ug` \| `pg` \| `doctoral` \| `lateral`; default `pg` |
| `stream` | String(30) | No | `ck_admission_stream`: `medical` \| `engineering` \| `law` \| `management` \| `arts_science` \| `general`; default `general` |
| `eligibility` | JSONB | No | `{min_qualification, attempts_limit, age_limit, ...}`; default `{}` |
| `admission_details` | JSONB | No | `{exam_pattern: [{phase, subjects, total_marks, duration_minutes, negative_marking, exam_mode}]}`; default `{}` |
| `selection_process` | JSONB | No | `[{phase, name, qualifying}]`; default `[]` |
| `seats_info` | JSONB | Yes | `{total_seats, by_category, note}` — institution/seat counts |
| `application_start` | Date | Yes | Registration opens |
| `application_end` | Date | Yes | Registration deadline |
| `admission_date` | Date | Yes | Date of main admission |
| `exam_start` | Date | Yes | Exam start date |
| `exam_end` | Date | Yes | Exam end date |
| `result_date` | Date | Yes | Expected result date |
| `counselling_start` | Date | Yes | Counselling round start |
| `fee` | JSONB | No | Application fees by category `{general, obc, sc_st, ews, female}` (INR); `0` = Free; default `{}` |
| `description` | Text | Yes | Full HTML description |
| `short_description` | Text | Yes | One-liner for listing cards |
| `source_url` | Text | Yes | Official website URL |
| `status` | String(20) | No | `ck_admission_status`: `upcoming` \| `active` \| `inactive` \| `closed`; default `active` |
| `published_at` | DateTime | Yes | When first published |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |
| `search_vector` | tsvector | — | GENERATED ALWAYS (admission_name A, conducting_body B, description C) — GIN indexed |

**Indexes:** `idx_admissions_slug` (unique), `idx_admissions_stream_status`, `idx_admissions_search` (GIN), `idx_admissions_organization_id`

**Key design difference from `jobs`:**

| Dimension | `jobs` | `admissions` |
|-----------|--------|------------------|
| Outcome | Employment (govt job) | Education (college/IIT/NLU seat) |
| Vacancies | `total_vacancies` + `vacancy_breakdown` | `seats_info` (seats by institution) |
| Salary | `salary_initial`, `salary_max` | — (not applicable) |
| Organization FK | `organization_id` → `organizations.id` | `organization_id` → `organizations.id` |
| Counselling | — | `counselling_body`, `counselling_start` |
| Attempts | — | `eligibility.attempts_limit` |

---

### 14. `user_tracks`
Polymorphic tracking table. Records which jobs, admissions, or organizations a user is following. Used to drive notification dispatch.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID (PK) | No | Auto-generated |
| `user_id` | UUID (FK → `users.id`) | No | CASCADE delete |
| `entity_type` | String(12) | No | `ck_user_tracks_entity_type`: `job` \| `admission` \| `organization` |
| `entity_id` | UUID | No | ID of the tracked entity — `jobs.id`, `admissions.id`, or `organizations.id` |
| `created_at` | DateTime | No | When the track was created |

> UNIQUE constraint `uq_user_track` on `(user_id, entity_type, entity_id)`. Max 100 tracks per user (enforced in application layer).

**Indexes:** `ix_user_tracks_user_id`, `ix_user_tracks_entity`

---

> **`alembic_version`** — Alembic-managed table, single row tracking the current migration revision. Not a user-defined table.
