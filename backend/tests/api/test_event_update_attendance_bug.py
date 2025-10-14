"""
Test to verify that updating an event preserves attendance data.

This test reproduces and verifies the fix for the bug where updating an event's
end time (or other fields) would wipe out the attendance records.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_user
from app.models import User

# Mock authentication for testing
async def get_test_user():
    return User(id=1, username="test_user", password_hash="hashed", role="admin")

app.dependency_overrides[get_current_user] = get_test_user
client = TestClient(app)

class TestEventUpdateAttendanceBug:
    
    def test_event_update_preserves_attendance_data(self):
        """Test that updating an event preserves existing attendance records"""
        
        # Step 1: Create a person to check in
        person_data = {
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": "2005-01-15",
            "grade": 10,
            "school_name": "Test High School"
        }
        person_response = client.post("/person", json=person_data)
        assert person_response.status_code == 200
        person = person_response.json()
        person_id = person["id"]
        
        # Step 2: Create an event
        event_data = {
            "date": "2025-10-15",
            "name": "Test Event",
            "desc": "Original description",
            "start_time": "19:00",
            "end_time": "21:00",
            "location": "Test Location"
        }
        event_response = client.post("/event", json=event_data)
        assert event_response.status_code == 200
        event = event_response.json()
        event_id = event["id"]
        
        # Step 3: Check in the person to the event
        checkin_data = {"person_id": person_id}
        checkin_response = client.post(f"/event/{event_id}/checkin", json=checkin_data)
        assert checkin_response.status_code == 200
        
        # Step 4: Verify the person is checked in
        attendance_response = client.get(f"/event/{event_id}/attendance")
        assert attendance_response.status_code == 200
        attendance_before = attendance_response.json()
        assert len(attendance_before) == 1
        assert attendance_before[0]["person_id"] == person_id
        assert attendance_before[0]["first_name"] == "John"
        assert attendance_before[0]["check_in"] is not None
        assert attendance_before[0]["check_out"] is None
        
        # Step 5: Update the event (change end time)
        updated_event_data = {
            "id": event_id,
            "date": "2025-10-15",
            "name": "Test Event",
            "desc": "Updated description",
            "start_time": "19:00",
            "end_time": "22:00",  # Changed from 21:00 to 22:00
            "location": "Test Location"
        }
        update_response = client.put(f"/event/{event_id}", json=updated_event_data)
        assert update_response.status_code == 200
        updated_event = update_response.json()
        
        # Verify the event was updated correctly
        assert updated_event["end_time"] == "22:00"
        assert updated_event["desc"] == "Updated description"
        
        # Step 6: Verify attendance data is still intact (this is the critical test)
        attendance_response_after = client.get(f"/event/{event_id}/attendance")
        assert attendance_response_after.status_code == 200
        attendance_after = attendance_response_after.json()
        
        # This should pass with the fix - attendance should be preserved
        assert len(attendance_after) == 1, "Attendance records should be preserved after event update"
        assert attendance_after[0]["person_id"] == person_id
        assert attendance_after[0]["first_name"] == "John"
        assert attendance_after[0]["check_in"] is not None
        assert attendance_after[0]["check_out"] is None
        
        # Verify the specific attendance data hasn't changed
        assert attendance_after[0]["check_in"] == attendance_before[0]["check_in"]
        
    def test_event_update_preserves_checkout_data(self):
        """Test that updating an event preserves checkout timestamps"""
        
        # Create person and event
        person_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "birth_date": "2006-03-20",
            "grade": 9,
            "school_name": "Test School"
        }
        person_response = client.post("/person", json=person_data)
        person_id = person_response.json()["id"]
        
        event_data = {
            "date": "2025-10-16",
            "name": "Checkout Test Event",
            "start_time": "18:00",
            "end_time": "20:00"
        }
        event_response = client.post("/event", json=event_data)
        event_id = event_response.json()["id"]
        
        # Check in and then check out the person
        checkin_data = {"person_id": person_id}
        client.post(f"/event/{event_id}/checkin", json=checkin_data)
        
        checkout_data = {"person_id": person_id}
        checkout_response = client.put(f"/event/{event_id}/checkout", json=checkout_data)
        assert checkout_response.status_code == 200
        
        # Get attendance data before update
        attendance_before = client.get(f"/event/{event_id}/attendance").json()
        assert len(attendance_before) == 1
        assert attendance_before[0]["check_out"] is not None
        
        # Update the event
        updated_event_data = {
            "id": event_id,
            "date": "2025-10-16",
            "name": "Updated Checkout Test Event",
            "start_time": "18:30",  # Changed start time
            "end_time": "20:30"     # Changed end time
        }
        client.put(f"/event/{event_id}", json=updated_event_data)
        
        # Verify checkout data is preserved
        attendance_after = client.get(f"/event/{event_id}/attendance").json()
        assert len(attendance_after) == 1
        assert attendance_after[0]["check_out"] is not None
        assert attendance_after[0]["check_out"] == attendance_before[0]["check_out"]
        
    def test_event_update_preserves_multiple_attendees(self):
        """Test that updating an event preserves multiple attendees with different check-in/out states"""
        
        # Create multiple people
        people = []
        for i in range(3):
            person_data = {
                "first_name": f"Person{i}",
                "last_name": "Test",
                "birth_date": "2005-01-01",
                "grade": 10
            }
            response = client.post("/person", json=person_data)
            people.append(response.json())
        
        # Create event
        event_data = {
            "date": "2025-10-17",
            "name": "Multi-Attendee Test",
            "start_time": "19:00",
            "end_time": "21:00"
        }
        event_response = client.post("/event", json=event_data)
        event_id = event_response.json()["id"]
        
        # Check in all people
        for person in people:
            checkin_data = {"person_id": person["id"]}
            client.post(f"/event/{event_id}/checkin", json=checkin_data)
        
        # Check out one person
        checkout_data = {"person_id": people[1]["id"]}
        client.put(f"/event/{event_id}/checkout", json=checkout_data)
        
        # Get attendance before update
        attendance_before = client.get(f"/event/{event_id}/attendance").json()
        assert len(attendance_before) == 3
        
        # Count checked in vs checked out
        checked_in_before = sum(1 for a in attendance_before if a["check_out"] is None)
        checked_out_before = sum(1 for a in attendance_before if a["check_out"] is not None)
        assert checked_in_before == 2
        assert checked_out_before == 1
        
        # Update the event
        updated_event_data = {
            "id": event_id,
            "date": "2025-10-17",
            "name": "Updated Multi-Attendee Test",
            "desc": "Added description",
            "start_time": "19:30",
            "end_time": "21:30",
            "location": "New Location"
        }
        client.put(f"/event/{event_id}", json=updated_event_data)
        
        # Verify all attendance data is preserved
        attendance_after = client.get(f"/event/{event_id}/attendance").json()
        assert len(attendance_after) == 3
        
        # Verify same check-in/out counts
        checked_in_after = sum(1 for a in attendance_after if a["check_out"] is None)
        checked_out_after = sum(1 for a in attendance_after if a["check_out"] is not None)
        assert checked_in_after == 2
        assert checked_out_after == 1
        
        # Verify specific person IDs are still present
        person_ids_after = {a["person_id"] for a in attendance_after}
        person_ids_before = {a["person_id"] for a in attendance_before}
        assert person_ids_after == person_ids_before