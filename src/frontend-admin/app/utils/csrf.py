"""
Lightweight CSRF protection using session-bound tokens.

Usage
-----
  from app.utils.csrf import generate_csrf_token, validate_csrf_token

In app factory:
  app.jinja_env.globals['csrf_token'] = generate_csrf_token
  app.before_request(check_csrf)

In templates:
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
"""
import hashlib
import os

from flask import abort, request, session


_CSRF_SESSION_KEY = '_csrf_token'


def generate_csrf_token() -> str:
    """Return the session CSRF token, creating it if it doesn't exist yet."""
    if _CSRF_SESSION_KEY not in session:
        session[_CSRF_SESSION_KEY] = hashlib.sha256(os.urandom(32)).hexdigest()
    return session[_CSRF_SESSION_KEY]


def validate_csrf_token() -> bool:
    """Return True if the token in the form matches the one in the session."""
    session_token = session.get(_CSRF_SESSION_KEY)
    form_token = request.form.get('csrf_token', '')
    return bool(session_token and form_token and session_token == form_token)


def check_csrf() -> None:
    """
    before_request hook — validate CSRF token on all state-changing requests.
    Only checks POST/PUT/PATCH/DELETE; skips GET/HEAD/OPTIONS.
    """
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return
    if not validate_csrf_token():
        abort(400, description='Invalid or missing CSRF token.')
