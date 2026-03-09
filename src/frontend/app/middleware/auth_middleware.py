"""
Auth middleware for the user frontend.

Provides the ``@login_required`` decorator that redirects unauthenticated
requests to the login page.
"""
from functools import wraps

from flask import redirect, session, url_for

from app.utils.session_manager import is_authenticated


def login_required(f):
    """
    Decorator: redirect to login if the user is not authenticated.

    Usage::

        from app.middleware.auth_middleware import login_required

        @bp.route('/profile')
        @login_required
        def profile():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function
