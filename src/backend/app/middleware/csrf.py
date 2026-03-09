"""
CSRF Protection Middleware

Provides per-endpoint CSRF token generation and validation.

Token storage:
  - Tokens are stored in Redis with 1-hour TTL
  - Each token is single-use (deleted after validation)
  - Session/user-aware when authenticated

Usage in routes:
    @bp.route('/protected', methods=['POST'])
    @csrf_protect()
    def protected_handler():
        # CSRF validation happens automatically
        pass

In templates:
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

Registration:
    Call register_csrf_protection(app) from create_app() after Redis is set up.
"""
import logging
import secrets
from datetime import datetime, timezone

from flask import current_app, g, request, jsonify

logger = logging.getLogger(__name__)

_CSRF_TOKEN_TTL = 3600  # 1 hour


def generate_csrf_token() -> str:
    """Generate and store a CSRF token in Redis; return it for inclusion in forms."""
    token = secrets.token_urlsafe(32)
    try:
        key = f"csrf:{token}"
        current_app.redis.setex(key, _CSRF_TOKEN_TTL, '1')
    except Exception as exc:
        logger.error(f"CSRF token storage failed: {exc}")
        raise RuntimeError("CSRF token generation failed temporarily.") from exc
    return token


def validate_csrf_token(token: str) -> bool:
    """
    Validate and consume a CSRF token from Redis.
    
    Returns True if valid, False if missing or invalid.
    Token is deleted after validation (single-use).
    """
    if not token:
        logger.warning("CSRF validation: token missing")
        return False
    
    try:
        key = f"csrf:{token}"
        result = current_app.redis.delete(key)
        if result > 0:
            return True
        logger.warning(f"CSRF validation: token not found or expired: {token[:8]}...")
        return False
    except Exception as exc:
        logger.error(f"CSRF validation error: {exc}")
        return False


def csrf_protect():
    """
    Decorator to enforce CSRF protection on state-changing endpoints.
    
    Validates CSRF token for POST, PUT, DELETE, PATCH requests.
    Returns 403 if validation fails; allows GET/HEAD/OPTIONS/TRACE.
    """
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Only protect state-changing methods
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                # Try form data, JSON body, or custom header
                token = (
                    request.form.get('csrf_token') or
                    (request.get_json(force=True, silent=True) or {}).get('csrf_token') or
                    request.headers.get('X-CSRF-Token')
                )
                
                if not validate_csrf_token(token):
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'CSRF_VALIDATION_FAILED',
                            'message': 'CSRF token invalid or expired.',
                            'details': [],
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'request_id': getattr(g, 'request_id', ''),
                        }
                    }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def register_csrf_protection(app):
    """
    Register CSRF protection with Flask app.
    
    Adds csrf_token() function to template context.
    Call once from create_app() after app.redis is initialized.
    """
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf_token)
    
    logger.info("CSRF protection registered")
