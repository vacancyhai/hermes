# Admin Users Table - Design Document

**Date**: March 10, 2026  
**Purpose**: Separate authentication and authorization for admin panel

---

## Overview

The `admin_users` table provides **dedicated admin authentication** separate from regular `users`. This design improves security and provides granular permission management for the admin panel.

## Why Separate Table?

### Problems with Single `users` Table for Both:

1. **Security Risk**: Regular users and admins share same authentication flow
2. **Permission Complexity**: RBAC becomes complicated mixing user roles with admin roles
3. **Audit Trail**: Hard to distinguish admin actions from user actions
4. **Credentials Leakage**: User credentials breach could expose admin access
5. **Different Requirements**: Admins need 2FA, session timeouts, audit logs

### Benefits of Separate `admin_users` Table:

✅ **Isolated Authentication**: Separate login endpoints and credentials  
✅ **Enhanced Security**: Different password policies, 2FA enforcement  
✅ **Granular Permissions**: JSONB permissions field for flexible access control  
✅ **Clear Audit Trail**: All admin actions linked to `admin_users.id`  
✅ **Account Lockout**: Protection against brute force attacks  
✅ **Self-Referential Tracking**: Track which admin created/updated other admins

---

## Table Schema

### Fields

```sql
CREATE TABLE admin_users (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username              VARCHAR(100) NOT NULL UNIQUE,
  email                 VARCHAR(255) NOT NULL UNIQUE,
  password_hash         VARCHAR(255) NOT NULL,
  full_name             VARCHAR(255) NOT NULL,
  
  -- Role system
  role                  VARCHAR(50) NOT NULL DEFAULT 'operator'
                          CHECK (role IN ('super_admin', 'admin', 'operator', 'moderator', 'viewer')),
  
  -- Permissions (JSONB for flexibility)
  permissions           JSONB NOT NULL DEFAULT '{}',
  -- Example: {'jobs': ['create', 'edit', 'delete'], 'users': ['view', 'edit']}
  
  -- Status
  status                VARCHAR(20) NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active', 'suspended', 'inactive')),
  
  -- Security
  is_verified           BOOLEAN NOT NULL DEFAULT false,
  is_2fa_enabled        BOOLEAN NOT NULL DEFAULT false,
  failed_login_attempts INTEGER NOT NULL DEFAULT 0,
  locked_until          TIMESTAMP WITH TIME ZONE,
  last_login            TIMESTAMP WITH TIME ZONE,
  last_login_ip         INET,
  
  -- Audit trail
  created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_by            UUID REFERENCES admin_users(id) ON DELETE SET NULL,
  updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_by            UUID REFERENCES admin_users(id) ON DELETE SET NULL
);

-- Indexes
CREATE UNIQUE INDEX idx_admin_users_username ON admin_users(username);
CREATE UNIQUE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_role ON admin_users(role);
CREATE INDEX idx_admin_users_status ON admin_users(status);
CREATE INDEX idx_admin_users_permissions ON admin_users USING gin(permissions);
```

---

## Role Hierarchy

### 1. **Admin** (`admin`)
- Full admin panel access
- Manage jobs, users, content
- Create/delete other admin users
- View analytics and reports
- Can delete resources
- Manage system settings

**Typical permissions**:
```json
{
  "jobs": ["create", "edit", "delete", "publish"],
  "users": ["view", "edit", "suspend", "delete"],
  "content": ["create", "edit", "delete", "publish"],
  "analytics": ["view", "export"],
  "admin_users": ["view", "create", "edit", "delete"],
  "system": ["settings", "logs"]
}
```

### 2. **Operator** (`operator`)
- Create/edit jobs and content
- View users (cannot edit or delete)
- Limited analytics access (view only)
- Cannot delete resources
- Cannot manage other admin users
- Cannot modify system settings

**Typical permissions**:
```json
{
  "jobs": ["create", "edit", "view"],
  "users": ["view"],
  "content": ["create", "edit", "view"],
  "analytics": ["view"]
}
```

---

## Permissions System

### JSONB Structure

```json
{
  "jobs": ["create", "edit", "delete", "publish"],
  "users": ["view", "edit", "suspend"],
  "content": ["create", "edit", "delete"],
  "analytics": ["view"],
  "admin_users": ["view"],
  "system": []
}
```

### Wildcard Permissions

```json
{
  "jobs": ["*"],  // All job operations
  "users": ["view", "edit"]
}
```

### Permission Checking

```python
# In code
if admin.has_permission('jobs', 'delete'):
    # Allow job deletion
    pass

# Admins typically have more permissions than operators
if admin.role == 'admin':
    # Can manage other admins and system settings
    pass
```

---

## Security Features

### 1. **Account Lockout**
- After 5 failed login attempts
- Account locked for 30 minutes
- Prevents brute force attacks

### 2. **Password Requirements** (to implement)
- Minimum 12 characters
- Must include uppercase, lowercase, number, special char
- Cannot reuse last 5 passwords
- Expires every 90 days

### 3. **Session Management**
- Shorter session timeout (8 hours vs 7 days for users)
- Require re-authentication for sensitive operations
- Automatic logout on role change

### 4. **2FA Support** (to implement)
- Optional for operators
- Recommended for admins
- TOTP (Time-based One-Time Password)

### 5. **IP Tracking**
- Log IP address on every login
- Alert on login from new location
- Can restrict logins to specific IP ranges

---

## Migration Strategy

### Phase 1: Create Table (✅ Current)
```bash
# Run migration
cd src/backend
docker-compose exec backend flask db upgrade
```

### Phase 2: Create Initial Admin
```python
from app.services.admin_service import create_admin_user

# Create first admin (run in Flask shell)
admin = create_admin_user(
    username='admin',
    email='admin@hermes.in',
    password='SuperSecurePassword123!',
    full_name='System Administrator',
    role='admin',
    permissions={
        'jobs': ['*'],
        'users': ['*'],
        'content': ['*'],
        'analytics': ['*'],
        'admin_users': ['*'],
        'system': ['*']
    }
)
```

### Phase 3: Update Admin Routes (✅ COMPLETE - March 10, 2026)
- ✅ Frontend-admin authenticates against `admin_users` via `/api/v1/admin/auth/login`
- ✅ JWT claims include `user_type='admin'` and admin role
- ✅ Middleware checks `admin_users` permissions with @require_admin() and @require_admin_role()
- ✅ API client updated with 13 new admin methods
- ✅ Session manager handles 'admin' key from API response
- ✅ Auth route updated to use admin_login() with username parameter
- ✅ Admin users route created for CRUD operations
- ✅ Navigation link added to sidebar (admin role only)

### Phase 4: Migrate Existing Admins (TODO)
```sql
-- Copy existing admins from users table to admin_users
INSERT INTO admin_users (username, email, password_hash, full_name, role, status)
SELECT 
    email as username,
    email,
    password_hash,
    full_name,
    CASE 
        WHEN role = 'admin' THEN 'admin'
        ELSE 'operator'
    END as role,
    status
FROM users
WHERE role IN ('admin', 'operator');
```

---

## API Endpoints (✅ Implemented)

### Admin Authentication (✅ COMPLETE)
```
POST   /api/v1/admin/auth/login           - Admin login (separate from user login)
POST   /api/v1/admin/auth/logout          - Admin logout
POST   /api/v1/admin/auth/refresh         - Refresh admin token
POST   /api/v1/admin/auth/change-password - Change own password
GET    /api/v1/admin/auth/me              - Get current admin info
```

### Admin User Management (✅ COMPLETE - Admin Role Only)
```
POST   /api/v1/admin/users                - Create new admin user (admin only)
GET    /api/v1/admin/users                - List all admin users
GET    /api/v1/admin/users/<id>           - Get admin user details
PUT    /api/v1/admin/users/<id>           - Update admin user (admin only)
DELETE /api/v1/admin/users/<id>           - Deactivate admin user (admin only)
PUT    /api/v1/admin/users/<id>/permissions - Update permissions (admin only)
PUT    /api/v1/admin/users/<id>/role      - Update role (admin only)
```

### Admin Audit Log (✅ COMPLETE)
```
GET    /api/v1/admin/audit/logs           - View admin action logs (filterable)
GET    /api/v1/admin/audit/access         - View access audit logs (filterable)
```

### Admin Dashboard (✅ COMPLETE)
```
GET    /api/v1/admin/stats                - Dashboard statistics
GET    /api/v1/admin/analytics            - Analytics (to implement)
```

---

## Frontend Changes Needed

### 1. Admin Login Page
- Change endpoint from `/api/v1/auth/login` to `/api/v1/admin/auth/login`
- Add "Admin Panel" branding to distinguish from user login
- Store admin JWT separately from user JWT

### 2. Permission Checks
```javascript
// Check permission before showing UI elements
if (admin.has_permission('jobs', 'delete')) {
  showDeleteButton();
}
```

### 3. Admin User Management UI
- Page to create/edit admin users
- Permission matrix (checkboxes for each resource × action)
- Role selector
- Audit log viewer

---

## Testing Strategy

### Unit Tests
```python
def test_create_admin_user():
    admin = create_admin_user(
        username='testadmin',
        email='test@hermes.in',
        password='Test123!',
        full_name='Test Admin',
        role='operator',
        permissions={'jobs': ['create', 'edit']}
    )
    assert admin.username == 'testadmin'
    assert admin.has_permission('jobs', 'create') == True
    assert admin.has_permission('users', 'delete') == False

def test_admin_lockout():
    admin = get_admin_by_username('testadmin')
    
    # Fail login 5 times
    for i in range(5):
        with pytest.raises(UnauthorizedError):
            authenticate_admin('testadmin', 'wrong_password')
    
    # Should be locked
    assert admin.is_locked() == True
    
    # Login should fail even with correct password
    with pytest.raises(UnauthorizedError):
        authenticate_admin('testadmin', 'correct_password')
```

---

## Comparison: Regular Users vs Admin Users

| Feature | Regular Users (`users`) | Admin Users (`admin_users`) |
|---------|------------------------|----------------------------|
| **Purpose** | Public job seekers | Internal staff |
| **Login URL** | `/api/v1/auth/login` | `/api/v1/admin/auth/login` |
| **Token Expiry** | 7 days | 8 hours |
| **Permissions** | Fixed by role | Granular JSONB |
| **2FA** | Optional | Mandatory (super_admin) |
| **Account Lockout** | No | Yes (5 attempts) |
| **Audit Log** | No | Yes (all actions) |
| **Self-Service** | Yes (register) | No (created by super_admin) |
| **Password Reset** | Email link | Admin must request |

---

## Next Steps

### Immediate (High Priority)
1. ✅ Run migration to create `admin_users` table (COMPLETE - March 10, 2026)
2. ✅ Create initial admin via Flask shell (COMPLETE - March 10, 2026)
3. ✅ Implement admin authentication endpoints (COMPLETE)
4. ✅ Update frontend-admin login to use new endpoints (COMPLETE - March 10, 2026)

### Short Term
5. ✅ Build admin user management UI (COMPLETE - March 10, 2026)
6. ✅ Implement permission checking middleware (COMPLETE)
7. 🔲 Add audit log viewer UI
8. 🔲 Write integration tests

### Long Term
9. 🔲 Implement 2FA (TOTP)
10. 🔲 Add email notifications for admin actions
11. 🔲 Build permission matrix UI
12. 🔲 Migrate existing admins from `users` table

---

## Security Considerations

### ⚠️ Important Notes:

1. **Never expose admin API publicly**: Admin endpoints should be behind VPN or IP whitelist
2. **Use stronger password policy**: Minimum 12 chars, complexity requirements
3. **Enable 2FA for admins**: Recommended for all admin users
4. **Rotate credentials regularly**: Force password change every 90 days
5. **Monitor failed logins**: Alert on suspicious activity
6. **Audit everything**: Log all admin actions with IP and user agent
7. **Principle of least privilege**: Give minimum permissions needed
8. **Role separation**: Admins manage system, operators handle content

---

**Document Status**: ✅ Design Complete | ✅ Backend Implementation Complete | ✅ Frontend Integration Complete (March 10, 2026)  
**Migration File**: `0002_create_admin_users_table.py` ✅ (applied)  
**Model File**: `app/models/admin.py` (AdminUser class) ✅  
**Service File**: `app/services/admin_service.py` ✅  
**Route Files**:  
- `app/routes/admin_auth.py` ✅  
- `app/routes/admin_users.py` ✅  
- `app/routes/admin_audit.py` ✅  
- `app/routes/admin.py` ✅  
**Middleware**: `app/middleware/admin_auth_middleware.py` ✅  
**Validators**: `app/validators/admin_validator.py` ✅  
**Frontend Files**:  
- `frontend-admin/app/utils/api_client.py` ✅ (13 new admin methods)  
- `frontend-admin/app/routes/auth.py` ✅ (updated to admin_login)  
- `frontend-admin/app/routes/admin_users.py` ✅ (CRUD routes)  
- `frontend-admin/templates/pages/admin_users/` ✅ (list, create, edit templates)  
- `frontend-admin/templates/layouts/base.html` ✅ (admin users nav link)
