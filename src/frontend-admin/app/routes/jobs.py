"""
Job Management Routes — Admin Frontend

Handles listing, creating, editing, and deleting job vacancies.
Operator+ required for create/update; admin-only for delete.

Templates:
  jobs/list.html
  jobs/create.html
  jobs/edit.html
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.middleware.auth_middleware import login_required, role_required
from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import get_access_token

bp = Blueprint('jobs', __name__, url_prefix='/jobs')
_api = APIClient()

_JOB_TYPES = [
    ('latest_job', 'Latest Job'),
    ('result', 'Result'),
    ('admit_card', 'Admit Card'),
    ('answer_key', 'Answer Key'),
    ('admission', 'Admission'),
    ('yojana', 'Yojana'),
]
_QUALIFICATIONS = [
    ('10th', '10th Pass'), ('12th', '12th Pass'), ('diploma', 'Diploma'),
    ('graduation', 'Graduate'), ('post_graduation', 'Post Graduate'), ('phd', 'PhD'),
]


@bp.route('/', methods=['GET'])
@login_required
def list_jobs():
    access_token = get_access_token(session)
    params = {
        'page': request.args.get('page', 1, type=int),
        'per_page': 20,
    }
    for key in ('q', 'type', 'status'):
        val = request.args.get(key, '').strip()
        if val:
            params[key] = val

    try:
        data = _api.get_jobs(access_token, **params)
    except APIError as e:
        flash(e.message, 'error')
        data = {}

    return render_template('pages/jobs/list.html',
                           jobs=data.get('jobs', []),
                           meta=data.get('meta', {}),
                           filters=params,
                           job_types=_JOB_TYPES)


@bp.route('/create', methods=['GET', 'POST'])
@role_required('admin', 'operator')
def create_job():
    access_token = get_access_token(session)

    if request.method == 'GET':
        return render_template('pages/jobs/create.html',
                               job_types=_JOB_TYPES,
                               qualifications=_QUALIFICATIONS)

    payload = _collect_job_form()
    try:
        _api.create_job(access_token, payload)
        flash('Job created successfully.', 'success')
        return redirect(url_for('jobs.list_jobs'))
    except APIError as e:
        flash(e.message, 'error')
        return render_template('pages/jobs/create.html',
                               job_types=_JOB_TYPES,
                               qualifications=_QUALIFICATIONS,
                               form_data=payload)


@bp.route('/<slug>/edit', methods=['GET', 'POST'])
@role_required('admin', 'operator')
def edit_job(slug):
    access_token = get_access_token(session)

    if request.method == 'GET':
        try:
            data = _api.get_job(slug, access_token)
        except APIError as e:
            flash(e.message, 'error')
            return redirect(url_for('jobs.list_jobs'))
        return render_template('pages/jobs/edit.html',
                               job=data.get('job', {}),
                               job_types=_JOB_TYPES,
                               qualifications=_QUALIFICATIONS)

    job_id = request.form.get('job_id', '').strip()
    payload = _collect_job_form()
    try:
        _api.update_job(access_token, job_id, payload)
        flash('Job updated successfully.', 'success')
        return redirect(url_for('jobs.list_jobs'))
    except APIError as e:
        flash(e.message, 'error')
        return redirect(url_for('jobs.edit_job', slug=slug))


@bp.route('/<job_id>/delete', methods=['POST'])
@role_required('admin')
def delete_job(job_id):
    access_token = get_access_token(session)
    try:
        _api.delete_job(access_token, job_id)
        flash('Job deleted.', 'success')
    except APIError as e:
        flash(e.message, 'error')
    return redirect(url_for('jobs.list_jobs'))


def _collect_job_form() -> dict:
    """Extract job fields from request.form, skipping blank values."""
    fields = (
        'job_title', 'organization', 'job_type', 'description',
        'total_vacancies', 'salary_min', 'salary_max',
        'application_start', 'application_end', 'exam_date',
        'eligibility', 'qualification_level',
        'official_url', 'apply_url', 'status',
    )
    payload = {}
    for f in fields:
        val = request.form.get(f, '').strip()
        if val:
            payload[f] = val
    for int_field in ('total_vacancies', 'salary_min', 'salary_max'):
        if int_field in payload:
            try:
                payload[int_field] = int(payload[int_field])
            except ValueError:
                pass
    return payload

