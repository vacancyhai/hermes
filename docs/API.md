# Hermes API Reference

Base URL: `http://localhost:8000/api/v1`

All list endpoints return: `{ "data": [...], "pagination": { "limit", "offset", "total", "has_more" } }`

> **Docs URL:** Available only in `development` mode at `/api/v1/docs` (Swagger) and `/api/v1/redoc`. Disabled in production.

---

## Authentication

### User Auth (Firebase)

| Method | Endpoint | Auth | Rate Limit | Description |
|--------|----------|------|------------|-------------|
| POST | `/auth/verify-token` | Public | 10/min | Verify Firebase ID token → upsert user → internal JWT pair |
| POST | `/auth/send-email-otp` | Public | 3/min | Send OTP to email for registration |
| POST | `/auth/resend-verification` | User JWT | 3/min | Resend OTP to authenticated user's email (only if not yet verified) |
| POST | `/auth/verify-email-otp` | Public | 5/min | Verify email OTP → returns short-lived verification token (5 min) |
| POST | `/auth/complete-registration` | Public | 5/min | Create Firebase user + send welcome email after OTP verification |
| POST | `/auth/check-phone-availability` | Public | — | Check if a phone number is already registered and verified |
| POST | `/auth/check-user-providers` | Public | 10/min | Check which Firebase auth providers a user has (Google, password) |
| POST | `/auth/add-password` | Public | — | Add password to an existing Google-only account (requires OTP verification token) |
| POST | `/auth/logout` | User JWT | — | Revoke access token + optional refresh token via Redis blocklist (returns 204) |
| POST | `/auth/refresh` | Public | — | Rotate user token pair (old refresh JTI is blocklisted) |

**Registration flow — email/password:**
1. `POST /auth/send-email-otp` → 6-digit OTP stored in Redis with 5-minute TTL, emailed synchronously (not via Celery)
2. `POST /auth/verify-email-otp` → validates OTP (one-time use), returns a short-lived JWT `verification_token` (5 min, purpose=`email_verified`)
3. `POST /auth/complete-registration` → creates Firebase user server-side, sends welcome email via Celery, returns Firebase `custom_token` for client-side sign-in
4. Client signs in with `custom_token`, gets Firebase ID token → `POST /auth/verify-token` → internal JWT pair

**Registration flow — Google OAuth / Phone:**
- Handled entirely client-side by Firebase JS SDK
- Client presents Firebase ID token → `POST /auth/verify-token` → internal JWT pair

**`/auth/verify-token` upsert logic:**
1. Find user by `firebase_uid` → return existing user
2. Find user by `email` → link `firebase_uid`, set `migration_status = "migrated"`
3. No match → create new user with `migration_status = "native"` + create empty `UserProfile`

**Firebase verify-token body:**
```json
{ "id_token": "<Firebase-ID-token>", "full_name": "Optional Name" }
```
`full_name` is optional — only used when creating a new user.

**Logout body (optional):**
```json
{ "refresh_token": "<refresh-JWT>" }
```
If `refresh_token` is provided, its JTI is also blocklisted. Without it, the refresh token remains valid until it expires.

**JWT claims (issued by backend after Firebase verification):**
- `sub`: UUID of the user/admin
- `user_type`: `"user"` or `"admin"` — determines which table to look up
- `type`: `"access"` or `"refresh"`
- `role`: (admin tokens only) `"admin"` or `"operator"`
- `jti`: unique token ID (stored in Redis as `hermes:blocklist:{jti}` on logout/refresh)

**Token expiry (configurable via env):**
- Access token: `JWT_ACCESS_TOKEN_EXPIRES` (default 900s = 15 minutes)
- Refresh token: `JWT_REFRESH_TOKEN_EXPIRES` (default 604800s = 7 days)

### Admin Auth

| Method | Endpoint | Auth | Rate Limit | Description |
|--------|----------|------|------------|-------------|
| POST | `/auth/admin/login` | Public | 5/min | Admin/operator login (email + bcrypt password) → JWT pair |
| POST | `/auth/admin/logout` | Admin JWT | — | Invalidate admin token (logs action + blocklists JTI) |
| POST | `/auth/admin/refresh` | Public | — | Rotate admin token pair (logs action) |

Admin accounts use local bcrypt authentication, not Firebase.

---

## User Endpoints

All require a valid user JWT.

| Method | Endpoint | Rate Limit | Description |
|--------|----------|------------|-------------|
| GET | `/users/profile` | — | Get own user data + profile |
| PUT | `/users/profile` | — | Update profile fields; triggers async eligibility recompute |
| PUT | `/users/profile/phone` | — | Update phone number on user record (marks as unverified); sends email notification if user has email |
| POST | `/users/me/send-phone-otp` | 3/min | Initiate phone verification — instructs client to use Firebase phone auth |
| POST | `/users/me/verify-phone-otp` | 5/min | Mark phone as verified after Firebase phone auth; validates phone in Firebase ID token matches stored phone |
| POST | `/users/me/set-password` | 5/min | Set password for Google-only accounts (via Firebase Admin SDK) |
| POST | `/users/me/change-password` | 5/min | Change existing password (client must re-authenticate first) |
| POST | `/users/me/link-email-password` | 5/min | Link email+password to phone-only account (checks both PostgreSQL and Firebase for duplicates) |
| POST | `/users/me/fcm-token` | — | Register FCM device token (max 10, stored in `user_profiles.fcm_tokens`) |
| DELETE | `/users/me/fcm-token` | — | Unregister FCM device token |
| PUT | `/users/me/notification-preferences` | — | Merge-update notification channel preferences |
| DELETE | `/users/me/notification-preferences` | — | Reset notification preferences to `{}` (all channels re-enabled by app defaults) |

**Notes:**
- `PUT /users/profile` triggers `recompute_eligibility_for_user.delay(user_id)` (async Celery task).
- FCM tokens are stored as `[{"token": "...", "device_name": "...", "registered_at": "ISO8601"}]` in `user_profiles.fcm_tokens` (JSONB). Max 10 per user.
- Push notifications read FCM tokens from `user_profiles.fcm_tokens` (not `user_devices` table). `user_devices` is populated separately.
- Profile response does **not** include `fcm_tokens` (treated as sensitive).

**Profile preference fields (used for eligibility checking):**
- `highest_qualification` — one of: `10th`, `12th`, `diploma`, `graduate`, `postgraduate`, `phd`
- `category` — one of: `general`, `obc`, `sc`, `st`, `ews`, `ebc` (lowercase in DB)
- `date_of_birth` — used to compute age for eligibility
- `state` — compared against `domicile_required` in job eligibility
- `is_pwd` — triggers `PwBD`/`PwD_UR` age relaxation
- `is_ex_serviceman` — triggers `Ex_Serviceman` age relaxation
- `preferred_states` — JSONB array, used for future filtering (not currently applied in eligibility)
- `preferred_categories` — JSONB array, for future filtering

---

## Track Jobs & Admissions & Organizations

Users can track specific jobs, admissions, or organizations. Max 100 tracks per user (enforced in application layer). Uses the `user_tracks` table with polymorphic `entity_type` + `entity_id`.

### Job Tracking

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/jobs/{job_id}/track` | User | Track a job — idempotent; returns `{"tracking": true}` |
| DELETE | `/jobs/{job_id}/track` | User | Untrack a job (404 if not tracking) |
| GET | `/jobs/{job_id}/track` | User | Check tracking status for a job |

### Admission Tracking

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/admissions/{admission_id}/track` | User | Track an admission — idempotent |
| DELETE | `/admissions/{admission_id}/track` | User | Untrack an admission |
| GET | `/admissions/{admission_id}/track` | User | Check tracking status for an admission |

### Tracked List

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users/me/tracked` | User | List all tracked jobs + admissions (sorted by `track.created_at DESC`) |

**Response for `GET /users/me/tracked`:**
```json
{
  "jobs": [{ "id": "uuid", "job_title": "...", "slug": "...", "organization": "...", "application_end": "2026-05-01", "status": "active" }],
  "admissions": [{ "id": "uuid", "admission_name": "...", "slug": "...", "conducting_body": "...", "application_end": "2026-06-01", "status": "active" }],
  "total": 2
}
```

**Automatic notifications triggered by tracking:**
- `deadline_reminder_7d` — 7 days before `application_end`
- `deadline_reminder_3d` — 3 days before `application_end`
- `deadline_reminder_1d` — Last day to apply (high priority)
- `tracked_item_updated` — When admin updates a tracked job/admission to `active` status

**Note:** Tracking uses `entity_id` as UUID. Job track endpoints accept `job_id` UUID path param; admission endpoints accept `admission_id` UUID path param.

---

## Organizations

### Public

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/organizations` | Public | List all organizations with active job + admission counts |
| GET | `/organizations/tracked` | User | List organizations followed by current user |
| GET | `/organizations/{org_id}` | Public | Organization detail + up to 20 recent jobs (all statuses) |

**Query parameters for `GET /organizations`:**

| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Name partial match (ILIKE) |
| `org_type` | string | `jobs` → orgs with type `jobs` or `both`; `admissions` → `admissions` or `both` |
| `limit` | int | 1-100, default: 50 |
| `offset` | int | Default: 0 |

**Note:** `GET /organizations` returns `{"data": [...], "total": N, "limit": N, "offset": N}` (not the standard pagination wrapper — no `has_more`).

### Organization Tracking

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/organizations/{org_id}/track` | User | Follow an organization — idempotent |
| DELETE | `/organizations/{org_id}/track` | User | Unfollow an organization |
| GET | `/organizations/{org_id}/track` | User | Check follow status |

When a user follows an organization and a new job is posted, `send_new_job_notifications` is triggered (if the org has an `organization_id`).

---

## Job Vacancies (Public)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/jobs` | Public | List jobs excluding `inactive` (filtered, paginated, FTS) |
| GET | `/jobs/eligibility/{slug}` | User JWT | Per-job eligibility check against user profile |
| GET | `/jobs/{slug}` | Public | Job detail by slug (includes admit cards, answer keys, results) |

**Query Parameters for `GET /jobs`:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Full-text search using PostgreSQL `tsvector` (`search_vector` column); results ordered by `ts_rank` |
| `qualification_level` | string | Exact match: `10th`, `12th`, `diploma`, `graduate`, `postgraduate`, `phd` |
| `organization` | string | Partial match (ILIKE) against `jobs.organization` free-text column |
| `department` | string | Partial match (ILIKE) against `jobs.department` |
| `limit` | int | 1-100, default: 20 |
| `offset` | int | Default: 0 |

Default ordering (no `q`): `created_at DESC`.

**Note:** There is no `status` filter parameter on `GET /jobs` — the endpoint always excludes `inactive` jobs (`status != 'inactive'`).

**Job list response includes `organization_logo_url`** fetched from `organizations` table via `organization_id`.

---

## Admissions (Public)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/admissions` | Public | List admissions excluding `inactive` (stream/admission_type/FTS filters) |
| GET | `/admissions/eligibility/{slug}` | User JWT | Per-admission eligibility check against user profile |
| GET | `/admissions/{slug}` | Public | Admission detail by slug (includes admit cards, answer keys, results) |

**Query Parameters for `GET /admissions`:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Full-text search |
| `stream` | string | `medical`, `engineering`, `law`, `management`, `arts_science`, `general` |
| `admission_type` | string | `ug`, `pg`, `doctoral`, `lateral` |
| `limit` | int | 1-100, default: 20 |
| `offset` | int | Default: 0 |

**Note:** There is no `status` filter on public listing. The endpoint excludes `inactive` (`status != 'inactive'`). Both `active` and `upcoming` admissions are returned to the public.

---

## Admit Cards, Answer Keys, and Results (Public)

These are top-level resources, each linked to either a job OR an admission via polymorphic FKs.

### Admit Cards

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admit-cards` | List all admit cards (paginated) |
| GET | `/admit-cards/{id}` | Get single admit card by ID |

### Answer Keys

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/answer-keys` | List all answer keys (paginated) |
| GET | `/answer-keys/{id}` | Get single answer key by ID |

### Results

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/results` | List all results (paginated) |
| GET | `/results/{id}` | Get single result by ID |

---

## Notifications

All require a user JWT.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications` | List notifications (paginated, newest first) |
| GET | `/notifications/count` | Unread notification count |
| PUT | `/notifications/read-all` | Mark all unread as read |
| PUT | `/notifications/{id}/read` | Mark single notification as read |
| DELETE | `/notifications/{id}` | Delete a notification (204) |

**Query Parameters for `GET /notifications`:**

| Param | Type | Description |
|-------|------|-------------|
| `type` | string | Filter by notification type |
| `is_read` | boolean | Filter read/unread |
| `limit` | int | 1-100, default: 20 |
| `offset` | int | Default: 0 |

**Notification Types in use:** `deadline_reminder_7d`, `deadline_reminder_3d`, `deadline_reminder_1d`, `tracked_item_updated`, `new_job_from_followed_org`

**Delivery channels:** in-app (always), FCM push, email, WhatsApp. Channel delivery is controlled by `notification_preferences`.

---

## FCM Tokens & Notification Preferences

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/users/me/fcm-token` | User | Register FCM device token (max 10 per user) |
| DELETE | `/users/me/fcm-token` | User | Unregister FCM token by token value |
| PUT | `/users/me/notification-preferences` | User | Merge-update preference fields |
| DELETE | `/users/me/notification-preferences` | User | Reset preferences to `{}` |

**Notification preferences fields:**
- `email` (bool) — default enabled if unset
- `push` (bool) — default enabled if unset
- `whatsapp` (bool) — default enabled if unset; WhatsApp is a placeholder (not yet active)
- `in_app` — always delivered; there is no preference check for in-app

**FCM token registration body:**
```json
{ "token": "<FCM-device-token>", "device_name": "Pixel 7" }
```
FCM tokens are stored in `user_profiles.fcm_tokens` JSONB. Max 10 per user. Duplicates are de-duplicated by token value.

---

## Smart Notification Routing

All notifications are routed through `NotificationService` (sync, runs inside Celery tasks) via the `smart_notify` Celery task.

### Two Delivery Modes

| Mode | In-app | Push | Email | WhatsApp | Use case |
|------|--------|------|-------|----------|----------|
| `instant` | T+0 | T+0 | T+0 | T+0 | OTP, welcome, urgent |
| `staggered` | T+0 | T+0 | T+`NOTIFY_EMAIL_DELAY` (default 15 min) | T+`NOTIFY_WHATSAPP_DELAY` (default 1 hr) | Job alerts, deadline reminders |

### Channel Delivery Details

| Channel | Source | Notes |
|---------|--------|-------|
| In-app | Always inserted into `notifications` table | No preference check |
| FCM Push | Reads from `user_devices` table (`is_active=true`, `fcm_token IS NOT NULL`) | De-duplicated by `device_fingerprint`. Skipped if no active devices |
| Email | Reads email from `users` table | Subject to OCI 2700/day soft cap (tracked in Redis). Skipped if no email |
| WhatsApp | Reads phone from `user_profiles` or `users.phone` | Placeholder — always returns `False`; no external API configured |

Every delivery attempt is logged in `notification_delivery_log` with statuses: `pending`, `sent`, `delivered`, `failed`, `queued`, `skipped`.

---

## Admin Endpoints

All admin endpoints require an admin JWT (`user_type: "admin"`).

### Content Management — Jobs

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/jobs` | Operator+ | List all jobs (any status) |
| POST | `/admin/jobs` | Operator+ | Create job |
| GET | `/admin/jobs/{id}` | Operator+ | Get job by ID |
| PUT | `/admin/jobs/{id}` | Operator+ | Update job |
| DELETE | `/admin/jobs/{id}` | Admin only | Delete job (cascade) |

### Content Management — Admissions

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/admissions` | Operator+ | List all admissions (any status) |
| POST | `/admin/admissions` | Operator+ | Create admission |
| GET | `/admin/admissions/{id}` | Operator+ | Get admission by ID |
| PUT | `/admin/admissions/{id}` | Operator+ | Update admission |
| DELETE | `/admin/admissions/{id}` | Admin only | Delete admission (cascade) |

### Content Management — Admit Cards

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/admit-cards` | Operator+ | List all admit cards |
| POST | `/admin/admit-cards` | Operator+ | Create admit card (specify `job_id` OR `admission_id`) |
| PUT | `/admin/admit-cards/{id}` | Operator+ | Update admit card |
| DELETE | `/admin/admit-cards/{id}` | Operator+ | Delete admit card |

### Content Management — Answer Keys

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/answer-keys` | Operator+ | List all answer keys |
| POST | `/admin/answer-keys` | Operator+ | Create answer key (specify `job_id` OR `admission_id`) |
| PUT | `/admin/answer-keys/{id}` | Operator+ | Update answer key |
| DELETE | `/admin/answer-keys/{id}` | Operator+ | Delete answer key |

### Content Management — Results

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/results` | Operator+ | List all results |
| POST | `/admin/results` | Operator+ | Create result (specify `job_id` OR `admission_id`) |
| PUT | `/admin/results/{id}` | Operator+ | Update result |
| DELETE | `/admin/results/{id}` | Operator+ | Delete result |

### User Management

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/users` | Operator+ | List users (search by name/email; filter by status) |
| GET | `/admin/users/{id}` | Operator+ | User detail with partial profile |
| PUT | `/admin/users/{id}/status` | Admin only | Suspend or activate user (also disables/enables Firebase account) |
| DELETE | `/admin/users/{id}` | Admin only | Permanently delete user from PostgreSQL AND Firebase |

### Admin Self

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/me` | Operator+ | Get currently authenticated admin/operator profile |

### Admin Account Management

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/admin/admin-users` | Admin only | Create a new admin or operator account |
| GET | `/admin/admin-users` | Admin only | List all admin/operator accounts |
| GET | `/admin/admin-users/{id}` | Admin only | Get a single admin/operator account |
| PUT | `/admin/admin-users/{id}` | Admin only | Update admin/operator (name, phone, dept, role, status) |
| DELETE | `/admin/admin-users/{id}` | Admin only | Delete admin account (cannot delete own account) |

**Create admin user body:**
```json
{
  "email": "operator@hermes.com",
  "password": "Oper@123", <!-- pragma: allowlist secret -->
  "full_name": "New Operator",
  "role": "operator",
  "phone": null,
  "department": null
}
```

### Dashboard & Logs

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/stats` | Operator+ | Counts for jobs, admissions, admit_cards, answer_keys, results, users |
| GET | `/admin/logs` | Admin only | Admin audit trail (filterable by admin_id, action, resource_type, date_from, date_to) |

### Organizations (Admin CRUD)

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/organizations` | Operator+ | List all organizations |
| POST | `/admin/organizations` | Operator+ | Create organization |
| GET | `/admin/organizations/{id}` | Operator+ | Get organization by ID |
| PUT | `/admin/organizations/{id}` | Operator+ | Update organization (name, slug, short_name, logo_url, website_url, org_type) |
| DELETE | `/admin/organizations/{id}` | Admin only | Delete organization (linked jobs get `organization_id = NULL`) |

**Stats response:**
```json
{
  "jobs": { "total": 7, "active": 6 },
  "admit_cards": { "total": 15 },
  "answer_keys": { "total": 3 },
  "results": { "total": 2 },
  "admissions": { "total": 5, "active": 4 },
  "users": { "total": 3, "active": 3, "new_this_week": 1 }
}
```

**Side effects on admin write operations:**
- Creating/updating a job → triggers `recompute_eligibility_for_job.delay(job_id)`
- Creating/updating a job to `active` → triggers `notify_trackers_on_update.delay("job", job_id)`
- Creating a new job → triggers `send_new_job_notifications.delay(job_id)` (notifies org followers)
- Creating/updating an admission → triggers `recompute_eligibility_for_admission.delay(admission_id)`
- Creating/updating an admission to `active` → triggers `notify_trackers_on_update.delay("admission", admission_id)`

---

## Health Check

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | Public | Returns `{"status": "ok"}` |

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

| HTTP Status | Error Code | Trigger |
|-------------|-----------|---------|
| 400 | `VALIDATION_EMAIL_EXISTS` | Email already registered |
| 401 | `AUTH_INVALID_CREDENTIALS` | Invalid token or wrong type |
| 401 | `AUTH_TOKEN_REVOKED` | Token in Redis blocklist |
| 401 | `AUTH_TOKEN_EXPIRED` | Token past expiry |
| 403 | `FORBIDDEN_PERMISSION_DENIED` | Wrong scope or role |
| 403 | `FORBIDDEN_ADMIN_ONLY` | Non-admin accessing admin endpoint |
| 404 | `NOT_FOUND_USER` | User not found |
| 404 | `NOT_FOUND_JOB` | Job not found |
| 404 | `NOT_FOUND_APPLICATION` | Application not found |
| 422 | `VALIDATION_MISSING_FIELD` | Pydantic validation error (includes per-field details) |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `SERVER_ERROR` | Unhandled exception |

**Note:** 409 (conflict) responses are raised directly with `detail` strings, not the structured error format. The error format applies to HTTPException and RequestValidationError handlers only.

---

## Application Fee Fields

Fees are stored in a `fee` JSONB field on both `jobs` and `admissions`. Keys are optional.

| Key | Description |
|-----|-------------|
| `general` | Fee for General / UR |
| `obc` | Fee for OBC-NCL |
| `sc_st` | Fee for SC / ST |
| `ews` | Fee for EWS |
| `female` | Fee for Female / PwBD |

`0` = Free. Omitting a key means fee not specified.

---

## Celery Beat Schedule

| Task | Schedule | Description |
|------|----------|-------------|
| `send_deadline_reminders` | Daily 08:00 UTC | T-7, T-3, T-1 reminders for tracked jobs + admissions |
| `purge_expired_notifications` | Daily 01:00 UTC | Delete notifications past `expires_at` |
| `purge_expired_admin_logs` | Daily 01:30 UTC | Delete admin logs past `expires_at` |
| `purge_soft_deleted_jobs` | Daily 02:00 UTC | Hard-delete soft-deleted jobs |
| `close_expired_job_listings` | Daily 02:30 UTC | Auto-close jobs past `application_end` |
| `update_admission_statuses` | Daily 02:35 UTC | Auto-update admission statuses |
| `generate_sitemap` | Daily 04:00 UTC | Regenerate `sitemap.xml` with all active jobs |

---

## SEO

- Sitemap generated daily at 04:00 UTC via `tasks/seo.py`; saved to `SITEMAP_PATH` (default `/app/sitemap.xml`); served via Nginx

---

## Database Tables

| Table | Description |
|-------|-------------|
| `users` | Regular user accounts (Firebase-linked) |
| `admin_users` | Admin/operator accounts (bcrypt, role-based) |
| `user_profiles` | Extended profile (education, category, location, FCM tokens, notification preferences) |
| `user_devices` | Device registry (FCM token, fingerprint — used for push de-duplication) |
| `user_tracks` | Polymorphic tracking: `entity_type` ∈ `{job, admission, organization}` |
| `job_eligibility` | Pre-computed eligibility per (user, job) — populated by Celery |
| `admission_eligibility` | Pre-computed eligibility per (user, admission) — populated by Celery |
| `organizations` | Organization registry (slug, org_type, logo_url) |
| `jobs` | Job vacancy postings with FTS vector |
| `admissions` | Admissions (NEET, JEE, CLAT, CAT, GATE etc.) |
| `admit_cards` | Admit cards linked to job OR admission (polymorphic) |
| `answer_keys` | Answer keys linked to job OR admission (polymorphic) |
| `results` | Results linked to job OR admission (polymorphic) |
| `notifications` | User notification records |
| `notification_delivery_log` | Per-channel delivery tracking |
| `admin_logs` | Admin audit trail (auto-expire 30 days) |
