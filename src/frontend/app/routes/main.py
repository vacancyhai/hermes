"""
Main Routes - Stub (implement in EPIC_10)
"""
from flask import Blueprint, jsonify

bp = Blueprint('main', __name__)


@bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "frontend"}), 200


@bp.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Hermes Frontend", "status": "running"}), 200
