"""
Integration tests for app/routes/notifications.py

Service layer is fully mocked — no DB or Redis needed.
Uses the shared `client` / `app` fixtures from conftest (fakeredis + JWT).
The notifications blueprint is registered here because conftest only wires
auth + jobs + users by default.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.routes.notifications import bp as notifications_bp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def notif_client(app):
    """Test client with notifications blueprint added."""
    if 'notifications' not in app.blueprints:
        app.register_blueprint(notifications_bp)
    return app.test_client()


@pytest.fixture
def admin_header(access_token_for):
    return {'Authorization': f'Bearer {access_token_for(role="admin")}'}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_notif(**kwargs):
    n = MagicMock()
    n.id = kwargs.get('id', uuid.uuid4())
    n.user_id = kwargs.get('user_id', uuid.uuid4())
    n.type = kwargs.get('type', 'job_alert')
    n.title = kwargs.get('title', 'New Job')
    n.message = kwargs.get('message', 'A new vacancy is open.')
    n.action_url = kwargs.get('action_url', '/jobs/ssc-cgl')
    n.entity_type = kwargs.get('entity_type', 'job')
    n.entity_id = kwargs.get('entity_id', None)
    n.is_read = kwargs.get('is_read', False)
    n.priority = kwargs.get('priority', 'medium')
    n.created_at = kwargs.get('created_at', datetime(2026, 3, 8, tzinfo=timezone.utc))
    n.read_at = kwargs.get('read_at', None)
    return n


# ---------------------------------------------------------------------------
# GET /api/v1/notifications  — list
# ---------------------------------------------------------------------------

class TestListNotifications:
    def test_requires_auth(self, notif_client):
        resp = notif_client.get('/api/v1/notifications')
        assert resp.status_code == 401

    def test_returns_paginated_list(self, notif_client, auth_header):
        notifs = [_mock_notif() for _ in range(3)]
        paginated = {'items': notifs, 'total': 3, 'page': 1, 'per_page': 20, 'pages': 1}

        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.get_notifications.return_value = paginated
            resp = notif_client.get('/api/v1/notifications', headers=auth_header)

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert len(data['data']) == 3
        assert data['meta']['total'] == 3

    def test_respects_page_and_per_page_params(self, notif_client, auth_header):
        paginated = {'items': [], 'total': 0, 'page': 2, 'per_page': 5, 'pages': 0}

        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.get_notifications.return_value = paginated
            resp = notif_client.get(
                '/api/v1/notifications?page=2&per_page=5',
                headers=auth_header,
            )

        assert resp.status_code == 200
        mock_svc.get_notifications.assert_called_once_with(
            'test-user-id', page=2, per_page=5
        )

    def test_caps_per_page_at_100(self, notif_client, auth_header):
        paginated = {'items': [], 'total': 0, 'page': 1, 'per_page': 100, 'pages': 0}

        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.get_notifications.return_value = paginated
            notif_client.get(
                '/api/v1/notifications?per_page=500',
                headers=auth_header,
            )

        _call_kwargs = mock_svc.get_notifications.call_args
        assert _call_kwargs[1]['per_page'] == 100


# ---------------------------------------------------------------------------
# GET /api/v1/notifications/count  — unread count
# ---------------------------------------------------------------------------

class TestUnreadCount:
    def test_requires_auth(self, notif_client):
        resp = notif_client.get('/api/v1/notifications/count')
        assert resp.status_code == 401

    def test_returns_count(self, notif_client, auth_header):
        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.get_unread_count.return_value = 4
            resp = notif_client.get('/api/v1/notifications/count', headers=auth_header)

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['unread_count'] == 4

    def test_returns_zero_when_all_read(self, notif_client, auth_header):
        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.get_unread_count.return_value = 0
            resp = notif_client.get('/api/v1/notifications/count', headers=auth_header)

        assert resp.status_code == 200
        assert resp.get_json()['data']['unread_count'] == 0


# ---------------------------------------------------------------------------
# PUT /api/v1/notifications/<id>/read  — mark single read
# ---------------------------------------------------------------------------

class TestMarkRead:
    def test_requires_auth(self, notif_client):
        resp = notif_client.put(f'/api/v1/notifications/{uuid.uuid4()}/read')
        assert resp.status_code == 401

    def test_marks_notification_read(self, notif_client, auth_header):
        notif = _mock_notif(is_read=True)
        notif_id = str(uuid.uuid4())

        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.mark_read.return_value = notif
            resp = notif_client.put(
                f'/api/v1/notifications/{notif_id}/read',
                headers=auth_header,
            )

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['is_read'] is True
        mock_svc.mark_read.assert_called_once_with(notif_id, 'test-user-id')

    def test_returns_404_when_not_found(self, notif_client, auth_header):
        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.mark_read.side_effect = ValueError('NOT_FOUND')
            resp = notif_client.put(
                f'/api/v1/notifications/{uuid.uuid4()}/read',
                headers=auth_header,
            )

        assert resp.status_code == 404

    def test_cannot_read_other_users_notification(self, notif_client, auth_header):
        """Service raises ValueError when user_id doesn't match; route returns 404."""
        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.mark_read.side_effect = ValueError('NOT_FOUND')
            resp = notif_client.put(
                f'/api/v1/notifications/{uuid.uuid4()}/read',
                headers=auth_header,
            )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/v1/notifications/read-all  — mark all read
# ---------------------------------------------------------------------------

class TestMarkAllRead:
    def test_requires_auth(self, notif_client):
        resp = notif_client.put('/api/v1/notifications/read-all')
        assert resp.status_code == 401

    def test_marks_all_read_and_returns_count(self, notif_client, auth_header):
        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.mark_all_read.return_value = 8
            resp = notif_client.put('/api/v1/notifications/read-all', headers=auth_header)

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['updated'] == 8
        mock_svc.mark_all_read.assert_called_once_with('test-user-id')

    def test_returns_zero_when_nothing_to_mark(self, notif_client, auth_header):
        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.mark_all_read.return_value = 0
            resp = notif_client.put('/api/v1/notifications/read-all', headers=auth_header)

        assert resp.status_code == 200
        assert resp.get_json()['data']['updated'] == 0


# ---------------------------------------------------------------------------
# DELETE /api/v1/notifications/<id>  — delete
# ---------------------------------------------------------------------------

class TestDeleteNotification:
    def test_requires_auth(self, notif_client):
        resp = notif_client.delete(f'/api/v1/notifications/{uuid.uuid4()}')
        assert resp.status_code == 401

    def test_deletes_notification(self, notif_client, auth_header):
        notif_id = str(uuid.uuid4())

        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.delete_notification.return_value = None
            resp = notif_client.delete(
                f'/api/v1/notifications/{notif_id}',
                headers=auth_header,
            )

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'deleted' in data['data']['message'].lower()
        mock_svc.delete_notification.assert_called_once_with(notif_id, 'test-user-id')

    def test_returns_404_when_not_found(self, notif_client, auth_header):
        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.delete_notification.side_effect = ValueError('NOT_FOUND')
            resp = notif_client.delete(
                f'/api/v1/notifications/{uuid.uuid4()}',
                headers=auth_header,
            )

        assert resp.status_code == 404

    def test_cannot_delete_other_users_notification(self, notif_client, auth_header):
        """Service raises ValueError when user_id doesn't match; route returns 404."""
        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.delete_notification.side_effect = ValueError('NOT_FOUND')
            resp = notif_client.delete(
                f'/api/v1/notifications/{uuid.uuid4()}',
                headers=auth_header,
            )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------

class TestResponseShape:
    def test_list_response_has_meta(self, notif_client, auth_header):
        paginated = {'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0}

        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.get_notifications.return_value = paginated
            resp = notif_client.get('/api/v1/notifications', headers=auth_header)

        body = resp.get_json()
        for key in ('total', 'page', 'per_page', 'pages'):
            assert key in body['meta'], f'Missing meta key: {key!r}'

    def test_notification_fields_in_response(self, notif_client, auth_header):
        eid = uuid.uuid4()
        notif = _mock_notif(entity_id=eid, is_read=False)
        paginated = {'items': [notif], 'total': 1, 'page': 1, 'per_page': 20, 'pages': 1}

        with patch('app.routes.notifications.notification_service') as mock_svc:
            mock_svc.get_notifications.return_value = paginated
            resp = notif_client.get('/api/v1/notifications', headers=auth_header)

        item = resp.get_json()['data'][0]
        for field in ('id', 'type', 'title', 'message', 'is_read', 'priority', 'created_at'):
            assert field in item, f'Missing field {field!r} in notification item'
