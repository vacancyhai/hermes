"""SEO Celery tasks — sitemap generation.

Scheduled:
  generate_sitemap  — Daily 04:00 UTC, writes /app/sitemap.xml
"""

import os
from xml.etree.ElementTree import Element, ElementTree, SubElement

from app.celery_app import celery
from app.database import sync_engine
from sqlalchemy import text
from sqlalchemy.orm import Session

SITE_URL = os.environ.get("SITE_URL", "http://localhost:8080")
SITEMAP_PATH = os.environ.get("SITEMAP_PATH", "/app/sitemap.xml")


@celery.task(name="app.tasks.seo.generate_sitemap")
def generate_sitemap():
    """Regenerate /sitemap.xml with all active job + admission exam URLs. Daily 04:00 UTC."""
    with Session(sync_engine) as session:
        jobs = session.execute(
            text(
                "SELECT slug, updated_at FROM jobs WHERE status = 'active' ORDER BY updated_at DESC"
            )
        ).fetchall()
        exams = session.execute(
            text(
                "SELECT slug, updated_at FROM entrance_exams"
                " WHERE status IN ('active','upcoming') ORDER BY updated_at DESC"
            )
        ).fetchall()

    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Section pages
    for path, freq, priority in [
        ("/", "daily", "1.0"),
        ("/admit-cards", "daily", "0.9"),
        ("/answer-keys", "daily", "0.9"),
        ("/results", "daily", "0.9"),
        ("/entrance-exams", "daily", "0.9"),
    ]:
        url_el = SubElement(urlset, "url")
        SubElement(url_el, "loc").text = f"{SITE_URL}{path}"
        SubElement(url_el, "changefreq").text = freq
        SubElement(url_el, "priority").text = priority

    # Job detail pages
    for slug, updated_at in jobs:
        url_el = SubElement(urlset, "url")
        SubElement(url_el, "loc").text = f"{SITE_URL}/jobs/{slug}"
        if updated_at:
            SubElement(url_el, "lastmod").text = updated_at.strftime("%Y-%m-%d")
        SubElement(url_el, "changefreq").text = "daily"
        SubElement(url_el, "priority").text = "0.8"

    # Admission exam detail pages
    for slug, updated_at in exams:
        url_el = SubElement(urlset, "url")
        SubElement(url_el, "loc").text = f"{SITE_URL}/entrance-exams/{slug}"
        if updated_at:
            SubElement(url_el, "lastmod").text = updated_at.strftime("%Y-%m-%d")
        SubElement(url_el, "changefreq").text = "weekly"
        SubElement(url_el, "priority").text = "0.8"

    tree = ElementTree(urlset)
    tree.write(SITEMAP_PATH, xml_declaration=True, encoding="UTF-8")

    return {"jobs_count": len(jobs), "exams_count": len(exams), "path": SITEMAP_PATH}
