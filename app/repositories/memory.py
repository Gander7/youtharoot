from typing import List, Optional, Union
from app.repositories.base import PersonRepository, EventRepository, UserRepository
from app.models import Youth, Leader, Event, User
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

class InMemoryUserRepository(UserRepository):
    """In-memory implementation for user management"""
    
    def __init__(self):
        self.store = {}
        self.next_id = 1
        # Initialize with seed data
        self._initialize_seed_data()
    
    def _initialize_seed_data(self):
        """Initialize with admin and user seed data"""
        # Note: These are proper bcrypt hashes for demo purposes
        # In production, initial users should be created through secure setup process
        
        # Admin user - password: "admin123"
        admin_user = User(
            id=1,
            username="admin",
            password_hash="$2b$12$UgEizDPb.75.tE6qHLPR7.LCISLwlLGnoCyb/ummRVs07sGLBY2nu",
            role="admin",
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        # Regular user - password: "user123"  
        regular_user = User(
            id=2,
            username="user",
            password_hash="$2b$12$IEUDH2tE8c1qh.XziSOa5OanTf9cdeDOYgFPtpk4J719zVh3YcWUK",
            role="user",
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        self.store[1] = admin_user
        self.store[2] = regular_user
        self.next_id = 3
    
    async def create_user(self, user: User) -> User:
        # Generate ID if not provided
        if user.id is None:
            user.id = self.next_id
            self.next_id += 1
        
        # Set created_at if not provided
        if user.created_at is None:
            user.created_at = datetime.datetime.now(datetime.timezone.utc)
        
        # Check for duplicate username
        for existing_user in self.store.values():
            if existing_user.username == user.username:
                raise ValueError(f"Username '{user.username}' already exists")
        
        self.store[user.id] = user
        return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        return self.store.get(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        for user in self.store.values():
            if user.username == username:
                return user
        return None
    
    async def get_all_users(self) -> List[User]:
        return list(self.store.values())
    
    async def update_user(self, user_id: int, user: User) -> User:
        if user_id not in self.store:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check for duplicate username (excluding current user)
        for existing_id, existing_user in self.store.items():
            if existing_id != user_id and existing_user.username == user.username:
                raise ValueError(f"Username '{user.username}' already exists")
        
        user.id = user_id  # Ensure ID matches
        self.store[user_id] = user
        return user
    
    async def delete_user(self, user_id: int) -> bool:
        if user_id not in self.store:
            return False
        
        del self.store[user_id]
        return True