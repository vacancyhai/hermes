"""Hermes Admin Frontend — Flask + Jinja2 + HTMX.

Routes:
  /health              — Health check
  /                    — Dashboard (stats, quick links)
  /login               — Admin login
  /logout              — Clear session
  /jobs                — Job management (list, search, status filter)
  /jobs/list           — HTMX partial for job table rows
  /jobs/upload         — Upload PDF for AI extraction
  /jobs/<id>/review    — Review/edit draft job, approve or update
  /jobs/<id>/approve   — Approve draft → active
  /users               — User management (list, search, status filter)
  /users/list          — HTMX partial for user table rows
  /users/<id>/suspend  — Toggle user suspend/activate
  /logs                — Admin audit log viewer
  /logs/list           — HTMX partial for log rows
"""

import os

from flask import Flask, current_app, flash, redirect, render_template, request, session, url_for

from app.api_client import ApiClient


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "admin-dev-secret-key")

    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://backend:8000/api/v1")
    )

    # --- Health ---

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "hermes-frontend-admin"}

    # --- Auth ---

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")

        email = request.form.get("email", "")
        password = request.form.get("password", "")
        resp = current_app.api_client.post("/auth/admin/login", json={"email": email, "password": password})
        if resp.ok:
            data = resp.json()
            session["token"] = data.get("access_token")
            session["admin_name"] = data.get("admin", {}).get("full_name", email)
            session["admin_role"] = data.get("admin", {}).get("role", "operator")
            return redirect("/")
        flash("Invalid credentials", "error")
        return render_template("login.html")

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
        stats = stats_resp.json() if stats_resp.ok else {}

        return render_template("dashboard.html", stats=stats)

    # --- Job Management ---

    @app.route("/jobs")
    def jobs():
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
            "jobs.html",
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

        params = {"limit": 20, "offset": int(request.args.get("offset", 0))}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/jobs", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("_job_rows.html", jobs=data["data"], pagination=data.get("pagination", {}), current_status=status_filter)

    @app.route("/jobs/<job_id>/approve", methods=["POST"])
    def approve_job(job_id):
        token = session.get("token")
        if not token:
            return redirect("/login")

        current_app.api_client.put(f"/admin/jobs/{job_id}/approve", token=token)
        return redirect("/jobs")

    # --- PDF Upload ---

    @app.route("/jobs/upload", methods=["GET", "POST"])
    def upload_pdf():
        token = session.get("token")
        if not token:
            return redirect("/login")

        if request.method == "GET":
            return render_template("job_upload.html")

        file = request.files.get("pdf_file")
        if not file or not file.filename:
            flash("Please select a PDF file", "error")
            return render_template("job_upload.html")

        resp = current_app.api_client.post_file(
            "/admin/jobs/upload-pdf",
            token=token,
            files={"file": (file.filename, file.stream, "application/pdf")},
        )

        if resp.ok:
            data = resp.json()
            flash(f"PDF uploaded successfully. Extraction task started (ID: {data.get('task_id', 'N/A')[:8]}...)", "success")
            return redirect("/jobs?status=draft")

        detail = resp.json().get("detail", "Upload failed") if resp.headers.get("content-type", "").startswith("application/json") else "Upload failed"
        flash(detail, "error")
        return render_template("job_upload.html")

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

        # GET — fetch job detail
        resp = current_app.api_client.get(f"/admin/jobs", token=token, params={"limit": 100, "offset": 0})
        job = None
        if resp.ok:
            for j in resp.json().get("data", []):
                if j["id"] == job_id:
                    job = j
                    break

        if not job:
            flash("Job not found", "error")
            return redirect("/jobs")

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

        params = {"limit": 20, "offset": int(request.args.get("offset", 0))}
        q = request.args.get("q")
        if q:
            params["q"] = q
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        resp = current_app.api_client.get("/admin/users", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("_user_rows.html", users=data["data"], pagination=data.get("pagination", {}), current_status=status_filter, search_q=q or "")

    @app.route("/users/<user_id>/suspend", methods=["POST"])
    def toggle_user_status(user_id):
        """Suspend or activate a user."""
        token = session.get("token")
        if not token:
            return redirect("/login")

        new_status = request.form.get("status", "suspended")
        current_app.api_client.put(f"/admin/users/{user_id}/status", token=token, json={"status": new_status})
        return redirect("/users")

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

        params = {"limit": 20, "offset": int(request.args.get("offset", 0))}
        resp = current_app.api_client.get("/admin/logs", token=token, params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}

        return render_template("_log_rows.html", logs=data["data"], pagination=data.get("pagination", {}))

    return app


# Flask CLI entry point
app = create_app()
