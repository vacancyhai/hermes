# Sarkari Path - Government Job Vacancy Portal

## Project Overview

A comprehensive web application that provides users with personalized government job vacancy notifications based on their educational qualifications, preferences, and job priorities. The system includes user authentication, profile management, intelligent notification filtering, and an admin panel for job management.

## Tech Stack

- **Backend Framework**: Python Flask
- **Database**: MongoDB (NoSQL)
- **Authentication**: Flask-Login with JWT tokens
- **Task Queue**: Celery with Redis (for scheduled notifications)
- **Frontend**: HTML5, CSS3, JavaScript (can be extended with React/Vue)
- **Email Service**: Flask-Mail or SendGrid
- **Push Notifications**: Firebase Cloud Messaging (FCM)

## System Architecture

### Core Components

1. **User Management Module**
2. **Job Vacancy Module**
3. **Notification Engine**
4. **Admin Panel**
5. **Profile Matching System**
6. **Application Tracking System**

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

## Deployment Architecture

```
Load Balancer (Nginx)
    |
    ├─> Flask App Server 1
    ├─> Flask App Server 2
    └─> Flask App Server 3
         |
         ├─> MongoDB Cluster
         ├─> Redis (Session & Celery)
         └─> Celery Workers
```

## Project Structure

```
sarkari-path/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── job.py
│   │   ├── application.py
│   │   └── notification.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── jobs.py
│   │   ├── applications.py
│   │   ├── notifications.py
│   │   └── admin.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── matching_engine.py
│   │   ├── notification_service.py
│   │   ├── email_service.py
│   │   └── analytics_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── validators.py
│   │   └── helpers.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── job_matching.py
│   │   └── reminders.py
│   └── templates/
│       ├── admin/
│       ├── auth/
│       ├── jobs/
│       └── profile/
├── static/
│   ├── css/
│   ├── js/
│   └── img/
├── migrations/
├── tests/
│   ├── test_auth.py
│   ├── test_jobs.py
│   └── test_matching.py
├── config.py
├── requirements.txt
├── celery_worker.py
├── run.py
└── .env
```

## Required Python Packages

```txt
Flask==3.0.0
Flask-PyMongo==2.3.0
Flask-Login==0.6.3
Flask-JWT-Extended==4.5.3
Flask-Mail==0.9.1
Flask-WTF==1.2.1
Flask-Cors==4.0.0
celery==5.3.4
redis==5.0.1
pymongo==4.6.0
bcrypt==4.1.2
python-dotenv==1.0.0
email-validator==2.1.0
gunicorn==21.2.0
Pillow==10.1.0
firebase-admin==6.3.0
```

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

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

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

## Monitoring & Maintenance

1. **Application Monitoring**: Use tools like Sentry for error tracking
2. **Performance Monitoring**: Monitor API response times
3. **Database Monitoring**: MongoDB Atlas monitoring
4. **Log Management**: Centralized logging with ELK stack
5. **Backup Strategy**: Daily automated MongoDB backups
6. **Update Schedule**: Weekly security patches, monthly feature updates

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

---

**Project Repository**: https://github.com/yourusername/sarkari-path
**Documentation**: https://docs.sarkaripath.com
**License**: MIT License
