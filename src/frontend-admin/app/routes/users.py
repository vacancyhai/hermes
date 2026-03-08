"""
User Management Routes — Admin Frontend

Lists all users, views a user, and changes user status (active/suspended/banned).
Admin-only.

Templates:
  users/list.html
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.middleware.auth_middleware import role_required
from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import get_access_token

bp = Blueprint('users', __name__, url_prefix='/users')
_api = APIClient()

_STATUSES = ['active', 'suspended', 'banned']


@bp.route('/', methods=['GET'])
@role_required('admin')
def list_users():
    access_token = get_access_token(session)
    params = {'page': request.args.get('page', 1, type=int), 'per_page': 20}
    for key in ('q', 'status', 'role'):
        val = request.args.get(key, '').strip()
        if val:
            params[key] = val

    try:
        data = _api.get_users(access_token, **params)
    except APIError as e:
        flash(e.message, 'error')
        data = {}

    return render_template('pages/users/list.html',
                           users=data.get('users', []),
                           meta=data.get('meta', {}),
                           filters=params,
                           statuses=_STATUSES)


@bp.route('/<user_id>/status', methods=['POST'])
@role_required('admin')
def update_status(user_id):
    access_token = get_access_token(session)
    status = request.form.get('status', '').strip()
    if status not in _STATUSES:
        flash('Invalid status value.', 'error')
        return redirect(url_for('users.list_users'))

    try:
        _api.update_user_status(access_token, user_id, status)
        flash(f'User status updated to {status}.', 'success')
    except APIError as e:
        flash(e.message, 'error')

    return redirect(url_for('users.list_users'))

