"""
Unit / functional tests for app/middleware/request_id.py

Tests the before_request and after_request hooks registered by
register_request_id(app).  A minimal Flask app with a single test
route is used — no JWT, no DB needed.
"""
import uuid

import pytest
from flask import Flask, g, jsonify


# ---------------------------------------------------------------------------
# Fixture: minimal app with request ID middleware registered
# ---------------------------------------------------------------------------

@pytest.fixture
def app_with_request_id():
    """Minimal Flask app with the request ID middleware registered."""
    app = Flask(__name__)
    app.config['TESTING'] = True

    from app.middleware.request_id import register_request_id
    register_request_id(app)

    @app.route('/ping')
    def ping():
        return jsonify({'request_id': g.request_id})

    return app


@pytest.fixture
def client(app_with_request_id):
    return app_with_request_id.test_client()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRequestIdMiddleware:
    def test_response_always_has_request_id_header(self, client):
        resp = client.get('/ping')
        assert 'X-Request-ID' in resp.headers

    def test_client_header_is_preserved_in_response(self, client):
        resp = client.get('/ping', headers={'X-Request-ID': 'client-trace-123'})
        assert resp.headers['X-Request-ID'] == 'client-trace-123'

    def test_client_header_stored_in_g(self, client):
        resp = client.get('/ping', headers={'X-Request-ID': 'trace-abc'})
        assert resp.get_json()['request_id'] == 'trace-abc'

    def test_uuid_generated_when_header_absent(self, client):
        resp = client.get('/ping')
        req_id = resp.headers['X-Request-ID']
        assert req_id  # non-empty
        # Must be a valid UUID4
        parsed = uuid.UUID(req_id)
        assert parsed.version == 4

    def test_consecutive_requests_get_different_ids(self, client):
        id1 = client.get('/ping').headers['X-Request-ID']
        id2 = client.get('/ping').headers['X-Request-ID']
        assert id1 != id2

    def test_whitespace_only_header_treated_as_absent(self, client):
        resp = client.get('/ping', headers={'X-Request-ID': '   '})
        # Whitespace stripped → empty → new UUID generated
        req_id = resp.headers['X-Request-ID']
        uuid.UUID(req_id)  # valid UUID means it was re-generated

    def test_g_request_id_accessible_inside_handler(self, client):
        resp = client.get('/ping', headers={'X-Request-ID': 'handler-check'})
        assert resp.get_json()['request_id'] == 'handler-check'

    def test_404_response_still_has_request_id_header(self, client):
        resp = client.get('/nonexistent')
        assert 'X-Request-ID' in resp.headers
