"""
Auth Routes — Admin Frontend

Only 'admin' and 'operator' roles may log in here. If a user with role
'user' attempts to log in, the session is not saved and an error is shown.

No registration route exists — admin accounts are created directly via
the backend or via a future admin creation endpoint.

Templates expected (Story 6):
  auth/login.html
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_user, logout_user

from app.models.user import User
from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import (
    _decode_jwt_payload,
    clear_session,
    get_access_token,
    get_user_data,
    save_login_session,
)

bp = Blueprint('auth', __name__, url_prefix='/auth')
_api = APIClient()

_ALLOWED_ROLES = ('admin', 'operator')


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')

    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not email or not password:
        flash('Email and password are required.', 'error')
        return render_template('auth/login.html', email=email)

    try:
        data = _api.login(email, password)
    except APIError as e:
        flash(e.message, 'error')
        return render_template('auth/login.html', email=email)

    # Decode role from JWT before saving session — reject non-admin/operator
    try:
        role = _decode_jwt_payload(data['access_token']).get('role', '')
    except (ValueError, KeyError):
        flash('Authentication failed. Please try again.', 'error')
        return render_template('auth/login.html', email=email)

    if role not in _ALLOWED_ROLES:
        # Blocklist the issued token so it cannot be reused
        try:
            _api.logout(data['access_token'], data.get('refresh_token', ''))
        except APIError:
            pass
        flash('Access denied. This portal is for administrators and operators only.', 'error')
        return render_template('auth/login.html', email=email)

    save_login_session(session, data)
    login_user(User.from_session(get_user_data(session)))

    next_page = request.args.get('next')
    if next_page and next_page.startswith('/'):
        return redirect(next_page)
    return redirect(url_for('dashboard.index'))


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@bp.route('/logout', methods=['POST'])
def logout():
    access_token = get_access_token(session)

    if access_token:
        try:
            _api.logout(access_token, session.get('refresh_token', ''))
        except APIError:
            pass

    logout_user()
    clear_session(session)
    return redirect(url_for('auth.login'))

