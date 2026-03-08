"""
Shared helpers for route blueprints.

Provides consistent response builders and input parsers used across
jobs, users, and notifications routes.
"""
from datetime import datetime, timezone

from flask import g, jsonify, request
from marshmallow import ValidationError

from app.utils.constants import ErrorCode


def _ok(data, status=200, meta=None):
    """Build a success JSON response. meta fields are spread into the top level."""
    body = {'success': True, 'data': data}
    if meta:
        body.update(meta)
    return jsonify(body), status


def _err(code, message, status, details=None):
    """Build an error JSON response, including the request ID from g."""
    return jsonify({
        'success': False,
        'error': {
            'code': code,
            'message': message,
            'details': details or [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': getattr(g, 'request_id', ''),
        },
    }), status


def _flatten(messages):
    """Flatten Marshmallow ValidationError.messages into a list of strings."""
    result = []
    for field, errors in messages.items():
        if isinstance(errors, list):
            for e in errors:
                result.append(f'{field}: {e}')
        else:
            result.append(f'{field}: {errors}')
    return result


def _load_json(schema):
    """Parse and validate the request JSON body. Returns (data, None) or (None, err_response)."""
    try:
        return schema.load(request.get_json(silent=True) or {}), None
    except ValidationError as e:
        return None, _err(ErrorCode.VALIDATION_ERROR, 'Invalid request data.', 400,
                          details=_flatten(e.messages))


def _load_args(schema):
    """Parse and validate query-string args. Returns (data, None) or (None, err_response)."""
    try:
        return schema.load(request.args.to_dict()), None
    except ValidationError as e:
        return None, _err(ErrorCode.VALIDATION_ERROR, 'Invalid query parameters.', 400,
                          details=_flatten(e.messages))
