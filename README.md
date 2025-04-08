# Avier Homes Telegram Bot

A Python-based Telegram bot that fetches and displays real estate properties from Avier Homes WordPress site via REST API. The bot offers a natural conversational experience for users searching for real estate properties in Kenya.

## Features

- Search properties by location with text commands or menu options
- Automatic display of available properties upon initial interaction
- Personalized greetings with user's name for a more engaging experience
- Display property details including price, bedrooms, bathrooms, location, and featured image
- Natural language understanding for conversational queries like "Show me houses in Lavington"
- Smart responses to greetings, thank you messages, and questions about capabilities
- Context-aware conversations that remember your search context
- Direct property lookup when mentioning locations in conversation
- Intuitive navigation with inline buttons
- Property Alerts: Subscribe to notifications for new properties matching your criteria
- Alert Management: Create, view, and delete personalized property alerts
- Filtered Notifications: Set up alerts based on location, price range, and number of bedrooms
- Dynamically fetches locations and property data from the WordPress API
- Stable conversation flow with improved callback handling
- Efficient caching system for faster property loading
- Optimized API requests with time-based cache expiration
- Preloading of popular locations for improved initial response time
- Property Alerts: Subscribe to notifications for new properties matching your criteria
- Alert Management: Create, view, and delete personalized property alerts
- Filtered Notifications: Set up alerts based on location, price range, and number of bedrooms
- **Property Alerts:** Subscribe to notifications for new properties matching your criteria
- PostgreSQL database for property alerts feature
- Flask and SQLAlchemy for database operations
- **Alert Management:** Create, view, and delete personalized property alerts
- **Filtered Notifications:** Set up alerts based on location, price range, and number of bedrooms

## Prerequisites

- Python 3.9+
- python-telegram-bot (v20.7+)
- requests

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/avier-homes-bot.git
   cd avier-homes-bot
   ```

2. Install the required packages:
   ```
   pip install python-telegram-bot requests
   ```

3. Set up your Telegram Bot:
   - Talk to [BotFather](https://t.me/botfather) on Telegram to create a new bot
   - Get your bot token

4. Set the environment variable for your bot token:
   ```
   export TELEGRAM_TOKEN="your_telegram_bot_token"
   ```

## Running the Bot

- `/alerts` - Manage property alerts and notifications
Run the bot locally:
```python
python main.py
```

## Using the Bot

### Commands
- `/start` - Start the bot, get a welcome message, and immediately see available properties
- `/search` - Browse properties by location
- `/help` - Show the help message with available commands

### Conversational Features
Users can interact with the bot in a natural way:

1. **Location-Based Queries**:
   - "Show me properties in Lavington"
   - "I'm looking for a house in Kilimani"
   - "Find apartments in Karen"

2. **General Property Searches**:
   - "I want to buy a house"
   - "Show me available properties"
   - "Looking for real estate"

3. **Specific Feature Inquiries**:
   - "How many bedrooms do the properties have?"
   - "What's the price range for homes in Westlands?"
   - "Tell me about bathrooms in these properties"

4. **Natural Conversation**:
   - The bot responds to greetings ("Hi", "Hello")
   - Saying "Hello" will trigger the bot to show available properties
   - Acknowledges appreciation ("Thanks", "Thank you")
   - Answers questions about its capabilities ("What can you do?")

## Project Structure

- `main.py` - Entry point that starts the bot
- `bot.py` - Contains the bot's handlers and conversation logic
- `api.py` - Handles API requests to the WordPress site
- `utils.py` - Helper functions for formatting messages and processing data
- `config.py` - Configuration variables and message templates

## API Endpoints

The bot connects to the following WordPress API endpoints:

- **All Properties**: `https://avierhomes.co.ke/wp-json/wp/v2/property?_embed`
- **Filter by Location**: `https://avierhomes.co.ke/wp-json/wp/v2/property?acf[location]=Lavington&_embed`

The `_embed` parameter ensures media and other embedded resources are included in the API response.

## Future Enhancements

- Price range filtering
- Bedroom and bathroom filters
- Property favoriting and saved searches
- Notifications for new properties
- Advanced search with multiple criteria
### Property Alerts
Users can set up custom property alerts to receive notifications when new properties matching their criteria are added:

1. **Creating Alerts**:
   - Use the `/alerts` command to access alert management
   - Select "Create Alert" to set up a new alert
   - Choose location preferences or select "All Locations"
   - Optionally specify price range and minimum bedroom requirements

2. **Managing Alerts**:
   - View all active alerts through the "My Alerts" option
   - Delete alerts that are no longer needed
   - Receive notifications automatically when matching properties are added
