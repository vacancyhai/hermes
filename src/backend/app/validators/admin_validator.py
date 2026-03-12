"""
Marshmallow schemas for admin endpoint input validation.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, RAISE


class AdminLoginSchema(Schema):
    class Meta:
        unknown = RAISE

    username = fields.String(required=True, validate=validate.Length(min=3, max=50))
    password = fields.String(required=True, load_only=True)


class AdminChangePasswordSchema(Schema):
    class Meta:
        unknown = RAISE

    current_password = fields.String(required=True, load_only=True)
    new_password = fields.String(
        required=True,
        validate=validate.Length(min=12, max=128),
        load_only=True,
    )


class CreateAdminSchema(Schema):
    class Meta:
        unknown = RAISE

    username = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=50),
            validate.Regexp(r'^[a-z0-9_]+$', error='Username must be lowercase alphanumeric with underscores only.')
        ]
    )
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.String(
        required=True,
        validate=validate.Length(min=12, max=128),
        load_only=True,
    )
    full_name = fields.String(
        required=True,
        validate=[
            validate.Length(min=1, max=255),
            validate.Regexp(r'^\S.*', error='full_name must not be blank.')
        ],
    )
    role = fields.String(
        required=True,
        validate=validate.OneOf(['admin', 'operator'])
    )
    permissions = fields.Dict(
        keys=fields.String(),
        values=fields.List(fields.String()),
        missing={}
    )


class UpdateAdminSchema(Schema):
    class Meta:
        unknown = RAISE

    email = fields.Email(validate=validate.Length(max=255))
    full_name = fields.String(
        validate=[
            validate.Length(min=1, max=255),
            validate.Regexp(r'^\S.*', error='full_name must not be blank.')
        ]
    )
    status = fields.String(validate=validate.OneOf(['active', 'inactive', 'suspended']))


class UpdateAdminRoleSchema(Schema):
    class Meta:
        unknown = RAISE

    role = fields.String(
        required=True,
        validate=validate.OneOf(['admin', 'operator'])
    )


class UpdateAdminPermissionsSchema(Schema):
    class Meta:
        unknown = RAISE

    permissions = fields.Dict(
        keys=fields.String(),
        values=fields.List(fields.String()),
        required=True
    )


class AuditLogQuerySchema(Schema):
    class Meta:
        unknown = RAISE

    admin_id = fields.UUID()
    action = fields.String()
    resource_type = fields.String()
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    page = fields.Integer(missing=1, validate=validate.Range(min=1))
    per_page = fields.Integer(missing=20, validate=validate.Range(min=1, max=100))


class AccessAuditQuerySchema(Schema):
    class Meta:
        unknown = RAISE

    admin_id = fields.UUID()
    ip_address = fields.String()
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    page = fields.Integer(missing=1, validate=validate.Range(min=1))
    per_page = fields.Integer(missing=20, validate=validate.Range(min=1, max=100))
