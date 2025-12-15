# Sarkari Path - Quick Start Guide

## 📋 What This Project Does

**Sarkari Path** is a comprehensive government job notification portal that:
- ✅ Shows latest government job vacancies (Railway, SSC, UPSC, Banking, Police, Defense, Teaching)
- ✅ Sends personalized notifications based on user qualifications (10th, 12th, Graduation) and physical standards
- ✅ Tracks application deadlines with automatic reminders
- ✅ Provides admit card, exam date, answer key, and result notifications
- ✅ Supports Board Results (CBSE, UP Board, Bihar Board, etc.)
- ✅ Government Schemes/Yojanas (PM Kisan, Scholarships, etc.)
- ✅ College/University Admissions (JEE, NEET, etc.)
- ✅ Admin panel for complete content management
- ✅ Advanced analytics and search tracking

> **🗄️ Database**: Enhanced 15-collection MongoDB schema (expanded from 6 to support complete Sarkari Result portal features)

---

## 🏗️ Architecture Overview

### Microservices Design (6 Containers)

```
User Browser
    ↓
Nginx (Port 80/443) → Routes traffic
    ↓                      ↓
Frontend Flask       Backend Flask API
(Jinja2 Pages)       (REST Endpoints)
    ↓                      ↓
         MongoDB + Redis + Celery
```

**Why this architecture?**
- **Frontend Container**: Renders web pages using Jinja2 templates
- **Backend Container**: Handles business logic, authentication, database operations
- **Separated**: Can update/scale frontend and backend independently

---

## 📁 Project Structure

```
sarkari-path/
├── backend/              # Flask REST API
│   ├── app/
│   │   ├── routes/      # API endpoints (/api/auth, /api/jobs, etc.)
│   │   ├── models/      # MongoDB models
│   │   ├── services/    # Business logic (job matching, notifications)
│   │   └── tasks/       # Celery background tasks
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/             # Flask + Jinja2 UI
│   ├── app/
│   │   ├── routes/      # Page routes (/, /jobs, /profile, etc.)
│   │   ├── templates/   # Jinja2 HTML templates
│   │   ├── static/      # CSS, JS, images
│   │   └── utils/
│   │       └── api_client.py  # Calls backend API
│   ├── Dockerfile
│   └── requirements.txt
│
├── nginx/                # Reverse proxy
│   └── nginx.conf
│
├── docker-compose.yml    # All services orchestration
├── .env                  # Configuration
└── mongo-init.js         # Database initialization
```

---

## 🚀 Quick Deployment (10 Minutes)

### Prerequisites
- Docker & Docker Compose installed
- Domain name (optional, for SSL)
- SMTP email credentials (Gmail/Outlook)

### Steps

**1. Clone Repository**
```bash
git clone https://github.com/SumanKr7/sarkari_path_2.0.git
cd sarkari_path_2.0
```

**2. Configure Environment**
```bash
cp .env.example .env
nano .env
```

Required environment variables:
```env
# MongoDB
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=your_secure_password
MONGO_USER=sarkaripath_user
MONGO_PASSWORD=your_db_password

# Redis
REDIS_PASSWORD=your_redis_password

# Flask
SECRET_KEY=your-secret-key-min-32-characters
JWT_SECRET_KEY=your-jwt-secret-key

# Email (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Firebase (for push notifications)
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
```

**3. Start All Services**
```bash
docker compose up -d --build
```

This starts:
- ✅ MongoDB (database)
- ✅ Redis (cache & queue)
- ✅ Backend API (Flask)
- ✅ Frontend UI (Flask + Jinja2)
- ✅ Celery Worker (background tasks)
- ✅ Celery Beat (scheduler)
- ✅ Nginx (reverse proxy)

**4. Verify Deployment**
```bash
# Check all containers are running
docker compose ps

# View logs
docker compose logs -f frontend backend

# Test endpoints
curl http://localhost/health        # Should return "OK"
curl http://localhost/api/health    # Should return {"status":"healthy"}
```

**5. Access Application**
- Website: `http://localhost` or `http://your-domain.com`
- Admin panel: `http://localhost/admin`

---

## 🔧 Management Commands

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f celery_worker
```

### Restart Services
```bash
# All services
docker compose restart

# Specific service
docker compose restart frontend
docker compose restart backend
```

### Update Code
```bash
# Pull latest code
git pull origin main

# Rebuild and restart only changed services
docker compose up -d --build

# Or update specific service
docker compose up -d --no-deps --build frontend
```

### Database Operations
```bash
# Access MongoDB shell
docker compose exec mongodb mongosh -u sarkaripath_user -p your_db_password --authenticationDatabase sarkari_path

# Backup database
docker compose exec mongodb mongodump --uri="mongodb://sarkaripath_user:your_db_password@localhost:27017/sarkari_path?authSource=sarkari_path" --out=/backup

# View Redis keys
docker compose exec redis redis-cli -a your_redis_password
```

### Stop & Clean Up
```bash
# Stop all containers
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v

# Remove unused images
docker system prune -a
```

---

## 📊 How It Works

### 1. User Flow
```
User registers → Creates profile (education, preferences)
    ↓
Admin posts new job
    ↓
Celery matches job with eligible users (education/age/category)
    ↓
Notifications sent (Email + Push + In-app)
    ↓
User receives notification → Views job → Applies
    ↓
Celery sends deadline reminders (7d, 3d, 1d before)
```

### 2. Frontend-Backend Communication

**Frontend (Flask + Jinja2):**
```python
# frontend/app/routes/jobs.py
from app.utils.api_client import APIClient

@bp.route('/jobs')
def job_list():
    # Frontend calls backend API
    jobs_data, status = APIClient.get('/jobs', params={'limit': 20})
    
    # Render template with data
    return render_template('jobs/job_list.html', jobs=jobs_data)
```

**Backend (Flask API):**
```python
# backend/app/routes/jobs.py
@bp.route('/api/jobs', methods=['GET'])
def get_jobs():
    limit = request.args.get('limit', 20)
    jobs = Job.find_all(limit=limit)
    return jsonify({'jobs': jobs}), 200
```

### 3. Notification System

**Triggers:**
1. **New Job Posted** → Celery task matches with users → Sends notifications
2. **Deadline Reminder** → Celery beat checks daily → Sends reminders
3. **Admit Card Released** → Admin updates job → Notifications sent
4. **Result Announced** → Admin updates job → Notifications sent

**Channels:**
- 📧 **Email**: Flask-Mail via SMTP (Gmail/Outlook)
- 📱 **Push**: Firebase Cloud Messaging (web + mobile)
- 🔔 **In-app**: Stored in MongoDB notifications collection

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Complete project documentation with database schemas, API endpoints, deployment guides |
| **DOCKER_DEPLOYMENT.md** | Detailed Docker setup with all configuration files (Dockerfile, docker-compose.yml, nginx.conf) |
| **WORKFLOW_DIAGRAMS.md** | ASCII diagrams showing 10 system workflows (registration, job matching, notifications, etc.) |
| **JINJA2_TEMPLATES_GUIDE.md** | Complete Flask template architecture with examples (base.html, components, pages, email templates) |
| **PROJECT_SUMMARY.md** | This file - quick start guide and overview |

---

## 🔐 Security Features

- ✅ **Password Hashing**: bcrypt
- ✅ **JWT Authentication**: Secure API tokens
- ✅ **Rate Limiting**: Nginx (10 req/s API, 5 req/min login)
- ✅ **HTTPS/SSL**: Let's Encrypt certificates
- ✅ **MongoDB Auth**: Username/password authentication
- ✅ **Redis Auth**: Password protected
- ✅ **CORS**: Controlled cross-origin access
- ✅ **Input Validation**: All user inputs sanitized
- ✅ **Security Headers**: X-Frame-Options, X-XSS-Protection, etc.

---

## 📈 Scaling Guide

### Vertical Scaling (Increase Resources)
```yaml
# In docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'      # Increase from 1
          memory: 2G     # Increase from 1G
```

### Horizontal Scaling (More Containers)
```bash
# Scale backend workers
docker compose up -d --scale backend=3

# Scale celery workers
docker compose up -d --scale celery_worker=3
```

### Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test backend API
ab -n 1000 -c 10 http://localhost/api/jobs

# Test frontend
ab -n 1000 -c 10 http://localhost/
```

---

## 🐛 Troubleshooting

### Issue: Containers not starting
```bash
# Check logs
docker compose logs mongodb redis

# Check if ports are in use
sudo lsof -i :80
sudo lsof -i :27017
sudo lsof -i :6379

# Solution: Stop conflicting services or change ports
```

### Issue: Frontend can't connect to backend
```bash
# Check if backend is healthy
curl http://localhost/api/health

# Check docker network
docker network inspect sarkari_network

# Restart backend
docker compose restart backend
```

### Issue: Celery tasks not running
```bash
# Check celery worker logs
docker compose logs celery_worker celery_beat

# Check Redis connection
docker compose exec redis redis-cli -a your_redis_password ping

# Restart celery services
docker compose restart celery_worker celery_beat
```

### Issue: MongoDB connection failed
```bash
# Check MongoDB logs
docker compose logs mongodb

# Test connection
docker compose exec mongodb mongosh -u admin -p your_root_password

# Recreate MongoDB with fresh data
docker compose down -v
docker compose up -d mongodb
```

---

## 💡 Development Tips

### Local Development (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python run.py
```

**Frontend:**
```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

**MongoDB & Redis:**
```bash
# Install locally or use Docker
docker run -d -p 27017:27017 mongo:7.0
docker run -d -p 6379:6379 redis:7-alpine
```

### Testing

**Backend API Tests:**
```bash
cd backend
pytest tests/
```

**Frontend Integration Tests:**
```bash
cd frontend
python -m pytest tests/
```

### Database Seeding (Sample Data)

```bash
# Create seed script: backend/seed_data.py
docker compose exec backend python seed_data.py
```

---

## 🎯 Next Steps

After deployment:

1. **Create Admin User**
   - Register via `/auth/register`
   - Manually update role in MongoDB: `db.users.updateOne({email: "admin@example.com"}, {$set: {role: "admin"}})`

2. **Post Test Job**
   - Login to admin panel: `/admin`
   - Create a test job vacancy

3. **Test Notifications**
   - Register test user with profile
   - Check if notification is received

4. **Setup SSL**
   ```bash
   # Install certbot in nginx container
   docker compose exec nginx sh
   apk add certbot certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

5. **Setup Backups**
   - Configure automated MongoDB backups
   - Set up backup retention policy
   - Test restore procedure

6. **Monitoring**
   - Setup application monitoring (Sentry, etc.)
   - Configure uptime monitoring
   - Setup alerts for errors

---

## 📞 Support

- **Documentation**: Check all `.md` files in project root
- **Issues**: Create issue on GitHub repository
- **Logs**: Always check container logs first: `docker compose logs -f`

---

## 🎓 Learning Resources

**Flask Microservices:**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Compose Tutorial](https://docs.docker.com/compose/)
- [MongoDB with Python](https://pymongo.readthedocs.io/)

**Celery:**
- [Celery Documentation](https://docs.celeryproject.org/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html)

**Deployment:**
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Built with ❤️ for Indian job seekers**
