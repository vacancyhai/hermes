# Sarkari Path - Government Job Vacancy Portal

> **🚀 Quick Start**: New to this project? Read [docs/PROJECT_SUMMARY.md](./docs/PROJECT_SUMMARY.md) for a 10-minute deployment guide.

> **📂 Project Structure**: See [docs/PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md) for complete folder structure and architecture.

> **📚 Documentation Index**: Browse [docs/INDEX.md](./docs/INDEX.md) for all available documentation.

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [System Architecture](#system-architecture)
4. [Database Schema](#database-schema-mongodb-collections)
5. [API Endpoints](#api-endpoints)
6. [Key Features](#key-features-implementation)
7. [Deployment Options](#deployment-options)
8. [Project Structure](#project-structure-microservices)
9. [Environment Setup](#environment-variables-env)
10. [Development Workflow](#development-workflow)
11. [Deployment Guides](#hostinger-vps-deployment-guide)
12. [Troubleshooting](#troubleshooting-hostinger-vps)

📖 **Additional Documentation**:
- [Docker Deployment Guide](./docs/DOCKER_DEPLOYMENT.md)
- [Jinja2 Templates Guide](./docs/JINJA2_TEMPLATES_GUIDE.md)
- [Workflow Diagrams](./docs/WORKFLOW_DIAGRAMS.md)

## Project Overview

A comprehensive web application that provides users with personalized government job vacancy notifications based on their educational qualifications, preferences, and job priorities. The system includes user authentication, profile management, intelligent notification filtering, and an admin panel for job management.

### Key Capabilities
- 🎯 **Intelligent Job Matching**: Automatically matches jobs based on user's education (10th, 12th, Graduation), stream (Science/Commerce/Arts), age, and category (General/OBC/SC/ST)
- 📧 **Multi-Channel Notifications**: Email (Flask-Mail), Push (Firebase FCM), and In-app notifications
- ⏰ **Smart Reminders**: Automatic deadline reminders at 7 days, 3 days, and 1 day before application closes
- 📊 **Admin Dashboard**: Complete job management with analytics and user tracking
- 🔐 **Secure Authentication**: JWT-based API authentication with session management
- 🐳 **Containerized Deployment**: Docker microservices architecture for easy scaling

## Tech Stack

### Backend (Flask API)
- **Framework**: Python Flask 3.0.0
- **Database**: MongoDB 7.0 (NoSQL)
- **Authentication**: Flask-JWT-Extended
- **Task Queue**: Celery 5.3.4 with Redis broker
- **Email Service**: Flask-Mail (SMTP)
- **Push Notifications**: Firebase Cloud Messaging (FCM)
- **Production Server**: Gunicorn 21.2.0

### Frontend (Flask + Jinja2)
- **Framework**: Python Flask 3.0.0
- **Template Engine**: Jinja2
- **Session Management**: Flask-Login
- **Static Assets**: HTML5, CSS3, JavaScript
- **API Client**: Python Requests library
- **Production Server**: Gunicorn 21.2.0

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx (load balancing, SSL, static files)
- **Cache & Broker**: Redis 7.0
- **Deployment**: Hostinger VPS (Ubuntu 22.04 LTS)

## System Architecture

### Microservices Architecture (Containerized)

```
┌────────────────────────────────────────────────────────────┐
│                    User's Browser                          │
└────────────────┬───────────────────────────────────────────┘
                 │ HTTPS (Port 443)
                 ↓
┌────────────────────────────────────────────────────────────┐
│           Nginx Reverse Proxy Container                    │
│         - SSL Termination (Let's Encrypt)                  │
│         - Load Balancing                                   │
│         - Static File Serving                              │
│         - Rate Limiting                                    │
└──────┬──────────────────────────────────┬──────────────────┘
       │                                  │
       │ /api/* → backend:5000           │ /* → frontend:8080
       ↓                                  ↓
┌─────────────────────┐          ┌─────────────────────────┐
│ Backend Container   │          │  Frontend Container     │
│ (Flask REST API)    │          │  (Flask + Jinja2)       │
│                     │          │                         │
│ - Business Logic    │          │ - UI Rendering          │
│ - Data Validation   │◄─────────│ - Template Engine       │
│ - Authentication    │  Calls   │ - User Sessions         │
│ - Job Matching      │  API     │ - Static Assets         │
│ - Notifications     │          │ - API Client            │
│                     │          │                         │
│ Port: 5000          │          │ Port: 8080              │
└──────┬──────────────┘          └─────────────────────────┘
       │
       ├────────────────┬────────────────┬───────────────┐
       │                │                │               │
       ↓                ↓                ↓               ↓
┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐
│  MongoDB    │  │   Redis     │  │ Celery   │  │ Celery   │
│  Container  │  │  Container  │  │ Worker   │  │  Beat    │
│             │  │             │  │Container │  │Container │
│ - Jobs DB   │  │ - Cache     │  │          │  │          │
│ - Users DB  │  │ - Sessions  │  │ - Emails │  │- Schedule│
│ - Logs      │  │ - Queue     │  │ - Push   │  │- Cron    │
│             │  │             │  │ - Match  │  │          │
│Port: 27017  │  │Port: 6379   │  │          │  │          │
└─────────────┘  └─────────────┘  └──────────┘  └──────────┘

         All containers connected via Docker bridge network
```

### Core Components

1. **User Management Module** (Backend + Frontend)
2. **Job Vacancy Module** (Backend + Frontend)
3. **Notification Engine** (Backend + Celery)
4. **Admin Panel** (Backend + Frontend)
5. **Profile Matching System** (Backend + Celery)
6. **Application Tracking System** (Backend + Frontend)

## Database Schema (MongoDB Collections)

### 1. Users Collection
```json
{
  "_id": "ObjectId",
  "email": "user@example.com",
  "password": "hashed_password",
  "full_name": "John Doe",
  "phone": "+91-9876543210",
  "created_at": "2025-12-07T10:00:00Z",
  "last_login": "2025-12-07T10:00:00Z",
  "is_verified": true,
  "role": "user" // or "admin"
}
```

### 2. User Profiles Collection
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId (ref: Users)",
  "personal_info": {
    "date_of_birth": "1995-01-15",
    "gender": "Male/Female/Other",
    "category": "General/OBC/SC/ST/EWS",
    "pwd": false,
    "state": "Delhi",
    "city": "New Delhi"
  },
  "education": {
    "highest_qualification": "12th/Graduation/Post-Graduation/PhD",
    "12th": {
      "completed": true,
      "stream": "Science/Commerce/Arts",
      "percentage": 85.5,
      "year": 2013
    },
    "graduation": {
      "completed": true,
      "degree": "B.Tech",
      "specialization": "Computer Science",
      "percentage": 75.0,
      "year": 2017
    },
    "post_graduation": {
      "completed": false
    }
  },
  "notification_preferences": {
    "organizations": ["Railway", "SSC", "UPSC", "Banking"],
    "job_types": ["Technical", "Non-Technical", "Teaching"],
    "locations": ["Delhi", "Mumbai", "Bangalore"],
    "email_enabled": true,
    "sms_enabled": false,
    "push_enabled": true,
    "frequency": "instant" // instant/daily/weekly
  },
  "updated_at": "2025-12-07T10:00:00Z"
}
```

### 3. Job Vacancies Collection
```json
{
  "_id": "ObjectId",
  "job_title": "Assistant Loco Pilot",
  "organization": "Indian Railways",
  "department": "Railway Recruitment Board (RRB)",
  "post_code": "RRB-ALP-2025",
  "total_vacancies": 5000,
  "description": "Full job description...",
  "eligibility": {
    "min_qualification": "12th",
    "required_stream": ["Science"], // null for any stream
    "age_limit": {
      "min": 18,
      "max": 30,
      "relaxation": {
        "OBC": 3,
        "SC/ST": 5,
        "PWD": 10
      }
    },
    "category_wise_vacancies": {
      "General": 2000,
      "OBC": 1500,
      "SC": 1000,
      "ST": 500
    }
  },
  "application_details": {
    "application_fee": {
      "General": 500,
      "SC/ST": 0,
      "PWD": 0
    },
    "application_mode": "Online",
    "official_website": "https://rrbcdg.gov.in"
  },
  "important_dates": {
    "notification_date": "2025-12-01",
    "application_start": "2025-12-10",
    "application_end": "2025-12-31",
    "exam_date": "2026-02-15",
    "admit_card_date": "2026-02-01",
    "result_date": "2026-03-15"
  },
  "documents_required": [
    "10th Certificate",
    "12th Certificate",
    "Aadhar Card",
    "Photograph",
    "Signature"
  ],
  "selection_process": [
    "Computer Based Test (CBT)",
    "Physical Efficiency Test (PET)",
    "Document Verification",
    "Medical Examination"
  ],
  "status": "active", // active/closed/cancelled
  "created_by": "ObjectId (ref: Users - admin)",
  "created_at": "2025-12-01T10:00:00Z",
  "updated_at": "2025-12-07T10:00:00Z",
  "views": 15000,
  "applications_count": 2500
}
```

### 4. User Job Applications Collection
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId (ref: Users)",
  "job_id": "ObjectId (ref: Job Vacancies)",
  "application_number": "RRB2025123456",
  "is_priority": true,
  "applied_on": "2025-12-15T10:00:00Z",
  "status": "applied", // applied/admit-card-released/exam-completed/result-pending/selected/rejected
  "notes": "User's personal notes about this application",
  "reminders": [
    {
      "type": "application_deadline",
      "date": "2025-12-31",
      "notified": false
    },
    {
      "type": "admit_card",
      "date": "2026-02-01",
      "notified": false
    },
    {
      "type": "exam_date",
      "date": "2026-02-15",
      "notified": false
    }
  ]
}
```

### 5. Notifications Collection
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId (ref: Users)",
  "job_id": "ObjectId (ref: Job Vacancies)",
  "type": "new_vacancy/application_reminder/admit_card/exam_date/result",
  "title": "New Railway Vacancy Alert!",
  "message": "RRB has released 5000 ALP vacancies...",
  "is_read": false,
  "sent_via": ["email", "push", "in-app"],
  "created_at": "2025-12-07T10:00:00Z",
  "priority": "high" // low/medium/high
}
```

### 6. Admin Logs Collection
```json
{
  "_id": "ObjectId",
  "admin_id": "ObjectId (ref: Users)",
  "action": "create_job/update_job/delete_job/approve_user",
  "resource_type": "job_vacancy",
  "resource_id": "ObjectId",
  "details": "Created new job vacancy for RRB ALP",
  "timestamp": "2025-12-07T10:00:00Z",
  "ip_address": "192.168.1.1"
}
```

## API Endpoints

### Authentication APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/auth/register` | User registration | Public |
| POST | `/api/auth/login` | User login | Public |
| POST | `/api/auth/logout` | User logout | Authenticated |
| POST | `/api/auth/forgot-password` | Password reset request | Public |
| POST | `/api/auth/reset-password` | Reset password | Public |
| GET | `/api/auth/verify-email/:token` | Email verification | Public |

### User Profile APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/profile` | Get user profile | User |
| PUT | `/api/profile` | Update user profile | User |
| POST | `/api/profile/education` | Add education details | User |
| PUT | `/api/profile/education/:id` | Update education | User |
| GET | `/api/profile/preferences` | Get notification preferences | User |
| PUT | `/api/profile/preferences` | Update preferences | User |

### Job Vacancy APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/jobs` | Get all jobs (with filters) | Public |
| GET | `/api/jobs/:id` | Get job details | Public |
| GET | `/api/jobs/recommended` | Get personalized jobs | User |
| POST | `/api/jobs/search` | Advanced job search | Public |
| GET | `/api/jobs/organization/:org` | Jobs by organization | Public |

### Application APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/applications` | Mark job as applied | User |
| GET | `/api/applications` | Get user's applications | User |
| GET | `/api/applications/:id` | Get application details | User |
| PUT | `/api/applications/:id/priority` | Toggle priority | User |
| PUT | `/api/applications/:id/notes` | Update notes | User |
| DELETE | `/api/applications/:id` | Remove application | User |

### Notification APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/notifications` | Get user notifications | User |
| PUT | `/api/notifications/:id/read` | Mark as read | User |
| PUT | `/api/notifications/read-all` | Mark all as read | User |
| DELETE | `/api/notifications/:id` | Delete notification | User |

### Admin APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/admin/jobs` | Create new job | Admin |
| PUT | `/api/admin/jobs/:id` | Update job | Admin |
| DELETE | `/api/admin/jobs/:id` | Delete job | Admin |
| GET | `/api/admin/users` | Get all users | Admin |
| PUT | `/api/admin/users/:id/status` | Update user status | Admin |
| GET | `/api/admin/analytics` | Get platform analytics | Admin |
| GET | `/api/admin/logs` | Get admin activity logs | Admin |

## Key Features Implementation

### 1. Intelligent Job Matching Algorithm

```python
def match_job_with_user(job, user_profile):
    """
    Matches a job vacancy with user profile based on eligibility criteria
    Returns: (is_eligible, match_score)
    """
    score = 0
    
    # Education matching
    if check_education_eligibility(job.eligibility, user_profile.education):
        score += 40
    else:
        return (False, 0)
    
    # Age verification
    if check_age_eligibility(job.eligibility.age_limit, user_profile.personal_info):
        score += 20
    else:
        return (False, 0)
    
    # Category preference
    if user_profile.personal_info.category in job.eligibility.category_wise_vacancies:
        score += 10
    
    # Organization preference
    if job.organization in user_profile.notification_preferences.organizations:
        score += 20
    
    # Location preference
    if job.location in user_profile.notification_preferences.locations:
        score += 10
    
    return (True, score)
```

### 2. Notification Trigger System

**Triggers for Notifications:**

1. **New Job Posted**: When a new job matching user's profile is created
2. **Application Deadline**: 7 days, 3 days, 1 day before deadline
3. **Admit Card Release**: When admit card dates are announced
4. **Exam Date Reminder**: 7 days, 3 days, 1 day before exam
5. **Result Announcement**: When results are declared
6. **Priority Job Updates**: Any update on jobs marked as priority

### 3. Background Job Scheduler (Celery Tasks)

```python
# Daily job matching task
@celery.task
def daily_job_matching():
    """Run daily to match new jobs with users"""
    new_jobs = get_jobs_created_in_last_24_hours()
    users = get_all_active_users()
    
    for job in new_jobs:
        for user in users:
            if match_job_with_user(job, user.profile)[0]:
                send_job_notification(user, job)

# Reminder tasks
@celery.task
def send_deadline_reminders():
    """Check and send reminders for upcoming deadlines"""
    applications = get_applications_with_pending_reminders()
    
    for app in applications:
        check_and_send_reminders(app)
```

### 4. Flask-Mail Email Service

```python
from flask_mail import Mail, Message

mail = Mail(app)

def send_job_notification_email(user, job):
    """Send job notification via Flask-Mail"""
    msg = Message(
        subject=f"New Job Alert: {job.job_title}",
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )
    
    msg.html = render_template(
        'emails/job_notification.html',
        user=user,
        job=job
    )
    
    mail.send(msg)

def send_reminder_email(user, application, reminder_type):
    """Send application reminder via Flask-Mail"""
    msg = Message(
        subject=f"Reminder: {reminder_type} for {application.job.job_title}",
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )
    
    msg.html = render_template(
        'emails/reminder.html',
        user=user,
        application=application,
        reminder_type=reminder_type
    )
    
    mail.send(msg)
```

## Admin Panel Features

### Dashboard
- Total users, active jobs, total applications
- Recent activity feed
- Analytics graphs (daily registrations, applications)
- Popular jobs
- User engagement metrics

### Job Management
- Create/Edit/Delete job vacancies
- Bulk upload jobs via CSV/Excel
- Job status management (active/closed/cancelled)
- Clone existing job posting
- Schedule job posting for future date

### User Management
- View all users
- User details and activity
- Ban/Unban users
- Export user data
- View user applications

### Analytics
- User demographics
- Popular organizations
- Application trends
- Notification delivery stats
- Platform usage metrics

### Content Management
- Manage static pages (About, Contact, FAQ)
- Manage email templates
- Notification templates
- Banner/Advertisement management

## Security Features

1. **Password Security**: bcrypt hashing
2. **JWT Authentication**: Secure token-based authentication
3. **Rate Limiting**: Prevent API abuse
4. **CORS Configuration**: Proper origin control
5. **Input Validation**: Sanitize all user inputs
6. **SQL Injection Prevention**: Use parameterized queries (MongoDB)
7. **XSS Protection**: Escape output data
8. **CSRF Protection**: Flask-WTF CSRF tokens
9. **Admin Access Control**: Role-based permissions

## Deployment Options

### ⭐ Option 1: Docker Microservices (Recommended)

**Containerized Architecture:**
- 🐳 **6 Containers**: Nginx, Frontend, Backend, MongoDB, Redis, Celery
- ✅ **10-minute setup** vs 2-hour manual installation  
- ✅ **Independent scaling** - Scale frontend/backend separately
- ✅ **Zero-downtime updates** - Update services without full restart
- ✅ **Built-in health checks** and auto-restart
- ✅ **Service isolation** - Each component in separate container

**Quick Start:**
```bash
git clone https://github.com/SumanKr7/sarkari_path_2.0.git
cd sarkari_path_2.0

# Configure environment
cp .env.example .env
nano .env  # Add your MongoDB, Redis, Email credentials

# Deploy all services
docker compose up -d --build

# View logs
docker compose logs -f frontend backend

# Check status
docker compose ps
```

**Container Communication:**
- Frontend calls Backend via internal Docker network: `http://backend:5000/api`
- All external traffic goes through Nginx reverse proxy
- Containers restart automatically if they crash

📘 **Complete Docker Guide**: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)

### Option 2: Traditional Monolithic Deployment

Single Flask application with Supervisor on Hostinger VPS.  
See "Hostinger VPS Deployment Guide" below for full instructions.

**Note**: For production, Docker microservices architecture is recommended for better scalability and maintenance.

---

## Deployment Architecture

### Docker Microservices Architecture (Recommended)

```
┌───────────────────────────────────────────────────────────────┐
│                  Hostinger VPS + Docker                       │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Nginx Container (Port 80/443)                 │ │
│  │      - SSL/TLS Termination (Let's Encrypt)              │ │
│  │      - Reverse Proxy & Load Balancing                   │ │
│  │      - Static File Caching (30 days)                    │ │
│  │      - Rate Limiting & Security Headers                 │ │
│  └──────────────────┬───────────────────┬──────────────────┘ │
│                     │                   │                     │
│       /api/*        │                   │        /*           │
│         ↓           │                   │         ↓           │
│  ┌──────────────────┴─┐             ┌───┴──────────────────┐ │
│  │  Backend Container │             │ Frontend Container   │ │
│  │  (Flask REST API)  │             │ (Flask + Jinja2)     │ │
│  │                    │             │                      │ │
│  │  - Gunicorn (3w)   │◄────API─────│  - Gunicorn (2w)     │ │
│  │  - Port 5000       │   Calls     │  - Port 8080         │ │
│  │  - JWT Auth        │             │  - Sessions          │ │
│  │  - Business Logic  │             │  - UI Templates      │ │
│  └─────────┬──────────┘             └──────────────────────┘ │
│            │                                                  │
│  ┌─────────┼──────────────────────────────────────────────┐ │
│  │         │                                               │ │
│  │    ┌────▼─────┐  ┌──────────┐  ┌──────────┐  ┌──────┐│ │
│  │    │ MongoDB  │  │  Redis   │  │  Celery  │  │Celery││ │
│  │    │Container │  │Container │  │  Worker  │  │ Beat ││ │
│  │    │          │  │          │  │Container │  │ Cont ││ │
│  │    │- Port    │  │- Port    │  │          │  │      ││ │
│  │    │  27017   │  │  6379    │  │- Emails  │  │-Cron ││ │
│  │    │- Auth    │  │- Cache   │  │- Notify  │  │Tasks ││ │
│  │    │- Persist │  │- Queue   │  │- Match   │  │      ││ │
│  │    └──────────┘  └──────────┘  └──────────┘  └──────┘│ │
│  │                                                       │ │
│  │        Docker Bridge Network (sarkari_network)       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Volumes: mongodb_data, redis_data, backend_logs          │
└─────────────────────────────────────────────────────────────┘

        Internet ↕️ HTTPS (Port 443)
```

### Traditional VPS Deployment

```
┌─────────────────────────────────────────────────────────┐
│              Hostinger VPS Server                       │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Nginx (Reverse Proxy + SSL)                      │ │
│  │  - Port 80/443                                    │ │
│  │  - SSL Certificate (Let's Encrypt)               │ │
│  └─────────────────┬─────────────────────────────────┘ │
│                    │                                    │
│       ┌────────────┼────────────┐                      │
│       │            │            │                      │
│  ┌────▼────┐  ┌────▼────┐  ┌───▼─────┐               │
│  │ Gunicorn│  │ Gunicorn│  │ Gunicorn│               │
│  │ Worker 1│  │ Worker 2│  │ Worker 3│               │
│  │ (Flask) │  │ (Flask) │  │ (Flask) │               │
│  └────┬────┘  └────┬────┘  └───┬─────┘               │
│       │            │            │                      │
│       └────────────┼────────────┘                      │
│                    │                                    │
│  ┌─────────────────┼─────────────────────────────┐    │
│  │                 │                             │    │
│  │  ┌──────────────▼──────────┐  ┌─────────────┐│    │
│  │  │     MongoDB             │  │   Redis     ││    │
│  │  │  - Port 27017           │  │ - Port 6379 ││    │
│  │  │  - Local/Atlas          │  │ - Cache     ││    │
│  │  └─────────────────────────┘  │ - Sessions  ││    │
│  │                                │ - Celery    ││    │
│  │                                └─────────────┘│    │
│  │                                                │    │
│  │  ┌─────────────────────────────────────────┐ │    │
│  │  │     Celery Workers (Background)         │ │    │
│  │  │  - Job Matching                         │ │    │
│  │  │  - Email Notifications                  │ │    │
│  │  │  - Reminders                            │ │    │
│  │  └─────────────────────────────────────────┘ │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

        Internet ↕️ HTTPS (Port 443)
```

## Project Structure (Microservices)

```
sarkari-path/
├── backend/                           # Backend API Container
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   └── notification.py
│   │   ├── routes/                    # REST API Endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # /api/auth/*
│   │   │   ├── profile.py            # /api/profile/*
│   │   │   ├── jobs.py               # /api/jobs/*
│   │   │   ├── applications.py       # /api/applications/*
│   │   │   ├── notifications.py      # /api/notifications/*
│   │   │   └── admin.py              # /api/admin/*
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── matching_engine.py
│   │   │   ├── notification_service.py
│   │   │   ├── email_service.py
│   │   │   └── analytics_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── decorators.py
│   │       ├── validators.py
│   │       └── helpers.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── job_matching.py
│   │   └── reminders.py
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_jobs.py
│   │   └── test_matching.py
│   ├── config.py
│   ├── run.py
│   ├── celery_worker.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                          # Frontend UI Container
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes/                    # Page Routes
│   │   │   ├── __init__.py
│   │   │   ├── main.py               # Homepage, about, contact
│   │   │   ├── auth.py               # Login/register pages
│   │   │   ├── jobs.py               # Job listing/details pages
│   │   │   ├── profile.py            # User profile pages
│   │   │   ├── applications.py       # My applications pages
│   │   │   └── admin.py              # Admin dashboard pages
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── admin/
│   │   │   │   ├── dashboard.html
│   │   │   │   ├── job_form.html
│   │   │   │   ├── job_list.html
│   │   │   │   ├── user_list.html
│   │   │   │   └── analytics.html
│   │   │   ├── auth/
│   │   │   │   ├── login.html
│   │   │   │   ├── register.html
│   │   │   │   ├── forgot_password.html
│   │   │   │   └── verify_email.html
│   │   │   ├── jobs/
│   │   │   │   ├── job_list.html
│   │   │   │   ├── job_detail.html
│   │   │   │   └── recommended.html
│   │   │   ├── profile/
│   │   │   │   ├── profile.html
│   │   │   │   ├── edit_profile.html
│   │   │   │   └── preferences.html
│   │   │   ├── applications/
│   │   │   │   ├── my_applications.html
│   │   │   │   └── application_detail.html
│   │   │   ├── notifications/
│   │   │   │   └── notifications.html
│   │   │   └── components/
│   │   │       ├── navbar.html
│   │   │       ├── footer.html
│   │   │       ├── job_card.html
│   │   │       └── notification_item.html
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   ├── style.css
│   │   │   │   ├── admin.css
│   │   │   │   └── components.css
│   │   │   ├── js/
│   │   │   │   ├── main.js
│   │   │   │   ├── notifications.js
│   │   │   │   └── admin.js
│   │   │   ├── img/
│   │   │   │   ├── logo.png
│   │   │   │   └── default-avatar.png
│   │   │   └── fonts/
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── api_client.py         # Backend API client
│   ├── config.py
│   ├── run.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── nginx/                             # Nginx Reverse Proxy
│   ├── nginx.conf
│   └── ssl/
│       ├── cert.pem
│       └── key.pem
│
├── mongo-init.js                      # MongoDB initialization
├── docker-compose.yml                 # All services orchestration
├── .env                               # Environment variables
├── .env.example
├── .gitignore
├── README.md
├── DOCKER_DEPLOYMENT.md
├── WORKFLOW_DIAGRAMS.md
└── JINJA2_TEMPLATES_GUIDE.md
```

## Required Python Packages

```txt
# Flask Framework
Flask==3.0.0
Flask-PyMongo==2.3.0
Flask-Login==0.6.3
Flask-JWT-Extended==4.5.3
Flask-Mail==0.9.1
Flask-WTF==1.2.1
Flask-Cors==4.0.0

# Database & Caching
pymongo==4.6.0
redis==5.0.1

# Background Tasks
celery==5.3.4

# Security
bcrypt==4.1.2

# Utilities
python-dotenv==1.0.0
email-validator==2.1.0
Pillow==10.1.0

# Push Notifications
firebase-admin==6.3.0

# Production Server (Hostinger VPS)
gunicorn==21.2.0
gevent==23.9.1

# Monitoring & Logging
sentry-sdk[flask]==1.39.0
```

## Hostinger VPS Server Requirements

### Minimum Specifications
- **RAM**: 4GB (8GB recommended for production)
- **CPU**: 2 cores (4 cores recommended)
- **Storage**: 40GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Bandwidth**: Unmetered

### Recommended Hostinger Plan
- **VPS Plan**: VPS 2 or higher
- **Monthly Users**: Up to 10,000 active users
- **Concurrent Requests**: ~100-200

### Resource Usage Estimates
- **Flask App (3 Gunicorn workers)**: ~1.5GB RAM
- **MongoDB**: ~1GB RAM
- **Redis**: ~500MB RAM
- **Celery Workers**: ~500MB RAM
- **System & Nginx**: ~500MB RAM

## Environment Variables (.env)

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/sarkari_path

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Flask-Mail Email Configuration (SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@sarkaripath.com
MAIL_MAX_EMAILS=100
MAIL_ASCII_ATTACHMENTS=False

# Firebase Configuration (for push notifications)
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Admin Configuration
ADMIN_EMAIL=admin@sarkaripath.com
```

## Development Workflow

### Phase 1: Setup & Core (Week 1-2)
- Project setup and environment configuration
- Database schema design and MongoDB setup
- User authentication system
- Basic profile management

### Phase 2: Job Module (Week 3-4)
- Job vacancy CRUD operations
- Job listing and search
- Job details page
- Admin job management

### Phase 3: Matching Engine (Week 5-6)
- Profile-based job matching algorithm
- Eligibility checker
- Recommendation system
- Testing with sample data

### Phase 4: Application Tracking (Week 7-8)
- Application management
- Priority marking
- Notes and reminders
- Application dashboard

### Phase 5: Notification System (Week 9-10)
- Notification engine
- Email integration
- Push notification setup
- Celery task scheduler
- Notification preferences

### Phase 6: Admin Panel (Week 11-12)
- Admin dashboard
- Analytics and reports
- User management
- Content management

### Phase 7: Testing & Deployment (Week 13-14)
- Unit testing
- Integration testing
- Security audit
- Performance optimization
- Production deployment

## Testing Strategy

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test API endpoints
3. **Matching Algorithm Tests**: Verify job-user matching logic
4. **Notification Tests**: Verify notification triggers
5. **Load Testing**: Test with multiple concurrent users
6. **Security Testing**: Penetration testing

## Hostinger VPS Deployment Guide

### Prerequisites
- Hostinger VPS (minimum 4GB RAM, 2 CPU cores)
- Ubuntu 22.04 LTS
- Domain name pointed to VPS IP
- SSH access to server

### Step 1: Initial Server Setup

```bash
# Connect to VPS
ssh root@your-vps-ip

# Update system packages
sudo apt update && sudo apt upgrade -y

# Create application user
sudo adduser sarkaripath
sudo usermod -aG sudo sarkaripath

# Setup firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Step 2: Install Required Software

```bash
# Install Python 3.11 and dependencies
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Install Redis
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Install Nginx
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx

# Install Supervisor (for process management)
sudo apt install supervisor -y
```

### Step 3: Clone and Setup Application

```bash
# Switch to application user
su - sarkaripath

# Clone repository
cd /home/sarkaripath
git clone https://github.com/SumanKr7/sarkari_path_2.0.git
cd sarkari_path_2.0

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
nano .env
# Add your environment variables (see .env section)
```

### Step 4: Configure Gunicorn

```bash
# Create gunicorn configuration
nano /home/sarkaripath/sarkari_path_2.0/gunicorn_config.py
```

```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
accesslog = "/home/sarkaripath/sarkari_path_2.0/logs/gunicorn_access.log"
errorlog = "/home/sarkaripath/sarkari_path_2.0/logs/gunicorn_error.log"
loglevel = "info"
```

### Step 5: Configure Supervisor for Flask App

```bash
sudo nano /etc/supervisor/conf.d/sarkaripath.conf
```

```ini
[program:sarkaripath]
command=/home/sarkaripath/sarkari_path_2.0/venv/bin/gunicorn -c /home/sarkaripath/sarkari_path_2.0/gunicorn_config.py run:app
directory=/home/sarkaripath/sarkari_path_2.0
user=sarkaripath
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/sarkaripath/sarkari_path_2.0/logs/supervisor_error.log
stdout_logfile=/home/sarkaripath/sarkari_path_2.0/logs/supervisor_out.log
```

### Step 6: Configure Supervisor for Celery Workers

```bash
sudo nano /etc/supervisor/conf.d/celery_worker.conf
```

```ini
[program:celery_worker]
command=/home/sarkaripath/sarkari_path_2.0/venv/bin/celery -A celery_worker.celery worker --loglevel=info
directory=/home/sarkaripath/sarkari_path_2.0
user=sarkaripath
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/sarkaripath/sarkari_path_2.0/logs/celery_worker_error.log
stdout_logfile=/home/sarkaripath/sarkari_path_2.0/logs/celery_worker.log

[program:celery_beat]
command=/home/sarkaripath/sarkari_path_2.0/venv/bin/celery -A celery_worker.celery beat --loglevel=info
directory=/home/sarkaripath/sarkari_path_2.0
user=sarkaripath
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/sarkaripath/sarkari_path_2.0/logs/celery_beat_error.log
stdout_logfile=/home/sarkaripath/sarkari_path_2.0/logs/celery_beat.log
```

```bash
# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
sudo supervisorctl status
```

### Step 7: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/sarkaripath
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size limit
    client_max_body_size 10M;

    # Serve static files directly
    location /static {
        alias /home/sarkaripath/sarkari_path_2.0/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    # Access and error logs
    access_log /var/log/nginx/sarkaripath_access.log;
    error_log /var/log/nginx/sarkaripath_error.log;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/sarkaripath /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (certbot adds cron job automatically)
sudo certbot renew --dry-run
```

### Step 9: Setup MongoDB (Production Configuration)

```bash
# Secure MongoDB
sudo nano /etc/mongod.conf
```

```yaml
# MongoDB Configuration
net:
  port: 27017
  bindIp: 127.0.0.1

security:
  authorization: enabled

storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
```

```bash
# Create MongoDB admin user
mongosh

use admin
db.createUser({
  user: "admin",
  pwd: "your_strong_password",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
})

use sarkari_path
db.createUser({
  user: "sarkaripath_user",
  pwd: "your_db_password",
  roles: [ { role: "readWrite", db: "sarkari_path" } ]
})

exit

# Restart MongoDB
sudo systemctl restart mongod
```

### Step 10: Environment Variables for Production

```bash
nano /home/sarkaripath/sarkari_path_2.0/.env
```

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-production-secret-key-min-32-chars

# MongoDB Configuration
MONGO_URI=mongodb://sarkaripath_user:your_db_password@localhost:27017/sarkari_path?authSource=sarkari_path

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Flask-Mail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=/home/sarkaripath/sarkari_path_2.0/firebase-credentials.json

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-different-from-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Admin Configuration
ADMIN_EMAIL=admin@yourdomain.com

# Application URL
APP_URL=https://yourdomain.com
```

### Step 11: Setup Automated Backups

```bash
# Create backup script
nano /home/sarkaripath/backup_mongodb.sh
```

```bash
#!/bin/bash
# MongoDB Backup Script

BACKUP_DIR="/home/sarkaripath/backups/mongodb"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="sarkaripath_backup_$DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump MongoDB
mongodump --uri="mongodb://sarkaripath_user:your_db_password@localhost:27017/sarkari_path?authSource=sarkari_path" --out="$BACKUP_DIR/$BACKUP_NAME"

# Compress backup
cd $BACKUP_DIR
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Delete backups older than 7 days
find $BACKUP_DIR -name "*.tar.gz" -type f -mtime +7 -delete

echo "Backup completed: $BACKUP_NAME.tar.gz"
```

```bash
# Make script executable
chmod +x /home/sarkaripath/backup_mongodb.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add this line:
0 2 * * * /home/sarkaripath/backup_mongodb.sh >> /home/sarkaripath/logs/backup.log 2>&1
```

### Step 12: Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/sarkaripath
```

```
/home/sarkaripath/sarkari_path_2.0/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 sarkaripath sarkaripath
    sharedscripts
    postrotate
        supervisorctl restart sarkaripath celery_worker celery_beat
    endscript
}
```

### Deployment Commands

```bash
# Update application
cd /home/sarkaripath/sarkari_path_2.0
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart all

# View logs
sudo tail -f /home/sarkaripath/sarkari_path_2.0/logs/gunicorn_error.log
sudo supervisorctl tail -f sarkaripath stderr

# Check status
sudo supervisorctl status
sudo systemctl status nginx
sudo systemctl status mongod
sudo systemctl status redis-server

# Restart services
sudo supervisorctl restart all
sudo systemctl restart nginx
```

## Monitoring & Maintenance

1. **Application Monitoring**: Use tools like Sentry for error tracking
2. **Performance Monitoring**: Monitor API response times with Nginx logs
3. **Database Monitoring**: MongoDB monitoring with mongostat and mongotop
4. **Log Management**: Centralized logging with logrotate
5. **Backup Strategy**: Daily automated MongoDB backups (retention: 7 days)
6. **Update Schedule**: Weekly security patches, monthly feature updates
7. **Server Monitoring**: Use htop, iostat for resource monitoring
8. **Uptime Monitoring**: UptimeRobot or similar service

## Future Enhancements

1. **Mobile Application**: Native iOS and Android apps
2. **AI-Powered Resume Builder**: Help users create job-specific resumes
3. **Mock Test Platform**: Practice tests for various exams
4. **Study Material Section**: Notes and resources
5. **Discussion Forum**: Community for job seekers
6. **Video Tutorials**: Preparation guides
7. **Referral System**: Users can refer friends
8. **Premium Features**: Advanced analytics and priority notifications
9. **Multi-language Support**: Support for regional languages
10. **Interview Preparation**: Tips and common questions

## Success Metrics

1. **User Engagement**: Daily active users, session duration
2. **Job Discovery**: Average jobs viewed per user
3. **Application Rate**: Jobs applied vs jobs viewed
4. **Notification Effectiveness**: Open rate, click-through rate
5. **User Retention**: Monthly active users returning
6. **Platform Growth**: New registrations per month
7. **Job Success Rate**: Users selected in applied jobs

## Troubleshooting (Hostinger VPS)

### Application won't start
```bash
# Check supervisor logs
sudo supervisorctl tail -f sarkaripath stderr

# Check if port is in use
sudo lsof -i :8000

# Restart application
sudo supervisorctl restart sarkaripath
```

### High Memory Usage
```bash
# Check memory usage
free -h
htop

# Reduce Gunicorn workers in gunicorn_config.py
workers = 2  # Instead of 3

# Restart services
sudo supervisorctl restart all
```

### MongoDB Connection Issues
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Test connection
mongosh "mongodb://sarkaripath_user:password@localhost:27017/sarkari_path"
```

### Celery Tasks Not Running
```bash
# Check Celery worker status
sudo supervisorctl status celery_worker celery_beat

# View Celery logs
sudo supervisorctl tail -f celery_worker stderr

# Restart Celery
sudo supervisorctl restart celery_worker celery_beat
```

### SSL Certificate Issues
```bash
# Renew certificate manually
sudo certbot renew --nginx

# Check certificate expiry
sudo certbot certificates
```

### 502 Bad Gateway Error
```bash
# Check if Gunicorn is running
sudo supervisorctl status sarkaripath

# Check Nginx error logs
sudo tail -f /var/log/nginx/sarkaripath_error.log

# Restart services
sudo supervisorctl restart sarkaripath
sudo systemctl restart nginx
```

---

**Project Repository**: https://github.com/SumanKr7/sarkari_path_2.0
**License**: MIT License
