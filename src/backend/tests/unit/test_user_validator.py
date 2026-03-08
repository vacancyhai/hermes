"""
Unit tests for app/validators/user_validator.py

No Flask app context needed — Marshmallow schemas are pure Python.
"""
import pytest
from marshmallow import ValidationError

from app.validators.user_validator import UpdatePhoneSchema, UpdateProfileSchema


# ---------------------------------------------------------------------------
# UpdateProfileSchema
# ---------------------------------------------------------------------------

class TestUpdateProfileSchema:
    schema = UpdateProfileSchema()

    def test_empty_payload_is_valid(self):
        """All fields are optional — empty dict must not raise."""
        data = self.schema.load({})
        assert data.get('gender') is None
        assert data.get('category') is None
        assert data.get('pincode') is None

    def test_valid_full_payload(self):
        data = self.schema.load({
            'gender': 'male',
            'category': 'general',
            'state': 'Maharashtra',
            'city': 'Mumbai',
            'pincode': '400001',
            'highest_qualification': 'graduate',
            'is_pwd': False,
            'is_ex_serviceman': False,
        })
        assert data['gender'] == 'male'
        assert data['state'] == 'Maharashtra'
        assert data['pincode'] == '400001'

    def test_invalid_gender_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'gender': 'unknown'})
        assert 'gender' in exc.value.messages

    def test_invalid_category_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'category': 'invalid'})
        assert 'category' in exc.value.messages

    def test_all_valid_categories(self):
        for cat in ('general', 'obc', 'sc', 'st'):
            data = self.schema.load({'category': cat})
            assert data['category'] == cat

    def test_pincode_non_digits_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'pincode': 'abc123'})
        assert 'pincode' in exc.value.messages

    def test_pincode_five_digits_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'pincode': '12345'})
        assert 'pincode' in exc.value.messages

    def test_pincode_seven_digits_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'pincode': '1234567'})
        assert 'pincode' in exc.value.messages

    def test_pincode_exactly_six_digits_valid(self):
        data = self.schema.load({'pincode': '110001'})
        assert data['pincode'] == '110001'

    def test_state_too_long_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'state': 'x' * 101})
        assert 'state' in exc.value.messages

    def test_city_too_long_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'city': 'y' * 101})
        assert 'city' in exc.value.messages

    def test_unknown_field_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'extra_field': 'should_fail'})
        assert 'extra_field' in exc.value.messages

    def test_invalid_highest_qualification_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'highest_qualification': 'phd'})
        assert 'highest_qualification' in exc.value.messages

    def test_all_valid_qualification_levels(self):
        for q in ('10th', '12th', 'diploma', 'graduate', 'postgraduate', 'doctorate'):
            data = self.schema.load({'highest_qualification': q})
            assert data['highest_qualification'] == q

    def test_education_accepts_dict(self):
        data = self.schema.load({'education': {'level': 'graduate', 'year': 2020}})
        assert data['education'] == {'level': 'graduate', 'year': 2020}

    def test_notification_preferences_accepts_dict(self):
        data = self.schema.load({'notification_preferences': {'email_enabled': True}})
        assert data['notification_preferences']['email_enabled'] is True


# ---------------------------------------------------------------------------
# UpdatePhoneSchema
# ---------------------------------------------------------------------------

class TestUpdatePhoneSchema:
    schema = UpdatePhoneSchema()

    def test_valid_indian_number_with_country_code(self):
        data = self.schema.load({'phone': '+919876543210'})
        assert data['phone'] == '+919876543210'

    def test_valid_ten_digit_without_country_code(self):
        data = self.schema.load({'phone': '9876543210'})
        assert data['phone'] == '9876543210'

    def test_letters_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'phone': 'abcdefghij'})
        assert 'phone' in exc.value.messages

    def test_too_short_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'phone': '12345'})
        assert 'phone' in exc.value.messages

    def test_missing_phone_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({})
        assert 'phone' in exc.value.messages

    def test_unknown_field_raises(self):
        with pytest.raises(ValidationError) as exc:
            self.schema.load({'phone': '+919876543210', 'extra': 'bad'})
        assert 'extra' in exc.value.messages
