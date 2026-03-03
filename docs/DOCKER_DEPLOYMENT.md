# Docker Deployment Guide - Sarkari Path

## Microservices Architecture with Separated Containers

This deployment uses **6 Docker containers** with separated Flask frontend and backend for better scalability and maintenance.

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
2. **Nginx Routes**:
   - `/api/*` → Backend Container (Port 5000)
   - `/*` (pages) → Frontend Container (Port 8080)
   - `/static/*` → Frontend Container static files
3. **Frontend** → Calls Backend API via internal network: `http://backend:5000/api`
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

  # Redis Cache & Broker
  redis:
    image: redis:7-alpine
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
      - BACKEND_API_URL=http://backend:5000/api
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
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
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
      - MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/sarkari_path?authSource=sarkari_path
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
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

        # API requests → Backend container
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
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

# MongoDB Configuration
MONGO_ROOT_PASSWORD=strong_root_password_change_this
MONGO_USER=sarkaripath_user
MONGO_PASSWORD=strong_db_password_change_this

# Redis Configuration
REDIS_PASSWORD=strong_redis_password_change_this

# Flask-Mail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Firebase Configuration (Optional)
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# JWT Configuration
JWT_SECRET_KEY=jwt-secret-key-different-from-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Admin Configuration
ADMIN_EMAIL=admin@yourdomain.com

# Application URL
APP_URL=https://yourdomain.com
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
