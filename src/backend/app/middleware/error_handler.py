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
"""
from flask import jsonify, request
from datetime import datetime, timezone


def _error_response(code, message, http_status, details=None):
    request_id = request.headers.get('X-Request-ID', '')
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

    @app.errorhandler(500)
    def internal_error(e):
        return _error_response('SERVER_ERROR', 'An internal server error occurred.', 500)
