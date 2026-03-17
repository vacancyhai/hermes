"""
Admin User Service - Handles admin user management and authentication

Provides CRUD operations and authentication for admin_users table.
This is separate from user_service.py to maintain strict separation
between regular users and admin users.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Union
import uuid as _uuid_mod
import logging

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.admin import AdminUser, AdminLog
from app.middleware.error_handler import (
    NotFoundError,
    ConflictError,
    ValidationError,
    UnauthorizedError
)

logger = logging.getLogger(__name__)

# Security constants
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def authenticate_admin(
    username: str,
    password: str,
    ip_address: str = None,
    user_agent: str = None
) -> AdminUser:
    """
    Authenticate an admin user and return the admin object.
    
    Args:
        username: Username (can also accept email)
        password: Plain text password
        ip_address: IP address for audit log
        user_agent: User agent string for audit log
    
    Returns:
        AdminUser object
    
    Raises:
        ValueError: If credentials are invalid or account is locked
    """
    # Find admin by username or email
    admin = AdminUser.query.filter(
        db.or_(
            AdminUser.username == username,
            AdminUser.email == username
        )
    ).first()
    
    if not admin:
        logger.warning(f"Admin login attempt with unknown username: {username}")
        raise ValueError("Invalid credentials")
    
    # Check if account is locked
    if admin.is_locked():
        logger.warning(f"Admin login attempt for locked account: {admin.username}")
        raise ValueError(f"Account locked until {admin.locked_until.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Check if account is active
    if admin.status != 'active':
        logger.warning(f"Admin login attempt for {admin.status} account: {admin.username}")
        raise ValueError(f"Account is {admin.status}")
    
    # Verify password
    if not check_password_hash(admin.password_hash, password):
        # Increment failed attempts
        admin.failed_login_attempts += 1
        
        # Lock account if max attempts reached
        if admin.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            admin.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            logger.warning(f"Admin account locked due to failed login attempts: {admin.username}")
        
        db.session.commit()
        raise ValueError("Invalid credentials")
    
    # Successful login - update login tracking
    admin.last_login = datetime.now(timezone.utc)
    admin.last_login_ip = ip_address
    
    db.session.commit()
    
    logger.info(f"Successful admin login: {admin.username} ({admin.role})")
    
    return admin


def reset_failed_login_attempts(admin_id: str) -> None:
    """Reset failed login attempts counter for an admin user."""
    from app.models.admin import AdminUser
    
    admin = db.session.get(AdminUser, admin_id)
    if admin:
        admin.failed_login_attempts = 0
        admin.locked_until = None
        db.session.commit()
        logger.info(f"Reset failed login attempts for admin: {admin.username}")


def _generate_admin_jwt(admin: AdminUser) -> str:
    """Generate JWT token for admin user"""
    from flask_jwt_extended import create_access_token
    
    additional_claims = {
        'admin_id': str(admin.id),
        'role': admin.role,
        'permissions': admin.permissions,
        'is_admin': True  # Flag to distinguish from regular users
    }
    
    return create_access_token(
        identity=str(admin.id),
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=8)  # Shorter expiry for admin tokens
    )


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------

def create_admin_user(
    username: str,
    email: str,
    password: str,
    full_name: str,
    role: str,
    permissions: Dict[str, List[str]],
    created_by_id: str = None
) -> AdminUser:
    """
    Create a new admin user.
    
    Args:
        username: Unique username (lowercase, alphanumeric + underscore)
        email: Unique email address
        password: Plain text password (will be hashed)
        full_name: Full name of the admin
        role: Role ('admin' or 'operator')
        permissions: Dict of permissions like {'jobs': ['create', 'edit'], 'users': ['view']}
        created_by_id: UUID of the admin creating this user
    
    Returns:
        Created AdminUser instance
    
    Raises:
        ConflictError: If username or email already exists
        ValidationError: If invalid role or permissions
    """
    # Validate role
    valid_roles = ['admin', 'operator']
    if role not in valid_roles:
        raise ValidationError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
    
    # Check uniqueness
    if AdminUser.query.filter_by(username=username).first():
        raise ConflictError(f"Username '{username}' already exists")
    
    if AdminUser.query.filter_by(email=email).first():
        raise ConflictError(f"Email '{email}' already exists")
    
    # Create admin user
    admin = AdminUser(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        full_name=full_name,
        role=role,
        permissions=permissions,
        status='active',
        is_verified=False,  # Should verify email
        created_by=_uuid_mod.UUID(created_by_id) if created_by_id else None
    )
    
    db.session.add(admin)
    db.session.commit()
    
    logger.info(f"Created admin user: {username} ({role})")
    
    # Log the action
    if created_by_id:
        log_admin_action(
            admin_id=created_by_id,
            action='create_admin_user',
            resource_type='admin_user',
            resource_id=str(admin.id),
            details=f"Created admin user: {username}"
        )
    
    return admin


def get_admin_user(admin_id: str) -> AdminUser:
    """Get admin user by ID"""
    admin = db.session.get(AdminUser, admin_id)
    if not admin:
        raise NotFoundError("Admin user not found")
    return admin


def get_admin_by_username(username: str) -> Optional[AdminUser]:
    """Get admin user by username"""
    return AdminUser.query.filter_by(username=username).first()


def get_admin_by_email(email: str) -> Optional[AdminUser]:
    """Get admin user by email"""
    return AdminUser.query.filter_by(email=email).first()


def list_admin_users(
    role: str = None,
    status: str = None,
    page: int = 1,
    per_page: int = 20
) -> Dict:
    """
    List admin users with optional filters.
    
    Returns dict with 'items', 'total', 'page', 'per_page', 'pages'
    """
    from app.utils.helpers import paginate
    
    query = AdminUser.query
    
    if role:
        query = query.filter_by(role=role)
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(AdminUser.created_at.desc())
    
    return paginate(query, page=page, per_page=per_page)


def update_admin_user(
    admin_id: str,
    updated_by_id: str,
    **updates
) -> AdminUser:
    """
    Update admin user fields.
    
    Allowed updates: full_name, email, role, permissions, status
    Password must be updated via separate method.
    """
    admin = get_admin_user(admin_id)
    
    allowed_fields = ['full_name', 'email', 'role', 'permissions', 'status']
    changes = {}
    
    for field, value in updates.items():
        if field not in allowed_fields:
            continue
        
        if field == 'email' and value != admin.email:
            # Check email uniqueness
            existing = AdminUser.query.filter_by(email=value).first()
            if existing and existing.id != admin.id:
                raise ConflictError(f"Email '{value}' already in use")
        
        old_value = getattr(admin, field)
        if old_value != value:
            changes[field] = {'old': old_value, 'new': value}
            setattr(admin, field, value)
    
    if changes:
        admin.updated_by = _uuid_mod.UUID(updated_by_id)
        admin.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        logger.info(f"Updated admin user {admin.username}: {changes}")
        
        # Log the action
        log_admin_action(
            admin_id=updated_by_id,
            action='update_admin_user',
            resource_type='admin_user',
            resource_id=admin_id,
            details=f"Updated admin user: {admin.username}",
            changes=changes
        )
    
    return admin


def update_admin_password(
    admin_id: str,
    current_password: str,
    new_password: str
) -> AdminUser:
    """Update admin user password"""
    admin = get_admin_user(admin_id)
    
    # Verify current password
    if not check_password_hash(admin.password_hash, current_password):
        raise ValueError("Current password is incorrect")
    
    # Update password
    admin.password_hash = generate_password_hash(new_password)
    admin.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    logger.info(f"Password updated for admin user: {admin.username}")
    
    return admin


def delete_admin_user(admin_id: str, deleted_by_id: str) -> None:
    """
    Soft delete admin user (set status to 'inactive').
    Only super_admins should be able to actually delete.
    """
    admin = get_admin_user(admin_id)
    
    # Prevent self-deletion
    if admin_id == deleted_by_id:
        raise ValidationError("Cannot delete your own admin account")
    
    admin.status = 'inactive'
    admin.updated_by = _uuid_mod.UUID(deleted_by_id)
    admin.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    logger.info(f"Deactivated admin user: {admin.username}")
    
    # Log the action
    log_admin_action(
        admin_id=deleted_by_id,
        action='delete_admin_user',
        resource_type='admin_user',
        resource_id=admin_id,
        details=f"Deactivated admin user: {admin.username}"
    )


# ---------------------------------------------------------------------------
# Permission Management
# ---------------------------------------------------------------------------

def update_admin_permissions(
    admin_id: str,
    permissions: Dict[str, List[str]],
    updated_by_id: str
) -> AdminUser:
    """Update admin user permissions"""
    admin = get_admin_user(admin_id)
    
    old_permissions = admin.permissions.copy()
    admin.permissions = permissions
    admin.updated_by = _uuid_mod.UUID(updated_by_id)
    admin.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    logger.info(f"Updated permissions for admin user: {admin.username}")
    
    # Log the action
    log_admin_action(
        admin_id=updated_by_id,
        action='update_admin_permissions',
        resource_type='admin_user',
        resource_id=admin_id,
        details=f"Updated permissions for: {admin.username}",
        changes={'old': old_permissions, 'new': permissions}
    )
    
    return admin


# ---------------------------------------------------------------------------
# Admin Action Logging
# ---------------------------------------------------------------------------

def log_admin_action(
    admin_id: str,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    details: Union[str, dict, None] = None,
    changes: Dict = None,
    ip_address: str = None,
    user_agent: str = None
) -> AdminLog:
    """Log an admin action for audit trail"""
    _details = json.dumps(details) if isinstance(details, dict) else details
    log_entry = AdminLog(
        admin_id=_uuid_mod.UUID(str(admin_id)),
        action=action,
        resource_type=resource_type,
        resource_id=_uuid_mod.UUID(str(resource_id)) if resource_id else None,
        details=_details,
        changes=changes or {},
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.session.add(log_entry)
    db.session.commit()
    
    return log_entry


def get_admin_logs(
    admin_id: str = None,
    action: str = None,
    resource_type: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    page: int = 1,
    per_page: int = 20
) -> Dict:
    """
    Retrieve admin action logs with optional filters.
    
    Args:
        admin_id: Filter by specific admin user
        action: Filter by action type
        resource_type: Filter by resource type
        start_date: Filter logs after this date
        end_date: Filter logs before this date
        page: Page number
        per_page: Items per page
    
    Returns:
        Dict with 'items', 'total', 'page', 'per_page', 'pages'
    """
    from app.utils.helpers import paginate
    
    query = AdminLog.query
    
    if admin_id:
        query = query.filter_by(admin_id=_uuid_mod.UUID(admin_id))
    
    if action:
        query = query.filter_by(action=action)
    
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    
    if start_date:
        query = query.filter(AdminLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AdminLog.timestamp <= end_date)
    
    query = query.order_by(AdminLog.timestamp.desc())
    
    return paginate(query, page=page, per_page=per_page)


def get_access_audit_logs(
    admin_id: str = None,
    ip_address: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    page: int = 1,
    per_page: int = 20
) -> Dict:
    """
    Retrieve access audit logs with optional filters.
    
    Args:
        admin_id: Filter by specific admin user
        ip_address: Filter by IP address
        start_date: Filter logs after this date
        end_date: Filter logs before this date
        page: Page number
        per_page: Items per page
    
    Returns:
        Dict with 'items', 'total', 'page', 'per_page', 'pages'
    """
    from app.models.admin import AccessAuditLog
    from app.utils.helpers import paginate
    
    query = AccessAuditLog.query
    
    if admin_id:
        query = query.filter_by(admin_id=_uuid_mod.UUID(admin_id))
    
    if ip_address:
        query = query.filter_by(ip_address=ip_address)
    
    if start_date:
        query = query.filter(AccessAuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AccessAuditLog.timestamp <= end_date)
    
    query = query.order_by(AccessAuditLog.timestamp.desc())
    
    return paginate(query, page=page, per_page=per_page)
