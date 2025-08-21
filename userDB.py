from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

event_participants = Table(

    'event_participants',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('event_id', Integer, ForeignKey('events.id'))
)




class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    student_code = Column(Integer, nullable=False)
    phone_number = Column(Integer, nullable=False)
    email = Column(String(50), nullable=True)
    joined_date = Column(DateTime, default=datetime.datetime.utcnow)

    registered_event = relationship('Event', secondary=event_participants, back_populates="participants")


class Event(Base):

    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    eventType = Column(String , nullable=False)
    shortDescription = Column(String)
    description = Column(Text)
    start_Date = Column(DateTime)
    last_Date = Column(DateTime)
    location = Column(String)
    instructor = Column(String,nullable=True)
    max_participants = Column(Integer, nullable=True)
    registration_link = Column(String,nullable=True)
    event_poster = Column(String,nullable=True)


    participants = relationship("User", secondary=event_participants, back_populates="registered_event")


class Settings(Base):
    """Settings table for storing bot configuration"""
    
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)



def db_init():
    engine = create_engine('sqlite:///bot.db')
    Base.metadata.create_all(engine)
