# Hermes API Reference

Base URL: `http://localhost:8000/api/v1`

All list endpoints return: `{ "data": [...], "pagination": { "limit", "offset", "total", "has_more" } }`

---

## Authentication

### User Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | Public | Create user account |
| POST | `/auth/login` | Public | Login → JWT token pair |
| POST | `/auth/logout` | User JWT | Invalidate token (Redis blocklist) |
| POST | `/auth/refresh` | Public | Rotate token pair |
| POST | `/auth/forgot-password` | Public | Request password reset email |
| POST | `/auth/reset-password` | Public | Reset password with token |
| GET | `/auth/verify-email/:token` | Public | Verify email address |
| GET | `/auth/csrf-token` | Public | Generate CSRF token |

### Admin Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/admin/login` | Public | Admin/operator login → JWT |
| POST | `/auth/admin/logout` | Admin JWT | Invalidate admin token |
| POST | `/auth/admin/refresh` | Public | Rotate admin token pair |

**JWT Claims:**
- `user_type`: `"user"` or `"admin"` — determines which table to look up
- `role`: (admin tokens only) `"admin"` or `"operator"`
- `sub`: UUID of the user/admin
- `jti`: unique token ID (used for blocklist)

---

## User Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users/profile` | User | Get own profile + user data |
| PUT | `/users/profile` | User | Update profile fields |
| PUT | `/users/profile/phone` | User | Update phone number |

---

## Job Vacancies (Public)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/jobs` | Public | List active jobs (filtered, paginated, FTS) |
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
| PUT | `/admin/jobs/:id` | Operator+ | Update job |
| PUT | `/admin/jobs/:id/approve` | Operator+ | Approve draft → active |
| DELETE | `/admin/jobs/:id` | Admin only | Soft-delete (→ cancelled) |

### User Management

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/users` | Operator+ | List users (search by name/email) |
| GET | `/admin/users/:id` | Operator+ | User detail with profile |
| PUT | `/admin/users/:id/status` | Admin only | Suspend or activate user |

### Dashboard & Logs

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/stats` | Operator+ | Job/user counts |
| GET | `/admin/logs` | Admin only | Admin audit trail |

---

## Request/Response Examples

### Register
```
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "Test User"
}
→ 201 { "id": "uuid", "email": "...", "full_name": "...", "message": "Registration successful..." }
```

### Login
```
POST /api/v1/auth/login
{ "email": "user@example.com", "password": "SecurePass123" }
→ 200 { "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }
```

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

---

## Error Responses

All errors follow: `{ "detail": "Error message" }`

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Unauthorized (invalid/expired/revoked token) |
| 403 | Forbidden (wrong role or token scope) |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate email) |
| 422 | Validation error (Pydantic) |

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
| `admin_logs` | Admin audit trail |
