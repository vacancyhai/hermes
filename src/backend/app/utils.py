"""Shared utilities — constants and helpers used across multiple modules."""

import re

# JWT algorithm — single source of truth (also imported by dependencies.py and auth.py)
ALGORITHM = "HS256"

# Maximum FCM tokens per user — also enforced in Celery tasks
MAX_FCM_TOKENS = 10


def slugify(text: str) -> str:
    """Generate a URL-safe slug from arbitrary text."""
    slug = re.sub(r"[^\w\s-]", "", text.lower().strip())
    slug = re.sub(r"[\s_]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-")
