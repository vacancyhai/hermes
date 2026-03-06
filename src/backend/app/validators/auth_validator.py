"""
Marshmallow schemas for auth endpoint input validation.
"""
from marshmallow import Schema, fields, validate, RAISE


class RegisterSchema(Schema):
    class Meta:
        unknown = RAISE

    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128),
        load_only=True,
    )
    full_name = fields.String(
        required=True,
        validate=[validate.Length(min=1, max=100), validate.Regexp(r'^\S.*', error='full_name must not be blank.')],
    )


class LoginSchema(Schema):
    class Meta:
        unknown = RAISE

    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class PasswordResetRequestSchema(Schema):
    class Meta:
        unknown = RAISE

    email = fields.Email(required=True)


class PasswordResetSchema(Schema):
    class Meta:
        unknown = RAISE

    token = fields.String(required=True)
    new_password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128),
        load_only=True,
    )
