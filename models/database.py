from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime
import secrets
import string

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    national_code = Column(String(10), unique=True, nullable=False)
    phone_number = Column(String(15), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    registrations = relationship("Registration", back_populates="user")

class Event(Base):
    __tablename__ = 'events'
    
    event_id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    poster_path = Column(String(500))
    amount = Column(Integer, nullable=False)  # Payment amount
    card_number = Column(String(20), nullable=False)
    capacity = Column(Integer, nullable=False)
    registered_count = Column(Integer, default=0)
    status = Column(String(20), default='active')  # active/inactive/full/expired
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    unique_code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    registrations = relationship("Registration", back_populates="event")
    
    @staticmethod
    def generate_unique_code():
        """Generate a unique event code"""
        return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))

class Registration(Base):
    __tablename__ = 'registrations'
    
    registration_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.event_id'), nullable=False)
    status = Column(String(20), default='pending')  # pending/approved/rejected
    payment_receipt_path = Column(String(500))
    payment_receipt_text = Column(Text)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)
    approval_date = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")

class Admin(Base):
    __tablename__ = 'admins'
    
    admin_id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    is_super_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RejectedRegistration(Base):
    __tablename__ = 'rejected_registrations'
    
    rejected_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=False)
    telegram_id = Column(Integer, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    national_code = Column(String(10), nullable=False)
    phone_number = Column(String(15), nullable=False)
    payment_receipt_path = Column(String(500))
    payment_receipt_text = Column(Text)
    rejection_reason = Column(Text)
    rejected_date = Column(DateTime, default=datetime.datetime.utcnow)

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    
    log_id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class MessageLog(Base):
    __tablename__ = 'message_logs'
    
    message_id = Column(Integer, primary_key=True)
    telegram_user_id = Column(Integer, nullable=False)
    message_content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Database connection and session management
class DatabaseManager:
    def __init__(self, db_url='sqlite:///event_bot.db'):
        self.engine = create_engine(db_url)
        Base.metadata.bind = self.engine
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        session.close()

# Global database instance
db_manager = DatabaseManager()