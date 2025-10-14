"""
Test cases for Group Management API endpoints following TDD methodology.
Testing CRUD operations for message groups and membership management.

RED-GREEN-REFACTOR cycle:
1. RED: Write failing tests first
2. GREEN: Write minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from tests.test_helpers import get_authenticated_client
from app.repositories.memory import InMemoryPersonRepository

# Use authenticated client for all tests
client = get_authenticated_client()
GROUPS_ENDPOINT = "/groups"


@pytest.fixture(autouse=True)
def clear_stores():
    """Clear all stores for each test."""
    from app.repositories import get_person_repository, get_group_repository, get_user_repository
    from app.config import settings
    
    if settings.DATABASE_TYPE == "postgresql":
        # For PostgreSQL integration tests, ensure test users exist for both possible IDs
        from app.database import get_db
        from app.db_models import UserDB, MessageGroupDB, MessageGroupMembershipDB
        
        db = next(get_db())
        if db is not None:
            try:
                # Clear groups and memberships first to avoid foreign key issues
                db.query(MessageGroupMembershipDB).delete()
                db.query(MessageGroupDB).delete()
                
                # Create test users for both ID 1 and ID 999 to handle different test environments
                test_users = [
                    {"id": 1, "username": "test_admin_1"},
                    {"id": 999, "username": "test_admin_999"}
                ]
                
                for user_data in test_users:
                    existing_user = db.query(UserDB).filter(UserDB.id == user_data["id"]).first()
                    if not existing_user:
                        test_user_db = UserDB(
                            id=user_data["id"],
                            username=user_data["username"],
                            password_hash="test_hash",
                            role="admin"
                        )
                        db.add(test_user_db)
                
                db.commit()
            except Exception as e:
                # If user creation fails, try to rollback
                try:
                    db.rollback()
                except:
                    pass
    else:
        # For memory tests, clear the stores
        class MockSession:
            pass
        
        mock_session = MockSession()
        person_repo = get_person_repository(mock_session)
        group_repo = get_group_repository(mock_session)
        
        if isinstance(person_repo, InMemoryPersonRepository):
            person_repo.store.clear()
        
        # Clear group stores
        if hasattr(group_repo, 'groups_store'):
            group_repo.groups_store.clear()
            group_repo.memberships_store.clear()
            group_repo.next_group_id = 1
            group_repo.next_membership_id = 1


def valid_group_payload():
    """Helper function to create valid group data."""
    return {
        "name": "Youth Team",
        "description": "All youth members for general announcements",
        "is_active": True
    }


def valid_member_payload():
    """Helper function to create valid membership data."""
    return {
        "person_id": 1
    }


class TestGroupManagementAPI:
    """Test suite for Group Management API endpoints using TDD approach."""
    
    # RED Phase: Write failing tests first
    
    def test_create_message_group_should_return_created_group(self):
        """Test creating a new message group."""
        group_data = valid_group_payload()
        
        response = client.post(GROUPS_ENDPOINT, json=group_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Youth Team"
        assert data["description"] == "All youth members for general announcements"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_group_with_duplicate_name_should_fail(self):
        """Test that creating a group with duplicate name fails."""
        group_data = valid_group_payload()
        
        # First, create a group
        response1 = client.post(GROUPS_ENDPOINT, json=group_data)
        assert response1.status_code == 201
        
        # Try to create another group with same name
        duplicate_data = {
            "name": "Youth Team", 
            "description": "Duplicate group"
        }
        response2 = client.post(GROUPS_ENDPOINT, json=duplicate_data)
        
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    def test_get_all_groups_should_return_user_groups(self):
        """Test retrieving all groups created by current user."""
        # Create some test groups
        group1_data = {"name": "Youth Team", "description": "Youth group"}
        group2_data = {"name": "Leaders", "description": "Leadership team"}
        
        client.post(GROUPS_ENDPOINT, json=group1_data)
        client.post(GROUPS_ENDPOINT, json=group2_data)
        
        response = client.get(GROUPS_ENDPOINT)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        group_names = [group["name"] for group in data]
        assert "Youth Team" in group_names
        assert "Leaders" in group_names

    def test_get_group_by_id_should_return_group_details(self):
        """Test retrieving a specific group by ID."""
        group_data = valid_group_payload()
        
        # Create group
        create_response = client.post(GROUPS_ENDPOINT, json=group_data)
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]
        
        # Get group by ID
        response = client.get(f"{GROUPS_ENDPOINT}/{group_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == group_id
        assert data["name"] == "Youth Team"
        assert data["description"] == "All youth members for general announcements"

    def test_get_nonexistent_group_should_return_404(self):
        """Test retrieving a group that doesn't exist."""
        response = client.get(f"{GROUPS_ENDPOINT}/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_group_should_modify_group_details(self):
        """Test updating an existing group."""
        group_data = valid_group_payload()
        
        # Create group
        create_response = client.post(GROUPS_ENDPOINT, json=group_data)
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]
        
        # Update group
        update_data = {
            "name": "Youth Ministry",
            "description": "Updated youth ministry group"
        }
        
        response = client.put(f"{GROUPS_ENDPOINT}/{group_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Youth Ministry"
        assert data["description"] == "Updated youth ministry group"

    def test_delete_group_should_remove_group(self):
        """Test deleting a group."""
        group_data = valid_group_payload()
        
        # Create group
        create_response = client.post(GROUPS_ENDPOINT, json=group_data)
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]
        
        # Delete group
        response = client.delete(f"{GROUPS_ENDPOINT}/{group_id}")
        
        assert response.status_code == 204
        
        # Verify group is deleted
        get_response = client.get(f"{GROUPS_ENDPOINT}/{group_id}")
        assert get_response.status_code == 404

    def test_add_member_to_group_should_create_membership(self):
        """Test adding a person to a group."""
        # First create a person
        person_data = {
            "first_name": "Alex",
            "last_name": "Johnson",
            "birth_date": "2005-04-12",
            "phone_number": "+14165551234"
        }
        person_response = client.post("/person", json=person_data)
        assert person_response.status_code in (200, 201)
        person_id = person_response.json()["id"]
        
        # Create group
        group_data = valid_group_payload()
        group_response = client.post(GROUPS_ENDPOINT, json=group_data)
        assert group_response.status_code == 201
        group_id = group_response.json()["id"]
        
        # Add member to group
        member_data = {"person_id": person_id}
        
        response = client.post(f"{GROUPS_ENDPOINT}/{group_id}/members", json=member_data)
        
        # Debug output if test fails
        if response.status_code != 201:
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["group_id"] == group_id
        assert data["person_id"] == person_id

    def test_add_duplicate_member_should_fail(self):
        """Test that adding the same person twice to a group fails."""
        # Create person
        person_data = {
            "first_name": "Alex",
            "last_name": "Johnson", 
            "birth_date": "2005-04-12"
        }
        person_response = client.post("/person", json=person_data)
        person_id = person_response.json()["id"]
        
        # Create group
        group_data = valid_group_payload()
        group_response = client.post(GROUPS_ENDPOINT, json=group_data)
        group_id = group_response.json()["id"]
        
        # Add member first time
        member_data = {"person_id": person_id}
        response1 = client.post(f"{GROUPS_ENDPOINT}/{group_id}/members", json=member_data)
        assert response1.status_code == 201
        
        # Try to add same member again
        response2 = client.post(f"{GROUPS_ENDPOINT}/{group_id}/members", json=member_data)
        
        assert response2.status_code == 400
        assert "already a member" in response2.json()["detail"].lower()

    def test_get_group_members_should_return_member_list(self):
        """Test retrieving all members of a group."""
        # Create persons
        person1_data = {"first_name": "Alex", "last_name": "Johnson", "birth_date": "2005-04-12"}
        person2_data = {"first_name": "Sarah", "last_name": "Wilson", "birth_date": "2006-03-15"}
        
        person1_response = client.post("/person", json=person1_data)
        person2_response = client.post("/person", json=person2_data)
        
        person1_id = person1_response.json()["id"]
        person2_id = person2_response.json()["id"]
        
        # Create group
        group_data = valid_group_payload()
        group_response = client.post(GROUPS_ENDPOINT, json=group_data)
        group_id = group_response.json()["id"]
        
        # Add members
        client.post(f"{GROUPS_ENDPOINT}/{group_id}/members", json={"person_id": person1_id})
        client.post(f"{GROUPS_ENDPOINT}/{group_id}/members", json={"person_id": person2_id})
        
        # Get members
        response = client.get(f"{GROUPS_ENDPOINT}/{group_id}/members")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        member_ids = [member["person_id"] for member in data]
        assert person1_id in member_ids
        assert person2_id in member_ids

    def test_remove_member_from_group_should_delete_membership(self):
        """Test removing a person from a group."""
        # Create person
        person_data = {"first_name": "Alex", "last_name": "Johnson", "birth_date": "2005-04-12"}
        person_response = client.post("/person", json=person_data)
        person_id = person_response.json()["id"]
        
        # Create group
        group_data = valid_group_payload()
        group_response = client.post(GROUPS_ENDPOINT, json=group_data)
        group_id = group_response.json()["id"]
        
        # Add member
        client.post(f"{GROUPS_ENDPOINT}/{group_id}/members", json={"person_id": person_id})
        
        # Remove member
        response = client.delete(f"{GROUPS_ENDPOINT}/{group_id}/members/{person_id}")
        
        assert response.status_code == 204
        
        # Verify membership is removed
        members_response = client.get(f"{GROUPS_ENDPOINT}/{group_id}/members")
        members = members_response.json()
        assert len(members) == 0

    def test_add_multiple_members_should_create_bulk_memberships(self):
        """Test adding multiple people to a group at once."""
        # Create persons
        person1_response = client.post("/person", json={"first_name": "Alex", "last_name": "Johnson", "birth_date": "2005-04-12"})
        person2_response = client.post("/person", json={"first_name": "Sarah", "last_name": "Wilson", "birth_date": "2006-03-15"})
        person3_response = client.post("/person", json={"first_name": "Mike", "last_name": "Brown", "birth_date": "1990-01-01"})
        
        person_ids = [
            person1_response.json()["id"],
            person2_response.json()["id"], 
            person3_response.json()["id"]
        ]
        
        # Create group
        group_data = valid_group_payload()
        group_response = client.post(GROUPS_ENDPOINT, json=group_data)
        group_id = group_response.json()["id"]
        
        # Add multiple members
        members_data = {"person_ids": person_ids}
        
        response = client.post(f"{GROUPS_ENDPOINT}/{group_id}/members/bulk", json=members_data)
        
        # Debug output if test fails
        if response.status_code != 201:
            print(f"DEBUG: Bulk response status: {response.status_code}")
            print(f"DEBUG: Bulk response body: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        assert data["added_count"] == 3


class TestGroupValidation:
    """Test input validation for group management."""

    def test_create_group_with_empty_name_should_fail(self):
        """Test that group name is required."""
        group_data = {"name": "", "description": "Test group"}
        
        response = client.post(GROUPS_ENDPOINT, json=group_data)
        
        assert response.status_code == 422

    def test_create_group_with_long_name_should_fail(self):
        """Test that group name has length limit."""
        group_data = {
            "name": "A" * 101,  # Exceeds 100 character limit
            "description": "Test group"
        }
        
        response = client.post(GROUPS_ENDPOINT, json=group_data)
        
        assert response.status_code == 422

    def test_add_nonexistent_person_to_group_should_fail(self):
        """Test adding a person that doesn't exist to a group."""
        # Create group
        group_data = valid_group_payload()
        group_response = client.post(GROUPS_ENDPOINT, json=group_data)
        group_id = group_response.json()["id"]
        
        # Try to add non-existent person
        member_data = {"person_id": 99999}
        
        response = client.post(f"{GROUPS_ENDPOINT}/{group_id}/members", json=member_data)
        
        assert response.status_code == 404
        assert "person not found" in response.json()["detail"].lower()