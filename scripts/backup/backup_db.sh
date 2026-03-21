#!/usr/bin/env bash
# backup_db.sh — Daily PostgreSQL backup
# Run via cron: 0 2 * * * /path/to/hermes/scripts/backup/backup_db.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting database backup..."

docker exec hermes_postgresql pg_dump \
    -U "${POSTGRES_USER:-hermes_user}" \
    -d "${POSTGRES_DB:-hermes_db}" \
    --format=custom \
    --compress=9 \
    > "$BACKUP_DIR/hermes_db_${TIMESTAMP}.dump"

echo "[$(date)] Backup saved to $BACKUP_DIR/hermes_db_${TIMESTAMP}.dump"

# Keep only last 7 daily backups
find "$BACKUP_DIR" -name "hermes_db_*.dump" -mtime +7 -delete
echo "[$(date)] Old backups cleaned up."
