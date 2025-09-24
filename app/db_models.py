from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime, date
from typing import Optional

class PersonDB(Base):
    __tablename__ = "persons"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True)
    archived_on = Column(DateTime, nullable=True)
    person_type = Column(String(20), nullable=False)  # "youth" or "leader"
    
    # Youth-specific fields
    grade = Column(Integer, nullable=True)
    school_name = Column(String(200), nullable=True)
    birth_date = Column(Date, nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    
    # Leader-specific fields
    role = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EventDB(Base):
    __tablename__ = "events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    date = Column(String(10), nullable=False)  # ISO date string
    name = Column(String(200), nullable=False, default="Youth Group")
    desc = Column(Text, default="")
    start_time = Column(String(5), default="19:00")  # HH:MM format
    end_time = Column(String(5), default="21:00")    # HH:MM format
    location = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EventPersonDB(Base):
    __tablename__ = "event_persons"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    event_id = Column(BigInteger, nullable=False)
    person_id = Column(BigInteger, nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=True)
    person_type = Column(String(20), nullable=False)  # "youth" or "leader"
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())