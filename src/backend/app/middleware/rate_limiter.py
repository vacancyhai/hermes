"""
Shared Flask-Limiter instance for all routes.

Provides a JWT-aware key function so that:
  - Authenticated requests are rate-limited per user identity (not per IP),
    avoiding false positives for users behind NAT or shared proxies.
  - Unauthenticated requests fall back to the remote IP.

Usage in routes:
    from app.middleware.rate_limiter import limiter

    @bp.route('/endpoint')
    @limiter.limit('20 per minute')
    def endpoint():
        ...

Initialization:
    Call init_limiter(app) once from create_app() after app config is loaded.
    The limiter reads RATELIMIT_ENABLED, RATELIMIT_STORAGE_URI, etc. from
    Flask config — set RATELIMIT_ENABLED=False in tests to disable throttling.

Per-route limit strings follow the Flask-Limiter format:
    'N per second|minute|hour|day'
    e.g. '5 per minute', '100 per hour'

Recommended limits (mirrors settings.py constants):
  - Public read endpoints  : 100 per minute  (RATE_LIMIT_IP_PER_MINUTE)
  - Authenticated endpoints: 1000 per minute (RATE_LIMIT_USER_PER_MINUTE)
  - Login / register       : 5 per minute    (RATE_LIMIT_LOGIN_ATTEMPTS)
"""
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)


def _rate_limit_key() -> str:
    """
    Return the rate-limit bucket key for the current request.

    Resolution order:
      1. If the request carries a valid (or optional) JWT, return 'user:<sub>'.
      2. Otherwise return the remote IP address.

    verify_jwt_in_request(optional=True) does not raise when no token is
    present — it returns silently, leaving get_jwt_identity() returning None.
    Any other exception (malformed token, etc.) is also caught and discarded
    so the limiter never blocks a legitimate request due to auth errors.
    """
    try:
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
        from flask_jwt_extended.exceptions import JWTExtendedException
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            return f'user:{user_id}'
    except JWTExtendedException as e:
        logger.debug(f"Rate limit JWT extraction failed, falling back to IP: {type(e).__name__}")
    return get_remote_address()


limiter = Limiter(key_func=_rate_limit_key)


def init_limiter(app):
    """
    Bind the shared limiter to the Flask application.

    Call once from create_app() after app.config is populated.
    Storage URI is derived from REDIS_URL when RATELIMIT_STORAGE_URI is not
    explicitly set — Flask-Limiter uses RATELIMIT_STORAGE_URI if present,
    otherwise the default in-memory backend (fine for a single process).
    """
    # Forward Redis URL as Limiter storage when not explicitly overridden
    if not app.config.get('RATELIMIT_STORAGE_URI') and app.config.get('REDIS_URL'):
        app.config['RATELIMIT_STORAGE_URI'] = app.config['REDIS_URL']

    limiter.init_app(app)
