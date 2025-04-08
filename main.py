import logging
import asyncio
import signal
from bot import create_bot
from config import TELEGRAM_TOKEN
from alert_service import start_property_alert_service
from app import app

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
        # Use a signal-based approach to keep the application running
        stop_signal = asyncio.Event()
        
        # Handle shutdown gracefully when SIGINT or SIGTERM is received
        async def stop_bot():
            # Stop the polling and shutdown the bot
            await application.updater.stop_polling()
            await application.stop()
            await application.shutdown()
            # Set the signal to indicate we're done
            stop_signal.set()
        
        # Register the signal handlers
        for signal_name in ('SIGINT', 'SIGTERM'):
            try:
                loop = asyncio.get_running_loop()
                loop.add_signal_handler(
                    getattr(signal, signal_name),
                    lambda: asyncio.create_task(stop_bot())
                )
            except (NotImplementedError, RuntimeError):
                # Some systems don't support add_signal_handler
                pass
        
        # Wait until a stop signal is received
        await stop_signal.wait()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        # Make sure to stop the application properly
        await application.updater.stop_polling()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())