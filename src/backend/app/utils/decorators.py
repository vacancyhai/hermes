"""
Route decorators for role-based access control.

Thin wrappers around auth_middleware.require_role that give routes a clean,
readable decorator instead of @require_role('admin', 'operator').

IMPORTANT: Both decorators must be stacked *beneath* @jwt_required() so that
JWT claims are already decoded when they run.

Usage:
    from flask_jwt_extended import jwt_required
    from app.utils.decorators import admin_required, operator_required

    @bp.route('/admin-only')
    @jwt_required()
    @admin_required
    def admin_view():
        ...

    @bp.route('/staff-only')
    @jwt_required()
    @operator_required
    def staff_view():
        ...
"""
from app.middleware.auth_middleware import require_role


def admin_required(fn):
    """Allow access to admin role only."""
    return require_role('admin')(fn)


def operator_required(fn):
    """Allow access to admin or operator roles."""
    return require_role('admin', 'operator')(fn)
