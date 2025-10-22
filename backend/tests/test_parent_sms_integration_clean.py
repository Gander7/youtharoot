"""
Test cases for Parent SMS Integration following TDD methodology.

RED-GREEN-REFACTOR cycle:
1. RED: Write failing tests first  
2. GREEN: Write minimal code to make tests pass
3. REFACTOR: Improve code while keeping tests green
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from tests.test_helpers import get_authenticated_client
from app.config import settings

# Use authenticated client for all tests
client = get_authenticated_client()


@pytest.fixture(autouse=True)
def setup_test_user():
    """Create test user in database for SMS group tests."""
    if settings.DATABASE_TYPE != "postgresql":
        yield
        return
    
    from app.database import get_db
    from app.db_models import UserDB, MessageGroupDB, MessageGroupMembershipDB
    
    db = next(get_db())
    if db is not None:
        try:
            # Clean existing data first
            db.query(MessageGroupMembershipDB).delete()
            db.query(MessageGroupDB).delete()
            
            # Create test user with ID 999 (matches test_helpers.py)
            existing_user = db.query(UserDB).filter(UserDB.id == 999).first()
            if not existing_user:
                test_user = UserDB(
                    id=999,
                    username="test_admin",
                    password_hash="test_hash",
                    role="admin"
                )
                db.add(test_user)
                db.commit()
                
        except Exception as e:
            print(f"Test user setup error: {e}")
            try:
                db.rollback()
            except:
                pass
    
    yield
    
    # Cleanup after tests
    if settings.DATABASE_TYPE == "postgresql" and db is not None:
        try:
            db.query(MessageGroupMembershipDB).delete()
            db.query(MessageGroupDB).delete()
            db.commit()
        except Exception as e:
            print(f"Test cleanup error: {e}")
            try:
                db.rollback()
            except:
                pass


class TestParentsInSMSGroups:
    """Test that parents can be included in SMS message groups."""

    def test_parents_should_be_available_for_sms_groups(self):
        """Test that parents appear in group member selection alongside youth and leaders"""
        # RED: This test will fail until we update group membership endpoints to include parents
        
        # Create parent, youth, and leader
        parent_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "person_type": "parent",
            "phone": "555-1234"
        }
        youth_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "birth_date": "2005-04-12",
            "phone_number": "555-5678",
            "grade": 10,
            "school_name": "Central High",
            "emergency_contact_name": "Jane Smith",
            "emergency_contact_phone": "555-1234",
            "emergency_contact_relationship": "Parent"
        }
        leader_data = {
            "first_name": "Bob",
            "last_name": "Wilson",
            "role": "Youth Pastor",
            "phone_number": "555-9999"
        }
        
        parent_response = client.post("/parent", json=parent_data)
        youth_response = client.post("/person", json=youth_data)
        leader_response = client.post("/person", json=leader_data)
        
        assert parent_response.status_code in (200, 201)
        assert youth_response.status_code in (200, 201)
        assert leader_response.status_code in (200, 201)
        
        parent_id = parent_response.json()["id"]
        youth_id = youth_response.json()["id"]
        leader_id = leader_response.json()["id"]
        
        # Create SMS group
        group_data = {"name": "Test Group", "description": "Test group for all types"}
        group_response = client.post("/groups", json=group_data)
        
        assert group_response.status_code == 201
        group_id = group_response.json()["id"]
        
        # Try to get available members for group (should include parents)
        # RED: This endpoint probably doesn't exist yet or doesn't include parents
        members_response = client.get(f"/groups/{group_id}/available-members")
        
        assert members_response.status_code == 200
        available_members = members_response.json()
        
        # Should have separate sections for different person types
        assert "parents" in available_members
        assert "youth" in available_members  
        assert "leaders" in available_members
        
        # Our created persons should be in appropriate sections
        parent_ids = [p["id"] for p in available_members["parents"]]
        youth_ids = [y["id"] for y in available_members["youth"]]
        leader_ids = [l["id"] for l in available_members["leaders"]]
        
        assert parent_id in parent_ids
        assert youth_id in youth_ids
        assert leader_id in leader_ids
    
    def test_parents_should_be_addable_to_sms_groups(self):
        """Test that parents can be added as group members"""
        # RED: This will fail until we support adding parents to groups
        
        # Create parent and group
        parent_data = {
            "first_name": "Mary",
            "last_name": "Johnson",
            "person_type": "parent",
            "phone": "555-2468"
        }
        
        parent_response = client.post("/parent", json=parent_data)
        assert parent_response.status_code in (200, 201)
        parent_id = parent_response.json()["id"]
        
        group_data = {"name": "Parent Group", "description": "Group for parents"}
        group_response = client.post("/groups", json=group_data)
        assert group_response.status_code == 201
        group_id = group_response.json()["id"]
        
        # Add parent to group
        membership_data = {"person_id": parent_id}
        add_response = client.post(f"/groups/{group_id}/members", json=membership_data)
        
        assert add_response.status_code == 201
        
        # Verify parent is now a member
        members_response = client.get(f"/groups/{group_id}/members")
        assert members_response.status_code == 200
        
        members = members_response.json()
        member_ids = [m["person_id"] for m in members]
        assert parent_id in member_ids
    
    def test_sms_should_be_sendable_to_groups_with_parents(self):
        """Test sending SMS to groups that include parent members"""
        # RED: This will fail until SMS service supports sending to parents
        
        # Create parent and add to group  
        parent_data = {
            "first_name": "David",
            "last_name": "Wilson", 
            "person_type": "parent",
            "phone": "555-3579"
        }
        
        parent_response = client.post("/parent", json=parent_data)
        assert parent_response.status_code in (200, 201)
        parent_id = parent_response.json()["id"]
        
        group_data = {"name": "Mixed Group", "description": "Group with parents and youth"}
        group_response = client.post("/groups", json=group_data)
        assert group_response.status_code == 201
        group_id = group_response.json()["id"]
        
        # Add parent to group
        membership_data = {"person_id": parent_id}
        add_response = client.post(f"/groups/{group_id}/members", json=membership_data)
        assert add_response.status_code == 201
        
        # Mock SMS service dependency for testing
        from app.routers.sms import get_sms_service
        from app.services.sms_service import SMSService
        from app.main import app
        
        def get_mock_sms_service():
            mock_service = Mock()
            # Mock the get_sms_recipients method which should filter out opted-out users
            mock_service.get_sms_recipients = Mock(return_value=[
                {
                    "id": parent_id,
                    "first_name": "David",
                    "last_name": "Wilson", 
                    "phone_number": "555-3579",
                    "person_type": "parent"
                }
            ])
            # Mock the send_message method used by the SMS router
            mock_service.send_message = Mock(return_value={
                "success": True,
                "message_sid": "SM123456789",
                "status": "sent"
            })
            return mock_service
        
        # Override the SMS service dependency
        original_override = app.dependency_overrides.get(get_sms_service)
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        try:
            # Send SMS to group
            sms_data = {
                "group_id": group_id,
                "message": "Test message for parents too!"
            }
            sms_response = client.post("/api/sms/send-group", json=sms_data)
            
            print(f"SMS Response Status: {sms_response.status_code}")
            print(f"SMS Response Content: {sms_response.content}")
            if sms_response.status_code != 200:
                try:
                    print(f"SMS Response JSON: {sms_response.json()}")
                except:
                    pass
            assert sms_response.status_code == 200
            response_data = sms_response.json()
            assert response_data["success"] is True
            assert response_data["sent_count"] >= 1  # Should include parent
        finally:
            # Restore original dependency override
            if original_override:
                app.dependency_overrides[get_sms_service] = original_override
            else:
                app.dependency_overrides.pop(get_sms_service, None)

    def test_parent_sms_opt_out_should_be_respected(self):
        """Test that parents who opted out don't receive SMS messages"""
        # RED: This will fail until we implement opt-out handling for parents
        
        # Create parent and mark as opted out
        parent_data = {
            "first_name": "Susan",
            "last_name": "Davis",
            "person_type": "parent", 
            "phone": "555-4680",
            "sms_opt_out": True  # Opted out of SMS
        }
        
        parent_response = client.post("/parent", json=parent_data)
        assert parent_response.status_code in (200, 201)
        parent_id = parent_response.json()["id"]
        
        group_data = {"name": "Opt Out Test", "description": "Test opt-out handling"}
        group_response = client.post("/groups", json=group_data)
        assert group_response.status_code == 201
        group_id = group_response.json()["id"]
        
        # Add parent to group  
        membership_data = {"person_id": parent_id}
        add_response = client.post(f"/groups/{group_id}/members", json=membership_data)
        assert add_response.status_code == 201
        
        # Mock SMS service dependency for testing
        from app.routers.sms import get_sms_service
        from app.services.sms_service import SMSService
        from app.main import app
        
        def get_mock_sms_service():
            mock_service = Mock(spec=SMSService)
            # Opted-out parent should not be in recipients
            mock_service.get_sms_recipients = Mock(return_value=[])
            mock_service.send_message = Mock()
            return mock_service
        
        # Override the SMS service dependency
        original_override = app.dependency_overrides.get(get_sms_service)
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        try:
            # Send SMS to group
            sms_data = {
                "group_id": group_id,
                "message": "This should not reach opted-out parent"
            }
            sms_response = client.post("/api/sms/send-group", json=sms_data)
            
            assert sms_response.status_code == 400  # Should fail with no recipients
            response_data = sms_response.json()
            assert "no eligible recipients" in response_data["detail"].lower()
        finally:
            # Restore original dependency override
            if original_override:
                app.dependency_overrides[get_sms_service] = original_override
            else:
                app.dependency_overrides.pop(get_sms_service, None)


class TestParentSMSBackendIntegration:
    """Test backend integration for parent SMS functionality."""
    
    def test_parent_repository_should_support_sms_opt_out(self):
        """Test that parent repository handles SMS opt-out field"""
        # RED: This will fail until we add sms_opt_out support to parent creation
        
        parent_data = {
            "first_name": "Robert",
            "last_name": "Taylor",
            "person_type": "parent",
            "phone": "555-5791", 
            "sms_opt_out": True
        }
        
        response = client.post("/parent", json=parent_data)
        assert response.status_code in (200, 201)
        
        parent = response.json()
        assert parent["sms_opt_out"] is True
        
        # Test retrieving parent maintains opt-out status
        get_response = client.get(f"/parent/{parent['id']}")
        assert get_response.status_code == 200
        retrieved_parent = get_response.json()
        assert retrieved_parent["sms_opt_out"] is True
    
    def test_message_history_should_include_parent_recipients(self):
        """Test that message history shows when messages were sent to parents"""
        # RED: This will fail until message history includes parent information
        
        # Create parent and group
        parent_data = {
            "first_name": "Lisa",
            "last_name": "Anderson", 
            "person_type": "parent",
            "phone": "555-6802"
        }
        
        parent_response = client.post("/parent", json=parent_data)
        assert parent_response.status_code in (200, 201)
        parent_id = parent_response.json()["id"]
        
        group_data = {"name": "History Test", "description": "Test message history"}
        group_response = client.post("/groups", json=group_data)
        assert group_response.status_code == 201
        group_id = group_response.json()["id"]
        
        # Add parent to group
        membership_data = {"person_id": parent_id}
        add_response = client.post(f"/groups/{group_id}/members", json=membership_data)
        assert add_response.status_code == 201
        
        # Mock SMS service dependency for testing
        from app.routers.sms import get_sms_service
        from app.services.sms_service import SMSService
        from app.main import app
        
        def get_mock_sms_service():
            mock_service = Mock(spec=SMSService)
            mock_service.get_sms_recipients = Mock(return_value=[
                {
                    "id": parent_id,
                    "first_name": "Lisa",
                    "last_name": "Anderson",
                    "phone_number": "555-6802",
                    "person_type": "parent"
                }
            ])
            mock_service.send_message = Mock(return_value={
                "success": True,
                "message_sid": "SM987654321"
            })
            return mock_service
        
        # Override the SMS service dependency
        original_override = app.dependency_overrides.get(get_sms_service)
        app.dependency_overrides[get_sms_service] = get_mock_sms_service
        
        try:
            sms_data = {
                "group_id": group_id,
                "message": "Test message for history"
            }
            sms_response = client.post("/api/sms/send-group", json=sms_data)
            assert sms_response.status_code == 200
        finally:
            # Restore original dependency override
            if original_override:
                app.dependency_overrides[get_sms_service] = original_override
            else:
                app.dependency_overrides.pop(get_sms_service, None)
        
        # Check message history
        history_response = client.get(f"/api/sms/history?group_id={group_id}")
        assert history_response.status_code == 200
        
        history_data = history_response.json()
        assert "messages" in history_data
        messages = history_data["messages"]
        assert len(messages) >= 1
        
        # Should show parent as recipient in the message record
        latest_message = messages[0]
        assert latest_message["content"] == "Test message for history"
        assert "recipient_person_id" in latest_message
        assert latest_message["recipient_person_id"] == parent_id