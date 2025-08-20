from telethon import TelegramClient, events, Button
from telethon.tl.custom.message import Message
from config import api_id, api_hash, token
from userDB import db_init, create_db_session, RegistrationStatus
from utils import is_admin, is_super_admin, log_message
from event_manager import EventManager
from registration_manager import RegistrationManager
from admin_approval import AdminApprovalManager, ExcelExporter
import os

# Initialize database
db_init()

# Bot client
client = TelegramClient(session="event_registration_bot",
                        api_id=api_id,
                        api_hash=api_hash,
                        )

# Initialize managers
event_manager = EventManager()
registration_manager = RegistrationManager()
admin_approval = AdminApprovalManager()

# Create receipts directory
os.makedirs("receipts", exist_ok=True)

@client.on(events.NewMessage(pattern=r'^/start(?:\s+(.+))?$', func=lambda e: e.is_private))
async def handle_start(event):
    """Handle /start command"""
    try:
        # Log message
        db_session = create_db_session()
        log_message(db_session, event.sender_id, event.text)
        db_session.close()
        
        # Check for event code
        match = event.pattern_match
        if match and match.group(1):
            # User clicked on event link
            event_code = match.group(1)
            await registration_manager.handle_event_start(event, client, event_code)
        else:
            # Regular start command
            await show_main_menu(event)
            
    except Exception as e:
        await event.respond(f"خطا: {str(e)}")

async def show_main_menu(event):
    """Show main menu based on user type"""
    db_session = create_db_session()
    
    try:
        user_id = event.sender_id
        
        if is_super_admin(db_session, user_id):
            message = "🔧 پنل مدیر اصلی"
            buttons = [
                [Button.text("ایجاد رویداد", resize=True)],
                [Button.text("مدیریت رویدادها", resize=True)],
                [Button.text("مدیریت ادمین‌ها", resize=True)],
                [Button.text("آمار کلی", resize=True)]
            ]
        elif is_admin(db_session, user_id):
            message = "🔧 پنل ادمین"
            buttons = [
                [Button.text("ایجاد رویداد", resize=True)],
                [Button.text("مدیریت رویدادها", resize=True)],
                [Button.text("آمار", resize=True)]
            ]
        else:
            message = (
                "🎯 به ربات ثبت نام رویدادها خوش آمدید!\n\n"
                "برای ثبت نام در رویدادها، روی لینک اختصاری رویداد کلیک کنید.\n"
                "یا از طریق منوی زیر اقدام کنید:"
            )
            buttons = [
                [Button.text("درباره ما", resize=True)],
                [Button.text("راهنما", resize=True)]
            ]
        
        await event.respond(message, buttons=buttons)
        
    except Exception as e:
        await event.respond(f"خطا: {str(e)}")
    finally:
        db_session.close()

@client.on(events.NewMessage(pattern=r'^/(create_event|list_events|add_admin|stats)$', func=lambda e: e.is_private))
async def handle_admin_commands(event):
    """Handle admin commands"""
    db_session = create_db_session()
    
    try:
        user_id = event.sender_id
        command = event.text[1:]  # Remove /
        
        # Check admin privileges
        if not is_admin(db_session, user_id):
            await event.respond("⛔ شما دسترسی ادمین ندارید.")
            return
        
        if command == "create_event":
            await event_manager.handle_create_event_command(event, client)
        elif command == "list_events":
            await event_manager.handle_list_events(event, client)
        elif command == "add_admin":
            if is_super_admin(db_session, user_id):
                await handle_add_admin_command(event)
            else:
                await event.respond("⛔ فقط ادمین اصلی می‌تواند ادمین جدید اضافه کند.")
        elif command == "stats":
            await handle_stats_command(event)
        
    except Exception as e:
        await event.respond(f"خطا: {str(e)}")
    finally:
        db_session.close()

@client.on(events.NewMessage(func=lambda e: e.is_private))
async def handle_messages(event):
    """Handle all private messages"""
    try:
        # Log message
        db_session = create_db_session()
        log_message(db_session, event.sender_id, event.text)
        db_session.close()
        
        user_id = event.sender_id
        
        # Check if it's an admin command step
        if event.text in ["ایجاد رویداد"]:
            db_session = create_db_session()
            if is_admin(db_session, user_id):
                await event_manager.handle_create_event_command(event, client)
            else:
                await event.respond("⛔ شما دسترسی ادمین ندارید.")
            db_session.close()
            return
        
        if event.text in ["مدیریت رویدادها"]:
            db_session = create_db_session()
            if is_admin(db_session, user_id):
                await event_manager.handle_list_events(event, client)
            else:
                await event.respond("⛔ شما دسترسی ادمین ندارید.")
            db_session.close()
            return
        
        # Check for event manager steps
        if await event_manager.handle_create_event_step(event, client):
            return
        
        # Check for registration steps
        if await registration_manager.handle_registration_step(event, client):
            return
        
        # Handle other messages
        if event.text == "درباره ما":
            await event.respond(
                "🏢 این ربات برای ثبت نام در رویدادهای مختلف طراحی شده است.\n\n"
                "✨ ویژگی‌ها:\n"
                "• ثبت نام آسان و سریع\n"
                "• بارگذاری فیش واریزی\n"
                "• تایید ادمین\n"
                "• پیگیری وضعیت ثبت نام\n\n"
                "📞 پشتیبانی: @admin"
            )
        elif event.text == "راهنما":
            await event.respond(
                "📚 راهنمای استفاده:\n\n"
                "1️⃣ روی لینک رویداد کلیک کنید\n"
                "2️⃣ مبلغ را واریز کنید\n"
                "3️⃣ اطلاعات خود را وارد کنید\n"
                "4️⃣ فیش واریزی را ارسال کنید\n"
                "5️⃣ منتظر تایید ادمین باشید\n\n"
                "💡 نکته: می‌توانید از اعداد فارسی استفاده کنید."
            )
        
    except Exception as e:
        print(f"Error in handle_messages: {e}")

@client.on(events.CallbackQuery)
async def handle_callbacks(event):
    """Handle inline button callbacks"""
    try:
        data = event.data.decode('utf-8')
        
        if data.startswith('view_event_'):
            event_id = int(data.split('_')[2])
            await event_manager.handle_event_view(event, event_id)
        
        elif data.startswith('registrations_'):
            event_id = int(data.split('_')[1])
            await event_manager.handle_registrations_view(event, event_id)
        
        elif data.startswith('export_excel_'):
            event_id = int(data.split('_')[2])
            await ExcelExporter.export_event_registrations(event, client, event_id)
        
        elif data.startswith(('approve_reg_', 'reject_reg_')):
            await admin_approval.handle_approval_callback(event, client, data)
        
        elif data == 'back_to_events':
            await event_manager.handle_list_events(event, client)
    
    except Exception as e:
        await event.edit(f"خطا: {str(e)}")

async def handle_add_admin_command(event):
    """Handle add admin command"""
    await event.respond(
        "👤 برای افزودن ادمین جدید، یکی از روش‌های زیر را انتخاب کنید:\n\n"
        "1️⃣ کاربر را به ربات Forward کنید\n"
        "2️⃣ یا User ID را ارسال کنید"
    )

async def handle_stats_command(event):
    """Handle stats command"""
    db_session = create_db_session()
    
    try:
        from userDB import User, Event, Registration
        
        total_users = db_session.query(User).count()
        total_events = db_session.query(Event).count()
        total_registrations = db_session.query(Registration).count()
        approved_registrations = db_session.query(Registration).filter_by(
            status=RegistrationStatus.APPROVED
        ).count()
        
        response = (
            "📊 آمار کلی سیستم:\n\n"
            f"👥 کل کاربران: {total_users}\n"
            f"📋 کل رویدادها: {total_events}\n"
            f"📝 کل ثبت نام‌ها: {total_registrations}\n"
            f"✅ ثبت نام‌های تایید شده: {approved_registrations}\n"
        )
        
        await event.respond(response)
        
    except Exception as e:
        await event.respond(f"خطا در دریافت آمار: {str(e)}")
    finally:
        db_session.close()

if __name__ == '__main__':
    print("Starting Event Registration Bot...")
    
    async def main():
        await client.start(bot_token=token)
        if client.is_connected():
            me = await client.get_me()
            print('✅ Bot Connected Successfully!')
            print(f'Bot username: @{me.username}')
        else:
            print('❌ Failed to connect bot')
        
        await client.run_until_disconnected()
    
    import asyncio
    asyncio.run(main())




