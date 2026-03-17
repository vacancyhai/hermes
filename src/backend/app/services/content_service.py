"""
Content Service — CRUD for all 6 content types.

Content types handled:
    Result       — exam results with cutoff marks and statistics
    AdmitCard    — hall tickets with exam dates and download links
    AnswerKey    — answer keys with objection windows
    Admission    — college/university admissions (JEE, NEET, etc.)
    Yojana       — government schemes/programmes
    BoardResult  — class 10/12 board examination results

Public API follows the same pattern as job_service.py:
    list_<type>(filters)              → paginated dict
    get_<type>_by_id(id)             → model instance (raises NotFoundError)
    create_<type>(data)              → model instance
    update_<type>(id, data)          → model instance
    delete_<type>(id)                → None  (soft-delete: status → 'expired')

All functions raise custom exceptions (NotFoundError, ValidationError) which
are automatically converted to appropriate HTTP responses by the error handler
middleware.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.extensions import db
from app.middleware.error_handler import NotFoundError
from app.models.content import (
    AdmitCard,
    Admission,
    AnswerKey,
    BoardResult,
    Result,
    Yojana,
)
from app.utils.helpers import paginate, slugify

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _apply_common_filters(query, model, filters: dict):
    """Apply status and featured filters shared by several content types."""
    status = filters.get('status', 'active')
    if status:
        query = query.filter(model.status == status)

    if filters.get('featured'):
        if hasattr(model, 'is_featured'):
            query = query.filter(model.is_featured.is_(True))

    return query


def _set_fields(instance, data: dict, allowed: tuple) -> None:
    """Set only the allowed fields from data onto an ORM instance."""
    for field in allowed:
        value = data.get(field)
        if value is not None:
            setattr(instance, field, value)


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

_RESULT_FIELDS = (
    'job_id', 'result_type', 'result_phase', 'result_title',
    'result_date', 'result_links', 'cut_off_marks', 'statistics',
    'is_final', 'status',
)


def list_results(filters: dict) -> dict:
    """Return paginated list of results."""
    query = Result.query
    status = filters.get('status', 'active')
    if status:
        query = query.filter(Result.status == status)
    if filters.get('job_id'):
        query = query.filter(Result.job_id == filters['job_id'])
    query = query.order_by(Result.created_at.desc())
    return paginate(query, page=filters.get('page', 1), per_page=min(filters.get('per_page', 20), 100))


def get_result_by_id(result_id: str) -> Result:
    """Fetch a Result by UUID, raises NotFoundError if missing."""
    result = db.session.get(Result, result_id)
    if not result:
        raise NotFoundError("Result not found")
    return result


def create_result(data: dict) -> Result:
    """Create and persist a new Result row."""
    result = Result(
        result_type=data['result_type'],
        result_title=data['result_title'],
        job_id=data.get('job_id'),
        result_phase=data.get('result_phase'),
        result_date=data.get('result_date'),
        result_links=data.get('result_links') or {},
        cut_off_marks=data.get('cut_off_marks') or {},
        statistics=data.get('statistics') or {},
        is_final=data.get('is_final', False),
        status=data.get('status', 'active'),
    )
    db.session.add(result)
    db.session.commit()
    return result


def update_result(result_id: str, data: dict) -> Result:
    """Partially update a Result."""
    result = get_result_by_id(result_id)
    _set_fields(result, data, _RESULT_FIELDS)
    result.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return result


def delete_result(result_id: str) -> None:
    """Soft-delete a result by setting status to 'cancelled'."""
    result = get_result_by_id(result_id)
    result.status = 'cancelled'
    result.updated_at = datetime.now(timezone.utc)
    db.session.commit()


# ---------------------------------------------------------------------------
# AdmitCard
# ---------------------------------------------------------------------------

_ADMIT_CARD_FIELDS = (
    'job_id', 'exam_name', 'exam_phase', 'release_date',
    'exam_date_start', 'exam_date_end', 'exam_mode', 'download_link',
    'exam_city_link', 'mock_test_link', 'instructions',
    'reporting_time', 'exam_timing', 'important_documents',
    'exam_centers', 'status',
)


def list_admit_cards(filters: dict) -> dict:
    """Return paginated list of admit cards."""
    query = AdmitCard.query
    status = filters.get('status', 'active')
    if status:
        query = query.filter(AdmitCard.status == status)
    if filters.get('job_id'):
        query = query.filter(AdmitCard.job_id == filters['job_id'])
    query = query.order_by(AdmitCard.created_at.desc())
    return paginate(query, page=filters.get('page', 1), per_page=min(filters.get('per_page', 20), 100))


def get_admit_card_by_id(admit_card_id: str) -> AdmitCard:
    """Fetch an AdmitCard by UUID, raises NotFoundError if missing."""
    admit_card = db.session.get(AdmitCard, admit_card_id)
    if not admit_card:
        raise NotFoundError("Admit card not found")
    return admit_card


def create_admit_card(data: dict) -> AdmitCard:
    """Create and persist a new AdmitCard row."""
    admit_card = AdmitCard(
        exam_name=data['exam_name'],
        job_id=data.get('job_id'),
        exam_phase=data.get('exam_phase'),
        release_date=data.get('release_date'),
        exam_date_start=data.get('exam_date_start'),
        exam_date_end=data.get('exam_date_end'),
        exam_mode=data.get('exam_mode'),
        download_link=data.get('download_link'),
        exam_city_link=data.get('exam_city_link'),
        mock_test_link=data.get('mock_test_link'),
        instructions=data.get('instructions'),
        reporting_time=data.get('reporting_time'),
        exam_timing=data.get('exam_timing'),
        important_documents=data.get('important_documents') or [],
        exam_centers=data.get('exam_centers') or [],
        status=data.get('status', 'active'),
    )
    db.session.add(admit_card)
    db.session.commit()
    return admit_card


def update_admit_card(admit_card_id: str, data: dict) -> AdmitCard:
    """Partially update an AdmitCard."""
    admit_card = get_admit_card_by_id(admit_card_id)
    _set_fields(admit_card, data, _ADMIT_CARD_FIELDS)
    admit_card.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return admit_card


def delete_admit_card(admit_card_id: str) -> None:
    """Soft-delete an admit card by setting status to 'expired'."""
    admit_card = get_admit_card_by_id(admit_card_id)
    admit_card.status = 'expired'
    admit_card.updated_at = datetime.now(timezone.utc)
    db.session.commit()


# ---------------------------------------------------------------------------
# AnswerKey
# ---------------------------------------------------------------------------

_ANSWER_KEY_FIELDS = (
    'job_id', 'exam_name', 'exam_phase', 'paper_name', 'release_date',
    'answer_key_links', 'subject_wise_links', 'objection_start',
    'objection_end', 'objection_fee', 'objection_link',
    'response_sheet_link', 'question_paper_link', 'total_questions', 'status',
)


def list_answer_keys(filters: dict) -> dict:
    """Return paginated list of answer keys."""
    query = AnswerKey.query
    status = filters.get('status', 'active')
    if status:
        query = query.filter(AnswerKey.status == status)
    if filters.get('job_id'):
        query = query.filter(AnswerKey.job_id == filters['job_id'])
    query = query.order_by(AnswerKey.created_at.desc())
    return paginate(query, page=filters.get('page', 1), per_page=min(filters.get('per_page', 20), 100))


def get_answer_key_by_id(answer_key_id: str) -> AnswerKey:
    """Fetch an AnswerKey by UUID, raises NotFoundError if missing."""
    answer_key = db.session.get(AnswerKey, answer_key_id)
    if not answer_key:
        raise NotFoundError("Answer key not found")
    return answer_key


def create_answer_key(data: dict) -> AnswerKey:
    """Create and persist a new AnswerKey row."""
    answer_key = AnswerKey(
        exam_name=data['exam_name'],
        job_id=data.get('job_id'),
        exam_phase=data.get('exam_phase'),
        paper_name=data.get('paper_name'),
        release_date=data.get('release_date'),
        answer_key_links=data.get('answer_key_links') or [],
        subject_wise_links=data.get('subject_wise_links') or [],
        objection_start=data.get('objection_start'),
        objection_end=data.get('objection_end'),
        objection_fee=data.get('objection_fee'),
        objection_link=data.get('objection_link'),
        response_sheet_link=data.get('response_sheet_link'),
        question_paper_link=data.get('question_paper_link'),
        total_questions=data.get('total_questions'),
        status=data.get('status', 'active'),
    )
    db.session.add(answer_key)
    db.session.commit()
    return answer_key


def update_answer_key(answer_key_id: str, data: dict) -> AnswerKey:
    """Partially update an AnswerKey."""
    answer_key = get_answer_key_by_id(answer_key_id)
    _set_fields(answer_key, data, _ANSWER_KEY_FIELDS)
    answer_key.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return answer_key


def delete_answer_key(answer_key_id: str) -> None:
    """Soft-delete an answer key by setting status to 'expired'."""
    answer_key = get_answer_key_by_id(answer_key_id)
    answer_key.status = 'expired'
    answer_key.updated_at = datetime.now(timezone.utc)
    db.session.commit()


# ---------------------------------------------------------------------------
# Admission
# ---------------------------------------------------------------------------

_ADMISSION_FIELDS = (
    'title', 'slug', 'admission_type', 'course_name', 'conducting_body',
    'total_seats', 'description', 'eligibility', 'application_dates',
    'application_fee', 'application_link', 'notification_pdf',
    'syllabus_link', 'exam_pattern', 'selection_process',
    'status', 'is_featured',
)


def list_admissions(filters: dict) -> dict:
    """Return paginated list of admissions."""
    query = Admission.query
    status = filters.get('status', 'active')
    if status:
        query = query.filter(Admission.status == status)
    if filters.get('admission_type'):
        query = query.filter(Admission.admission_type == filters['admission_type'])
    if filters.get('featured'):
        query = query.filter(Admission.is_featured.is_(True))
    query = query.order_by(Admission.created_at.desc())
    return paginate(query, page=filters.get('page', 1), per_page=min(filters.get('per_page', 20), 100))


def get_admission_by_id(admission_id: str) -> Admission:
    """Fetch an Admission by UUID, raises NotFoundError if missing."""
    admission = db.session.get(Admission, admission_id)
    if not admission:
        raise NotFoundError("Admission not found")
    return admission


def get_admission_by_slug(slug: str) -> Admission:
    """Fetch an Admission by slug, raises NotFoundError if missing."""
    admission = Admission.query.filter_by(slug=slug, status='active').first()
    if not admission:
        raise NotFoundError("Admission not found")
    return admission


def create_admission(data: dict) -> Admission:
    """Create and persist a new Admission row. Slug auto-generated from title."""
    slug = data.get('slug') or slugify(data['title'])
    # Ensure slug uniqueness
    if Admission.query.filter_by(slug=slug).first():
        import uuid as _uuid
        slug = f"{slug}-{_uuid.uuid4().hex[:8]}"

    admission = Admission(
        title=data['title'],
        slug=slug,
        admission_type=data['admission_type'],
        course_name=data.get('course_name'),
        conducting_body=data.get('conducting_body'),
        total_seats=data.get('total_seats'),
        description=data.get('description'),
        eligibility=data.get('eligibility'),
        application_dates=data.get('application_dates'),
        application_fee=data.get('application_fee'),
        application_link=data.get('application_link'),
        notification_pdf=data.get('notification_pdf'),
        syllabus_link=data.get('syllabus_link'),
        exam_pattern=data.get('exam_pattern'),
        selection_process=data.get('selection_process'),
        status=data.get('status', 'active'),
        is_featured=data.get('is_featured', False),
    )
    db.session.add(admission)
    db.session.commit()
    return admission


def update_admission(admission_id: str, data: dict) -> Admission:
    """Partially update an Admission."""
    admission = get_admission_by_id(admission_id)
    _set_fields(admission, data, _ADMISSION_FIELDS)
    admission.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return admission


def delete_admission(admission_id: str) -> None:
    """Soft-delete an admission by setting status to 'expired'."""
    admission = get_admission_by_id(admission_id)
    admission.status = 'expired'
    admission.updated_at = datetime.now(timezone.utc)
    db.session.commit()


# ---------------------------------------------------------------------------
# Yojana
# ---------------------------------------------------------------------------

_YOJANA_FIELDS = (
    'title', 'slug', 'yojana_type', 'state', 'department',
    'short_description', 'full_description', 'eligibility', 'benefits',
    'benefit_amount', 'installment_details', 'how_to_apply',
    'required_documents', 'application_link', 'official_website',
    'guidelines_pdf', 'helpline', 'email', 'start_date', 'last_date',
    'is_active', 'status', 'is_featured',
)


def list_yojanas(filters: dict) -> dict:
    """Return paginated list of yojanas."""
    query = Yojana.query
    status = filters.get('status', 'active')
    if status:
        query = query.filter(Yojana.status == status)
    if filters.get('yojana_type'):
        query = query.filter(Yojana.yojana_type == filters['yojana_type'])
    if filters.get('state'):
        query = query.filter(Yojana.state == filters['state'])
    if filters.get('featured'):
        query = query.filter(Yojana.is_featured.is_(True))
    query = query.order_by(Yojana.created_at.desc())
    return paginate(query, page=filters.get('page', 1), per_page=min(filters.get('per_page', 20), 100))


def get_yojana_by_id(yojana_id: str) -> Yojana:
    """Fetch a Yojana by UUID, raises NotFoundError if missing."""
    yojana = db.session.get(Yojana, yojana_id)
    if not yojana:
        raise NotFoundError("Yojana not found")
    return yojana


def get_yojana_by_slug(slug: str) -> Yojana:
    """Fetch a Yojana by slug, raises NotFoundError if missing."""
    yojana = Yojana.query.filter_by(slug=slug, status='active').first()
    if not yojana:
        raise NotFoundError("Yojana not found")
    return yojana


def create_yojana(data: dict) -> Yojana:
    """Create and persist a new Yojana row. Slug auto-generated from title."""
    slug = data.get('slug') or slugify(data['title'])
    if Yojana.query.filter_by(slug=slug).first():
        import uuid as _uuid
        slug = f"{slug}-{_uuid.uuid4().hex[:8]}"

    yojana = Yojana(
        title=data['title'],
        slug=slug,
        yojana_type=data['yojana_type'],
        state=data.get('state'),
        department=data.get('department'),
        short_description=data.get('short_description'),
        full_description=data.get('full_description'),
        eligibility=data.get('eligibility'),
        benefits=data.get('benefits'),
        benefit_amount=data.get('benefit_amount'),
        installment_details=data.get('installment_details'),
        how_to_apply=data.get('how_to_apply'),
        required_documents=data.get('required_documents') or [],
        application_link=data.get('application_link'),
        official_website=data.get('official_website'),
        guidelines_pdf=data.get('guidelines_pdf'),
        helpline=data.get('helpline'),
        email=data.get('email'),
        start_date=data.get('start_date'),
        last_date=data.get('last_date'),
        is_active=data.get('is_active', True),
        status=data.get('status', 'active'),
        is_featured=data.get('is_featured', False),
    )
    db.session.add(yojana)
    db.session.commit()
    return yojana


def update_yojana(yojana_id: str, data: dict) -> Yojana:
    """Partially update a Yojana."""
    yojana = get_yojana_by_id(yojana_id)
    _set_fields(yojana, data, _YOJANA_FIELDS)
    yojana.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return yojana


def delete_yojana(yojana_id: str) -> None:
    """Soft-delete a yojana by setting status to 'expired' and is_active to False."""
    yojana = get_yojana_by_id(yojana_id)
    yojana.status = 'expired'
    yojana.is_active = False
    yojana.updated_at = datetime.now(timezone.utc)
    db.session.commit()


# ---------------------------------------------------------------------------
# BoardResult
# ---------------------------------------------------------------------------

_BOARD_RESULT_FIELDS = (
    'board_name', 'class_', 'stream', 'exam_year', 'result_type',
    'exam_start_date', 'exam_end_date', 'result_date', 'result_time',
    'result_link', 'marksheet_download_link', 'topper_list_link',
    'date_sheet_link', 'statistics', 'how_to_check',
    'alternative_links', 'status',
)


def list_board_results(filters: dict) -> dict:
    """Return paginated list of board results."""
    query = BoardResult.query
    status = filters.get('status', 'active')
    if status:
        query = query.filter(BoardResult.status == status)
    if filters.get('board_name'):
        query = query.filter(BoardResult.board_name == filters['board_name'])
    if filters.get('class_'):
        query = query.filter(BoardResult.class_ == filters['class_'])
    if filters.get('exam_year'):
        query = query.filter(BoardResult.exam_year == int(filters['exam_year']))
    query = query.order_by(BoardResult.exam_year.desc(), BoardResult.created_at.desc())
    return paginate(query, page=filters.get('page', 1), per_page=min(filters.get('per_page', 20), 100))


def get_board_result_by_id(board_result_id: str) -> BoardResult:
    """Fetch a BoardResult by UUID, raises NotFoundError if missing."""
    board_result = db.session.get(BoardResult, board_result_id)
    if not board_result:
        raise NotFoundError("Board result not found")
    return board_result


def create_board_result(data: dict) -> BoardResult:
    """Create and persist a new BoardResult row."""
    board_result = BoardResult(
        board_name=data['board_name'],
        class_=data['class_'],
        exam_year=data['exam_year'],
        stream=data.get('stream'),
        result_type=data.get('result_type', 'regular'),
        exam_start_date=data.get('exam_start_date'),
        exam_end_date=data.get('exam_end_date'),
        result_date=data.get('result_date'),
        result_time=data.get('result_time'),
        result_link=data.get('result_link'),
        marksheet_download_link=data.get('marksheet_download_link'),
        topper_list_link=data.get('topper_list_link'),
        date_sheet_link=data.get('date_sheet_link'),
        statistics=data.get('statistics'),
        how_to_check=data.get('how_to_check'),
        alternative_links=data.get('alternative_links') or [],
        status=data.get('status', 'active'),
    )
    db.session.add(board_result)
    db.session.commit()
    return board_result


def update_board_result(board_result_id: str, data: dict) -> BoardResult:
    """Partially update a BoardResult."""
    board_result = get_board_result_by_id(board_result_id)
    # Handle 'class_' mapping separately since it's a reserved keyword
    if 'class_' in data and data['class_'] is not None:
        board_result.class_ = data['class_']
    _set_fields(board_result, data, tuple(f for f in _BOARD_RESULT_FIELDS if f != 'class_'))
    board_result.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return board_result


def delete_board_result(board_result_id: str) -> None:
    """Soft-delete a board result by setting status to 'expired'."""
    board_result = get_board_result_by_id(board_result_id)
    board_result.status = 'expired'
    board_result.updated_at = datetime.now(timezone.utc)
    db.session.commit()
