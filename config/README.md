# Config - Environment Templates

This folder contains environment configuration templates for different deployment stages.

## 📁 Structure

```
config/
├── development/        # Development environment
│   ├── .env.backend.development           # Backend dev config template
│   ├── .env.frontend.development          # User frontend dev config template
│   └── .env.frontend-admin.development    # Admin frontend dev config template
│
├── staging/           # Staging environment
│   ├── .env.backend.staging               # Backend staging config template
│   ├── .env.frontend.staging              # User frontend staging config template
│   └── .env.frontend-admin.staging        # Admin frontend staging config template
│
└── production/        # Production environment
    ├── .env.backend.production            # Backend prod config template
    ├── .env.frontend.production           # User frontend prod config template
    └── .env.frontend-admin.production     # Admin frontend prod config template
```

## 🔧 How to Use

### Development Setup

1. **Copy backend configuration:**
```bash
cp config/development/.env.backend.development src/backend/.env
```

2. **Edit with your values:**
```bash
nano src/backend/.env
# Update:
# - DB_PASSWORD (any value for dev)
# - REDIS_PASSWORD (any value for dev)
# - SECRET_KEY (any secure string)
# - MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD
```

3. **Copy user frontend configuration:**
```bash
cp config/development/.env.frontend.development src/frontend/.env
```

4. **Copy admin frontend configuration:**
```bash
cp config/development/.env.frontend-admin.development src/frontend-admin/.env
```

5. **Edit if needed:**
```bash
nano src/frontend/.env
# Key setting: BACKEND_API_URL=http://localhost:5000/api/v1

nano src/frontend-admin/.env
# Key setting: BACKEND_API_URL=http://localhost:5000/api/v1
```

6. **Start services:**
```bash
./scripts/deployment/deploy_all.sh development
```

---

### Staging Setup

1. **Copy configurations:**
```bash
cp config/staging/.env.backend.staging src/backend/.env
cp config/staging/.env.frontend.staging src/frontend/.env
cp config/staging/.env.frontend-admin.staging src/frontend-admin/.env
```

2. **Edit with staging values:**
```bash
# Backend
nano src/backend/.env
# Update:
# - DB_PASSWORD (strong value)
# - REDIS_PASSWORD (strong value)
# - SECRET_KEY (strong random value)
# - CORS_ORIGINS (staging domains for both frontends)

# User Frontend
nano src/frontend/.env
# Update: BACKEND_API_URL (staging backend URL)

# Admin Frontend
nano src/frontend-admin/.env
# Update: BACKEND_API_URL (staging backend URL)
```

3. **Deploy:**
```bash
./scripts/deployment/deploy_all.sh staging
```

---

### Production Setup

⚠️ **CRITICAL SECURITY STEPS FOR PRODUCTION:**

1. **Copy configurations:**
```bash
cp config/production/.env.backend.production src/backend/.env
cp config/production/.env.frontend.production src/frontend/.env
cp config/production/.env.frontend-admin.production src/frontend-admin/.env
```

2. **Update all sensitive values:**
```bash
nano src/backend/.env

# MUST UPDATE:
✓ DB_PASSWORD - Strong, unique, 32+ characters
✓ REDIS_PASSWORD - Strong, unique, 32+ characters
✓ SECRET_KEY - Strong random string, 32+ characters
✓ JWT_SECRET_KEY - Strong random string, 32+ characters
✓ MAIL_PASSWORD - SendGrid API key or equivalent
✓ FIREBASE_CREDENTIALS_PATH - Path to Firebase config
✓ CORS_ORIGINS - Include both frontend origins (yourdomain.com + admin.yourdomain.com)

# Recommendation: Use HashiCorp Vault or cloud secrets manager
# instead of .env file for production
```

3. **User frontend production config:**
```bash
nano src/frontend/.env

# MUST UPDATE:
✓ BACKEND_API_URL - Production backend (HTTPS): https://api.yourdomain.com/api/v1
✓ SECRET_KEY - Strong random string
✓ SESSION_COOKIE_SECURE=True (for HTTPS)
```

4. **Admin frontend production config:**
```bash
nano src/frontend-admin/.env

# MUST UPDATE:
✓ BACKEND_API_URL - Production backend (HTTPS): https://api.yourdomain.com/api/v1
✓ SECRET_KEY - Strong random string (different from user frontend!)
✓ SESSION_COOKIE_SECURE=True (for HTTPS)

# ⚠️  SECURITY: Firewall port 8081 — restrict to trusted IPs only!
# Admin frontend should NOT be publicly accessible
```

5. **Secure the .env files:**
```bash
# Restrict access to .env (current user only)
chmod 600 src/backend/.env
chmod 600 src/frontend/.env
chmod 600 src/frontend-admin/.env

# Do NOT commit .env to git
# .gitignore should have: /.env
```

5. **Deploy:**
```bash
./scripts/deployment/deploy_all.sh production
```

---

## 🔐 Security Best Practices

### Never Commit Secrets to Git
```bash
# Add to .gitignore (already should be there)
echo ".env" >> .gitignore

# Verify .env files are not tracked
git status
# Should NOT show:
# - src/backend/.env
# - src/frontend/.env
```

### Secrets Management (Production)

**Option 1: HashiCorp Vault (Recommended)**
```bash
# Store secrets in Vault
vault kv put secret/hermes/backend \
  DB_PASSWORD=your_strong_password \
  REDIS_PASSWORD=your_strong_password

# Load in startup script
export $(vault kv get -format=env secret/hermes/backend)
./scripts/deployment/deploy_backend.sh production
```

**Option 2: AWS Secrets Manager**
```bash
# Store secrets
aws secretsmanager create-secret \
  --name hermes/backend/prod \
  --secret-string '{"DB_PASSWORD":"...","REDIS_PASSWORD":"..."}'

# Load in startup script
aws secretsmanager get-secret-value --secret-id hermes/backend/prod
```

**Option 3: Google Cloud Secret Manager**
```bash
# Store secrets
gcloud secrets create hermes-backend-prod --data-file=.env

# Load in startup script
gcloud secrets versions access latest --secret="hermes-backend-prod"
```

### Password Generation (Strong)
```bash
# Generate 32-character random password
openssl rand -base64 32

# Or use Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📋 Environment-Specific Differences

### Development vs Staging vs Production

| Setting | Development | Staging | Production |
|---------|-------------|---------|-----------|
| **FLASK_ENV** | development | production | production |
| **DEBUG** | True | False | False |
| **DB_POOL_SIZE** | 20 | 30 | 50 |
| **RATE_LIMIT_PER_IP** | 100 | 200 | 500 |
| **SESSION_COOKIE_SECURE** | False | False | True |
| **CORS_ORIGINS** | localhost:8080 + localhost:8081 | staging domain + admin.staging | yourdomain.com + admin.yourdomain.com |
| **User Frontend URL** | http://localhost:8080 | http://staging-url:8080 | https://yourdomain.com |
| **Admin Frontend URL** | http://localhost:8081 | http://staging-admin:8081 | https://admin.yourdomain.com |
| **BACKEND_API_URL** | http://localhost:5000 | http://staging-backend:5000 | https://api.yourdomain.com |
| **LOG_LEVEL** | DEBUG | INFO | WARNING |

---

## ✅ Verification Checklist

### Before Deploying Development
- [ ] DB_PASSWORD and REDIS_PASSWORD set
- [ ] SECRET_KEY is 32+ characters
- [ ] MAIL credentials correct (or mock SMTP)
- [ ] BACKEND_API_URL points to localhost

### Before Deploying Staging
- [ ] All passwords are strong (32+ chars, random)
- [ ] CORS_ORIGINS set to staging domain
- [ ] EMAIL configured for staging
- [ ] BACKEND_API_URL points to staging server
- [ ] DEBUG=False

### Before Deploying Production
- [ ] All passwords are VERY strong (32+ chars, cryptographically random)
- [ ] Secrets stored in secure vault (not .env)
- [ ] CORS_ORIGINS set to production domain ONLY
- [ ] EMAIL configured with production provider (SendGrid, AWS SES, etc)
- [ ] BACKEND_API_URL uses HTTPS
- [ ] SESSION_COOKIE_SECURE=True
- [ ] FIREBASE credentials valid
- [ ] Database backups scheduled
- [ ] Logging configured for production
- [ ] SSL certificates valid (Let's Encrypt)
- [ ] Health checks configured

---

## 📝 Example: Production Deployment

```bash
# 1. Create backup
./scripts/backup/backup_db.sh ./backups/prod

# 2. Setup environment
cp config/production/.env.backend.production src/backend/.env
nano src/backend/.env
# Update all sensitive values from vault/secrets manager

cp config/production/.env.frontend.production src/frontend/.env
cp config/production/.env.frontend-admin.production src/frontend-admin/.env
nano src/frontend/.env            # Update BACKEND_API_URL
nano src/frontend-admin/.env     # Update BACKEND_API_URL

# 3. Secure files
chmod 600 src/backend/.env
chmod 600 src/frontend/.env
chmod 600 src/frontend-admin/.env

# 4. Deploy
./scripts/deployment/deploy_all.sh production

# 5. Verify
curl https://yourdomain.com/api/v1/health
curl https://yourdomain.com/health
curl https://admin.yourdomain.com/health

# 6. Check logs
docker-compose -f src/backend/docker-compose.yml logs -f
docker-compose -f src/frontend/docker-compose.yml logs -f
docker-compose -f src/frontend-admin/docker-compose.yml logs -f
```

---

## 🆘 Troubleshooting

### Docker fails to start with "env file not found"
**Solution:** Copy env file to correct location
```bash
cp config/[env]/.env.* src/[backend|frontend]/.env
```

### Backend can't connect to PostgreSQL
**Solution:** Check connection string
```bash
# Verify DATABASE_URL in .env
echo $DATABASE_URL

# Check PostgreSQL is running
docker-compose ps postgresql
```

### Frontend can't reach backend
**Solution:** Check BACKEND_API_URL
```bash
# Verify in user frontend .env
grep BACKEND_API_URL src/frontend/.env

# Verify in admin frontend .env
grep BACKEND_API_URL src/frontend-admin/.env

# Test connection
curl http://localhost:5000/api/v1/health
```

### CORS errors in browser console
**Solution:** Update CORS_ORIGINS
```bash
# In src/backend/.env, update:
CORS_ORIGINS=http://localhost:8080,https://yourdomain.com
```

---

## 📚 Related Documentation

- [DOCKER_DEPLOYMENT.md](../docs/DOCKER_DEPLOYMENT.md) - Docker setup guide
- [scripts/README.md](../scripts/README.md) - Deployment scripts guide

---

**Last Updated:** March 5, 2026  
**Version:** 1.0
