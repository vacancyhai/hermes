"""Import all models so SQLAlchemy can resolve relationships."""

from app.models.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_profile import UserProfile  # noqa: F401
from app.models.job_vacancy import JobVacancy  # noqa: F401
from app.models.application import UserJobApplication  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.admin_log import AdminLog  # noqa: F401