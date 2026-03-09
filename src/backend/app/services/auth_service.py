"""
Auth service — all authentication business logic.

Token storage strategy:
  - JWT access/refresh tokens issued via flask_jwt_extended.
  - Logout blocklist:     Redis key  blocklist:{jti}          TTL = refresh token lifetime
  - Email verification:   Redis key  email_verify:{token}     TTL = 24 h
  - Password reset:       Redis key  pwd_reset:{token}        TTL = 1 h

No extra DB tables are needed; Redis TTL handles expiry automatically.
"""
import secrets
from datetime import datetime, timezone

import bcrypt
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User, UserProfile

_EMAIL_VERIFY_TTL = 86_400   # 24 hours in seconds
_PWD_RESET_TTL = 3_600       # 1 hour in seconds


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register(data):
    """
    Create a new user + empty profile.

    Returns:
        tuple: ((access_token, refresh_token), email_verify_token)

    Raises:
        ValueError('EMAIL_TAKEN') if email is already registered.
    """
    email = data['email'].lower().strip()

    if User.query.filter_by(email=email).first():
        raise ValueError('EMAIL_TAKEN')

    rounds = current_app.config.get('BCRYPT_LOG_ROUNDS', 12)
    pw_hash = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt(rounds=rounds)).decode()

    user = User(
        email=email,
        password_hash=pw_hash,
        full_name=data['full_name'].strip(),
    )
    db.session.add(user)
    try:
        db.session.flush()  # populate user.id before profile FK insert
        db.session.add(UserProfile(user_id=user.id))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError('EMAIL_TAKEN')

    verify_token = _store_redis_token('email_verify', str(user.id), _EMAIL_VERIFY_TTL)
    access_token, refresh_token = _issue_tokens(user)
    return user, access_token, refresh_token, verify_token


def login(email, password):
    """
    Verify credentials and return a fresh token pair.

    Returns:
        tuple: (access_token, refresh_token)

    Raises:
        ValueError('INVALID_CREDENTIALS') on bad email/password.
        ValueError('ACCOUNT_SUSPENDED')   if user.status != 'active'.
    """
    user = User.query.filter_by(email=email.lower().strip()).first()

    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise ValueError('INVALID_CREDENTIALS')

    if user.status != 'active':
        raise ValueError('ACCOUNT_SUSPENDED')

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    return _issue_tokens(user)


def logout(jti):
    """
    Add access token JTI to the Redis blocklist.

    The TTL is set to the full refresh token lifetime so that even if a
    refresh token is still valid, its paired access JTI remains blocked.
    """
    ttl = int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds())
    current_app.redis.setex(f'blocklist:{jti}', ttl, '1')


def refresh(user_id, old_jti):
    """
    Rotate tokens: blocklist the old refresh JTI and issue a new pair.

    Returns:
        tuple: (access_token, refresh_token)

    Raises:
        ValueError('USER_NOT_FOUND') if user is missing or suspended.
    """
    user = db.session.get(User, user_id)
    if not user or user.status != 'active':
        raise ValueError('USER_NOT_FOUND')

    ttl = int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds())
    current_app.redis.setex(f'blocklist:{old_jti}', ttl, '1')

    return _issue_tokens(user)


def request_password_reset(email):
    """
    Generate a password-reset token and store it in Redis.

    Returns:
        tuple: (user, reset_token) — both are None if email is not found
               so that callers cannot infer whether an account exists.
    """
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user:
        return None, None

    reset_token = _store_redis_token('pwd_reset', str(user.id), _PWD_RESET_TTL)
    return user, reset_token


def reset_password(token, new_password):
    """
    Validate a reset token from Redis and update the user's password.

    Raises:
        ValueError('INVALID_OR_EXPIRED_TOKEN') if token is bad/expired.
    """
    user_id = current_app.redis.get(f'pwd_reset:{token}')
    if not user_id:
        raise ValueError('INVALID_OR_EXPIRED_TOKEN')

    user = db.session.get(User, user_id)
    if not user:
        raise ValueError('INVALID_OR_EXPIRED_TOKEN')

    rounds = current_app.config.get('BCRYPT_LOG_ROUNDS', 12)
    user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=rounds)).decode()
    db.session.commit()
    current_app.redis.delete(f'pwd_reset:{token}')


def verify_email(token):
    """
    Validate an email-verification token from Redis and mark the user verified.

    Returns:
        User: the verified user.

    Raises:
        ValueError('INVALID_OR_EXPIRED_TOKEN') if token is bad/expired.
    """
    user_id = current_app.redis.get(f'email_verify:{token}')
    if not user_id:
        raise ValueError('INVALID_OR_EXPIRED_TOKEN')

    user = db.session.get(User, user_id)
    if not user:
        raise ValueError('INVALID_OR_EXPIRED_TOKEN')

    user.is_email_verified = True
    db.session.commit()
    current_app.redis.delete(f'email_verify:{token}')
    return user


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _issue_tokens(user):
    """Create and return a (access_token, refresh_token) pair for user."""
    additional_claims = {'role': user.role, 'email': user.email}
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims,
    )
    refresh_token = create_refresh_token(identity=str(user.id))
    return access_token, refresh_token


def _store_redis_token(prefix, user_id, ttl):
    """Generate a secure URL-safe token, store it in Redis, and return it."""
    token = secrets.token_urlsafe(32)
    current_app.redis.setex(f'{prefix}:{token}', ttl, user_id)
    return token
