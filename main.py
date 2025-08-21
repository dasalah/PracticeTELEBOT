from telethon import TelegramClient, events, Button
from telethon.tl.types import DocumentAttributeFilename
import logging
import asyncio

# Import configuration
import config

# Import database
from models.database import db_manager, Admin

# Import handlers
from handlers.registration import (
    handle_start_with_event,
    handle_text_message,
    handle_photo_message
)
from handlers.admin import handle_admin_start, is_admin
from handlers.callbacks import handle_callback_query

# Import utilities
from utils.helpers import (
    ensure_directories,
    log_activity,
    log_message,
    MessageTemplates
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize bot client
client = TelegramClient(
    config.SESSION_NAME,
    config.API_ID,
    config.API_HASH
)

@client.on(events.NewMessage(pattern=r'^/start', func=lambda e: e.is_private))
async def handle_start(event):
    """Handle /start command"""
    telegram_id = event.chat_id
    
    try:
        # Log the message
        await log_message(telegram_id, event.text)
        
        # Check if it's an admin
        if await is_admin(telegram_id):
            parts = event.text.split(' ')
            if len(parts) == 1:
                # Admin start without parameters
                await handle_admin_start(event, client)
                return
        
        # Check if start has event code parameter
        parts = event.text.split(' ')
        if len(parts) == 2:
            event_code = parts[1]
            await handle_start_with_event(event, client, event_code)
        else:
            # Regular start - show welcome message
            await log_activity(telegram_id, "accessed_start")
            await event.respond(MessageTemplates.WELCOME)
        
    except Exception as e:
        logger.error(f"Error in handle_start: {e}")
        await event.respond(config.MESSAGES['error_occurred'])

@client.on(events.NewMessage(pattern=r'^/admin', func=lambda e: e.is_private))
async def handle_admin_command(event):
    """Handle /admin command"""
    await handle_admin_start(event, client)

@client.on(events.NewMessage(pattern=r'^/status', func=lambda e: e.is_private))
async def handle_status(event):
    """Handle /status command"""
    telegram_id = event.chat_id
    
    await log_activity(telegram_id, "checked_status")
    await event.respond("🔍 بررسی وضعیت در حال توسعه است.")

@client.on(events.NewMessage(func=lambda e: e.is_private and e.photo))
async def handle_photo(event):
    """Handle photo messages"""
    await handle_photo_message(event, client)

@client.on(events.NewMessage(func=lambda e: e.is_private and not e.text.startswith('/')))
async def handle_text(event):
    """Handle text messages"""
    await handle_text_message(event, client)

@client.on(events.CallbackQuery)
async def handle_callback(event):
    """Handle callback queries"""
    await handle_callback_query(event, client)

async def initialize_bot():
    """Initialize bot and database"""
    try:
        # Validate configuration
        config.validate_config()
        
        # Ensure directories exist
        ensure_directories()
        
        # Create database tables
        db_manager.create_tables()
        
        # Create super admin if not exists
        await create_super_admin()
        
        logger.info("Bot initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        raise

async def create_super_admin():
    """Create super admin if not exists"""
    session = db_manager.get_session()
    try:
        existing_admin = session.query(Admin).filter(
            Admin.telegram_id == config.SUPER_ADMIN_ID
        ).first()
        
        if not existing_admin:
            super_admin = Admin(
                telegram_id=config.SUPER_ADMIN_ID,
                is_super_admin=True
            )
            session.add(super_admin)
            session.commit()
            logger.info(f"Created super admin: {config.SUPER_ADMIN_ID}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating super admin: {e}")
    finally:
        db_manager.close_session(session)

async def main():
    """Main function"""
    try:
        # Initialize bot
        await initialize_bot()
        
        # Start the bot
        await client.start(bot_token=config.BOT_TOKEN)
        
        if client.is_connected():
            logger.info("Bot connected and running!")
            print("🤖 ربات با موفقیت راه‌اندازی شد!")
        
        # Keep the bot running
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"❌ خطا در راه‌اندازی ربات: {e}")

if __name__ == '__main__':
    asyncio.run(main())
