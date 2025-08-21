from telethon import Button
from models.database import db_manager, Admin, Event, Registration, User, RejectedRegistration
from utils.helpers import (
    log_activity,
    safe_send_message,
    format_event_info,
    format_registration_info,
    MessageTemplates,
    generate_filename,
    ensure_directories
)
from utils.excel_export import create_registration_excel, ensure_export_directory
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

async def is_admin(telegram_id):
    """Check if user is admin"""
    session = db_manager.get_session()
    try:
        admin = session.query(Admin).filter(Admin.telegram_id == telegram_id).first()
        return admin is not None
    finally:
        db_manager.close_session(session)

async def is_super_admin(telegram_id):
    """Check if user is super admin"""
    session = db_manager.get_session()
    try:
        admin = session.query(Admin).filter(
            Admin.telegram_id == telegram_id,
            Admin.is_super_admin == True
        ).first()
        return admin is not None
    finally:
        db_manager.close_session(session)

async def handle_admin_start(event, client):
    """Handle admin start command"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.respond(MessageTemplates.NO_PERMISSION)
        return
    
    await log_activity(telegram_id, "accessed_admin_panel")
    
    is_super = await is_super_admin(telegram_id)
    
    buttons = [
        [Button.inline("📊 آمار کلی", "admin_stats")],
        [Button.inline("📋 مدیریت رویدادها", "admin_events")],
        [Button.inline("✅ تایید ثبت‌نام‌ها", "admin_approvals")],
        [Button.inline("📁 دریافت Excel", "admin_excel")]
    ]
    
    if is_super:
        buttons.append([Button.inline("👥 مدیریت ادمین‌ها", "admin_manage_admins")])
    
    await event.respond(
        MessageTemplates.ADMIN_PANEL,
        buttons=buttons
    )

async def handle_admin_stats(event, client):
    """Show admin statistics"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.answer(MessageTemplates.NO_PERMISSION)
        return
    
    session = db_manager.get_session()
    try:
        # Get statistics
        total_events = session.query(Event).count()
        active_events = session.query(Event).filter(Event.status == 'active').count()
        total_registrations = session.query(Registration).count()
        pending_registrations = session.query(Registration).filter(Registration.status == 'pending').count()
        approved_registrations = session.query(Registration).filter(Registration.status == 'approved').count()
        rejected_registrations = session.query(Registration).filter(Registration.status == 'rejected').count()
        total_users = session.query(User).count()
        
        stats_text = f"""📊 آمار کلی سیستم:

🎭 رویدادها:
  • کل رویدادها: {total_events}
  • رویدادهای فعال: {active_events}

👥 کاربران:
  • کل کاربران: {total_users}

📋 ثبت‌نام‌ها:
  • کل ثبت‌نام‌ها: {total_registrations}
  • در انتظار تایید: {pending_registrations}
  • تایید شده: {approved_registrations}
  • رد شده: {rejected_registrations}

🕐 تاریخ گزارش: {datetime.now().strftime('%Y/%m/%d - %H:%M')}"""
        
        await event.edit(
            stats_text,
            buttons=[
                [Button.inline("🔙 بازگشت", "admin_back")]
            ]
        )
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        await event.edit("❌ خطا در دریافت آمار.")
    finally:
        db_manager.close_session(session)

async def handle_admin_events(event, client):
    """Handle admin events management"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.answer(MessageTemplates.NO_PERMISSION)
        return
    
    session = db_manager.get_session()
    try:
        events = session.query(Event).order_by(Event.created_at.desc()).limit(10).all()
        
        if not events:
            await event.edit(
                "📋 هیچ رویدادی یافت نشد.",
                buttons=[
                    [Button.inline("➕ ایجاد رویداد جدید", "admin_create_event")],
                    [Button.inline("🔙 بازگشت", "admin_back")]
                ]
            )
            return
        
        events_text = "📋 رویدادهای اخیر:\n\n"
        buttons = []
        
        for event_obj in events:
            status_emoji = {'active': '✅', 'inactive': '❌', 'full': '🚫', 'expired': '⏰'}.get(event_obj.status, '❓')
            events_text += f"{status_emoji} {event_obj.name} ({event_obj.registered_count}/{event_obj.capacity})\n"
            buttons.append([Button.inline(f"📝 {event_obj.name[:30]}...", f"admin_event_{event_obj.event_id}")])
        
        buttons.append([Button.inline("➕ ایجاد رویداد جدید", "admin_create_event")])
        buttons.append([Button.inline("🔙 بازگشت", "admin_back")])
        
        await event.edit(events_text, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error handling admin events: {e}")
        await event.edit("❌ خطا در دریافت رویدادها.")
    finally:
        db_manager.close_session(session)

async def handle_admin_approvals(event, client):
    """Handle registration approvals"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.answer(MessageTemplates.NO_PERMISSION)
        return
    
    session = db_manager.get_session()
    try:
        pending_registrations = session.query(Registration).filter(
            Registration.status == 'pending'
        ).join(User).join(Event).order_by(Registration.registration_date.desc()).limit(5).all()
        
        if not pending_registrations:
            await event.edit(
                "✅ هیچ ثبت‌نام در انتظار تایید نیست.",
                buttons=[
                    [Button.inline("🔙 بازگشت", "admin_back")]
                ]
            )
            return
        
        buttons = []
        for registration in pending_registrations:
            user_name = f"{registration.user.first_name} {registration.user.last_name}"
            event_name = registration.event.name[:20]
            buttons.append([
                Button.inline(f"👤 {user_name} - {event_name}", f"admin_review_{registration.registration_id}")
            ])
        
        buttons.append([Button.inline("🔙 بازگشت", "admin_back")])
        
        await event.edit(
            f"⏳ ثبت‌نام‌های در انتظار تایید ({len(pending_registrations)}):",
            buttons=buttons
        )
        
    except Exception as e:
        logger.error(f"Error handling approvals: {e}")
        await event.edit("❌ خطا در دریافت ثبت‌نام‌ها.")
    finally:
        db_manager.close_session(session)

async def handle_registration_review(event, client, registration_id):
    """Handle individual registration review"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.answer(MessageTemplates.NO_PERMISSION)
        return
    
    session = db_manager.get_session()
    try:
        registration = session.query(Registration).filter(
            Registration.registration_id == registration_id
        ).join(User).join(Event).first()
        
        if not registration:
            await event.edit("❌ ثبت‌نام یافت نشد.")
            return
        
        # Prepare registration info
        reg_info = {
            'first_name': registration.user.first_name,
            'last_name': registration.user.last_name,
            'national_code': registration.user.national_code,
            'phone_number': registration.user.phone_number,
            'registration_date': registration.registration_date,
            'payment_receipt_text': registration.payment_receipt_text
        }
        
        review_text = f"""📋 بررسی ثبت‌نام:

🎭 رویداد: {registration.event.name}

{format_registration_info(reg_info)}

وضعیت: {registration.status}"""
        
        buttons = [
            [
                Button.inline("✅ تایید", f"approve_{registration_id}"),
                Button.inline("❌ رد", f"reject_{registration_id}")
            ]
        ]
        
        # Add receipt view button if available
        if registration.payment_receipt_path and os.path.exists(registration.payment_receipt_path):
            buttons.append([Button.inline("🖼 نمایش فیش", f"view_receipt_{registration_id}")])
        
        buttons.append([Button.inline("🔙 بازگشت", "admin_approvals")])
        
        await event.edit(review_text, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error reviewing registration: {e}")
        await event.edit("❌ خطا در نمایش ثبت‌نام.")
    finally:
        db_manager.close_session(session)

async def handle_approve_registration(event, client, registration_id):
    """Approve a registration"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.answer(MessageTemplates.NO_PERMISSION)
        return
    
    session = db_manager.get_session()
    try:
        registration = session.query(Registration).filter(
            Registration.registration_id == registration_id
        ).join(User).first()
        
        if not registration:
            await event.answer("❌ ثبت‌نام یافت نشد.")
            return
        
        # Update registration status
        registration.status = 'approved'
        registration.approval_date = datetime.now()
        session.commit()
        
        await log_activity(telegram_id, "approved_registration", f"Registration ID: {registration_id}")
        
        # Notify user
        try:
            await client.send_message(
                registration.user.telegram_id,
                MessageTemplates.REGISTRATION_APPROVED
            )
        except:
            logger.warning(f"Could not notify user {registration.user.telegram_id}")
        
        await event.answer("✅ ثبت‌نام تایید شد و کاربر مطلع گردید.")
        
        # Return to approvals list
        await handle_admin_approvals(event, client)
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error approving registration: {e}")
        await event.answer("❌ خطا در تایید ثبت‌نام.")
    finally:
        db_manager.close_session(session)

async def handle_reject_registration(event, client, registration_id):
    """Reject a registration"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.answer(MessageTemplates.NO_PERMISSION)
        return
    
    session = db_manager.get_session()
    try:
        registration = session.query(Registration).filter(
            Registration.registration_id == registration_id
        ).join(User).join(Event).first()
        
        if not registration:
            await event.answer("❌ ثبت‌نام یافت نشد.")
            return
        
        # Move to rejected registrations
        rejected_registration = RejectedRegistration(
            user_id=registration.user_id,
            event_id=registration.event_id,
            telegram_id=registration.user.telegram_id,
            first_name=registration.user.first_name,
            last_name=registration.user.last_name,
            national_code=registration.user.national_code,
            phone_number=registration.user.phone_number,
            payment_receipt_path=registration.payment_receipt_path,
            payment_receipt_text=registration.payment_receipt_text,
            rejection_reason="رد شده توسط ادمین"
        )
        
        session.add(rejected_registration)
        
        # Update registration status
        registration.status = 'rejected'
        session.commit()
        
        # Decrease event registered count
        event_obj = registration.event
        if event_obj.registered_count > 0:
            event_obj.registered_count -= 1
            session.commit()
        
        await log_activity(telegram_id, "rejected_registration", f"Registration ID: {registration_id}")
        
        # Notify user
        try:
            await client.send_message(
                registration.user.telegram_id,
                MessageTemplates.REGISTRATION_REJECTED
            )
        except:
            logger.warning(f"Could not notify user {registration.user.telegram_id}")
        
        await event.answer("❌ ثبت‌نام رد شد و کاربر مطلع گردید.")
        
        # Return to approvals list
        await handle_admin_approvals(event, client)
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error rejecting registration: {e}")
        await event.answer("❌ خطا در رد ثبت‌نام.")
    finally:
        db_manager.close_session(session)

async def handle_view_receipt(event, client, registration_id):
    """View payment receipt"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.answer(MessageTemplates.NO_PERMISSION)
        return
    
    session = db_manager.get_session()
    try:
        registration = session.query(Registration).filter(
            Registration.registration_id == registration_id
        ).first()
        
        if not registration:
            await event.answer("❌ ثبت‌نام یافت نشد.")
            return
        
        if registration.payment_receipt_path and os.path.exists(registration.payment_receipt_path):
            await client.send_file(
                telegram_id,
                registration.payment_receipt_path,
                caption="💳 فیش واریزی"
            )
        else:
            await event.answer("❌ فیش واریزی یافت نشد.")
        
    except Exception as e:
        logger.error(f"Error viewing receipt: {e}")
        await event.answer("❌ خطا در نمایش فیش.")
    finally:
        db_manager.close_session(session)

async def handle_admin_excel(event, client):
    """Handle Excel export request"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.answer(MessageTemplates.NO_PERMISSION)
        return
    
    session = db_manager.get_session()
    try:
        # Get events for selection
        events = session.query(Event).order_by(Event.created_at.desc()).limit(10).all()
        
        if not events:
            await event.edit(
                "📋 هیچ رویدادی برای صدور Excel یافت نشد.",
                buttons=[[Button.inline("🔙 بازگشت", "admin_back")]]
            )
            return
        
        buttons = []
        for event_obj in events:
            buttons.append([
                Button.inline(f"📊 {event_obj.name[:30]}...", f"excel_{event_obj.event_id}")
            ])
        
        buttons.append([Button.inline("🔙 بازگشت", "admin_back")])
        
        await event.edit(
            "📁 انتخاب رویداد برای دریافت Excel:",
            buttons=buttons
        )
        
    except Exception as e:
        logger.error(f"Error handling Excel request: {e}")
        await event.edit("❌ خطا در آماده‌سازی لیست رویدادها.")
    finally:
        db_manager.close_session(session)

async def handle_generate_excel(event, client, event_id):
    """Generate and send Excel file"""
    telegram_id = event.chat_id
    
    if not await is_admin(telegram_id):
        await event.answer(MessageTemplates.NO_PERMISSION)
        return
    
    await event.answer("📊 در حال تولید فایل Excel...")
    
    session = db_manager.get_session()
    try:
        # Get event data
        db_event = session.query(Event).filter(Event.event_id == event_id).first()
        if not db_event:
            await event.edit("❌ رویداد یافت نشد.")
            return
        
        # Get registrations data
        registrations = session.query(Registration).filter(
            Registration.event_id == event_id
        ).join(User).all()
        
        approved_registrations = [r for r in registrations if r.status == 'approved']
        rejected_registrations = session.query(RejectedRegistration).filter(
            RejectedRegistration.event_id == event_id
        ).all()
        
        # Prepare data
        event_data = {
            'name': db_event.name,
            'description': db_event.description,
            'amount': db_event.amount,
            'card_number': db_event.card_number,
            'capacity': db_event.capacity,
            'registered_count': db_event.registered_count,
            'status': db_event.status,
            'start_date': db_event.start_date,
            'end_date': db_event.end_date,
            'unique_code': db_event.unique_code,
            'created_at': db_event.created_at
        }
        
        def prepare_registration_data(regs):
            return [{
                'first_name': r.user.first_name if hasattr(r, 'user') else r.first_name,
                'last_name': r.user.last_name if hasattr(r, 'user') else r.last_name,
                'national_code': r.user.national_code if hasattr(r, 'user') else r.national_code,
                'phone_number': r.user.phone_number if hasattr(r, 'user') else r.phone_number,
                'status': getattr(r, 'status', 'rejected'),
                'registration_date': getattr(r, 'registration_date', getattr(r, 'rejected_date', None)),
                'approval_date': getattr(r, 'approval_date', None),
                'payment_receipt_text': r.payment_receipt_text,
                'payment_receipt_path': r.payment_receipt_path
            } for r in regs]
        
        all_registrations_data = prepare_registration_data(registrations)
        approved_data = prepare_registration_data(approved_registrations)
        rejected_data = prepare_registration_data(rejected_registrations)
        
        # Generate Excel file
        ensure_export_directory()
        filename = generate_filename(f"event_{db_event.event_id}_registrations", "xlsx")
        filepath = os.path.join("exports", filename)
        
        create_registration_excel(
            event_data,
            all_registrations_data,
            approved_data,
            rejected_data,
            filepath
        )
        
        await log_activity(telegram_id, "generated_excel", f"Event ID: {event_id}")
        
        # Send file
        await client.send_file(
            telegram_id,
            filepath,
            caption=f"📊 گزارش Excel رویداد: {db_event.name}",
            attributes=[
                DocumentAttributeFilename(
                    file_name=f"{db_event.name}_registrations.xlsx"
                )
            ]
        )
        
        # Clean up file
        try:
            os.remove(filepath)
        except:
            pass
        
        await event.edit("✅ فایل Excel ارسال شد.")
        
    except Exception as e:
        logger.error(f"Error generating Excel: {e}")
        await event.edit("❌ خطا در تولید فایل Excel.")
    finally:
        db_manager.close_session(session)

async def handle_admin_back(event, client):
    """Handle admin back button"""
    await handle_admin_start(event, client)