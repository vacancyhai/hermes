"""SEO Celery tasks."""

from app.celery_app import celery


@celery.task(name="app.tasks.seo.generate_sitemap")
def generate_sitemap():
    """Regenerate /sitemap.xml with all active job URLs. Daily 04:00 UTC.
    TODO: Implement.
    """
    pass
