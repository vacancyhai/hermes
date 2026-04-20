"""Hermes Admin Frontend — Flask + Jinja2 + HTMX.

Routes:
  /health                         — Health check
  /                               — Dashboard (stats, quick links)
  /login                          — Admin login
  /logout                         — Clear session
  /jobs                           — Job management (list)
  /jobs/new                       — Create job
  /jobs/<id>/edit                 — Edit job + manage phase docs
  /jobs/<id>/delete               — POST: soft-delete job
  /jobs/<id>/docs/admit-cards     — POST: add admit card to job
  /jobs/<id>/docs/answer-keys     — POST: add answer key to job
  /jobs/<id>/docs/results         — POST: add result to job
  /jobs/<id>/docs/<type>/<id>/delete — POST: delete doc from job
  /admissions                 — Admission management
  /admissions/new             — Create admission
  /admissions/<id>/edit       — Edit admission
  /admissions/<id>/delete     — POST: delete admission
  /admissions/<id>/docs/...   — POST: add/delete docs on admission
  /users                          — User management (list, search, status filter)
  /users/<id>                     — User detail
  /users/<id>/suspend             — Toggle user suspend/activate
  /users/<id>/delete              — Permanently delete user
  /logs                           — Admin audit log viewer
  /organizations                   — Organization management (list)
  /organizations/new               — Create organization
  /organizations/<id>/edit         — Edit organization
  /organizations/<id>/delete       — POST: delete organization
"""

import base64
import json
import os
import secrets
import uuid as _uuid

from datetime import timedelta

from flask import Blueprint, Flask, current_app, flash, redirect, render_template, request, session

from app._flask_utils import (
    _int_arg,
    _pick_date_fields,
    _pick_int_fields,
    _pick_nonempty,
    _pick_text_fields,
    _set_int_fields,
    _set_optional,
    _set_or_none,
)
from app.api_client import ApiClient


def _jwt_payload(token: str) -> dict:
    """Decode JWT payload without signature verification (read-only)."""
    try:
        part = token.split(".")[1]
        part += "=" * (4 - len(part) % 4)
        return json.loads(base64.b64decode(part))
    except Exception:
        return {}


_URL_LOGIN = "/login"
_URL_JOBS = "/jobs"
_URL_ADMISSIONS = "/admissions"
_API_ADMIN_JOBS = "/admin/jobs"
_API_ADMIN_ADMIT_CARDS = "/admin/admit-cards"
_API_ADMIN_ANSWER_KEYS = "/admin/answer-keys"
_API_ADMIN_RESULTS = "/admin/results"
_API_ADMIN_ADMISSIONS = "/admin/admissions"
_CONTENT_TYPE_JSON = "application/json"
_URL_USERS = "/users"
_URL_ORGANIZATIONS = "/organizations"
_API_ADMIN_ORGANIZATIONS = "/admin/organizations"

_DOC_TYPE_API = {
    "admit-cards": _API_ADMIN_ADMIT_CARDS,
    "answer-keys": _API_ADMIN_ANSWER_KEYS,
    "results": _API_ADMIN_RESULTS,
}

_DOC_FLASH = {
    "admit-cards": "Admit card added.",
    "answer-keys": "Answer key added.",
    "results": "Result added.",
}

_PARENT_BASE_URL = {
    "job_id": _URL_JOBS,
    "admission_id": _URL_ADMISSIONS,
}


def _add_doc(parent_key: str, parent_id: str, doc_type: str):
    """Shared handler for adding a phase document (admit card / answer key / result)."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    try:
        safe_id = str(_uuid.UUID(parent_id))
    except ValueError:
        flash("Invalid parent ID.", "error")
        return redirect(_PARENT_BASE_URL.get(parent_key, "/"))
    base = _PARENT_BASE_URL.get(parent_key, "/")
    back_url = f"{base}/{safe_id}/edit#docs"
    api_url = _DOC_TYPE_API.get(doc_type)
    if not api_url:
        flash("Unknown document type.", "error")
        return redirect(back_url)
    form = request.form.to_dict()
    try:
        links = json.loads(form.get("links_json", "[]"))
    except Exception:
        links = []
    payload = {
        parent_key: parent_id,
        "slug": form.get("slug", ""),
        "title": form.get("title", ""),
        "links": links,
    }
    if doc_type == "admit-cards":
        payload["exam_start"] = form.get("exam_start") or None
        payload["exam_end"] = form.get("exam_end") or None
    else:
        payload["start_date"] = form.get("start_date") or None
        payload["end_date"] = form.get("end_date") or None
    payload["published_at"] = form.get("published_at") or None
    current_app.api_client.post(api_url, token=token, json=payload)
    flash(_DOC_FLASH.get(doc_type, "Document added."), "success")
    return redirect(back_url)


bp = Blueprint("admin", __name__)

_CSRF_EXEMPT = {"/health", "/logout"}



def _get_csrf_token():
    """Return a persistent per-session CSRF token, creating one if absent."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


@bp.app_context_processor
def inject_csrf():
    return {"csrf_token": _get_csrf_token()}


@bp.before_app_request
def validate_csrf():
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    if request.path in _CSRF_EXEMPT:
        return
    form_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
    if not form_token or form_token != session.get("csrf_token"):
        flash("Invalid or expired form submission. Please try again.", "error")
        return redirect(_URL_LOGIN)


def _try_refresh():
    """Refresh admin access token using stored refresh token. Updates session. Returns new token or None."""
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        session.clear()
        return None
    r = current_app.api_client.post("/auth/admin/refresh", json={"refresh_token": refresh_token})
    if not r.ok:
        session.clear()
        return None
    data = r.json()
    session["token"] = data.get("access_token")
    session["refresh_token"] = data.get("refresh_token", refresh_token)
    return session["token"]


# --- Health ---


@bp.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "hermes-frontend-admin"}


# --- Auth ---


@bp.route(_URL_LOGIN, methods=["GET", "POST"])  # NOSONAR
def login():
    if request.method == "GET":
        return render_template("auth/login.html", csrf_token=_get_csrf_token())

    # CSRF validated by the global before_app_request guard.

    email = request.form.get("email", "")
    password = request.form.get("password", "")
    resp = current_app.api_client.post("/auth/admin/login", json={"email": email, "password": password})
    if resp.ok:
        data = resp.json()
        session["token"] = data.get("access_token")
        session["refresh_token"] = data.get("refresh_token")
        # Decode role from JWT payload (avoids an extra API call)
        payload = _jwt_payload(session["token"])
        session["admin_name"] = email
        session["admin_role"] = payload.get("role", "operator")
        if request.form.get("remember"):
            session.permanent = True
            current_app.permanent_session_lifetime = timedelta(days=30)
        return redirect("/")
    flash("Invalid credentials", "error")
    return redirect(_URL_LOGIN)


@bp.route("/logout", methods=["GET"])
def logout():
    token = session.get("token")
    if token:
        current_app.api_client.post("/auth/admin/logout", token=token)
    session.clear()
    return redirect(_URL_LOGIN)


# --- Dashboard ---


@bp.route("/", methods=["GET"])
def index():
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    stats_resp = current_app.api_client.get("/admin/stats", token=token)
    if stats_resp.status_code == 401:
        token = _try_refresh()
        if not token:
            return redirect(_URL_LOGIN)
        stats_resp = current_app.api_client.get("/admin/stats", token=token)
    stats = stats_resp.json() if stats_resp.ok else {}

    return render_template("auth/dashboard.html", stats=stats)


# --- Job Management ---


@bp.route("/jobs", methods=["GET"])
def jobs():
    """Manage job vacancies."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    params = {"limit": 20, "offset": 0}
    resp = current_app.api_client.get(_API_ADMIN_JOBS, token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template(
        "jobs/jobs_manage.html",
        jobs=data["data"],
        pagination=data.get("pagination", {}),
    )


@bp.route("/jobs/list", methods=["GET"])
def jobs_list_partial():
    """HTMX partial — job table rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401

    params = {"limit": 20, "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get(_API_ADMIN_JOBS, token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template("jobs/_job_rows.html", jobs=data["data"], pagination=data.get("pagination", {}))


@bp.route("/jobs/new", methods=["GET", "POST"])  # NOSONAR
def new_job():
    """Create a job vacancy."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    orgs_resp = current_app.api_client.get(_API_ADMIN_ORGANIZATIONS, token=token, params={"limit": 200})
    organizations = orgs_resp.json().get("data", []) if orgs_resp.ok else []

    if request.method == "POST":
        import json as _json
        form = request.form.to_dict()
        payload = {}
        _pick_text_fields(form, ["job_title", "slug", "organization", "department",
                                  "qualification_level", "employment_type",
                                  "description", "short_description", "source_url"], payload)
        if form.get("organization_id"):
            payload["organization_id"] = form["organization_id"]
        _pick_int_fields(form, ["total_vacancies", "salary_initial", "salary_max"], payload)
        fee = {k: int(v) for k, v in {
            "general": form.get("fee_general", ""),
            "obc": form.get("fee_obc", ""),
            "sc_st": form.get("fee_sc_st", ""),
            "ews": form.get("fee_ews", ""),
            "female": form.get("fee_female", ""),
        }.items() if v.strip() != ""}
        payload["fee"] = fee
        _pick_date_fields(form, ["notification_date", "application_start", "application_end",
                                  "exam_start", "exam_end", "result_date"], payload)
        payload["status"] = form.get("status", "active")
        posts_raw = form.get("posts_json", "").strip()
        zones_raw = form.get("zonewise_json", "").strip()
        links_raw = form.get("links_json", "").strip()
        tv_raw = form.get("total_vacancy_json", "").strip()
        try:
            vacancy = {}
            if posts_raw:
                vacancy["posts"] = _json.loads(posts_raw)
            if zones_raw:
                parsed_zones = _json.loads(zones_raw)
                if parsed_zones:
                    vacancy["zonewise_vacancy"] = parsed_zones
            if tv_raw:
                parsed_tv = _json.loads(tv_raw)
                if any(v is not None for v in parsed_tv.values()):
                    vacancy["total_vacancy"] = parsed_tv
            if vacancy:
                payload["vacancy_breakdown"] = vacancy
            if links_raw:
                parsed_links = _json.loads(links_raw)
                if parsed_links:
                    payload["application_details"] = {"important_links": parsed_links}
        except ValueError:
            flash("Invalid form data. Please try again.", "error")
            return render_template("jobs/job_create.html", organizations=organizations)
        resp = current_app.api_client.post(_API_ADMIN_JOBS, token=token, json=payload)
        if resp.ok:
            job_id = resp.json().get("id")
            flash("Job created successfully.", "success")
            return redirect(f"/jobs/{job_id}/edit")
        detail = resp.json().get("detail", "Failed to create job") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create job"
        flash(detail, "error")
        return render_template("jobs/job_create.html", organizations=organizations)

    return render_template("jobs/job_create.html", organizations=organizations)


@bp.route("/jobs/<job_id>/delete", methods=["POST"])
def delete_job(job_id):
    """Hard-delete a job (admin role only)."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/jobs/{job_id}", token=token)
    flash("Job deleted.", "success")
    return redirect(_URL_JOBS)


# --- Job Edit ---


@bp.route("/jobs/<job_id>/edit", methods=["GET", "POST"])  # NOSONAR
def edit_job(job_id):
    """Edit an existing job."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    if request.method == "POST":
        form = request.form.to_dict()
        update = {}
        _pick_text_fields(form, ["job_title", "slug", "organization", "department",
                                  "qualification_level", "description",
                                  "short_description", "source_url", "status"], update)
        if form.get("organization_id"):
            update["organization_id"] = form["organization_id"]
        _pick_int_fields(form, ["total_vacancies", "salary_initial", "salary_max"], update)
        fee = {k: int(v) for k, v in {
            "general": form.get("fee_general", ""),
            "obc": form.get("fee_obc", ""),
            "sc_st": form.get("fee_sc_st", ""),
            "ews": form.get("fee_ews", ""),
            "female": form.get("fee_female", ""),
        }.items() if v.strip() != ""}
        update["fee"] = fee
        _pick_date_fields(form, ["notification_date", "application_start",
                                  "application_end", "exam_start",
                                  "exam_end", "result_date"], update)
        import json as _json
        posts_raw = form.get("posts_json", "").strip()
        zones_raw = form.get("zonewise_json", "").strip()
        tv_raw = form.get("total_vacancy_json", "").strip()
        links_raw = form.get("links_json", "").strip()
        try:
            vacancy = {}
            if posts_raw:
                vacancy["posts"] = _json.loads(posts_raw)
            if zones_raw:
                parsed_zones = _json.loads(zones_raw)
                if parsed_zones:
                    vacancy["zonewise_vacancy"] = parsed_zones
            if tv_raw:
                parsed_tv = _json.loads(tv_raw)
                if any(v is not None for v in parsed_tv.values()):
                    vacancy["total_vacancy"] = parsed_tv
            if vacancy:
                update["vacancy_breakdown"] = vacancy
            if links_raw:
                parsed_links = _json.loads(links_raw)
                if parsed_links:
                    update["application_details"] = {"important_links": parsed_links}
        except ValueError:
            flash("Invalid form data. Please try again.", "error")
            return redirect(f"/jobs/{job_id}/edit")
        if update:
            current_app.api_client.put(f"/admin/jobs/{job_id}", token=token, json=update)
        flash("Job saved.", "success")
        return redirect(f"/jobs/{job_id}/edit")

    resp = current_app.api_client.get(f"/admin/jobs/{job_id}", token=token)
    if not resp.ok:
        flash("Job not found.", "error")
        return redirect(_URL_JOBS)
    job = resp.json()

    ac_resp = current_app.api_client.get(
        f"{_API_ADMIN_ADMIT_CARDS}?job_id={job_id}&limit=100", token=token
    )
    ak_resp = current_app.api_client.get(
        f"{_API_ADMIN_ANSWER_KEYS}?job_id={job_id}&limit=100", token=token
    )
    re_resp = current_app.api_client.get(
        f"{_API_ADMIN_RESULTS}?job_id={job_id}&limit=100", token=token
    )

    orgs_resp = current_app.api_client.get(_API_ADMIN_ORGANIZATIONS, token=token, params={"limit": 200})
    organizations = orgs_resp.json().get("data", []) if orgs_resp.ok else []

    return render_template(
        "jobs/job_edit.html",
        job=job,
        organizations=organizations,
        admit_cards=ac_resp.json().get("data", []) if ac_resp.ok else [],
        answer_keys=ak_resp.json().get("data", []) if ak_resp.ok else [],
        results=re_resp.json().get("data", []) if re_resp.ok else [],
    )


@bp.route("/jobs/<job_id>/docs/<doc_type>", methods=["POST"])
def job_add_doc(job_id, doc_type):
    return _add_doc("job_id", job_id, doc_type)


@bp.route("/jobs/<job_id>/docs/<doc_type>/<doc_id>/delete", methods=["POST"])
def job_delete_doc(job_id, doc_type, doc_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/{doc_type}/{doc_id}", token=token)
    flash("Document deleted.", "success")
    return redirect(f"/jobs/{job_id}/edit#docs")


# --- User Management ---


@bp.route(_URL_USERS, methods=["GET"])
def users():
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    resp = current_app.api_client.get("/admin/users", token=token, params={"limit": 20, "offset": 0})
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template(
        "users/users.html",
        users=data["data"],
        pagination=data.get("pagination", {}),
    )


@bp.route("/users/list", methods=["GET"])
def users_list_partial():
    """HTMX partial — user table rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401

    resp = current_app.api_client.get("/admin/users", token=token, params={"limit": 20, "offset": _int_arg("offset", 0)})
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template("users/_user_rows.html", users=data["data"], pagination=data.get("pagination", {}))


@bp.route("/users/<user_id>", methods=["GET"])
def user_detail(user_id):
    """User detail view."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    resp = current_app.api_client.get(f"/admin/users/{user_id}", token=token)
    if not resp.ok:
        flash("User not found.", "error")
        return redirect(_URL_USERS)
    user = resp.json()
    return render_template("users/user_detail.html", user=user)


@bp.route("/users/<user_id>/suspend", methods=["POST"])
def toggle_user_status(user_id):
    """Suspend or activate a user."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    new_status = request.form.get("status", "suspended")
    current_app.api_client.put(f"/admin/users/{user_id}/status", token=token, json={"status": new_status})
    return redirect(_URL_USERS)


@bp.route("/users/<user_id>/delete", methods=["POST"])
def delete_user_permanently(user_id):
    """Permanently delete a user from both PostgreSQL and Firebase."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    resp = current_app.api_client.delete(f"/admin/users/{user_id}", token=token)
    if resp.ok:
        flash("User permanently deleted.", "success")
    else:
        flash("Failed to delete user.", "error")
    return redirect(_URL_USERS)


# --- Admission Management ---


@bp.route("/admissions", methods=["GET"])
def admissions():
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    params = {"limit": 20, "offset": 0}
    resp = current_app.api_client.get(_API_ADMIN_ADMISSIONS, token=token, params=params)
    if resp.status_code == 401:
        token = _try_refresh()
        if not token:
            return redirect(_URL_LOGIN)
        resp = current_app.api_client.get(_API_ADMIN_ADMISSIONS, token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    return render_template("admissions/admissions.html", admissions=data["data"], pagination=data.get("pagination", {}))


@bp.route("/admissions/list", methods=["GET"])
def admissions_list_partial():
    """HTMX partial — admission table rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401
    params = {"limit": 20, "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get(_API_ADMIN_ADMISSIONS, token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    return render_template("admissions/_admission_rows.html", admissions=data["data"], pagination=data.get("pagination", {}))


@bp.route("/admissions/new", methods=["GET", "POST"])  # NOSONAR
def new_admission():
    """Create a new admission."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    if request.method == "POST":
        form = request.form.to_dict()
        payload = {}
        _set_or_none(form, ["admission_name", "slug", "conducting_body", "counselling_body", "admission_type",
                             "stream", "description", "short_description", "source_url", "status"], payload)
        fee = {k: int(v) for k, v in {
            "general": form.get("fee_general", ""),
            "obc": form.get("fee_obc", ""),
            "sc_st": form.get("fee_sc_st", ""),
            "ews": form.get("fee_ews", ""),
            "female": form.get("fee_female", ""),
        }.items() if v.strip() != ""}
        payload["fee"] = fee
        _set_optional(form, ["application_start", "application_end", "admission_date",
                              "exam_start", "exam_end",
                              "result_date", "counselling_start"], payload)
        import json as _json
        for json_field, key in [("admission_details_json", "admission_details"),
                                  ("eligibility_json", "eligibility"),
                                  ("seats_info_json", "seats_info"),
                                  ("selection_process_json", "selection_process")]:
            raw = form.get(json_field, "").strip()
            if raw:
                try:
                    payload[key] = _json.loads(raw)
                except Exception:
                    pass
        if form.get("organization_id"):
            payload["organization_id"] = form["organization_id"]
        payload.setdefault("status", "active")
        resp = current_app.api_client.post(_API_ADMIN_ADMISSIONS, token=token, json=payload)
        if resp.ok:
            admission_id = resp.json().get("id")
            flash("Admission created.", "success")
            return redirect(f"/admissions/{admission_id}/edit")
        detail = resp.json().get("detail", "Failed to create admission") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create admission"
        flash(detail, "error")
    orgs_resp = current_app.api_client.get(_API_ADMIN_ORGANIZATIONS, token=token, params={"limit": 200})
    organizations = orgs_resp.json().get("data", []) if orgs_resp.ok else []
    return render_template("admissions/admission_create.html", organizations=organizations)


@bp.route("/admissions/<admission_id>/edit", methods=["GET", "POST"])  # NOSONAR
def edit_admission(admission_id):
    """Edit an existing admission."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    if request.method == "POST":
        form = request.form.to_dict()
        update = {}
        _pick_text_fields(form, ["admission_name", "slug", "conducting_body", "counselling_body", "admission_type",
                                  "stream", "description", "short_description", "source_url", "status"], update)
        fee = {k: int(v) for k, v in {
            "general": form.get("fee_general", ""),
            "obc": form.get("fee_obc", ""),
            "sc_st": form.get("fee_sc_st", ""),
            "ews": form.get("fee_ews", ""),
            "female": form.get("fee_female", ""),
        }.items() if v.strip() != ""}
        update["fee"] = fee
        _set_optional(form, ["application_start", "application_end", "admission_date",
                              "exam_start", "exam_end",
                              "result_date", "counselling_start"], update)
        if form.get("organization_id"):
            update["organization_id"] = form["organization_id"]
        import json as _json
        for json_field, key in [("admission_details_json", "admission_details"),
                                  ("eligibility_json", "eligibility"),
                                  ("seats_info_json", "seats_info"),
                                  ("selection_process_json", "selection_process")]:
            raw = form.get(json_field, "").strip()
            if raw:
                try:
                    update[key] = _json.loads(raw)
                except Exception:
                    pass
        resp = current_app.api_client.put(f"/admin/admissions/{admission_id}", token=token, json=update)
        if resp.ok:
            flash("Admission updated.", "success")
        else:
            flash("Failed to update admission.", "error")
        return redirect(f"/admissions/{admission_id}/edit")

    resp_detail_req = current_app.api_client.get(f"/admin/admissions/{admission_id}", token=token)
    if not resp_detail_req.ok:
        flash("Admission not found.", "error")
        return redirect(_URL_ADMISSIONS)
    resp_detail = resp_detail_req.json()

    ac_resp = current_app.api_client.get(
        f"{_API_ADMIN_ADMIT_CARDS}?admission_id={admission_id}&limit=100", token=token
    )
    ak_resp = current_app.api_client.get(
        f"{_API_ADMIN_ANSWER_KEYS}?admission_id={admission_id}&limit=100", token=token
    )
    re_resp = current_app.api_client.get(
        f"{_API_ADMIN_RESULTS}?admission_id={admission_id}&limit=100", token=token
    )

    orgs_resp = current_app.api_client.get(_API_ADMIN_ORGANIZATIONS, token=token, params={"limit": 200})
    organizations = orgs_resp.json().get("data", []) if orgs_resp.ok else []

    return render_template(
        "admissions/admission_edit.html",
        admission=resp_detail,
        organizations=organizations,
        admit_cards=ac_resp.json().get("data", []) if ac_resp.ok else [],
        answer_keys=ak_resp.json().get("data", []) if ak_resp.ok else [],
        results=re_resp.json().get("data", []) if re_resp.ok else [],
    )


@bp.route("/admissions/<admission_id>/delete", methods=["POST"])
def delete_admission(admission_id):
    """Delete an admission (admin only)."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/admissions/{admission_id}", token=token)
    flash("Admission deleted.", "success")
    return redirect(_URL_ADMISSIONS)


# Per-admission phase document management


@bp.route("/admissions/<admission_id>/docs/<doc_type>", methods=["POST"])
def admission_add_doc(admission_id, doc_type):
    return _add_doc("admission_id", admission_id, doc_type)


@bp.route("/admissions/<admission_id>/docs/<doc_type>/<doc_id>/delete", methods=["POST"])
def admission_delete_doc(admission_id, doc_type, doc_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/{doc_type}/{doc_id}", token=token)
    flash("Document deleted.", "success")
    return redirect(f"/admissions/{admission_id}/edit#docs")


# --- Organization Management ---


@bp.route(_URL_ORGANIZATIONS, methods=["GET"])
def organizations():
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    resp = current_app.api_client.get(_API_ADMIN_ORGANIZATIONS, token=token, params={"limit": 200})
    data = resp.json() if resp.ok else {"data": [], "total": 0}
    return render_template("organizations/organizations.html", organizations=data["data"], total=data.get("total", 0))


@bp.route("/organizations/new", methods=["GET", "POST"])  # NOSONAR
def new_organization():
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    if request.method == "POST":
        form = request.form.to_dict()
        payload = {
            "name": form.get("name", "").strip(),
            "slug": form.get("slug", "").strip() or None,
            "org_type": form.get("org_type", "both").strip() or "both",
            "short_name": form.get("short_name", "").strip() or None,
            "logo_url": form.get("logo_url", "").strip() or None,
            "website_url": form.get("website_url", "").strip() or None,
        }
        resp = current_app.api_client.post(_API_ADMIN_ORGANIZATIONS, token=token, json=payload)
        if resp.ok:
            flash("Organization created.", "success")
            return redirect(_URL_ORGANIZATIONS)
        detail = resp.json().get("detail", "Failed to create organization") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create organization"
        flash(detail, "error")
    return render_template("organizations/org_create.html")


@bp.route("/organizations/<org_id>/edit", methods=["GET", "POST"])  # NOSONAR
def edit_organization(org_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    if request.method == "POST":
        form = request.form.to_dict()
        payload = {
            "name": form.get("name", "").strip(),
            "slug": form.get("slug", "").strip() or None,
            "org_type": form.get("org_type", "both").strip() or "both",
            "short_name": form.get("short_name", "").strip() or None,
            "logo_url": form.get("logo_url", "").strip() or None,
            "website_url": form.get("website_url", "").strip() or None,
        }
        resp = current_app.api_client.put(f"/admin/organizations/{org_id}", token=token, json=payload)
        if resp.ok:
            flash("Organization updated.", "success")
        else:
            detail = resp.json().get("detail", "Failed to update") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to update"
            flash(detail, "error")
        return redirect(f"/organizations/{org_id}/edit")
    resp = current_app.api_client.get(f"/admin/organizations/{org_id}", token=token)
    if not resp.ok:
        flash("Organization not found.", "error")
        return redirect(_URL_ORGANIZATIONS)
    org = resp.json()
    return render_template("organizations/org_edit.html", org=org)


@bp.route("/organizations/<org_id>/delete", methods=["POST"])
def delete_organization(org_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/organizations/{org_id}", token=token)
    flash("Organization deleted.", "success")
    return redirect(_URL_ORGANIZATIONS)


# --- Audit Logs ---


@bp.route("/logs", methods=["GET"])
def logs():
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    params = {"limit": 20, "offset": 0}
    resp = current_app.api_client.get("/admin/logs", token=token, params=params)
    if resp.status_code == 403:
        flash("Audit logs are only accessible to admin accounts.", "error")
        return redirect("/")
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template("audit_logs/logs.html", logs=data["data"], pagination=data.get("pagination", {}))


@bp.route("/logs/list", methods=["GET"])
def logs_list_partial():
    """HTMX partial — log rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401

    params = {"limit": 20, "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get("/admin/logs", token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template("audit_logs/_log_rows.html", logs=data["data"], pagination=data.get("pagination", {}))


def _handle_unexpected_error(exc):
    current_app.logger.error("Unhandled exception: %s", exc, exc_info=True)
    return render_template("shared/500.html"), 500


_DEFAULT_SECRET_KEY = "admin-dev-secret-key"  # pragma: allowlist secret


def create_app():
    app = Flask(__name__)  # NOSONAR
    app.secret_key = os.environ.get("SECRET_KEY", _DEFAULT_SECRET_KEY)
    if os.environ.get("FLASK_ENV") == "production" and app.secret_key == _DEFAULT_SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set to a secure value in production.")
    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://backend:8000/api/v1")  # NOSONAR
    )
    app.register_blueprint(bp)
    app.register_error_handler(Exception, _handle_unexpected_error)
    return app


# Flask CLI entry point
app = create_app()
