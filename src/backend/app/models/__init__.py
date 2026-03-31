"""Import all models so SQLAlchemy can resolve relationships."""

from app.models.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_profile import UserProfile  # noqa: F401
from app.models.job import Job  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.admin_user import AdminUser  # noqa: F401
from app.models.admin_log import AdminLog  # noqa: F401
from app.models.user_device import UserDevice  # noqa: F401
from app.models.notification_delivery_log import NotificationDeliveryLog  # noqa: F401
from app.models.admit_card import AdmitCard  # noqa: F401
from app.models.answer_key import AnswerKey  # noqa: F401
from app.models.result import Result  # noqa: F401
from app.models.entrance_exam import EntranceExam  # noqa: F401
from app.models.user_watch import UserWatch  # noqa: F401