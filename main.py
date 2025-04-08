import logging
import asyncio
from bot import create_bot
from config import TELEGRAM_TOKEN
from alert_service import start_property_alert_service

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Start the bot."""
    # Validate token
    if not TELEGRAM_TOKEN:
        logger.error("No Telegram token provided. Set the TELEGRAM_TOKEN environment variable.")
        return
    
    # Create and start the bot
    application = create_bot()
    
    # Create a bot instance for the alert service to use for sending notifications
    bot = application.bot
    
    # Schedule the alert service as a background task
    asyncio.create_task(start_property_alert_service(bot))
    
    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot with alert service...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    try:
        # Keep the application running until terminated
        await application.updater.stop.wait()
    finally:
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
