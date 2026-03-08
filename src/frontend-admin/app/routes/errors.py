"""
Error Handlers - Stub
"""
from flask import Blueprint, jsonify

bp = Blueprint('errors', __name__)


@bp.app_errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found"}), 404


@bp.app_errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal Server Error"}), 500
