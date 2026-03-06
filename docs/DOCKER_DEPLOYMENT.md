# Docker Deployment Guide - Hermes

## Separated Microservices Architecture (INDEPENDENT Backend + Frontend)

**🎯 MAJOR CHANGE**: Backend and Frontend are now **COMPLETELY SEPARATED** into different folders under `src/`. Each service has its own Docker Compose file and can be deployed independently.

**Container Breakdown:**

### Backend Service (`src/backend/docker-compose.yml`):
1. **PostgreSQL** - Database with SQLAlchemy ORM
2. **Redis** - Cache + Queue (AOF persistence)
3. **Backend API** - Flask REST API (/api/v1/*)
4. **Celery Worker** - Background task executor (scalable: 1-N)
5. **Celery Beat** - Task scheduler (always 1 instance)

### Frontend Service (`src/frontend/docker-compose.yml`):
6. **Frontend** - Flask + Jinja2 UI (or React/Mobile in future)

**Total**: 6 containers across 2 services (vs 8 in previous monolithic setup)

## Why Separated Services Architecture?

### ✅ Advantages
1. **Complete Independence**: Backend and frontend can be developed without interfering
2. **Independent Deployment**: Update frontend without restarting backend (zero downtime)
3. **Independent Scaling**: Scale backend and frontend separately based on actual load
4. **Technology Flexibility**: Replace frontend (Flask → React → iOS → Android) WITHOUT touching backend
5. **Multiple Frontends**: Run Flask web + React admin + Mobile apps ALL calling same backend API
6. **Different Servers**: Deploy backend on powerful server, frontend on edge servers
7. **Cleaner Git History**: Can have separate repositories for backend and frontend
8. **Team Separation**: Backend team and frontend team don't conflict
9. **Easier Testing**: Test backend API independently without frontend
10. **API-First Design**: Backend is pure REST API, can serve any client

### 🔄 Migration Path
**Current**: Flask SSR (Server-Side Rendered HTML)
**Future Options** (NO backend changes needed):
- React SPA (Single Page Application)
- React Native (iOS + Android)
- Native iOS (Swift)
- Native Android (Kotlin)
- Flutter
- Any client that can make HTTP calls!

### ⚠️ Considerations Compared to Monolithic Docker Compose
- **Network Configuration**: Frontend must know backend URL (environment variable)
- **CORS Setup**: Backend must allow requests from frontend origin
- **Authentication**: Frontend must handle JWT tokens and pass to backend
- **Error Handling**: Frontend must handle backend API errors gracefully

### 📊 Recommendation
**YES, use separated services!** The flexibility and scalability benefits far outweigh the small additional complexity.

---

## Architecture Diagrams

### Overall System (Separated Services)

```
┌──────────────────────────────────────────────────────────────────┐
│              SEPARATED MICROSERVICES ARCHITECTURE                 │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐      ┌──────────────────────────────┐
│  BACKEND SERVICE            │      │  FRONTEND SERVICE            │
│  (src/backend/)             │◄─────│  (src/frontend/)             │
│                             │ HTTP │                              │
│  Port: 5000                 │ REST │  Port: 8080                  │
│                             │ API  │                              │
│  docker-compose.yml         │      │  docker-compose.yml          │
│  ┌─────────────────┐        │      │  ┌──────────────────┐       │
│  │ 1. PostgreSQL   │        │      │  │ Frontend         │       │
│  │    - Database   │        │      │  │ - Flask/Jinja2   │       │
│  │    - Port 5432  │        │      │  │ - Calls Backend  │       │
│  │    - Persistent │        │      │  │   via HTTP       │       │
│  └─────────────────┘        │      │  │ - Renders HTML   │       │
│                             │      │  └──────────────────┘       │
│  ┌─────────────────┐        │      │                              │
│  │ 2. Redis        │        │      │  Environment:                │
│  │    - Cache      │        │      │  BACKEND_API_URL=            │
│  │    - Task Queue │        │      │  http://backend:5000/api/v1  │
│  │    - Port 6379  │        │      │                              │
│  │    - AOF Persist│        │      │  Can be replaced with:       │
│  └─────────────────┘        │      │  - React SPA                 │
│            ↓                │      │  - React Native              │
│  ┌─────────────────┐        │      │  - iOS app                   │
│  │ 3. Backend API  │        │      │  - Android app               │
│  │    - Flask REST │        │      │  WITHOUT changing backend!   │
│  │    - /api/v1/*  │        │      │                              │
│  │    - JWT Auth   │        │      └──────────────────────────────┘
│  │    - CORS enabled│       │
│  └─────────────────┘        │             User Browser
│            ↓                │                  ↓
│  ┌─────────────────┐        │                  │
│  │ 4. Celery Worker│        │      ┌───────────┴───────────┐
│  │    - (1-N)      │        │      │                       │
│  │    - Tasks      │        │      ↓                       ↓
│  └─────────────────┘        │   Frontend              Direct API
│                             │   (HTML Pages)          (Mobile/SPA)
│  ┌─────────────────┐        │      ↓                       ↓
│  │ 5. Celery Beat  │        │      └───────── HTTP ────────┘
│  │    - (Always 1) │        │              ↓
│  │    - Scheduler  │        │      Backend REST API
│  └─────────────────┘        │      /api/v1/*
│                             │
│  Exposes: /api/v1/*         │
│  on localhost:5000          │
└─────────────────────────────┘

  Deploy on Server 1           Deploy on Server 2
  (or same server)             (or same server)
  Can scale separately!        Can scale separately!
```

### Container Communication Flow

```
User Request (Mobile/Web/Desktop)
    ↓
Frontend Service (src/frontend/ - Port 8080)
    ├─ Renders UI (HTML/React/Mobile)
    └─ Makes HTTP request to backend
    ↓
HTTP: http://BACKEND_URL:5000/api/v1/jobs
    ├─ Headers: Authorization: Bearer <JWT>
    ├─ Headers: X-Request-ID: <uuid>
    ├─ Headers: Origin: http://frontend-url
    └─ Body: JSON data
    ↓
Backend Service (src/backend/ - Port 5000)
    ├─ CORS check (allow frontend origin)
    ├─ JWT verification
    ├─ Rate limiting
    ├─ Route → Service → Model
    ↓
PostgreSQL / Redis
    ↓
Response: JSON
    ├─ Status: 200/400/401/500
    ├─ Headers: Access-Control-Allow-Origin
    ├─ Headers: X-Request-ID
    └─ Body: {data, error}
    ↓
Frontend receives JSON
    ├─ Parse data
    ├─ Update UI
    └─ Handle errors
    ↓
User sees result
```

---

## Docker Files

### 1. Backend Dockerfile (Flask REST API)

**src/backend/Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/v1/health')"

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "60", "run:app"]
```

### 2. Frontend Dockerfile (Flask + Jinja2)

**src/frontend/Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "30", "run:app"]
```

---

## Docker Compose Files (SEPARATED SERVICES)

### Backend Service: docker-compose.yml

**src/backend/docker-compose.yml** (Complete backend ecosystem):

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgresql:
    image: postgres:16-alpine
    container_name: hermes_postgresql
    restart: unless-stopped
    environment:
      POSTGRES_USER: hermes_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: hermes_db
    volumes:
      - postgresql_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"  # Expose to host (optional for external access)
    networks:
      - backend_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hermes_user -d hermes_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache & Broker
  redis:
    image: redis:7-alpine
    container_name: hermes_redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes --appendfsync everysec
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"  # Expose to host (optional for external access)
    networks:
      - backend_network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Backend API
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hermes_api
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:${DB_PASSWORD}@postgresql:5432/hermes_db
      - DB_POOL_SIZE=20
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
      - MAIL_SERVER=${MAIL_SERVER}
      - MAIL_PORT=${MAIL_PORT}
      - MAIL_USERNAME=${MAIL_USERNAME}
      - MAIL_PASSWORD=${MAIL_PASSWORD}
      - FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
      # CORS: Allow frontend origin
      - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:8080,http://frontend:8080}
    volumes:
      - ./app:/app/app
      - backend_logs:/app/logs
    ports:
      - "${BACKEND_PORT:-5000}:5000"  # Expose backend API to host
    depends_on:
      postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - backend_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/v1/health"]
      interval: 30s
      timeout: 10s
      start_period: 40s
      retries: 3

  # Celery Worker (Background Tasks)
  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hermes_celery_worker
    restart: unless-stopped
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
    environment:
      - SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:${DB_PASSWORD}@postgresql:5432/hermes_db
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
      - MAIL_SERVER=${MAIL_SERVER}
      - MAIL_PORT=${MAIL_PORT}
      - MAIL_USERNAME=${MAIL_USERNAME}
      - MAIL_PASSWORD=${MAIL_PASSWORD}
      - FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
    volumes:
      - ./app:/app/app
    depends_on:
      postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
      backend:
        condition: service_healthy
    networks:
      - backend_network

  # Celery Beat (Task Scheduler)
  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hermes_celery_beat
    restart: unless-stopped
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      - SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:${DB_PASSWORD}@postgresql:5432/hermes_db
      - DB_POOL_SIZE=20
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
    volumes:
      - ./app:/app/app
    depends_on:
      postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
      backend:
        condition: service_healthy
    networks:
      - backend_network

volumes:
  postgresql_data:
  redis_data:
  backend_logs:

networks:
  backend_network:
    driver: bridge
```

**Key Points:**
- ✅ Backend runs on port 5000 (exposed to host)
- ✅ All backend services (PostgreSQL, Redis, Celery) in one compose file
- ✅ Self-contained: Can run completely independently
- ✅ CORS enabled to allow frontend requests

---

### Frontend Service: docker-compose.yml

**src/frontend/docker-compose.yml** (Frontend only):

```yaml
version: '3.8'

services:
  # Frontend Application
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hermes_frontend
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      # Backend API URL - CRITICAL CONFIGURATION
      - BACKEND_API_URL=${BACKEND_API_URL:-http://localhost:5000/api/v1}
      # Session configuration
      - SESSION_TIMEOUT=${SESSION_TIMEOUT:-3600}
    volumes:
      - ./app:/app/app
      - ./templates:/app/templates
      - ./static:/app/static
    ports:
      - "${FRONTEND_PORT:-8080}:8080"  # Expose frontend to host
    networks:
      - frontend_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      start_period: 20s
      retries: 3

networks:
  frontend_network:
    driver: bridge
```

**Key Points:**
- ✅ Frontend runs on port 8080 (exposed to host)
- ✅ Minimal: Only frontend service (no database)
- ✅ `BACKEND_API_URL` environment variable points to backend
- ✅ Can be replaced with React app docker-compose in future

**Environment Configuration for Frontend:**

```bash
# src/frontend/.env
FRONTEND_PORT=8080
SECRET_KEY=your-frontend-secret-key
SESSION_TIMEOUT=3600

# Backend API URL - Change based on deployment
# Development (same machine):
BACKEND_API_URL=http://localhost:5000/api/v1

# Production (different server):
# BACKEND_API_URL=http://192.168.1.10:5000/api/v1
# BACKEND_API_URL=https://api.yourdomain.com/api/v1
```

---

## Deployment Procedures

### Development: Both Services on Same Machine

**Step 1: Start Backend**
```bash
cd src/backend
cp .env.example .env
# Edit .env with your values
nano .env
docker-compose up -d --build
docker-compose logs -f
```

**Step 2: Start Frontend**
```bash
cd src/frontend
cp .env.example .env
# Set BACKEND_API_URL=http://localhost:5000/api/v1
nano .env
docker-compose up -d --build
docker-compose logs -f
```

**Step 3: Access**
- Backend API: http://localhost:5000/api/v1/
- Frontend: http://localhost:8080

---

### Production: Services on Different Servers

**Backend Server (e.g., 192.168.1.10)**
```bash
cd src/backend
docker-compose up -d --build
# Backend API available at: http://192.168.1.10:5000/api/v1/
```

**Frontend Server (e.g., 192.168.1.20)**
```bash
cd src/frontend
# Edit .env
nano .env
# Set: BACKEND_API_URL=http://192.168.1.10:5000/api/v1
docker-compose up -d --build
# Frontend available at: http://192.168.1.20:8080
```

**Setup Nginx on Frontend Server (Optional - for SSL)**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

### 3. docker-compose.yml (OLD - Monolithic, for Reference Only)

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  # ⚡ IMPORTANT FOR PRODUCTION: This is single-node setup
  # For production failover, setup read replicas or use managed PostgreSQL (RDS, Cloud SQL)
  # Current setup: Suitable for development/staging with single-node persistence
  postgresql:
    image: postgres:16-alpine
    container_name: hermes_postgresql
    restart: unless-stopped
    environment:
      POSTGRES_USER: hermes_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: hermes_db
    volumes:
      - postgresql_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - hermes_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hermes_user -d hermes_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache & Broker with AOF Persistence
  # ⚡ AOF (Append-Only File) ensures data survives Redis restarts
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    container_name: hermes_redis
    restart: unless-stopped
    # ⚡ PERSISTENCE: Redis needs AOF persistence for task queue reliability
    # Without this, queued tasks die on restart
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes --appendfsync everysec
    volumes:
      - redis_data:/data
    networks:
      - hermes_network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    # Note: For production, consider Redis Cluster or Sentinel for HA
    # Current setup: Single instance with persistence, suitable for small-medium scale

### ⚡ Redis Caching Strategy

**Redis serves two purposes**:
1. **Celery Broker** (task queue) - DB updates → Celery task → Redis → Workers execute
2. **Cache Layer** (session/data cache) - App check Redis before querying PostgreSQL

**Cache-Aside Pattern** (Used throughout app):
```python
# backend/app/services/cache_service.py
def get_jobs(limit=20, page=1):
    cache_key = f"jobs:limit_{limit}:page_{page}"
    
    # Step 1: Check Redis cache
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)  # Cache hit!
    
    # Step 2: Cache miss - load from PostgreSQL
    jobs = Job.query.order_by(Job.created_at.desc()).limit(limit).offset((page-1)*limit).all()
    jobs_data = [j.to_dict() for j in jobs]
    
    # Step 3: Store in Redis for next request
    redis.setex(
        cache_key,
        3600,  # 1 hour
        json.dumps(jobs_data)
    )
    
    return jobs_data
```

**Cache TTL by Data Type**:
```
User Sessions:      15 min   (logged-in user)
Job Listings:       1 hour   (updated frequently)
User Preferences:   24 hours (rarely changed)
Search Results:     30 min   (popular searches)
Rate Limit Counts:  1 min    (sliding window)
Analytics Cache:    24 hours (daily aggregates)
```

**Cache Invalidation**:
```python
# When admin updates a job, invalidate cache
@bp.route('/api/v1/admin/jobs/<job_id>', methods=['PUT'])
def update_job(job_id):
    # Update in DB
    job = Job.update(job_id, request.json)
    
    # Invalidate all cache keys containing this job
    redis.delete(f"job:{job_id}")
    redis.delete_pattern("jobs:*")  # Clear all job list caches
    
    return jsonify(job), 200
```

---

## ⚡ PostgreSQL Data Retention & Scheduled Cleanup

**`expires_at` column + Celery nightly purge** handle scheduled data cleanup (saving storage costs):

```sql
-- In init.sql - Add expires_at columns for auto-cleanup via Celery

-- Notifications: expires after 90 days
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS
  expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '90 days');

-- Application Logs (admin_logs): expires after 30 days
ALTER TABLE admin_logs ADD COLUMN IF NOT EXISTS
  expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '30 days');

-- Search Logs: expires after 6 months
ALTER TABLE search_logs ADD COLUMN IF NOT EXISTS
  expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '180 days');

-- Create index on expires_at for fast cleanup queries
CREATE INDEX IF NOT EXISTS idx_notifications_expires_at ON notifications(expires_at);
CREATE INDEX IF NOT EXISTS idx_admin_logs_expires_at ON admin_logs(expires_at);
CREATE INDEX IF NOT EXISTS idx_search_logs_expires_at ON search_logs(expires_at);
```

**Celery Nightly Purge Task** (runs at 2:00 AM):
```python
# backend/app/tasks/maintenance.py
from app import db
from datetime import datetime

@celery.task
def purge_expired_rows():
    """Delete expired rows from all tables with expires_at column."""
    now = datetime.utcnow()
    tables = [Notification, AdminLog, SearchLog]
    for model in tables:
        deleted = model.query.filter(model.expires_at <= now).delete()
        db.session.commit()
        logger.info(f"Purged {deleted} rows from {model.__tablename__}")
```

**How It Works**:
```
Celery Beat triggers purge_expired_rows() nightly at 2:00 AM
Task queries all rows where expires_at <= NOW()
Deletes expired rows and commits transaction
Frees disk space automatically - no manual cleanup needed
```

**Storage Benefits**:
```
Without expires_at:  100,000 notifications per month
  × 12 months = 1.2M notifications stored forever
  Size: ~500 MB

With 90-day expires_at:  Only 300,000 notifications at any time
  Size: ~125 MB
  Savings: 75% disk space reduction
```

---
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: hermes_api
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:${DB_PASSWORD}@postgresql:5432/hermes_db
      - DB_POOL_SIZE=20
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
      - MAIL_SERVER=${MAIL_SERVER}
      - MAIL_PORT=${MAIL_PORT}
      - MAIL_USERNAME=${MAIL_USERNAME}
      - MAIL_PASSWORD=${MAIL_PASSWORD}
      - FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
    volumes:
      - ./backend:/app
      - backend_logs:/app/logs
    depends_on:
      # ⚡ Only start after dependencies are healthy
      postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - hermes_network
    # ⚡ Health check for backend - Nginx won't route to unhealthy backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/v1/health"]
      interval: 30s
      timeout: 10s
      start_period: 40s
      retries: 3
    
    # ⚡ SECRETS MANAGEMENT - Store sensitive data securely
    # NEVER commit secrets to git. Use one of:
    # Option 1 (Dev): .env file (in .gitignore)
    # Option 2 (Prod): HashiCorp Vault
    # Option 3 (Cloud): AWS Secrets Manager / Google Cloud Secrets
    # Current setup uses .env, but for production upgrade to Vault: 
    # vault kv get secret/hermes/db_password

  # Frontend UI Container
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: hermes_frontend
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - BACKEND_API_URL=http://backend:5000/api/v1  # ⚡ API v1
    volumes:
      - ./frontend:/app
    depends_on:
      # ⚡ Only start after backend is healthy
      backend:
        condition: service_healthy
    networks:
      - hermes_network
    # ⚡ Health check for frontend container
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      start_period: 40s
      retries: 3

  # ⚡ CELERY WORKER - SEPARATES task execution from scheduling
  # This container ONLY executes tasks from the queue
  # Separate from Celery Beat (which only schedules)
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: hermes_celery_worker
    restart: unless-stopped
    # ⚡ Only runs workers, NOT scheduler
    command: celery -A celery_worker.celery worker --loglevel=info --concurrency=2
    environment:
      - FLASK_ENV=production
      - SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:${DB_PASSWORD}@postgresql:5432/hermes_db
      - DB_POOL_SIZE=20
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
      - CELERY_TASK_ROUTES={"high":"email","medium":"matching","low":"analytics"}  # ⚡ Task routing
      - MAIL_SERVER=${MAIL_SERVER}
      - MAIL_PORT=${MAIL_PORT}
      - MAIL_USERNAME=${MAIL_USERNAME}
      - MAIL_PASSWORD=${MAIL_PASSWORD}
    volumes:
      - ./backend:/app
    depends_on:
      # ⚡ Workers wait for queue to be ready
      postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - hermes_network
    # ⚡ Can scale: docker compose up -d --scale celery_worker=3

  # ⚡ CELERY BEAT - ONLY controls scheduling, separate from workers
  # This container ONLY triggers scheduled tasks
  # Separate from Celery Worker (which executes tasks)
  # KEEP ONLY 1 BEAT INSTANCE (do NOT scale this)
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: hermes_celery_beat
    restart: unless-stopped
    # ⚡ Only runs scheduler (Beat), NOT workers
    command: celery -A celery_worker.celery beat --loglevel=info
    environment:
      - FLASK_ENV=production
      - SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:${DB_PASSWORD}@postgresql:5432/hermes_db
      - DB_POOL_SIZE=20
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    volumes:
      - ./backend:/app
    depends_on:
      # ⚡ Beat waits for queue to be ready
      - redis
    networks:
      - hermes_network
    # ⚡ IMPORTANT: Keep only 1 Beat (never scale with --scale)
    # Multiple Beats = duplicate scheduled tasks
    # For HA, use Celery Flower or external beat scheduler (Celery on Kubernetes)

  # Nginx Reverse Proxy with Health Checks
  # ⚡ Health checks ensure only healthy upstreams receive traffic
  nginx:
    image: nginx:alpine
    container_name: hermes_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      # ⚡ These conditions ensure services are healthy before Nginx starts
      frontend:
        condition: service_healthy
      backend:
        condition: service_healthy
    networks:
      - hermes_network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  hermes_network:
    driver: bridge

volumes:
  postgresql_data:
  redis_data:
  backend_logs:
```
```

### 3. .dockerignore

```
# .dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
ENV/
.venv
.git
.gitignore
.vscode
.idea
*.log
logs/
*.db
*.sqlite
.env.example
README.md
*.md
docker-compose.yml
Dockerfile
.DS_Store
node_modules/
```

### 4. init.sql (PostgreSQL Initialization)

```sql
-- init.sql
-- Creates application user and grants permissions

CREATE USER hermes_user WITH PASSWORD :'DB_PASSWORD';
CREATE DATABASE hermes_db OWNER hermes_user;
GRANT ALL PRIVILEGES ON DATABASE hermes_db TO hermes_user;

\c hermes_db

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ⚡ Production: Create B-tree and GIN indexes for performance
-- Users: unique email index
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- User profiles: unique user_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- Job search indexes (critical for performance with filters)
CREATE INDEX IF NOT EXISTS idx_job_vacancies_organization ON job_vacancies(organization);
CREATE INDEX IF NOT EXISTS idx_job_vacancies_status ON job_vacancies(status);
CREATE INDEX IF NOT EXISTS idx_job_vacancies_created_at ON job_vacancies(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_vacancies_eligibility ON job_vacancies USING GIN (eligibility);

-- Application tracking indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_job_apps_user_job
  ON user_job_applications(user_id, job_id);
CREATE INDEX IF NOT EXISTS idx_user_job_apps_user_date
  ON user_job_applications(user_id, applied_date DESC);

-- Notification query indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_read
  ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_user_date
  ON notifications(user_id, created_at DESC);
```

---

### 4a. ⚡ Production PostgreSQL High Availability Setup

**Why HA?** Single PostgreSQL instance = no failover. If it crashes, the entire system is down.

**For Production, use streaming replication** (1 primary + 1 standby) or a managed service (AWS RDS, Google Cloud SQL):

```bash
# Check PostgreSQL is running and healthy
docker compose exec postgresql pg_isready -U hermes_user -d hermes_db

# Connect to PostgreSQL
docker compose exec postgresql psql -U hermes_user -d hermes_db

# Run migrations
docker compose exec backend flask db upgrade

# Verify tables created
docker compose exec postgresql psql -U hermes_user -d hermes_db -c '\dt'
```

**Update Connection String for Read Replica** (optional):
```bash
# Primary (read/write)
SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:pass@postgresql:5432/hermes_db

# With read replica (using pgBouncer or SQLAlchemy routing)
SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:pass@pgbouncer:5432/hermes_db
```

**Benefits**:
- ✅ Streaming replication for automatic failover
- ✅ pg_dump for reliable backups
- ✅ pg_stat_activity for query analysis
- ✅ JSONB + GIN indexes for flexible querying

**Current Development Setup**: Single-node is fine; add streaming replication before going to production.

---

### 4b. ⚡ SQLAlchemy Connection Pooling Configuration

**Why Connection Pooling?** Creating new database connections is expensive (100-500ms). Connection pools reuse existing connections.

**Configuration in Environment Variables:**
```bash
# Development (low traffic)
SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:pass@postgresql:5432/hermes_db
DB_POOL_SIZE=5

# Production (high traffic)
SQLALCHEMY_DATABASE_URI=postgresql://hermes_user:pass@postgresql:5432/hermes_db
DB_POOL_SIZE=20
```

**SQLAlchemy Engine Configuration:**
```python
# backend/config/settings.py
from sqlalchemy import create_engine

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_size=20,          # Maximum 20 persistent connections
    max_overflow=30,       # Allow 30 extra connections under load
    pool_pre_ping=True,    # Verify connection health before use
    pool_recycle=3600,     # Recycle connections after 1 hour
    connect_args={"connect_timeout": 5}
)
```

**Connection Pool Parameters:**
- `pool_size=20` - Always keep 20 connections ready
- `max_overflow=30` - Allow up to 50 total under peak load
- `pool_pre_ping=True` - Auto-recover from dropped connections
- `pool_recycle=3600` - Prevent stale connection errors

**Benefits:**
- ✅ Faster query execution (no connection overhead)
- ✅ Prevents connection exhaustion
- ✅ Automatic connection recovery
- ✅ Better resource utilization

**Connection Pool Events:**
```python
# backend/app/utils/db_utils.py
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "connect")
def on_connect(dbapi_conn, connection_record):
    print(f"New DB connection established")

@event.listens_for(Pool, "checkout")
def on_checkout(dbapi_conn, connection_record, connection_proxy):
    print(f"Connection checked out from pool")

@event.listens_for(Pool, "checkin")
def on_checkin(dbapi_conn, connection_record):
    print(f"Connection returned to pool")
```

---

### 4c. ⚡ API Response Standards & Error Handling

**Standardized Error Response Format:**
All API errors follow this structure for consistent frontend handling:

```json
{
  "error": {
    "code": "AUTH_INVALID_TOKEN",
    "message": "Authentication token has expired",
    "details": {
      "expired_at": "2026-03-05T10:30:00Z",
      "token_type": "access_token"
    },
    "request_id": "abc123-def456-ghi789",
    "timestamp": "2026-03-05T10:35:00Z"
  }
}
```

**Error Code Taxonomy:**
```
AUTH_*         - Authentication errors (invalid token, expired session)
VALIDATION_*   - Input validation errors (invalid email, missing field)
FORBIDDEN_*    - Authorization errors (insufficient permissions)
NOT_FOUND_*    - Resource not found (user, job, notification)
RATE_LIMIT_*   - Rate limiting errors (too many requests)
SERVER_*       - Internal server errors (database down, service unavailable)
```

**API Response SLAs (Service Level Agreements):**
```
Auth endpoints (login/register):     < 100ms (p95)
Read endpoints (GET /jobs):          < 200ms (p95)
Write endpoints (POST /jobs):        < 300ms (p95)
Search endpoints (search with filters): < 500ms (p95)
Admin endpoints (analytics):         < 1000ms (p95)
```

**Request ID Propagation:**
Every request gets a unique ID for distributed tracing:

```python
# backend/app/middleware/request_id.py
import uuid
from flask import request, g

@app.before_request
def assign_request_id():
    # Use client-provided ID or generate new one
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    g.start_time = time.time()

@app.after_request
def add_request_id_header(response):
    # Add request ID to response for correlation
    response.headers['X-Request-ID'] = g.request_id
    response.headers['X-Response-Time'] = f"{(time.time() - g.start_time) * 1000:.2f}ms"
    return response
```

**Graceful Degradation Patterns:**
```python
# backend/app/services/job_service.py
def get_jobs(limit=20):
    try:
        # Try Redis cache first
        cached = redis.get(f"jobs:limit_{limit}")
        if cached:
            return json.loads(cached)
    except redis.ConnectionError:
        # Cache unavailable, continue to database
        logger.warning("Redis unavailable, falling back to database")
    
    try:
        # Load from PostgreSQL
        jobs = Job.query.order_by(Job.created_at.desc()).limit(limit).all()
        jobs_data = [j.to_dict() for j in jobs]
        
        # Try to cache for next time
        try:
            redis.setex(f"jobs:limit_{limit}", 3600, json.dumps(jobs_data))
        except redis.ConnectionError:
            pass  # Cache write failed, but we have the data
        
        return jobs_data
    except sqlalchemy.exc.OperationalError:
        # Database is down - return stale cache if available
        stale_cache = redis.get(f"jobs:limit_{limit}:backup")
        if stale_cache:
            return {
                "data": json.loads(stale_cache),
                "warning": "Using cached data (database temporarily unavailable)"
            }
        raise ServiceUnavailable("Database connection failed")
```

**Connection Pool Exhausted Handling:**
```python
# backend/app/utils/db_handler.py
from sqlalchemy.exc import OperationalError
import time

def execute_with_retry(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except OperationalError:
            if attempt == max_retries - 1:
                raise ServiceUnavailable("Database connection pool exhausted")
            # Exponential backoff: 100ms, 200ms, 400ms
            time.sleep(0.1 * (2 ** attempt))
            continue
```

---

### 4d. ⚡ Redis Socket Keepalive & Connection Management

**Redis Configuration for Production:**
```yaml
# In docker-compose.yml redis service
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --appendonly yes
    --requirepass ${REDIS_PASSWORD}
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
    --tcp-keepalive 60
    --timeout 300
```

**Backend Redis Client Configuration:**
```python
# backend/config/redis_config.py
import redis
from redis.connection import ConnectionPool

# Production-grade connection pool
redis_pool = ConnectionPool(
    host='redis',
    port=6379,
    password=os.getenv('REDIS_PASSWORD'),
    db=0,
    max_connections=50,
    socket_keepalive=True,
    socket_keepalive_options={
        socket.TCP_KEEPIDLE: 60,    # Start keepalive after 60s idle
        socket.TCP_KEEPINTVL: 10,   # Send keepalive every 10s
        socket.TCP_KEEPCNT: 3        # Close after 3 failed keepalives
    },
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30  # Check connection health every 30s
)

redis_client = redis.Redis(connection_pool=redis_pool)
```

**Benefits:**
- ✅ Prevents "connection reset by peer" errors
- ✅ Detects dead connections before use
- ✅ Automatic connection recovery
- ✅ Reduces Redis memory usage (closes idle connections)

---

### 5. nginx/nginx.conf (Nginx Reverse Proxy)

```nginx
# nginx/nginx.conf
events {
    worker_connections 2048;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 10M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;

    # ⚡ Rate limiting per user in Nginx
    # This prevents individual users from overwhelming the API
    limit_req_zone $binary_remote_addr zone=user_api_limit:10m rate=100r/m;  # 100 req/min per IP
    limit_req_zone $http_x_user_id zone=user_app_limit:10m rate=1000r/m;    # 1000 req/min per user
    
    location /api/ {
        # IP-based rate limiting (applies before auth)
        limit_req zone=user_api_limit burst=20 nodelay;
        
        # Also check authenticated user ID
        limit_req zone=user_app_limit burst=50 nodelay;
        
        # Rest of config...

    # Upstream backends
    upstream backend_api {
        server backend:5000 max_fails=3 fail_timeout=30s;
    }

    upstream frontend_app {
        server frontend:8080 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # API v1 requests → Backend container
        # ⚡ Request ID propagation for correlation tracking
        location /api/v1/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            # ⚡ Request ID for distributed tracing
            proxy_set_header X-Request-ID $request_id;
            proxy_redirect off;
            
            # Timeouts (⚡ 10-second timeout per API request for SLA compliance)
            proxy_connect_timeout 10s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
        }

        # Static files from frontend
        location /static/ {
            proxy_pass http://frontend_app/static/;
            proxy_set_header Host $host;
            
            # Cache static assets
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # All other routes → Frontend container
        location / {
            proxy_pass http://frontend_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "OK\n";
            add_header Content-Type text/plain;
        }
    }

    # HTTPS configuration (after SSL setup)
    # Uncomment after running certbot
    # server {
    #     listen 443 ssl http2;
    #     server_name yourdomain.com www.yourdomain.com;
    #
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #     ssl_protocols TLSv1.2 TLSv1.3;
    #     ssl_ciphers HIGH:!aNULL:!MD5;
    #
    #     # ... (same location blocks as above)
    # }
}
```
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Health check endpoint
        location /health {
            proxy_pass http://flask_app/health;
            access_log off;
        }

        # Static files
        location /static {
            alias /app/static;
            expires 30d;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # API rate limiting
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://flask_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        # Auth rate limiting
        location ~ ^/(login|register|auth) {
            limit_req zone=login_limit burst=5 nodelay;
            proxy_pass http://flask_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        # Main application
        location / {
            proxy_pass http://flask_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
            proxy_buffering off;
        }
    }
}
```

### 6. .env.example (Environment Variables Template)

```env
# .env.example
# Copy to .env and fill in your values

# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-min-32-chars-change-this

# API Configuration
API_VERSION=v1

# PostgreSQL Configuration with Connection Pooling
DB_PASSWORD=strong_db_password_change_this
# ⚡ Connection pool settings for production
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Redis Configuration with Socket Keepalive
REDIS_PASSWORD=strong_redis_password_change_this
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_KEEPALIVE=true

# Flask-Mail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Firebase Configuration (Optional - for push notifications)
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# JWT Configuration (⚡ Updated for security)
JWT_SECRET_KEY=jwt-secret-key-different-from-secret-key
JWT_ACCESS_TOKEN_EXPIRES=900  # 15 minutes (not 3600 = 1 hour)
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 days (not 2592000 = 30 days)

# Rate Limiting Configuration
RATE_LIMIT_PER_IP=100  # requests per minute per IP
RATE_LIMIT_PER_USER=1000  # requests per minute per authenticated user
RATE_LIMIT_LOGIN=5  # login attempts per minute

# Timeout Configuration
API_REQUEST_TIMEOUT=10  # seconds per API request
DB_CONNECTION_TIMEOUT=5  # seconds for database connection
REDIS_SOCKET_TIMEOUT=5  # seconds for Redis operations

# Data Retention Policy (in seconds)
NOTIFICATION_TTL=7776000  # 90 days
LOG_TTL=2592000  # 30 days
AUDIT_TTL=31536000  # 1 year

# Celery Configuration
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=Asia/Kolkata

# Admin Configuration
ADMIN_EMAIL=admin@yourdomain.com

# Application URL
APP_URL=https://yourdomain.com

# Logging
LOG_LEVEL=INFO
ENABLE_REQUEST_LOGGING=true
```

---

## Deployment Steps on Hostinger VPS

### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Deploy Application

```bash
# 1. Clone repository
cd /home/hermes
git clone https://github.com/SumanKr7/hermes.git
cd hermes

# 2. Create .env file
cp .env.example .env
nano .env  # Fill in your actual values

# 3. Create required directories
mkdir -p logs/nginx nginx/ssl

# 4. Build and start containers
docker compose up -d --build

# 5. Check container status
docker compose ps

# 6. View logs
docker compose logs -f

# 7. Setup SSL with Let's Encrypt (after DNS is configured)
docker compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  -d yourdomain.com -d www.yourdomain.com \
  --email your-email@example.com \
  --agree-tos --no-eff-email

# 8. Restart nginx to use SSL
docker compose restart nginx
```

### Add Certbot Service (docker-compose.yml)

Add this service to your docker-compose.yml for SSL:

```yaml
  certbot:
    image: certbot/certbot
    container_name: hermes_certbot
    volumes:
      - ./nginx/ssl:/etc/letsencrypt
      - ./certbot-webroot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - hermes_network
```


---

## Docker Management Commands

### Basic Operations
```bash
# Start all containers
docker compose up -d

# Stop all containers
docker compose down

# Restart all containers
docker compose restart

# View running containers
docker compose ps

# View logs
docker compose logs -f
docker compose logs -f app  # specific container

# Execute command in container
docker compose exec app bash
docker compose exec postgresql psql -U hermes_user -d hermes_db

# Update application (pull latest code)
cd /home/hermes/hermes
git pull origin main
docker compose up -d --build app celery_worker celery_beat
```

### Database Operations
```bash
# PostgreSQL shell access
docker compose exec postgresql psql -U hermes_user -d hermes_db

# Backup PostgreSQL
docker compose exec -T postgresql pg_dump -U hermes_user hermes_db > backup.sql

# Restore PostgreSQL
docker compose exec -T postgresql psql -U hermes_user -d hermes_db < backup.sql

# Redis CLI access
docker compose exec redis redis-cli -a your_redis_password
```

### Maintenance
```bash
# Remove stopped containers
docker compose down

# Remove all (including volumes - BE CAREFUL!)
docker compose down -v

# Clean up Docker system
docker system prune -a

# View disk usage
docker system df

# Update specific service
docker compose up -d --build --no-deps app
```

---

## Automated Backup Script (Docker)

Create `backup.sh`:

```bash
#!/bin/bash
# backup.sh - Docker PostgreSQL Backup Script

BACKUP_DIR="/home/hermes/backups/postgresql"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="hermes_backup_$DATE.dump"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL from Docker container
docker compose exec -T postgresql pg_dump \
  -U hermes_user \
  -d hermes_db \
  -F c \
  -f /tmp/$BACKUP_NAME

# Copy backup from container
docker compose cp postgresql:/tmp/$BACKUP_NAME $BACKUP_DIR/

# Delete backups older than 7 days
find $BACKUP_DIR -name "*.dump" -type f -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME"
```

```bash
# Make executable
chmod +x backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /home/hermes/hermes/backup.sh >> /home/hermes/logs/backup.log 2>&1
```

---

## Performance Optimization

### 1. Resource Limits (docker-compose.yml)
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### 2. Multi-stage Dockerfile (Smaller Image)
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["gunicorn", "-c", "gunicorn_config.py", "run:app"]
```

### 3. Docker Compose Override for Development
Create `docker-compose.override.yml`:

```yaml
version: '3.8'
services:
  app:
    command: flask run --host=0.0.0.0 --debug
    environment:
      - FLASK_ENV=development
    volumes:
      - .:/app
```

---

---

## 🔐 Security Features Implementation

This section details all security measures implemented in the Docker deployment as per PROJECT_SUMMARY.md.

### 1. Password Hashing & Authentication

**bcrypt with Salt:**
```python
# backend/app/utils/auth.py
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    # bcrypt automatically adds random salt
    return generate_password_hash(password, method='bcrypt')

def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)
```

### 2. JWT Token Rotation Strategy

**Short-lived Access Tokens + Long-lived Refresh Tokens:**

```python
# backend/app/routes/auth.py
from flask_jwt_extended import create_access_token, create_refresh_token

@bp.route('/api/v1/auth/login', methods=['POST'])
def login():
    user = authenticate_user(request.json)
    
    # ⚡ Access token: 15 minutes (not 1 hour)
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(minutes=15)
    )
    
    # ⚡ Refresh token: 7 days (not 30 days)
    refresh_token = create_refresh_token(
        identity=str(user.id),
        expires_delta=timedelta(days=7)
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 900  # 15 minutes in seconds
    }

@bp.route('/api/v1/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    
    # Issue new access token
    new_access_token = create_access_token(identity=current_user)
    
    return {'access_token': new_access_token}
```

**Token Rotation Benefits:**
- ✅ Reduces exposure window (compromised token invalid in 15 min)
- ✅ Prevents long-term token theft
- ✅ Automatic refresh for active users
- ✅ Forces re-authentication after 7 days

### 3. Role-Based Access Control (RBAC)

**Permission Decorator:**
```python
# backend/app/middleware/rbac.py
from functools import wraps
from flask_jwt_extended import get_jwt

def require_role(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role', 'user')
            
            if user_role not in allowed_roles:
                return {'error': 'FORBIDDEN_INSUFFICIENT_PERMISSIONS'}, 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Usage:
@bp.route('/api/v1/admin/users', methods=['GET'])
@jwt_required()
@require_role('admin')
def list_users():
    # Only admins can access
    pass
```

**Permission Matrix:**
| Endpoint | User | Operator | Admin |
|----------|------|----------|-------|
| GET /api/v1/jobs | ✅ | ✅ | ✅ |
| POST /api/v1/jobs | ❌ | ❌ | ✅ |
| PUT /api/v1/jobs/:id | ❌ | ✅ (limited) | ✅ |
| DELETE /api/v1/jobs/:id | ❌ | ❌ | ✅ |
| GET /api/v1/admin/* | ❌ | ❌ | ✅ |

### 4. Rate Limiting (Multi-Layer)

**Nginx Layer (IP-based):**
```nginx
# In nginx.conf
http {
    # ⚡ 100 requests per minute per IP
    limit_req_zone $binary_remote_addr zone=ip_limit:10m rate=100r/m;
    
    # ⚡ 1000 requests per minute per authenticated user
    limit_req_zone $http_x_user_id zone=user_limit:10m rate=1000r/m;
    
    # ⚡ 5 login attempts per minute
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
    
    server {
        location /api/v1/ {
            limit_req zone=ip_limit burst=20 nodelay;
            limit_req zone=user_limit burst=50 nodelay;
        }
        
        location /api/v1/auth/login {
            limit_req zone=login_limit burst=2 nodelay;
        }
    }
}
```

**Application Layer (Flask-Limiter):**
```python
# backend/app/__init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=f"redis://:{os.getenv('REDIS_PASSWORD')}@redis:6379/2",
    default_limits=["1000 per hour"]
)

# Per-endpoint limits
@bp.route('/api/v1/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    pass

@bp.route('/api/v1/jobs/search', methods=['GET'])
@limiter.limit("30 per minute")
def search_jobs():
    pass
```

### 5. CORS (Cross-Origin Resource Sharing)

```python
# backend/app/__init__.py
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://yourdomain.com",
            "https://www.yourdomain.com"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Request-ID"],
        "expose_headers": ["X-Request-ID", "X-Response-Time"],
        "supports_credentials": True,
        "max_age": 3600
    }
})
```

### 6. Security Headers (Nginx)

```nginx
# In nginx.conf - HTTPS server block
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

### 7. Input Validation & Sanitization

```python
# backend/app/validators/job_validator.py
from marshmallow import Schema, fields, validate, validates, ValidationError

class JobCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=5, max=200))
    organization = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    vacancies = fields.Int(required=True, validate=validate.Range(min=1, max=100000))
    salary_min = fields.Int(validate=validate.Range(min=0))
    salary_max = fields.Int(validate=validate.Range(min=0))
    
    @validates('salary_max')
    def validate_salary_range(self, value):
        if self.salary_min and value < self.salary_min:
            raise ValidationError("salary_max must be >= salary_min")

# Usage:
@bp.route('/api/v1/jobs', methods=['POST'])
@jwt_required()
@require_role('admin')
def create_job():
    schema = JobCreateSchema()
    try:
        validated_data = schema.load(request.json)
    except ValidationError as err:
        return {'error': 'VALIDATION_FAILED', 'details': err.messages}, 400
    
    job = Job.create(validated_data)
    return job, 201
```

### 8. Database Security

**PostgreSQL Authentication:**
```yaml
# In docker-compose.yml
postgresql:
  environment:
    POSTGRES_USER: hermes_user
    POSTGRES_PASSWORD: ${DB_PASSWORD}
    POSTGRES_DB: hermes_db
```

**Redis Authentication:**
```yaml
# In docker-compose.yml
redis:
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
```

**Connection String Security:**
```python
# Never log connection strings
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Use environment variables, never hardcode
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')  # ✅
# SQLALCHEMY_DATABASE_URI = "postgresql://user:pass@host"  # ❌ NEVER DO THIS
```

### 9. Secrets Management

**Development: .env file**
```bash
# .env (added to .gitignore)
SECRET_KEY=development-secret-key
JWT_SECRET_KEY=jwt-secret-key
# NEVER commit this file to git
```

**Production: HashiCorp Vault (Recommended)**
```python
# backend/app/utils/vault.py
import hvac

client = hvac.Client(url='http://vault:8200', token=os.getenv('VAULT_TOKEN'))

# Read secrets from Vault
secret = client.secrets.kv.v2.read_secret_version(path='hermes/prod')
DB_PASSWORD = secret['data']['data']['db_password']
```

**Alternative: AWS Secrets Manager**
```python
import boto3

client = boto3.client('secretsmanager', region_name='us-east-1')
response = client.get_secret_value(SecretId='hermes/db_password')
DB_PASSWORD = response['SecretString']
```

### 10. Audit Logging

```python
# backend/app/middleware/audit.py
from functools import wraps
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models import AdminLog

def audit_log(action):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            request_id = g.get('request_id')
            
            # Log before action
            log = AdminLog(
                admin_id=user_id,
                action=action,
                request_id=request_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                status='initiated'
            )
            db.session.add(log)
            db.session.commit()
            
            # Execute action
            result = fn(*args, **kwargs)
            
            # Log after action
            AdminLog.query.filter_by(request_id=request_id).update({'status': 'completed'})
            db.session.commit()
            
            return result
        return wrapper
    return decorator

# Usage:
@bp.route('/api/v1/admin/users/<user_id>/role', methods=['PUT'])
@jwt_required()
@require_role('admin')
@audit_log('change_user_role')
def change_user_role(user_id):
    pass
```

### Security Checklist

Before deploying to production, verify:

- [ ] All secrets moved to environment variables (no hardcoded passwords)
- [ ] HTTPS/SSL enabled with valid certificate
- [ ] PostgreSQL and Redis password-protected
- [ ] JWT tokens use short expiration (15 min access, 7 day refresh)
- [ ] Rate limiting enabled at nginx and application layers
- [ ] CORS configured with specific allowed origins
- [ ] Security headers added to all responses
- [ ] Input validation on all user inputs
- [ ] Audit logging for sensitive operations
- [ ] Database backups configured with encryption
- [ ] Secrets stored in Vault/AWS Secrets Manager (not .env)
- [ ] Regular security updates applied to Docker images

---

## Comparison: Docker vs Traditional Deployment

| Feature | Docker | Traditional |
|---------|--------|-------------|
| **Setup Time** | 10 minutes | 1-2 hours |
| **Consistency** | ✅ Identical everywhere | ⚠️ Manual config |
| **Scalability** | ✅ Easy (docker scale) | ⚠️ Complex |
| **Updates** | ✅ One command | ⚠️ Multiple steps |
| **Rollback** | ✅ Instant | ⚠️ Manual restore |
| **Resource Usage** | ~4GB RAM total | ~3.5GB RAM total |
| **Isolation** | ✅ Full isolation | ⚠️ Shared system |
| **Portability** | ✅ Any server | ⚠️ OS-specific |
| **Backup** | ✅ Volume snapshots | ⚠️ Manual scripts |

---

## Troubleshooting

### Container won't start
```bash
docker compose logs app
docker compose up --force-recreate app
```

### Port already in use
```bash
sudo lsof -i :8000
docker compose down
docker compose up -d
```

### Out of disk space
```bash
docker system prune -a
docker volume prune
```

### PostgreSQL connection issues
```bash
docker compose logs postgresql
docker compose exec app env | grep SQLALCHEMY
```

---

## Conclusion

**Recommendation: Use Docker for production deployment!**

Docker provides significant advantages for this project:
- ✅ Faster deployment (10 minutes vs 2 hours)
- ✅ Better consistency across environments
- ✅ Easier scaling and updates
- ✅ Built-in health checks and auto-restart
- ✅ Simplified backup and restore

The slight memory overhead (~200MB) is worth the operational benefits.
