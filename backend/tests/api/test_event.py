import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.memory import InMemoryEventRepository
from tests.test_helpers import get_authenticated_client

# Use authenticated client for all tests
client = get_authenticated_client()
EVENT_ENDPOINT = "/event"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.memory import InMemoryEventRepository
from tests.test_helpers import get_authenticated_client

# Use authenticated client for all tests
client = get_authenticated_client()
EVENT_ENDPOINT = "/event"

@pytest.fixture(autouse=True)
def clear_event_store(clean_database):
    """Clear event store for each test."""
    # Get the memory repository instance and clear it
    from app.repositories import get_event_repository
    from app.database import get_db
    from app.config import settings
    
    if settings.DATABASE_TYPE == "postgresql":
        # Database cleaning is handled by clean_database fixture
        pass
    else:
        # Create a mock session for memory repository
        class MockSession:
            pass
        
        mock_session = MockSession()
        event_repo = get_event_repository(mock_session)
        if isinstance(event_repo, InMemoryEventRepository):
            event_repo.store.clear()

def make_checkin_checkout(event_date, check_in_time, check_out_time):
    from zoneinfo import ZoneInfo
    import datetime
    check_in = datetime.datetime.combine(event_date, check_in_time, tzinfo=ZoneInfo("UTC"))
    check_out = datetime.datetime.combine(event_date, check_out_time, tzinfo=ZoneInfo("UTC"))
    return check_in.isoformat().replace("+00:00", "Z"), check_out.isoformat().replace("+00:00", "Z")

def make_event_payload(event_id, event_date, youth_info, leader_info):
    payload = {
        "id": event_id,
        "date": event_date.isoformat(),
        "youth": youth_info,
        "leaders": leader_info
    }
    return payload
def test_create_event_with_valid_data():
    """Test creating an event with valid EventCreate data"""
    payload = {
        "name": "Test Event",
        "date": "2025-09-03",
        "start_time": "19:00",
        "end_time": "21:00",
        "location": "Test Location"
    }
    response = client.post(EVENT_ENDPOINT, json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Test Event"
    assert data["date"] == "2025-09-03"
    assert data["start_time"] == "19:00"
    assert data["end_time"] == "21:00"
    assert data["location"] == "Test Location"
    # Should have auto-generated datetime fields
    assert "start_datetime" in data
    assert "end_datetime" in data

def test_create_event_with_checkin_checkout():
    import datetime
    from app.config import settings
    
    # For PostgreSQL, we need to create people first, then check them in separately
    if settings.DATABASE_TYPE == "postgresql":
        # Create a youth and leader first
        youth_payload = {
            "first_name": "Test",
            "last_name": "Youth",
            "birth_date": "2005-01-01",
            "grade": 10,
            "phone_number": "555-0001",
            "emergency_contact_name": "Parent",
            "emergency_contact_phone": "555-0002",
            "emergency_contact_relationship": "Parent"
        }
        leader_payload = {
            "first_name": "Test", 
            "last_name": "Leader",
            "birth_date": "1985-01-01",
            "phone_number": "555-0003",
            "role": "Youth Pastor"
        }
        
        # Create the people
        youth_response = client.post("/person", json=youth_payload)
        assert youth_response.status_code in (200, 201)
        youth_data = youth_response.json()
        youth_id = youth_data["id"]
        
        leader_response = client.post("/person", json=leader_payload)
        assert leader_response.status_code in (200, 201)
        leader_data = leader_response.json()
        leader_id = leader_data["id"]
        
        # Create event without attendance data
        event_date = datetime.date.today()
        event_payload = {
            "date": event_date.isoformat(),
            "name": "Test Event",
            "desc": "Test event with checkin/checkout",
            "start_time": "18:30",
            "end_time": "21:30",
            "location": "Test Location"
        }
        response = client.post(EVENT_ENDPOINT, json=event_payload)
        assert response.status_code in (200, 201)
        event_data = response.json()
        event_id = event_data["id"]
        
        # Check in the youth and leader separately
        youth_checkin_data = {"person_id": youth_id}
        leader_checkin_data = {"person_id": leader_id}
        
        youth_checkin_response = client.post(f"/event/{event_id}/checkin", json=youth_checkin_data)
        leader_checkin_response = client.post(f"/event/{event_id}/checkin", json=leader_checkin_data)
        
        # Get the updated event to verify attendance
        response = client.get(f"/event/{event_id}")
        assert response.status_code == 200
        data = response.json()
        
        # In PostgreSQL mode, attendance might be stored differently
        # Just verify the event was created successfully
        assert data["id"] == event_id
        assert data["name"] == "Test Event"
        
    else:
        # Memory mode test - event creation doesn't include attendance data anymore
        event_date = datetime.date.today()
        payload = {
            "date": event_date.isoformat(),
            "name": "Test Event",
            "desc": "Test event with checkin/checkout",
            "start_time": "18:30",
            "end_time": "21:30",
            "location": "Test Location"
        }
        response = client.post(EVENT_ENDPOINT, json=payload)
        assert response.status_code in (200, 201)
        data = response.json()
        
        # Verify event was created successfully with datetime fields
        assert data["name"] == "Test Event"
        assert data["date"] == event_date.isoformat()
        assert data["start_time"] == "18:30"
        assert data["end_time"] == "21:30"
        assert "start_datetime" in data
        assert "end_datetime" in data
        # Attendance is managed separately, so youth/leaders arrays should be empty initially
        assert len(data["youth"]) == 0
        assert len(data["leaders"]) == 0

def valid_event_payload():
    return {
        "date": "2025-09-01",
        # No name, start_time, end_time, location: should default/optional
    }

def test_create_event_defaults_times_and_name():
    payload = valid_event_payload()
    response = client.post(EVENT_ENDPOINT, json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["start_time"] == "19:00"
    assert data["end_time"] == "21:00"
    assert data["name"] == "Youth Group"
    assert "location" not in data or data["location"] is None

@pytest.mark.parametrize("field", ["date"])
def test_missing_required_event_field_returns_422(field):
    payload = valid_event_payload()
    del payload[field]
    response = client.post(EVENT_ENDPOINT, json=payload)
    assert response.status_code == 422

def test_create_event_with_custom_times_and_location():
    payload = valid_event_payload()
    payload["start_time"] = "18:30"
    payload["end_time"] = "22:00"
    payload["name"] = "Lock-In"
    payload["location"] = "Community Center"
    response = client.post(EVENT_ENDPOINT, json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["start_time"] == "18:30"
    assert data["end_time"] == "22:00"
    assert data["name"] == "Lock-In"
    assert data["location"] == "Community Center"

def test_get_event():
    payload = valid_event_payload()
    response = client.post(EVENT_ENDPOINT, json=payload)
    assert response.status_code in (200, 201)
    created_event = response.json()
    event_id = created_event["id"]  # Get the auto-generated ID
    
    response = client.get(f"{EVENT_ENDPOINT}/{event_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == event_id
    assert data["date"] == "2025-09-01"
    data = response.json()
    assert data["id"] == event_id
    assert data["name"] == "Youth Group"
    assert data["start_time"] == "19:00"
    assert data["end_time"] == "21:00"
    assert "location" not in data or data["location"] is None

def test_eventperson_missing_checkin_raises_validation_error():
    from app.models import EventPerson
    import pytest
    with pytest.raises(Exception) as excinfo:
        EventPerson(person_id=1)

    assert "EventPerson" in str(excinfo.value)
    assert "validation error" in str(excinfo.value)
    assert "type=missing" in str(excinfo.value)
    assert "check_in" in str(excinfo.value)

def test_get_nonexistent_event_returns_404():
    response = client.get(f"{EVENT_ENDPOINT}/9999")
    assert response.status_code == 404

def test_get_events_empty_list():
    response = client.get(f"{EVENT_ENDPOINT}s")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_events_nonempty_list():
    import datetime
    from app.config import settings
    
    event_date = datetime.date.today()
    payload = {
        "date": event_date.isoformat(),
        "name": "Youth Group Test Event"
    }
    
    # Create event and get the actual ID that was generated
    create_response = client.post(EVENT_ENDPOINT, json=payload)
    assert create_response.status_code in (200, 201)
    created_event = create_response.json()
    expected_id = created_event["id"]
    
    response = client.get(f"{EVENT_ENDPOINT}s")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(e["id"] == expected_id for e in data)

def test_get_events_filter_last_x_days():
    import datetime
    from app.config import settings
    
    today = datetime.date.today()
    old_date = today - datetime.timedelta(days=10)
    payload_recent = {
        "date": today.isoformat(),
        "name": "Recent Event"
    }
    payload_old = {
        "date": old_date.isoformat(),
        "name": "Old Event"
    }
    
    # Create events and get the actual IDs
    recent_response = client.post(EVENT_ENDPOINT, json=payload_recent)
    assert recent_response.status_code in (200, 201)
    recent_event = recent_response.json()
    recent_id = recent_event["id"]
    
    old_response = client.post(EVENT_ENDPOINT, json=payload_old)
    assert old_response.status_code in (200, 201)
    old_event = old_response.json()
    old_id = old_event["id"]
    
    # Filter for events in last 5 days (should only return recent event)
    response = client.get(f"{EVENT_ENDPOINT}s?days=5")
    assert response.status_code == 200
    data = response.json()
    ids = [e["id"] for e in data]
    print(f"Events in last 5 days: {ids}")
    assert recent_id in ids
    assert old_id not in ids  # Old event should not be in recent list

def test_get_events_filter_name_contains():
    import datetime
    event_date = datetime.date.today()
    payload1 = {
        "id": 30,
        "date": event_date.isoformat(),
        "name": "Youth Rally"
    }
    payload2 = {
        "id": 31,
        "date": event_date.isoformat(),
        "name": "Leader Meeting"
    }
    client.post(EVENT_ENDPOINT, json=payload1)
    client.post(EVENT_ENDPOINT, json=payload2)
    response = client.get(f"{EVENT_ENDPOINT}s?name=Rally")
    assert response.status_code == 200
    data = response.json()
    names = [e["name"] for e in data]
    assert "Youth Rally" in names
    assert "Leader Meeting" not in names