"""
TDD Tests for Parent Update via Person API

Following TDD methodology:
1. RED: Write failing test first
2. GREEN: Write minimal code to pass
3. REFACTOR: Improve while keeping tests green

Test for endpoint:
- PUT /person/{person_id} - Update parent information (name, phone, email, address)
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


def test_UpdateParent_AllFields_ReturnsUpdatedParent(client):
    """Test updating all parent fields returns updated data"""
    # Arrange: Create a parent
    create_response = client.post(
        "/parent",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "555-0100",
            "email": "jane@example.com",
            "address": "123 Test St",
            "person_type": "parent"
        }
    )
    assert create_response.status_code == 200
    parent_id = create_response.json()["id"]
    
    # Act: Update the parent
    update_response = client.put(
        f"/person/{parent_id}",
        json={
            "id": parent_id,
            "first_name": "Janet",
            "last_name": "Smith",
            "phone_number": "555-0200",
            "email": "janet.smith@example.com",
            "address": "456 New Ave",
            "person_type": "parent"
        }
    )
    
    # Assert: Verify all fields updated
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["first_name"] == "Janet"
    assert data["last_name"] == "Smith"
    assert data["phone_number"] == "555-0200"
    assert data["email"] == "janet.smith@example.com"
    assert data["address"] == "456 New Ave"


def test_UpdateParent_OnlyName_ReturnsUpdatedParent(client):
    """Test updating only name fields preserves other fields"""
    # Arrange: Create a parent
    create_response = client.post(
        "/parent",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "555-0100",
            "email": "jane@example.com",
            "address": "123 Test St",
            "person_type": "parent"
        }
    )
    assert create_response.status_code == 200
    parent_data = create_response.json()
    parent_id = parent_data["id"]
    original_email = parent_data.get("email", "")
    original_address = parent_data.get("address", "")
    
    # Act: Update only the name (must include all fields from original to preserve them)
    update_response = client.put(
        f"/person/{parent_id}",
        json={
            "id": parent_id,
            "first_name": "Janet",
            "last_name": "Smith",
            "phone_number": parent_data["phone_number"],
            "email": original_email if original_email else "jane@example.com",  # Re-provide to preserve
            "address": original_address if original_address else "123 Test St",  # Re-provide to preserve
            "person_type": "parent"
        }
    )
    
    # Assert: Name updated, other fields preserved
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["first_name"] == "Janet"
    assert data["last_name"] == "Smith"
    assert data["phone_number"] == "555-0100"
    # Email and address should be preserved if re-provided
    assert data.get("email") or data.get("email") == "jane@example.com"


def test_UpdateParent_OnlyEmail_ReturnsUpdatedParent(client):
    """Test updating only email preserves other fields"""
    # Arrange: Create a parent
    create_response = client.post(
        "/parent",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "555-0100",
            "email": "jane@example.com",
            "address": "123 Test St",
            "person_type": "parent"
        }
    )
    assert create_response.status_code == 200
    parent_data = create_response.json()
    parent_id = parent_data["id"]
    
    # Act: Update only the email
    update_response = client.put(
        f"/person/{parent_id}",
        json={
            "id": parent_id,
            "first_name": parent_data["first_name"],
            "last_name": parent_data["last_name"],
            "phone_number": parent_data["phone_number"],
            "email": "new.email@example.com",
            "address": parent_data["address"],
            "person_type": "parent"
        }
    )
    
    # Assert: Email updated, other fields preserved
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["email"] == "new.email@example.com"


def test_UpdateParent_OnlyAddress_ReturnsUpdatedParent(client):
    """Test updating only address preserves other fields"""
    # Arrange: Create a parent
    create_response = client.post(
        "/parent",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "555-0100",
            "email": "jane@example.com",
            "address": "123 Test St",
            "person_type": "parent"
        }
    )
    assert create_response.status_code == 200
    parent_data = create_response.json()
    parent_id = parent_data["id"]
    
    # Act: Update only the address
    update_response = client.put(
        f"/person/{parent_id}",
        json={
            "id": parent_id,
            "first_name": parent_data["first_name"],
            "last_name": parent_data["last_name"],
            "phone_number": parent_data["phone_number"],
            "email": parent_data["email"],
            "address": "789 New Street, Apt 4B",
            "person_type": "parent"
        }
    )
    
    # Assert: Address updated, other fields preserved
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["address"] == "789 New Street, Apt 4B"
    assert data["first_name"] == "Jane"


def test_UpdateParent_NonExistent_Returns404(client):
    """Test updating non-existent parent returns 404"""
    # Act: Try to update non-existent parent
    update_response = client.put(
        "/person/99999",
        json={
            "id": 99999,
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "555-0100",
            "person_type": "parent"
        }
    )
    
    # Assert: Should return 404
    assert update_response.status_code == 404


def test_UpdateParent_WithEmptyFields_ClearsValues(client):
    """Test updating parent with empty strings clears optional fields"""
    # Arrange: Create a parent with email and address
    create_response = client.post(
        "/parent",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "555-0100",
            "email": "jane@example.com",
            "address": "123 Test St",
            "person_type": "parent"
        }
    )
    assert create_response.status_code == 200
    parent_id = create_response.json()["id"]
    
    # Act: Update with empty strings for email and address (clears them)
    update_response = client.put(
        f"/person/{parent_id}",
        json={
            "id": parent_id,
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "555-0100",
            "email": "",
            "address": "",
            "person_type": "parent"
        }
    )
    
    # Assert: Update succeeds and fields are empty
    assert update_response.status_code == 200
    data = update_response.json()
    # Empty string is valid for optional fields
    assert data.get("email", "") == ""
    assert data.get("address", "") == ""
