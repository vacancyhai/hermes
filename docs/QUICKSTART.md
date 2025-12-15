# Quick Start Guide - Sarkari Path

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker & Docker Compose installed
- Git installed
- Port 80, 5000, 5001 available

### Step 1: Clone Repository
```bash
git clone https://github.com/SumanKr7/sarkari_path_2.0.git
cd sarkari_path_2.0
```

### Step 2: Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

### Step 3: Start Services
```bash
# Using Docker (Recommended)
docker-compose up -d

# Or using Makefile
make docker-up
```

### Step 4: Access Application
- **Frontend**: http://localhost:5001
- **Backend API**: http://localhost:5000/api
- **Nginx**: http://localhost

## 📂 Project Structure

```
sarkari_path_2.0/
├── backend/          # Flask REST API
├── frontend/         # Flask + Jinja2 UI
├── infrastructure/   # Nginx, Docker configs
├── scripts/          # Utility scripts
├── docs/             # All documentation
└── docker-compose.yml
```

## 🔧 Development Workflow

### Run Backend Locally
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### Run Frontend Locally
```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

## 📚 Documentation

- **Full Documentation**: [README.md](../README.md)
- **Project Structure**: [docs/PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)
- **Docker Guide**: [docs/DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- **Templates Guide**: [docs/JINJA2_TEMPLATES_GUIDE.md](./JINJA2_TEMPLATES_GUIDE.md)

## 🛠️ Common Commands

```bash
# Build Docker images
make docker-build

# Start containers
make docker-up

# Stop containers
make docker-down

# View logs
make docker-logs

# Run tests
make test

# Clean temporary files
make clean
```

## 🔐 Default Credentials

After first run, create admin user through API or seed script.

## 📞 Need Help?

- Read [docs/INDEX.md](./INDEX.md) for complete documentation index
- Check [docs/PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) for detailed setup
- Review [docs/WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md) for system flows

## 📊 Database Architecture

**Enhanced MongoDB Schema**: 15 Collections
- ✅ Core: Users, Profiles, Jobs, Applications, Notifications, Admin Logs
- ✅ Portal: Results, Admit Cards, Answer Keys, Admissions, Yojanas, Board Results
- ✅ System: Categories, Page Views, Search Logs

> **Complete Schema**: See [README.md Database Section](../README.md#database-schema-mongodb-collections---enhanced)

## 🎯 Next Steps

1. **Set up MongoDB**: 15 collections auto-created on first use
2. **Configure Email**: Set up SMTP credentials for notifications
3. **Create Admin User**: Use seed script
4. **Add Sample Jobs**: Test the system with real data
5. **Configure Notifications**: Set up Celery tasks for automated alerts

---

**Happy Coding! 🚀**
