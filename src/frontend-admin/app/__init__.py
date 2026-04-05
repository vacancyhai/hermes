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
  /admit-cards                    — Admit card management
  /admit-cards/new                — Create admit card
  /answer-keys                    — Answer key management
  /answer-keys/new                — Create answer key
  /results                        — Results management
  /results/new                    — Create result
  /entrance-exams                 — Entrance exam management
  /entrance-exams/new             — Create entrance exam
  /entrance-exams/<id>/edit       — Edit entrance exam
  /entrance-exams/<id>/delete     — POST: delete entrance exam
  /entrance-exams/<id>/docs/...   — POST: add/delete docs on exam
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

from flask import Blueprint, Flask, current_app, flash, redirect, render_template, request, session

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
_URL_ADMIT_CARDS = "/admit-cards"
_URL_ANSWER_KEYS = "/answer-keys"
_URL_RESULTS = "/results"
_URL_USERS = "/users"
_API_ADMIN_ENTRANCE_EXAMS = "/admin/entrance-exams"


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


# --- Health ---


@bp.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "hermes-frontend-admin"}


# --- Auth ---


@bp.route(_URL_LOGIN, methods=["GET", "POST"])
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


@bp.route(_URL_ADMIT_CARDS, methods=["GET"])
def admit_cards():
    """Manage admit cards."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    resp = current_app.api_client.get(_API_ADMIN_ADMIT_CARDS, token=token, params={"limit": 20, "offset": 0})
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template(
        "admit_cards/admitcards_manage.html",
        items=data["data"],
        pagination=data.get("pagination", {}),
    )


@bp.route(_URL_ANSWER_KEYS, methods=["GET"])
def answer_keys():
    """Manage answer keys."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    resp = current_app.api_client.get(_API_ADMIN_ANSWER_KEYS, token=token, params={"limit": 20, "offset": 0})
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template(
        "answer_keys/answerkeys_manage.html",
        items=data["data"],
        pagination=data.get("pagination", {}),
    )


@bp.route(_URL_RESULTS, methods=["GET"])
def results():
    """Manage results."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    resp = current_app.api_client.get(_API_ADMIN_RESULTS, token=token, params={"limit": 20, "offset": 0})
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template(
        "results/results_manage.html",
        items=data["data"],
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


@bp.route("/admit-cards/list", methods=["GET"])
def admit_cards_list_partial():
    """HTMX partial — admit card table rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401

    resp = current_app.api_client.get(_API_ADMIN_ADMIT_CARDS, token=token, params={"limit": 20, "offset": _int_arg("offset", 0)})
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template("admit_cards/_admitcard_rows.html", items=data["data"], pagination=data.get("pagination", {}))


@bp.route("/answer-keys/list", methods=["GET"])
def answer_keys_list_partial():
    """HTMX partial — answer key table rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401

    resp = current_app.api_client.get(_API_ADMIN_ANSWER_KEYS, token=token, params={"limit": 20, "offset": _int_arg("offset", 0)})
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template("answer_keys/_answerkey_rows.html", items=data["data"], pagination=data.get("pagination", {}))


@bp.route("/results/list", methods=["GET"])
def results_list_partial():
    """HTMX partial — result table rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401

    resp = current_app.api_client.get(_API_ADMIN_RESULTS, token=token, params={"limit": 20, "offset": _int_arg("offset", 0)})
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template("results/_result_rows.html", items=data["data"], pagination=data.get("pagination", {}))


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


@bp.route("/jobs/new", methods=["GET", "POST"])
def new_job():
    """Create a job vacancy."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    if request.method == "POST":
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
        payload["is_featured"] = form.get("is_featured") == "true"
        payload["is_urgent"] = form.get("is_urgent") == "true"

        resp = current_app.api_client.post(_API_ADMIN_JOBS, token=token, json=payload)
        if resp.ok:
            job_id = resp.json().get("id")
            flash("Job created successfully.", "success")
            return redirect(f"/jobs/{job_id}/edit")
        detail = resp.json().get("detail", "Failed to create job") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create job"
        flash(detail, "error")
        return render_template("jobs/job_create.html")

    return render_template("jobs/job_create.html")


@bp.route("/admit-cards/new", methods=["GET", "POST"])
def new_admit_card():
    """Create an admit card entry."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    if request.method == "POST":
        form = request.form.to_dict()
        payload = {"title": form.get("title", "").strip()}
        _pick_nonempty(form, ["job_id", "exam_id", "download_url", "notes"], payload)
        _set_optional(form, ["valid_from", "valid_until"], payload)
        phase = form.get("phase_number", "").strip()
        payload["phase_number"] = int(phase) if phase else None

        resp = current_app.api_client.post(_API_ADMIN_ADMIT_CARDS, token=token, json=payload)
        if resp.ok:
            flash("Admit card created successfully.", "success")
            return redirect(_URL_ADMIT_CARDS)
        detail = resp.json().get("detail", "Failed to create admit card") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create admit card"
        flash(detail, "error")
        return render_template("admit_cards/admitcard_create.html")

    return render_template("admit_cards/admitcard_create.html")


@bp.route("/answer-keys/new", methods=["GET", "POST"])
def new_answer_key():
    """Create an answer key entry."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    if request.method == "POST":
        form = request.form.to_dict()
        payload = {
            "title": form.get("title", "").strip(),
            "answer_key_type": form.get("answer_key_type", "provisional"),
        }
        _pick_nonempty(form, ["job_id", "exam_id", "objection_url"], payload)
        objection_deadline = form.get("objection_deadline", "").strip()
        payload["objection_deadline"] = objection_deadline if objection_deadline else None
        phase = form.get("phase_number", "").strip()
        payload["phase_number"] = int(phase) if phase else None

        resp = current_app.api_client.post(_API_ADMIN_ANSWER_KEYS, token=token, json=payload)
        if resp.ok:
            flash("Answer key created successfully.", "success")
            return redirect(_URL_ANSWER_KEYS)
        detail = resp.json().get("detail", "Failed to create answer key") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create answer key"
        flash(detail, "error")
        return render_template("answer_keys/answerkey_create.html")

    return render_template("answer_keys/answerkey_create.html")


@bp.route("/results/new", methods=["GET", "POST"])
def new_result():
    """Create a result entry."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    if request.method == "POST":
        form = request.form.to_dict()
        payload = {
            "title": form.get("title", "").strip(),
            "result_type": form.get("result_type", "merit_list"),
        }
        _pick_nonempty(form, ["job_id", "exam_id", "download_url", "notes"], payload)
        phase = form.get("phase_number", "").strip()
        payload["phase_number"] = int(phase) if phase else None
        total_q = form.get("total_qualified", "").strip()
        payload["total_qualified"] = int(total_q) if total_q else None

        resp = current_app.api_client.post(_API_ADMIN_RESULTS, token=token, json=payload)
        if resp.ok:
            flash("Result created successfully.", "success")
            return redirect(_URL_RESULTS)
        detail = resp.json().get("detail", "Failed to create result") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create result"
        flash(detail, "error")
        return render_template("results/result_create.html")

    return render_template("results/result_create.html")


@bp.route("/admit-cards/<card_id>/edit", methods=["GET", "POST"])
def edit_admit_card(card_id):
    """Edit an existing admit card."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    if request.method == "POST":
        form = request.form.to_dict()
        payload = {}
        _pick_text_fields(form, ["title", "download_url", "notes"], payload)
        _set_optional(form, ["valid_from", "valid_until"], payload)
        phase = form.get("phase_number", "").strip()
        payload["phase_number"] = int(phase) if phase else None
        current_app.api_client.put(f"/admin/admit-cards/{card_id}", token=token, json=payload)
        flash("Admit card updated.", "success")
        return redirect(f"/admit-cards/{card_id}/edit")
    resp = current_app.api_client.get(f"/admit-cards/{card_id}")
    if not resp.ok:
        flash("Admit card not found.", "error")
        return redirect(_URL_ADMIT_CARDS)
    return render_template("admit_cards/admitcard_edit.html", item=resp.json())


@bp.route("/answer-keys/<key_id>/edit", methods=["GET", "POST"])
def edit_answer_key(key_id):
    """Edit an existing answer key."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    if request.method == "POST":
        form = request.form.to_dict()
        payload = {}
        _pick_text_fields(form, ["title", "answer_key_type", "objection_url"], payload)
        objection_deadline = form.get("objection_deadline", "").strip()
        payload["objection_deadline"] = objection_deadline if objection_deadline else None
        phase = form.get("phase_number", "").strip()
        payload["phase_number"] = int(phase) if phase else None
        current_app.api_client.put(f"/admin/answer-keys/{key_id}", token=token, json=payload)
        flash("Answer key updated.", "success")
        return redirect(f"/answer-keys/{key_id}/edit")
    resp = current_app.api_client.get(f"/answer-keys/{key_id}")
    if not resp.ok:
        flash("Answer key not found.", "error")
        return redirect(_URL_ANSWER_KEYS)
    return render_template("answer_keys/answerkey_edit.html", item=resp.json())


@bp.route("/results/<result_id>/edit", methods=["GET", "POST"])
def edit_result(result_id):
    """Edit an existing result."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    if request.method == "POST":
        form = request.form.to_dict()
        payload = {}
        _pick_text_fields(form, ["title", "result_type", "download_url", "notes"], payload)
        phase = form.get("phase_number", "").strip()
        payload["phase_number"] = int(phase) if phase else None
        total_q = form.get("total_qualified", "").strip()
        payload["total_qualified"] = int(total_q) if total_q else None
        current_app.api_client.put(f"/admin/results/{result_id}", token=token, json=payload)
        flash("Result updated.", "success")
        return redirect(f"/results/{result_id}/edit")
    resp = current_app.api_client.get(f"/results/{result_id}")
    if not resp.ok:
        flash("Result not found.", "error")
        return redirect(_URL_RESULTS)
    return render_template("results/result_edit.html", item=resp.json())


@bp.route("/admit-cards/<card_id>/delete", methods=["POST"])
def delete_admit_card(card_id):
    """Delete an admit card."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/admit-cards/{card_id}", token=token)
    flash("Admit card deleted.", "success")
    return redirect(_URL_ADMIT_CARDS)


@bp.route("/answer-keys/<key_id>/delete", methods=["POST"])
def delete_answer_key(key_id):
    """Delete an answer key."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/answer-keys/{key_id}", token=token)
    flash("Answer key deleted.", "success")
    return redirect(_URL_ANSWER_KEYS)


@bp.route("/results/<result_id>/delete", methods=["POST"])
def delete_result(result_id):
    """Delete a result."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/results/{result_id}", token=token)
    flash("Result deleted.", "success")
    return redirect(_URL_RESULTS)


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


@bp.route("/jobs/<job_id>/edit", methods=["GET", "POST"])
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
                                  "application_end", "exam_start"], update)
        update["is_featured"] = form.get("is_featured") == "on"
        update["is_urgent"] = form.get("is_urgent") == "on"
        if update:
            current_app.api_client.put(f"/admin/jobs/{job_id}", token=token, json=update)
        flash("Job saved.", "success")
        return redirect(f"/jobs/{job_id}/edit")

    resp = current_app.api_client.get(f"/admin/jobs/{job_id}", token=token)
    if not resp.ok:
        flash("Job not found.", "error")
        return redirect("/jobs")
    job = resp.json()

    pub = current_app.api_client.get(f"/jobs/{job_id}")
    pub_data = pub.json() if pub.ok else {}

    return render_template(
        "jobs/job_edit.html",
        job=job,
        admit_cards=pub_data.get("admit_cards", []),
        answer_keys=pub_data.get("answer_keys", []),
        results=pub_data.get("results", []),
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


# --- Entrance Exam Management ---


@bp.route("/entrance-exams", methods=["GET"])
def entrance_exams():
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    params = {"limit": 20, "offset": 0}
    resp = current_app.api_client.get(_API_ADMIN_ENTRANCE_EXAMS, token=token, params=params)
    if resp.status_code == 401:
        token = _try_refresh()
        if not token:
            return redirect(_URL_LOGIN)
        resp = current_app.api_client.get(_API_ADMIN_ENTRANCE_EXAMS, token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    return render_template("entrance_exams/entrance_exams.html", exams=data["data"], pagination=data.get("pagination", {}))


@bp.route("/entrance-exams/list", methods=["GET"])
def entrance_exams_list_partial():
    """HTMX partial — exam table rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401
    params = {"limit": 20, "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get(_API_ADMIN_ENTRANCE_EXAMS, token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}
    return render_template("entrance_exams/_exam_rows.html", exams=data["data"], pagination=data.get("pagination", {}))


@bp.route("/entrance-exams/new", methods=["GET", "POST"])
def new_entrance_exam():
    """Create a new entrance exam."""
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
        payload["is_featured"] = form.get("is_featured") == "on"
        payload.setdefault("status", "active")
        resp = current_app.api_client.post(_API_ADMIN_ENTRANCE_EXAMS, token=token, json=payload)
        if resp.ok:
            exam_id = resp.json().get("id")
            flash("Entrance exam created.", "success")
            return redirect(f"/entrance-exams/{exam_id}/edit")
        detail = resp.json().get("detail", "Failed to create exam") if resp.headers.get("content-type", "").startswith(_CONTENT_TYPE_JSON) else "Failed to create exam"
        flash(detail, "error")
    return render_template("entrance_exams/exam_create.html")


@bp.route("/entrance-exams/<exam_id>/edit", methods=["GET", "POST"])
def edit_entrance_exam(exam_id):
    """Edit an existing entrance exam."""
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
        update["is_featured"] = form.get("is_featured") == "on"
        resp = current_app.api_client.put(f"/admin/entrance-exams/{exam_id}", token=token, json=update)
        if resp.ok:
            flash("Exam updated.", "success")
        else:
            flash("Failed to update exam.", "error")
        return redirect(f"/entrance-exams/{exam_id}/edit")

    resp_detail_req = current_app.api_client.get(f"/admin/entrance-exams/{exam_id}", token=token)
    if not resp_detail_req.ok:
        flash("Exam not found.", "error")
        return redirect("/entrance-exams")
    resp_detail = resp_detail_req.json()

    exam_public_resp = current_app.api_client.get(f"/entrance-exams/{exam_id}")
    exam_with_docs = exam_public_resp.json() if exam_public_resp.ok else {}
    admit_cards = exam_with_docs.get("admit_cards", [])
    answer_keys = exam_with_docs.get("answer_keys", [])
    results = exam_with_docs.get("results", [])

    return render_template("entrance_exams/exam_edit.html", exam=resp_detail,
                           admit_cards=admit_cards, answer_keys=answer_keys, results=results)


@bp.route("/entrance-exams/<exam_id>/delete", methods=["POST"])
def delete_entrance_exam(exam_id):
    """Delete an entrance exam (admin only)."""
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/entrance-exams/{exam_id}", token=token)
    flash("Exam deleted.", "success")
    return redirect("/entrance-exams")


# Per-exam phase document management


@bp.route("/entrance-exams/<exam_id>/docs/admit-cards", methods=["POST"])
def entrance_exam_add_admit_card(exam_id):
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
    return redirect(f"/entrance-exams/{exam_id}/edit#docs")


@bp.route("/entrance-exams/<exam_id>/docs/answer-keys", methods=["POST"])
def entrance_exam_add_answer_key(exam_id):
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
    return redirect(f"/entrance-exams/{exam_id}/edit#docs")


@bp.route("/entrance-exams/<exam_id>/docs/results", methods=["POST"])
def entrance_exam_add_result(exam_id):
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
    return redirect(f"/entrance-exams/{exam_id}/edit#docs")


@bp.route("/entrance-exams/<exam_id>/docs/<doc_type>/<doc_id>/delete", methods=["POST"])
def entrance_exam_delete_doc(exam_id, doc_type, doc_id):
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)
    current_app.api_client.delete(f"/admin/{doc_type}/{doc_id}", token=token)
    flash("Document deleted.", "success")
    return redirect(f"/entrance-exams/{exam_id}/edit#docs")


# --- Audit Logs ---


@bp.route("/logs", methods=["GET"])
def logs():
    token = session.get("token")
    if not token:
        return redirect(_URL_LOGIN)

    params = {"limit": 20, "offset": 0}
    resp = current_app.api_client.get("/admin/logs", token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template("logs/logs.html", logs=data["data"], pagination=data.get("pagination", {}))


@bp.route("/logs/list", methods=["GET"])
def logs_list_partial():
    """HTMX partial — log rows for load-more."""
    token = session.get("token")
    if not token:
        return "", 401

    params = {"limit": 20, "offset": _int_arg("offset", 0)}
    resp = current_app.api_client.get("/admin/logs", token=token, params=params)
    data = resp.json() if resp.ok else {"data": [], "pagination": {}}

    return render_template("logs/_log_rows.html", logs=data["data"], pagination=data.get("pagination", {}))


def _handle_unexpected_error(exc):
    current_app.logger.error("Unhandled exception: %s", exc, exc_info=True)
    return render_template("auth/login.html"), 500


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "admin-dev-secret-key")
    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://backend:8000/api/v1")
    )
    app.register_blueprint(bp)
    app.register_error_handler(Exception, _handle_unexpected_error)
    return app


# Flask CLI entry point
app = create_app()
