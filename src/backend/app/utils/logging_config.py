"""
Structured JSON Logging Configuration

Configures JSON logging for production-ready log aggregation.
Includes request_id injection for request tracing.
"""
import logging
import os
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that includes request context."""
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = self.formatTime(record, self.datefmt)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add request_id if available (injected by request_id middleware)
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        # Add environment
        log_record['environment'] = os.getenv('FLASK_ENV', 'development')


def configure_logging(app):
    """
    Configure structured JSON logging for the application.
    
    In development: keeps human-readable format
    In production: uses JSON format for log aggregators (ELK, CloudWatch, Datadog)
    """
    env = os.getenv('FLASK_ENV', 'development')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    if env == 'production' or os.getenv('LOG_FORMAT', '').lower() == 'json':
        # Use JSON formatter for production
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    else:
        # Use simple formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure Flask app logger
    app.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Suppress overly verbose loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Only show SQL in debug mode
    if app.config.get('SQLALCHEMY_ECHO'):
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    else:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    app.logger.info(f"Logging configured: env={env}, level={log_level}, format={'JSON' if env == 'production' else 'TEXT'}")


def inject_request_id_to_logs():
    """
    Inject request_id into all log records within request context.
    Called by request_id middleware.
    """
    from flask import g
    
    class RequestIdFilter(logging.Filter):
        def filter(self, record):
            record.request_id = getattr(g, 'request_id', 'N/A')
            return True
    
    return RequestIdFilter()
