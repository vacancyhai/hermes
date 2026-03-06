"""
Content models: Result, AdmitCard, AnswerKey, Admission, Yojana, BoardResult
"""
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.extensions import db


class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('job_vacancies.id', ondelete='SET NULL'))
    result_type = db.Column(db.String(50), nullable=False)
    result_phase = db.Column(db.String(100))
    result_title = db.Column(db.String(500), nullable=False)
    result_date = db.Column(db.Date)
    result_links = db.Column(JSONB, nullable=False, default=dict)
    cut_off_marks = db.Column(JSONB, nullable=False, default=dict)
    statistics = db.Column(JSONB, nullable=False, default=dict)
    is_final = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Result {self.result_title}>'


class AdmitCard(db.Model):
    __tablename__ = 'admit_cards'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('job_vacancies.id', ondelete='SET NULL'))
    exam_name = db.Column(db.String(500), nullable=False)
    exam_phase = db.Column(db.String(100))
    release_date = db.Column(db.Date)
    exam_date_start = db.Column(db.Date)
    exam_date_end = db.Column(db.Date)
    exam_mode = db.Column(db.String(50))
    download_link = db.Column(db.Text)
    exam_city_link = db.Column(db.Text)
    mock_test_link = db.Column(db.Text)
    instructions = db.Column(db.Text)
    reporting_time = db.Column(db.String(50))
    exam_timing = db.Column(db.String(100))
    important_documents = db.Column(ARRAY(db.Text))
    exam_centers = db.Column(ARRAY(db.Text))
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AdmitCard {self.exam_name}>'


class AnswerKey(db.Model):
    __tablename__ = 'answer_keys'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('job_vacancies.id', ondelete='SET NULL'))
    exam_name = db.Column(db.String(500), nullable=False)
    exam_phase = db.Column(db.String(100))
    paper_name = db.Column(db.String(255))
    release_date = db.Column(db.Date)
    answer_key_links = db.Column(JSONB, nullable=False, default=list)
    subject_wise_links = db.Column(JSONB, nullable=False, default=list)
    objection_start = db.Column(db.Date)
    objection_end = db.Column(db.Date)
    objection_fee = db.Column(db.Integer)
    objection_link = db.Column(db.Text)
    response_sheet_link = db.Column(db.Text)
    question_paper_link = db.Column(db.Text)
    total_questions = db.Column(db.Integer)
    status = db.Column(db.String(30), nullable=False, default='active')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AnswerKey {self.exam_name}>'


class Admission(db.Model):
    __tablename__ = 'admissions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(320), unique=True, nullable=False)
    admission_type = db.Column(db.String(30), nullable=False)
    course_name = db.Column(db.String(200))
    conducting_body = db.Column(db.String(200))
    total_seats = db.Column(db.Integer)
    description = db.Column(db.Text)
    eligibility = db.Column(JSONB)
    application_dates = db.Column(JSONB)
    application_fee = db.Column(JSONB)
    application_link = db.Column(db.Text)
    notification_pdf = db.Column(db.Text)
    syllabus_link = db.Column(db.Text)
    exam_pattern = db.Column(JSONB)
    selection_process = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='active')
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    views = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Admission {self.title}>'


class Yojana(db.Model):
    __tablename__ = 'yojanas'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(320), unique=True, nullable=False)
    yojana_type = db.Column(db.String(30), nullable=False)
    state = db.Column(db.String(100))
    department = db.Column(db.String(200))
    short_description = db.Column(db.Text)
    full_description = db.Column(db.Text)
    eligibility = db.Column(db.Text)
    benefits = db.Column(db.Text)
    benefit_amount = db.Column(db.String(100))
    installment_details = db.Column(db.Text)
    how_to_apply = db.Column(db.Text)
    required_documents = db.Column(ARRAY(db.Text))
    application_link = db.Column(db.Text)
    official_website = db.Column(db.Text)
    guidelines_pdf = db.Column(db.Text)
    helpline = db.Column(db.String(50))
    email = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    last_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    views = db.Column(db.Integer, nullable=False, default=0)
    applicants_count = db.Column(db.BigInteger, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Yojana {self.title}>'


class BoardResult(db.Model):
    __tablename__ = 'board_results'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_name = db.Column(db.String(100), nullable=False)
    class_ = db.Column('class', db.String(10), nullable=False)
    stream = db.Column(db.String(30))
    exam_year = db.Column(db.Integer, nullable=False)
    result_type = db.Column(db.String(30), nullable=False, default='regular')
    exam_start_date = db.Column(db.Date)
    exam_end_date = db.Column(db.Date)
    result_date = db.Column(db.Date)
    result_time = db.Column(db.String(20))
    result_link = db.Column(db.Text)
    marksheet_download_link = db.Column(db.Text)
    topper_list_link = db.Column(db.Text)
    date_sheet_link = db.Column(db.Text)
    statistics = db.Column(JSONB)
    how_to_check = db.Column(db.Text)
    alternative_links = db.Column(ARRAY(db.Text))
    status = db.Column(db.String(20), nullable=False, default='active')
    views = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BoardResult {self.board_name} {self.class_} {self.exam_year}>'
