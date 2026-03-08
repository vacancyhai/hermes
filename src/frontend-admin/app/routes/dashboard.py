"""
Dashboard Routes - Stub
Admin/operator dashboard overview (implement in future story)
"""
from flask import Blueprint, jsonify

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@bp.route('/')
def index():
    return jsonify({"message": "Admin Dashboard", "status": "stub"}), 200
