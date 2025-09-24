from typing import List, Optional, Union
from app.repositories.base import PersonRepository, EventRepository
from app.models import Youth, Leader, Event
import datetime

class InMemoryPersonRepository(PersonRepository):
    """In-memory implementation for development"""
    
    def __init__(self):
        self.store = {}
        self.next_person_id = 1
    
    async def create_person(self, person: Union[Youth, Leader]) -> Union[Youth, Leader]:
        if person.archived_on is not None:
            raise ValueError("Cannot create archived person")
        
        # Generate ID if not provided
        if person.id is None:
            person.id = self.next_person_id
            self.next_person_id += 1
        
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
        self.next_id = 1
    
    async def create_event(self, event: Event) -> Event:
        # Generate ID if not provided
        if event.id is None:
            event.id = self.next_id
            self.next_id += 1
        
        self.store[event.id] = event
        return event
    
    async def get_event(self, event_id: int) -> Optional[Event]:
        return self.store.get(event_id)
    
    async def get_events(self, days: Optional[int] = None, name: Optional[str] = None) -> List[Event]:
        import time
        start_time = time.time()
        
        events = list(self.store.values())
        list_time = time.time()
        
        if days is not None:
            cutoff = datetime.date.today() - datetime.timedelta(days=days)
            events = [e for e in events if datetime.date.fromisoformat(e.date) >= cutoff]
        
        if name:
            events = [e for e in events if name.lower() in e.name.lower()]
        
        filter_time = time.time()
        
        print(f"🧠 Memory repo: list creation took {list_time - start_time:.3f}s, filtering took {filter_time - list_time:.3f}s, total: {filter_time - start_time:.3f}s")
        print(f"🧠 Memory repo: {len(events)} events in store")
        
        return events
    
    async def update_event(self, event_id: int, event: Event) -> Event:
        if event_id not in self.store:
            raise ValueError(f"Event with ID {event_id} not found")
        
        event.id = event_id  # Ensure ID matches
        self.store[event_id] = event
        return event
    
    async def delete_event(self, event_id: int) -> bool:
        if event_id not in self.store:
            return False
        
        # Check if event has any event_persons
        if await self.has_event_persons(event_id):
            raise ValueError("Cannot delete event that has attendance records")
        
        del self.store[event_id]
        return True
    
    async def has_event_persons(self, event_id: int) -> bool:
        """Check if event has any event_persons attached"""
        event = self.store.get(event_id)
        if not event:
            return False
        
        # Check if there are any youth or leaders with check-in records
        return len(event.youth) > 0 or len(event.leaders) > 0