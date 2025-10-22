from abc import ABC, abstractmethod
from typing import List, Optional, Union
from app.models import Youth, Leader, Parent, Event, EventCreate, EventUpdate, User, PersonCreate, PersonUpdate, ParentYouthRelationshipCreate
from app.messaging_models import MessageGroup, MessageGroupCreate, MessageGroupUpdate, MessageGroupMembership, MessageGroupMembershipCreate, MessageGroupMembershipWithPerson, BulkGroupMembershipResponse
from datetime import datetime

class PersonRepository(ABC):
    """Abstract interface for person storage"""
    
    @abstractmethod
    async def create_person(self, person: Union[Youth, Leader, Parent]) -> Union[Youth, Leader, Parent]:
        pass
    
    # New unified person management methods
    @abstractmethod
    async def create_person_unified(self, person: PersonCreate) -> dict:
        """Create any type of person (youth, leader, parent) using unified model"""
        pass
    
    @abstractmethod
    async def update_person_unified(self, person_id: int, person_update: PersonUpdate) -> dict:
        """Update any type of person using unified model"""
        pass
    
    @abstractmethod
    async def get_person_unified(self, person_id: int) -> Optional[dict]:
        """Get any type of person as dictionary"""
        pass
    
    @abstractmethod
    async def search_persons(self, person_type: str, query: Optional[str] = None) -> List[dict]:
        """Search persons by type with optional name/phone/email filter"""
        pass
    
    # Parent-specific methods
    @abstractmethod
    async def get_all_parents(self) -> List[dict]:
        """Get all parents"""
        pass
    
    @abstractmethod
    async def link_parent_to_youth(self, relationship: ParentYouthRelationshipCreate) -> dict:
        """Create parent-youth relationship"""
        pass
    
    @abstractmethod
    async def unlink_parent_from_youth(self, parent_id: int, youth_id: int) -> bool:
        """Remove parent-youth relationship"""
        pass
    
    @abstractmethod
    async def get_parents_for_youth(self, youth_id: int) -> List[dict]:
        """Get all parents linked to a youth with relationship details"""
        pass
    
    @abstractmethod
    async def get_youth_for_parent(self, parent_id: int) -> List[dict]:
        """Get all youth linked to a parent with relationship details"""
        pass
    
    # Legacy methods (maintained for backward compatibility)
    @abstractmethod
    async def get_person(self, person_id: int) -> Optional[Union[Youth, Leader, Parent]]:
        pass
    
    @abstractmethod
    async def update_person(self, person_id: int, person: Union[Youth, Leader, Parent]) -> Union[Youth, Leader, Parent]:
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
    async def create_event(self, event: EventCreate) -> Event:
        pass
    
    @abstractmethod
    async def get_event(self, event_id: int) -> Optional[Event]:
        pass
    
    @abstractmethod
    async def get_events(self, days: Optional[int] = None, name: Optional[str] = None) -> List[Event]:
        pass
    
    @abstractmethod
    async def update_event(self, event_id: int, event_update: EventUpdate) -> Event:
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


class MessageGroupRepository(ABC):
    """Abstract interface for message group storage"""
    
    @abstractmethod
    async def create_group(self, group: MessageGroupCreate, created_by: int) -> MessageGroup:
        pass
    
    @abstractmethod
    async def get_group(self, group_id: int, created_by: int) -> Optional[MessageGroup]:
        pass
    
    @abstractmethod
    async def get_all_groups(self, created_by: int) -> List[MessageGroup]:
        pass
    
    @abstractmethod
    async def update_group(self, group_id: int, group_update: MessageGroupUpdate, created_by: int) -> Optional[MessageGroup]:
        pass
    
    @abstractmethod
    async def delete_group(self, group_id: int, created_by: int) -> bool:
        pass
    
    @abstractmethod
    async def group_name_exists(self, name: str, created_by: int, exclude_id: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    async def add_member(self, group_id: int, person_id: int, added_by: int) -> Optional[MessageGroupMembership]:
        pass
    
    @abstractmethod
    async def remove_member(self, group_id: int, person_id: int) -> bool:
        pass
    
    @abstractmethod
    async def get_group_members(self, group_id: int) -> List[MessageGroupMembership]:
        pass
    
    @abstractmethod
    async def get_group_members_with_person(self, group_id: int) -> List[MessageGroupMembershipWithPerson]:
        """Get all members of a group with full person details."""
        pass
    
    @abstractmethod
    async def is_member(self, group_id: int, person_id: int) -> bool:
        pass
    
    @abstractmethod
    async def add_multiple_members(self, group_id: int, person_ids: List[int], added_by: int) -> BulkGroupMembershipResponse:
        pass