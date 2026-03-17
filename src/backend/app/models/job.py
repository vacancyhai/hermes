"""
JobVacancy and UserJobApplication models
"""
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class JobVacancy(db.Model):
    __tablename__ = 'job_vacancies'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(500), unique=True, nullable=False)
    organization = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(255))
    post_code = db.Column(db.String(100))
    job_type = db.Column(db.String(50), nullable=False, default='latest_job')
    employment_type = db.Column(db.String(50), default='permanent')
    qualification_level = db.Column(db.String(50))
    total_vacancies = db.Column(db.Integer)
    vacancy_breakdown = db.Column(JSONB, nullable=False, default=dict)
    description = db.Column(db.Text)
    short_description = db.Column(db.Text)
    eligibility = db.Column(JSONB, nullable=False, default=dict)
    application_details = db.Column(JSONB, nullable=False, default=dict)
    notification_date = db.Column(db.Date)
    application_start = db.Column(db.Date)
    application_end = db.Column(db.Date)
    last_date_fee = db.Column(db.Date)
    admit_card_release = db.Column(db.Date)
    exam_city_release = db.Column(db.Date)
    exam_start = db.Column(db.Date)
    exam_end = db.Column(db.Date)
    correction_start = db.Column(db.Date)
    correction_end = db.Column(db.Date)
    answer_key_release = db.Column(db.Date)
    result_date = db.Column(db.Date)
    exam_details = db.Column(JSONB, nullable=False, default=dict)
    salary_initial = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    salary = db.Column(JSONB, nullable=False, default=dict)
    selection_process = db.Column(JSONB, nullable=False, default=list)
    documents_required = db.Column(JSONB, nullable=False, default=list)
    status = db.Column(db.String(20), nullable=False, default='active')
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_urgent = db.Column(db.Boolean, nullable=False, default=False)
    is_trending = db.Column(db.Boolean, nullable=False, default=False)
    priority = db.Column(db.SmallInteger, nullable=False, default=0)
    meta_title = db.Column(db.String(500))
    meta_description = db.Column(db.Text)
    meta_keywords = db.Column(db.ARRAY(db.Text))
    version = db.Column(db.Integer, nullable=False, default=1)
    views = db.Column(db.Integer, nullable=False, default=0)
    applications_count = db.Column(db.Integer, nullable=False, default=0)
    shares_count = db.Column(db.Integer, nullable=False, default=0)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'))
    published_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = db.relationship('UserJobApplication', back_populates='job', cascade='all, delete-orphan')
    # Relationship to the user who created this job; used for eager loading to avoid N+1 queries.
    created_by_user = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<JobVacancy {self.job_title}>'


class UserJobApplication(db.Model):
    __tablename__ = 'user_job_applications'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('job_vacancies.id', ondelete='CASCADE'), nullable=False)
    application_number = db.Column(db.String(100))
    is_priority = db.Column(db.Boolean, nullable=False, default=False)
    applied_on = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    exam_center = db.Column(db.String(255))
    admit_card_downloaded = db.Column(db.Boolean, nullable=False, default=False)
    exam_appeared = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(50), nullable=False, default='applied')
    notes = db.Column(db.Text)
    reminders = db.Column(JSONB, nullable=False, default=list)
    result_info = db.Column(JSONB, nullable=False, default=dict)

    __table_args__ = (db.UniqueConstraint('user_id', 'job_id', name='uq_user_job_application'),)

    user = db.relationship('User', back_populates='applications')
    job = db.relationship('JobVacancy', back_populates='applications')

    def __repr__(self):
        return f'<UserJobApplication user={self.user_id} job={self.job_id}>'
