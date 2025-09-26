from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.models import Event, User
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
    from app.repositories import get_event_repository
    return {
        "event": get_event_repository(db_session)
    }

router = APIRouter()

@router.post("/event", response_model=Event)
async def create_event(
    event: Event, 
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_dependency())
):
    repos = get_repositories(db)
    return await repos["event"].create_event(event)

@router.get("/event/{event_id}", response_model=Event)
async def get_event(
    event_id: int, 
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_dependency())
):
    repos = get_repositories(db)
    event = await repos["event"].get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/events", response_model=list[Event])
async def get_events(
    days: Optional[int] = Query(None), 
    name: Optional[str] = Query(None), 
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_dependency())
):
    import time
    start_time = time.time()
    
    repos = get_repositories(db)
    repo_time = time.time()
    
    result = await repos["event"].get_events(days=days, name=name)
    end_time = time.time()
    
    print(f"🔍 Events endpoint: repo creation took {repo_time - start_time:.3f}s, query took {end_time - repo_time:.3f}s, total: {end_time - start_time:.3f}s")
    return result

@router.put("/event/{event_id}", response_model=Event)
async def update_event(
    event_id: int, 
    event: Event, 
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_dependency())
):
    repos = get_repositories(db)
    try:
        return await repos["event"].update_event(event_id, event)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/event/{event_id}")
async def delete_event(
    event_id: int, 
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_dependency())
):
    repos = get_repositories(db)
    try:
        success = await repos["event"].delete_event(event_id)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))  # 409 Conflict

@router.get("/event/{event_id}/can-delete")
async def can_delete_event(
    event_id: int, 
    db: Session = Depends(connect_to_db()),
    current_user: User = Depends(get_current_user_dependency())
):
    repos = get_repositories(db)
    event = await repos["event"].get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    has_attendees = await repos["event"].has_event_persons(event_id)
    return {"can_delete": not has_attendees, "has_attendees": has_attendees}