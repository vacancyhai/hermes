"""SEO Celery tasks — sitemap generation.

Scheduled:
  generate_sitemap  — Daily 04:00 UTC, writes /app/sitemap.xml
"""

import os
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, ElementTree

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.celery_app import celery
from app.database import sync_engine

SITE_URL = os.environ.get("SITE_URL", "http://localhost:8080")
SITEMAP_PATH = os.environ.get("SITEMAP_PATH", "/app/sitemap.xml")


@celery.task(name="app.tasks.seo.generate_sitemap")
def generate_sitemap():
    """Regenerate /sitemap.xml with all active job URLs. Daily 04:00 UTC."""
    with Session(sync_engine) as session:
        result = session.execute(
            text("SELECT slug, updated_at FROM job_vacancies WHERE status = 'active' ORDER BY updated_at DESC")
        )
        jobs = result.fetchall()

    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Homepage
    home = SubElement(urlset, "url")
    SubElement(home, "loc").text = SITE_URL
    SubElement(home, "changefreq").text = "daily"
    SubElement(home, "priority").text = "1.0"

    # Job pages
    for slug, updated_at in jobs:
        url_el = SubElement(urlset, "url")
        SubElement(url_el, "loc").text = f"{SITE_URL}/jobs/{slug}"
        if updated_at:
            SubElement(url_el, "lastmod").text = updated_at.strftime("%Y-%m-%d")
        SubElement(url_el, "changefreq").text = "daily"
        SubElement(url_el, "priority").text = "0.8"

    tree = ElementTree(urlset)
    tree.write(SITEMAP_PATH, xml_declaration=True, encoding="UTF-8")

    return {"jobs_count": len(jobs), "path": SITEMAP_PATH}
