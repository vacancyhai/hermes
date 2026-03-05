# Docker Deployment Guide - Sarkari Path

## Microservices Architecture with Separated Containers

This deployment uses **8 Docker containers (Optimized)** with separated Flask frontend and backend for better scalability and maintenance.

**Container Breakdown:**
1. **Nginx** - Reverse proxy with health checks
2. **Frontend** - Flask + Jinja2 UI
3. **Backend** - Flask REST API (/api/v1/)
4. **MongoDB** - Database with TTL indexes
5. **Redis** - Cache + Queue (AOF persistence)
6. **Celery Worker** - Background task executor (scalable: 1-N)
7. **Celery Beat** - Task scheduler (always 1 instance)
8. **Monitoring** - Health checks & logging (optional)

## Why Docker + Microservices for This Project?

### ✅ Advantages
1. **Service Isolation**: Frontend and backend run independently
2. **Independent Scaling**: Scale frontend and backend separately based on load
3. **Zero-Downtime Updates**: Update frontend without restarting backend (and vice versa)
4. **Consistency**: Same environment across development, staging, and production
5. **Easy Deployment**: Single command deployment on any server
6. **Portability**: Works on any platform (Hostinger VPS, AWS, DigitalOcean, etc.)
7. **Quick Setup**: No manual installation of dependencies
8. **Version Control**: Docker images are versioned
9. **Resource Management**: Better control over CPU/RAM allocation per service
10. **Easy Rollback**: Quickly revert individual services to previous versions

### ⚠️ Considerations
- **Learning Curve**: Need to understand Docker and microservices basics
- **Overhead**: Slight memory overhead (~100-200MB per container)
- **Disk Space**: Docker images take more space
- **Complexity**: More containers to manage (6 instead of 1)

### 📊 Recommendation
**YES, use Docker microservices for production!** The benefits far outweigh the drawbacks, especially for a multi-service application like Sarkari Path.

---

## Docker Microservices Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hostinger VPS Server                         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Docker Compose Network                        │ │
│  │                  (sarkari_network)                         │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────┐     │ │
│  │  │         Nginx Container                          │     │ │
│  │  │  - Port 80:80, 443:443                           │     │ │
│  │  │  - SSL Termination (Let's Encrypt)               │     │ │
│  │  │  - Reverse Proxy                                 │     │ │
│  │  │  - Static File Serving                           │     │ │
│  │  │  - Rate Limiting                                 │     │ │
│  │  └─────────┬──────────────────────┬─────────────────┘     │ │
│  │            │                      │                       │ │
│  │      /api/*│                      │/*                     │ │
│  │            ↓                      ↓                       │ │
│  │  ┌──────────────────┐   ┌────────────────────────┐       │ │
│  │  │  Backend         │   │  Frontend              │       │ │
│  │  │  Container       │   │  Container             │       │ │
│  │  │  (Flask API)     │←──│  (Flask + Jinja2)      │       │ │
│  │  │                  │   │                        │       │ │
│  │  │  - Port 5000     │   │  - Port 8080           │       │ │
│  │  │  - Gunicorn 3w   │   │  - Gunicorn 2w         │       │ │
│  │  │  - REST API      │   │  - UI Rendering        │       │ │
│  │  │  - Auth & Logic  │   │  - Templates           │       │ │
│  │  └────────┬─────────┘   │  - Static Assets       │       │ │
│  │           │              │  - API Client          │       │ │
│  │           │              └────────────────────────┘       │ │
│  │           │                                               │ │
│  │      ┌────┼────────────────────┬──────────────┐          │ │
│  │      │    │                    │              │          │ │
│  │      ↓    ↓                    ↓              ↓          │ │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  ┌───────┐│
│  │  │  MongoDB   │  │   Redis      │  │  Celery     │  │Celery ││
│  │  │  Container │  │  Container   │  │  Worker     │  │ Beat  ││
│  │  │            │  │              │  │  Container  │  │ Cont. ││
│  │  │ Port 27017 │  │  Port 6379   │  │             │  │       ││
│  │  │ - Auth     │  │  - Cache     │  │ - Jobs      │  │-Cron  ││
│  │  │ - 15 Cols  │  │  - Sessions  │  │ - Emails    │  │-Tasks ││
│  │  │ - Persist  │  │  - Queue     │  │ - Notify    │  │       ││
│  │  └────────────┘  └──────────────┘  └─────────────┘  └───────┘│
│  │                                                            │ │
│  │  Volumes (Persistent Storage):                            │ │
│  │  - mongodb_data    - redis_data                           │ │
│  │  - backend_logs    - nginx_ssl                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

        Internet ↕️ HTTPS (Port 443)
```

### Container Communication Flow

1. **User Request** → Nginx (Port 80/443)
2. **Nginx Routes** (with health checks):
   - `/api/v1/*` → Backend Container (Port 5000) - Only if healthy
   - `/*` (pages) → Frontend Container (Port 8080) - Only if healthy
   - `/static/*` → Frontend Container static files
3. **Frontend** → Calls Backend API via internal network: `http://backend:5000/api/v1`
4. **Backend** → Accesses MongoDB and Redis
5. **Celery Worker** → Processes background tasks from Redis queue (separate worker containers)
6. **Celery Beat** → Triggers scheduled tasks (separate Beat container, scales independently)

### ⚡ Important: Celery Separation
**Celery Beat and Celery Worker are SEPARATE containers** (not 1 process doing both):

**Why Separate?**
- **Scaling**: Scale workers without re-triggering schedules
- **Failures**: If a worker crashes, Beat keeps scheduling
- **Monitoring**: Track task execution separately from scheduling
- **Scalability**: Run 5 workers + 1 Beat = better throughput

**In docker-compose.yml**:
- `celery_worker`: Services = scales from 1 to N
- `celery_beat`: Services = always 1 (only one schedule master)

Do NOT use: `celery -A celery_app worker --beat` (this couples them together)

---

## Docker Files

### 1. Backend Dockerfile (Flask API)

**backend/Dockerfile:**
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
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')"

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "60", "run:app"]
```

### 2. Frontend Dockerfile (Flask + Jinja2)

**frontend/Dockerfile:**
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

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "30", "run:app"]
```

### 3. docker-compose.yml (Complete Orchestration)

```yaml
version: '3.8'

services:
  # MongoDB Database
  # ⚡ IMPORTANT FOR PRODUCTION: This is single-node setup
  # For production failover, setup 3-node replica set:
  # - rs.initiate({_id: "rs0", members: [{_id: 0, host: "mongo1:27017"}, ...]})
  # Current setup: Suitable for development/staging with single-node persistence
  mongodb:
    image: mongo:7.0
    container_name: sarkari_mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
      MONGO_INITDB_DATABASE: sarkari_path
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    networks:
      - sarkari_network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/sarkari_path --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache & Broker with AOF Persistence
  # ⚡ AOF (Append-Only File) ensures data survives Redis restarts
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    container_name: sarkari_redis
    restart: unless-stopped
    # ⚡ PERSISTENCE: Redis needs AOF persistence for task queue reliability
    # Without this, queued tasks die on restart
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes --appendfsync everysec
    volumes:
      - redis_data:/data
    networks:
      - sarkari_network
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
2. **Cache Layer** (session/data cache) - App check Redis before querying MongoDB

**Cache-Aside Pattern** (Used throughout app):
```python
# backend/app/services/cache_service.py
def get_jobs(limit=20, page=1):
    cache_key = f"jobs:limit_{limit}:page_{page}"
    
    # Step 1: Check Redis cache
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)  # Cache hit!
    
    # Step 2: Cache miss - load from MongoDB
    jobs = db.jobs.find().limit(limit).skip((page-1)*limit)
    
    # Step 3: Store in Redis for next request
    redis.setex(
        cache_key,
        TTL=3600,  # 1 hour
        value=json.dumps(jobs)
    )
    
    return jobs
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

## ⚡ MongoDB Data Retention & TTL Cleanup

**TTL Indexes auto-delete old data** (saving storage costs):

```javascript
// mongo-init.js - Create TTL Indexes

// Notifications: Auto-delete after 90 days (3 months)
db.notifications.createIndex(
  {"created_at": 1},
  {expireAfterSeconds: 7776000}  // 90 days
)

// Application Logs: Auto-delete after 30 days
db.application_logs.createIndex(
  {"timestamp": 1},
  {expireAfterSeconds: 2592000}  // 30 days
)

// Email Events: Keep for 60 days (bounce/delivery tracking)
db.email_events.createIndex(
  {"created_at": 1},
  {expireAfterSeconds: 5184000}  // 60 days
)

// Audit Trail: Keep for 1 year (compliance requirement)
db.audit_trail.createIndex(
  {"created_at": 1},
  {expireAfterSeconds: 31536000}  // 365 days
)

// Search History: Keep for 6 months
db.search_history.createIndex(
  {"timestamp": 1},
  {expireAfterSeconds: 15552000}  // 180 days
)
```

**How It Works**:
```
MongoDB runs cleanup job every 60 seconds (configurable)
Reads all documents with TTL indexes
Deletes any where (current_time - created_at) > TTL
Frees disk space automatically - no manual cleanup needed
```

**Storage Benefits**:
```
Without TTL:  100,000 notifications per month
  × 12 months = 1.2M notifications stored forever
  Size: ~500 MB

With 90-day TTL:  Only 300,000 notifications at any time
  Size: ~125 MB
  Savings: 75% disk space reduction
```

---
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: sarkari_backend
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/sarkari_path?authSource=sarkari_path
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
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - sarkari_network
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
    # vault kv get secret/sarkari_path/db_password

  # Frontend UI Container
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: sarkari_frontend
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
      - sarkari_network
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
    container_name: sarkari_celery_worker
    restart: unless-stopped
    # ⚡ Only runs workers, NOT scheduler
    command: celery -A celery_worker.celery worker --loglevel=info --concurrency=2
    environment:
      - FLASK_ENV=production
      - MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/sarkari_path?authSource=sarkari_path&maxPoolSize=50
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
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - sarkari_network
    # ⚡ Can scale: docker compose up -d --scale celery_worker=3

  # ⚡ CELERY BEAT - ONLY controls scheduling, separate from workers
  # This container ONLY triggers scheduled tasks
  # Separate from Celery Worker (which executes tasks)
  # KEEP ONLY 1 BEAT INSTANCE (do NOT scale this)
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: sarkari_celery_beat
    restart: unless-stopped
    # ⚡ Only runs scheduler (Beat), NOT workers
    command: celery -A celery_worker.celery beat --loglevel=info
    environment:
      - FLASK_ENV=production
      - MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/sarkari_path?authSource=sarkari_path
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    volumes:
      - ./backend:/app
    depends_on:
      # ⚡ Beat waits for queue to be ready
      - redis
    networks:
      - sarkari_network
    # ⚡ IMPORTANT: Keep only 1 Beat (never scale with --scale)
    # Multiple Beats = duplicate scheduled tasks
    # For HA, use Celery Flower or external beat scheduler (Celery on Kubernetes)

  # Nginx Reverse Proxy with Health Checks
  # ⚡ Health checks ensure only healthy upstreams receive traffic
  nginx:
    image: nginx:alpine
    container_name: sarkari_nginx
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
      - sarkari_network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  sarkari_network:
    driver: bridge

volumes:
  mongodb_data:
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

### 4. mongo-init.js (MongoDB Initialization)

```javascript
// mongo-init.js
db = db.getSiblingDB('sarkari_path');

db.createUser({
  user: process.env.MONGO_USER,
  pwd: process.env.MONGO_PASSWORD,
  roles: [
    {
      role: 'readWrite',
      db: 'sarkari_path'
    }
  ]
});

// ⚡ Production: Create TTL indexes for auto-cleanup
// Notifications older than 90 days auto-delete
db.notifications.createIndex({ "created_at": 1 }, { expireAfterSeconds: 7776000 });

// Old logs auto-delete after 30 days
db.activity_logs.createIndex({ "created_at": 1 }, { expireAfterSeconds: 2592000 });

// ⚡ Create necessary indexes for queries (MUST HAVE for performance)
db.users.createIndex({ "email": 1 }, { unique: true });
db.user_profiles.createIndex({ "user_id": 1 }, { unique: true });

// Job search indexes (critical for performance with filters)
db.job_vacancies.createIndex({ "organization": 1 });
db.job_vacancies.createIndex({ "status": 1 });
db.job_vacancies.createIndex({ "created_at": -1 });
db.job_vacancies.createIndex({ "eligibility.qualification": 1, "organization": 1 });
db.job_vacancies.createIndex({ "important_dates.application_end": 1 });

// Application tracking indexes
db.user_job_applications.createIndex({ "user_id": 1, "job_id": 1 }, { unique: true });
db.user_job_applications.createIndex({ "user_id": 1, "applied_date": -1 });

// Notification query indexes
db.notifications.createIndex({ "user_id": 1, "is_read": 1 });
db.notifications.createIndex({ "user_id": 1, "created_at": -1 });

print('MongoDB initialized with TTL and query indexes');
```

---

### 4a. ⚡ Production MongoDB Replica Set Setup

**Why Replica Set?** Single MongoDB instance = no failover. If it crashes, entire system is down.

**For Production, setup 3-node replica set** (1 primary + 2 secondaries):

```bash
# After MongoDB is running, initialize replica set
docker compose exec mongodb mongosh -u admin -p your_password

# Inside mongosh, run:
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongodb1:27017" },
    { _id: 1, host: "mongodb2:27017" },
    { _id: 2, host: "mongodb3:27017" }
  ]
});

# Verify:
rs.status()  # Primary shows as "PRIMARY", others as "SECONDARY"
```

**Update Connection String for Replica Set**:
```bash
# Before (single node):
MONGO_URI=mongodb://user:pass@mongodb:27017/sarkari_path

# After (replica set):
MONGO_URI=mongodb://user:pass@mongodb1:27017,mongodb2:27017,mongodb3:27017/sarkari_path?replicaSet=rs0&authSource=admin
```

**Benefits**:
- ✅ Automatic failover (primary crashes → secondary takes over)
- ✅ Read scaling (read from secondaries)
- ✅ Zero-downtime upgrades (upgrade one node at a time)
- ✅ Data redundancy (3 copies of data)

**Current Development Setup**: Single-node is fine, but add this before going to production.

---

### 4b. ⚡ MongoDB Connection Pooling Configuration

**Why Connection Pooling?** Creating new database connections is expensive (100-500ms). Connection pools reuse existing connections.

**Configuration in Environment Variables:**
```bash
# Development (low traffic)
MONGO_URI=mongodb://user:pass@mongodb:27017/sarkari_path?authSource=sarkari_path&maxPoolSize=10&minPoolSize=2

# Production (high traffic)
MONGO_URI=mongodb://user:pass@mongodb:27017/sarkari_path?authSource=sarkari_path&maxPoolSize=50&minPoolSize=10&maxIdleTimeMS=60000
```

**Connection Pool Parameters:**
- `maxPoolSize=50` - Maximum 50 concurrent connections
- `minPoolSize=10` - Always keep 10 connections ready
- `maxIdleTimeMS=60000` - Close idle connections after 60 seconds
- `waitQueueTimeoutMS=5000` - Wait max 5 seconds for available connection

**Benefits:**
- ✅ Faster query execution (no connection overhead)
- ✅ Prevents connection exhaustion
- ✅ Automatic connection recovery
- ✅ Better resource utilization

**Monitoring Connection Pool:**
```python
# backend/app/utils/db_monitor.py
from pymongo import monitoring

class ConnectionPoolLogger(monitoring.ConnectionPoolListener):
    def pool_created(self, event):
        print(f"Connection pool created: {event.address}")
    
    def connection_checked_out(self, event):
        print(f"Connection checked out: Pool size: {event.connection_id}")
    
    def connection_checked_in(self, event):
        print(f"Connection returned to pool")

# Register monitor
monitoring.register(ConnectionPoolLogger())
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
        # Load from MongoDB
        jobs = db.jobs.find().limit(limit)
        
        # Try to cache for next time
        try:
            redis.setex(f"jobs:limit_{limit}", 3600, json.dumps(jobs))
        except redis.ConnectionError:
            pass  # Cache write failed, but we have the data
        
        return jobs
    except pymongo.errors.ServerSelectionTimeoutError:
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
from pymongo.errors import ServerSelectionTimeoutError
import time

def execute_with_retry(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except ServerSelectionTimeoutError:
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

# MongoDB Configuration with Connection Pooling
MONGO_ROOT_PASSWORD=strong_root_password_change_this
MONGO_USER=sarkaripath_user
MONGO_PASSWORD=strong_db_password_change_this
# ⚡ Connection pool settings for production
MONGO_MAX_POOL_SIZE=50
MONGO_MIN_POOL_SIZE=10

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

# Monitoring & Logging
LOG_LEVEL=INFO
ENABLE_REQUEST_LOGGING=true
ENABLE_PERFORMANCE_MONITORING=true
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
cd /home/sarkaripath
git clone https://github.com/SumanKr7/sarkari_path_2.0.git
cd sarkari_path_2.0

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
    container_name: sarkaripath_certbot
    volumes:
      - ./nginx/ssl:/etc/letsencrypt
      - ./certbot-webroot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - sarkaripath_network
```

---

## ⚡ Monitoring & Logging Setup (Production)

### Centralized Logging (ELK Stack)

Add to docker-compose.yml for production log aggregation:

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    container_name: sarkari_elasticsearch
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - sarkaripath_network

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    container_name: sarkari_kibana
    restart: unless-stopped
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    networks:
      - sarkaripath_network
```

**Enable JSON logging in all services**:
```python
# backend/app/__init__.py
import logging
from pythonjsonlogger import jsonlogger

handler = logging.FileHandler('logs/app.log')
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)

# Now logs: {"timestamp": "...", "service": "backend", "level": "INFO", "message": ""}
```

**Access Kibana**: http://localhost:5601
Search: `service:backend AND level:ERROR`

### Performance Monitoring (Prometheus + Grafana)

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: sarkari_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - sarkaripath_network

  grafana:
    image: grafana/grafana:latest
    container_name: sarkari_grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - sarkaripath_network
```

**Metrics to Monitor**:
- API response times (goal: < 200ms for job search)
- Database query latency (goal: < 50ms)
- Celery task execution time (goal: email < 5s)
- Error rates (goal: < 1%)
- Memory/CPU per container (goal: < 80%)

**Access Grafana**: http://localhost:3000 (admin/admin)

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
docker compose exec mongodb mongosh

# Update application (pull latest code)
cd /home/sarkaripath/sarkari_path_2.0
git pull origin main
docker compose up -d --build app celery_worker celery_beat
```

### Monitoring
```bash
# Check resource usage
docker stats

# Inspect container
docker compose inspect app

# Check container health
docker compose ps

# View application logs
docker compose logs -f --tail=100 app

# View Celery logs
docker compose logs -f celery_worker
```

### Database Operations
```bash
# MongoDB shell access
docker compose exec mongodb mongosh -u sarkaripath_user -p

# Backup MongoDB
docker compose exec mongodb mongodump --out=/data/backup

# Restore MongoDB
docker compose exec mongodb mongorestore /data/backup

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
# backup.sh - Docker MongoDB Backup Script

BACKUP_DIR="/home/sarkaripath/backups/mongodb"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="sarkaripath_backup_$DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup MongoDB from Docker container
docker compose exec -T mongodb mongodump \
  --uri="mongodb://sarkaripath_user:${MONGO_PASSWORD}@localhost:27017/sarkari_path?authSource=sarkari_path" \
  --out=/tmp/$BACKUP_NAME

# Copy backup from container
docker compose cp mongodb:/tmp/$BACKUP_NAME $BACKUP_DIR/

# Compress
cd $BACKUP_DIR
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Delete backups older than 7 days
find $BACKUP_DIR -name "*.tar.gz" -type f -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME.tar.gz"
```

```bash
# Make executable
chmod +x backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /home/sarkaripath/sarkari_path_2.0/backup.sh >> /home/sarkaripath/logs/backup.log 2>&1
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
        identity=str(user['_id']),
        expires_delta=timedelta(minutes=15)
    )
    
    # ⚡ Refresh token: 7 days (not 30 days)
    refresh_token = create_refresh_token(
        identity=str(user['_id']),
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

**MongoDB Authentication:**
```yaml
# In docker-compose.yml
mongodb:
  environment:
    MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USER}
    MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
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
logging.getLogger('pymongo').setLevel(logging.WARNING)

# Use environment variables, never hardcode
MONGO_URI = os.getenv('MONGO_URI')  # ✅
# MONGO_URI = "mongodb://user:pass@host"  # ❌ NEVER DO THIS
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
secret = client.secrets.kv.v2.read_secret_version(path='sarkari_path/prod')
MONGO_PASSWORD = secret['data']['data']['mongo_password']
```

**Alternative: AWS Secrets Manager**
```python
import boto3

client = boto3.client('secretsmanager', region_name='us-east-1')
response = client.get_secret_value(SecretId='sarkari_path/mongo_password')
MONGO_PASSWORD = response['SecretString']
```

### 10. Audit Logging

```python
# backend/app/middleware/audit.py
from functools import wraps
from flask_jwt_extended import get_jwt_identity

def audit_log(action):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            request_id = g.get('request_id')
            
            # Log before action
            db.audit_trail.insert_one({
                'user_id': user_id,
                'action': action,
                'request_id': request_id,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'timestamp': datetime.utcnow(),
                'status': 'initiated'
            })
            
            # Execute action
            result = fn(*args, **kwargs)
            
            # Log after action
            db.audit_trail.update_one(
                {'request_id': request_id},
                {'$set': {'status': 'completed'}}
            )
            
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
- [ ] MongoDB and Redis password-protected
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
| **Monitoring** | ✅ Built-in tools | ⚠️ Custom setup |

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

### MongoDB connection issues
```bash
docker compose logs mongodb
docker compose exec app env | grep MONGO
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
