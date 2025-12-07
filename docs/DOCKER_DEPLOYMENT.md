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
│  │  │ - Persist  │  │  - Sessions  │  │ - Emails    │  │-Tasks ││
│  │  │            │  │  - Queue     │  │ - Notify    │  │       ││
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
5. **Celery Worker** → Processes background tasks from Redis queue
6. **Celery Beat** → Triggers scheduled tasks

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
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - sarkari_network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Backend API Container
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
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - sarkari_network

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
      - backend
    networks:
      - sarkari_network

  # Celery Worker
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: sarkari_celery_worker
    restart: unless-stopped
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
      - mongodb
      - redis
      - backend
    networks:
      - sarkari_network

  # Celery Beat Scheduler
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: sarkari_celery_beat
    restart: unless-stopped
    command: celery -A celery_worker.celery beat --loglevel=info
    environment:
      - FLASK_ENV=production
      - MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/sarkari_path?authSource=sarkari_path
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    volumes:
      - ./backend:/app
    depends_on:
      - redis
      - celery_worker
    networks:
      - sarkari_network

  # Nginx Reverse Proxy
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
      - frontend
      - backend
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

// Create indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.user_profiles.createIndex({ "user_id": 1 }, { unique: true });
db.job_vacancies.createIndex({ "organization": 1 });
db.job_vacancies.createIndex({ "status": 1 });
db.job_vacancies.createIndex({ "created_at": -1 });
db.user_job_applications.createIndex({ "user_id": 1, "job_id": 1 }, { unique: true });
db.notifications.createIndex({ "user_id": 1, "is_read": 1 });

print('MongoDB initialized successfully');
```

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

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

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
