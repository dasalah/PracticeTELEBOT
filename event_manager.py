"""
Event management system for admins
"""

from telethon import Button
from datetime import datetime
import os
from userDB import Event, EventStatus, Registration, RegistrationStatus, create_db_session
from utils import generate_unique_event_code, create_event_link, format_currency

class EventManager:
    def __init__(self, bot_username="eventregistrationbot"):
        self.bot_username = bot_username
        self.sessions = {}  # Store user sessions for multi-step operations
    
    def init_session(self, user_id, operation):
        """Initialize user session for multi-step operations"""
        self.sessions[user_id] = {
            'operation': operation,
            'step': 0,
            'data': {}
        }
    
    def get_session(self, user_id):
        """Get user session"""
        return self.sessions.get(user_id)
    
    def clear_session(self, user_id):
        """Clear user session"""
        if user_id in self.sessions:
            del self.sessions[user_id]
    
    async def handle_create_event_command(self, event, client):
        """Handle /create_event command"""
        user_id = event.sender_id
        self.init_session(user_id, 'create_event')
        
        await event.respond(
            "📝 ایجاد رویداد جدید\n\n"
            "لطفا نام رویداد را وارد کنید:",
            buttons=[Button.text("لغو", resize=True)]
        )
    
    async def handle_create_event_step(self, event, client):
        """Handle create event steps"""
        user_id = event.sender_id
        session = self.get_session(user_id)
        
        if not session or session['operation'] != 'create_event':
            return False
        
        if event.text == "لغو":
            self.clear_session(user_id)
            await event.respond("عملیات لغو شد.", buttons=Button.clear())
            return True
        
        step = session['step']
        
        if step == 0:  # Event name
            session['data']['name'] = event.text
            session['step'] = 1
            await event.respond("✏️ توضیحات رویداد را وارد کنید:")
        
        elif step == 1:  # Description
            session['data']['description'] = event.text
            session['step'] = 2
            await event.respond("💰 مبلغ ثبت نام را وارد کنید (به تومان):")
        
        elif step == 2:  # Amount
            try:
                amount = int(event.text.replace(',', '').replace('٬', ''))
                session['data']['amount'] = amount
                session['step'] = 3
                await event.respond("💳 شماره کارت برای واریز را وارد کنید:")
            except ValueError:
                await event.respond("لطفا مبلغ را به درستی وارد کنید (فقط عدد):")
        
        elif step == 3:  # Card number
            session['data']['card_number'] = event.text
            session['step'] = 4
            await event.respond("👥 ظرفیت رویداد را وارد کنید:")
        
        elif step == 4:  # Capacity
            try:
                capacity = int(event.text)
                session['data']['capacity'] = capacity
                session['step'] = 5
                await event.respond(
                    "📅 تاریخ شروع رویداد را وارد کنید (فرمت: YYYY-MM-DD HH:MM):\n"
                    "مثال: 2024-12-25 10:00"
                )
            except ValueError:
                await event.respond("لطفا ظرفیت را به درستی وارد کنید (فقط عدد):")
        
        elif step == 5:  # Start date
            try:
                start_date = datetime.strptime(event.text, "%Y-%m-%d %H:%M")
                session['data']['start_date'] = start_date
                session['step'] = 6
                await event.respond(
                    "📅 تاریخ پایان رویداد را وارد کنید (فرمت: YYYY-MM-DD HH:MM):\n"
                    "مثال: 2024-12-25 18:00"
                )
            except ValueError:
                await event.respond(
                    "فرمت تاریخ اشتباه است. لطفا به فرمت زیر وارد کنید:\n"
                    "YYYY-MM-DD HH:MM\n"
                    "مثال: 2024-12-25 10:00"
                )
        
        elif step == 6:  # End date
            try:
                end_date = datetime.strptime(event.text, "%Y-%m-%d %H:%M")
                session['data']['end_date'] = end_date
                
                # Create event
                await self.create_event(event, session['data'])
                self.clear_session(user_id)
                
            except ValueError:
                await event.respond(
                    "فرمت تاریخ اشتباه است. لطفا به فرمت زیر وارد کنید:\n"
                    "YYYY-MM-DD HH:MM\n"
                    "مثال: 2024-12-25 18:00"
                )
        
        return True
    
    async def create_event(self, event, data):
        """Create new event in database"""
        db_session = create_db_session()
        
        try:
            unique_code = generate_unique_event_code()
            event_link = create_event_link(self.bot_username, unique_code)
            
            new_event = Event(
                name=data['name'],
                description=data['description'],
                amount=data['amount'],
                card_number=data['card_number'],
                capacity=data['capacity'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                unique_code=unique_code,
                status=EventStatus.ACTIVE
            )
            
            db_session.add(new_event)
            db_session.commit()
            
            # Format response
            response = (
                "✅ رویداد با موفقیت ایجاد شد!\n\n"
                f"📋 نام: {data['name']}\n"
                f"📝 توضیحات: {data['description']}\n"
                f"💰 مبلغ: {format_currency(data['amount'])}\n"
                f"💳 شماره کارت: {data['card_number']}\n"
                f"👥 ظرفیت: {data['capacity']} نفر\n"
                f"📅 شروع: {data['start_date'].strftime('%Y-%m-%d %H:%M')}\n"
                f"📅 پایان: {data['end_date'].strftime('%Y-%m-%d %H:%M')}\n\n"
                f"🔗 لینک ثبت نام:\n{event_link}"
            )
            
            await event.respond(response, buttons=Button.clear())
            
        except Exception as e:
            await event.respond(f"خطا در ایجاد رویداد: {str(e)}")
        finally:
            db_session.close()
    
    async def handle_list_events(self, event, client):
        """Handle /list_events command"""
        db_session = create_db_session()
        
        try:
            events = db_session.query(Event).order_by(Event.created_at.desc()).all()
            
            if not events:
                await event.respond("هیچ رویدادی یافت نشد.")
                return
            
            buttons = []
            response = "📋 لیست رویدادها:\n\n"
            
            for i, evt in enumerate(events, 1):
                status_emoji = {
                    EventStatus.ACTIVE: "🟢",
                    EventStatus.INACTIVE: "🔴", 
                    EventStatus.COMPLETED: "✅",
                    EventStatus.EXPIRED: "⏰"
                }.get(evt.status, "❓")
                
                response += (
                    f"{i}. {status_emoji} {evt.name}\n"
                    f"   👥 {evt.registered_count}/{evt.capacity}\n"
                    f"   📅 {evt.start_date.strftime('%Y-%m-%d') if evt.start_date else 'تاریخ نامشخص'}\n\n"
                )
                
                buttons.append([Button.inline(f"مشاهده {evt.name}", data=f"view_event_{evt.event_id}")])
            
            await event.respond(response, buttons=buttons)
            
        except Exception as e:
            await event.respond(f"خطا در دریافت رویدادها: {str(e)}")
        finally:
            db_session.close()
    
    async def handle_event_view(self, event, event_id):
        """Handle event view inline button"""
        db_session = create_db_session()
        
        try:
            evt = db_session.query(Event).filter_by(event_id=event_id).first()
            
            if not evt:
                await event.edit("رویداد یافت نشد.")
                return
            
            status_text = {
                EventStatus.ACTIVE: "فعال",
                EventStatus.INACTIVE: "غیرفعال",
                EventStatus.COMPLETED: "تمام شده", 
                EventStatus.EXPIRED: "منقضی شده"
            }.get(evt.status, "نامشخص")
            
            event_link = create_event_link(self.bot_username, evt.unique_code)
            
            response = (
                f"📋 {evt.name}\n\n"
                f"📝 توضیحات: {evt.description}\n"
                f"💰 مبلغ: {format_currency(evt.amount)}\n"
                f"💳 شماره کارت: {evt.card_number}\n"
                f"👥 ظرفیت: {evt.registered_count}/{evt.capacity}\n"
                f"📊 وضعیت: {status_text}\n"
                f"📅 شروع: {evt.start_date.strftime('%Y-%m-%d %H:%M') if evt.start_date else 'نامشخص'}\n"
                f"📅 پایان: {evt.end_date.strftime('%Y-%m-%d %H:%M') if evt.end_date else 'نامشخص'}\n\n"
                f"🔗 لینک ثبت نام:\n{event_link}"
            )
            
            buttons = [
                [Button.inline("📊 مشاهده ثبت نامها", data=f"registrations_{event_id}")],
                [Button.inline("📄 دریافت Excel", data=f"export_excel_{event_id}")],
                [Button.inline("✏️ ویرایش", data=f"edit_event_{event_id}")],
                [Button.inline("🔄 تغییر وضعیت", data=f"toggle_status_{event_id}")],
                [Button.inline("🔙 بازگشت", data="back_to_events")]
            ]
            
            await event.edit(response, buttons=buttons)
            
        except Exception as e:
            await event.edit(f"خطا: {str(e)}")
        finally:
            db_session.close()
    
    async def handle_registrations_view(self, event, event_id):
        """Handle registrations view for an event"""
        db_session = create_db_session()
        
        try:
            registrations = db_session.query(Registration).join(Event).filter(
                Registration.event_id == event_id
            ).order_by(Registration.registration_date.desc()).all()
            
            if not registrations:
                await event.edit("هیچ ثبت نامی برای این رویداد وجود ندارد.")
                return
            
            response = f"👥 ثبت نام‌های رویداد:\n\n"
            
            for reg in registrations[:10]:  # Show max 10
                status_emoji = {
                    RegistrationStatus.PENDING: "⏳",
                    RegistrationStatus.APPROVED: "✅",
                    RegistrationStatus.REJECTED: "❌"
                }.get(reg.status, "❓")
                
                user = reg.user
                response += (
                    f"{status_emoji} {user.first_name} {user.last_name}\n"
                    f"   📱 {user.phone_number}\n"
                    f"   📅 {reg.registration_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                )
            
            if len(registrations) > 10:
                response += f"... و {len(registrations) - 10} ثبت نام دیگر"
            
            buttons = [
                [Button.inline("📄 دریافت Excel کامل", data=f"export_excel_{event_id}")],
                [Button.inline("🔙 بازگشت", data=f"view_event_{event_id}")]
            ]
            
            await event.edit(response, buttons=buttons)
            
        except Exception as e:
            await event.edit(f"خطا: {str(e)}")
        finally:
            db_session.close()