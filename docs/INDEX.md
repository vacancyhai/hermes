# Hermes - Documentation Index

## 📚 Complete Documentation Guide

**🎯 MAJOR ARCHITECTURE CHANGE**: Backend and Frontend are now **COMPLETELY SEPARATED** into different folders under `src/`. Each service has its own Docker Compose file and can be deployed independently. This allows changing the frontend technology (Flask → React → iOS → Android) without touching the backend.

This project contains comprehensive documentation across multiple files. Use this index to navigate:

---

## 🎯 Start Here

### For First-Time Users
**👉 [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)**
- 10-minute deployment guide for **SEPARATED** backend and frontend services
- Architecture overview with independent services
- Deployment options (same server vs separate servers)
- Common commands and troubleshooting
- Best for: Getting started with the new separated architecture

**👉 [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)**
- Complete folder structure with **src/** separation
- Backend folder (`src/backend/`) - Independent service
- Frontend folder (`src/frontend/`) - Independent service (replaceable!)
- Design principles (KISS, DRY, YAGNI)
- Directory explanations
- Best for: Understanding the new project organization

---

## 📖 Main Documentation

### 1. **[README.md](./README.md)** - Complete Reference
**What's inside:**
- ✅ Project overview and key capabilities
- ✅ Complete tech stack (Frontend, Backend, Infrastructure)
- ✅ Microservices architecture diagram
- ✅ Enhanced database schemas (15 PostgreSQL tables - expanded from 6 to support complete Hermes job notification portal)
- ✅ API endpoints (60+ REST endpoints with descriptions)
- ✅ Key features implementation (Job matching algorithm, Notification system)
- ✅ Flask-Mail email service configuration
- ✅ Deployment options (Docker vs Traditional)
- ✅ Complete project structure (Backend + Frontend separation)
- ✅ Python package requirements
- ✅ Hostinger VPS deployment guide (12 detailed steps)
- ✅ Server requirements and troubleshooting

**Best for:** Understanding the complete system, API reference, database design

**Sections:**
1. Tech Stack → What technologies are used
2. System Architecture → How components connect
3. Database Schema → 15 PostgreSQL tables (Jobs, Results, Admit Cards, Answer Keys, Admissions, Yojanas, Board Results, etc.)
4. API Endpoints → All REST API routes
5. Key Features → Job matching algorithm, notification triggers
6. Deployment Options → Docker microservices (recommended)
7. Project Structure → File organization
8. Environment Variables → .env configuration
9. Development Workflow → Phase-by-phase development plan
10. Hostinger VPS Deployment → Traditional server setup
11. Monitoring & Maintenance → Production operations
12. Troubleshooting → Common issues and solutions

---

### 2. **[DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)** - Separated Services Setup
**What's inside:**
- ✅ Why separated services? (Advantages explained)
- ✅ Complete architecture diagram (7 containers with Nginx proxy)
- ✅ Backend Dockerfile (Flask REST API)
- ✅ Frontend Dockerfile (Flask + Jinja2, replaceable with React/Mobile)
- ✅ Backend docker-compose.yml (PostgreSQL, Redis, Backend API, Celery Worker, Celery Beat)
- ✅ Frontend docker-compose.yml (Frontend only)
- ✅ .env.example for both backend and frontend
- ✅ Deployment steps (backend first, then frontend)
- ✅ Management commands (logs, restart, update, scale)
- ✅ Deployment options:
  - Same server (development)
  - Different servers (production)
  - With Nginx reverse proxy (production with SSL)
- ✅ Communication flow (Frontend → HTTP → Backend API)
- ✅ CORS configuration
- ✅ SSL setup with Let's Encrypt

**Best for:** Production deployment, DevOps, understanding separated services

**Sections:**
1. Why Separated Services → Benefits explanation
2. Architecture Diagrams → Visual container layout for both services
3. Dockerfiles → Backend and Frontend containers
4. Backend docker-compose.yml → Complete backend ecosystem
5. Frontend docker-compose.yml → Frontend only
6. Deployment Procedures → Step-by-step for different scenarios
7. Environment Variables → .env setup for both services
8. Management Commands → Daily operations for each service
9. Scaling → Independent scaling of backend and frontend
10. Troubleshooting → Service-specific issues

---

### 3. **[WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md)** - Visual Flows
**What's inside:**
- ✅ 10 detailed ASCII workflow diagrams (updated for separated architecture)
- ✅ Overall system architecture (separated microservices)
- ✅ Backend service components (PostgreSQL, Redis, API, Celery)
- ✅ Frontend service components (UI, API client)
- ✅ Communication flow (Frontend HTTP → Backend REST API)
- ✅ User registration & profile setup flow
- ✅ Admin job creation & publishing flow
- ✅ Job matching algorithm (step-by-step eligibility checks)
- ✅ User job application tracking
- ✅ Priority job update notifications
- ✅ Admin dashboard layout
- ✅ 15 PostgreSQL tables with relationships and indexes
- ✅ Celery task scheduler (7 scheduled tasks with timing)
- ✅ Complete user journey map (registration → result)

**Best for:** Understanding workflows, visual learners, system design, separated services communication

**Diagrams:**
1. Overall System Architecture → Separated Backend & Frontend Services
2. User Registration Flow → From form to email verification
3. Job Creation Flow → Admin creates job → Celery triggers matching
4. Job Matching Algorithm → Education check → Age check → Category check
5. Application Tracking → User marks applied → Reminders set
6. Priority Job Notifications → Update triggers immediate notification
7. Admin Dashboard → Stats, recent activity, analytics
8. Database Tables → All 15 tables (in Backend service)
9. Celery Scheduler → Daily tasks, weekly reports, cleanup jobs (in Backend service)
10. User Journey → Complete flow from signup to getting hired

---

---

## 🗺️ Navigation Guide

### "I want to..."

#### Deploy the application
1. Start → [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) (Quick start with separated services)
2. Then → [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) (Complete setup for backend and frontend)
3. Backend → Deploy `src/backend/docker-compose.yml`
4. Frontend → Deploy `src/frontend/docker-compose.yml`
5. Reference → Environment variables for both services
6. Epic plan → [EPIC_01_DOCKER_INFRASTRUCTURE.md](../epic/EPIC_01_DOCKER_INFRASTRUCTURE.md) (Detailed tasks)

#### Understand the new separated architecture
1. Start → [WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md) (Visual overview of separated services)
2. Then → [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) (src/ folder structure)
3. Deep dive → [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) (Communication between services)
4. Planning → [Epic folder](../epic/) (Feature breakdowns)

#### Develop the frontend
1. Start → [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) (Frontend folder: `src/frontend/`)
2. Environment → Set `BACKEND_API_URL` in frontend/.env
3. Architecture → Frontend calls Backend via HTTP REST API
4. Reference → Backend API endpoints to call
5. Deploy → `cd src/frontend && docker-compose up`
6. Epic plan → [EPIC_10_FRONTEND_UI.md](../epic/EPIC_10_FRONTEND_UI.md) (Implementation tasks)
7. **Migration** → Can replace entire `src/frontend/` with React, mobile apps, etc.

#### Develop the backend
1. Start → [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) (Backend folder: `src/backend/`)
- Environment → Configure backend/.env (PostgreSQL, Redis, SMTP)
3. Architecture → Backend exposes `/api/v1/*` REST endpoints
4. CORS → Configure allowed frontend origins
5. Flow → [WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md) (Business logic flows)
6. Deploy → `cd src/backend && docker-compose up`
7. Epic plan → [EPIC_02_BACKEND_API_FOUNDATION.md](../epic/EPIC_02_BACKEND_API_FOUNDATION.md) (Detailed tasks)
8. **Important** → Backend technology is stable, won't change!

#### Deploy on production (different servers)
1. **Backend Server** → Deploy `src/backend/` on powerful server
2. **Frontend Server** → Deploy `src/frontend/` on edge server (or same)
3. **Configuration** → Set `BACKEND_API_URL` in frontend to backend server IP/domain
4. **CORS** → Configure backend to allow frontend origin
5. **Nginx** → Optional reverse proxy for SSL on frontend server
6. **Scaling** → Scale backend and frontend independently

#### Replace frontend with React/Mobile
1. **Current** → Flask + Jinja2 in `src/frontend/`
2. **Future** → Delete `src/frontend/`, create new React/React Native/iOS/Android app
3. **API Calls** → New frontend calls same `http://backend:5000/api/v1/*` endpoints
4. **Backend Changes** → **ZERO!** Backend code remains unchanged 🎉
5. **Example** → React component calls `fetch('http://api.domain.com/api/v1/jobs')`

#### Plan a sprint/feature
1. Start → [Epic folder](../epic/) (Choose feature area - 12 epics available)
2. Review epic → Read epic overview, stories, and acceptance criteria
3. Break down → Epic stories into tasks with story points
4. Track → Epic progress tracking sections (Weekly goals and metrics)

#### Set up notifications
1. Logic → Backend service handles all notifications
2. Implementation → `src/backend/app/services/notification_service.py`
3. Configuration → Email/Firebase credentials in `src/backend/.env`
4. Flow → [WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md) (Celery Task Scheduler)
5. Epic plan → [EPIC_08_NOTIFICATION_SYSTEM.md](../epic/EPIC_08_NOTIFICATION_SYSTEM.md) (Tasks)

#### Troubleshoot issues
1. **Backend Issues** → `cd src/backend && docker-compose logs -f`
2. **Frontend Issues** → `cd src/frontend && docker-compose logs -f`
3. **Communication Issues** → Check `BACKEND_API_URL` in frontend .env
4. **CORS Issues** → Check `CORS_ORIGINS` in backend .env
5. Quick fixes → [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) (Troubleshooting section)
6. Docker issues → [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) (Docker troubleshooting)

---

## 📊 Documentation Comparison

| File | Length | Depth | Best For | Updated |
|------|--------|-------|----------|---------|
| **PROJECT_SUMMARY.md** | Short | Overview | Quick start with separated services | ✅ NEW |
| **PROJECT_STRUCTURE.md** | Long | Complete | src/ folder structure (backend/frontend) | ✅ NEW |
| **DOCKER_DEPLOYMENT.md** | Medium | Technical | Separated docker-compose files | ✅ NEW |
| **WORKFLOW_DIAGRAMS.md** | Medium | Visual | Understanding separated services flow | ✅ NEW |
| **INDEX.md** | Short | Nav | This file - navigation updated | ✅ NEW |
| **README.md** | Long | Complete | Reference, API docs (needs update) | ⚠️ OLD |
| **EPIC_01-12** | Long | Detailed | Sprint planning, task tracking | ℹ️ Legacy |

**Key Changes:**
- ✅ All docs updated to reflect **src/** structure
- ✅ Backend and Frontend **completely separated**
- ✅ Each service has own docker-compose.yml
- ✅ Frontend can be replaced (Flask → React → Mobile)
- ✅ Independent deployment explained

---

## 🚀 Project Setup Files

### Configuration & Setup (NEW Structure)

**Backend Configuration (`src/backend/`)**
- **docker-compose.yml** - Backend services (PostgreSQL, Redis, API, Celery)
- **.env.example** - Backend environment variables
- **requirements.txt** - Python dependencies
- **Dockerfile** - Backend container definition
- **init.sql** - PostgreSQL initialization (DDL + indexes)

**Frontend Configuration (`src/frontend/`)**
- **docker-compose.yml** - Frontend service only
- **.env.example** - Frontend environment variables (includes BACKEND_API_URL)
- **requirements.txt** - Python dependencies (Flask version)
- **Dockerfile** - Frontend container definition

**Shared Configuration (`config/`)**
- **production/** - Production .env templates (backend + frontend)
- **staging/** - Staging .env templates
- **development/** - Development .env templates

**Deployment Scripts (`scripts/`)**
- **deployment/deploy_backend.sh** - Deploy backend service
- **deployment/deploy_frontend.sh** - Deploy frontend service
- **deployment/deploy_all.sh** - Deploy both services
- **backup/backup_db.sh** - Backup PostgreSQL via pg_dump (backend)

**Root Files**
- **Makefile** - Common commands for both services
- **.gitignore** - Git ignore rules

---

## 🔧 Quick Commands

### Start Backend
```bash
cd src/backend
cp .env.example .env
# Edit .env
docker-compose up -d --build
docker-compose logs -f
```

### Start Frontend
```bash
cd src/frontend
cp .env.example .env
# Set BACKEND_API_URL=http://localhost:5000/api/v1
docker-compose up -d --build
docker-compose logs -f
```

### Stop Services
```bash
# Backend
cd src/backend && docker-compose down

# Frontend
cd src/frontend && docker-compose down
```

### Update Code
```bash
# Backend
cd src/backend && git pull && docker-compose up -d --build

# Frontend
cd src/frontend && git pull && docker-compose up -d --build
```

---
- 7 containers (Nginx Reverse Proxy, Backend API, Frontend, PostgreSQL, Redis, Celery Worker, Celery Beat)
- Network and volume configuration

---

## 📋 Epic Planning Documents

### Agile Sprint Planning (12 Epics, 4-Month Roadmap)

The `/epic` folder contains detailed implementation plans organized as epics with user stories, tasks, and acceptance criteria. Each epic covers a major feature area with technical specifications, testing strategies, and progress tracking.

**👉 [EPIC_01_DOCKER_INFRASTRUCTURE.md](../epic/EPIC_01_DOCKER_INFRASTRUCTURE.md)** 🔥 CRITICAL
- 6 stories, 34 story points, Week 1-4
- Docker base infrastructure & container orchestration
- Nginx reverse proxy, PostgreSQL, Redis setup
- Health monitoring, environment configuration
- **Current Status**: Story 1.1 (70% complete - needs health checks, init.sql, Redis AOF)

**👉 [EPIC_02_BACKEND_API_FOUNDATION.md](../epic/EPIC_02_BACKEND_API_FOUNDATION.md)**
- Backend Flask API foundation
- REST endpoints structure
- Database models and services
- Middleware and error handling

**👉 [EPIC_03_USER_AUTHENTICATION.md](../epic/EPIC_03_USER_AUTHENTICATION.md)**
- JWT authentication system
- Login, registration, password reset
- Email verification
- Session management

**👉 [EPIC_04_RBAC_SYSTEM.md](../epic/EPIC_04_RBAC_SYSTEM.md)**
- Role-Based Access Control
- User roles (Admin, Operator, User)
- Permission management
- Access control middleware

**👉 [EPIC_05_JOB_MANAGEMENT.md](../epic/EPIC_05_JOB_MANAGEMENT.md)**
- Job CRUD operations
- Admin job creation/editing
- Job categories and filtering
- Application deadline tracking

**👉 [EPIC_06_JOB_MATCHING_SYSTEM.md](../epic/EPIC_06_JOB_MATCHING_SYSTEM.md)**
- Intelligent job matching algorithm
- Eligibility checking (education, age, category)
- Personalized job recommendations
- Celery background processing

**👉 [EPIC_07_USER_PROFILES.md](../epic/EPIC_07_USER_PROFILES.md)**
- User profile management
- Qualification tracking (10th, 12th, Graduation)
- Physical standards preferences
- Application history

**👉 [EPIC_08_NOTIFICATION_SYSTEM.md](../epic/EPIC_08_NOTIFICATION_SYSTEM.md)**
- Multi-channel notifications (Email, Push, SMS)
- Notification triggers and scheduling
- Priority job alerts
- Deadline reminders

**👉 [EPIC_09_ADMIN_PANEL.md](../epic/EPIC_09_ADMIN_PANEL.md)**
- Admin dashboard with analytics
- User management interface
- Job management tools
- System monitoring

**👉 [EPIC_10_FRONTEND_UI.md](../epic/EPIC_10_FRONTEND_UI.md)**
- Jinja2 template implementation
- Responsive UI design
- Component library
- User experience flows

**👉 [EPIC_11_SARKARI_RESULTS.md](../epic/EPIC_11_SARKARI_RESULTS.md)**
- Board results integration
- Admit card notifications
- Answer key publishing
- Result announcements

**👉 [EPIC_12_ADVANCED_FEATURES.md](../epic/EPIC_12_ADVANCED_FEATURES.md)**
- Analytics and reporting
- Advanced search
- Export functionality
- Performance optimizations

### Epic Structure
Each epic document contains:
- 📋 Epic Overview (ID, description, business value, timeline)
- 📊 Epic Metrics (story count, story points, dependencies)
- 📝 User Stories (with acceptance criteria and technical tasks)
- 🔄 Epic Dependencies
- 📈 Progress Tracking (weekly goals)
- 🧪 Testing Strategy
- 📚 Documentation Requirements
- ⚠️ Risks & Mitigation

**Best for:** Sprint planning, task breakdown, implementation tracking, Agile development

---

## 🎓 Learning Path

### Beginner (Never used Flask/Docker)
1. Read [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) → Understand what the system does
2. View [WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md) → Visualize the flows
3. Try deployment from [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) → Get it running
4. Explore [README.md](./README.md) → Learn the details

### Intermediate (Know Flask, new to Docker)
1. Read [README.md](./README.md) → Understand architecture and API
2. Study [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) → Learn containerization
3. Check [WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md) → Understand system flows
4. Review [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) → Learn folder organization

### Advanced (Ready to deploy to production)
1. Study [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) → Master container orchestration
2. Reference [README.md](./README.md) → Review all configurations
3. Implement from [WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md) → Build all features
4. Deploy using [README.md](./README.md) → Hostinger VPS section

### Project Manager/Team Lead
1. Study [Epic folder](../epic/) → Understand all 12 epics (4-month plan)
2. Review [EPIC_01_DOCKER_INFRASTRUCTURE.md](../epic/EPIC_01_DOCKER_INFRASTRUCTURE.md) → Start with foundation
3. Plan sprints → Use epic stories and story points for estimation
4. Track progress → Use epic weekly goals and metrics
5. Reference [README.md](./README.md) → Technical requirements

---

## 🔍 Quick Reference

### Database Tables
→ [README.md](../README.md) (Database Schema section)
- 15 PostgreSQL tables with SQL DDL
- B-tree and GIN indexes explained
- Foreign key relationships documented

### API Endpoints
→ [README.md](../README.md) (API Endpoints section)
- 60+ endpoints organized by category
- Authentication, Profile, Jobs, Applications, Notifications, Admin
- HTTP methods and access levels

### Docker Commands
→ [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) (Management Commands section)
- Build, start, stop, restart
- Logs, scaling, updates
- Backup and restore

### Frontend Structure
→ [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) (Frontend section)
→ [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) (Frontend container)
- Template organization (layouts, components, pages)
- Static file structure (CSS, JS, images)
- Frontend routes and middleware

### Notification System
→ [README.md](../README.md) (Notification Trigger System section)
→ [WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md) (Celery scheduler)
- 6 notification triggers
- Multi-channel delivery (Email, Push, SMS)
- Celery task implementation

---

## 💡 Tips

1. **Always start with PROJECT_SUMMARY.md** if you're new
2. **Use README.md as reference** when coding (database schemas, API endpoints)
3. **Check WORKFLOW_DIAGRAMS.md** when confused about flow
4. **Use DOCKER_DEPLOYMENT.md** for production deployment
5. **Refer to PROJECT_STRUCTURE.md** to understand folder organization
6. **Use Epic documents for sprint planning** and task breakdown
7. **Track progress using epic weekly goals** to stay on schedule

---

## 🐛 Found Something Unclear?

If any documentation is confusing:
1. Check the section in INDEX.md (this file)
2. Look for related sections in other docs
3. Create an issue on GitHub with suggestions

---

**Documentation Version**: 2.0 (Microservices Architecture)  
**Last Updated**: March 5, 2026  
**Project Repository**: https://github.com/SumanKr7/hermes
