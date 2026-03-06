"""
Admin models: AdminLog, RolePermission, AccessAuditLog
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY
from app.extensions import db


class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(100))
    resource_id = db.Column(UUID(as_uuid=True))
    details = db.Column(db.Text)
    changes = db.Column(JSONB, nullable=False, default=dict)
    ip_address = db.Column(INET)
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=30)
    )

    def __repr__(self):
        return f'<AdminLog {self.action} admin={self.admin_id}>'


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = db.Column(db.String(20), nullable=False)
    resource = db.Column(db.String(50), nullable=False)
    actions = db.Column(JSONB, nullable=False)
    field_restrictions = db.Column(ARRAY(db.Text), nullable=False, default=list)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    is_restricted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('role', 'resource', name='uq_role_resource'),)

    def __repr__(self):
        return f'<RolePermission {self.role}:{self.resource}>'


class AccessAuditLog(db.Model):
    __tablename__ = 'access_audit_logs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    resource = db.Column(db.String(50))
    changes = db.Column(JSONB)
    reason = db.Column(db.Text)
    ip_address = db.Column(INET)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<AccessAuditLog {self.action} admin={self.admin_id}>'
