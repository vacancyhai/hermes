"""
Unit tests for app/tasks/notification_tasks.py

Celery infrastructure is bypassed — tasks are called as plain functions.
All DB + service + email calls are mocked.
"""
import uuid
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_job(**kwargs):
    job = MagicMock()
    job.id = kwargs.get('id', uuid.uuid4())
    job.job_title = kwargs.get('job_title', 'SSC CGL 2024')
    job.slug = kwargs.get('slug', 'ssc-cgl-2024')
    job.organization = kwargs.get('organization', 'SSC')
    job.application_end = kwargs.get('application_end', None)
    job.is_urgent = kwargs.get('is_urgent', False)
    return job


def _mock_user_info(**kwargs):
    return {
        'user_id': str(kwargs.get('user_id', uuid.uuid4())),
        'email': kwargs.get('email', 'user@example.com'),
        'full_name': kwargs.get('full_name', 'Test User'),
    }


# ---------------------------------------------------------------------------
# send_new_job_notifications
# ---------------------------------------------------------------------------

# Mock self for bind=True tasks (first arg is the Celery task instance)
_MOCK_SELF = MagicMock()


class TestSendNewJobNotifications:
    def test_returns_zeros_when_job_not_found(self):
        from app.tasks.notification_tasks import send_new_job_notifications

        job_id = str(uuid.uuid4())
        with patch('app.models.job.JobVacancy') as mock_model:
            mock_model.query.get.return_value = None

            result = send_new_job_notifications.run(job_id)

        assert result == {'matched': 0, 'created': 0, 'emails_queued': 0}

    def test_creates_notifications_for_all_matched_users(self):
        from app.tasks.notification_tasks import send_new_job_notifications

        job = _mock_job()
        job.application_end = '2026-04-30'
        users = [_mock_user_info(), _mock_user_info()]

        with patch('app.models.job.JobVacancy') as mock_model, \
             patch('app.services.notification_service.match_job_to_users', return_value=users), \
             patch('app.services.notification_service.create_notification') as mock_create, \
             patch('app.tasks.notification_tasks.deliver_notification_email') as mock_email:

            mock_model.query.get.return_value = job
            mock_create.return_value = MagicMock()
            mock_email.delay = MagicMock()

            result = send_new_job_notifications.run(str(job.id))

        assert result['matched'] == 2
        assert result['created'] == 2
        assert result['emails_queued'] == 2
        assert mock_create.call_count == 2
        assert mock_email.delay.call_count == 2

    def test_notification_title_includes_job_title(self):
        from app.tasks.notification_tasks import send_new_job_notifications

        job = _mock_job(job_title='UPSC Prelims')
        job.application_end = '2026-05-01'
        users = [_mock_user_info()]

        with patch('app.models.job.JobVacancy') as mock_model, \
             patch('app.services.notification_service.match_job_to_users', return_value=users), \
             patch('app.services.notification_service.create_notification') as mock_create, \
             patch('app.tasks.notification_tasks.deliver_notification_email') as mock_email:

            mock_model.query.get.return_value = job
            mock_create.return_value = MagicMock()
            mock_email.delay = MagicMock()

            send_new_job_notifications.run(str(job.id))

        kwargs = mock_create.call_args.kwargs
        assert 'UPSC Prelims' in kwargs['title']

    def test_email_queued_with_correct_fields(self):
        from app.tasks.notification_tasks import send_new_job_notifications

        job = _mock_job(organization='UPSC', job_title='Civil Services')
        job.application_end = '2026-06-15'
        job.slug = 'civil-services'
        user = _mock_user_info(email='civil@example.com', full_name='Arjun Sharma')
        users = [user]

        with patch('app.models.job.JobVacancy') as mock_model, \
             patch('app.services.notification_service.match_job_to_users', return_value=users), \
             patch('app.services.notification_service.create_notification') as mock_create, \
             patch('app.tasks.notification_tasks.deliver_notification_email') as mock_email:

            mock_model.query.get.return_value = job
            mock_create.return_value = MagicMock()
            mock_email.delay = MagicMock()

            send_new_job_notifications.run(str(job.id))

        mock_email.delay.assert_called_once_with(
            to_email='civil@example.com',
            full_name='Arjun Sharma',
            job_title='Civil Services',
            organization='UPSC',
            application_end=str(job.application_end),
            job_url='/jobs/civil-services',
        )

    def test_partial_failure_does_not_abort_batch(self):
        """One user's notification failing should not prevent the rest."""
        from app.tasks.notification_tasks import send_new_job_notifications

        job = _mock_job()
        job.application_end = None
        users = [_mock_user_info(), _mock_user_info(), _mock_user_info()]

        call_count = {'n': 0}

        def _create_side_effect(**kwargs):
            call_count['n'] += 1
            if call_count['n'] == 2:
                raise RuntimeError('DB error')
            return MagicMock()

        with patch('app.models.job.JobVacancy') as mock_model, \
             patch('app.services.notification_service.match_job_to_users', return_value=users), \
             patch('app.services.notification_service.create_notification', side_effect=_create_side_effect), \
             patch('app.tasks.notification_tasks.deliver_notification_email') as mock_email:

            mock_model.query.get.return_value = job
            mock_email.delay = MagicMock()

            result = send_new_job_notifications.run(str(job.id))

        # 2 succeeded, 1 failed
        assert result['matched'] == 3
        assert result['created'] == 2
        assert result['emails_queued'] == 2

    def test_no_matched_users_returns_empty(self):
        from app.tasks.notification_tasks import send_new_job_notifications

        job = _mock_job()
        job.application_end = '2026-03-31'

        with patch('app.models.job.JobVacancy') as mock_model, \
             patch('app.services.notification_service.match_job_to_users', return_value=[]), \
             patch('app.services.notification_service.create_notification') as mock_create, \
             patch('app.tasks.notification_tasks.deliver_notification_email') as mock_email:

            mock_model.query.get.return_value = job
            mock_email.delay = MagicMock()

            result = send_new_job_notifications.run(str(job.id))

        assert result == {'matched': 0, 'created': 0, 'emails_queued': 0}
        mock_create.assert_not_called()
        mock_email.delay.assert_not_called()

    def test_urgent_job_sets_high_priority(self):
        from app.tasks.notification_tasks import send_new_job_notifications

        job = _mock_job(is_urgent=True)
        job.application_end = '2026-04-01'
        users = [_mock_user_info()]

        with patch('app.models.job.JobVacancy') as mock_model, \
             patch('app.services.notification_service.match_job_to_users', return_value=users), \
             patch('app.services.notification_service.create_notification') as mock_create, \
             patch('app.tasks.notification_tasks.deliver_notification_email') as mock_email:

            mock_model.query.get.return_value = job
            mock_create.return_value = MagicMock()
            mock_email.delay = MagicMock()

            send_new_job_notifications.run(str(job.id))

        kwargs = mock_create.call_args.kwargs
        assert kwargs['priority'] == 'high'

    def test_non_urgent_job_sets_medium_priority(self):
        from app.tasks.notification_tasks import send_new_job_notifications

        job = _mock_job(is_urgent=False)
        job.application_end = '2026-04-01'
        users = [_mock_user_info()]

        with patch('app.models.job.JobVacancy') as mock_model, \
             patch('app.services.notification_service.match_job_to_users', return_value=users), \
             patch('app.services.notification_service.create_notification') as mock_create, \
             patch('app.tasks.notification_tasks.deliver_notification_email') as mock_email:

            mock_model.query.get.return_value = job
            mock_create.return_value = MagicMock()
            mock_email.delay = MagicMock()

            send_new_job_notifications.run(str(job.id))

        kwargs = mock_create.call_args.kwargs
        assert kwargs['priority'] == 'medium'


# ---------------------------------------------------------------------------
# deliver_notification_email
# ---------------------------------------------------------------------------

class TestDeliverNotificationEmail:
    def test_calls_email_service(self):
        from app.tasks.notification_tasks import deliver_notification_email

        with patch('app.services.email_service.send_job_notification_email') as mock_send:
            deliver_notification_email.run(
                to_email='user@example.com',
                full_name='Priya Singh',
                job_title='Bank PO',
                organization='SBI',
                application_end='2026-05-30',
                job_url='/jobs/sbi-bank-po',
            )

        mock_send.assert_called_once_with(
            to_email='user@example.com',
            full_name='Priya Singh',
            job_title='Bank PO',
            organization='SBI',
            application_end='2026-05-30',
            job_url='/jobs/sbi-bank-po',
        )

    def test_retries_on_smtp_failure(self):
        from app.tasks.notification_tasks import deliver_notification_email

        # Celery re-raises the original exc passed to self.retry(exc=exc)
        with patch('app.services.email_service.send_job_notification_email',
                   side_effect=ConnectionError('SMTP down')), \
             pytest.raises(ConnectionError):
            deliver_notification_email.run(
                to_email='user@example.com',
                full_name='Test',
                job_title='Job',
                organization='Org',
                application_end='2026-05-01',
                job_url='/jobs/test',
            )


# ---------------------------------------------------------------------------
# send_verification_email_task
# ---------------------------------------------------------------------------

class TestSendVerificationEmailTask:
    def test_sends_verification_email(self):
        from app.tasks.notification_tasks import send_verification_email_task

        mock_user = MagicMock()
        mock_user.email = 'new@example.com'
        mock_user.full_name = 'New User'

        with patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_verification_email') as mock_send:
            mock_user_model.query.get.return_value = mock_user
            send_verification_email_task.run('user-123', 'abc-token')

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        assert call_kwargs[0][0] == 'new@example.com'
        assert call_kwargs[0][1] == 'New User'
        assert 'abc-token' in call_kwargs[0][2]

    def test_returns_early_when_user_not_found(self):
        from app.tasks.notification_tasks import send_verification_email_task

        with patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_verification_email') as mock_send:
            mock_user_model.query.get.return_value = None
            send_verification_email_task.run('missing-id', 'token')

        mock_send.assert_not_called()

    def test_verify_url_contains_frontend_url(self):
        from app.tasks.notification_tasks import send_verification_email_task

        mock_user = MagicMock()
        mock_user.email = 'u@example.com'
        mock_user.full_name = 'User'

        with patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_verification_email') as mock_send, \
             patch.dict('os.environ', {'FRONTEND_URL': 'https://hermes.example.com'}):
            mock_user_model.query.get.return_value = mock_user
            send_verification_email_task.run('uid', 'tok123')

        verify_url = mock_send.call_args[0][2]
        assert verify_url.startswith('https://hermes.example.com')
        assert 'tok123' in verify_url

    def test_retries_on_smtp_failure(self):
        from app.tasks.notification_tasks import send_verification_email_task

        mock_user = MagicMock()
        mock_user.email = 'u@example.com'
        mock_user.full_name = 'User'

        with patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_verification_email',
                   side_effect=ConnectionError('SMTP fail')), \
             pytest.raises(ConnectionError):
            mock_user_model.query.get.return_value = mock_user
            send_verification_email_task.run('uid', 'tok')


# ---------------------------------------------------------------------------
# send_password_reset_email_task
# ---------------------------------------------------------------------------

class TestSendPasswordResetEmailTask:
    def test_sends_reset_email(self):
        from app.tasks.notification_tasks import send_password_reset_email_task

        mock_user = MagicMock()
        mock_user.email = 'reset@example.com'
        mock_user.full_name = 'Reset User'

        with patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_password_reset_email') as mock_send:
            mock_user_model.query.get.return_value = mock_user
            send_password_reset_email_task.run('user-456', 'reset-token')

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert call_args[0] == 'reset@example.com'
        assert call_args[1] == 'Reset User'
        assert 'reset-token' in call_args[2]

    def test_returns_early_when_user_not_found(self):
        from app.tasks.notification_tasks import send_password_reset_email_task

        with patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_password_reset_email') as mock_send:
            mock_user_model.query.get.return_value = None
            send_password_reset_email_task.run('missing', 'tok')

        mock_send.assert_not_called()

    def test_reset_url_contains_token(self):
        from app.tasks.notification_tasks import send_password_reset_email_task

        mock_user = MagicMock()
        mock_user.email = 'u@example.com'
        mock_user.full_name = 'User'

        with patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_password_reset_email') as mock_send, \
             patch.dict('os.environ', {'FRONTEND_URL': 'https://hermes.example.com'}):
            mock_user_model.query.get.return_value = mock_user
            send_password_reset_email_task.run('uid', 'reset-xyz')

        reset_url = mock_send.call_args[0][2]
        assert 'reset-xyz' in reset_url
        assert 'https://hermes.example.com' in reset_url

    def test_retries_on_smtp_failure(self):
        from app.tasks.notification_tasks import send_password_reset_email_task

        mock_user = MagicMock()
        mock_user.email = 'u@example.com'
        mock_user.full_name = 'User'

        with patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_password_reset_email',
                   side_effect=ConnectionError('SMTP fail')), \
             pytest.raises(ConnectionError):
            mock_user_model.query.get.return_value = mock_user
            send_password_reset_email_task.run('uid', 'tok')
