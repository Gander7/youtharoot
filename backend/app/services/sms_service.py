"""
SMS Service for Twilio integration.

Handles SMS sending, phone number validation, webhooks, rate limiting, and cost tracking.
Follows enterprise security practices with proper error handling and monitoring.
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
import phonenumbers
from phonenumbers import NumberParseException
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy.orm import Session

from app.db_models import MessageDB, PersonDB
from app.messaging_models import MessageStatus

# Configure logging
logger = logging.getLogger(__name__)


class SMSError(Exception):
    """Base exception for SMS service errors."""
    pass


class RateLimitError(SMSError):
    """Exception raised when rate limit is exceeded."""
    pass


class ValidationError(SMSError):
    """Exception raised for validation errors."""
    pass


class SMSSettings(BaseModel):
    """SMS service configuration settings."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    twilio_account_sid: str = Field(..., min_length=34)
    twilio_auth_token: str = Field(..., min_length=32)
    twilio_phone_number: str = Field(..., pattern=r'^\+\d{10,15}$')
    max_messages_per_hour: int = Field(default=200, gt=0, description="Hourly SMS rate limit for cost/spam protection")
    cost_per_sms: float = Field(default=0.0075, ge=0.0, description="Cost per SMS for budget tracking and alerts")
    
    @field_validator('twilio_phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate Twilio phone number format."""
        try:
            parsed = phonenumbers.parse(v)
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError(f"Invalid Twilio phone number: {v}")
            return v
        except NumberParseException as e:
            raise ValidationError(f"Invalid Twilio phone number format: {v} - {e}")


class SMSService:
    """
    SMS service for sending messages via Twilio.
    
    Features:
    - SMS sending with error handling
    - Phone number validation 
    - Rate limiting and cost tracking
    - Webhook processing for delivery status
    - Security validation for webhooks
    """
    
    def __init__(self, settings: SMSSettings, db: Optional[Session] = None):
        """Initialize SMS service with Twilio client."""
        self.settings = settings
        self.db = db
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.validator = RequestValidator(settings.twilio_auth_token)
        
        # Rate limiting tracking (in-memory for now - could use Redis in production)
        self._message_timestamps: deque = deque()
        self._total_cost = 0.0
        
        logger.info(f"SMS Service initialized with phone number {settings.twilio_phone_number}")
    
    def send_message(self, to_phone: str, message_body: str, person_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Send SMS message via Twilio.
        
        Args:
            to_phone: Recipient phone number in E.164 format
            message_body: Message content
            person_id: Optional person ID to check opt-out status
            
        Returns:
            Dict with success status, message_sid, status, and error info
            
        Raises:
            RateLimitError: If rate limit exceeded
            SMSError: If Twilio API error occurs
        """
        # Check if person has opted out of SMS
        if person_id and self.db:
            person = self.db.query(PersonDB).filter(PersonDB.id == person_id).first()
            if person and person.sms_opt_out:
                logger.info(f"SMS blocked for person {person_id}: user has opted out")
                return {
                    "success": False,
                    "message_sid": None,
                    "status": "opted_out",
                    "error": "Recipient has opted out of SMS messages"
                }
        
        # Check rate limit
        self._check_rate_limit()
        
        # Validate phone number
        phone_validation = self.validate_phone_number(to_phone)
        if not phone_validation["valid"]:
            raise SMSError(f"Invalid phone number: {phone_validation['error']}")
        
        try:
            # Send message via Twilio
            message = self.client.messages.create(
                to=to_phone,
                from_=self.settings.twilio_phone_number,
                body=message_body
            )
            
            # Track for rate limiting and costs
            self._track_message()
            
            logger.info(f"SMS sent successfully to {to_phone}, SID: {message.sid}")
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "error": None
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error sending SMS to {to_phone}: {e}")
            raise SMSError(f"Twilio API error: {e.msg}")
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {to_phone}: {e}")
            raise SMSError(f"Unexpected error: {str(e)}")
    
    def get_sms_recipients(self, person_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Get list of persons who will receive SMS (haven't opted out).
        
        Args:
            person_ids: Optional list of specific person IDs to check. If None, checks all persons.
            
        Returns:
            List of dicts with person info who will receive SMS
        """
        if not self.db:
            return []
        
        query = self.db.query(PersonDB).filter(
            PersonDB.sms_opt_out == False,
            PersonDB.phone_number.isnot(None),
            PersonDB.phone_number != "",
            PersonDB.archived_on.is_(None)  # Don't include archived persons
        )
        
        if person_ids:
            query = query.filter(PersonDB.id.in_(person_ids))
        
        persons = query.all()
        
        return [
            {
                "id": person.id,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "phone_number": person.phone_number,
                "person_type": person.person_type
            }
            for person in persons
        ]
    
    def validate_phone_number(self, phone_number: str, default_region: str = "CA") -> Dict[str, Any]:
        """
        Validate phone number format with Canadian default.
        
        Args:
            phone_number: Phone number to validate
            default_region: Default country code for numbers without country prefix (CA for Canada)
            
        Returns:
            Dict with valid status, formatted number, and error info
        """
        if not phone_number:
            return {
                "valid": False,
                "formatted": None,
                "error": "Phone number is required"
            }
        
        try:
            # Parse phone number with Canadian default for numbers without country code
            parsed = phonenumbers.parse(phone_number, default_region)
            
            # Check if valid
            if not phonenumbers.is_valid_number(parsed):
                return {
                    "valid": False,
                    "formatted": None,
                    "error": "Invalid phone number format"
                }
            
            # Format in E.164 format
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            
            return {
                "valid": True,
                "formatted": formatted,
                "error": None
            }
            
        except NumberParseException as e:
            return {
                "valid": False,
                "formatted": None,
                "error": f"Phone number parsing error: {e}"
            }
        except Exception as e:
            return {
                "valid": False,
                "formatted": None,
                "error": f"Validation error: {str(e)}"
            }
    
    def handle_webhook(self, webhook_data: Dict[str, Any], url: str, signature: str) -> Dict[str, Any]:
        """
        Handle Twilio webhook for delivery status updates.
        
        Args:
            webhook_data: Webhook payload from Twilio
            url: Webhook URL for signature validation
            signature: X-Twilio-Signature header value
            
        Returns:
            Dict with validation status and update info
            
        Raises:
            ValidationError: If webhook signature is invalid
        """
        print(f"🔍 SMS Service webhook validation:")
        print(f"   URL: {url}")
        print(f"   Signature: {signature}")
        print(f"   Webhook data: {webhook_data}")
        print(f"   Auth token configured: {bool(self.client.auth[1] if hasattr(self.client, 'auth') else False)}")
        
        # Validate webhook signature for security
        is_valid = self.validator.validate(url, webhook_data, signature)
        print(f"   Signature valid: {is_valid}")
        
        if not is_valid:
            logger.warning(f"Invalid webhook signature for URL: {url}")
            print(f"❌ Webhook validation failed!")
            raise ValidationError("Invalid webhook signature")
        
        message_sid = webhook_data.get("MessageSid")
        message_status = webhook_data.get("MessageStatus")
        error_code = webhook_data.get("ErrorCode")
        
        print(f"   Message SID: {message_sid}")
        print(f"   Message Status: {message_status}")
        print(f"   Error Code: {error_code}")
        
        logger.info(f"Processing webhook for message {message_sid}, status: {message_status}")
        
        # Update message status in database if available
        updated = False
        if self.db and message_sid:
            message = self.db.query(MessageDB).filter(
                MessageDB.twilio_sid == message_sid
            ).first()
            
            if message:
                # Update status
                if message_status == "delivered":
                    message.status = MessageStatus.DELIVERED
                    message.delivered_at = datetime.now(timezone.utc)
                elif message_status == "failed":
                    message.status = MessageStatus.FAILED
                    message.error_code = error_code
                elif message_status == "undelivered":
                    message.status = MessageStatus.FAILED
                    message.error_code = error_code
                
                self.db.commit()
                updated = True
                logger.info(f"Updated message {message_sid} status to {message_status}")
                print(f"✅ Message status updated in database")
        
        return {
            "valid": True,
            "message_sid": message_sid,
            "status": message_status,
            "updated": updated
        }
    
    def get_total_cost(self) -> float:
        """Get total cost of SMS messages sent."""
        return self._total_cost
    
    def get_hourly_cost(self) -> float:
        """Get cost of SMS messages sent in the last hour."""
        return self._total_cost  # Simplified for now - in practice would track by time
    
    def _check_rate_limit(self) -> None:
        """Check if rate limit is exceeded."""
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        
        # Remove old timestamps
        while self._message_timestamps and self._message_timestamps[0] < one_hour_ago:
            self._message_timestamps.popleft()
        
        # Check limit
        if len(self._message_timestamps) >= self.settings.max_messages_per_hour:
            raise RateLimitError(
                f"Rate limit exceeded: {len(self._message_timestamps)} messages "
                f"in last hour (limit: {self.settings.max_messages_per_hour})"
            )
    
    def _track_message(self) -> None:
        """Track message for rate limiting and cost calculation."""
        now = datetime.now(timezone.utc)
        self._message_timestamps.append(now)
        self._total_cost += self.settings.cost_per_sms