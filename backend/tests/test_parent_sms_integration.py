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
from app.repositories.memory import InMemoryPersonRepository, InMemoryMessageGroupRepository

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


@pytest.fixture(autouse=True)
def clear_stores():
    """Clear all stores for each test."""
    # Clear memory stores
    if hasattr(InMemoryPersonRepository, '_store'):
        InMemoryPersonRepository._store.clear()
    if hasattr(InMemoryPersonRepository, '_next_id'):
        InMemoryPersonRepository._next_id = 1
    
    # Clear relationships
    InMemoryPersonRepository.relationships = {}
    
    # Clear message group stores
    if hasattr(InMemoryMessageGroupRepository, 'groups_store'):
        InMemoryMessageGroupRepository.groups_store = {}
    if hasattr(InMemoryMessageGroupRepository, 'memberships_store'):
        InMemoryMessageGroupRepository.memberships_store = {}
    if hasattr(InMemoryMessageGroupRepository, 'next_group_id'):
        InMemoryMessageGroupRepository.next_group_id = 1
    if hasattr(InMemoryMessageGroupRepository, 'next_membership_id'):
        InMemoryMessageGroupRepository.next_membership_id = 1


class TestParentsInSMSGroups:
    def clear_stores():
        """Clear all stores for each test."""
        # Clear person store
        if hasattr(InMemoryPersonRepository, '_store'):
            InMemoryPersonRepository._store.clear()
        if hasattr(InMemoryPersonRepository, '_next_id'):
            InMemoryPersonRepository._next_id = 1
            
        # Clear relationships store
        InMemoryPersonRepository.relationships = {}
        
        # Clear group stores
        if hasattr(InMemoryMessageGroupRepository, 'groups_store'):
            InMemoryMessageGroupRepository.groups_store = {}
        if hasattr(InMemoryMessageGroupRepository, 'memberships_store'):
            InMemoryMessageGroupRepository.memberships_store = {}
        if hasattr(InMemoryMessageGroupRepository, 'next_group_id'):
            InMemoryMessageGroupRepository.next_group_id = 1
        if hasattr(InMemoryMessageGroupRepository, 'next_membership_id'):
            InMemoryMessageGroupRepository.next_membership_id = 1


class TestParentsInSMSGroups:
    """Test parents can be added to SMS groups and receive messages"""
    
    def test_parents_should_be_available_for_sms_groups(self):
        """Test that parents appear in group member selection alongside youth and leaders"""
        # RED: This test will fail until we update group membership endpoints to include parents
        client = get_authenticated_client()
        
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
        assert group_response.status_code in (200, 201)
        group_id = group_response.json()["id"]
        
        # Add parent, youth, and leader to group
        parent_membership = {"person_id": parent_id}
        youth_membership = {"person_id": youth_id}
        leader_membership = {"person_id": leader_id}
        
        parent_add_response = client.post(f"/groups/{group_id}/members", json=parent_membership)
        youth_add_response = client.post(f"/groups/{group_id}/members", json=youth_membership)
        leader_add_response = client.post(f"/groups/{group_id}/members", json=leader_membership)
        
        assert parent_add_response.status_code in (200, 201)
        assert youth_add_response.status_code in (200, 201)
        assert leader_add_response.status_code in (200, 201)
        
        # Get group members and verify parent is included
        members_response = client.get(f"/groups/{group_id}/members")
        assert members_response.status_code == 200
        
        members = members_response.json()
        assert len(members) == 3
        
        # Verify all person types are present
        person_types = [member["person"]["person_type"] for member in members]
        assert "parent" in person_types
        assert "youth" in person_types
        assert "leader" in person_types
    
    def test_parents_should_receive_sms_messages_when_in_group(self):
        """Test that parents receive SMS messages when they're part of a group"""
        # RED: This test will fail until SMS sending includes parents
        client = get_authenticated_client()
        
        # Create parent with valid phone
        parent_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "person_type": "parent", 
            "phone": "555-1234"
        }
        parent_response = client.post("/parent", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        # Create group and add parent
        group_data = {"name": "Parent Group", "description": "Group with parents"}
        group_response = client.post("/groups", json=group_data)
        group_id = group_response.json()["id"]
        
        membership_data = {"person_id": parent_id}
        client.post(f"/groups/{group_id}/members", json=membership_data)
        
        # Mock SMS service to track sends
        with patch('app.routers.sms.SMSService') as mock_sms_service:
            mock_service = Mock()
            mock_service.send_sms = AsyncMock(return_value={
                "success": True,
                "message_sid": "SM123456",
                "status": "queued"
            })
            mock_sms_service.return_value = mock_service
            
            # Send group SMS
            sms_data = {
                "group_id": group_id,
                "message": "Test message to parents"
            }
            
            response = client.post("/api/sms/send-group", json=sms_data)
            
            # Should succeed and include parent in recipients
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["sent_count"] >= 1
            
            # Verify SMS service was called with parent's phone
            assert mock_service.send_sms.called
            calls = mock_service.send_sms.call_args_list
            phone_numbers = [call[1]["phone_number"] for call in calls if len(call) > 1]
            assert "555-1234" in phone_numbers
    
    def test_parents_should_respect_sms_opt_out_setting(self):
        """Test that parents who opt out of SMS don't receive messages"""
        # RED: This test will fail until SMS opt-out filtering works for parents
        client = get_authenticated_client()
        
        # Create parent with SMS opt-out enabled
        parent_data = {
            "first_name": "Jane", 
            "last_name": "Smith",
            "person_type": "parent",
            "phone": "555-1234",
            "sms_opt_out": True
        }
        parent_response = client.post("/parent", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        # Create group and add opted-out parent
        group_data = {"name": "Parent Group", "description": "Group with opted-out parent"}
        group_response = client.post("/groups", json=group_data)
        group_id = group_response.json()["id"]
        
        membership_data = {"person_id": parent_id}
        client.post(f"/groups/{group_id}/members", json=membership_data)
        
        # Mock SMS service
        with patch('app.routers.sms.SMSService') as mock_sms_service:
            mock_service = Mock()
            mock_service.send_sms = AsyncMock()
            mock_sms_service.return_value = mock_service
            
            # Send group SMS
            sms_data = {
                "group_id": group_id,
                "message": "Test message that should be skipped"
            }
            
            response = client.post("/api/sms/send-group", json=sms_data)
            
            # Should succeed but skip opted-out parent
            assert response.status_code == 200
            result = response.json()
            assert result["skipped_count"] >= 1
            assert result["sent_count"] == 0
            
            # Verify SMS service was not called for opted-out parent
            assert not mock_service.send_sms.called


class TestParentSMSMessageHistory:
    """Test message history properly displays parent recipients"""
    
    def test_message_history_should_show_parent_recipients(self):
        """Test that message history includes parent recipients in details"""
        # RED: This test will fail until message history properly shows parents
        client = get_authenticated_client()
        
        # Create parent and group
        parent_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "person_type": "parent",
            "phone": "555-1234"
        }
        parent_response = client.post("/parent", json=parent_data)
        parent_id = parent_response.json()["id"]
        
        group_data = {"name": "Parent Group"}
        group_response = client.post("/groups", json=group_data)
        group_id = group_response.json()["id"]
        
        # Add parent to group
        membership_data = {"person_id": parent_id}
        client.post(f"/groups/{group_id}/members", json=membership_data)
        
        # Mock successful SMS send
        with patch('app.routers.sms.SMSService') as mock_sms_service:
            mock_service = Mock()
            mock_service.send_sms = AsyncMock(return_value={
                "success": True,
                "message_sid": "SM123456", 
                "status": "delivered"
            })
            mock_sms_service.return_value = mock_service
            
            # Send message to group
            sms_data = {
                "group_id": group_id,
                "message": "Test message to parent"
            }
            client.post("/api/sms/send-group", json=sms_data)
        
        # Get message history and verify parent is shown
        history_response = client.get("/api/sms/history")
        assert history_response.status_code == 200
        
        history = history_response.json()
        messages = history["messages"]
        
        # Should have at least one message
        assert len(messages) > 0
        
        # Find our message and check if parent info is preserved
        test_message = None
        for msg in messages:
            if msg.get("content") == "Test message to parent":
                test_message = msg
                break
        
        assert test_message is not None
        # Message should indicate it was sent to parent group
        assert test_message.get("group_id") == group_id


class TestParentSMSBackendIntegration:
    """Test backend properly handles parents in SMS operations"""
    
    @pytest.mark.asyncio
    async def test_get_group_members_with_person_should_include_parents(self):
        """Test repository method includes parent details correctly"""
        # RED: This test will fail until repository methods handle parents properly
        from app.repositories.memory import InMemoryPersonRepository, InMemoryMessageGroupRepository
        from app.models import PersonCreate
        from app.messaging_models import MessageGroupCreate
        
        person_repo = InMemoryPersonRepository()
        group_repo = InMemoryMessageGroupRepository()
        
        # Create parent
        parent = PersonCreate(
            first_name="Jane",
            last_name="Smith", 
            person_type="parent",
            phone="555-1234"
        )
        parent_result = await person_repo.create_person_unified(parent)
        parent_id = parent_result["id"]
        
        # Create group
        group = MessageGroupCreate(name="Test Group")
        group_result = await group_repo.create_group(group, created_by=1)
        group_id = group_result.id
        
        # Add parent to group
        await group_repo.add_member(group_id, parent_id, added_by=1)
        
        # Get group members with person details
        members = await group_repo.get_group_members_with_person(group_id)
        
        assert len(members) == 1
        member = members[0]
        assert member.person.person_type == "parent"
        assert member.person.first_name == "Jane"
        assert member.person.last_name == "Smith"
        assert member.person.phone_number == "555-1234"
    
    @pytest.mark.asyncio
    async def test_sms_service_should_get_parent_phone_numbers(self):
        """Test that SMS sending gets correct phone numbers for parents"""
        # This tests the data flow from group membership to SMS sending
        from app.repositories.memory import InMemoryPersonRepository, InMemoryMessageGroupRepository
        from app.models import PersonCreate
        from app.messaging_models import MessageGroupCreate
        
        person_repo = InMemoryPersonRepository()
        group_repo = InMemoryMessageGroupRepository()
        
        # Create parent with phone
        parent = PersonCreate(
            first_name="Jane",
            last_name="Smith",
            person_type="parent", 
            phone="555-1234"
        )
        parent_result = await person_repo.create_person_unified(parent)
        
        # Create group and add parent
        group = MessageGroupCreate(name="Parent Group")
        group_result = await group_repo.create_group(group, created_by=1)
        await group_repo.add_member(group_result.id, parent_result["id"], added_by=1)
        
        # Get members for SMS sending
        members = await group_repo.get_group_members_with_person(group_result.id)
        
        # Should have parent member with correct phone
        assert len(members) == 1
        parent_member = members[0]
        assert parent_member.person.phone_number == "555-1234"
        assert parent_member.person.person_type == "parent"
        assert parent_member.person.sms_opt_out is False  # Default should be False
