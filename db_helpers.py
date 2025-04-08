import logging
from datetime import datetime
from models import db, User, PropertyAlert, PropertyListing, AlertNotification
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_or_create_user(telegram_id, first_name=None, last_name=None, username=None):
    """Get an existing user or create a new one if they don't exist"""
    try:
        user = User.query.filter_by(telegram_id=telegram_id).first()
        
        if user:
            # Update last interaction time
            user.last_interaction = datetime.utcnow()
            # Update user info if changed
            if first_name and user.first_name != first_name:
                user.first_name = first_name
            if last_name and user.last_name != last_name:
                user.last_name = last_name
            if username and user.username != username:
                user.username = username
            db.session.commit()
        else:
            # Create new user
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user: {user}")
        
        return user
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while getting/creating user: {e}")
        return None

def create_property_alert(user_id, location=None, min_price=None, max_price=None, min_bedrooms=None):
    """Create a property alert subscription for a user"""
    try:
        alert = PropertyAlert(
            user_id=user_id,
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_bedrooms=min_bedrooms
        )
        db.session.add(alert)
        db.session.commit()
        logger.info(f"Created property alert: {alert}")
        return alert
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while creating property alert: {e}")
        return None

def get_user_alerts(user_id):
    """Get all active property alerts for a user"""
    try:
        return PropertyAlert.query.filter_by(user_id=user_id, is_active=True).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while getting user alerts: {e}")
        return []

def delete_property_alert(alert_id, user_id):
    """Delete a property alert by ID, ensuring it belongs to the specified user"""
    try:
        alert = PropertyAlert.query.filter_by(id=alert_id, user_id=user_id).first()
        if alert:
            db.session.delete(alert)
            db.session.commit()
            logger.info(f"Deleted property alert: {alert}")
            return True
        return False
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while deleting property alert: {e}")
        return False

def deactivate_property_alert(alert_id, user_id):
    """Deactivate a property alert by ID, ensuring it belongs to the specified user"""
    try:
        alert = PropertyAlert.query.filter_by(id=alert_id, user_id=user_id).first()
        if alert:
            alert.is_active = False
            db.session.commit()
            logger.info(f"Deactivated property alert: {alert}")
            return True
        return False
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while deactivating property alert: {e}")
        return False

def save_property_listing(property_data):
    """Save a property from the API to track it in the database"""
    try:
        wp_id = property_data.get('id')
        if not wp_id:
            logger.error("Property data missing ID")
            return None
        
        # Check if the property already exists
        existing = PropertyListing.query.filter_by(wp_id=wp_id).first()
        if existing:
            logger.info(f"Property already exists: {wp_id}")
            # Update any changed fields
            existing.last_updated = datetime.utcnow()
            db.session.commit()
            return existing
        
        # Extract property details from the API data
        title = property_data.get('title', {}).get('rendered', 'Unnamed Property') 
        
        # Extract ACF fields
        acf = property_data.get('acf', {})
        location = acf.get('location')
        price = acf.get('price')
        
        # Parse bedrooms - extract the first number from the string
        bedrooms_text = acf.get('bedrooms', '')
        bedrooms = None
        if bedrooms_text:
            import re
            # Extract just the number from text like "4 Bedrooms ALL ensuite + DSQ"
            bedroom_match = re.search(r'\d+', str(bedrooms_text))
            if bedroom_match:
                bedrooms = int(bedroom_match.group())
        
        # Parse bathrooms - ensure it's an integer
        bathrooms_text = acf.get('bathrooms', '')
        bathrooms = None
        if bathrooms_text:
            try:
                bathrooms = int(bathrooms_text)
            except (ValueError, TypeError):
                # If bathrooms can't be converted to int, try to extract the first number
                import re
                bathroom_match = re.search(r'\d+', str(bathrooms_text))
                if bathroom_match:
                    bathrooms = int(bathroom_match.group())
        
        # Get property URL
        property_url = property_data.get('link')
        
        # Get thumbnail URL
        thumbnail_url = None
        if '_embedded' in property_data and 'wp:featuredmedia' in property_data['_embedded']:
            featured_media = property_data['_embedded']['wp:featuredmedia']
            if featured_media and len(featured_media) > 0 and 'source_url' in featured_media[0]:
                thumbnail_url = featured_media[0]['source_url']
        
        # Create new property listing
        property_listing = PropertyListing(
            wp_id=wp_id,
            title=title,
            location=location,
            price=price,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            thumbnail_url=thumbnail_url,
            property_url=property_url,
            details=property_data  # Store the complete property data as JSON
        )
        
        db.session.add(property_listing)
        db.session.commit()
        logger.info(f"Saved new property: {property_listing}")
        return property_listing
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while saving property: {e}")
        return None

def get_new_properties_since(timestamp):
    """Get properties added since the given timestamp"""
    try:
        return PropertyListing.query.filter(PropertyListing.first_seen >= timestamp).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while getting new properties: {e}")
        return []

def get_matching_properties_for_alert(alert):
    """Get properties that match the criteria in a PropertyAlert"""
    try:
        query = PropertyListing.query
        
        # Apply filters based on alert criteria
        if alert.location:
            query = query.filter(PropertyListing.location == alert.location)
        if alert.min_price is not None:
            # Convert string price to integer for comparison
            # This is a simplification; in practice would need more robust price parsing
            query = query.filter(PropertyListing.price.cast(db.Integer) >= alert.min_price)
        if alert.max_price is not None:
            query = query.filter(PropertyListing.price.cast(db.Integer) <= alert.max_price)
        if alert.min_bedrooms is not None:
            query = query.filter(PropertyListing.bedrooms >= alert.min_bedrooms)
        
        return query.all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while getting matching properties: {e}")
        return []

def record_notification(user_id, property_id):
    """Record that a notification was sent to avoid duplicate alerts"""
    try:
        # Check if notification was already sent
        existing = AlertNotification.query.filter_by(
            user_id=user_id, 
            property_id=property_id
        ).first()
        
        if existing:
            logger.info(f"Notification already sent to user {user_id} for property {property_id}")
            return existing
        
        # Create new notification record
        notification = AlertNotification(user_id=user_id, property_id=property_id)
        db.session.add(notification)
        db.session.commit()
        logger.info(f"Recorded new notification: {notification}")
        return notification
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while recording notification: {e}")
        return None

def get_users_for_notifications(property_listing):
    """Get all users who should be notified about this property based on their alerts"""
    try:
        # Get all active alerts that match this property
        matching_alerts = []
        
        # Get all active alerts
        all_alerts = PropertyAlert.query.filter_by(is_active=True).all()
        
        for alert in all_alerts:
            matches = True
            
            # Check location filter
            if alert.location and property_listing.location != alert.location:
                matches = False
            
            # Check price filters if the property has a numeric price
            if property_listing.price and property_listing.price.isdigit():
                price_value = int(property_listing.price)
                if alert.min_price is not None and price_value < alert.min_price:
                    matches = False
                if alert.max_price is not None and price_value > alert.max_price:
                    matches = False
            
            # Check bedroom filter
            if alert.min_bedrooms is not None and (
                property_listing.bedrooms is None or 
                property_listing.bedrooms < alert.min_bedrooms
            ):
                matches = False
            
            if matches:
                matching_alerts.append(alert)
        
        # Get unique users who haven't been notified yet
        users_to_notify = []
        for alert in matching_alerts:
            # Check if user was already notified about this property
            notification = AlertNotification.query.filter_by(
                user_id=alert.user_id,
                property_id=property_listing.id
            ).first()
            
            if not notification:
                # Add user to notification list if not already included
                if alert.user_id not in [u.id for u in users_to_notify]:
                    user = User.query.get(alert.user_id)
                    if user and user.is_active:
                        users_to_notify.append(user)
        
        return users_to_notify
    
    except SQLAlchemyError as e:
        logger.error(f"Database error while getting users for notifications: {e}")
        return []