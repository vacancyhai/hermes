# Sarkari Path - Project Structure

## 📁 Complete Folder Structure

This project follows a **microservices architecture** with clear separation of concerns, adhering to **KISS** (Keep It Simple, Stupid), **DRY** (Don't Repeat Yourself), and **YAGNI** (You Aren't Gonna Need It) principles.

```
sarkari_path_2.0/
│
├── README.md                          # Main project documentation
│
├── docs/                              # 📚 All documentation files
│   ├── INDEX.md                       # Documentation index
│   ├── PROJECT_SUMMARY.md             # Quick start guide
│   ├── DOCKER_DEPLOYMENT.md           # Docker deployment guide
│   ├── JINJA2_TEMPLATES_GUIDE.md      # Frontend templating guide
│   ├── WORKFLOW_DIAGRAMS.md           # System workflow diagrams
│   └── PROJECT_STRUCTURE.md           # This file
│
├── backend/                           # 🔧 Backend Flask API Service
│   ├── app/
│   │   ├── __init__.py               # Flask app factory
│   │   │
│   │   ├── models/                   # 📊 Database models (MongoDB)
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # User model
│   │   │   ├── job.py               # Job posting model
│   │   │   ├── notification.py      # Notification model
│   │   │   ├── application.py       # User job applications
│   │   │   └── admin.py             # Admin user model
│   │   │
│   │   ├── routes/                   # 🛣️ API endpoints (RESTful v1)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # /api/v1/auth/* (login, register, logout, refresh)
│   │   │   ├── jobs.py              # /api/v1/jobs/* (CRUD operations)
│   │   │   ├── users.py             # /api/v1/users/* (profile, preferences)
│   │   │   ├── notifications.py     # /api/v1/notifications/*
│   │   │   ├── admin.py             # /api/v1/admin/* (admin panel, RBAC)
│   │   │   └── health.py            # /api/v1/health (health check)
│   │   │
│   │   ├── services/                 # 💼 Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py      # Authentication logic
│   │   │   ├── job_service.py       # Job matching algorithm
│   │   │   ├── notification_service.py  # Notification logic
│   │   │   ├── email_service.py     # Email sending
│   │   │   └── user_service.py      # User management
│   │   │
│   │   ├── tasks/                    # ⚡ Celery background tasks
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py        # Celery configuration
│   │   │   ├── notification_tasks.py # Send notifications
│   │   │   ├── reminder_tasks.py    # Deadline reminders
│   │   │   └── cleanup_tasks.py     # Database cleanup
│   │   │
│   │   ├── utils/                    # 🛠️ Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── validators.py        # Input validation helpers
│   │   │   ├── decorators.py        # Custom decorators
│   │   │   ├── helpers.py           # Common helper functions
│   │   │   └── constants.py         # Application constants
│   │   │
│   │   ├── middleware/               # 🔐 Middleware components
│   │   │   ├── __init__.py
│   │   │   ├── auth_middleware.py   # JWT verification & token rotation
│   │   │   ├── error_handler.py     # Global error handling with standard codes
│   │   │   ├── rate_limiter.py      # Multi-layer API rate limiting
│   │   │   ├── request_id.py        # Request ID generation for tracing
│   │   │   └── rbac.py              # Role-based access control
│   │   │
│   │   └── validators/               # ✅ Request validators
│   │       ├── __init__.py
│   │       ├── user_validator.py    # User input validation
│   │       ├── job_validator.py     # Job data validation
│   │       └── auth_validator.py    # Auth request validation
│   │
│   ├── config/                       # ⚙️ Configuration files
│   │   ├── __init__.py
│   │   ├── settings.py              # App settings (JWT, rate limits, timeouts)
│   │   ├── database.py              # MongoDB connection with pooling
│   │   ├── redis_config.py          # Redis connection with keepalive
│   │   └── celery_config.py         # Celery configuration with task routing
│   │
│   ├── tests/                        # 🧪 Backend tests
│   │   ├── unit/                    # Unit tests
│   │   │   ├── test_models.py
│   │   │   ├── test_services.py
│   │   │   └── test_validators.py
│   │   └── integration/             # Integration tests
│   │       ├── test_api_auth.py
│   │       ├── test_api_jobs.py
│   │       └── test_notifications.py
│   │
│   ├── logs/                         # 📝 Application logs
│   │   ├── app.log
│   │   └── error.log
│   │
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Docker image definition
│   ├── .dockerignore
│   └── run.py                        # Application entry point
│
├── frontend/                         # 🎨 Frontend Flask + Jinja2 Service
│   ├── app/
│   │   ├── __init__.py              # Flask app factory
│   │   │
│   │   ├── routes/                   # 🛣️ Page routes
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # / (homepage)
│   │   │   ├── auth.py              # /login, /register, /logout
│   │   │   ├── jobs.py              # /jobs, /jobs/<id>
│   │   │   ├── profile.py           # /profile, /settings
│   │   │   ├── admin.py             # /admin/*
│   │   │   └── errors.py            # Error pages (404, 500)
│   │   │
│   │   ├── utils/                    # 🛠️ Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── api_client.py        # Backend API HTTP client
│   │   │   ├── session_manager.py   # Session handling
│   │   │   └── helpers.py           # Template helpers
│   │   │
│   │   └── middleware/               # 🔐 Middleware
│   │       ├── __init__.py
│   │       ├── auth_middleware.py   # Login required decorator
│   │       └── error_handler.py     # Error handling
│   │
│   ├── templates/                    # 📄 Jinja2 templates
│   │   ├── layouts/                 # Base layouts
│   │   │   ├── base.html            # Main layout
│   │   │   ├── admin.html           # Admin layout
│   │   │   └── minimal.html         # Minimal layout (auth pages)
│   │   │
│   │   ├── components/              # Reusable components
│   │   │   ├── navbar.html
│   │   │   ├── footer.html
│   │   │   ├── sidebar.html
│   │   │   ├── job_card.html
│   │   │   ├── notification_item.html
│   │   │   └── pagination.html
│   │   │
│   │   └── pages/                   # Page templates
│   │       ├── index.html           # Homepage
│   │       │
│   │       ├── auth/                # Authentication pages
│   │       │   ├── login.html
│   │       │   ├── register.html
│   │       │   └── forgot_password.html
│   │       │
│   │       ├── jobs/                # Job-related pages
│   │       │   ├── list.html        # Job listings
│   │       │   ├── detail.html      # Job detail page
│   │       │   └── search.html      # Job search
│   │       │
│   │       ├── profile/             # User profile pages
│   │       │   ├── dashboard.html   # User dashboard
│   │       │   ├── settings.html    # Profile settings
│   │       │   ├── applications.html # My applications
│   │       │   └── notifications.html
│   │       │
│   │       └── admin/               # Admin pages
│   │           ├── dashboard.html
│   │           ├── jobs_manage.html
│   │           ├── users_manage.html
│   │           └── analytics.html
│   │
│   ├── static/                       # 📦 Static assets
│   │   ├── css/
│   │   │   ├── main.css             # Main stylesheet
│   │   │   ├── auth.css             # Auth pages styles
│   │   │   ├── jobs.css             # Job pages styles
│   │   │   └── admin.css            # Admin styles
│   │   │
│   │   ├── js/
│   │   │   ├── main.js              # Main JavaScript
│   │   │   ├── jobs.js              # Job interactions
│   │   │   ├── notifications.js     # Notification handling
│   │   │   └── admin.js             # Admin functionality
│   │   │
│   │   ├── images/
│   │   │   ├── logo.png
│   │   │   ├── favicon.ico
│   │   │   └── placeholder.jpg
│   │   │
│   │   └── fonts/                   # Custom fonts
│   │
│   ├── config/                       # ⚙️ Configuration
│   │   ├── __init__.py
│   │   └── settings.py
│   │
│   ├── tests/                        # 🧪 Frontend tests
│   │   ├── unit/
│   │   │   └── test_utils.py
│   │   └── integration/
│   │       ├── test_routes.py
│   │       └── test_templates.py
│   │
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Docker image definition
│   ├── .dockerignore
│   └── run.py                        # Application entry point
│
├── infrastructure/                   # 🏗️ Infrastructure as code
│   ├── nginx/
│   │   ├── nginx.conf               # Main Nginx config
│   │   ├── ssl/                     # SSL certificates
│   │   └── Dockerfile
│   │
│   ├── docker/
│   │   └── docker-compose.yml       # Multi-container orchestration
│   │
│   └── monitoring/
│       ├── prometheus.yml           # Prometheus config
│       └── grafana/                 # Grafana dashboards
│
├── scripts/                          # 🔧 Utility scripts
│   ├── deployment/
│   │   ├── deploy.sh                # Deployment script
│   │   ├── rollback.sh              # Rollback script
│   │   └── health_check.sh          # Health check
│   │
│   ├── backup/
│   │   ├── backup_db.sh             # Database backup
│   │   └── restore_db.sh            # Database restore
│   │
│   └── migration/
│       ├── init_db.js               # Initialize MongoDB
│       └── seed_data.py             # Seed sample data
│
├── config/                           # 🌍 Environment configs
│   ├── production/
│   │   └── .env.production
│   ├── staging/
│   │   └── .env.staging
│   └── development/
│       └── .env.development
│
├── tests/                            # 🧪 End-to-end tests
│   ├── e2e/
│   │   ├── test_user_flow.py
│   │   └── test_admin_flow.py
│   └── load/
│       └── locustfile.py            # Load testing
│
├── .env.example                      # Environment template
├── .gitignore                        # Git ignore rules
├── docker-compose.yml                # Docker orchestration
└── Makefile                          # Common commands

```

## 🎯 Design Principles Applied

### 1. **KISS (Keep It Simple, Stupid)**
- Clear separation: Backend API ↔ Frontend UI
- Single responsibility per module
- Simple, self-explanatory naming conventions
- Minimal dependencies
- API versioning for future compatibility

### 2. **DRY (Don't Repeat Yourself)**
- Services layer for reusable business logic
- Shared utilities and helpers
- Template components for UI reusability
- Common middleware across routes
- Centralized configuration
- Standardized error response format

### 3. **YAGNI (You Aren't Gonna Need It)**
- Only essential folders created
- No premature abstractions
- Features added as needed
- Scalable but not over-engineered

### 4. **Security First**
- JWT token rotation (15 min access + 7 day refresh)
- Multi-layer rate limiting (Nginx + Application)
- RBAC with role-based permissions
- Input validation on all endpoints
- Request ID propagation for tracing
- Connection pooling for performance

### 5. **Production Ready**
- Health checks for all containers
- Redis AOF persistence for task queue
- MongoDB connection pooling (50 max)
- Graceful degradation patterns
- API response SLAs (< 200ms for reads)
- Comprehensive audit logging

## 📂 Key Directory Explanations

### Backend Structure

#### `/backend/app/models/`
MongoDB document models using PyMongo or MongoEngine. Each model represents a collection with proper indexing and TTL (Time To Live) for auto-cleanup.

#### `/backend/app/routes/`
API v1 endpoints organized by resource. Returns standardized JSON responses with error codes (AUTH_*, VALIDATION_*, etc.). All routes prefixed with `/api/v1/`.

#### `/backend/app/services/`
Business logic separated from routes. Keeps controllers thin and logic reusable. Implements graceful degradation (cache fallbacks, retry logic).

#### `/backend/app/tasks/`
Celery tasks for asynchronous operations (emails, notifications, reminders). Tasks routed by priority: HIGH (email), MEDIUM (matching), LOW (analytics).

#### `/backend/app/middleware/`
Request/response interceptors for:
- **JWT authentication** with token rotation
- **Request ID generation** for distributed tracing
- **RBAC enforcement** (role-based access control)
- **Rate limiting** (100 req/min per IP, 1000 req/min per user)
- **Error handling** with standardized response format
- **Audit logging** for sensitive operations

#### `/backend/app/validators/`
Input validation schemas using Marshmallow to ensure data integrity before processing. Prevents injection attacks and validates all user inputs.

### Frontend Structure

#### `/frontend/templates/layouts/`
Base HTML templates extended by pages. Provides consistent structure.

#### `/frontend/templates/components/`
Reusable UI components included in multiple pages (navbar, footer, cards).

#### `/frontend/templates/pages/`
Complete page templates for different routes.

#### `/frontend/static/`
CSS, JavaScript, images, and fonts served directly.

#### `/frontend/app/utils/api_client.py`
HTTP client to communicate with backend API. Centralizes all API calls.

### Infrastructure

#### `/infrastructure/nginx/`
Reverse proxy configuration with:
- **Health check routing** - Only forwards to healthy backends
- **SSL/TLS termination** - HTTPS with Let's Encrypt
- **Rate limiting** - IP-based (100 req/min) and user-based (1000 req/min)
- **Request ID propagation** - X-Request-ID header for correlation
- **Security headers** - HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **API versioning routing** - /api/v1/* to backend

#### `/infrastructure/docker/`
Docker Compose files for **8-container microservices** setup:
1. Nginx (reverse proxy)
2. Frontend (Flask + Jinja2)
3. Backend (Flask REST API)
4. MongoDB (database with connection pooling)
5. Redis (cache + queue with AOF persistence)
6. Celery Worker (scalable: 1-N instances)
7. Celery Beat (scheduler: always 1 instance)
8. Monitoring (health checks & logging)

#### `/scripts/`
Automation scripts for deployment, database backup/restore, and maintenance tasks.

## 🚀 Quick Navigation

- **Start Development**: See `/backend/run.py` and `/frontend/run.py`
- **API Documentation**: Check `/backend/app/routes/`
- **Database Models**: See `/backend/app/models/`
- **UI Templates**: Browse `/frontend/templates/`
- **Configuration**: Environment files in `/config/`
- **Deployment**: Docker Compose in `/infrastructure/docker/`

## 📝 File Naming Conventions

- **Python files**: `snake_case.py` (e.g., `user_service.py`)
- **HTML templates**: `lowercase.html` (e.g., `dashboard.html`)
- **CSS files**: `lowercase.css` (e.g., `main.css`)
- **JavaScript files**: `lowercase.js` (e.g., `notifications.js`)
- **Config files**: `lowercase.ext` or `UPPERCASE.md`

## 🔄 Data Flow

```
User Request + X-Request-ID
    ↓
Nginx (Port 80/443)
    ├─ Rate Limiting (100 req/min per IP)
    ├─ Health Check Routing (only healthy backends)
    ├─ SSL Termination (HTTPS)
    └─ Request ID Propagation
    ↓
Frontend Flask (Jinja2 Rendering)
    ↓
API Client (HTTP Request to /api/v1/*)
    ├─ JWT Token (15 min access token)
    └─ Request ID Header
    ↓
Backend Flask API
    ├─ JWT Verification (Auth Middleware)
    ├─ RBAC Check (Role-based permissions)
    ├─ Rate Limiting (1000 req/min per user)
    ├─ Input Validation (Marshmallow schemas)
    ├─ Route → Service → Model
    └─ Audit Logging (sensitive operations)
    ↓
Data Layer (with connection pooling)
    ├─ MongoDB (maxPoolSize=50)
    │   └─ TTL Indexes (auto-cleanup)
    └─ Redis (AOF persistence, socket keepalive)
        ├─ Cache (Cache-aside pattern)
        └─ Celery Queue (task routing by priority)
    ↓
Response (JSON with standard error codes)
    ├─ X-Request-ID header
    ├─ X-Response-Time header
    └─ Error: {code, message, details, request_id}
    ↓
Frontend (Template Rendering)
    ↓
User Browser


Background Tasks Flow:
    Celery Beat (Scheduler)
        ↓
    Redis Queue (Task routing: HIGH/MEDIUM/LOW)
        ↓
    Celery Workers (Scalable)
        ├─ Email notifications (5x retry with exponential backoff)
        ├─ Job matching (deadline reminders)
        └─ Database cleanup (TTL enforcement)
```

## 🧪 Testing Strategy

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints and services
- **E2E Tests**: Test complete user workflows
- **Load Tests**: Test system under load

## 📦 Extensibility

This structure allows easy addition of:
- New API endpoints (add to `/backend/app/routes/`)
- New services (add to `/backend/app/services/`)
- New pages (add to `/frontend/templates/pages/`)
- New background tasks (add to `/backend/app/tasks/`)
- New models (add to `/backend/app/models/`)

## 🔐 Security Features

### Authentication & Authorization
- **JWT Token Rotation**: 15-minute access tokens + 7-day refresh tokens
- **bcrypt Password Hashing**: Salted password storage
- **RBAC System**: Three roles (User, Operator, Admin) with permission matrix
- **Session Management**: Secure session handling in frontend

### API Security
- **Multi-Layer Rate Limiting**:
  - Nginx: 100 req/min per IP
  - Application: 1000 req/min per user
  - Login: 5 attempts per minute
- **Input Validation**: Marshmallow schemas on all endpoints
- **CORS**: Whitelisted origins only
- **API Versioning**: `/api/v1/` for safe upgrades

### Data Security
- **MongoDB Authentication**: Password-protected with connection pooling
- **Redis Authentication**: Password + AOF persistence
- **Environment Variables**: Secrets in .env (dev) or Vault (prod)
- **Secrets Management**: HashiCorp Vault or AWS Secrets Manager

### Network Security
- **HTTPS/SSL**: Let's Encrypt certificates with auto-renewal
- **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **SSL/TLS**: TLS 1.2+ only, strong cipher suites

### Monitoring & Auditing
- **Request ID Propagation**: X-Request-ID header for distributed tracing
- **Audit Logging**: All sensitive operations logged with user, IP, timestamp
- **Error Tracking**: Standardized error codes (AUTH_*, VALIDATION_*, etc.)
- **Health Checks**: All containers monitored by Nginx

### Production Checklist
- [ ] All secrets in environment variables (no hardcoded passwords)
- [ ] HTTPS enabled with valid certificate
- [ ] JWT tokens use short expiration (15 min access, 7 day refresh)
- [ ] Rate limiting enabled at both Nginx and application layers
- [ ] CORS configured with specific allowed origins
- [ ] Security headers on all responses
- [ ] Input validation on all endpoints
- [ ] Audit logging for admin operations
- [ ] Database backups with encryption
- [ ] Secrets in Vault/AWS Secrets Manager (not .env)

## 📊 Performance Optimizations

### Connection Pooling
- **MongoDB**: maxPoolSize=50, minPoolSize=10
- **Redis**: 50 max connections, socket keepalive enabled
- **Benefits**: Faster queries, prevents connection exhaustion

### Caching Strategy (Cache-Aside Pattern)
```
Request → Check Redis Cache
    ├─ Cache Hit → Return data (fast)
    └─ Cache Miss → Load from MongoDB → Cache for next time
```

**Cache TTLs by Data Type:**
- User Sessions: 15 minutes
- Job Listings: 1 hour
- User Preferences: 24 hours
- Search Results: 30 minutes
- Rate Limit Counts: 1 minute

### API Response SLAs
- Auth endpoints (login/register): < 100ms (p95)
- Read endpoints (GET /jobs): < 200ms (p95)
- Write endpoints (POST /jobs): < 300ms (p95)
- Search endpoints: < 500ms (p95)
- Admin endpoints: < 1000ms (p95)

### Database Optimization
- **TTL Indexes**: Auto-delete old notifications (90d), logs (30d), audits (1y)
- **Query Indexes**: Fast lookups on email, user_id, job filters
- **Aggregation**: Use MongoDB aggregation pipeline for analytics

### Celery Task Routing
- **HIGH Priority**: Email notifications (immediate)
- **MEDIUM Priority**: Job matching (hourly)
- **LOW Priority**: Analytics & cleanup (daily)

### Graceful Degradation
- **Redis Down**: Fall back to database, queue tasks for later
- **MongoDB Slow**: Return stale cache with warning flag
- **Celery Down**: Accept job, queue in Redis, process when available
- **Email Failed**: Retry 5x with exponential backoff

---

## 🔧 Configuration Management

### Environment-Specific Configs
```
config/
├── development/
│   └── .env.development    # Local dev settings
├── staging/
│   └── .env.staging        # Staging settings
└── production/
    └── .env.production     # Production (use Vault/Secrets Manager)
```

### Key Configuration Parameters

**JWT Settings:**
- `JWT_ACCESS_TOKEN_EXPIRES=900` (15 minutes)
- `JWT_REFRESH_TOKEN_EXPIRES=604800` (7 days)

**Rate Limiting:**
- `RATE_LIMIT_PER_IP=100` (per minute)
- `RATE_LIMIT_PER_USER=1000` (per minute)
- `RATE_LIMIT_LOGIN=5` (per minute)

**Timeouts:**
- `API_REQUEST_TIMEOUT=10` (seconds)
- `DB_CONNECTION_TIMEOUT=5` (seconds)
- `REDIS_SOCKET_TIMEOUT=5` (seconds)

**Data Retention:**
- `NOTIFICATION_TTL=7776000` (90 days)
- `LOG_TTL=2592000` (30 days)
- `AUDIT_TTL=31536000` (1 year)

**Connection Pooling:**
- `MONGO_MAX_POOL_SIZE=50`
- `MONGO_MIN_POOL_SIZE=10`
- `REDIS_MAX_CONNECTIONS=50`

---

**Last Updated**: March 2026
**Version**: 2.0
**Architecture**: 8-Container Microservices with API v1
