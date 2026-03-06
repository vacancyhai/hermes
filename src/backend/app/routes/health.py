"""
Health Check Routes
"""
from flask import Blueprint, jsonify

bp = Blueprint('health', __name__)


@bp.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "backend"}), 200
