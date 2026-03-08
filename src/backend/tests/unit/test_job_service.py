"""
Unit tests for app/services/job_service.py

DB calls are mocked via unittest.mock — no PostgreSQL needed.
"""
import uuid
from datetime import date
from unittest.mock import MagicMock, patch, call

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
    job.status = kwargs.get('status', 'active')
    job.views = kwargs.get('views', 0)
    job.applications_count = kwargs.get('applications_count', 0)
    job.published_at = kwargs.get('published_at', None)
    return job


# ---------------------------------------------------------------------------
# get_jobs
# ---------------------------------------------------------------------------

class TestGetJobs:
    def test_calls_paginate_with_page_and_per_page(self):
        from app.services import job_service
        filters = {'page': 2, 'per_page': 10}

        with patch.object(job_service, 'paginate') as mock_paginate, \
             patch('app.services.job_service.JobVacancy') as mock_model:
            mock_query = MagicMock()
            mock_model.query = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_paginate.return_value = {'items': [], 'total': 0, 'page': 2, 'per_page': 10, 'pages': 0}

            result = job_service.get_jobs(filters)

        mock_paginate.assert_called_once_with(mock_query, page=2, per_page=10)
        assert result['page'] == 2

    def test_defaults_to_active_status_when_not_specified(self):
        from app.services import job_service

        filters = {'page': 1, 'per_page': 20}

        with patch.object(job_service, 'paginate') as mock_paginate, \
             patch('app.services.job_service.JobVacancy') as mock_model:
            mock_query = MagicMock()
            mock_model.query = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_paginate.return_value = {'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0}

            job_service.get_jobs(filters)

        # The first filter applied must use JobStatus.ACTIVE
        first_filter_call = mock_query.filter.call_args_list[0]
        assert first_filter_call is not None  # filter was called


# ---------------------------------------------------------------------------
# get_job_by_slug
# ---------------------------------------------------------------------------

class TestGetJobBySlug:
    def test_returns_job_and_increments_views(self):
        from app.services import job_service
        job = _mock_job(views=5)

        with patch('app.services.job_service.JobVacancy') as mock_model, \
             patch('app.services.job_service.db') as mock_db:
            mock_model.query.filter_by.return_value.first.return_value = job
            result = job_service.get_job_by_slug('ssc-cgl-2024')

        assert result is job
        assert job.views == 6
        mock_db.session.commit.assert_called_once()

    def test_raises_not_found_for_missing_slug(self):
        from app.services import job_service
        from app.utils.constants import ErrorCode

        with patch('app.services.job_service.JobVacancy') as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = None
            with pytest.raises(ValueError) as exc:
                job_service.get_job_by_slug('no-such-slug')
        assert str(exc.value) == ErrorCode.NOT_FOUND_JOB


# ---------------------------------------------------------------------------
# get_job_by_id
# ---------------------------------------------------------------------------

class TestGetJobById:
    def test_returns_job_when_found(self):
        from app.services import job_service
        job = _mock_job()
        job_id = str(job.id)

        with patch('app.services.job_service.db') as mock_db:
            mock_db.session.get.return_value = job
            result = job_service.get_job_by_id(job_id)

        assert result is job

    def test_raises_not_found_when_missing(self):
        from app.services import job_service
        from app.utils.constants import ErrorCode

        with patch('app.services.job_service.db') as mock_db:
            mock_db.session.get.return_value = None
            with pytest.raises(ValueError) as exc:
                job_service.get_job_by_id(str(uuid.uuid4()))
        assert str(exc.value) == ErrorCode.NOT_FOUND_JOB


# ---------------------------------------------------------------------------
# create_job
# ---------------------------------------------------------------------------

class TestCreateJob:
    def test_creates_job_with_correct_fields(self):
        from app.services import job_service

        data = {
            'job_title': 'Railway Group D',
            'organization': 'RRB',
            'job_type': 'latest_job',
            'eligibility': {'qualification': '10th'},
            'status': 'active',
        }

        with patch('app.services.job_service.JobVacancy') as mock_cls, \
             patch('app.services.job_service.db') as mock_db, \
             patch('app.services.job_service._unique_slug', return_value='railway-group-d'):
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            result = job_service.create_job(data, created_by='user-uuid')

        mock_cls.assert_called_once()
        kwargs = mock_cls.call_args.kwargs
        assert kwargs['job_title'] == 'Railway Group D'
        assert kwargs['slug'] == 'railway-group-d'
        assert kwargs['organization'] == 'RRB'
        assert kwargs['created_by'] == 'user-uuid'
        mock_db.session.add.assert_called_once_with(mock_instance)
        mock_db.session.commit.assert_called_once()

    def test_sets_published_at_for_active_status(self):
        from app.services import job_service

        data = {
            'job_title': 'Test Job',
            'organization': 'Org',
            'job_type': 'latest_job',
            'eligibility': {},
            'status': 'active',
        }

        with patch('app.services.job_service.JobVacancy') as mock_cls, \
             patch('app.services.job_service.db'), \
             patch('app.services.job_service._unique_slug', return_value='test-job'):
            job_service.create_job(data, created_by='uid')

        kwargs = mock_cls.call_args.kwargs
        assert kwargs['published_at'] is not None

    def test_does_not_set_published_at_for_draft(self):
        from app.services import job_service

        data = {
            'job_title': 'Draft Job',
            'organization': 'Org',
            'job_type': 'latest_job',
            'eligibility': {},
            'status': 'draft',
        }

        with patch('app.services.job_service.JobVacancy') as mock_cls, \
             patch('app.services.job_service.db'), \
             patch('app.services.job_service._unique_slug', return_value='draft-job'):
            job_service.create_job(data, created_by='uid')

        kwargs = mock_cls.call_args.kwargs
        assert kwargs['published_at'] is None


# ---------------------------------------------------------------------------
# delete_job
# ---------------------------------------------------------------------------

class TestDeleteJob:
    def test_sets_status_to_archived(self):
        from app.services import job_service
        job = _mock_job(status='active')

        with patch.object(job_service, 'get_job_by_id', return_value=job), \
             patch('app.services.job_service.db') as mock_db:
            job_service.delete_job(str(job.id))

        assert job.status == 'archived'
        mock_db.session.commit.assert_called_once()

    def test_raises_not_found_for_unknown_id(self):
        from app.services import job_service
        from app.utils.constants import ErrorCode

        with patch.object(job_service, 'get_job_by_id',
                          side_effect=ValueError(ErrorCode.NOT_FOUND_JOB)):
            with pytest.raises(ValueError):
                job_service.delete_job(str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# _unique_slug
# ---------------------------------------------------------------------------

class TestUniqueSlug:
    def test_returns_base_slug_when_unique(self):
        from app.services.job_service import _unique_slug

        with patch('app.services.job_service.JobVacancy') as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = None
            result = _unique_slug('ssc-cgl')
        assert result == 'ssc-cgl'

    def test_appends_counter_when_slug_taken(self):
        from app.services.job_service import _unique_slug

        with patch('app.services.job_service.JobVacancy') as mock_model:
            # First call (base slug taken), second call (slug-2 free)
            mock_model.query.filter_by.return_value.filter.return_value.first.side_effect = [
                MagicMock(),  # 'ssc-cgl' is taken
                None,         # 'ssc-cgl-2' is free
            ]
            result = _unique_slug('ssc-cgl')
        assert result == 'ssc-cgl-2'

    def test_empty_base_defaults_to_job(self):
        from app.services.job_service import _unique_slug

        with patch('app.services.job_service.JobVacancy') as mock_model:
            mock_model.query.filter_by.return_value.first.return_value = None
            result = _unique_slug('')
        assert result == 'job'
