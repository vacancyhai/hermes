"""Hermes User Frontend — Flask + Jinja2 + HTMX."""

import os

from flask import Flask, render_template

from app.api_client import ApiClient


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    # API client for backend communication
    app.api_client = ApiClient(
        base_url=os.environ.get("BACKEND_API_URL", "http://localhost:8000/api/v1")
    )

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "hermes-frontend"}

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


# Flask CLI entry point
app = create_app()
