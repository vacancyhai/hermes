"""
Analytics models: Category, PageView, SearchLog
"""
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY
from app.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey('categories.id', ondelete='SET NULL'))
    type = db.Column(db.String(30), nullable=False)
    icon = db.Column(db.String(100))
    description = db.Column(db.Text)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    job_count = db.Column(db.Integer, nullable=False, default=0)
    meta_title = db.Column(db.String(300))
    meta_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

    def __repr__(self):
        return f'<Category {self.name}>'


class PageView(db.Model):
    __tablename__ = 'page_views'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = db.Column(db.String(30), nullable=False)
    entity_id = db.Column(UUID(as_uuid=True))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'))
    session_id = db.Column(db.String(100))
    ip_address = db.Column(INET)
    user_agent = db.Column(db.Text)
    device_type = db.Column(db.String(20))
    browser = db.Column(db.String(50))
    os = db.Column(db.String(50))
    referrer = db.Column(db.Text)
    page_url = db.Column(db.Text)
    time_spent_seconds = db.Column(db.Integer)
    viewed_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<PageView {self.entity_type} {self.entity_id}>'


class SearchLog(db.Model):
    __tablename__ = 'search_logs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'))
    session_id = db.Column(db.String(100))
    search_query = db.Column(db.String(500), nullable=False)
    filters_applied = db.Column(JSONB)
    results_count = db.Column(db.Integer, nullable=False, default=0)
    clicked_results = db.Column(ARRAY(UUID(as_uuid=True)))
    first_click_position = db.Column(db.Integer)
    time_to_first_click_seconds = db.Column(db.Integer)
    no_results = db.Column(db.Boolean, nullable=False, default=False)
    searched_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<SearchLog "{self.search_query}">'
