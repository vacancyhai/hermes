"""
Admin models: AdminUser, AdminLog, RolePermission, AccessAuditLog
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY
from app.extensions import db


class AdminUser(db.Model):
    """
    Separate admin users table with dedicated authentication and permissions.
    
    This table is independent from the regular 'users' table to provide:
    - Isolated authentication for admin panel
    - Granular permission management
    - Enhanced security (separate credentials)
    - Audit trail of admin actions
    """
    __tablename__ = 'admin_users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    
    # Role: 'admin', 'operator'
    role = db.Column(db.String(50), nullable=False, default='operator')
    
    # Permissions (JSONB for flexibility)
    # Example: {'jobs': ['create', 'edit', 'delete'], 'users': ['view', 'edit'], ...}
    permissions = db.Column(JSONB, nullable=False, default=dict)
    
    # Status: 'active', 'suspended', 'inactive'
    status = db.Column(db.String(20), nullable=False, default='active')
    
    # Security fields
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    is_2fa_enabled = db.Column(db.Boolean, nullable=False, default=False)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True))
    last_login = db.Column(db.DateTime(timezone=True))
    last_login_ip = db.Column(INET)
    
    # Metadata
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id'))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id'))
    
    # Relationships
    created_admins = db.relationship('AdminUser', foreign_keys=[created_by], remote_side=[id], backref='creator')
    
    __table_args__ = (
        db.CheckConstraint(
            "role IN ('admin', 'operator')",
            name='ck_admin_users_role'
        ),
        db.CheckConstraint(
            "status IN ('active', 'suspended', 'inactive')",
            name='ck_admin_users_status'
        ),
    )

    def __repr__(self):
        return f'<AdminUser {self.username} ({self.role})>'

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if admin has specific permission"""
        if self.status != 'active':
            return False
        
        resource_perms = self.permissions.get(resource, [])
        return action in resource_perms or '*' in resource_perms

    def is_locked(self) -> bool:
        """Check if account is locked due to failed login attempts"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until


class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id'), nullable=False)
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
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    resource = db.Column(db.String(50))
    changes = db.Column(JSONB)
    reason = db.Column(db.Text)
    ip_address = db.Column(INET)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<AccessAuditLog {self.action} admin={self.admin_id}>'
