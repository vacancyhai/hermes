"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-03-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # USERS
    # ------------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('avatar_url', sa.Text),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_email_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_mobile_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("role IN ('user','admin','operator')", name='ck_users_role'),
        sa.CheckConstraint("status IN ('active','suspended','deleted')", name='ck_users_status'),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_status', 'users', ['status'])

    # ------------------------------------------------------------------
    # USER PROFILES
    # ------------------------------------------------------------------
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('date_of_birth', sa.Date),
        sa.Column('gender', sa.String(20)),
        sa.Column('category', sa.String(20)),
        sa.Column('is_pwd', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_ex_serviceman', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('state', sa.String(100)),
        sa.Column('city', sa.String(100)),
        sa.Column('pincode', sa.String(10)),
        sa.Column('highest_qualification', sa.String(50)),
        sa.Column('education', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('physical_details', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('quick_filters', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('notification_preferences', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("gender IN ('Male','Female','Other')", name='ck_user_profiles_gender'),
        sa.CheckConstraint("category IN ('General','OBC','SC','ST','EWS','EBC')", name='ck_user_profiles_category'),
    )
    op.create_index('idx_user_profiles_user_id', 'user_profiles', ['user_id'], unique=True)
    op.create_index('idx_user_profiles_education', 'user_profiles', ['education'], postgresql_using='gin')
    op.create_index('idx_user_profiles_notif_prefs', 'user_profiles', ['notification_preferences'], postgresql_using='gin')

    # ------------------------------------------------------------------
    # JOB VACANCIES
    # ------------------------------------------------------------------
    op.create_table(
        'job_vacancies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_title', sa.String(500), nullable=False),
        sa.Column('slug', sa.String(500), unique=True, nullable=False),
        sa.Column('organization', sa.String(255), nullable=False),
        sa.Column('department', sa.String(255)),
        sa.Column('post_code', sa.String(100)),
        sa.Column('job_type', sa.String(50), nullable=False, server_default='latest_job'),
        sa.Column('employment_type', sa.String(50), server_default='permanent'),
        sa.Column('qualification_level', sa.String(50)),
        sa.Column('total_vacancies', sa.Integer),
        sa.Column('vacancy_breakdown', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('description', sa.Text),
        sa.Column('short_description', sa.Text),
        sa.Column('eligibility', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('application_details', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('notification_date', sa.Date),
        sa.Column('application_start', sa.Date),
        sa.Column('application_end', sa.Date),
        sa.Column('last_date_fee', sa.Date),
        sa.Column('admit_card_release', sa.Date),
        sa.Column('exam_city_release', sa.Date),
        sa.Column('exam_start', sa.Date),
        sa.Column('exam_end', sa.Date),
        sa.Column('correction_start', sa.Date),
        sa.Column('correction_end', sa.Date),
        sa.Column('answer_key_release', sa.Date),
        sa.Column('result_date', sa.Date),
        sa.Column('exam_details', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('salary_initial', sa.Integer),
        sa.Column('salary_max', sa.Integer),
        sa.Column('salary', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('selection_process', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('documents_required', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('is_featured', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_urgent', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_trending', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('priority', sa.SmallInteger, nullable=False, server_default='0'),
        sa.Column('meta_title', sa.String(500)),
        sa.Column('meta_description', sa.Text),
        sa.Column('meta_keywords', postgresql.ARRAY(sa.Text)),
        sa.Column('views', sa.Integer, nullable=False, server_default='0'),
        sa.Column('applications_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('shares_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("job_type IN ('latest_job','result','admit_card','answer_key','admission','yojana')", name='ck_jobs_job_type'),
        sa.CheckConstraint("status IN ('active','expired','cancelled','upcoming')", name='ck_jobs_status'),
    )
    op.create_index('idx_jobs_organization', 'job_vacancies', ['organization'])
    op.create_index('idx_jobs_status_created', 'job_vacancies', ['status', sa.text('created_at DESC')])
    op.create_index('idx_jobs_qual_level', 'job_vacancies', ['qualification_level'])
    op.create_index('idx_jobs_application_end', 'job_vacancies', ['application_end'])
    op.create_index('idx_jobs_eligibility_gin', 'job_vacancies', ['eligibility'], postgresql_using='gin')

    # ------------------------------------------------------------------
    # USER JOB APPLICATIONS
    # ------------------------------------------------------------------
    op.create_table(
        'user_job_applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('application_number', sa.String(100)),
        sa.Column('is_priority', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('applied_on', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('exam_center', sa.String(255)),
        sa.Column('admit_card_downloaded', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('exam_appeared', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('status', sa.String(50), nullable=False, server_default='applied'),
        sa.Column('notes', sa.Text),
        sa.Column('reminders', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('result_info', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.UniqueConstraint('user_id', 'job_id', name='uq_user_job_application'),
        sa.CheckConstraint(
            "status IN ('applied','admit_card_released','exam_completed','result_pending','selected','rejected','waiting_list')",
            name='ck_applications_status'
        ),
    )
    op.create_index('idx_applications_user_job', 'user_job_applications', ['user_id', 'job_id'])
    op.create_index('idx_applications_user_applied', 'user_job_applications', ['user_id', sa.text('applied_on DESC')])

    # ------------------------------------------------------------------
    # NOTIFICATIONS
    # ------------------------------------------------------------------
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', sa.String(50)),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True)),
        sa.Column('type', sa.String(60), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('action_url', sa.Text),
        sa.Column('is_read', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('sent_via', postgresql.ARRAY(sa.Text)),
        sa.Column('priority', sa.String(10), nullable=False, server_default='medium'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now() + INTERVAL '90 days'")),
        sa.CheckConstraint("priority IN ('low','medium','high')", name='ck_notifications_priority'),
    )
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notifications_user_created', 'notifications', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_notifications_expires', 'notifications', ['expires_at'])

    # ------------------------------------------------------------------
    # RESULTS
    # ------------------------------------------------------------------
    op.create_table(
        'results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='SET NULL')),
        sa.Column('result_type', sa.String(50), nullable=False),
        sa.Column('result_phase', sa.String(100)),
        sa.Column('result_title', sa.String(500), nullable=False),
        sa.Column('result_date', sa.Date),
        sa.Column('result_links', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('cut_off_marks', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('statistics', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('is_final', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("status IN ('active','revised','cancelled')", name='ck_results_status'),
    )
    op.create_index('idx_results_job_id', 'results', ['job_id'])

    # ------------------------------------------------------------------
    # ADMIT CARDS
    # ------------------------------------------------------------------
    op.create_table(
        'admit_cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='SET NULL')),
        sa.Column('exam_name', sa.String(500), nullable=False),
        sa.Column('exam_phase', sa.String(100)),
        sa.Column('release_date', sa.Date),
        sa.Column('exam_date_start', sa.Date),
        sa.Column('exam_date_end', sa.Date),
        sa.Column('exam_mode', sa.String(50)),
        sa.Column('download_link', sa.Text),
        sa.Column('exam_city_link', sa.Text),
        sa.Column('mock_test_link', sa.Text),
        sa.Column('instructions', sa.Text),
        sa.Column('reporting_time', sa.String(50)),
        sa.Column('exam_timing', sa.String(100)),
        sa.Column('important_documents', postgresql.ARRAY(sa.Text)),
        sa.Column('exam_centers', postgresql.ARRAY(sa.Text)),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("status IN ('active','expired')", name='ck_admit_cards_status'),
    )
    op.create_index('idx_admit_cards_job_id', 'admit_cards', ['job_id'])

    # ------------------------------------------------------------------
    # ANSWER KEYS
    # ------------------------------------------------------------------
    op.create_table(
        'answer_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='SET NULL')),
        sa.Column('exam_name', sa.String(500), nullable=False),
        sa.Column('exam_phase', sa.String(100)),
        sa.Column('paper_name', sa.String(255)),
        sa.Column('release_date', sa.Date),
        sa.Column('answer_key_links', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('subject_wise_links', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('objection_start', sa.Date),
        sa.Column('objection_end', sa.Date),
        sa.Column('objection_fee', sa.Integer),
        sa.Column('objection_link', sa.Text),
        sa.Column('response_sheet_link', sa.Text),
        sa.Column('question_paper_link', sa.Text),
        sa.Column('total_questions', sa.Integer),
        sa.Column('status', sa.String(30), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("status IN ('active','expired','final_published')", name='ck_answer_keys_status'),
    )
    op.create_index('idx_answer_keys_job_id', 'answer_keys', ['job_id'])

    # ------------------------------------------------------------------
    # ADMIN LOGS
    # ------------------------------------------------------------------
    op.create_table(
        'admin_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('details', sa.Text),
        sa.Column('changes', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.Text),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now() + INTERVAL '30 days'")),
    )
    op.create_index('idx_admin_logs_admin_ts', 'admin_logs', ['admin_id', sa.text('timestamp DESC')])
    op.create_index('idx_admin_logs_expires', 'admin_logs', ['expires_at'])

    # ------------------------------------------------------------------
    # ROLE PERMISSIONS
    # ------------------------------------------------------------------
    op.create_table(
        'role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('resource', sa.String(50), nullable=False),
        sa.Column('actions', postgresql.JSONB, nullable=False),
        sa.Column('field_restrictions', postgresql.ARRAY(sa.Text), nullable=False, server_default='{}'),
        sa.Column('is_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_restricted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('role', 'resource', name='uq_role_resource'),
        sa.CheckConstraint("role IN ('user','operator','admin')", name='ck_role_permissions_role'),
    )
    op.create_index('idx_role_permissions_role', 'role_permissions', ['role', 'resource'])

    # ------------------------------------------------------------------
    # ACCESS AUDIT LOGS
    # ------------------------------------------------------------------
    op.create_table(
        'access_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('resource', sa.String(50)),
        sa.Column('changes', postgresql.JSONB),
        sa.Column('reason', sa.Text),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_audit_logs_role', 'access_audit_logs', ['role', sa.text('timestamp DESC')])
    op.create_index('idx_audit_logs_admin', 'access_audit_logs', ['admin_id', sa.text('timestamp DESC')])

    # ------------------------------------------------------------------
    # ADMISSIONS
    # ------------------------------------------------------------------
    op.create_table(
        'admissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('slug', sa.String(320), unique=True, nullable=False),
        sa.Column('admission_type', sa.String(30), nullable=False),
        sa.Column('course_name', sa.String(200)),
        sa.Column('conducting_body', sa.String(200)),
        sa.Column('total_seats', sa.Integer),
        sa.Column('description', sa.Text),
        sa.Column('eligibility', postgresql.JSONB),
        sa.Column('application_dates', postgresql.JSONB),
        sa.Column('application_fee', postgresql.JSONB),
        sa.Column('application_link', sa.Text),
        sa.Column('notification_pdf', sa.Text),
        sa.Column('syllabus_link', sa.Text),
        sa.Column('exam_pattern', postgresql.JSONB),
        sa.Column('selection_process', sa.Text),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('is_featured', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('views', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("admission_type IN ('ug','pg','diploma','certificate','school','entrance_exam')", name='ck_admissions_type'),
        sa.CheckConstraint("status IN ('active','expired','upcoming')", name='ck_admissions_status'),
    )
    op.create_index('idx_admissions_slug', 'admissions', ['slug'])
    op.create_index('idx_admissions_status', 'admissions', ['status', sa.text('created_at DESC')])
    op.create_index('idx_admissions_type', 'admissions', ['admission_type'])
    op.create_index('idx_admissions_eligibility', 'admissions', ['eligibility'], postgresql_using='gin')

    # ------------------------------------------------------------------
    # YOJANAS
    # ------------------------------------------------------------------
    op.create_table(
        'yojanas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('slug', sa.String(320), unique=True, nullable=False),
        sa.Column('yojana_type', sa.String(30), nullable=False),
        sa.Column('state', sa.String(100)),
        sa.Column('department', sa.String(200)),
        sa.Column('short_description', sa.Text),
        sa.Column('full_description', sa.Text),
        sa.Column('eligibility', sa.Text),
        sa.Column('benefits', sa.Text),
        sa.Column('benefit_amount', sa.String(100)),
        sa.Column('installment_details', sa.Text),
        sa.Column('how_to_apply', sa.Text),
        sa.Column('required_documents', postgresql.ARRAY(sa.Text)),
        sa.Column('application_link', sa.Text),
        sa.Column('official_website', sa.Text),
        sa.Column('guidelines_pdf', sa.Text),
        sa.Column('helpline', sa.String(50)),
        sa.Column('email', sa.String(200)),
        sa.Column('start_date', sa.Date),
        sa.Column('last_date', sa.Date),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('is_featured', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('views', sa.Integer, nullable=False, server_default='0'),
        sa.Column('applicants_count', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("yojana_type IN ('central','state','scholarship','pension','subsidy','insurance','loan')", name='ck_yojanas_type'),
        sa.CheckConstraint("status IN ('active','expired','upcoming')", name='ck_yojanas_status'),
    )
    op.create_index('idx_yojanas_slug', 'yojanas', ['slug'])
    op.create_index('idx_yojanas_type', 'yojanas', ['yojana_type'])
    op.create_index('idx_yojanas_status', 'yojanas', ['status', 'is_active'])

    # ------------------------------------------------------------------
    # BOARD RESULTS
    # ------------------------------------------------------------------
    op.create_table(
        'board_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('board_name', sa.String(100), nullable=False),
        sa.Column('class', sa.String(10), nullable=False),
        sa.Column('stream', sa.String(30)),
        sa.Column('exam_year', sa.Integer, nullable=False),
        sa.Column('result_type', sa.String(30), nullable=False, server_default='regular'),
        sa.Column('exam_start_date', sa.Date),
        sa.Column('exam_end_date', sa.Date),
        sa.Column('result_date', sa.Date),
        sa.Column('result_time', sa.String(20)),
        sa.Column('result_link', sa.Text),
        sa.Column('marksheet_download_link', sa.Text),
        sa.Column('topper_list_link', sa.Text),
        sa.Column('date_sheet_link', sa.Text),
        sa.Column('statistics', postgresql.JSONB),
        sa.Column('how_to_check', sa.Text),
        sa.Column('alternative_links', postgresql.ARRAY(sa.Text)),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('views', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("result_type IN ('regular','supplementary','compartment','improvement')", name='ck_board_results_type'),
        sa.CheckConstraint("status IN ('active','expired')", name='ck_board_results_status'),
    )
    op.create_index('idx_board_results_board', 'board_results', ['board_name'])
    op.create_index('idx_board_results_year', 'board_results', [sa.text('exam_year DESC')])
    op.create_index('idx_board_results_statistics', 'board_results', ['statistics'], postgresql_using='gin')

    # ------------------------------------------------------------------
    # CATEGORIES
    # ------------------------------------------------------------------
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(220), unique=True, nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL')),
        sa.Column('type', sa.String(30), nullable=False),
        sa.Column('icon', sa.String(100)),
        sa.Column('description', sa.Text),
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('job_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('meta_title', sa.String(300)),
        sa.Column('meta_description', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("type IN ('organization','job_type','department','board')", name='ck_categories_type'),
    )
    op.create_index('idx_categories_slug', 'categories', ['slug'])
    op.create_index('idx_categories_type', 'categories', ['type'])
    op.create_index('idx_categories_parent', 'categories', ['parent_id'])
    op.create_index('idx_categories_order', 'categories', ['display_order', 'type'])

    # ------------------------------------------------------------------
    # PAGE VIEWS
    # ------------------------------------------------------------------
    op.create_table(
        'page_views',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(30), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True)),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('session_id', sa.String(100)),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.Text),
        sa.Column('device_type', sa.String(20)),
        sa.Column('browser', sa.String(50)),
        sa.Column('os', sa.String(50)),
        sa.Column('referrer', sa.Text),
        sa.Column('page_url', sa.Text),
        sa.Column('time_spent_seconds', sa.Integer),
        sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("entity_type IN ('job','result','admit_card','admission','yojana','page')", name='ck_page_views_entity_type'),
        sa.CheckConstraint("device_type IN ('desktop','mobile','tablet')", name='ck_page_views_device_type'),
    )
    op.create_index('idx_page_views_entity', 'page_views', ['entity_type', 'entity_id'])
    op.create_index('idx_page_views_user', 'page_views', ['user_id', sa.text('viewed_at DESC')])
    op.create_index('idx_page_views_date', 'page_views', [sa.text('viewed_at DESC')])

    # ------------------------------------------------------------------
    # SEARCH LOGS
    # ------------------------------------------------------------------
    op.create_table(
        'search_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('session_id', sa.String(100)),
        sa.Column('search_query', sa.String(500), nullable=False),
        sa.Column('filters_applied', postgresql.JSONB),
        sa.Column('results_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('clicked_results', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('first_click_position', sa.Integer),
        sa.Column('time_to_first_click_seconds', sa.Integer),
        sa.Column('no_results', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('searched_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_search_logs_user', 'search_logs', ['user_id', sa.text('searched_at DESC')])
    op.create_index('idx_search_logs_query', 'search_logs', ['search_query'])
    op.create_index('idx_search_logs_date', 'search_logs', [sa.text('searched_at DESC')])
    op.create_index('idx_search_logs_filters', 'search_logs', ['filters_applied'], postgresql_using='gin')

    # ------------------------------------------------------------------
    # updated_at TRIGGERS
    # Ensures updated_at is always current even on direct SQL writes,
    # not just ORM updates.
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION _set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    for _tbl in [
        'users', 'user_profiles', 'job_vacancies', 'role_permissions',
        'results', 'admit_cards', 'answer_keys', 'admissions',
        'yojanas', 'board_results', 'categories',
    ]:
        op.execute(f"""
            CREATE TRIGGER trg_{_tbl}_updated_at
            BEFORE UPDATE ON {_tbl}
            FOR EACH ROW EXECUTE FUNCTION _set_updated_at();
        """)

    # ------------------------------------------------------------------
    # DEFAULT ROLE PERMISSIONS SEED
    # Populates the baseline RBAC matrix so authenticated requests don't
    # return 403 on a fresh deployment.
    # ------------------------------------------------------------------
    import json as _json
    _permissions = [
        # (role, resource, actions_dict, field_restrictions_pg_literal)
        ('user', 'jobs',          {'GET': True,  'POST': False, 'PUT': False, 'DELETE': False}, '{}'),
        ('user', 'applications',  {'GET': True,  'POST': True,  'PUT': True,  'DELETE': True},  '{}'),
        ('user', 'notifications', {'GET': True,  'POST': False, 'PUT': True,  'DELETE': True},  '{}'),
        ('user', 'users',         {'GET': True,  'POST': False, 'PUT': True,  'DELETE': False}, '{}'),
        ('user', 'admin',         {'GET': False, 'POST': False, 'PUT': False, 'DELETE': False}, '{}'),
        ('operator', 'jobs',          {'GET': True,  'POST': False, 'PUT': True,  'DELETE': False}, '{salary_initial,salary_max,total_vacancies,vacancy_breakdown}'),
        ('operator', 'applications',  {'GET': True,  'POST': False, 'PUT': False, 'DELETE': False}, '{}'),
        ('operator', 'notifications', {'GET': True,  'POST': False, 'PUT': False, 'DELETE': False}, '{}'),
        ('operator', 'users',         {'GET': True,  'POST': False, 'PUT': False, 'DELETE': False}, '{password_hash}'),
        ('operator', 'admin',         {'GET': False, 'POST': False, 'PUT': False, 'DELETE': False}, '{}'),
        ('admin', 'jobs',          {'GET': True, 'POST': True, 'PUT': True, 'DELETE': True}, '{}'),
        ('admin', 'applications',  {'GET': True, 'POST': True, 'PUT': True, 'DELETE': True}, '{}'),
        ('admin', 'notifications', {'GET': True, 'POST': True, 'PUT': True, 'DELETE': True}, '{}'),
        ('admin', 'users',         {'GET': True, 'POST': True, 'PUT': True, 'DELETE': True}, '{}'),
        ('admin', 'admin',         {'GET': True, 'POST': True, 'PUT': True, 'DELETE': True}, '{}'),
    ]
    for _role, _resource, _actions, _fields in _permissions:
        _actions_sql = _json.dumps(_actions).replace("'", "''")
        op.execute(f"""
            INSERT INTO role_permissions (id, role, resource, actions, field_restrictions)
            VALUES (
                gen_random_uuid(), '{_role}', '{_resource}',
                '{_actions_sql}'::jsonb, '{_fields}'::text[]
            )
            ON CONFLICT (role, resource) DO NOTHING;
        """)

    # Grant all privileges to the app user
    op.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hermes_user")
    op.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hermes_user")


def downgrade() -> None:
    # Drop triggers and shared function before dropping tables
    for _tbl in [
        'categories', 'board_results', 'yojanas', 'admissions',
        'answer_keys', 'admit_cards', 'results', 'role_permissions',
        'job_vacancies', 'user_profiles', 'users',
    ]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{_tbl}_updated_at ON {_tbl};")
    op.execute("DROP FUNCTION IF EXISTS _set_updated_at();")

    op.drop_table('search_logs')
    op.drop_table('page_views')
    op.drop_table('categories')
    op.drop_table('board_results')
    op.drop_table('yojanas')
    op.drop_table('admissions')
    op.drop_table('access_audit_logs')
    op.drop_table('role_permissions')
    op.drop_table('admin_logs')
    op.drop_table('answer_keys')
    op.drop_table('admit_cards')
    op.drop_table('results')
    op.drop_table('notifications')
    op.drop_table('user_job_applications')
    op.drop_table('job_vacancies')
    op.drop_table('user_profiles')
    op.drop_table('users')
