"""
Backend Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

def create_app():
    """
    Application factory pattern for Flask
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.settings.Config')
    
    # Initialize extensions
    CORS(app)
    JWTManager(app)
    
    # Register blueprints
    from app.routes import auth, jobs, users, notifications, admin, health
    app.register_blueprint(auth.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(notifications.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(health.bp)
    
    # Register error handlers
    from app.middleware.error_handler import register_error_handlers
    register_error_handlers(app)
    
    return app
