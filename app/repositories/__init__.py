from app.repositories.base import PersonRepository, EventRepository
from app.repositories.memory import InMemoryPersonRepository, InMemoryEventRepository
from app.repositories.postgresql import PostgreSQLPersonRepository, PostgreSQLEventRepository
from app.config import settings
from app.database import get_db
from sqlalchemy.orm import Session

# Global repository instances
person_repo: PersonRepository = None
event_repo: EventRepository = None

def init_repositories():
    """Initialize repositories based on configuration"""
    global person_repo, event_repo
    
    if settings.DATABASE_TYPE == "memory":
        person_repo = InMemoryPersonRepository()
        event_repo = InMemoryEventRepository()
        print("✅ Initialized in-memory repositories")
    else:
        # PostgreSQL repositories will be created per-request with dependency injection
        print("✅ PostgreSQL repositories will be created per-request")

def get_person_repository(db: Session = None) -> PersonRepository:
    """Get person repository instance"""
    if settings.DATABASE_TYPE == "memory":
        return person_repo
    else:
        if db is None:
            raise ValueError("Database session required for PostgreSQL repository")
        return PostgreSQLPersonRepository(db)

def get_event_repository(db: Session = None) -> EventRepository:
    """Get event repository instance"""
    if settings.DATABASE_TYPE == "memory":
        return event_repo
    else:
        if db is None:
            raise ValueError("Database session required for PostgreSQL repository")
        return PostgreSQLEventRepository(db)