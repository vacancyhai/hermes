"""
Unit tests for app/validators/auth_validator.py

No Flask app context needed — Marshmallow schemas are pure Python.
"""
import pytest
from marshmallow import ValidationError

from app.validators.auth_validator import (
    LoginSchema,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    RegisterSchema,
)


# ---------------------------------------------------------------------------
# RegisterSchema
# ---------------------------------------------------------------------------

class TestRegisterSchema:
    schema = RegisterSchema()

    def test_valid_data(self):
        data = self.schema.load({
            'email': 'user@example.com',
            'password': 'securepass123',
            'full_name': 'Jane Doe',
        })
        assert data['email'] == 'user@example.com'
        assert data['full_name'] == 'Jane Doe'

    def test_missing_email_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'password': 'securepass123', 'full_name': 'Jane'})
        assert 'email' in exc.value.messages

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'email': 'not-an-email', 'password': 'securepass123', 'full_name': 'Jane'})
        assert 'email' in exc.value.messages

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'email': 'u@e.com', 'password': 'short', 'full_name': 'Jane'})
        assert 'password' in exc.value.messages

    def test_password_too_long_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'email': 'u@e.com', 'password': 'x' * 129, 'full_name': 'Jane'})
        assert 'password' in exc.value.messages

    def test_missing_full_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'email': 'u@e.com', 'password': 'securepass123'})
        assert 'full_name' in exc.value.messages

    def test_blank_full_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'email': 'u@e.com', 'password': 'securepass123', 'full_name': ' '})
        assert 'full_name' in exc.value.messages

    def test_unknown_field_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({
                'email': 'u@e.com',
                'password': 'securepass123',
                'full_name': 'Jane',
                'extra_field': 'should fail',
            })
        assert 'extra_field' in exc.value.messages

    def test_email_max_length_raises(self):
        long_email = 'a' * 250 + '@x.com'
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'email': long_email, 'password': 'securepass123', 'full_name': 'Jane'})
        assert 'email' in exc.value.messages

    def test_password_exact_min_length_ok(self):
        data = self.schema.load({'email': 'u@e.com', 'password': '12345678', 'full_name': 'Jane'})
        assert 'password' in data

    def test_password_exact_max_length_ok(self):
        data = self.schema.load({'email': 'u@e.com', 'password': 'x' * 128, 'full_name': 'Jane'})
        assert 'password' in data


# ---------------------------------------------------------------------------
# LoginSchema
# ---------------------------------------------------------------------------

class TestLoginSchema:
    schema = LoginSchema()

    def test_valid_data(self):
        data = self.schema.load({'email': 'user@example.com', 'password': 'anypass'})
        assert data['email'] == 'user@example.com'

    def test_missing_password_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'email': 'u@e.com'})
        assert 'password' in exc.value.messages

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            self.schema.load({'email': 'bad', 'password': 'pass'})

    def test_unknown_field_raises(self):
        with pytest.raises(ValidationError):
            self.schema.load({'email': 'u@e.com', 'password': 'pass', 'role': 'admin'})


# ---------------------------------------------------------------------------
# PasswordResetRequestSchema
# ---------------------------------------------------------------------------

class TestPasswordResetRequestSchema:
    schema = PasswordResetRequestSchema()

    def test_valid_email(self):
        data = self.schema.load({'email': 'reset@example.com'})
        assert data['email'] == 'reset@example.com'

    def test_missing_email_raises(self):
        with pytest.raises(ValidationError):
            self.schema.load({})

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            self.schema.load({'email': 'not-valid'})


# ---------------------------------------------------------------------------
# PasswordResetSchema
# ---------------------------------------------------------------------------

class TestPasswordResetSchema:
    schema = PasswordResetSchema()

    def test_valid_data(self):
        data = self.schema.load({'token': 'abc123', 'new_password': 'newpassword1'})
        assert data['token'] == 'abc123'

    def test_missing_token_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'new_password': 'newpassword1'})
        assert 'token' in exc.value.messages

    def test_short_new_password_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'token': 'abc123', 'new_password': 'short'})
        assert 'new_password' in exc.value.messages

    def test_long_new_password_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'token': 'abc123', 'new_password': 'x' * 129})
        assert 'new_password' in exc.value.messages
