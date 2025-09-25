from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.models import Event, User
from sqlalchemy.orm import Session
import datetime

router = APIRouter()


def connect_to_db():
    from app.database import get_db
    db_generator = get_db()
    try:
        db = next(db_generator)
        yield db
    finally:
        try:
            next(db_generator)
        except StopIteration:
            pass

def get_current_user_dependency():
    from app.auth import get_current_user
    return get_current_user

# Use this as the actual dependency
get_current_user_lazy = Depends(get_current_user_dependency())

def get_repositories():
    from app.repositories import get_event_repository
    return get_event_repository

@router.post("/event", response_model=Event)
async def create_event(
    event: Event, 
    db: Session = Depends(connect_to_db),
    current_user: User = get_current_user_lazy
):
    get_event_repository = get_repositories()
    repo = get_event_repository(db)
    return await repo.create_event(event)

@router.get("/event/{event_id}", response_model=Event)
async def get_event(
    event_id: int, 
    db: Session = Depends(connect_to_db),
    current_user: User = get_current_user_lazy
):
    get_event_repository = get_repositories()
    repo = get_event_repository(db)
    event = await repo.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/events", response_model=list[Event])
async def get_events(
    days: Optional[int] = Query(None), 
    name: Optional[str] = Query(None), 
    db: Session = Depends(connect_to_db),
    current_user: User = get_current_user_lazy
):
    import time
    start_time = time.time()
    
    get_event_repository = get_repositories()
    repo = get_event_repository(db)
    repo_time = time.time()
    
    result = await repo.get_events(days=days, name=name)
    end_time = time.time()
    
    print(f"🔍 Events endpoint: repo creation took {repo_time - start_time:.3f}s, query took {end_time - repo_time:.3f}s, total: {end_time - start_time:.3f}s")
    return result

@router.put("/event/{event_id}", response_model=Event)
async def update_event(
    event_id: int, 
    event: Event, 
    db: Session = Depends(connect_to_db),
    current_user: User = get_current_user_lazy
):
    get_event_repository = get_repositories()
    repo = get_event_repository(db)
    try:
        return await repo.update_event(event_id, event)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/event/{event_id}")
async def delete_event(
    event_id: int, 
    db: Session = Depends(connect_to_db),
    current_user: User = get_current_user_lazy
):
    get_event_repository = get_repositories()
    repo = get_event_repository(db)
    try:
        success = await repo.delete_event(event_id)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))  # 409 Conflict

@router.get("/event/{event_id}/can-delete")
async def can_delete_event(
    event_id: int, 
    db: Session = Depends(connect_to_db),
    current_user: User = get_current_user_lazy
):
    get_event_repository = get_repositories()
    repo = get_event_repository(db)
    event = await repo.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    has_attendees = await repo.has_event_persons(event_id)
    return {"can_delete": not has_attendees, "has_attendees": has_attendees}