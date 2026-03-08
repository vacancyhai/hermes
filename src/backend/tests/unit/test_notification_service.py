"""
Unit tests for app/services/notification_service.py

DB calls are mocked via unittest.mock — no PostgreSQL needed.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_notif(**kwargs):
    n = MagicMock()
    n.id = kwargs.get('id', uuid.uuid4())
    n.user_id = kwargs.get('user_id', uuid.uuid4())
    n.type = kwargs.get('type', 'job_alert')
    n.title = kwargs.get('title', 'New Job')
    n.message = kwargs.get('message', 'A new job is available.')
    n.action_url = kwargs.get('action_url', None)
    n.entity_type = kwargs.get('entity_type', 'job')
    n.entity_id = kwargs.get('entity_id', None)
    n.is_read = kwargs.get('is_read', False)
    n.priority = kwargs.get('priority', 'medium')
    n.created_at = kwargs.get('created_at', datetime(2026, 3, 8, tzinfo=timezone.utc))
    n.read_at = kwargs.get('read_at', None)
    return n


# ---------------------------------------------------------------------------
# create_notification
# ---------------------------------------------------------------------------

class TestCreateNotification:
    def test_inserts_and_commits(self):
        from app.services import notification_service

        with patch('app.services.notification_service.db') as mock_db, \
             patch('app.services.notification_service.Notification') as mock_cls:
            mock_notif = _mock_notif()
            mock_cls.return_value = mock_notif

            result = notification_service.create_notification(
                user_id=str(uuid.uuid4()),
                notification_type='job_alert',
                title='New SSC Job',
                message='SSC CGL is open.',
            )

        mock_db.session.add.assert_called_once_with(mock_notif)
        mock_db.session.commit.assert_called_once()
        assert result is mock_notif

    def test_passes_optional_fields(self):
        from app.services import notification_service

        uid = str(uuid.uuid4())
        eid = str(uuid.uuid4())

        with patch('app.services.notification_service.db'), \
             patch('app.services.notification_service.Notification') as mock_cls:
            mock_cls.return_value = _mock_notif()
            notification_service.create_notification(
                user_id=uid,
                notification_type='deadline_reminder',
                title='Deadline soon',
                message='Apply by tomorrow.',
                entity_type='job',
                entity_id=eid,
                action_url='/jobs/slug',
                priority='high',
            )

        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs['entity_type'] == 'job'
        assert call_kwargs['action_url'] == '/jobs/slug'
        assert call_kwargs['priority'] == 'high'


# ---------------------------------------------------------------------------
# mark_read
# ---------------------------------------------------------------------------

class TestMarkRead:
    def test_marks_unread_notification_as_read(self):
        from app.services import notification_service

        notif = _mock_notif(is_read=False)

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch('app.services.notification_service.db') as mock_db:
            mock_cls.query.filter_by.return_value.first.return_value = notif

            result = notification_service.mark_read(str(notif.id), str(notif.user_id))

        assert notif.is_read is True
        assert notif.read_at is not None
        mock_db.session.commit.assert_called_once()
        assert result is notif

    def test_does_not_double_commit_already_read(self):
        from app.services import notification_service

        notif = _mock_notif(is_read=True)

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch('app.services.notification_service.db') as mock_db:
            mock_cls.query.filter_by.return_value.first.return_value = notif

            notification_service.mark_read(str(notif.id), str(notif.user_id))

        mock_db.session.commit.assert_not_called()

    def test_raises_if_not_found(self):
        from app.services import notification_service

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch('app.services.notification_service.db'):
            mock_cls.query.filter_by.return_value.first.return_value = None

            with pytest.raises(ValueError):
                notification_service.mark_read(str(uuid.uuid4()), str(uuid.uuid4()))

    def test_raises_if_belongs_to_different_user(self):
        from app.services import notification_service

        # filter_by(id=..., user_id=...) will return None when user_id doesn't match
        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch('app.services.notification_service.db'):
            mock_cls.query.filter_by.return_value.first.return_value = None

            with pytest.raises(ValueError):
                notification_service.mark_read(str(uuid.uuid4()), str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# mark_all_read
# ---------------------------------------------------------------------------

class TestMarkAllRead:
    def test_bulk_updates_and_commits(self):
        from app.services import notification_service

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch('app.services.notification_service.db') as mock_db:
            mock_cls.query.filter_by.return_value.update.return_value = 5

            count = notification_service.mark_all_read(str(uuid.uuid4()))

        assert count == 5
        mock_db.session.commit.assert_called_once()

    def test_returns_zero_when_nothing_to_read(self):
        from app.services import notification_service

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch('app.services.notification_service.db'):
            mock_cls.query.filter_by.return_value.update.return_value = 0

            count = notification_service.mark_all_read(str(uuid.uuid4()))

        assert count == 0

    def test_update_sets_correct_fields(self):
        from app.services import notification_service

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch('app.services.notification_service.db'):
            mock_update = mock_cls.query.filter_by.return_value.update
            mock_update.return_value = 3

            notification_service.mark_all_read(str(uuid.uuid4()))

        update_payload = mock_update.call_args[0][0]
        assert update_payload['is_read'] is True
        assert 'read_at' in update_payload


# ---------------------------------------------------------------------------
# delete_notification
# ---------------------------------------------------------------------------

class TestDeleteNotification:
    def test_deletes_and_commits(self):
        from app.services import notification_service

        notif = _mock_notif()

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch('app.services.notification_service.db') as mock_db:
            mock_cls.query.filter_by.return_value.first.return_value = notif

            notification_service.delete_notification(str(notif.id), str(notif.user_id))

        mock_db.session.delete.assert_called_once_with(notif)
        mock_db.session.commit.assert_called_once()

    def test_raises_if_not_found(self):
        from app.services import notification_service

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch('app.services.notification_service.db'):
            mock_cls.query.filter_by.return_value.first.return_value = None

            with pytest.raises(ValueError):
                notification_service.delete_notification(str(uuid.uuid4()), str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# get_notifications
# ---------------------------------------------------------------------------

class TestGetNotifications:
    def test_calls_paginate_with_correct_args(self):
        from app.services import notification_service

        uid = str(uuid.uuid4())

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch.object(notification_service, 'paginate') as mock_paginate:
            mock_query = MagicMock()
            mock_cls.query.filter_by.return_value.order_by.return_value = mock_query
            mock_paginate.return_value = {'items': [], 'total': 0, 'page': 2, 'per_page': 10, 'pages': 0}

            result = notification_service.get_notifications(uid, page=2, per_page=10)

        mock_paginate.assert_called_once_with(mock_query, page=2, per_page=10)
        assert result['page'] == 2

    def test_filters_by_user_id(self):
        from app.services import notification_service

        uid = str(uuid.uuid4())

        with patch('app.services.notification_service.Notification') as mock_cls, \
             patch.object(notification_service, 'paginate') as mock_paginate:
            mock_cls.query.filter_by.return_value.order_by.return_value = MagicMock()
            mock_paginate.return_value = {'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0}

            notification_service.get_notifications(uid)

        mock_cls.query.filter_by.assert_called_once_with(user_id=uid)


# ---------------------------------------------------------------------------
# get_unread_count
# ---------------------------------------------------------------------------

class TestGetUnreadCount:
    def test_returns_count(self):
        from app.services import notification_service

        uid = str(uuid.uuid4())

        with patch('app.services.notification_service.Notification') as mock_cls:
            mock_cls.query.filter_by.return_value.count.return_value = 7

            count = notification_service.get_unread_count(uid)

        assert count == 7
        mock_cls.query.filter_by.assert_called_once_with(user_id=uid, is_read=False)

    def test_returns_zero_when_all_read(self):
        from app.services import notification_service

        with patch('app.services.notification_service.Notification') as mock_cls:
            mock_cls.query.filter_by.return_value.count.return_value = 0

            count = notification_service.get_unread_count(str(uuid.uuid4()))

        assert count == 0


# ---------------------------------------------------------------------------
# match_job_to_users
# ---------------------------------------------------------------------------

class TestMatchJobToUsers:
    def _mock_user(self, uid, status='active'):
        u = MagicMock()
        u.id = uid
        u.email = f'{uid}@example.com'
        u.full_name = f'User {uid}'
        u.status = status
        return u

    def _mock_profile(self, qual='graduation', category='general', prefs=None):
        p = MagicMock()
        p.highest_qualification = qual
        p.category = category
        p.notification_preferences = prefs or {}
        return p

    def test_returns_eligible_users(self):
        from app.services import notification_service

        uid = uuid.uuid4()
        job = MagicMock()
        job.qualification_level = 'graduation'
        job.eligibility = {}
        job.job_type = 'central'

        with patch('app.services.notification_service.db') as mock_db:
            user = self._mock_user(uid)
            profile = self._mock_profile(qual='graduation')
            mock_db.session.query.return_value.join.return_value.filter.return_value.all.return_value = [
                (user, profile)
            ]

            result = notification_service.match_job_to_users(job)

        assert len(result) == 1
        assert result[0]['user_id'] == str(uid)

    def test_excludes_user_below_qualification(self):
        from app.services import notification_service

        uid = uuid.uuid4()
        job = MagicMock()
        job.qualification_level = 'post_graduation'
        job.eligibility = {}
        job.job_type = 'central'

        with patch('app.services.notification_service.db') as mock_db:
            user = self._mock_user(uid)
            profile = self._mock_profile(qual='12th')
            mock_db.session.query.return_value.join.return_value.filter.return_value.all.return_value = [
                (user, profile)
            ]

            result = notification_service.match_job_to_users(job)

        assert result == []

    def test_excludes_user_with_disabled_job_type(self):
        from app.services import notification_service

        uid = uuid.uuid4()
        job = MagicMock()
        job.qualification_level = None
        job.eligibility = {}
        job.job_type = 'state'

        with patch('app.services.notification_service.db') as mock_db:
            user = self._mock_user(uid)
            profile = self._mock_profile(prefs={'disabled_job_types': ['state']})
            mock_db.session.query.return_value.join.return_value.filter.return_value.all.return_value = [
                (user, profile)
            ]

            result = notification_service.match_job_to_users(job)

        assert result == []

    def test_excludes_user_not_in_category_vacancies(self):
        from app.services import notification_service

        uid = uuid.uuid4()
        job = MagicMock()
        job.qualification_level = None
        job.eligibility = {'category_vacancies': {'obc': 50, 'sc': 20}}
        job.job_type = 'central'

        with patch('app.services.notification_service.db') as mock_db:
            user = self._mock_user(uid)
            profile = self._mock_profile(category='general')
            mock_db.session.query.return_value.join.return_value.filter.return_value.all.return_value = [
                (user, profile)
            ]

            result = notification_service.match_job_to_users(job)

        assert result == []

    def test_includes_user_in_category_vacancies(self):
        from app.services import notification_service

        uid = uuid.uuid4()
        job = MagicMock()
        job.qualification_level = None
        job.eligibility = {'category_vacancies': {'obc': 50, 'general': 100}}
        job.job_type = 'central'

        with patch('app.services.notification_service.db') as mock_db:
            user = self._mock_user(uid)
            profile = self._mock_profile(category='general')
            mock_db.session.query.return_value.join.return_value.filter.return_value.all.return_value = [
                (user, profile)
            ]

            result = notification_service.match_job_to_users(job)

        assert len(result) == 1
