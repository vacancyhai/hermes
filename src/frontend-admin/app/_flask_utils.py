"""Shared Flask/form utility helpers for the admin frontend."""

from flask import request


def _int_arg(name: str, default: int) -> int:
    """Parse an integer query parameter safely."""
    try:
        return int(request.args.get(name, default))
    except (ValueError, TypeError):
        return default


def _pick_text_fields(form: dict, fields: list, payload: dict) -> None:
    """Copy present text fields from form into payload; missing/empty become None."""
    for f in fields:
        if f in form:
            payload[f] = form[f] or None


def _pick_int_fields(form: dict, fields: list, payload: dict) -> None:
    """Parse present integer fields from form into payload; missing/empty become None."""
    for f in fields:
        if f in form:
            val = form[f].strip()
            payload[f] = int(val) if val else None


def _pick_date_fields(form: dict, fields: list, payload: dict) -> None:
    """Copy present date string fields from form into payload; empty become None."""
    for f in fields:
        if f in form:
            val = form[f].strip()
            payload[f] = val if val else None


def _set_int_fields(form: dict, fields: list, payload: dict) -> None:
    """Parse all integer fields from form into payload; empty become None."""
    for f in fields:
        val = form.get(f, "").strip()
        payload[f] = int(val) if val else None


def _set_optional(form: dict, fields: list, payload: dict) -> None:
    """Copy all string fields from form into payload; empty become None."""
    for f in fields:
        val = form.get(f, "").strip()
        payload[f] = val if val else None


def _set_or_none(form: dict, fields: list, payload: dict) -> None:
    """Copy all fields from form into payload using form.get(f) or None."""
    for f in fields:
        payload[f] = form.get(f) or None


def _pick_nonempty(form: dict, fields: list, payload: dict) -> None:
    """Copy non-empty string fields from form into payload; skip empty/missing."""
    for f in fields:
        val = form.get(f, "").strip()
        if val:
            payload[f] = val
