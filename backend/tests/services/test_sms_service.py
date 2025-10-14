"""
TDD Tests for SMS Service Integration with Twilio.

Following TDD RED-GREEN-REFACTOR cycle:
1. RED: Write failing tests first (this file)
2. GREEN: Write minimal code to make tests pass
3. REFACTOR: Improve code while keeping tests green

Test Strategy:
- Mock Twilio client to avoid API costs during testing
- Test all SMS service methods: send_message(), validate_phone_number(), handle_webhook()
- Test error handling scenarios (invalid phones, API failures, rate limits)
- Test cost monitoring and rate limiting
- Test webhook signature validation for security
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any

# These imports will fail initially - that's expected for TDD RED phase
try:
    from app.services.sms_service import SMSService, SMSError, RateLimitError, ValidationError
    from app.services.sms_service import SMSSettings
except ImportError:
    # Expected to fail initially in TDD RED phase
    SMSService = None
    SMSError = None
    RateLimitError = None
    ValidationError = None
    SMSSettings = None


class TestSMSService:
    """Test SMS service functionality with mocked Twilio client."""
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Mock Twilio client for testing."""
        with patch('app.services.sms_service.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def sms_service(self, mock_twilio_client):
        """Create SMS service instance with mocked Twilio client."""
        # This will fail initially - expected for TDD RED phase
        if SMSService is None:
            pytest.skip("SMSService not implemented yet - TDD RED phase")
        
        settings = SMSSettings(
            twilio_account_sid="AC" + "0" * 32,  # Valid format
            twilio_auth_token="test_auth_token_123456789012345678901234567890",  # Valid length
            twilio_phone_number="+12025551234",  # Valid US number
            max_messages_per_hour=200,
            cost_per_sms=0.0075
        )
        return SMSService(settings)
    
    def test_send_sms_success(self, sms_service, mock_twilio_client):
        """Test successful SMS sending."""
        # Arrange
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "queued"
        mock_message.error_code = None
        mock_twilio_client.messages.create.return_value = mock_message
        
        to_phone = "+16505551234"
        message_body = "Test message"
        
        # Act
        result = sms_service.send_message(to_phone, message_body)
        
        # Assert
        assert result["success"] is True
        assert result["message_sid"] == "SM123456789"
        assert result["status"] == "queued"
        assert result["error"] is None
        
        # Verify Twilio client was called correctly
        mock_twilio_client.messages.create.assert_called_once_with(
            to=to_phone,
            from_=sms_service.settings.twilio_phone_number,
            body=message_body
        )
    
    def test_send_sms_twilio_error(self, sms_service, mock_twilio_client):
        """Test SMS sending with Twilio API error."""
        # Arrange
        from twilio.base.exceptions import TwilioRestException
        mock_twilio_client.messages.create.side_effect = TwilioRestException(
            status=400, 
            uri="test_uri",
            msg="Invalid phone number"
        )
        
        # Act & Assert - use a valid format phone number so validation passes
        # but Twilio call fails
        with pytest.raises(SMSError) as exc_info:
            sms_service.send_message("+12025551234", "Test message")
        
        assert "Twilio API error" in str(exc_info.value)
        assert "Invalid phone number" in str(exc_info.value)
    
    def test_validate_phone_number_valid_formats(self, sms_service):
        """Test phone number validation with valid formats."""
        valid_phones = [
            "+12025551234",   # US format with country code
            "+14165551234",   # Canadian Toronto
            "+16045551234",   # Canadian Vancouver
            "+442071234567",  # UK format
            "+61212345678",   # Australia format
            "416-555-1234",   # Canadian format without country code -> +14165551234
            "(604) 555-1234", # Canadian format with parentheses -> +16045551234
        ]
        
        for phone in valid_phones:
            result = sms_service.validate_phone_number(phone)
            assert result["valid"] is True, f"Phone {phone} should be valid"
            assert result["formatted"].startswith("+"), f"Phone {phone} should be in E.164 format"
            assert result["error"] is None
    
    def test_validate_phone_number_invalid_formats(self, sms_service):
        """Test phone number validation with invalid formats."""
        invalid_phones = [
            "1234567",        # Too short for any region
            "+1234",          # Too short
            "+123456789012345",  # Too long
            "invalid",        # Not a number
            "",               # Empty string
            None,             # None value
        ]

        for phone in invalid_phones:
            result = sms_service.validate_phone_number(phone)
            assert result["valid"] is False
            assert result["formatted"] is None
            assert result["error"] is not None
    
    def test_validate_canadian_phone_numbers(self, sms_service):
        """Test Canadian phone number validation with various formats."""
        canadian_numbers = [
            ("+14165551234", "+14165551234"),      # Toronto with country code
            ("+16045551234", "+16045551234"),      # Vancouver with country code
            ("416-555-1234", "+14165551234"),     # Toronto without country code
            ("(604) 555-1234", "+16045551234"),   # Vancouver with formatting
            ("4165551234", "+14165551234"),       # Toronto digits only
            ("+1 416 555 1234", "+14165551234"),  # With spaces
        ]
        
        for input_phone, expected_formatted in canadian_numbers:
            result = sms_service.validate_phone_number(input_phone)
            assert result["valid"] is True, f"Failed for {input_phone}"
            assert result["formatted"] == expected_formatted, f"Formatting mismatch for {input_phone}"
            assert result["error"] is None

    def test_sms_opt_out_blocks_message(self, sms_service, mock_twilio_client, test_db):
        """Test that SMS is blocked for users who have opted out."""
        # Arrange - create a person who has opted out
        from app.db_models import PersonDB
        
        person = PersonDB(
            id=123,
            first_name="Test",
            last_name="User",
            phone_number="+14165551234",
            sms_opt_out=True,
            person_type="youth"
        )
        test_db.add(person)
        test_db.commit()
        
        # Create SMS service with database
        sms_service_with_db = SMSService(sms_service.settings, test_db)
        sms_service_with_db.client = mock_twilio_client
        
        # Act
        result = sms_service_with_db.send_message("+14165551234", "Test message", person_id=123)
        
        # Assert
        assert result["success"] is False
        assert result["status"] == "opted_out"
        assert "opted out" in result["error"]
        
        # Verify Twilio API was not called
        mock_twilio_client.messages.create.assert_not_called()

    def test_sms_sends_to_non_opted_out_users(self, sms_service, mock_twilio_client, test_db):
        """Test that SMS sends successfully to users who have not opted out."""
        # Arrange - create a person who has not opted out
        from app.db_models import PersonDB
        
        person = PersonDB(
            id=456,
            first_name="Test",
            last_name="User",
            phone_number="+14165551234",
            sms_opt_out=False,
            person_type="youth"
        )
        test_db.add(person)
        test_db.commit()
        
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "queued"
        mock_twilio_client.messages.create.return_value = mock_message
        
        # Create SMS service with database
        sms_service_with_db = SMSService(sms_service.settings, test_db)
        sms_service_with_db.client = mock_twilio_client
        
        # Act
        result = sms_service_with_db.send_message("+14165551234", "Test message", person_id=456)
        
        # Assert
        assert result["success"] is True
        assert result["message_sid"] == "SM123456789"
        
        # Verify Twilio API was called
        mock_twilio_client.messages.create.assert_called_once()

    def test_get_sms_recipients_excludes_opted_out(self, sms_service, test_db):
        """Test that get_sms_recipients only returns users who haven't opted out."""
        # Arrange - create multiple persons with different opt-out status
        from app.db_models import PersonDB
        
        persons = [
            PersonDB(id=1, first_name="Will", last_name="Receive", phone_number="+14165551111", sms_opt_out=False, person_type="youth"),
            PersonDB(id=2, first_name="Opted", last_name="Out", phone_number="+14165552222", sms_opt_out=True, person_type="youth"),
            PersonDB(id=3, first_name="Also", last_name="Receives", phone_number="+14165553333", sms_opt_out=False, person_type="leader"),
            PersonDB(id=4, first_name="No", last_name="Phone", phone_number=None, sms_opt_out=False, person_type="youth"),  # Should be excluded
        ]
        
        for person in persons:
            test_db.add(person)
        test_db.commit()
        
        # Create SMS service with database
        sms_service_with_db = SMSService(sms_service.settings, test_db)
        
        # Act
        recipients = sms_service_with_db.get_sms_recipients()
        
        # Assert
        assert len(recipients) == 2  # Only persons 1 and 3
        recipient_ids = [r["id"] for r in recipients]
        assert 1 in recipient_ids
        assert 3 in recipient_ids
        assert 2 not in recipient_ids  # Opted out
        assert 4 not in recipient_ids  # No phone number
    
    def test_rate_limiting_enforced(self, sms_service, mock_twilio_client):
        """Test that rate limiting is enforced."""
        # Arrange - simulate hitting rate limit
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "queued"
        mock_twilio_client.messages.create.return_value = mock_message
        
        # Send messages up to the limit
        for i in range(sms_service.settings.max_messages_per_hour):
            sms_service.send_message("+16505551234", f"Message {i}")
        
        # Act & Assert - next message should trigger rate limit
        with pytest.raises(RateLimitError) as exc_info:
            sms_service.send_message("+16505551234", "Rate limit test")
        
        assert "Rate limit exceeded" in str(exc_info.value)
    
    def test_cost_tracking(self, sms_service, mock_twilio_client):
        """Test SMS cost tracking."""
        # Arrange
        mock_message = Mock()
        mock_message.sid = "SM123456789"
        mock_message.status = "queued"
        mock_twilio_client.messages.create.return_value = mock_message
        
        # Act - send 3 messages
        for i in range(3):
            sms_service.send_message("+16505551234", f"Message {i}")
        
        # Assert
        total_cost = sms_service.get_total_cost()
        expected_cost = 3 * sms_service.settings.cost_per_sms
        assert abs(total_cost - expected_cost) < 0.001  # Float comparison
        
        # Test cost tracking for time period
        hourly_cost = sms_service.get_hourly_cost()
        assert hourly_cost == expected_cost


class TestSMSWebhook:
    """Test SMS webhook handling for delivery status updates."""
    
    @pytest.fixture
    def sms_service(self, test_db):
        """Create SMS service for webhook testing."""
        if SMSService is None:
            pytest.skip("SMSService not implemented yet - TDD RED phase")
            
        settings = SMSSettings(
            twilio_account_sid="AC" + "0" * 32,
            twilio_auth_token="test_auth_token_123456789012345678901234567890",
            twilio_phone_number="+12025551234",
            max_messages_per_hour=200,
            cost_per_sms=0.0075
        )
        return SMSService(settings, db=test_db)
    
    def test_webhook_signature_validation_success(self, sms_service):
        """Test successful webhook signature validation."""
        # Arrange
        webhook_data = {
            "MessageSid": "SM123456789",
            "MessageStatus": "delivered",
            "To": "+16505551234",
            "From": "+12025551234"
        }
        
        # Mock the validator instance that already exists
        sms_service.validator.validate = Mock(return_value=True)
        
        # Act
        result = sms_service.handle_webhook(
            webhook_data, 
            "https://example.com/webhook",
            "valid_signature"
        )
        
        # Assert
        assert result["valid"] is True
        assert result["message_sid"] == "SM123456789"
        assert result["status"] == "delivered"
    
    def test_webhook_signature_validation_failure(self, sms_service):
        """Test webhook signature validation failure."""
        # Arrange
        webhook_data = {
            "MessageSid": "SM123456789",
            "MessageStatus": "delivered"
        }
        
        # Mock the validator instance that already exists
        sms_service.validator.validate = Mock(return_value=False)
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            sms_service.handle_webhook(
                webhook_data,
                "https://example.com/webhook", 
                "invalid_signature"
            )
        
        assert "Invalid webhook signature" in str(exc_info.value)
    
    def test_webhook_status_update_processing(self, sms_service, test_db):
        """Test webhook processes status updates correctly."""
        # This test will connect to our messaging database models
        # Arrange - create the required related records first
        from app.db_models import MessageDB, MessageGroupDB, UserDB
        from app.messaging_models import MessageChannel, MessageStatus
        
        # Create a user first
        user = UserDB(
            username="test_user",
            password_hash="hashed_password"
        )
        test_db.add(user)
        test_db.flush()  # Get the ID
        
        # Create a message group
        group = MessageGroupDB(
            name="Test Group",
            description="Test group for webhook testing",
            created_by=user.id
        )
        test_db.add(group)
        test_db.flush()  # Get the ID
        
        # Create a message
        message = MessageDB(
            group_id=group.id,
            sent_by=user.id,
            channel=MessageChannel.SMS,
            content="Test message",
            status=MessageStatus.SENT,
            twilio_sid="SM123456789"
        )
        test_db.add(message)
        test_db.commit()
        
        webhook_data = {
            "MessageSid": "SM123456789", 
            "MessageStatus": "delivered",
            "ErrorCode": None
        }
        
        # Mock the validator instance that already exists
        sms_service.validator.validate = Mock(return_value=True)
        
        # Act
        result = sms_service.handle_webhook(
            webhook_data,
            "https://example.com/webhook",
            "valid_signature"
        )
        
        # Assert
        assert result["valid"] is True
        assert result["updated"] is True
        
        # Verify database was updated
        updated_message = test_db.query(MessageDB).filter(
            MessageDB.twilio_sid == "SM123456789"
        ).first()
        assert updated_message.status == MessageStatus.DELIVERED
        assert updated_message.delivered_at is not None
class TestSMSServiceConfiguration:
    """Test SMS service configuration and settings."""
    
    def test_sms_settings_validation(self):
        """Test SMS settings validation."""
        if SMSSettings is None:
            pytest.skip("SMSSettings not implemented yet - TDD RED phase")
        
        # Test valid settings
        valid_settings = SMSSettings(
            twilio_account_sid="AC" + "0" * 32,
            twilio_auth_token="auth_token_123456789012345678901234567890",
            twilio_phone_number="+12025551234",
            max_messages_per_hour=200,
            cost_per_sms=0.0075
        )
        assert valid_settings.twilio_account_sid == "AC" + "0" * 32
        assert valid_settings.max_messages_per_hour == 200
    
    def test_sms_settings_invalid_phone_number(self):
        """Test SMS settings with invalid phone number."""
        if SMSSettings is None:
            pytest.skip("SMSSettings not implemented yet - TDD RED phase")
        
        # Pydantic raises its own ValidationError, so we catch both
        from pydantic import ValidationError as PydanticValidationError
        
        with pytest.raises((ValidationError, PydanticValidationError)):
            SMSSettings(
                twilio_account_sid="AC" + "0" * 32,
                twilio_auth_token="auth_token_123456789012345678901234567890",
                twilio_phone_number="invalid_phone",  # Invalid format
                max_messages_per_hour=100,
                cost_per_sms=0.0075
            )
    
    def test_sms_settings_rate_limit_validation(self):
        """Test SMS settings rate limit validation."""
        if SMSSettings is None:
            pytest.skip("SMSSettings not implemented yet - TDD RED phase")
        
        # Pydantic raises its own ValidationError, so we catch both
        from pydantic import ValidationError as PydanticValidationError
        
        with pytest.raises((ValidationError, PydanticValidationError)):
            SMSSettings(
                twilio_account_sid="AC" + "0" * 32,
                twilio_auth_token="auth_token_123456789012345678901234567890",
                twilio_phone_number="+12025551234",
                max_messages_per_hour=0,  # Invalid - must be positive
                cost_per_sms=0.0075
            )