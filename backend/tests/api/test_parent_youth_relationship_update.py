"""
TDD Tests for Parent-Youth Relationship Update API Endpoint

Following TDD methodology - RED Phase:
1. RED: Write failing test first (we are here)
2. GREEN: Write minimal code to pass
3. REFACTOR: Improve while keeping tests green

Test for endpoint:
- PUT /youth/{youth_id}/parents/{parent_id} - Update parent-youth relationship
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


def test_UpdateParentYouthRelationship_ValidData_ReturnsSuccess(client):
    """Test updating parent-youth relationship with valid data"""
    # Arrange: Create a youth
    youth_response = client.post(
        "/person",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": "2010-01-01",
            "grade": 8,
            "school_name": "Test School",
            "person_type": "youth"
        }
    )
    assert youth_response.status_code == 200
    youth_id = youth_response.json()["id"]
    
    # Create a parent
    parent_response = client.post(
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
    assert parent_response.status_code == 200
    parent_id = parent_response.json()["id"]
    
    # Link parent to youth
    link_response = client.post(
        f"/youth/{youth_id}/parents",
        json={
            "parent_id": parent_id,
            "relationship_type": "mother",
            "is_primary_contact": False
        }
    )
    assert link_response.status_code == 200
    
    # Act: Update the relationship
    update_response = client.put(
        f"/youth/{youth_id}/parents/{parent_id}",
        json={
            "relationship_type": "guardian",
            "is_primary_contact": True
        }
    )
    
    # Assert: Verify successful update
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["relationship_type"] == "guardian"
    assert data["is_primary_contact"] is True


def test_UpdateParentYouthRelationship_NonExistentYouth_Returns404(client):
    """Test updating relationship for non-existent youth"""
    # Arrange: Create only a parent
    parent_response = client.post(
        "/parent",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "555-0100",
            "email": "jane@example.com",
            "person_type": "parent"
        }
    )
    parent_id = parent_response.json()["id"]
    
    # Act: Try to update relationship with non-existent youth
    update_response = client.put(
        f"/youth/99999/parents/{parent_id}",
        json={"relationship_type": "mother", "is_primary_contact": True}
    )
    
    # Assert: Should return 404
    assert update_response.status_code == 404


def test_UpdateParentYouthRelationship_NonExistentParent_Returns404(client):
    """Test updating relationship for non-existent parent"""
    # Arrange: Create only a youth
    youth_response = client.post(
        "/person",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": "2010-01-01",
            "grade": 8,
            "school_name": "Test School",
            "person_type": "youth"
        }
    )
    youth_id = youth_response.json()["id"]
    
    # Act: Try to update relationship with non-existent parent
    update_response = client.put(
        f"/youth/{youth_id}/parents/99999",
        json={"relationship_type": "mother", "is_primary_contact": True}
    )
    
    # Assert: Should return 404
    assert update_response.status_code == 404


def test_UpdateParentYouthRelationship_NoExistingRelationship_Returns404(client):
    """Test updating a relationship that doesn't exist"""
    # Arrange: Create youth and parent but don't link them
    youth_response = client.post(
        "/person",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": "2010-01-01",
            "grade": 8,
            "school_name": "Test School",
            "person_type": "youth"
        }
    )
    youth_id = youth_response.json()["id"]
    
    parent_response = client.post(
        "/parent",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "555-0100",
            "email": "jane@example.com",
            "person_type": "parent"
        }
    )
    parent_id = parent_response.json()["id"]
    
    # Act: Try to update non-existent relationship
    update_response = client.put(
        f"/youth/{youth_id}/parents/{parent_id}",
        json={"relationship_type": "mother", "is_primary_contact": True}
    )
    
    # Assert: Should return 404
    assert update_response.status_code == 404
