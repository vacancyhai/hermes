"""
SQLAlchemy models — all imported here so Flask-Migrate can detect them.
"""
from .user import User, UserProfile
from .job import JobVacancy, UserJobApplication
from .notification import Notification
from .content import Result, AdmitCard, AnswerKey, Admission, Yojana, BoardResult
from .admin import AdminUser, AdminLog, RolePermission, AccessAuditLog
from .analytics import Category, PageView, SearchLog

__all__ = [
    'User', 'UserProfile',
    'JobVacancy', 'UserJobApplication',
    'Notification',
    'Result', 'AdmitCard', 'AnswerKey', 'Admission', 'Yojana', 'BoardResult',
    'AdminUser', 'AdminLog', 'RolePermission', 'AccessAuditLog',
    'Category', 'PageView', 'SearchLog',
]
