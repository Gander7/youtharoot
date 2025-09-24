from typing import List, Optional, Union
from app.repositories.base import PersonRepository, EventRepository
from app.models import Youth, Leader, Event
import datetime

class InMemoryPersonRepository(PersonRepository):
    """In-memory implementation for development"""
    
    def __init__(self):
        self.store = {}
    
    async def create_person(self, person: Union[Youth, Leader]) -> Union[Youth, Leader]:
        if person.archived_on is not None:
            raise ValueError("Cannot create archived person")
        self.store[person.id] = person
        return person
    
    async def get_person(self, person_id: int) -> Optional[Union[Youth, Leader]]:
        person = self.store.get(person_id)
        if person and person.archived_on is None:
            return person
        return None
    
    async def update_person(self, person_id: int, person: Union[Youth, Leader]) -> Union[Youth, Leader]:
        if person.archived_on is not None:
            raise ValueError("Cannot update person with archived_on field")
        if person_id not in self.store:
            raise ValueError("Person not found")
        
        existing = self.store[person_id]
        if existing.archived_on is not None:
            raise ValueError("Person not found")
        
        self.store[person_id] = person
        return person
    
    async def archive_person(self, person_id: int) -> bool:
        person = self.store.get(person_id)
        if person:
            person.archived_on = datetime.datetime.now(datetime.timezone.utc)
            return True
        return False
    
    async def get_all_youth(self) -> List[Youth]:
        result = []
        for person in self.store.values():
            if isinstance(person, Youth) and person.archived_on is None:
                result.append(person)
        return result

class InMemoryEventRepository(EventRepository):
    """In-memory implementation for development"""
    
    def __init__(self):
        self.store = {}
    
    async def create_event(self, event: Event) -> Event:
        self.store[event.id] = event
        return event
    
    async def get_event(self, event_id: int) -> Optional[Event]:
        return self.store.get(event_id)
    
    async def get_events(self, days: Optional[int] = None, name: Optional[str] = None) -> List[Event]:
        events = list(self.store.values())
        
        if days is not None:
            cutoff = datetime.date.today() - datetime.timedelta(days=days)
            events = [e for e in events if datetime.date.fromisoformat(e.date) >= cutoff]
        
        if name:
            events = [e for e in events if name.lower() in e.name.lower()]
        
        return events