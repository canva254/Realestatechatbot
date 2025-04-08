import os

# Telegram Bot Token - get from environment variable
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# WordPress API URL
WP_API_URL = "https://avierhomes.co.ke/wp-json/wp/v2/property"

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
        "I can help you find your dream home in Kenya.\n\n"
        "Use the /search command to browse properties by location."
    ),
    "search_prompt": "Please select a location to view available properties:",
    "loading": "🔍 Searching for properties...",
    "property_not_found": "No properties found in this location. Try another location.",
    "property_count": "Found {} properties in {}. I'll show them to you one by one.",
    "more_properties": "Would you like to see more properties in this location?",
    "end_of_properties": "That's all the properties I have for {}. Would you like to search in another location?",
    "help": (
        "*Avier Homes Property Bot Help*\n\n"
        "Available commands:\n"
        "/start - Start the bot and get a welcome message\n"
        "/search - Search for properties by location\n"
        "/help - Show this help message\n\n"
        "To search for properties, just use the /search command and choose a location."
    )
}
