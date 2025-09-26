from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.models import User
from sqlalchemy.orm import Session
import datetime

# Lazy loading functions
def connect_to_db():
    """Lazily import and return database dependency"""
    from app.database import get_db
    return get_db

def get_current_user_dependency():
    """Lazily import and return current user dependency"""
    from app.auth import get_current_user
    return get_current_user

def get_repositories(db_session):
    """Lazily import and return repository instances"""
    from app.repositories import get_event_repository, get_person_repository
    return {
        "event": get_event_repository(db_session),
        "person": get_person_repository(db_session)
    }

router = APIRouter()

class CheckInRequest(BaseModel):
    person_id: int

class CheckOutRequest(BaseModel):
    person_id: int

@router.post("/event/{event_id}/checkin")
async def check_in_person(
    event_id: int, 
    request: CheckInRequest, 
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_dependency())
):
    """Check in a person to an event"""
    try:
        repos = get_repositories(db)
        
        # Verify event exists
        event = await repos["event"].get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Verify person exists
        person = await repos["person"].get_person(request.person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        from app.config import settings
        
        if settings.DATABASE_TYPE == "memory":
            # Handle in-memory repository
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
            
        else:
            # Handle PostgreSQL database directly
            from app.db_models import EventPersonDB
            
            # Check if already checked in
            existing = db.query(EventPersonDB).filter(
                EventPersonDB.event_id == event_id,
                EventPersonDB.person_id == request.person_id
            ).first()
            
            if existing:
                raise HTTPException(status_code=409, detail="Person is already checked in to this event")
            
            # Create new check-in record
            event_person = EventPersonDB(
                event_id=event_id,
                person_id=request.person_id,
                check_in=datetime.datetime.now(),
                person_type="youth" if hasattr(person, 'grade') else "leader"
            )
            
            db.add(event_person)
            db.commit()
            
            return {"message": "Person checked in successfully", "check_in": event_person.check_in}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in check_in_person: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/event/{event_id}/checkout")
async def check_out_person(
    event_id: int, 
    request: CheckOutRequest, 
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_dependency())
):
    """Check out a person from an event"""
    try:
        # Verify event exists
        repos = get_repositories(db)
        event = await repos["event"].get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        from app.config import settings
        
        if settings.DATABASE_TYPE == "memory":
            # Handle in-memory repository
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
            await repos["event"].update_event(event_id, event)
            
            return {"message": "Person checked out successfully", "check_out": event_person.check_out}
            
        else:
            # Handle PostgreSQL database directly
            from app.db_models import EventPersonDB
            
            event_person = db.query(EventPersonDB).filter(
                EventPersonDB.event_id == event_id,
                EventPersonDB.person_id == request.person_id
            ).first()
            
            if not event_person:
                raise HTTPException(status_code=404, detail="Person is not checked in to this event")
            
            if event_person.check_out:
                raise HTTPException(status_code=409, detail="Person is already checked out")
            
            # Update check-out time
            event_person.check_out = datetime.datetime.now()
            db.commit()
            
            return {"message": "Person checked out successfully", "check_out": event_person.check_out}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in check_out_person: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/event/{event_id}/attendance")
async def get_event_attendance(
    event_id: int, 
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_dependency())
):
    """Get all attendance records for an event"""
    try:
        # Verify event exists
        repos = get_repositories(db)
        event = await repos["event"].get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        result = []
        
        # Process youth attendees
        for event_person in event.youth:
            person = await repos["person"].get_person(event_person.person_id)
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
            person = await repos["person"].get_person(event_person.person_id)
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