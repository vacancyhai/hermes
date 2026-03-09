"""
User Profile & Application Routes

GET    /api/v1/users/profile                   — get own profile     (JWT)
PUT    /api/v1/users/profile                   — update own profile  (JWT)
PUT    /api/v1/users/profile/phone             — update phone number (JWT)
GET    /api/v1/users/applications              — list own apps       (JWT, paginated)
POST   /api/v1/users/applications              — apply to a job      (JWT)
DELETE /api/v1/users/applications/<app_id>     — withdraw            (JWT)
GET    /api/v1/users                           — list all users      (admin)
PUT    /api/v1/users/<user_id>/status          — change user status  (admin)
"""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.routes._helpers import _err, _flatten, _load_json, _ok
from app.services import user_service
from app.utils.constants import ErrorCode
from app.utils.decorators import admin_required
from app.validators.user_validator import ApplyToJobSchema, UpdatePhoneSchema, UpdateProfileSchema, UpdateUserStatusSchema

bp = Blueprint('users', __name__, url_prefix='/api/v1/users')

_profile_schema = UpdateProfileSchema()
_phone_schema = UpdatePhoneSchema()
_apply_schema = ApplyToJobSchema()
_update_status_schema = UpdateUserStatusSchema()


# ---------------------------------------------------------------------------
# Own profile
# ---------------------------------------------------------------------------

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user, profile = user_service.get_profile(get_jwt_identity())
    except ValueError:
        return _err(ErrorCode.NOT_FOUND_USER, 'User not found.', 404)
    return _ok(_serialize_profile(user, profile))


@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    data, err = _load_json(_profile_schema)
    if err:
        return err

    try:
        user, profile = user_service.update_profile(get_jwt_identity(), data)
    except ValueError:
        return _err(ErrorCode.NOT_FOUND_USER, 'User not found.', 404)
    return _ok(_serialize_profile(user, profile))


@bp.route('/profile/phone', methods=['PUT'])
@jwt_required()
def update_phone():
    data, err = _load_json(_phone_schema)
    if err:
        return err

    try:
        user = user_service.update_phone(get_jwt_identity(), data['phone'])
    except ValueError:
        return _err(ErrorCode.NOT_FOUND_USER, 'User not found.', 404)
    return _ok(_serialize_user(user))


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

@bp.route('/applications', methods=['GET'])
@jwt_required()
def list_applications():
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    except (TypeError, ValueError):
        return _err(ErrorCode.VALIDATION_INVALID_FORMAT, "'page' and 'per_page' must be positive integers.", 400)

    result = user_service.get_applications(get_jwt_identity(), page=page, per_page=per_page)
    return _ok(
        [_serialize_application(a) for a in result['items']],
        meta={
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
        },
    )


@bp.route('/applications', methods=['POST'])
@jwt_required()
def apply_to_job():
    data, err = _load_json(_apply_schema)
    if err:
        return err

    try:
        application = user_service.apply_to_job(get_jwt_identity(), str(data['job_id']))
    except ValueError as e:
        code = str(e)
        if code == ErrorCode.NOT_FOUND_JOB:
            return _err(ErrorCode.NOT_FOUND_JOB, 'Job not found or no longer active.', 404)
        if code == ErrorCode.ALREADY_APPLIED:
            return _err(ErrorCode.ALREADY_APPLIED, 'You have already applied to this job.', 409)
        return _err(ErrorCode.SERVER_ERROR, 'Could not process application.', 500)

    return _ok(_serialize_application(application), 201)


@bp.route('/applications/<app_id>', methods=['DELETE'])
@jwt_required()
def withdraw_application(app_id):
    try:
        application = user_service.withdraw_application(get_jwt_identity(), app_id)
    except ValueError:
        return _err(ErrorCode.NOT_FOUND_APPLICATION, 'Application not found.', 404)
    return _ok(_serialize_application(application))


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@bp.route('', methods=['GET'])
@jwt_required()
@admin_required
def list_users():
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 50))))
    except (TypeError, ValueError):
        return _err(ErrorCode.VALIDATION_INVALID_FORMAT, "'page' and 'per_page' must be positive integers.", 400)

    result = user_service.get_all_users(page=page, per_page=per_page)
    return _ok(
        [_serialize_user(u) for u in result['items']],
        meta={
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
        },
    )


@bp.route('/<user_id>/status', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_status(user_id):
    if user_id == get_jwt_identity():
        return _err(ErrorCode.FORBIDDEN_OWN_RESOURCE_ONLY, 'Admins cannot modify their own status.', 403)

    data, err = _load_json(_update_status_schema)
    if err:
        return err

    try:
        user = user_service.update_user_status(user_id, data['status'])
    except ValueError as e:
        code = str(e)
        if code == ErrorCode.NOT_FOUND_USER:
            return _err(ErrorCode.NOT_FOUND_USER, 'User not found.', 404)
        return _err(ErrorCode.SERVER_ERROR, 'Could not update user status.', 500)
    return _ok(_serialize_user(user))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _serialize_user(user) -> dict:
    return {
        'id': str(user.id),
        'email': user.email,
        'full_name': user.full_name,
        'phone': user.phone,
        'role': user.role,
        'status': user.status,
        'is_email_verified': user.is_email_verified,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }


def _serialize_profile(user, profile) -> dict:
    return {
        'user': _serialize_user(user),
        'profile': {
            'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            'gender': profile.gender,
            'category': profile.category,
            'is_pwd': profile.is_pwd,
            'is_ex_serviceman': profile.is_ex_serviceman,
            'state': profile.state,
            'city': profile.city,
            'pincode': profile.pincode,
            'highest_qualification': profile.highest_qualification,
            'education': profile.education,
            'physical_details': profile.physical_details,
            'notification_preferences': profile.notification_preferences,
            'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
        },
    }


def _serialize_application(application) -> dict:
    return {
        'id': str(application.id),
        'user_id': str(application.user_id),
        'job_id': str(application.job_id),
        'status': application.status,
        'is_priority': application.is_priority,
        'application_number': application.application_number,
        'exam_center': application.exam_center,
        'notes': application.notes,
        'applied_on': application.applied_on.isoformat() if application.applied_on else None,
    }
