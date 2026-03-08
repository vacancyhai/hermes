"""
Unit tests for app/services/user_service.py

DB calls are mocked via unittest.mock — no PostgreSQL needed.
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_user(**kwargs):
    user = MagicMock()
    user.id = kwargs.get('id', uuid.uuid4())
    user.email = kwargs.get('email', 'user@example.com')
    user.full_name = kwargs.get('full_name', 'Test User')
    user.role = kwargs.get('role', 'user')
    user.status = kwargs.get('status', 'active')
    user.phone = kwargs.get('phone', None)
    user.last_login = None
    user.created_at = None
    user.profile = kwargs.get('profile', MagicMock())
    return user


def _mock_profile(**kwargs):
    profile = MagicMock()
    profile.gender = kwargs.get('gender', None)
    profile.state = kwargs.get('state', None)
    profile.pincode = kwargs.get('pincode', None)
    profile.highest_qualification = kwargs.get('highest_qualification', None)
    profile.updated_at = None
    return profile


def _mock_application(**kwargs):
    app = MagicMock()
    app.id = kwargs.get('id', uuid.uuid4())
    app.user_id = kwargs.get('user_id', uuid.uuid4())
    app.job_id = kwargs.get('job_id', uuid.uuid4())
    app.status = kwargs.get('status', 'applied')
    app.is_priority = False
    app.application_number = None
    app.notes = None
    app.applied_on = None
    return app


# ---------------------------------------------------------------------------
# get_profile
# ---------------------------------------------------------------------------

class TestGetProfile:
    def test_returns_user_and_profile(self):
        from app.services import user_service
        user = _mock_user()

        with patch('app.services.user_service.db') as mock_db:
            mock_db.session.get.return_value = user
            result_user, result_profile = user_service.get_profile(str(user.id))

        assert result_user is user
        assert result_profile is user.profile

    def test_raises_not_found_for_missing_user(self):
        from app.services import user_service
        from app.utils.constants import ErrorCode

        with patch('app.services.user_service.db') as mock_db:
            mock_db.session.get.return_value = None
            with pytest.raises(ValueError) as exc:
                user_service.get_profile(str(uuid.uuid4()))
        assert str(exc.value) == ErrorCode.NOT_FOUND_USER

    def test_raises_not_found_for_suspended_user(self):
        from app.services import user_service
        from app.utils.constants import ErrorCode

        user = _mock_user(status='suspended')

        with patch('app.services.user_service.db') as mock_db:
            mock_db.session.get.return_value = user
            with pytest.raises(ValueError) as exc:
                user_service.get_profile(str(user.id))
        assert str(exc.value) == ErrorCode.NOT_FOUND_USER


# ---------------------------------------------------------------------------
# update_profile
# ---------------------------------------------------------------------------

class TestUpdateProfile:
    def test_updates_non_none_fields(self):
        from app.services import user_service
        profile = _mock_profile()
        user = _mock_user(profile=profile)

        with patch.object(user_service, 'get_profile', return_value=(user, profile)), \
             patch('app.services.user_service.db') as mock_db:
            user_service.update_profile(str(user.id), {
                'gender': 'male',
                'state': 'Maharashtra',
            })

        assert profile.gender == 'male'
        assert profile.state == 'Maharashtra'
        mock_db.session.commit.assert_called_once()

    def test_does_not_overwrite_with_none(self):
        from app.services import user_service
        profile = _mock_profile(gender='female')
        user = _mock_user(profile=profile)

        with patch.object(user_service, 'get_profile', return_value=(user, profile)), \
             patch('app.services.user_service.db'):
            # data contains only state; gender=None means "not provided"
            user_service.update_profile(str(user.id), {
                'gender': None,
                'state': 'Gujarat',
            })

        assert profile.gender == 'female'  # unchanged
        assert profile.state == 'Gujarat'


# ---------------------------------------------------------------------------
# apply_to_job
# ---------------------------------------------------------------------------

class TestApplyToJob:
    def test_creates_application_and_increments_count(self):
        from app.services import user_service
        job = MagicMock()
        job.status = 'active'
        job.applications_count = 3

        with patch('app.services.user_service.db') as mock_db, \
             patch('app.services.user_service.UserJobApplication') as mock_app_cls, \
             patch('app.services.user_service.JobVacancy'):
            mock_db.session.get.return_value = job
            mock_db.session.get.side_effect = None
            # Override get for job
            mock_db.session.get.return_value = job

            mock_app_cls.query.filter_by.return_value.first.return_value = None
            mock_instance = MagicMock()
            mock_app_cls.return_value = mock_instance

            result = user_service.apply_to_job('user-id', 'job-id')

        assert job.applications_count == 4
        mock_db.session.add.assert_called_once_with(mock_instance)
        mock_db.session.commit.assert_called_once()

    def test_raises_not_found_for_inactive_job(self):
        from app.services import user_service
        from app.utils.constants import ErrorCode

        job = MagicMock()
        job.status = 'closed'

        with patch('app.services.user_service.db') as mock_db:
            mock_db.session.get.return_value = job
            with pytest.raises(ValueError) as exc:
                user_service.apply_to_job('user-id', 'job-id')
        assert str(exc.value) == ErrorCode.NOT_FOUND_JOB

    def test_raises_not_found_for_missing_job(self):
        from app.services import user_service
        from app.utils.constants import ErrorCode

        with patch('app.services.user_service.db') as mock_db:
            mock_db.session.get.return_value = None
            with pytest.raises(ValueError) as exc:
                user_service.apply_to_job('user-id', 'job-id')
        assert str(exc.value) == ErrorCode.NOT_FOUND_JOB

    def test_raises_already_applied_on_duplicate(self):
        from app.services import user_service
        job = MagicMock()
        job.status = 'active'

        with patch('app.services.user_service.db') as mock_db, \
             patch('app.services.user_service.UserJobApplication') as mock_app_cls:
            mock_db.session.get.return_value = job
            mock_app_cls.query.filter_by.return_value.first.return_value = MagicMock()
            with pytest.raises(ValueError) as exc:
                user_service.apply_to_job('user-id', 'job-id')
        assert str(exc.value) == 'ALREADY_APPLIED'


# ---------------------------------------------------------------------------
# withdraw_application
# ---------------------------------------------------------------------------

class TestWithdrawApplication:
    def test_sets_status_to_withdrawn(self):
        from app.services import user_service
        application = _mock_application(status='applied')
        job = MagicMock()
        job.applications_count = 5

        with patch('app.services.user_service.UserJobApplication') as mock_cls, \
             patch('app.services.user_service.db') as mock_db:
            mock_cls.query.filter_by.return_value.first.return_value = application
            mock_db.session.get.return_value = job

            user_service.withdraw_application('user-id', str(application.id))

        assert application.status == 'withdrawn'
        assert job.applications_count == 4
        mock_db.session.commit.assert_called_once()

    def test_raises_not_found_for_wrong_user(self):
        from app.services import user_service
        from app.utils.constants import ErrorCode

        with patch('app.services.user_service.UserJobApplication') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = None
            with pytest.raises(ValueError) as exc:
                user_service.withdraw_application('wrong-user', 'app-id')
        assert str(exc.value) == ErrorCode.NOT_FOUND_APPLICATION

    def test_idempotent_for_already_withdrawn(self):
        from app.services import user_service
        application = _mock_application(status='withdrawn')

        with patch('app.services.user_service.UserJobApplication') as mock_cls, \
             patch('app.services.user_service.db') as mock_db:
            mock_cls.query.filter_by.return_value.first.return_value = application
            user_service.withdraw_application('user-id', str(application.id))

        # Status stays 'withdrawn'; commit not called (no change needed)
        assert application.status == 'withdrawn'
        mock_db.session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# update_user_status
# ---------------------------------------------------------------------------

class TestUpdateUserStatus:
    def test_updates_status_successfully(self):
        from app.services import user_service
        user = _mock_user(status='active')

        with patch('app.services.user_service.db') as mock_db:
            mock_db.session.get.return_value = user
            result = user_service.update_user_status(str(user.id), 'suspended')

        assert user.status == 'suspended'
        mock_db.session.commit.assert_called_once()
        assert result is user

    def test_raises_invalid_status_for_unknown_value(self):
        from app.services import user_service
        with pytest.raises(ValueError) as exc:
            user_service.update_user_status('uid', 'banned')
        assert str(exc.value) == 'INVALID_STATUS'

    def test_raises_not_found_for_missing_user(self):
        from app.services import user_service
        from app.utils.constants import ErrorCode

        with patch('app.services.user_service.db') as mock_db:
            mock_db.session.get.return_value = None
            with pytest.raises(ValueError) as exc:
                user_service.update_user_status(str(uuid.uuid4()), 'suspended')
        assert str(exc.value) == ErrorCode.NOT_FOUND_USER
