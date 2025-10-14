"""
Test to verify that updating event details preserves attendance data.
This addresses the bug where updating an event's end time caused 
checked-in people to lose their check-in status.
"""
import pytest
from app.models import Event, EventPerson
import datetime

@pytest.mark.asyncio
async def test_update_event_preserves_attendance_memory():
    """Test that updating event details in memory repository preserves attendance data"""
    from app.repositories.memory import InMemoryEventRepository
    
    # Create repository and test event with attendance
    repo = InMemoryEventRepository()
    
    # Create an event with some checked-in attendees
    original_event = Event(
        date="2025-10-13",
        name="Youth Group",
        desc="Weekly meeting", 
        start_time="19:00",
        end_time="21:00",
        location="BLT",
        youth=[
            EventPerson(person_id=1, check_in=datetime.datetime.now())
        ],
        leaders=[
            EventPerson(person_id=2, check_in=datetime.datetime.now())
        ]
    )
    
    # Create the event in the repository
    created_event = await repo.create_event(original_event)
    event_id = created_event.id
    
    # Verify the event has attendees
    assert len(created_event.youth) == 1
    assert len(created_event.leaders) == 1
    assert created_event.youth[0].person_id == 1
    assert created_event.leaders[0].person_id == 2
    
    # Update the event with only basic details (simulating EventForm submission)
    update_event = Event(
        date="2025-10-13",
        name="Youth Group",
        desc="Weekly meeting - Updated",  # Changed description
        start_time="19:00", 
        end_time="21:30",  # Changed end time
        location="Main Hall",  # Changed location
        youth=[],  # EventForm doesn't send attendance data
        leaders=[]  # EventForm doesn't send attendance data
    )
    
    # Update the event
    updated_event = await repo.update_event(event_id, update_event)
    
    # Verify basic fields were updated
    assert updated_event.desc == "Weekly meeting - Updated"
    assert updated_event.end_time == "21:30"
    assert updated_event.location == "Main Hall"
    
    # CRITICAL: Verify attendance data was preserved despite empty arrays in update
    assert len(updated_event.youth) == 1, "Youth attendance should be preserved"
    assert len(updated_event.leaders) == 1, "Leader attendance should be preserved"
    assert updated_event.youth[0].person_id == 1, "Youth data should be unchanged"
    assert updated_event.leaders[0].person_id == 2, "Leader data should be unchanged"
    
    print("✅ Memory repository correctly preserves attendance data during event updates")


@pytest.mark.asyncio 
async def test_update_event_preserves_attendance_postgresql():
    """Test that updating event details in PostgreSQL repository preserves attendance data"""
    # Note: PostgreSQL repository stores attendance in separate EventPersonDB table
    # so this test verifies the separation works correctly
    
    from app.repositories.postgresql import PostgreSQLEventRepository, PostgreSQLPersonRepository
    from app.database import get_db
    from app.db_models import EventDB, PersonDB, EventPersonDB
    from sqlalchemy.orm import Session
    
    # Get database session
    db = next(get_db())
    
    # Skip this test if no database session available (in-memory mode)
    if db is None:
        pytest.skip("PostgreSQL test requires database connection")
    
    try:
        # Create repositories  
        event_repo = PostgreSQLEventRepository(db)
        person_repo = PostgreSQLPersonRepository(db)
        
        # Create test persons first
        from app.models import Youth, Leader
        
        youth = Youth(
            first_name="Alice", last_name="Johnson", phone_number="555-0004",
            grade=11, school_name="Test High", birth_date=datetime.date(2007, 5, 15),
            emergency_contact_name="Bob Johnson", emergency_contact_phone="555-0005", 
            emergency_contact_relationship="Father"
        )
        leader = Leader(
            first_name="Sarah", last_name="Wilson", phone_number="555-0006",
            role="Assistant", birth_date=datetime.date(1990, 3, 10)
        )
        
        created_youth = await person_repo.create_person(youth)
        created_leader = await person_repo.create_person(leader)
        
        # Create event
        original_event = Event(
            date="2025-10-13",
            name="Bible Study", 
            desc="Weekly study",
            start_time="18:00",
            end_time="20:00", 
            location="Chapel"
        )
        
        created_event = await event_repo.create_event(original_event)
        event_id = created_event.id
        
        # Manually add attendance records to simulate check-ins
        # (This simulates what happens when people check in)
        youth_attendance = EventPersonDB(
            event_id=event_id,
            person_id=created_youth.id,
            checked_in=True
        )
        leader_attendance = EventPersonDB(
            event_id=event_id, 
            person_id=created_leader.id,
            checked_in=True
        )
        
        db.add(youth_attendance)
        db.add(leader_attendance)
        db.commit()
        
        # Verify attendance records exist
        attendance_count = db.query(EventPersonDB).filter(
            EventPersonDB.event_id == event_id,
            EventPersonDB.checked_in == True
        ).count()
        assert attendance_count == 2, "Should have 2 people checked in"
        
        # Update event with basic details only (simulating EventForm)
        update_event = Event(
            date="2025-10-13",
            name="Bible Study - Advanced",  # Changed name
            desc="Advanced weekly study",   # Changed description  
            start_time="18:30",             # Changed start time
            end_time="20:30",               # Changed end time
            location="Large Conference Room" # Changed location
        )
        
        # Update the event
        updated_event = await event_repo.update_event(event_id, update_event)
        
        # Verify basic fields were updated
        assert updated_event.name == "Bible Study - Advanced"
        assert updated_event.desc == "Advanced weekly study"
        assert updated_event.start_time == "18:30"
        assert updated_event.end_time == "20:30"
        assert updated_event.location == "Large Conference Room"
        
        # CRITICAL: Verify attendance records still exist in database
        final_attendance_count = db.query(EventPersonDB).filter(
            EventPersonDB.event_id == event_id,
            EventPersonDB.checked_in == True
        ).count()
        assert final_attendance_count == 2, "Attendance records should be preserved after event update"
        
        # Verify specific people are still checked in
        youth_still_checked_in = db.query(EventPersonDB).filter(
            EventPersonDB.event_id == event_id,
            EventPersonDB.person_id == created_youth.id,
            EventPersonDB.checked_in == True
        ).first()
        
        leader_still_checked_in = db.query(EventPersonDB).filter(
            EventPersonDB.event_id == event_id,
            EventPersonDB.person_id == created_leader.id, 
            EventPersonDB.checked_in == True
        ).first()
        
        assert youth_still_checked_in is not None, "Youth should still be checked in"
        assert leader_still_checked_in is not None, "Leader should still be checked in"
        
        print("✅ PostgreSQL repository correctly preserves attendance data during event updates")
        
    finally:
        # Clean up test data
        if db is not None:
            db.query(EventPersonDB).filter(EventPersonDB.event_id == event_id).delete()
            db.query(EventDB).filter(EventDB.id == event_id).delete()
            db.query(PersonDB).filter(PersonDB.id.in_([created_youth.id, created_leader.id])).delete()
            db.commit()
            db.close()


if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        print("Testing event update attendance preservation...")
        
        try:
            await test_update_event_preserves_attendance_memory()
            await test_update_event_preserves_attendance_postgresql()
            print("🎉 All tests passed! Event updates correctly preserve attendance data.")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise
    
    asyncio.run(run_tests())