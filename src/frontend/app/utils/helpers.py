"""
Jinja2 / view-layer helpers for the user frontend.

Registered as template filters and global functions in create_app().
Import helpers directly in route code where needed as well.
"""
from __future__ import annotations

from datetime import date, datetime


# ---------------------------------------------------------------------------
# Date / time formatters
# ---------------------------------------------------------------------------

def format_date(value, fmt: str = "%d %b %Y") -> str:
    """
    Format a date or ISO-8601 string for display.

    Usage in templates: {{ job.application_end | format_date }}

    Returns 'N/A' if value is None or cannot be parsed.
    """
    if value is None:
        return "N/A"
    if isinstance(value, (date, datetime)):
        return value.strftime(fmt)
    # Try parsing ISO string
    for pattern in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(str(value), pattern).strftime(fmt)
        except ValueError:
            continue
    return str(value)


def time_ago(value) -> str:
    """
    Human-readable relative time (e.g. "2 hours ago", "3 days ago").

    Accepts datetime objects or ISO-8601 strings.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return str(value)

    now = datetime.utcnow()
    if hasattr(value, "tzinfo") and value.tzinfo is not None:
        value = value.replace(tzinfo=None)

    delta = now - value
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        m = seconds // 60
        return f"{m} minute{'s' if m > 1 else ''} ago"
    if seconds < 86400:
        h = seconds // 3600
        return f"{h} hour{'s' if h > 1 else ''} ago"
    if seconds < 86400 * 30:
        d = seconds // 86400
        return f"{d} day{'s' if d > 1 else ''} ago"
    if seconds < 86400 * 365:
        mo = seconds // (86400 * 30)
        return f"{mo} month{'s' if mo > 1 else ''} ago"
    y = seconds // (86400 * 365)
    return f"{y} year{'s' if y > 1 else ''} ago"


def days_remaining(end_date) -> str:
    """
    Return a human-readable string for days left until a deadline.

    Examples: "3 days left", "Closed", "Last day!"
    """
    if end_date is None:
        return ""
    if isinstance(end_date, str):
        try:
            end_date = date.fromisoformat(end_date)
        except ValueError:
            return ""
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    today = date.today()
    delta = (end_date - today).days

    if delta < 0:
        return "Closed"
    if delta == 0:
        return "Last day!"
    if delta == 1:
        return "1 day left"
    return f"{delta} days left"


# ---------------------------------------------------------------------------
# Number / salary formatters
# ---------------------------------------------------------------------------

def format_salary(value) -> str:
    """
    Format an integer salary (in INR) as a human-readable string.

    Examples: 25000 → '₹25,000', 1200000 → '₹12 LPA'
    """
    if value is None:
        return "N/A"
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)

    if value >= 100_000:
        lpa = value / 100_000
        return f"₹{lpa:.1f} LPA".rstrip("0").rstrip(".")
    # Indian number formatting: 1,00,000
    return f"₹{value:,}"


def format_number(value) -> str:
    """Format a large integer with commas: 12345 → '12,345'."""
    if value is None:
        return "0"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------

def truncate(text: str, length: int = 150, suffix: str = "…") -> str:
    """Truncate text to `length` characters, appending suffix."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + suffix


def job_type_label(job_type: str) -> str:
    """Return a human-friendly label for a job_type constant."""
    _map = {
        "latest_job": "Latest Job",
        "result": "Result",
        "admit_card": "Admit Card",
        "answer_key": "Answer Key",
        "admission": "Admission",
        "yojana": "Yojana",
    }
    return _map.get(job_type, job_type.replace("_", " ").title() if job_type else "")


def qualification_label(qual: str) -> str:
    """Return display label for qualification_level constants."""
    _map = {
        "10th": "10th Pass",
        "12th": "12th Pass",
        "diploma": "Diploma",
        "graduation": "Graduate",
        "post_graduation": "Post Graduate",
        "phd": "PhD",
    }
    return _map.get(qual, qual.replace("_", " ").title() if qual else "")


# ---------------------------------------------------------------------------
# Registration helper — call from create_app()
# ---------------------------------------------------------------------------

def register_template_helpers(app) -> None:
    """
    Register all helpers as Jinja2 filters and global functions.

    Call this inside create_app() after the app object is created:

        from app.utils.helpers import register_template_helpers
        register_template_helpers(app)
    """
    # Filters  (used as {{ value | filter_name }})
    app.jinja_env.filters["format_date"] = format_date
    app.jinja_env.filters["time_ago"] = time_ago
    app.jinja_env.filters["days_remaining"] = days_remaining
    app.jinja_env.filters["format_salary"] = format_salary
    app.jinja_env.filters["format_number"] = format_number
    app.jinja_env.filters["truncate_text"] = truncate
    app.jinja_env.filters["job_type_label"] = job_type_label
    app.jinja_env.filters["qualification_label"] = qualification_label

    # Global functions (used as {{ format_date(value) }} in templates)
    app.jinja_env.globals["days_remaining"] = days_remaining
