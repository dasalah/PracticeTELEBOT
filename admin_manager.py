"""
Admin management script
Run this script to add initial super admin
"""

from userDB import db_init, create_db_session, Admin

def add_super_admin(telegram_id):
    """Add super admin to database"""
    db_init()
    db_session = create_db_session()
    
    try:
        # Check if admin already exists
        existing_admin = db_session.query(Admin).filter_by(telegram_id=telegram_id).first()
        
        if existing_admin:
            existing_admin.is_super_admin = True
            print(f"Updated existing admin {telegram_id} to super admin")
        else:
            # Create new super admin
            super_admin = Admin(
                telegram_id=telegram_id,
                is_super_admin=True
            )
            db_session.add(super_admin)
            print(f"Added new super admin: {telegram_id}")
        
        db_session.commit()
        print("✅ Super admin added successfully!")
        
    except Exception as e:
        db_session.rollback()
        print(f"❌ Error adding super admin: {e}")
    finally:
        db_session.close()

def list_admins():
    """List all admins"""
    db_init()
    db_session = create_db_session()
    
    try:
        admins = db_session.query(Admin).all()
        
        if not admins:
            print("No admins found.")
            return
        
        print("\n📋 List of admins:")
        print("-" * 50)
        for admin in admins:
            admin_type = "Super Admin" if admin.is_super_admin else "Admin"
            print(f"ID: {admin.telegram_id} | Type: {admin_type} | Created: {admin.created_at.strftime('%Y-%m-%d %H:%M')}")
        
    except Exception as e:
        print(f"❌ Error listing admins: {e}")
    finally:
        db_session.close()

def remove_admin(telegram_id):
    """Remove admin from database"""
    db_init()
    db_session = create_db_session()
    
    try:
        admin = db_session.query(Admin).filter_by(telegram_id=telegram_id).first()
        
        if admin:
            db_session.delete(admin)
            db_session.commit()
            print(f"✅ Removed admin: {telegram_id}")
        else:
            print(f"❌ Admin {telegram_id} not found")
        
    except Exception as e:
        db_session.rollback()
        print(f"❌ Error removing admin: {e}")
    finally:
        db_session.close()

if __name__ == "__main__":
    print("🔧 Admin Management Tool")
    print("1. Add Super Admin")
    print("2. List Admins")
    print("3. Remove Admin")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        telegram_id = input("Enter Telegram ID for super admin: ").strip()
        try:
            telegram_id = int(telegram_id)
            add_super_admin(telegram_id)
        except ValueError:
            print("❌ Invalid Telegram ID. Please enter a number.")
    
    elif choice == "2":
        list_admins()
    
    elif choice == "3":
        telegram_id = input("Enter Telegram ID to remove: ").strip()
        try:
            telegram_id = int(telegram_id)
            remove_admin(telegram_id)
        except ValueError:
            print("❌ Invalid Telegram ID. Please enter a number.")
    
    else:
        print("❌ Invalid choice")