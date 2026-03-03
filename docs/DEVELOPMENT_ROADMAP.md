# Development Roadmap - Files to Implement

## 🎯 Priority 1: Core Backend API (Start Here)

### 1. Database Models (`backend/app/models/`)
- [ ] `user.py` - User model with authentication fields
- [ ] `job.py` - Job posting model
- [ ] `notification.py` - Notification model
- [ ] `application.py` - User job applications tracking
- [ ] `admin.py` - Admin user model

### 2. API Routes (`backend/app/routes/`)
- [ ] `health.py` - Health check endpoint
  ```python
  # GET /api/health
  ```
- [ ] `auth.py` - Authentication endpoints
  ```python
  # POST /api/auth/register
  # POST /api/auth/login
  # POST /api/auth/logout
  # POST /api/auth/refresh
  ```
- [ ] `users.py` - User management
  ```python
  # GET /api/users/profile
  # PUT /api/users/profile
  # GET /api/users/preferences
  # PUT /api/users/preferences
  ```
- [ ] `jobs.py` - Job CRUD operations
  ```python
  # GET /api/jobs
  # GET /api/jobs/<id>
  # POST /api/jobs (admin only)
  # PUT /api/jobs/<id> (admin only)
  # DELETE /api/jobs/<id> (admin only)
  ```
- [ ] `notifications.py` - Notification management
  ```python
  # GET /api/notifications
  # PUT /api/notifications/<id>/read
  # DELETE /api/notifications/<id>
  ```
- [ ] `admin.py` - Admin panel APIs
  ```python
  # GET /api/v1/admin/stats
  # GET /api/v1/admin/users
  # GET /api/v1/admin/jobs
  ```

### 2a. API Versioning Strategy ⚡ IMPORTANT
**All API endpoints MUST use versioning format: `/api/v1/`**

Why? Without versioning, when you update endpoints, frontend breaks. With versioning, you can run v1 and v2 simultaneously.

**Implementation**:
```python
# backend/app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Register blueprint with version prefix
    from app.routes import auth_bp, jobs_bp, users_bp, admin_bp
    
    api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
    api_v1.register_blueprint(auth_bp)
    api_v1.register_blueprint(jobs_bp)
    api_v1.register_blueprint(users_bp)
    api_v1.register_blueprint(admin_bp)
    
    app.register_blueprint(api_v1)
    return app
```

**Endpoint Format**:
- ✅ Future-safe: `GET /api/v1/jobs?limit=20`
- ✅ Easy v2: `GET /api/v2/jobs?page=2`
- ✅ Frontend compatibility: Change base URL on deploy

- [ ] `rbac_service.py` - Role-based access control
  - Check user permissions
  - Verify admin/user/moderator roles
  - Grant resource access based on role

### 3b. ⚡ Role-Based Access Control (RBAC) Matrix

**Who can access what?**

| Resource | Create | Read | Update | Delete | User | Admin | Moderator |
|----------|--------|------|--------|--------|------|-------|---------- |
| Own Profile | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| Other Profiles | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Jobs (View) | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Jobs (Create) | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Jobs (Update) | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Jobs (Delete) | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Notifications | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Admin Panel | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Analytics | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

**Implementation**:
```python
# backend/app/middleware/rbac_middleware.py
from functools import wraps
from flask import abort

def require_role(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = get_current_user()  # From JWT
            
            if user.role not in allowed_roles:
                abort(403)  # Forbidden
            
            return fn(*args, **kwargs)
        return wrapped
    return decorator

# Usage in routes:
# @bp.route('/api/v1/admin/jobs', methods=['POST'])
# @require_role('admin')
# def create_job():
#     # Only admin can execute
#     pass
```

### 3b. ⚡ CORS Configuration (Frontend-Backend Separation)

**Why CORS?** Frontend and Backend are different origins. Without proper CORS, browser blocks requests.

**Implementation**:
```python
# backend/app/__init__.py
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # ⚡ CORS - only allow frontend origin
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:8080",      # Local dev
                "https://yourdomain.com",     # Production
            ],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    return app
```

**Security**: Only whitelisted origins can access API. Credentials only sent to trusted domains.

- [ ] `auth_service.py` - Authentication logic
  - User registration
  - Login with JWT (access + refresh tokens)
  - Password hashing with bcrypt
  - Token generation/validation
  - ⚡ Token rotation every 15 minutes (refresh token = new access token)
  
- [ ] `job_service.py` - Job matching algorithm
  - Match jobs to user qualifications
  - Filter by education, category, age
  - Sort by relevance
  
- [ ] `notification_service.py` - Notification logic
  - Create notifications
  - Mark as read
  - Send notifications
  
- [ ] `email_service.py` - Email sending
  - Send welcome email
  - Send job alerts
  - Send deadline reminders
  
- [ ] `user_service.py` - User management
  - Profile updates
  - Preference management
  - Application tracking

### 3a. ⚡ JWT Token Rotation Strategy (CRITICAL for Security)

**Problem**: Long-lived JWT tokens = if compromised, attacker has access for hours/days

**Solution**: Use access + refresh token pattern with automatic rotation every 15 minutes

**Implementation**:
```python
# backend/app/services/auth_service.py
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token

class AuthService:
    @staticmethod
    def generate_tokens(user_id):
        # Access token = short-lived (15 minutes)
        access_token = create_access_token(
            identity=user_id,
            expires_delta=timedelta(minutes=15)
        )
        
        # Refresh token = long-lived (7 days)
        refresh_token = create_refresh_token(
            identity=user_id,
            expires_delta=timedelta(days=7)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 900  # 15 minutes in seconds
        }

# Endpoint: POST /api/v1/auth/refresh
# Frontend calls this every 14 minutes automatically
# Gets new access_token without re-login
```

**Frontend Implementation**:
```javascript
// frontend/app/utils/api_client.py
class APIClient:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
    
    def auto_refresh_token(self):
        # Call every 14 minutes to get new access token
        response = requests.post(
            'http://backend:5000/api/v1/auth/refresh',
            headers={'Authorization': f'Bearer {self.refresh_token}'}
        )
        self.access_token = response.json()['access_token']
```

**Benefits**:
- ✅ If access_token is stolen, only ~15 minutes of access
- ✅ Refresh_token is longer-lived but rotated separately
- ✅ Each refresh = new token (can't reuse old ones)
- ✅ Users stay logged in seamlessly

### 4. Database Configuration (`backend/config/`)
- [ ] `database.py` - MongoDB connection
  ```python
  # PyMongo client setup
  # Collections initialization
  # Connection pooling
  ```

### 5. Celery Tasks (`backend/app/tasks/`)
- [ ] `celery_app.py` - Celery configuration
- [ ] `notification_tasks.py` - Send notifications
  - Send email notifications
  - Send push notifications
  
- [ ] `reminder_tasks.py` - Deadline reminders
  - Check jobs expiring in 7 days
  - Check jobs expiring in 3 days
  - Check jobs expiring in 1 day
  
- [ ] `cleanup_tasks.py` - Database cleanup
  - Remove expired jobs
  - Archive old notifications

## 🎯 Priority 2: Frontend UI

### 1. Page Routes (`frontend/app/routes/`)
- [ ] `main.py` - Homepage route
- [ ] `auth.py` - Login, register, logout pages
- [ ] `jobs.py` - Job listing and detail pages
- [ ] `profile.py` - User profile and settings
- [ ] `admin.py` - Admin dashboard pages
- [ ] `errors.py` - Error pages (404, 500)

### 2. Templates (`frontend/templates/`)

#### Layouts (`layouts/`)
- [ ] `base.html` - Main layout with navbar, footer
- [ ] `admin.html` - Admin panel layout
- [ ] `minimal.html` - Minimal layout for auth pages

#### Components (`components/`)
- [ ] `navbar.html` - Navigation bar
- [ ] `footer.html` - Footer
- [ ] `sidebar.html` - User dashboard sidebar
- [ ] `job_card.html` - Job listing card
- [ ] `notification_item.html` - Notification item
- [ ] `pagination.html` - Pagination controls

#### Pages (`pages/`)

**Homepage**
- [ ] `index.html` - Landing page with featured jobs

**Auth Pages** (`pages/auth/`)
- [ ] `login.html` - Login form
- [ ] `register.html` - Registration form
- [ ] `forgot_password.html` - Password reset

**Job Pages** (`pages/jobs/`)
- [ ] `list.html` - Job listings with filters
- [ ] `detail.html` - Job detail page
- [ ] `search.html` - Job search page

**Profile Pages** (`pages/profile/`)
- [ ] `dashboard.html` - User dashboard
- [ ] `settings.html` - Profile settings
- [ ] `applications.html` - My applications
- [ ] `notifications.html` - Notifications

**Admin Pages** (`pages/admin/`)
- [ ] `dashboard.html` - Admin dashboard
- [ ] `jobs_manage.html` - Manage jobs
- [ ] `users_manage.html` - Manage users
- [ ] `analytics.html` - Analytics

### 3. Static Assets (`frontend/static/`)

#### CSS (`css/`)
- [ ] `main.css` - Main stylesheet
- [ ] `auth.css` - Auth pages styles
- [ ] `jobs.css` - Job pages styles
- [ ] `admin.css` - Admin styles

#### JavaScript (`js/`)
- [ ] `main.js` - Main JavaScript
- [ ] `jobs.js` - Job interactions
- [ ] `notifications.js` - Notification handling
- [ ] `admin.js` - Admin functionality

### 4. API Client (`frontend/app/utils/`)
- [ ] `api_client.py` - HTTP client for backend API
  ```python
  # Methods:
  # - login(email, password)
  # - register(user_data)
  # - get_jobs(filters)
  # - get_job(job_id)
  # - get_profile()
  # - update_profile(data)
  # - get_notifications()
  ```

## 🎯 Priority 2b: Advanced Strategies

### Error Code Implementation
- [ ] Define error code taxonomy (AUTH_*, VALIDATION_*, FORBIDDEN_*, etc.)
- [ ] Implement standardized error response format in middleware
- [ ] Each error includes: code, message, details, timestamp, request_id
- [ ] Frontend displays user-friendly messages based on error codes

### Request ID & Correlation Tracing
- [ ] Generate unique request_id for every API request
- [ ] Pass request_id through all services (Frontend → Backend → Database)
- [ ] Log request_id with every log entry (ELK Elasticsearch)
- [ ] Allow searching logs by request_id to trace full request flow
- [ ] Add X-Request-ID header to all responses

### Redis Caching Strategy
- [ ] Cache user sessions (15 min TTL)
- [ ] Cache job listings (1 hour TTL)
- [ ] Cache user preferences (24 hour TTL)
- [ ] Cache rate limit counters (1 min TTL)
- [ ] Implement cache-aside pattern (check cache first, load if missing)
- [ ] Invalidate cache when data changes (job updates, user profile updates)

### Celery Task Routing by Priority
- [ ] HIGH priority queue: Email notifications (immediate)
- [ ] MEDIUM priority queue: Job matching, digest generation (5 min acceptable)
- [ ] LOW priority queue: Analytics aggregation, cleanup (1+ hour acceptable)
- [ ] Task retry strategy with exponential backoff
- [ ] Track task status and failed tasks

### API Response Time SLAs
- [ ] Auth endpoints: < 100ms target
- [ ] Read endpoints: < 200ms target
- [ ] Write endpoints: < 300ms target
- [ ] Search endpoints: < 500ms target (Elasticsearch)
- [ ] Admin endpoints: < 1000ms target
- [ ] Set up monitoring alerts for SLA violations
- [ ] Dashboard shows p50, p95, p99 latencies

## 🎯 Priority 3: API & Communication Standards

### API Response Formatting
- [ ] **Pagination**:
  - Limit/Offset for small datasets (notifications, applications)
  - Cursor-based for large datasets (job listings > 10K records)
  - Always include `has_more` flag for frontend

- [ ] **Error Responses** (Standardized format):
  ```javascript
  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Email is invalid",
      "details": [{ "field": "email", "issue": "..." }],
      "timestamp": "2026-03-03T10:30:00Z",
      "request_id": "req_123abc"
    }
  }
  ```

- [ ] **Timeout & Retry Logic**:
  - Frontend implements exponential backoff (2s, 4s, 8s)
  - Max 3 retries for transient failures
  - 10-second timeout per request

- [ ] **Notification Retry Strategy**:
  - Celery auto-retry failed emails (5 attempts)
  - Exponential backoff (1s, 2s, 4s, 8s, 16s)
  - Max wait: 10 minutes between retries

## 🎯 Priority 3a: Utilities & Middleware

### Backend Utilities (`backend/app/utils/`)
- [ ] `validators.py` - Input validation helpers
- [ ] `decorators.py` - Custom decorators (auth_required, admin_required)
- [ ] `helpers.py` - Common helper functions, pagination helper
- [ ] `constants.py` - Application constants, error codes
- [ ] `response_formatter.py` - Standardize API responses (success/error)

### Backend Middleware (`backend/app/middleware/`)
- [ ] `auth_middleware.py` - JWT verification
- [ ] `error_handler.py` - Global error handling (returns standardized error format)
- [ ] `rate_limiter.py` - API rate limiting
- [ ] `request_logger.py` - Log all requests with request_id (for tracing)

### Backend Validators (`backend/app/validators/`)
- [ ] `user_validator.py` - User input validation
- [ ] `job_validator.py` - Job data validation (title, desc, etc.)
- [ ] `auth_validator.py` - Auth request validation (email format, password strength)

### Frontend Middleware (`frontend/app/middleware/`)
- [ ] `auth_middleware.py` - Login required decorator
- [ ] `error_handler.py` - Catch API errors, show user-friendly messages
- [ ] `api_retry_handler.py` - Auto-retry on transient failures

## 🎯 Priority 4: Monitoring & Performance

### Logging (ELK Stack Setup)
- [ ] Elasticsearch container for centralized logs
- [ ] Kibana for log visualization & searching
- [ ] Logstash for parsing & forwarding logs
- [ ] JSON logging from all services (request_id, timestamp, level, message)
- [ ] Ability to search: `service:backend AND level:ERROR AND request_id:req_123`

### Full-Text Search (Elasticsearch for Jobs)
- [ ] Index job_vacancies collection in Elasticsearch
- [ ] Fuzzy matching (typo tolerance): "Consttable" → "Constable"
- [ ] Relevance scoring: Weight job_title > organization > description
- [ ] Job search endpoint uses ES instead of MongoDB text index
- [ ] Auto-update ES index when new jobs added

### Application Performance Monitoring (APM)
- [ ] Track API endpoint response times (goal: < 200ms for job search)
- [ ] Monitor database query latency (goal: < 50ms)
- [ ] Monitor Celery task execution time (email: < 5s)
- [ ] Slow query logging (> 1s queries logged for optimization)
- [ ] Memory/CPU usage per container

### Real-Time Alerts
- [ ] Error rate > 1% ← Alert
- [ ] Response time > 500ms ← Alert
- [ ] Celery task failure > 5% ← Alert
- [ ] Memory usage > 80% ← Alert
- [ ] Disk space < 10% ← Alert

## 🎯 Priority 5: Testing

### Backend Tests (`backend/tests/`)

#### Unit Tests (`unit/`)
- [ ] `test_models.py` - Test database models
- [ ] `test_services.py` - Test business logic
- [ ] `test_validators.py` - Test validators
- [ ] `test_pagination.py` - Test pagination logic

#### Integration Tests (`integration/`)
- [ ] `test_api_auth.py` - Test auth endpoints (JWT, refresh)
- [ ] `test_api_jobs.py` - Test job endpoints (pagination, search, indexing)
- [ ] `test_notifications.py` - Test notification retry logic
- [ ] `test_error_responses.py` - Verify standardized error format

### Frontend Tests (`frontend/tests/`)
- [ ] `test_routes.py` - Test page routes
- [ ] `test_templates.py` - Test template rendering
- [ ] `test_api_retry.py` - Test retry logic with mock failures

## 🎯 Priority 6: Deployment Scripts

### Scripts (`scripts/`)

#### Deployment (`deployment/`)
- [ ] `deploy.sh` - Deployment script
- [ ] `rollback.sh` - Rollback script
- [ ] `health_check.sh` - Health check

#### Backup (`backup/`)
- [ ] `backup_db.sh` - Database backup
- [ ] `restore_db.sh` - Database restore

#### Migration (`migration/`)
- [ ] `init_db.js` - Initialize MongoDB collections
- [ ] `seed_data.py` - Seed sample data

## 🎯 Priority 7: Environment Configs

### Configuration Files (`config/`)
- [ ] `production/.env.production` - Production environment
- [ ] `staging/.env.staging` - Staging environment
- [ ] `development/.env.development` - Development environment

## 📝 Implementation Order Suggestion

1. **Week 1: Core Backend**
   - Database models
   - Basic auth routes
   - User service
   - Database configuration

2. **Week 2: Job Management**
   - Job model
   - Job routes (CRUD)
   - Job service with matching algorithm
   - Admin routes

3. **Week 3: Frontend Basics**
   - Base layouts
   - Homepage
   - Auth pages (login, register)
   - API client

4. **Week 4: Job UI**
   - Job listing page
   - Job detail page
   - Job search and filters
   - Job card component

5. **Week 5: User Dashboard**
   - Profile pages
   - Settings page
   - Applications tracking
   - Notifications UI

6. **Week 6: Notifications**
   - Notification service
   - Email service
   - Celery tasks
   - Reminder system

7. **Week 7: Admin Panel**
   - Admin dashboard
   - User management
   - Job management
   - Analytics

8. **Week 8: Testing & Polish**
   - Unit tests
   - Integration tests
   - Bug fixes
   - Performance optimization

9. **Week 9: Deployment**
   - Docker testing
   - Deployment scripts
   - Production environment setup
   - SSL configuration

10. **Week 10: Launch**
    - Final testing
    - Documentation
    - User guide
    - Go live!

## 🎨 Starter Code Templates

Each file should follow this pattern:

### Model Template (`backend/app/models/user.py`)
```python
from datetime import datetime

class User:
    def __init__(self, db):
        self.collection = db.users
    
    def create(self, user_data):
        # Implementation
        pass
    
    def find_by_email(self, email):
        # Implementation
        pass
```

### Route Template (`backend/app/routes/auth.py`)
```python
from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    # Implementation
    pass
```

### Service Template (`backend/app/services/auth_service.py`)
```python
class AuthService:
    def __init__(self, user_model):
        self.user_model = user_model
    
    def register_user(self, user_data):
        # Implementation
        pass
```

## ✅ Checklist

Use this checklist to track your progress:

- [ ] Set up MongoDB connection
- [ ] Create User model
- [ ] Implement authentication
- [ ] Create Job model
- [ ] Implement job CRUD
- [ ] Set up email service
- [ ] Configure Celery
- [ ] Create frontend layouts
- [ ] Implement homepage
- [ ] Create auth pages
- [ ] Create job pages
- [ ] Create profile pages
- [ ] Implement admin panel
- [ ] Write tests
- [ ] Deploy to production

---

**Focus on completing Priority 1 first before moving to Priority 2!**

Good luck! 🚀
