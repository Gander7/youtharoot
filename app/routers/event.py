from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.models import Event
from app.database import get_db
from app.repositories import get_event_repository
from sqlalchemy.orm import Session
import datetime

router = APIRouter()

@router.post("/event", response_model=Event)
async def create_event(event: Event, db: Session = Depends(get_db)):
    repo = get_event_repository(db)
    return await repo.create_event(event)

@router.get("/event/{event_id}", response_model=Event)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    repo = get_event_repository(db)
    event = await repo.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/events", response_model=list[Event])
async def get_events(days: Optional[int] = Query(None), name: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = get_event_repository(db)
    return await repo.get_events(days=days, name=name)