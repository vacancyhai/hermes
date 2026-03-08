"""
Unit tests for app/tasks/reminder_tasks.py

No PostgreSQL needed — DB calls are mocked with unittest.mock.
"""
import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_job(**kwargs):
    job = MagicMock()
    job.id = kwargs.get('id', uuid.uuid4())
    job.job_title = kwargs.get('job_title', 'SSC CHSL')
    job.slug = kwargs.get('slug', 'ssc-chsl')
    job.organization = kwargs.get('organization', 'SSC')
    job.application_end = kwargs.get('application_end', date.today() + timedelta(days=7))
    return job


def _mock_application(job_id=None, user_id=None, status='applied'):
    app = MagicMock()
    app.job_id = job_id or uuid.uuid4()
    app.user_id = user_id or uuid.uuid4()
    app.status = status
    return app


def _mock_user(active=True, pref_reminders=True, user_id=None):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = 'applicant@example.com'
    user.full_name = 'Test Applicant'
    user.status = 'active' if active else 'suspended'
    profile = MagicMock()
    profile.notification_preferences = {'email_reminders': pref_reminders}
    user.profile = profile
    return user


# ---------------------------------------------------------------------------
# send_deadline_reminders
# ---------------------------------------------------------------------------

class TestSendDeadlineReminders:
    def test_sends_emails_for_jobs_closing_in_7_days(self):
        from app.tasks.reminder_tasks import send_deadline_reminders

        today = date.today()
        job = _mock_job(application_end=today + timedelta(days=7))
        application = _mock_application(job_id=job.id)
        user = _mock_user()

        with patch('app.extensions.db'), \
             patch('app.models.job.JobVacancy') as mock_job_model, \
             patch('app.models.job.UserJobApplication') as mock_app_model, \
             patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_deadline_reminder_email') as mock_email:

            mock_job_model.query.filter.return_value.all.return_value = [job]
            mock_app_model.query.filter.return_value.all.return_value = [application]
            mock_user_model.query.get.return_value = user

            result = send_deadline_reminders.run()

        assert mock_email.call_count >= 1
        assert result['emails_sent'] >= 1

    def test_skips_inactive_users(self):
        from app.tasks.reminder_tasks import send_deadline_reminders

        job = _mock_job()
        application = _mock_application(job_id=job.id)
        user = _mock_user(active=False)

        with patch('app.extensions.db'), \
             patch('app.models.job.JobVacancy') as mock_job_model, \
             patch('app.models.job.UserJobApplication') as mock_app_model, \
             patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_deadline_reminder_email') as mock_email:

            mock_job_model.query.filter.return_value.all.return_value = [job]
            mock_app_model.query.filter.return_value.all.return_value = [application]
            mock_user_model.query.get.return_value = user

            result = send_deadline_reminders.run()

        mock_email.assert_not_called()

    def test_skips_users_with_reminders_disabled(self):
        from app.tasks.reminder_tasks import send_deadline_reminders

        job = _mock_job()
        application = _mock_application(job_id=job.id)
        user = _mock_user(pref_reminders=False)

        with patch('app.extensions.db'), \
             patch('app.models.job.JobVacancy') as mock_job_model, \
             patch('app.models.job.UserJobApplication') as mock_app_model, \
             patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_deadline_reminder_email') as mock_email:

            mock_job_model.query.filter.return_value.all.return_value = [job]
            mock_app_model.query.filter.return_value.all.return_value = [application]
            mock_user_model.query.get.return_value = user

            result = send_deadline_reminders.run()

        mock_email.assert_not_called()
        assert result['emails_sent'] == 0

    def test_skips_users_with_no_profile(self):
        from app.tasks.reminder_tasks import send_deadline_reminders

        job = _mock_job()
        application = _mock_application(job_id=job.id)
        user = _mock_user()
        user.profile = None   # no profile → no preferences → should still send

        with patch('app.extensions.db'), \
             patch('app.models.job.JobVacancy') as mock_job_model, \
             patch('app.models.job.UserJobApplication') as mock_app_model, \
             patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_deadline_reminder_email') as mock_email:

            mock_job_model.query.filter.return_value.all.return_value = [job]
            mock_app_model.query.filter.return_value.all.return_value = [application]
            mock_user_model.query.get.return_value = user

            send_deadline_reminders.run()

        # No profile means no pref to disable — email should be sent
        assert mock_email.call_count >= 1

    def test_no_jobs_returns_zero_emails(self):
        from app.tasks.reminder_tasks import send_deadline_reminders

        with patch('app.extensions.db'), \
             patch('app.models.job.JobVacancy') as mock_job_model, \
             patch('app.services.email_service.send_deadline_reminder_email') as mock_email:

            mock_job_model.query.filter.return_value.all.return_value = []

            result = send_deadline_reminders.run()

        mock_email.assert_not_called()
        assert result['emails_sent'] == 0

    def test_email_error_does_not_abort_remaining_users(self):
        from app.tasks.reminder_tasks import send_deadline_reminders

        job = _mock_job()
        uid1, uid2 = uuid.uuid4(), uuid.uuid4()
        app1 = _mock_application(job_id=job.id, user_id=uid1)
        app2 = _mock_application(job_id=job.id, user_id=uid2)
        user1 = _mock_user()
        user2 = _mock_user()

        send_call = {'n': 0}

        def _send_side_effect(**kwargs):
            send_call['n'] += 1
            if send_call['n'] == 1:
                raise ConnectionError('SMTP down')

        # Return [job] only for the 7-day threshold; return [] for the others
        job_query = MagicMock()
        job_query.all.side_effect = [[job], [], []]

        with patch('app.extensions.db'), \
             patch('app.models.job.JobVacancy') as mock_job_model, \
             patch('app.models.job.UserJobApplication') as mock_app_model, \
             patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_deadline_reminder_email',
                   side_effect=_send_side_effect) as mock_email:

            mock_job_model.query.filter.return_value = job_query
            mock_app_model.query.filter.return_value.all.return_value = [app1, app2]
            mock_user_model.query.get.side_effect = [user1, user2]

            result = send_deadline_reminders.run()

        # First failed, second succeeded
        assert result['emails_sent'] == 1
        assert mock_email.call_count == 2

    def test_processes_all_three_reminder_thresholds(self):
        from app.tasks.reminder_tasks import send_deadline_reminders

        with patch('app.extensions.db'), \
             patch('app.models.job.JobVacancy') as mock_job_model, \
             patch('app.services.email_service.send_deadline_reminder_email'):

            mock_job_model.query.filter.return_value.all.return_value = []

            result = send_deadline_reminders.run()

        assert result['thresholds_processed'] == 3

    def test_email_sent_with_correct_days_left(self):
        from app.tasks.reminder_tasks import send_deadline_reminders

        today = date.today()
        job = _mock_job(application_end=today + timedelta(days=3))
        application = _mock_application(job_id=job.id)
        user = _mock_user()

        # Return job only for the 3-day threshold (second iteration); [] for 7 and 1
        job_query = MagicMock()
        job_query.all.side_effect = [[], [job], []]

        with patch('app.extensions.db'), \
             patch('app.models.job.JobVacancy') as mock_job_model, \
             patch('app.models.job.UserJobApplication') as mock_app_model, \
             patch('app.models.user.User') as mock_user_model, \
             patch('app.services.email_service.send_deadline_reminder_email') as mock_email:

            mock_job_model.query.filter.return_value = job_query
            mock_app_model.query.filter.return_value.all.return_value = [application]
            mock_user_model.query.get.return_value = user

            send_deadline_reminders.run()

        assert mock_email.call_count == 1
        call_kwargs = mock_email.call_args.kwargs
        assert call_kwargs['days_left'] == 3
