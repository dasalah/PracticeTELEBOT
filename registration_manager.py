"""
Registration system for users
"""

from telethon import Button
from datetime import datetime
import os
from userDB import (User, Event, Registration, RegistrationStatus, EventStatus, 
                   create_db_session, Admin)
from utils import (validate_iranian_national_code, validate_iranian_phone,
                   normalize_national_code, normalize_phone_number,
                   check_duplicate_registration, format_currency, log_activity)

class RegistrationManager:
    def __init__(self):
        self.sessions = {}  # Store user registration sessions
    
    def init_registration_session(self, user_id, event_id):
        """Initialize registration session for user"""
        self.sessions[user_id] = {
            'event_id': event_id,
            'step': 0,
            'data': {}
        }
    
    def get_session(self, user_id):
        """Get user registration session"""
        return self.sessions.get(user_id)
    
    def clear_session(self, user_id):
        """Clear user registration session"""
        if user_id in self.sessions:
            del self.sessions[user_id]
    
    async def handle_event_start(self, event, client, event_code):
        """Handle user clicking on event registration link"""
        db_session = create_db_session()
        
        try:
            # Find event by unique code
            event_obj = db_session.query(Event).filter_by(unique_code=event_code).first()
            
            if not event_obj:
                await event.respond("رویداد یافت نشد.")
                return
            
            # Check event status
            if event_obj.status != EventStatus.ACTIVE:
                status_msg = {
                    EventStatus.INACTIVE: "این رویداد غیرفعال است.",
                    EventStatus.COMPLETED: "این رویداد تمام شده است.",
                    EventStatus.EXPIRED: "مهلت ثبت نام این رویداد به پایان رسیده است."
                }.get(event_obj.status, "این رویداد در حال حاضر قابل دسترس نیست.")
                
                await event.respond(status_msg)
                return
            
            # Check capacity
            if event_obj.registered_count >= event_obj.capacity:
                await event.respond("ظرفیت این رویداد تکمیل شده است.")
                return
            
            # Show event information and start registration
            await self.show_event_info(event, client, event_obj)
            
        except Exception as e:
            await event.respond(f"خطا در بارگیری رویداد: {str(e)}")
        finally:
            db_session.close()
    
    async def show_event_info(self, event, client, event_obj):
        """Show event information to user"""
        response = (
            f"📋 {event_obj.name}\n\n"
            f"📝 توضیحات:\n{event_obj.description}\n\n"
            f"💰 هزینه ثبت نام: {format_currency(event_obj.amount)}\n"
            f"💳 شماره کارت: {event_obj.card_number}\n"
            f"👥 ظرفیت: {event_obj.registered_count}/{event_obj.capacity}\n"
        )
        
        if event_obj.start_date:
            response += f"📅 تاریخ شروع: {event_obj.start_date.strftime('%Y-%m-%d %H:%M')}\n"
        
        if event_obj.end_date:
            response += f"📅 تاریخ پایان: {event_obj.end_date.strftime('%Y-%m-%d %H:%M')}\n"
        
        response += (
            "\n⚠️ توجه: پس از واریز مبلغ، فیش واریزی را آپلود کرده و سپس اقدام به ثبت نام نمایید.\n\n"
            "برای شروع ثبت نام روی دکمه زیر کلیک کنید:"
        )
        
        buttons = [
            [Button.text("شروع ثبت نام", resize=True)],
            [Button.text("بررسی وضعیت ثبت نام من", resize=True)]
        ]
        
        # Initialize registration session
        self.init_registration_session(event.sender_id, event_obj.event_id)
        
        await event.respond(response, buttons=buttons)
    
    async def handle_registration_step(self, event, client):
        """Handle registration steps"""
        user_id = event.sender_id
        session = self.get_session(user_id)
        
        if not session:
            return False
        
        if event.text == "لغو":
            self.clear_session(user_id)
            await event.respond("ثبت نام لغو شد.", buttons=Button.clear())
            return True
        
        if event.text == "شروع ثبت نام":
            session['step'] = 1
            await event.respond(
                "لطفا نام خود را وارد کنید:",
                buttons=[Button.text("لغو", resize=True)]
            )
            return True
        
        if event.text == "بررسی وضعیت ثبت نام من":
            await self.check_registration_status(event, client, user_id, session['event_id'])
            return True
        
        step = session['step']
        
        if step == 1:  # First name
            session['data']['first_name'] = event.text.strip()
            session['step'] = 2
            await event.respond("لطفا نام خانوادگی خود را وارد کنید:")
        
        elif step == 2:  # Last name
            session['data']['last_name'] = event.text.strip()
            session['step'] = 3
            await event.respond(
                "لطفا کد ملی خود را وارد کنید:\n"
                "(می‌توانید از اعداد فارسی نیز استفاده کنید)"
            )
        
        elif step == 3:  # National code
            national_code = normalize_national_code(event.text)
            
            if not validate_iranian_national_code(national_code):
                await event.respond(
                    "کد ملی وارد شده معتبر نیست. لطفا دوباره وارد کنید:\n"
                    "(10 رقم - می‌توانید از اعداد فارسی استفاده کنید)"
                )
                return True
            
            # Check for duplicate registration
            if check_duplicate_registration(create_db_session(), national_code, session['event_id']):
                await event.respond(
                    "شما قبلاً برای این رویداد ثبت نام کرده‌اید.\n"
                    "برای بررسی وضعیت از دکمه 'بررسی وضعیت ثبت نام من' استفاده کنید."
                )
                return True
            
            session['data']['national_code'] = national_code
            session['step'] = 4
            await event.respond(
                "لطفا شماره تلفن همراه خود را وارد کنید:\n"
                "(فرمت: 09xxxxxxxxx - می‌توانید از اعداد فارسی استفاده کنید)"
            )
        
        elif step == 4:  # Phone number
            phone = normalize_phone_number(event.text)
            
            if not validate_iranian_phone(phone):
                await event.respond(
                    "شماره تلفن وارد شده معتبر نیست.\n"
                    "لطفا شماره تلفن ایرانی را به فرمت 09xxxxxxxxx وارد کنید:\n"
                    "(می‌توانید از اعداد فارسی استفاده کنید)"
                )
                return True
            
            session['data']['phone_number'] = phone
            session['step'] = 5
            await event.respond(
                "🧾 لطفا فیش واریزی خود را ارسال کنید:\n\n"
                "• می‌توانید عکس فیش را ارسال کنید\n"
                "• یا متن فیش را تایپ کنید\n\n"
                "⚠️ توجه: فیش باید مطابق مبلغ اعلام شده و به شماره کارت مشخص شده باشد."
            )
        
        elif step == 5:  # Payment receipt
            receipt_text = None
            receipt_path = None
            
            # Check if it's a photo
            if hasattr(event, 'photo') and event.photo:
                # Save photo
                receipt_path = await self.save_payment_receipt(event, client, user_id)
            else:
                # It's text
                receipt_text = event.text
            
            session['data']['receipt_text'] = receipt_text
            session['data']['receipt_path'] = receipt_path
            
            # Show confirmation
            await self.show_registration_confirmation(event, client, session)
        
        return True
    
    async def save_payment_receipt(self, event, client, user_id):
        """Save payment receipt photo"""
        try:
            # Create receipts directory if it doesn't exist
            receipts_dir = "receipts"
            if not os.path.exists(receipts_dir):
                os.makedirs(receipts_dir)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"receipt_{user_id}_{timestamp}.jpg"
            filepath = os.path.join(receipts_dir, filename)
            
            # Download and save photo
            await event.download_media(file=filepath)
            
            return filepath
            
        except Exception as e:
            print(f"Error saving receipt: {e}")
            return None
    
    async def show_registration_confirmation(self, event, client, session):
        """Show registration confirmation to user"""
        data = session['data']
        
        response = (
            "✅ اطلاعات شما برای بررسی ارسال شد:\n\n"
            f"👤 نام: {data['first_name']} {data['last_name']}\n"
            f"🆔 کد ملی: {data['national_code']}\n"
            f"📱 شماره تلفن: {data['phone_number']}\n"
            f"🧾 فیش واریزی: {'ارسال شده' if data.get('receipt_path') or data.get('receipt_text') else 'ارسال نشده'}\n\n"
            "📋 اطلاعات شما برای تایید به ادمین ارسال شده است.\n"
            "پس از بررسی، نتیجه به شما اطلاع داده خواهد شد.\n\n"
            "💡 می‌توانید از دکمه 'بررسی وضعیت ثبت نام من' برای پیگیری استفاده کنید."
        )
        
        # Save registration to database
        await self.save_registration(session)
        
        # Send to admins for approval
        await self.send_to_admins_for_approval(client, session)
        
        # Clear session
        self.clear_session(event.sender_id)
        
        await event.respond(response, buttons=Button.clear())
    
    async def save_registration(self, session):
        """Save registration to database"""
        db_session = create_db_session()
        
        try:
            data = session['data']
            
            # Create or get user
            user = db_session.query(User).filter_by(national_code=data['national_code']).first()
            
            if not user:
                user = User(
                    telegram_id=session.get('user_id', 0),  # We'll update this later
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    national_code=data['national_code'],
                    phone_number=data['phone_number']
                )
                db_session.add(user)
                db_session.flush()  # Get user_id
            
            # Create registration
            registration = Registration(
                user_id=user.user_id,
                event_id=session['event_id'],
                status=RegistrationStatus.PENDING,
                payment_receipt_path=data.get('receipt_path'),
                payment_receipt_text=data.get('receipt_text')
            )
            
            db_session.add(registration)
            db_session.commit()
            
            # Log activity
            log_activity(db_session, user.user_id, "registration_submitted", 
                        f"Event ID: {session['event_id']}")
            
        except Exception as e:
            db_session.rollback()
            print(f"Error saving registration: {e}")
        finally:
            db_session.close()
    
    async def send_to_admins_for_approval(self, client, session):
        """Send registration to admins for approval"""
        db_session = create_db_session()
        
        try:
            # Get admins
            admins = db_session.query(Admin).all()
            
            if not admins:
                return
            
            # Get event info
            event_obj = db_session.query(Event).filter_by(event_id=session['event_id']).first()
            if not event_obj:
                return
            
            data = session['data']
            
            message = (
                f"🔔 ثبت نام جدید برای تایید\n\n"
                f"📋 رویداد: {event_obj.name}\n"
                f"👤 نام: {data['first_name']} {data['last_name']}\n"
                f"🆔 کد ملی: {data['national_code']}\n"
                f"📱 تلفن: {data['phone_number']}\n"
                f"📅 تاریخ ثبت نام: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            )
            
            # Send to all admins
            for admin in admins:
                try:
                    buttons = [
                        [Button.inline("✅ تایید", data=f"approve_reg_{session['event_id']}_{data['national_code']}")],
                        [Button.inline("❌ رد", data=f"reject_reg_{session['event_id']}_{data['national_code']}")]
                    ]
                    
                    await client.send_message(admin.telegram_id, message, buttons=buttons)
                    
                    # Send receipt if available
                    if data.get('receipt_path'):
                        await client.send_file(admin.telegram_id, data['receipt_path'], 
                                             caption="فیش واریزی:")
                    elif data.get('receipt_text'):
                        await client.send_message(admin.telegram_id, 
                                                f"متن فیش:\n{data['receipt_text']}")
                    
                except Exception as e:
                    print(f"Error sending to admin {admin.telegram_id}: {e}")
            
        except Exception as e:
            print(f"Error sending to admins: {e}")
        finally:
            db_session.close()
    
    async def check_registration_status(self, event, client, user_telegram_id, event_id):
        """Check user's registration status"""
        db_session = create_db_session()
        
        try:
            # Find user's registration
            registration = db_session.query(Registration).join(User).filter(
                User.telegram_id == user_telegram_id,
                Registration.event_id == event_id
            ).first()
            
            if not registration:
                await event.respond("شما هنوز برای این رویداد ثبت نام نکرده‌اید.")
                return
            
            status_text = {
                RegistrationStatus.PENDING: "⏳ در حال بررسی",
                RegistrationStatus.APPROVED: "✅ تایید شده",
                RegistrationStatus.REJECTED: "❌ رد شده"
            }.get(registration.status, "نامشخص")
            
            event_obj = registration.event
            
            response = (
                f"📋 وضعیت ثبت نام شما:\n\n"
                f"🎯 رویداد: {event_obj.name}\n"
                f"📊 وضعیت: {status_text}\n"
                f"📅 تاریخ ثبت نام: {registration.registration_date.strftime('%Y-%m-%d %H:%M')}\n"
            )
            
            if registration.approval_date:
                response += f"📅 تاریخ تایید/رد: {registration.approval_date.strftime('%Y-%m-%d %H:%M')}\n"
            
            await event.respond(response)
            
        except Exception as e:
            await event.respond(f"خطا در بررسی وضعیت: {str(e)}")
        finally:
            db_session.close()