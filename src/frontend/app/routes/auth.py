"""
Auth Routes — User Frontend

Handles login, register, logout, forgot-password, and reset-password.
All form submissions call the backend API via APIClient; errors are
shown back to the user via flash messages.

Templates expected (implemented in Story 6):
  auth/login.html
  auth/register.html
  auth/forgot_password.html
  auth/reset_password.html
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_user, logout_user

from app.models.user import User
from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import clear_session, save_login_session

bp = Blueprint('auth', __name__, url_prefix='/auth')
_api = APIClient()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('pages/auth/login.html')

    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not email or not password:
        flash('Email and password are required.', 'error')
        return render_template('pages/auth/login.html', email=email)

    try:
        data = _api.login(email, password)
    except APIError as e:
        flash(e.message, 'error')
        return render_template('pages/auth/login.html', email=email)

    save_login_session(session, data)
    user_data = {'user_id': session['user_id'], 'email': session['email'],
                 'full_name': session.get('full_name', ''), 'role': session['role']}
    login_user(User.from_session(user_data))

    next_page = request.args.get('next')
    if next_page and next_page.startswith('/'):
        return redirect(next_page)
    return redirect(url_for('main.index'))


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('pages/auth/register.html')

    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not full_name or not email or not password:
        flash('All fields are required.', 'error')
        return render_template('pages/auth/register.html', full_name=full_name, email=email)

    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('pages/auth/register.html', full_name=full_name, email=email)

    try:
        data = _api.register(full_name, email, password)
    except APIError as e:
        flash(e.message, 'error')
        return render_template('pages/auth/register.html', full_name=full_name, email=email)

    save_login_session(session, data)
    user_data = {'user_id': session['user_id'], 'email': session['email'],
                 'full_name': session.get('full_name', ''), 'role': session['role']}
    login_user(User.from_session(user_data))

    flash('Account created successfully. Please verify your email.', 'success')
    return redirect(url_for('main.index'))


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@bp.route('/logout', methods=['POST'])
def logout():
    access_token = session.get('access_token')
    refresh_token = session.get('refresh_token')

    if access_token:
        try:
            _api.logout(access_token, refresh_token)
        except APIError:
            # Backend logout failed (token may already be expired/blocklisted).
            # Clear the local session regardless.
            pass

    logout_user()
    clear_session(session)
    return redirect(url_for('auth.login'))


# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('pages/auth/forgot_password.html')

    email = request.form.get('email', '').strip()
    if not email:
        flash('Email is required.', 'error')
        return render_template('pages/auth/forgot_password.html')

    try:
        _api.forgot_password(email)
    except APIError as e:
        flash(e.message, 'error')
        return render_template('pages/auth/forgot_password.html', email=email)

    # Always show the same success message regardless of whether the email exists
    # (backend already follows this pattern — prevents email enumeration)
    flash('If an account exists for this email, a password reset link has been sent.', 'success')
    return render_template('pages/auth/forgot_password.html')


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------

@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token', '')

    if request.method == 'GET':
        if not token:
            flash('Invalid or missing reset token.', 'error')
            return redirect(url_for('auth.forgot_password'))
        return render_template('pages/auth/reset_password.html', token=token)

    token = request.form.get('token', '').strip()
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not token or not new_password:
        flash('All fields are required.', 'error')
        return render_template('pages/auth/reset_password.html', token=token)

    if new_password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('pages/auth/reset_password.html', token=token)

    try:
        _api.reset_password(token, new_password)
    except APIError as e:
        flash(e.message, 'error')
        return render_template('pages/auth/reset_password.html', token=token)

    flash('Password reset successfully. Please log in.', 'success')
    return redirect(url_for('auth.login'))

