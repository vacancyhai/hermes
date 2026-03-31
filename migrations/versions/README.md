# Migration Files Status

## Current Situation

The database is at alembic version `0004` but the migration files are not present in this directory.

This indicates that:
1. The database was migrated using SQL migrations or direct schema creation
2. The migration files were not committed to the repository

## Database Schema

The database currently contains all 14 tables:
- users
- user_profiles
- user_devices
- jobs
- applications
- notifications
- notification_delivery_log
- admin_users
- admin_logs
- admit_cards
- answer_keys
- results
- entrance_exams

## For Fresh Deployments

To initialize a fresh database, use one of these approaches:

### Option 1: Direct SQL Migration (Recommended)
If you have a `0001_initial.sql` file:
```bash
docker exec -i hermes_postgresql psql -U hermes_user -d hermes_db < migrations/0001_initial.sql
```

### Option 2: Generate New Migration
If the migration files are lost but models are up-to-date:
```bash
# Delete alembic_version table first
docker exec -i hermes_postgresql psql -U hermes_user -d hermes_db -c "DROP TABLE IF EXISTS alembic_version;"

# Generate fresh migration
docker exec -w /app -e PYTHONPATH=/app hermes_backend alembic revision --autogenerate -m "initial_schema"

# Apply it
docker exec -w /app -e PYTHONPATH=/app hermes_backend alembic upgrade head
```

## Note

All 14 models are now properly imported in `migrations/env.py` so future migrations will detect all schema changes correctly.
