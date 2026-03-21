#!/usr/bin/env bash
# deploy_all.sh — Deploy all Hermes services
# Usage: ./deploy_all.sh [development|production]
set -euo pipefail

ENV="${1:-development}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "================================================"
echo "  Deploying Hermes — $ENV environment"
echo "================================================"

# Validate environment
if [[ "$ENV" != "development" && "$ENV" != "production" ]]; then
    echo "Error: Environment must be 'development' or 'production'"
    exit 1
fi

# Copy env files
echo ""
echo "[1/4] Copying environment files..."
cp "$PROJECT_DIR/config/$ENV/.env.backend.$ENV"         "$PROJECT_DIR/src/backend/.env"
cp "$PROJECT_DIR/config/$ENV/.env.frontend.$ENV"        "$PROJECT_DIR/src/frontend/.env"
cp "$PROJECT_DIR/config/$ENV/.env.frontend-admin.$ENV"  "$PROJECT_DIR/src/frontend-admin/.env"
echo "  Done."

# Start backend services (PostgreSQL, Redis, PgBouncer, Backend, Celery)
echo ""
echo "[2/4] Starting backend services..."
cd "$PROJECT_DIR/src/backend"
docker compose up -d --build
echo "  Waiting for PostgreSQL to be ready..."
docker compose exec -T backend sh -c 'until curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; do sleep 2; done'
echo "  Backend is healthy."

# Run migrations
echo ""
echo "[3/4] Running database migrations..."
docker compose exec -T backend alembic upgrade head
echo "  Migrations applied."

# Start frontends
echo ""
echo "[4/4] Starting frontend services..."
cd "$PROJECT_DIR/src/frontend"
docker compose up -d --build

cd "$PROJECT_DIR/src/frontend-admin"
docker compose up -d --build

echo ""
echo "================================================"
echo "  Hermes is running!"
echo ""
echo "  Backend API:     http://localhost:8000/api/v1/health"
echo "  User Frontend:   http://localhost:8080"
echo "  Admin Frontend:  http://localhost:8081"
echo "  API Docs:        http://localhost:8000/api/v1/docs"
echo "================================================"
