"""
Main Routes
"""
from flask import Blueprint, jsonify, redirect, render_template, session, url_for

from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import get_access_token, is_authenticated

bp = Blueprint('main', __name__)
_api = APIClient()


@bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "frontend"}), 200


@bp.route('/', methods=['GET'])
def index():
    access_token = get_access_token(session)
    try:
        data = _api.get_jobs(access_token=access_token, per_page=6)
        featured_jobs = data.get('jobs', [])
    except APIError:
        featured_jobs = []

    return render_template('pages/index.html',
                           featured_jobs=featured_jobs,
                           is_authenticated=is_authenticated(session))

