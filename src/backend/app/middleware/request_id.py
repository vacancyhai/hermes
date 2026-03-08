"""
Request ID middleware.

Assigns a unique X-Request-ID to every request:
  - Uses the value from the incoming X-Request-ID header if the client
    provided one (supports end-to-end tracing from browser → Nginx → backend).
  - Generates a new UUID4 when the header is absent.

The ID is stored on flask.g so other middleware (error_handler) and logging
code can access it without re-reading the header.

The same ID is echoed back in the X-Request-ID response header so the client
can correlate requests and responses.

Usage:
    Call register_request_id(app) once from create_app().

Accessing the ID in a request handler or other middleware:
    from flask import g
    request_id = g.request_id
"""
import uuid

from flask import g, request


def register_request_id(app):
    """
    Register before_request / after_request hooks on *app*.

    Call once from create_app() — no return value.
    """
    @app.before_request
    def _assign_request_id():
        incoming = request.headers.get('X-Request-ID', '').strip()
        g.request_id = incoming if incoming else str(uuid.uuid4())

    @app.after_request
    def _echo_request_id(response):
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
        return response
