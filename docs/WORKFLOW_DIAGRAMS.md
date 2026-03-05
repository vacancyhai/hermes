# Hermes - System Workflow Diagrams (ASCII)

## 1. Overall System Architecture (SEPARATED MICROSERVICES)

**🎯 MAJOR CHANGE**: Backend and Frontend are now **COMPLETELY SEPARATED** services with their own Docker Compose files. They communicate via HTTP REST API.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│        HERMES - SEPARATED MICROSERVICES (6 Containers, 2 Services)           │
└──────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   Internet   │
                              │   (HTTPS)    │
                              └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐  ┌──────▼───────┐  ┌────▼────────┐
            │   Web Users  │  │ Mobile Users │  │   Admin     │
            └───────┬──────┘  └──────┬───────┘  └────┬────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         │  Option 1: Same Server    │   Option 2: Different     │
         │  (Development)            │   Servers (Production)    │
         │                           │                           │
         ↓                           ↓                           ↓
┌────────────────────────┐   ┌──────────────────────┐   ┌───────────────────────┐
│  FRONTEND SERVICE      │   │  Nginx Reverse Proxy │   │  BACKEND SERVICE      │
│  (src/frontend/)       │   │  (Optional)          │   │  (src/backend/)       │
│                        │   │                      │   │                       │
│  docker-compose.yml    │   │  Routes:             │   │  docker-compose.yml   │
│  ┌──────────────────┐  │   │  /api/* → Backend   │   │  ┌─────────────────┐  │
│  │  Frontend        │  │   │  /*     → Frontend  │   │  │  1. MongoDB     │  │
│  │  - Flask/Jinja2  │  │   └──────────────────────┘   │  │  Database       │  │
│  │  - Port 8080     │  │            │                 │  │  Port 27017     │  │
│  │  - Renders HTML  │  │            │                 │  │  Persistent     │  │
│  │                  │  │            │                 │  │                 │  │
│  │  Calls Backend:  │──┼────────────┘                 │  └────────┬────────┘  │
│  │  HTTP API        │  │         HTTP REST API        │           │           │
│  │  http://backend  │  │         /api/v1/*            │  ┌────────▼────────┐  │
│  │  :5000/api/v1/*  │  │                              │  │  2. Redis       │  │
│  │                  │  │    ┌─────────────────────┐   │  │  Cache + Queue  │  │
│  │  Future: Replace │  │    │  Can deploy on      │   │  │  Port 6379      │  │
│  │  with React/iOS/ │  │    │  different servers: │   │  │  AOF Persist    │  │
│  │  Android WITHOUT │  │    │                     │   │  │                 │  │
│  │  touching backend│  │    │  Frontend: Server 1 │   │  └────────┬────────┘  │
│  │                  │  │    │  Backend:  Server 2 │   │           │           │
│  └──────────────────┘  │    │                     │   │  ┌────────▼────────┐  │
│                        │    └─────────────────────┘   │  │  3. Backend API │  │
│  Environment:          │                              │  │  Flask REST     │  │
│  BACKEND_API_URL=      │                              │  │  Port 5000      │  │
│  http://backend:5000   │                              │  │  /api/v1/*      │  │
│  /api/v1/              │                              │  │  JWT Auth       │  │
│                        │                              │  │  CORS Enabled   │  │
└────────────────────────┘                              │  │  RBAC           │  │
                                                        │  └────────┬────────┘  │
         Deploy Separately!                             │           │           │
         Can scale independently!                       │  ┌────────▼────────┐  │
         Can change tech stack anytime!                 │  │ 4. Celery Worker│  │
                                                        │  │  Background     │  │
                                                        │  │  Tasks (1-N)    │  │
                                                        │  │  - Emails       │  │
                                                        │  │  - Notifications│  │
                                                        │  │  - Matching     │  │
                                                        │  └─────────────────┘  │
                                                        │                       │
                                                        │  ┌─────────────────┐  │
                                                        │  │ 5. Celery Beat  │  │
                                                        │  │  Task Scheduler │  │
                                                        │  │  (Always 1)     │  │
                                                        │  │  - Daily tasks  │  │
                                                        │  │  - Reminders    │  │
                                                        │  │  - Cleanup      │  │
                                                        │  └─────────────────┘  │
                                                        │                       │
                                                        │  Exposes: /api/v1/*   │
                                                        │  on port 5000         │
                                                        │                       │
                                                        └───────────────────────┘
                                                                 │
                                                        Deploy Separately!
                                                        Can scale independently!
                                                        Technology won't change!
                                                                 │
                                                                 ↓
                                              ┌──────────────────────────────┐
                                              │  External Services           │
                                              │  ┌────────────┐             │
                                              │  │  Email     │             │
                                              │  │  (SMTP)    │             │
                                              │  └────────────┘             │
                                              │  ┌────────────┐             │
                                              │  │  Firebase  │             │
                                              │  │  FCM (Push)│             │
                                              │  └────────────┘             │
                                              └──────────────────────────────┘

**Key Architecture Changes**:
✅ Backend and Frontend in separate folders (src/backend/, src/frontend/)
✅ Each has its own docker-compose.yml
✅ Frontend calls Backend via HTTP (not internal Docker network)
✅ Can deploy on same server OR different servers
✅ Can replace Frontend (Flask → React → Mobile) WITHOUT touching Backend
✅ Backend technology is stable and won't change
✅ Frontend technology can evolve based on requirements

**Communication Flow**:
User → Frontend (HTML/SPA/Mobile)  
     → HTTP Request to Backend API (http://backend:5000/api/v1/*)
     → Backend processes request
     → Returns JSON response
     → Frontend renders result to user
```

## 2. User Registration & Profile Setup Flow

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌──────────────────────┐
│ User visits website  │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Click on "Register"  │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Fill registration form:           │
│ - Email                           │
│ - Password                        │
│ - Full Name                       │
│ - Phone                           │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│ Submit form          │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐      ┌─────────────────┐
│ Validate input       │─────►│  Error? Show    │
│                      │      │  validation msg │
└────┬─────────────────┘      └────────┬────────┘
     │                                  │
     │ Valid                            │
     ▼                                  │
┌──────────────────────┐               │
│ Hash password        │               │
└────┬─────────────────┘               │
     │                                  │
     ▼                                  │
┌──────────────────────┐               │
│ Save to MongoDB      │               │
│ (Users collection)   │               │
└────┬─────────────────┘               │
     │                                  │
     ▼                                  │
┌──────────────────────┐               │
│ Generate JWT token   │               │
└────┬─────────────────┘               │
     │                                  │
     ▼                                  │
┌──────────────────────┐               │
│ Send verification    │               │
│ email                │               │
└────┬─────────────────┘               │
     │                                  │
     ▼                                  │
┌──────────────────────┐               │
│ Redirect to profile  │◄──────────────┘
│ setup page           │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Complete Profile Setup:           │
│ 1. Personal Information           │
│    - DOB, Gender, Category        │
│    - State, City                  │
│                                   │
│ 2. Education Details              │
│    - 10th, 12th, Graduation       │
│    - Stream, Percentage           │
│                                   │
│ 3. Notification Preferences       │
│    - Preferred Organizations      │
│    - Job Types                    │
│    - Locations                    │
│    - Notification Channels        │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│ Save profile to      │
│ User Profiles        │
│ collection           │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Profile Complete!    │
│ Redirect to          │
│ Dashboard            │
└────┬─────────────────┘
     │
     ▼
┌─────────┐
│   END   │
└─────────┘
```

## 3. Job Vacancy Creation & Publishing (Admin Flow)

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌──────────────────────┐
│ Admin logs in        │
│ (role: "admin")      │
└────┬─────────────────┘
     │
     ▼
┌────────────────────────┐
│ 🔒 PERMISSION CHECK    │
│ Is user.role = admin?  │
└────┬───────────────────┘
     │
     ├─ NO → 403 Forbidden
     │
     ▼ YES
┌──────────────────────┐
│ Navigate to          │
│ Admin Dashboard      │
│ (/api/v1/admin)      │
│ + X-Request-ID       │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Click "Add New Job"  │
└────┬─────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│ Fill Job Details Form:                  │
│                                         │
│ ┌───────────────────────────────────┐  │
│ │ Basic Information                 │  │
│ │ - Job Title                       │  │
│ │ - Organization                    │  │
│ │ - Department                      │  │
│ │ - Total Vacancies                 │  │
│ │ - Description                     │  │
│ └───────────────────────────────────┘  │
│                                         │
│ ┌───────────────────────────────────┐  │
│ │ Eligibility Criteria              │  │
│ │ - Minimum Qualification           │  │
│ │ - Stream Required                 │  │
│ │ - Age Limit (Min/Max)             │  │
│ │ - Category-wise Vacancies         │  │
│ └───────────────────────────────────┘  │
│                                         │
│ ┌───────────────────────────────────┐  │
│ │ Application Details               │  │
│ │ - Application Fee                 │  │
│ │ - Application Mode                │  │
│ │ - Official Website                │  │
│ └───────────────────────────────────┘  │
│                                         │
│ ┌───────────────────────────────────┐  │
│ │ Important Dates                   │  │
│ │ - Application Start/End           │  │
│ │ - Exam Date                       │  │
│ │ - Admit Card Date                 │  │
│ │ - Result Date                     │  │
│ └───────────────────────────────────┘  │
└────┬───────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Submit form                      │
│ POST /api/v1/admin/jobs          │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ 🔒 PERMISSION CHECK              │
│ @require_role('admin')           │
│ Is user.role == 'admin'?         │
└────┬───────────────────────────────┘
     │
     ├─ NO (403 Forbidden) → Return error
     │
     ▼ YES (admin verified)
┌──────────────────────┐
│ Submit form          │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐      ┌─────────────────┐
│ Validate all fields  │─────►│ Error? Show     │
└────┬─────────────────┘      │ validation msg  │
     │                        └────────┬────────┘
     │ Valid                           │
     ▼                                 │
┌──────────────────────┐              │
│ Save to MongoDB      │              │
│ (Job Vacancies       │              │
│  collection)         │              │
└────┬─────────────────┘              │
     │                                 │
     ▼                                 │
┌──────────────────────┐              │
│ Create admin log     │              │
│ entry                │              │
└────┬─────────────────┘              │
     │                                 │
     ▼                                 │
┌──────────────────────┐              │
│ Trigger Celery Task: │              │
│ "match_new_job_      │              │
│  with_users"         │              │
└────┬─────────────────┘              │
     │                                 │
     ▼                                 │
┌─────────────────────────────────┐   │
│ Celery Task Execution:          │   │
│                                 │   │
│ 1. Fetch all active users       │   │
│ 2. For each user:               │   │
│    ├─► Check profile eligibility│   │
│    ├─► Check preferences match  │   │
│    └─► Calculate match score    │   │
│ 3. If eligible & preferences    │   │
│    match:                        │   │
│    └─► Create notification      │   │
└────┬────────────────────────────┘   │
     │                                 │
     ▼                                 │
┌──────────────────────┐              │
│ Send notifications   │              │
│ to matched users via:│              │
│ - Email              │              │
│ - Push notification  │              │
│ - In-app alert       │              │
└────┬─────────────────┘              │
     │                                 │
     ▼                                 │
┌──────────────────────┐              │
│ Job successfully     │◄─────────────┘
│ published!           │
│ Show success message │
└────┬─────────────────┘
     │
     ▼
┌─────────┐
│   END   │
└─────────┘
```

## 4. Job Matching & Notification Flow

```
┌─────────────────────┐
│ Trigger: New Job    │
│ Created or Daily    │
│ Scheduled Task      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Fetch Job Details   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Get All Active      │
│ Users from DB       │
└─────────┬───────────┘
          │
          ▼
     ┌────────────────────────────┐
     │  FOR EACH USER:            │
     │  ┌──────────────────────┐  │
     │  │ Fetch User Profile   │  │
     │  └──────────┬───────────┘  │
     │             │              │
     │             ▼              │
     │  ┌──────────────────────┐  │
     │  │ Check Education      │  │
     │  │ Eligibility          │  │
     │  └──────────┬───────────┘  │
     │             │              │
     │     ┌───────┴────────┐     │
     │     │                │     │
     │     ▼                ▼     │
     │ ┌────────┐      ┌────────┐│
     │ │  Not   │      │Eligible││
     │ │Eligible│      └───┬────┘│
     │ └───┬────┘          │     │
     │     │               ▼     │
     │     │    ┌──────────────┐ │
     │     │    │ Check Stream │ │
     │     │    │ (if required)│ │
     │     │    └───┬──────────┘ │
     │     │        │            │
     │     │  ┌─────┴─────┐      │
     │     │  │           │      │
     │     │  ▼           ▼      │
     │     │ No      ┌────────┐  │
     │     │ Match   │ Match! │  │
     │     │         └───┬────┘  │
     │     │             │       │
     │     │             ▼       │
     │     │   ┌─────────────┐   │
     │     │   │ Check Age   │   │
     │     │   │ Eligibility │   │
     │     │   └──────┬──────┘   │
     │     │          │          │
     │     │    ┌─────┴─────┐    │
     │     │    │           │    │
     │     │    ▼           ▼    │
     │     │   No      ┌────────┐│
     │     │   Match   │Eligible││
     │     │           └───┬────┘│
     │     │               │     │
     │     │               ▼     │
     │     │   ┌──────────────┐  │
     │     │   │Check Category│  │
     │     │   │  Vacancies   │  │
     │     │   └──────┬───────┘  │
     │     │          │          │
     │     │    ┌─────┴─────┐    │
     │     │    │           │    │
     │     │    ▼           ▼    │
     │     │   No     ┌─────────┐│
     │     │   Vacancy│ Available││
     │     │          └────┬────┘│
     │     │               │     │
     │     │               ▼     │
     │     │ ┌──────────────────┐│
     │     │ │ Check User       ││
     │     │ │ Notification     ││
     │     │ │ Preferences      ││
     │     │ └────────┬─────────┘│
     │     │          │          │
     │     │    ┌─────┴─────┐    │
     │     │    │           │    │
     │     │    ▼           ▼    │
     │     │  Doesn't  ┌────────┐│
     │     │  Match    │ Match! ││
     │     │           └───┬────┘│
     │     │               │     │
     │     │               ▼     │
     │     │   ┌──────────────┐  │
     │     │   │ Calculate    │  │
     │     │   │ Match Score  │  │
     │     │   └──────┬───────┘  │
     │     │          │          │
     │     │          ▼          │
     │     │   ┌──────────────┐  │
     │     │   │Create        │  │
     │     │   │Notification  │  │
     │     │   │Record in DB  │  │
     │     │   └──────┬───────┘  │
     │     │          │          │
     │     └──────────┼──────────┘
     │                │
     └────────────────┼──────────┐
                      │          │
          ┌───────────┘          │
          │                      │
          ▼                      │ Skip
┌──────────────────┐             │
│ Queue Notification│            │
│ for Sending       │            │
└─────────┬─────────┘            │
          │                      │
          ▼                      │
┌──────────────────────────┐     │
│ Check User Preference:   │     │
│ - Email enabled?         │     │
│ - Push enabled?          │     │
│ - SMS enabled?           │     │
└─────────┬────────────────┘     │
          │                      │
          ▼                      │
┌──────────────────┐             │
│ Send via enabled │             │
│ channels:        │             │
│                  │             │
│ ┌──────────────┐ │             │
│ │ Send Email   │ │             │
│ └──────────────┘ │             │
│ ┌──────────────┐ │             │
│ │ Send Push    │ │             │
│ └──────────────┘ │             │
│ ┌──────────────┐ │             │
│ │ Send SMS     │ │             │
│ └──────────────┘ │             │
└─────────┬────────┘             │
          │                      │
          ▼                      │
┌──────────────────┐             │
│ Update           │             │
│ notification     │             │
│ status as "sent" │             │
└─────────┬────────┘             │
          │                      │
          └──────────────────────┘
                   │
                   ▼
          ┌────────────────┐
          │ Process Next   │
          │ User           │
          └────────────────┘
                   │
                   ▼ (All users processed)
          ┌────────────────┐
          │ END            │
          └────────────────┘
```

## 5. User Job Application & Tracking Flow

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌──────────────────────┐
│ User browses jobs    │
│ (Dashboard/Search)   │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Click on job to view │
│ full details         │
└────┬─────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ Job Details Page Shows:            │
│ - Job Title & Organization         │
│ - Eligibility Criteria             │
│ - Important Dates                  │
│ - Application Fee                  │
│ - Selection Process                │
│ - Official Website Link            │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ [Apply Now] [Add to Tracker]  │ │
│ │ [Mark as Priority]             │ │
│ └────────────────────────────────┘ │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│ User clicks          │
│ "Add to Tracker"     │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Check if already     │
│ tracked              │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐      ┌─────────────────┐
│ Already tracked?     │─────►│ Show message:   │
└────┬─────────────────┘ YES  │ "Already in     │
     │                        │  tracker"       │
     │ NO                     └─────────────────┘
     ▼
┌────────────────────────────────────┐
│ Show Application Form:             │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ Application Number (optional)  │ │
│ │ ┌────────────────────────────┐ │ │
│ │ │ [________________]         │ │ │
│ │ └────────────────────────────┘ │ │
│ │                                │ │
│ │ Mark as Priority? [✓]          │ │
│ │                                │ │
│ │ Personal Notes:                │ │
│ │ ┌────────────────────────────┐ │ │
│ │ │                            │ │ │
│ │ │ (Text area for notes)      │ │ │
│ │ │                            │ │ │
│ │ └────────────────────────────┘ │ │
│ │                                │ │
│ │ Enable Reminders:              │ │
│ │ [✓] Application Deadline       │ │
│ │ [✓] Admit Card Release         │ │
│ │ [✓] Exam Date                  │ │
│ │ [✓] Result Declaration         │ │
│ │                                │ │
│ │ [ Submit ]  [ Cancel ]         │ │
│ └────────────────────────────────┘ │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│ Create application   │
│ record in DB         │
│ (User Job            │
│  Applications)       │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Generate reminder    │
│ entries based on     │
│ job important dates  │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ If marked as         │
│ priority, set        │
│ priority flag        │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Show success message │
│ "Added to your       │
│  application tracker"│
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ User navigates to    │
│ "My Applications"    │
└────┬─────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ Applications Dashboard Shows:      │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ Tabs:                          │ │
│ │ [All] [Priority] [Upcoming]    │ │
│ │ [Past Exams] [Results Pending] │ │
│ └────────────────────────────────┘ │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ ┌────────────────────────────┐ │ │
│ │ │ Job: Railway ALP           │ │ │
│ │ │ Org: RRB                   │ │ │
│ │ │ ⭐ Priority                │ │ │
│ │ │                            │ │ │
│ │ │ Next: Exam on 15-Feb-2026  │ │ │
│ │ │ Status: Applied            │ │ │
│ │ │                            │ │ │
│ │ │ [View] [Edit] [Delete]     │ │ │
│ │ └────────────────────────────┘ │ │
│ │                                │ │
│ │ ┌────────────────────────────┐ │ │
│ │ │ Job: SSC CGL               │ │ │
│ │ │ Org: SSC                   │ │ │
│ │ │                            │ │ │
│ │ │ Next: Application Deadline │ │ │
│ │ │       31-Dec-2025          │ │ │
│ │ │ Status: Application Open   │ │ │
│ │ │                            │ │ │
│ │ │ [View] [Edit] [Delete]     │ │ │
│ │ └────────────────────────────┘ │ │
│ └────────────────────────────────┘ │
└────────────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│ Background Process:  │
│ Celery checks        │
│ reminders daily      │
└────┬─────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ For each application with          │
│ upcoming dates:                    │
│                                    │
│ IF date is in:                     │
│ - 7 days: Send reminder            │
│ - 3 days: Send reminder            │
│ - 1 day: Send reminder             │
│ - Same day: Send final reminder    │
│                                    │
│ Update reminder status as "sent"   │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│ User receives        │
│ notifications via    │
│ email/push/SMS       │
└────┬─────────────────┘
     │
     ▼
┌─────────┐
│   END   │
└─────────┘
```

## 6. Priority Job Update Notification Flow

```
┌─────────────────────┐
│ Trigger: Admin      │
│ updates a job       │
│ (dates, status)     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Save updated job    │
│ to database         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────┐
│ Trigger Celery Task:            │
│ check_priority_jobs             │
│ Queue: HIGH (priority)          │
│ Retry: 5x exponential backoff   │
└─────────┬───────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Find all users who  │
│ marked this job as  │
│ priority            │
└─────────┬───────────┘
          │
          ▼
     ┌────────────────────────────┐
     │  FOR EACH USER:            │
     │                            │
     │  ┌──────────────────────┐  │
     │  │ Get user's           │  │
     │  │ notification         │  │
     │  │ preferences          │  │
     │  └──────────┬───────────┘  │
     │             │              │
     │             ▼              │
     │  ┌──────────────────────┐  │
     │  │ Determine what       │  │
     │  │ changed:             │  │
     │  │ - Application date?  │  │
     │  │ - Exam date?         │  │
     │  │ - Admit card date?   │  │
     │  │ - Result date?       │  │
     │  │ - Job cancelled?     │  │
     │  └──────────┬───────────┘  │
     │             │              │
     │             ▼              │
     │  ┌──────────────────────┐  │
     │  │ Create notification  │  │
     │  │ with update details  │  │
     │  └──────────┬───────────┘  │
     │             │              │
     │             ▼              │
     │  ┌──────────────────────┐  │
     │  │ Set priority: HIGH   │  │
     │  │ Route to: HIGH queue │  │
     │  └──────────┬───────────┘  │
     │             │              │
     │             ▼              │
     │  ┌──────────────────────┐  │
     │  │ Send notification    │  │
     │  │ via all enabled      │  │
     │  │ channels             │  │
     │  │ Retry: 5x on failure │  │
     │  └──────────┬───────────┘  │
     │             │              │
     │             ▼              │
     │   ┌────────────────┐       │
     │   │  Email Failed? │       │
     │   └─────┬──────────┘       │
     │         │                  │
     │    ┌────┴─────┐            │
     │    │          │            │
     │    ▼ YES      ▼ NO         │
     │  ┌────────┐  ┌──────────┐ │
     │  │ Retry  │  │ Continue │ │
     │  │ 5x with│  └────┬─────┘ │
     │  │ exp BO │       │       │
     │  └───┬────┘       │       │
     │      │            │       │
     │      ▼            ▼       │
     │  ┌──────────────────────┐ │
     │  │ Update user's        │ │
     │  │ application record   │ │
     │  │ with new dates       │ │
     │  └──────────────────────┘ │
     │                            │
     └────────────────────────────┘
                   │
                   ▼
          ┌────────────────┐
          │ END            │
          └────────────────┘
```

## 7. Admin Dashboard Workflow

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌──────────────────────┐
│ Admin Login          │
└────┬─────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────┐
│            ADMIN DASHBOARD                         │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ Statistics Cards:                            │ │
│  │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │ │
│  │ │ Total  │ │ Active │ │  Total │ │  New   │ │ │
│  │ │ Users  │ │  Jobs  │ │  Apps  │ │ Users  │ │ │
│  │ │ 10,547 │ │   234  │ │ 45,231 │ │  +127  │ │ │
│  │ └────────┘ └────────┘ └────────┘ └────────┘ │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ Quick Actions:                               │ │
│  │ [+ Add New Job]  [View Users]  [Analytics]   │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ Recent Activity:                             │ │
│  │ • New user registration: john@example.com    │ │
│  │ • Job application: SSC CGL by 25 users       │ │
│  │ • Job updated: Railway ALP dates changed     │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │ Popular Jobs (Most Applied):                 │ │
│  │ 1. SSC CGL - 5,234 applications              │ │
│  │ 2. Railway ALP - 4,892 applications          │ │
│  │ 3. UPSC CSE - 3,456 applications             │ │
│  └──────────────────────────────────────────────┘ │
└────┬───────────────────────────────────────────────┘
     │
     ├──────────────┬──────────────┬──────────────┐
     │              │              │              │
     ▼              ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Job    │  │   User   │  │Analytics │  │ Content  │
│Management│  │Management│  │   &      │  │Management│
└────┬────┘  └────┬─────┘  │ Reports  │  └────┬─────┘
     │            │         └────┬─────┘       │
     │            │              │             │
     ▼            ▼              ▼             ▼
┌────────────────────────────────────────────────────┐
│                                                    │
│  JOB MANAGEMENT:          USER MANAGEMENT:        │
│  • Create Job             • View All Users        │
│  • Edit Job               • User Details          │
│  • Delete Job             • Ban/Unban Users       │
│  • Bulk Upload            • Export User Data      │
│  • Job Status             • User Applications     │
│                                                    │
│  ANALYTICS:               CONTENT MANAGEMENT:     │
│  • User Demographics      • Edit Pages            │
│  • Application Trends     • Email Templates       │
│  • Popular Organizations  • Notification Templates│
│  • Notification Stats     • Banner Management     │
│                                                    │
└────────────────────────────────────────────────────┘
```

## 8. Database Operations Flow

```
┌────────────────────────────────────────────────────┐
│              MONGODB COLLECTIONS                   │
└────────────────────────────────────────────────────┘

         ┌─────────────────────────────┐
         │        Users                │
         │  - _id (Primary Key)        │
         │  - email                    │
         │  - password_hash            │
         │  - role                     │
         └───────────┬─────────────────┘
                     │
                     │ (One-to-One)
                     │
         ┌───────────▼─────────────────┐
         │    User Profiles            │
         │  - _id (Primary Key)        │
         │  - user_id (Foreign Key)    │
         │  - personal_info            │
         │  - education                │
         │  - preferences              │
         └───────────┬─────────────────┘
                     │
                     │
         ┌───────────┴─────────────────┐
         │                             │
         │ (One-to-Many)               │ (Many-to-Many)
         │                             │
┌────────▼──────────┐      ┌───────────▼──────────┐
│  Notifications    │      │ User Job Applications│
│  - _id            │      │  - _id               │
│  - user_id (FK)   │      │  - user_id (FK)      │
│  - job_id (FK)    │      │  - job_id (FK)       │
│  - message        │      │  - is_priority       │
│  - is_read        │      │  - status            │
└───────────────────┘      └──────────┬───────────┘
                                      │
                                      │ (Many-to-One)
                                      │
                           ┌──────────▼───────────┐
                           │   Job Vacancies      │
                           │  - _id (Primary Key) │
                           │  - job_title         │
                           │  - organization      │
                           │  - eligibility       │
                           │  - important_dates   │
                           └──────────┬───────────┘
                                      │
                                      │ (One-to-Many)
                                      │
                           ┌──────────▼───────────┐
                           │    Admin Logs        │
                           │  - _id               │
                           │  - admin_id (FK)     │
                           │  - action            │
                           │  - resource_id       │
                           └──────────────────────┘

INDEXES FOR PERFORMANCE:
═══════════════════════

Users:
  - email (unique)
  - role

User Profiles:
  - user_id (unique)
  - education.highest_qualification
  - personal_info.category

Job Vacancies:
  - organization
  - eligibility.min_qualification
  - important_dates.application_end
  - status
  - created_at

User Job Applications:
  - user_id + job_id (compound, unique)
  - user_id + is_priority
  - job_id

Notifications:
  - user_id + is_read
  - created_at
  - job_id
```

## 9. Celery Task Scheduler Flow

```
┌────────────────────────────────────────────────────┐
│              CELERY BEAT SCHEDULER                 │
│            (Background Tasks Runner)               │
└────────────────────────────────────────────────────┘

┌──────────────────┐       ┌──────────────────┐
│   DAILY TASKS    │       │  HOURLY TASKS    │
│   (1:00 AM)      │       │  (Every Hour)    │
└────────┬─────────┘       └────────┬─────────┘
         │                          │
         ▼                          ▼
┌──────────────────┐       ┌──────────────────┐
│ Match New Jobs   │       │ Send Pending     │
│ with Users       │       │ Notifications    │
└────────┬─────────┘       └────────┬─────────┘
         │                          │
         │                          │
         └────────┬─────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  REDIS QUEUE   │
         │   (Broker)     │
         └────────┬───────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌────────┐   ┌────────┐   ┌────────┐
│ Worker │   │ Worker │   │ Worker │
│   1    │   │   2    │   │   3    │
└────┬───┘   └────┬───┘   └────┬───┘
     │            │            │
     └────────────┼────────────┘
                  │
                  ▼
     ┌────────────────────────┐
     │   TASK EXECUTION       │
     │                        │
     │ ┌────────────────────┐ │
     │ │ Fetch data from DB │ │
     │ └──────────┬─────────┘ │
     │            │           │
     │            ▼           │
     │ ┌────────────────────┐ │
     │ │ Process business   │ │
     │ │ logic              │ │
     │ └──────────┬─────────┘ │
     │            │           │
     │            ▼           │
     │ ┌────────────────────┐ │
     │ │ Send notifications │ │
     │ │ / Update DB        │ │
     │ └──────────┬─────────┘ │
     │            │           │
     │            ▼           │
     │ ┌────────────────────┐ │
     │ │ Store result in    │ │
     │ │ Redis backend      │ │
     │ └────────────────────┘ │
     └────────────────────────┘

SCHEDULED TASKS (with Priority Routing):
════════════════════════════════════════

1. daily_job_matching
   Run: Every day at 1:00 AM
   Priority: MEDIUM
   Purpose: Match new jobs with users
   Retry: 3x with exponential backoff

2. send_deadline_reminders
   Run: Every day at 9:00 AM
   Priority: HIGH
   Purpose: Send application deadline reminders
   Retry: 5x with exponential backoff

3. check_admit_card_dates
   Run: Every day at 8:00 AM
   Priority: HIGH
   Purpose: Check and notify admit card releases
   Retry: 5x (critical notifications)

4. check_exam_dates
   Run: Every day at 7:00 AM
   Priority: HIGH
   Purpose: Remind users of upcoming exams
   Retry: 5x (critical notifications)

5. check_result_dates
   Run: Every day at 6:00 PM
   Priority: HIGH
   Purpose: Notify about result declarations
   Retry: 5x (critical notifications)

6. cleanup_old_notifications
   Run: Every week (Sunday 2:00 AM)
   Priority: LOW
   Purpose: Archive old read notifications (TTL: 90 days)
   Retry: 1x

7. generate_weekly_report
   Run: Every Monday 6:00 AM
   Priority: LOW
   Purpose: Generate analytics report for admin
   Retry: 2x

8. cleanup_old_logs
   Run: Every week (Sunday 3:00 AM)
   Priority: LOW
   Purpose: Delete logs older than 30 days (TTL enforcement)
   Retry: 1x
```

## 10. Complete User Journey Map

```
┌────────────────────────────────────────────────────────────────┐
│                    USER JOURNEY MAP                            │
└────────────────────────────────────────────────────────────────┘

DAY 1: DISCOVERY & REGISTRATION
═══════════════════════════════
User finds website → Register → Verify Email → Complete Profile
                                                      │
                                                      ▼
                                            Setup Preferences:
                                            • Organizations
                                            • Job Types
                                            • Locations

DAY 2-7: JOB DISCOVERY
═══════════════════════
User Dashboard → Browse Jobs → Filter by Eligibility → View Details
                    │                                       │
                    └───────────────────────────────────────┘
                                    │
                                    ▼
                          Add to Application Tracker
                          Mark Important Jobs Priority

ONGOING: NOTIFICATION & TRACKING
═════════════════════════════════
Receive Notifications → Check Dashboard → Update Application Status
         │                                          │
         ├─ New Jobs (Matching Profile)            │
         ├─ Application Deadlines                  │
         ├─ Admit Card Releases                    │
         ├─ Exam Reminders                         │
         └─ Result Announcements                   │
                                                    ▼
                                    View "My Applications" Dashboard:
                                    • Upcoming Exams
                                    • Pending Applications
                                    • Past Exams
                                    • Results Awaited

APPLICATION PHASE
═════════════════
Select Job → Visit Official Website → Fill Application → Get App Number
                                                              │
                                                              ▼
                                              Update in Tracker with:
                                              • Application Number
                                              • Personal Notes
                                              • Enable Reminders

EXAM PHASE
══════════
Receive Admit Card Alert → Download Admit Card → Exam Reminder
                                                       │
                                                       ▼
                                            Take Exam → Mark as "Completed"

RESULT PHASE
════════════
Receive Result Notification → Check Result → Update Status:
                                                  │
                                   ┌──────────────┼──────────────┐
                                   │              │              │
                                   ▼              ▼              ▼
                              Selected      Not Selected    Interview Call
                                   │              │              │
                                   └──────────────┴──────────────┘
                                                  │
                                                  ▼
                                          Share Feedback (Optional)
                                          Continue Job Search
```

---

## 11. Role-Based Access Control (RBAC) Permission Enforcement

```
┌────────────────────────────────────────────────────────────────────┐
│           PERMISSION CHECK MIDDLEWARE (Every API Request)          │
└────────────────────────────────────────────────────────────────────┘

REQUEST FLOW with PERMISSION CHECKS:
════════════════════════════════════

    ┌─────────────────┐
    │ API Request     │
    │ (with JWT token)│
    └────────┬────────┘
             │
             ▼
    ┌──────────────────────┐
    │ Extract JWT token    │
    │ from header:         │
    │ Authorization:       │
    │   Bearer <token>     │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │ Decode JWT           │
    │ Extract claims:      │
    │ - user_id            │
    │ - email              │
    │ - role ⭐            │
    │ - exp                │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │ 🔒 Check endpoint    │
    │ Is this protected?   │
    └────────┬─────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼ NO              ▼ YES
 PUBLIC            PROTECTED
    │                 │
    │                 ▼
    │         ┌──────────────────────┐
    │         │ @require_role(...)   │
    │         │ Check allowed roles  │
    │         └────────┬─────────────┘
    │                  │
    │         ┌────────┴─────────┐
    │         │                  │
    │         ▼ ALLOWED          ▼ DENIED
    │      CONTINUE          (403 FORBIDDEN)
    │         │                  │
    └─────────┼──────────────────┘
              │
              ▼
    ┌──────────────────────┐
    │ Execute endpoint     │
    │ Return response      │
    └──────────────────────┘

ROLE-BASED ENDPOINT MATRIX:
═══════════════════════════

USER ROLE (👤) - Regular Job Seeker
────────────────────────────────────
✅ GET    /api/v1/jobs                    View all jobs (public)
✅ GET    /api/v1/jobs/<id>               View job details (public)
✅ GET    /api/v1/users/profile           View own profile
✅ PUT    /api/v1/users/profile           Update own profile
✅ GET    /api/v1/notifications           View own notifications
✅ GET    /api/v1/applications            View own applications
✅ POST   /api/v1/applications            Add to tracker
✅ POST   /api/v1/auth/refresh            Refresh access token

Rate Limits:
  - API: 1000 requests/min per user
  - Login: 5 attempts/min

❌ POST   /api/v1/admin/jobs              (Admin only) 403
❌ PUT    /api/v1/admin/jobs/<id>         (Admin only) 403
❌ DELETE /api/v1/admin/jobs/<id>         (Admin only) 403
❌ GET    /api/v1/admin/users             (Admin only) 403
❌ PUT    /api/v1/admin/users/<id>/role   (Admin only) 403
❌ GET    /api/v1/admin/analytics         (Admin only) 403

OPERATOR ROLE (🔧) - Content Reviewer
──────────────────────────────────────
✅ GET    /api/v1/jobs                    View all jobs
✅ GET    /api/v1/jobs/<id>               View job details
✅ PUT    /api/v1/jobs/<id>               Update job (limited fields)
  └─→ Can modify: status, description, important_dates
  └─→ CANNOT modify: salary_max, salary_min, vacancies

✅ GET    /api/v1/users/profile           View own profile
✅ PUT    /api/v1/users/profile           Update own profile
✅ GET    /api/v1/notifications           View own notifications
✅ GET    /api/v1/applications            View own applications
✅ POST   /api/v1/auth/refresh            Refresh access token

Rate Limits:
  - API: 1000 requests/min per user
  - Login: 5 attempts/min

❌ POST   /api/v1/jobs                    (Admin only) 403
❌ DELETE /api/v1/jobs/<id>               (Admin only) 403
❌ GET    /api/v1/admin/users             (Admin only) 403
❌ PUT    /api/v1/admin/users/<id>/role   (Admin only) 403
❌ GET    /api/v1/admin/analytics         (Admin only) 403
❌ POST   /api/v1/admin/jobs/<id>/toggle  (Admin only) 403

ADMIN ROLE (👨‍💼) - Full Control
──────────────────────────────────
✅ GET    /api/v1/jobs                    View all jobs
✅ GET    /api/v1/jobs/<id>               View job details
✅ POST   /api/v1/jobs                    Create job
✅ PUT    /api/v1/jobs/<id>               Update job (all fields)
✅ DELETE /api/v1/jobs/<id>               Delete job

✅ GET    /api/v1/users/profile           View own profile
✅ PUT    /api/v1/users/profile           Update own profile
✅ GET    /api/v1/admin/users             List all users
✅ GET    /api/v1/admin/users/<id>        View user details
✅ PUT    /api/v1/admin/users/<id>/role   Change user role (audit logged)
✅ PUT    /api/v1/admin/users/<id>/status Suspend/activate user

✅ GET    /api/v1/admin/analytics         View analytics
✅ GET    /api/v1/admin/logs              View activity logs
✅ GET    /api/v1/admin/audit             View audit trail
✅ GET    /api/v1/admin/jobs              List all jobs (admin panel)
✅ POST   /api/v1/admin/permissions       Update role permissions
✅ POST   /api/v1/auth/refresh            Refresh access token

Rate Limits:
  - API: 1000 requests/min per user
  - Login: 5 attempts/min

All admin actions are logged in audit_trail collection

EXAMPLE PERMISSION CHECK IN CODE:
═════════════════════════════════

# backend/app/routes/jobs.py

@bp.route('/<job_id>', methods=['PUT'])
@jwt_required()
@require_role('admin', 'operator')  # ⭐ Permission check
def update_job(job_id):
    claims = get_jwt()
    user_role = claims['role']
    
    # Get the job
    job = Job.objects(id=job_id).first()
    if not job:
        return {"error": "NOT_FOUND_JOB"}, 404
    
    # Get request data
    data = request.json
    
    # If operator, restrict what fields can be updated
    if user_role == 'operator':
        # Operator can only update: status, description, important_dates
        allowed_fields = ['status', 'description', 'important_dates']
        for key in data:
            if key not in allowed_fields:
                return {
                    "error": "FORBIDDEN_PERMISSION_DENIED",
                    "message": f"Operators cannot modify '{key}'"
                }, 403
    
    # Update the job
    job.update(**data)
    
    return jsonify(job.to_dict()), 200


@bp.route('/<job_id>', methods=['DELETE'])
@jwt_required()
@require_role('admin')  # ⭐ Only admin can delete
def delete_job(job_id):
    job = Job.objects(id=job_id).first()
    if not job:
        return {"error": "NOT_FOUND_JOB"}, 404
    
    job.delete()
    return '', 204

PERMISSION CHECK FLOW EXAMPLE:
══════════════════════════════

Request: PUT /api/v1/jobs/123
Header: 
  Authorization: Bearer eyJhbGc...[JWT]...
  X-Request-ID: abc123-def456-ghi789
Body: {"status": "APPROVED", "salary_max": 50000}

Step 1: Extract JWT
  user_id = "456"
  email = "operator@example.com"
  role = "operator"

Step 2: Check Endpoint Protection
  PUT /api/v1/jobs/<id> requires @require_role('admin', 'operator')

Step 3: Check Permission
  Is role='operator' in ['admin', 'operator']?
  ✅ YES → Continue

Step 4: Execute Business Logic
  Check operator restrictions:
  data = {"status": "APPROVED", "salary_max": 50000}
  
  allowed_fields = ['status', 'description', 'important_dates']
  
  "status" in allowed_fields? ✅ YES → Allow
  "salary_max" in allowed_fields? ❌ NO → Reject
  
  Return: 403 Forbidden
  "Operators cannot modify 'salary_max'"

Step 5: Log the attempt
  action = "UPDATE_JOB_ATTEMPTED"
  result = "FORBIDDEN - unauthorized field"
  request_id = "abc123-def456-ghi789"
  user_id = "456"
  email = "operator@example.com"
  ip_address = "192.168.1.100"
  timestamp = "2026-03-05T10:30:00Z"
  field_attempted = "salary_max"
  stored in audit_trail collection (TTL: 1 year)
```

---

## 12. JWT Token Rotation & Refresh Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    JWT TOKEN LIFECYCLE                           │
└──────────────────────────────────────────────────────────────────┘

INITIAL LOGIN:
══════════════

User Login
    │
    ▼
┌──────────────────────┐
│ POST /api/v1/auth/   │
│      login           │
│ + X-Request-ID       │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Validate credentials │
└────────┬─────────────┘
         │
         ▼ Valid
┌────────────────────────────────────┐
│ Generate TWO tokens:               │
│                                    │
│ 1. ACCESS TOKEN (15 minutes)       │
│    • Used for API calls            │
│    • Short-lived for security      │
│    • Contains: user_id, role, email│
│                                    │
│ 2. REFRESH TOKEN (7 days)          │
│    • Used to get new access token  │
│    • Long-lived                    │
│    • Stored securely               │
└────────┬───────────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Return to client:    │
│ {                    │
│   "access_token":    │
│      "eyJ...",       │
│   "refresh_token":   │
│      "eyJ...",       │
│   "expires_in": 900  │
│ }                    │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Client stores:       │
│ • Access token in    │
│   memory/localStorage│
│ • Refresh token in   │
│   httpOnly cookie    │
│   (more secure)      │
└──────────────────────┘


MAKING API CALLS:
═════════════════

Client makes API call
    │
    ▼
┌──────────────────────┐
│ Add header:          │
│ Authorization:       │
│   Bearer <access>    │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Backend validates    │
│ access token         │
└────────┬─────────────┘
         │
    ┌────┴────┐
    │         │
    ▼ Valid   ▼ Expired/Invalid
 Process    Return 401
 Request    Unauthorized
    │         │
    │         ▼
    │    ┌──────────────────────┐
    │    │ Client detects 401   │
    │    │ Automatically trigger│
    │    │ token refresh        │
    │    └──────────┬───────────┘
    │               │
    └───────────────┘


TOKEN REFRESH FLOW:
═══════════════════

Access Token Expired (after 15 min)
    │
    ▼
┌──────────────────────┐
│ POST /api/v1/auth/   │
│      refresh         │
│ + X-Request-ID       │
│                      │
│ Header:              │
│ Authorization:       │
│   Bearer <refresh>   │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Validate refresh     │
│ token                │
└────────┬─────────────┘
         │
    ┌────┴────┐
    │         │
    ▼ Valid   ▼ Invalid/Expired
┌─────────┐  ┌────────────────┐
│ Generate│  │ Return 401     │
│ NEW     │  │ User must      │
│ Access  │  │ login again    │
│ Token   │  │ (7 days passed)│
└────┬────┘  └────────────────┘
     │
     ▼
┌──────────────────────┐
│ Return:              │
│ {                    │
│   "access_token":    │
│      "eyJ... (new)", │
│   "expires_in": 900  │
│ }                    │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Client updates       │
│ access token         │
│ Retry original       │
│ request              │
└──────────────────────┘


SECURITY BENEFITS:
══════════════════

✅ Short access token (15 min)
   • Stolen token expires quickly
   • Limits exposure window

✅ Automatic refresh
   • Seamless UX for active users
   • No interruption

✅ Long refresh token (7 days)
   • Stored in httpOnly cookie
   • Not accessible to JavaScript
   • Protected from XSS attacks

✅ Forced re-login after 7 days
   • Periodic authentication verification
   • Compromised refresh token expires

✅ Token rotation
   • Each refresh issues new access token
   • Old tokens can be blacklisted


TOKEN STORAGE BEST PRACTICES:
═════════════════════════════

┌──────────────────────────────────┐
│ ACCESS TOKEN                     │
│ • Store in: Memory/localStorage  │
│ • Pros: Easy access for API calls│
│ • Cons: XSS vulnerable           │
│ • Mitigation: Short TTL (15 min) │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│ REFRESH TOKEN                    │
│ • Store in: httpOnly cookie      │
│ • Pros: Not accessible to JS     │
│ • Cons: CSRF vulnerable          │
│ • Mitigation: Same-Site cookie   │
│              + CSRF token        │
└──────────────────────────────────┘


LOGOUT FLOW:
════════════

User Logout
    │
    ▼
┌──────────────────────┐
│ POST /api/v1/auth/   │
│      logout          │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Backend:             │
│ • Blacklist tokens   │
│   in Redis (TTL 7d)  │
│ • Clear session      │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Client:              │
│ • Clear access token │
│ • Clear refresh token│
│ • Redirect to login  │
└──────────────────────┘


COMPROMISED TOKEN HANDLING:
═══════════════════════════

Suspicious Activity Detected
(e.g., multiple concurrent sessions)
    │
    ▼
┌──────────────────────┐
│ Admin/System:        │
│ • Add token to       │
│   blacklist (Redis)  │
│ • Force user logout  │
│ • Require re-login   │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ User attempts API    │
│ call with old token  │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Backend checks:      │
│ • Token in blacklist?│
│   ✅ YES → 401       │
│                      │
│ • Token expired?     │
│   ✅ YES → 401       │
└──────────────────────┘
```

---

## 13. Request ID Propagation & Distributed Tracing

```
┌──────────────────────────────────────────────────────────────────┐
│              REQUEST ID TRACING ACROSS SERVICES                  │
└──────────────────────────────────────────────────────────────────┘

User Request
    │
    ▼
┌────────────────────────────────────┐
│ Nginx receives request             │
│ Generates X-Request-ID if missing  │
│ X-Request-ID: abc123-def456-ghi789 │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Nginx forwards to Frontend         │
│ Headers:                           │
│   X-Request-ID: abc123-...         │
│   X-Real-IP: 192.168.1.100         │
│   X-Forwarded-For: ...             │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Frontend Flask                     │
│ @before_request:                   │
│   g.request_id = get_header(       │
│     'X-Request-ID')                │
│                                    │
│ Log: [abc123...] Page load: /jobs │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Frontend calls Backend API         │
│ GET /api/v1/jobs                   │
│ Headers:                           │
│   X-Request-ID: abc123-...         │
│   Authorization: Bearer eyJ...     │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Backend Flask                      │
│ @before_request:                   │
│   g.request_id = get_header(       │
│     'X-Request-ID')                │
│   g.start_time = time()            │
│                                    │
│ Log: [abc123...] API: GET /jobs   │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Backend queries MongoDB            │
│ Log: [abc123...] Query jobs DB     │
│      Duration: 45ms                │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Backend returns response           │
│ @after_request:                    │
│   response.headers.add(            │
│     'X-Request-ID', g.request_id)  │
│   response.headers.add(            │
│     'X-Response-Time', '67ms')     │
│                                    │
│ Log: [abc123...] Response: 200     │
│      Total: 67ms                   │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Frontend receives response         │
│ Log: [abc123...] API call complete │
│      Render template               │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ Nginx returns to user              │
│ Headers include:                   │
│   X-Request-ID: abc123-...         │
│   X-Response-Time: 67ms            │
└────────────────────────────────────┘


SEARCHING LOGS BY REQUEST ID:
═════════════════════════════

# View complete request flow across all services

$ grep "abc123-def456-ghi789" /var/log/nginx/access.log
[2026-03-05 10:30:00] GET /jobs abc123-def456-ghi789 200

$ grep "abc123-def456-ghi789" /app/frontend/logs/app.log
[abc123-def456-ghi789] Page load: /jobs
[abc123-def456-ghi789] Calling API: GET /api/v1/jobs
[abc123-def456-ghi789] API call complete: 200

$ grep "abc123-def456-ghi789" /app/backend/logs/app.log
[abc123-def456-ghi789] API: GET /api/v1/jobs
[abc123-def456-ghi789] User: 456 Role: user
[abc123-def456-ghi789] Query jobs DB - Duration: 45ms
[abc123-def456-ghi789] Response: 200 - Total: 67ms


ELASTICSEARCH AGGREGATION:
═══════════════════════════

GET /logs/_search
{
  "query": {
    "match": {
      "request_id": "abc123-def456-ghi789"
    }
  },
  "sort": [
    {"timestamp": "asc"}
  ]
}

Result: Complete timeline of request across all services


PERFORMANCE TRACKING:
═════════════════════

Request ID: abc123-def456-ghi789
  Nginx → Frontend:    5ms
  Frontend → Backend:  12ms
  Backend Query:       45ms
  Backend Processing:  10ms
  Total:               67ms
  
  Bottleneck: MongoDB query (67% of time)
  Recommendation: Add index on query field
```

---

## 14. Error Handling & Graceful Degradation Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                 ERROR HANDLING & GRACEFUL DEGRADATION              │
└────────────────────────────────────────────────────────────────────┘

SCENARIO 1: Email Service Failure
═════════════════════════════════

User triggers notification
    │
    ▼
┌──────────────────────┐
│ Queue email task     │
│ to Celery HIGH queue │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Celery worker picks  │
│ task from queue      │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Attempt to send      │
│ via SMTP             │
└────────┬─────────────┘
         │
    ┌────┴─────┐
    │          │
    ▼ Success  ▼ Failure (SMTP timeout)
┌────────┐  ┌──────────────────────┐
│ Mark   │  │ Catch exception      │
│ sent   │  │ Log error with       │
└───┬────┘  │ request_id           │
    │       └────────┬─────────────┘
    │                │
    │                ▼
    │       ┌──────────────────────┐
    │       │ Retry #1             │
    │       │ Wait: 2^1 = 2 sec    │
    │       └────────┬─────────────┘
    │                │
    │           ┌────┴─────┐
    │           │          │
    │           ▼ Success  ▼ Failure
    │       ┌────────┐  ┌──────────┐
    │       │ Done   │  │ Retry #2 │
    │       └────────┘  │ Wait: 4s │
    │                   └────┬─────┘
    │                        │
    │                   ┌────┴─────┐
    │                   │          │
    │                   ▼ Success  ▼ Failure
    │               ┌────────┐  ┌──────────┐
    │               │ Done   │  │ Retry #3 │
    │               └────────┘  │ Wait: 8s │
    │                           └────┬─────┘
    │                                │
    │                           ┌────┴─────┐
    │                           │          │
    │                           ▼ Success  ▼ Failure
    │                       ┌────────┐  ┌──────────┐
    │                       │ Done   │  │ Retry #4 │
    │                       └────────┘  │ Wait: 16s│
    │                                   └────┬─────┘
    │                                        │
    │                                   ┌────┴─────┐
    │                                   │          │
    │                                   ▼ Success  ▼ Failure
    │                               ┌────────┐  ┌──────────┐
    │                               │ Done   │  │ Retry #5 │
    │                               └────────┘  │ Wait: 32s│
    │                                           └────┬─────┘
    │                                                │
    │                                           ┌────┴─────┐
    │                                           │          │
    │                                           ▼ Success  ▼ Failure (All retries exhausted)
    │                                       ┌────────┐  ┌──────────────────┐
    │                                       │ Done   │  │ Mark as FAILED   │
    │                                       └────────┘  │ Store in DB      │
    │                                                   │ Alert admin      │
    │                                                   └────────┬─────────┘
    │                                                            │
    └────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                            ┌────────────────┐
                            │ User still gets│
                            │ in-app notif   │
                            └────────────────┘


SCENARIO 2: Firebase Push Notification Failure
══════════════════════════════════════════════

┌──────────────────────┐
│ Send push via FCM    │
└────────┬─────────────┘
         │
    ┌────┴─────┐
    │          │
    ▼ Success  ▼ Failure (Token invalid / Network error)
┌────────┐  ┌──────────────────────┐
│ Done   │  │ Fallback Strategy    │
└────────┘  └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │ 1. Store in          │
            │    in-app            │
            │    notifications     │
            └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │ 2. Send email        │
            │    (with 5x retry)   │
            └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │ Log FCM error        │
            │ for debugging        │
            └──────────────────────┘


SCENARIO 3: MongoDB Slow Response
══════════════════════════════════

API Request: GET /api/v1/jobs
    │
    ▼
┌──────────────────────┐
│ Check Redis cache    │
└────────┬─────────────┘
         │
    ┌────┴─────┐
    │          │
    ▼ HIT      ▼ MISS
┌────────┐  ┌──────────────────────┐
│ Return │  │ Query MongoDB        │
│ cached │  │ Timeout: 2 seconds   │
│ data   │  └────────┬─────────────┘
└────────┘           │
                ┌────┴─────┐
                │          │
                ▼ Fast (<2s) ▼ Slow (>2s timeout)
         ┌────────────┐  ┌──────────────────────┐
         │ Return data│  │ Check Redis again    │
         │ Cache it   │  │ for stale data       │
         └────────────┘  └────────┬─────────────┘
                                  │
                             ┌────┴─────┐
                             │          │
                             ▼ Found    ▼ Not found
                      ┌──────────────┐  ┌──────────────────┐
                      │ Return with  │  │ Return 503       │
                      │ flag:        │  │ Service temp     │
                      │ "stale_data":│  │ unavailable      │
                      │ true         │  │ Retry after: 30s │
                      └──────────────┘  └──────────────────┘


SCENARIO 4: Celery Worker Down
═══════════════════════════════

┌──────────────────────┐
│ New job posted       │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Queue matching task  │
│ to Redis             │
└────────┬─────────────┘
         │
         ▼
    ┌────────────────┐
    │ Workers alive? │
    └────┬───────────┘
         │
    ┌────┴─────┐
    │          │
    ▼ YES      ▼ NO (All workers down)
┌────────┐  ┌──────────────────────┐
│ Process│  │ Task stays in        │
│ task   │  │ Redis queue          │
└────────┘  │ (persistent)         │
            └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │ When worker restarts │
            │ it picks up queued   │
            │ tasks automatically  │
            └────────┬─────────────┘
                     │
                     ▼
            ┌──────────────────────┐
            │ Process all pending  │
            │ tasks in order       │
            └──────────────────────┘


SCENARIO 5: Connection Pool Exhausted
══════════════════════════════════════

API Request arrives
    │
    ▼
┌──────────────────────────┐
│ Try to get DB connection │
│ from pool (max: 50)      │
└────────┬─────────────────┘
         │
    ┌────┴─────┐
    │          │
    ▼ Available ▼ All busy
┌────────┐  ┌──────────────────────┐
│ Process│  │ Queue request        │
│ request│  │ Wait: 10 seconds max │
└────────┘  └────────┬─────────────┘
                     │
                ┌────┴─────┐
                │          │
                ▼ Available ▼ Timeout (10s)
         ┌────────────┐  ┌──────────────────┐
         │ Process    │  │ Return 503       │
         │ request    │  │ {                │
         └────────────┘  │   "error":       │
                         │   "SERVER_       │
                         │   OVERLOADED",   │
                         │   "retry_after": │
                         │   30             │
                         │ }                │
                         └──────────────────┘


ERROR CODE TAXONOMY:
═══════════════════

┌─────────────────────────────────────────────┐
│ AUTH_INVALID_TOKEN                          │
│ AUTH_EXPIRED_TOKEN                          │
│ AUTH_MISSING_TOKEN                          │
│ AUTH_INVALID_CREDENTIALS                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ VALIDATION_MISSING_FIELD                    │
│ VALIDATION_INVALID_EMAIL                    │
│ VALIDATION_INVALID_FORMAT                   │
│ VALIDATION_OUT_OF_RANGE                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ FORBIDDEN_PERMISSION_DENIED                 │
│ FORBIDDEN_ROLE_REQUIRED                     │
│ FORBIDDEN_RESOURCE_LOCKED                   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ RATE_LIMIT_IP_EXCEEDED                      │
│ RATE_LIMIT_USER_EXCEEDED                    │
│ RATE_LIMIT_LOGIN_ATTEMPTS                   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ SERVER_DATABASE_ERROR                       │
│ SERVER_TIMEOUT                              │
│ SERVER_OVERLOADED                           │
│ SERVER_SERVICE_UNAVAILABLE                  │
└─────────────────────────────────────────────┘

ALL ERRORS RETURN CONSISTENT FORMAT:
{
  "error": "ERROR_CODE",
  "message": "Human readable description",
  "details": { /* Optional context */ },
  "request_id": "abc123-def456",
  "timestamp": "2026-03-05T10:30:00Z"
}
```

---

## 15. Redis Cache-Aside Strategy Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                     REDIS CACHE-ASIDE PATTERN                      │
└────────────────────────────────────────────────────────────────────┘

CACHE-ASIDE PATTERN OVERVIEW:
═════════════════════════════

Application → Check Cache → Cache Hit? → Return cached data
                   │
                   ▼ Cache Miss
            Query Database → Store in Cache → Return data


DETAILED FLOW:
═════════════

┌─────────────────────┐
│ API Request arrives │
│ GET /api/v1/jobs    │
└─────────┬───────────┘
          │
          ▼
┌──────────────────────────────┐
│ Generate cache key:          │
│ "jobs:list:page1:limit20"    │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│ REDIS GET cache_key          │
└─────────┬────────────────────┘
          │
     ┌────┴─────┐
     │          │
     ▼ HIT      ▼ MISS
┌────────────┐  ┌──────────────────────┐
│ Return     │  │ Query MongoDB        │
│ cached     │  │ db.jobs.find()       │
│ data       │  └─────────┬────────────┘
│            │            │
│ Response   │            ▼
│ time:      │  ┌──────────────────────┐
│ ~5ms       │  │ Transform data       │
└────────────┘  │ to JSON              │
                └─────────┬────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │ REDIS SET cache_key  │
                │ value EX <TTL>       │
                └─────────┬────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │ Return data          │
                │                      │
                │ Response time:       │
                │ ~50ms (first time)   │
                │ ~5ms (subsequent)    │
                └──────────────────────┘


TTL STRATEGY BY DATA TYPE:
═════════════════════════

┌───────────────────────────────────────────────────┐
│ SESSIONS (15 minutes)                             │
│ Key: session:{user_id}:{token_id}                 │
│ Value: {user_id, role, email, permissions}        │
│ Why: Balance security (short) vs UX (not too short)│
│                                                   │
│ Example:                                          │
│ SETEX session:123:abc 900 '{"user_id":123,...}'  │
└───────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────┐
│ JOBS (1 hour)                                     │
│ Key: jobs:list:{page}:{filters_hash}             │
│ Value: [job_id_1, job_id_2, ...]                 │
│ Why: Jobs don't change frequently, reduce DB load │
│                                                   │
│ Individual job:                                   │
│ Key: job:{job_id}                                 │
│ TTL: 1 hour                                       │
│ Invalidate on: Job update/delete                 │
└───────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────┐
│ USER PREFERENCES (24 hours)                       │
│ Key: user:preferences:{user_id}                   │
│ Value: {organizations, locations, channels}       │
│ Why: Rarely changes, expensive to compute         │
│      (used in job matching)                       │
│                                                   │
│ Invalidate on: User updates preferences           │
└───────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────┐
│ RATE LIMITS (1 minute)                            │
│ Key: ratelimit:ip:{ip_address}                    │
│ Value: request_count                              │
│ Why: Short window for rate limiting               │
│                                                   │
│ Example:                                          │
│ INCR ratelimit:ip:192.168.1.1                    │
│ EXPIRE ratelimit:ip:192.168.1.1 60               │
│ If count > 100: Block request                     │
└───────────────────────────────────────────────────┘


CACHE INVALIDATION STRATEGIES:
══════════════════════════════

STRATEGY 1: Time-based (TTL)
────────────────────────────
✅ Automatic expiration
✅ Simple to implement
❌ May serve stale data until TTL expires

Used for: Jobs, preferences, non-critical data


STRATEGY 2: Event-based (Explicit Delete)
─────────────────────────────────────────
✅ Always fresh data
✅ Full control
❌ More complex code

Example flow:
┌──────────────────────┐
│ Admin updates job    │
│ (title, dates, etc)  │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Save to MongoDB      │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Delete from cache:   │
│ DEL job:{job_id}     │
│ DEL jobs:list:*      │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Next request will    │
│ rebuild cache from DB│
└──────────────────────┘

Used for: Jobs (when updated), user profiles


STRATEGY 3: Write-through
─────────────────────────
✅ Cache always in sync
❌ Slower writes
❌ Complex consistency

Not used in current system (cache-aside is simpler)


CACHE WARMING ON STARTUP:
════════════════════════

Backend container starts
    │
    ▼
┌──────────────────────┐
│ Load most popular    │
│ jobs into cache      │
│ (top 100 by views)   │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ FOR EACH job:        │
│   SETEX job:{id}     │
│   3600 (1 hour)      │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Cache warmed         │
│ First requests fast  │
└──────────────────────┘


MONITORING CACHE PERFORMANCE:
════════════════════════════

Track these metrics:

┌───────────────────────────────────────────┐
│ Cache Hit Rate                            │
│ = (Cache Hits / Total Requests) × 100     │
│                                           │
│ Target: > 80% for jobs                    │
│         > 95% for preferences             │
└───────────────────────────────────────────┘

┌───────────────────────────────────────────┐
│ Cache Memory Usage                        │
│ REDIS INFO memory                         │
│                                           │
│ Monitor: used_memory_human                │
│ Alert if: > 90% of max_memory             │
└───────────────────────────────────────────┘

┌───────────────────────────────────────────┐
│ Cache Latency                             │
│ Measure: Time for GET operations          │
│                                           │
│ Target: < 1ms for GET                     │
│         < 2ms for SET                     │
└───────────────────────────────────────────┘


EXAMPLE CODE:
════════════

# backend/app/utils/cache.py

import redis
import json
from functools import wraps

redis_client = redis.Redis(
    host='redis',
    port=6379,
    password=os.getenv('REDIS_PASSWORD'),
    socket_keepalive=True,
    decode_responses=True
)

def cache_aside(key_prefix, ttl_seconds):
    """Decorator for cache-aside pattern"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{args[0]}"  # Simplified
            
            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Cache miss - query database
            result = func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator


# Usage:
@cache_aside('job', 3600)  # 1 hour TTL
def get_job_by_id(job_id):
    """Fetch job from database"""
    return db.jobs.find_one({'_id': job_id})


# First call: Queries DB, caches result (~50ms)
# Subsequent calls: Returns from cache (~5ms)
job = get_job_by_id('507f1f77bcf86cd799439011')
```

---

**End of Workflow Diagrams**

*These ASCII diagrams provide a comprehensive visual representation of all major flows in the Hermes application system, including the 8-container microservices architecture, JWT token rotation with 15-minute access tokens and 7-day refresh tokens, RBAC enforcement with three roles (User, Operator, Admin), request ID tracing for distributed debugging, API v1 versioning, health checks, connection pooling, error handling with graceful degradation (5x retry with exponential backoff), Redis cache-aside pattern with TTL strategy, and production-ready resilience features.*
