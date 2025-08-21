#!/usr/bin/env python3
"""
Demo script to create a sample event for testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import db_manager, Event, Admin
from datetime import datetime, timedelta

def create_sample_data():
    """Create sample event and admin for testing"""
    session = db_manager.get_session()
    
    try:
        # Create sample event
        existing_event = session.query(Event).filter(Event.unique_code == 'sample2024').first()
        
        if not existing_event:
            sample_event = Event(
                name='وبینار برنامه‌نویسی پایتون',
                description='''🐍 وبینار جامع برنامه‌نویسی پایتون
                
📚 محتوای دوره:
• مقدمات پایتون
• برنامه‌نویسی شی‌گرا
• کار با دیتابیس
• ساخت وب اپلیکیشن

👨‍💻 مدرس: استاد محمدی
🕐 مدت: ۳ ساعت
📅 تاریخ: ۱۴۰۳/۰۶/۱۵''',
                amount=150000,
                card_number='6037991234567890',
                capacity=50,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                unique_code='sample2024'
            )
            
            session.add(sample_event)
            session.commit()
            
            print(f"✅ Sample event created!")
            print(f"🎭 Event: {sample_event.name}")
            print(f"💰 Amount: {sample_event.amount:,} تومان")
            print(f"🔗 Registration link: t.me/your_bot_username?start=sample2024")
            
        else:
            print("✅ Sample event already exists")
            print(f"🔗 Registration link: t.me/your_bot_username?start=sample2024")
        
        # Create super admin if not exists
        admin_id = 6033723482  # From config
        existing_admin = session.query(Admin).filter(Admin.telegram_id == admin_id).first()
        
        if not existing_admin:
            admin = Admin(telegram_id=admin_id, is_super_admin=True)
            session.add(admin)
            session.commit()
            print(f"✅ Super admin created: {admin_id}")
        else:
            print(f"✅ Super admin already exists: {admin_id}")
            
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        db_manager.close_session(session)

if __name__ == '__main__':
    print("📊 Creating sample data...")
    db_manager.create_tables()
    create_sample_data()
    print("✅ Done!")