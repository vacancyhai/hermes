# Hermes — Diagrams

## 1. System Architecture

All services run from a single root `docker-compose.yml`. They communicate via HTTP REST API.

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
│  Public users:      │  │  Staff only:        │  │  4. hermes-worker      │
│  - Register         │  │  - Admin login      │  │  5. hermes-scheduler   │
│  - Login            │  │  - Operator login   │  │  JWT Auth + RBAC       │
│  - Browse jobs      │  │  - Manage jobs      │  │  /api/v1/* endpoints   │
│                     │  │  - Manage users     │  │                        │
│  Calls backend via  │  │                     │  │  Persistent storage:   │
│  BACKEND_API_URL    │  │  Calls backend via  │  │  PostgreSQL + Redis    │
│                     │  │  BACKEND_API_URL    │  │  AOF persistence       │
│  Network:           │  │                     │  └──────────┬─────────────┘
│  hermes_network     │  │  Network:           │             │
│                     │  │  hermes_network     │             ▼
└─────────────────────┘  │                     │  ┌──────────────────────┐
                         │  Firewall port 8081 │  │  External Services   │
                         │  from public        │  │  - OCI Email Delivery│
                         │  internet!          │  │  - Firebase FCM      │
                         └─────────────────────┘  └──────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  All services defined in root docker-compose.yml. Single hermes_network.     │
└──────────────────────────────────────────────────────────────────────────────┘

Architecture properties:
- Three services: User Frontend (8080), Admin Frontend (8081), Backend (8000)
- All share one Docker network (hermes_network) defined in root docker-compose.yml
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
│ Is user.role = admin   │
│ or operator?           │
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
│ │ - Admission Date                  │  │       │
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
│ @require_operator                │             │
│ Is user.role == 'admin'          │             │
│ or 'operator'?                   │             │
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
│ (`jobs` table)       │
│                      │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Create admin log     │
│ entry                │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ If status == 'active':           │
│ Trigger Celery Task:             │
│ notify_watchers_on_update        │
│ (entity_type='job', entity_id)   │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Celery Task Execution:           │
│                                  │
│ 1. Find all user_watches rows    │
│    WHERE entity_type='job'       │
│    AND entity_id=job.id          │
│ 2. For each watcher:             │
│    └─► smart_notify(staggered)   │
└────┬─────────────────────────────┘
     │
     ▼
┌──────────────────────┐
│ Send notifications   │
│ to watchers via      │
│ smart_notify (5ch):  │
│ - In-app (T+0)       │
│ - Push (T+0)         │
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

## 4. Deadline Reminder & Watcher Notification Flow

```
┌─────────────────────┐
│ Trigger: Daily Beat  │
│ Task at 08:00 UTC    │
│ OR: Job/Admission updated │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Fetch Job Details   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Fetch user_watches  │
│ WHERE entity_type=  │
│ 'job' or 'admission'│
└─────────┬───────────┘
          │
          ▼
     ┌────────────────────────────────┐
     │  FOR EACH WATCHER:             │
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

## 5. Watch Job / Admission Flow

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌────────────────────────────────────┐
│ User views job or admission detail page │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ Click [Watch] button               │
│ POST /api/v1/jobs/{id}/watch       │
│   OR                               │
│ POST /api/v1/admissions/       │
│      {id}/watch                    │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────┐      ┌─────────────────┐
│ Already watching?    │─────►│ 200: "Already   │
└────┬─────────────────┘ YES  │  watching"      │
     │                        └─────────────────┘
     │ NO
     ▼
┌──────────────────────┐      ┌─────────────────┐
│ Watch count ≥ 100?   │─────►│ 400: max 100    │
└────┬─────────────────┘ YES  │  watches allowed│
     │                        └─────────────────┘
     │ NO
     ▼
┌────────────────────────────────────┐
│ Insert user_watches row:           │
│ { user_id, entity_type, entity_id} │
│ UNIQUE(user_id, entity_type,       │
│        entity_id) enforced in DB   │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ 200: { watching: true,             │
│       message: "Now watching" }    │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ Daily Beat Task (08:00 UTC):       │
│ send_deadline_reminders finds      │
│ all watches where entity's         │
│ application_end is in T-7/T-3/T-1 │
│ → smart_notify(staggered) per user │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ User receives notification via     │
│ smart_notify (5 channels):         │
│ in-app (T+0), push (T+0),          │
│ email (T+15min), Telegram (T+15m), │
│ WhatsApp (T+1hr) — per prefs      │
└────┬───────────────────────────────┘
     │
     ▼
┌─────────┐
│   END   │
└─────────┘
```

## 6. Watcher Update Notification Flow

┌─────────────────────────────────┐
│ Trigger: Admin approves or     │
│ updates a job/admission             │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Save updated job/admission to DB     │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Trigger Celery Task:            │
│ notify_watchers_on_update       │
│ (entity_type, entity_id)        │
│ → smart_notify(staggered) per   │
│   user who watches this entity  │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Find all user_watches rows      │
│ WHERE entity_type AND entity_id │
│ match the updated job/admission      │
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
     │  │ Build notification:       │  │
     │  │ type='watched_item_       │  │
     │  │       updated'            │  │
     │  │ title = job/admission title    │  │
     │  │ action_url = detail page │  │
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
     │  │ Log delivery per channel  │  │
     │  │ in notification_delivery  │  │
     │  │ _log table                │  │
     │  └──────────────────────────┘  │
     │                                │
     └────────────────────────────────┘
                │
                ▼
       ┌───────────────────┐
       │        END        │
       └───────────────────┘

## 7. Admin Dashboard Workflow

┌───────────────────────────────────────────────────────────────────┐
│                        POSTGRESQL TABLES                          │
└───────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│           admin_users           │      │             users               │
│  - id UUID PK                   │      │  - id UUID PK                   │
│  - email, password_hash         │      │  - firebase_uid (unique)        │
│  - role (admin/operator)        │      │  - email, full_name             │
│  - is_active                    │      │  - is_active                    │
└───────────────┬─────────────────┘      └───────────────┬─────────────────┘
                │                                        │
                │ (One-to-Many)                          │ (One-to-One)
                │                                        │
┌───────────────▼─────────────────┐      ┌───────────────▼─────────────────┐
│          admin_logs             │      │         user_profiles           │
│  - id UUID PK                   │      │  - id UUID PK                   │
│  - admin_id FK                  │      │  - user_id FK (unique)          │
│  - action, target_type/id       │      │  - personal_info JSONB          │
│  - expires_at (30 day TTL)      │      │  - education JSONB              │
└─────────────────────────────────┘      │  - followed_orgs JSONB          │
                                         └───────────────┬─────────────────┘
                                                         │
                                         ┌───────────────┼─────────────────┐
                                         │               │                 │
                         ┌───────────────▼───────┐ ┌─────▼─────────┐ ┌─────▼──────────┐
                         │      user_devices     │ │ notifications │ │  user_watches  │
                         │  - id UUID PK         │ │  - id UUID PK │ │  - id UUID PK  │
                         │  - user_id FK         │ │  - user_id FK │ │  - user_id FK  │
                         │  - fcm_token          │ │  - title, body│ │  - entity_type │
                         │  - device_fingerprint │ │  - is_read    │ │  - entity_id   │
                         └───────────────┬───────┘ └─────┬─────────┘ └────────────────┘
                                         │               │                              ▲
                                         │               ▼                              │
                                         │ ┌─────────────────────────┐    ┌─────────────┴──────┐
                                         └─►notif_delivery_log       │    │       jobs         │
                                           │  - id UUID PK           │    │  - id UUID PK      │
                                           │  - notification_id FK   │    │  - job_title, org  │
                                           │  - channel, status      │    │  - eligibility     │
                                           └─────────────────────────┘    │  - application_end │
                                                                          └────────────────────┘
                                                                                    │
                                                                          ┌─────────▼──────────┐
                                                                          │   admissions   │
                                                                          │  - id UUID PK      │
                                                                          │  - admission_name       │
                                                                          │  - conducting_body │
                                                                          │  - status          │
                                                                          └────────────────────┘

INDEXES FOR PERFORMANCE:
════════════════════════

users & admin_users:
  - email (unique)
  - firebase_uid (unique, users only)
  - role (admin_users)

user_profiles:
  - user_id (unique FK)

jobs:
  - organization
  - status, created_at
  - search_vector GIN (full-text)
  - slug (unique)

admissions:
  - status, admission_date
  - search_vector GIN (full-text)
  - slug (unique)

user_watches:
  - UNIQUE(user_id, entity_type, entity_id)

Notifications & Devices:
  - user_id + is_read (notifications)
  - notification_id (notif_delivery_log)
  - fcm_token (unique, user_devices)
  - user_id + device_fingerprint (user_devices)
```

## 8. Celery Task Scheduler Flow

```
┌──────────────────────────────────────────────────┐
│              hermes-scheduler (Beat)               │
│            (Background Tasks Runner)               │
└────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│                  DAILY BEAT TASKS                │
│              (from celery_app.py beat_schedule)  │
└──────────┬───────────────────────────────┘
                   │
                  │
                  ▼
         ┌────────────────┐
         │  REDIS QUEUE   │
         │   (Broker)     │
         └────────┬───────┘
                  │
                  ┌───┬───┐
                  │       │
              ┌───▼───┐ ┌─▼─────┐
              │Worker │ │Worker │
              │  1    │ │  2    │
              └───┬───┘ └───┬───┘
                  └────┬────┘
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

SCHEDULED TASKS (beat_schedule in celery_app.py):
══════════════════════════════════════════════════

1. app.tasks.notifications.send_deadline_reminders
   Run: Daily 08:00 UTC
   Purpose: T-7, T-3, T-1 reminders for all user_watches watchers

2. app.tasks.cleanup.purge_expired_notifications
   Run: Daily 01:00 UTC
   Purpose: Delete notifications past their expires_at (90 days)

3. app.tasks.cleanup.purge_expired_admin_logs
   Run: Daily 01:30 UTC
   Purpose: Delete admin_logs past their expires_at (30 days)

4. app.tasks.cleanup.purge_soft_deleted_jobs
   Run: Daily 02:00 UTC
   Purpose: Hard-delete closed jobs older than 90 days

5. app.tasks.jobs.close_expired_job_listings
   Run: Daily 02:30 UTC
   Purpose: Set status='closed' on jobs past application_end

6. app.tasks.jobs.update_admission_statuses
   Run: Daily 02:35 UTC
   Purpose: Set status='closed' on admissions past admission_date

7. app.tasks.seo.generate_sitemap
   Run: Daily 04:00 UTC
   Purpose: Regenerate /sitemap.xml with active jobs + admissions

EVENT-TRIGGERED TASKS:
═══════════════════════

• notify_watchers_on_update(entity_type, entity_id)
  Triggered when job/admission is approved or updated → notifies all watchers

• smart_notify(user_id, ...)
  Unified delivery entry — instant or staggered, 5 channels

• deliver_delayed_email / deliver_delayed_whatsapp / deliver_delayed_telegram
  Staggered delivery tasks fired after NOTIFY_*_DELAY seconds

• send_email_notification(to, subject, template, context)
  Direct email send via SMTP (retries 3x with exponential backoff)

NOTE: send_new_job_notifications and notify_priority_subscribers are
registered tasks but are no-op stubs (pass body) — not yet implemented.
```

## 9. Complete User Journey Map

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
                          Watch Jobs & Admissions (user_watches table)
                          max 100 watches per user

ONGOING: NOTIFICATION & TRACKING
═════════════════════════════════
Receive Notifications → Check Dashboard → Visit official site to apply
         │
         ├─ Deadline Reminders (T-7, T-3, T-1 for watched items)
         ├─ Admit Card Releases (when admin publishes admit_cards)
         ├─ Answer Key Releases (when admin publishes answer_keys)
         ├─ Result Releases (when admin publishes results)
         └─ Job/Admission Updates (when admin modifies watched item)

ADMISSION PHASE
═══════════════
Receive Admit Card Notification → Download from official site → Admission Reminder
                                                       │
                                                       ▼
                                            Attend Admission → Receive Result notification

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

## 10. Role-Based Access Control (RBAC) Permission Enforcement

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
    │ - sub (user_id)      │
    │ - user_type ⭐       │
    │ - jti                │
    │ - exp                │
    │ - iat                │
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
    │         │ @require_operator or  │
    │         │ @require_admin guard  │
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
✅ GET    /api/v1/jobs                    View jobs (public)
✅ GET    /api/v1/jobs/<slug>             View job details (public)
✅ POST   /api/v1/jobs/<id>/watch        Watch job
✅ DELETE /api/v1/jobs/<id>/watch        Unwatch job
✅ GET    /api/v1/users/me/watched       List watched items
✅ GET    /api/v1/users/profile          View own profile
✅ PUT    /api/v1/users/profile          Update own profile
✅ GET    /api/v1/notifications          View own notifications
✅ POST   /api/v1/auth/refresh           Refresh access token

Rate Limits:
  - API: 1000 requests/min per user (SlowAPI)
  - verify-token: 10 attempts/min

❌ POST   /api/v1/admin/jobs              (Operator+ only) 403
❌ DELETE /api/v1/admin/jobs/<id>         (Admin only) 403
❌ GET    /api/v1/admin/users             (Operator+ only) 403
❌ PUT    /api/v1/admin/users/<id>/status (Admin only) 403

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
✅ POST   /api/v1/auth/refresh            Refresh access token

Rate Limits:
  - API: 1000 requests/min per user (SlowAPI)
  - verify-token: 10 attempts/min

❌ POST   /api/v1/admin/jobs              (Admin only for create) 403
❌ DELETE /api/v1/admin/jobs/<id>         (Admin only) 403
❌ PUT    /api/v1/admin/users/<id>/status (Admin only) 403

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
✅ PUT    /api/v1/admin/users/<id>/status Suspend/activate user (audit logged)
✅ GET    /api/v1/admin/stats             Dashboard stats
✅ GET    /api/v1/admin/logs              View audit logs (admin only)
✅ GET    /api/v1/admin/jobs              List all jobs (admin panel)
✅ POST   /api/v1/admin/admin-users       Create new admin/operator account
✅ POST   /api/v1/auth/refresh            Refresh access token

Rate Limits:
  - API: 1000 requests/min per user
  - Login: 5 attempts/min

All admin actions are logged in admin_logs table
```

---

## 11. JWT Token Rotation & Refresh Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    JWT TOKEN LIFECYCLE                           │
└──────────────────────────────────────────────────────────────────┘

INITIAL LOGIN (Users):
══════════════════════

Firebase login (email OTP / Google / Phone) on client
    │
    ▼
┌──────────────────────┐
│ POST /api/v1/auth/   │
│   verify-token        │
│ { id_token,           │
│   full_name? }        │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Firebase Admin SDK   │
│ verifies token,      │
│ upserts user in DB   │
└────────┬─────────────┘
         │
         ▼ Valid
┌────────────────────────────────────┐
│ Generate TWO tokens:               │
│                                    │
│ 1. ACCESS TOKEN (15 minutes)       │
│    • Used for API calls            │
│    • Short-lived for security      │
│    • Contains: user_id, user_type, │
│      jti, exp, iat                  │
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
│ Flask stores tokens  │
│ in server-side       │
│ session:             │
│ • session["token"]   │
│ • session["refresh_  │
│   token"]            │
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
│                      │
│ Body (JSON):         │
│ { "refresh_token":   │
│   "eyJ..." }         │
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
   • Flask frontend auto-refreshes on 401
   • No user interruption

✅ Long refresh token (7 days)
   • Stored in Flask server-side session
   • Not exposed in HTTP response body

✅ Forced re-login after 7 days
   • Periodic authentication verification
   • Compromised refresh token expires

✅ Token rotation
   • Each /auth/refresh issues new pair
   • Old refresh JTI is blocklisted in Redis


TOKEN STORAGE (Flask Frontend):
═════════════════════════════

┌──────────────────────────────────┐
│ TOKENS IN FLASK SESSION          │
│ • session["token"]  (access)    │
│ • session["refresh_token"]      │
│ • Server-side session cookie    │
│ • CSRF token also in session    │
│   validated on every POST form  │
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

## 12. Admission Data Model

Admissions (NEET, JEE, CLAT, CAT, GATE etc.) are stored in a
separate `admissions` table, distinct from `jobs`. The three
document tables (`admit_cards`, `answer_keys`, `results`) are
**polymorphic** — each row links to either a job or an admission.

```
┌──────────────────────────────────────────────────────────────────────────┐
│              ADMISSION DATA MODEL                                        │
└──────────────────────────────────────────────────────────────────────────┘

  WHY SEPARATE?
  ─────────────
  jobs fields                   admissions fields
  ─────────────────────         ─────────────────────────────
  total_vacancies        ≠      seats_info (seats by college)
  salary_initial/max     ≠      (no salary — it's education)
  employment_type        ≠      admission_type (ug/pg/doctoral)
  qualification_level    ≠      stream (medical/engineering/law)
  organization/dept      ≠      conducting_body + counselling_body
  application tracking   ≠      seat allotment via counselling

  TABLE STRUCTURE:
  ─────────────────

  ┌──────────────────────────┐         ┌──────────────────────────────┐
  │         jobs             │         │       admissions         │
  │  (Government Jobs)       │         │  (NEET/JEE/CLAT/CAT/GATE)   │
  │                          │         │                              │
  │  id UUID PK              │         │  id UUID PK                  │
  │  job_title               │         │  admission_name                   │
  │  organization            │         │  conducting_body             │
  │  total_vacancies         │         │  counselling_body            │
  │  salary_initial/max      │         │  admission_type (ug/pg/doctoral)  │
  │  employment_type         │         │  stream (medical/engg/law)   │
  │  qualification_level     │         │  eligibility JSONB           │
  │  vacancy_breakdown JSONB │         │  admission_details JSONB          │
  │  fee_general/obc/sc_st/  │         │  selection_process JSONB     │
  │    ews/female (integers) │         │  seats_info JSONB            │
  │  source (manual/         │         │  fee_* (5 columns)           │
  │    pdf_upload)           │         │  status (upcoming/active/    │
  │  status (upcoming/active/│         │    inactive/closed)          │
  │    inactive/closed)      │         │  search_vector GENERATED     │
  │  search_vector GENERATED │         │                              │
  └──────────┬───────────────┘         └─────────────┬────────────────┘
             │                         │
             │          POLYMORPHIC DOCUMENT TABLES  │
             │          ────────────────────────────  │
             │                                       │
             │  job_id FK (nullable) ─────────────┐  │
             │                                   ▼  │
             │                          ┌──────────────────┐
             └─────────────────────────►│  job_admit_cards │
                                         │                  │
  admission_id FK (nullable) ──────────────► │  id UUID PK      │ ◄── CHECK:
                                         │  job_id  UUID?   │ ◀── CHECK:
                                         │  admission_id UUID?│     (job_id IS NOT NULL
                                         │  phase_number    │      AND admission_id IS NULL)
                                         │  title           │     OR
                                         │  download_url    │     (job_id IS NULL
                                         │  valid_from/until│      AND admission_id IS NOT NULL)
                                         │  notes           │
                                         └──────────────────┘

  Same polymorphic pattern applies to:
    • answer_keys  (job_id XOR admission_id + phase docs)
    • results      (job_id XOR admission_id + cutoff_marks JSONB)

  SEEDED DATA (current):
  ──────────────────────
  jobs:  10 jobs + (admit_cards/answer_keys/results linked via job_id FK)
  admissions: 9 admissions
    • NEET PG 2026 (medical, pg)     → 3 phase docs (admit card + answer key + result)
    • NEET UG 2026 (medical, ug)     → 4 phase docs
    • JEE Main 2026 (engineering)    → 7 phase docs (2 sessions, each with docs)
    • JEE Advanced 2026 (engg, ug)   → 3 phase docs
    • CLAT 2026 (law, ug)            → 3 phase docs
    • CAT 2025 (management, pg)      → 3 phase docs
    • CUET UG 2026 (general, ug)     → 4 phase docs
    • NEET SS 2025 (medical, doctoral)→3 phase docs
    • GATE 2026 (engineering, pg)    → 3 phase docs
  Total: 32 phase documents seeded via admission_id FK
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
  │ 💼 Jobs   │ 📄 Admit    │ ✏️ Answer    │ 🏆 Results│ 🎓 Admissions│
  │     /     │  Cards      │   Keys       │ /results  │              │
  │           │/admit-cards │/answer-keys  │           │ /admissions  │
  │           │             │              │           │              │
  └───────────┴─────────────┴──────────────┴───────────┴──────────────┘
  Active section highlighted with white border-bottom + white text

  HERO COLOUR CODING (each section has a matching gradient):
  ──────────────────────────────────────────────────────────
  Section       URL              Hero Gradient         DB Source
  ──────────    ───────────────  ──────────────────    ──────────────────
  Jobs          /                Navy → Blue            jobs
  Admit Cards   /admit-cards     Blue → Sky Blue        admit_cards
  Answer Keys   /answer-keys     Brown → Amber          answer_keys
  Results       /results         Dark Green → Green     results
  Admissions /admissions  Dark Purple → Purple   admissions

  CARD ACCENT (list pages — section-specific CSS class):
  ────────────────────────────────────
  Jobs section         → navy/blue left border
  Admit Cards section  → blue left border
  Answer Keys section  → amber left border
  Results section      → green left border
  Admissions       → purple left border

  DETAIL PAGE FLOW:
  ─────────────────
  User clicks job card                  User clicks admission card
        │                                       │
        ▼                                       ▼
  GET /jobs/<slug>                       GET /admissions/<slug>
        │                                       │
        ▼                                       ▼
  Flask renders job_detail.html          Flask renders admission_detail.html
  (type-aware hero: hero-job /           (hero-admission: purple gradient)
   hero-admit / hero-answer /
   hero-result)
        │                                       │
        ▼                                       ▼
  Doc tabs section shown                 Doc tabs section shown
  if job_type == 'latest_job'            (always shown for admissions)
        │                                       │
        ▼                                       ▼
  HTMX loads /partials/jobs/             HTMX loads /partials/admissions/
  {job_id}/admit-cards                   {admission_id}/admit-cards
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
                    WHERE admission_id={id}  ← for admission_detail.html
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
lifecycle, admission data model, 5-section frontend navigation,
and HTMX phase document tab loading.*
