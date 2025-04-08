# Avier Homes Real Estate Telegram Bot

A sophisticated Telegram bot for real estate property searches in Kenya, providing an intelligent and interactive property discovery platform that connects users with their ideal properties through advanced conversational AI and seamless WordPress REST API integration.

## Features

- **Conversational Property Search**: Natural language understanding for property queries
- **Location-Based Search**: Find properties by specifying locations (e.g., "Lavington")
- **Property Details**: View comprehensive property information including price, bedrooms, bathrooms, location and images
- **Property Alerts**: Subscribe to receive notifications about new property listings
- **Interactive Navigation**: Easily browse through multiple property listings with intuitive buttons
- **Web Dashboard**: View bot statistics and usage information

## Demo

Try the bot on Telegram: [@AvierhomesBot](https://t.me/AvierhomesBot)

## Technology Stack

- Python 3.9+
- python-telegram-bot library (v20+)
- Flask web framework
- SQLAlchemy ORM
- PostgreSQL database
- WordPress REST API integration
- Gunicorn WSGI server

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

## WordPress API Integration

The bot integrates with the WordPress REST API to fetch real-time property data:
- All Properties: `https://avierhomes.co.ke/wp-json/wp/v2/property?_embed`
- Location Filtering: `https://avierhomes.co.ke/wp-json/wp/v2/property?acf[location]=Lavington&_embed`

## Installation and Setup

### Prerequisites
- Python 3.9 or higher
- PostgreSQL database
- Telegram Bot token (obtained from [BotFather](https://t.me/botfather))

### Installation

1. Clone this repository
   ```bash
   git clone https://github.com/canva254/Realestatechatbot.git
   cd Realestatechatbot
   ```

2. Install dependencies
   ```bash
   pip install -r dependencies.txt
   ```

3. Set up environment variables
   ```bash
   # Required environment variables
   export TELEGRAM_TOKEN="your_telegram_bot_token"
   export DATABASE_URL="postgresql://username:password@localhost:5432/avierhomes"
   
   # Optional environment variables
   export CACHE_TTL="1800"  # Cache time to live in seconds
   ```

4. Initialize the database
   ```bash
   # The database tables will be created automatically when you run the application
   ```

5. Run the bot
   ```bash
   python main.py
   ```

6. Access the web dashboard
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

## Property Alerts Feature

Users can set up alerts to be notified when new properties matching their criteria become available:

1. Start alert setup with `/alerts` command
2. Choose a location of interest
3. Set optional filters like price range and minimum bedrooms
4. Receive instant notifications when matching properties are listed

## Project Structure

- `main.py`: Entry point for the Telegram bot
- `bot.py`: Core bot functionality and conversation handlers
- `api.py`: WordPress API integration and data fetching with caching
- `models.py`: Database models for users, alerts, and properties
- `utils.py`: Utility functions for formatting property messages
- `alert_service.py`: Background service for property alerts
- `web.py`: Web dashboard interface
- `app.py`: Flask application setup
- `db_helpers.py`: Database helper functions for user and alert management
- `config.py`: Configuration settings

## Error Handling

The bot includes comprehensive error handling:
- API connection issues
- No properties available in a location
- Invalid user inputs
- Database connection problems

## Continuous Integration/Deployment

This project features automatic GitHub synchronization:
- Every commit is automatically pushed to GitHub via Git hooks
- Development changes are instantly reflected in the repository
- Ensures the GitHub repository is always up-to-date with the latest changes

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License

## Author

Avier Homes Team