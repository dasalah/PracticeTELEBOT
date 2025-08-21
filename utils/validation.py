import re

def persian_to_english_numbers(text):
    """Convert Persian/Farsi numbers to English numbers"""
    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    english_numbers = '0123456789'
    
    for persian, english in zip(persian_numbers, english_numbers):
        text = text.replace(persian, english)
    
    return text

def validate_iranian_national_code(national_code):
    """
    Validate Iranian national code using the official algorithm
    Returns True if valid, False otherwise
    """
    # Convert Persian numbers to English
    national_code = persian_to_english_numbers(str(national_code))
    
    # Remove any non-digit characters
    national_code = re.sub(r'\D', '', national_code)
    
    # Must be exactly 10 digits
    if len(national_code) != 10:
        return False
    
    # All digits can't be the same
    if len(set(national_code)) == 1:
        return False
    
    # Calculate check digit
    check_sum = 0
    for i in range(9):
        check_sum += int(national_code[i]) * (10 - i)
    
    remainder = check_sum % 11
    check_digit = int(national_code[9])
    
    # Validation logic
    if remainder < 2:
        return check_digit == remainder
    else:
        return check_digit == 11 - remainder

def validate_iranian_phone(phone):
    """
    Validate Iranian phone number
    Accepts formats: 09xxxxxxxxx, +989xxxxxxxxx, 00989xxxxxxxxx
    """
    # Convert Persian numbers to English
    phone = persian_to_english_numbers(str(phone))
    
    # Remove any non-digit characters except + at the beginning
    if phone.startswith('+'):
        phone = '+' + re.sub(r'\D', '', phone[1:])
    else:
        phone = re.sub(r'\D', '', phone)
    
    # Different valid patterns
    patterns = [
        r'^09\d{9}$',           # 09xxxxxxxxx
        r'^\+989\d{9}$',        # +989xxxxxxxxx
        r'^00989\d{9}$'         # 00989xxxxxxxxx
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    
    return False

def normalize_iranian_phone(phone):
    """
    Normalize Iranian phone number to 09xxxxxxxxx format
    """
    # Convert Persian numbers to English
    phone = persian_to_english_numbers(str(phone))
    
    # Remove any non-digit characters except + at the beginning
    if phone.startswith('+'):
        phone = re.sub(r'\D', '', phone[1:])
    else:
        phone = re.sub(r'\D', '', phone)
    
    # Convert to standard format
    if phone.startswith('00989'):
        return '0' + phone[4:]
    elif phone.startswith('989'):
        return '0' + phone[2:]
    elif phone.startswith('9') and len(phone) == 10:
        return '0' + phone
    elif phone.startswith('09') and len(phone) == 11:
        return phone
    
    return None

def validate_amount(amount_str):
    """
    Validate and convert amount string to integer
    """
    try:
        # Convert Persian numbers
        amount_str = persian_to_english_numbers(str(amount_str))
        # Remove any non-digit characters
        amount_str = re.sub(r'\D', '', amount_str)
        amount = int(amount_str)
        return amount if amount > 0 else None
    except (ValueError, TypeError):
        return None

def format_currency(amount):
    """
    Format currency amount with thousands separator
    """
    return f"{amount:,} تومان"

def clean_text_input(text):
    """
    Clean and validate text input
    """
    if not text or not isinstance(text, str):
        return None
    
    # Strip whitespace
    text = text.strip()
    
    # Must not be empty after stripping
    if not text:
        return None
    
    # Must be reasonable length
    if len(text) > 100:
        return None
    
    return text