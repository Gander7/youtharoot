from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLAlchemy setup
engine = None
SessionLocal = None
Base = declarative_base()

def evolve_schema(engine):
    """
    Apply schema evolution changes that can't be handled by create_all().
    This function is idempotent and safe to run multiple times.
    """
    try:
        with engine.connect() as conn:
            # Check if messages table exists and has the old schema
            result = conn.execute(text("""
                SELECT column_name, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'group_id'
            """))
            
            group_id_info = result.fetchone()
            
            if group_id_info and group_id_info[1] == 'NO':  # is_nullable = 'NO'
                print("🔄 Updating messages table schema to support individual messages...")
                
                # Make group_id nullable for individual messages
                conn.execute(text("ALTER TABLE messages ALTER COLUMN group_id DROP NOT NULL"))
                print("✅ Made group_id nullable in messages table")
                
                # Add recipient_phone column if it doesn't exist
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'messages' AND column_name = 'recipient_phone'
                """))
                
                if not result.fetchone():
                    conn.execute(text("""
                        ALTER TABLE messages 
                        ADD COLUMN recipient_phone VARCHAR(20)
                    """))
                    print("✅ Added recipient_phone column to messages table")
                
                conn.commit()
                print("🎉 Schema evolution completed successfully!")
            else:
                print("✅ Messages table schema is already up to date")
                
    except Exception as e:
        print(f"⚠️ Schema evolution error (this may be normal for new installations): {e}")


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
        
        # Apply schema evolution changes
        evolve_schema(engine)
        
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