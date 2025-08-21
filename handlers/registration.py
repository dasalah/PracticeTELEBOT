from telethon import Button
from telethon.tl.types import DocumentAttributeFilename
from models.database import db_manager, User, Event, Registration, RejectedRegistration
from utils.validation import (
    validate_iranian_national_code, 
    validate_iranian_phone, 
    normalize_iranian_phone,
    clean_text_input
)
from utils.helpers import (
    get_user_session, 
    clear_user_session, 
    log_activity,
    log_message,
    safe_send_message,
    format_event_info,
    MessageTemplates,
    RegistrationSteps,
    generate_filename
)
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

async def handle_start_with_event(event, client, event_code):
    """Handle /start command with event code"""
    telegram_id = event.chat_id
    
    # Log the activity
    await log_activity(telegram_id, "accessed_event_link", f"Event code: {event_code}")
    
    # Find the event
    session = db_manager.get_session()
    try:
        db_event = session.query(Event).filter(Event.unique_code == event_code).first()
        
        if not db_event:
            await event.respond("❌ رویداد مورد نظر یافت نشد.")
            return
        
        # Check event status
        now = datetime.now()
        if db_event.status == 'inactive':
            await event.respond("❌ این رویداد غیرفعال است.")
            return
        elif db_event.status == 'expired' or now > db_event.end_date:
            await event.respond(MessageTemplates.EVENT_EXPIRED)
            return
        elif db_event.status == 'full' or db_event.registered_count >= db_event.capacity:
            await event.respond(MessageTemplates.EVENT_FULL)
            return
        
        # Check if user already registered
        existing_user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if existing_user:
            existing_registration = session.query(Registration).filter(
                Registration.user_id == existing_user.user_id,
                Registration.event_id == db_event.event_id
            ).first()
            
            if existing_registration:
                status_messages = {
                    'pending': "⏳ شما قبلاً در این رویداد ثبت‌نام کرده‌اید و در انتظار تایید هستید.",
                    'approved': "✅ شما قبلاً در این رویداد ثبت‌نام کرده و تایید شده‌اید.",
                    'rejected': "❌ ثبت‌نام قبلی شما رد شده است."
                }
                await event.respond(status_messages.get(existing_registration.status, "شما قبلاً ثبت‌نام کرده‌اید."))
                return
        
        # Show event info and start registration
        event_info = {
            'name': db_event.name,
            'description': db_event.description,
            'amount': db_event.amount,
            'card_number': db_event.card_number,
            'capacity': db_event.capacity,
            'registered_count': db_event.registered_count,
            'status': db_event.status,
            'start_date': db_event.start_date,
            'end_date': db_event.end_date
        }
        
        # Send event poster if available
        if db_event.poster_path and os.path.exists(db_event.poster_path):
            await client.send_file(
                telegram_id,
                db_event.poster_path,
                caption=format_event_info(event_info)
            )
        else:
            await event.respond(format_event_info(event_info))
        
        # Show payment information and registration button
        payment_message = f"""💳 اطلاعات پرداخت:
مبلغ: {db_event.amount:,} تومان
شماره کارت: {db_event.card_number}

⚠️ لطفا ابتدا مبلغ را واریز کرده، سپس ثبت‌نام را شروع کنید."""
        
        await event.respond(
            payment_message,
            buttons=[
                [Button.inline("شروع ثبت‌نام", f"start_registration_{db_event.event_id}")],
                [Button.inline("انصراف", "cancel_registration")]
            ]
        )
        
    except Exception as e:
        logger.error(f"Error handling start with event: {e}")
        await event.respond("❌ خطایی رخ داد. لطفا دوباره تلاش کنید.")
    finally:
        db_manager.close_session(session)

async def handle_registration_callback(event, client, event_id):
    """Handle registration start callback"""
    telegram_id = event.chat_id
    
    try:
        # Initialize user session
        user_session = get_user_session(telegram_id)
        user_session.event_id = int(event_id)
        user_session.set_step(RegistrationSteps.WAITING_FOR_FIRST_NAME)
        
        await log_activity(telegram_id, "started_registration", f"Event ID: {event_id}")
        
        await event.edit(
            "📝 لطفا نام خود را وارد کنید:",
            buttons=[
                [Button.inline("لغو ثبت‌نام", "cancel_registration")]
            ]
        )
        
    except Exception as e:
        logger.error(f"Error starting registration: {e}")
        await event.respond("❌ خطایی رخ داد. لطفا دوباره تلاش کنید.")

async def handle_text_message(event, client):
    """Handle text messages during registration process"""
    telegram_id = event.chat_id
    user_session = get_user_session(telegram_id)
    
    # Log message
    await log_message(telegram_id, event.text)
    
    if not user_session.step:
        return
    
    text = event.text.strip()
    
    try:
        if user_session.step == RegistrationSteps.WAITING_FOR_FIRST_NAME:
            first_name = clean_text_input(text)
            if not first_name:
                await event.respond("❌ نام وارد شده صحیح نیست. لطفا دوباره وارد کنید:")
                return
            
            user_session.set_data('first_name', first_name)
            user_session.set_step(RegistrationSteps.WAITING_FOR_LAST_NAME)
            await event.respond("👍 نام خانوادگی خود را وارد کنید:")
            
        elif user_session.step == RegistrationSteps.WAITING_FOR_LAST_NAME:
            last_name = clean_text_input(text)
            if not last_name:
                await event.respond("❌ نام خانوادگی وارد شده صحیح نیست. لطفا دوباره وارد کنید:")
                return
            
            user_session.set_data('last_name', last_name)
            user_session.set_step(RegistrationSteps.WAITING_FOR_NATIONAL_CODE)
            await event.respond("🆔 کد ملی خود را وارد کنید (10 رقم):")
            
        elif user_session.step == RegistrationSteps.WAITING_FOR_NATIONAL_CODE:
            if not validate_iranian_national_code(text):
                await event.respond("❌ کد ملی وارد شده صحیح نیست. لطفا کد ملی 10 رقمی معتبر وارد کنید:")
                return
            
            # Check if national code is already registered for this event
            session = db_manager.get_session()
            try:
                existing_user = session.query(User).filter(User.national_code == text).first()
                if existing_user:
                    existing_registration = session.query(Registration).filter(
                        Registration.user_id == existing_user.user_id,
                        Registration.event_id == user_session.event_id
                    ).first()
                    
                    if existing_registration:
                        await event.respond("❌ این کد ملی قبلاً در این رویداد ثبت‌نام شده است.")
                        clear_user_session(telegram_id)
                        return
                
            finally:
                db_manager.close_session(session)
            
            user_session.set_data('national_code', text)
            user_session.set_step(RegistrationSteps.WAITING_FOR_PHONE)
            await event.respond("📱 شماره تلفن همراه خود را وارد کنید (مثال: 09123456789):")
            
        elif user_session.step == RegistrationSteps.WAITING_FOR_PHONE:
            if not validate_iranian_phone(text):
                await event.respond("❌ شماره تلفن وارد شده صحیح نیست. لطفا شماره 11 رقمی معتبر وارد کنید (مثال: 09123456789):")
                return
            
            phone = normalize_iranian_phone(text)
            user_session.set_data('phone_number', phone)
            user_session.set_step(RegistrationSteps.WAITING_FOR_RECEIPT)
            
            await event.respond(
                "💳 فیش واریزی خود را ارسال کنید:\n"
                "• می‌توانید عکس فیش را ارسال کنید\n"
                "• یا شماره پیگیری/متن فیش را تایپ کنید"
            )
            
        elif user_session.step == RegistrationSteps.WAITING_FOR_RECEIPT:
            # Handle text receipt
            user_session.set_data('receipt_text', text)
            await show_confirmation(event, client, user_session)
            
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        await event.respond("❌ خطایی رخ داد. لطفا دوباره تلاش کنید.")

async def handle_photo_message(event, client):
    """Handle photo messages (receipt images)"""
    telegram_id = event.chat_id
    user_session = get_user_session(telegram_id)
    
    if user_session.step != RegistrationSteps.WAITING_FOR_RECEIPT:
        return
    
    try:
        # Generate filename for receipt
        filename = generate_filename("receipt", "jpg", telegram_id)
        filepath = os.path.join("receipts", filename)
        
        # Download photo
        await event.download_media(file=filepath)
        
        user_session.set_data('receipt_path', filepath)
        user_session.set_data('receipt_text', event.text or "تصویر فیش واریزی")
        
        await show_confirmation(event, client, user_session)
        
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        await event.respond("❌ خطا در دریافت تصویر. لطفا دوباره تلاش کنید.")

async def show_confirmation(event, client, user_session):
    """Show registration confirmation"""
    try:
        # Get event info
        session = db_manager.get_session()
        db_event = session.query(Event).filter(Event.event_id == user_session.event_id).first()
        
        if not db_event:
            await event.respond("❌ رویداد یافت نشد.")
            clear_user_session(event.chat_id)
            return
        
        confirmation_text = f"""📋 اطلاعات ثبت‌نام شما:

👤 نام: {user_session.get_data('first_name')} {user_session.get_data('last_name')}
🆔 کد ملی: {user_session.get_data('national_code')}
📱 تلفن: {user_session.get_data('phone_number')}
🎭 رویداد: {db_event.name}
💳 فیش: {user_session.get_data('receipt_text', 'ارسال شده')}

آیا اطلاعات صحیح است؟"""
        
        user_session.set_step(RegistrationSteps.CONFIRMATION)
        
        await event.respond(
            confirmation_text,
            buttons=[
                [Button.inline("✅ تایید و ثبت نهایی", "confirm_registration")],
                [Button.inline("✏️ ویرایش اطلاعات", "edit_registration")],
                [Button.inline("❌ انصراف", "cancel_registration")]
            ]
        )
        
    except Exception as e:
        logger.error(f"Error showing confirmation: {e}")
        await event.respond("❌ خطایی رخ داد. لطفا دوباره تلاش کنید.")
    finally:
        if 'session' in locals():
            db_manager.close_session(session)

async def handle_confirm_registration(event, client):
    """Handle final registration confirmation"""
    telegram_id = event.chat_id
    user_session = get_user_session(telegram_id)
    
    if user_session.step != RegistrationSteps.CONFIRMATION:
        await event.answer("❌ مرحله ثبت‌نام صحیح نیست.")
        return
    
    session = db_manager.get_session()
    try:
        # Create or get user
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                first_name=user_session.get_data('first_name'),
                last_name=user_session.get_data('last_name'),
                national_code=user_session.get_data('national_code'),
                phone_number=user_session.get_data('phone_number')
            )
            session.add(user)
            session.flush()  # To get user_id
        
        # Create registration
        registration = Registration(
            user_id=user.user_id,
            event_id=user_session.event_id,
            status='pending',
            payment_receipt_path=user_session.get_data('receipt_path'),
            payment_receipt_text=user_session.get_data('receipt_text')
        )
        
        session.add(registration)
        session.commit()
        
        # Update event registered count
        db_event = session.query(Event).filter(Event.event_id == user_session.event_id).first()
        if db_event:
            db_event.registered_count += 1
            session.commit()
        
        await log_activity(telegram_id, "completed_registration", f"Event ID: {user_session.event_id}")
        
        await event.edit(MessageTemplates.REGISTRATION_SUCCESS)
        
        # Clear session
        clear_user_session(telegram_id)
        
        # Notify admins (this would be implemented in admin handlers)
        # await notify_admins_new_registration(client, registration)
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error confirming registration: {e}")
        await event.respond("❌ خطا در ثبت اطلاعات. لطفا دوباره تلاش کنید.")
    finally:
        db_manager.close_session(session)

async def handle_cancel_registration(event, client):
    """Handle registration cancellation"""
    telegram_id = event.chat_id
    
    clear_user_session(telegram_id)
    await log_activity(telegram_id, "cancelled_registration")
    
    await event.edit(MessageTemplates.OPERATION_CANCELLED)

async def handle_edit_registration(event, client):
    """Handle registration edit request"""
    telegram_id = event.chat_id
    user_session = get_user_session(telegram_id)
    
    # Reset to first step
    user_session.set_step(RegistrationSteps.WAITING_FOR_FIRST_NAME)
    user_session.data.clear()
    
    await event.edit(
        "✏️ ویرایش اطلاعات - لطفا نام خود را وارد کنید:",
        buttons=[
            [Button.inline("لغو ثبت‌نام", "cancel_registration")]
        ]
    )