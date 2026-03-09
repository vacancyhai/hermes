"""
Database helper utilities for common patterns (get-or-raise, error handling).
"""
import logging
from sqlalchemy.exc import OperationalError

from app.middleware.error_handler import NotFoundError, ExternalServiceError

logger = logging.getLogger(__name__)


def get_or_raise(model, filter_kwargs, error_code, error_message):
    """
    Fetch a single record from database or raise NotFoundError.
    
    Args:
        model: SQLAlchemy model class (e.g., User, JobVacancy)
        filter_kwargs: dict of filter conditions for query.filter_by(**kwargs)
        error_code: ErrorCode constant (for logging; message is more user-friendly)
        error_message: Human-readable error message for NotFoundError
    
    Raises:
        NotFoundError: If record not found
        ExternalServiceError: If database operation fails
    """
    try:
        record = model.query.filter_by(**filter_kwargs).first()
    except OperationalError as e:
        logger.error(f"DB error fetching {model.__name__}: {e}", exc_info=True)
        raise ExternalServiceError("Database")
    
    if not record:
        logger.debug(f"{model.__name__} not found: {filter_kwargs}")
        raise NotFoundError(error_message)
    
    return record
