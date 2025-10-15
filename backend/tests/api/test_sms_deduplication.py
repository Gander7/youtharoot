"""
Test SMS deduplication functionality.

Ensures that duplicate phone numbers in a group don't result in duplicate SMS sends.
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.routers.sms import router
from app.models import User
from app.messaging_models import MessageGroupMembership


@pytest.mark.asyncio
async def test_group_sms_deduplicates_phone_numbers():
    """Test that duplicate phone numbers are removed before sending SMS."""
    
    # Mock user
    mock_user = User(id=1, username="testuser", email="test@test.com", password_hash="fake_hash")
    
    # Mock group members with duplicate phone numbers
    from datetime import datetime
    mock_members = [
        MessageGroupMembership(id=1, group_id=1, person_id=1, added_by=1, joined_at=datetime.now()),
        MessageGroupMembership(id=2, group_id=1, person_id=2, added_by=1, joined_at=datetime.now()),
        MessageGroupMembership(id=3, group_id=1, person_id=3, added_by=1, joined_at=datetime.now()),  # Different person, same phone as person 1
    ]
    
    # Mock SMS recipients with duplicate phone numbers
    mock_recipients = [
        {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+15551234567",
            "person_type": "youth"
        },
        {
            "id": 2,
            "first_name": "Jane",
            "last_name": "Smith",
            "phone_number": "+15559876543",
            "person_type": "youth"
        },
        {
            "id": 3,
            "first_name": "Jim",
            "last_name": "Doe",  # Same family, same phone as John
            "phone_number": "+15551234567",  # DUPLICATE!
            "person_type": "youth"
        }
    ]
    
    with patch('app.routers.sms.get_group_repository') as mock_repo, \
         patch('app.routers.sms.get_sms_service') as mock_sms_service, \
         patch('app.routers.sms.get_db') as mock_db:
        
        # Setup mocks
        mock_group_repo = AsyncMock()
        mock_group_repo.get_group.return_value = {"id": 1, "name": "Test Group"}
        mock_group_repo.get_group_members.return_value = mock_members
        mock_repo.return_value = mock_group_repo
        
        mock_sms = AsyncMock()
        mock_sms.get_sms_recipients.return_value = mock_recipients
        
        # Track how many times send_message is called
        send_calls = []
        def mock_send_message(**kwargs):
            send_calls.append(kwargs)
            return {
                "success": True,
                "message_sid": f"SM{len(send_calls)}",
                "status": "sent",
                "error": None
            }
        
        mock_sms.send_message.side_effect = mock_send_message
        mock_sms_service.return_value = mock_sms
        
        # Mock database
        mock_session = AsyncMock()
        mock_db.return_value = mock_session
        
        from app.routers.sms import GroupSMSSendRequest
        
        # Test the deduplication
        request = GroupSMSSendRequest(
            group_id=1,
            message="Test message"
        )
        
        # This should only send 2 SMS messages (not 3) due to deduplication
        with patch('app.routers.sms.get_current_user', return_value=mock_user):
            response = await router.send_group_sms(
                request=request,
                current_user=mock_user,
                sms_service=mock_sms,
                db=mock_session
            )
        
        # Verify deduplication worked
        assert len(send_calls) == 2, f"Expected 2 SMS sends (after deduplication), got {len(send_calls)}"
        
        # Verify the unique phone numbers were used
        sent_phones = {call['to_phone'] for call in send_calls}
        expected_phones = {"+15551234567", "+15559876543"}
        assert sent_phones == expected_phones, f"Expected {expected_phones}, got {sent_phones}"
        
        # Verify response shows correct counts
        assert response.sent_count == 2
        assert response.success is True


@pytest.mark.asyncio  
async def test_group_sms_logs_duplicates():
    """Test that duplicate removal is properly logged."""
    
    with patch('app.routers.sms.logger') as mock_logger:
        # Run the previous test to trigger duplicate removal
        await test_group_sms_deduplicates_phone_numbers()
        
        # Check that duplicate warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "Duplicate phone number detected" in str(call)]
        
        assert len(warning_calls) >= 1, "Should log duplicate phone number warning"
        
        # Check that duplicate count was logged
        info_calls = [call for call in mock_logger.info.call_args_list 
                     if "Removed" in str(call) and "duplicate" in str(call)]
        
        assert len(info_calls) >= 1, "Should log duplicate removal count"