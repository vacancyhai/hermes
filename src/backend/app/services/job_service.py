"""
Job service — all job-vacancy business logic.

Public API:
    get_jobs(filters: dict) -> dict
        — paginated list with optional filters
    
    get_job_by_slug(slug: str) -> JobVacancy
        — public detail view; increments views counter via Redis
    
    get_job_by_id(job_id: str | UUID) -> JobVacancy
        — admin/staff lookup by UUID
    
    create_job(data: dict, created_by: str) -> JobVacancy
        — create a new vacancy (slug auto-generated)
    
    update_job(job_id: str | UUID, data: dict) -> JobVacancy
        — partial update; regenerates slug if title changes
    
    delete_job(job_id: str | UUID) -> JobVacancy
        — soft delete (sets status → 'archived')

All functions raise ValueError with a constant from ErrorCode on failure so
the route layer can map it to the right HTTP status without leaking details.

Redis Resilience:
    - View counter increments are buffered in Redis with graceful fallback.
    - If Redis is unavailable, a warning is logged and views are not counted
      (preferable to flooding PostgreSQL with writes during Redis outage).
"""
from datetime import datetime, timezone
from typing import Dict, Optional
import uuid as _uuid_mod
import logging

from flask import current_app
from redis.exceptions import RedisError
from sqlalchemy import or_, update as sa_update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.job import JobVacancy, UserJobApplication
from app.utils.constants import ApplicationStatus, ErrorCode, JobStatus
from app.utils.helpers import paginate, slugify

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_jobs(filters: dict) -> dict:
    """
    Return a paginate() dict for the job list.

    filters is the already-validated output from JobSearchSchema.load().
    Only 'active' jobs are ever returned — non-active status values are not
    accepted from the public API (status was removed from JobSearchSchema).
    """
    query = (
        JobVacancy.query
        .options(joinedload(JobVacancy.created_by_user))
        .filter(JobVacancy.status == JobStatus.ACTIVE)
    )

    if filters.get('job_type'):
        query = query.filter(JobVacancy.job_type == filters['job_type'])

    if filters.get('qualification_level'):
        query = query.filter(JobVacancy.qualification_level == filters['qualification_level'])

    if filters.get('organization'):
        org = _escape_ilike(filters['organization'])
        query = query.filter(JobVacancy.organization.ilike(f"%{org}%", escape='\\'))

    if filters.get('featured') is True:
        query = query.filter(JobVacancy.is_featured.is_(True))

    if filters.get('urgent') is True:
        query = query.filter(JobVacancy.is_urgent.is_(True))

    if filters.get('q'):
        term = f"%{_escape_ilike(filters['q'])}%"
        query = query.filter(or_(
            JobVacancy.job_title.ilike(term, escape='\\'),
            JobVacancy.organization.ilike(term, escape='\\'),
            JobVacancy.short_description.ilike(term, escape='\\'),
        ))

    query = query.order_by(JobVacancy.priority.desc(), JobVacancy.created_at.desc())
    per_page = min(filters.get('per_page', 20), 100)
    return paginate(query, page=filters.get('page', 1), per_page=per_page)


def get_job_by_slug(slug: str) -> JobVacancy:
    """
    Fetch an active job by slug and increment its view counter via Redis.

    View counts are buffered in Redis (key: "job:views:<job_id>") and
    periodically flushed to PostgreSQL by views_flush_task.flush_job_views.

    Raises:
        ValueError(ErrorCode.NOT_FOUND_JOB) if not found or not active.
    """
    job = JobVacancy.query.filter_by(slug=slug, status=JobStatus.ACTIVE).first()
    if not job:
        raise ValueError(ErrorCode.NOT_FOUND_JOB)

    # Buffer view increment in Redis; flush task writes deltas to DB in bulk.
    try:
        current_app.redis.incr(f"job:views:{job.id}")
    except RedisError as exc:
        # Redis unavailable — log and skip; sacrificing this view count is
        # preferable to flooding PostgreSQL with writes under Redis failure.
        current_app.logger.warning("get_job_by_slug: Redis unavailable, skipping view increment for job %s: %s", job.id, exc)

    return job


def get_job_by_id(job_id: str) -> JobVacancy:
    """
    Fetch a job by UUID regardless of status (used by admin/staff routes).

    Raises:
        ValueError(ErrorCode.NOT_FOUND_JOB) if not found.
    """
    job = db.session.get(JobVacancy, job_id)
    if not job:
        raise ValueError(ErrorCode.NOT_FOUND_JOB)
    return job


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def create_job(data: dict, created_by: str) -> JobVacancy:
    """
    Create a new JobVacancy row.

    - Slug is auto-generated from job_title; a numeric suffix is added if the
      base slug already exists.
    - published_at is set to NOW when status is 'active'.
    - created_by is the authenticated user's UUID string.

    Returns the saved JobVacancy instance.
    """
    base_slug = slugify(data['job_title'])
    slug = _unique_slug(base_slug)

    published_at = None
    if data.get('status', JobStatus.ACTIVE) == JobStatus.ACTIVE:
        published_at = datetime.now(timezone.utc)

    job = JobVacancy(
        job_title=data['job_title'],
        slug=slug,
        organization=data['organization'],
        department=data.get('department'),
        post_code=data.get('post_code'),
        job_type=data['job_type'],
        employment_type=data.get('employment_type', 'permanent'),
        qualification_level=data.get('qualification_level'),
        total_vacancies=data.get('total_vacancies'),
        vacancy_breakdown=data.get('vacancy_breakdown') or {},
        description=data.get('description'),
        short_description=data.get('short_description'),
        eligibility=data['eligibility'],
        application_details=data.get('application_details') or {},
        notification_date=data.get('notification_date'),
        application_start=data.get('application_start'),
        application_end=data.get('application_end'),
        last_date_fee=data.get('last_date_fee'),
        exam_start=data.get('exam_start'),
        exam_end=data.get('exam_end'),
        result_date=data.get('result_date'),
        exam_details=data.get('exam_details') or {},
        salary_initial=data.get('salary_initial'),
        salary_max=data.get('salary_max'),
        salary=data.get('salary') or {},
        selection_process=data.get('selection_process') or [],
        documents_required=data.get('documents_required') or [],
        status=data.get('status', JobStatus.ACTIVE),
        is_featured=data.get('is_featured', False),
        is_urgent=data.get('is_urgent', False),
        is_trending=data.get('is_trending', False),
        priority=data.get('priority', 0),
        meta_title=data.get('meta_title'),
        meta_description=data.get('meta_description'),
        created_by=created_by,
        published_at=published_at,
    )
    db.session.add(job)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Concurrent insert took the slug — use a UUID suffix for guaranteed uniqueness.
        job.slug = _unique_slug_fallback(base_slug)
        db.session.add(job)
        db.session.commit()
    return job


def update_job(job_id: str, data: dict) -> JobVacancy:
    """
    Partial update an existing job.

    Only non-None values from UpdateJobSchema are applied.
    Slug is regenerated when job_title is provided.

    Raises:
        ValueError(ErrorCode.NOT_FOUND_JOB) if job does not exist.
    """
    job = get_job_by_id(job_id)

    # Regenerate slug if title is being changed
    if data.get('job_title') and data['job_title'] != job.job_title:
        base_slug = slugify(data['job_title'])
        job.slug = _unique_slug(base_slug, exclude_id=job.id)

    _UPDATABLE = (
        'job_title', 'organization', 'department', 'post_code', 'job_type',
        'employment_type', 'qualification_level', 'total_vacancies',
        'vacancy_breakdown', 'description', 'short_description', 'eligibility',
        'application_details', 'notification_date', 'application_start',
        'application_end', 'last_date_fee', 'exam_start', 'exam_end',
        'result_date', 'exam_details', 'salary_initial', 'salary_max', 'salary',
        'selection_process', 'documents_required', 'status', 'is_featured',
        'is_urgent', 'is_trending', 'priority', 'meta_title', 'meta_description',
    )
    for field in _UPDATABLE:
        value = data.get(field)
        if value is not None and value != '':
            setattr(job, field, value)

    # Set published_at if the job is being activated for the first time
    if data.get('status') == JobStatus.ACTIVE and job.published_at is None:
        job.published_at = datetime.now(timezone.utc)

    db.session.commit()
    return job


def delete_job(job_id: str) -> None:
    """
    Soft-delete a job by setting its status to 'archived'.

    Also cascades to close all pending applications so users no longer see
    open applications against an archived vacancy.

    Raises:
        ValueError(ErrorCode.NOT_FOUND_JOB) if job does not exist.
    """
    job = get_job_by_id(job_id)
    job.status = JobStatus.ARCHIVED
    # Close all pending applications — prevents users from seeing ghost-open
    # applications against a vacancy that no longer accepts them.
    db.session.execute(
        sa_update(UserJobApplication)
        .where(
            UserJobApplication.job_id == job.id,
            UserJobApplication.status == ApplicationStatus.APPLIED,
        )
        .values(status=ApplicationStatus.REJECTED)
    )
    db.session.commit()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

_MAX_SLUG_ATTEMPTS = 50


def _escape_ilike(value: str) -> str:
    """Escape ILIKE wildcard characters so user input is treated as literal text."""
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def _unique_slug(base_slug: str, exclude_id=None) -> str:
    """
    Return a candidate slug for a new or updated job.

    For creates (exclude_id is None): returns the base slug without any DB
    lookup — the DB unique constraint is the true uniqueness guard.  The caller
    must catch IntegrityError and retry with _unique_slug_fallback().

    For updates (exclude_id set): performs a single point-lookup to detect
    conflicts with *other* jobs and returns a UUID-suffixed slug when one is
    found, avoiding an unnecessary suffix on a no-op title update.
    """
    slug = base_slug or 'job'
    if exclude_id:
        conflict = JobVacancy.query.filter(
            JobVacancy.slug == slug,
            JobVacancy.id != exclude_id,
        ).first()
        if conflict:
            slug = _unique_slug_fallback(slug)
    return slug


def _unique_slug_fallback(base_slug: str) -> str:
    """Return a slug suffixed with an 8-hex UUID fragment; effectively collision-free."""
    return f"{base_slug or 'job'}-{_uuid_mod.uuid4().hex[:8]}"
