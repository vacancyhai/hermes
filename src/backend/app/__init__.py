"""
Backend Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.extensions import db, migrate


def create_app():
    """
    Application factory pattern for Flask
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object('config.settings.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    JWTManager(app)

    # Import models so Flask-Migrate can detect schema changes
    from app import models  # noqa: F401

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
