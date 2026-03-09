"""
Marshmallow schemas for job vacancy endpoint input validation.

CreateJobSchema  — POST /api/v1/admin/jobs
UpdateJobSchema  — PUT  /api/v1/admin/jobs/<id>   (all required fields become optional)
JobSearchSchema  — GET  /api/v1/jobs              (query-string parameters)

Note: 'slug' is intentionally absent from Create/UpdateJobSchema.
      It is generated server-side by helpers.slugify(job_title) — never accepted from
      the client to prevent arbitrary slug injection.
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError, RAISE

from app.utils.constants import JobStatus, JobType, QualificationLevel


class CreateJobSchema(Schema):
    class Meta:
        unknown = RAISE

    # --- Required fields (map to NOT NULL columns without safe DB defaults) ---
    job_title = fields.String(required=True, validate=validate.Length(min=1, max=500))
    organization = fields.String(required=True, validate=validate.Length(min=1, max=255))
    job_type = fields.String(
        required=True,
        validate=validate.OneOf(JobType.ALL, error='Invalid job_type.'),
    )
    eligibility = fields.Dict(required=True)

    # --- Optional fields ---
    department = fields.String(
        required=False, load_default=None, validate=validate.Length(max=255),
    )
    post_code = fields.String(
        required=False, load_default=None, validate=validate.Length(max=100),
    )
    employment_type = fields.String(
        required=False,
        load_default='permanent',
        validate=validate.OneOf(['permanent', 'contractual', 'temporary', 'deputation']),
    )
    qualification_level = fields.String(
        required=False,
        load_default=None,
        validate=validate.OneOf(QualificationLevel.ALL, error='Invalid qualification_level.'),
    )
    total_vacancies = fields.Integer(
        required=False, load_default=None, validate=validate.Range(min=0),
    )
    vacancy_breakdown = fields.Dict(required=False, load_default=dict)
    description = fields.String(required=False, load_default=None)
    short_description = fields.String(
        required=False, load_default=None, validate=validate.Length(max=500),
    )
    application_details = fields.Dict(required=False, load_default=dict)
    notification_date = fields.Date(required=False, load_default=None)
    application_start = fields.Date(required=False, load_default=None)
    application_end = fields.Date(required=False, load_default=None)
    last_date_fee = fields.Date(required=False, load_default=None)
    exam_start = fields.Date(required=False, load_default=None)
    exam_end = fields.Date(required=False, load_default=None)
    result_date = fields.Date(required=False, load_default=None)
    exam_details = fields.Dict(required=False, load_default=dict)
    salary_initial = fields.Integer(
        required=False, load_default=None, validate=validate.Range(min=0),
    )
    salary_max = fields.Integer(
        required=False, load_default=None, validate=validate.Range(min=0),
    )
    salary = fields.Dict(required=False, load_default=dict)
    selection_process = fields.List(fields.String(), required=False, load_default=list)
    documents_required = fields.List(fields.String(), required=False, load_default=list)
    status = fields.String(
        required=False,
        load_default=JobStatus.ACTIVE,
        validate=validate.OneOf(JobStatus.ALL, error='Invalid status.'),
    )
    is_featured = fields.Boolean(required=False, load_default=False)
    is_urgent = fields.Boolean(required=False, load_default=False)
    is_trending = fields.Boolean(required=False, load_default=False)
    priority = fields.Integer(
        required=False, load_default=0, validate=validate.Range(min=0, max=100),
    )
    meta_title = fields.String(
        required=False, load_default=None, validate=validate.Length(max=500),
    )
    meta_description = fields.String(required=False, load_default=None)

    @validates_schema
    def validate_date_and_salary_ranges(self, data, **kwargs):
        app_start = data.get('application_start')
        app_end = data.get('application_end')
        if app_start and app_end and app_end < app_start:
            raise ValidationError(
                'application_end must be on or after application_start.',
                field_name='application_end',
            )

        sal_min = data.get('salary_initial')
        sal_max = data.get('salary_max')
        if sal_min is not None and sal_max is not None and sal_max < sal_min:
            raise ValidationError(
                'salary_max must be greater than or equal to salary_initial.',
                field_name='salary_max',
            )


class UpdateJobSchema(CreateJobSchema):
    """
    Same validation rules as CreateJobSchema but every field is optional,
    allowing partial updates (PATCH-style PUT).
    """
    job_title = fields.String(
        required=False, load_default=None, validate=validate.Length(min=1, max=500),
    )
    organization = fields.String(
        required=False, load_default=None, validate=validate.Length(min=1, max=255),
    )
    job_type = fields.String(
        required=False,
        load_default=None,
        validate=validate.OneOf(JobType.ALL, error='Invalid job_type.'),
    )
    eligibility = fields.Dict(required=False, load_default=None)


class JobSearchSchema(Schema):
    """
    Query-string parameters for GET /api/v1/jobs.
    All fields optional; marshmallow coerces string args to declared types.
    """
    class Meta:
        unknown = RAISE

    q = fields.String(required=False, load_default=None, validate=validate.Length(max=100))
    organization = fields.String(required=False, load_default=None, validate=validate.Length(max=100))
    qualification_level = fields.String(
        required=False,
        load_default=None,
        validate=validate.OneOf(QualificationLevel.ALL, error='Invalid qualification_level.'),
    )
    job_type = fields.String(
        required=False,
        load_default=None,
        validate=validate.OneOf(JobType.ALL, error='Invalid job_type.'),
    )
    featured = fields.Boolean(required=False, load_default=None)
    urgent = fields.Boolean(required=False, load_default=None)
    page = fields.Integer(
        required=False, load_default=1, validate=validate.Range(min=1),
    )
    per_page = fields.Integer(
        required=False, load_default=20, validate=validate.Range(min=1, max=100),
    )
