# Sarkari Path - Project Structure

## 📁 Complete Folder Structure

This project follows a **fully decoupled microservices architecture** with **complete separation of backend and frontend**, adhering to **KISS** (Keep It Simple, Stupid), **DRY** (Don't Repeat Yourself), and **YAGNI** (You Aren't Gonna Need It) principles.

**🎯 KEY ARCHITECTURE DECISION**: Backend and Frontend are **COMPLETELY INDEPENDENT** services living in separate folders under `src/`. Each can be developed, deployed, and scaled independently. This allows changing the frontend technology stack (Flask → React → iOS → Android) without touching the backend code.

```
sarkari_path_2.0/
│
├── README.md                          # Main project documentation
│
├── docs/                              # 📚 All documentation files
│   ├── INDEX.md                       # Documentation index
│   ├── PROJECT_SUMMARY.md             # Quick start guide
│   ├── DOCKER_DEPLOYMENT.md           # Docker deployment guide
│   ├── JINJA2_TEMPLATES_GUIDE.md      # Frontend templating guide (Flask)
│   ├── WORKFLOW_DIAGRAMS.md           # System workflow diagrams
│   └── PROJECT_STRUCTURE.md           # This file
│
├── epic/                              # 📋 Feature epics and planning
│   ├── EPIC_01_DOCKER_INFRASTRUCTURE.md
│   ├── EPIC_02_BACKEND_API_FOUNDATION.md
│   ├── EPIC_03_USER_AUTHENTICATION.md
│   └── ... (12 epic files total)
│
├── src/                               # 🚀 SOURCE CODE (Backend + Frontend SEPARATED)
│   │
│   ├── backend/                       # 🔧 BACKEND SERVICE (INDEPENDENT)
│   │   │
│   │   ├── docker-compose.yml        # Backend orchestration
│   │   │                              # Services: MongoDB, Redis, Backend API, Celery Worker, Celery Beat
│   │   ├── Dockerfile                # Backend container definition
│   │   ├── requirements.txt          # Python dependencies
│   │   ├── .env.example              # Backend environment template
│   │   ├── .dockerignore
│   │   ├── run.py                    # Backend entry point
│   │   ├── README.md                 # Backend-specific documentation
│   │   │
│   │   ├── app/
│   │   │   ├── __init__.py               # Flask app factory
│   │   │   │
│   │   │   ├── models/                   # 📊 Database models (MongoDB)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py              # User model
│   │   │   │   ├── job.py               # Job posting model
│   │   │   │   ├── notification.py      # Notification model
│   │   │   │   ├── application.py       # User job applications
│   │   │   │   └── admin.py             # Admin user model
│   │   │   │
│   │   │   ├── routes/                   # 🛣️ API endpoints (RESTful v1)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py              # /api/v1/auth/* (login, register, logout, refresh)
│   │   │   │   ├── jobs.py              # /api/v1/jobs/* (CRUD operations)
│   │   │   │   ├── users.py             # /api/v1/users/* (profile, preferences)
│   │   │   │   ├── notifications.py     # /api/v1/notifications/*
│   │   │   │   ├── admin.py             # /api/v1/admin/* (admin panel, RBAC)
│   │   │   │   └── health.py            # /api/v1/health (health check)
│   │   │   │
│   │   │   ├── services/                 # 💼 Business logic layer
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_service.py      # Authentication logic
│   │   │   │   ├── job_service.py       # Job matching algorithm
│   │   │   │   ├── notification_service.py  # Notification logic
│   │   │   │   ├── email_service.py     # Email sending
│   │   │   │   └── user_service.py      # User management
│   │   │   │
│   │   │   ├── tasks/                    # ⚡ Celery background tasks
│   │   │   │   ├── __init__.py
│   │   │   │   ├── celery_app.py        # Celery configuration
│   │   │   │   ├── notification_tasks.py # Send notifications
│   │   │   │   ├── reminder_tasks.py    # Deadline reminders
│   │   │   │   └── cleanup_tasks.py     # Database cleanup
│   │   │   │
│   │   │   ├── utils/                    # 🛠️ Utility functions
│   │   │   │   ├── __init__.py
│   │   │   │   ├── validators.py        # Input validation helpers
│   │   │   │   ├── decorators.py        # Custom decorators
│   │   │   │   ├── helpers.py           # Common helper functions
│   │   │   │   └── constants.py         # Application constants
│   │   │   │
│   │   │   ├── middleware/               # 🔐 Middleware components
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth_middleware.py   # JWT verification & token rotation
│   │   │   │   ├── error_handler.py     # Global error handling with standard codes
│   │   │   │   ├── rate_limiter.py      # Multi-layer API rate limiting
│   │   │   │   ├── request_id.py        # Request ID generation for tracing
│   │   │   │   └── rbac.py              # Role-based access control
│   │   │   │
│   │   │   └── validators/               # ✅ Request validators
│   │   │       ├── __init__.py
│   │   │       ├── user_validator.py    # User input validation
│   │   │       ├── job_validator.py     # Job data validation
│   │   │       └── auth_validator.py    # Auth request validation
│   │   │
│   │   ├── config/                       # ⚙️ Configuration files
│   │   │   ├── __init__.py
│   │   │   ├── settings.py              # App settings (JWT, rate limits, timeouts)
│   │   │   ├── database.py              # MongoDB connection with pooling
│   │   │   ├── redis_config.py          # Redis connection with keepalive
│   │   │   └── celery_config.py         # Celery configuration with task routing
│   │   │
│   │   ├── tests/                        # 🧪 Backend tests
│   │   │   ├── unit/                    # Unit tests
│   │   │   │   ├── test_models.py
│   │   │   │   ├── test_services.py
│   │   │   │   └── test_validators.py
│   │   │   └── integration/             # Integration tests
│   │   │       ├── test_api_auth.py
│   │   │       ├── test_api_jobs.py
│   │   │       └── test_notifications.py
│   │   │
│   │   └── logs/                         # 📝 Application logs
│   │       ├── app.log
│   │       └── error.log
│   │
│   │
│   └── frontend/                      # 🎨 FRONTEND SERVICE (INDEPENDENT)
│       │                              # 🔄 Can be replaced with React, React Native, iOS, Android
│       │                              # Current: Flask + Jinja2 (SSR)
│       │                              # Future: React SPA / Mobile Apps
│       │
│       ├── docker-compose.yml        # Frontend orchestration (Frontend only)
│       ├── Dockerfile                # Frontend container definition
│       ├── requirements.txt          # Python dependencies (Flask version)
│       ├── .env.example              # Frontend environment template
│       ├── .dockerignore
│       ├── run.py                    # Frontend entry point
│       ├── README.md                 # Frontend-specific documentation
│       │
│       ├── app/
│       │   ├── __init__.py              # Flask app factory
│       │   │
│       │   ├── routes/                   # 🛣️ Page routes
│       │   │   ├── __init__.py
│       │   │   ├── main.py              # / (homepage)
│       │   │   ├── auth.py              # /login, /register, /logout
│       │   │   ├── jobs.py              # /jobs, /jobs/<id>
│       │   │   ├── profile.py           # /profile, /settings
│       │   │   ├── admin.py             # /admin/*
│       │   │   └── errors.py            # Error pages (404, 500)
│       │   │
│       │   ├── utils/                    # 🛠️ Utility functions
│       │   │   ├── __init__.py
│       │   │   ├── api_client.py        # Backend API HTTP client
│       │   │   │                         # Calls: http://BACKEND_API_URL/api/v1/*
│       │   │   ├── session_manager.py   # Session handling
│       │   │   └── helpers.py           # Template helpers
│       │   │
│       │   └── middleware/               # 🔐 Middleware
│       │       ├── __init__.py
│       │       ├── auth_middleware.py   # Login required decorator
│       │       └── error_handler.py     # Error handling
│       │
│       ├── templates/                    # 📄 Jinja2 templates (Flask only)
│       │   │                             # NOTE: Remove this folder for React/Mobile
│       │   ├── layouts/                 # Base layouts
│       │   │   ├── base.html            # Main layout
│       │   │   ├── admin.html           # Admin layout
│       │   │   └── minimal.html         # Minimal layout (auth pages)
│       │   │
│       │   ├── components/              # Reusable components
│       │   │   ├── navbar.html
│       │   │   ├── footer.html
│       │   │   ├── sidebar.html
│       │   │   ├── job_card.html
│       │   │   ├── notification_item.html
│       │   │   └── pagination.html
│       │   │
│       │   └── pages/                   # Page templates
│       │       ├── index.html           # Homepage
│       │       │
│       │       ├── auth/                # Authentication pages
│       │       │   ├── login.html
│       │       │   ├── register.html
│       │       │   └── forgot_password.html
│       │       │
│       │       ├── jobs/                # Job-related pages
│       │       │   ├── list.html        # Job listings
│       │       │   ├── detail.html      # Job detail page
│       │       │   └── search.html      # Job search
│       │       │
│       │       ├── profile/             # User profile pages
│       │       │   ├── dashboard.html   # User dashboard
│       │       │   ├── settings.html    # Profile settings
│       │       │   ├── applications.html # My applications
│       │       │   └── notifications.html
│       │       │
│       │       └── admin/               # Admin pages
│       │           ├── dashboard.html
│       │           ├── jobs_manage.html
│       │           ├── users_manage.html
│       │           └── analytics.html
│       │
│       ├── static/                       # 📦 Static assets (Flask only)
│       │   │                             # NOTE: Remove this folder for React/Mobile
│       │   ├── css/
│       │   │   ├── main.css             # Main stylesheet
│       │   │   ├── auth.css             # Auth pages styles
│       │   │   ├── jobs.css             # Job pages styles
│       │   │   └── admin.css            # Admin styles
│       │   │
│       │   ├── js/
│       │   │   ├── main.js              # Main JavaScript
│       │   │   ├── jobs.js              # Job interactions
│       │   │   ├── notifications.js     # Notification handling
│       │   │   └── admin.js             # Admin functionality
│       │   │
│       │   ├── images/
│       │   │   ├── logo.png
│       │   │   ├── favicon.ico
│       │   │   └── placeholder.jpg
│       │   │
│       │   └── fonts/                   # Custom fonts
│       │
│       ├── config/                       # ⚙️ Configuration
│       │   ├── __init__.py
│       │   └── settings.py
│       │
│       └── tests/                        # 🧪 Frontend tests
│           ├── unit/
│           │   └── test_utils.py
│           └── integration/
│               ├── test_routes.py
│               └── test_templates.py
│
├── config/                           # 🌍 Environment configs (shared reference only)
│   ├── production/
│   │   ├── .env.backend.production
│   │   └── .env.frontend.production
│   ├── staging/
│   │   ├── .env.backend.staging
│   │   └── .env.frontend.staging
│   └── development/
│       ├── .env.backend.development
│       └── .env.frontend.development
│
├── scripts/                          # 🔧 Utility scripts
│   ├── deployment/
│   │   ├── deploy_backend.sh        # Deploy backend
│   │   ├── deploy_frontend.sh       # Deploy frontend
│   │   ├── deploy_all.sh            # Deploy both
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
├── tests/                            # 🧪 End-to-end tests
│   ├── e2e/
│   │   ├── test_user_flow.py
│   │   └── test_admin_flow.py
│   └── load/
│       └── locustfile.py            # Load testing
│
├── .gitignore                        # Git ignore rules
└── Makefile                          # Common commands

```

## 🎯 Design Principles Applied

### 1. **Complete Separation** ✨
**Backend and Frontend are COMPLETELY INDEPENDENT:**
- ✅ Each lives in its own folder under `src/`
- ✅ Each has its own `docker-compose.yml`
- ✅ Each has its own `.env` file
- ✅ Each can be developed independently
- ✅ Each can be deployed to different servers
- ✅ Each can be scaled independently
- ✅ Each has its own git repository (if needed)

**Communication**: Frontend calls Backend via HTTP REST API
```
Frontend (any tech) → HTTP → Backend API (http://backend-url:5000/api/v1/*)
```

**Future-Proof**: Can replace frontend WITHOUT touching backend:
- Current: Flask + Jinja2 (SSR)
- Future Options:
  - React SPA
  - React Native (iOS + Android)
  - Native iOS (Swift)
  - Native Android (Kotlin)
  - Flutter
  - Any technology that can make HTTP calls!

### 2. **KISS (Keep It Simple, Stupid)**
- Clear separation: Backend API ↔ Frontend UI
- Single responsibility per module
- Simple, self-explanatory naming conventions
- Minimal dependencies
- API versioning for future compatibility (`/api/v1/`)

### 3. **DRY (Don't Repeat Yourself)**
- Services layer for reusable business logic
- Shared utilities and helpers
- Template components for UI reusability (Flask)
- Common middleware across routes
- Centralized configuration
- Standardized error response format

### 4. **YAGNI (You Aren't Gonna Need It)**
- Only essential folders created
- No premature abstractions
- Features added as needed
- Scalable but not over-engineered

### 5. **Security First**
- JWT token rotation (15 min access + 7 day refresh)
- Multi-layer rate limiting (API level)
- RBAC with role-based permissions
- Input validation on all endpoints
- Request ID propagation for tracing
- Connection pooling for performance

### 6. **Production Ready**
- Health checks for all containers
- Redis AOF persistence for task queue
- MongoDB connection pooling (50 max)
- Graceful degradation patterns
- API response SLAs (< 200ms for reads)
- Comprehensive audit logging

## 📂 Key Directory Explanations

### Backend Structure (`src/backend/`)

**Complete Backend Ecosystem:**
- MongoDB (Database)
- Redis (Cache + Task Queue)
- Backend API (Flask REST)
- Celery Worker (Background tasks)
- Celery Beat (Task scheduler)

All orchestrated via `src/backend/docker-compose.yml`

#### `/backend/app/models/`
MongoDB document models using PyMongo or MongoEngine. Each model represents a collection with proper indexing and TTL (Time To Live) for auto-cleanup.

#### `/backend/app/routes/`
API v1 endpoints organized by resource. Returns standardized JSON responses with error codes. All routes prefixed with `/api/v1/`.

#### `/backend/app/services/`
Business logic separated from routes. Keeps controllers thin and logic reusable. Implements graceful degradation.

#### `/backend/app/tasks/`
Celery tasks for asynchronous operations (emails, notifications, reminders). Tasks routed by priority: HIGH, MEDIUM, LOW.

#### `/backend/app/middleware/`
Request/response interceptors for JWT auth, RBAC, rate limiting, error handling, audit logging.

#### `/backend/app/validators/`
Input validation schemas using Marshmallow to ensure data integrity before processing.

### Frontend Structure (`src/frontend/`)

**Complete Frontend Service:**
- Frontend web server (Flask + Jinja2)
- Static assets (CSS, JS, images)
- Templates (HTML)
- API client to call backend

All orchestrated via `src/frontend/docker-compose.yml`

#### `/frontend/app/utils/api_client.py`
HTTP client to communicate with backend API. Centralizes all API calls.
Example: `http://backend:5000/api/v1/jobs`

#### `/frontend/templates/`
Jinja2 templates for Flask. **NOTE**: Remove this when migrating to React/Mobile.

#### `/frontend/static/`
CSS, JavaScript, images served directly. **NOTE**: Remove this when migrating to React/Mobile.

### Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SEPARATED SERVICES                        │
└─────────────────────────────────────────────────────────────┘

┌───────────────────────────┐       ┌──────────────────────────┐
│   BACKEND SERVICE         │       │   FRONTEND SERVICE       │
│   (src/backend/)          │◄──────│   (src/frontend/)        │
│                           │ HTTP  │                          │
│   Port: 5000              │ REST  │   Port: 8080 or any      │
│                           │ API   │                          │
│   docker-compose.yml:     │       │   docker-compose.yml:    │
│   - MongoDB               │       │   - Frontend only        │
│   - Redis                 │       │                          │
│   - Backend API           │       │   Calls backend via:     │
│   - Celery Worker         │       │   http://backend:5000    │
│   - Celery Beat           │       │   /api/v1/*              │
│                           │       │                          │
│   Exposes: /api/v1/*      │       │   Serves: HTML/SPA       │
└───────────────────────────┘       └──────────────────────────┘

        Deploy separately on different servers if needed!
```

## 🚀 Quick Navigation

### Backend Development
- **Start Backend**: `cd src/backend && docker-compose up`
- **API Documentation**: Check `/src/backend/app/routes/`
- **Database Models**: See `/src/backend/app/models/`
- **Business Logic**: See `/src/backend/app/services/`

### Frontend Development
- **Start Frontend**: `cd src/frontend && docker-compose up`
- **UI Templates**: Browse `/src/frontend/templates/`
- **API Client**: See `/src/frontend/app/utils/api_client.py`
- **Static Assets**: See `/src/frontend/static/`

### Deployment
- **Backend Only**: `cd src/backend && docker-compose up -d`
- **Frontend Only**: `cd src/frontend && docker-compose up -d`
- **Both**: Run both commands above

## 📝 File Naming Conventions

- **Python files**: `snake_case.py` (e.g., `user_service.py`)
- **HTML templates**: `lowercase.html` (e.g., `dashboard.html`)
- **CSS files**: `lowercase.css` (e.g., `main.css`)
- **JavaScript files**: `lowercase.js` (e.g., `notifications.js`)
- **Config files**: `lowercase.ext` or `UPPERCASE.md`

## 🔄 Data Flow

```
User Request
    ↓
Frontend Service (src/frontend/)
    ├─ Render UI (Flask/React/Mobile)
    └─ Call Backend API
    ↓
HTTP Request: http://backend-url:5000/api/v1/*
    ├─ Headers: Authorization: Bearer <JWT>
    ├─ Headers: X-Request-ID: <uuid>
    └─ Body: JSON data
    ↓
Backend Service (src/backend/)
    ├─ JWT Verification
    ├─ RBAC Check
    ├─ Rate Limiting
    ├─ Input Validation
    ├─ Business Logic (Service Layer)
    └─ Database Operations
    ↓
Response: JSON
    ├─ Status: 200/400/401/403/500
    ├─ Headers: X-Request-ID
    └─ Body: {data, error, message}
    ↓
Frontend Service
    ├─ Parse Response
    ├─ Update UI
    └─ Handle Errors
    ↓
User sees result


Background Tasks (in Backend):
    Celery Beat → Schedule tasks
        ↓
    Redis Queue
        ↓
    Celery Workers → Execute tasks
        ├─ Send emails
        ├─ Match jobs
        └─ Clean database
```

## 🧪 Testing Strategy

- **Backend Unit Tests**: Test API endpoints, services, models
- **Frontend Unit Tests**: Test UI components, API client
- **Integration Tests**: Test frontend →  backend communication
- **E2E Tests**: Test complete user workflows
- **Load Tests**: Test system under load

## 📦 Extensibility

This structure allows easy addition of:
- **New API endpoints**: Add to `/src/backend/app/routes/`
- **New services**: Add to `/src/backend/app/services/`
- **New frontend pages**: Add to `/src/frontend/templates/pages/`
- **New background tasks**: Add to `/src/backend/app/tasks/`
- **New models**: Add to `/src/backend/app/models/`
- **New frontend tech**: Replace entire `/src/frontend/` folder!

## 🔄 Migration Path: Flask → React → Mobile

### Current State (Flask SSR)
```
src/frontend/
├── templates/          # Jinja2 HTML
├── static/             # CSS, JS
└── app/routes/         # Flask routes
```

### Future State (React SPA)
```
src/frontend/
├── src/                # React components
│   ├── components/
│   ├── pages/
│   ├── services/
│   │   └── api.js     # Calls backend REST API
│   └── App.jsx
├── public/
├── package.json
└── Dockerfile          # Node.js container
```

### Future State (React Native Mobile)
```
src/frontend-mobile/
├── src/
│   ├── screens/
│   ├── components/
│   ├── services/
│   │   └── api.js     # Calls backend REST API
│   └── App.jsx
├── ios/
├── android/
├── package.json
└── No Docker needed    # Mobile apps
```

**Backend Code**: ZERO CHANGES! 🎉

## 🔐 Security Features

### Authentication & Authorization
- **JWT Token Rotation**: 15-minute access tokens + 7-day refresh tokens
- **bcrypt Password Hashing**: Salted password storage
- **RBAC System**: Three roles (User, Operator, Admin)

### API Security
- **Rate Limiting**: 100 req/min per IP, 1000 req/min per user
- **Input Validation**: Marshmallow schemas on all endpoints
- **CORS**: Configurable origins
- **API Versioning**: `/api/v1/` for safe upgrades

### Data Security
- **MongoDB Authentication**: Password-protected with connection pooling
- **Redis Authentication**: Password + AOF persistence
- **Environment Variables**: Secrets in `.env` files

### Monitoring & Auditing
- **Request ID Propagation**: X-Request-ID header for tracing
- **Audit Logging**: All sensitive operations logged
- **Error Tracking**: Standardized error codes
- **Health Checks**: All services monitored

## 📊 Performance Optimizations

### Connection Pooling
- **MongoDB**: maxPoolSize=50, minPoolSize=10
- **Redis**: 50 max connections, socket keepalive enabled

### Caching Strategy
- User Sessions: 15 minutes
- Job Listings: 1 hour
- User Preferences: 24 hours

### API Response SLAs
- Auth endpoints: < 100ms (p95)
- Read endpoints: < 200ms (p95)
- Write endpoints: < 300ms (p95)

### Celery Task Routing
- **HIGH Priority**: Email notifications
- **MEDIUM Priority**: Job matching
- **LOW Priority**: Analytics & cleanup

---

**Last Updated**: March 2026
**Version**: 2.0
**Architecture**: Decoupled Backend + Frontend (src/ separation)