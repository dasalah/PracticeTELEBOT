"""
Utility functions for validation and Persian number support
"""

import re
import hashlib
import random
import string
from datetime import datetime

# Persian to English number mapping
PERSIAN_NUMBERS = {
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
}

ARABIC_NUMBERS = {
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
}

def persian_to_english(text):
    """Convert Persian/Arabic numbers to English numbers"""
    if not text:
        return text
    
    result = str(text)
    
    # Convert Persian numbers
    for persian, english in PERSIAN_NUMBERS.items():
        result = result.replace(persian, english)
    
    # Convert Arabic numbers
    for arabic, english in ARABIC_NUMBERS.items():
        result = result.replace(arabic, english)
    
    return result

def validate_iranian_national_code(code):
    """
    Validate Iranian national code (کد ملی)
    Returns True if valid, False otherwise
    """
    if not code:
        return False
    
    # Convert Persian/Arabic numbers to English
    code = persian_to_english(code)
    
    # Remove any non-digit characters
    code = re.sub(r'\D', '', code)
    
    # Check length
    if len(code) != 10:
        return False
    
    # Check if all digits are the same
    if len(set(code)) == 1:
        return False
    
    # Special invalid codes
    invalid_codes = ['0123456789', '1234567890', '0000000000', '1111111111',
                    '2222222222', '3333333333', '4444444444', '5555555555',
                    '6666666666', '7777777777', '8888888888', '9999999999']
    
    if code in invalid_codes:
        return False
    
    # Calculate checksum using Iranian national code algorithm
    check_sum = 0
    for i in range(9):
        check_sum += int(code[i]) * (10 - i)
    
    remainder = check_sum % 11
    check_digit = int(code[9])
    
    if remainder < 2:
        return check_digit == remainder
    else:
        return check_digit == 11 - remainder

def validate_iranian_phone(phone):
    """
    Validate Iranian phone number
    Returns True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Convert Persian/Arabic numbers to English
    phone = persian_to_english(phone)
    
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Check if it's an Iranian mobile number (starts with 09 and has 11 digits)
    if len(phone) == 11 and phone.startswith('09'):
        return True
    
    return False

def normalize_phone_number(phone):
    """
    Normalize phone number to standard format
    """
    if not phone:
        return None
    
    # Convert Persian/Arabic numbers to English
    phone = persian_to_english(phone)
    
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Ensure it starts with 09
    if len(phone) == 11 and phone.startswith('09'):
        return phone
    elif len(phone) == 10 and phone.startswith('9'):
        return '0' + phone
    
    return None

def normalize_national_code(code):
    """
    Normalize national code to standard format
    """
    if not code:
        return None
    
    # Convert Persian/Arabic numbers to English
    code = persian_to_english(code)
    
    # Remove any non-digit characters
    code = re.sub(r'\D', '', code)
    
    # Pad with zeros if needed (up to 10 digits)
    if len(code) <= 10:
        code = code.zfill(10)
    
    return code

def generate_unique_event_code():
    """
    Generate unique code for event
    """
    timestamp = str(int(datetime.now().timestamp()))
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"event_{timestamp}_{random_suffix}"

def create_event_link(bot_username, event_code):
    """
    Create event registration link
    """
    return f"t.me/{bot_username}?start={event_code}"

def sanitize_filename(filename):
    """
    Sanitize filename for saving files
    """
    # Remove/replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename

def format_currency(amount):
    """
    Format currency in Iranian style
    """
    if not amount:
        return "0 تومان"
    
    # Add thousand separators
    formatted = f"{amount:,}".replace(',', '٬')
    return f"{formatted} تومان"

def log_activity(session, user_id, action, details=None):
    """
    Log user activity
    """
    from userDB import ActivityLog
    
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        details=details
    )
    session.add(activity)
    session.commit()

def log_message(session, telegram_user_id, message_content):
    """
    Log message
    """
    from userDB import MessageLog
    
    message_log = MessageLog(
        telegram_user_id=telegram_user_id,
        message_content=message_content
    )
    session.add(message_log)
    session.commit()

def is_admin(session, telegram_id):
    """
    Check if user is admin
    """
    from userDB import Admin
    
    admin = session.query(Admin).filter_by(telegram_id=telegram_id).first()
    return admin is not None

def is_super_admin(session, telegram_id):
    """
    Check if user is super admin
    """
    from userDB import Admin
    
    admin = session.query(Admin).filter_by(telegram_id=telegram_id, is_super_admin=True).first()
    return admin is not None

def check_duplicate_registration(session, national_code, event_id):
    """
    Check if user with this national code is already registered for this event
    """
    from userDB import User, Registration, RegistrationStatus
    
    user = session.query(User).filter_by(national_code=national_code).first()
    if not user:
        return False
    
    existing_registration = session.query(Registration).filter_by(
        user_id=user.user_id,
        event_id=event_id,
        status=RegistrationStatus.APPROVED
    ).first()
    
    return existing_registration is not None