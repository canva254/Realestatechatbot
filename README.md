# Avier Homes Real Estate Telegram Bot

A sophisticated Telegram bot for real estate property searches in Kenya, providing an intelligent and interactive property discovery platform that connects users with their ideal properties through advanced conversational AI and seamless WordPress REST API integration.

## Features

- **Conversational Property Search**: Natural language understanding for property queries
- **Location-Based Search**: Find properties by specifying locations (e.g., "Lavington")
- **Property Details**: View comprehensive property information including price, bedrooms, bathrooms, location and images
- **Property Alerts**: Subscribe to receive notifications about new property listings
- **Interactive Navigation**: Easily browse through multiple property listings with intuitive buttons
- **Web Dashboard**: View bot statistics and usage information

## Technology Stack

- Python 3.9+
- python-telegram-bot library
- Flask web framework
- SQLAlchemy ORM
- PostgreSQL database
- WordPress REST API integration

## Commands

- `/start` - Begin interaction with the bot and view available properties
- `/search` - Start a property search by location
- `/alerts` - Set up and manage property alerts
- `/help` - View available commands and usage information

## Natural Language Queries

The bot understands various ways to ask for properties:
- "Show me properties in Lavington"
- "I'm looking for a house in Kilimani"
- "Find properties"

## Getting Started

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   - `TELEGRAM_TOKEN`: Your Telegram bot token
   - `DATABASE_URL`: PostgreSQL database URL
4. Run the bot: `python main.py`
5. Access the web dashboard: `python web.py`

## Project Structure

- `main.py`: Entry point for the Telegram bot
- `bot.py`: Core bot functionality and conversation handlers
- `api.py`: WordPress API integration and data fetching
- `models.py`: Database models for users, alerts, and properties
- `utils.py`: Utility functions for formatting messages
- `alert_service.py`: Background service for property alerts
- `web.py`: Web dashboard interface
- `app.py`: Flask application setup
- `db_helpers.py`: Database helper functions

## License

MIT License

## Author

Avier Homes Team