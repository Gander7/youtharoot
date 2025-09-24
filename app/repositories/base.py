from abc import ABC, abstractmethod
from typing import List, Optional, Union
from app.models import Youth, Leader, Event, User
from datetime import datetime

class PersonRepository(ABC):
    """Abstract interface for person storage"""
    
    @abstractmethod
    async def create_person(self, person: Union[Youth, Leader]) -> Union[Youth, Leader]:
        pass
    
    @abstractmethod
    async def get_person(self, person_id: int) -> Optional[Union[Youth, Leader]]:
        pass
    
    @abstractmethod
    async def update_person(self, person_id: int, person: Union[Youth, Leader]) -> Union[Youth, Leader]:
        pass
    
    @abstractmethod
    async def archive_person(self, person_id: int) -> bool:
        pass
    
    @abstractmethod
    async def get_all_youth(self) -> List[Youth]:
        pass
    
    @abstractmethod
    async def get_all_leaders(self) -> List[Leader]:
        pass

class EventRepository(ABC):
    """Abstract interface for event storage"""
    
    @abstractmethod
    async def create_event(self, event: Event) -> Event:
        pass
    
    @abstractmethod
    async def get_event(self, event_id: int) -> Optional[Event]:
        pass
    
    @abstractmethod
    async def get_events(self, days: Optional[int] = None, name: Optional[str] = None) -> List[Event]:
        pass
    
    @abstractmethod
    async def update_event(self, event_id: int, event: Event) -> Event:
        pass
    
    @abstractmethod
    async def delete_event(self, event_id: int) -> bool:
        pass
    
    @abstractmethod
    async def has_event_persons(self, event_id: int) -> bool:
        """Check if event has any event_persons attached"""
        pass

class UserRepository(ABC):
    """Abstract interface for user storage"""
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def get_all_users(self) -> List[User]:
        pass
    
    @abstractmethod
    async def update_user(self, user_id: int, user: User) -> User:
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        pass