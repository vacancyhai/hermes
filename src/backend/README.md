# Hermes - Backend Service

## Overview

This is the **Backend Service** for Hermes - a completely independent REST API service that can serve multiple frontend clients (Web, Mobile, Desktop).

**Technology Stack:**
- Flask (Python web framework)
- PostgreSQL 16 (Relational Database)
- Redis (Cache + Task Queue)
- Celery (Background tasks)
- JWT (Authentication)

**Port:** 5000
**API Base:** `/api/v1/`

---

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
nano .env
# Update all values, especially:
# - PostgreSQL credentials (DB_USER, DB_PASSWORD, DB_NAME)
# - Redis password
# - Secret keys
# - Email credentials
# - CORS origins (frontend URLs)
```

### 2. Start Backend Services

```bash
docker-compose up -d --build
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 5000)
- Celery Worker (background tasks)
- Celery Beat (scheduler)

### 3. Verify Services

```bash
# Check all containers
docker-compose ps

# View logs
docker-compose logs -f

# Test API health
curl http://localhost:5000/api/v1/health
# Should return: {"status": "healthy"}
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1/`

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh JWT token

### Jobs
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/jobs/<id>` - Get job details
- `POST /api/v1/jobs` - Create job (Admin only)
- `PUT /api/v1/jobs/<id>` - Update job (Admin only)
- `DELETE /api/v1/jobs/<id>` - Delete job (Admin only)

### Users
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `GET /api/v1/users/preferences` - Get user preferences
- `PUT /api/v1/users/preferences` - Update preferences

### Notifications
- `GET /api/v1/notifications` - Get user notifications
- `PUT /api/v1/notifications/<id>/read` - Mark as read

### Admin
- `GET /api/v1/admin/stats` - Dashboard statistics
- `GET /api/v1/admin/users` - List all users
- `GET /api/v1/admin/analytics` - Analytics data

---

## Environment Variables

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `DB_USER` - PostgreSQL username
- `DB_PASSWORD` - PostgreSQL password
- `DB_NAME` - PostgreSQL database name
- `REDIS_URL` - Redis connection URL
- `SECRET_KEY` - Flask secret key (minimum 32 characters)
- `JWT_SECRET_KEY` - JWT signing key
- `MAIL_SERVER` - SMTP server (e.g., smtp.gmail.com)
- `MAIL_USERNAME` - Email username
- `MAIL_PASSWORD` - Email password

**Optional:**
- `CORS_ORIGINS` - Allowed frontend origins, comma-separated (default: `http://localhost:8080,http://frontend:8080`)
- `BACKEND_PORT` - API port (default: 5000)
- `RATE_LIMIT_PER_IP` - Rate limit per IP in requests/minute (default: 100)
- `RATE_LIMIT_PER_USER` - Rate limit per user in requests/minute (default: 1000)
- `DB_POOL_SIZE` - PostgreSQL connection pool size (default: 20)
- `DB_MAX_OVERFLOW` - PostgreSQL connection pool overflow (default: 40)

---

## CORS Configuration

By default, the backend allows requests from:
- `http://localhost:8080` (local frontend)
- `http://frontend:8080` (Docker frontend)

To add more origins, update `CORS_ORIGINS` in `.env`:

```env
CORS_ORIGINS=http://localhost:8080,https://yourdomain.com,https://app.yourdomain.com
```

---

## Database

**PostgreSQL Tables:**
- `users` - User accounts and authentication
- `user_profiles` - Extended user profile information
- `job_vacancies` - Job postings with detailed eligibility
- `user_job_applications` - User applications tracking
- `notifications` - User notifications and alerts
- `results` - Exam results and cutoff marks
- `admit_cards` - Admit card information
- `answer_keys` - Answer key releases with objection data
- `admissions` - University/college admissions
- `yojanas` - Government schemes/yojanas
- `board_results` - Board exam results
- `categories` - Job categories and organizations
- `page_views` - Analytics - page view tracking
- `search_logs` - Analytics - search history
- `role_permissions` - Dynamic RBAC permission mapping
- `access_audit_logs` - Access control audit trail

**Database Migrations:**

```bash
# Run migrations (Alembic)
docker-compose exec backend flask db upgrade
```

**Backup Database:**

```bash
# Create backup (custom format - compressed)
docker-compose exec postgresql pg_dump \
  -U hermes_user -d hermes_db \
  -F c -f /backup/hermes_backup_$(date +%Y%m%d_%H%M%S).dump

# Restore from backup
docker-compose exec postgresql pg_restore \
  -U hermes_user -d hermes_db \
  /backup/hermes_backup_YYYYMMDD_HHMMSS.dump
```

**View Database:**

```bash
# Connect to PostgreSQL CLI
docker-compose exec postgresql psql -U hermes_user -d hermes_db

# List tables
\dt

# View schema
\d users
```

---

## Celery Tasks

**Background Tasks:**
- Send email notifications
- Send push notifications
- Match jobs with users
- Deadline reminders
- Database cleanup

**View Celery Workers:**

```bash
docker-compose logs -f celery_worker
```

**View Celery Beat (Scheduler):**

```bash
docker-compose logs -f celery_beat
```

---

## Management Commands

**View Logs:**
```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

**Restart Services:**
```bash
docker-compose restart
docker-compose restart backend
```

**Stop Services:**
```bash
docker-compose down
```

**Clean Everything:**
```bash
docker-compose down -v
```

**Scale Celery Workers:**
```bash
docker-compose up -d --scale celery_worker=3
```

---

## Folder Structure

```
src/backend/
├── docker-compose.yml       # Service orchestration
├── Dockerfile               # Backend container
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
├── README.md                # This file
│
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── routes/             # API endpoints
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   ├── tasks/              # Celery tasks
│   ├── middleware/         # Middleware
│   ├── utils/              # Utilities
│   └── validators/         # Input validators
│
├── config/
│   ├── settings.py         # App settings (PostgreSQL config)
│   └── redis_config.py     # Redis config
│
├── alembic/                # Database migrations
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
│
└── logs/
    ├── app.log
    └── error.log
```

---

## Independent Deployment

This backend service is **completely independent** and can:

1. ✅ Run without any frontend
2. ✅ Serve multiple frontends (Web, iOS, Android)
3. ✅ Be deployed on a different server
4. ✅ Scale independently
5. ✅ Be tested independently

**Test API without Frontend:**

```bash
# Register user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Get jobs (with JWT token)
curl http://localhost:5000/api/v1/jobs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Security

- ✅ JWT Authentication (15 min access + 7 day refresh tokens)
- ✅ Password hashing (bcrypt)
- ✅ Rate limiting (IP + User level)
- ✅ CORS protection
- ✅ Input validation
- ✅ SQL injection prevention
- ✅ RBAC (Role-Based Access Control)

---

## Support

For backend-related issues:
1. Check logs: `docker-compose logs -f backend`
2. Verify database: Check PostgreSQL connection
3. Check Redis: Verify Redis is running
4. Review environment variables in `.env`

---

**Last Updated:** March 2026
**Version:** 2.0 (Separated Architecture)
