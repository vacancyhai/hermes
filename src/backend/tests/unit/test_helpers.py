"""
Unit tests for app/utils/helpers.py

slugify()         — pure Python, no context needed.
success_response() — needs an active Flask app context (jsonify).
paginate()         — needs an active request context (reads request.args)
                     and a mock SQLAlchemy pagination object.
"""
from unittest.mock import MagicMock

import pytest
from flask import Flask


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def flask_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic_ascii(self):
        from app.utils.helpers import slugify
        assert slugify('SSC CGL 2024') == 'ssc-cgl-2024'

    def test_leading_trailing_spaces_stripped(self):
        from app.utils.helpers import slugify
        assert slugify('  UPSC  ') == 'upsc'

    def test_leading_trailing_hyphens_stripped(self):
        from app.utils.helpers import slugify
        assert slugify(' -- UPSC -- ') == 'upsc'

    def test_special_chars_become_hyphens(self):
        from app.utils.helpers import slugify
        assert slugify('UPSC (Civil Services)') == 'upsc-civil-services'

    def test_multiple_spaces_become_single_hyphen(self):
        from app.utils.helpers import slugify
        assert slugify('Railway   Recruitment') == 'railway-recruitment'

    def test_accented_chars_ascii_fallback(self):
        from app.utils.helpers import slugify
        # 'é' NFKD → e + combining acute → encode ascii ignore → 'e'
        assert slugify('café') == 'cafe'

    def test_non_ascii_only_returns_empty(self):
        from app.utils.helpers import slugify
        # Pure Devanagari has no ASCII equivalent
        assert slugify('रेलवे भर्ती') == ''

    def test_numbers_preserved(self):
        from app.utils.helpers import slugify
        assert slugify('UPSC 2024-25') == 'upsc-2024-25'

    def test_already_valid_slug_unchanged(self):
        from app.utils.helpers import slugify
        assert slugify('already-a-slug') == 'already-a-slug'

    def test_empty_string_returns_empty(self):
        from app.utils.helpers import slugify
        assert slugify('') == ''

    def test_whitespace_only_returns_empty(self):
        from app.utils.helpers import slugify
        assert slugify('   ') == ''

    def test_en_dash_stripped_chars_join(self):
        from app.utils.helpers import slugify
        # '–' (en-dash, U+2013) is non-ASCII; encode('ascii','ignore') drops it
        # entirely, so 'A–B' → 'ab' (no hyphen inserted between the letters).
        result = slugify('A–B')
        assert result == 'ab'


# ---------------------------------------------------------------------------
# success_response
# ---------------------------------------------------------------------------

class TestSuccessResponse:
    def test_default_200_status(self, flask_app):
        from app.utils.helpers import success_response
        with flask_app.app_context():
            response, status = success_response({'id': 1})
        assert status == 200

    def test_json_shape(self, flask_app):
        from app.utils.helpers import success_response
        with flask_app.app_context():
            response, status = success_response({'key': 'value'})
        data = response.get_json()
        assert data['success'] is True
        assert data['data'] == {'key': 'value'}

    def test_custom_status_code(self, flask_app):
        from app.utils.helpers import success_response
        with flask_app.app_context():
            _, status = success_response({}, status_code=201)
        assert status == 201

    def test_meta_merged_into_body(self, flask_app):
        from app.utils.helpers import success_response
        with flask_app.app_context():
            response, _ = success_response(
                [],
                meta={'total': 0, 'page': 1},
            )
        data = response.get_json()
        assert data['total'] == 0
        assert data['page'] == 1
        assert data['success'] is True

    def test_none_data_serialises(self, flask_app):
        from app.utils.helpers import success_response
        with flask_app.app_context():
            response, status = success_response(None)
        data = response.get_json()
        assert data['data'] is None
        assert status == 200


# ---------------------------------------------------------------------------
# paginate
# ---------------------------------------------------------------------------

def _make_mock_pagination(items=None, total=0, page=1, per_page=20, pages=1):
    """Return a MagicMock that looks like a Flask-SQLAlchemy Pagination object."""
    p = MagicMock()
    p.items = items if items is not None else []
    p.total = total
    p.page = page
    p.per_page = per_page
    p.pages = pages
    return p


def _make_mock_query(pagination):
    """Return a MagicMock query whose .paginate() returns the given pagination."""
    q = MagicMock()
    q.paginate.return_value = pagination
    return q


class TestPaginate:
    def test_returns_expected_dict_shape(self, flask_app):
        from app.utils.helpers import paginate
        pagination = _make_mock_pagination(items=['a', 'b'], total=2, page=1, per_page=20, pages=1)
        query = _make_mock_query(pagination)

        with flask_app.test_request_context('/'):
            result = paginate(query, page=1, per_page=20)

        assert result['items'] == ['a', 'b']
        assert result['total'] == 2
        assert result['page'] == 1
        assert result['per_page'] == 20
        assert result['pages'] == 1

    def test_per_page_capped_at_100(self, flask_app):
        from app.utils.helpers import paginate
        pagination = _make_mock_pagination()
        query = _make_mock_query(pagination)

        with flask_app.test_request_context('/'):
            paginate(query, page=1, per_page=999)

        _, call_kwargs = query.paginate.call_args
        assert call_kwargs['per_page'] == 100

    def test_reads_page_from_request_args(self, flask_app):
        from app.utils.helpers import paginate
        pagination = _make_mock_pagination(page=3, per_page=20)
        query = _make_mock_query(pagination)

        with flask_app.test_request_context('/?page=3&per_page=20'):
            paginate(query)  # no explicit args

        _, call_kwargs = query.paginate.call_args
        assert call_kwargs['page'] == 3

    def test_invalid_page_arg_defaults_to_1(self, flask_app):
        from app.utils.helpers import paginate
        pagination = _make_mock_pagination()
        query = _make_mock_query(pagination)

        with flask_app.test_request_context('/?page=abc'):
            paginate(query)

        _, call_kwargs = query.paginate.call_args
        assert call_kwargs['page'] == 1

    def test_per_page_minimum_is_1(self, flask_app):
        from app.utils.helpers import paginate
        pagination = _make_mock_pagination()
        query = _make_mock_query(pagination)

        with flask_app.test_request_context('/'):
            paginate(query, page=1, per_page=0)

        _, call_kwargs = query.paginate.call_args
        assert call_kwargs['per_page'] == 1
