"""
Unit tests for app/validators/job_validator.py

No Flask app context needed — Marshmallow schemas are pure Python.
"""
from datetime import date

import pytest
from marshmallow import ValidationError

from app.validators.job_validator import CreateJobSchema, JobSearchSchema, UpdateJobSchema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_payload(**overrides):
    """Return a minimal valid CreateJobSchema payload."""
    base = {
        'job_title': 'SSC CGL 2024',
        'organization': 'Staff Selection Commission',
        'job_type': 'latest_job',
        'eligibility': {'qualification': 'graduate'},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# CreateJobSchema
# ---------------------------------------------------------------------------

class TestCreateJobSchema:
    schema = CreateJobSchema()

    def test_minimal_valid_payload(self):
        data = self.schema.load(_base_payload())
        assert data['job_title'] == 'SSC CGL 2024'
        assert data['status'] == 'active'   # default
        assert data['is_featured'] is False  # default

    # Required field absence -------------------------------------------------

    def test_missing_job_title_raises(self):
        payload = _base_payload()
        del payload['job_title']
        with pytest.raises(ValidationError) as exc:
            self.schema.load(payload)
        assert 'job_title' in exc.value.messages

    def test_missing_organization_raises(self):
        payload = _base_payload()
        del payload['organization']
        with pytest.raises(ValidationError) as exc:
            self.schema.load(payload)
        assert 'organization' in exc.value.messages

    def test_missing_job_type_raises(self):
        payload = _base_payload()
        del payload['job_type']
        with pytest.raises(ValidationError) as exc:
            self.schema.load(payload)
        assert 'job_type' in exc.value.messages

    def test_missing_eligibility_raises(self):
        payload = _base_payload()
        del payload['eligibility']
        with pytest.raises(ValidationError) as exc:
            self.schema.load(payload)
        assert 'eligibility' in exc.value.messages

    # OneOf validation -------------------------------------------------------

    def test_invalid_job_type_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(job_type='unknown_type'))
        assert 'job_type' in exc.value.messages

    def test_all_valid_job_types(self):
        for jt in ('latest_job', 'result', 'admit_card', 'answer_key', 'admission', 'yojana'):
            data = self.schema.load(_base_payload(job_type=jt))
            assert data['job_type'] == jt

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(status='invalid'))
        assert 'status' in exc.value.messages

    def test_invalid_qualification_level_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(qualification_level='phd'))
        assert 'qualification_level' in exc.value.messages

    def test_valid_qualification_level(self):
        data = self.schema.load(_base_payload(qualification_level='graduate'))
        assert data['qualification_level'] == 'graduate'

    # Cross-field date validation --------------------------------------------

    def test_application_end_before_start_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(
                application_start=date(2024, 6, 1),
                application_end=date(2024, 5, 31),
            ))
        assert 'application_end' in exc.value.messages

    def test_application_same_start_end_valid(self):
        data = self.schema.load(_base_payload(
            application_start=date(2024, 6, 1),
            application_end=date(2024, 6, 1),
        ))
        assert data['application_start'] == date(2024, 6, 1)

    def test_application_end_after_start_valid(self):
        data = self.schema.load(_base_payload(
            application_start=date(2024, 6, 1),
            application_end=date(2024, 7, 31),
        ))
        assert data['application_end'] == date(2024, 7, 31)

    # Cross-field salary validation ------------------------------------------

    def test_salary_max_less_than_initial_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(salary_initial=50000, salary_max=30000))
        assert 'salary_max' in exc.value.messages

    def test_salary_max_equal_to_initial_valid(self):
        data = self.schema.load(_base_payload(salary_initial=50000, salary_max=50000))
        assert data['salary_max'] == 50000

    def test_salary_max_greater_than_initial_valid(self):
        data = self.schema.load(_base_payload(salary_initial=30000, salary_max=80000))
        assert data['salary_max'] == 80000

    # Range validation -------------------------------------------------------

    def test_negative_total_vacancies_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(total_vacancies=-1))
        assert 'total_vacancies' in exc.value.messages

    def test_negative_salary_initial_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(salary_initial=-100))
        assert 'salary_initial' in exc.value.messages

    def test_priority_out_of_range_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(priority=101))
        assert 'priority' in exc.value.messages

    # Unknown fields ---------------------------------------------------------

    def test_unknown_field_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(extra_field='bad'))
        assert 'extra_field' in exc.value.messages

    # slug must not be accepted ----------------------------------------------

    def test_slug_field_not_accepted(self):
        """slug is server-generated — client supplying it must be rejected."""
        with pytest.raises(ValidationError) as exc:
            self.schema.load(_base_payload(slug='injected-slug'))
        assert 'slug' in exc.value.messages


# ---------------------------------------------------------------------------
# UpdateJobSchema
# ---------------------------------------------------------------------------

class TestUpdateJobSchema:
    schema = UpdateJobSchema()

    def test_empty_payload_valid(self):
        """All fields optional for updates."""
        data = self.schema.load({})
        assert data.get('job_title') is None

    def test_partial_update_valid(self):
        data = self.schema.load({'status': 'closed', 'is_featured': True})
        assert data['status'] == 'closed'
        assert data['is_featured'] is True

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'status': 'invalid'})
        assert 'status' in exc.value.messages

    def test_cross_field_date_validation_still_applies(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({
                'application_start': date(2024, 6, 1),
                'application_end': date(2024, 5, 1),
            })
        assert 'application_end' in exc.value.messages

    def test_cross_field_salary_validation_still_applies(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'salary_initial': 60000, 'salary_max': 40000})
        assert 'salary_max' in exc.value.messages


# ---------------------------------------------------------------------------
# JobSearchSchema
# ---------------------------------------------------------------------------

class TestJobSearchSchema:
    schema = JobSearchSchema()

    def test_empty_query_uses_defaults(self):
        data = self.schema.load({})
        assert data['page'] == 1
        assert data['per_page'] == 20
        assert data['q'] is None
        assert data['status'] is None
        assert data['job_type'] is None

    def test_valid_filters(self):
        data = self.schema.load({
            'job_type': 'result',
            'status': 'active',
            'page': 2,
            'per_page': 50,
            'q': 'railway',
        })
        assert data['job_type'] == 'result'
        assert data['page'] == 2
        assert data['q'] == 'railway'

    def test_per_page_exceeds_100_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'per_page': 200})
        assert 'per_page' in exc.value.messages

    def test_page_zero_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'page': 0})
        assert 'page' in exc.value.messages

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'status': 'bogus'})
        assert 'status' in exc.value.messages

    def test_invalid_job_type_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'job_type': 'unknown'})
        assert 'job_type' in exc.value.messages

    def test_invalid_qualification_level_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'qualification_level': 'phd'})
        assert 'qualification_level' in exc.value.messages

    def test_unknown_field_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'unknown_param': 'value'})
        assert 'unknown_param' in exc.value.messages
