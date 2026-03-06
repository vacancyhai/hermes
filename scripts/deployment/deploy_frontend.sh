#!/bin/bash

# Deploy Frontend Service - Hermes
# This script deploys the frontend service to the specified environment
# Usage: ./deploy_frontend.sh [development|staging|production]

set -e  # Exit on error

ENVIRONMENT=${1:-development}
FRONTEND_PATH="./src/frontend"

echo "================================"
echo "Deploying Frontend Service"
echo "Environment: $ENVIRONMENT"
echo "================================"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "Usage: $0 [development|staging|production]"
    exit 1
fi

# Validate frontend directory exists
if [ ! -d "$FRONTEND_PATH" ]; then
    echo "❌ Frontend directory not found: $FRONTEND_PATH"
    exit 1
fi

cd "$FRONTEND_PATH"

# Load environment configuration
if [ -f "../../config/$ENVIRONMENT/.env.frontend.$ENVIRONMENT" ]; then
    echo "📋 Loading configuration from: config/$ENVIRONMENT/.env.frontend.$ENVIRONMENT"
    export $(grep -v '^\s*#' "../../config/$ENVIRONMENT/.env.frontend.$ENVIRONMENT" | grep -v '^\s*$' | xargs)
fi

# Check if .env exists in frontend root
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  .env not found. Using .env.example as template."
        cp .env.example .env
        echo "✏️  Please edit .env with your configuration (especially BACKEND_API_URL):"
        echo "    nano .env"
        exit 1
    fi
fi

echo "🔨 Building frontend Docker image..."
docker-compose build

echo "🚀 Starting frontend service..."
docker-compose up -d --build

echo "⏳ Waiting for service to be healthy..."
sleep 5

# Check if frontend is running
if docker-compose ps frontend | grep -q "Up"; then
    echo "✅ Frontend service is running!"
    echo ""
    echo "📊 Active Services:"
    docker-compose ps
    echo ""
    echo "🔗 Endpoints:"
    echo "  - Frontend: http://localhost:8080"
    echo "  - Health check: curl http://localhost:8080/health"
    echo ""
    echo "📋 View logs:"
    echo "  cd $FRONTEND_PATH && docker-compose logs -f"
else
    echo "❌ Frontend service failed to start"
    echo "📋 Docker logs:"
    docker-compose logs
    exit 1
fi
