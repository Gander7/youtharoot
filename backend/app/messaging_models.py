"""
Pydantic models for messaging functionality.

These models handle validation and serialization for the messaging API endpoints.
They correspond to the SQLAlchemy models in db_models.py and provide:
- Request/response validation
- API documentation
- Type safety
- Data serialization/deserialization

Following TDD approach - these models support the test requirements.
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum


# Enums for type safety
class MessageChannel(str, Enum):
    """Supported message channels."""
    SMS = "sms"
    EMAIL = "email"


class MessageStatus(str, Enum):
    """Message delivery status."""
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class MessageCategory(str, Enum):
    """Message template categories."""
    EVENT = "event"
    REMINDER = "reminder"
    ANNOUNCEMENT = "announcement"
    EMERGENCY = "emergency"
    OTHER = "other"


# Base models for common fields
class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at fields."""
    created_at: datetime
    updated_at: datetime


# Message Group Models
class MessageGroupBase(BaseModel):
    """Base model for message group."""
    name: str = Field(..., min_length=1, max_length=100, description="Group name (must be unique)")
    description: Optional[str] = Field(None, max_length=1000, description="Group description")
    is_active: bool = Field(True, description="Whether the group is active")


class MessageGroupCreate(MessageGroupBase):
    """Model for creating a new message group."""
    pass


class MessageGroupUpdate(BaseModel):
    """Model for updating a message group."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class MessageGroup(MessageGroupBase, TimestampMixin):
    """Complete message group model."""
    id: int
    created_by: int

    model_config = ConfigDict(from_attributes=True)


# Message Group Membership Models
class MessageGroupMembershipBase(BaseModel):
    """Base model for group membership."""
    group_id: int
    person_id: int


class MessageGroupMembershipCreate(BaseModel):
    """Model for adding a person to a group via API."""
    person_id: int


class MessageGroupMembership(MessageGroupMembershipBase):
    """Complete group membership model."""
    id: int
    added_by: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Message Models
class MessageBase(BaseModel):
    """Base model for messages."""
    channel: MessageChannel = Field(..., description="Message channel (sms or email)")
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    subject: Optional[str] = Field(None, max_length=200, description="Email subject (required for email)")
    group_id: int = Field(..., description="Target message group ID")

    @model_validator(mode='after')
    def validate_subject_for_email(self):
        """Ensure email messages have a subject."""
        if self.channel == MessageChannel.EMAIL and not self.subject:
            raise ValueError('Subject is required for email messages')
        if self.channel == MessageChannel.SMS and self.subject:
            raise ValueError('Subject should not be provided for SMS messages')
        return self


class MessageCreate(MessageBase):
    """Model for creating a new message."""
    pass


class MessageUpdate(BaseModel):
    """Model for updating message status (typically from webhooks)."""
    status: MessageStatus
    twilio_sid: Optional[str] = None
    external_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = Field(None, max_length=1000)


class Message(MessageBase, TimestampMixin):
    """Complete message model."""
    id: int
    sent_by: int
    status: MessageStatus
    twilio_sid: Optional[str] = None
    external_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Message Template Models
class MessageTemplateBase(BaseModel):
    """Base model for message templates."""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    content: str = Field(..., min_length=1, max_length=10000, description="Template content with variables")
    category: Optional[MessageCategory] = Field(None, description="Template category")
    is_active: bool = Field(True, description="Whether the template is active")


class MessageTemplateCreate(MessageTemplateBase):
    """Model for creating a new message template."""
    pass


class MessageTemplateUpdate(BaseModel):
    """Model for updating a message template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    category: Optional[MessageCategory] = None
    is_active: Optional[bool] = None


class MessageTemplate(MessageTemplateBase, TimestampMixin):
    """Complete message template model."""
    id: int
    created_by: int

    model_config = ConfigDict(from_attributes=True)


# Extended Person Model for SMS fields
class PersonSMSUpdate(BaseModel):
    """Model for updating SMS-related person fields."""
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number in international format")
    sms_consent: Optional[bool] = Field(None, description="Whether person consents to SMS messages")
    sms_opt_out: Optional[bool] = Field(None, description="Whether person has opted out of SMS")

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        """Basic phone number validation."""
        if v is None:
            return v
        
        # Remove spaces and common formatting
        cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Basic validation - starts with + and contains only digits after
        if not cleaned.startswith('+') or not cleaned[1:].isdigit():
            raise ValueError('Phone number must be in international format (e.g., +1234567890)')
        
        if len(cleaned) < 8 or len(cleaned) > 15:
            raise ValueError('Phone number must be between 8 and 15 digits')
        
        return cleaned


# API Response Models
class MessageGroupWithMemberships(MessageGroup):
    """Message group with member details."""
    member_count: int
    members: Optional[List[dict]] = None  # Will contain person details


class MessageSendResponse(BaseModel):
    """Response model for sending messages."""
    message_id: int
    status: MessageStatus
    recipients_count: int
    estimated_cost: Optional[float] = None
    twilio_sid: Optional[str] = None


class MessageStatusUpdate(BaseModel):
    """Model for Twilio webhook status updates."""
    message_sid: str = Field(..., description="Twilio message SID")
    status: MessageStatus
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# Bulk Operations
class BulkGroupMembershipCreate(BaseModel):
    """Model for adding multiple people to a group via API."""
    person_ids: List[int] = Field(..., min_length=1, max_length=1000)


class BulkGroupMembershipResponse(BaseModel):
    """Response for bulk group membership operations."""
    added_count: int
    skipped_count: int  # Already members
    failed_count: int
    failed_person_ids: List[int] = []


# Analytics Models
class MessageAnalytics(BaseModel):
    """Message delivery analytics."""
    total_sent: int
    total_delivered: int
    total_failed: int
    delivery_rate: float
    average_delivery_time: Optional[float] = None  # seconds
    cost_total: Optional[float] = None