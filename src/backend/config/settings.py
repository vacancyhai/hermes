"""
Backend Configuration Settings
"""
import os
from datetime import timedelta

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
    
    # JWT (⚡ SECURITY: Short-lived access + long-lived refresh)
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)  # Short-lived: auto-refresh
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)     # Long-lived: user stays logged in
    
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
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
    
    # API Request Handling
    REQUEST_TIMEOUT = 10  # seconds per API request
    REQUEST_MAX_RETRIES = 3
    REQUEST_RETRY_BACKOFF = [2, 4, 8]  # exponential backoff in seconds
    
    # Rate Limiting (⚡ Per-user + IP-based)
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_IP_PER_MINUTE = 100  # 100 requests per minute per IP
    RATE_LIMIT_USER_PER_MINUTE = 1000  # 1000 requests per minute per authenticated user
    RATE_LIMIT_LOGIN_ATTEMPTS = 5  # max 5 failed attempts before lockout
    RATE_LIMIT_LOGIN_DURATION = 300  # 5 minutes lockout
    
    # PostgreSQL Timeouts
    DB_CONNECT_TIMEOUT = 10  # seconds
    DB_STATEMENT_TIMEOUT = 30000  # milliseconds
    DB_POOL_TIMEOUT = 10  # seconds waiting for connection
    
    # Redis Connection
    REDIS_SOCKET_CONNECT_TIMEOUT = 5  # seconds
    REDIS_SOCKET_KEEPALIVE = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS = {'TCP_KEEPIDLE': 60}
    REDIS_CONNECTION_POOL_MAX_CONNECTIONS = 50
    
    # Data Retention Policies (PostgreSQL - cleanup via scheduled Celery tasks)
    NOTIFICATION_RETENTION_DAYS = 90  # auto-delete old notifications
    LOG_RETENTION_DAYS = 30  # auto-delete old application logs
    EMAIL_EVENT_RETENTION_DAYS = 60  # keep email delivery logs
    AUDIT_TRAIL_RETENTION_DAYS = 365  # compliance requirement
    SEARCH_HISTORY_RETENTION_DAYS = 180  # 6 months

def get_config():
    """Get configuration object"""
    return Config()
