# Hermes — Diagrams

## 1. System Architecture

Backend, User Frontend, and Admin Frontend are independent services with
separate Docker Compose files. They communicate via HTTP REST API.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│        HERMES - SEPARATED MICROSERVICES (8 Containers, 3 Services)           │
└──────────────────────────────────────────────────────────────────────────────┘

                               ┌──────────────┐
                               │   Internet   │
                               │   (HTTPS)    │
                               └──────┬───────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                 │                 │
            ┌───────▼──────┐  ┌───────▼───────┐  ┌──────▼───────┐
            │  Web Users   │  │ Mobile Users  │  │Admin/Operator│
            └───────┬──────┘  └───────┬───────┘  └──────┬───────┘
                    │                 │                 │
                    └─────────────────┬─────────────────┘
                                      │
                             ┌────────▼─────────┐
                             │ Nginx (Optional) │
                             │ /*   → Port 8080 │
                             │ /admin/→ 8081    │
                             │ /api/  → 8000    │
                             └────────┬─────────┘
                                      │
               ┌──────────────────────┼──────────────────────┐
               │                      │                      │
               ▼                      ▼                      ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌────────────────────────┐
│  USER FRONTEND      │  │  ADMIN FRONTEND     │  │  BACKEND SERVICE       │
│  src/frontend/      │  │  src/frontend-admin/│  │  src/backend/          │
│                     │  │                     │  │                        │
│  1 container        │  │  1 container        │  │  5 containers:         │
│  Port: 8080         │  │  Port: 8081         │  │  1. PostgreSQL (5432)  │
│  Flask/Jinja2       │  │  Flask/Jinja2       │  │  2. Redis (6379)       │
│                     │  │                     │  │  3. Backend API (8000) │
│  Public users:      │  │  Staff only:        │  │  4. Celery Worker      │
│  - Register         │  │  - Admin login      │  │  5. Celery Beat        │
│  - Login            │  │  - Operator login   │  │                        │
│  - Browse jobs      │  │  - Manage jobs      │  │  JWT Auth + RBAC       │
│                     │  │  - Manage users     │  │  /api/v1/* endpoints   │
│  Calls backend via  │  │                     │  │                        │
│  BACKEND_API_URL    │  │  Calls backend via  │  │  Persistent storage:   │
│                     │  │  BACKEND_API_URL    │  │  PostgreSQL + Redis    │
│  Network:           │  │                     │  │  AOF persistence       │
│  src_frontend_      │  │  Network:           │  └──────────┬─────────────┘
│  network            │  │  src_frontend_      │             │
└─────────────────────┘  │  admin_network      │             ▼
                         │                     │  ┌──────────────────────┐
         Deploy          │  Firewall port 8081 │  │  External Services   │
         Separately!     │  from public        │  │  - OCI Email Delivery│
         Can scale       │  internet!          │  │  - Firebase FCM      │
         independently!  └─────────────────────┘  └──────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  Can deploy on same server (dev) or different servers (prod)                 │
│  Frontends: Server 1                   Backend: Server 2                     │
│  Each service has independent docker-compose.yml                             │
└──────────────────────────────────────────────────────────────────────────────┘

Architecture properties:
- Three separated services: User Frontend (8080), Admin Frontend (8081), Backend (8000)
- Each service has its own docker-compose.yml and Docker network
- Both frontends call Backend via HTTP REST API
- Admin Frontend at port 8081 — can be firewalled from public internet
- Any frontend can be replaced (Flask → React → React Native) without touching Backend

Communication flow:
Public User → User Frontend (port 8080)
     → HTTP Request to Backend API (http://backend:8000/api/v1/*)
     → Backend processes request
     → Returns JSON response
     → User Frontend renders result to user

Admin/Operator → Admin Frontend (port 8081)
     → HTTP Request to Backend API (http://backend:8000/api/v1/*)
     → Backend processes request (RBAC role checks applied)
     → Returns JSON response
     → Admin Frontend renders result
```

## 2. User Sign-In & Profile Setup Flow (Firebase Auth)

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌─────────────────────────┐
│ User visits /login      │
│ (Firebase JS SDK loaded)│
└────┬────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────┐
│ Choose sign-in method                            │
│                                                  │
│  A) Email OTP Registration  B) Google  C) Phone │
└────┬─────────────────────────────────────────────┘
     │
     ├─────────────────────────────────────────────┐
     │ A) Email OTP Registration (New Users)       │
     ▼                                             │
┌──────────────────────────────────┐               │
│ 1. User enters email + full name │               │
│ POST /auth/send-email-otp        │               │
│ → Backend sends OTP via email    │               │
└────┬─────────────────────────────┘               │
     │                                             │
     ▼                                             │
┌──────────────────────────────────┐               │
│ 2. User enters 6-digit OTP       │               │
│ POST /auth/verify-email-otp      │               │
│ → Returns verification token     │               │
└────┬─────────────────────────────┘               │
     │                                             │
     ▼                                             │
┌──────────────────────────────────┐               │
│ 3. User enters password          │               │
│ (min 8 chars, 1 uppercase,       │               │
│  1 special character)            │               │
│ POST /auth/complete-registration │               │
│ → Creates Firebase user          │               │
│ → Returns custom Firebase token  │               │
└────┬─────────────────────────────┘               │
     │                                             │
     │    B) Google OAuth (Existing & New)         │
     │         ┌─────────────────────────┐         │
     │         │ signInWithPopup         │         │
     │         │ (GoogleAuthProvider)    │         │
     │         │ → Firebase handles auth │         │
     │         └────┬────────────────────┘         │
     │              │                              │
     │              │  C) Phone OTP (Existing)     │
     │              │  ┌──────────────────────┐    │
     │              │  │ signInWithPhone       │    │
     │              │  │ (Firebase JS SDK)     │    │
     │              │  │ → SMS sent via Firebase│   │
     │              │  │ User enters OTP 6-dig │    │
     │              │  │ confirmResult.confirm │    │
     │              │  └──────┬───────────────┘    │
     │              │         │                    │
     ▼              ▼         ▼                    │
┌──────────────────────────────────────┐           │
│ Firebase returns ID Token            │◄──────────┘
│ (JWT signed by Firebase, ~1hr TTL)   │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ POST /auth/firebase-callback         │
│ (Flask frontend relay)               │
│ { id_token, full_name? }             │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ POST /api/v1/auth/verify-token       │
│ (FastAPI backend)                    │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ firebase-admin SDK verifies token    │
│ Decodes: uid, email, phone, name,    │
│ email_verified, sign_in_provider     │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐      ┌─────────────────────────┐
│ Upsert user in PostgreSQL            │─────►│ Existing by firebase_uid│
│                                      │      │ → update last_login     │
│ Lookup order:                        │      └─────────────────────────┘
│ 1. firebase_uid → found → update     │      ┌─────────────────────────┐
│ 2. email       → found → link uid    │─────►│ Legacy user linked:     │
│                    migration_status  │      │ migration_status =      │
│                    = "migrated"      │      │ "migrated"              │
│ 3. not found   → create new user +  │      └─────────────────────────┘
│                    UserProfile row   │      ┌─────────────────────────┐
│                    migration_status  │─────►│ New user created        │
│                    = "native"        │      │ migration_status =      │
└────┬─────────────────────────────────┘      │ "native"                │
     │                                        └─────────────────────────┘
     ▼
┌──────────────────────────────────────┐
│ Return internal JWT pair             │
│ { access_token (15m),               │
│   refresh_token (7d) }              │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ Flask stores tokens in session       │
│ Redirect → /dashboard                │
└────┬─────────────────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ Complete Profile Setup  │
│ (optional, on /profile) │
│                         │
│ - Category, State, City │
│ - Qualification level   │
│ - Preferred states      │
│ - Org follows           │
│ - Notification prefs    │
└────┬────────────────────┘
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
┌──────────────────────────────────────┐
│ Admin logs in                        │
│ via src/frontend-admin/ (port 8081)  │
│ (role: "admin")                      │
└────┬─────────────────────────────────┘
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
┌──────────────────────────────────────┐
│ OPTIONAL: PDF Auto-Fill              │
│                                      │
│ 📄 Upload PDF notification           │
│ → Click "Extract Data"               │
│ → AI extracts fields (Claude API)    │
│ → Form auto-filled instantly         │
└────┬─────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│ Fill/Review Job Details Form:          │◄──────┐
│ (Manual entry OR review extracted data)│       │
│                                        │       │
│ ┌───────────────────────────────────┐  │       │
│ │ Basic Information                 │  │       │
│ │ - Job Title                       │  │       │
│ │ - Organization                    │  │       │
│ │ - Department                      │  │       │
│ │ - Total Vacancies                 │  │       │
│ │ - Description                     │  │       │
│ └───────────────────────────────────┘  │       │
│                                        │       │
│ ┌───────────────────────────────────┐  │       │
│ │ Eligibility Criteria              │  │       │
│ │ - Minimum Qualification           │  │       │
│ │ - Stream Required                 │  │       │
│ │ - Age Limit (Min/Max)             │  │       │
│ │ - Category-wise Vacancies         │  │       │
│ └───────────────────────────────────┘  │       │
│                                        │       │
│ ┌───────────────────────────────────┐  │       │
│ │ Application Details               │  │       │
│ │ - Application Fee                 │  │       │
│ │ - Application Mode                │  │       │
│ │ - Official Website                │  │       │
│ └───────────────────────────────────┘  │       │
│                                        │       │
│ ┌───────────────────────────────────┐  │       │
│ │ Important Dates                   │  │       │
│ │ - Application Start/End           │  │       │
│ │ - Exam Date                       │  │       │
│ │ - Admit Card Date                 │  │       │
│ │ - Result Date                     │  │       │
│ └───────────────────────────────────┘  │       │
└────┬───────────────────────────────────┘       │
     │                                           │
     ▼                                           │
┌──────────────────────────────────┐             │
│ Submit form                      │             │
│ POST /api/v1/admin/jobs          │             │
└────┬───────────────────────────────┘           │
     │                                           │
     ▼                                           │
┌──────────────────────────────────┐             │
│ 🔒 PERMISSION CHECK              │             │
│ @require_role('admin')           │             │
│ Is user.role == 'admin'?         │             │
└────┬───────────────────────────────┘           │
     │                                           │
     ├─ NO (403 Forbidden) → Return error        │
     │                                           │
     ▼ YES (admin verified)                      │
┌──────────────────────┐                         │
│ Submit form          │                         │
└────┬─────────────────┘                         │
     │                                           │
     ▼                                           │
┌──────────────────────┐      ┌──────────────────┴┐
│ Validate all fields  │─────►│ Error? Show       │
└────┬─────────────────┘      │ validation msg    │
     │                        └───────────────────┘
     │ Valid
     ▼
┌──────────────────────┐
│ Save to PostgreSQL   │
│ (job_vacancies       │
│  table)              │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Create admin log     │
│ entry                │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Trigger Celery Task: │
│ "match_new_job_      │
│  with_users"         │
└────┬─────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ Celery Task Execution:          │
│                                 │
│ 1. Fetch all active users       │
│ 2. For each user:               │
│    ├─► Check profile eligibility│
│    ├─► Check preferences match  │
│    └─► Calculate match score    │
│ 3. If eligible & preferences    │
│    match:                       │
│    └─► Create notification      │
└────┬────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│ Send notifications   │
│ to matched users via │
│ smart_notify (5ch):  │
│ - In-app             │
│ - Push (FCM)         │
│ - Email (T+15min)    │
│ - Telegram (T+15min) │
│ - WhatsApp (T+1hr)   │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Job successfully     │
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
     ┌────────────────────────────────┐
     │  FOR EACH USER:                │
     │  ┌──────────────────────────┐  │
     │  │ Fetch User Profile       │  │
     │  └────────────┬─────────────┘  │
     │               │                │
     │               ▼                │
     │  ┌──────────────────────────┐  │
     │  │ Check Education          │  │
     │  │ Eligibility              │  │
     │  └────────────┬─────────────┘  │
     │               │                │
     │       ┌───────┴───────┐        │
     │       │               │        │
     │       ▼               ▼        │
     │   ┌────────┐     ┌────────┐    │
     │   │  Not   │     │Eligible│    │
     │   │Eligible│     └───┬────┘    │
     │   └───┬────┘         │         │
     │       │              ▼         │
     │       │  ┌──────────────────┐  │
     │       │  │ Check Stream     │  │
     │       │  │ (if required)    │  │
     │       │  └────────┬─────────┘  │
     │       │           │            │
     │       │    ┌──────┴──────┐     │
     │       │    │             │     │
     │       │    ▼             ▼     │
     │       │ ┌──────┐     ┌──────┐  │
     │       │ │  No  │     │Match!│  │
     │       │ │Match │     └──┬───┘  │
     │       │ └──┬───┘        │      │
     │       │    │            ▼      │
     │       │    │ ┌────────────────┐│
     │       │    │ │ Check Age      ││
     │       │    │ │ Eligibility    ││
     │       │    │ └────────┬───────┘│
     │       │    │          │        │
     │       │    │   ┌──────┴──────┐ │
     │       │    │   │             │ │
     │       │    │   ▼             ▼ │
     │       │    │┌──────┐     ┌──────┐
     │       │    ││  No  │     │Elig- │
     │       │    ││Match │     │ible  │
     │       │    │└──┬───┘     └──┬───┘
     │       │    │   │            │  │
     │       │    │   │            ▼  │
     │       │    │   │ ┌────────────────┐
     │       │    │   │ │ Check Category │
     │       │    │   │ │ Vacancies      │
     │       │    │   │ └────────┬───────┘
     │       │    │   │          │
     │       │    │   │   ┌──────┴──────┐
     │       │    │   │   │             │
     │       │    │   │   ▼             ▼
     │       │    │   │┌───────┐    ┌─────────┐
     │       │    │   ││  No   │    │Available│
     │       │    │   ││Vacancy│    └────┬────┘
     │       │    │   │└───┬───┘         │
     │       │    │   │    │             ▼
     │  (Any Failure Merges Here)        │
     │       ▼    ▼   ▼    ▼             │
     │       └────┴───┴────┘             │
     │             │                     │
     │             │      ┌────────────────────┐
     │             │      │ Check User         │
     │             │      │ Notification       │
     │             │      │ Preferences        │
     │             │      └─────────┬──────────┘
     │             │                │
     │             │       ┌────────┴────────┐
     │             │       │                 │
     │             │       ▼                 ▼
     │             │  ┌────────┐         ┌──────┐
     │             │  │Doesn't │         │Match!│
     │             │  │Match   │         └──┬───┘
     │             │  └───┬────┘            │
     │             │      │                 ▼
     │             │      │      ┌────────────────┐
     │             │      │      │ Calculate      │
     │             │      │      │ Match Score    │
     │             │      │      └────────┬───────┘
     │             │      │               │
     │             │      │               ▼
     │             │      │      ┌────────────────┐
     │             │      │      │ Create         │
     │             │      │      │ Notification   │
     │             │      │      │ Record in DB   │
     │             │      │      └────────┬───────┘
     │             │      │               │
     │             └──────┴───────────────┴────────
     │                            │
     └────────────────────────────┼───────────┐
                                  │           │
                      ┌───────────┘           │
                      │                       │
                      │                       │ Skip
                      ▼                       │
            ┌──────────────────┐              │
            │ Queue Notif      │              │
            │ for Sending      │              │
            └─────────┬────────┘              │
                      │                       │
                      ▼                       │
          ┌───────────────────────┐           │
          │ Check User Prefs:     │           │
          │ - Email enabled?      │           │
          │ - Push enabled?       │           │
          │ - Telegram enabled?   │           │
          │ - WhatsApp enabled?   │           │
          └───────────┬───────────┘           │
                      │                       │
                      ▼                       │
            ┌──────────────────┐              │
            │ smart_notify     │              │
            │ (staggered):     │              │
            │                  │              │
            │ ┌──────────────┐ │              │
            │ │ In-app (T+0) │ │              │
            │ └──────────────┘ │              │
            │ ┌──────────────┐ │              │
            │ │ Push (T+0)   │ │              │
            │ └──────────────┘ │              │
            │ ┌──────────────┐ │              │
            │ │ Email +15min │ │              │
            │ └──────────────┘ │              │
            │ ┌──────────────┐ │              │
            │ │ Telegram+15m │ │              │
            │ └──────────────┘ │              │
            │ ┌──────────────┐ │              │
            │ │ WhatsApp +1h │ │              │
            │ └──────────────┘ │              │
            └─────────┬────────┘              │
                      │                       │
                      ▼                       │
            ┌──────────────────┐              │
            │ Update           │              │
            │ notification     │              │
            │ status as "sent" │              │
            └─────────┬────────┘              │
                      │                       │
                      └───────────────────────┘
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
┌────────────────────────────────────┐
│ User browses jobs                  │
│ (Dashboard/Search)                 │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ Click on job to view               │◄────────┐
│ full details                       │         │
└────┬───────────────────────────────┘         │
     │                                         │
     ▼                                         │
┌────────────────────────────────────┐         │
│ Job Details Page Shows:            │         │
│ - Job Title & Organization         │         │
│ - Eligibility Criteria             │         │
│ - Important Dates                  │         │
│ - Application Fee                  │         │
│ - Selection Process                │         │
│ - Official Website Link            │         │
│                                    │         │
│ ┌────────────────────────────────┐ │         │
│ │ [Apply Now] [Add to Tracker]   │ │         │
│ │ [Mark as Priority]             │ │         │
│ └────────────────────────────────┘ │         │
└────┬───────────────────────────────┘         │
     │                                         │
     ▼                                         │
┌──────────────────────┐                       │
│ User clicks          │                       │
│ "Add to Tracker"     │                       │
└────┬─────────────────┘                       │
     │                                         │
     ▼                                         │
┌──────────────────────┐                       │
│ Check if already     │                       │
│ tracked              │                       │
└────┬─────────────────┘                       │
     │                                         │
     ▼                                         │
┌──────────────────────┐      ┌────────────────┴┐
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
┌────────────────────────────────────┐
│ Create application                 │
│ record in DB                       │
│ (User Job Applications)            │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ Generate reminder                  │
│ entries based on                   │
│ job important dates                │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ If marked as                       │
│ priority, set                      │
│ priority flag                      │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ Show success message               │
│ "Added to your                     │
│  application tracker"              │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ User navigates to                  │
│ "My Applications"                  │
└────┬───────────────────────────────┘
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
┌────────────────────────────────────┐
│ Background Process:                │
│ Celery checks                      │
│ reminders daily                    │
└────┬───────────────────────────────┘
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
┌────────────────────────────────────┐
│ User receives notifications via    │
│ smart_notify (up to 5 channels):   │
│ in-app, push, email, Telegram,     │
│ WhatsApp (based on preferences)    │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────┐
│   END   │
└─────────┘
```

## 6. Priority Job Update Notification Flow

```
┌─────────────────────────────────┐
│ Trigger: Admin updates a job    │
│ (dates, status)                 │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Save updated job to database    │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Trigger Celery Task:            │
│ notify_priority_subscribers     │
│ → smart_notify per user         │
│   (staggered, priority=high)    │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Find all users who marked this  │
│ job as priority                 │
└───────────────┬─────────────────┘
                │
                ▼
     ┌────────────────────────────────┐
     │  FOR EACH USER:                │
     │                                │
     │  ┌──────────────────────────┐  │
     │  │ Get user's notification  │  │
     │  │ preferences              │  │
     │  └────────────┬─────────────┘  │
     │               │                │
     │               ▼                │
     │  ┌──────────────────────────┐  │
     │  │ Determine what changed:  │  │
     │  │ - Application date?      │  │
     │  │ - Exam date?             │  │
     │  │ - Admit card date?       │  │
     │  │ - Result date?           │  │
     │  │ - Job cancelled?         │  │
     │  └────────────┬─────────────┘  │
     │               │                │
     │               ▼                │
     │  ┌──────────────────────────┐  │
     │  │ Create notification      │  │
     │  │ with update details      │  │
     │  └────────────┬─────────────┘  │
     │               │                │
     │               ▼                │
     │  ┌──────────────────────────┐  │
     │  │ Set priority: HIGH       │  │
     │  │ Route to: HIGH queue     │  │
     │  └────────────┬─────────────┘  │
     │               │                │
     │               ▼                │
     │  ┌──────────────────────────┐  │
     │  │ smart_notify (instant):  │  │
     │  │ in-app + push + email +  │  │
     │  │ Telegram + WhatsApp T+0  │  │
     │  │ (based on user prefs)    │  │
     │  └────────────┬─────────────┘  │
     │               │                │
     │               ▼                │
     │  ┌──────────────────────────┐  │
     │  │ Delivery logged per      │  │
     │  │ channel in               │  │
     │  │ notification_delivery_log│  │
     │  └──────┬────────────┬──────┘  │
     │         │            │         │
     │  Fail   ▼            ▼ OK      │
     │   ┌───────────┐  ┌──────────┐  │
     │   │ Logged as │  │ Continue │  │
     │   │ 'failed'  │  └────┬─────┘  │
     │   │ in log    │       │        │
     │   └─────┬─────┘       │        │
     │         │             │        │
     │         ▼             ▼        │
     │  ┌──────────────────────────┐  │
     │  │ Update user's            │  │
     │  │ application record       │  │
     │  │ with new dates           │  │
     │  └──────────────────────────┘  │
     │                                │
     └────────────────────────────────┘
                │
                ▼
       ┌───────────────────┐
       │        END        │
       └───────────────────┘
```

## 7. Admin Dashboard Workflow

```
┌──────────────────────────────────────┐
│ Admin Login                          │
│ src/frontend-admin/ (port 8081)      │
│ http://localhost:8081/auth/login     │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────┐
│                  ADMIN DASHBOARD                   │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Statistics Cards:                            │  │
│  │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │  │
│  │ │ Total  │ │ Active │ │  Total │ │  New   │  │  │
│  │ │ Users  │ │  Jobs  │ │  Apps  │ │ Users  │  │  │
│  │ │ 10,547 │ │   234  │ │ 45,231 │ │  +127  │  │  │
│  │ └────────┘ └────────┘ └────────┘ └────────┘  │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Quick Actions:                               │  │
│  │ [+ Add New Job]  [View Users]  [Analytics]   │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Recent Activity:                             │  │
│  │ • New user registration: john@example.com    │  │
│  │ • Job application: SSC CGL by 25 users       │  │
│  │ • Job updated: Railway ALP dates changed     │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Popular Jobs (Most Applied):                 │  │
│  │ 1. SSC CGL - 5,234 applications              │  │
│  │ 2. Railway ALP - 4,892 applications          │  │
│  │ 3. UPSC CSE - 3,456 applications             │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────┬─────────────────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
     ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│   Job    │  │   User   │  │Analytics │
│Management│  │Management│  │    &     │
│          │  │          │  │ Reports  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────┐
│                                                    │
│  JOB MANAGEMENT:          USER MANAGEMENT:         │
│  • Create Job             • View All Users         │
│  • Edit Job               • User Details           │
│  • Delete Job             • Suspend/Activate       │
│  • Job Status             • Change Roles           │
│                                                    │
│  ANALYTICS:                                        │
│  • User Demographics                               │
│  • Application Trends                              │
│  • Popular Organizations                           │
│  • Notification Stats                              │
│                                                    │
└────────────────────────────────────────────────────┘
```

## 8. Database Operations Flow

```
┌───────────────────────────────────────────────────────────────────┐
│                        POSTGRESQL TABLES                          │
└───────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│           Admin Users           │      │             Users               │
│  - id (Primary Key, UUID)       │      │  - id (Primary Key, UUID)       │
│  - email, password_hash         │      │  - email, password_hash         │
│  - role (admin/operator)        │      │  - status                       │
└───────────────┬─────────────────┘      └───────────────┬─────────────────┘
                │                                        │
                │ (One-to-Many)                          │ (One-to-One)
                │                                        │
┌───────────────▼─────────────────┐      ┌───────────────▼─────────────────┐
│          Admin Logs             │      │         User Profiles           │
│  - id                           │      │  - id (Primary Key, UUID)       │
│  - admin_id (FK)                │      │  - user_id (Foreign Key)        │
│  - action, resource_id          │      │  - personal_info, education     │
└─────────────────────────────────┘      └───────────────┬─────────────────┘
                                                         │
                                         ┌───────────────┼─────────────────┐
                                         │               │                 │
                         ┌───────────────▼───────┐ ┌─────▼─────────┐ ┌─────▼───────────────┐
                         │      User Devices     │ │ Notifications │ │User Job Applications│
                         │  - id                 │ │  - id         │ │  - id               │
                         │  - user_id (FK)       │ │  - user_id    │ │  - user_id (FK)     │
                         │  - fcm_token          │ │  - message    │ │  - job_id (FK)      │
                         └───────────────┬───────┘ └─────┬─────────┘ └─────┬───────────────┘
                                         │               │                 │
                                         │               ▼                 │
                                         │ ┌─────────────────────────┐     │
                                         └─►Notification Delivery Log│     │
                                           │  - id                   │     │
                                           │  - notification_id (FK) │     │
                                           │  - channel, status      │     │
                                           └─────────────────────────┘     │
                                                                           │
                                                                 ┌─────────▼───────────────┐
                                                                 │      Job Vacancies      │
                                                                 │  - id (PK, UUID)        │
                                                                 │  - job_title, org       │
                                                                 │  - eligibility        │
                                                                 │  - important_dates    │
                                                                 └─────────┬───────────────┘
                                                                           │
                                                                           │ (Tracked By)
                                                                           │
                                                                 ┌─────────▼───────────────┐
                                                                 │   Target Organizations  │
                                                                 │   (In User Preferences) │
                                                                 └─────────────────────────┘

INDEXES FOR PERFORMANCE:
════════════════════════

Users & Admin Users:
  - email (unique)
  - role (Admin Users)

User Profiles:
  - user_id (unique)
  - education.highest_qualification
  - personal_info.category

Job Vacancies:
  - organization
  - eligibility.min_qualification
  - status, created_at

User Job Applications:
  - user_id + job_id (compound, unique)
  - user_id + is_priority

Notifications & Devices:
  - user_id + is_read (Notifications)
  - notification_id (Delivery Log)
  - fcm_token (unique, User Devices)
  - user_id + device_fingerprint (User Devices)
```

## 9. Celery Task Scheduler Flow

```
┌──────────────────────────────────────────────────┐
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

1. app.tasks.notifications.send_deadline_reminders
   Run: Every day at 08:00 UTC
   Priority: HIGH
   Purpose: Send application deadline reminders

2. app.tasks.cleanup.purge_expired_notifications
   Run: Every day at 01:00 UTC
   Priority: LOW
   Purpose: Archive old notifications (TTL enforcement)
   Retry: 1x

3. app.tasks.cleanup.purge_expired_admin_logs
   Run: Every day at 01:30 UTC
   Priority: LOW
   Purpose: Delete expired admin logs (TTL enforcement)
   Retry: 1x

4. app.tasks.cleanup.purge_soft_deleted_jobs
   Run: Every day at 02:00 UTC
   Priority: LOW
   Purpose: Permanently delete soft-deleted jobs
   Retry: 1x

5. app.tasks.jobs.close_expired_job_listings
   Run: Every day at 02:30 UTC
   Priority: MEDIUM
   Purpose: Close job listings that have passed their deadline
   Retry: 3x

6. app.tasks.seo.generate_sitemap
   Run: Every day at 04:00 UTC
   Priority: LOW
   Purpose: Generate updated sitemap for SEO
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
✅ PUT    /api/v1/admin/jobs/<id>         Update job (limited fields)
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

❌ POST   /api/v1/admin/jobs              (Admin only) 403
❌ DELETE /api/v1/admin/jobs/<id>         (Admin only) 403
❌ GET    /api/v1/admin/users             (Admin only) 403
❌ PUT    /api/v1/admin/users/<id>/role   (Admin only) 403
❌ GET    /api/v1/admin/analytics         (Admin only) 403

ADMIN ROLE (👨‍💼) - Full Control
──────────────────────────────────
✅ GET    /api/v1/jobs                    View all jobs
✅ GET    /api/v1/jobs/<id>               View job details
✅ POST   /api/v1/admin/jobs              Create job
✅ PUT    /api/v1/admin/jobs/<id>         Update job (all fields)
✅ DELETE /api/v1/admin/jobs/<id>         Delete job

✅ GET    /api/v1/users/profile           View own profile
✅ PUT    /api/v1/users/profile           Update own profile
✅ GET    /api/v1/admin/users             List all users
✅ GET    /api/v1/admin/users/<id>        View user details
✅ PUT    /api/v1/admin/users/<id>/role   Change user role (audit logged)
✅ PUT    /api/v1/admin/users/<id>/status Suspend/activate user

✅ GET    /api/v1/admin/analytics         View analytics
✅ GET    /api/v1/admin/logs              View activity logs
✅ GET    /api/v1/admin/jobs              List all jobs (admin panel)
✅ POST   /api/v1/auth/refresh            Refresh access token

Rate Limits:
  - API: 1000 requests/min per user
  - Login: 5 attempts/min

All admin actions are logged in admin_logs table
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

---

## 13. Entrance Exam Data Model

Entrance exams (NEET, JEE, CLAT, CAT, GATE, CUET etc.) are stored in a
separate `entrance_exams` table, distinct from `job_vacancies`. The three
document tables (`job_admit_cards`, `job_answer_keys`, `job_results`) are
**polymorphic** — each row links to either a job or an entrance exam.

```
┌──────────────────────────────────────────────────────────────────────────┐
│              ENTRANCE EXAM DATA MODEL                                    │
└──────────────────────────────────────────────────────────────────────────┘

  WHY SEPARATE?
  ─────────────
  job_vacancies fields          entrance_exams fields
  ─────────────────────         ─────────────────────────────
  total_vacancies        ≠      seats_info (seats by college)
  salary_initial/max     ≠      (no salary — it's education)
  employment_type        ≠      exam_type (ug/pg/doctoral)
  qualification_level    ≠      stream (medical/engineering/law)
  organization/dept      ≠      conducting_body + counselling_body
  application tracking   ≠      seat allotment via counselling

  TABLE STRUCTURE:
  ─────────────────

  ┌──────────────────────────┐         ┌──────────────────────────────┐
  │     job_vacancies        │         │       entrance_exams         │
  │  (Government Jobs)       │         │  (NEET/JEE/CLAT/CAT/GATE)   │
  │                          │         │                              │
  │  id UUID PK              │         │  id UUID PK                  │
  │  job_title               │         │  exam_name                   │
  │  organization            │         │  conducting_body             │
  │  total_vacancies         │         │  counselling_body            │
  │  salary_initial/max      │         │  exam_type (ug/pg/doctoral)  │
  │  employment_type         │         │  stream (medical/engg/law)   │
  │  qualification_level     │         │  eligibility JSONB           │
  │  vacancy_breakdown JSONB │         │  exam_details JSONB          │
  │  job_type (latest_job/   │         │  selection_process JSONB     │
  │    admit_card/answer_key/│         │  seats_info JSONB            │
  │    result)               │         │  fee_* (5 columns)           │
  │  fee_* (5 columns)       │         │  status (upcoming/active/    │
  │  search_vector GENERATED │         │    completed/cancelled)      │
  └──────────┬───────────────┘         │  search_vector GENERATED     │
             │                         └─────────────┬────────────────┘
             │                                       │
             │          POLYMORPHIC DOCUMENT TABLES  │
             │          ────────────────────────────  │
             │                                       │
             │  job_id FK (nullable) ─────────────┐  │
             │                                   ▼  │
             │                          ┌──────────────────┐
             └──────────────────────── ▶│  job_admit_cards │
                                         │                  │
  exam_id FK (nullable) ──────────────▶ │  id UUID PK      │
                                         │  job_id  UUID?   │ ◀── CHECK:
                                         │  exam_id UUID?   │     (job_id IS NOT NULL
                                         │  phase_number    │      AND exam_id IS NULL)
                                         │  title           │     OR
                                         │  download_url    │     (job_id IS NULL
                                         │  valid_from/until│      AND exam_id IS NOT NULL)
                                         │  notes           │
                                         └──────────────────┘

  Same polymorphic pattern applies to:
    • job_answer_keys  (job_id XOR exam_id + phase docs)
    • job_results      (job_id XOR exam_id + cutoff_marks JSONB)

  SEEDED DATA (current):
  ──────────────────────
  job_vacancies:  10 jobs + 9 admit card posts + 9 answer key posts + 9 result posts
  entrance_exams: 9 exams
    • NEET PG 2026 (medical, pg)     → 3 phase docs (admit card + answer key + result)
    • NEET UG 2026 (medical, ug)     → 4 phase docs
    • JEE Main 2026 (engineering)    → 7 phase docs (2 sessions, each with docs)
    • JEE Advanced 2026 (engg, ug)   → 3 phase docs
    • CLAT 2026 (law, ug)            → 3 phase docs
    • CAT 2025 (management, pg)      → 3 phase docs
    • CUET UG 2026 (general, ug)     → 4 phase docs
    • NEET SS 2025 (medical, doctoral)→3 phase docs
    • GATE 2026 (engineering, pg)    → 3 phase docs
  Total: 32 phase documents seeded via exam_id FK
```

---

## 14. 5-Section Frontend Navigation

The user frontend is divided into 5 content sections, each with its own
listing page, gradient hero colour, and detail page design.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  5-SECTION FRONTEND NAVIGATION                           │
└──────────────────────────────────────────────────────────────────────────┘

  SECTION NAV STRIP (shown on all pages):
  ─────────────────────────────────────────
  ┌───────────┬─────────────┬──────────────┬───────────┬──────────────┐
  │ 💼 Jobs   │ 📄 Admit    │ ✏️ Answer    │ 🏆 Results│ 🎓 Entrance  │
  │     /     │  Cards      │   Keys       │ /results  │    Exams     │
  │           │/admit-cards │/answer-keys  │           │/entrance-    │
  │           │             │              │           │  exams       │
  └───────────┴─────────────┴──────────────┴───────────┴──────────────┘
  Active section highlighted with white border-bottom + white text

  HERO COLOUR CODING (each section has a matching gradient):
  ──────────────────────────────────────────────────────────
  Section       URL              Hero Gradient         DB Source
  ──────────    ───────────────  ──────────────────    ──────────────────
  Jobs          /                Navy → Blue            job_vacancies (latest_job)
  Admit Cards   /admit-cards     Blue → Sky Blue        job_vacancies (admit_card)
  Answer Keys   /answer-keys     Brown → Amber          job_vacancies (answer_key)
  Results       /results         Dark Green → Green     job_vacancies (result)
  Entrance Exams /entrance-exams  Dark Purple → Purple   entrance_exams

  JOB CARD LEFT ACCENT (list pages):
  ────────────────────────────────────
  job_type=latest_job  → purple left border  (.card-latest)
  job_type=admit_card  → blue left border    (.card-admit)
  job_type=answer_key  → amber left border   (.card-answer)
  job_type=result      → green left border   (.card-result)
  entrance_exam        → purple left border  (admission card)

  DETAIL PAGE FLOW:
  ─────────────────
  User clicks job card                  User clicks entrance exam card
        │                                       │
        ▼                                       ▼
  GET /jobs/<slug>                       GET /entrance-exams/<slug>
        │                                       │
        ▼                                       ▼
  Flask renders job_detail.html          Flask renders entrance_exam_detail.html
  (type-aware hero: hero-job /           (hero-admission: purple gradient)
   hero-admit / hero-answer /
   hero-result)
        │                                       │
        ▼                                       ▼
  Doc tabs section shown                 Doc tabs section shown
  if job_type == 'latest_job'            (always shown for exams)
        │                                       │
        ▼                                       ▼
  HTMX loads /partials/jobs/             HTMX loads /partials/exams/
  {job_id}/admit-cards                   {exam_id}/admit-cards
  (on tab click)                         (on tab click)
```

---

## 15. HTMX Phase Document Tab Flow

Phase documents (admit cards, answer keys, results) are loaded on-demand
via HTMX into tabbed panels on job and admission detail pages.

```
┌──────────────────────────────────────────────────────────────────────────┐
│               HTMX PHASE DOCUMENT TAB FLOW                               │
└──────────────────────────────────────────────────────────────────────────┘

  TEMPLATE STRUCTURE (Alpine.js x-data controls active tab):
  ──────────────────────────────────────────────────────────

  <div x-data="{tab:'admit_cards'}">                 ← Alpine state
    <div class="doc-tabs-bar">
      <button @click="tab='admit_cards'"             ← Tab 1
              :class="{'active':tab==='admit_cards'}">
        📄 Admit Cards
      </button>
      <button @click="tab='answer_keys'">✏️ Answer Keys</button>
      <button @click="tab='results'">🏆 Results</button>
    </div>

    <!-- Panels are OUTSIDE the tab bar, INSIDE the x-data wrapper -->

    <div x-show="tab==='admit_cards'"                ← Panel 1
         hx-get="/partials/jobs/{id}/admit-cards"    ← HTMX endpoint
         hx-trigger="load"                           ← Load immediately
         hx-swap="innerHTML">
      Loading…
    </div>
    <div x-show="tab==='answer_keys'" x-cloak        ← Panel 2 (hidden initially)
         hx-get="/partials/jobs/{id}/answer-keys"
         hx-trigger="intersect once"                 ← Lazy load on intersection
         hx-swap="innerHTML">
      Loading…
    </div>
    <div x-show="tab==='results'" x-cloak
         hx-get="/partials/jobs/{id}/results"
         hx-trigger="intersect once"
         hx-swap="innerHTML">
      Loading…
    </div>
  </div>

  REQUEST FLOW:
  ─────────────
  Browser loads job_detail page
        │
        ▼
  Alpine.js initialises: tab = 'admit_cards'
        │
        ▼
  HTMX fires GET /partials/jobs/{id}/admit-cards   ← hx-trigger="load"
        │
        ▼
  Flask route: partials_admit_cards(job_id)
        │
        ▼
  Calls Backend API: GET /api/v1/jobs/{id}/admit-cards
        │
        ▼
  FastAPI queries job_admit_cards WHERE job_id={id}
        │                 OR
                    WHERE exam_id={id}  ← for entrance_exam_detail.html
        │
        ▼
  Returns list of admit card rows (JSON)
        │
        ▼
  Flask renders _admit_cards_panel.html partial
        │
        ▼
  HTMX swaps innerHTML of the admit_cards panel div

  USER CLICKS "Answer Keys" TAB:
  ────────────────────────────────
  @click sets tab = 'answer_keys'
        │
        ▼
  Alpine.js hides admit_cards panel (x-show=false)
  Alpine.js shows answer_keys panel (x-show=true)
        │
        ▼
  HTMX fires GET /partials/jobs/{id}/answer-keys   ← hx-trigger="intersect once"
  (fires only once — result cached in DOM)
        │
        ▼
  Renders _answer_keys_panel.html
    ├── Phase N pill (amber)
    ├── Provisional / ✓ Final badge
    ├── Per-file download buttons (amber)
    └── Raise Objection button (if objection_url set)

  PANEL CARD TYPES:
  ──────────────────
  _admit_cards_panel.html   → .doc-card-admit   (blue bg)
  _answer_keys_panel.html   → .doc-card-answer  (amber bg)
  _results_panel.html       → .doc-card-result  (green bg)

  Each panel uses shared CSS classes from base.html:
    .doc-card, .doc-card-body, .doc-card-actions
    .doc-phase-pill (.phase-blue / .phase-amber / .phase-green)
    .doc-title, .doc-meta, .doc-note, .doc-deadline
    .doc-btn (.doc-btn-blue / .doc-btn-amber / .doc-btn-green / .doc-btn-outline)
    .doc-cutoff + .doc-cutoff-row  ← for results cutoff marks table
    .doc-empty                     ← empty state text
```

---

*These diagrams cover the major flows in Hermes: system architecture,
user registration, job creation, matching & notifications, application
tracking, priority job updates, admin dashboard, database schema,
Celery task scheduling, user journey map, RBAC enforcement, JWT token
lifecycle, entrance exam data model, 5-section frontend navigation,
and HTMX phase document tab loading.*
