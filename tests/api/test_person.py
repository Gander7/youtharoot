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
    "grade",
    "emergency_contact_name",
    "emergency_contact_phone",
    "emergency_contact_relationship"
])
def test_missing_required_youth_field_returns_422(missing_field):
    payload = valid_youth_payload()
    del payload[missing_field]
    response = client.post(PERSON_ENDPOINT, json=payload)
    print(f"DEBUG: Response status code: {response.status_code}")
    assert response.status_code == 422

@pytest.mark.parametrize("missing_field", [
    "first_name",
    "last_name",
])
def test_missing_required_leader_field_returns_422(missing_field):
    payload = valid_leader_payload()
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
    assert delete_resp.json() == {}

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
    assert delete_resp.json() == {}

def test_get_nonexistent_person_returns_404():
    response = client.get(f"{PERSON_ENDPOINT}/9999")
    assert response.status_code == 404

def test_update_nonexistent_person_returns_404():
    payload = valid_youth_payload()
    response = client.put(f"{PERSON_ENDPOINT}/9999", json=payload)
    assert response.status_code == 404

def test_delete_nonexistent_person_returns_200():
    response = client.delete(f"{PERSON_ENDPOINT}/9999")
    assert response.status_code == 200

def test_get_archived_person_returns_404():
    payload = valid_youth_payload()
    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    person_id = post_resp.json()["id"]
    # Archive person
    client.delete(f"{PERSON_ENDPOINT}/{person_id}")
    # Try to get archived person
    get_resp = client.get(f"{PERSON_ENDPOINT}/{person_id}")
    assert get_resp.status_code == 404

def test_update_archived_person_returns_404():
    payload = valid_youth_payload()

    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    person_id = post_resp.json()["id"]
    del_resp = client.delete(f"{PERSON_ENDPOINT}/{person_id}")
    updated = payload.copy()
    updated["first_name"] = "UpdatedName"
    put_resp = client.put(f"{PERSON_ENDPOINT}/{person_id}", json=updated)

    assert put_resp.status_code == 404

def test_create_person_with_archived_on_fails():
    payload = valid_youth_payload()
    import datetime
    payload["archived_on"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    response = client.post(PERSON_ENDPOINT, json=payload)
    assert response.status_code == 422

def test_update_does_not_unarchive_person():
    payload = valid_youth_payload()

    # Create
    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    person_id = post_resp.json()["id"]
    # Delete person
    client.delete(f"{PERSON_ENDPOINT}/{person_id}")
    # Attempt to update archived person
    updated = payload.copy()
    updated["first_name"] = "UpdatedName"
    put_resp = client.put(f"{PERSON_ENDPOINT}/{person_id}", json=updated)
    # Confirm update is blocked
    assert put_resp.status_code == 404
    # Confirm archived_on is still set
    get_resp = client.get(f"{PERSON_ENDPOINT}/{person_id}")
    assert get_resp.status_code == 404

def test_get_all_non_archived_youth():
    # Create two youth, one archived
    payload1 = valid_youth_payload()
    payload2 = valid_youth_payload()
    payload2["id"] = 2
    payload2["first_name"] = "Taylor"
    post_resp1 = client.post(PERSON_ENDPOINT, json=payload1)
    post_resp2 = client.post(PERSON_ENDPOINT, json=payload2)
    assert post_resp1.status_code in (200, 201)
    assert post_resp2.status_code in (200, 201)
    # Archive one youth
    client.delete(f"{PERSON_ENDPOINT}/{payload1['id']}")

    # Get all non-archived youth
    resp = client.get(f"{PERSON_ENDPOINT}/youth")
    assert resp.status_code == 200
    data = resp.json()

    # Only non-archived youth should be returned
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == payload2["id"]
    # archived_on should not be present in the returned youth
    assert "archived_on" not in data[0] or data[0]["archived_on"] is None

def test_update_person_with_archived_on_fails():
    # Create youth
    payload = valid_youth_payload()
    post_resp = client.post(PERSON_ENDPOINT, json=payload)
    person_id = post_resp.json()["id"]
    # Try to update with archived_on set
    import datetime
    updated = payload.copy()
    updated["archived_on"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    put_resp = client.put(f"{PERSON_ENDPOINT}/{person_id}", json=updated)
    assert put_resp.status_code == 422

    # Create leader
    leader_payload = valid_leader_payload()
    post_resp_leader = client.post(PERSON_ENDPOINT, json=leader_payload)
    leader_id = post_resp_leader.json()["id"]
    updated_leader = leader_payload.copy()
    updated_leader["archived_on"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    put_resp_leader = client.put(f"{PERSON_ENDPOINT}/{leader_id}", json=updated_leader)
    assert put_resp_leader.status_code == 422