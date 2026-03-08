#!/bin/bash

# Deploy All Services - Hermes
# This script deploys all three services: backend, user frontend, admin frontend
# Usage: ./deploy_all.sh [development|staging|production]

set -e  # Exit on error

ENVIRONMENT=${1:-development}
SCRIPTS_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================"
echo "Deploying All Services (3-service architecture)"
echo "Environment: $ENVIRONMENT"
echo "================================"
echo ""

# Deploy backend first (it has critical services: PostgreSQL, Redis)
echo "Step 1️⃣  of 3️⃣ : Deploying Backend..."
echo "---"
"$SCRIPTS_PATH/deploy_backend.sh" "$ENVIRONMENT"

echo ""
echo "================================"
echo "Step 2️⃣  of 3️⃣ : Deploying User Frontend..."
echo "---"
"$SCRIPTS_PATH/deploy_frontend.sh" "$ENVIRONMENT"

echo ""
echo "================================"
echo "Step 3️⃣  of 3️⃣ : Deploying Admin Frontend..."
echo "---"
"$SCRIPTS_PATH/deploy_frontend_admin.sh" "$ENVIRONMENT"

echo ""
echo "================================"
echo "✅ All Services Deployed! (8 containers total)"
echo "================================"
echo ""
echo "📍 Deployment Summary:"
echo "  Environment:    $ENVIRONMENT"
echo "  Backend API:    http://localhost:5000/api/v1/"
echo "  User Frontend:  http://localhost:8080"
echo "  Admin Frontend: http://localhost:8081"
echo "  Admin Login:    http://localhost:8081/auth/login"
echo ""
echo "📊 View all services:"
echo "  cd src/backend && docker-compose ps"
echo "  cd src/frontend && docker-compose ps"
echo "  cd src/frontend-admin && docker-compose ps"
echo ""
echo "⛔ Stop all services:"
echo "  cd src/backend && docker-compose down"
echo "  cd src/frontend && docker-compose down"
echo "  cd src/frontend-admin && docker-compose down"
