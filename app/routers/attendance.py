from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.repositories import get_event_repository, get_person_repository
from sqlalchemy.orm import Session
import datetime

router = APIRouter()

class CheckInRequest(BaseModel):
    person_id: int

class CheckOutRequest(BaseModel):
    person_id: int

@router.post("/event/{event_id}/checkin")
async def check_in_person(event_id: int, request: CheckInRequest, db: Session = Depends(get_db)):
    """Check in a person to an event"""
    try:
        # Verify event exists
        event_repo = get_event_repository(db)
        event = await event_repo.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Verify person exists
        person_repo = get_person_repository(db)
        person = await person_repo.get_person(request.person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Check if already checked in
        all_attendees = event.youth + event.leaders
        for attendee in all_attendees:
            if attendee.person_id == request.person_id:
                raise HTTPException(status_code=409, detail="Person is already checked in to this event")
        
        # Create event_person record
        from app.models import EventPerson
        event_person = EventPerson(
            person_id=request.person_id,
            check_in=datetime.datetime.now()
        )
        
        # Add to appropriate list based on person type
        if hasattr(person, 'grade'):  # Youth
            event.youth.append(event_person)
        else:  # Leader
            event.leaders.append(event_person)
        
        # Update the event in the repository
        await event_repo.update_event(event_id, event)
        
        return {"message": "Person checked in successfully", "check_in": event_person.check_in}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in check_in_person: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/event/{event_id}/checkout")
async def check_out_person(event_id: int, request: CheckOutRequest, db: Session = Depends(get_db)):
    """Check out a person from an event"""
    try:
        # Verify event exists
        event_repo = get_event_repository(db)
        event = await event_repo.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Find the event_person record
        all_attendees = event.youth + event.leaders
        event_person = None
        for attendee in all_attendees:
            if attendee.person_id == request.person_id:
                event_person = attendee
                break
        
        if not event_person:
            raise HTTPException(status_code=404, detail="Person is not checked in to this event")
        
        if event_person.check_out:
            raise HTTPException(status_code=409, detail="Person is already checked out")
        
        # Update check-out time
        event_person.check_out = datetime.datetime.now()
        
        # Update the event in the repository
        await event_repo.update_event(event_id, event)
        
        return {"message": "Person checked out successfully", "check_out": event_person.check_out}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in check_out_person: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/event/{event_id}/attendance")
async def get_event_attendance(event_id: int, db: Session = Depends(get_db)):
    """Get all attendance records for an event"""
    try:
        # Verify event exists
        event_repo = get_event_repository(db)
        event = await event_repo.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        person_repo = get_person_repository(db)
        result = []
        
        # Process youth attendees
        for event_person in event.youth:
            person = await person_repo.get_person(event_person.person_id)
            if person:
                result.append({
                    "person_id": person.id,
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                    "person_type": "youth",
                    "check_in": event_person.check_in,
                    "check_out": event_person.check_out,
                    "grade": person.grade,
                    "school_name": person.school_name,
                    "role": None
                })
        
        # Process leader attendees  
        for event_person in event.leaders:
            person = await person_repo.get_person(event_person.person_id)
            if person:
                result.append({
                    "person_id": person.id,
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                    "person_type": "leader",
                    "check_in": event_person.check_in,
                    "check_out": event_person.check_out,
                    "grade": None,
                    "school_name": None,
                    "role": person.role
                })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_event_attendance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")