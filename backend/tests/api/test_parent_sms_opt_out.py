"""
Test suite for parent SMS opt-out field functionality.

Tests ensure that:
1. SMS opt-out field can be set when creating a parent
2. SMS opt-out field can be updated when editing a parent
3. SMS opt-out field is returned in GET requests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_helpers import get_authenticated_client


@pytest.fixture
def client():
    """Test client for API calls"""
    return get_authenticated_client()


@pytest.fixture(autouse=True)
def clear_person_store(clean_database):
    """Clear person store for each test."""
    from app.repositories import get_person_repository
    from app.config import settings
    
    if settings.DATABASE_TYPE == "postgresql":
        # Database cleaning is handled by clean_database fixture
        pass
    else:
        # Create a mock session for memory repository
        class MockSession:
            pass
        
        mock_session = MockSession()
        person_repo = get_person_repository(mock_session)
        from app.repositories.memory import InMemoryPersonRepository
        if isinstance(person_repo, InMemoryPersonRepository):
            person_repo.store.clear()


def test_CreateParent_WithSmsOptOut_SavesAndReturnsField(client):
    """
    Test that sms_opt_out field is saved and returned when creating a parent.
    
    Arrange: Prepare parent data with sms_opt_out=True
    Act: POST to /parent endpoint
    Assert: Response includes sms_opt_out=True
    """
    # Arrange
    parent_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "phone_number": "416-555-0102",
        "email": "jane@example.com",
        "address": "456 Oak St",
        "sms_opt_out": True,
        "person_type": "parent"
    }
    
    # Act
    response = client.post("/parent", json=parent_data)
    
    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["first_name"] == "Jane"
    assert response_data["last_name"] == "Smith"
    assert response_data["email"] == "jane@example.com"
    assert response_data["sms_opt_out"] is True


def test_CreateParent_WithoutSmsOptOut_DefaultsToFalse(client):
    """
    Test that sms_opt_out defaults to False when not provided.
    
    Arrange: Prepare parent data without sms_opt_out field
    Act: POST to /parent endpoint
    Assert: Response includes sms_opt_out=False
    """
    # Arrange
    parent_data = {
        "first_name": "Bob",
        "last_name": "Johnson",
        "phone_number": "416-555-0103",
        "email": "bob@example.com",
        "person_type": "parent"
    }
    
    # Act
    response = client.post("/parent", json=parent_data)
    
    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["sms_opt_out"] is False


def test_UpdateParent_ToggleSmsOptOut_SavesAndReturnsUpdatedValue(client):
    """
    Test that sms_opt_out can be toggled when updating a parent.
    
    Arrange: Create parent with sms_opt_out=False, then update to True
    Act: PUT to /person/{id} endpoint
    Assert: Response includes sms_opt_out=True
    """
    # Arrange - Create parent with sms_opt_out=False
    parent_data = {
        "first_name": "Alice",
        "last_name": "Brown",
        "phone_number": "416-555-0104",
        "email": "alice@example.com",
        "sms_opt_out": False,
        "person_type": "parent"
    }
    create_response = client.post("/parent", json=parent_data)
    assert create_response.status_code == 200
    parent = create_response.json()
    parent_id = parent["id"]
    
    # Act - Update to sms_opt_out=True
    update_data = {
        "id": parent_id,
        "first_name": "Alice",
        "last_name": "Brown",
        "phone_number": "416-555-0104",
        "email": "alice@example.com",
        "address": "",
        "sms_opt_out": True,  # Toggle to True
        "person_type": "parent"
    }
    update_response = client.put(f"/person/{parent_id}", json=update_data)
    
    # Assert
    assert update_response.status_code == 200
    updated_parent = update_response.json()
    assert updated_parent["sms_opt_out"] is True


def test_GetParent_ReturnsSmsOptOutField(client):
    """
    Test that GET /person/{id} returns the sms_opt_out field.
    
    Arrange: Create parent with sms_opt_out=True
    Act: GET /person/{id}
    Assert: Response includes sms_opt_out=True
    """
    # Arrange - Create parent
    parent_data = {
        "first_name": "Charlie",
        "last_name": "Davis",
        "phone_number": "416-555-0105",
        "email": "charlie@example.com",
        "sms_opt_out": True,
        "person_type": "parent"
    }
    create_response = client.post("/parent", json=parent_data)
    assert create_response.status_code == 200
    parent = create_response.json()
    parent_id = parent["id"]
    
    # Act
    get_response = client.get(f"/person/{parent_id}")
    
    # Assert
    assert get_response.status_code == 200
    retrieved_parent = get_response.json()
    assert retrieved_parent["id"] == parent_id
    assert retrieved_parent["first_name"] == "Charlie"
    assert retrieved_parent["sms_opt_out"] is True


def test_UpdateParent_WithEmail_BothFieldsSaved(client):
    """
    Test that both email and sms_opt_out are saved together (regression test).
    
    Arrange: Create parent, then update both email and sms_opt_out
    Act: PUT to /person/{id} with both fields
    Assert: Both fields are correctly saved and returned
    """
    # Arrange - Create parent
    parent_data = {
        "first_name": "Diana",
        "last_name": "Evans",
        "phone_number": "416-555-0106",
        "email": "diana@example.com",
        "sms_opt_out": False,
        "person_type": "parent"
    }
    create_response = client.post("/parent", json=parent_data)
    assert create_response.status_code == 200
    parent = create_response.json()
    parent_id = parent["id"]
    
    # Act - Update both email and sms_opt_out
    update_data = {
        "id": parent_id,
        "first_name": "Diana",
        "last_name": "Evans",
        "phone_number": "416-555-0106",
        "email": "diana.evans@example.com",  # Changed email
        "address": "789 Pine St",
        "sms_opt_out": True,  # Changed to True
        "person_type": "parent"
    }
    update_response = client.put(f"/person/{parent_id}", json=update_data)
    
    # Assert
    assert update_response.status_code == 200
    updated_parent = update_response.json()
    assert updated_parent["email"] == "diana.evans@example.com"
    assert updated_parent["sms_opt_out"] is True
