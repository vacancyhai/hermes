"""
Admin Frontend Flask Application Factory
"""
from flask import Flask, session
from flask_login import LoginManager


def create_app():
    """
    Application factory pattern for Flask admin frontend.
    Only admin and operator roles are permitted to log in here.
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object('config.settings.Config')

    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        from app.utils.session_manager import get_user_data
        data = get_user_data(session)
        if data and data.get("user_id") == user_id:
            return User.from_session(data)
        return None

    # Register blueprints
    from app.routes import main, auth, dashboard, users, jobs, errors
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(errors.bp)

    return app
