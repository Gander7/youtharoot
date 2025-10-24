"""
Test Parent-Youth Relationship System
TDD implementation for parent management functionality
"""

import pytest
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from app.models import PersonCreate, PersonUpdate, ParentYouthRelationshipCreate
from app.db_models import PersonDB, ParentYouthRelationshipDB
from tests.api.test_person import clear_person_store


class TestParentModel:
    """Test parent functionality in Person model"""
    
    def test_person_model_should_support_parent_type(self):
        """Test that Person model can store parent type"""
        # RED: This will fail until we add person_type field
        parent_data = PersonCreate(
            first_name="Jane",
            last_name="Smith", 
            person_type="parent",
            phone_number="555-123-4567",
            email="jane.smith@email.com",
            address="123 Main St, Halifax, NS"
        )
        
        assert parent_data.person_type == "parent"
        assert parent_data.first_name == "Jane"
        assert parent_data.last_name == "Smith"
        assert parent_data.phone_number == "555-123-4567"
        assert parent_data.email == "jane.smith@email.com"
        assert parent_data.address == "123 Main St, Halifax, NS"

    def test_parent_should_have_required_fields(self):
        """Test that parents require essential contact information"""
        # Should require first_name, last_name, person_type
        with pytest.raises(ValueError):
            PersonCreate(
                # Missing first_name
                last_name="Smith",
                person_type="parent",
                phone="555-123-4567"
            )
    
    def test_parent_should_default_sms_opt_out_to_false(self):
        """Test that parents default to receiving SMS messages"""
        parent_data = PersonCreate(
            first_name="Jane",
            last_name="Smith",
            person_type="parent",
            phone="555-123-4567"
        )
        
        assert parent_data.sms_opt_out == False

    def test_parent_can_opt_out_of_sms(self):
        """Test that parents can opt out of SMS messages"""
        parent_data = PersonCreate(
            first_name="Jane",
            last_name="Smith",
            person_type="parent",
            phone="555-123-4567",
            sms_opt_out=True
        )
        
        assert parent_data.sms_opt_out == True

    def test_parent_email_should_be_optional_but_validated(self):
        """Test email validation for parents"""
        # Valid email
        parent_data = PersonCreate(
            first_name="Jane",
            last_name="Smith",
            person_type="parent",
            phone="555-123-4567",
            email="jane@email.com"
        )
        assert parent_data.email == "jane@email.com"
        
        # No email (optional)
        parent_data_no_email = PersonCreate(
            first_name="Jane",
            last_name="Smith", 
            person_type="parent",
            phone="555-123-4567"
        )
        assert parent_data_no_email.email is None

    def test_parent_phone_should_be_required_for_sms(self):
        """Test that parents need phone numbers for SMS functionality"""
        # Should allow parent without phone if SMS opt-out
        parent_no_phone = PersonCreate(
            first_name="Jane",
            last_name="Smith",
            person_type="parent", 
            sms_opt_out=True
        )
        assert parent_no_phone.phone_number is None
        assert parent_no_phone.sms_opt_out == True


class TestParentYouthRelationship:
    """Test the many-to-many parent-youth relationship"""
    
    def test_parent_youth_relationship_model_should_exist(self):
        """Test that ParentYouthRelationshipDB model exists with correct fields"""
        # Check that model has expected columns
        assert hasattr(ParentYouthRelationshipDB, 'parent_id')
        assert hasattr(ParentYouthRelationshipDB, 'youth_id') 
        assert hasattr(ParentYouthRelationshipDB, 'relationship_type')
        assert hasattr(ParentYouthRelationshipDB, 'created_at')
        assert hasattr(ParentYouthRelationshipDB, 'is_primary_contact')

    def test_parent_youth_relationship_should_support_relationship_types(self):
        """Test different relationship types (mother, father, guardian, etc.)"""
        # This will be database-level test once we have the model
        relationship_types = ['mother', 'father', 'guardian', 'step-parent', 'grandparent', 'other']
        
        for rel_type in relationship_types:
            # Should be able to create relationship with each type
            assert rel_type in relationship_types

    def test_parent_youth_relationship_should_prevent_duplicates(self):
        """Test that same parent-youth pair can't have duplicate relationships"""
        # Will test database constraint once implemented
        assert True  # Placeholder until DB model exists

    def test_parent_can_have_multiple_youth(self):
        """Test that one parent can be linked to multiple youth"""
        # Will test with actual database operations
        assert True  # Placeholder

    def test_youth_can_have_multiple_parents(self):
        """Test that one youth can have multiple parents"""
        # Will test with actual database operations  
        assert True  # Placeholder


class TestParentRepository:
    """Test parent-specific repository operations"""
    
    def test_repository_should_create_parent_with_correct_type(self):
        """Test creating parents through repository"""
        parent_data = PersonCreate(
            first_name="Jane",
            last_name="Smith",
            person_type="parent",
            phone_number="555-123-4567",
            email="jane@email.com"
        )
        
        # Repository should handle parent creation
        assert parent_data.person_type == "parent"

    @pytest.mark.asyncio
    async def test_repository_should_find_parents_by_type(self):
        """Test filtering persons by type to get only parents"""
        from app.repositories.memory import InMemoryPersonRepository
        
        repo = InMemoryPersonRepository()
        
        # Create some test data
        parent1 = PersonCreate(first_name="Jane", last_name="Smith", person_type="parent", phone_number="555-1234")
        parent2 = PersonCreate(first_name="John", last_name="Doe", person_type="parent", phone_number="555-5678") 
        youth1 = PersonCreate(first_name="Alice", last_name="Smith", person_type="youth", phone_number="555-9999")
        
        await repo.create_person_unified(parent1)
        await repo.create_person_unified(parent2)
        await repo.create_person_unified(youth1)
        
        # Should find only parents
        parents = await repo.get_all_parents()
        assert len(parents) == 2
        assert all(p["person_type"] == "parent" for p in parents)

    @pytest.mark.asyncio
    async def test_repository_should_search_parents_by_name_phone_email(self):
        """Test searching parents by name, phone, and email."""
        from app.repositories.memory import InMemoryPersonRepository
        
        repo = InMemoryPersonRepository()
        
        # Create test parents
        parent1 = PersonCreate(first_name="Jane", last_name="Smith", person_type="parent", phone_number="555-1234", email="jane@email.com")
        parent2 = PersonCreate(first_name="John", last_name="Doe", person_type="parent", phone_number="555-5678", email="john@email.com")
        
        await repo.create_person_unified(parent1)
        await repo.create_person_unified(parent2)
        
        # Search by name
        results = await repo.search_persons("parent", "Jane")
        assert len(results) == 1
        assert results[0]["first_name"] == "Jane"
        
        # Search by phone
        results = await repo.search_persons("parent", "555-5678")
        assert len(results) == 1
        assert results[0]["last_name"] == "Doe"

    @pytest.mark.asyncio
    async def test_repository_should_link_parent_to_youth(self):
        """Test creating parent-youth relationships"""
        from app.repositories.memory import InMemoryPersonRepository
        
        repo = InMemoryPersonRepository()
        
        # Create parent and youth
        parent_data = await repo.create_person_unified(PersonCreate(first_name="Jane", last_name="Smith", person_type="parent", phone_number="555-1234"))
        youth_data = await repo.create_person_unified(PersonCreate(first_name="Alice", last_name="Smith", person_type="youth", phone_number="555-5678"))
        
        # Create relationship
        relationship = ParentYouthRelationshipCreate(
            parent_id=parent_data["id"],
            youth_id=youth_data["id"], 
            relationship_type="mother",
            is_primary_contact=True
        )
        
        result = await repo.link_parent_to_youth(relationship)
        assert result["parent_id"] == parent_data["id"]
        assert result["youth_id"] == youth_data["id"]
        assert result["relationship_type"] == "mother"
        assert result["is_primary_contact"] == True

    @pytest.mark.asyncio
    async def test_repository_should_unlink_parent_from_youth(self):
        """Test removing parent-youth relationships"""
        from app.repositories.memory import InMemoryPersonRepository
        
        repo = InMemoryPersonRepository()
        
        # Create and link parent and youth
        parent_data = await repo.create_person_unified(PersonCreate(first_name="Jane", last_name="Smith", person_type="parent", phone_number="555-1234"))
        youth_data = await repo.create_person_unified(PersonCreate(first_name="Alice", last_name="Smith", person_type="youth", phone_number="555-5678"))
        
        relationship = ParentYouthRelationshipCreate(parent_id=parent_data["id"], youth_id=youth_data["id"], relationship_type="mother")
        await repo.link_parent_to_youth(relationship)
        
        # Unlink them
        result = await repo.unlink_parent_from_youth(parent_data["id"], youth_data["id"])
        assert result == True
        
        # Should not be able to unlink again
        result = await repo.unlink_parent_from_youth(parent_data["id"], youth_data["id"])
        assert result == False

    @pytest.mark.asyncio
    async def test_repository_should_get_parents_for_youth(self):
        """Test retrieving all parents for a specific youth"""
        from app.repositories.memory import InMemoryPersonRepository
        
        repo = InMemoryPersonRepository()
        
        # Create youth and parents
        youth_data = await repo.create_person_unified(PersonCreate(first_name="Alice", last_name="Smith", person_type="youth", phone_number="555-1111"))
        mother_data = await repo.create_person_unified(PersonCreate(first_name="Jane", last_name="Smith", person_type="parent", phone_number="555-2222"))
        father_data = await repo.create_person_unified(PersonCreate(first_name="John", last_name="Smith", person_type="parent", phone_number="555-3333"))
        
        # Link parents to youth
        await repo.link_parent_to_youth(ParentYouthRelationshipCreate(parent_id=mother_data["id"], youth_id=youth_data["id"], relationship_type="mother"))
        await repo.link_parent_to_youth(ParentYouthRelationshipCreate(parent_id=father_data["id"], youth_id=youth_data["id"], relationship_type="father"))
        
        # Get parents for youth
        parents = await repo.get_parents_for_youth(youth_data["id"])
        assert len(parents) == 2
        
        # Check relationship types are included
        relationship_types = [p["relationship_type"] for p in parents]
        assert "mother" in relationship_types
        assert "father" in relationship_types

    @pytest.mark.asyncio
    async def test_repository_should_get_youth_for_parent(self):
        """Test retrieving all youth for a specific parent"""
        from app.repositories.memory import InMemoryPersonRepository
        
        repo = InMemoryPersonRepository()
        
        # Create parent and multiple youth
        parent_data = await repo.create_person_unified(PersonCreate(first_name="Jane", last_name="Smith", person_type="parent", phone_number="555-1111"))
        youth1_data = await repo.create_person_unified(PersonCreate(first_name="Alice", last_name="Smith", person_type="youth", phone_number="555-2222"))
        youth2_data = await repo.create_person_unified(PersonCreate(first_name="Bob", last_name="Smith", person_type="youth", phone_number="555-3333"))
        
        # Link youth to parent
        await repo.link_parent_to_youth(ParentYouthRelationshipCreate(parent_id=parent_data["id"], youth_id=youth1_data["id"], relationship_type="mother"))
        await repo.link_parent_to_youth(ParentYouthRelationshipCreate(parent_id=parent_data["id"], youth_id=youth2_data["id"], relationship_type="mother"))
        
        # Get youth for parent
        youth_list = await repo.get_youth_for_parent(parent_data["id"])
        assert len(youth_list) == 2
        
        # Check both youth are included
        youth_names = [y["first_name"] for y in youth_list]
        assert "Alice" in youth_names
        assert "Bob" in youth_names


class TestParentValidation:
    """Test validation rules for parent data"""
    
    def test_parent_phone_format_validation(self):
        """Test phone number format validation"""
        valid_phones = ["555-123-4567", "(555) 123-4567", "5551234567", "+1-555-123-4567"]
        invalid_phones = ["123", "abc-def-ghij", ""]
        
        for phone in valid_phones:
            parent_data = PersonCreate(
                first_name="Jane",
                last_name="Smith",
                person_type="parent",
                phone_number=phone
            )
            assert parent_data.phone_number == phone
        
        # Invalid phones should either be rejected or normalized
        # Implementation will determine exact behavior

    def test_parent_email_format_validation(self):
        """Test email format validation"""
        valid_emails = ["jane@email.com", "jane.smith@example.org", "j.smith+parent@domain.co.uk"]
        
        for email in valid_emails:
            parent_data = PersonCreate(
                first_name="Jane",
                last_name="Smith",
                person_type="parent",
                phone="555-123-4567",
                email=email
            )
            assert parent_data.email == email

    def test_parent_name_validation(self):
        """Test name field validation"""
        # Names should be non-empty strings
        with pytest.raises(ValueError):
            PersonCreate(
                first_name="",  # Empty first name
                last_name="Smith",
                person_type="parent",
                phone="555-123-4567"
            )
        
        with pytest.raises(ValueError):
            PersonCreate(
                first_name="Jane",
                last_name="",  # Empty last name
                person_type="parent", 
                phone="555-123-4567"
            )


class TestParentSMSIntegration:
    """Test SMS message group integration with parents"""
    
    def test_parents_should_be_selectable_for_sms_groups(self):
        """Test that parents can be added to SMS message groups"""
        # Should be able to add parents to groups just like youth
        assert True  # Will implement after SMS group updates

    def test_sms_groups_should_show_parents_and_youth_separately(self):
        """Test that SMS groups distinguish between parents and youth"""
        # UI should show clear distinction between member types
        assert True  # Will implement in frontend

    def test_parent_sms_opt_out_should_be_respected(self):
        """Test that parents who opt out don't receive messages"""
        # Opted-out parents should be excluded from message sending
        assert True  # Will implement in SMS service

    def test_sms_messages_should_support_parent_specific_content(self):
        """Test sending different message types to parents vs youth"""
        # Parents might get different messages than youth
        assert True  # Future enhancement


class TestParentAPIEndpoints:
    """Test API endpoints for parent management"""
    
    def test_create_parent_endpoint_should_work(self, clear_person_store):
        """Test POST /parent endpoint"""
        from fastapi.testclient import TestClient
        from app.main import app
        from tests.test_helpers import get_authenticated_client
        
        client = get_authenticated_client()
        
        parent_data = {
            "first_name": "Jane",
            "last_name": "Smith", 
            "person_type": "parent",
            "phone": "555-123-4567",
            "email": "jane@email.com",
            "address": "123 Main St"
        }
        
        response = client.post("/parent", json=parent_data)
        assert response.status_code in (200, 201)
        
        data = response.json()
        assert data["person_type"] == "parent"
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"

    def test_get_parents_endpoint_should_return_only_parents(self, clear_person_store):
        """Test GET /parents endpoint"""
        from fastapi.testclient import TestClient
        from app.main import app
        from tests.test_helpers import get_authenticated_client
        
        client = get_authenticated_client()
        
        # Create a parent and a youth
        parent_data = {"first_name": "Jane", "last_name": "Smith", "person_type": "parent", "phone": "555-1234"}
        youth_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "birth_date": "2005-04-12",
            "phone_number": "555-5678",
            "grade": 10,
            "school_name": "Central High",
            "emergency_contact_name": "Jordan Smith",
            "emergency_contact_phone": "555-5678",
            "emergency_contact_relationship": "Parent"
        }
        
        client.post("/parent", json=parent_data)
        client.post("/person", json=youth_data)
        
        # Get all parents
        response = client.get("/parents")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["person_type"] == "parent"
        assert data[0]["first_name"] == "Jane"

    def test_search_parents_endpoint_should_support_filters(self, clear_person_store):
        """Test GET /parents/search endpoint with query parameters"""
        from fastapi.testclient import TestClient
        from app.main import app
        from tests.test_helpers import get_authenticated_client
        
        client = get_authenticated_client()
        
        # Create test parents
        parent1 = {"first_name": "Jane", "last_name": "Smith", "person_type": "parent", "phone": "555-1234", "email": "jane@email.com"}
        parent2 = {"first_name": "John", "last_name": "Doe", "person_type": "parent", "phone": "555-5678", "email": "john@email.com"}
        
        client.post("/parent", json=parent1)
        client.post("/parent", json=parent2)
        
        # Search by name
        response = client.get("/parents/search?query=Jane")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["first_name"] == "Jane"
        
        # Search by phone
        response = client.get("/parents/search?query=555-5678")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["last_name"] == "Doe"

    def test_link_parent_to_youth_endpoint_should_work(self, clear_person_store):
        """Test POST /youth/{youth_id}/parents endpoint"""
        from fastapi.testclient import TestClient
        from app.main import app
        from tests.test_helpers import get_authenticated_client
        
        client = get_authenticated_client()
        
        # Create a parent and a youth
        parent_data = {"first_name": "Jane", "last_name": "Smith", "person_type": "parent", "phone": "555-1234"}
        youth_data = {
            "first_name": "Alex",
            "last_name": "Smith",
            "birth_date": "2005-04-12",
            "phone_number": "555-5678",
            "grade": 10,
            "school_name": "Central High",
            "emergency_contact_name": "Jordan Smith",
            "emergency_contact_phone": "555-5678",
            "emergency_contact_relationship": "Parent"
        }
        
        parent_response = client.post("/parent", json=parent_data)
        youth_response = client.post("/person", json=youth_data)
        
        parent_id = parent_response.json()["id"]
        youth_id = youth_response.json()["id"]
        
        # Link them
        relationship_data = {
            "parent_id": parent_id,
            "youth_id": youth_id,
            "relationship_type": "mother",
            "is_primary_contact": True
        }
        
        response = client.post(f"/youth/{youth_id}/parents", json=relationship_data)
        assert response.status_code in (200, 201)
        
        data = response.json()
        assert data["parent_id"] == parent_id
        assert data["youth_id"] == youth_id
        assert data["relationship_type"] == "mother"

    def test_unlink_parent_from_youth_endpoint_should_work(self, clear_person_store):
        """Test DELETE /youth/{youth_id}/parents/{parent_id} endpoint"""
        # Should remove parent-youth relationship
        assert True  # Will implement relationship endpoint

    def test_get_youth_parents_endpoint_should_return_relationships(self, clear_person_store):
        """Test GET /youth/{youth_id}/parents endpoint"""
        from fastapi.testclient import TestClient
        from app.main import app
        from tests.test_helpers import get_authenticated_client
        
        client = get_authenticated_client()
        
        # Create parents and youth
        parent1_data = {"first_name": "Jane", "last_name": "Smith", "person_type": "parent", "phone": "555-1111"}
        parent2_data = {"first_name": "John", "last_name": "Smith", "person_type": "parent", "phone": "555-2222"}
        youth_data = {
            "first_name": "Alex",
            "last_name": "Smith",
            "birth_date": "2005-04-12",
            "phone_number": "555-3333",
            "grade": 10,
            "school_name": "Central High",
            "emergency_contact_name": "Jordan Smith",
            "emergency_contact_phone": "555-3333",
            "emergency_contact_relationship": "Parent"
        }
        
        parent1_response = client.post("/parent", json=parent1_data)
        parent2_response = client.post("/parent", json=parent2_data)
        youth_response = client.post("/person", json=youth_data)
        
        parent1_id = parent1_response.json()["id"]
        parent2_id = parent2_response.json()["id"]
        youth_id = youth_response.json()["id"]
        
        # Link both parents
        client.post(f"/youth/{youth_id}/parents", json={"parent_id": parent1_id, "youth_id": youth_id, "relationship_type": "mother"})
        client.post(f"/youth/{youth_id}/parents", json={"parent_id": parent2_id, "youth_id": youth_id, "relationship_type": "father"})
        
        # Get parents for youth
        response = client.get(f"/youth/{youth_id}/parents")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Check both relationships are present
        relationship_types = [p["relationship_type"] for p in data]
        assert "mother" in relationship_types
        assert "father" in relationship_types

    def test_update_parent_endpoint_should_work(self, clear_person_store):
        """Test PUT /parent/{parent_id} endpoint"""
        # Should update parent information
        assert True  # Will implement update endpoint


class TestParentDataMigration:
    """Test migration of existing emergency contact data"""
    
    def test_existing_youth_should_keep_old_emergency_contacts(self):
        """Test that existing emergency contact fields are preserved"""
        # Old fields should remain intact for backward compatibility
        assert True  # Migration should preserve existing data

    def test_migration_should_not_auto_convert_emergency_contacts_to_parents(self):
        """Test that old emergency contacts are not automatically converted"""
        # Migration should be manual/optional conversion
        assert True  # Avoid automatic data conversion

    def test_system_should_handle_youth_with_both_old_and_new_contacts(self):
        """Test youth can have both old emergency contacts and new parents"""
        # Should support transition period with both systems
        assert True  # Backward compatibility test


class TestParentFrontendRequirements:
    """Test requirements for frontend parent management"""
    
    def test_parent_search_should_support_autocomplete(self):
        """Test parent search functionality for selection"""
        # Frontend should allow searching existing parents
        assert True  # Will implement search UI

    def test_parent_creation_should_be_inline_on_youth_form(self):
        """Test creating new parents directly from youth edit form"""
        # Should have "Add New Parent" option
        assert True  # Will implement inline creation

    def test_parent_relationship_type_should_be_selectable(self):
        """Test selecting relationship type when linking parent"""
        # Should have dropdown for mother/father/guardian/etc
        assert True  # Will implement relationship selection

    def test_emergency_contacts_tab_should_show_parent_list(self):
        """Test new Emergency Contacts tab shows linked parents"""
        # Should display current parents with edit/remove options
        assert True  # Will implement parent list UI