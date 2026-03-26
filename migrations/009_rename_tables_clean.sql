-- Migration: Rename tables to cleaner names without job_ prefix
-- Date: 2026-03-26
-- Description: Simplify table names for better readability

-- Rename tables (order matters due to foreign key dependencies)
ALTER TABLE job_admit_cards RENAME TO admit_cards;
ALTER TABLE job_answer_keys RENAME TO answer_keys;
ALTER TABLE job_results RENAME TO results;
ALTER TABLE user_job_applications RENAME TO applications;
ALTER TABLE job_vacancies RENAME TO jobs;

-- Note: Foreign key constraints automatically update to reference the new table names
-- No need to recreate constraints as PostgreSQL handles this during ALTER TABLE RENAME
