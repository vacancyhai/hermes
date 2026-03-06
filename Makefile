.PHONY: help install dev-install test clean backend-build backend-up backend-down backend-logs frontend-build frontend-up frontend-down frontend-logs backend-run frontend-run nginx-up nginx-down nginx-logs monitoring-up monitoring-down monitoring-logs all-up all-down all-logs all-status

help:
	@echo "Hermes - Separated Microservices Architecture"
	@echo "=============================================="
	@echo ""
	@echo "📦 BACKEND COMMANDS (src/backend/)"
	@echo "  make backend-build   - Build backend Docker image"
	@echo "  make backend-up      - Start backend services (PostgreSQL, Redis, API, Celery)"
	@echo "  make backend-down    - Stop backend services"
	@echo "  make backend-logs    - View backend logs"
	@echo "  make backend-run     - Run backend locally (without Docker)"
	@echo ""
	@echo "🎨 FRONTEND COMMANDS (src/frontend/)"
	@echo "  make frontend-build  - Build frontend Docker image"
	@echo "  make frontend-up     - Start frontend service"
	@echo "  make frontend-down   - Stop frontend service"
	@echo "  make frontend-logs   - View frontend logs"
	@echo "  make frontend-run    - Run frontend locally (without Docker)"
	@echo ""
	@echo "🌐 NGINX COMMANDS (src/nginx/)"
	@echo "  make nginx-up        - Start Nginx reverse proxy"
	@echo "  make nginx-down      - Stop Nginx reverse proxy"
	@echo "  make nginx-logs      - View Nginx logs"
	@echo ""
	@echo "📊 MONITORING COMMANDS (src/monitoring/)"
	@echo "  make monitoring-up   - Start monitoring stack (Prometheus, Grafana, AlertManager)"
	@echo "  make monitoring-down - Stop monitoring stack"
	@echo "  make monitoring-logs - View monitoring logs"
	@echo ""
	@echo "🔗 FULL STACK COMMANDS"
	@echo "  make all-up         - Start all services (backend → frontend → nginx → monitoring)"
	@echo "  make all-down       - Stop all services"
	@echo "  make all-logs       - View all service logs"
	@echo "  make all-status     - Show status of all services"
	@echo ""
	@echo "🧪 DEVELOPMENT COMMANDS"
	@echo "  make install        - Install all dependencies (backend + frontend)"
	@echo "  make dev-install    - Install development dependencies (pytest, flake8, etc)"
	@echo "  make test           - Run all tests (backend + frontend)"
	@echo "  make clean          - Clean temporary files (__pycache__, .pyc, etc)"
	@echo ""
	@echo "💡 QUICK START (4-step deployment)"
	@echo "  make backend-up && make frontend-up && make nginx-up && make monitoring-up"
	@echo "  OR use: make all-up"
	@echo ""
	@echo "📌 SERVICE STATUS AFTER STARTUP"
	@echo "  Backend API: http://localhost:5000/api/v1/"
	@echo "  Frontend: http://localhost/  (via Nginx proxy)"
	@echo "  Grafana: http://localhost:3000"
	@echo "  Prometheus: http://localhost:9090"
	@echo ""

# ============================================
# BACKEND COMMANDS (src/backend/)
# ============================================

backend-build:
	@echo "🔨 Building backend Docker image..."
	cd src/backend && docker-compose build

backend-up:
	@echo "🚀 Starting backend services (PostgreSQL, Redis, API, Celery)..."
	cd src/backend && docker-compose up -d --build
	@echo "✅ Backend services started!"
	@echo "   Backend API: http://localhost:5000/api/v1/"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   Redis: localhost:6379"

backend-down:
	@echo "⛔ Stopping backend services..."
	cd src/backend && docker-compose down

backend-logs:
	@echo "📋 Backend logs (Ctrl+C to exit)..."
	cd src/backend && docker-compose logs -f

backend-run:
	@echo "🐍 Starting backend server (local, no Docker)..."
	cd src/backend && python run.py

# ============================================
# FRONTEND COMMANDS (src/frontend/)
# ============================================

frontend-build:
	@echo "🔨 Building frontend Docker image..."
	cd src/frontend && docker-compose build

frontend-up:
	@echo "🚀 Starting frontend service..."
	cd src/frontend && docker-compose up -d --build
	@echo "✅ Frontend service started!"
	@echo "   Frontend: http://localhost:8080"

frontend-down:
	@echo "⛔ Stopping frontend service..."
	cd src/frontend && docker-compose down

frontend-logs:
	@echo "📋 Frontend logs (Ctrl+C to exit)..."
	cd src/frontend && docker-compose logs -f

frontend-run:
	@echo "🐍 Starting frontend server (local, no Docker)..."
	cd src/frontend && python run.py

# ============================================
# DEVELOPMENT COMMANDS
# ============================================

install:
	@echo "📦 Installing dependencies..."
	@echo "   Installing backend dependencies..."
	cd src/backend && pip install -r requirements.txt
	@echo "   Installing frontend dependencies..."
	cd src/frontend && pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

dev-install:
	@echo "🔧 Installing development dependencies..."
	pip install pytest pytest-cov black flake8 pylint
	@echo "✅ Development dependencies installed!"

test:
	@echo "🧪 Running tests..."
	@echo "   Running backend tests..."
	cd src/backend && pytest tests/ -v
	@echo "   Running frontend tests..."
	cd src/frontend && pytest tests/ -v
	@echo "✅ All tests completed!"

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".DS_Store" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned!"

# ============================================
# NGINX COMMANDS (src/nginx/)
# ============================================

nginx-up:
	@echo "🚀 Starting Nginx reverse proxy..."
	cd src/nginx && docker-compose up -d
	@echo "✅ Nginx service started!"
	@echo "   Nginx: http://localhost"
	@echo "   Backend API: http://localhost/api/v1/"
	@echo "   Frontend: http://localhost"

nginx-down:
	@echo "⛔ Stopping Nginx service..."
	cd src/nginx && docker-compose down

nginx-logs:
	@echo "📋 Nginx logs (Ctrl+C to exit)..."
	cd src/nginx && docker-compose logs -f

# ============================================
# MONITORING COMMANDS (src/monitoring/)
# ============================================

monitoring-up:
	@echo "🚀 Starting monitoring stack (Prometheus, Grafana, AlertManager)..."
	cd src/monitoring && docker-compose up -d
	@echo "✅ Monitoring services started!"
	@echo "   Grafana: http://localhost:3000 (admin/securepassword123)"
	@echo "   Prometheus: http://localhost:9090"
	@echo "   AlertManager: http://localhost:9093"

monitoring-down:
	@echo "⛔ Stopping monitoring stack..."
	cd src/monitoring && docker-compose down

monitoring-logs:
	@echo "📋 Monitoring logs (Ctrl+C to exit)..."
	cd src/monitoring && docker-compose logs -f

# ============================================
# FULL STACK COMMANDS
# ============================================

all-up: backend-up frontend-up nginx-up
	@echo ""
	@echo "🎉 FULL PLATFORM STARTED!"
	@echo ""
	@echo "📌 Access Your Services:"
	@echo "   Frontend: http://localhost"
	@echo "   Backend API: http://localhost/api/v1/"
	@echo "   Direct Backend: http://localhost:5000/api/v1/"
	@echo ""
	@echo "💡 Optional Services (start separately):"
	@echo "   Monitoring: make monitoring-up"
	@echo "   Grafana: http://localhost:3000 (admin/securepassword123)"
	@echo "   Prometheus: http://localhost:9090"
	@echo ""

all-down: backend-down frontend-down nginx-down monitoring-down
	@echo "✅ All services stopped!"

all-logs:
	@echo "📋 All service logs..."
	@echo "💡 You can run individual logs:"
	@echo "   make backend-logs"
	@echo "   make frontend-logs"
	@echo "   make nginx-logs"
	@echo "   make monitoring-logs"

all-status:
	@echo "📊 SERVICE STATUS"
	@echo "=================="
	@echo ""
	@echo "Backend Services:"
	@cd src/backend && docker-compose ps || true
	@echo ""
	@echo "Frontend Services:"
	@cd src/frontend && docker-compose ps || true
	@echo ""
	@echo "Nginx Service:"
	@cd src/nginx && docker-compose ps || true
	@echo ""
	@echo "Monitoring Services:"
	@cd src/monitoring && docker-compose ps || true
