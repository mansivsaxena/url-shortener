from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    salt = db.Column(db.LargeBinary, nullable=False)
    pw_hash = db.Column(db.LargeBinary, nullable=False) 
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    token = db.Column(db.Text)
    
    # Relationship: One User has Many URLs
    urls = db.relationship('URL', backref='owner', cascade="all, delete-orphan")

class URL(db.Model):
    __tablename__ = 'urls'
    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    long_url = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    click_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime(timezone=True))
    expires_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))