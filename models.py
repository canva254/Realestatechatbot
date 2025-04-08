from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    """User model to store Telegram user information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('PropertyAlert', back_populates='user', lazy='dynamic')
    
    def __repr__(self):
        return f"<User {self.id}: {self.telegram_id} - {self.first_name}>"

class PropertyAlert(db.Model):
    """Property alert subscriptions for users"""
    __tablename__ = 'property_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    location = db.Column(db.String(100), nullable=True)  # Optional location filter
    min_price = db.Column(db.Integer, nullable=True)  # Optional min price filter
    max_price = db.Column(db.Integer, nullable=True)  # Optional max price filter
    min_bedrooms = db.Column(db.Integer, nullable=True)  # Optional min bedrooms filter
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', back_populates='subscriptions')
    
    def __repr__(self):
        filters = []
        if self.location:
            filters.append(f"location={self.location}")
        if self.min_price:
            filters.append(f"min_price={self.min_price}")
        if self.max_price:
            filters.append(f"max_price={self.max_price}")
        if self.min_bedrooms:
            filters.append(f"min_bedrooms={self.min_bedrooms}")
        
        filter_str = ", ".join(filters) if filters else "no filters"
        return f"<PropertyAlert {self.id}: user_id={self.user_id}, {filter_str}>"

class PropertyListing(db.Model):
    """Stores property listings from the API to track new ones"""
    __tablename__ = 'property_listings'
    
    id = db.Column(db.Integer, primary_key=True)
    wp_id = db.Column(db.Integer, unique=True, nullable=False)  # WordPress property ID
    title = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    price = db.Column(db.String(100), nullable=True)  # Store as string to preserve exact format
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Integer, nullable=True)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    property_url = db.Column(db.String(255), nullable=True)
    details = db.Column(JSONB, nullable=True)  # Store additional property details as JSON
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PropertyListing {self.id}: wp_id={self.wp_id}, title={self.title[:20]}...>"

class AlertNotification(db.Model):
    """Track which alerts have been sent to avoid duplicate notifications"""
    __tablename__ = 'alert_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property_listings.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure we don't send duplicate notifications to the same user for the same property
    __table_args__ = (
        db.UniqueConstraint('user_id', 'property_id', name='uq_user_property'),
    )
    
    def __repr__(self):
        return f"<AlertNotification {self.id}: user_id={self.user_id}, property_id={self.property_id}>"