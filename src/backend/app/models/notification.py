"""
Notification model
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(UUID(as_uuid=True))
    type = db.Column(db.String(60), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    message = db.Column(db.Text, nullable=False)
    action_url = db.Column(db.Text)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    sent_via = db.Column(ARRAY(db.Text))
    priority = db.Column(db.String(10), nullable=False, default='medium')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime(timezone=True))
    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=90)
    )

    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.type} user={self.user_id}>'
