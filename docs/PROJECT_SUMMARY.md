# Hermes - Quick Start Guide

## 📋 What This Project Does

**Hermes** is a comprehensive government job notification portal that:
- ✅ Shows latest government job vacancies (Railway, SSC, UPSC, Banking, Police, Defense, Teaching)
- ✅ Sends personalized notifications based on user qualifications (10th, 12th, Graduation) and physical standards
- ✅ Tracks application deadlines with automatic reminders
- ✅ Provides admit card, exam date, answer key, and result notifications
- ✅ Supports Board Results (CBSE, UP Board, Bihar Board, etc.)
- ✅ Government Schemes/Yojanas (PM Kisan, Scholarships, etc.)
- ✅ College/University Admissions (JEE, NEET, etc.)
- ✅ Admin panel for complete content management
- ✅ Advanced analytics and search tracking

> **🗄️ Database**: Enhanced 15-table PostgreSQL 16 schema (expanded from 6 to support complete Hermes job notification portal features)

---

## 🏗️ Architecture Overview

### Three-Service Design (INDEPENDENT Backend + Two Frontends)

Three completely separate services, each with its own Docker Compose file and Docker network. Backend is shared — both frontends call it via HTTP REST.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        THREE INDEPENDENT SERVICES                         │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│   BACKEND SERVICE   │   │  USER FRONTEND      │   │  ADMIN FRONTEND     │
│   (src/backend/)    │   │  (src/frontend/)    │   │  (src/frontend-     │
│                     │◄──│                     │   │   admin/)           │
│   Port: 5000        │HTTP│  Port: 8080        │   │                     │
│                     │REST│                    │   │  Port: 8081         │
│   docker-compose:   │API │  docker-compose:   │   │                     │
│   - PostgreSQL      │   │  - frontend only   │◄──│  docker-compose:    │
│   - Redis           │   │                    │HTTP│  - frontend-admin   │
│   - Backend API     │   │  Serves:           │REST│    only             │
│   - Celery Worker   │   │  - Register/Login  │API │                     │
│   - Celery Beat     │   │  - Job browsing    │   │  Serves:            │
│                     │   │  - User profile    │   │  - Admin login      │
│   Exposes: /api/v1/ │   │  - Notifications   │   │  - Dashboard        │
│                     │   │                    │   │  - User management  │
│                     │   │  Audience:         │   │  - Job management   │
│                     │   │  Public users      │   │                     │
│                     │   │                    │   │  Audience:          │
│                     │   │                    │   │  admin + operator   │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

**Architecture Benefits:**
- ✅ **Complete Separation**: Each service in its own folder with independent Docker Compose
- ✅ **Security isolation**: Admin interface on a separate port/container — can be firewalled from public internet
- ✅ **Independent Deployment**: Deploy backend without restarting either frontend (and vice versa)
- ✅ **Independent Scaling**: Scale backend and each frontend separately based on load
- ✅ **Tech Stack Flexibility**: Replace any frontend (Flask → React → Mobile) WITHOUT touching backend
- ✅ **API Versioning**: All endpoints use `/api/v1/` for future compatibility
- ✅ **Separated Celery**: Beat (scheduler = 1 instance) and Workers (executors = scalable)
- ✅ **Different Servers**: Deploy backend on a private server, user frontend on edge, admin frontend on internal network

---

## 📁 Project Structure (Three Independent Services)

```
hermes/
├── src/                              # 🚀 All source code
│   │
│   ├── backend/                      # 🔧 BACKEND SERVICE (port 5000)
│   │   ├── docker-compose.yml        # PostgreSQL, Redis, API, Celery Worker, Celery Beat
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   ├── run.py
│   │   ├── app/
│   │   │   ├── routes/               # API endpoints (/api/v1/*)
│   │   │   ├── models/               # SQLAlchemy ORM models (PostgreSQL)
│   │   │   ├── services/             # Business logic (auth_service ✅)
│   │   │   ├── middleware/           # JWT auth, RBAC, error handlers
│   │   │   ├── validators/           # Marshmallow schemas (auth ✅)
│   │   │   └── tasks/                # Celery background tasks
│   │   ├── config/
│   │   └── tests/                    # 74 tests passing ✅
│   │
│   ├── frontend/                     # 🎨 USER FRONTEND SERVICE (port 8080)
│   │   ├── docker-compose.yml        # User frontend only
│   │   ├── Dockerfile
│   │   ├── .env.example
│   │   ├── run.py
│   │   ├── app/
│   │   │   ├── routes/               # Page routes (/, /auth, /jobs, /profile)
│   │   │   ├── templates/            # Jinja2 HTML
│   │   │   ├── static/               # CSS, JS, images
│   │   │   └── utils/                # api_client.py (calls backend)
│   │   └── config/
│   │
│   ├── frontend-admin/               # 👨‍💼 ADMIN FRONTEND SERVICE (port 8081)
│   │   ├── docker-compose.yml        # Admin frontend only
│   │   ├── Dockerfile
│   │   ├── .env.example
│   │   ├── run.py
│   │   ├── app/
│   │   │   ├── routes/               # Page routes (/auth, /dashboard, /users, /jobs)
│   │   │   ├── templates/            # Jinja2 HTML (admin/operator views)
│   │   │   ├── static/               # CSS, JS, images
│   │   │   └── utils/                # api_client.py (calls backend)
│   │   └── config/
│   │
│   └── nginx/                        # 🌐 REVERSE PROXY (ports 80/443)
│       ├── docker-compose.yml        # References backend + frontend + frontend-admin networks
│       └── nginx.conf                # Routes /api/* → backend, /* → frontend, /admin/* → frontend-admin
│
├── docs/
├── config/                           # Env templates per environment
├── scripts/
└── README.md
```

**Key Points:**
- ✅ Backend lives in `src/backend/` — shared API for both frontends
- ✅ User frontend lives in `src/frontend/` — public users only (register, login, jobs, profile)
- ✅ Admin frontend lives in `src/frontend-admin/` — admin + operator only (dashboard, user mgmt, job mgmt)
- ✅ Each service has its own `.env` file, Docker Compose file, and Docker network
- ✅ Both frontends call the backend via HTTP REST API (`BACKEND_API_URL`)
- ✅ Can run any service independently: `cd src/<service> && docker-compose up`
- ✅ Can replace any frontend without touching backend code

---

## 🚀 Quick Deployment (10 Minutes)

### Prerequisites
- Docker & Docker Compose installed
- Domain name (optional, for production SSL)
- SMTP email credentials (Gmail/Outlook)

### Option 1: Deploy Both Services Together (Development)

**1. Clone Repository**
```bash
git clone https://github.com/SumanKr7/hermes.git
cd hermes
```

**2. Deploy Backend First**
```bash
cd src/backend

# Configure backend environment
cp .env.example .env
nano .env
```

Required backend environment variables:
```env
# PostgreSQL
SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:your_db_password@postgresql:5432/hermes_db
DB_POOL_SIZE=20

# Redis
REDIS_PASSWORD=your_redis_password

# Flask
SECRET_KEY=your-secret-key-min-32-characters
JWT_SECRET_KEY=your-jwt-secret-key

# Email (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Firebase (for push notifications)
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# Backend Port
BACKEND_PORT=5000

# Note: Database is hermes_db
```

**3. Start Backend Services**
```bash
# From src/backend/
docker-compose up -d --build
```

This starts:
- ✅ PostgreSQL 16 (database)
- ✅ Redis (cache & queue)
- ✅ Backend API (Flask REST API on port 5000)
- ✅ Celery Worker (background tasks)
- ✅ Celery Beat (scheduler)

**4. Verify Backend**
```bash
# Check backend containers
docker-compose ps

# View backend logs
docker-compose logs -f backend

# Test backend API
curl http://localhost:5000/api/v1/health
# Should return: {"status":"healthy"}
```

**5. Deploy User Frontend**
```bash
cd ../frontend

# Configure frontend environment
cp .env.example .env
nano .env
```

Required frontend environment variables:
```env
# Backend API URL (where frontend calls backend)
BACKEND_API_URL=http://localhost:5000/api/v1

# Frontend Port
FRONTEND_PORT=8080

# Flask Secret
SECRET_KEY=your-frontend-secret-key

# Session Configuration
SESSION_TIMEOUT=3600
```

**6. Start User Frontend Service**
```bash
# From src/frontend/
docker-compose up -d --build
```

This starts:
- ✅ User Frontend (Flask + Jinja2 on port 8080)

**7. Deploy Admin Frontend**
```bash
cd ../frontend-admin

# Configure admin frontend environment
cp .env.example .env
nano .env
```

Required admin frontend environment variables:
```env
# Backend API URL
BACKEND_API_URL=http://localhost:5000/api/v1

# Admin Frontend Port
FRONTEND_ADMIN_PORT=8081

# Flask Secret (must differ from user frontend secret)
SECRET_KEY=your-admin-frontend-secret-key

# Session Configuration
SESSION_TIMEOUT=3600
```

**8. Start Admin Frontend Service**
```bash
# From src/frontend-admin/
docker-compose up -d --build
```

This starts:
- ✅ Admin Frontend (Flask + Jinja2 on port 8081)

**9. Verify Both Frontends**
```bash
# Test user frontend
curl http://localhost:8080/health
# Returns: {"status":"healthy","service":"frontend"}

# Test admin frontend
curl http://localhost:8081/health
# Returns: {"status":"healthy","service":"frontend-admin"}
```

**10. Access Application**
- Backend API: `http://localhost:5000/api/v1/`
- User Website: `http://localhost:8080`
- Admin Panel: `http://localhost:8081`

**Note:** Database name is `hermes_db` (changed from `sarkari_path`)

---

### Option 2: Deploy on Separate Servers (Production)

**Backend Server (e.g., 192.168.1.10)**
```bash
# On backend server
cd hermes/src/backend
cp .env.example .env
# Edit .env with production values
docker-compose up -d --build

# Expose port 5000 to network (or use internal IP)
# Backend API: http://192.168.1.10:5000/api/v1/
```

**User Frontend Server (e.g., 192.168.1.20)**
```bash
cd hermes/src/frontend
cp .env.example .env
# BACKEND_API_URL=http://192.168.1.10:5000/api/v1
docker-compose up -d --build
# User Frontend: http://192.168.1.20:8080
```

**Admin Frontend Server (e.g., 192.168.1.30 — internal network recommended)**
```bash
cd hermes/src/frontend-admin
cp .env.example .env
# BACKEND_API_URL=http://192.168.1.10:5000/api/v1
docker-compose up -d --build
# Admin Frontend: http://192.168.1.30:8081
```

---

### Option 3: Deploy with Nginx (Production with SSL)

**Deploy Backend**
```bash
cd src/backend
docker-compose up -d --build
# Backend running on port 5000
```

**Deploy User Frontend**
```bash
cd src/frontend
docker-compose up -d --build
# User Frontend running on port 8080
```

**Deploy Admin Frontend**
```bash
cd src/frontend-admin
docker-compose up -d --build
# Admin Frontend running on port 8081
```

**Setup Nginx Reverse Proxy**
```bash
# Install Nginx on host machine (not in container)
sudo apt install nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/hermes
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # User Frontend
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Admin Frontend — separate server block or subdomain recommended
server {
    listen 80;
    server_name admin.yourdomain.com;

    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/hermes /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

**Access Application**
- Website: `https://yourdomain.com`
- Backend API: `https://yourdomain.com/api/v1/`

---

## 🔧 Management Commands

### Backend Management (src/backend/)

**View Logs**
```bash
cd src/backend

# All backend services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgresql      # Database: hermes_db
docker-compose logs -f redis
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

**Restart Services**
```bash
cd src/backend

# All backend services
docker-compose restart

# Specific service
docker-compose restart backend
docker-compose restart celery_worker
```

**Update Backend Code**
```bash
cd src/backend

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Or update specific service
docker-compose up -d --no-deps --build backend
```

**Database Operations**
```bash
cd src/backend

# Access PostgreSQL shell
docker-compose exec postgresql psql -U hermes_user -d hermes_db

# Backup database
docker-compose exec postgresql pg_dump -U hermes_user -d hermes_db -F c -f /backup/hermes_backup.dump

# View Redis keys
docker-compose exec redis redis-cli -a your_redis_password
```

**Stop & Clean Up Backend**
```bash
cd src/backend

# Stop all backend containers
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

---

### User Frontend Management (src/frontend/)

**View Logs**
```bash
cd src/frontend
docker-compose logs -f frontend
```

**Restart / Update**
```bash
cd src/frontend
git pull origin main
docker-compose up -d --build
```

**Stop**
```bash
cd src/frontend
docker-compose down
```

---

### Admin Frontend Management (src/frontend-admin/)

**View Logs**
```bash
cd src/frontend-admin
docker-compose logs -f frontend-admin
```

**Restart / Update**
```bash
cd src/frontend-admin
git pull origin main
docker-compose up -d --build
```

**Stop**
```bash
cd src/frontend-admin
docker-compose down
```

---

### All Services Management

**Update All**
```bash
cd src/backend && git pull && docker-compose up -d --build && cd ../..
cd src/frontend && git pull && docker-compose up -d --build && cd ../..
cd src/frontend-admin && git pull && docker-compose up -d --build && cd ../..
```

**Stop All**
```bash
cd src/backend && docker-compose down && cd ../..
cd src/frontend && docker-compose down && cd ../..
cd src/frontend-admin && docker-compose down && cd ../..
```

**Clean Everything**
```bash
cd src/backend && docker-compose down -v && cd ../..
cd src/frontend && docker-compose down -v && cd ../..
cd src/frontend-admin && docker-compose down -v && cd ../..
docker system prune -a
```

---

## 📊 How It Works

### 1. User Flow
```
User registers → Creates profile (education, preferences)
    ↓
Admin posts new job
    ↓
Celery matches job with eligible users (education/age/category)
    ↓
Notifications sent (Email + Push + In-app)
    ↓
User receives notification → Views job → Applies
    ↓
Celery sends deadline reminders (7d, 3d, 1d before)
```

### 2. Frontend-Backend Communication (SEPARATED SERVICES)

**🎯 KEY**: Frontend and Backend are SEPARATE services calling each other via HTTP.

**Frontend (Flask + Jinja2):**
```python
# src/frontend/app/routes/jobs.py
from app.utils.api_client import APIClient
import os

# Backend URL from environment variable
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000/api/v1')

@bp.route('/jobs')
def job_list():
    # Frontend calls backend API via HTTP
    # No internal Docker network - uses external HTTP call
    jobs_data, status = APIClient.get(f'{BACKEND_API_URL}/jobs', params={'limit': 20})
    
    # Render template with data
    return render_template('jobs/job_list.html', jobs=jobs_data)
```

**Backend (Flask API):**
```python
# src/backend/app/routes/jobs.py
@bp.route('/api/v1/jobs', methods=['GET'])
def get_jobs():
    limit = request.args.get('limit', 20)
    jobs = Job.find_all(limit=limit)
    return jsonify({'jobs': jobs}), 200
```

**Communication Flow:**
```
User Browser
    ↓
Frontend Service (src/frontend/) - Port 8080
    ├─ User requests: http://yoursite.com/jobs
    ├─ Frontend route handler receives request
    ├─ Frontend makes HTTP call to backend
    ↓
HTTP Request: http://backend-url:5000/api/v1/jobs
    ├─ Headers: Authorization: Bearer <JWT>
    ├─ Headers: X-Request-ID: <uuid>
    └─ Params: ?limit=20
    ↓
Backend Service (src/backend/) - Port 5000
    ├─ Receives HTTP request on /api/v1/jobs
    ├─ Validates JWT token
    ├─ Fetches data from PostgreSQL via SQLAlchemy
    └─ Returns JSON response
    ↓
HTTP Response: JSON
    ├─ Status: 200
    ├─ Headers: X-Request-ID
    └─ Body: {jobs: [...]}
    ↓
Frontend Service
    ├─ Receives JSON data
    ├─ Renders HTML template with data
    └─ Sends HTML to user browser
    ↓
User sees job listings page
```

**Environment Configuration:**

Backend (.env in src/backend/):
```env
BACKEND_PORT=5000
SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:password@postgresql:5432/hermes_db
REDIS_URL=redis://:password@redis:6379/0
```

Frontend (.env in src/frontend/):
```env
FRONTEND_PORT=8080
BACKEND_API_URL=http://localhost:5000/api/v1  # Dev
# BACKEND_API_URL=http://backend-server-ip:5000/api/v1  # Production
# BACKEND_API_URL=https://api.yoursite.com/api/v1  # Production with domain
```

**🔄 Future: Replace Frontend with React**

When migrating to React, you only need to:
1. Replace `src/frontend/` folder with React app
2. Update React API calls to same `BACKEND_API_URL`
3. **ZERO CHANGES to backend!** 🎉

React API call example:
```javascript
// src/frontend/src/services/api.js
const BACKEND_API_URL = process.env.REACT_APP_BACKEND_API_URL;

export const getJobs = async (limit = 20) => {
  const response = await fetch(`${BACKEND_API_URL}/jobs?limit=${limit}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Request-ID': generateUUID()
    }
  });
  return await response.json();
};
```

Same backend, different frontend technology! ✨

### 3. Notification System

**Triggers:**
1. **New Job Posted** → Celery task matches with users → Sends notifications
2. **Deadline Reminder** → Celery beat checks daily → Sends reminders
3. **Admit Card Released** → Admin updates job → Notifications sent
4. **Result Announced** → Admin updates job → Notifications sent

**Channels:**
- 📧 **Email**: Flask-Mail via SMTP (Gmail/Outlook)
- 📱 **Push**: Firebase Cloud Messaging (web + mobile)
- 🔔 **In-app**: Stored in PostgreSQL notifications table

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Complete project documentation with database schemas, API endpoints, deployment guides |
| **WORKFLOW_DIAGRAMS.md** | ASCII diagrams showing 10 system workflows (registration, job matching, notifications, etc.) |
| **PROJECT_STRUCTURE.md** | Folder tree with implementation status (✅/🟡/❌) for every file, plus known design issues |
| **PROJECT_SUMMARY.md** | This file - quick start guide and overview |

---

## 🔐 Security Features

- ✅ **Password Hashing**: bcrypt (salted)
- ✅ **JWT Authentication**: Short-lived access tokens (15 min) + long-lived refresh tokens (7 days)
- ✅ **Token Rotation**: Auto-refresh prevents compromise exposure
- ✅ **Role-Based Access Control**: Admin, User, Operator roles with permission matrix
- ✅ **Rate Limiting**: IP-level (100 req/min) + User-level (1000 req/min) + Login (5 attempts/min)
- ✅ **CORS**: Only whitelisted origins allowed, credentials protected
- ✅ **HTTPS/SSL**: Let's Encrypt with HSTS headers
- ✅ **Input Validation**: Email, password, and all user inputs sanitized
- ✅ **Database Auth**: PostgreSQL and Redis password protected
- ✅ **Security Headers**: X-Frame-Options, X-Content-Type-Options, CSP, HSTS, etc.
- ✅ **Secrets Management**: .env in dev, Vault/AWS Secrets in production
- ✅ **API Versioning**: `/api/v1/` allows safe upgrades

---

## � Database & API Standards

**Database**:
- ✅ **Indexed queries**: Job searches use database indexes (10x faster)
- ✅ **TTL cleanup**: Old notifications/logs auto-delete (saves storage)
- ✅ **Denormalization (optional)**: Cache user job matches for faster matching

**API Responses**:
- ✅ **Standardized errors**: All errors use same format (code, message, details)
- ✅ **Pagination**: All lists support limit/offset (cursor-based for large datasets)
- ✅ **Request timeouts**: 10-second timeout, 3-retry exponential backoff
- ✅ **Notification retries**: Failed emails auto-retry up to 5 times


---
## ⚡ Advanced Design Improvements (13 New Features)

### Configuration & Security
- ✅ **JWT Token Rotation**: 15-min access + 7-day refresh (not 1-hour + 30-day)
- ✅ **Rate Limiting Config**: 100 req/min per IP, 1000 req/min per user
- ✅ **Request Timeout**: 10-second timeout per API request
- ✅ **Connection Pooling**: PostgreSQL SQLAlchemy pool_size=20, Redis socket keepalive
- ✅ **Data Retention Policy**: Notifications 90d, Logs 30d, Audits 1 year auto-cleanup

### Error Handling & Tracing
- ✅ **Error Code Taxonomy**: AUTH_*, VALIDATION_*, FORBIDDEN_*, RATE_LIMIT_*, SERVER_* codes
- ✅ **Request ID Propagation**: X-Request-ID header traced through all services
- ✅ **Correlation Tracking**: Search all logs by request_id to debug full request flow

### Performance & Caching
- ✅ **Redis Cache Strategy**: Cache-aside pattern with TTL by data type
  - Sessions: 15 min, Jobs: 1 hour, Preferences: 24 hours, Rate limits: 1 min
- ✅ **Celery Task Routing**: HIGH (email), MEDIUM (matching), LOW (analytics) queues
- ✅ **API Response SLAs**: Auth < 100ms, Read < 200ms, Write < 300ms, Search < 500ms, Admin < 1000ms

### Resilience & Graceful Degradation
- ✅ **Failed Email Handling**: Queue + auto-retry 5x with exponential backoff
- ✅ **FCM Fallback**: To in-app notification + email if push fails
- ✅ **Database Slow Response**: Return cached data with STALE_DATA flag
- ✅ **Celery Down**: Accept job, queue in Redis, process when available
- ✅ **Connection Pool Exhausted**: Queue request (10s timeout), 503 on failure

---
## �📈 Scaling Guide

### Vertical Scaling (Increase Resources)
```yaml
# In docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'      # Increase from 1
          memory: 2G     # Increase from 1G
```

### Horizontal Scaling (More Containers)
```bash
# Scale backend workers
docker compose up -d --scale backend=3

# Scale celery workers
docker compose up -d --scale celery_worker=3
```

### Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test backend API
ab -n 1000 -c 10 http://localhost/api/jobs

# Test frontend
ab -n 1000 -c 10 http://localhost/
```

---

## 🐛 Troubleshooting

### Issue: Containers not starting
```bash
# Check logs
docker compose logs postgresql redis

# Check if ports are in use
sudo lsof -i :80
sudo lsof -i :5432
sudo lsof -i :6379

# Solution: Stop conflicting services or change ports
```

### Issue: Frontend can't connect to backend
```bash
# Check if backend is healthy
curl http://localhost:5000/api/v1/health

# Check docker network
docker network inspect hermes_network

# Restart backend
docker compose restart backend
```

### Issue: Celery tasks not running
```bash
# Check celery worker logs
docker compose logs celery_worker celery_beat

# Check Redis connection
docker compose exec redis redis-cli -a your_redis_password ping

# Restart celery services
docker compose restart celery_worker celery_beat
```

### Issue: PostgreSQL connection failed
```bash
# Check PostgreSQL logs
docker compose logs postgresql

# Test connection
docker compose exec postgresql psql -U hermes_user -d hermes_db -c "SELECT 1;"

# Recreate PostgreSQL with fresh data
docker compose down -v
docker compose up -d postgresql
```

---

## 💡 Development Tips

### Local Development (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python run.py
```

**User Frontend:**
```bash
cd src/frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

**Admin Frontend:**
```bash
cd src/frontend-admin
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

**PostgreSQL & Redis:**
```bash
# Install locally or use Docker
docker run -d -p 5432:5432 -e POSTGRES_USER=hermes_user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=hermes_db postgres:16-alpine
docker run -d -p 6379:6379 redis:7-alpine
```

### Testing

**Backend API Tests:**
```bash
cd backend
pytest tests/
```

**Frontend Integration Tests:**
```bash
cd frontend
python -m pytest tests/
```

### Database Seeding (Sample Data)

```bash
# Create seed script: backend/seed_data.py
docker compose exec backend python seed_data.py
```

---

## 👥 User & Role Management

### Role Types

The system has **3 user roles** with different permissions:

| Role | Purpose | Can Create Jobs | Can Review Jobs | Can Access Admin Panel |
|------|---------|-----------------|-----------------|------------------------|
| **User** 👤 | Job seeker | ❌ | ❌ | ❌ |
| **Operator** 🔧 | Content reviewer | ❌ | ✅ | ❌ |
| **Admin** 👨‍💼 | Full control | ✅ | ✅ | ✅ |

### Step 1: Create First Admin (Bootstrap)

**New users always register with "user" role by default.** To create the first admin:

**Option A: PostgreSQL Direct Insert** (Quickest for first admin)
```bash
# Connect to PostgreSQL
docker compose exec postgresql psql -U hermes_user -d hermes_db

# Create admin user directly
INSERT INTO users (
  email, password_hash, full_name, role,
  is_verified, is_email_verified, status,
  created_at, last_login
) VALUES (
  'admin@example.com',
  '$2b$12$HASHED_PASSWORD_HERE',  -- Use bcrypt hash
  'Admin User', 'admin',
  TRUE, TRUE, 'active',
  NOW(), NOW()
);

\q
```
  role: "admin", // Directly set admin role
  is_verified: true,
  is_email_verified: true,
  status: "active",
  created_at: new Date(),
  last_login: new Date()
})

exit
```

**Option B: Register + Manual Update** (If app is running)
```bash
# 1. Register via API
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePassword123!",
    "name": "Admin User"
  }'

# 2. Update role in PostgreSQL
docker compose exec postgresql psql -U hermes_user -d hermes_db
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
\q
```

### Step 2: Create Operators (Admin-Only)

Only **Admin** users can create operators. Use this API endpoint:

**Endpoint:** `PUT /api/v1/admin/users/<user_id>/role`

**Request** (from admin account):
```json
{
  "new_role": "operator"
}
```

**cURL Example:**
```bash
# First register a user normally
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "operator@example.com",
    "password": "SecurePassword123!",
    "name": "Operator User"
  }'

# Get the user_id from response, then promote to operator
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

### Step 3: Create Another Admin (Admin-Only)

Same endpoint as operators, but use `"new_role": "admin"`:

```bash
curl -X PUT http://localhost:5000/api/v1/admin/users/USER_ID/role \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_role": "admin"}'
```

### Permission Matrix by Endpoint

| Endpoint | User | Operator | Admin |
|----------|------|----------|-------|
| `GET /api/v1/jobs` | ✅ | ✅ | ✅ |
| `GET /api/v1/jobs/<id>` | ✅ | ✅ | ✅ |
| `POST /api/v1/jobs` | ❌ | ❌ | ✅ |
| `PUT /api/v1/jobs/<id>` | ❌ | ✅ (limited) | ✅ |
| `DELETE /api/v1/jobs/<id>` | ❌ | ❌ | ✅ |
| `GET /api/v1/admin/users` | ❌ | ❌ | ✅ |
| `PUT /api/v1/admin/users/<id>/role` | ❌ | ❌ | ✅ |
| `GET /api/v1/admin/analytics` | ❌ | ❌ | ✅ |

**Operator Restrictions:** Operators can update job status and description, but NOT salary ranges or vacancy counts.

### Code Example: Promoting User to Operator

```python
# backend/app/routes/admin.py

from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps
from app.extensions import db
from app.models import User, AdminLog

bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')

def require_role(*allowed_roles):
    """Decorator to check user role"""
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')
            
            if user_role not in allowed_roles:
                return {"error": "FORBIDDEN_PERMISSION_DENIED"}, 403
            
            return fn(*args, **kwargs)
        return wrapped
    return decorator

@bp.route('/users/<user_id>/role', methods=['PUT'])
@jwt_required()
@require_role('admin')  # ⭐ Only admins can change roles
def change_user_role(user_id):
    """Change a user's role (admin only)"""
    data = request.json
    new_role = data.get('new_role')
    
    # Validate role
    if new_role not in ['user', 'operator', 'admin']:
        return {"error": "VALIDATION_INVALID_ROLE"}, 400
    
    # Find and update user
    user = User.query.get(user_id)

    if not user:
        return {"error": "NOT_FOUND_USER"}, 404

    old_role = user.role
    user.role = new_role
    db.session.add(AdminLog(
        action='role_changed',
        admin_id=get_jwt()['sub'],
        user_id=user_id,
        details={'new_role': new_role, 'old_role': old_role}
    ))
    db.session.commit()

    return {
        'user_id': str(user.id),
        'email': user.email,
        'role': user.role,
        'updated_at': user.updated_at.isoformat()
    }, 200
```

---

## 🔐 Dynamic Access Management

### Enable/Disable Access per Role

While the static **RBAC matrix** defines base permissions, sometimes you need **runtime control** - enable/disable access without code changes.

**Example:** Disable all user access during maintenance, or restrict delete operations for compliance.

### Three-Level Permission System

| Level | Example | Scope |
|-------|---------|-------|
| **Role-Based** | User can see jobs | All users with that role |
| **Resource-Based** | Can access /jobs but not /admin | Specific API resource |
| **Action-Based** | Can GET and PUT but not DELETE | HTTP method (GET/POST/PUT/DELETE) |
| **Field-Based** | Operator can't modify salary_max | Restrict sensitive fields per role |

### Quick Commands

**View current permissions:**
```bash
curl -X GET "http://localhost:5000/api/v1/admin/permissions?role=operator" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Restrict delete operations:**
```bash
curl -X PUT http://localhost:5000/api/v1/admin/permissions \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "operator",
    "resource": "jobs",
    "actions": {"GET": true, "POST": false, "PUT": true, "DELETE": false},
    "reason": "Compliance requirement"
  }'
```

**Emergency: Disable entire role:**
```bash
curl -X POST http://localhost:5000/api/v1/admin/permissions/disable-role \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"role": "user", "reason": "Maintenance mode"}'
```

**View permission change history:**
```bash
curl -X GET "http://localhost:5000/api/v1/admin/permissions/audit-log?role=operator" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**See [README.md - Dynamic Access Management](../README.md#-dynamic-access-management-system)** for complete API documentation and code examples.

---

## 🎯 Next Steps

After deployment:

1. **Create Admin User**
   - Follow the bootstrap instructions in [👥 User & Role Management](#-user--role-management) section
   - Use PostgreSQL direct insert or register + manual update methods

2. **Create Operators** (Optional)
   - Use the `PUT /api/v1/admin/users/<id>/role` endpoint from admin account
   - See code examples in role management section

3. **Post Test Job**
   - Login to admin frontend: `http://localhost:8081/auth/login`
   - Create a test job vacancy

3. **Test Notifications**
   - Register test user with profile
   - Check if notification is received

4. **Setup SSL**
   ```bash
   # Install certbot in nginx container
   docker compose exec nginx sh
   apk add certbot certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

5. **Setup Backups**
   - Configure automated PostgreSQL backups via pg_dump
   - Set up backup retention policy
   - Test restore procedure


---

## 📞 Support

- **Documentation**: Check all `.md` files in project root
- **Issues**: Create issue on GitHub repository
- **Logs**: Always check container logs first: `docker compose logs -f`

---

## 🎓 Learning Resources

**Flask Microservices:**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Compose Tutorial](https://docs.docker.com/compose/)
- [PostgreSQL with SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)

**Celery:**
- [Celery Documentation](https://docs.celeryproject.org/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html)

**Deployment:**
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Built with ❤️ for Indian job seekers**
