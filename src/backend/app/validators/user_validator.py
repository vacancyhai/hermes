"""
Marshmallow schemas for user profile endpoint input validation.

All profile fields are optional (partial update / PATCH-style PUT).
The schemas enforce:
  - Allowed values for enum-like fields (gender, category, qualification)
  - Format constraints (pincode must be exactly 6 digits)
  - Length limits on string fields
  - Unknown fields rejected (unknown = RAISE)
"""
from marshmallow import Schema, fields, validate, RAISE


class UpdateProfileSchema(Schema):
    class Meta:
        unknown = RAISE

    date_of_birth = fields.Date(required=False, load_default=None)
    gender = fields.String(
        required=False,
        load_default=None,
        validate=validate.OneOf(['male', 'female', 'other']),
    )
    category = fields.String(
        required=False,
        load_default=None,
        validate=validate.OneOf(['general', 'obc', 'sc', 'st']),
    )
    is_pwd = fields.Boolean(required=False, load_default=None)
    is_ex_serviceman = fields.Boolean(required=False, load_default=None)
    state = fields.String(
        required=False,
        load_default=None,
        validate=validate.Length(max=100),
    )
    city = fields.String(
        required=False,
        load_default=None,
        validate=validate.Length(max=100),
    )
    pincode = fields.String(
        required=False,
        load_default=None,
        validate=validate.Regexp(r'^\d{6}$', error='pincode must be exactly 6 digits.'),
    )
    highest_qualification = fields.String(
        required=False,
        load_default=None,
        validate=validate.OneOf(
            ['10th', '12th', 'diploma', 'graduate', 'postgraduate', 'doctorate'],
        ),
    )
    education = fields.Dict(required=False, load_default=None)
    physical_details = fields.Dict(required=False, load_default=None)
    notification_preferences = fields.Dict(required=False, load_default=None)


class UpdatePhoneSchema(Schema):
    class Meta:
        unknown = RAISE

    phone = fields.String(
        required=True,
        validate=validate.Regexp(
            r'^\+?[1-9]\d{9,14}$',
            error='phone must be a valid international phone number.',
        ),
    )
