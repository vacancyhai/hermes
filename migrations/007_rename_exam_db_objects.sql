-- Migration: Rename exam database objects to entrance_exam for consistency
-- Date: 2026-03-26
-- Description: Rename indexes and constraints from exam to entrance_exam prefix

-- Rename indexes
ALTER INDEX IF EXISTS idx_exams_search RENAME TO idx_entrance_exams_search;
ALTER INDEX IF EXISTS idx_exams_slug RENAME TO idx_entrance_exams_slug;
ALTER INDEX IF EXISTS idx_exams_stream_status RENAME TO idx_entrance_exams_stream_status;

-- Rename check constraints
ALTER TABLE entrance_exams RENAME CONSTRAINT ck_exam_status TO ck_entrance_exam_status;
ALTER TABLE entrance_exams RENAME CONSTRAINT ck_exam_stream TO ck_entrance_exam_stream;
ALTER TABLE entrance_exams RENAME CONSTRAINT ck_exam_type TO ck_entrance_exam_type;
