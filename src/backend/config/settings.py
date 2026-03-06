"""
Backend Configuration Settings
"""
import os
import sys
from datetime import timedelta

# Variables that must be explicitly set in production (no insecure defaults allowed)
_REQUIRED_IN_PRODUCTION = [
    'SECRET_KEY',
    'JWT_SECRET_KEY',
    'DATABASE_URL',
    'REDIS_URL',
    'REDIS_PASSWORD',
]

def _validate_env():
    """Abort startup if required production vars are missing or still set to dev defaults."""
    env = os.getenv('FLASK_ENV', 'development')
    if env != 'production':
        return

    _INSECURE_DEFAULTS = {
        'SECRET_KEY': 'dev-secret-key-change-in-production',
        'JWT_SECRET_KEY': 'jwt-secret-change-in-production',
    }

    missing = [v for v in _REQUIRED_IN_PRODUCTION if not os.getenv(v)]
    insecure = [k for k, bad in _INSECURE_DEFAULTS.items() if os.getenv(k) == bad]

    errors = []
    if missing:
        errors.append(f"Missing required env vars: {', '.join(missing)}")
    if insecure:
        errors.append(f"Insecure default values still set for: {', '.join(insecure)}")

    if errors:
        for msg in errors:
            print(f"[CONFIG ERROR] {msg}", file=sys.stderr)
        sys.exit(1)

_validate_env()


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://hermes_user:hermes_password@localhost:5432/hermes_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('DEBUG', 'False') == 'True'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 20)),
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 40
    }

    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # JWT (short-lived access + long-lived refresh)
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # JWT blocklist — logout stores token jti in Redis; every request checks it.
    # The check is registered in app/__init__.py via @jwt.token_in_blocklist_loader.
    # On logout the route must call: app.redis.setex(f"blocklist:{jti}", 604800, "1")
    JWT_BLOCKLIST_ENABLED = True

    # CORS — comma-separated list of allowed origins.
    # Dev default allows the local frontend; override in production .env:
    #   CORS_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com
    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv('CORS_ORIGINS', 'http://localhost:8080,http://localhost:3000').split(',')
        if o.strip()
    ]

    # Email (Flask-Mail)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60        # 30-minute hard limit
    CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25-minute soft limit

    # API Request Handling
    REQUEST_TIMEOUT = 10
    REQUEST_MAX_RETRIES = 3
    REQUEST_RETRY_BACKOFF = [2, 4, 8]  # exponential backoff in seconds

    # Rate Limiting (flask-limiter)
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_IP_PER_MINUTE = 100
    RATE_LIMIT_USER_PER_MINUTE = 1000
    RATE_LIMIT_LOGIN_ATTEMPTS = 5
    RATE_LIMIT_LOGIN_DURATION = 300  # seconds

    # PostgreSQL Timeouts
    DB_CONNECT_TIMEOUT = 10       # seconds
    DB_STATEMENT_TIMEOUT = 30000  # milliseconds
    DB_POOL_TIMEOUT = 10          # seconds

    # Redis Connection
    REDIS_SOCKET_CONNECT_TIMEOUT = 5
    REDIS_SOCKET_KEEPALIVE = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS = {'TCP_KEEPIDLE': 60}
    REDIS_CONNECTION_POOL_MAX_CONNECTIONS = 50

    # Views counter batching.
    # Do NOT increment job_vacancies.views with a direct UPDATE on every request —
    # that causes row-level lock contention at scale. Instead:
    #   1. INCR views:{entity_type}:{entity_id} in Redis on each page hit
    #   2. A periodic Celery task reads these keys and flushes to PostgreSQL
    # VIEWS_FLUSH_INTERVAL_SECONDS controls how often the flush task runs.
    VIEWS_REDIS_KEY_PREFIX = 'views:'
    VIEWS_FLUSH_INTERVAL_SECONDS = int(os.getenv('VIEWS_FLUSH_INTERVAL_SECONDS', 300))

    # Data Retention Policies (cleanup via scheduled Celery tasks)
    NOTIFICATION_RETENTION_DAYS = 90
    LOG_RETENTION_DAYS = 30
    EMAIL_EVENT_RETENTION_DAYS = 60
    AUDIT_TRAIL_RETENTION_DAYS = 365
    SEARCH_HISTORY_RETENTION_DAYS = 180


def get_config():
    """Get configuration object"""
    return Config()
