"""
Utility helpers used by service and route layers.

Functions:
    paginate(query, page, per_page)  — wraps a SQLAlchemy BaseQuery
    success_response(data, ...)      — standard JSON success envelope
    slugify(text)                    — URL-safe slug from arbitrary text
"""
import re
import unicodedata

from flask import jsonify, request

_MAX_PER_PAGE = 100


def paginate(query, page: int = None, per_page: int = None) -> dict:
    """
    Execute a paginated SQLAlchemy query and return a plain dict.

    page and per_page are read from request.args if not supplied explicitly.
    per_page is capped at _MAX_PER_PAGE (100) regardless of the caller's input.

    Returns:
        {
            "items":    [<model instances>],
            "total":    int,
            "page":     int,
            "per_page": int,
            "pages":    int,
        }
    """
    if page is None:
        try:
            page = max(1, int(request.args.get('page', 1)))
        except (TypeError, ValueError):
            page = 1

    if per_page is None:
        try:
            per_page = int(request.args.get('per_page', 20))
        except (TypeError, ValueError):
            per_page = 20

    per_page = max(1, min(per_page, _MAX_PER_PAGE))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }


def success_response(data, status_code: int = 200, meta: dict = None):
    """
    Return a standard JSON success envelope as a Flask (response, status) tuple.

    Shape: {"success": true, "data": <data>, ...<meta keys>}

    Args:
        data:        Serialisable payload (dict, list, or None).
        status_code: HTTP status code (default 200).
        meta:        Optional dict of extra top-level keys, e.g. pagination info.
    """
    body = {'success': True, 'data': data}
    if meta:
        body.update(meta)
    return jsonify(body), status_code


def slugify(text: str) -> str:
    """
    Convert arbitrary text to a URL-safe lowercase slug.

    Steps:
      1. NFKD-normalise → decompose characters (accent stripping).
      2. Encode to ASCII, ignoring non-ASCII bytes.
      3. Lowercase.
      4. Replace any run of non-alphanumeric characters with a single '-'.
      5. Strip leading/trailing '-'.

    Returns '' for empty or whitespace-only input, and for text that contains
    no ASCII-representable characters (e.g. pure Devanagari).

    Examples:
        slugify('SSC CGL 2024')          → 'ssc-cgl-2024'
        slugify('  UPSC–IAS ')           → 'upsc-ias'
        slugify('café')                  → 'cafe'
        slugify('रेलवे भर्ती')           → ''
    """
    if not text or not text.strip():
        return ''

    normalised = unicodedata.normalize('NFKD', text)
    ascii_bytes = normalised.encode('ascii', 'ignore')
    lower = ascii_bytes.decode('ascii').lower()
    slug = re.sub(r'[^a-z0-9]+', '-', lower)
    return slug.strip('-')
