"""
Error Handler Middleware

All errors follow the standardized format defined in README.md:
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message",
        "details": [],
        "timestamp": "2026-03-03T10:30:00Z",
        "request_id": "req_abc123"
    }
}

Custom Error Classes (for service layer):
  - ServiceError: base exception with error_code, message, http_status
  - ValidationError: input validation failed (400)
  - PermissionError: authorization failed (403)
  - NotFoundError: resource not found (404)
  - ConflictError: resource conflict (409)
  - ExternalServiceError: third-party service failed (503)
"""
import logging
from datetime import datetime, timezone

from flask import g, jsonify, request

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for service-layer errors. Automatically converts to JSON response."""
    def __init__(self, code, message, http_status=500):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class ValidationError(ServiceError):
    def __init__(self, message):
        super().__init__('VALIDATION_ERROR', message, 400)


class PermissionError(ServiceError):
    def __init__(self, message):
        super().__init__('FORBIDDEN_PERMISSION_DENIED', message, 403)


class NotFoundError(ServiceError):
    def __init__(self, message):
        super().__init__('NOT_FOUND', message, 404)


class ConflictError(ServiceError):
    def __init__(self, message):
        super().__init__('CONFLICT', message, 409)


class ExternalServiceError(ServiceError):
    def __init__(self, service_name, cause=None):
        msg = f"{service_name} service temporarily unavailable. Please try again later."
        super().__init__('EXTERNAL_SERVICE_ERROR', msg, 503)
        self.cause = cause


def _error_response(code, message, http_status, details=None):
    # Prefer g.request_id (set by request_id middleware); fall back to header
    request_id = getattr(g, 'request_id', None) or request.headers.get('X-Request-ID', '')
    body = {
        'success': False,
        'error': {
            'code': code,
            'message': message,
            'details': details or [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': request_id,
        }
    }
    return jsonify(body), http_status


def register_error_handlers(app):
    @app.errorhandler(ServiceError)
    def handle_service_error(e):
        return _error_response(e.code, e.message, e.http_status)

    @app.errorhandler(400)
    def bad_request(e):
        return _error_response('VALIDATION_ERROR', str(e), 400)

    @app.errorhandler(401)
    def unauthorized(e):
        return _error_response('AUTH_UNAUTHORIZED', str(e), 401)

    @app.errorhandler(403)
    def forbidden(e):
        return _error_response('FORBIDDEN_PERMISSION_DENIED', str(e), 403)

    @app.errorhandler(404)
    def not_found(e):
        return _error_response('NOT_FOUND_ENDPOINT', str(e), 404)

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return _error_response('RATE_LIMIT_EXCEEDED', str(e), 429)

    # Database errors
    from sqlalchemy.exc import IntegrityError, OperationalError
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        logger.warning(f"Database integrity error: {e}")
        return _error_response('CONFLICT', 'Resource already exists or constraint violation.', 409)
    
    @app.errorhandler(OperationalError)
    def handle_operational_error(e):
        logger.error(f"Database operational error: {e}", exc_info=True)
        return _error_response('SERVICE_UNAVAILABLE', 'Database temporarily unavailable.', 503)
    
    # Redis errors
    from redis.exceptions import RedisError
    
    @app.errorhandler(RedisError)
    def handle_redis_error(e):
        logger.error(f"Redis error: {e}", exc_info=True)
        return _error_response('SERVICE_UNAVAILABLE', 'Cache service temporarily unavailable.', 503)

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return _error_response('SERVER_ERROR', 'An internal server error occurred.', 500)
