#!/bin/bash

# Deploy Admin Frontend Service - Hermes
# This script deploys the admin frontend service to the specified environment
# Usage: ./deploy_frontend_admin.sh [development|staging|production]

set -e  # Exit on error

ENVIRONMENT=${1:-development}
FRONTEND_ADMIN_PATH="./src/frontend-admin"

echo "================================"
echo "Deploying Admin Frontend Service"
echo "Environment: $ENVIRONMENT"
echo "================================"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "Usage: $0 [development|staging|production]"
    exit 1
fi

# Validate admin frontend directory exists
if [ ! -d "$FRONTEND_ADMIN_PATH" ]; then
    echo "❌ Admin frontend directory not found: $FRONTEND_ADMIN_PATH"
    exit 1
fi

cd "$FRONTEND_ADMIN_PATH"

# Load environment configuration
if [ -f "../../config/$ENVIRONMENT/.env.frontend-admin.$ENVIRONMENT" ]; then
    echo "📋 Loading configuration from: config/$ENVIRONMENT/.env.frontend-admin.$ENVIRONMENT"
    export $(grep -v '^\s*#' "../../config/$ENVIRONMENT/.env.frontend-admin.$ENVIRONMENT" | grep -v '^\s*$' | xargs)
fi

# Check if .env exists in admin frontend root
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  .env not found. Using .env.example as template."
        cp .env.example .env
        echo "✏️  Please edit .env with your configuration (especially BACKEND_API_URL):"
        echo "    nano .env"
        exit 1
    fi
fi

echo "🔨 Building admin frontend Docker image..."
docker-compose build

echo "🚀 Starting admin frontend service..."
docker-compose up -d --build

echo "⏳ Waiting for service to be healthy..."
sleep 5

# Check if admin frontend is running
if docker-compose ps frontend-admin | grep -q "Up"; then
    echo "✅ Admin frontend service is running!"
    echo ""
    echo "📊 Active Services:"
    docker-compose ps
    echo ""
    echo "🔗 Endpoints:"
    echo "  - Admin Frontend: http://localhost:8081"
    echo "  - Admin Login:    http://localhost:8081/auth/login"
    echo "  - Health check:   curl http://localhost:8081/health"
    echo ""
    echo "📋 View logs:"
    echo "  cd $FRONTEND_ADMIN_PATH && docker-compose logs -f"
else
    echo "❌ Admin frontend service failed to start"
    echo "📋 Docker logs:"
    docker-compose logs
    exit 1
fi
