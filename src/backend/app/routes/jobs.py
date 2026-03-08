"""
Job Vacancy Routes

GET    /api/v1/jobs              — list jobs (public, paginated, filterable)
GET    /api/v1/jobs/<slug>       — job detail (public; increments views)
POST   /api/v1/jobs              — create job (operator / admin)
PUT    /api/v1/jobs/<job_id>     — update job (operator / admin)
DELETE /api/v1/jobs/<job_id>     — soft delete job (admin only)
"""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.middleware.rate_limiter import limiter
from app.services import job_service
from app.utils.constants import ErrorCode
from app.utils.decorators import admin_required, operator_required
from app.validators.job_validator import CreateJobSchema, JobSearchSchema, UpdateJobSchema

bp = Blueprint('jobs', __name__, url_prefix='/api/v1/jobs')

_search_schema = JobSearchSchema()
_create_schema = CreateJobSchema()
_update_schema = UpdateJobSchema()


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@bp.route('', methods=['GET'])
@limiter.limit('100 per minute')
def list_jobs():
    filters, err = _load_args(_search_schema)
    if err:
        return err

    result = job_service.get_jobs(filters)
    return _ok(
        [_serialize_job(j) for j in result['items']],
        meta={
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
        },
    )


@bp.route('/<slug>', methods=['GET'])
@limiter.limit('200 per minute')
def get_job(slug):
    try:
        job = job_service.get_job_by_slug(slug)
    except ValueError:
        return _err(ErrorCode.NOT_FOUND_JOB, 'Job not found.', 404)
    return _ok(_serialize_job(job))


# ---------------------------------------------------------------------------
# Staff endpoints (operator or admin)
# ---------------------------------------------------------------------------

@bp.route('', methods=['POST'])
@jwt_required()
@operator_required
@limiter.limit('20 per minute')
def create_job():
    data, err = _load_json(_create_schema)
    if err:
        return err

    job = job_service.create_job(data, created_by=get_jwt_identity())

    # Dispatch job-notification task for newly published jobs
    from app.utils.constants import JobStatus
    if job.status == JobStatus.ACTIVE:
        from app.tasks.notification_tasks import send_new_job_notifications
        send_new_job_notifications.delay(str(job.id))

    return _ok(_serialize_job(job), 201)


@bp.route('/<job_id>', methods=['PUT'])
@jwt_required()
@operator_required
def update_job(job_id):
    data, err = _load_json(_update_schema)
    if err:
        return err

    try:
        job = job_service.update_job(job_id, data)
    except ValueError:
        return _err(ErrorCode.NOT_FOUND_JOB, 'Job not found.', 404)
    return _ok(_serialize_job(job))


# ---------------------------------------------------------------------------
# Admin-only endpoints
# ---------------------------------------------------------------------------

@bp.route('/<job_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_job(job_id):
    try:
        job_service.delete_job(job_id)
    except ValueError:
        return _err(ErrorCode.NOT_FOUND_JOB, 'Job not found.', 404)
    return _ok({'message': 'Job archived successfully.'})


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _load_args(schema):
    """Parse + validate query-string args. Returns (data, None) or (None, err)."""
    try:
        return schema.load(request.args.to_dict()), None
    except ValidationError as e:
        return None, _err(ErrorCode.VALIDATION_ERROR, 'Invalid query parameters.', 400,
                          details=_flatten(e.messages))


def _load_json(schema):
    """Parse + validate request JSON. Returns (data, None) or (None, err)."""
    try:
        return schema.load(request.get_json(silent=True) or {}), None
    except ValidationError as e:
        return None, _err(ErrorCode.VALIDATION_ERROR, 'Invalid request data.', 400,
                          details=_flatten(e.messages))


def _ok(data, status=200, meta=None):
    body = {'success': True, 'data': data}
    if meta:
        body.update(meta)
    return jsonify(body), status


def _err(code, message, status, details=None):
    return jsonify({
        'success': False,
        'error': {
            'code': code,
            'message': message,
            'details': details or [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': request.headers.get('X-Request-ID', ''),
        },
    }), status


def _flatten(messages):
    result = []
    for field, errors in messages.items():
        if isinstance(errors, list):
            for e in errors:
                result.append(f'{field}: {e}')
        else:
            result.append(f'{field}: {errors}')
    return result


def _serialize_job(job) -> dict:
    """Convert JobVacancy ORM instance to a JSON-safe dict."""
    def _d(val):
        return val.isoformat() if val else None

    return {
        'id': str(job.id),
        'job_title': job.job_title,
        'slug': job.slug,
        'organization': job.organization,
        'department': job.department,
        'post_code': job.post_code,
        'job_type': job.job_type,
        'employment_type': job.employment_type,
        'qualification_level': job.qualification_level,
        'total_vacancies': job.total_vacancies,
        'vacancy_breakdown': job.vacancy_breakdown,
        'description': job.description,
        'short_description': job.short_description,
        'eligibility': job.eligibility,
        'application_details': job.application_details,
        'notification_date': _d(job.notification_date),
        'application_start': _d(job.application_start),
        'application_end': _d(job.application_end),
        'last_date_fee': _d(job.last_date_fee),
        'admit_card_release': _d(job.admit_card_release),
        'exam_start': _d(job.exam_start),
        'exam_end': _d(job.exam_end),
        'result_date': _d(job.result_date),
        'exam_details': job.exam_details,
        'salary_initial': job.salary_initial,
        'salary_max': job.salary_max,
        'salary': job.salary,
        'selection_process': job.selection_process,
        'documents_required': job.documents_required,
        'status': job.status,
        'is_featured': job.is_featured,
        'is_urgent': job.is_urgent,
        'is_trending': job.is_trending,
        'priority': job.priority,
        'views': job.views,
        'applications_count': job.applications_count,
        'created_by': str(job.created_by) if job.created_by else None,
        'published_at': _d(job.published_at),
        'created_at': _d(job.created_at),
        'updated_at': _d(job.updated_at),
    }
