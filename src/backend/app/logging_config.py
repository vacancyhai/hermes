"""Structured JSON logging configuration using structlog."""

import logging

import structlog


def setup_logging():
    """Configure structlog for JSON output.

    All backend services (FastAPI, Celery) use this for consistent
    structured logs with request_id, user_id, endpoint, duration_ms.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set root logger to INFO
    logging.basicConfig(format="%(message)s", level=logging.INFO)
