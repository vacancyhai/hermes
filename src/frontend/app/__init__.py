"""
Frontend Flask Application Factory
"""
from flask import Flask
from flask_login import LoginManager

def create_app():
    """
    Application factory pattern for Flask
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
        # Stub: implement with real User model lookup in EPIC_03/EPIC_10
        return None

    # Register blueprints
    from app.routes import main, auth, jobs, profile, admin, errors
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(errors.bp)
    
    return app
