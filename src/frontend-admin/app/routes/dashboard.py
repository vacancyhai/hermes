"""
Dashboard Routes — Admin Frontend

Shows a summary: total jobs (by status), total users, recent applications.

Template: dashboard/index.html
"""
from flask import Blueprint, flash, redirect, render_template, session, url_for

from app.middleware.auth_middleware import login_required
from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import get_access_token

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
_api = APIClient()


@bp.route('/', methods=['GET'])
@login_required
def index():
    access_token = get_access_token(session)

    jobs_data = {}
    users_data = {}

    try:
        jobs_data = _api.get_jobs(access_token, per_page=5, page=1)
    except APIError as e:
        flash(e.message, 'error')

    try:
        users_data = _api.get_users(access_token, page=1, per_page=5)
    except APIError as e:
        flash(e.message, 'error')

    recent_jobs = jobs_data.get('jobs', [])
    jobs_meta = jobs_data.get('meta', {})
    recent_users = users_data.get('users', [])
    users_meta = users_data.get('meta', {})

    return render_template(
        'pages/dashboard/index.html',
        recent_jobs=recent_jobs,
        jobs_meta=jobs_meta,
        recent_users=recent_users,
        users_meta=users_meta,
    )

