"""
Test to verify that updating event details preserves attendance data.
This addresses the bug where updating an event's end time caused 
checked-in people to lose their check-in status.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_user
from app.models import User

# Module-level repository storage for test isolation
_attendance_test_repositories = None

@pytest.fixture(scope="module", autouse=True)
def setup_attendance_test_environment():
    """Setup isolated test environment for attendance tests only"""
    global _attendance_test_repositories
    
    # Check if we're using PostgreSQL or memory
    from app.config import settings
    
    if settings.DATABASE_TYPE == "postgresql":
        # For PostgreSQL, use the normal repository system with database cleaning
        _attendance_test_repositories = None
    else:
        # Create singleton repositories for this test module (memory mode)
        from app.repositories.memory import InMemoryPersonRepository, InMemoryEventRepository
        _attendance_test_repositories = {
            "person": InMemoryPersonRepository(),
            "event": InMemoryEventRepository()
        }
    
    # Mock authentication for testing
    async def get_test_user():
        return User(id=1, username="test_user", password_hash="hashed", role="admin")

    # Mock repository access to use our test singletons (only for memory mode)
    def mock_get_repositories(db_session):
        """Return test singleton repositories"""
        if _attendance_test_repositories:
            return _attendance_test_repositories
        else:
            # Use normal repositories for PostgreSQL mode
            from app.repositories import get_person_repository, get_event_repository
            return {
                "person": get_person_repository(db_session),
                "event": get_event_repository(db_session)
            }

    # Store original functions to restore later
    from app.routers import attendance, event, person
    original_functions = {
        'attendance_get_repos': getattr(attendance, 'get_repositories', None),
        'event_get_repos': getattr(event, 'get_repositories', None),
        'person_get_repos': getattr(person, 'get_repositories', None),
        'auth_override': app.dependency_overrides.get(get_current_user, None)
    }
    
    # Apply overrides for this test module
    app.dependency_overrides[get_current_user] = get_test_user
    
    # Only override repositories in memory mode
    if _attendance_test_repositories:
        attendance.get_repositories = mock_get_repositories
        event.get_repositories = mock_get_repositories  
        person.get_repositories = mock_get_repositories
    
    print("✅ Setup isolated attendance test environment")
    
    yield
    
    # Cleanup - restore original functions
    if original_functions['auth_override']:
        app.dependency_overrides[get_current_user] = original_functions['auth_override']
    elif get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
        
    # Only restore repository overrides if we set them (memory mode)
    if _attendance_test_repositories:
        if original_functions['attendance_get_repos']:
            attendance.get_repositories = original_functions['attendance_get_repos']
        if original_functions['event_get_repos']:
            event.get_repositories = original_functions['event_get_repos']
        if original_functions['person_get_repos']:
            person.get_repositories = original_functions['person_get_repos']
    
    print("✅ Cleaned up isolated attendance test environment")

@pytest.fixture
def client(clean_database):
    """Test client for attendance tests"""
    from tests.test_helpers import get_authenticated_client
    return get_authenticated_client()

class TestEventUpdatePreservesAttendance:
    """Test that event updates don't wipe out attendance data"""
    
    def test_update_event_end_time_preserves_attendance(self, client):
        """Test the specific bug: updating event end time should not remove checked-in people"""
        
        from app.config import settings
        
        # Create a person regardless of database type
        person_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "555-0123",
            "birth_date": "2005-01-01",
            "grade": 10,
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "555-0124",
            "emergency_contact_relationship": "Parent"
        }

        person_response = client.post("/person", json=person_data)
        assert person_response.status_code in (200, 201)
        person = person_response.json()
        person_id = person["id"]        # 1. Create an event
        event_data = {
            "date": "2025-10-14",
            "name": "Youth Group Meeting",
            "desc": "Weekly youth meeting",
            "start_time": "19:00",
            "end_time": "21:00",
            "location": "Main Hall"
        }

        response = client.post("/event", json=event_data)
        print(f"Event creation response status: {response.status_code}")
        print(f"Event creation response: {response.content}")
        assert response.status_code == 200
        event = response.json()
        event_id = event["id"]
        print(f"Created event with ID: {event_id}")
        
        # 2. Check in the person
        checkin_data = {
            "person_id": person_id
        }

        response = client.post(f"/event/{event_id}/checkin", json=checkin_data)
        print(f"Checkin response status: {response.status_code}")
        print(f"Checkin response content: {response.content}")
        assert response.status_code == 200
        
        # 4. Verify attendance was recorded
        response = client.get(f"/event/{event_id}/attendance")
        assert response.status_code == 200
        attendance_before = response.json()
        assert len(attendance_before) == 1
        assert attendance_before[0]["person_id"] == person_id
        assert attendance_before[0]["first_name"] == "John"
        assert attendance_before[0]["last_name"] == "Doe"
        assert attendance_before[0]["check_in"] is not None
        assert attendance_before[0]["check_out"] is None
        
        # 5. Update the event end time (reproduces the bug)
        updated_event_data = {
            "date": "2025-10-14",
            "name": "Youth Group Meeting",
            "desc": "Weekly youth meeting", 
            "start_time": "19:00",
            "end_time": "21:30",  # Changed end time
            "location": "Main Hall"
        }
        
        response = client.put(f"/event/{event_id}", json=updated_event_data)
        assert response.status_code == 200
        
        # 6. Verify attendance is STILL there (the bug fix)
        response = client.get(f"/event/{event_id}/attendance")
        assert response.status_code == 200
        attendance_after = response.json()
        
        # The bug was that attendance would be empty after update
        assert len(attendance_after) == 1, f"Expected 1 person still checked in, got {len(attendance_after)}"
        assert attendance_after[0]["person_id"] == person_id
        assert attendance_after[0]["first_name"] == "John"
        assert attendance_after[0]["last_name"] == "Doe"
        assert attendance_after[0]["check_in"] is not None
        assert attendance_after[0]["check_out"] is None
        
        # The check-in time should remain the same
        assert attendance_before[0]["check_in"] == attendance_after[0]["check_in"]

    def test_update_multiple_fields_preserves_multiple_attendees(self, client):
        """Test updating multiple event fields with multiple attendees checked in"""
        
        from app.config import settings
        
        # 1. Create an event
        event_data = {
            "date": "2025-10-15",
            "name": "Bible Study",
            "desc": "Weekly Bible study",
            "start_time": "18:00",
            "end_time": "20:00",
            "location": "Chapel"
        }

        response = client.post("/event", json=event_data)
        assert response.status_code == 200
        event = response.json()
        event_id = event["id"]

        # 2. Create and check in multiple people
        people = []
        
        # Create people regardless of database type
        for i, name in enumerate([("Alice", "Smith"), ("Bob", "Johnson")]):
            person_data = {
                "first_name": name[0],
                "last_name": name[1],
                "phone_number": f"555-100{i}",
                "birth_date": "2005-01-01",
                "grade": 10 + i,
                "emergency_contact_name": "Parent",
                "emergency_contact_phone": f"555-200{i}",
                "emergency_contact_relationship": "Parent"
            }

            person_response = client.post("/person", json=person_data)
            assert person_response.status_code in (200, 201)
            person = person_response.json()
            people.append(person["id"])        # Check people in
        for person_id in people:
            checkin_data = {"person_id": person_id}
            response = client.post(f"/event/{event_id}/checkin", json=checkin_data)
            assert response.status_code == 200

        # 3. Verify all are checked in
        response = client.get(f"/event/{event_id}/attendance")
        assert response.status_code == 200
        attendance_before = response.json()
        assert len(attendance_before) == 2

        # 4. Update multiple event fields
        updated_event_data = {
            "date": "2025-10-15",
            "name": "Bible Study & Fellowship",  # Changed name
            "desc": "Weekly Bible study with fellowship time",  # Changed desc
            "start_time": "17:30",  # Changed start time
            "end_time": "20:30",  # Changed end time
            "location": "Fellowship Hall"  # Changed location
        }

        response = client.put(f"/event/{event_id}", json=updated_event_data)
        assert response.status_code == 200

        # 5. Verify attendance is preserved for all attendees
        response = client.get(f"/event/{event_id}/attendance")
        assert response.status_code == 200
        attendance_after = response.json()

        assert len(attendance_after) == 2, f"Expected 2 people still checked in, got {len(attendance_after)}"
        # Verify both people are still there
        after_person_ids = [p["person_id"] for p in attendance_after]
        assert people[0] in after_person_ids
        assert people[1] in after_person_ids

        # Verify all still have check-in times and no check-out times  
        before_times = {p["person_id"]: p["check_in"] for p in attendance_before}
        after_times = {p["person_id"]: p["check_in"] for p in attendance_after}
        
        for person_id in people:
            assert before_times[person_id] == after_times[person_id], \
                f"Check-in time changed for person {person_id}"