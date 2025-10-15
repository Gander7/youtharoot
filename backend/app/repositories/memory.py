from typing import List, Optional, Union
from app.repositories.base import PersonRepository, EventRepository, UserRepository, MessageGroupRepository
from app.models import Youth, Leader, Event, User
from app.messaging_models import MessageGroup, MessageGroupCreate, MessageGroupUpdate, MessageGroupMembership, MessageGroupMembershipCreate, MessageGroupMembershipWithPerson, BulkGroupMembershipResponse, YouthWithType, LeaderWithType
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
    
    async def get_all_leaders(self) -> List[Leader]:
        result = []
        for person in self.store.values():
            if isinstance(person, Leader) and person.archived_on is None:
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
        
        # Get the existing event to preserve attendance data
        existing_event = self.store[event_id]
        
        # Update only the editable fields, preserve attendance data
        updated_event = Event(
            id=event_id,
            date=event.date,
            name=event.name,
            desc=event.desc,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location,
            youth=existing_event.youth,  # Preserve existing attendance
            leaders=existing_event.leaders  # Preserve existing attendance
        )
        
        self.store[event_id] = updated_event
        return updated_event
    
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
        """Initialize with secure seed data based on environment variables"""
        import os
        import bcrypt
        
        # Only initialize users if none exist yet
        if len(self.store) > 0:
            return
            
        # Get admin credentials from environment (for development/demo only)
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        # Generate secure password if not provided
        if not admin_password:
            import secrets
            import string
            admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(16))
            print(f"🔐 Generated admin password: {admin_password}")
            print("🚨 SAVE THIS PASSWORD! It won't be shown again.")
        
        # Hash the password securely
        password_bytes = admin_password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        # Create admin user
        admin_user = User(
            id=1,
            username=admin_username,
            password_hash=password_hash,
            role="admin",
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        self.store[1] = admin_user
        self.next_id = 2
        
        print(f"✅ Initialized admin user: {admin_username}")
        if os.getenv("ADMIN_PASSWORD"):
            print("🔑 Using password from ADMIN_PASSWORD environment variable")
        else:
            print("⚠️  No ADMIN_PASSWORD set, generated random password (see above)")
    
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


class InMemoryMessageGroupRepository(MessageGroupRepository):
    """In-memory implementation for message group management"""
    
    def __init__(self):
        self.groups_store = {}
        self.memberships_store = {}
        self.next_group_id = 1
        self.next_membership_id = 1
    
    async def create_group(self, group: MessageGroupCreate, created_by: int) -> MessageGroup:
        # Check for duplicate name for this user
        if await self.group_name_exists(group.name, created_by):
            raise ValueError(f"Group with name '{group.name}' already exists")
        
        # Create group
        group_id = self.next_group_id
        self.next_group_id += 1
        
        now = datetime.datetime.now(datetime.timezone.utc)
        new_group = MessageGroup(
            id=group_id,
            name=group.name,
            description=group.description,
            is_active=group.is_active,
            created_by=created_by,
            created_at=now,
            updated_at=now
        )
        
        self.groups_store[group_id] = new_group
        return new_group
    
    async def get_group(self, group_id: int, created_by: int) -> Optional[MessageGroup]:
        group = self.groups_store.get(group_id)
        if group and group.created_by == created_by:
            # Calculate member count
            member_count = len([m for m in self.memberships_store.values() if m.group_id == group.id])
            group.member_count = member_count
            return group
        return None
    
    async def get_all_groups(self, created_by: int) -> List[MessageGroup]:
        groups = [group for group in self.groups_store.values() if group.created_by == created_by]
        # Calculate member count for each group
        for group in groups:
            member_count = len([m for m in self.memberships_store.values() if m.group_id == group.id])
            group.member_count = member_count
        return groups
    
    async def update_group(self, group_id: int, group_update: MessageGroupUpdate, created_by: int) -> Optional[MessageGroup]:
        group = await self.get_group(group_id, created_by)
        if not group:
            return None
        
        # Check for duplicate name if name is being updated
        if group_update.name is not None and group_update.name != group.name:
            if await self.group_name_exists(group_update.name, created_by, exclude_id=group_id):
                raise ValueError(f"Group with name '{group_update.name}' already exists")
        
        # Update fields
        if group_update.name is not None:
            group.name = group_update.name
        if group_update.description is not None:
            group.description = group_update.description
        if group_update.is_active is not None:
            group.is_active = group_update.is_active
        
        group.updated_at = datetime.datetime.now(datetime.timezone.utc)
        self.groups_store[group_id] = group
        return group
    
    async def delete_group(self, group_id: int, created_by: int) -> bool:
        group = await self.get_group(group_id, created_by)
        if not group:
            return False
        
        # Delete all memberships for this group
        memberships_to_delete = [
            membership_id for membership_id, membership in self.memberships_store.items()
            if membership.group_id == group_id
        ]
        for membership_id in memberships_to_delete:
            del self.memberships_store[membership_id]
        
        # Delete the group
        del self.groups_store[group_id]
        return True
    
    async def group_name_exists(self, name: str, created_by: int, exclude_id: Optional[int] = None) -> bool:
        for group_id, group in self.groups_store.items():
            if (group.name == name and 
                group.created_by == created_by and 
                (exclude_id is None or group_id != exclude_id)):
                return True
        return False
    
    async def add_member(self, group_id: int, person_id: int, added_by: int) -> Optional[MessageGroupMembership]:
        # Check if already a member
        if await self.is_member(group_id, person_id):
            raise ValueError("Person is already a member of this group")
        
        # Create membership
        membership_id = self.next_membership_id
        self.next_membership_id += 1
        
        membership = MessageGroupMembership(
            id=membership_id,
            group_id=group_id,
            person_id=person_id,
            added_by=added_by,
            joined_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        self.memberships_store[membership_id] = membership
        return membership
    
    async def remove_member(self, group_id: int, person_id: int) -> bool:
        # Find membership
        membership_to_delete = None
        for membership_id, membership in self.memberships_store.items():
            if membership.group_id == group_id and membership.person_id == person_id:
                membership_to_delete = membership_id
                break
        
        if membership_to_delete:
            del self.memberships_store[membership_to_delete]
            return True
        return False
    
    async def get_group_members(self, group_id: int) -> List[MessageGroupMembership]:
        return [
            membership for membership in self.memberships_store.values()
            if membership.group_id == group_id
        ]
    
    async def get_group_members_with_person(self, group_id: int) -> List[MessageGroupMembershipWithPerson]:
        """Get all members of a message group with full person details"""
        from app.repositories import get_person_repository
        person_repo = get_person_repository(None)  # Memory mode doesn't need db session
        
        memberships = await self.get_group_members(group_id)
        result = []
        
        for membership in memberships:
            person = await person_repo.get_person(membership.person_id)
            if person:
                # Create appropriate typed person object with person_type field
                if isinstance(person, Youth):
                    person_with_type = YouthWithType(**person.model_dump(), person_type="youth")
                else:  # Leader
                    person_with_type = LeaderWithType(**person.model_dump(), person_type="leader")
                
                membership_with_person = MessageGroupMembershipWithPerson(
                    **membership.model_dump(),
                    person=person_with_type
                )
                result.append(membership_with_person)
        
        return result
    
    async def is_member(self, group_id: int, person_id: int) -> bool:
        for membership in self.memberships_store.values():
            if membership.group_id == group_id and membership.person_id == person_id:
                return True
        return False
    
    async def add_multiple_members(self, group_id: int, person_ids: List[int], added_by: int) -> BulkGroupMembershipResponse:
        added_count = 0
        skipped_count = 0
        failed_count = 0
        failed_person_ids = []
        
        for person_id in person_ids:
            try:
                # Check if already a member
                if await self.is_member(group_id, person_id):
                    skipped_count += 1
                    continue
                
                # Add member
                await self.add_member(group_id, person_id, added_by)
                added_count += 1
                
            except Exception:
                failed_count += 1
                failed_person_ids.append(person_id)
        
        return BulkGroupMembershipResponse(
            added_count=added_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            failed_person_ids=failed_person_ids
        )