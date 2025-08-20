from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime
import enum

Base = declarative_base()

class EventStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    COMPLETED = "completed"
    EXPIRED = "expired"

class RegistrationStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    national_code = Column(String(10), nullable=False)
    phone_number = Column(String(15), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to registrations
    registrations = relationship("Registration", back_populates="user")

class Event(Base):
    __tablename__ = 'events'
    
    event_id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    poster_path = Column(String(500))
    amount = Column(Integer, nullable=False, default=0)
    card_number = Column(String(20))
    capacity = Column(Integer, nullable=False, default=100)
    registered_count = Column(Integer, default=0)
    status = Column(Enum(EventStatus), default=EventStatus.ACTIVE)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    unique_code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to registrations
    registrations = relationship("Registration", back_populates="event")

class Registration(Base):
    __tablename__ = 'registrations'
    
    registration_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.event_id'), nullable=False)
    status = Column(Enum(RegistrationStatus), default=RegistrationStatus.PENDING)
    payment_receipt_path = Column(String(500))
    payment_receipt_text = Column(Text)  # For text receipts when no photo
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
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    event_id = Column(Integer, ForeignKey('events.event_id'), nullable=False)
    payment_receipt_path = Column(String(500))
    payment_receipt_text = Column(Text)
    rejection_reason = Column(Text)
    registration_date = Column(DateTime)
    rejection_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    event = relationship("Event", foreign_keys=[event_id])

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    
    log_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    action = Column(String(100), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship
    user = relationship("User", foreign_keys=[user_id])

class MessageLog(Base):
    __tablename__ = 'message_logs'
    
    message_id = Column(Integer, primary_key=True)
    telegram_user_id = Column(Integer, nullable=False)
    message_content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def create_db_session():
    """Create database session"""
    engine = create_engine('sqlite:///bot.db')
    Session = sessionmaker(bind=engine)
    return Session()

def db_init():
    """Initialize database tables"""
    engine = create_engine('sqlite:///bot.db')
    Base.metadata.create_all(engine)
