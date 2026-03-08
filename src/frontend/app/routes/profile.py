"""
Profile Routes — User Frontend

Handles view/edit profile, applications list, and withdrawing an application.
All routes are login-protected.

Templates:
  profile/index.html
  profile/edit.html
  profile/applications.html
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.middleware.auth_middleware import login_required
from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import get_access_token

bp = Blueprint('profile', __name__, url_prefix='/profile')
_api = APIClient()


@bp.route('/', methods=['GET'])
@login_required
def index():
    access_token = get_access_token(session)
    try:
        data = _api.get_profile(access_token)
    except APIError as e:
        flash(e.message, 'error')
        data = {}

    user = data.get('user', {})
    profile = data.get('profile', {})
    return render_template('pages/profile/index.html', user=user, profile=profile)


@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    access_token = get_access_token(session)

    if request.method == 'GET':
        try:
            data = _api.get_profile(access_token)
        except APIError as e:
            flash(e.message, 'error')
            data = {}
        user = data.get('user', {})
        profile = data.get('profile', {})
        return render_template('pages/profile/edit.html', user=user, profile=profile)

    payload = {}
    for field in ('full_name', 'phone', 'date_of_birth', 'gender', 'category',
                  'state', 'city', 'pincode', 'highest_qualification'):
        val = request.form.get(field, '').strip()
        if val:
            payload[field] = val

    try:
        _api.update_profile(access_token, payload)
        flash('Profile updated successfully.', 'success')
    except APIError as e:
        flash(e.message, 'error')

    return redirect(url_for('profile.index'))


@bp.route('/applications', methods=['GET'])
@login_required
def applications():
    access_token = get_access_token(session)
    page = request.args.get('page', 1, type=int)
    try:
        data = _api.get_applications(access_token, page=page)
    except APIError as e:
        flash(e.message, 'error')
        data = {}

    apps = data.get('applications', [])
    meta = data.get('meta', {})
    return render_template('pages/profile/applications.html', applications=apps, meta=meta)


@bp.route('/applications/<application_id>/withdraw', methods=['POST'])
@login_required
def withdraw(application_id):
    access_token = get_access_token(session)
    try:
        _api.withdraw_application(access_token, application_id)
        flash('Application withdrawn.', 'success')
    except APIError as e:
        flash(e.message, 'error')
    return redirect(url_for('profile.applications'))

