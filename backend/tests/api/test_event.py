import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.memory import InMemoryEventRepository
from tests.test_helpers import get_authenticated_client

# Use authenticated client for all tests
client = get_authenticated_client()
EVENT_ENDPOINT = "/event"

@pytest.fixture(autouse=True)
def clear_event_store():
    """Clear event store for each test."""
    # Get the memory repository instance and clear it
    from app.repositories import get_event_repository
    from app.database import get_db
    
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
def test_create_event_missing_checkin_returns_422():
    payload = {
        "id": 3,
        "date": "2025-09-03",
        "youth": [
            {
                "person_id": 1,
                # Missing check_in
                "check_out": "2025-09-03T21:05:00+00:00"
            }
        ],
        "leaders": [
            {
                "person_id": 2,
                # Missing check_in
                "check_out": "2025-09-03T21:15:00+00:00"
            }
        ]
    }
    response = client.post(EVENT_ENDPOINT, json=payload)
    assert response.status_code == 422

def test_create_event_with_checkin_checkout():
    import datetime
    event_date = datetime.date.today()
    youth_checkin, youth_checkout = make_checkin_checkout(event_date, datetime.time(18, 55), datetime.time(21, 5))
    leader_checkin, leader_checkout = make_checkin_checkout(event_date, datetime.time(18, 45), datetime.time(21, 15))
    youth_info = [{"person_id": 1, "check_in": youth_checkin, "check_out": youth_checkout}]
    leader_info = [{"person_id": 2, "check_in": leader_checkin, "check_out": leader_checkout}]
    payload = make_event_payload(2, event_date, youth_info, leader_info)
    response = client.post(EVENT_ENDPOINT, json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert len(data["youth"]) == 1
    assert data["youth"][0]["person_id"] == 1
    assert data["youth"][0]["check_in"] == youth_checkin
    assert data["youth"][0]["check_out"] == youth_checkout
    assert len(data["leaders"]) == 1
    assert data["leaders"][0]["person_id"] == 2
    assert data["leaders"][0]["check_in"] == leader_checkin
    assert data["leaders"][0]["check_out"] == leader_checkout

def valid_event_payload():
    return {
        "id": 1,
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
    client.post(EVENT_ENDPOINT, json=payload)
    event_id = payload["id"]
    response = client.get(f"{EVENT_ENDPOINT}/{event_id}")
    assert response.status_code == 200
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
    event_date = datetime.date.today()
    payload = {
        "id": 10,
        "date": event_date.isoformat(),
        "name": "Youth Group"
    }
    client.post(EVENT_ENDPOINT, json=payload)
    response = client.get(f"{EVENT_ENDPOINT}s")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(e["id"] == 10 for e in data)

def test_get_events_filter_last_x_days():
    import datetime
    today = datetime.date.today()
    old_date = today - datetime.timedelta(days=10)
    payload_recent = {
        "id": 20,
        "date": today.isoformat(),
        "name": "Recent Event"
    }
    payload_old = {
        "id": 21,
        "date": old_date.isoformat(),
        "name": "Old Event"
    }
    client.post(EVENT_ENDPOINT, json=payload_recent)
    client.post(EVENT_ENDPOINT, json=payload_old)
    response = client.get(f"{EVENT_ENDPOINT}s?days=5")
    assert response.status_code == 200
    data = response.json()
    ids = [e["id"] for e in data]
    assert 20 in ids
    assert 21 not in ids

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