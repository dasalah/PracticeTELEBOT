
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
API_ID = int(os.getenv('API_ID', '7960798'))
API_HASH = os.getenv('API_HASH', '481fb8835f23b673264c49abfc092122')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7520442360:AAEB8GkJLcJXQpeg7KJ2umyv-eRutvlPblI')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///event_bot.db')

# Super Admin Configuration (Telegram ID of the main admin)
SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID', '6033723482'))

# File Upload Configuration
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB default
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']

# Session Configuration
SESSION_NAME = os.getenv('SESSION_NAME', 'event_bot_session')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'bot.log')

# Directories
RECEIPTS_DIR = 'receipts'
POSTERS_DIR = 'posters'  
EXPORTS_DIR = 'exports'

# Validation Configuration
NATIONAL_CODE_LENGTH = 10
PHONE_NUMBER_LENGTH = 11

# Persian messages
MESSAGES = {
    'welcome': '🌟 خوش آمدید به سیستم ثبت‌نام رویدادها',
    'invalid_event_code': '❌ کد رویداد نامعتبر است',
    'event_not_found': '❌ رویداد مورد نظر یافت نشد',
    'event_inactive': '❌ این رویداد غیرفعال است',
    'event_expired': '⏰ مهلت ثبت‌نام این رویداد به پایان رسیده است',
    'event_full': '🚫 متاسفانه ظرفیت این رویداد تکمیل شده است',
    'already_registered': '⚠️ شما قبلاً در این رویداد ثبت‌نام کرده‌اید',
    'registration_success': '✅ ثبت‌نام شما با موفقیت انجام شد و در انتظار تایید قرار گرفت',
    'registration_approved': '🎉 تبریک! ثبت‌نام شما تایید شد',
    'registration_rejected': '❌ متاسفانه ثبت‌نام شما رد شد',
    'invalid_national_code': '❌ کد ملی وارد شده صحیح نیست',
    'invalid_phone': '❌ شماره تلفن وارد شده صحیح نیست',
    'operation_cancelled': '🔴 عملیات لغو شد',
    'admin_panel': '🛠 پنل مدیریت',
    'no_permission': '⛔ شما اجازه دسترسی به این بخش را ندارید',
    'error_occurred': '❌ خطایی رخ داد. لطفا دوباره تلاش کنید'
}

def validate_config():
    """Validate required configuration"""
    required_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'SUPER_ADMIN_ID']
    missing_vars = []
    
    for var in required_vars:
        if not globals().get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True