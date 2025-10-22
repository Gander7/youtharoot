"""
TDD Tests for Parent-Youth Relationship API Endpoints

Following TDD methodology:
1. RED: Write failing test first
2. GREEN: Write minimal code to pass 
3. REFACTOR: Improve while keeping tests green

Tests for endpoints:
- GET /youth/{youth_id}/parents - List parents for a youth
- POST /youth/{youth_id}/parents - Add parent to youth  
- DELETE /youth/{youth_id}/parents/{parent_id} - Remove parent from youth
- GET /parents/{parent_id}/youth - List youth for a parent
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.models import PersonCreate, ParentYouthRelationshipCreate
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


@pytest.fixture
def sample_youth_and_parent(client, clear_person_store):
    """Create sample youth and parent for testing relationships"""
    # Create youth
    youth_data = {
        "first_name": "John",
        "last_name": "Doe", 
        "person_type": "youth",
        "phone_number": "555-0001",
        "birth_date": "2005-01-15"
    }
    youth_response = client.post("/person", json=youth_data)
    assert youth_response.status_code == 200
    youth = youth_response.json()
    
    # Create parent
    parent_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "person_type": "parent", 
        "phone": "555-0002",
        "address": "123 Main St"
    }
    parent_response = client.post("/parent", json=parent_data)
    assert parent_response.status_code == 200
    parent = parent_response.json()
    
    return {"youth": youth, "parent": parent}


class TestParentYouthRelationshipAPI:
    """Test parent-youth relationship API endpoints"""
    
    def test_get_youth_parents_empty_list(self, client, sample_youth_and_parent):
        """Test getting parents for youth with no relationships"""
        youth_id = sample_youth_and_parent["youth"]["id"]
        
        # Should return empty list initially
        response = client.get(f"/youth/{youth_id}/parents")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_add_parent_to_youth(self, client, sample_youth_and_parent):
        """Test adding a parent to a youth"""
        youth_id = sample_youth_and_parent["youth"]["id"]
        parent_id = sample_youth_and_parent["parent"]["id"]
        
        # Add parent to youth
        relationship_data = {
            "parent_id": parent_id,
            "relationship_type": "mother",
            "is_primary_contact": True
        }
        
        response = client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        assert response.status_code == 200
        
        relationship = response.json()
        assert relationship["parent_id"] == parent_id
        assert relationship["youth_id"] == youth_id
        assert relationship["relationship_type"] == "mother"
        assert relationship["is_primary_contact"] == True
        
    def test_get_youth_parents_after_adding(self, client, sample_youth_and_parent):
        """Test getting parents for youth after adding relationship"""
        youth_id = sample_youth_and_parent["youth"]["id"]
        parent_id = sample_youth_and_parent["parent"]["id"]
        
        # Add parent to youth first
        relationship_data = {
            "parent_id": parent_id,
            "relationship_type": "father",
            "is_primary_contact": False
        }
        client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        
        # Get parents for youth
        response = client.get(f"/youth/{youth_id}/parents")
        assert response.status_code == 200
        
        parents = response.json()
        assert len(parents) == 1
        
        parent_relationship = parents[0]
        assert parent_relationship["parent"]["first_name"] == "Jane"
        assert parent_relationship["parent"]["last_name"] == "Doe"
        assert parent_relationship["relationship_type"] == "father"
        assert parent_relationship["is_primary_contact"] == False
    
    def test_prevent_duplicate_parent_youth_relationship(self, client, sample_youth_and_parent):
        """Test that duplicate parent-youth relationships are prevented"""
        youth_id = sample_youth_and_parent["youth"]["id"]
        parent_id = sample_youth_and_parent["parent"]["id"]
        
        # Add parent to youth first time
        relationship_data = {
            "parent_id": parent_id,
            "relationship_type": "mother"
        }
        response1 = client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        assert response1.status_code == 200
        
        # Try to add same parent again - should return error
        response2 = client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        assert response2.status_code == 400
        assert "already linked" in response2.json()["detail"].lower()
        
    def test_remove_parent_from_youth(self, client, sample_youth_and_parent):
        """Test removing a parent from a youth"""
        youth_id = sample_youth_and_parent["youth"]["id"] 
        parent_id = sample_youth_and_parent["parent"]["id"]
        
        # Add parent to youth first
        relationship_data = {
            "parent_id": parent_id,
            "relationship_type": "guardian"
        }
        client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        
        # Remove parent from youth
        response = client.delete(f"/youth/{youth_id}/parents/{parent_id}")
        assert response.status_code == 200
        
        # Verify parent is removed
        parents_response = client.get(f"/youth/{youth_id}/parents")
        parents = parents_response.json()
        assert len(parents) == 0
        
    def test_get_youth_for_parent(self, client, sample_youth_and_parent):
        """Test getting youth for a parent"""
        youth_id = sample_youth_and_parent["youth"]["id"]
        parent_id = sample_youth_and_parent["parent"]["id"]
        
        # Add parent to youth first
        relationship_data = {
            "parent_id": parent_id,
            "relationship_type": "step-parent"
        }
        client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        
        # Get youth for parent
        response = client.get(f"/parents/{parent_id}/youth")
        assert response.status_code == 200
        
        youth_relationships = response.json()
        assert len(youth_relationships) == 1
        
        youth_relationship = youth_relationships[0]
        assert youth_relationship["youth"]["first_name"] == "John"
        assert youth_relationship["youth"]["last_name"] == "Doe"
        assert youth_relationship["relationship_type"] == "step-parent"
        
    def test_invalid_youth_id_returns_404(self, client):
        """Test that invalid youth ID returns 404"""
        response = client.get("/youth/99999/parents")
        assert response.status_code == 404
        
    def test_invalid_parent_id_returns_404(self, client):
        """Test that invalid parent ID returns 404"""
        response = client.get("/parents/99999/youth") 
        assert response.status_code == 404
        
    def test_add_parent_with_invalid_youth_returns_404(self, client, sample_youth_and_parent):
        """Test adding parent to invalid youth returns 404"""
        parent_id = sample_youth_and_parent["parent"]["id"]
        
        relationship_data = {
            "parent_id": parent_id,
            "relationship_type": "mother"
        }
        
        response = client.post("/youth/99999/parents", json=relationship_data)
        assert response.status_code == 404
        
    def test_add_invalid_parent_to_youth_returns_404(self, client, sample_youth_and_parent):
        """Test adding invalid parent to youth returns 404"""
        youth_id = sample_youth_and_parent["youth"]["id"]
        
        relationship_data = {
            "parent_id": 99999,
            "relationship_type": "father"
        }
        
        response = client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        assert response.status_code == 404


class TestParentYouthRelationshipValidation:
    """Test validation rules for parent-youth relationships"""
    
    def test_relationship_type_validation(self, client, sample_youth_and_parent):
        """Test that invalid relationship types are rejected"""
        youth_id = sample_youth_and_parent["youth"]["id"]
        parent_id = sample_youth_and_parent["parent"]["id"]
        
        # Try invalid relationship type
        relationship_data = {
            "parent_id": parent_id,
            "relationship_type": "invalid_type"
        }
        
        response = client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        assert response.status_code == 422
        
    def test_only_parents_can_be_linked_to_youth(self, client, sample_youth_and_parent):
        """Test that only persons with person_type='parent' can be linked to youth"""
        youth_id = sample_youth_and_parent["youth"]["id"]
        
        # Create a leader (not parent)
        leader_data = {
            "first_name": "Bob",
            "last_name": "Leader",
            "person_type": "leader",
            "phone_number": "555-0003",
            "role": "Assistant Leader"
        }
        leader_response = client.post("/person", json=leader_data)
        leader_id = leader_response.json()["id"]
        
        # Try to link leader as parent - should fail
        relationship_data = {
            "parent_id": leader_id,
            "relationship_type": "guardian"
        }
        
        response = client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        assert response.status_code == 400
        assert "parent" in response.json()["detail"].lower()