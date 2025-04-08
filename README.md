# Avier Homes Telegram Bot

A Python-based Telegram bot that fetches and displays real estate properties from Avier Homes WordPress site via REST API.

## Features

- Search properties by location
- Display property details including price, bedrooms, bathrooms, location, and featured image
- Conversational interface with intuitive navigation
- Dynamically fetches locations from the WordPress API

## Prerequisites

- Python 3.9+
- python-telegram-bot (v13+)
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

Run the bot locally:
