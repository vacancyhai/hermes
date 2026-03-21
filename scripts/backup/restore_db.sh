#!/usr/bin/env bash
# restore_db.sh — Restore PostgreSQL from a backup file
# Usage: ./restore_db.sh <backup_file.dump>
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file.dump>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "[$(date)] Restoring database from $BACKUP_FILE..."

cat "$BACKUP_FILE" | docker exec -i hermes_postgresql pg_restore \
    -U "${POSTGRES_USER:-hermes_user}" \
    -d "${POSTGRES_DB:-hermes_db}" \
    --clean \
    --if-exists \
    --no-owner

echo "[$(date)] Restore complete."
