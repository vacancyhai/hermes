"""
Frontend Flask Application Factory
"""
from flask import Flask, session
from flask_login import LoginManager

def create_app():
    """
    Application factory pattern for Flask
    """
    import os
    _base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app = Flask(__name__, template_folder=os.path.join(_base, 'templates'), static_folder=os.path.join(_base, 'static'))
    
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

    # Register CSRF protection
    from app.utils.csrf import check_csrf, generate_csrf_token
    app.before_request(check_csrf)
    app.jinja_env.globals['csrf_token'] = generate_csrf_token

    # Register blueprints
    from app.routes import main, auth, jobs, profile, admin, errors
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(errors.bp)

    # Register Jinja2 template filters / helpers
    from app.utils.helpers import register_template_helpers
    register_template_helpers(app)

    return app
