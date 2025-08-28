import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
PERSON_ENDPOINT = "/person"

def valid_youth_payload():
    return {
        "id": 1,
        "first_name": "Alex",
        "last_name": "Smith",
        "birth_date": "2005-04-12",
        "phone_number": "555-1234",
        "grade": 10,
        "school_name": "Central High",
        "emergency_contact_name": "Jordan Smith",
        "emergency_contact_phone": "555-5678",
        "emergency_contact_relationship": "Parent"
    }

def valid_leader_payload():
    return {
        "id": 2,
        "first_name": "Jamie",
        "last_name": "Brown",
        "birth_date": "1990-02-15",
        "phone_number": "555-2468",
        "role": "Mentor"
    }

@pytest.mark.parametrize("missing_field", [
    "first_name",
    "last_name",
    "birth_date",
    "emergency_contact_name",
    "emergency_contact_phone",
    "emergency_contact_relationship"
])
def test_missing_required_field_returns_422(missing_field):
    payload = valid_person_payload()
    del payload[missing_field]
    response = client.post(PERSON_ENDPOINT, json=payload)
    assert response.status_code == 422

def test_successful_youth_creation():
    payload = valid_youth_payload()
    response = client.post(PERSON_ENDPOINT, json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    print("DEBUG: Response data:", data)
    assert data["first_name"] == "Alex"
    assert data["grade"] == 10

def test_successful_leader_creation():
    payload = valid_leader_payload()
    response = client.post(PERSON_ENDPOINT, json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["first_name"] == "Jamie"
    assert data["role"] == "Mentor"

# Placeholder for read, update, delete tests
def test_read_youth():
    # Create youth
    payload = valid_youth_payload()
    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    assert post_resp.status_code in (200, 201)
    person_id = post_resp.json()["id"]
    # Read youth
    get_resp = client.get(f"{PERSON_ENDPOINT}/{person_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == person_id
    assert data["first_name"] == payload["first_name"]

def test_update_youth():
    # Create youth
    payload = valid_youth_payload()
    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    assert post_resp.status_code in (200, 201)
    person_id = post_resp.json()["id"]
    # Update youth
    updated = payload.copy()
    updated["first_name"] = "UpdatedName"
    put_resp = client.put(f"{PERSON_ENDPOINT}/{person_id}", json=updated)
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data["first_name"] == "UpdatedName"

def test_archive_youth():
    # Create youth
    payload = valid_youth_payload()
    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    assert post_resp.status_code in (200, 201)
    person_id = post_resp.json()["id"]
    # Archive youth
    delete_resp = client.delete(f"{PERSON_ENDPOINT}/{person_id}")
    assert delete_resp.status_code == 200
    data = delete_resp.json()
    assert data["archived"] is True

def test_read_leader():
    # Create leader
    payload = valid_leader_payload()
    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    assert post_resp.status_code in (200, 201)
    person_id = post_resp.json()["id"]
    # Read leader
    get_resp = client.get(f"{PERSON_ENDPOINT}/{person_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == person_id
    assert data["first_name"] == payload["first_name"]

def test_update_leader():
    # Create leader
    payload = valid_leader_payload()
    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    assert post_resp.status_code in (200, 201)
    person_id = post_resp.json()["id"]
    # Update leader
    updated = payload.copy()
    updated["first_name"] = "UpdatedLeader"
    put_resp = client.put(f"{PERSON_ENDPOINT}/{person_id}", json=updated)
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data["first_name"] == "UpdatedLeader"

def test_archive_leader():
    # Create leader
    payload = valid_leader_payload()
    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    assert post_resp.status_code in (200, 201)
    person_id = post_resp.json()["id"]
    # Archive leader
    delete_resp = client.delete(f"{PERSON_ENDPOINT}/{person_id}")
    assert delete_resp.status_code == 200
    data = delete_resp.json()
    assert data["archived"] is True
