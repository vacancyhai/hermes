"""
Celery application instance.

init_celery(app) must be called from the Flask app factory so that every
task runs inside a Flask application context and can safely use db.session,
current_app, and other Flask-bound resources.
"""
from celery import Celery
import os

celery_app = Celery(
    'hermes',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone=os.getenv('CELERY_TIMEZONE', 'UTC'),
    enable_utc=True,
    task_track_started=True,
)


def init_celery(app):
    """
    Wrap every Celery task so it executes inside a Flask application context.

    Call this once from create_app() after the Flask app is fully configured.
    Without this, tasks that access db.session or current_app will raise
    "RuntimeError: Working outside of application context."
    """
    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app
