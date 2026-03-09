"""
Backend Flask Application Factory
"""
import redis as redis_lib
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.extensions import db, migrate


def create_app():
    """
    Application factory pattern for Flask.

    Wiring order matters:
    1. Config loaded
    2. SQLAlchemy + Migrate initialised
    3. CORS configured with allowed origins from config
    4. JWT initialised + blocklist loader registered (uses Redis)
    5. Redis client attached to app for blocklist + future caching
    6. Models imported (so Flask-Migrate detects schema)
    7. Blueprints registered
    8. Error handlers registered
    9. Celery bound to app context (so tasks can use db.session)
    """
    app = Flask(__name__)
    app.config.from_object('config.settings.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # CORS — only origins listed in CORS_ORIGINS are allowed
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # JWT
    jwt = JWTManager(app)

    # Redis client — shared across JWT blocklist + future use (views batching, caching)
    app.redis = redis_lib.from_url(
        app.config['REDIS_URL'],
        decode_responses=True,
        socket_connect_timeout=app.config.get('REDIS_SOCKET_CONNECT_TIMEOUT', 5),
    )

    # JWT token blocklist.
    # On logout the route must do:
    #   jti = get_jwt()['jti']
    #   app.redis.setex(f"blocklist:{jti}", int(JWT_REFRESH_TOKEN_EXPIRES.total_seconds()), "1")
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get('jti')
        if not jti:
            return False
        return app.redis.get(f'blocklist:{jti}') is not None

    # Standardized JWT error responses + proactive token rotation
    from app.middleware.auth_middleware import register_jwt_error_handlers, register_token_rotation
    register_jwt_error_handlers(jwt)
    register_token_rotation(app)

    # Import models so Flask-Migrate can detect schema changes
    from app import models  # noqa: F401

    # Rate limiting (shared limiter across all blueprints)
    from app.middleware.rate_limiter import init_limiter
    init_limiter(app)

    # Request ID propagation
    from app.middleware.request_id import register_request_id
    register_request_id(app)

    # CSRF protection (requires Redis)
    from app.middleware.csrf import register_csrf_protection
    register_csrf_protection(app)

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

    # Bind Celery to Flask app context so tasks can safely use db.session
    from app.tasks.celery_app import init_celery
    init_celery(app)

    return app
