"""
Main Routes
"""
from flask import Blueprint, jsonify

bp = Blueprint('main', __name__)


@bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "frontend-admin"}), 200


@bp.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Hermes Admin Frontend", "status": "running"}), 200
