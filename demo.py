"""
Demo script to show how the event registration system works
"""

from userDB import db_init, create_db_session, User, Event, Registration, Admin, EventStatus
from utils import validate_iranian_national_code, validate_iranian_phone, generate_unique_event_code
from datetime import datetime, timedelta

def create_demo_data():
    """Create demo data for testing"""
    db_init()
    db_session = create_db_session()
    
    try:
        print("🔧 Creating demo data...")
        
        # Create a super admin
        admin = Admin(
            telegram_id=123456789,
            is_super_admin=True
        )
        db_session.add(admin)
        
        # Create a demo event
        event = Event(
            name="کنفرانس فناوری 2024",
            description="کنفرانسی درباره آخرین فناوری‌های روز دنیا",
            amount=50000,
            card_number="6037-9911-1234-5678",
            capacity=100,
            registered_count=0,
            status=EventStatus.ACTIVE,
            start_date=datetime.now() + timedelta(days=30),
            end_date=datetime.now() + timedelta(days=30, hours=8),
            unique_code=generate_unique_event_code()
        )
        db_session.add(event)
        
        # Create demo users
        demo_users = [
            {
                'telegram_id': 111111111,
                'first_name': 'علی',
                'last_name': 'احمدی',
                'national_code': '0060495219',
                'phone_number': '09151234567'
            },
            {
                'telegram_id': 222222222,
                'first_name': 'مریم',
                'last_name': 'محمدی',
                'national_code': '0012345673',
                'phone_number': '09357654321'
            }
        ]
        
        for user_data in demo_users:
            user = User(**user_data)
            db_session.add(user)
        
        db_session.commit()
        
        print("✅ Demo data created successfully!")
        print(f"📋 Event: {event.name}")
        print(f"🔗 Event code: {event.unique_code}")
        print(f"👤 Admin ID: {admin.telegram_id}")
        print(f"👥 Users created: {len(demo_users)}")
        
    except Exception as e:
        db_session.rollback()
        print(f"❌ Error creating demo data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_session.close()

def show_validation_examples():
    """Show validation examples"""
    print("\n🧪 Testing validation functions:")
    print("-" * 40)
    
    # National code tests
    print("📋 National Code Validation:")
    test_codes = ['0060495219', '1234567890', '۰۰۶۰۴۹۵۲۱۹', '0000000000']
    for code in test_codes:
        result = validate_iranian_national_code(code)
        print(f"  {code}: {'✅' if result else '❌'}")
    
    # Phone number tests
    print("\n📱 Phone Number Validation:")
    test_phones = ['09151234567', '۰۹۳۵۷۶۵۴۳۲۱', '+989151234567', '0915123456']
    for phone in test_phones:
        result = validate_iranian_phone(phone)
        print(f"  {phone}: {'✅' if result else '❌'}")

def show_database_structure():
    """Show database structure"""
    print("\n🗄️ Database Structure:")
    print("-" * 40)
    
    db_session = create_db_session()
    
    try:
        # Count records
        admin_count = db_session.query(Admin).count()
        event_count = db_session.query(Event).count()
        user_count = db_session.query(User).count()
        registration_count = db_session.query(Registration).count()
        
        print(f"👤 Admins: {admin_count}")
        print(f"📋 Events: {event_count}")
        print(f"👥 Users: {user_count}")
        print(f"📝 Registrations: {registration_count}")
        
        # Show events
        if event_count > 0:
            print("\n📋 Events:")
            events = db_session.query(Event).all()
            for event in events:
                print(f"  - {event.name} ({event.status.value})")
                print(f"    Capacity: {event.registered_count}/{event.capacity}")
                print(f"    Code: {event.unique_code}")
        
        # Show admins
        if admin_count > 0:
            print("\n👤 Admins:")
            admins = db_session.query(Admin).all()
            for admin in admins:
                admin_type = "Super Admin" if admin.is_super_admin else "Admin"
                print(f"  - {admin.telegram_id} ({admin_type})")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    finally:
        db_session.close()

if __name__ == "__main__":
    print("🎯 Event Registration System Demo")
    print("=" * 50)
    
    # Show validation examples
    show_validation_examples()
    
    # Create demo data
    create_demo_data()
    
    # Show database structure
    show_database_structure()
    
    print("\n🚀 System is ready!")
    print("Next steps:")
    print("1. Add your Telegram ID as super admin using admin_manager.py")
    print("2. Update config.py with your bot credentials")
    print("3. Run main.py to start the bot")
    print("4. Use /create_event to create your first event")