"""
User and UserProfile models
"""
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default='user')
    status = db.Column(db.String(20), nullable=False, default='active')
    avatar_url = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    is_email_verified = db.Column(db.Boolean, nullable=False, default=False)
    is_mobile_verified = db.Column(db.Boolean, nullable=False, default=False)
    last_login = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = db.relationship('UserProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    applications = db.relationship('UserJobApplication', back_populates='user', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    category = db.Column(db.String(20))
    is_pwd = db.Column(db.Boolean, nullable=False, default=False)
    is_ex_serviceman = db.Column(db.Boolean, nullable=False, default=False)
    state = db.Column(db.String(100))
    city = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    highest_qualification = db.Column(db.String(50))
    education = db.Column(JSONB, nullable=False, default=dict)
    physical_details = db.Column(JSONB, nullable=False, default=dict)
    quick_filters = db.Column(JSONB, nullable=False, default=dict)
    notification_preferences = db.Column(JSONB, nullable=False, default=dict)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='profile')

    def __repr__(self):
        return f'<UserProfile user_id={self.user_id}>'
