from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    
    sms_consent = Column(Boolean, default=True, nullable=False)
    sms_opt_out = Column(Boolean, default=False, nullable=False)
    
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

class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), default="user", nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# MESSAGING MODELS - tables for SMS/Email functionality

class MessageGroupDB(Base):
    """
    Message groups for organizing recipients (e.g., 'All Youth', 'Leaders', 'Grade 10').
    Supports dynamic and manual group creation.
    """
    __tablename__ = "message_groups"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("UserDB", backref="created_message_groups")
    memberships = relationship("MessageGroupMembershipDB", back_populates="group", cascade="all, delete-orphan")
    messages = relationship("MessageDB", back_populates="group")


class MessageGroupMembershipDB(Base):
    """
    Junction table linking persons to message groups.
    Supports both manual and automatic group membership.
    """
    __tablename__ = "message_group_membership"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    group_id = Column(BigInteger, ForeignKey("message_groups.id"), nullable=False)
    person_id = Column(BigInteger, ForeignKey("persons.id"), nullable=False)
    added_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=func.now())
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (
        UniqueConstraint('group_id', 'person_id', name='uq_group_person_membership'),
    )
    
    # Relationships
    group = relationship("MessageGroupDB", back_populates="memberships")
    person = relationship("PersonDB", backref="group_memberships")
    added_by_user = relationship("UserDB", backref="added_memberships")


class MessageDB(Base):
    """
    Messages sent to groups via SMS or Email.
    Designed to support both channels with extensible schema.
    """
    __tablename__ = "messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    channel = Column(String(20), nullable=False, index=True)  # 'sms' or 'email'
    content = Column(Text, nullable=False)
    subject = Column(String(200), nullable=True)  # For email messages
    group_id = Column(BigInteger, ForeignKey("message_groups.id"), nullable=True)  # Nullable for individual messages
    sent_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="queued", nullable=False, index=True)  # queued, sending, sent, delivered, failed
    
    # Individual message recipient (for non-group messages)
    recipient_phone = Column(String(20), nullable=True, index=True)  # For individual SMS messages
    
    # External service tracking
    twilio_sid = Column(String(100), nullable=True, index=True)  # Twilio message SID
    external_id = Column(String(100), nullable=True, index=True)  # Other service IDs
    
    # Delivery tracking
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    group = relationship("MessageGroupDB", back_populates="messages")
    sender = relationship("UserDB", backref="sent_messages")


class MessageTemplateDB(Base):
    """
    Reusable message templates for common scenarios.
    Supports variable substitution (e.g., {event_name}, {start_time}).
    """
    __tablename__ = "message_templates"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=True, index=True)  # 'event', 'reminder', 'announcement', etc.
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Unique constraint: template names must be unique per user
    __table_args__ = (
        UniqueConstraint('name', 'created_by', name='uq_template_name_per_user'),
    )
    
    # Relationships
    creator = relationship("UserDB", backref="message_templates")