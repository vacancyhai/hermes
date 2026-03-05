# Sarkari Path - Backend Service

## Overview

This is the **Backend Service** for Sarkari Path - a completely independent REST API service that can serve multiple frontend clients (Web, Mobile, Desktop).

**Technology Stack:**
- Flask (Python web framework)
- MongoDB (Database)
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
# - MongoDB credentials
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
- MongoDB (port 27017)
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
- `MONGO_URI` - MongoDB connection string
- `REDIS_URL` - Redis connection URL
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key
- `MAIL_SERVER` - SMTP server
- `MAIL_USERNAME` - Email username
- `MAIL_PASSWORD` - Email password

**Optional:**
- `CORS_ORIGINS` - Allowed frontend origins (comma-separated)
- `BACKEND_PORT` - API port (default: 5000)
- `RATE_LIMIT_PER_IP` - Rate limit per IP (default: 100)
- `RATE_LIMIT_PER_USER` - Rate limit per user (default: 1000)

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

**MongoDB Collections:**
- `users` - User accounts
- `jobs` - Job postings
- `notifications` - User notifications
- `applications` - User job applications
- `preferences` - User preferences
- `audit_logs` - Audit trail

**Backup Database:**

```bash
docker-compose exec mongodb mongodump \
  --uri="mongodb://sarkaripath_user:password@localhost:27017/sarkari_path?authSource=sarkari_path" \
  --out=/backup
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
│   ├── settings.py         # App settings
│   ├── database.py         # MongoDB config
│   └── redis_config.py     # Redis config
│
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
2. Verify database: Check MongoDB connection
3. Check Redis: Verify Redis is running
4. Review environment variables in `.env`

---

**Last Updated:** March 2026
**Version:** 2.0 (Separated Architecture)
