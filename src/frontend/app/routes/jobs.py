"""
Jobs Routes — User Frontend

Handles job listing, search, and detail pages.
Calls the backend API via APIClient; unauthenticated users can browse
jobs but must log in to apply.

Templates:
  jobs/list.html
  jobs/detail.html
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.middleware.auth_middleware import login_required
from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import get_access_token

bp = Blueprint('jobs', __name__, url_prefix='/jobs')
_api = APIClient()


@bp.route('/', methods=['GET'])
def list_jobs():
    params = {
        'page': request.args.get('page', 1, type=int),
        'per_page': 12,
    }
    for key in ('q', 'type', 'qualification', 'organization'):
        val = request.args.get(key, '').strip()
        if val:
            params[key] = val

    access_token = get_access_token(session)
    try:
        data = _api.get_jobs(access_token=access_token, **params)
    except APIError as e:
        flash(e.message, 'error')
        data = {'jobs': [], 'meta': {}}

    jobs = data.get('jobs', [])
    meta = data.get('meta', {})
    return render_template('pages/jobs/list.html', jobs=jobs, meta=meta, filters=params)


@bp.route('/<slug>', methods=['GET'])
def job_detail(slug):
    access_token = get_access_token(session)
    try:
        data = _api.get_job(slug, access_token=access_token)
    except APIError as e:
        if e.status_code == 404:
            return render_template('errors/404.html'), 404
        flash(e.message, 'error')
        return redirect(url_for('jobs.list_jobs'))

    job = data.get('job', {})
    already_applied = False

    if access_token:
        try:
            apps_data = _api.get_applications(access_token)
            app_job_ids = {a.get('job_id') for a in apps_data.get('applications', [])}
            already_applied = job.get('id') in app_job_ids
        except APIError:
            pass

    return render_template('pages/jobs/detail.html', job=job, already_applied=already_applied)


@bp.route('/<job_id>/apply', methods=['POST'])
@login_required
def apply(job_id):
    access_token = get_access_token(session)
    try:
        _api.apply_to_job(access_token, job_id)
        flash('Application submitted successfully.', 'success')
    except APIError as e:
        flash(e.message, 'error')

    slug = request.form.get('slug', '')
    if slug:
        return redirect(url_for('jobs.job_detail', slug=slug))
    return redirect(url_for('jobs.list_jobs'))

