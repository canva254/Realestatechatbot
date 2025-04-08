import logging
import re
import time
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, MessageHandler, filters
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from config import TELEGRAM_TOKEN, BOT_MESSAGES, ERROR_MESSAGES, CACHE_TTL
from api import get_locations, get_properties_by_location
from utils import format_property_message, get_property_image_url
from app import app
from db_helpers import (
    get_or_create_user,
    create_property_alert,
    get_user_alerts,
    delete_property_alert
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
SELECTING_LOCATION, SELECTING_BUDGET, SELECTING_BEDROOMS, VIEWING_PROPERTIES, CHATTING = range(5)

# Alert conversation states
(ALERT_MAIN, ALERT_CREATING, ALERT_LOCATION, ALERT_MIN_PRICE, 
ALERT_MAX_PRICE, ALERT_MIN_BEDROOMS, ALERT_LIST, ALERT_DELETE_CONFIRM) = range(5, 13)

# Property display cache to improve performance
# Structure: {location: {last_updated: timestamp, properties: [...]}}
property_display_cache = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued and immediately show available properties."""
    # Get user's first name for personalized greeting
    user_first_name = update.message.from_user.first_name
    
    # Send welcome message
    await update.message.reply_text(
        f"👋 *Welcome to Avier Homes Property Bot, {user_first_name}!*\n\n"
        "I can help you find your dream home in Kenya. Let me show you our available properties right away!\n\n"
        "You can also ask me things like:\n"
        "- \"Show me properties in Lavington\"\n"
        "- \"I'm looking for a house in Kilimani\"\n"
        "- \"Find properties\"\n\n"
        "Or just say hello to start exploring!",
        parse_mode="Markdown"
    )
    
    # Show loading message while fetching properties
    loading_message = await update.message.reply_text(BOT_MESSAGES["loading"])
    
    # Get all available properties
    from api import fetch_properties
    properties = fetch_properties()
    
    if not properties or len(properties) == 0:
        await loading_message.edit_text("Sorry, I couldn't find any properties at the moment. Please try again later.")
        return
    
    # Get available locations
    locations = get_locations()
    
    if locations:
        # Create a message with the count of available properties
        property_count_text = f"We have {len(properties)} properties available across {len(locations)} locations:"
        
        # Create keyboard with locations
        keyboard = []
        for location in locations:
            if not isinstance(location, str):
                logger.warning(f"Skipping non-string location: {location}")
                continue
            
            # Count properties in this location
            location_properties = get_properties_by_location(location)
            count = len(location_properties) if location_properties else 0
            
            # Ensure button text is a string
            button_text = f"{location} ({count} properties)"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"location:{location}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Show location options
        await loading_message.edit_text(
            f"{property_count_text}\n\nPlease select a location to view properties:",
            reply_markup=reply_markup
        )
    else:
        await loading_message.edit_text("Sorry, I couldn't find any locations. Please try again later.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    await update.message.reply_text(
        BOT_MESSAGES["help"],
        parse_mode="Markdown"
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /search command by showing location options."""
    # Show loading message
    message = await update.message.reply_text(BOT_MESSAGES["loading"])
    
    # Get locations from API
    locations = get_locations()
    
    # If no locations found, show error message
    if not locations:
        await message.edit_text(ERROR_MESSAGES["no_locations"])
        return ConversationHandler.END
    
    # Create keyboard with locations
    keyboard = []
    for location in locations:
        if not isinstance(location, str):
            logger.warning(f"Skipping non-string location in search: {location}")
            continue
        
        # Ensure button text is a string
        keyboard.append([InlineKeyboardButton(str(location), callback_data=f"location:{location}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Show location options
    await message.edit_text(
        BOT_MESSAGES["search_prompt"],
        reply_markup=reply_markup
    )
    
    return SELECTING_LOCATION
    
async def handle_text_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle text-based location selection during the search process."""
    user_text = update.message.text.strip()
    
    # Get available locations
    locations = get_locations()
    if not locations:
        await update.message.reply_text(ERROR_MESSAGES["no_locations"])
        return ConversationHandler.END
    
    # Check if the text matches any available location (case insensitive)
    matched_location = None
    for location in locations:
        if isinstance(location, str) and location.lower() == user_text.lower():
            matched_location = location
            break
    
    # If no exact match, try partial match
    if not matched_location:
        for location in locations:
            if isinstance(location, str) and location.lower() in user_text.lower():
                matched_location = location
                break
                
    # If still no match, show available locations
    if not matched_location:
        await update.message.reply_text(
            f"I couldn't find '{user_text}' in our available locations. Please select from the following:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(str(loc), callback_data=f"location:{loc}")]
                for loc in locations if isinstance(loc, str)
            ])
        )
        return SELECTING_LOCATION
        
    # We found a matching location
    context.user_data["location"] = matched_location
    
    # Show loading message
    message = await update.message.reply_text(BOT_MESSAGES["loading"])
    
    # Check if we have cached properties for this location
    current_time = time.time()
    if (matched_location in property_display_cache and 
        current_time - property_display_cache[matched_location]["last_updated"] < CACHE_TTL):
        logger.info(f"Using cached properties for {matched_location}")
        properties = property_display_cache[matched_location]["properties"]
    else:
        # Get properties for selected location
        logger.info(f"Fetching fresh properties for {matched_location}")
        properties = get_properties_by_location(matched_location)
        
        # Cache the results
        if properties:
            property_display_cache[matched_location] = {
                "last_updated": current_time,
                "properties": properties
            }
    
    # If no properties found, show error message
    if not properties:
        await message.edit_text(f"{BOT_MESSAGES['property_not_found']} ({matched_location})")
        return await search(update, context)
    
    # Store properties in context
    context.user_data["properties"] = properties
    context.user_data["current_index"] = 0
    
    # Display property count
    await message.edit_text(
        BOT_MESSAGES["property_count"].format(len(properties), matched_location)
    )
    
    # Get first property
    property_data = properties[0]
    
    # Format property message
    message_text = format_property_message(property_data)
    
    # Get property image URL
    image_url = get_property_image_url(property_data)
    
    # Create navigation buttons
    keyboard = []
    if len(properties) > 1:
        keyboard.append([InlineKeyboardButton("Next Property ➡️", callback_data="property:next")])
    keyboard.append([InlineKeyboardButton("New Search 🔍", callback_data="property:back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send property with image
    if image_url:
        await update.message.reply_photo(
            photo=image_url,
            caption=message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    return VIEWING_PROPERTIES

async def location_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract location from callback data
    location = query.data.split(":")[1]
    context.user_data["location"] = location
    
    # Show loading message
    await query.edit_message_text(BOT_MESSAGES["loading"])
    
    # Check if we have cached properties for this location and if they're still valid
    current_time = time.time()
    if (location in property_display_cache and 
        current_time - property_display_cache[location]["last_updated"] < CACHE_TTL):
        logger.info(f"Using cached properties for {location}")
        properties = property_display_cache[location]["properties"]
    else:
        # Get properties for selected location
        logger.info(f"Fetching fresh properties for {location}")
        properties = get_properties_by_location(location)
        
        # Cache the results
        if properties:
            property_display_cache[location] = {
                "last_updated": current_time,
                "properties": properties
            }
    
    # If no properties found, show error message
    if not properties:
        await query.edit_message_text(BOT_MESSAGES["property_not_found"])
        return ConversationHandler.END
    
    # Store properties in context
    context.user_data["properties"] = properties
    context.user_data["current_index"] = 0
    
    # Show first property
    await show_property(update, context)
    
    return VIEWING_PROPERTIES

async def show_property(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show a property with image and details."""
    query = update.callback_query
    
    properties = context.user_data.get("properties", [])
    current_index = context.user_data.get("current_index", 0)
    location = context.user_data.get("location", "Unknown")
    
    # If no properties left, end conversation
    if not properties or current_index >= len(properties):
        if query:
            await query.edit_message_text(BOT_MESSAGES["property_not_found"])
        return ConversationHandler.END
    
    # Get current property
    property_data = properties[current_index]
    
    # Format property message
    message = format_property_message(property_data)
    
    # Get property image URL
    image_url = get_property_image_url(property_data)
    
    # Create navigation buttons
    keyboard = []
    
    # Show next property button if there are more properties
    if current_index < len(properties) - 1:
        keyboard.append([InlineKeyboardButton("Next Property ➡️", callback_data="property:next")])
    else:
        keyboard.append([InlineKeyboardButton("New Search 🔍", callback_data="property:new_search")])
    
    # Always show back to search button
    keyboard.append([InlineKeyboardButton("Back to Search 🔙", callback_data="property:back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # If this is the first property, show property count message
    if current_index == 0 and query:
        await query.edit_message_text(
            BOT_MESSAGES["property_count"].format(len(properties), location)
        )
    
    # Send property with image
    if query:
        if image_url:
            await query.message.reply_photo(
                photo=image_url,
                caption=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            # Delete the previous message (loading or property count)
            await query.delete_message()
        else:
            # If no image, just send the text
            await query.edit_message_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    
    return VIEWING_PROPERTIES

async def property_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle property navigation."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split(":")[1]
    
    if action == "next":
        # Move to next property
        context.user_data["current_index"] += 1
        return await show_property(update, context)
    
    elif action == "back":
        # Go back to location selection
        await search(update, query)
        return SELECTING_LOCATION
    
    elif action == "new_search":
        # Start a new search
        await search(update, query)
        return SELECTING_LOCATION
    
    return VIEWING_PROPERTIES

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    if update.message:
        await update.message.reply_text("Search cancelled. You can start a new search anytime by typing 'find properties' or using the /search command.")
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle regular text messages from users in a conversational way."""
    message_text = update.message.text.lower()
    user_first_name = update.message.from_user.first_name
    
    # Check for greetings
    greeting_words = ["hi", "hello", "hey", "howdy", "greetings", "good morning", "good afternoon", "good evening"]
    if any(message_text.startswith(word) for word in greeting_words):
        # Send welcome greeting
        greeting_msg = await update.message.reply_text(
            f"Hello {user_first_name}! 👋 {BOT_MESSAGES['greeting']}\n\nI'll help you find your perfect property in Kenya."
        )
        
        # Show loading message while fetching properties
        loading_message = await update.message.reply_text(BOT_MESSAGES["loading"])
        
        # Get all available properties
        from api import fetch_properties
        properties = fetch_properties()
        
        if not properties or len(properties) == 0:
            await loading_message.edit_text("Sorry, I couldn't find any properties at the moment. Please try again later.")
            return CHATTING
        
        # Get available locations
        locations = get_locations()
        
        if locations:
            # Create a message with the count of available properties
            property_count_text = f"We have {len(properties)} properties available across {len(locations)} locations:"
            
            # Create keyboard with locations
            keyboard = []
            for location in locations:
                if not isinstance(location, str):
                    logger.warning(f"Skipping non-string location in handle_message: {location}")
                    continue
                    
                # Count properties in this location
                location_properties = get_properties_by_location(location)
                count = len(location_properties) if location_properties else 0
                
                # Ensure button text is a string
                button_text = f"{location} ({count} properties)"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"location:{location}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Show location options
            await loading_message.edit_text(
                f"{property_count_text}\n\nPlease select a location to view properties:",
                reply_markup=reply_markup
            )
            return SELECTING_LOCATION
        else:
            await loading_message.edit_text("Sorry, I couldn't find any locations. Please try again later.")
            return CHATTING
    
    # Check for thank you messages
    if any(word in message_text for word in ["thank", "thanks", "appreciate", "helpful"]):
        await update.message.reply_text(
            f"You're welcome, {user_first_name}! I'm here to help with your property search. Is there anything else you'd like to know?"
        )
        return CHATTING
    
    # Check for questions about bot capabilities
    if any(phrase in message_text for phrase in ["what can you do", "how do you work", "what do you do", "help me"]):
        await update.message.reply_text(BOT_MESSAGES["help"], parse_mode="Markdown")
        return CHATTING
    
    # Check for location queries
    locations = get_locations()
    
    # Check if the message is asking about properties or mentioning a location
    property_keywords = ["property", "properties", "home", "house", "apartment", "real estate", "find", "search", "looking for", "want to buy", "show me", "interested in"]
    if any(keyword in message_text for keyword in property_keywords):
        # If also mentioning a location, go directly to that location
        if locations:
            for location in locations:
                if location.lower() in message_text:
                    # Set the location in context
                    context.user_data["location"] = location
                    # Show loading message
                    message = await update.message.reply_text(BOT_MESSAGES["loading"])
                    
                    # Check cache first for this location
                    current_time = time.time()
                    if (location in property_display_cache and 
                        current_time - property_display_cache[location]["last_updated"] < CACHE_TTL):
                        logger.info(f"Using cached properties for {location} (natural language query)")
                        properties = property_display_cache[location]["properties"]
                    else:
                        # Get properties for selected location
                        logger.info(f"Fetching fresh properties for {location} (natural language query)")
                        properties = get_properties_by_location(location)
                        
                        # Cache the results
                        if properties:
                            property_display_cache[location] = {
                                "last_updated": current_time,
                                "properties": properties
                            }
                    
                    # If no properties found, show error message
                    if not properties:
                        await message.edit_text(f"I couldn't find any properties in {location} at the moment. Let me show you other available locations.")
                        # Show location options by calling search
                        return await search(update, context)
                    
                    # Store properties in context
                    context.user_data["properties"] = properties
                    context.user_data["current_index"] = 0
                    
                    # Display property count
                    await message.edit_text(
                        BOT_MESSAGES["property_count"].format(len(properties), location)
                    )
                    
                    # Prepare to show the first property
                    property_data = properties[0]
                    
                    # Format property message
                    message_text = format_property_message(property_data)
                    
                    # Get property image URL
                    image_url = get_property_image_url(property_data)
                    
                    # Create navigation buttons
                    keyboard = []
                    if len(properties) > 1:
                        keyboard.append([InlineKeyboardButton("Next Property ➡️", callback_data="property:next")])
                    keyboard.append([InlineKeyboardButton("Back to Search 🔙", callback_data="property:back")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Send property with image
                    if image_url:
                        await update.message.reply_photo(
                            photo=image_url,
                            caption=message_text,
                            reply_markup=reply_markup,
                            parse_mode="Markdown"
                        )
                    else:
                        await update.message.reply_text(
                            text=message_text,
                            reply_markup=reply_markup,
                            parse_mode="Markdown"
                        )
                    
                    return VIEWING_PROPERTIES
        
        # If no specific location mentioned, show all locations
        return await search(update, context)
    
    # Check if message directly mentions a location
    if locations:
        for location in locations:
            # Skip if location is not a string
            if not isinstance(location, str):
                logger.warning(f"Skipping non-string location in message handler: {location}")
                continue
                
            if location.lower() in message_text:
                await update.message.reply_text(f"Let me find properties in {location} for you...")
                context.user_data["location"] = location
                
                # Check cache first for this location
                current_time = time.time()
                if (location in property_display_cache and 
                    current_time - property_display_cache[location]["last_updated"] < CACHE_TTL):
                    logger.info(f"Using cached properties for {location} (direct mention)")
                    properties = property_display_cache[location]["properties"]
                else:
                    # Get properties for selected location
                    logger.info(f"Fetching fresh properties for {location} (direct mention)")
                    properties = get_properties_by_location(location)
                    
                    # Cache the results
                    if properties:
                        property_display_cache[location] = {
                            "last_updated": current_time,
                            "properties": properties
                        }
                
                # If no properties found, show error message and search options
                if not properties:
                    await update.message.reply_text(BOT_MESSAGES["no_results_suggestion"])
                    return await search(update, context)
                
                # Store properties in context
                context.user_data["properties"] = properties
                context.user_data["current_index"] = 0
                
                # Display property count
                await update.message.reply_text(
                    BOT_MESSAGES["property_count"].format(len(properties), location)
                )
                
                # Prepare to show the first property
                property_data = properties[0]
                
                # Format property message
                message_text = format_property_message(property_data)
                
                # Get property image URL
                image_url = get_property_image_url(property_data)
                
                # Create navigation buttons
                keyboard = []
                if len(properties) > 1:
                    keyboard.append([InlineKeyboardButton("Next Property ➡️", callback_data="property:next")])
                keyboard.append([InlineKeyboardButton("Back to Search 🔙", callback_data="property:back")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send property with image
                if image_url:
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=message_text,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        text=message_text,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                
                return VIEWING_PROPERTIES
    
    # Handle queries about specific property features
    if any(word in message_text for word in ["bedroom", "bathroom", "price", "cost", "how much"]):
        await update.message.reply_text(
            f"I can help you find properties with specific features. Let's start by selecting a location, then I can show you properties with details about bedrooms, bathrooms, and prices."
        )
        return await search(update, context)
    
    # If no specific query recognized, provide helpful suggestions
    await update.message.reply_text(BOT_MESSAGES["not_understood"])
    return CHATTING

async def preload_popular_locations(application):
    """Preload properties for popular locations to improve initial response time."""
    logger.info("Preloading property data for popular locations...")
    
    # Get all locations
    locations = get_locations()
    if not locations:
        logger.warning("No locations found to preload")
        return
    
    # Filter out non-string locations
    valid_locations = []
    for loc in locations:
        if isinstance(loc, str):
            valid_locations.append(loc)
        else:
            logger.warning(f"Skipping non-string location in preloading: {loc}")
    
    # If we have more than 3 locations, preload the first 3 (assuming they're more popular)
    # This is a simple heuristic - you could adjust based on actual user data
    preload_locations = valid_locations[:min(3, len(valid_locations))]
    
    for location in preload_locations:
        logger.info(f"Preloading properties for {location}")
        properties = get_properties_by_location(location)
        
        if properties:
            # Cache the results
            property_display_cache[location] = {
                "last_updated": time.time(),
                "properties": properties
            }
            logger.info(f"Successfully preloaded {len(properties)} properties for {location}")
        else:
            logger.warning(f"No properties found for {location}")
    
    logger.info("Preloading complete")

# Alert-related commands and handlers
async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the alerts management process"""
    # Get or create the user in our database
    with app.app_context():
        user = get_or_create_user(
            telegram_id=update.effective_user.id,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name,
            username=update.effective_user.username
        )
        
        if not user:
            await update.message.reply_text("There was an error accessing the database. Please try again later.")
            return ConversationHandler.END
        
        # Store user id in context
        context.user_data["db_user_id"] = user.id
    
    # Show alert options
    keyboard = [
        [InlineKeyboardButton("Create Alert", callback_data="alert:create")],
        [InlineKeyboardButton("My Alerts", callback_data="alert:list")],
        [InlineKeyboardButton("Cancel", callback_data="alert:cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        BOT_MESSAGES["alerts_welcome"],
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return ALERT_MAIN

async def alert_option_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle alert option selection"""
    query = update.callback_query
    await query.answer()
    
    # Extract action from callback data
    action = query.data.split(":")[1]
    
    if action == "create":
        # Start the alert creation process
        await query.edit_message_text(
            BOT_MESSAGES["alert_create_intro"],
            parse_mode="Markdown"
        )
        
        # Show location options
        locations = get_locations()
        
        # If no locations found, show error message
        if not locations:
            await query.edit_message_text(ERROR_MESSAGES["no_locations"])
            return ConversationHandler.END
        
        # Create keyboard with locations
        keyboard = []
        for location in locations:
            if not isinstance(location, str):
                logger.warning(f"Skipping non-string location in alert creation: {location}")
                continue
                
            # Ensure button text is a string
            keyboard.append([InlineKeyboardButton(str(location), callback_data=f"alert_location:{location}")])
        
        # Add option for no location filter (all locations)
        keyboard.append([InlineKeyboardButton("All Locations", callback_data="alert_location:all")])
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="alert:cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Show location options
        await query.edit_message_text(
            BOT_MESSAGES["alert_create_intro"],
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return ALERT_LOCATION
    
    elif action == "list":
        # Show user's existing alerts
        with app.app_context():
            user_id = context.user_data.get("db_user_id")
            if not user_id:
                await query.edit_message_text("There was an error retrieving your user information. Please try again.")
                return ConversationHandler.END
            
            alerts = get_user_alerts(user_id)
            
            if not alerts:
                keyboard = [
                    [InlineKeyboardButton("Create Alert", callback_data="alert:create")],
                    [InlineKeyboardButton("Cancel", callback_data="alert:cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    BOT_MESSAGES["alert_list_empty"],
                    reply_markup=reply_markup
                )
                return ALERT_MAIN
            
            # Create list of alerts with delete buttons
            message = BOT_MESSAGES["alert_list_intro"] + "\n\n"
            
            keyboard = []
            for i, alert in enumerate(alerts):
                alert_description = []
                if alert.location:
                    alert_description.append(f"Location: {alert.location}")
                else:
                    alert_description.append("Location: All")
                
                if alert.min_price:
                    alert_description.append(f"Min Price: {alert.min_price}")
                if alert.max_price:
                    alert_description.append(f"Max Price: {alert.max_price}")
                if alert.min_bedrooms:
                    alert_description.append(f"Min Bedrooms: {alert.min_bedrooms}")
                
                message += f"{i+1}. {' | '.join(alert_description)}\n"
                keyboard.append([InlineKeyboardButton(f"Delete Alert #{i+1}", callback_data=f"alert_delete:{alert.id}")])
            
            # Add back button
            keyboard.append([InlineKeyboardButton("Back to Alert Menu", callback_data="alert:back")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup
            )
            
            return ALERT_LIST
    
    elif action == "cancel" or action == "back":
        # Cancel alert process
        await query.edit_message_text("Alert settings closed. You can access them again with the /alerts command.")
        return ConversationHandler.END
    
    return ALERT_MAIN

async def alert_location_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location selection for alert creation"""
    query = update.callback_query
    await query.answer()
    
    # Extract location from callback data
    location = query.data.split(":")[1]
    
    # Store in context
    if location.lower() == "all":
        context.user_data["alert_location"] = None
    else:
        context.user_data["alert_location"] = location
    
    # Ask for minimum price
    await query.edit_message_text(BOT_MESSAGES["alert_create_min_price"])
    
    return ALERT_MIN_PRICE

async def alert_min_price_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle minimum price entry for alert creation"""
    message_text = update.message.text.strip().lower()
    
    if message_text == "skip":
        context.user_data["alert_min_price"] = None
    else:
        try:
            # Convert to integer, remove commas if present
            price = int(message_text.replace(",", ""))
            context.user_data["alert_min_price"] = price
        except ValueError:
            await update.message.reply_text(BOT_MESSAGES["invalid_input"])
            return ALERT_MIN_PRICE
    
    # Ask for maximum price
    await update.message.reply_text(BOT_MESSAGES["alert_create_max_price"])
    
    return ALERT_MAX_PRICE

async def alert_max_price_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle maximum price entry for alert creation"""
    message_text = update.message.text.strip().lower()
    
    if message_text == "skip":
        context.user_data["alert_max_price"] = None
    else:
        try:
            # Convert to integer, remove commas if present
            price = int(message_text.replace(",", ""))
            context.user_data["alert_max_price"] = price
        except ValueError:
            await update.message.reply_text(BOT_MESSAGES["invalid_input"])
            return ALERT_MAX_PRICE
    
    # Ask for minimum bedrooms
    await update.message.reply_text(BOT_MESSAGES["alert_create_min_bedrooms"])
    
    return ALERT_MIN_BEDROOMS

async def alert_min_bedrooms_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle minimum bedrooms entry for alert creation"""
    message_text = update.message.text.strip().lower()
    
    if message_text == "skip":
        context.user_data["alert_min_bedrooms"] = None
    else:
        try:
            bedrooms = int(message_text)
            context.user_data["alert_min_bedrooms"] = bedrooms
        except ValueError:
            await update.message.reply_text(BOT_MESSAGES["invalid_input"])
            return ALERT_MIN_BEDROOMS
    
    # Create the alert in the database
    with app.app_context():
        user_id = context.user_data.get("db_user_id")
        if not user_id:
            await update.message.reply_text("There was an error retrieving your user information. Please try again.")
            return ConversationHandler.END
        
        alert = create_property_alert(
            user_id=user_id,
            location=context.user_data.get("alert_location"),
            min_price=context.user_data.get("alert_min_price"),
            max_price=context.user_data.get("alert_max_price"),
            min_bedrooms=context.user_data.get("alert_min_bedrooms")
        )
        
        if not alert:
            await update.message.reply_text("There was an error creating your alert. Please try again.")
            return ConversationHandler.END
        
        # Determine location description for message
        location_desc = context.user_data.get("alert_location", "All Locations")
        
        # Confirm alert creation
        await update.message.reply_text(
            BOT_MESSAGES["alert_created"].format(location_desc),
            parse_mode="Markdown"
        )
    
    return ConversationHandler.END

async def alert_delete_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle alert deletion selection"""
    query = update.callback_query
    await query.answer()
    
    # Extract alert ID from callback data
    alert_id = int(query.data.split(":")[1])
    context.user_data["alert_delete_id"] = alert_id
    
    # Confirm deletion
    with app.app_context():
        user_id = context.user_data.get("db_user_id")
        if not user_id:
            await query.edit_message_text("There was an error retrieving your user information. Please try again.")
            return ConversationHandler.END
    
    # Create confirmation buttons
    keyboard = [
        [InlineKeyboardButton("Yes, Delete", callback_data="alert_delete_confirm:yes")],
        [InlineKeyboardButton("No, Keep", callback_data="alert_delete_confirm:no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Location is not available in the callback data, so we just use a generic message
    await query.edit_message_text(
        "Are you sure you want to delete this alert?",
        reply_markup=reply_markup
    )
    
    return ALERT_DELETE_CONFIRM

async def alert_delete_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle alert deletion confirmation"""
    query = update.callback_query
    await query.answer()
    
    # Extract confirmation from callback data
    confirm = query.data.split(":")[1]
    
    if confirm == "yes":
        # Delete the alert
        with app.app_context():
            user_id = context.user_data.get("db_user_id")
            alert_id = context.user_data.get("alert_delete_id")
            
            if not user_id or not alert_id:
                await query.edit_message_text("There was an error retrieving your alert information. Please try again.")
                return ConversationHandler.END
            
            success = delete_property_alert(alert_id, user_id)
            
            if success:
                await query.edit_message_text(BOT_MESSAGES["alert_deleted"])
            else:
                await query.edit_message_text("There was an error deleting the alert. Please try again.")
    else:
        # Cancelled
        await query.edit_message_text(BOT_MESSAGES["alert_delete_cancelled"])
    
    return ConversationHandler.END

def create_bot():
    """Create and configure the bot with all handlers."""
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Schedule the preloading to happen after the bot starts
    application.post_init = preload_popular_locations
    
    # Add conversation handler for property search with specific patterns
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("search", search),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        ],
        states={
            SELECTING_LOCATION: [
                # Handle button clicks for location selection
                CallbackQueryHandler(location_selected, pattern=r"^location:[A-Za-z ]+$"),
                # Handle text input for locations
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_location)
            ],
            SELECTING_BUDGET: [
                # For future implementation
            ],
            SELECTING_BEDROOMS: [
                # For future implementation
            ],
            VIEWING_PROPERTIES: [
                # Handle property navigation buttons
                CallbackQueryHandler(property_navigation, pattern=r"^property:(next|back|new_search)$")
            ],
            CHATTING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="property_conversation",  # Add name for better logging
        allow_reentry=True  # Allow the conversation to be reentered if the handlers don't match
    )
    
    # Add conversation handler for property alerts
    alerts_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("alerts", alerts_command)
        ],
        states={
            ALERT_MAIN: [
                CallbackQueryHandler(alert_option_selected, pattern=r"^alert:(create|list|cancel|back)$")
            ],
            ALERT_LOCATION: [
                CallbackQueryHandler(alert_location_selected, pattern=r"^alert_location:[A-Za-z ]+$"),
                CallbackQueryHandler(alert_option_selected, pattern=r"^alert:cancel$")
            ],
            ALERT_MIN_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, alert_min_price_entered)
            ],
            ALERT_MAX_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, alert_max_price_entered)
            ],
            ALERT_MIN_BEDROOMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, alert_min_bedrooms_entered)
            ],
            ALERT_LIST: [
                CallbackQueryHandler(alert_delete_selected, pattern=r"^alert_delete:\d+$"),
                CallbackQueryHandler(alert_option_selected, pattern=r"^alert:back$")
            ],
            ALERT_DELETE_CONFIRM: [
                CallbackQueryHandler(alert_delete_confirmed, pattern=r"^alert_delete_confirm:(yes|no)$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="alert_conversation",
        allow_reentry=True
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(alerts_conv_handler)  # Add the alerts handler
    application.add_handler(conv_handler)
    
    return application
