"""
Unit tests for app/tasks/cleanup_tasks.py

Tasks covered:
    purge_expired_notifications
    purge_expired_admin_logs
    purge_soft_deleted_jobs
    close_expired_job_listings
"""
from datetime import datetime, date, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.tasks.cleanup_tasks import (
    purge_expired_notifications,
    purge_expired_admin_logs,
    purge_soft_deleted_jobs,
    close_expired_job_listings,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db_mock(deleted=0, updated=0):
    """Return a mock db with query().filter().delete/update() wired."""
    mock_db = MagicMock()
    mock_db.session.query.return_value.filter.return_value.delete.return_value = deleted
    mock_db.session.query.return_value.filter.return_value.update.return_value = updated
    return mock_db


# ---------------------------------------------------------------------------
# purge_expired_notifications
# ---------------------------------------------------------------------------

class TestPurgeExpiredNotifications:
    def test_deletes_expired_rows_and_commits(self):
        mock_db = _make_db_mock(deleted=3)
        mock_notif = MagicMock()
        # Set expires_at to a real datetime so `expires_at < now` doesn't raise
        mock_notif.expires_at = datetime(2020, 1, 1, tzinfo=timezone.utc)

        with patch("app.extensions.db", mock_db), \
             patch("app.models.notification.Notification", mock_notif):
            result = purge_expired_notifications.run()

        assert result == {"deleted": 3}
        mock_db.session.commit.assert_called_once()

    def test_returns_zero_when_nothing_to_delete(self):
        mock_db = _make_db_mock(deleted=0)
        mock_notif = MagicMock()
        mock_notif.expires_at = datetime(2020, 1, 1, tzinfo=timezone.utc)

        with patch("app.extensions.db", mock_db), \
             patch("app.models.notification.Notification", mock_notif):
            result = purge_expired_notifications.run()

        assert result == {"deleted": 0}

    def test_queries_notification_model(self):
        """Verify db.session.query() is called with the Notification model."""
        mock_db = _make_db_mock(deleted=1)
        mock_notif = MagicMock()
        mock_notif.expires_at = datetime(2020, 1, 1, tzinfo=timezone.utc)

        with patch("app.extensions.db", mock_db), \
             patch("app.models.notification.Notification", mock_notif):
            purge_expired_notifications.run()

        mock_db.session.query.assert_called_once_with(mock_notif)


# ---------------------------------------------------------------------------
# purge_expired_admin_logs
# ---------------------------------------------------------------------------

class TestPurgeExpiredAdminLogs:
    def test_deletes_expired_rows_and_commits(self):
        mock_db = _make_db_mock(deleted=5)
        mock_log = MagicMock()
        mock_log.expires_at = datetime(2020, 1, 1, tzinfo=timezone.utc)

        with patch("app.extensions.db", mock_db), \
             patch("app.models.admin.AdminLog", mock_log):
            result = purge_expired_admin_logs.run()

        assert result == {"deleted": 5}
        mock_db.session.commit.assert_called_once()

    def test_returns_zero_when_nothing_to_delete(self):
        mock_db = _make_db_mock(deleted=0)
        mock_log = MagicMock()
        mock_log.expires_at = datetime(2020, 1, 1, tzinfo=timezone.utc)

        with patch("app.extensions.db", mock_db), \
             patch("app.models.admin.AdminLog", mock_log):
            result = purge_expired_admin_logs.run()

        assert result == {"deleted": 0}


# ---------------------------------------------------------------------------
# purge_soft_deleted_jobs
# ---------------------------------------------------------------------------

class TestPurgeSoftDeletedJobs:
    def test_hard_deletes_archived_jobs_and_commits(self):
        mock_db = _make_db_mock(deleted=2)
        mock_job = MagicMock()
        mock_job.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        mock_status = MagicMock()

        with patch("app.extensions.db", mock_db), \
             patch("app.models.job.JobVacancy", mock_job), \
             patch("app.utils.constants.JobStatus", mock_status):
            result = purge_soft_deleted_jobs.run()

        assert result == {"deleted": 2}
        mock_db.session.commit.assert_called_once()

    def test_returns_zero_when_no_archived_jobs(self):
        mock_db = _make_db_mock(deleted=0)
        mock_job = MagicMock()
        mock_job.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        mock_status = MagicMock()

        with patch("app.extensions.db", mock_db), \
             patch("app.models.job.JobVacancy", mock_job), \
             patch("app.utils.constants.JobStatus", mock_status):
            result = purge_soft_deleted_jobs.run()

        assert result == {"deleted": 0}

    def test_uses_90_day_cutoff(self):
        """Verify that timedelta(days=90) is used when computing the cutoff."""
        mock_db = _make_db_mock(deleted=0)
        mock_job = MagicMock()
        mock_job.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        mock_status = MagicMock()

        with patch("app.extensions.db", mock_db), \
             patch("app.models.job.JobVacancy", mock_job), \
             patch("app.utils.constants.JobStatus", mock_status), \
             patch("app.tasks.cleanup_tasks.timedelta", wraps=timedelta) as mock_td:
            purge_soft_deleted_jobs.run()

        mock_td.assert_called_once_with(days=90)


# ---------------------------------------------------------------------------
# close_expired_job_listings
# ---------------------------------------------------------------------------

class TestCloseExpiredJobListings:
    def test_closes_active_expired_jobs_and_commits(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.update.return_value = 4
        mock_job = MagicMock()
        mock_job.application_end = date(2020, 1, 1)
        mock_status = MagicMock()

        with patch("app.extensions.db", mock_db), \
             patch("app.models.job.JobVacancy", mock_job), \
             patch("app.utils.constants.JobStatus", mock_status):
            result = close_expired_job_listings.run()

        assert result == {"closed": 4}
        mock_db.session.commit.assert_called_once()

    def test_returns_zero_when_no_expired_jobs(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.update.return_value = 0
        mock_job = MagicMock()
        mock_job.application_end = date(2020, 1, 1)
        mock_status = MagicMock()

        with patch("app.extensions.db", mock_db), \
             patch("app.models.job.JobVacancy", mock_job), \
             patch("app.utils.constants.JobStatus", mock_status):
            result = close_expired_job_listings.run()

        assert result == {"closed": 0}

    def test_sets_status_to_closed(self):
        """Verify the update call sets status to JobStatus.CLOSED."""
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.update.return_value = 1
        mock_job = MagicMock()
        mock_job.application_end = date(2020, 1, 1)
        mock_status = MagicMock()

        with patch("app.extensions.db", mock_db), \
             patch("app.models.job.JobVacancy", mock_job), \
             patch("app.utils.constants.JobStatus", mock_status):
            close_expired_job_listings.run()

        update_call_kwargs = mock_db.session.query.return_value.filter.return_value.update.call_args
        assert update_call_kwargs is not None
        update_dict = update_call_kwargs[0][0]
        assert update_dict == {"status": mock_status.CLOSED}

