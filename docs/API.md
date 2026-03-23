# Hermes API Reference

Base URL: `http://localhost:8000/api/v1`

All list endpoints return: `{ "data": [...], "pagination": { "limit", "offset", "total", "has_more" } }`

---

## Authentication

### User Auth (Firebase)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/verify-token` | Public | Verify Firebase ID token → upsert user → internal JWT pair |
| POST | `/auth/logout` | User JWT | Invalidate token (Redis blocklist) |
| POST | `/auth/refresh` | Public | Rotate internal token pair |

User registration, email/password login, Google sign-in, phone OTP, password reset, and email verification are all handled client-side by the Firebase JS SDK. The backend only receives the resulting Firebase ID token via `/auth/verify-token`.

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
| PUT | `/users/profile/phone` | User | Update phone number |
| GET | `/users/me/following` | User | List followed organizations |

**Profile preference fields** (used for job matching):
- `preferred_states` — JSON array of state names, e.g. `["Delhi", "Uttar Pradesh"]`
- `preferred_categories` — JSON array of reservation categories, e.g. `["general", "obc"]`
- `highest_qualification` — `10th`, `12th`, `diploma`, `graduate`, `postgraduate`, `phd`

---

## Organization Follow

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/organizations/{name}/follow` | User | Follow an org (idempotent, max 50) |
| DELETE | `/organizations/{name}/follow` | User | Unfollow (404 if not following) |

When a job from a followed org is approved (draft → active), a `new_job_from_followed_org` notification is created via Celery.

---

## Job Vacancies (Public)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/jobs` | Public | List active jobs (filtered, paginated, FTS) |
| GET | `/jobs/recommended` | User JWT | Personalized recommendations by profile match |
| GET | `/jobs/:slug` | Public | Job detail by slug (increments views) |

**Query Parameters for `GET /jobs`:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Full-text search (uses PostgreSQL tsvector) |
| `job_type` | string | `latest_job`, `result`, `admit_card`, etc. |
| `qualification_level` | string | `graduate`, `postgraduate`, etc. |
| `organization` | string | Partial match (ILIKE) |
| `department` | string | Partial match (ILIKE) |
| `status` | string | Default: `active` |
| `is_featured` | boolean | Filter featured jobs |
| `is_urgent` | boolean | Filter urgent jobs |
| `limit` | int | 1-100, default: 20 |
| `offset` | int | Default: 0 |

---

## Admin Endpoints

All admin endpoints require an admin JWT token (`user_type: "admin"`).

### Job Management

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/jobs` | Operator+ | List all jobs (any status) |
| POST | `/admin/jobs` | Operator+ | Create job vacancy |
| POST | `/admin/jobs/upload-pdf` | Operator+ | Upload PDF → AI extraction → draft job |
| GET | `/admin/jobs/:id` | Operator+ | Get single job detail |
| PUT | `/admin/jobs/:id` | Operator+ | Update job |
| PUT | `/admin/jobs/:id/approve` | Operator+ | Approve draft → active |
| DELETE | `/admin/jobs/:id` | Admin only | Soft-delete (→ cancelled) |

### User Management

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/users` | Operator+ | List users (search by name/email) |
| GET | `/admin/users/:id` | Operator+ | User detail with profile |
| PUT | `/admin/users/:id/role` | Admin only | Change user role (admin/operator) |
| PUT | `/admin/users/:id/status` | Admin only | Suspend or activate user |

### Dashboard & Logs

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/stats` | Operator+ | Job/user/application counts (includes new_this_week) |
| GET | `/admin/analytics` | Admin only | Platform analytics (demographics, trends, etc.) |
| GET | `/admin/logs` | Admin only | Admin audit trail |

---

## Application Tracking

All application endpoints require a user JWT.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/applications` | User | List own tracked applications (filterable) |
| GET | `/applications/stats` | User | Application counts by status |
| POST | `/applications` | User | Track / save a job application |
| GET | `/applications/:id` | User | Get single application detail |
| PUT | `/applications/:id` | User | Update (status, notes, priority, app number) |
| DELETE | `/applications/:id` | User | Remove from tracker (204) |

**Query Parameters for `GET /applications`:**

| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status |
| `is_priority` | boolean | Filter priority applications |
| `limit` | int | 1-100, default: 20 |
| `offset` | int | Default: 0 |

**Valid statuses:** `applied`, `admit_card_released`, `exam_completed`, `result_pending`, `selected`, `rejected`, `waiting_list`

**Deadline Reminders:** A Celery Beat task runs daily at 08:00 UTC and creates in-app notifications at T-7, T-3, and T-1 days before `application_end` for all tracked applications. If the user has email enabled, a deadline reminder email is also sent.

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
| POST | `/users/me/fcm-token` | User | Register FCM device token (max 10) |
| DELETE | `/users/me/fcm-token` | User | Unregister FCM token |
| PUT | `/users/me/notification-preferences` | User | Update notification channel preferences |

---

## Smart Notification Routing

All notifications are routed through `NotificationService` via the `smart_notify` Celery task.

### Two Delivery Modes

| Mode | In-app + Push | Email | WhatsApp | Use Case |
|------|--------------|-------|----------|----------|
| **instant** | T+0 | T+0 | T+0 | OTP, welcome, urgent alerts |
| **staggered** | T+0 | T+15min* | T+1hr* | Job alerts, deadline reminders, admit cards |

*Configurable via `NOTIFY_EMAIL_DELAY` and `NOTIFY_WHATSAPP_DELAY` env vars (in seconds).

All channels always deliver — staggered just adds a time gap so the user isn't bombarded simultaneously.

### Channel Delivery

| Channel | Delivery | De-duplication |
|---------|----------|----------------|
| In-app | Always (persistent record in `notifications` table) | — |
| FCM Push | All physical devices | `device_fingerprint` — 1 push per physical device, not per login |
| Email | Always (unless user disabled or OCI 3k/day limit) | — |
| WhatsApp | Always (unless user disabled or not configured) | — |

### Push De-duplication Example

| Device | Login | Fingerprint | Gets Push? |
|--------|-------|-------------|------------|
| Phone | Android app | `phone_abc` | Yes |
| Laptop | Chrome web | `laptop_xyz` | Yes |
| Laptop | Chrome PWA | `laptop_xyz` | No (same physical device) |
| Tablet | Safari PWA | `tablet_def` | Yes |

3 physical devices → 3 pushes. Not 4.

Every delivery attempt is logged in `notification_delivery_log` with status (pending/sent/delivered/failed/skipped).

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
  "job_type": "latest_job",
  "qualification_level": "graduate",
  "total_vacancies": 8000,
  "description": "Combined Graduate Level recruitment...",
  "application_end": "2026-07-15",
  "status": "draft"
}
→ 201 { "id": "uuid", "slug": "ssc-cgl-2026", ... }
```

### Search Jobs
```
GET /api/v1/jobs?q=SSC+CGL&qualification_level=graduate&limit=10
→ 200 { "data": [...], "pagination": { "total": 1, "has_more": false, ... } }
```

### Get Recommended Jobs
```
GET /api/v1/jobs/recommended?limit=20&offset=0
Authorization: Bearer <user_token>
→ 200 { "data": [...], "pagination": { "total": 5, ... } }
```
Scoring: state match (+3), category match (+3), education match (+2), recency <7d (+1).
Fallback: returns latest active jobs if user has no preferences set.

### Follow Organization
```
POST /api/v1/organizations/UPSC/follow
Authorization: Bearer <user_token>
→ 200 { "message": "Now following UPSC", "followed_organizations": ["UPSC"] }
```

### List Following
```
GET /api/v1/users/me/following
Authorization: Bearer <user_token>
→ 200 { "followed_organizations": ["UPSC", "SSC"], "count": 2 }
```

### Track Application
```
POST /api/v1/applications
Authorization: Bearer <user_token>
{
  "job_id": "82886414-e24b-4bef-97ea-898936ca8333",
  "notes": "Preparing for this exam",
  "is_priority": true
}
→ 201 { "id": "uuid", "status": "applied", "job": { "job_title": "...", ... } }
```

### Update Application Status
```
PUT /api/v1/applications/<id>
Authorization: Bearer <user_token>
{ "status": "admit_card_released", "application_number": "UPSC-2026-12345" }
→ 200 { "id": "uuid", "status": "admit_card_released", ... }
```

### Application Stats
```
GET /api/v1/applications/stats
Authorization: Bearer <user_token>
→ 200 { "applied": 3, "admit_card_released": 1, "total": 4 }
```

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

All errors follow: `{ "detail": "Error message" }`

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

Job vacancies can include category-wise application fees (all nullable integers in INR):

| Field | Description |
|-------|-------------|
| `fee_general` | Fee for General category |
| `fee_obc` | Fee for OBC category |
| `fee_sc_st` | Fee for SC/ST category |
| `fee_ews` | Fee for EWS category |
| `fee_female` | Fee for Female candidates |

Fee fields are included in `JobCreateRequest`, `JobUpdateRequest`, `JobResponse`, and `JobListItem`.
Value `0` means "Free". `null` means fee not specified (row hidden in UI).

### Create Job with Fees
```
POST /api/v1/admin/jobs
Authorization: Bearer <admin_token>
{
  "job_title": "SSC GD Constable 2026",
  "organization": "Staff Selection Commission",
  "fee_general": 100,
  "fee_obc": 100,
  "fee_sc_st": 0,
  "fee_ews": 0,
  "fee_female": 0,
  ...
}
```

---

## Admin Dashboard Stats (enhanced)

```
GET /api/v1/admin/stats
Authorization: Bearer <admin_token>
→ 200 {
  "jobs": { "total": 7, "active": 6, "draft": 0 },
  "users": { "total": 3, "active": 3, "new_this_week": 1 },
  "applications": { "total": 12 }
}
```

---

## SEO

### Sitemap
- Celery Beat task `generate_sitemap` runs daily at 04:00 UTC
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

## Share Buttons

Job detail and job card pages include:
- **WhatsApp**: `https://wa.me/?text={encoded_url+title}`
- **Telegram**: `https://t.me/share/url?url={url}&text={title}`
- **Copy Link**: Clipboard API button

---

## PDF Upload & AI Extraction

### Upload PDF
```
POST /api/v1/admin/jobs/upload-pdf
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data

file: <pdf_file>

→ 202 {
  "message": "PDF uploaded, extraction in progress",
  "task_id": "celery-task-uuid",
  "filename": "notification.pdf"
}
```

**Constraints:**
- Only `.pdf` files accepted
- Maximum file size: 10MB (configurable via `PDF_MAX_SIZE_MB`)
- Requires `ANTHROPIC_API_KEY` for AI extraction (graceful fallback if not set)

**Workflow:**
1. Upload PDF → saved to `/app/uploads/pdfs/`
2. Celery task `extract_job_from_pdf` triggered
3. PDF text extracted via `pdfplumber`
4. Text sent to Anthropic Claude for structured field extraction
5. Draft job created in DB with extracted data
6. Admin reviews draft via `/jobs/{id}/review` in admin frontend
7. Admin approves → job goes live

**Extracted fields:** job_title, organization, department, qualification_level, total_vacancies, description, dates, fees, salary, eligibility, selection_process, source_url.

---

## PWA Support

The user frontend supports Progressive Web App features:

- **Web App Manifest** (`/static/manifest.json`): enables Add to Home Screen
- **Service Worker** (`/static/sw.js`): caches homepage and offline page
- **Offline Fallback** (`/offline`): shown when network unavailable during navigation
- **Theme Color**: `#1e3a5f` (Hermes brand)
- **Icons**: 192x192 and 512x512 PNG

---

## Database Tables

| Table | Description |
|-------|-------------|
| `users` | Regular user accounts (no role column) |
| `admin_users` | Admin/operator accounts (role, department, permissions) |
| `user_profiles` | Extended user profile (education, category, location) |
| `job_vacancies` | Job postings with FTS vector |
| `user_job_applications` | Application tracking |
| `notifications` | User notifications |
| `notification_delivery_log` | Per-channel delivery tracking (push/email/whatsapp) |
| `user_devices` | Device registry (FCM token, fingerprint de-duplication) |
| `admin_logs` | Admin audit trail |
