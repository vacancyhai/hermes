# Docker Environments

This document describes the three deployment environments and how they map to
Docker Compose services, network topology, and configuration files.

---

## Architecture overview

```
                     ┌──────────────────────────────────────────────────┐
                     │  Docker Host                                      │
  ┌──────────┐       │  ┌───────────┐        src_backend_network        │
  │  Browser │──────▶│  │   Nginx   │──────▶ ┌──────────┐              │
  └──────────┘  :80  │  │  (proxy)  │        │ backend  │ :5000        │
                :443 │  └─────┬─────┘        │  (API)   │              │
                     │        │              └────┬─────┘              │
                     │        │ src_frontend_network    │              │
                     │        ├──────────────│──────────────────┐     │
                     │        │              │ celery_worker      │     │
                     │        │  ┌──────────┐│ celery_beat        │     │
                     │        │  │ frontend │└──────────────────┘     │
                     │        │  │  :8080   │  PostgreSQL :5432        │
                     │        │  └──────────┘  Redis      :6379        │
                     │        │                                         │
                     │ src_frontend_admin_network                       │
                     │        │  ┌────────────────┐                    │
                     │        └─▶│ frontend-admin │                    │
                     │           │    :8081        │                    │
                     │           └────────────────┘                    │
                     └──────────────────────────────────────────────────┘
```

### Network isolation

| Docker network              | Services joined                                        |
| --------------------------- | ------------------------------------------------------ |
| `src_backend_network`       | backend, celery_worker, celery_beat, postgresql, redis, nginx |
| `src_frontend_network`      | frontend, nginx                                        |
| `src_frontend_admin_network`| frontend-admin, nginx                                  |

The frontend services **cannot** reach the database or Redis directly — all
persistence goes through the backend REST API.

---

## Services at a glance

| Service          | Image / Build   | Default port | Compose file                        |
| ---------------- | --------------- | ------------ | ----------------------------------- |
| `postgresql`     | postgres:16-alpine | `5432`    | `src/backend/docker-compose.yml`    |
| `redis`          | redis:7-alpine  | `6379`       | `src/backend/docker-compose.yml`    |
| `backend`        | local build     | `5000`       | `src/backend/docker-compose.yml`    |
| `celery_worker`  | local build     | —            | `src/backend/docker-compose.yml`    |
| `celery_beat`    | local build     | —            | `src/backend/docker-compose.yml`    |
| `frontend`       | local build     | `8080`       | `src/frontend/docker-compose.yml`   |
| `frontend-admin` | local build     | `8081`       | `src/frontend-admin/docker-compose.yml` |
| `nginx`          | nginx:alpine    | `80 / 443`   | `src/nginx/docker-compose.yml`      |

---

## Environment-specific differences

### Development

**Goal**: fast iteration, debug-friendly, no TLS.

| Aspect | Value |
| --- | --- |
| Config templates | `config/development/` |
| Flask `ENV` | `development` |
| `DEBUG` | `True` |
| Database | Local PostgreSQL container — data persisted in Docker volume `postgresql_data` |
| Redis | Local Redis container — no TLS requirement |
| Mail | Use [Mailhog](https://github.com/mailhog/MailHog) or SMTP stub (`MAIL_SUPPRESS_SEND=True`) |
| Nginx | Not required; services are accessed directly on their exposed ports |
| TLS | None — HTTP only |
| Volumes | Hot-reload mounts: `./app:/app/app`, `./templates:/app/templates`, `./static:/app/static` |

**Setup:**

```bash
cp config/development/.env.backend.development       src/backend/.env
cp config/development/.env.frontend.development      src/frontend/.env
cp config/development/.env.frontend-admin.development src/frontend-admin/.env

# Start backend stack (PostgreSQL + Redis + API + Celery)
cd src/backend && docker compose up -d

# Start user frontend
cd src/frontend && docker compose up -d

# Start admin frontend
cd src/frontend-admin && docker compose up -d
```

Or use the all-in-one script:
```bash
./scripts/deployment/deploy_all.sh development
```

**Verify:**
- API health:     `curl http://localhost:5000/api/v1/health`
- User frontend:  `http://localhost:8080`
- Admin frontend: `http://localhost:8081`

---

### Staging

**Goal**: production-like environment for integration testing; TLS optional.

| Aspect | Value |
| --- | --- |
| Config templates | `config/staging/` |
| Flask `ENV` | `production` |
| `DEBUG` | `False` |
| Database | Managed PostgreSQL **or** containerised postgres on the staging host |
| Redis | Containerised Redis with password authentication |
| Mail | Real SMTP relay — test accounts only |
| Nginx | Deployed; TLS via self-signed or Let's Encrypt staging cert |
| TLS | HTTPS on `443` — HTTP redirects to HTTPS |
| Volumes | No hot-reload code mounts — images must be rebuilt for code changes |

**Setup:**
```bash
cp config/staging/.env.backend.staging       src/backend/.env
cp config/staging/.env.frontend.staging      src/frontend/.env
cp config/staging/.env.frontend-admin.staging src/frontend-admin/.env

# Edit .env files with staging credentials before deploying
./scripts/deployment/deploy_all.sh staging
```

**Key difference from development:**
- `SECRET_KEY` must be a cryptographically strong value (≥ 32 random bytes).
- `BACKEND_API_URL` in both frontend `.env` files should point to the internal
  Docker hostname (`http://backend:5000/api/v1`) when all services run on the
  same host, or to the staging domain when split across hosts.

---

### Production

**Goal**: hardened, monitored, zero-downtime deployments.

| Aspect | Value |
| --- | --- |
| Config templates | `config/production/` |
| Flask `ENV` | `production` |
| `DEBUG` | `False` (never override) |
| Database | Managed PostgreSQL (e.g. AWS RDS, Cloud SQL) — **not** containerised |
| Redis | Managed Redis (e.g. AWS ElastiCache) — TLS + password |
| Mail | Production SMTP relay with SPF/DKIM configured |
| Nginx | TLS 1.2 / 1.3 only; HSTS enabled; valid certificate required |
| TLS | HTTPS mandatory — certificates mounted from `src/nginx/ssl/` |
| Volumes | No code mounts; container images are immutable artefacts |
| Gunicorn | Workers set via `WEB_CONCURRENCY` env var (default: CPU × 2 + 1) |

**Setup:**
```bash
cp config/production/.env.backend.production        src/backend/.env
cp config/production/.env.frontend.production       src/frontend/.env
cp config/production/.env.frontend-admin.production src/frontend-admin/.env

# Populate all secrets — do NOT commit .env files
./scripts/deployment/deploy_all.sh production
```

**Critical production checklist:**
- [ ] `SECRET_KEY` — minimum 32 random bytes, stored in a secrets manager
- [ ] `POSTGRES_PASSWORD` / `DB_PASSWORD` — strong, unique
- [ ] `REDIS_PASSWORD` — strong, unique
- [ ] `JWT_SECRET_KEY` — separate from `SECRET_KEY`
- [ ] `MAIL_PASSWORD` — app-specific password or API key
- [ ] TLS certificate and private key placed in `src/nginx/ssl/`
- [ ] `ALLOWED_ORIGINS` / `CORS_ORIGINS` restricted to production domain(s)

---

## Celery Beat schedule (all environments)

The `celery_beat` container runs the following cron tasks regardless of environment.
Task frequency can be adjusted in `src/backend/app/tasks/celery_app.py`.

| Task                         | Schedule          | Description                          |
| ---------------------------- | ----------------- | ------------------------------------ |
| `send-deadline-reminders`    | Daily 08:00 UTC   | Email reminders at T-7, T-3, T-1 days |
| `purge-expired-notifications`| Daily 01:00 UTC   | Remove old read notifications        |
| `purge-expired-admin-logs`   | Daily 01:30 UTC   | Archive / delete old admin audit logs|
| `purge-soft-deleted-jobs`    | Daily 02:00 UTC   | Hard-delete jobs soft-deleted > 90 days |
| `close-expired-job-listings` | Daily 02:30 UTC   | Auto-close jobs past `application_end` |

---

## Backup and restore

Database backups are scripted at `scripts/backup/`:

```bash
# Create a compressed dump
./scripts/backup/backup_db.sh

# Restore from dump
./scripts/backup/restore_db.sh <dump-file>
```

Backups should be scheduled (e.g. via host cron or CI) in staging and production.

---

## Related files

| File | Purpose |
| ---- | ------- |
| `src/backend/docker-compose.yml` | Backend stack definition |
| `src/frontend/docker-compose.yml` | User frontend definition |
| `src/frontend-admin/docker-compose.yml` | Admin frontend definition |
| `src/nginx/docker-compose.yml` | Nginx reverse proxy definition |
| `src/nginx/nginx.conf` | Nginx site config (rate limiting, TLS, upstreams) |
| `scripts/deployment/deploy_all.sh` | All-in-one deploy script |
| `config/README.md` | Config template usage guide |
