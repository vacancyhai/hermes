# Sarkari Path - System Workflow Diagrams (ASCII)

## 1. Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SARKARI PATH SYSTEM                              │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   Internet   │
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
                         ┌───────────▼──────────┐
                         │   Nginx Load         │
                         │   Balancer           │
                         └───────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐  ┌──────▼───────┐  ┌────▼────────┐
            │ Flask App 1  │  │ Flask App 2  │  │ Flask App 3 │
            └───────┬──────┘  └──────┬───────┘  └────┬────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐  ┌──────▼───────┐  ┌────▼────────┐
            │   MongoDB    │  │    Redis     │  │   Celery    │
            │   Cluster    │  │   (Cache &   │  │   Workers   │
            │              │  │   Sessions)  │  │             │
            └──────────────┘  └──────────────┘  └─────┬───────┘
                                                       │
                                     ┌─────────────────┼──────────────┐
                                     │                 │              │
                              ┌──────▼──────┐   ┌──────▼─────┐  ┌────▼────┐
                              │   Email     │   │  Firebase  │  │  SMS    │
                              │   Service   │   │    FCM     │  │ Gateway │
                              │  (SMTP)     │   │   (Push)   │  │         │
                              └─────────────┘   └────────────┘  └─────────┘
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
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Navigate to          │
│ Admin Dashboard      │
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
┌─────────────────────┐
│ Trigger Celery Task:│
│ check_priority_jobs │
└─────────┬───────────┘
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
     │  └──────────┬───────────┘  │
     │             │              │
     │             ▼              │
     │  ┌──────────────────────┐  │
     │  │ Send notification    │  │
     │  │ via all enabled      │  │
     │  │ channels             │  │
     │  └──────────┬───────────┘  │
     │             │              │
     │             ▼              │
     │  ┌──────────────────────┐  │
     │  │ Update user's        │  │
     │  │ application record   │  │
     │  │ with new dates       │  │
     │  └──────────────────────┘  │
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

SCHEDULED TASKS:
════════════════

1. daily_job_matching
   Run: Every day at 1:00 AM
   Purpose: Match new jobs with users

2. send_deadline_reminders
   Run: Every day at 9:00 AM
   Purpose: Send application deadline reminders

3. check_admit_card_dates
   Run: Every day at 8:00 AM
   Purpose: Check and notify admit card releases

4. check_exam_dates
   Run: Every day at 7:00 AM
   Purpose: Remind users of upcoming exams

5. check_result_dates
   Run: Every day at 6:00 PM
   Purpose: Notify about result declarations

6. cleanup_old_notifications
   Run: Every week (Sunday 2:00 AM)
   Purpose: Archive old read notifications

7. generate_weekly_report
   Run: Every Monday 6:00 AM
   Purpose: Generate analytics report for admin
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

**End of Workflow Diagrams**

*These ASCII diagrams provide a comprehensive visual representation of all major flows in the Sarkari Path application system.*
