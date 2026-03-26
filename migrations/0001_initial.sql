-- ============================================================================
-- Hermes Database Schema - Complete Initial Migration
-- ============================================================================
-- Migration: 0001_initial
-- Date: 2026-03-26
-- Description: Complete database schema for fresh installations
--
-- This consolidated migration combines all incremental migrations (001-010)
-- into a single file for clean, fresh database setup.
--
-- Tables created (in dependency order):
--   1. users
--   2. admin_users
--   3. user_profiles
--   4. jobs
--   5. applications
--   6. notifications
--   7. admin_logs
--   8. user_devices
--   9. notification_delivery_log
--  10. entrance_exams
--  11. admit_cards
--  12. answer_keys
--  13. results
-- ============================================================================

-- ============================================================================
-- 1. USERS TABLE
-- ============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    firebase_uid VARCHAR(128) UNIQUE,
    migration_status VARCHAR(20) NOT NULL DEFAULT 'native',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_users_status CHECK (status IN ('active', 'suspended', 'deleted'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE UNIQUE INDEX ix_users_firebase_uid ON users(firebase_uid);

-- ============================================================================
-- 2. ADMIN USERS TABLE
-- ============================================================================
CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'operator',
    department VARCHAR(255),
    permissions JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_admin_users_role CHECK (role IN ('admin', 'operator')),
    CONSTRAINT ck_admin_users_status CHECK (status IN ('active', 'suspended', 'deleted'))
);

CREATE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_status ON admin_users(status);

-- ============================================================================
-- 3. USER PROFILES TABLE
-- ============================================================================
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date_of_birth DATE,
    gender VARCHAR(20),
    category VARCHAR(20),
    is_pwd BOOLEAN NOT NULL DEFAULT FALSE,
    is_ex_serviceman BOOLEAN NOT NULL DEFAULT FALSE,
    state VARCHAR(100),
    city VARCHAR(100),
    pincode VARCHAR(10),
    highest_qualification VARCHAR(50),
    education JSONB NOT NULL DEFAULT '{}',
    notification_preferences JSONB NOT NULL DEFAULT '{}',
    preferred_states JSONB NOT NULL DEFAULT '[]',
    preferred_categories JSONB NOT NULL DEFAULT '[]',
    followed_organizations JSONB NOT NULL DEFAULT '[]',
    fcm_tokens JSONB NOT NULL DEFAULT '[]',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_profiles_gender CHECK (gender IN ('Male', 'Female', 'Other')),
    CONSTRAINT ck_profiles_category CHECK (category IN ('General', 'OBC', 'SC', 'ST', 'EWS', 'EBC'))
);

CREATE UNIQUE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_education ON user_profiles USING GIN(education);
CREATE INDEX idx_user_profiles_notif_prefs ON user_profiles USING GIN(notification_preferences);

-- ============================================================================
-- 4. JOBS TABLE (formerly job_vacancies)
-- ============================================================================
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    organization VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    employment_type VARCHAR(50) DEFAULT 'permanent',
    qualification_level VARCHAR(50),
    total_vacancies INTEGER,
    vacancy_breakdown JSONB NOT NULL DEFAULT '{}',
    description TEXT,
    short_description TEXT,
    eligibility JSONB NOT NULL DEFAULT '{}',
    application_details JSONB NOT NULL DEFAULT '{}',
    documents JSONB NOT NULL DEFAULT '[]',
    source_url TEXT,
    notification_date DATE,
    application_start DATE,
    application_end DATE,
    exam_start DATE,
    exam_end DATE,
    result_date DATE,
    exam_details JSONB NOT NULL DEFAULT '{}',
    salary_initial INTEGER,
    salary_max INTEGER,
    salary JSONB NOT NULL DEFAULT '{}',
    selection_process JSONB NOT NULL DEFAULT '[]',
    fee_general INTEGER,
    fee_obc INTEGER,
    fee_sc_st INTEGER,
    fee_ews INTEGER,
    fee_female INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    is_urgent BOOLEAN NOT NULL DEFAULT FALSE,
    views INTEGER NOT NULL DEFAULT 0,
    applications_count INTEGER NOT NULL DEFAULT 0,
    created_by UUID REFERENCES admin_users(id),
    source VARCHAR(20) NOT NULL DEFAULT 'manual',
    source_pdf_path TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_jobs_employment_type CHECK (employment_type IN ('permanent', 'temporary', 'contract', 'apprentice')),
    CONSTRAINT ck_jobs_status CHECK (status IN ('draft', 'active', 'expired', 'cancelled', 'upcoming')),
    CONSTRAINT ck_jobs_source CHECK (source IN ('manual', 'pdf_upload'))
);

CREATE INDEX idx_jobs_organization ON jobs(organization);
CREATE INDEX idx_jobs_status_created ON jobs(status, created_at DESC);
CREATE INDEX idx_jobs_qual_level ON jobs(qualification_level);
CREATE INDEX idx_jobs_application_end ON jobs(application_end);
CREATE INDEX idx_jobs_org_status ON jobs(organization, status, created_at DESC);
CREATE INDEX idx_jobs_eligibility_gin ON jobs USING GIN(eligibility);

-- Full-text search
ALTER TABLE jobs ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(job_title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(organization, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'C')
    ) STORED;

CREATE INDEX idx_jobs_search ON jobs USING GIN(search_vector);

-- ============================================================================
-- 5. APPLICATIONS TABLE (formerly user_job_applications)
-- ============================================================================
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    application_number VARCHAR(100),
    is_priority BOOLEAN NOT NULL DEFAULT FALSE,
    applied_on TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'applied',
    notes TEXT,
    reminders JSONB NOT NULL DEFAULT '[]',
    result_info JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, job_id),
    CONSTRAINT ck_applications_status CHECK (status IN ('applied', 'admit_card_released', 'exam_completed', 'result_pending', 'selected', 'rejected', 'waiting_list'))
);

CREATE INDEX idx_applications_user_job ON applications(user_id, job_id);
CREATE INDEX idx_applications_user_applied ON applications(user_id, applied_on DESC);

-- ============================================================================
-- 6. NOTIFICATIONS TABLE
-- ============================================================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_type VARCHAR(50),
    entity_id UUID,
    type VARCHAR(60) NOT NULL,
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    action_url TEXT,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    sent_via VARCHAR(20)[],
    priority VARCHAR(10) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '90 days',
    CONSTRAINT ck_notifications_priority CHECK (priority IN ('low', 'medium', 'high'))
);

CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_user_created ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_expires ON notifications(expires_at);

-- ============================================================================
-- 7. ADMIN LOGS TABLE
-- ============================================================================
CREATE TABLE admin_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES admin_users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details TEXT,
    changes JSONB NOT NULL DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '30 days'
);

CREATE INDEX idx_admin_logs_admin_ts ON admin_logs(admin_id, timestamp DESC);
CREATE INDEX idx_admin_logs_expires ON admin_logs(expires_at);

-- ============================================================================
-- 8. USER DEVICES TABLE
-- ============================================================================
CREATE TABLE user_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fcm_token VARCHAR(500),
    device_name VARCHAR(255) NOT NULL DEFAULT 'Unknown',
    device_type VARCHAR(20) NOT NULL DEFAULT 'web',
    device_fingerprint VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_devices_device_type CHECK (device_type IN ('web', 'pwa', 'android', 'ios'))
);

CREATE INDEX idx_devices_user_id ON user_devices(user_id);
CREATE UNIQUE INDEX idx_devices_fcm_token ON user_devices(fcm_token) WHERE fcm_token IS NOT NULL;
CREATE INDEX idx_devices_fingerprint ON user_devices(user_id, device_fingerprint);

-- ============================================================================
-- 9. NOTIFICATION DELIVERY LOG TABLE
-- ============================================================================
CREATE TABLE notification_delivery_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    device_id UUID REFERENCES user_devices(id) ON DELETE SET NULL,
    error_message TEXT,
    attempted_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_delivery_channel CHECK (channel IN ('in_app', 'push', 'email', 'whatsapp', 'telegram')),
    CONSTRAINT ck_delivery_status CHECK (status IN ('pending', 'sent', 'delivered', 'failed'))
);

CREATE INDEX idx_delivery_log_notif ON notification_delivery_log(notification_id);
CREATE INDEX idx_delivery_log_user ON notification_delivery_log(user_id, created_at DESC);

-- ============================================================================
-- 10. ENTRANCE EXAMS TABLE
-- ============================================================================
CREATE TABLE entrance_exams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(500) UNIQUE NOT NULL,
    exam_name VARCHAR(500) NOT NULL,
    conducting_body VARCHAR(255) NOT NULL,
    counselling_body VARCHAR(255),
    exam_type VARCHAR(20) NOT NULL DEFAULT 'pg',
    stream VARCHAR(30) NOT NULL DEFAULT 'general',
    eligibility JSONB NOT NULL DEFAULT '{}',
    exam_details JSONB NOT NULL DEFAULT '{}',
    selection_process JSONB NOT NULL DEFAULT '[]',
    seats_info JSONB,
    application_start DATE,
    application_end DATE,
    exam_date DATE,
    result_date DATE,
    counselling_start DATE,
    fee_general INTEGER,
    fee_obc INTEGER,
    fee_sc_st INTEGER,
    fee_ews INTEGER,
    fee_female INTEGER,
    description TEXT,
    short_description TEXT,
    source_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    views INTEGER NOT NULL DEFAULT 0,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_entrance_exam_type CHECK (exam_type IN ('ug', 'pg', 'doctoral', 'lateral')),
    CONSTRAINT ck_entrance_exam_stream CHECK (stream IN ('medical', 'engineering', 'law', 'management', 'arts_science', 'general')),
    CONSTRAINT ck_entrance_exam_status CHECK (status IN ('upcoming', 'active', 'completed', 'cancelled'))
);

CREATE UNIQUE INDEX idx_entrance_exams_slug ON entrance_exams(slug);
CREATE INDEX idx_entrance_exams_stream_status ON entrance_exams(stream, status, created_at);

-- Full-text search
ALTER TABLE entrance_exams ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(exam_name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(conducting_body, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'C')
    ) STORED;

CREATE INDEX idx_entrance_exams_search ON entrance_exams USING GIN(search_vector);

-- ============================================================================
-- 11. ADMIT CARDS TABLE (formerly job_admit_cards)
-- ============================================================================
CREATE TABLE admit_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    exam_id UUID REFERENCES entrance_exams(id) ON DELETE CASCADE,
    phase_number SMALLINT,
    title VARCHAR(255) NOT NULL,
    download_url TEXT NOT NULL,
    valid_from DATE,
    valid_until DATE,
    notes TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_admit_cards_source CHECK ((job_id IS NOT NULL AND exam_id IS NULL) OR (job_id IS NULL AND exam_id IS NOT NULL))
);

CREATE INDEX idx_admit_cards_job ON admit_cards(job_id, phase_number);
CREATE INDEX idx_admit_cards_exam ON admit_cards(exam_id, phase_number);
CREATE INDEX idx_admit_cards_pub ON admit_cards(published_at);

-- ============================================================================
-- 12. ANSWER KEYS TABLE (formerly job_answer_keys)
-- ============================================================================
CREATE TABLE answer_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    exam_id UUID REFERENCES entrance_exams(id) ON DELETE CASCADE,
    phase_number SMALLINT,
    title VARCHAR(255) NOT NULL,
    answer_key_type VARCHAR(20) NOT NULL DEFAULT 'provisional',
    files JSONB NOT NULL DEFAULT '[]',
    objection_url TEXT,
    objection_deadline DATE,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_answer_key_type CHECK (answer_key_type IN ('provisional', 'final')),
    CONSTRAINT ck_answer_keys_source CHECK ((job_id IS NOT NULL AND exam_id IS NULL) OR (job_id IS NULL AND exam_id IS NOT NULL))
);

CREATE INDEX idx_answer_keys_job ON answer_keys(job_id, phase_number);
CREATE INDEX idx_answer_keys_exam ON answer_keys(exam_id, phase_number);
CREATE INDEX idx_answer_keys_type ON answer_keys(job_id, answer_key_type);

-- ============================================================================
-- 13. RESULTS TABLE (formerly job_results)
-- ============================================================================
CREATE TABLE results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    exam_id UUID REFERENCES entrance_exams(id) ON DELETE CASCADE,
    phase_number SMALLINT,
    title VARCHAR(255) NOT NULL,
    result_type VARCHAR(20) NOT NULL,
    download_url TEXT,
    cutoff_marks JSONB,
    total_qualified INTEGER,
    notes TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_result_type CHECK (result_type IN ('shortlist', 'cutoff', 'merit_list', 'final')),
    CONSTRAINT ck_results_source CHECK ((job_id IS NOT NULL AND exam_id IS NULL) OR (job_id IS NULL AND exam_id IS NOT NULL))
);

CREATE INDEX idx_results_job ON results(job_id, phase_number);
CREATE INDEX idx_results_exam ON results(exam_id, phase_number);
CREATE INDEX idx_results_pub ON results(published_at);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- All tables, indexes, and constraints created successfully.
-- This schema represents the final state after all incremental migrations.
-- ============================================================================
