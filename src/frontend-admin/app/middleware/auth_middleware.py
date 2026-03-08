"""
Auth middleware for the admin frontend.

Provides two decorators:

``@login_required``
    Redirects unauthenticated requests to the admin login page.

``@role_required(*roles)``
    Redirects to login if the user is not authenticated, and redirects to
    dashboard if the authenticated user's role is not in the allowed set.

Usage::

    from app.middleware.auth_middleware import login_required, role_required

    @bp.route('/dashboard')
    @login_required
    def dashboard(): ...

    @bp.route('/jobs/create')
    @role_required('admin', 'operator')
    def create_job(): ...
"""
from functools import wraps

from flask import flash, redirect, session, url_for

from app.utils.session_manager import clear_session, get_user_data, is_authenticated

_ALLOWED_ROLES = ('admin', 'operator')


def login_required(f):
    """Redirect to login if the user has no valid session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session):
            return redirect(url_for('auth.login'))

        # Ensure role is still admin/operator (guards against stale sessions
        # if a user's role was downgraded while they were logged in)
        data = get_user_data(session)
        if not data or data.get('role') not in _ALLOWED_ROLES:
            clear_session(session)
            flash('Access denied. Admin or operator role required.', 'error')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)

    return decorated_function


def role_required(*roles):
    """
    Restrict access to users whose role is in ``roles``.

    Always implies ``login_required``.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_authenticated(session):
                return redirect(url_for('auth.login'))

            data = get_user_data(session)
            if not data or data.get('role') not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard.index'))

            return f(*args, **kwargs)

        return decorated_function
    return decorator
