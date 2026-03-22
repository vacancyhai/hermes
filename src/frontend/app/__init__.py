"""Hermes User Frontend — Flask + Jinja2 + HTMX."""

import os

from flask import Flask, current_app, render_template, request

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
