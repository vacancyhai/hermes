"""
Content Routes — CRUD endpoints for all 6 content types.

All public GET endpoints are rate-limited but do not require authentication.
Write endpoints (POST/PUT/DELETE) require JWT + operator/admin role.

Route summary:
    GET  /api/v1/results               - list results
    GET  /api/v1/results/<id>          - result detail
    POST /api/v1/results               - create result (operator+)
    PUT  /api/v1/results/<id>          - update result (operator+)
    DELETE /api/v1/results/<id>        - delete result (admin)

    (same pattern for admit-cards, answer-keys, admissions, yojanas, board-results)
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.middleware.rate_limiter import limiter
from app.routes._helpers import _d, _err, _load_args, _load_json, _ok
from app.services import content_service
from app.utils.constants import ErrorCode
from app.utils.decorators import admin_required, operator_required

bp = Blueprint('content', __name__, url_prefix='/api/v1')


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def _serialize_result(r) -> dict:
    return {
        'id': str(r.id),
        'job_id': str(r.job_id) if r.job_id else None,
        'result_type': r.result_type,
        'result_phase': r.result_phase,
        'result_title': r.result_title,
        'result_date': _d(r.result_date),
        'result_links': r.result_links,
        'cut_off_marks': r.cut_off_marks,
        'statistics': r.statistics,
        'is_final': r.is_final,
        'status': r.status,
        'created_at': _d(r.created_at),
        'updated_at': _d(r.updated_at),
    }


def _serialize_admit_card(a) -> dict:
    return {
        'id': str(a.id),
        'job_id': str(a.job_id) if a.job_id else None,
        'exam_name': a.exam_name,
        'exam_phase': a.exam_phase,
        'release_date': _d(a.release_date),
        'exam_date_start': _d(a.exam_date_start),
        'exam_date_end': _d(a.exam_date_end),
        'exam_mode': a.exam_mode,
        'download_link': a.download_link,
        'exam_city_link': a.exam_city_link,
        'mock_test_link': a.mock_test_link,
        'instructions': a.instructions,
        'reporting_time': a.reporting_time,
        'exam_timing': a.exam_timing,
        'important_documents': a.important_documents,
        'exam_centers': a.exam_centers,
        'status': a.status,
        'created_at': _d(a.created_at),
        'updated_at': _d(a.updated_at),
    }


def _serialize_answer_key(ak) -> dict:
    return {
        'id': str(ak.id),
        'job_id': str(ak.job_id) if ak.job_id else None,
        'exam_name': ak.exam_name,
        'exam_phase': ak.exam_phase,
        'paper_name': ak.paper_name,
        'release_date': _d(ak.release_date),
        'answer_key_links': ak.answer_key_links,
        'subject_wise_links': ak.subject_wise_links,
        'objection_start': _d(ak.objection_start),
        'objection_end': _d(ak.objection_end),
        'objection_fee': ak.objection_fee,
        'objection_link': ak.objection_link,
        'response_sheet_link': ak.response_sheet_link,
        'question_paper_link': ak.question_paper_link,
        'total_questions': ak.total_questions,
        'status': ak.status,
        'created_at': _d(ak.created_at),
        'updated_at': _d(ak.updated_at),
    }


def _serialize_admission(a) -> dict:
    return {
        'id': str(a.id),
        'title': a.title,
        'slug': a.slug,
        'admission_type': a.admission_type,
        'course_name': a.course_name,
        'conducting_body': a.conducting_body,
        'total_seats': a.total_seats,
        'description': a.description,
        'eligibility': a.eligibility,
        'application_dates': a.application_dates,
        'application_fee': a.application_fee,
        'application_link': a.application_link,
        'notification_pdf': a.notification_pdf,
        'syllabus_link': a.syllabus_link,
        'exam_pattern': a.exam_pattern,
        'selection_process': a.selection_process,
        'status': a.status,
        'is_featured': a.is_featured,
        'views': a.views,
        'created_at': _d(a.created_at),
        'updated_at': _d(a.updated_at),
    }


def _serialize_yojana(y) -> dict:
    return {
        'id': str(y.id),
        'title': y.title,
        'slug': y.slug,
        'yojana_type': y.yojana_type,
        'state': y.state,
        'department': y.department,
        'short_description': y.short_description,
        'eligibility': y.eligibility,
        'benefits': y.benefits,
        'benefit_amount': y.benefit_amount,
        'how_to_apply': y.how_to_apply,
        'required_documents': y.required_documents,
        'application_link': y.application_link,
        'official_website': y.official_website,
        'helpline': y.helpline,
        'start_date': _d(y.start_date),
        'last_date': _d(y.last_date),
        'is_active': y.is_active,
        'status': y.status,
        'is_featured': y.is_featured,
        'views': y.views,
        'created_at': _d(y.created_at),
        'updated_at': _d(y.updated_at),
    }


def _serialize_board_result(br) -> dict:
    return {
        'id': str(br.id),
        'board_name': br.board_name,
        'class_': br.class_,
        'stream': br.stream,
        'exam_year': br.exam_year,
        'result_type': br.result_type,
        'exam_start_date': _d(br.exam_start_date),
        'exam_end_date': _d(br.exam_end_date),
        'result_date': _d(br.result_date),
        'result_time': br.result_time,
        'result_link': br.result_link,
        'marksheet_download_link': br.marksheet_download_link,
        'topper_list_link': br.topper_list_link,
        'date_sheet_link': br.date_sheet_link,
        'statistics': br.statistics,
        'how_to_check': br.how_to_check,
        'alternative_links': br.alternative_links,
        'status': br.status,
        'views': br.views,
        'created_at': _d(br.created_at),
        'updated_at': _d(br.updated_at),
    }


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

@bp.route('/results', methods=['GET'])
@limiter.limit('100 per minute')
def list_results():
    result = content_service.list_results(filters=_get_common_filters())
    return _ok(
        [_serialize_result(r) for r in result['items']],
        meta={'total': result['total'], 'page': result['page'],
              'per_page': result['per_page'], 'pages': result['pages']},
    )


@bp.route('/results/<result_id>', methods=['GET'])
@limiter.limit('200 per minute')
def get_result(result_id):
    item = content_service.get_result_by_id(result_id)
    return _ok(_serialize_result(item))


@bp.route('/results', methods=['POST'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def create_result():
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.create_result(data)
    return _ok(_serialize_result(item), 201)


@bp.route('/results/<result_id>', methods=['PUT'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def update_result(result_id):
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.update_result(result_id, data)
    return _ok(_serialize_result(item))


@bp.route('/results/<result_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@limiter.limit('10 per minute')
def delete_result(result_id):
    content_service.delete_result(result_id)
    return _ok({'message': 'Result deleted successfully.'})


# ---------------------------------------------------------------------------
# Admit Cards
# ---------------------------------------------------------------------------

@bp.route('/admit-cards', methods=['GET'])
@limiter.limit('100 per minute')
def list_admit_cards():
    result = content_service.list_admit_cards(filters=_get_common_filters())
    return _ok(
        [_serialize_admit_card(a) for a in result['items']],
        meta={'total': result['total'], 'page': result['page'],
              'per_page': result['per_page'], 'pages': result['pages']},
    )


@bp.route('/admit-cards/<admit_card_id>', methods=['GET'])
@limiter.limit('200 per minute')
def get_admit_card(admit_card_id):
    item = content_service.get_admit_card_by_id(admit_card_id)
    return _ok(_serialize_admit_card(item))


@bp.route('/admit-cards', methods=['POST'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def create_admit_card():
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.create_admit_card(data)
    return _ok(_serialize_admit_card(item), 201)


@bp.route('/admit-cards/<admit_card_id>', methods=['PUT'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def update_admit_card(admit_card_id):
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.update_admit_card(admit_card_id, data)
    return _ok(_serialize_admit_card(item))


@bp.route('/admit-cards/<admit_card_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@limiter.limit('10 per minute')
def delete_admit_card(admit_card_id):
    content_service.delete_admit_card(admit_card_id)
    return _ok({'message': 'Admit card deleted successfully.'})


# ---------------------------------------------------------------------------
# Answer Keys
# ---------------------------------------------------------------------------

@bp.route('/answer-keys', methods=['GET'])
@limiter.limit('100 per minute')
def list_answer_keys():
    result = content_service.list_answer_keys(filters=_get_common_filters())
    return _ok(
        [_serialize_answer_key(ak) for ak in result['items']],
        meta={'total': result['total'], 'page': result['page'],
              'per_page': result['per_page'], 'pages': result['pages']},
    )


@bp.route('/answer-keys/<answer_key_id>', methods=['GET'])
@limiter.limit('200 per minute')
def get_answer_key(answer_key_id):
    item = content_service.get_answer_key_by_id(answer_key_id)
    return _ok(_serialize_answer_key(item))


@bp.route('/answer-keys', methods=['POST'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def create_answer_key():
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.create_answer_key(data)
    return _ok(_serialize_answer_key(item), 201)


@bp.route('/answer-keys/<answer_key_id>', methods=['PUT'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def update_answer_key(answer_key_id):
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.update_answer_key(answer_key_id, data)
    return _ok(_serialize_answer_key(item))


@bp.route('/answer-keys/<answer_key_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@limiter.limit('10 per minute')
def delete_answer_key(answer_key_id):
    content_service.delete_answer_key(answer_key_id)
    return _ok({'message': 'Answer key deleted successfully.'})


# ---------------------------------------------------------------------------
# Admissions
# ---------------------------------------------------------------------------

@bp.route('/admissions', methods=['GET'])
@limiter.limit('100 per minute')
def list_admissions():
    result = content_service.list_admissions(filters=_get_common_filters())
    return _ok(
        [_serialize_admission(a) for a in result['items']],
        meta={'total': result['total'], 'page': result['page'],
              'per_page': result['per_page'], 'pages': result['pages']},
    )


@bp.route('/admissions/<slug>', methods=['GET'])
@limiter.limit('200 per minute')
def get_admission(slug):
    # Try slug first (public API); fall back to UUID for admin tools
    try:
        item = content_service.get_admission_by_slug(slug)
    except Exception:
        item = content_service.get_admission_by_id(slug)
    return _ok(_serialize_admission(item))


@bp.route('/admissions', methods=['POST'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def create_admission():
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.create_admission(data)
    return _ok(_serialize_admission(item), 201)


@bp.route('/admissions/<admission_id>', methods=['PUT'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def update_admission(admission_id):
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.update_admission(admission_id, data)
    return _ok(_serialize_admission(item))


@bp.route('/admissions/<admission_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@limiter.limit('10 per minute')
def delete_admission(admission_id):
    content_service.delete_admission(admission_id)
    return _ok({'message': 'Admission deleted successfully.'})


# ---------------------------------------------------------------------------
# Yojanas
# ---------------------------------------------------------------------------

@bp.route('/yojanas', methods=['GET'])
@limiter.limit('100 per minute')
def list_yojanas():
    result = content_service.list_yojanas(filters=_get_common_filters())
    return _ok(
        [_serialize_yojana(y) for y in result['items']],
        meta={'total': result['total'], 'page': result['page'],
              'per_page': result['per_page'], 'pages': result['pages']},
    )


@bp.route('/yojanas/<slug>', methods=['GET'])
@limiter.limit('200 per minute')
def get_yojana(slug):
    try:
        item = content_service.get_yojana_by_slug(slug)
    except Exception:
        item = content_service.get_yojana_by_id(slug)
    return _ok(_serialize_yojana(item))


@bp.route('/yojanas', methods=['POST'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def create_yojana():
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.create_yojana(data)
    return _ok(_serialize_yojana(item), 201)


@bp.route('/yojanas/<yojana_id>', methods=['PUT'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def update_yojana(yojana_id):
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.update_yojana(yojana_id, data)
    return _ok(_serialize_yojana(item))


@bp.route('/yojanas/<yojana_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@limiter.limit('10 per minute')
def delete_yojana(yojana_id):
    content_service.delete_yojana(yojana_id)
    return _ok({'message': 'Yojana deleted successfully.'})


# ---------------------------------------------------------------------------
# Board Results
# ---------------------------------------------------------------------------

@bp.route('/board-results', methods=['GET'])
@limiter.limit('100 per minute')
def list_board_results():
    result = content_service.list_board_results(filters=_get_common_filters())
    return _ok(
        [_serialize_board_result(br) for br in result['items']],
        meta={'total': result['total'], 'page': result['page'],
              'per_page': result['per_page'], 'pages': result['pages']},
    )


@bp.route('/board-results/<board_result_id>', methods=['GET'])
@limiter.limit('200 per minute')
def get_board_result(board_result_id):
    item = content_service.get_board_result_by_id(board_result_id)
    return _ok(_serialize_board_result(item))


@bp.route('/board-results', methods=['POST'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def create_board_result():
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.create_board_result(data)
    return _ok(_serialize_board_result(item), 201)


@bp.route('/board-results/<board_result_id>', methods=['PUT'])
@jwt_required()
@operator_required
@limiter.limit('30 per minute')
def update_board_result(board_result_id):
    data = _get_json_body()
    if data is None:
        return _err(ErrorCode.VALIDATION_ERROR, 'Invalid request body.', 400)
    item = content_service.update_board_result(board_result_id, data)
    return _ok(_serialize_board_result(item))


@bp.route('/board-results/<board_result_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@limiter.limit('10 per minute')
def delete_board_result(board_result_id):
    content_service.delete_board_result(board_result_id)
    return _ok({'message': 'Board result deleted successfully.'})


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_common_filters() -> dict:
    """Parse common query-string filters shared by all content list endpoints."""
    from flask import request
    args = request.args
    filters = {}
    if args.get('status'):
        filters['status'] = args.get('status')
    if args.get('job_id'):
        filters['job_id'] = args.get('job_id')
    if args.get('featured'):
        filters['featured'] = args.get('featured', '').lower() in ('1', 'true', 'yes')
    if args.get('admission_type'):
        filters['admission_type'] = args.get('admission_type')
    if args.get('yojana_type'):
        filters['yojana_type'] = args.get('yojana_type')
    if args.get('state'):
        filters['state'] = args.get('state')
    if args.get('board_name'):
        filters['board_name'] = args.get('board_name')
    if args.get('class_'):
        filters['class_'] = args.get('class_')
    if args.get('exam_year'):
        filters['exam_year'] = args.get('exam_year')
    try:
        filters['page'] = max(1, int(args.get('page', 1)))
        filters['per_page'] = max(1, min(int(args.get('per_page', 20)), 100))
    except (TypeError, ValueError):
        filters['page'] = 1
        filters['per_page'] = 20
    return filters


def _get_json_body() -> dict | None:
    """Return request JSON body, or None if missing/invalid."""
    from flask import request
    return request.get_json(silent=True)
