-- Migration: Remove admit_card, answer_key, result from job_vacancies
-- Date: 2026-03-26
-- Description: Simplify job_vacancies to only store actual job postings.
--              Document announcements now only use separate tables (job_admit_cards, job_answer_keys, job_results)

-- Step 1: Delete all non-job entries from job_vacancies
DELETE FROM job_vacancies WHERE job_type IN ('admit_card', 'answer_key', 'result');

-- Step 2: Drop old CHECK constraint
ALTER TABLE job_vacancies DROP CONSTRAINT IF EXISTS ck_jobs_job_type;

-- Step 3: Add new CHECK constraint with only 'latest_job'
ALTER TABLE job_vacancies ADD CONSTRAINT ck_jobs_job_type 
    CHECK (job_type = 'latest_job');

-- Note: The job_type column is kept for potential future job subcategories
-- (e.g., 'government_job', 'psu_job', etc.) but currently only 'latest_job' is allowed
