"""
Error Handlers
"""
from flask import Blueprint, render_template

bp = Blueprint('errors', __name__)


@bp.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

