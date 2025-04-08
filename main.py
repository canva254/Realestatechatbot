import logging
from bot import create_bot
from config import TELEGRAM_TOKEN

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Validate token
    if not TELEGRAM_TOKEN:
        logger.error("No Telegram token provided. Set the TELEGRAM_TOKEN environment variable.")
        return
    
    # Create and start the bot
    application = create_bot()
    
    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
