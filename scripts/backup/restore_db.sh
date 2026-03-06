#!/bin/bash

# Restore PostgreSQL Database - Hermes Backend
# This script restores a PostgreSQL database from backup
# Usage: ./restore_db.sh <backup_file>
# Example: ./restore_db.sh hermes_backup_20260305_120000.dump

set -e  # Exit on error

BACKEND_PATH="./src/backend"
BACKUP_FILE=$1

echo "================================"
echo "PostgreSQL Database Restore"
echo "================================"
echo ""

# Validate arguments
if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Backup file not specified"
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 hermes_backup_20260305_120000.dump"
    exit 1
fi

# Validate backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Validate backend directory exists
if [ ! -d "$BACKEND_PATH" ]; then
    echo "❌ Backend directory not found: $BACKEND_PATH"
    exit 1
fi

# Check if docker-compose is running in backend
if ! docker-compose -f "$BACKEND_PATH/docker-compose.yml" ps postgresql &>/dev/null; then
    echo "❌ PostgreSQL container is not running"
    echo "   Start backend services first:"
    echo "   cd $BACKEND_PATH && docker-compose up -d"
    exit 1
fi

echo "⚠️  WARNING: This will REPLACE the current database!"
echo "   Database: hermes_db"
echo "   Backup file: $BACKUP_FILE"
echo ""
read -p "Continue? (yes/no): " -r CONFIRM
if [[ ! $CONFIRM =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

echo ""
echo "📥 Restoring database..."

# Copy backup file to container
CONTAINER_ID=$(docker-compose -f "$BACKEND_PATH/docker-compose.yml" ps -q postgresql)
docker cp "$BACKUP_FILE" "$CONTAINER_ID:/tmp/restore.dump"

# Drop and recreate database (clean slate)
docker-compose -f "$BACKEND_PATH/docker-compose.yml" exec -T postgresql \
    psql -U hermes_user -d postgres -c "DROP DATABASE IF EXISTS hermes_db;"

docker-compose -f "$BACKEND_PATH/docker-compose.yml" exec -T postgresql \
    psql -U hermes_user -d postgres -c "CREATE DATABASE hermes_db;"

# Restore from backup
docker-compose -f "$BACKEND_PATH/docker-compose.yml" exec -T postgresql \
    pg_restore -U hermes_user -d hermes_db /tmp/restore.dump

echo ""
echo "✅ Restore successful!"
echo "   Database: hermes_db"
echo "   Status: Ready to use"
echo ""
echo "💡 Tip: Verify the restore with:"
echo "   cd $BACKEND_PATH && docker-compose exec postgresql psql -U hermes_user -d hermes_db -c '\\dt'"
