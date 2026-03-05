# Sarkari Path - Frontend Service

## Overview

This is the **Frontend Service** for Sarkari Path - a completely independent UI service that calls the backend REST API.

**Current Technology:** Flask + Jinja2 (Server-Side Rendering)

**Future Options:**
- React SPA
- React Native (iOS + Android)
- Native iOS (Swift)
- Native Android (Kotlin)
- Any technology that can make HTTP calls!

**Port:** 8080
**Routes:** `/`, `/jobs`, `/profile`, `/admin`, etc.

---

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
nano .env

# CRITICAL: Set BACKEND_API_URL to your backend server
# Development:
BACKEND_API_URL=http://localhost:5000/api/v1

# Production (if backend on different server):
# BACKEND_API_URL=http://192.168.1.10:5000/api/v1
# BACKEND_API_URL=https://api.yourdomain.com/api/v1
```

### 2. Start Frontend Service

```bash
docker-compose up -d --build
```

This starts:
- Frontend UI (port 8080)

### 3. Verify Service

```bash
# Check container
docker-compose ps

# View logs
docker-compose logs -f

# Test frontend
curl http://localhost:8080
# Should return HTML homepage
```

### 4. Access Application

Open browser: `http://localhost:8080`

---

## How It Works

Frontend calls Backend API via HTTP:

```
User Browser
    ↓
Frontend (http://localhost:8080)
    ↓
Makes HTTP request to Backend
    ↓
Backend API (http://localhost:5000/api/v1/jobs)
    ↓
Returns JSON
    ↓
Frontend renders HTML
    ↓
User sees page
```

**Example API Call in Frontend:**

```python
# src/frontend/app/utils/api_client.py
import requests
import os

BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000/api/v1')

def get_jobs(limit=20):
    response = requests.get(f'{BACKEND_API_URL}/jobs', params={'limit': limit})
    return response.json()
```

---

## Environment Variables

**Required:**
- `BACKEND_API_URL` - Backend API URL (CRITICAL!)
- `SECRET_KEY` - Flask secret key

**Optional:**
- `FRONTEND_PORT` - Frontend port (default: 8080)
- `SESSION_TIMEOUT` - Session timeout in seconds (default: 3600)

---

## Routes

### Public Pages
- `/` - Homepage
- `/login` - Login page
- `/register` - Registration page
- `/jobs` - Job listings
- `/jobs/<id>` - Job details

### Authenticated Pages
- `/profile` - User profile
- `/profile/settings` - Profile settings
- `/profile/applications` - My applications
- `/profile/notifications` - My notifications

### Admin Pages (Admin only)
- `/admin` - Admin dashboard
- `/admin/jobs` - Manage jobs
- `/admin/users` - Manage users
- `/admin/analytics` - View analytics

---

## Folder Structure

```
src/frontend/
├── docker-compose.yml       # Frontend service only
├── Dockerfile               # Frontend container
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
├── README.md                # This file
│
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── routes/             # Page routes
│   │   ├── main.py         # Homepage
│   │   ├── auth.py         # Login/Register
│   │   ├── jobs.py         # Job pages
│   │   ├── profile.py      # Profile pages
│   │   └── admin.py        # Admin pages
│   ├── utils/
│   │   ├── api_client.py   # Backend API calls
│   │   └── helpers.py      # Template helpers
│   └── middleware/
│       └── auth_middleware.py  # Login required
│
├── templates/              # Jinja2 HTML templates
│   ├── layouts/
│   │   └── base.html       # Base layout
│   ├── components/
│   │   ├── navbar.html     # Navigation bar
│   │   └── footer.html     # Footer
│   └── pages/
│       ├── index.html      # Homepage
│       ├── auth/           # Auth pages
│       ├── jobs/           # Job pages
│       ├── profile/        # Profile pages
│       └── admin/          # Admin pages
│
├── static/                 # Static assets
│   ├── css/
│   │   └── main.css        # Styles
│   ├── js/
│   │   └── main.js         # JavaScript
│   └── images/
│       └── logo.png        # Logo
│
├── config/
│   └── settings.py         # Frontend config
│
└── tests/
    ├── unit/
    └── integration/
```

---

## API Communication

**Backend must be running first!**

Frontend makes HTTP calls to backend:

```python
# Get jobs from backend
import requests
jobs = requests.get('http://localhost:5000/api/v1/jobs').json()

# Login user
data = {'email': 'user@example.com', 'password': 'password123'}
response = requests.post('http://localhost:5000/api/v1/auth/login', json=data)
token = response.json()['access_token']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
profile = requests.get('http://localhost:5000/api/v1/users/profile', headers=headers).json()
```

---

## Management Commands

**View Logs:**
```bash
docker-compose logs -f
```

**Restart Frontend:**
```bash
docker-compose restart
```

**Stop Frontend:**
```bash
docker-compose down
```

**Update Code:**
```bash
git pull
docker-compose up -d --build
```

---

## Replacing with React/Mobile

This Flask frontend can be **completely replaced** without touching backend:

### Option 1: React SPA

1. Delete this folder's content (except docker-compose.yml)
2. Create React app: `npx create-react-app .`
3. Update API calls to use `BACKEND_API_URL`
4. Build: `npm run build`
5. Deploy: `docker-compose up`

**Example React API call:**

```javascript
// src/services/api.js
const BACKEND_API_URL = process.env.REACT_APP_BACKEND_API_URL;

export const getJobs = async () => {
  const response = await fetch(`${BACKEND_API_URL}/jobs`);
  return await response.json();
};
```

### Option 2: React Native (Mobile)

1. Create React Native app
2. Update API calls to use backend URL
3. Build iOS/Android apps
4. **No Docker needed** - mobile apps run natively

**Example React Native API call:**

```javascript
// services/api.js
const BACKEND_API_URL = 'https://api.yourdomain.com/api/v1';

export const getJobs = async () => {
  const response = await fetch(`${BACKEND_API_URL}/jobs`);
  return await response.json();
};
```

### Option 3: Native iOS/Android

Use Swift/Kotlin with HTTP libraries:
- iOS: URLSession or Alamofire
- Android: Retrofit or OkHttp

**Backend Code:** ZERO CHANGES! 🎉

---

## Independent Deployment

This frontend service is **completely independent** and can:

1. ✅ Run on a different server than backend
2. ✅ Be replaced with any technology
3. ✅ Scale independently
4. ✅ Be deployed multiple times (different regions)

**Deployment Scenarios:**

**Same Server:**
```bash
# Backend on port 5000
cd src/backend && docker-compose up -d

# Frontend on port 8080
cd src/frontend && docker-compose up -d
```

**Different Servers:**

Backend Server (192.168.1.10):
```bash
cd src/backend && docker-compose up -d
# Backend running on http://192.168.1.10:5000
```

Frontend Server (192.168.1.20):
```bash
cd src/frontend
nano .env
# Set: BACKEND_API_URL=http://192.168.1.10:5000/api/v1
docker-compose up -d
# Frontend running on http://192.168.1.20:8080
```

---

## Troubleshooting

### Cannot connect to backend

**Error:** `Connection refused` or `Failed to fetch`

**Solutions:**
1. Check `BACKEND_API_URL` in `.env`
2. Verify backend is running: `curl http://localhost:5000/api/v1/health`
3. Check network connectivity
4. Check CORS settings in backend

### CORS errors

**Error:** `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution:** Update backend `.env`:
```env
CORS_ORIGINS=http://localhost:8080,http://yourdomain.com
```

### Session issues

**Error:** User logged out frequently

**Solution:** Increase session timeout in `.env`:
```env
SESSION_TIMEOUT=7200  # 2 hours
```

---

## Support

For frontend-related issues:
1. Check logs: `docker-compose logs -f`
2. Verify backend connection: Check `BACKEND_API_URL`
3. Test backend API directly: `curl http://localhost:5000/api/v1/health`
4. Review environment variables in `.env`

---

**Last Updated:** March 2026
**Version:** 2.0 (Separated Architecture)
**Frontend:** Flask + Jinja2 (Replaceable!)
