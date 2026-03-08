"""
Auth middleware for the user frontend.

Provides the ``@login_required`` decorator that redirects unauthenticated
requests to the login page.

The decorator also attempts a transparent token refresh when the access
token has expired (the backend returns 401 with code AUTH_TOKEN_EXPIRED).
If the refresh succeeds the original view is called without the user
noticing. If the refresh fails (refresh token also expired or blocklisted)
the session is cleared and the user is sent to the login page.
"""
from functools import wraps

from flask import flash, redirect, session, url_for

from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import (
    clear_session,
    get_access_token,
    get_refresh_token,
    is_authenticated,
    update_tokens,
)


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
