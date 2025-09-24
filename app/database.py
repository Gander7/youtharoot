from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLAlchemy setup
engine = None
SessionLocal = None
Base = declarative_base()

def init_database():
    """Initialize database connection based on configuration"""
    global engine, SessionLocal
    
    if settings.DATABASE_TYPE == "postgresql" and settings.database_url:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        print(f"✅ Connected to PostgreSQL: {settings.database_url}")
    else:
        print("✅ Using in-memory storage (development mode)")

def get_db():
    """Dependency to get database session"""
    if SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        # For in-memory mode, we don't need a session
        yield None