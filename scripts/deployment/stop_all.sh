#!/usr/bin/env bash
# stop_all.sh — Stop all Hermes services
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Stopping all Hermes services..."

cd "$PROJECT_DIR/src/nginx"          && docker compose down 2>/dev/null || true
cd "$PROJECT_DIR/src/frontend-admin" && docker compose down 2>/dev/null || true
cd "$PROJECT_DIR/src/frontend"       && docker compose down 2>/dev/null || true
cd "$PROJECT_DIR/src/backend"        && docker compose down 2>/dev/null || true

echo "All services stopped."
