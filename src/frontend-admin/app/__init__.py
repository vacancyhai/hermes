"""Hermes Admin Frontend — Flask + Jinja2 + HTMX.

Routes:
  /health                         — Health check
  /                               — Dashboard (stats, quick links)
  /login                          — Admin login
  /logout                         — Clear session
  /jobs                           — Job management (list)
  /jobs/new                       — Create job with optional PDF extract
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
  /admissions/<id>/docs/...   — POST: add/delete docs on exam
  /users                          — User management (list, search, status filter)
  /users/<id>                     — User detail
  /users/<id>/suspend             — Toggle user suspend/activate
  /users/<id>/delete              — Permanently delete user
  /logs                           — Admin audit log viewer
"""

import base64
import json
import os
import secrets

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
_API_ADMIN_JOBS = "/admin/jobs"
_API_ADMIN_ADMIT_CARDS = "/admin/admit-cards"
_API_ADMIN_ANSWER_KEYS = "/admin/answer-keys"
_API_ADMIN_RESULTS = "/admin/results"
_CONTENT_TYPE_JSON = "application/json"
_URL_USERS = "/users"
_API_ADMIN_ADMISSIONS = "/admin/admissions"


bp = Blueprint("admin", __name__)


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
        csrf_token = secrets.token_hex(16)
        session["csrf_token"] = csrf_token
        return render_template("auth/login.html", csrf_token=csrf_token)

    # Validate CSRF token
    form_csrf = request.form.get("csrf_token", "")
    if not form_csrf or form_csrf != session.pop("csrf_token", None):
        flash("Invalid request. Please try again.", "error")
        return redirect(_URL_LOGIN)

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



@bp.route("/api/extract-pdf", methods=["POST"])
def extract_pdf():
    """Proxy endpoint for PDF extraction - uploads file to backend API and returns extracted data."""
    token = session.get("token")
    if not token:
        return {"error": "Not authenticated"}, 401

    if "file" not in request.files:
        return {"error": "No file provided"}, 400

    file = request.files["file"]

    # Forward to backend API
    resp = current_app.api_client.post_file(
        "/admin/jobs/extract-pdf",
        token=token,
        files={"file": (file.filename, file.stream, file.content_type)}
    )

    if resp.ok:
        return resp.json(), 200
    else:
        error_data = resp.json() if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else {"detail": "Extraction failed"}
        return error_data, resp.status_code


@bp.route("/jobs/new", methods=["GET", "POST"])  # NOSONAR
def new_job():
    """Create a job vacancy."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    if request.method == "POST":
        import json as _json
        form = request.form.to_dict()
        payload = {}
        _pick_text_fields(form, ["job_title", "organization", "department",
                                  "qualification_level", "employment_type",
                                  "description", "short_description", "source_url"], payload)
        _pick_int_fields(form, ["total_vacancies", "fee_general", "fee_obc", "fee_sc_st",
                                 "fee_ews", "fee_female", "salary_initial", "salary_max"], payload)
        _pick_date_fields(form, ["notification_date", "application_start", "application_end",
                                  "exam_start", "exam_end", "result_date"], payload)
        payload["status"] = form.get("status", "draft")
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
            return render_template("jobs/job_create.html")
        resp = current_app.api_client.post(_API_ADMIN_JOBS, token=token, json=payload)
        if resp.ok:
            job_id = resp.json().get("id")
            flash("Job created successfully.", "success")
            return redirect(f"/jobs/{job_id}/edit")
        detail = resp.json().get("detail", "Failed to create job") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create job"
        flash(detail, "error")
        return render_template("jobs/job_create.html")

    return render_template("jobs/job_create.html")


@bp.route("/jobs/<job_id>/delete", methods=["POST"])
def delete_job(job_id):
    """Soft-delete a job (admin role only)."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/jobs/{job_id}", token=token)
    flash("Job deleted.", "success")
    return redirect("/jobs")


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
        _pick_text_fields(form, ["job_title", "organization", "department",
                                  "qualification_level", "description",
                                  "short_description", "source_url", "status"], update)
        _pick_int_fields(form, ["total_vacancies", "fee_general", "fee_obc", "fee_sc_st",
                                 "fee_ews", "fee_female", "salary_initial", "salary_max"], update)
        _pick_date_fields(form, ["notification_date", "application_start",
                                  "application_end", "exam_start",
                                  "exam_end", "result_date"], update)
        import json as _json
        posts_raw = form.get("posts_json", "").strip()
        if posts_raw:
            try:
                update["selection_process"] = _json.loads(posts_raw)
            except ValueError:
                pass
        links_raw = form.get("links_json", "").strip()
        if links_raw:
            try:
                update["documents"] = _json.loads(links_raw)
            except ValueError:
                pass
        tv_raw = form.get("total_vacancy_json", "").strip()
        if tv_raw:
            try:
                update["vacancy_breakdown"] = _json.loads(tv_raw)
            except ValueError:
                pass
        zones_raw = form.get("zonewise_json", "").strip()
        if zones_raw:
            try:
                parsed_zones = _json.loads(zones_raw)
                existing_details = update.get("exam_details") or {}
                existing_details["zonewise_vacancy"] = parsed_zones
                update["exam_details"] = existing_details
            except ValueError:
                pass
        if update:
            current_app.api_client.put(f"/admin/jobs/{job_id}", token=token, json=update)
        flash("Job saved.", "success")
        return redirect(f"/jobs/{job_id}/edit")

    resp = current_app.api_client.get(f"/admin/jobs/{job_id}", token=token)
    if not resp.ok:
        flash("Job not found.", "error")
        return redirect("/jobs")
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

    return render_template(
        "jobs/job_edit.html",
        job=job,
        admit_cards=ac_resp.json().get("data", []) if ac_resp.ok else [],
        answer_keys=ak_resp.json().get("data", []) if ak_resp.ok else [],
        results=re_resp.json().get("data", []) if re_resp.ok else [],
    )


@bp.route("/jobs/<job_id>/docs/admit-cards", methods=["POST"])
def job_add_admit_card(job_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    form = request.form.to_dict()
    payload = {
        "job_id": job_id,
        "title": form.get("title", ""),
        "download_url": form.get("download_url", ""),
        "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
        "valid_from": form.get("valid_from") or None,
        "valid_until": form.get("valid_until") or None,
        "notes": form.get("notes") or None,
    }
    current_app.api_client.post(_API_ADMIN_ADMIT_CARDS, token=token, json=payload)
    flash("Admit card added.", "success")
    return redirect(f"/jobs/{job_id}/edit#docs")


@bp.route("/jobs/<job_id>/docs/answer-keys", methods=["POST"])
def job_add_answer_key(job_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    form = request.form.to_dict()
    try:
        files = json.loads(form.get("files_json", "[]"))
    except Exception:
        files = []
    payload = {
        "job_id": job_id,
        "title": form.get("title", ""),
        "answer_key_type": form.get("answer_key_type", "provisional"),
        "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
        "files": files,
        "objection_url": form.get("objection_url") or None,
        "objection_deadline": form.get("objection_deadline") or None,
    }
    current_app.api_client.post(_API_ADMIN_ANSWER_KEYS, token=token, json=payload)
    flash("Answer key added.", "success")
    return redirect(f"/jobs/{job_id}/edit#docs")


@bp.route("/jobs/<job_id>/docs/results", methods=["POST"])
def job_add_result(job_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    form = request.form.to_dict()
    payload = {
        "job_id": job_id,
        "title": form.get("title", ""),
        "result_type": form.get("result_type", "merit_list"),
        "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
        "download_url": form.get("download_url") or None,
        "total_qualified": int(form["total_qualified"]) if form.get("total_qualified") else None,
        "notes": form.get("notes") or None,
    }
    current_app.api_client.post(_API_ADMIN_RESULTS, token=token, json=payload)
    flash("Result added.", "success")
    return redirect(f"/jobs/{job_id}/edit#docs")


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
    return render_template("admissions/admissions.html", exams=data["data"], pagination=data.get("pagination", {}))


@bp.route("/admissions/list", methods=["GET"])
def admissions_list_partial():
    """HTMX partial — exam table rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401
    params = {"limit": 20, "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get(_API_ADMIN_ADMISSIONS, token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    return render_template("admissions/_admission_rows.html", exams=data["data"], pagination=data.get("pagination", {}))


@bp.route("/admissions/new", methods=["GET", "POST"])  # NOSONAR
def new_admission():
    """Create a new admission."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    if request.method == "POST":
        form = request.form.to_dict()
        payload = {}
        _set_or_none(form, ["exam_name", "conducting_body", "counselling_body", "exam_type",
                             "stream", "description", "short_description", "source_url", "status"], payload)
        _set_int_fields(form, ["fee_general", "fee_obc", "fee_sc_st", "fee_ews", "fee_female"], payload)
        _set_optional(form, ["application_start", "application_end", "exam_date",
                              "result_date", "counselling_start"], payload)
        import json as _json
        for json_field, key in [("exam_details_json", "exam_details"),
                                  ("eligibility_json", "eligibility"),
                                  ("seats_info_json", "seats_info"),
                                  ("selection_process_json", "selection_process")]:
            raw = form.get(json_field, "").strip()
            if raw:
                try:
                    payload[key] = _json.loads(raw)
                except Exception:
                    pass
        payload.setdefault("status", "active")
        resp = current_app.api_client.post(_API_ADMIN_ADMISSIONS, token=token, json=payload)
        if resp.ok:
            exam_id = resp.json().get("id")
            flash("Admission created.", "success")
            return redirect(f"/admissions/{exam_id}/edit")
        detail = resp.json().get("detail", "Failed to create exam") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create exam"
        flash(detail, "error")
    return render_template("admissions/admission_create.html")


@bp.route("/admissions/<exam_id>/edit", methods=["GET", "POST"])  # NOSONAR
def edit_admission(exam_id):
    """Edit an existing admission."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    if request.method == "POST":
        form = request.form.to_dict()
        update = {}
        _pick_text_fields(form, ["exam_name", "conducting_body", "counselling_body", "exam_type",
                                  "stream", "description", "short_description", "source_url", "status"], update)
        _set_int_fields(form, ["fee_general", "fee_obc", "fee_sc_st", "fee_ews", "fee_female"], update)
        _set_optional(form, ["application_start", "application_end", "exam_date",
                              "result_date", "counselling_start"], update)
        import json as _json
        for json_field, key in [("exam_details_json", "exam_details"),
                                  ("eligibility_json", "eligibility"),
                                  ("seats_info_json", "seats_info"),
                                  ("selection_process_json", "selection_process")]:
            raw = form.get(json_field, "").strip()
            if raw:
                try:
                    update[key] = _json.loads(raw)
                except Exception:
                    pass
        resp = current_app.api_client.put(f"/admin/admissions/{exam_id}", token=token, json=update)
        if resp.ok:
            flash("Admission updated.", "success")
        else:
            flash("Failed to update admission.", "error")
        return redirect(f"/admissions/{exam_id}/edit")

    resp_detail_req = current_app.api_client.get(f"/admin/admissions/{exam_id}", token=token)
    if not resp_detail_req.ok:
        flash("Admission not found.", "error")
        return redirect("/admissions")
    resp_detail = resp_detail_req.json()

    ac_resp = current_app.api_client.get(
        f"{_API_ADMIN_ADMIT_CARDS}?exam_id={exam_id}&limit=100", token=token
    )
    ak_resp = current_app.api_client.get(
        f"{_API_ADMIN_ANSWER_KEYS}?exam_id={exam_id}&limit=100", token=token
    )
    re_resp = current_app.api_client.get(
        f"{_API_ADMIN_RESULTS}?exam_id={exam_id}&limit=100", token=token
    )

    return render_template(
        "admissions/admission_edit.html",
        exam=resp_detail,
        admit_cards=ac_resp.json().get("data", []) if ac_resp.ok else [],
        answer_keys=ak_resp.json().get("data", []) if ak_resp.ok else [],
        results=re_resp.json().get("data", []) if re_resp.ok else [],
    )


@bp.route("/admissions/<exam_id>/delete", methods=["POST"])
def delete_admission(exam_id):
    """Delete an admission (admin only)."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/admissions/{exam_id}", token=token)
    flash("Admission deleted.", "success")
    return redirect("/admissions")


# Per-exam phase document management


@bp.route("/admissions/<exam_id>/docs/admit-cards", methods=["POST"])
def admission_add_admit_card(exam_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    form = request.form.to_dict()
    payload = {
        "exam_id": exam_id,
        "title": form.get("title", ""),
        "download_url": form.get("download_url", ""),
        "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
        "valid_from": form.get("valid_from") or None,
        "valid_until": form.get("valid_until") or None,
        "notes": form.get("notes") or None,
    }
    current_app.api_client.post(_API_ADMIN_ADMIT_CARDS, token=token, json=payload)
    flash("Admit card added.", "success")
    return redirect(f"/admissions/{exam_id}/edit#docs")


@bp.route("/admissions/<exam_id>/docs/answer-keys", methods=["POST"])
def admission_add_answer_key(exam_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    form = request.form.to_dict()
    try:
        files = json.loads(form.get("files_json", "[]"))
    except Exception:
        files = []
    payload = {
        "exam_id": exam_id,
        "title": form.get("title", ""),
        "answer_key_type": form.get("answer_key_type", "provisional"),
        "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
        "files": files,
        "objection_url": form.get("objection_url") or None,
        "objection_deadline": form.get("objection_deadline") or None,
    }
    current_app.api_client.post(_API_ADMIN_ANSWER_KEYS, token=token, json=payload)
    flash("Answer key added.", "success")
    return redirect(f"/admissions/{exam_id}/edit#docs")


@bp.route("/admissions/<exam_id>/docs/results", methods=["POST"])
def admission_add_result(exam_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    form = request.form.to_dict()
    payload = {
        "exam_id": exam_id,
        "title": form.get("title", ""),
        "result_type": form.get("result_type", "merit_list"),
        "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
        "download_url": form.get("download_url") or None,
        "total_qualified": int(form["total_qualified"]) if form.get("total_qualified") else None,
        "notes": form.get("notes") or None,
    }
    current_app.api_client.post(_API_ADMIN_RESULTS, token=token, json=payload)
    flash("Result added.", "success")
    return redirect(f"/admissions/{exam_id}/edit#docs")


@bp.route("/admissions/<exam_id>/docs/<doc_type>/<doc_id>/delete", methods=["POST"])
def admission_delete_doc(exam_id, doc_type, doc_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/{doc_type}/{doc_id}", token=token)
    flash("Document deleted.", "success")
    return redirect(f"/admissions/{exam_id}/edit#docs")


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


def create_app():
    app = Flask(__name__)  # NOSONAR
    app.secret_key = os.environ.get("SECRET_KEY", "admin-dev-secret-key")
    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://backend:8000/api/v1")  # NOSONAR
    )
    app.register_blueprint(bp)
    app.register_error_handler(Exception, _handle_unexpected_error)
    return app


# Flask CLI entry point
app = create_app()
