#!/bin/bash

# Deploy Backend Service - Hermes
# This script deploys the backend service to the specified environment
# Usage: ./deploy_backend.sh [development|staging|production]

set -e  # Exit on error

ENVIRONMENT=${1:-development}
BACKEND_PATH="./src/backend"

echo "================================"
echo "Deploying Backend Service"
echo "Environment: $ENVIRONMENT"
echo "================================"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "Usage: $0 [development|staging|production]"
    exit 1
fi

# Validate backend directory exists
if [ ! -d "$BACKEND_PATH" ]; then
    echo "❌ Backend directory not found: $BACKEND_PATH"
    exit 1
fi

cd "$BACKEND_PATH"

# Load environment configuration
if [ -f "../../config/$ENVIRONMENT/.env.backend.$ENVIRONMENT" ]; then
    echo "📋 Loading configuration from: config/$ENVIRONMENT/.env.backend.$ENVIRONMENT"
    export $(cat "../../config/$ENVIRONMENT/.env.backend.$ENVIRONMENT" | xargs)
fi

# Check if .env exists in backend root
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  .env not found. Using .env.example as template."
        cp .env.example .env
        echo "✏️  Please edit .env with your configuration:"
        echo "    nano .env"
        exit 1
    fi
fi

echo "🔨 Building backend Docker images..."
docker-compose build

echo "🚀 Starting backend services..."
docker-compose up -d --build

echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check if backend is running
if docker-compose ps backend | grep -q "Up"; then
    echo "✅ Backend service is running!"
    echo ""
    echo "📊 Active Services:"
    docker-compose ps
    echo ""
    echo "🔗 Endpoints:"
    echo "  - Backend API: http://localhost:5000/api/v1/"
    echo "  - Health check: curl http://localhost:5000/api/v1/health"
    echo ""
    echo "📋 View logs:"
    echo "  cd $BACKEND_PATH && docker-compose logs -f"
else
    echo "❌ Backend service failed to start"
    echo "📋 Docker logs:"
    docker-compose logs
    exit 1
fi
