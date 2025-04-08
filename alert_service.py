import logging
import asyncio
import time
from datetime import datetime, timedelta
from app import app
from api import fetch_properties
from db_helpers import (
    save_property_listing, 
    get_users_for_notifications,
    record_notification
)
from utils import format_property_message, get_property_image_url

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variables for sync
last_check_time = None
check_interval = 30 * 60  # Check for new properties every 30 minutes

async def check_for_new_properties(bot):
    """Check for new properties and send alerts to subscribed users"""
    global last_check_time
    
    logger.info("Checking for new properties...")
    current_time = time.time()
    
    # Skip if we checked recently
    if last_check_time and (current_time - last_check_time < check_interval):
        remaining = int(check_interval - (current_time - last_check_time))
        logger.info(f"Skipping property check, next check in {remaining} seconds")
        return
    
    # Update the last check time
    last_check_time = current_time
    
    # Fetch all properties from the API
    properties = fetch_properties()
    if not properties:
        logger.warning("Failed to fetch properties from API")
        return
    
    logger.info(f"Fetched {len(properties)} properties from API")
    
    # Process each property with the Flask app context
    with app.app_context():
        for property_data in properties:
            # Save property to database (this will track if it's new)
            property_listing = save_property_listing(property_data)
            
            if not property_listing:
                logger.warning(f"Failed to save property: {property_data.get('id')}")
                continue
            
            # Check if this is a new property (created within the last check interval)
            time_threshold = datetime.utcnow() - timedelta(seconds=check_interval)
            if property_listing.first_seen >= time_threshold:
                logger.info(f"New property detected: {property_listing.title}")
                
                # Find users who should be notified based on alert preferences
                users_to_notify = get_users_for_notifications(property_listing)
                
                if users_to_notify:
                    logger.info(f"Sending alerts to {len(users_to_notify)} users")
                    await send_property_alerts(bot, users_to_notify, property_listing, property_data)
                else:
                    logger.info("No users match alert criteria for this property")

async def send_property_alerts(bot, users, property_listing, property_data):
    """Send alerts about a new property to subscribed users"""
    # Format the property message
    message = format_property_message(property_data)
    message = f"🔔 *NEW PROPERTY ALERT* 🔔\n\n{message}"
    
    # Get property image URL
    image_url = get_property_image_url(property_data)
    
    # Send notification to each user
    for user in users:
        try:
            # Record that we're sending this notification
            with app.app_context():
                record_notification(user.id, property_listing.id)
            
            # Send the property alert
            if image_url:
                await bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=image_url,
                    caption=message,
                    parse_mode="Markdown"
                )
            else:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    parse_mode="Markdown"
                )
            
            logger.info(f"Sent property alert to user {user.telegram_id}")
            
            # Sleep briefly to avoid hitting rate limits
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error sending property alert to user {user.telegram_id}: {e}")

async def start_property_alert_service(bot):
    """Start the background task that checks for new properties and sends alerts"""
    logger.info("Starting property alert service...")
    
    while True:
        try:
            await check_for_new_properties(bot)
        except Exception as e:
            logger.error(f"Error in property alert service: {e}")
        
        # Check for new properties on a schedule
        await asyncio.sleep(60)  # Check every minute if it's time to run the full check