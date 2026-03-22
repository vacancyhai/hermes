"""Hermes User Frontend — Flask + Jinja2 + HTMX."""

import os

from flask import Flask, current_app, render_template, request, session, redirect, url_for, flash

from app.api_client import ApiClient


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://localhost:8000/api/v1")
    )

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "hermes-frontend"}

    @app.route("/")
    def index():
        """Landing page — full page with initial job listing."""
        params = _job_params()
        resp = current_app.api_client.get("/jobs", params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("index.html", jobs=data["data"], pagination=data.get("pagination", {}), params=params)

    @app.route("/jobs")
    def job_list_partial():
        """HTMX partial — returns only the job card rows + load-more button."""
        params = _job_params()
        resp = current_app.api_client.get("/jobs", params=params)
        data = resp.json() if resp.ok else {"data": [], "pagination": {}}
        return render_template("_job_cards.html", jobs=data["data"], pagination=data.get("pagination", {}), params=params)

    @app.route("/jobs/<slug>")
    def job_detail(slug):
        """Job detail page."""
        resp = current_app.api_client.get(f"/jobs/{slug}")
        if not resp.ok:
            return render_template("404.html"), 404
        job = resp.json()
        return render_template("job_detail.html", job=job)

    # --- Application Dashboard ---

    @app.route("/dashboard")
    def dashboard():
        """Application tracking dashboard — requires login."""
        token = session.get("token")
        if not token:
            return render_template("login.html", next="/dashboard")

        # Fetch stats
        stats_resp = current_app.api_client.get("/applications/stats", token=token)
        stats = stats_resp.json() if stats_resp.ok else {"total": 0}

        # Fetch applications
        params = {"limit": 20, "offset": 0}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        apps_resp = current_app.api_client.get("/applications", token=token, params=params)
        apps_data = apps_resp.json() if apps_resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "dashboard.html",
            stats=stats,
            applications=apps_data["data"],
            pagination=apps_data.get("pagination", {}),
            current_status=status_filter,
        )

    @app.route("/dashboard/applications")
    def dashboard_applications_partial():
        """HTMX partial — returns application rows for the dashboard."""
        token = session.get("token")
        if not token:
            return "", 401

        params = {"limit": 20, "offset": int(request.args.get("offset", 0))}
        status_filter = request.args.get("status")
        if status_filter:
            params["status"] = status_filter

        apps_resp = current_app.api_client.get("/applications", token=token, params=params)
        apps_data = apps_resp.json() if apps_resp.ok else {"data": [], "pagination": {}}

        return render_template(
            "_application_rows.html",
            applications=apps_data["data"],
            pagination=apps_data.get("pagination", {}),
            current_status=status_filter,
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Simple login form — stores JWT in session."""
        if request.method == "GET":
            return render_template("login.html", next=request.args.get("next", "/dashboard"))

        email = request.form.get("email", "")
        password = request.form.get("password", "")
        resp = current_app.api_client.post("/auth/login", json={"email": email, "password": password})
        if resp.ok:
            data = resp.json()
            session["token"] = data.get("access_token")
            session["user_name"] = data.get("user", {}).get("full_name", email)
            next_url = request.form.get("next", "/dashboard")
            return redirect(next_url)
        flash("Invalid email or password", "error")
        return render_template("login.html", next=request.form.get("next", "/dashboard"))

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/")

    def _job_params() -> dict:
        """Build query params from request args."""
        params: dict = {}
        for key in ("q", "job_type", "qualification_level", "organization", "department"):
            val = request.args.get(key)
            if val:
                params[key] = val
        params["limit"] = min(int(request.args.get("limit", 20)), 100)
        params["offset"] = int(request.args.get("offset", 0))
        return params

    return app


# Flask CLI entry point
app = create_app()
