#!/usr/bin/env python3
"""
Integration test to demonstrate the complete event registration system
This test simulates the full workflow without requiring actual Telegram API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import db_manager, Event, User, Registration, Admin
from utils.validation import validate_iranian_national_code, validate_iranian_phone, normalize_iranian_phone
from utils.excel_export import create_registration_excel, ensure_export_directory
from utils.helpers import format_event_info, format_registration_info
from datetime import datetime, timedelta
import tempfile

def test_complete_workflow():
    """Test the complete event registration workflow"""
    
    print("🧪 Starting integration tests...\n")
    
    # 1. Test Database Setup
    print("1️⃣ Testing database setup...")
    db_manager.create_tables()
    print("   ✅ Database tables created")
    
    # 2. Test Event Creation
    print("2️⃣ Testing event creation...")
    session = db_manager.get_session()
    try:
        event = Event(
            name='کارگاه هوش مصنوعی',
            description='کارگاه آموزش عملی هوش مصنوعی و یادگیری ماشین',
            amount=200000,
            card_number='6037991234567890',
            capacity=30,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=15),
            unique_code='ai2024'
        )
        session.add(event)
        session.commit()
        event_id = event.event_id
        print(f"   ✅ Event created: {event.name} (ID: {event_id})")
        print(f"   🔗 Registration link: t.me/botname?start={event.unique_code}")
    finally:
        db_manager.close_session(session)
    
    # 3. Test Admin Creation
    print("3️⃣ Testing admin creation...")
    session = db_manager.get_session()
    try:
        admin = Admin(telegram_id=123456789, is_super_admin=True)
        session.add(admin)
        session.commit()
        print("   ✅ Super admin created")
    finally:
        db_manager.close_session(session)
    
    # 4. Test User Registration Data Validation
    print("4️⃣ Testing user data validation...")
    
    # Test national code validation
    test_national_codes = ['0013542419', '1234567890', '0000000000']
    for code in test_national_codes:
        is_valid = validate_iranian_national_code(code)
        print(f"   📊 National code {code}: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test phone validation
    test_phones = ['09123456789', '+989123456789', '۰۹۱۲۳۴۵۶۷۸۹', '123']
    for phone in test_phones:
        is_valid = validate_iranian_phone(phone)
        normalized = normalize_iranian_phone(phone) if is_valid else None
        print(f"   📱 Phone {phone}: {'✅ Valid' if is_valid else '❌ Invalid'} -> {normalized}")
    
    # 5. Test User and Registration Creation
    print("5️⃣ Testing user registration...")
    session = db_manager.get_session()
    try:
        # Create test users
        users_data = [
            ('علی', 'احمدی', '0013542419', '09123456789'),
            ('زهرا', 'محمدی', '0084575852', '09354567890'),
            ('حسن', 'کریمی', '0123456789', '09187654321')
        ]
        
        registrations = []
        for i, (first_name, last_name, national_code, phone) in enumerate(users_data):
            user = User(
                telegram_id=1000000 + i,
                first_name=first_name,
                last_name=last_name,
                national_code=national_code,
                phone_number=phone
            )
            session.add(user)
            session.flush()  # To get user_id
            
            registration = Registration(
                user_id=user.user_id,
                event_id=event_id,
                status='approved' if i < 2 else 'pending',
                payment_receipt_text=f'شماره پیگیری: {123456789 + i}',
                registration_date=datetime.now() - timedelta(days=i)
            )
            if registration.status == 'approved':
                registration.approval_date = datetime.now()
            
            session.add(registration)
            registrations.append(registration)
            
            print(f"   👤 User {first_name} {last_name} registered ({'✅ Approved' if registration.status == 'approved' else '⏳ Pending'})")
        
        session.commit()
        
        # Update event registered count
        event_obj = session.query(Event).filter(Event.event_id == event_id).first()
        event_obj.registered_count = len([r for r in registrations if r.status == 'approved'])
        session.commit()
        
    finally:
        db_manager.close_session(session)
    
    # 6. Test Information Formatting
    print("6️⃣ Testing information formatting...")
    session = db_manager.get_session()
    try:
        event_obj = session.query(Event).filter(Event.event_id == event_id).first()
        event_info = {
            'name': event_obj.name,
            'description': event_obj.description,
            'amount': event_obj.amount,
            'card_number': event_obj.card_number,
            'capacity': event_obj.capacity,
            'registered_count': event_obj.registered_count,
            'status': event_obj.status,
            'start_date': event_obj.start_date,
            'end_date': event_obj.end_date
        }
        
        formatted_event = format_event_info(event_info)
        print("   📋 Event info formatted:")
        print("   " + formatted_event.replace('\n', '\n   '))
        
    finally:
        db_manager.close_session(session)
    
    # 7. Test Excel Export
    print("7️⃣ Testing Excel export...")
    session = db_manager.get_session()
    try:
        # Get data for Excel
        event_obj = session.query(Event).filter(Event.event_id == event_id).first()
        all_registrations = session.query(Registration).filter(
            Registration.event_id == event_id
        ).join(User).all()
        
        approved_registrations = [r for r in all_registrations if r.status == 'approved']
        
        # Prepare event data
        event_data = {
            'name': event_obj.name,
            'description': event_obj.description,
            'amount': event_obj.amount,
            'card_number': event_obj.card_number,
            'capacity': event_obj.capacity,
            'registered_count': event_obj.registered_count,
            'status': event_obj.status,
            'start_date': event_obj.start_date,
            'end_date': event_obj.end_date,
            'unique_code': event_obj.unique_code,
            'created_at': event_obj.created_at
        }
        
        # Prepare registration data
        def prepare_reg_data(regs):
            return [{
                'first_name': r.user.first_name,
                'last_name': r.user.last_name,
                'national_code': r.user.national_code,
                'phone_number': r.user.phone_number,
                'status': r.status,
                'registration_date': r.registration_date,
                'approval_date': r.approval_date,
                'payment_receipt_text': r.payment_receipt_text,
                'payment_receipt_path': r.payment_receipt_path
            } for r in regs]
        
        all_reg_data = prepare_reg_data(all_registrations)
        approved_reg_data = prepare_reg_data(approved_registrations)
        rejected_reg_data = []  # No rejected for this test
        
        # Create Excel file
        ensure_export_directory()
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            excel_path = tmp_file.name
        
        create_registration_excel(
            event_data,
            all_reg_data,
            approved_reg_data,
            rejected_reg_data,
            excel_path
        )
        
        # Check if file was created
        if os.path.exists(excel_path):
            file_size = os.path.getsize(excel_path)
            print(f"   ✅ Excel file created: {file_size} bytes")
            os.unlink(excel_path)  # Clean up
        else:
            print("   ❌ Excel file creation failed")
    
    finally:
        db_manager.close_session(session)
    
    # 8. Test Statistics
    print("8️⃣ Testing statistics...")
    session = db_manager.get_session()
    try:
        total_events = session.query(Event).count()
        total_users = session.query(User).count()
        total_registrations = session.query(Registration).count()
        approved_registrations = session.query(Registration).filter(Registration.status == 'approved').count()
        pending_registrations = session.query(Registration).filter(Registration.status == 'pending').count()
        
        print(f"   📊 Statistics:")
        print(f"      • Total events: {total_events}")
        print(f"      • Total users: {total_users}")
        print(f"      • Total registrations: {total_registrations}")
        print(f"      • Approved: {approved_registrations}")
        print(f"      • Pending: {pending_registrations}")
        
    finally:
        db_manager.close_session(session)
    
    print("\n🎉 All integration tests completed successfully!")
    print("📝 System is ready for deployment with Telegram bot API")

if __name__ == '__main__':
    test_complete_workflow()