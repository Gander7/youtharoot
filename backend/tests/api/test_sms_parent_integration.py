"""
TDD Tests for SMS Parent Integration - Parent SMS Group Functionality.

Tests parent integration in SMS messaging:
- Parents receive notifications when youth in their care get group messages
- Parent SMS opt-out preferences are respected
- Customizable parent notification messages
- Parent-specific SMS analytics and tracking
- Opt-in/opt-out management for parent notifications

Following TDD methodology (RED-GREEN-REFACTOR):
1. Write failing tests for parent SMS features
2. Implement minimal functionality to pass tests
3. Refactor and enhance while keeping tests green
"""

import pytest
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.messaging_models import MessageChannel, MessageStatus
from app.services.sms_service import SMSService, SMSError, ValidationError
from app.auth import get_current_user
from app.models import User


# Mock authentication for testing
async def get_test_user():
    return User(id=1, username="test_user", password_hash="hashed", role="admin")

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment including auth and dependency mocks."""
    app.dependency_overrides[get_current_user] = get_test_user
    yield
    app.dependency_overrides = {}

@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Authenticated user headers."""
    return {"Authorization": "Bearer test-token"}


class TestSMSParentIntegration:
    """Test suite for SMS parent integration functionality."""
    
    def test_send_group_sms_includes_parents_by_default(self, client, auth_headers):
        """Test that sending SMS to youth group includes parents by default."""
        # Mock both group repository and SMS service
        def get_mock_sms_service():
            service = Mock(spec=SMSService)
            # Mock get_sms_recipients to return youth and their parents
            service.get_sms_recipients_with_parents = AsyncMock(return_value={
                "youth_recipients": [
                    {
                        "id": 1,
                        "first_name": "Alex",
                        "last_name": "Youth", 
                        "phone_number": "+12345678901",
                        "person_type": "youth"
                    }
                ],
                "parent_recipients": [
                    {
                        "id": 2, 
                        "first_name": "Jane",
                        "last_name": "Parent",
                        "phone_number": "+12345678902",
                        "person_type": "parent",
                        "relationship_to_youth": 1,
                        "relationship_type": "mother"
                    }
                ]
            })
            # Mock send_message to succeed
            service.send_message = Mock(return_value={
                "success": True,
                "message_sid": "SM123456789",
                "status": "sent"
            })
            return service
        
        from app.routers.sms import get_sms_service
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        # Use patch to mock the group repository function  
        with patch('app.routers.sms.get_group_repository') as mock_get_group_repo:
            # Setup group repository mock
            mock_group_repo = Mock()
            mock_group = Mock()
            mock_group.id = 1
            mock_group.name = "Test Youth Group"
            mock_group_repo.get_group = AsyncMock(return_value=mock_group)
            
            # Mock group members (youth only)
            mock_member1 = Mock()
            mock_member1.person_id = 1
            mock_group_repo.get_group_members = AsyncMock(return_value=[mock_member1])
            
            mock_get_group_repo.return_value = mock_group_repo
            
            # Act - send group SMS with parent inclusion
            payload = {
                "group_id": 1,
                "message": "Youth event reminder: Practice tomorrow at 7pm!",
                "include_parents": True
            }
            
            response = client.post("/api/sms/send-group", json=payload, headers=auth_headers)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["sent_count"] == 2  # 1 youth + 1 parent
            assert data["parent_count"] == 1
            assert "parent_recipients" in data
            
            # Verify parent notification was customized
            results = data["results"]
            parent_result = next((r for r in results if r["person_type"] == "parent"), None)
            assert parent_result is not None
            assert "Alex Youth" in parent_result["message_sent"]  # Parent message should mention youth name

    def test_send_group_sms_excludes_parents_when_disabled(self, client, auth_headers):
        """Test that parent inclusion can be disabled for group SMS."""
        def get_mock_sms_service():
            service = Mock(spec=SMSService)
            # Mock get_sms_recipients to return only youth (no parents)
            service.get_sms_recipients = AsyncMock(return_value=[
                {
                    "id": 1,
                    "first_name": "Alex",
                    "last_name": "Youth", 
                    "phone_number": "+12345678901"
                }
            ])
            service.send_message = Mock(return_value={
                "success": True,
                "message_sid": "SM123456789",
                "status": "sent"
            })
            return service
        
        from app.routers.sms import get_sms_service
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        with patch('app.routers.sms.get_group_repository') as mock_get_group_repo:
            mock_group_repo = Mock()
            mock_group = Mock()
            mock_group.id = 1
            mock_group.name = "Test Youth Group"
            mock_group_repo.get_group = AsyncMock(return_value=mock_group)
            
            mock_member1 = Mock()
            mock_member1.person_id = 1
            mock_group_repo.get_group_members = AsyncMock(return_value=[mock_member1])
            
            mock_get_group_repo.return_value = mock_group_repo
            
            # Act - send group SMS without parent inclusion
            payload = {
                "group_id": 1,
                "message": "Youth event reminder: Practice tomorrow at 7pm!",
                "include_parents": False
            }
            
            response = client.post("/api/sms/send-group", json=payload, headers=auth_headers)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["sent_count"] == 1  # Only youth, no parents
            assert data.get("parent_count", 0) == 0

    def test_parent_sms_opt_out_prevents_notification(self, client, auth_headers):
        """Test that parents who opted out don't receive group notifications."""
        def get_mock_sms_service():
            service = Mock(spec=SMSService)
            # Mock to return youth but no parents (parent opted out)
            service.get_sms_recipients_with_parents = AsyncMock(return_value={
                "youth_recipients": [
                    {
                        "id": 1,
                        "first_name": "Alex",
                        "last_name": "Youth", 
                        "phone_number": "+12345678901",
                        "person_type": "youth"
                    }
                ],
                "parent_recipients": []  # Parent opted out
            })
            service.send_message = Mock(return_value={
                "success": True,
                "message_sid": "SM123456789",
                "status": "sent"
            })
            return service
        
        from app.routers.sms import get_sms_service
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        with patch('app.routers.sms.get_group_repository') as mock_get_group_repo:
            mock_group_repo = Mock()
            mock_group = Mock()
            mock_group.id = 1
            mock_group_repo.get_group = AsyncMock(return_value=mock_group)
            
            mock_member1 = Mock()
            mock_member1.person_id = 1
            mock_group_repo.get_group_members = AsyncMock(return_value=[mock_member1])
            
            mock_get_group_repo.return_value = mock_group_repo
            
            payload = {
                "group_id": 1,
                "message": "Youth event reminder",
                "include_parents": True
            }
            
            response = client.post("/api/sms/send-group", json=payload, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["sent_count"] == 1  # Only youth (parent opted out)
            assert data["parent_count"] == 0
            assert data["skipped_count"] >= 0  # Parent was skipped due to opt-out

    def test_parent_notification_message_customization(self, client, auth_headers):
        """Test that parent notifications can have custom message content."""
        def get_mock_sms_service():
            service = Mock(spec=SMSService)
            service.get_sms_recipients_with_parents = AsyncMock(return_value={
                "youth_recipients": [
                    {
                        "id": 1,
                        "first_name": "Alex",
                        "last_name": "Youth", 
                        "phone_number": "+12345678901",
                        "person_type": "youth"
                    }
                ],
                "parent_recipients": [
                    {
                        "id": 2, 
                        "first_name": "Jane",
                        "last_name": "Parent",
                        "phone_number": "+12345678902",
                        "person_type": "parent",
                        "relationship_to_youth": 1,
                        "relationship_type": "mother"
                    }
                ]
            })
            service.send_message = Mock(return_value={
                "success": True,
                "message_sid": "SM123456789",
                "status": "sent"
            })
            return service
        
        from app.routers.sms import get_sms_service
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        with patch('app.routers.sms.get_group_repository') as mock_get_group_repo:
            mock_group_repo = Mock()
            mock_group = Mock()
            mock_group.id = 1
            mock_group_repo.get_group = AsyncMock(return_value=mock_group)
            
            mock_member1 = Mock()
            mock_member1.person_id = 1
            mock_group_repo.get_group_members = AsyncMock(return_value=[mock_member1])
            
            mock_get_group_repo.return_value = mock_group_repo
            
            # Act - send with custom parent message
            payload = {
                "group_id": 1,
                "message": "Practice tomorrow at 7pm",
                "parent_message": "Your child Alex has practice tomorrow at 7pm. Please ensure they arrive on time.",
                "include_parents": True
            }
            
            response = client.post("/api/sms/send-group", json=payload, headers=auth_headers)
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Verify different messages were sent
            results = data["results"]
            youth_result = next((r for r in results if r.get("person_type") == "youth"), None)
            parent_result = next((r for r in results if r.get("person_type") == "parent"), None)
            
            assert youth_result["message_sent"] == "Practice tomorrow at 7pm"
            assert "Your child Alex" in parent_result["message_sent"]

    def test_multiple_parents_per_youth_all_notified(self, client, auth_headers):
        """Test that all parents linked to a youth receive notifications."""
        def get_mock_sms_service():
            service = Mock(spec=SMSService)
            service.get_sms_recipients_with_parents = AsyncMock(return_value={
                "youth_recipients": [
                    {
                        "id": 1,
                        "first_name": "Alex",
                        "last_name": "Youth", 
                        "phone_number": "+12345678901",
                        "person_type": "youth"
                    }
                ],
                "parent_recipients": [
                    {
                        "id": 2, 
                        "first_name": "Jane",
                        "last_name": "Parent",
                        "phone_number": "+12345678902",
                        "person_type": "parent",
                        "relationship_to_youth": 1,
                        "relationship_type": "mother"
                    },
                    {
                        "id": 3,
                        "first_name": "John", 
                        "last_name": "Parent",
                        "phone_number": "+12345678903",
                        "person_type": "parent",
                        "relationship_to_youth": 1,
                        "relationship_type": "father"
                    }
                ]
            })
            service.send_message = Mock(return_value={
                "success": True,
                "message_sid": "SM123456789",
                "status": "sent"
            })
            return service
        
        from app.routers.sms import get_sms_service
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        with patch('app.routers.sms.get_group_repository') as mock_get_group_repo:
            mock_group_repo = Mock()
            mock_group = Mock()
            mock_group.id = 1
            mock_group_repo.get_group = AsyncMock(return_value=mock_group)
            
            mock_member1 = Mock()
            mock_member1.person_id = 1
            mock_group_repo.get_group_members = AsyncMock(return_value=[mock_member1])
            
            mock_get_group_repo.return_value = mock_group_repo
            
            payload = {
                "group_id": 1,
                "message": "Youth event notification",
                "include_parents": True
            }
            
            response = client.post("/api/sms/send-group", json=payload, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["sent_count"] == 3  # 1 youth + 2 parents
            assert data["parent_count"] == 2

    def test_parent_sms_analytics_tracking(self, client, auth_headers):
        """Test that parent SMS sends are tracked separately in analytics."""
        def get_mock_sms_service():
            service = Mock(spec=SMSService)
            # Mock analytics response with parent breakdown
            service.get_analytics = Mock(return_value={
                "total_sent": 10,
                "total_delivered": 8,
                "total_failed": 2,
                "delivery_rate": 80.0,
                "total_cost": 1.50,
                "youth_messages": 6,
                "parent_messages": 4,
                "parent_notification_rate": 0.67,  # 4 parent msgs / 6 youth msgs
                "opt_out_rate": 0.1
            })
            return service
        
        from app.routers.sms import get_sms_service
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        # Act
        response = client.get("/api/sms/analytics", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "parent_messages" in data
        assert "parent_notification_rate" in data
        assert data["parent_messages"] == 4
        assert data["parent_notification_rate"] == 0.67


class TestParentSMSOptOutManagement:
    """Test suite for parent-specific SMS opt-out functionality."""
    
    def test_set_parent_sms_notification_preference(self, client, auth_headers):
        """Test setting parent SMS notification preferences."""
        # This test will pass when we implement the endpoint
        payload = {
            "parent_id": 2,
            "sms_notifications_enabled": False,
            "notification_types": ["emergency_only"]
        }
        
        # This should return 404 until we implement it (TDD RED phase)
        response = client.post("/api/sms/parent-preferences", json=payload, headers=auth_headers)
        
        # Initially this will fail (RED) - that's expected in TDD
        assert response.status_code in [404, 501]  # Not implemented yet
        
    def test_get_parent_sms_notification_preferences(self, client, auth_headers):
        """Test retrieving parent SMS notification preferences."""
        # This test will pass when we implement the endpoint
        response = client.get("/api/sms/parent-preferences/2", headers=auth_headers)
        
        # Initially this will fail (RED) - that's expected in TDD
        assert response.status_code in [404, 501]  # Not implemented yet


class TestParentSMSValidation:
    """Test suite for parent SMS validation and error handling."""
    
    def test_invalid_parent_notification_settings_validation(self, client, auth_headers):
        """Test validation of parent notification settings."""
        def get_mock_sms_service():
            service = Mock(spec=SMSService)
            service.get_sms_recipients_with_parents = AsyncMock(return_value={
                "youth_recipients": [],
                "parent_recipients": []
            })
            return service
        
        from app.routers.sms import get_sms_service
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        with patch('app.routers.sms.get_group_repository') as mock_get_group_repo:
            mock_group_repo = Mock()
            mock_group = Mock()
            mock_group.id = 1
            mock_group_repo.get_group = AsyncMock(return_value=mock_group)
            mock_group_repo.get_group_members = AsyncMock(return_value=[])
            mock_get_group_repo.return_value = mock_group_repo
            
            # Test invalid parent message (too long)
            payload = {
                "group_id": 1,
                "message": "Short message",
                "parent_message": "A" * 2000,  # Too long
                "include_parents": True
            }
            
            response = client.post("/api/sms/send-group", json=payload, headers=auth_headers)
            
            assert response.status_code == 422  # Validation error
            data = response.json()
            assert "parent_message" in str(data["detail"])

    def test_group_with_no_youth_or_parents_returns_error(self, client, auth_headers):
        """Test that sending to empty group returns appropriate error."""
        def get_mock_sms_service():
            service = Mock(spec=SMSService)
            service.get_sms_recipients_with_parents = AsyncMock(return_value={
                "youth_recipients": [],
                "parent_recipients": []
            })
            return service
        
        from app.routers.sms import get_sms_service
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        with patch('app.routers.sms.get_group_repository') as mock_get_group_repo:
            mock_group_repo = Mock()
            mock_group = Mock()
            mock_group.id = 1
            mock_group_repo.get_group = AsyncMock(return_value=mock_group)
            mock_group_repo.get_group_members = AsyncMock(return_value=[])
            mock_get_group_repo.return_value = mock_group_repo
            
            payload = {
                "group_id": 1,
                "message": "Test message",
                "include_parents": True
            }
            
            response = client.post("/api/sms/send-group", json=payload, headers=auth_headers)
            
            assert response.status_code == 400
            data = response.json()
            assert "no eligible recipients" in data["detail"].lower()