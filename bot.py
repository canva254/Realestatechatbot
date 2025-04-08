import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton

from config import TELEGRAM_TOKEN, BOT_MESSAGES, ERROR_MESSAGES
from api import get_locations, get_properties_by_location
from utils import format_property_message, get_property_image_url

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
SELECTING_LOCATION, VIEWING_PROPERTIES = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text(
        BOT_MESSAGES["welcome"],
        parse_mode="Markdown"
    )

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
        keyboard.append([InlineKeyboardButton(location, callback_data=f"location:{location}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Show location options
    await message.edit_text(
        BOT_MESSAGES["search_prompt"],
        reply_markup=reply_markup
    )
    
    return SELECTING_LOCATION

async def location_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle location selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract location from callback data
    location = query.data.split(":")[1]
    context.user_data["location"] = location
    
    # Show loading message
    await query.edit_message_text(BOT_MESSAGES["loading"])
    
    # Get properties for selected location
    properties = get_properties_by_location(location)
    
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
        await update.message.reply_text("Search cancelled. Use /search to start again.")
    return ConversationHandler.END

def create_bot():
    """Create and configure the bot with all handlers."""
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add conversation handler for property search
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search)],
        states={
            SELECTING_LOCATION: [
                CallbackQueryHandler(location_selected, pattern=r"^location:")
            ],
            VIEWING_PROPERTIES: [
                CallbackQueryHandler(property_navigation, pattern=r"^property:")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    
    return application
