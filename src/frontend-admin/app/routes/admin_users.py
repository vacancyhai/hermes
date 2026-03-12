"""
Admin User Management Routes — Admin Frontend

Manage admin users (create, edit, delete, change roles/permissions).
Only admins can access these routes.

Templates expected:
  admin_users/list.html
  admin_users/create.html
  admin_users/edit.html
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.middleware.auth_middleware import login_required, role_required
from app.utils.api_client import APIClient, APIError
from app.utils.session_manager import get_access_token

bp = Blueprint('admin_users', __name__, url_prefix='/admin-users')
_api = APIClient()


# ---------------------------------------------------------------------------
# List Admin Users
# ---------------------------------------------------------------------------

@bp.route('/', methods=['GET'])
@login_required
@role_required('admin')  # Only admins can manage admin users
def list_admin_users():
    """GET /admin-users/ — list all admin users with filters."""
    access_token = get_access_token(session)

    # Query params
    page = int(request.args.get('page', 1))
    role = request.args.get('role', '')
    status = request.args.get('status', '')

    params = {'page': page, 'per_page': 20}
    if role:
        params['role'] = role
    if status:
        params['status'] = status

    try:
        data = _api.get_admin_users(access_token, **params)
        admins = data.get('data', {}).get('admins', [])
        pagination = data.get('pagination', {})
    except APIError as e:
        flash(f'Failed to load admin users: {e.message}', 'error')
        admins = []
        pagination = {}

    return render_template(
        'pages/admin_users/list.html',
        admins=admins,
        pagination=pagination,
        filters={'role': role, 'status': status}
    )


# ---------------------------------------------------------------------------
# Create Admin User
# ---------------------------------------------------------------------------

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_admin_user():
    """GET+POST /admin-users/create — create new admin user."""
    if request.method == 'GET':
        return render_template('pages/admin_users/create.html')

    access_token = get_access_token(session)
    
    # Form data
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    full_name = request.form.get('full_name', '').strip()
    role = request.form.get('role', 'operator')

    # Basic validation
    if not all([username, email, password, full_name]):
        flash('All fields are required.', 'error')
        return render_template('pages/admin_users/create.html', form_data=request.form)

    if len(password) < 12:
        flash('Password must be at least 12 characters.', 'error')
        return render_template('pages/admin_users/create.html', form_data=request.form)

    # Build payload
    payload = {
        'username': username,
        'email': email,
        'password': password,
        'full_name': full_name,
        'role': role,
        'permissions': {}  # Default empty permissions, can be updated later
    }

    try:
        _api.create_admin_user(access_token, payload)
        flash(f'Admin user "{username}" created successfully!', 'success')
        return redirect(url_for('admin_users.list_admin_users'))
    except APIError as e:
        flash(f'Failed to create admin user: {e.message}', 'error')
        return render_template('pages/admin_users/create.html', form_data=request.form)


# ---------------------------------------------------------------------------
# Edit Admin User
# ---------------------------------------------------------------------------

@bp.route('/<admin_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_admin_user(admin_id: str):
    """GET+POST /admin-users/<id>/edit — edit admin user."""
    access_token = get_access_token(session)

    if request.method == 'GET':
        try:
            data = _api.get_admin_user(access_token, admin_id)
            admin = data.get('data', {}).get('admin', {})
        except APIError as e:
            flash(f'Failed to load admin user: {e.message}', 'error')
            return redirect(url_for('admin_users.list_admin_users'))

        return render_template('pages/admin_users/edit.html', admin=admin)

    # POST: Update admin user
    email = request.form.get('email', '').strip()
    full_name = request.form.get('full_name', '').strip()
    status = request.form.get('status', '')

    payload = {}
    if email:
        payload['email'] = email
    if full_name:
        payload['full_name'] = full_name
    if status:
        payload['status'] = status

    try:
        _api.update_admin_user(access_token, admin_id, payload)
        flash('Admin user updated successfully!', 'success')
        return redirect(url_for('admin_users.list_admin_users'))
    except APIError as e:
        flash(f'Failed to update admin user: {e.message}', 'error')
        return redirect(url_for('admin_users.edit_admin_user', admin_id=admin_id))


# ---------------------------------------------------------------------------
# Delete Admin User
# ---------------------------------------------------------------------------

@bp.route('/<admin_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_admin_user(admin_id: str):
    """POST /admin-users/<id>/delete — deactivate admin user."""
    access_token = get_access_token(session)

    try:
        _api.delete_admin_user(access_token, admin_id)
        flash('Admin user deactivated successfully!', 'success')
    except APIError as e:
        flash(f'Failed to deactivate admin user: {e.message}', 'error')

    return redirect(url_for('admin_users.list_admin_users'))


# ---------------------------------------------------------------------------
# Update Role
# ---------------------------------------------------------------------------

@bp.route('/<admin_id>/role', methods=['POST'])
@login_required
@role_required('admin')
def update_admin_role(admin_id: str):
    """POST /admin-users/<id>/role — update admin role."""
    access_token = get_access_token(session)
    role = request.form.get('role', '')

    if role not in ('admin', 'operator'):
        flash('Invalid role specified.', 'error')
        return redirect(url_for('admin_users.list_admin_users'))

    try:
        _api.update_admin_role(access_token, admin_id, role)
        flash(f'Admin role updated to {role}!', 'success')
    except APIError as e:
        flash(f'Failed to update role: {e.message}', 'error')

    return redirect(url_for('admin_users.list_admin_users'))
