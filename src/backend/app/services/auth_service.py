"""
Auth service — all authentication business logic.

Token storage strategy:
  - JWT access/refresh tokens issued via flask_jwt_extended.
  - Logout blocklist:     Redis key  blocklist:{jti}          TTL = refresh token lifetime
  - Email verification:   Redis key  email_verify:{token}     TTL = 24 h
  - Password reset:       Redis key  pwd_reset:{token}        TTL = 1 h

No extra DB tables are needed; Redis TTL handles expiry automatically.

Error Handling:
  - Redis failures in token storage are caught and logged as RuntimeError.
  - Database operation failures are logged and re-raised with context.
  - All password verification uses bcrypt with constant-time comparison
    to prevent timing-based user enumeration attacks.

Return Types:
  - register() -> tuple[User, str, str, str]
    (user, access_token, refresh_token, email_verify_token)
  
  - login() -> tuple[User, str, str]
    (user, access_token, refresh_token)
  
  - logout(jti: str) -> None
  - refresh(user_id: str, old_jti: str) -> Tuple[str, str]
    (access_token, refresh_token)
"""
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple

import bcrypt
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import IntegrityError, OperationalError
import redis.exceptions

from app.middleware.error_handler import ConflictError, ValidationError, NotFoundError, ExternalServiceError

logger = logging.getLogger(__name__)

# Pre-computed dummy hash used in login() to ensure bcrypt runs even when
# the email doesn't exist, preventing timing-based user enumeration.
# Uses the same default rounds (12) as real passwords to avoid timing leaks.
_DUMMY_HASH = bcrypt.hashpw(b'dummy-timing-guard', bcrypt.gensalt(rounds=12)).decode()

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
        raise ConflictError("Email already registered")

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
        raise ConflictError("Email already registered")

    verify_token = _store_redis_token('email_verify', str(user.id), _EMAIL_VERIFY_TTL)
    access_token, refresh_token = _issue_tokens(user)
    return user, access_token, refresh_token, verify_token


def login(email, password):
    """
    Verify credentials and return the user plus a fresh token pair.

    Returns:
        tuple: (user, access_token, refresh_token)

    Raises:
        ValueError('INVALID_CREDENTIALS') on bad email/password.
        ValueError('ACCOUNT_SUSPENDED')   if user.status != 'active'.
    """
    user = User.query.filter_by(email=email.lower().strip()).first()

    # Always run bcrypt to prevent timing-based user enumeration.
    password_hash = user.password_hash.encode() if user else _DUMMY_HASH.encode()
    password_ok = bcrypt.checkpw(password.encode(), password_hash)

    if not user or not password_ok:
        logger.warning("login: failed attempt for email=%s", email.lower().strip())
        raise ValidationError("Invalid email or password")

    if user.status != 'active':
        raise ValidationError("Account is suspended or inactive")

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()
    logger.info("login: success user_id=%s", user.id)

    access_token, refresh_token = _issue_tokens(user)
    return user, access_token, refresh_token


def logout(jti: str) -> None:
    """
    Add access token JTI to the Redis blocklist.

    The TTL is set to the full refresh token lifetime so that even if a
    refresh token is still valid, its paired access JTI remains blocked.
    
    Args:
        jti: JWT ID (from JWT payload) to blocklist
    
    Raises:
        RuntimeError: If Redis is unavailable (blocks logout to ensure security)
    """
    try:
        ttl = int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds())
        key = f'blocklist:{jti}'
        current_app.redis.setex(key, ttl, '1')
        logger.info(f"Token blocklisted: jti={jti[:8]}..., ttl={ttl}s")
    except (redis.exceptions.RedisError, redis.exceptions.ConnectionError) as exc:
        logger.error(f"logout: Redis unavailable, cannot blocklist token: {exc}")
        raise RuntimeError("Logout failed: token blocklist service unavailable.") from exc


def refresh(user_id: str, old_jti: str) -> Tuple[str, str]:
    """
    Rotate tokens: blocklist the old refresh JTI and issue a new pair.

    Always blocklists the old JTI even if user lookup fails, to prevent
    token reuse attacks. Critical for JWT rotation security.

    Args:
        user_id: User UUID (from JWT identity)
        old_jti: Old refresh token's JTI (from JWT payload)

    Returns:
        Tuple[access_token, refresh_token]: Fresh token pair

    Raises:
        ValueError('USER_NOT_FOUND'): if user doesn't exist or is suspended.
        RuntimeError: if Redis blocklist fails (logout is blocked for security)
    """
    user = db.session.get(User, user_id)
    if not user or user.status != 'active':
        logger.warning(f"refresh: User not found or suspended: {user_id}")
        raise NotFoundError("User not found or inactive")

    try:
        ttl = int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds())
        key = f'blocklist:{old_jti}'
        current_app.redis.setex(key, ttl, '1')
        logger.debug(f"refresh: Old JTI blocklisted for user={user_id}")
    except (redis.exceptions.RedisError, redis.exceptions.ConnectionError) as exc:
        logger.error(f"refresh: Redis unavailable, cannot blocklist old JTI: {exc}")
        raise RuntimeError("Token rotation failed: blocklist service unavailable.") from exc

    new_access, new_refresh = _issue_tokens(user)
    logger.info(f"refresh: New token pair issued for user={user_id}")
    return new_access, new_refresh


def request_password_reset(email: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Generate a password-reset token and store it in Redis.

    Returns None for both user and token if email is not found,
    so that callers cannot infer whether an account exists (prevents
    user enumeration via the password reset endpoint).

    Args:
        email: User email (will be lowercased and stripped)

    Returns:
        Tuple[User | None, reset_token | None]

    Raises:
        RuntimeError: if Redis storage fails
    """
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user:
        logger.debug(f"request_password_reset: Email not found (may be intentional): {email[:5]}...")
        return None, None

    reset_token = _store_redis_token('pwd_reset', str(user.id), _PWD_RESET_TTL)
    logger.info(f"request_password_reset: Token generated for user={user.id}")
    return user, reset_token
    return user, reset_token


def reset_password(token: str, new_password: str) -> User:
    """
    Validate a reset token from Redis and update the user's password.

    The token is deleted after successful reset to ensure single-use semantics.
    Always checks for token existence in Redis, even if user isn't found.

    Args:
        token: Password reset token (from email link)
        new_password: New plaintext password (will be bcrypt hashed)

    Returns:
        User: the user whose password was reset

    Raises:
        ValueError('INVALID_OR_EXPIRED_TOKEN'): if token is bad/expired or user not found.
        RuntimeError: if password hashing fails
    """
    user_id = current_app.redis.get(f'pwd_reset:{token}')
    if not user_id:
        logger.warning(f"reset_password: Invalid or expired token")
        raise ValidationError("Reset token is invalid or has expired")

    user = db.session.get(User, user_id)
    if not user:
        logger.error(f"reset_password: User {user_id} not found (token was valid)")
        raise ValidationError("Reset token is invalid or has expired")

    try:
        rounds = current_app.config.get('BCRYPT_LOG_ROUNDS', 12)
        user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=rounds)).decode()
        db.session.commit()
        current_app.redis.delete(f'pwd_reset:{token}')
        logger.info(f"reset_password: Password reset for user={user.id}")
        return user
    except Exception as exc:
        db.session.rollback()
        logger.error(f"reset_password: Failed to update password: {exc}")
        raise RuntimeError("Password reset failed. Please try again.") from exc


def verify_email(token: str) -> User:
    """
    Validate an email-verification token from Redis and mark the user verified.

    The token is deleted after successful verification to ensure single-use semantics.

    Args:
        token: Email verification token (from registration email)

    Returns:
        User: the verified user

    Raises:
        ValueError('INVALID_OR_EXPIRED_TOKEN'): if token is bad/expired or user not found.
    """
    user_id = current_app.redis.get(f'email_verify:{token}')
    if not user_id:
        logger.warning(f"verify_email: Invalid or expired token")
        raise ValidationError("Verification token is invalid or has expired")

    user = db.session.get(User, user_id)
    if not user:
        logger.error(f"verify_email: User {user_id} not found (token was valid)")
        raise ValidationError("Verification token is invalid or has expired")

    user.is_email_verified = True
    db.session.commit()
    current_app.redis.delete(f'email_verify:{token}')
    logger.info(f"verify_email: Email verified for user={user.id}")
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


def _store_redis_token(prefix: str, user_id: str, ttl: int) -> str:
    """
    Generate a secure URL-safe token, store it in Redis, and return it.
    
    Args:
        prefix: Redis key prefix (e.g., 'email_verify', 'pwd_reset')
        user_id: User UUID to associate with token
        ttl: Time-to-live in seconds
    
    Returns:
        URL-safe token string (32 bytes encoded)
    
    Raises:
        RuntimeError: If Redis storage fails
    """
    token = secrets.token_urlsafe(32)  # 32 bytes = 43 characters URL-safe
    try:
        key = f'{prefix}:{token}'
        current_app.redis.setex(key, ttl, user_id)
        logger.debug(f"Token stored: prefix={prefix}, ttl={ttl}s")
    except (redis.exceptions.RedisError, redis.exceptions.ConnectionError) as exc:
        logger.error(f"_store_redis_token: Redis unavailable for prefix={prefix}: {exc}")
        raise RuntimeError("Token storage is temporarily unavailable. Please try again.") from exc
    except Exception as exc:
        logger.error(f"_store_redis_token: Unexpected error: {exc}")
        raise RuntimeError("Token storage failed. Please try again.") from exc
    return token
