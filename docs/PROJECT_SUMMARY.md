# Sarkari Path - Quick Start Guide

## 📋 What This Project Does

**Sarkari Path** is a comprehensive government job notification portal that:
- ✅ Shows latest government job vacancies (Railway, SSC, UPSC, Banking, Police, Defense, Teaching)
- ✅ Sends personalized notifications based on user qualifications (10th, 12th, Graduation) and physical standards
- ✅ Tracks application deadlines with automatic reminders
- ✅ Provides admit card, exam date, answer key, and result notifications
- ✅ Supports Board Results (CBSE, UP Board, Bihar Board, etc.)
- ✅ Government Schemes/Yojanas (PM Kisan, Scholarships, etc.)
- ✅ College/University Admissions (JEE, NEET, etc.)
- ✅ Admin panel for complete content management
- ✅ Advanced analytics and search tracking

> **🗄️ Database**: Enhanced 15-collection MongoDB schema (expanded from 6 to support complete Sarkari Result portal features)

---

## 🏗️ Architecture Overview

### Fully Decoupled Services Design (INDEPENDENT Backend + Frontend)

**🎯 KEY CHANGE**: Backend and Frontend are **COMPLETELY SEPARATED** into different folders under `src/`. Each service runs independently with its own Docker Compose file. This allows replacing the frontend technology (Flask → React → iOS → Android) without touching the backend.

```
┌────────────────────────────────────────────────────────────┐
│                  SEPARATED SERVICES                         │
└────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐      ┌─────────────────────────────┐
│   BACKEND SERVICE           │      │   FRONTEND SERVICE          │
│   (src/backend/)            │◄─────│   (src/frontend/)           │
│                             │ HTTP │                             │
│   Port: 5000                │ REST │   Port: 8080 (or any)       │
│                             │ API  │                             │
│   docker-compose.yml:       │      │   docker-compose.yml:       │
│   - MongoDB                 │      │   - Frontend only           │
│   - Redis                   │      │                             │
│   - Backend API             │      │   API calls via HTTP:       │
│   - Celery Worker           │      │   http://backend:5000       │
│   - Celery Beat             │      │   /api/v1/*                 │
│                             │      │                             │
│   Exposes: /api/v1/*        │      │   Serves: HTML/SPA          │
│                             │      │                             │
│   Can deploy independently! │      │   Can deploy independently! │
│   Can scale independently!  │      │   Can scale independently!  │
│   Technology: Flask         │      │   Technology: Flask/React/  │
│   (Won't change)            │      │   Native iOS/Android        │
│                             │      │   (Can change anytime!)     │
└─────────────────────────────┘      └─────────────────────────────┘

          ↑                                      ↑
          │                                      │
    Deploy on Server 1                     Deploy on Server 2
    (or same server)                       (or same server)
```

**Architecture Benefits:**
- ✅ **Complete Separation**: Backend and frontend live in separate folders (`src/backend/`, `src/frontend/`)
- ✅ **Independent Deployment**: Deploy backend without restarting frontend (and vice versa)
- ✅ **Independent Scaling**: Scale backend and frontend separately based on load
- ✅ **Tech Stack Flexibility**: Replace frontend (Flask → React → Mobile) WITHOUT touching backend
- ✅ **API Versioning**: All endpoints use `/api/v1/` for future compatibility
- ✅ **Multiple Frontends**: Run Flask web + React Admin + iOS app ALL calling same backend API
- ✅ **Separated Celery**: Beat (scheduler = 1 instance) and Workers (executors = scalable)
- ✅ **Different Servers**: Deploy backend on powerful server, frontend on edge servers closer to users

---

## 📁 Project Structure (NEW: src/ Separation)

```
sarkari_path_2.0/
├── src/                              # 🚀 All source code
│   │
│   ├── backend/                      # 🔧 BACKEND SERVICE (INDEPENDENT)
│   │   ├── docker-compose.yml        # Backend: MongoDB, Redis, API, Celery
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.example              # Backend environment variables
│   │   ├── run.py
│   │   ├── app/
│   │   │   ├── routes/               # API endpoints (/api/v1/*)
│   │   │   ├── models/               # MongoDB models
│   │   │   ├── services/             # Business logic
│   │   │   └── tasks/                # Celery background tasks
│   │   ├── config/
│   │   ├── tests/
│   │   └── logs/
│   │
│   └── frontend/                     # 🎨 FRONTEND SERVICE (INDEPENDENT)
│       ├── docker-compose.yml        # Frontend only
│       ├── Dockerfile
│       ├── requirements.txt          # Flask deps (or package.json for React)
│       ├── .env.example              # Frontend environment variables
│       ├── run.py
│       ├── app/
│       │   ├── routes/               # Page routes (/, /jobs, /profile)
│       │   ├── templates/            # Jinja2 HTML (Flask only)
│       │   ├── static/               # CSS, JS, images (Flask only)
│       │   └── utils/
│       │       └── api_client.py     # Calls backend: http://backend:5000/api/v1/*
│       ├── config/
│       └── tests/
│
├── docs/                             # Documentation
├── epic/                             # Feature planning
├── config/                           # Environment configs (reference)
│   ├── development/
│   │   ├── .env.backend.dev
│   │   └── .env.frontend.dev
│   ├── staging/
│   └── production/
├── scripts/
│   └── deployment/
│       ├── deploy_backend.sh
│       ├── deploy_frontend.sh
│       └── deploy_all.sh
└── README.md
```

**Key Points:**
- ✅ Backend lives in `src/backend/` with its own docker-compose.yml
- ✅ Frontend lives in `src/frontend/` with its own docker-compose.yml
- ✅ Each service has its own .env file
- ✅ Each service can be git repository on its own
- ✅ Frontend calls backend via HTTP REST API
- ✅ Can run backend only: `cd src/backend && docker-compose up`
- ✅ Can run frontend only: `cd src/frontend && docker-compose up`
- ✅ Can replace frontend entirely without touching backend code!

---

## 🚀 Quick Deployment (10 Minutes)

### Prerequisites
- Docker & Docker Compose installed
- Domain name (optional, for production SSL)
- SMTP email credentials (Gmail/Outlook)

### Option 1: Deploy Both Services Together (Development)

**1. Clone Repository**
```bash
git clone https://github.com/SumanKr7/sarkari_path_2.0.git
cd sarkari_path_2.0
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
# MongoDB
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=your_secure_password
MONGO_USER=sarkaripath_user
MONGO_PASSWORD=your_db_password

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

# Backend API Port
BACKEND_PORT=5000
```

**3. Start Backend Services**
```bash
# From src/backend/
docker-compose up -d --build
```

This starts:
- ✅ MongoDB (database)
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

**5. Deploy Frontend**
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

**6. Start Frontend Service**
```bash
# From src/frontend/
docker-compose up -d --build
```

This starts:
- ✅ Frontend UI (Flask + Jinja2 on port 8080)

**7. Verify Frontend**
```bash
# Check frontend container
docker-compose ps

# View frontend logs
docker-compose logs -f frontend

# Test frontend
curl http://localhost:8080
# Should return HTML homepage
```

**8. Access Application**
- Backend API: `http://localhost:5000/api/v1/`
- Frontend Website: `http://localhost:8080`
- Admin panel: `http://localhost:8080/admin`

---

### Option 2: Deploy on Separate Servers (Production)

**Backend Server (e.g., 192.168.1.10)**
```bash
# On backend server
cd sarkari_path_2.0/src/backend
cp .env.example .env
# Edit .env with production values
docker-compose up -d --build

# Expose port 5000 to network (or use internal IP)
# Backend API: http://192.168.1.10:5000/api/v1/
```

**Frontend Server (e.g., 192.168.1.20)**
```bash
# On frontend server
cd sarkari_path_2.0/src/frontend
cp .env.example .env

# Set BACKEND_API_URL to backend server
nano .env
# BACKEND_API_URL=http://192.168.1.10:5000/api/v1

docker-compose up -d --build

# Frontend: http://192.168.1.20:8080
```

---

### Option 3: Deploy with Nginx (Production with SSL)

**Deploy Backend**
```bash
cd src/backend
docker-compose up -d --build
# Backend running on port 5000
```

**Deploy Frontend**
```bash
cd src/frontend
docker-compose up -d --build
# Frontend running on port 8080
```

**Setup Nginx Reverse Proxy**
```bash
# Install Nginx on host machine (not in container)
sudo apt install nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/sarkaripath
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Frontend
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
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/sarkaripath /etc/nginx/sites-enabled/
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
docker-compose logs -f mongodb
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

# Access MongoDB shell
docker-compose exec mongodb mongosh -u sarkaripath_user -p your_db_password --authenticationDatabase sarkari_path

# Backup database
docker-compose exec mongodb mongodump --uri="mongodb://sarkaripath_user:your_db_password@localhost:27017/sarkari_path?authSource=sarkari_path" --out=/backup

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

### Frontend Management (src/frontend/)

**View Logs**
```bash
cd src/frontend

# Frontend logs
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
```

**Restart Frontend**
```bash
cd src/frontend

# Restart frontend
docker-compose restart

# Or just restart specific service
docker-compose restart frontend
```

**Update Frontend Code**
```bash
cd src/frontend

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

**Stop & Clean Up Frontend**
```bash
cd src/frontend

# Stop frontend container
docker-compose down
```

---

### Both Services Management

**Update Both**
```bash
# Backend
cd src/backend && git pull && docker-compose up -d --build && cd ../..

# Frontend
cd src/frontend && git pull && docker-compose up -d --build && cd ../..
```

**Stop Both**
```bash
# Backend
cd src/backend && docker-compose down && cd ../..

# Frontend
cd src/frontend && docker-compose down && cd ../..
```

**Clean Everything**
```bash
# Remove all containers, volumes, images
cd src/backend && docker-compose down -v && cd ../..
cd src/frontend && docker-compose down -v && cd ../..
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
    ├─ Fetches data from MongoDB
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
MONGO_URI=mongodb://user:pass@mongodb:27017/sarkari_path
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
- 🔔 **In-app**: Stored in MongoDB notifications collection

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Complete project documentation with database schemas, API endpoints, deployment guides |
| **DOCKER_DEPLOYMENT.md** | Detailed Docker setup with all configuration files (Dockerfile, docker-compose.yml, nginx.conf) |
| **WORKFLOW_DIAGRAMS.md** | ASCII diagrams showing 10 system workflows (registration, job matching, notifications, etc.) |
| **JINJA2_TEMPLATES_GUIDE.md** | Complete Flask template architecture with examples (base.html, components, pages, email templates) |
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
- ✅ **Database Auth**: MongoDB and Redis password protected
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

**Monitoring**:
- ✅ **Centralized logging**: All container logs in Elasticsearch (ELK stack)
- ✅ **Full-text search**: Elasticsearch for job search (fuzzy matching, relevance)
- ✅ **APM**: Track API response times, database latency, Celery task performance
- ✅ **Real-time alerts**: Error rate, response time, memory usage thresholds

---
## ⚡ Advanced Design Improvements (13 New Features)

### Configuration & Security
- ✅ **JWT Token Rotation**: 15-min access + 7-day refresh (not 1-hour + 30-day)
- ✅ **Rate Limiting Config**: 100 req/min per IP, 1000 req/min per user
- ✅ **Request Timeout**: 10-second timeout per API request
- ✅ **Connection Pooling**: MongoDB 50-connection pool, Redis socket keepalive
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
docker compose logs mongodb redis

# Check if ports are in use
sudo lsof -i :80
sudo lsof -i :27017
sudo lsof -i :6379

# Solution: Stop conflicting services or change ports
```

### Issue: Frontend can't connect to backend
```bash
# Check if backend is healthy
curl http://localhost/api/health

# Check docker network
docker network inspect sarkari_network

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

### Issue: MongoDB connection failed
```bash
# Check MongoDB logs
docker compose logs mongodb

# Test connection
docker compose exec mongodb mongosh -u admin -p your_root_password

# Recreate MongoDB with fresh data
docker compose down -v
docker compose up -d mongodb
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

**Frontend:**
```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

**MongoDB & Redis:**
```bash
# Install locally or use Docker
docker run -d -p 27017:27017 mongo:7.0
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

**Option A: MongoDB Direct Insert** (Quickest for first admin)
```bash
# Connect to MongoDB
docker compose exec mongodb mongosh -u admin -p admin

# Switch to sarkari_path database
use sarkari_path

# Create admin user directly
db.users.insertOne({
  email: "admin@example.com",
  password: "$2b$12$HASHED_PASSWORD_HERE", // Use bcrypt hash
  full_name: "Admin User",
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

# 2. Update role in MongoDB
docker compose exec mongodb mongosh -u admin -p admin
use sarkari_path
db.users.updateOne(
  {email: "admin@example.com"},
  {$set: {role: "admin"}}
)
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
from bson import ObjectId

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
    from app.models import db
    user = db.users.find_one_and_update(
        {'_id': ObjectId(user_id)},
        {'$set': {'role': new_role, 'updated_at': datetime.utcnow()}},
        return_document=True
    )
    
    if not user:
        return {"error": "NOT_FOUND_USER"}, 404
    
    # Log audit trail
    admin_id = get_jwt()['sub']
    db.audit_trail.insert_one({
        'action': 'role_changed',
        'admin_id': ObjectId(admin_id),
        'user_id': ObjectId(user_id),
        'new_role': new_role,
        'old_role': user.get('role', 'user'),
        'timestamp': datetime.utcnow()
    })
    
    return {
        'user_id': str(user['_id']),
        'email': user['email'],
        'role': user['role'],
        'updated_at': user['updated_at'].isoformat()
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
   - Use MongoDB direct insert or register + manual update methods

2. **Create Operators** (Optional)
   - Use the `PUT /api/v1/admin/users/<id>/role` endpoint from admin account
   - See code examples in role management section

3. **Post Test Job**
   - Login to admin panel: `/admin`
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
   - Configure automated MongoDB backups
   - Set up backup retention policy
   - Test restore procedure

6. **Monitoring**
   - Setup application monitoring (Sentry, etc.)
   - Configure uptime monitoring
   - Setup alerts for errors

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
- [MongoDB with Python](https://pymongo.readthedocs.io/)

**Celery:**
- [Celery Documentation](https://docs.celeryproject.org/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html)

**Deployment:**
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Built with ❤️ for Indian job seekers**
