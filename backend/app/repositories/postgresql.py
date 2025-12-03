from typing import List, Optional, Union
from sqlalchemy.orm import Session
from app.repositories.base import PersonRepository, EventRepository, UserRepository, MessageGroupRepository
from app.models import Youth, Leader, Parent, Event, EventCreate, EventUpdate, EventPerson, User, PersonCreate, PersonUpdate, ParentYouthRelationshipCreate
from app.messaging_models import MessageGroup, MessageGroupCreate, MessageGroupUpdate, MessageGroupMembership, MessageGroupMembershipWithPerson, BulkGroupMembershipResponse, YouthWithType, LeaderWithType, ParentWithType
from app.db_models import PersonDB, EventDB, UserDB, MessageGroupDB, MessageGroupMembershipDB, ParentYouthRelationshipDB
from datetime import datetime, timezone
import datetime as dt

class PostgreSQLPersonRepository(PersonRepository):
    """PostgreSQL implementation for production"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _db_to_pydantic(self, db_person: PersonDB) -> Union[Youth, Leader, Parent]:
        """Convert database model to Pydantic model"""
        base_data = {
            "id": db_person.id,
            "first_name": db_person.first_name,
            "last_name": db_person.last_name,
            "phone_number": db_person.phone_number,
            "archived_on": db_person.archived_on
        }
        
        if db_person.person_type == "youth":
            return Youth(
                **base_data,
                grade=db_person.grade,
                school_name=db_person.school_name,
                birth_date=db_person.birth_date,
                email=db_person.email or "",
                emergency_contact_name=db_person.emergency_contact_name or "",
                emergency_contact_phone=db_person.emergency_contact_phone or "",
                emergency_contact_relationship=db_person.emergency_contact_relationship or "",
                emergency_contact_2_name=db_person.emergency_contact_2_name or "",
                emergency_contact_2_phone=db_person.emergency_contact_2_phone or "",
                emergency_contact_2_relationship=db_person.emergency_contact_2_relationship or "",
                allergies=db_person.allergies or "",
                other_considerations=db_person.other_considerations or ""
            )
        elif db_person.person_type == "parent":
            return Parent(
                **base_data,
                email=db_person.email or "",
                address=db_person.address or ""
            )
        else:
            return Leader(
                **base_data,
                role=db_person.role,
                birth_date=db_person.birth_date
            )
    
    def _pydantic_to_db(self, person: Union[Youth, Leader, Parent]) -> PersonDB:
        """Convert Pydantic model to database model"""
        person_type = "youth" if isinstance(person, Youth) else ("parent" if isinstance(person, Parent) else "leader")
        
        db_person = PersonDB(
            # Don't set ID, let PostgreSQL auto-generate it
            first_name=person.first_name,
            last_name=person.last_name,
            phone_number=person.phone_number,
            archived_on=person.archived_on,
            person_type=person_type
        )
        
        if isinstance(person, Youth):
            db_person.grade = person.grade
            db_person.school_name = person.school_name
            db_person.birth_date = person.birth_date
            db_person.email = person.email
            db_person.emergency_contact_name = person.emergency_contact_name
            db_person.emergency_contact_phone = person.emergency_contact_phone
            db_person.emergency_contact_relationship = person.emergency_contact_relationship
            db_person.emergency_contact_2_name = person.emergency_contact_2_name
            db_person.emergency_contact_2_phone = person.emergency_contact_2_phone
            db_person.emergency_contact_2_relationship = person.emergency_contact_2_relationship
            db_person.allergies = person.allergies
            db_person.other_considerations = person.other_considerations
        elif isinstance(person, Parent):
            db_person.email = person.email
            db_person.address = person.address
        else:
            db_person.role = person.role
            db_person.birth_date = person.birth_date
        
        return db_person
    
    async def create_person(self, person: Union[Youth, Leader, Parent]) -> Union[Youth, Leader, Parent]:
        if person.archived_on is not None:
            raise ValueError("Cannot create archived person")
        
        db_person = self._pydantic_to_db(person)
        self.db.add(db_person)
        self.db.commit()
        self.db.refresh(db_person)
        
        return self._db_to_pydantic(db_person)
    
    async def get_person(self, person_id: int) -> Optional[Union[Youth, Leader, Parent]]:
        db_person = self.db.query(PersonDB).filter(
            PersonDB.id == person_id,
            PersonDB.archived_on.is_(None)
        ).first()
        
        if db_person:
            return self._db_to_pydantic(db_person)
        return None
    
    async def update_person(self, person_id: int, person: Union[Youth, Leader, Parent]) -> Union[Youth, Leader, Parent]:
        if person.archived_on is not None:
            raise ValueError("Cannot update person with archived_on field")
        
        db_person = self.db.query(PersonDB).filter(
            PersonDB.id == person_id,
            PersonDB.archived_on.is_(None)
        ).first()
        
        if not db_person:
            raise ValueError("Person not found")
        
        # Update fields
        db_person.first_name = person.first_name
        db_person.last_name = person.last_name
        db_person.phone_number = person.phone_number
        db_person.sms_opt_out = getattr(person, 'sms_opt_out', False)
        
        if isinstance(person, Youth):
            db_person.grade = person.grade
            db_person.school_name = person.school_name
            db_person.birth_date = person.birth_date
            db_person.email = person.email
            db_person.emergency_contact_name = person.emergency_contact_name
            db_person.emergency_contact_phone = person.emergency_contact_phone
            db_person.emergency_contact_relationship = person.emergency_contact_relationship
            db_person.emergency_contact_2_name = person.emergency_contact_2_name
            db_person.emergency_contact_2_phone = person.emergency_contact_2_phone
            db_person.emergency_contact_2_relationship = person.emergency_contact_2_relationship
            db_person.allergies = person.allergies
            db_person.other_considerations = person.other_considerations
        elif isinstance(person, Leader):
            db_person.role = person.role
            db_person.birth_date = getattr(person, 'birth_date', None)
        elif isinstance(person, Parent):
            db_person.email = getattr(person, 'email', None)
            db_person.address = getattr(person, 'address', None)
            db_person.birth_date = getattr(person, 'birth_date', None)
        
        self.db.commit()
        self.db.refresh(db_person)
        
        return self._db_to_pydantic(db_person)
    
    async def archive_person(self, person_id: int) -> bool:
        db_person = self.db.query(PersonDB).filter(PersonDB.id == person_id).first()
        if db_person:
            db_person.archived_on = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False
    
    async def get_all_youth(self) -> List[Youth]:
        db_persons = self.db.query(PersonDB).filter(
            PersonDB.person_type == "youth",
            PersonDB.archived_on.is_(None)
        ).all()
        
        return [self._db_to_pydantic(db_person) for db_person in db_persons]
    
    async def get_all_leaders(self) -> List[Leader]:
        db_persons = self.db.query(PersonDB).filter(
            PersonDB.person_type == "leader",
            PersonDB.archived_on.is_(None)
        ).all()
        
        return [self._db_to_pydantic(db_person) for db_person in db_persons]

    # New unified person management methods
    async def create_person_unified(self, person: PersonCreate) -> dict:
        """Create any type of person (youth, leader, parent) using unified model"""
        db_person = PersonDB(
            first_name=person.first_name,
            last_name=person.last_name,
            phone_number=person.phone_number,
            address=person.address if hasattr(person, 'address') else None,
            person_type=person.person_type,
            sms_consent=person.sms_consent if hasattr(person, 'sms_consent') else True,
            sms_opt_out=person.sms_opt_out if hasattr(person, 'sms_opt_out') else False
        )
        
        # Add type-specific fields
        if person.person_type == "youth":
            db_person.grade = person.grade
            db_person.school_name = person.school_name
            db_person.birth_date = person.birth_date
            db_person.email = person.email
            db_person.emergency_contact_name = person.emergency_contact_name
            db_person.emergency_contact_phone = person.emergency_contact_phone
            db_person.emergency_contact_relationship = person.emergency_contact_relationship
            db_person.emergency_contact_2_name = person.emergency_contact_2_name
            db_person.emergency_contact_2_phone = person.emergency_contact_2_phone
            db_person.emergency_contact_2_relationship = person.emergency_contact_2_relationship
            db_person.allergies = person.allergies
            db_person.other_considerations = person.other_considerations
        elif person.person_type == "leader":
            db_person.role = person.role
            db_person.birth_date = person.birth_date
            db_person.email = person.email
        elif person.person_type == "parent":
            # Parent-specific fields (address already set above)
            db_person.email = person.email if hasattr(person, 'email') else None
            db_person.birth_date = person.birth_date if hasattr(person, 'birth_date') else None
        
        self.db.add(db_person)
        self.db.commit()
        self.db.refresh(db_person)
        
        return self._db_to_dict(db_person)
    
    async def update_person_unified(self, person_id: int, person_update: PersonUpdate) -> dict:
        """Update any type of person using unified model"""
        db_person = self.db.query(PersonDB).filter(PersonDB.id == person_id).first()
        if not db_person:
            return None
            
        # Update fields that are provided
        for field, value in person_update.model_dump(exclude_unset=True).items():
            if hasattr(db_person, field):
                setattr(db_person, field, value)
        
        self.db.commit()
        self.db.refresh(db_person)
        
        return self._db_to_dict(db_person)
    
    async def get_person_unified(self, person_id: int) -> Optional[dict]:
        """Get any type of person as dictionary"""
        db_person = self.db.query(PersonDB).filter(
            PersonDB.id == person_id,
            PersonDB.archived_on.is_(None)
        ).first()
        
        if db_person:
            return self._db_to_dict(db_person)
        return None
    
    async def search_persons(self, person_type: str, query: Optional[str] = None) -> List[dict]:
        """Search persons by type with optional name/phone/email filter"""
        db_query = self.db.query(PersonDB).filter(
            PersonDB.person_type == person_type,
            PersonDB.archived_on.is_(None)
        )
        
        if query:
            search_filter = (
                PersonDB.first_name.ilike(f"%{query}%") |
                PersonDB.last_name.ilike(f"%{query}%") |
                PersonDB.phone_number.ilike(f"%{query}%")
            )
            if person_type != "parent":  # Only youth and leaders have email
                search_filter = search_filter | PersonDB.email.ilike(f"%{query}%")
            db_query = db_query.filter(search_filter)
        
        db_persons = db_query.all()
        return [self._db_to_dict(db_person) for db_person in db_persons]
    
    async def get_all_parents(self) -> List[dict]:
        """Get all parents"""
        db_persons = self.db.query(PersonDB).filter(
            PersonDB.person_type == "parent",
            PersonDB.archived_on.is_(None)
        ).all()
        
        return [self._db_to_dict(db_person) for db_person in db_persons]
    
    async def link_parent_to_youth(self, relationship: ParentYouthRelationshipCreate) -> dict:
        """Create parent-youth relationship"""
        # Verify parent exists
        parent = self.db.query(PersonDB).filter(
            PersonDB.id == relationship.parent_id,
            PersonDB.archived_on.is_(None)
        ).first()
        if not parent:
            raise ValueError("Parent not found")
        
        # Verify parent is actually a parent type
        if parent.person_type != "parent":
            raise ValueError("Person is not a parent type")
        
        # Verify youth exists and is a youth
        youth = self.db.query(PersonDB).filter(
            PersonDB.id == relationship.youth_id,
            PersonDB.person_type == "youth",
            PersonDB.archived_on.is_(None)
        ).first()
        if not youth:
            raise ValueError("Youth not found or is not a youth type")
        
        # Check if relationship already exists
        existing = self.db.query(ParentYouthRelationshipDB).filter(
            ParentYouthRelationshipDB.parent_id == relationship.parent_id,
            ParentYouthRelationshipDB.youth_id == relationship.youth_id
        ).first()
        if existing:
            raise ValueError("Parent is already linked to this youth")
        
        # Create relationship
        db_relationship = ParentYouthRelationshipDB(
            parent_id=relationship.parent_id,
            youth_id=relationship.youth_id,
            relationship_type=relationship.relationship_type,
            is_primary_contact=relationship.is_primary_contact
        )
        
        self.db.add(db_relationship)
        self.db.commit()
        self.db.refresh(db_relationship)
        
        return {
            "id": db_relationship.id,
            "parent_id": db_relationship.parent_id,
            "youth_id": db_relationship.youth_id,
            "relationship_type": db_relationship.relationship_type,
            "is_primary_contact": db_relationship.is_primary_contact,
            "created_at": db_relationship.created_at
        }
    
    async def unlink_parent_from_youth(self, parent_id: int, youth_id: int) -> bool:
        """Remove parent-youth relationship"""
        relationship = self.db.query(ParentYouthRelationshipDB).filter(
            ParentYouthRelationshipDB.parent_id == parent_id,
            ParentYouthRelationshipDB.youth_id == youth_id
        ).first()
        
        if relationship:
            self.db.delete(relationship)
            self.db.commit()
            return True
        return False
    
    async def get_parents_for_youth(self, youth_id: int) -> List[dict]:
        """Get all parents linked to a youth with relationship details"""
        # Verify youth exists
        youth = self.db.query(PersonDB).filter(
            PersonDB.id == youth_id,
            PersonDB.person_type == "youth",
            PersonDB.archived_on.is_(None)
        ).first()
        if not youth:
            raise ValueError("Youth not found")
        
        # Get relationships with parent details
        relationships = self.db.query(ParentYouthRelationshipDB, PersonDB).join(
            PersonDB, PersonDB.id == ParentYouthRelationshipDB.parent_id
        ).filter(
            ParentYouthRelationshipDB.youth_id == youth_id,
            PersonDB.archived_on.is_(None)
        ).all()
        
        results = []
        for relationship, parent in relationships:
            results.append({
                "id": relationship.id,
                "parent_id": relationship.parent_id,
                "youth_id": relationship.youth_id,
                "relationship_type": relationship.relationship_type,
                "is_primary_contact": relationship.is_primary_contact,
                "created_at": relationship.created_at,
                "parent": self._db_to_dict(parent)
            })
        
        return results
    
    async def get_youth_for_parent(self, parent_id: int) -> List[dict]:
        """Get all youth linked to a parent with relationship details"""
        # Verify parent exists
        parent = self.db.query(PersonDB).filter(
            PersonDB.id == parent_id,
            PersonDB.person_type == "parent",
            PersonDB.archived_on.is_(None)
        ).first()
        if not parent:
            raise ValueError("Parent not found")
        
        # Get relationships with youth details
        relationships = self.db.query(ParentYouthRelationshipDB, PersonDB).join(
            PersonDB, PersonDB.id == ParentYouthRelationshipDB.youth_id
        ).filter(
            ParentYouthRelationshipDB.parent_id == parent_id,
            PersonDB.archived_on.is_(None)
        ).all()
        
        results = []
        for relationship, youth in relationships:
            results.append({
                "id": relationship.id,
                "parent_id": relationship.parent_id,
                "youth_id": relationship.youth_id,
                "relationship_type": relationship.relationship_type,
                "is_primary_contact": relationship.is_primary_contact,
                "created_at": relationship.created_at,
                "youth": self._db_to_dict(youth)
            })
        
        return results
    
    def _db_to_dict(self, db_person: PersonDB) -> dict:
        """Convert database model to dictionary"""
        result = {
            "id": db_person.id,
            "first_name": db_person.first_name,
            "last_name": db_person.last_name,
            "phone_number": db_person.phone_number,
            "phone": db_person.phone_number,  # Alias for parents
            "address": db_person.address,
            "archived_on": db_person.archived_on,
            "person_type": db_person.person_type,
            "sms_consent": db_person.sms_consent,
            "sms_opt_out": db_person.sms_opt_out,
            "created_at": db_person.created_at,
            "updated_at": db_person.updated_at
        }
        
        # Add type-specific fields
        if db_person.person_type == "youth":
            result.update({
                "grade": db_person.grade,
                "school_name": db_person.school_name,
                "birth_date": db_person.birth_date,
                "email": db_person.email,
                "emergency_contact_name": db_person.emergency_contact_name,
                "emergency_contact_phone": db_person.emergency_contact_phone,
                "emergency_contact_relationship": db_person.emergency_contact_relationship,
                "emergency_contact_2_name": db_person.emergency_contact_2_name,
                "emergency_contact_2_phone": db_person.emergency_contact_2_phone,
                "emergency_contact_2_relationship": db_person.emergency_contact_2_relationship,
                "allergies": db_person.allergies,
                "other_considerations": db_person.other_considerations
            })
        elif db_person.person_type == "leader":
            result.update({
                "role": db_person.role,
                "birth_date": db_person.birth_date,
                "email": db_person.email
            })
        
        return result

class PostgreSQLEventRepository(EventRepository):
    """PostgreSQL implementation for production"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _db_to_pydantic(self, db_event: EventDB) -> Event:
        """Convert database model to Pydantic model"""
        from app.db_models import EventPersonDB
        
        # Load attendance records
        event_persons = self.db.query(EventPersonDB).filter(
            EventPersonDB.event_id == db_event.id
        ).all()
        
        youth = []
        leaders = []
        
        for ep in event_persons:
            event_person = EventPerson(
                person_id=ep.person_id,
                check_in=ep.check_in,
                check_out=ep.check_out
            )
            
            if ep.person_type == "youth":
                youth.append(event_person)
            else:
                leaders.append(event_person)
        
        return Event(
            id=db_event.id,
            date=db_event.date,
            name=db_event.name,
            desc=db_event.desc,
            start_time=db_event.start_time,
            end_time=db_event.end_time,
            location=db_event.location,
            start_datetime=db_event.start_datetime,  # Include new datetime fields
            end_datetime=db_event.end_datetime,      # Include new datetime fields
            youth=youth,
            leaders=leaders
        )
    
    async def create_event(self, event: EventCreate) -> Event:
        db_event = EventDB(
            # Don't set ID, let PostgreSQL auto-generate it
            date=event.date,
            name=event.name,
            desc=event.desc,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location,
            start_datetime=event.start_datetime,  # Auto-generated by EventCreate
            end_datetime=event.end_datetime       # Auto-generated by EventCreate
        )
        
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        
        return self._db_to_pydantic(db_event)
    
    async def get_event(self, event_id: int) -> Optional[Event]:
        db_event = self.db.query(EventDB).filter(EventDB.id == event_id).first()
        if db_event:
            return self._db_to_pydantic(db_event)
        return None
    
    async def get_events(self, days: Optional[int] = None, name: Optional[str] = None) -> List[Event]:
        import time
        start_time = time.time()
        
        query = self.db.query(EventDB)
        
        if days is not None:
            cutoff = dt.date.today() - dt.timedelta(days=days)
            query = query.filter(EventDB.date >= cutoff.isoformat())
        
        if name:
            query = query.filter(EventDB.name.ilike(f"%{name}%"))
        
        db_events = query.all()
        query_time = time.time()
        
        result = [self._db_to_pydantic(db_event) for db_event in db_events]
        end_time = time.time()
        
        print(f"⏱️ Event query took {query_time - start_time:.3f}s, conversion took {end_time - query_time:.3f}s, total: {end_time - start_time:.3f}s")
        return result
    
    async def update_event(self, event_id: int, event_update: EventUpdate) -> Event:
        db_event = self.db.query(EventDB).filter(EventDB.id == event_id).first()
        if not db_event:
            raise ValueError(f"Event with ID {event_id} not found")
        
        # Apply updates from EventUpdate
        update_data = event_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(db_event, field, value)
        
        self.db.commit()
        self.db.refresh(db_event)
        
        return self._db_to_pydantic(db_event)
    
    async def delete_event(self, event_id: int) -> bool:
        db_event = self.db.query(EventDB).filter(EventDB.id == event_id).first()
        if not db_event:
            return False
        
        # Check if event has any event_persons
        if await self.has_event_persons(event_id):
            raise ValueError("Cannot delete event that has attendance records")
        
        self.db.delete(db_event)
        self.db.commit()
        return True
    
    async def has_event_persons(self, event_id: int) -> bool:
        """Check if event has any event_persons attached"""
        from app.db_models import EventPersonDB
        
        count = self.db.query(EventPersonDB).filter(EventPersonDB.event_id == event_id).count()
        return count > 0

class PostgreSQLUserRepository(UserRepository):
    """PostgreSQL implementation for user management"""
    
    def __init__(self, db: Session):
        self.db = db
        # Initialize admin user if no users exist (production safety)
        self._ensure_admin_exists()
    
    def _ensure_admin_exists(self):
        """Ensure admin user exists in production database"""
        import os
        import bcrypt
        from app.db_models import UserDB
        
        # Check if any users exist
        user_count = self.db.query(UserDB).count()
        if user_count > 0:
            return  # Users already exist, don't initialize
            
        # Get admin credentials from environment
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not admin_password:
            print("🚨 WARNING: No ADMIN_PASSWORD set in production environment!")
            print("🚨 Cannot initialize admin user. Set ADMIN_PASSWORD environment variable.")
            return
            
        # Hash the password securely
        password_bytes = admin_password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        # Create admin user in database
        admin_user = UserDB(
            username=admin_username,
            password_hash=password_hash,
            role="admin"
        )
        
        try:
            self.db.add(admin_user)
            self.db.commit()
            print(f"✅ Initialized PostgreSQL admin user: {admin_username}")
        except Exception as e:
            self.db.rollback()
            print(f"❌ Failed to initialize admin user: {e}")
    
    def _db_to_pydantic(self, db_user: UserDB) -> User:
        """Convert database model to Pydantic model"""
        return User(
            id=db_user.id,
            username=db_user.username,
            password_hash=db_user.password_hash,
            role=db_user.role,
            created_at=db_user.created_at
        )
    
    def _pydantic_to_db(self, user: User) -> UserDB:
        """Convert Pydantic model to database model"""
        return UserDB(
            # Don't set ID, let PostgreSQL auto-generate it
            username=user.username,
            password_hash=user.password_hash,
            role=user.role
        )
    
    async def create_user(self, user: User) -> User:
        # Check for duplicate username
        existing = self.db.query(UserDB).filter(UserDB.username == user.username).first()
        if existing:
            raise ValueError(f"Username '{user.username}' already exists")
        
        db_user = self._pydantic_to_db(user)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return self._db_to_pydantic(db_user)
    
    async def get_user(self, user_id: int) -> Optional[User]:
        db_user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if db_user:
            return self._db_to_pydantic(db_user)
        return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        db_user = self.db.query(UserDB).filter(UserDB.username == username).first()
        if db_user:
            return self._db_to_pydantic(db_user)
        return None
    
    async def get_all_users(self) -> List[User]:
        db_users = self.db.query(UserDB).all()
        return [self._db_to_pydantic(db_user) for db_user in db_users]
    
    async def update_user(self, user_id: int, user: User) -> User:
        db_user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not db_user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check for duplicate username (excluding current user)
        existing = self.db.query(UserDB).filter(
            UserDB.username == user.username,
            UserDB.id != user_id
        ).first()
        if existing:
            raise ValueError(f"Username '{user.username}' already exists")
        
        # Update fields
        db_user.username = user.username
        db_user.password_hash = user.password_hash
        db_user.role = user.role
        
        self.db.commit()
        self.db.refresh(db_user)
        
        return self._db_to_pydantic(db_user)
    
    async def delete_user(self, user_id: int) -> bool:
        db_user = self.db.query(UserDB).filter(UserDB.id == user_id).first()
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True


class PostgreSQLMessageGroupRepository(MessageGroupRepository):
    """PostgreSQL implementation for message group management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _db_to_pydantic_group(self, db_group: MessageGroupDB) -> MessageGroup:
        """Convert database model to Pydantic model"""
        # Calculate member count
        member_count = self.db.query(MessageGroupMembershipDB).filter(
            MessageGroupMembershipDB.group_id == db_group.id
        ).count()
        
        return MessageGroup(
            id=db_group.id,
            name=db_group.name,
            description=db_group.description,
            is_active=db_group.is_active,
            created_by=db_group.created_by,
            member_count=member_count,
            created_at=db_group.created_at,
            updated_at=db_group.updated_at
        )
    
    def _db_to_pydantic_membership(self, db_membership: MessageGroupMembershipDB) -> MessageGroupMembership:
        """Convert database membership model to Pydantic model"""
        return MessageGroupMembership(
            id=db_membership.id,
            group_id=db_membership.group_id,
            person_id=db_membership.person_id,
            added_by=db_membership.added_by,
            joined_at=db_membership.joined_at
        )
    
    async def create_group(self, group: MessageGroupCreate, created_by: int) -> MessageGroup:
        """Create a new message group"""
        # Check for duplicate name for this user
        if await self.group_name_exists(group.name, created_by):
            raise ValueError(f"Group with name '{group.name}' already exists")
        
        try:
            db_group = MessageGroupDB(
                name=group.name,
                description=group.description,
                is_active=group.is_active,
                created_by=created_by
            )
            
            self.db.add(db_group)
            self.db.commit()
            self.db.refresh(db_group)
            
            return self._db_to_pydantic_group(db_group)
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def get_group(self, group_id: int, created_by: int) -> Optional[MessageGroup]:
        """Get a message group by ID (user-scoped)"""
        db_group = self.db.query(MessageGroupDB).filter(
            MessageGroupDB.id == group_id,
            MessageGroupDB.created_by == created_by
        ).first()
        
        if db_group:
            return self._db_to_pydantic_group(db_group)
        return None
    
    async def get_all_groups(self, created_by: int) -> List[MessageGroup]:
        """Get all message groups for a user"""
        db_groups = self.db.query(MessageGroupDB).filter(
            MessageGroupDB.created_by == created_by
        ).all()
        
        return [self._db_to_pydantic_group(db_group) for db_group in db_groups]
    
    async def update_group(self, group_id: int, group_update: MessageGroupUpdate, created_by: int) -> Optional[MessageGroup]:
        """Update a message group"""
        db_group = self.db.query(MessageGroupDB).filter(
            MessageGroupDB.id == group_id,
            MessageGroupDB.created_by == created_by
        ).first()
        
        if not db_group:
            return None
        
        try:
            # Check for duplicate name if name is being updated
            if group_update.name is not None and group_update.name != db_group.name:
                if await self.group_name_exists(group_update.name, created_by, exclude_id=group_id):
                    raise ValueError(f"Group with name '{group_update.name}' already exists")
            
            # Update fields
            if group_update.name is not None:
                db_group.name = group_update.name
            if group_update.description is not None:
                db_group.description = group_update.description
            if group_update.is_active is not None:
                db_group.is_active = group_update.is_active
            
            db_group.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(db_group)
            
            return self._db_to_pydantic_group(db_group)
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def delete_group(self, group_id: int, created_by: int) -> bool:
        """Delete a message group and all its memberships"""
        db_group = self.db.query(MessageGroupDB).filter(
            MessageGroupDB.id == group_id,
            MessageGroupDB.created_by == created_by
        ).first()
        
        if not db_group:
            return False
        
        try:
            # Delete all memberships first (handled by cascade in DB model)
            self.db.delete(db_group)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def group_name_exists(self, name: str, created_by: int, exclude_id: Optional[int] = None) -> bool:
        """Check if a group name already exists for a user"""
        query = self.db.query(MessageGroupDB).filter(
            MessageGroupDB.name == name,
            MessageGroupDB.created_by == created_by
        )
        
        if exclude_id is not None:
            query = query.filter(MessageGroupDB.id != exclude_id)
        
        return query.first() is not None
    
    async def add_member(self, group_id: int, person_id: int, added_by: int) -> Optional[MessageGroupMembership]:
        """Add a person to a message group"""
        # Check if already a member
        if await self.is_member(group_id, person_id):
            raise ValueError("Person is already a member of this group")
        
        try:
            db_membership = MessageGroupMembershipDB(
                group_id=group_id,
                person_id=person_id,
                added_by=added_by
            )
            
            self.db.add(db_membership)
            self.db.commit()
            self.db.refresh(db_membership)
            
            return self._db_to_pydantic_membership(db_membership)
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def remove_member(self, group_id: int, person_id: int) -> bool:
        """Remove a person from a message group"""
        db_membership = self.db.query(MessageGroupMembershipDB).filter(
            MessageGroupMembershipDB.group_id == group_id,
            MessageGroupMembershipDB.person_id == person_id
        ).first()
        
        if not db_membership:
            return False
        
        try:
            self.db.delete(db_membership)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def get_group_members(self, group_id: int) -> List[MessageGroupMembership]:
        """Get all members of a message group"""
        db_memberships = self.db.query(MessageGroupMembershipDB).filter(
            MessageGroupMembershipDB.group_id == group_id
        ).all()
        
        return [self._db_to_pydantic_membership(db_membership) for db_membership in db_memberships]
    
    async def get_group_members_with_person(self, group_id: int) -> List[MessageGroupMembershipWithPerson]:
        """Get all members of a message group with full person details"""
        # Get the person repository to fetch person details
        from app.repositories import get_person_repository
        person_repo = get_person_repository(self.db)
        
        # Get basic memberships first
        memberships = await self.get_group_members(group_id)
        
        result = []
        for membership in memberships:
            # Fetch full person details
            person = await person_repo.get_person(membership.person_id)
            if person:
                # Create appropriate typed person object with person_type field
                if isinstance(person, Youth):
                    person_with_type = YouthWithType(**person.model_dump(), person_type="youth")
                elif isinstance(person, Leader):
                    person_with_type = LeaderWithType(**person.model_dump(), person_type="leader")
                elif isinstance(person, Parent):
                    person_with_type = ParentWithType(**person.model_dump())
                else:
                    # Skip unknown person types
                    continue
                
                # Create the combined model
                membership_with_person = MessageGroupMembershipWithPerson(
                    **membership.model_dump(),
                    person=person_with_type
                )
                result.append(membership_with_person)
        
        return result
    
    async def is_member(self, group_id: int, person_id: int) -> bool:
        """Check if a person is a member of a group"""
        db_membership = self.db.query(MessageGroupMembershipDB).filter(
            MessageGroupMembershipDB.group_id == group_id,
            MessageGroupMembershipDB.person_id == person_id
        ).first()
        
        return db_membership is not None
    
    async def add_multiple_members(self, group_id: int, person_ids: List[int], added_by: int) -> BulkGroupMembershipResponse:
        """Add multiple people to a message group"""
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