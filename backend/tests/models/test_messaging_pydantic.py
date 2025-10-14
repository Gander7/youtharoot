"""
Tests for messaging Pydantic models.

Tests validation, serialization, and API contract compliance.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from app.messaging_models import (
    MessageGroupCreate, MessageGroupUpdate, MessageGroup,
    MessageCreate, MessageUpdate, Message, MessageChannel, MessageStatus,
    MessageTemplateCreate, MessageTemplate,
    PersonSMSUpdate, MessageSendResponse
)


class TestMessageGroupModels:
    """Test message group Pydantic models."""
    
    def test_message_group_create_valid(self):
        """Test creating a valid message group."""
        group_data = {
            "name": "All Youth",
            "description": "All youth group members",
            "is_active": True
        }
        group = MessageGroupCreate(**group_data)
        assert group.name == "All Youth"
        assert group.description == "All youth group members"
        assert group.is_active is True
    
    def test_message_group_create_minimal(self):
        """Test creating a message group with minimal data."""
        group = MessageGroupCreate(name="Leaders")
        assert group.name == "Leaders"
        assert group.description is None
        assert group.is_active is True  # Default value
    
    def test_message_group_name_required(self):
        """Test that group name is required."""
        with pytest.raises(ValidationError) as exc:
            MessageGroupCreate()
        assert "name" in str(exc.value)
    
    def test_message_group_name_length_validation(self):
        """Test name length validation."""
        # Too short
        with pytest.raises(ValidationError):
            MessageGroupCreate(name="")
        
        # Too long
        with pytest.raises(ValidationError):
            MessageGroupCreate(name="x" * 101)


class TestMessageModels:
    """Test message Pydantic models."""
    
    def test_message_create_sms_valid(self):
        """Test creating a valid SMS message."""
        message_data = {
            "channel": "sms",
            "content": "Test SMS message",
            "group_id": 1
        }
        message = MessageCreate(**message_data)
        assert message.channel == MessageChannel.SMS
        assert message.content == "Test SMS message"
        assert message.subject is None
        assert message.group_id == 1
    
    def test_message_create_email_valid(self):
        """Test creating a valid email message."""
        message_data = {
            "channel": "email",
            "content": "Test email content",
            "subject": "Test Subject",
            "group_id": 1
        }
        message = MessageCreate(**message_data)
        assert message.channel == MessageChannel.EMAIL
        assert message.content == "Test email content"
        assert message.subject == "Test Subject"
        assert message.group_id == 1
    
    def test_email_requires_subject(self):
        """Test that email messages require a subject."""
        with pytest.raises(ValidationError) as exc:
            MessageCreate(
                channel="email",
                content="Test content",
                group_id=1
                # Missing subject
            )
        assert "Subject is required for email messages" in str(exc.value)
    
    def test_sms_should_not_have_subject(self):
        """Test that SMS messages should not have a subject."""
        with pytest.raises(ValidationError) as exc:
            MessageCreate(
                channel="sms",
                content="Test SMS",
                subject="Should not have this",
                group_id=1
            )
        assert "Subject should not be provided for SMS messages" in str(exc.value)
    
    def test_message_update_status(self):
        """Test updating message status."""
        update = MessageUpdate(
            status="delivered",
            twilio_sid="SM123456789",
            delivered_at=datetime.now(timezone.utc)
        )
        assert update.status == MessageStatus.DELIVERED
        assert update.twilio_sid == "SM123456789"
        assert update.delivered_at is not None


class TestMessageTemplateModels:
    """Test message template Pydantic models."""
    
    def test_template_create_valid(self):
        """Test creating a valid message template."""
        template_data = {
            "name": "Event Reminder",
            "content": "Reminder: {event_name} starts at {start_time}",
            "category": "event",
            "is_active": True
        }
        template = MessageTemplateCreate(**template_data)
        assert template.name == "Event Reminder"
        assert "{event_name}" in template.content
        assert template.category == "event"
        assert template.is_active is True


class TestPersonSMSModels:
    """Test person SMS-related models."""
    
    def test_person_sms_update_valid_phone(self):
        """Test updating person with valid phone number."""
        update = PersonSMSUpdate(
            phone_number="+1234567890",
            sms_consent=True,
            sms_opt_out=False
        )
        assert update.phone_number == "+1234567890"
        assert update.sms_consent is True
        assert update.sms_opt_out is False
    
    def test_phone_number_validation_international_format(self):
        """Test phone number international format validation."""
        # Valid formats
        valid_phones = ["+1234567890", "+44123456789", "+86123456789012"]
        for phone in valid_phones:
            update = PersonSMSUpdate(phone_number=phone)
            assert update.phone_number == phone
    
    def test_phone_number_validation_invalid_format(self):
        """Test phone number validation rejects invalid formats."""
        invalid_phones = [
            "1234567890",  # Missing +
            "+123",        # Too short
            "+123456789012345678",  # Too long
            "+abc123456789",  # Contains letters
            "+123-456-7890"   # Contains hyphens (should be cleaned)
        ]
        
        for phone in invalid_phones[:-1]:  # Skip the last one as it should be cleaned
            with pytest.raises(ValidationError):
                PersonSMSUpdate(phone_number=phone)
    
    def test_phone_number_formatting_cleanup(self):
        """Test that phone numbers are cleaned of formatting."""
        update = PersonSMSUpdate(phone_number="+1 (234) 567-890")
        # Should be cleaned to remove spaces, parentheses, hyphens
        assert "(" not in update.phone_number
        assert ")" not in update.phone_number
        assert "-" not in update.phone_number
        assert " " not in update.phone_number


class TestAPIResponseModels:
    """Test API response models."""
    
    def test_message_send_response(self):
        """Test message send response model."""
        response = MessageSendResponse(
            message_id=123,
            status="queued",
            recipients_count=5,
            estimated_cost=0.50,
            twilio_sid="SM123456789"
        )
        assert response.message_id == 123
        assert response.status == MessageStatus.QUEUED
        assert response.recipients_count == 5
        assert response.estimated_cost == 0.50
        assert response.twilio_sid == "SM123456789"