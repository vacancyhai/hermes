"""
Frontend Configuration Settings
"""
import os

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8080))
    
    # Backend API
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000/api/v1')
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

def get_config():
    """Get configuration object"""
    return Config()
