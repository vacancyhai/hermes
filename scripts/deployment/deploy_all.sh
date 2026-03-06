#!/bin/bash

# Deploy All Services - Hermes
# This script deploys both backend and frontend services
# Usage: ./deploy_all.sh [development|staging|production]

set -e  # Exit on error

ENVIRONMENT=${1:-development}
SCRIPTS_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================"
echo "Deploying All Services"
echo "Environment: $ENVIRONMENT"
echo "================================"
echo ""

# Deploy backend first (it has critical services: PostgreSQL, Redis)
echo "Step 1️⃣  of 2️⃣ : Deploying Backend..."
echo "---"
"$SCRIPTS_PATH/deploy_backend.sh" "$ENVIRONMENT"

echo ""
echo "================================"
echo "Step 2️⃣  of 2️⃣ : Deploying Frontend..."
echo "---"
"$SCRIPTS_PATH/deploy_frontend.sh" "$ENVIRONMENT"

echo ""
echo "================================"
echo "✅ All Services Deployed!"
echo "================================"
echo ""
echo "📍 Deployment Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Backend:  http://localhost:5000/api/v1/"
echo "  Frontend: http://localhost:8080"
echo ""
echo "📊 View all services:"
echo "  cd src/backend && docker-compose ps"
echo "  cd src/frontend && docker-compose ps"
echo ""
echo "⛔ Stop all services:"
echo "  cd src/backend && docker-compose down"
echo "  cd src/frontend && docker-compose down"
