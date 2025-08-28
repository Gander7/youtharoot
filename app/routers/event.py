from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models import Event
import datetime

router = APIRouter()
event_store = {}

@router.post("/event", response_model=Event)
async def create_event(event: Event):
    event_store[event.id] = event
    return event

@router.get("/event/{event_id}", response_model=Event)
async def get_event(event_id: int):
    event = event_store.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/events", response_model=list[Event])
async def get_events(days: Optional[int] = Query(None), name: Optional[str] = Query(None)):
    events = list(event_store.values())
    if days is not None:
        cutoff = datetime.date.today() - datetime.timedelta(days=days)
        events = [e for e in events if datetime.date.fromisoformat(e.date) >= cutoff]
    if name:
        events = [e for e in events if name.lower() in e.name.lower()]
    return events