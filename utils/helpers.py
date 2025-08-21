import os
import logging
import asyncio
from datetime import datetime
from models.database import db_manager, ActivityLog, MessageLog

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Session management for user registration process
user_sessions = {}

class UserSession:
    def __init__(self, telegram_id):
        self.telegram_id = telegram_id
        self.step = None
        self.data = {}
        self.event_id = None
        self.created_at = datetime.now()
    
    def set_step(self, step):
        self.step = step
        logger.info(f"User {self.telegram_id} moved to step: {step}")
    
    def set_data(self, key, value):
        self.data[key] = value
        logger.info(f"User {self.telegram_id} set {key}")
    
    def get_data(self, key):
        return self.data.get(key)
    
    def clear(self):
        self.step = None
        self.data = {}
        self.event_id = None

def get_user_session(telegram_id):
    """Get or create user session"""
    if telegram_id not in user_sessions:
        user_sessions[telegram_id] = UserSession(telegram_id)
    return user_sessions[telegram_id]

def clear_user_session(telegram_id):
    """Clear user session"""
    if telegram_id in user_sessions:
        user_sessions[telegram_id].clear()

async def log_activity(telegram_id, action, details=None):
    """Log user activity to database"""
    session = db_manager.get_session()
    try:
        activity = ActivityLog(
            telegram_id=telegram_id,
            action=action,
            details=details
        )
        session.add(activity)
        session.commit()
        logger.info(f"Activity logged: {telegram_id} - {action}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error logging activity: {e}")
    finally:
        db_manager.close_session(session)

async def log_message(telegram_user_id, message_content):
    """Log message to database"""
    session = db_manager.get_session()
    try:
        message = MessageLog(
            telegram_user_id=telegram_user_id,
            message_content=message_content[:1000]  # Limit length
        )
        session.add(message)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error logging message: {e}")
    finally:
        db_manager.close_session(session)

def ensure_directories():
    """Ensure all required directories exist"""
    directories = ['receipts', 'posters', 'exports']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def generate_filename(prefix, extension, user_id=None):
    """Generate unique filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if user_id:
        return f"{prefix}_{user_id}_{timestamp}.{extension}"
    return f"{prefix}_{timestamp}.{extension}"

async def safe_send_message(client, chat_id, message, **kwargs):
    """Safely send message with error handling"""
    try:
        return await client.send_message(chat_id, message, **kwargs)
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")
        return None

async def safe_edit_message(message, new_text, **kwargs):
    """Safely edit message with error handling"""
    try:
        return await message.edit(new_text, **kwargs)
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return None

def format_persian_date(dt):
    """Format datetime to Persian readable format"""
    if not dt:
        return "نامشخص"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    
    return dt.strftime("%Y/%m/%d - %H:%M")

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def format_registration_info(registration_data):
    """Format registration information for display"""
    return f"""👤 نام: {registration_data.get('first_name', '')} {registration_data.get('last_name', '')}
🆔 کد ملی: {registration_data.get('national_code', '')}
📱 تلفن: {registration_data.get('phone_number', '')}
📅 تاریخ ثبت‌نام: {format_persian_date(registration_data.get('registration_date', ''))}
💳 متن فیش: {truncate_text(registration_data.get('payment_receipt_text', 'ندارد'))}"""

def format_event_info(event_data):
    """Format event information for display"""
    status_emoji = {
        'active': '✅',
        'inactive': '❌',
        'full': '🚫',
        'expired': '⏰'
    }
    
    status = event_data.get('status', 'active')
    emoji = status_emoji.get(status, '❓')
    
    return f"""🎭 {event_data.get('name', '')}
📋 {event_data.get('description', '')}
💰 مبلغ: {event_data.get('amount', 0):,} تومان
💳 شماره کارت: {event_data.get('card_number', '')}
👥 ظرفیت: {event_data.get('registered_count', 0)}/{event_data.get('capacity', 0)}
{emoji} وضعیت: {status}
📅 شروع: {format_persian_date(event_data.get('start_date', ''))}
📅 پایان: {format_persian_date(event_data.get('end_date', ''))}"""

class MessageTemplates:
    """Message templates for consistent messaging"""
    
    WELCOME = "🌟 خوش آمدید به سیستم ثبت‌نام رویدادها"
    
    START_REGISTRATION = "📝 برای شروع ثبت‌نام، اطلاعات زیر را به ترتیب ارسال کنید:"
    
    REGISTRATION_SUCCESS = "✅ ثبت‌نام شما با موفقیت انجام شد و در انتظار تایید قرار گرفت."
    
    REGISTRATION_APPROVED = "🎉 تبریک! ثبت‌نام شما تایید شد."
    
    REGISTRATION_REJECTED = "❌ متاسفانه ثبت‌نام شما رد شد."
    
    EVENT_FULL = "🚫 متاسفانه ظرفیت این رویداد تکمیل شده است."
    
    EVENT_EXPIRED = "⏰ مهلت ثبت‌نام این رویداد به پایان رسیده است."
    
    INVALID_INPUT = "❌ اطلاعات وارد شده صحیح نیست. لطفا دوباره تلاش کنید."
    
    OPERATION_CANCELLED = "🔴 عملیات لغو شد."
    
    ADMIN_PANEL = "🛠 پنل مدیریت"
    
    NO_PERMISSION = "⛔ شما اجازه دسترسی به این بخش را ندارید."

# Registration steps
class RegistrationSteps:
    WAITING_FOR_FIRST_NAME = "first_name"
    WAITING_FOR_LAST_NAME = "last_name"
    WAITING_FOR_NATIONAL_CODE = "national_code"
    WAITING_FOR_PHONE = "phone"
    WAITING_FOR_RECEIPT = "receipt"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"