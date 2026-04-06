"""Shared Flask/form utility helpers for the user frontend."""

from flask import request


def _int_arg(name: str, default: int) -> int:
    """Parse an integer query parameter safely."""
    try:
        return int(request.args.get(name, default))
    except (ValueError, TypeError):
        return default
