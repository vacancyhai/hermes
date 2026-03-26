"""Hermes Admin Frontend — Flask + Jinja2 + HTMX.

Routes:
  /health                         — Health check
  /                               — Dashboard (stats, quick links)
  /login                          — Admin login
  /logout                         — Clear session
  /jobs                           — Job management (list, search, status filter)
  /jobs/list                      — HTMX partial for job table rows
  /jobs/<id>/review               — Review/edit draft job, approve or update
  /jobs/<id>/approve              — Approve draft → active
  /api/extract-pdf                — PDF extraction for form auto-fill (inline)
  /jobs/<id>/docs/admit-cards                — POST: add admit card to job
  /jobs/<id>/docs/answer-keys     — POST: add answer key to job
  /jobs/<id>/docs/results         — POST: add result to job
  /jobs/<id>/docs/<type>/<doc_id>/delete — POST: delete doc from job
  /exams                          — Entrance exam management (list, search)
  /exams/list                     — HTMX partial for exam table rows
  /exams/new                      — Create entrance exam (GET/POST)
  /exams/<id>/edit                — Edit entrance exam (GET/POST)
  /exams/<id>/delete              — POST: delete entrance exam
  /exams/<id>/docs/admit-cards    — POST: add admit card to exam
  /exams/<id>/docs/answer-keys    — POST: add answer key to exam
  /exams/<id>/docs/results        — POST: add result to exam
  /exams/<id>/docs/<type>/<doc_id>/delete — POST: delete doc from exam
  /users                          — User management (list, search, status filter)
  /users/list                     — HTMX partial for user table rows
  /users/<id>/suspend             — Toggle user suspend/activate
  /logs                           — Admin audit log viewer
  /logs/list                      — HTMX partial for log rows
"""

import base64
import json
import os
import secrets

from flask import Flask, current_app, flash, redirect, render_template, request, session

from app.api_client import ApiClient


def _jwt_payload(token: str) -> dict:
    """Decode JWT payload without signature verification (read-only)."""
    try:
        part = token.split(".")[1]
        part += "=" * (4 - len(part) % 4)
        return json.loads(base64.b64decode(part))
    except Exception:
        return {}


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "admin-dev-secret-key")

    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://backend:8000/api/v1")
    )

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

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "hermes-frontend-admin"}

    # --- Auth ---

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            csrf_token = secrets.token_hex(16)
            session["csrf_token"] = csrf_token
            return render_template("login.html", csrf_token=csrf_token)

        # Validate CSRF token
        form_csrf = request.form.get("csrf_token", "")
        if not form_csrf or form_csrf != session.pop("csrf_token", None):
            flash("Invalid request. Please try again.", "error")
            return redirect("/login")

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
        return redirect("/login")

    @app.route("/logout")
    def logout():
        token = session.get("token")
        if token:
            current_app.api_client.post("/auth/admin/logout", token=token)
        session.clear()
        return redirect("/login")

    # --- Dashboard ---

    @app.route("/")
    def index():
        token = session.get("token")
        if not token:
            return redirect("/login")

        stats_resp = current_app.api_client.get("/admin/stats", token=token)
        if stats_resp.status_code == 401:
            token = _try_refresh()
            if not token:
                return redirect("/login")
            stats_resp = current_app.api_client.get("/admin/stats", token=token)
        stats = stats_resp.json() if stats_resp.ok else {}

        analytics = {}
        if session.get("admin_role") == "admin":
            analytics_resp = current_app.api_client.get("/admin/analytics", token=token)
            analytics = analytics_resp.json() if analytics_resp.ok else {}

        return render_template("dashboard.html", stats=stats, analytics=analytics)

    # --- Job Management ---

    @app.route("/jobs")
    def jobs():
        """Manage job vacancies (latest_job type only)."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        params = {"limit": 20, "offset": 0}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/jobs", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "jobs_manage.html",
            jobs=data["data"],
            pagination=data.get("pagination", {}),
            current_status=status_filter,
        )

    @app.route("/admit-cards")
    def admit_cards():
        """Manage admit cards."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        params = {"limit": 20, "offset": 0}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/admit-cards", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "admitcards_manage.html",
            jobs=data["data"],
            pagination=data.get("pagination", {}),
            current_status=status_filter,
        )

    @app.route("/answer-keys")
    def answer_keys():
        """Manage answer keys."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        params = {"limit": 20, "offset": 0}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/answer-keys", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "answerkeys_manage.html",
            jobs=data["data"],
            pagination=data.get("pagination", {}),
            current_status=status_filter,
        )

    @app.route("/results")
    def results():
        """Manage results."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        params = {"limit": 20, "offset": 0}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/results", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "results_manage.html",
            jobs=data["data"],
            pagination=data.get("pagination", {}),
            current_status=status_filter,
        )

    @app.route("/jobs/list")
    def jobs_list_partial():
        """HTMX partial — job table rows for load-more."""
        token = session.get("token")
        if not token:
            return "", 401

        params = {"limit": 20, "offset": _int_arg("offset", 0)}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/jobs", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("_job_rows.html", jobs=data["data"], pagination=data.get("pagination", {}), current_status=status_filter)

    @app.route("/admit-cards/list")
    def admit_cards_list_partial():
        """HTMX partial — admit card table rows for load-more."""
        token = session.get("token")
        if not token:
            return "", 401

        params = {"limit": 20, "offset": _int_arg("offset", 0)}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/admit-cards", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("_admitcard_rows.html", jobs=data["data"], pagination=data.get("pagination", {}), current_status=status_filter)

    @app.route("/answer-keys/list")
    def answer_keys_list_partial():
        """HTMX partial — answer key table rows for load-more."""
        token = session.get("token")
        if not token:
            return "", 401

        params = {"limit": 20, "offset": _int_arg("offset", 0)}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/answer-keys", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("_answerkey_rows.html", jobs=data["data"], pagination=data.get("pagination", {}), current_status=status_filter)

    @app.route("/results/list")
    def results_list_partial():
        """HTMX partial — result table rows for load-more."""
        token = session.get("token")
        if not token:
            return "", 401

        params = {"limit": 20, "offset": _int_arg("offset", 0)}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/results", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("_result_rows.html", jobs=data["data"], pagination=data.get("pagination", {}), current_status=status_filter)

    @app.route("/api/extract-pdf", methods=["POST"])
    def extract_pdf():
        """Proxy endpoint for PDF extraction - uploads file to backend API and returns extracted data."""
        token = session.get("token")
        if not token:
            return {"error": "Not authenticated"}, 401

        if "file" not in request.files:
            return {"error": "No file provided"}, 400

        file = request.files["file"]
        
        # Forward to backend API
        resp = current_app.api_client.post(
            "/admin/jobs/extract-pdf",
            token=token,
            files={"file": (file.filename, file.stream, file.content_type)}
        )
        
        if resp.ok:
            return resp.json(), 200
        else:
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"detail": "Extraction failed"}
            return error_data, resp.status_code

    @app.route("/jobs/new", methods=["GET", "POST"])
    def new_job():
        """Create a job vacancy (latest_job type)."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        if request.method == "POST":
            form = request.form.to_dict()
            payload = {}
            for f in ["job_title", "organization", "department", "job_type", "qualification_level",
                      "employment_type", "description", "short_description", "source_url"]:
                if f in form:
                    payload[f] = form[f] or None
            for f in ["total_vacancies", "fee_general", "fee_obc", "fee_sc_st",
                      "fee_ews", "fee_female", "salary_initial", "salary_max"]:
                if f in form:
                    val = form[f].strip()
                    payload[f] = int(val) if val else None
            for f in ["notification_date", "application_start", "application_end", "exam_start", "exam_end", "result_date"]:
                if f in form:
                    val = form[f].strip()
                    payload[f] = val if val else None
            payload["status"] = form.get("status", "draft")
            payload["is_featured"] = form.get("is_featured") == "true"
            payload["is_urgent"] = form.get("is_urgent") == "true"

            resp = current_app.api_client.post("/admin/jobs", token=token, json=payload)
            if resp.ok:
                job_id = resp.json().get("id")
                flash("Job created successfully.", "success")
                return redirect(f"/jobs/{job_id}/review")
            detail = resp.json().get("detail", "Failed to create job") if resp.headers.get("content-type", "").startswith("application/json") else "Failed to create job"
            flash(detail, "error")
            return render_template("job_create.html")

        return render_template("job_create.html")

    @app.route("/admit-cards/new", methods=["GET", "POST"])
    def new_admit_card():
        """Create an admit card entry."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        if request.method == "POST":
            form = request.form.to_dict()
            payload = {"job_type": "admit_card"}
            for f in ["job_title", "organization", "department", "qualification_level",
                      "description", "short_description", "source_url"]:
                if f in form:
                    payload[f] = form[f] or None
            for f in ["total_vacancies"]:
                if f in form:
                    val = form[f].strip()
                    payload[f] = int(val) if val else None
            for f in ["notification_date", "application_start", "application_end", "exam_start", "exam_end"]:
                if f in form:
                    val = form[f].strip()
                    payload[f] = val if val else None
            payload["status"] = form.get("status", "draft")
            payload["is_featured"] = form.get("is_featured") == "true"
            payload["is_urgent"] = form.get("is_urgent") == "true"

            resp = current_app.api_client.post("/admin/jobs", token=token, json=payload)
            if resp.ok:
                job_id = resp.json().get("id")
                flash("Admit card created successfully.", "success")
                return redirect(f"/jobs/{job_id}/review")
            detail = resp.json().get("detail", "Failed to create admit card") if resp.headers.get("content-type", "").startswith("application/json") else "Failed to create admit card"
            flash(detail, "error")
            return render_template("admitcard_create.html")

        return render_template("admitcard_create.html")

    @app.route("/answer-keys/new", methods=["GET", "POST"])
    def new_answer_key():
        """Create an answer key entry."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        if request.method == "POST":
            form = request.form.to_dict()
            payload = {"job_type": "answer_key"}
            for f in ["job_title", "organization", "department", "qualification_level",
                      "description", "short_description", "source_url"]:
                if f in form:
                    payload[f] = form[f] or None
            for f in ["total_vacancies"]:
                if f in form:
                    val = form[f].strip()
                    payload[f] = int(val) if val else None
            for f in ["notification_date", "application_start", "application_end", "exam_start", "result_date"]:
                if f in form:
                    val = form[f].strip()
                    payload[f] = val if val else None
            payload["status"] = form.get("status", "draft")
            payload["is_featured"] = form.get("is_featured") == "true"

            resp = current_app.api_client.post("/admin/jobs", token=token, json=payload)
            if resp.ok:
                job_id = resp.json().get("id")
                flash("Answer key created successfully.", "success")
                return redirect(f"/jobs/{job_id}/review")
            detail = resp.json().get("detail", "Failed to create answer key") if resp.headers.get("content-type", "").startswith("application/json") else "Failed to create answer key"
            flash(detail, "error")
            return render_template("answerkey_create.html")

        return render_template("answerkey_create.html")

    @app.route("/results/new", methods=["GET", "POST"])
    def new_result():
        """Create a result entry."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        if request.method == "POST":
            form = request.form.to_dict()
            payload = {"job_type": "result"}
            for f in ["job_title", "organization", "department", "qualification_level",
                      "description", "short_description", "source_url"]:
                if f in form:
                    payload[f] = form[f] or None
            for f in ["total_vacancies"]:
                if f in form:
                    val = form[f].strip()
                    payload[f] = int(val) if val else None
            for f in ["notification_date", "application_start", "application_end", "exam_start", "result_date"]:
                if f in form:
                    val = form[f].strip()
                    payload[f] = val if val else None
            payload["status"] = form.get("status", "draft")
            payload["is_featured"] = form.get("is_featured") == "true"

            resp = current_app.api_client.post("/admin/jobs", token=token, json=payload)
            if resp.ok:
                job_id = resp.json().get("id")
                flash("Result created successfully.", "success")
                return redirect(f"/jobs/{job_id}/review")
            detail = resp.json().get("detail", "Failed to create result") if resp.headers.get("content-type", "").startswith("application/json") else "Failed to create result"
            flash(detail, "error")
            return render_template("result_create.html")

        return render_template("result_create.html")

    @app.route("/jobs/<job_id>/delete", methods=["POST"])
    def delete_job(job_id):
        """Soft-delete a job (admin role only)."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        current_app.api_client.delete(f"/admin/jobs/{job_id}", token=token)
        flash("Job deleted.", "success")
        return redirect("/jobs")

    @app.route("/jobs/<job_id>/approve", methods=["POST"])
    def approve_job(job_id):
        token = session.get("token")
        if not token:
            return redirect("/login")

        current_app.api_client.put(f"/admin/jobs/{job_id}/approve", token=token)
        return redirect("/jobs")

    # --- Draft Review ---

    @app.route("/jobs/<job_id>/review", methods=["GET", "POST"])
    def review_job(job_id):
        token = session.get("token")
        if not token:
            return redirect("/login")

        if request.method == "POST":
            form = request.form.to_dict()
            update = {}
            text_fields = ["job_title", "organization", "department", "qualification_level",
                           "description", "short_description", "source_url"]
            for f in text_fields:
                if f in form:
                    update[f] = form[f] or None

            int_fields = ["total_vacancies", "fee_general", "fee_obc", "fee_sc_st",
                          "fee_ews", "fee_female", "salary_initial", "salary_max"]
            for f in int_fields:
                if f in form:
                    val = form[f].strip()
                    update[f] = int(val) if val else None

            date_fields = ["notification_date", "application_start", "application_end", "exam_start"]
            for f in date_fields:
                if f in form:
                    val = form[f].strip()
                    update[f] = val if val else None

            action = form.get("action", "save")

            if update:
                current_app.api_client.put(f"/admin/jobs/{job_id}", token=token, json=update)

            if action == "approve":
                current_app.api_client.put(f"/admin/jobs/{job_id}/approve", token=token)
                flash("Job approved and published", "success")
                return redirect("/jobs?status=active")

            flash("Draft saved", "success")
            return redirect(f"/jobs/{job_id}/review")

        # GET — fetch job detail directly by ID
        resp = current_app.api_client.get(f"/admin/jobs/{job_id}", token=token)
        if not resp.ok:
            flash("Job not found", "error")
            return redirect("/jobs")
        job = resp.json()

        return render_template("job_review.html", job=job)

    # --- User Management ---

    @app.route("/users")
    def users():
        token = session.get("token")
        if not token:
            return redirect("/login")

        params = {"limit": 20, "offset": 0}
        q = request.args.get("q")
        if q:
            params["q"] = q
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/users", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "users.html",
            users=data["data"],
            pagination=data.get("pagination", {}),
            current_status=status_filter,
            search_q=q or "",
        )

    @app.route("/users/list")
    def users_list_partial():
        """HTMX partial — user table rows for load-more."""
        token = session.get("token")
        if not token:
            return "", 401

        params = {"limit": 20, "offset": _int_arg("offset", 0)}
        q = request.args.get("q")
        if q:
            params["q"] = q
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/users", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("_user_rows.html", users=data["data"], pagination=data.get("pagination", {}), current_status=status_filter, search_q=q or "")

    @app.route("/users/<user_id>")
    def user_detail(user_id):
        """User detail view."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        resp = current_app.api_client.get(f"/admin/users/{user_id}", token=token)
        if not resp.ok:
            flash("User not found.", "error")
            return redirect("/users")
        user = resp.json()
        return render_template("user_detail.html", user=user)

    @app.route("/users/<user_id>/suspend", methods=["POST"])
    def toggle_user_status(user_id):
        """Suspend or activate a user."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        new_status = request.form.get("status", "suspended")
        current_app.api_client.put(f"/admin/users/{user_id}/status", token=token, json={"status": new_status})
        return redirect("/users")

    @app.route("/users/<user_id>/delete", methods=["POST"])
    def delete_user_permanently(user_id):
        """Permanently delete a user from both PostgreSQL and Firebase."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        
        resp = current_app.api_client.delete(f"/admin/users/{user_id}", token=token)
        if resp.ok:
            flash("User permanently deleted.", "success")
        else:
            flash("Failed to delete user.", "error")
        return redirect("/users")

    # --- Per-Job Phase Document HTMX Partials (used in job_review.html) ---

    @app.route("/partials/admin/jobs/<job_id>/admit-cards")
    def admin_job_admit_cards(job_id):
        """HTMX partial — existing admit cards for a job (job_review.html)."""
        token = session.get("token")
        if not token:
            return "", 401
        resp = current_app.api_client.get(f"/jobs/{job_id}/admit-cards", token=token)
        docs = resp.json() if resp.ok else []
        return _render_doc_list(docs, job_id, "admit-cards")

    @app.route("/partials/admin/jobs/<job_id>/answer-keys")
    def admin_job_answer_keys(job_id):
        """HTMX partial — existing answer keys for a job (job_review.html)."""
        token = session.get("token")
        if not token:
            return "", 401
        resp = current_app.api_client.get(f"/jobs/{job_id}/answer-keys", token=token)
        docs = resp.json() if resp.ok else []
        return _render_doc_list(docs, job_id, "answer-keys")

    @app.route("/partials/admin/jobs/<job_id>/results")
    def admin_job_results(job_id):
        """HTMX partial — existing results for a job (job_review.html)."""
        token = session.get("token")
        if not token:
            return "", 401
        resp = current_app.api_client.get(f"/jobs/{job_id}/results", token=token)
        docs = resp.json() if resp.ok else []
        return _render_doc_list(docs, job_id, "results")

    def _render_doc_list(docs: list, parent_id: str, doc_type: str) -> str:
        """Render a compact table of existing docs with delete buttons."""
        if not docs:
            return '<p style="color:#9ca3af;font-size:.85rem">No entries yet.</p>'
        rows = ""
        for d in docs:
            phase = d.get("phase_number") or "—"
            title = d.get("title", "")
            doc_id = d.get("id", "")
            rows += (
                f'<tr>'
                f'<td style="font-size:.8rem;padding:.3rem .5rem">{phase}</td>'
                f'<td style="font-size:.8rem;padding:.3rem .5rem">{title}</td>'
                f'<td style="padding:.3rem .5rem">'
                f'<form method="POST" action="/jobs/{parent_id}/docs/{doc_type}/{doc_id}/delete"'
                f' onsubmit="return confirm(\'Delete this document?\')" style="display:inline">'
                f'<button type="submit" style="font-size:.75rem;padding:.2rem .5rem;border:1px solid #fca5a5;background:#fff;color:#dc2626;border-radius:.3rem;cursor:pointer">Del</button>'
                f'</form></td>'
                f'</tr>'
            )
        return (
            f'<table style="width:100%;border-collapse:collapse;font-size:.825rem">'
            f'<thead><tr>'
            f'<th style="text-align:left;font-size:.75rem;color:#6b7280;padding:.3rem .5rem">Phase</th>'
            f'<th style="text-align:left;font-size:.75rem;color:#6b7280;padding:.3rem .5rem">Title</th>'
            f'<th></th></tr></thead><tbody>{rows}</tbody></table>'
        )

    # --- Per-Job Phase Document Management ---

    @app.route("/jobs/<job_id>/docs/admit-cards", methods=["POST"])
    def job_add_admit_card(job_id):
        """Add an admit card to a job."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        form = request.form.to_dict()
        payload = {
            "title": form.get("title", ""),
            "download_url": form.get("download_url", ""),
            "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
            "valid_from": form.get("valid_from") or None,
            "valid_until": form.get("valid_until") or None,
            "notes": form.get("notes") or None,
        }
        current_app.api_client.post(f"/admin/jobs/{job_id}/admit-cards", token=token, json=payload)
        flash("Admit card added.", "success")
        return redirect(f"/jobs/{job_id}/review#docs")

    @app.route("/jobs/<job_id>/docs/answer-keys", methods=["POST"])
    def job_add_answer_key(job_id):
        """Add an answer key to a job."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        form = request.form.to_dict()
        files_raw = form.get("files_json", "[]")
        try:
            files = json.loads(files_raw)
        except Exception:
            files = []
        payload = {
            "title": form.get("title", ""),
            "answer_key_type": form.get("answer_key_type", "provisional"),
            "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
            "files": files,
            "objection_url": form.get("objection_url") or None,
            "objection_deadline": form.get("objection_deadline") or None,
        }
        current_app.api_client.post(f"/admin/jobs/{job_id}/answer-keys", token=token, json=payload)
        flash("Answer key added.", "success")
        return redirect(f"/jobs/{job_id}/review#docs")

    @app.route("/jobs/<job_id>/docs/results", methods=["POST"])
    def job_add_result(job_id):
        """Add a result to a job."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        form = request.form.to_dict()
        payload = {
            "title": form.get("title", ""),
            "result_type": form.get("result_type", "merit_list"),
            "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
            "download_url": form.get("download_url") or None,
            "total_qualified": int(form["total_qualified"]) if form.get("total_qualified") else None,
            "notes": form.get("notes") or None,
        }
        current_app.api_client.post(f"/admin/jobs/{job_id}/results", token=token, json=payload)
        flash("Result added.", "success")
        return redirect(f"/jobs/{job_id}/review#docs")

    @app.route("/jobs/<job_id>/docs/<doc_type>/<doc_id>/delete", methods=["POST"])
    def job_delete_doc(job_id, doc_type, doc_id):
        """Delete a phase document from a job."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        current_app.api_client.delete(f"/admin/jobs/{job_id}/{doc_type}/{doc_id}", token=token)
        flash("Document deleted.", "success")
        return redirect(f"/jobs/{job_id}/review#docs")

    # --- Entrance Exam Management ---

    @app.route("/exams")
    def exams():
        token = session.get("token")
        if not token:
            return redirect("/login")
        params = {"limit": 20, "offset": 0}
        stream = request.args.get("stream")
        if stream:
            params["stream"] = stream
        resp = current_app.api_client.get("/admin/exams", token=token, params=params)
        if resp.status_code == 401:
            token = _try_refresh()
            if not token:
                return redirect("/login")
            resp = current_app.api_client.get("/admin/exams", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("exams.html", exams=data["data"], pagination=data.get("pagination", {}), current_stream=stream)

    @app.route("/exams/list")
    def exams_list_partial():
        """HTMX partial — exam table rows for load-more."""
        token = session.get("token")
        if not token:
            return "", 401
        params = {"limit": 20, "offset": _int_arg("offset", 0)}
        stream = request.args.get("stream")
        if stream:
            params["stream"] = stream
        resp = current_app.api_client.get("/admin/exams", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("_exam_rows.html", exams=data["data"], pagination=data.get("pagination", {}), current_stream=stream)

    @app.route("/exams/new", methods=["GET", "POST"])
    def new_exam():
        """Create a new entrance exam."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        if request.method == "POST":
            form = request.form.to_dict()
            payload = {}
            for f in ["exam_name", "conducting_body", "counselling_body", "exam_type",
                      "stream", "description", "short_description", "source_url", "status"]:
                payload[f] = form.get(f) or None
            for f in ["fee_general", "fee_obc", "fee_sc_st", "fee_ews", "fee_female"]:
                val = form.get(f, "").strip()
                payload[f] = int(val) if val else None
            for f in ["application_start", "application_end", "exam_date",
                      "result_date", "counselling_start"]:
                val = form.get(f, "").strip()
                payload[f] = val if val else None
            payload["is_featured"] = form.get("is_featured") == "on"
            payload.setdefault("status", "active")
            resp = current_app.api_client.post("/admin/exams", token=token, json=payload)
            if resp.ok:
                exam_id = resp.json().get("id")
                flash("Entrance exam created.", "success")
                return redirect(f"/exams/{exam_id}/edit")
            detail = resp.json().get("detail", "Failed to create exam") if resp.headers.get("content-type", "").startswith("application/json") else "Failed to create exam"
            flash(detail, "error")
        return render_template("exam_edit.html", exam=None, mode="new")

    @app.route("/exams/<exam_id>/edit", methods=["GET", "POST"])
    def edit_exam(exam_id):
        """Edit an existing entrance exam."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        if request.method == "POST":
            form = request.form.to_dict()
            update = {}
            for f in ["exam_name", "conducting_body", "counselling_body", "exam_type",
                      "stream", "description", "short_description", "source_url", "status"]:
                if f in form:
                    update[f] = form[f] or None
            for f in ["fee_general", "fee_obc", "fee_sc_st", "fee_ews", "fee_female"]:
                val = form.get(f, "").strip()
                update[f] = int(val) if val else None
            for f in ["application_start", "application_end", "exam_date",
                      "result_date", "counselling_start"]:
                val = form.get(f, "").strip()
                update[f] = val if val else None
            update["is_featured"] = form.get("is_featured") == "on"
            resp = current_app.api_client.put(f"/admin/exams/{exam_id}", token=token, json=update)
            if resp.ok:
                flash("Exam updated.", "success")
            else:
                flash("Failed to update exam.", "error")
            return redirect(f"/exams/{exam_id}/edit")

        resp_detail_req = current_app.api_client.get(f"/admin/exams/{exam_id}", token=token)
        if not resp_detail_req.ok:
            flash("Exam not found.", "error")
            return redirect("/exams")
        resp_detail = resp_detail_req.json()

        ac_resp = current_app.api_client.get(f"/exams/{exam_id}/admit-cards", token=token)
        ak_resp = current_app.api_client.get(f"/exams/{exam_id}/answer-keys", token=token)
        re_resp = current_app.api_client.get(f"/exams/{exam_id}/results", token=token)
        admit_cards = ac_resp.json() if ac_resp.ok else []
        answer_keys = ak_resp.json() if ak_resp.ok else []
        results = re_resp.json() if re_resp.ok else []

        return render_template("exam_edit.html", exam=resp_detail, mode="edit",
                               admit_cards=admit_cards, answer_keys=answer_keys, results=results)

    @app.route("/exams/<exam_id>/delete", methods=["POST"])
    def delete_exam(exam_id):
        """Delete an entrance exam (admin only)."""
        token = session.get("token")
        if not token:
            return redirect("/login")
        current_app.api_client.delete(f"/admin/exams/{exam_id}", token=token)
        flash("Exam deleted.", "success")
        return redirect("/exams")

    # Per-exam phase document management

    @app.route("/exams/<exam_id>/docs/admit-cards", methods=["POST"])
    def exam_add_admit_card(exam_id):
        token = session.get("token")
        if not token:
            return redirect("/login")
        form = request.form.to_dict()
        payload = {
            "title": form.get("title", ""),
            "download_url": form.get("download_url", ""),
            "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
            "valid_from": form.get("valid_from") or None,
            "valid_until": form.get("valid_until") or None,
            "notes": form.get("notes") or None,
        }
        current_app.api_client.post(f"/admin/exams/{exam_id}/admit-cards", token=token, json=payload)
        flash("Admit card added.", "success")
        return redirect(f"/exams/{exam_id}/edit#docs")

    @app.route("/exams/<exam_id>/docs/answer-keys", methods=["POST"])
    def exam_add_answer_key(exam_id):
        token = session.get("token")
        if not token:
            return redirect("/login")
        form = request.form.to_dict()
        try:
            files = json.loads(form.get("files_json", "[]"))
        except Exception:
            files = []
        payload = {
            "title": form.get("title", ""),
            "answer_key_type": form.get("answer_key_type", "provisional"),
            "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
            "files": files,
            "objection_url": form.get("objection_url") or None,
            "objection_deadline": form.get("objection_deadline") or None,
        }
        current_app.api_client.post(f"/admin/exams/{exam_id}/answer-keys", token=token, json=payload)
        flash("Answer key added.", "success")
        return redirect(f"/exams/{exam_id}/edit#docs")

    @app.route("/exams/<exam_id>/docs/results", methods=["POST"])
    def exam_add_result(exam_id):
        token = session.get("token")
        if not token:
            return redirect("/login")
        form = request.form.to_dict()
        payload = {
            "title": form.get("title", ""),
            "result_type": form.get("result_type", "merit_list"),
            "phase_number": int(form["phase_number"]) if form.get("phase_number") else None,
            "download_url": form.get("download_url") or None,
            "total_qualified": int(form["total_qualified"]) if form.get("total_qualified") else None,
            "notes": form.get("notes") or None,
        }
        current_app.api_client.post(f"/admin/exams/{exam_id}/results", token=token, json=payload)
        flash("Result added.", "success")
        return redirect(f"/exams/{exam_id}/edit#docs")

    @app.route("/exams/<exam_id>/docs/<doc_type>/<doc_id>/delete", methods=["POST"])
    def exam_delete_doc(exam_id, doc_type, doc_id):
        token = session.get("token")
        if not token:
            return redirect("/login")
        current_app.api_client.delete(f"/admin/exams/{exam_id}/{doc_type}/{doc_id}", token=token)
        flash("Document deleted.", "success")
        return redirect(f"/exams/{exam_id}/edit#docs")

    # --- Audit Logs ---

    @app.route("/logs")
    def logs():
        token = session.get("token")
        if not token:
            return redirect("/login")

        params = {"limit": 20, "offset": 0}
        resp = current_app.api_client.get("/admin/logs", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("logs.html", logs=data["data"], pagination=data.get("pagination", {}))

    @app.route("/logs/list")
    def logs_list_partial():
        """HTMX partial — log rows for load-more."""
        token = session.get("token")
        if not token:
            return "", 401

        params = {"limit": 20, "offset": _int_arg("offset", 0)}
        resp = current_app.api_client.get("/admin/logs", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("_log_rows.html", logs=data["data"], pagination=data.get("pagination", {}))

    def _int_arg(name: str, default: int) -> int:
        """Parse an integer query parameter safely."""
        try:
            return int(request.args.get(name, default))
        except (ValueError, TypeError):
            return default

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        app.logger.error("Unhandled exception: %s", exc, exc_info=True)
        return render_template("login.html"), 500

    return app


# Flask CLI entry point
app = create_app()
