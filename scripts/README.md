# Scripts - Hermes Deployment & Maintenance

This folder contains deployment and maintenance scripts for the Hermes application.

## 📁 Structure

```
scripts/
├── deployment/          # Deployment scripts
│   ├── deploy_backend.sh           # Deploy backend service (5 containers)
│   ├── deploy_frontend.sh          # Deploy user frontend service (port 8080)
│   ├── deploy_frontend_admin.sh    # Deploy admin frontend service (port 8081)
│   └── deploy_all.sh               # Deploy all 3 services (8 containers total)
│
├── backup/             # Database backup/restore scripts
│   ├── backup_db.sh            # Backup PostgreSQL database
│   └── restore_db.sh           # Restore PostgreSQL database
│
└── migration/          # Database migration scripts (future)
```

## 🚀 Deployment Scripts

### Deploy Backend Service
```bash
./scripts/deployment/deploy_backend.sh [development|staging|production]
```

**What it does:**
- Builds backend Docker image
- Starts PostgreSQL, Redis, Backend API, and Celery services
- Loads environment configuration from `config/[env]/.env.backend.[env]`
- Verifies all services are healthy
- Shows active services and endpoints

**Example:**
```bash
./scripts/deployment/deploy_backend.sh development
# Output:
# 🚀 Starting backend services...
# ✅ Backend service is running!
# 📊 Active Services: (docker-compose ps output)
# 🔗 Endpoints: http://localhost:5000/api/v1/
```

---

### Deploy User Frontend Service
```bash
./scripts/deployment/deploy_frontend.sh [development|staging|production]
```

**What it does:**
- Builds user frontend Docker image
- Starts user frontend service on port 8080
- Loads environment configuration from `config/[env]/.env.frontend.[env]`
- Verifies frontend is healthy
- Shows endpoints

**Example:**
```bash
./scripts/deployment/deploy_frontend.sh development
# Output:
# 🚀 Starting frontend service...
# ✅ Frontend service is running!
# 🔗 Endpoints: http://localhost:8080
```

---

### Deploy Admin Frontend Service
```bash
./scripts/deployment/deploy_frontend_admin.sh [development|staging|production]
```

**What it does:**
- Builds admin frontend Docker image
- Starts admin frontend service on port 8081
- Loads environment configuration from `config/[env]/.env.frontend-admin.[env]`
- Verifies admin frontend is healthy
- Shows admin login endpoint

**Example:**
```bash
./scripts/deployment/deploy_frontend_admin.sh development
# Output:
# 🚀 Starting admin frontend service...
# ✅ Admin frontend service is running!
# 🔗 Endpoints: http://localhost:8081 (Admin Login: /auth/login)
```

---

### Deploy All Services
```bash
./scripts/deployment/deploy_all.sh [development|staging|production]
```

**What it does:**
- Deploys backend first (PostgreSQL, Redis, API, Celery — 5 containers)
- Deploys user frontend second (port 8080)
- Deploys admin frontend third (port 8081)
- Shows summary of all three deployments (8 containers total)

**Example:**
```bash
./scripts/deployment/deploy_all.sh development
# Deploys backend, then user frontend, then admin frontend
# Shows endpoints for all three services
```

---

## 💾 Backup & Restore Scripts

### Backup Database
```bash
./scripts/backup/backup_db.sh [output_directory]
```

**What it does:**
- Creates PostgreSQL dump file from `hermes_db` database
- Saves in custom format (compressed, fast restore)
- Outputs to specified directory (default: current directory)

**Example:**
```bash
# Backup to current directory
./scripts/backup/backup_db.sh

# Output: hermes_backup_20260305_120000.dump (45 MB)

# Backup to backup folder
./scripts/backup/backup_db.sh ./backups
```

**Backup Retention:**
- Keep backups for at least 7-30 days
- Store offsite for critical data
- Schedule daily automated backups in production

---

### Restore Database
```bash
./scripts/backup/restore_db.sh <backup_file>
```

**What it does:**
- ⚠️  **DESTRUCTIVE**: Replaces current database with backup
- Drops existing `hermes_db` database
- Creates new database from backup file
- Confirms before proceeding

**Example:**
```bash
./scripts/backup/restore_db.sh hermes_backup_20260305_120000.dump

# Output:
# ⚠️  WARNING: This will REPLACE the current database!
# Continue? (yes/no): yes
# 📥 Restoring database...
# ✅ Restore successful!
```

---

## 🔧 Quick Start Workflows

### First-Time Setup (Development)
```bash
# 1. Deploy backend (with PostgreSQL, Redis)
./scripts/deployment/deploy_backend.sh development

# 2. Deploy user frontend
./scripts/deployment/deploy_frontend.sh development

# 3. Deploy admin frontend
./scripts/deployment/deploy_frontend_admin.sh development

# 4. Access application
# Backend API:    http://localhost:5000/api/v1/
# User Frontend:  http://localhost:8080
# Admin Frontend: http://localhost:8081  (login: /auth/login)

# Or deploy all at once:
./scripts/deployment/deploy_all.sh development
```

### Backup Before Update
```bash
# 1. Backup current database
./scripts/backup/backup_db.sh ./backups

# 2. Update code (git pull, etc)
# 3. Redeploy services
./scripts/deployment/deploy_all.sh development

# 4. Test application
# 5. If issues, restore from backup
./scripts/backup/restore_db.sh ./backups/hermes_backup_YYYYMMDD_HHMMSS.dump
```

### Deploy to Staging
```bash
# 1. Deploy all services to staging environment
./scripts/deployment/deploy_all.sh staging

# Configuration loaded from:
# - config/staging/.env.backend.staging
# - config/staging/.env.frontend.staging
```

### Deploy to Production
```bash
# 1. Create backup of current production data
./scripts/backup/backup_db.sh ./backups/production

# 2. Deploy to production
./scripts/deployment/deploy_all.sh production

# 3. Run health checks
curl https://yourdomain.com/api/v1/health
```

---

## ⚠️ Important Notes

### Script Permissions
```bash
# Make scripts executable
chmod +x scripts/deployment/*.sh
chmod +x scripts/backup/*.sh
```

### Environment Variables
- Scripts automatically load configuration from `config/[env]/.env.*` files
- Override by setting environment variables before running script
- Example: `ENVIRONMENT=staging ./scripts/deployment/deploy_backend.sh staging`

### Docker Requirements
- Scripts require Docker and Docker Compose to be installed
- Backend services must be running before frontend can connect
- Health checks verify services are ready before continuing

### Database Backups
- Backups are in PostgreSQL custom format (compressed)
- Use `restore_db.sh` to restore (not manual pg_restore)
- Keep multiple generations of backups (daily for 7 days)
- Store some backups offsite for disaster recovery

### Logging & Troubleshooting
```bash
# View logs after deployment
cd src/backend && docker-compose logs -f
cd src/frontend && docker-compose logs -f
cd src/frontend-admin && docker-compose logs -f

# Check container status
docker ps

# Stop services
cd src/backend && docker-compose down
cd src/frontend && docker-compose down
cd src/frontend-admin && docker-compose down
```

---

## 📚 Related Documentation

- [DOCKER_DEPLOYMENT.md](../docs/DOCKER_DEPLOYMENT.md) - Detailed Docker setup
- [PROJECT_SUMMARY.md](../docs/PROJECT_SUMMARY.md) - Quick start guide
- [PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md) - Folder organization

---

**Last Updated:** March 5, 2026  
**Version:** 1.0
