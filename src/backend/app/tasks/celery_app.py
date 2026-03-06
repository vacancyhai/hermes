"""
Celery App - Stub (tasks implemented in EPIC_08)
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
