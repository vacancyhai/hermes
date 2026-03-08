"""
Unit tests for app/tasks/views_flush_task.py

Uses fakeredis + a minimal Flask app so current_app.redis works.
DB calls are mocked via unittest.mock — no PostgreSQL needed.
"""
import uuid
from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from flask import Flask


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def redis_client():
    """Fresh fakeredis instance per test."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture()
def flask_app(redis_client):
    """Minimal Flask app with fakeredis attached as app.redis."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.redis = redis_client
    return app


# ---------------------------------------------------------------------------
# flush_job_views
# ---------------------------------------------------------------------------

class TestFlushJobViews:
    def test_returns_zeros_when_no_keys(self, flask_app):
        from app.tasks.views_flush_task import flush_job_views

        with flask_app.app_context(), \
             patch('app.extensions.db'):
            result = flush_job_views.run()

        assert result == {'jobs_updated': 0, 'total_views_flushed': 0}

    def test_flushes_single_job_views_to_db(self, flask_app, redis_client):
        from app.tasks.views_flush_task import flush_job_views

        job_id = str(uuid.uuid4())
        redis_client.set(f'job:views:{job_id}', '15')

        mock_job = MagicMock()
        mock_job.views = 100

        with flask_app.app_context(), \
             patch('app.extensions.db') as mock_db:

            mock_db.session.get.return_value = mock_job

            result = flush_job_views.run()

        assert result['jobs_updated'] == 1
        assert result['total_views_flushed'] == 15
        assert mock_job.views == 115  # 100 + 15
        mock_db.session.commit.assert_called_once()

    def test_flushes_multiple_jobs(self, flask_app, redis_client):
        from app.tasks.views_flush_task import flush_job_views

        ids = [str(uuid.uuid4()) for _ in range(3)]
        for i, jid in enumerate(ids):
            redis_client.set(f'job:views:{jid}', str(i + 1))

        jobs = {jid: MagicMock(views=0) for jid in ids}

        with flask_app.app_context(), \
             patch('app.extensions.db') as mock_db:

            mock_db.session.get.side_effect = lambda model, jid: jobs.get(jid)

            result = flush_job_views.run()

        assert result['jobs_updated'] == 3
        assert result['total_views_flushed'] == 1 + 2 + 3

    def test_redis_key_deleted_after_flush(self, flask_app, redis_client):
        from app.tasks.views_flush_task import flush_job_views

        job_id = str(uuid.uuid4())
        redis_client.set(f'job:views:{job_id}', '5')
        mock_job = MagicMock(views=0)

        with flask_app.app_context(), \
             patch('app.extensions.db') as mock_db:

            mock_db.session.get.return_value = mock_job
            flush_job_views.run()

        # Key must be gone after flush
        assert redis_client.get(f'job:views:{job_id}') is None

    def test_skips_unknown_job_id(self, flask_app, redis_client):
        from app.tasks.views_flush_task import flush_job_views

        job_id = str(uuid.uuid4())
        redis_client.set(f'job:views:{job_id}', '10')

        with flask_app.app_context(), \
             patch('app.extensions.db') as mock_db:

            mock_db.session.get.return_value = None   # job not in DB

            result = flush_job_views.run()

        assert result['jobs_updated'] == 0
        assert result['total_views_flushed'] == 0
        mock_db.session.commit.assert_not_called()

    def test_rolls_back_on_commit_failure(self, flask_app, redis_client):
        from app.tasks.views_flush_task import flush_job_views

        job_id = str(uuid.uuid4())
        redis_client.set(f'job:views:{job_id}', '7')
        mock_job = MagicMock(views=0)

        with flask_app.app_context(), \
             patch('app.extensions.db') as mock_db:

            mock_db.session.get.return_value = mock_job
            mock_db.session.commit.side_effect = Exception('DB error')

            result = flush_job_views.run()

        mock_db.session.rollback.assert_called_once()
        assert result == {'jobs_updated': 0, 'total_views_flushed': 0}

    def test_ignores_invalid_redis_values(self, flask_app, redis_client):
        from app.tasks.views_flush_task import flush_job_views

        job_id = str(uuid.uuid4())
        redis_client.set(f'job:views:{job_id}', 'not-a-number')

        with flask_app.app_context(), \
             patch('app.extensions.db') as mock_db:

            result = flush_job_views.run()

        assert result['jobs_updated'] == 0
        assert result['total_views_flushed'] == 0
        mock_db.session.commit.assert_not_called()

    def test_ignores_zero_delta(self, flask_app, redis_client):
        from app.tasks.views_flush_task import flush_job_views

        job_id = str(uuid.uuid4())
        redis_client.set(f'job:views:{job_id}', '0')

        with flask_app.app_context(), \
             patch('app.extensions.db') as mock_db:

            result = flush_job_views.run()

        assert result['jobs_updated'] == 0
        mock_db.session.commit.assert_not_called()
