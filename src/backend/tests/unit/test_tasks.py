"""Unit tests for Celery tasks — cleanup, seo, jobs.

All DB calls are mocked so these run without a live database/Redis/Celery broker.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch, call


# ─── cleanup tasks ────────────────────────────────────────────────────────────

def _make_conn_ctx(rowcount: int = 3):
    """Build a mock that works as a context-manager for sync_engine.connect()."""
    conn = MagicMock()
    result = MagicMock()
    result.rowcount = rowcount
    conn.execute.return_value = result
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=conn)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx, conn


def test_execute_cleanup_returns_rowcount():
    ctx, conn = _make_conn_ctx(rowcount=5)
    with patch("app.tasks.cleanup.sync_engine") as mock_engine:
        mock_engine.connect.return_value = ctx
        from app.tasks.cleanup import _execute_cleanup
        count = _execute_cleanup("DELETE FROM foo WHERE 1=1")

    assert count == 5
    conn.commit.assert_called_once()


def test_purge_expired_notifications():
    ctx, _ = _make_conn_ctx(rowcount=2)
    with patch("app.tasks.cleanup.sync_engine") as mock_engine:
        mock_engine.connect.return_value = ctx
        from app.tasks.cleanup import purge_expired_notifications
        result = purge_expired_notifications()

    assert result == {"purged_notifications": 2}


def test_purge_expired_admin_logs():
    ctx, _ = _make_conn_ctx(rowcount=1)
    with patch("app.tasks.cleanup.sync_engine") as mock_engine:
        mock_engine.connect.return_value = ctx
        from app.tasks.cleanup import purge_expired_admin_logs
        result = purge_expired_admin_logs()

    assert result == {"purged_admin_logs": 1}


def test_purge_soft_deleted_jobs():
    ctx, _ = _make_conn_ctx(rowcount=0)
    with patch("app.tasks.cleanup.sync_engine") as mock_engine:
        mock_engine.connect.return_value = ctx
        from app.tasks.cleanup import purge_soft_deleted_jobs
        result = purge_soft_deleted_jobs()

    assert result == {"purged_jobs": 0}


# ─── seo tasks ────────────────────────────────────────────────────────────────

def _make_session_ctx(rows=None):
    """Build a mock for Session(sync_engine) context manager."""
    session = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = rows or []
    session.execute.return_value = result
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


def test_generate_sitemap_empty():
    """Sitemap is generated even when no active jobs exist."""
    from datetime import datetime, timezone
    session_ctx = _make_session_ctx(rows=[])

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        tmp_path = f.name

    try:
        with patch("app.tasks.seo.Session", return_value=session_ctx), \
             patch("app.tasks.seo.SITEMAP_PATH", tmp_path):
            from app.tasks.seo import generate_sitemap
            result = generate_sitemap()

        assert result["jobs_count"] == 0
        assert os.path.exists(tmp_path)
        with open(tmp_path, "rb") as f:
            content = f.read()
        assert b"urlset" in content
    finally:
        os.unlink(tmp_path)


def test_generate_sitemap_with_jobs():
    """Sitemap includes job URLs."""
    from datetime import datetime, timezone
    slug = "ssc-cgl-2024"
    updated_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    session_ctx = _make_session_ctx(rows=[(slug, updated_at)])

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        tmp_path = f.name

    try:
        with patch("app.tasks.seo.Session", return_value=session_ctx), \
             patch("app.tasks.seo.SITEMAP_PATH", tmp_path), \
             patch("app.tasks.seo.SITE_URL", "http://example.com"):
            from app.tasks.seo import generate_sitemap
            result = generate_sitemap()

        assert result["jobs_count"] == 1
        with open(tmp_path, "rb") as f:
            content = f.read()
        assert b"ssc-cgl-2024" in content
        assert b"example.com" in content
    finally:
        os.unlink(tmp_path)


def test_generate_sitemap_job_no_updated_at():
    """Jobs with null updated_at are still included (no lastmod tag)."""
    session_ctx = _make_session_ctx(rows=[("test-job-slug", None)])

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        tmp_path = f.name

    try:
        with patch("app.tasks.seo.Session", return_value=session_ctx), \
             patch("app.tasks.seo.SITEMAP_PATH", tmp_path):
            from app.tasks.seo import generate_sitemap
            result = generate_sitemap()

        assert result["jobs_count"] == 1
    finally:
        os.unlink(tmp_path)


# ─── jobs tasks ───────────────────────────────────────────────────────────────

def test_close_expired_job_listings_none_expired():
    session = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = []  # no rows returned (no expired jobs)
    session.execute.return_value = result
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.jobs.Session", return_value=ctx):
        from app.tasks.jobs import close_expired_job_listings
        result_dict = close_expired_job_listings()

    assert result_dict == {"closed_count": 0}
    session.commit.assert_called_once()


def test_close_expired_job_listings_some_expired():
    import uuid as _uuid
    expired_ids = [_uuid.uuid4(), _uuid.uuid4()]
    session = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = [(eid,) for eid in expired_ids]
    session.execute.return_value = result
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=session)
    ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.tasks.jobs.Session", return_value=ctx):
        from app.tasks.jobs import close_expired_job_listings
        result_dict = close_expired_job_listings()

    assert result_dict == {"closed_count": 2}
