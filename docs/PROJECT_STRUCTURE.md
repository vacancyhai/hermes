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
│   │   ├── routes/                   # 🛣️ API endpoints (RESTful)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # /api/auth/* (login, register, logout)
│   │   │   ├── jobs.py              # /api/jobs/* (CRUD operations)
│   │   │   ├── users.py             # /api/users/* (profile, preferences)
│   │   │   ├── notifications.py     # /api/notifications/*
│   │   │   ├── admin.py             # /api/admin/* (admin panel)
│   │   │   └── health.py            # /api/health (health check)
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
│   │   │   ├── auth_middleware.py   # JWT verification
│   │   │   ├── error_handler.py     # Global error handling
│   │   │   └── rate_limiter.py      # API rate limiting
│   │   │
│   │   └── validators/               # ✅ Request validators
│   │       ├── __init__.py
│   │       ├── user_validator.py    # User input validation
│   │       ├── job_validator.py     # Job data validation
│   │       └── auth_validator.py    # Auth request validation
│   │
│   ├── config/                       # ⚙️ Configuration files
│   │   ├── __init__.py
│   │   ├── settings.py              # App settings
│   │   ├── database.py              # MongoDB connection
│   │   └── celery_config.py         # Celery configuration
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

### 2. **DRY (Don't Repeat Yourself)**
- Services layer for reusable business logic
- Shared utilities and helpers
- Template components for UI reusability
- Common middleware across routes
- Centralized configuration

### 3. **YAGNI (You Aren't Gonna Need It)**
- Only essential folders created
- No premature abstractions
- Features added as needed
- Scalable but not over-engineered

## 📂 Key Directory Explanations

### Backend Structure

#### `/backend/app/models/`
MongoDB document models using PyMongo or MongoEngine. Each model represents a collection.

#### `/backend/app/routes/`
API endpoints organized by resource. Returns JSON responses.

#### `/backend/app/services/`
Business logic separated from routes. Keeps controllers thin and logic reusable.

#### `/backend/app/tasks/`
Celery tasks for asynchronous operations (emails, notifications, reminders).

#### `/backend/app/middleware/`
Request/response interceptors for authentication, logging, error handling.

#### `/backend/app/validators/`
Input validation schemas to ensure data integrity before processing.

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
Reverse proxy configuration for routing and SSL termination.

#### `/infrastructure/docker/`
Docker Compose files for multi-container setup.

#### `/scripts/`
Automation scripts for deployment, backup, and maintenance.

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
User Request
    ↓
Nginx (Port 80/443)
    ↓
Frontend Flask (Jinja2 Rendering)
    ↓
API Client (HTTP Request)
    ↓
Backend Flask API (Route → Service → Model)
    ↓
MongoDB/Redis
    ↓
Response (JSON)
    ↓
Frontend (Template Rendering)
    ↓
User Browser
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

## 🔐 Security Considerations

- Environment variables in `/config/` (never committed)
- JWT tokens for API authentication
- Session management in frontend
- Input validation in validators
- Rate limiting middleware
- HTTPS via Nginx

---

**Last Updated**: December 2025
**Version**: 2.0
