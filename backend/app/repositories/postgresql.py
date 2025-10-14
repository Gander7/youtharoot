from typing import List, Optional, Union
from sqlalchemy.orm import Session
from app.repositories.base import PersonRepository, EventRepository, UserRepository
from app.models import Youth, Leader, Event, EventPerson, User
from app.db_models import PersonDB, EventDB, UserDB
from datetime import datetime, timezone
import datetime as dt

class PostgreSQLPersonRepository(PersonRepository):
    """PostgreSQL implementation for production"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _db_to_pydantic(self, db_person: PersonDB) -> Union[Youth, Leader]:
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
                emergency_contact_name=db_person.emergency_contact_name or "",
                emergency_contact_phone=db_person.emergency_contact_phone or "",
                emergency_contact_relationship=db_person.emergency_contact_relationship or ""
            )
        else:
            return Leader(
                **base_data,
                role=db_person.role,
                birth_date=db_person.birth_date
            )
    
    def _pydantic_to_db(self, person: Union[Youth, Leader]) -> PersonDB:
        """Convert Pydantic model to database model"""
        db_person = PersonDB(
            # Don't set ID, let PostgreSQL auto-generate it
            first_name=person.first_name,
            last_name=person.last_name,
            phone_number=person.phone_number,
            archived_on=person.archived_on,
            person_type="youth" if isinstance(person, Youth) else "leader"
        )
        
        if isinstance(person, Youth):
            db_person.grade = person.grade
            db_person.school_name = person.school_name
            db_person.birth_date = person.birth_date
            db_person.emergency_contact_name = person.emergency_contact_name
            db_person.emergency_contact_phone = person.emergency_contact_phone
            db_person.emergency_contact_relationship = person.emergency_contact_relationship
        else:
            db_person.role = person.role
            db_person.birth_date = person.birth_date
        
        return db_person
    
    async def create_person(self, person: Union[Youth, Leader]) -> Union[Youth, Leader]:
        if person.archived_on is not None:
            raise ValueError("Cannot create archived person")
        
        db_person = self._pydantic_to_db(person)
        self.db.add(db_person)
        self.db.commit()
        self.db.refresh(db_person)
        
        return self._db_to_pydantic(db_person)
    
    async def get_person(self, person_id: int) -> Optional[Union[Youth, Leader]]:
        db_person = self.db.query(PersonDB).filter(
            PersonDB.id == person_id,
            PersonDB.archived_on.is_(None)
        ).first()
        
        if db_person:
            return self._db_to_pydantic(db_person)
        return None
    
    async def update_person(self, person_id: int, person: Union[Youth, Leader]) -> Union[Youth, Leader]:
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
        
        if isinstance(person, Youth):
            db_person.grade = person.grade
            db_person.school_name = person.school_name
            db_person.birth_date = person.birth_date
            db_person.emergency_contact_name = person.emergency_contact_name
            db_person.emergency_contact_phone = person.emergency_contact_phone
            db_person.emergency_contact_relationship = person.emergency_contact_relationship
        else:
            db_person.role = person.role
            db_person.birth_date = person.birth_date
        
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
            youth=youth,
            leaders=leaders
        )
    
    async def create_event(self, event: Event) -> Event:
        db_event = EventDB(
            # Don't set ID, let PostgreSQL auto-generate it
            date=event.date,
            name=event.name,
            desc=event.desc,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location
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
    
    async def update_event(self, event_id: int, event: Event) -> Event:
        db_event = self.db.query(EventDB).filter(EventDB.id == event_id).first()
        if not db_event:
            raise ValueError(f"Event with ID {event_id} not found")
        
        # Update fields
        db_event.date = event.date
        db_event.name = event.name
        db_event.desc = event.desc
        db_event.start_time = event.start_time
        db_event.end_time = event.end_time
        db_event.location = event.location
        
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