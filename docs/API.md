# Hermes API Reference

Base URL: `http://localhost:8000/api/v1`

All list endpoints return: `{ "data": [...], "pagination": { "limit", "offset", "total", "has_more" } }`

---

## Authentication

### User Auth (Firebase)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/verify-token` | Public | Verify Firebase ID token → upsert user → internal JWT pair |
| POST | `/auth/send-email-otp` | Public | Send OTP to email for registration (rate-limited: 3/min) |
| POST | `/auth/verify-email-otp` | Public | Verify email OTP → returns short-lived verification token (5 min) |
| POST | `/auth/complete-registration` | Public | Create Firebase user + send welcome email after OTP verification |
| POST | `/auth/check-phone-availability` | Public | Check if phone number is already registered |
| POST | `/auth/check-user-providers` | Public | Check which auth providers a Firebase user has (Google, password) |
| POST | `/auth/add-password` | Public | Add password to an existing social-auth (Google) account (requires OTP verification token) |
| POST | `/auth/logout` | User JWT | Revoke access + optional refresh token via Redis blocklist (returns 204) |
| POST | `/auth/refresh` | Public | Rotate internal token pair (old refresh JTI is blocklisted) |

**Registration Methods:**
- Email/Password: Send OTP → verify OTP → complete registration with password
- Google OAuth: Handled client-side by Firebase JS SDK
- Phone OTP: Handled client-side by Firebase JS SDK

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 special character (!@#$%^&*(),.?":{}|<>)

**Logout body (optional):**
```json
{ "refresh_token": "<refresh-JWT>" }
```
If `refresh_token` is provided, its JTI is also added to the Redis blocklist so it cannot be used to generate new access tokens after logout. Without it, the refresh token remains valid until it expires.

### Admin Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/admin/login` | Public | Admin/operator login → JWT |
| POST | `/auth/admin/logout` | Admin JWT | Invalidate admin token |
| POST | `/auth/admin/refresh` | Public | Rotate admin token pair |

**Internal JWT Claims** (issued by backend after Firebase verification):
- `user_type`: `"user"` or `"admin"` — determines which table to look up
- `role`: (admin tokens only) `"admin"` or `"operator"`
- `sub`: UUID of the user/admin
- `jti`: unique token ID (stored in Redis as `hermes:blocklist:{jti}` on logout/refresh)

**Firebase verify-token upsert logic:**
1. Find user by `firebase_uid` → return existing user
2. Find user by `email` → link `firebase_uid`, set `migration_status = "migrated"`
3. No match → create new user with `migration_status = "native"`

---

## User Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users/profile` | User | Get own profile + user data |
| PUT | `/users/profile` | User | Update profile fields |
| PUT | `/users/profile/phone` | User | Update phone number (marks as unverified) |
| POST | `/users/me/send-phone-otp` | User | Send OTP to verify phone number |
| POST | `/users/me/verify-phone-otp` | User | Verify phone number with OTP |
| POST | `/users/me/set-password` | User | Set password for Google OAuth users |
| POST | `/users/me/change-password` | User | Change password (requires re-authentication client-side before calling) |
| POST | `/users/me/link-email-password` | User | Link email+password to phone-only account |

**Profile preference fields** (used for eligibility checking):
- `preferred_states` — JSON array of state names, e.g. `["Delhi", "Uttar Pradesh"]`
- `preferred_categories` — JSON array of reservation categories the user wants to see, e.g. `["General", "OBC"]`
- `category` — User's actual reservation category: `General`, `OBC`, `SC`, `ST`, `EWS`, or `EBC`. Used for per-job/admission eligibility checks.
- `highest_qualification` — Enum: `10th`, `12th`, `diploma`, `graduate`, `postgraduate`, `phd`
- `gender` — Enum: `Male`, `Female`, `Other`
- `date_of_birth` — Used to compute age for age-range eligibility matching in per-job/admission eligibility checks

**Note:** The profile response does not include `fcm_tokens` (sensitive device tokens). Register/unregister tokens via the FCM token endpoints.

---

## Track Jobs & Admissions

Users can track specific jobs or admissions to receive automatic notifications.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/jobs/{job_id}/track` | User | Track a job (idempotent, max 100) |
| DELETE | `/jobs/{job_id}/track` | User | Untrack a job (404 if not tracking) |
| POST | `/admissions/{admission_id}/track` | User | Track an admission (idempotent) |
| DELETE | `/admissions/{admission_id}/track` | User | Untrack an admission |
| GET | `/users/me/tracked` | User | List all tracked jobs + admissions |

**Automatic notifications triggered by tracking:**
- `deadline_reminder_7d` — 7 days before `application_end`
- `deadline_reminder_3d` — 3 days before `application_end`
- `deadline_reminder_1d` — Last day to apply (high priority)
- `tracked_item_updated` — When admin approves or updates the job/admission

**Response for `GET /users/me/tracked`:**
```json
{
  "jobs": [{ "id": "uuid", "job_title": "...", "slug": "...", "organization": "...", "application_end": "2026-05-01", "status": "active" }],
  "admissions": [{ "id": "uuid", "admission_name": "...", "slug": "...", "conducting_body": "...", "application_end": "2026-06-01", "status": "active" }],
  "total": 2
}
```

---

## Job Vacancies (Public)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/jobs` | Public | List active jobs (filtered, paginated, FTS) |
| GET | `/jobs/eligibility/:slug` | User JWT | Per-job eligibility check against user profile |
| GET | `/jobs/:slug` | Public | Job detail by slug |

**Query Parameters for `GET /jobs`:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Full-text search (uses PostgreSQL tsvector) |
| `qualification_level` | string | `graduate`, `postgraduate`, etc. |
| `organization` | string | Partial match (ILIKE) |
| `department` | string | Partial match (ILIKE) |
| `status` | string | Default: `active` |
| `limit` | int | 1-100, default: 20 |
| `offset` | int | Default: 0 |

---

## Admin Endpoints

All admin endpoints require an admin JWT token (`user_type: "admin"`).

### Content Management

Content is stored across four dedicated tables: `jobs`, `admit_cards`, `answer_keys`, `results`.

#### Job Vacancies

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/jobs` | Operator+ | List all job vacancies |
| POST | `/admin/jobs` | Operator+ | Create job vacancy |

#### Admit Cards

| Method | Endpoint | Role | Description |
|--------|----------|------|---------|
| GET | `/admin/admit-cards` | Operator+ | List all admit cards |
| POST | `/admin/admit-cards` | Operator+ | Create admit card (must specify `job_id` OR `admission_id`) |
| PUT | `/admin/admit-cards/{id}` | Operator+ | Update admit card |
| DELETE | `/admin/admit-cards/{id}` | Operator+ | Delete admit card |

> **Admin UI:** Admit cards are managed from the parent job or admission edit page (`/jobs/<id>/edit#docs` or `/admissions/<id>/edit#docs`). There is no standalone `/admit-cards` management page.

#### Answer Keys

| Method | Endpoint | Role | Description |
|--------|----------|------|---------|
| GET | `/admin/answer-keys` | Operator+ | List all answer keys |
| POST | `/admin/answer-keys` | Operator+ | Create answer key (must specify `job_id` OR `admission_id`) |
| PUT | `/admin/answer-keys/{id}` | Operator+ | Update answer key |
| DELETE | `/admin/answer-keys/{id}` | Operator+ | Delete answer key |

> **Admin UI:** Answer keys are managed from the parent job or admission edit page. There is no standalone `/answer-keys` management page.

#### Results

| Method | Endpoint | Role | Description |
|--------|----------|------|---------|
| GET | `/admin/results` | Operator+ | List all results |
| POST | `/admin/results` | Operator+ | Create result (must specify `job_id` OR `admission_id`) |
| PUT | `/admin/results/{id}` | Operator+ | Update result |
| DELETE | `/admin/results/{id}` | Operator+ | Delete result |

> **Admin UI:** Results are managed from the parent job or admission edit page. There is no standalone `/results` management page.

#### Common Job Operations

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/jobs/:id` | Operator+ | Get single content detail |
| PUT | `/admin/jobs/:id` | Operator+ | Update content |
| DELETE | `/admin/jobs/:id` | Admin only | Hard-delete (cascade) |

**Query Parameters for List Endpoints:**

| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status (`upcoming` / `active` / `inactive` / `closed`) |
| `limit` | int | 1-100, default: 20 |
| `offset` | int | Default: 0 |

### User Management

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/users` | Operator+ | List users (search by name/email) |
| GET | `/admin/users/:id` | Operator+ | User detail with profile |
| PUT | `/admin/users/:id/status` | Admin only | Suspend or activate user |

### Admin Account Management

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/admin/admin-users` | Admin only | Create a new admin or operator account |

**Request body:**
```json
{
  "email": "operator@hermes.com",
  "password": "Oper@123",  # pragma: allowlist secret
  "full_name": "New Operator",
  "role": "operator",
  "phone": null,
  "department": null
}
```
The first admin account must be seeded directly in the database. All subsequent accounts can be created through this endpoint.

### Dashboard & Logs

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/stats` | Operator+ | Job/user counts by status (includes new_this_week) |
| GET | `/admin/logs` | Admin only | Admin audit trail |

---

## Notifications

All notification endpoints require a user JWT.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/notifications` | User | List notifications (paginated, filterable) |
| GET | `/notifications/count` | User | Unread notification count |
| PUT | `/notifications/{id}/read` | User | Mark single notification as read |
| PUT | `/notifications/read-all` | User | Mark all unread → read |
| DELETE | `/notifications/{id}` | User | Delete notification (204) |

**Query Parameters for `GET /notifications`:**

| Param | Type | Description |
|-------|------|-------------|
| `type` | string | Filter by notification type |
| `is_read` | boolean | Filter read/unread |
| `limit` | int | 1-100, default: 20 |
| `offset` | int | Default: 0 |

**Notification Types:** `deadline_reminder_7d`, `deadline_reminder_3d`, `deadline_reminder_1d`, `new_job_from_followed_org`, `priority_job_update`, `welcome`

**Email Notifications:** When creating in-app notifications, the system also queues email via Celery if the user's `notification_preferences.email` is not explicitly `false`. Dev environment uses Mailpit (SMTP port 1025, Web UI port 8025).

**Push Notifications:** FCM push notification is sent if `FIREBASE_CREDENTIALS_PATH` is configured and the user has registered FCM tokens with `notification_preferences.push` not set to `false`.

---

## FCM Tokens & Notification Preferences

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/users/me/fcm-token` | User | Register FCM device token (max 10 per user) |
| DELETE | `/users/me/fcm-token` | User | Unregister FCM token |
| PUT | `/users/me/notification-preferences` | User | Update notification channel preferences |

**Notification preferences fields:** `email` (bool), `push` (bool), `in_app` (bool), `whatsapp` (bool), `telegram` (bool). All default to enabled if unset. Send `false` to disable a channel.

**Setting a Telegram chat_id** (required before Telegram messages can be delivered):
```json
PUT /api/v1/users/me/notification-preferences
{ "telegram_chat_id": "123456789" }
```
Users must first message the bot on Telegram to get their chat_id. The chat_id is stored nested in `notification_preferences.telegram.chat_id`.

**FCM token registration body:**
```json
{ "token": "<FCM-device-token>", "device_name": "Pixel 7" }
```
Tokens are stored in `user_profiles.fcm_tokens` and read by the notification service at send time. Invalid/unregistered tokens are automatically removed.

---

## Smart Notification Routing

All notifications are routed through `NotificationService` via the `smart_notify` Celery task.

### Two Delivery Modes

| Mode | In-app + Push | Email | WhatsApp | Telegram | Use Case |
|------|--------------|-------|----------|----------|---------|
| **instant** | T+0 | T+0 | T+0 | T+0 | OTP, welcome, urgent alerts |
| **staggered** | T+0 | T+15min* | T+1hr* | T+15min* | Job alerts, deadline reminders, admit cards |

*Configurable via `NOTIFY_EMAIL_DELAY`, `NOTIFY_WHATSAPP_DELAY`, `NOTIFY_TELEGRAM_DELAY` env vars (in seconds).

All channels always deliver — staggered just adds a time gap so the user isn't bombarded simultaneously.

### Channel Delivery

| Channel | Delivery | Notes |
|---------|----------|-------|
| In-app | Always (persistent record in `notifications` table) | — |
| FCM Push | All tokens in `user_profiles.fcm_tokens` | Tokens registered via `POST /users/me/fcm-token`; invalid tokens auto-removed on send failure |
| Email | If user has `notification_preferences.email` not set to `false` | Subject to OCI 3 000/day soft limit |
| WhatsApp | If user has `notification_preferences.whatsapp` not set to `false` | Placeholder until `WHATSAPP_API_TOKEN` is configured |
| Telegram | If user has chat_id set in `notification_preferences.telegram.chat_id` and `notification_preferences.telegram.enabled` not `false` | Requires `TELEGRAM_BOT_TOKEN`; uses Bot API `sendMessage` with Markdown |}

Every delivery attempt is logged in `notification_delivery_log` with status (`pending`, `sent`, `delivered`, `failed`). Status starts as `pending`, moves to `sent` on dispatch, `delivered` on confirmation, `failed` on error.

---

## Request/Response Examples

### Verify Firebase Token (unified login/register)
```
POST /api/v1/auth/verify-token
{ "id_token": "<Firebase-ID-token>", "full_name": "Test User" }
→ 200 { "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }
```

The `full_name` field is optional — only used when creating a new user. The Firebase ID token is obtained client-side via the Firebase JS SDK (email/password, Google popup, or phone OTP).

### Create Job (Admin)
```
POST /api/v1/admin/jobs
Authorization: Bearer <admin_token>
{
  "job_title": "SSC CGL 2026",
  "organization": "Staff Selection Commission",
  "qualification_level": "graduate",
  "total_vacancies": 8000,
  "description": "Combined Graduate Level recruitment...",
  "application_end": "2026-07-15",
  "status": "active"
}
→ 201 { "id": "uuid", "slug": "ssc-cgl-2026", ... }
```

### Search Jobs
```
GET /api/v1/jobs?q=SSC+CGL&qualification_level=graduate&limit=10
→ 200 { "data": [...], "pagination": { "total": 1, "has_more": false, ... } }
```

### Check Job Eligibility
```
GET /api/v1/jobs/eligibility/ssc-cgl-2026
Authorization: Bearer <user_token>
→ 200 {
    "status": "eligible" | "partially_eligible" | "not_eligible" | "unknown",
    "reasons": [
      "Your qualification (graduate) meets the requirement (graduate)",
      "Age 26 is within the eligible range",
      "Your category (OBC) is eligible"
    ]
  }
```
`unknown` is returned when the user's profile has insufficient data — frontend prompts them to complete their profile.

### List Notifications
```
GET /api/v1/notifications?is_read=false&limit=10
Authorization: Bearer <user_token>
→ 200 { "data": [{ "id": "uuid", "type": "deadline_reminder_3d", "title": "3 days left: SSC CGL 2026", ... }], "pagination": { ... } }
```

### Unread Count
```
GET /api/v1/notifications/count
Authorization: Bearer <user_token>
→ 200 { "count": 5 }
```

### Register FCM Token
```
POST /api/v1/users/me/fcm-token
Authorization: Bearer <user_token>
{ "token": "fcm-device-token-string", "device_name": "Chrome" }
→ 200 { "message": "FCM token registered", "fcm_tokens_count": 1 }
```

### Update Notification Preferences
```
PUT /api/v1/users/me/notification-preferences
Authorization: Bearer <user_token>
{ "email": true, "push": false }
→ 200 { "message": "Preferences updated", "notification_preferences": { "email": true, "push": false } }
```

---

## Error Responses

All errors follow the structured format from `app/main.py`:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": [],
    "timestamp": "2026-04-07T06:00:00Z"
  }
}
```

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Unauthorized (invalid/expired/revoked token) |
| 403 | Forbidden (wrong role or token scope) |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate email, already tracking job) |
| 422 | Validation error (Pydantic) |

---

## Application Fee Fields

Fees are stored in a single `fee` JSONB field on both `jobs` and `admissions`. Keys are optional — only include categories that apply.

| Key | Description |
|-----|-------------|
| `general` | Fee for General / UR category |
| `obc` | Fee for OBC-NCL category |
| `sc_st` | Fee for SC / ST category |
| `ews` | Fee for EWS category |
| `female` | Fee for Female / PwBD candidates |

`fee` is included in `JobCreateRequest`, `JobUpdateRequest`, `JobResponse`, `JobListItem`, `AdmissionCreateRequest`, `AdmissionUpdateRequest`, `AdmissionResponse`, and `AdmissionListItem`.
Value `0` means "Free". Omitting a key means fee not specified (hidden in UI).

### Create Job with Fees
```
POST /api/v1/admin/jobs
Authorization: Bearer <admin_token>
{
  "job_title": "SSC GD Constable 2026",
  "organization": "Staff Selection Commission",
  "fee": { "general": 100, "obc": 100, "sc_st": 0, "ews": 0, "female": 0 },
  ...
}
```

---

## Admin Dashboard Stats (enhanced)

```
GET /api/v1/admin/stats
Authorization: Bearer <admin_token>
→ 200 {
  "jobs": { "total": 7, "active": 6 },
  "admit_cards": { "total": 15 },
  "answer_keys": { "total": 3 },
  "results": { "total": 2 },
  "admissions": { "total": 5, "active": 4 },
  "users": { "total": 3, "active": 3, "new_this_week": 1 }
}
```

**Content Type Breakdown:**
- `jobs` — Job vacancies (`jobs` table)
- `admit_cards` — Admit card releases (`admit_cards` table)
- `answer_keys` — Answer key publications (`answer_keys` table)
- `results` — Exam results (`results` table)
- `admissions` — Admission information (`admissions` table)

---

## SEO

### Sitemap
- `hermes-scheduler` task `generate_sitemap` runs daily at 04:00 UTC
- Generates `/sitemap.xml` with all active job URLs
- Served via Nginx at `/sitemap.xml`

### Meta Tags (job detail pages)
- `<title>`: `{job_title} | {organization} | Hermes`
- `<meta name="description">`: First 160 chars of description
- Open Graph: `og:title`, `og:description`, `og:url`, `og:type`, `og:site_name`

### JobPosting JSON-LD (job detail pages)
- Embedded `<script type="application/ld+json">` on each job detail page
- Fields: title, description, datePosted, validThrough, hiringOrganization, jobLocation, employmentType, educationRequirements, baseSalary

---

## Share Button

Every job card and detail page includes a single **Share** button using the Web Share API:
- **Mobile (native share sheet):** `navigator.share({ title, url })` triggers the OS-level share dialog
- **Desktop fallback:** `navigator.clipboard.writeText(url)` — button text changes to `✓ Copied` for 1.8 seconds
- URL and title are passed via `data-url` and `data-title` HTML attributes to avoid Jinja2/JS context issues

WhatsApp and Telegram share links have been removed.

---

## Admit Cards, Answer Keys, and Results

These are now top-level resources, independent of jobs and admissions. Each document can be linked to either a job OR an admission via polymorphic foreign keys.

### Admit Cards

#### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admit-cards` | List all admit cards (paginated) |
| GET | `/admit-cards/{id}` | Get single admit card by ID (includes job/admission context) |

#### Admin Endpoints (operator+)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/admit-cards` | List all admit cards (any status) |
| POST | `/admin/admit-cards` | Create admit card (must specify job_id OR admission_id) |
| PUT | `/admin/admit-cards/{id}` | Update admit card |
| DELETE | `/admin/admit-cards/{id}` | Delete admit card |

### Answer Keys

#### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/answer-keys` | List all answer keys (paginated) |
| GET | `/answer-keys/{id}` | Get single answer key by ID (includes job/admission context) |

#### Admin Endpoints (operator+)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/answer-keys` | List all answer keys (any status) |
| POST | `/admin/answer-keys` | Create answer key (must specify job_id OR admission_id) |
| PUT | `/admin/answer-keys/{id}` | Update answer key |
| DELETE | `/admin/answer-keys/{id}` | Delete answer key |

### Results

#### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/results` | List all results (paginated) |
| GET | `/results/{id}` | Get single result by ID (includes job/admission context) |

#### Admin Endpoints (operator+)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/results` | List all results (any status) |
| POST | `/admin/results` | Create result (must specify job_id OR admission_id) |
| PUT | `/admin/results/{id}` | Update result |
| DELETE | `/admin/results/{id}` | Delete result |

### Document Creation

When creating a document via the top-level admin endpoints, you must specify **either** `job_id` OR `admission_id` in the request body:

```json
// Create admit card for a job
POST /api/v1/admin/admit-cards
{
  "job_id": "uuid-here",
  "slug": "ssc-cgl-tier1-admit-card-2026",
  "title": "SSC CGL Tier-1 Admit Card 2026",
  "links": [{"label": "Download Admit Card", "url": "https://..."}],
  "exam_start": "2026-04-01",
  "exam_end": "2026-04-15"
}

// Create answer key for an admission
POST /api/v1/admin/answer-keys
{
  "admission_id": "uuid-here",
  "slug": "neet-ug-2026-answer-key",
  "title": "NEET UG 2026 Provisional Answer Key",
  "links": [{"label": "Set A", "url": "https://..."}, {"label": "Objection Portal", "url": "https://..."}],
  "start_date": "2026-05-10",
  "end_date": "2026-05-15"
}

// Create result for a job
POST /api/v1/admin/results
{
  "job_id": "uuid-here",
  "slug": "ssc-cgl-2026-result",
  "title": "SSC CGL 2026 Final Result",
  "links": [{"label": "View Result", "url": "https://..."}, {"label": "Download Scorecard", "url": "https://..."}],
  "start_date": "2026-08-01",
  "end_date": "2026-08-31"
}
```

**Validation rules:**
- Cannot specify both `job_id` and `admission_id`
- Must specify at least one
- Parent job/admission must exist in database
- `slug` is required and must be unique

**`links` field** is a JSONB array of labelled URLs (same pattern across admit cards, answer keys, and results):
```json
[{"label": "Download", "url": "https://..."}, {"label": "Notice PDF", "url": "https://..."}]
```

---

## PWA Support

The user frontend supports Progressive Web App features:

- **Web App Manifest** (`/static/manifest.json`): enables Add to Home Screen
- **Service Worker** (`/static/sw.js`): caches homepage and offline page
- **Offline Fallback** (`/offline`): shown when network unavailable during navigation
- **Theme Color**: `#1e3a5f` (Hermes brand)
- **Icons**: 192x192 and 512x512 PNG

---

## Admissions

Admissions (NEET, JEE, CLAT, CAT, GATE etc.) are stored in the `admissions` table, separate from `jobs`.
They have admission-specific fields: `stream`, `admission_type`, `counselling_body`, `seats_info`, admission pattern.

### Public (read-only, active admissions only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admissions` | List active admissions (stream/admission_type/search filters) |
| GET | `/admissions/{slug}` | Admission detail by slug (unique URL-friendly identifier) |
| GET | `/admissions/{slug}/admit-cards` | Per-phase admit cards (admission status must not be `closed`) |
| GET | `/admissions/{slug}/answer-keys` | Per-phase answer keys (admission status must not be `closed`) |
| GET | `/admissions/{slug}/results` | Per-phase results (admission status must not be `closed`) |

**Query Parameters for `GET /admissions`:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Full-text search on admission name, conducting body, description |
| `stream` | string | `medical`, `engineering`, `law`, `management`, `arts_science`, `general` |
| `admission_type` | string | `ug`, `pg`, `doctoral`, `lateral` |
| `limit` | int | 1-100, default: 20 |
| `offset` | int | Default: 0 |

**Note:** `status='upcoming'` admissions are excluded from public listing (only `status='active'` returned).

### Admin CRUD (operator+)

| Method | Endpoint | Description |
|--------|----------|-----------|
| GET | `/admin/admissions` | List all admissions (any status, filterable by stream/admission_type/status) |
| GET | `/admin/admissions/{id}` | Get single admission detail by ID (any status) |
| POST | `/admin/admissions` | Create admission |
| PUT | `/admin/admissions/{id}` | Update admission |
| DELETE | `/admin/admissions/{id}` | Delete admission (cascades to linked docs) |

### Example — List Medical Admissions
```
GET /api/v1/admissions?stream=medical&limit=10
→ 200 {
  "data": [
    {
      "slug": "nta-neet-pg-2026",
      "admission_name": "NTA NEET PG 2026 — Medical PG Admissionination",
      "conducting_body": "National Testing Agency",
      "counselling_body": "Medical Counselling Committee (MCC)",
      "admission_type": "pg",
      "stream": "medical",
      "application_end": "2025-11-30",
      "admission_date": "2026-03-09",
      "fee": { "general": 4250, "obc": 4250, "sc_st": 2000 }
    },
    ...
  ],
  "pagination": { "total": 3, "has_more": false }
}
```

### Admission JSON Field Structures

**`admission_details`** — Exam pattern and paper structure:
```json
{
  "mode": "Online",
  "duration_minutes": 180,
  "total_marks": 360,
  "total_questions": 90,
  "negative_marking": 1.0,
  "language": ["Hindi", "English"],
  "subjects": [
    { "name": "Physics", "questions": 30, "marks": 120 },
    { "name": "Chemistry", "questions": 30, "marks": 120 },
    { "name": "Mathematics", "questions": 30, "marks": 120 }
  ]
}
```

**`eligibility`** — Candidate eligibility criteria:
```json
{
  "qualification": "12th Pass with Physics, Chemistry, Mathematics from a recognised board",
  "min_percentage": 75,
  "age_limit": { "min": 17, "max": 25 },
  "attempts_allowed": 2,
  "notes": "SC/ST candidates: 65% aggregate. Age relaxation as per govt norms."
}
```

**`seats_info`** — Category-wise seat breakdown:
```json
{
  "total": 17385,
  "UR": 7850,
  "OBC": 4680,
  "EWS": 1740,
  "SC": 2610,
  "ST": 505
}
```

### Example — Create Admission (Admin)
```
POST /api/v1/admin/admissions
Authorization: Bearer <admin_token>
{
  "admission_name": "JEE Advanced 2026",
  "conducting_body": "IIT Bombay",
  "counselling_body": "JoSAA",
  "admission_type": "ug",
  "stream": "engineering",
  "eligibility": {
    "qualification": "12th Pass with PCM",
    "min_percentage": 75,
    "age_limit": { "min": 17, "max": 25 },
    "attempts_allowed": 2
  },
  "seats_info": { "total": 17385, "UR": 7850, "OBC": 4680, "EWS": 1740, "SC": 2610, "ST": 505 },
  "admission_details": {
    "mode": "Online",
    "duration_minutes": 180,
    "total_marks": 360,
    "subjects": [
      { "name": "Physics", "questions": 30, "marks": 120 },
      { "name": "Chemistry", "questions": 30, "marks": 120 },
      { "name": "Mathematics", "questions": 30, "marks": 120 }
    ]
  },
  "admission_date": "2026-05-25",
  "fee": { "general": 3200, "sc_st": 1600 },
  "status": "active"
}
→ 201 { "id": "uuid", "slug": "jee-advanced-2026", ... }
```

---

## Database Tables

| Table | Description |
|-------|-------------|
| `users` | Regular user accounts |
| `admin_users` | Admin/operator accounts (role, department, permissions) |
| `user_profiles` | Extended user profile (education, category, location, followed_organizations) |
| `jobs` | Job vacancy postings with FTS vector |
| `admissions` | Admissions (NEET, JEE, CLAT, CAT, GATE etc.) |
| `notifications` | User notifications |
| `notification_delivery_log` | Per-channel delivery tracking (push/email/whatsapp/telegram) |
| `user_devices` | Device registry (FCM token, fingerprint de-duplication) |
| `admin_logs` | Admin audit trail |
| `user_tracks` | Jobs and admissions a user is tracking (for notifications) |
| `admit_cards` | Admit cards linked to job OR admission — `slug`, `links` JSONB, `exam_start`/`exam_end` |
| `answer_keys` | Answer keys linked to job OR admission — `slug`, `links` JSONB, `start_date`/`end_date` |
| `results` | Results linked to job OR admission — `slug`, `links` JSONB, `start_date`/`end_date` |
