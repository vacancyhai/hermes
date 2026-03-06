#!/bin/bash

# Backup PostgreSQL Database - Hermes Backend
# This script creates a backup of the PostgreSQL database
# Usage: ./backup_db.sh [output_directory]

BACKEND_PATH="./src/backend"
OUTPUT_DIR=${1:-.}
BACKUP_FILENAME="hermes_backup_$(date +%Y%m%d_%H%M%S).dump"
BACKUP_PATH="$OUTPUT_DIR/$BACKUP_FILENAME"

echo "================================"
echo "PostgreSQL Database Backup"
echo "================================"
echo ""

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

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "📦 Backing up database..."
echo "   Database: hermes_db"
echo "   User: hermes_user"
echo "   Output: $BACKUP_PATH"
echo ""

# Create backup using pg_dump
docker-compose -f "$BACKEND_PATH/docker-compose.yml" exec -T postgresql pg_dump \
    -U hermes_user \
    -d hermes_db \
    -F c \
    -f "/tmp/$BACKUP_FILENAME"

# Copy backup from container to host
docker cp "$(docker-compose -f "$BACKEND_PATH/docker-compose.yml" ps -q postgresql):/tmp/$BACKUP_FILENAME" \
    "$BACKUP_PATH"

# Verify backup was created
if [ -f "$BACKUP_PATH" ]; then
    FILESIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    echo "✅ Backup successful!"
    echo "   File: $BACKUP_FILENAME"
    echo "   Size: $FILESIZE"
    echo "   Path: $BACKUP_PATH"
else
    echo "❌ Backup failed!"
    exit 1
fi
