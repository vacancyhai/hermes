"""
Admin Frontend Configuration Settings
"""
import os
from datetime import timedelta


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8081))

    # Backend API
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000/api/v1')

    # Session — cookie-based (JWT tokens stored in Flask session cookie)
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.getenv('SESSION_TIMEOUT', 3600)))


def get_config():
    """Get configuration object (used by run.py for dev server)"""
    return Config()
