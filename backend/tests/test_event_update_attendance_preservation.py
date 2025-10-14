"""
Test to verify that updating event details preserves attendance data.
This addresses the bug where updating an event's end time caused 
checked-in people to lose their check-in status.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_helpers import get_authenticated_client

# Use the authenticated client that properly initializes repositories
client = get_authenticated_client()

class TestEventUpdatePreservesAttendance:
    """Test that event updates don't wipe out attendance data"""
    
    def test_update_event_end_time_preserves_attendance(self):
        """Test the specific bug: updating event end time should not remove checked-in people"""
        
        # 1. Create an event
        event_data = {
            "date": "2025-10-14",
            "name": "Youth Group Meeting", 
            "desc": "Weekly youth meeting",
            "start_time": "19:00",
            "end_time": "21:00",
            "location": "Main Hall"
        }
        
        response = client.post("/event", json=event_data)
        assert response.status_code == 200
        event = response.json()
        event_id = event["id"]
        
        # 2. Create a person to check in
        person_data = {
            "first_name": "John",
            "last_name": "Doe", 
            "phone_number": "555-0123",
            "type": "youth",
            "grade": 10,
            "school_name": "Test High School",
            "birth_date": "2008-05-15",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "555-0124",
            "emergency_contact_relationship": "Mother"
        }
        
        response = client.post("/person", json=person_data)
        assert response.status_code == 200
        person = response.json()
        person_id = person["id"]
        
        # 3. Check the person into the event
        checkin_data = {
            "person_id": person_id,
            "checked_in": True
        }
        
        response = client.post(f"/event/{event_id}/checkin", json=checkin_data)
        assert response.status_code == 200
        
        # 4. Verify person is checked in
        response = client.get(f"/event/{event_id}")
        assert response.status_code == 200
        event_before_update = response.json()
        
        # Should have 1 youth checked in
        assert len(event_before_update["youth"]) == 1
        print(f"DEBUG: Youth object structure: {event_before_update['youth'][0]}")
        # The youth array contains attendance records, not full person data
        assert event_before_update["youth"][0]["person_id"] == person_id
        assert event_before_update["youth"][0]["check_in"] is not None
        assert event_before_update["youth"][0]["check_out"] is None  # Not checked out yet
        
        # 5. Update the event end time (the problematic operation)
        update_data = {
            "date": "2025-10-14",
            "name": "Youth Group Meeting",
            "desc": "Weekly youth meeting", 
            "start_time": "19:00",
            "end_time": "21:30",  # Changed from 21:00 to 21:30
            "location": "Main Hall"
        }
        
        response = client.put(f"/event/{event_id}", json=update_data)
        assert response.status_code == 200
        
        # 6. CRITICAL TEST: Verify the person is STILL checked in after update
        response = client.get(f"/event/{event_id}")
        assert response.status_code == 200
        event_after_update = response.json()
        
        # Verify basic fields were updated
        assert event_after_update["end_time"] == "21:30"
        
        # CRITICAL: Verify attendance was preserved (this is the bug fix)
        assert len(event_after_update["youth"]) == 1, "Person should still be checked in after event update"
        assert event_after_update["youth"][0]["person_id"] == person_id, "Same person should still be checked in"
        assert event_after_update["youth"][0]["check_in"] is not None, "Check-in time should be preserved"
        
        print("✅ Event update correctly preserved attendance data!")
        
    def test_update_multiple_fields_preserves_multiple_attendees(self):
        """Test updating multiple event fields with multiple attendees checked in"""
        
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
        people_data = [
            {
                "first_name": "Alice", "last_name": "Smith", "phone_number": "555-0001",
                "type": "youth", "grade": 11, "school_name": "Test High",
                "birth_date": "2007-03-10", "emergency_contact_name": "Bob Smith",
                "emergency_contact_phone": "555-0002", "emergency_contact_relationship": "Father"
            },
            {
                "first_name": "Pastor", "last_name": "Johnson", "phone_number": "555-0003",
                "type": "leader", "role": "Youth Pastor", "birth_date": "1985-07-20"
            }
        ]
        
        person_ids = []
        for person_data in people_data:
            response = client.post("/person", json=person_data)
            assert response.status_code == 200
            person = response.json()
            person_ids.append(person["id"])
            
            # Check them in
            checkin_data = {"person_id": person["id"], "checked_in": True}
            response = client.post(f"/event/{event_id}/checkin", json=checkin_data)
            assert response.status_code == 200
        
        # 3. Verify both are checked in
        response = client.get(f"/event/{event_id}")
        assert response.status_code == 200
        event_before = response.json()
        
        assert len(event_before["youth"]) == 1, "Should have 1 youth"
        assert len(event_before["leaders"]) == 1, "Should have 1 leader"
        
        # 4. Update multiple event fields
        update_data = {
            "date": "2025-10-15",
            "name": "Advanced Bible Study",  # Changed name
            "desc": "Advanced weekly Bible study session",  # Changed description
            "start_time": "18:30",  # Changed start time
            "end_time": "20:30",   # Changed end time  
            "location": "Large Conference Room"  # Changed location
        }
        
        response = client.put(f"/event/{event_id}", json=update_data)
        assert response.status_code == 200
        
        # 5. CRITICAL: Verify ALL attendees are still checked in
        response = client.get(f"/event/{event_id}")
        assert response.status_code == 200
        event_after = response.json()
        
        # Verify all fields were updated
        assert event_after["name"] == "Advanced Bible Study"
        assert event_after["desc"] == "Advanced weekly Bible study session"
        assert event_after["start_time"] == "18:30"
        assert event_after["end_time"] == "20:30"
        assert event_after["location"] == "Large Conference Room"
        
        # CRITICAL: Verify ALL attendance preserved
        assert len(event_after["youth"]) == 1, "Youth should still be checked in"
        assert len(event_after["leaders"]) == 1, "Leader should still be checked in"
        # Check that the same people are still checked in by person_id
        assert event_after["youth"][0]["person_id"] == person_ids[0], "Same youth should still be checked in"
        assert event_after["leaders"][0]["person_id"] == person_ids[1], "Same leader should still be checked in"
        
        print("✅ Multi-field event update correctly preserved all attendance data!")

if __name__ == "__main__":
    # Run the tests directly
    test_instance = TestEventUpdatePreservesAttendance()
    try:
        test_instance.test_update_event_end_time_preserves_attendance()
        test_instance.test_update_multiple_fields_preserves_multiple_attendees()
        print("🎉 All attendance preservation tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise