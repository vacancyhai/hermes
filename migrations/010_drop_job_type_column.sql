-- Migration: Drop job_type column from jobs table
-- Date: 2026-03-26
-- Description: Remove job_type column as the table now exclusively stores jobs

-- Drop the CHECK constraint first
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS ck_jobs_job_type;

-- Drop the job_type column
ALTER TABLE jobs DROP COLUMN IF EXISTS job_type;
