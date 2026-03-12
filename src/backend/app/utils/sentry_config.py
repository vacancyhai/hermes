"""
Sentry Error Tracking Integration

Configures Sentry for production error tracking and monitoring.
Environment-aware: only enables in production unless SENTRY_DSN explicitly set.
"""
import os
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


logger = logging.getLogger(__name__)


def init_sentry(app):
    """
    Initialize Sentry error tracking.
    
    Requires SENTRY_DSN environment variable to be set.
    Optional environment variables:
    - SENTRY_ENVIRONMENT (defaults to FLASK_ENV)
    - SENTRY_TRACES_SAMPLE_RATE (defaults to 0.1 for 10% sampling)
    - SENTRY_PROFILES_SAMPLE_RATE (defaults to 0.1 for 10% sampling)
    """
    sentry_dsn = os.getenv('SENTRY_DSN')
    
    if not sentry_dsn:
        logger.info("Sentry disabled: SENTRY_DSN not set")
        return
    
    environment = os.getenv('SENTRY_ENVIRONMENT', os.getenv('FLASK_ENV', 'development'))
    traces_sample_rate = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
    profiles_sample_rate = float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1'))
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        integrations=[
            FlaskIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
            SqlalchemyIntegration(),
        ],
        # Send user context
        send_default_pii=False,  # Don't send PII by default
        
        # Attach server name
        server_name=os.getenv('HOSTNAME', 'unknown'),
        
        # Release tracking (useful for identifying which version has errors)
        release=os.getenv('APP_VERSION', 'unknown'),
        
        # Before send hook to scrub sensitive data
        before_send=before_send_hook,
    )
    
    logger.info(f"Sentry initialized: environment={environment}, traces_sample_rate={traces_sample_rate}")


def before_send_hook(event, hint):
    """
    Hook called before sending event to Sentry.
    Use this to scrub sensitive data or filter events.
    """
    # Don't send health check errors
    if event.get('request', {}).get('url', '').endswith('/health'):
        return None
    
    # Scrub sensitive headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        sensitive_headers = ['Authorization', 'Cookie', 'X-CSRF-Token']
        for header in sensitive_headers:
            if header in headers:
                headers[header] = '[Filtered]'
    
    return event


def capture_exception(exc, context=None):
    """
    Manually capture an exception and send to Sentry.
    
    Args:
        exc: Exception instance
        context: Optional dict with additional context
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            sentry_sdk.capture_exception(exc)
    else:
        sentry_sdk.capture_exception(exc)


def capture_message(message, level='info', context=None):
    """
    Manually capture a message and send to Sentry.
    
    Args:
        message: Message string
        level: Severity level (debug, info, warning, error, fatal)
        context: Optional dict with additional context
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            sentry_sdk.capture_message(message, level)
    else:
        sentry_sdk.capture_message(message, level)
