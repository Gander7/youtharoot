from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
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
        
        # Import database models to ensure they're registered with Base
        from app import db_models
        
        # Create tables (this will update schema if needed)
        Base.metadata.create_all(bind=engine)
        
        print(f"✅ Connected to PostgreSQL: {settings.database_url}")
    else:
        print("✅ Using in-memory storage (development mode)")

def get_db():
    """Dependency to get database session"""
    if SessionLocal:
        import time
        start_time = time.time()
        
        db = SessionLocal()
        db_time = time.time()
        print(f"💾 Database session creation took {db_time - start_time:.3f}s")
        
        try:
            yield db
        finally:
            close_time = time.time()
            db.close()
            print(f"💾 Database session close took {close_time - db_time:.3f}s")
    else:
        # For in-memory mode, we don't need a session
        yield None