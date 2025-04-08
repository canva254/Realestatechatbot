import os

# Telegram Bot Token - get from environment variable
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Performance optimization settings
CACHE_TTL = 300  # Cache time-to-live in seconds (5 minutes)

# WordPress API URLs
WP_API_URL = "https://avierhomes.co.ke/wp-json/wp/v2/property"

# URL format for filtered properties by location: 
# https://avierhomes.co.ke/wp-json/wp/v2/property?acf[location]=Lavington&_embed

# Request parameters
PARAMS = {
    "_embed": True,  # Include embedded resources like featured media
    "per_page": 100  # Maximum number of properties to fetch per request
}

# Error messages
ERROR_MESSAGES = {
    "api_error": "Sorry, I couldn't connect to the property database. Please try again later.",
    "no_properties": "Sorry, I couldn't find any properties matching your criteria.",
    "no_locations": "Sorry, I couldn't find any locations in our database.",
    "generic_error": "Something went wrong. Please try again later."
}

# Bot messages
BOT_MESSAGES = {
    "welcome": (
        "👋 *Welcome to Avier Homes Property Bot!*\n\n"
        "I can help you find your dream home in Kenya. Let me show you our available properties right away!\n\n"
        "You can also ask me things like:\n"
        "- \"Show me properties in Lavington\"\n"
        "- \"I'm looking for a house in Kilimani\"\n"
        "- \"Find properties\"\n\n"
        "Or just say hello to start exploring!"
    ),
    "search_prompt": "Which area are you interested in? Please select a location to view available properties:",
    "loading": "🔍 Looking for perfect homes for you...",
    "property_not_found": "I couldn't find any properties in this location right now. Would you like to try another area?",
    "property_count": "Great news! I found {} properties in {}. Let me show them to you.",
    "more_properties": "Would you like to see more properties in this location?",
    "end_of_properties": "That's all the properties I have for {}. Would you like to search in another location?",
    "help": (
        "*Avier Homes Property Bot Help*\n\n"
        "I'm your personal real estate assistant. Here's how I can help:\n\n"
        "• *Find Properties* - Simply type what you're looking for, like \"Show me houses in Lavington\"\n"
        "• *Browse Locations* - Use /search to see all available areas\n"
        "• *Set Alerts* - Use /alerts to get notified about new properties\n"
        "• *Get Help* - Type /help to see these instructions again\n\n"
        "I understand natural language, so you can chat with me just like you would with a real estate agent!"
    ),
    "not_understood": "I'm not sure I understood that. Would you like to search for properties? Just tell me what area you're interested in or use the /search command.",
    "greeting": "Hello there! How can I help with your property search today?",
    "no_results_suggestion": "I couldn't find any properties matching your criteria. Would you like to try a different location?",

    # New alert-related messages
    "alerts_welcome": (
        "🔔 *Property Alert Settings*\n\n"
        "I can notify you when new properties that match your criteria become available.\n\n"
        "What would you like to do?"
    ),
    "alert_create_intro": (
        "Let's set up a new property alert. I'll notify you when new properties matching your criteria are listed.\n\n"
        "Please select the location you're interested in:"
    ),
    "alert_created": "✅ Your alert has been created! I'll notify you about new properties in {}.",
    "alert_create_min_price": "What's the minimum price you're looking for? (Type 'skip' if you don't want to set this filter)",
    "alert_create_max_price": "What's the maximum price you're looking for? (Type 'skip' if you don't want to set this filter)",
    "alert_create_min_bedrooms": "How many bedrooms do you need at minimum? (Type 'skip' if you don't want to set this filter)",
    "alert_list_empty": "You don't have any active property alerts. Use the 'Create Alert' button to set one up.",
    "alert_list_intro": "Here are your active property alerts:",
    "alert_deleted": "✅ Alert deleted successfully!",
    "alert_delete_confirm": "Are you sure you want to delete this alert for {}?",
    "alert_delete_cancelled": "Alert deletion cancelled.",
    "invalid_input": "Sorry, I couldn't understand that input. Please try again."
}
