from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
import pytz
from datetime import datetime, timezone

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
            # Evolution for persons table - add new youth fields
            print("🔄 Checking persons table schema...")
            
            # Check if email column exists
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'persons' AND column_name = 'email'
                  AND table_schema = current_schema()
            """))
            
            if not result.fetchone():
                print("🔄 Adding email column to persons table...")
                conn.execute(text("""
                    ALTER TABLE persons 
                    ADD COLUMN email VARCHAR(200)
                """))
                print("✅ Added email column to persons table")
            
            # Check if second emergency contact fields exist
            fields_to_add = [
                ('emergency_contact_2_name', 'VARCHAR(100)'),
                ('emergency_contact_2_phone', 'VARCHAR(20)'),
                ('emergency_contact_2_relationship', 'VARCHAR(50)'),
                ('allergies', 'TEXT'),
                ('other_considerations', 'TEXT')
            ]
            
            for field_name, field_type in fields_to_add:
                result = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'persons' AND column_name = '{field_name}'
                      AND table_schema = current_schema()
                """))
                
                if not result.fetchone():
                    print(f"🔄 Adding {field_name} column to persons table...")
                    conn.execute(text(f"""
                        ALTER TABLE persons 
                        ADD COLUMN {field_name} {field_type}
                    """))
                    print(f"✅ Added {field_name} column to persons table")
            
            # Evolution for messages table
            print("🔄 Checking messages table schema...")
            
            # Check if messages table exists and has the old schema
            result = conn.execute(text("""
                SELECT column_name, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'group_id'
                  AND table_schema = current_schema()
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
                      AND table_schema = current_schema()
                """))
                
                if not result.fetchone():
                    conn.execute(text("""
                        ALTER TABLE messages 
                        ADD COLUMN recipient_phone VARCHAR(20)
                    """))
                    print("✅ Added recipient_phone column to messages table")
                
                # Add recipient_person_id column if it doesn't exist
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'messages' AND column_name = 'recipient_person_id'
                      AND table_schema = current_schema()
                """))
                
                if not result.fetchone():
                    conn.execute(text("""
                        ALTER TABLE messages 
                        ADD COLUMN recipient_person_id BIGINT REFERENCES persons(id)
                    """))
                    print("✅ Added recipient_person_id column to messages table")
                
                print("🎉 Messages table schema evolution completed!")
            else:
                # Check for recipient_person_id even if group_id is already nullable
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'messages' AND column_name = 'recipient_person_id'
                      AND table_schema = current_schema()
                """))
                
                if not result.fetchone():
                    print("🔄 Adding recipient_person_id column to messages table...")
                    conn.execute(text("""
                        ALTER TABLE messages 
                        ADD COLUMN recipient_person_id BIGINT REFERENCES persons(id)
                    """))
                    print("✅ Added recipient_person_id column to messages table")
                else:
                    print("✅ Messages table schema is already up to date")
            
            # Evolution for events table - add new datetime fields
            print("🔄 Checking events table schema...")
            
            events_fields_to_check = [
                ('start_datetime', 'TIMESTAMP WITH TIME ZONE'),
                ('end_datetime', 'TIMESTAMP WITH TIME ZONE')
            ]
            
            for field_name, field_type in events_fields_to_check:
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='events' AND column_name='{field_name}'
                      AND table_schema = current_schema()
                """))
                
                if not result.fetchone():
                    print(f"🔄 Adding {field_name} column to events table...")
                    conn.execute(text(f"ALTER TABLE events ADD COLUMN {field_name} {field_type}"))
                    print(f"✅ Added {field_name} column to events table")
                else:
                    print(f"✅ {field_name} column already exists in events table")
            
            # Migrate existing event data to datetime fields
            migrate_existing_events_to_datetime(conn)
            
            # Evolution for persons table - add address field for parents
            print("🔄 Checking persons table for parent support...")
            
            persons_fields_to_check = [
                ('address', 'VARCHAR(500)'),
            ]
            
            for field_name, field_type in persons_fields_to_check:
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='persons' AND column_name='{field_name}'
                      AND table_schema = current_schema()
                """))
                
                if not result.fetchone():
                    print(f"🔄 Adding {field_name} column to persons table...")
                    conn.execute(text(f"ALTER TABLE persons ADD COLUMN {field_name} {field_type}"))
                    print(f"✅ Added {field_name} column to persons table")
                else:
                    print(f"✅ {field_name} column already exists in persons table")
            
            # Create parent-youth relationship table if it doesn't exist
            print("🔄 Checking parent-youth relationship table...")
            
            table_check = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'parent_youth_relationships' AND table_schema = current_schema()
            """))
            
            if not table_check.fetchone():
                print("🔄 Creating parent_youth_relationships table...")
                conn.execute(text("""
                    CREATE TABLE parent_youth_relationships (
                        id BIGSERIAL PRIMARY KEY,
                        parent_id BIGINT NOT NULL REFERENCES persons(id),
                        youth_id BIGINT NOT NULL REFERENCES persons(id),
                        relationship_type VARCHAR(50) NOT NULL DEFAULT 'parent',
                        is_primary_contact BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(parent_id, youth_id)
                    )
                """))
                print("✅ Created parent_youth_relationships table")
            else:
                print("✅ parent_youth_relationships table already exists")
            
            conn.commit()
            print("🎉 Schema evolution completed successfully!")
                
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


def migrate_existing_events_to_datetime(conn):
    """Migrate existing events from date/time strings to UTC datetimes"""
    
    print("🔄 Migrating existing events to UTC datetime format...")
    
    try:
        # First check if events table exists
        table_check = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'events' AND table_schema = current_schema()
        """))
        
        if not table_check.fetchone():
            print("✅ Events table doesn't exist yet - no migration needed")
            return
            
        # Get all events that don't have datetime fields populated
        result = conn.execute(text("""
            SELECT id, date, start_time, end_time 
            FROM events 
            WHERE start_datetime IS NULL OR end_datetime IS NULL
        """))
        
        events_to_migrate = result.fetchall()
        
        if not events_to_migrate:
            print("✅ No events need datetime migration")
            return
        
        halifax_tz = pytz.timezone('America/Halifax')
        migrated_count = 0
        
        for event_row in events_to_migrate:
            event_id, date_str, start_time_str, end_time_str = event_row
            
            try:
                # Convert Halifax date/time to UTC datetime
                start_datetime_utc, end_datetime_utc = convert_halifax_to_utc(
                    date_str, start_time_str, end_time_str, halifax_tz
                )
                
                # Update the event with UTC datetimes
                conn.execute(text("""
                    UPDATE events 
                    SET start_datetime = :start_dt, end_datetime = :end_dt 
                    WHERE id = :event_id
                """), {
                    "start_dt": start_datetime_utc,
                    "end_dt": end_datetime_utc,
                    "event_id": event_id
                })
                
                migrated_count += 1
                print(f"✅ Migrated event {event_id}: {date_str} {start_time_str}-{end_time_str} Halifax → UTC")
                
            except Exception as e:
                print(f"❌ Error migrating event {event_id}: {e}")
                # Continue with other events, don't fail the entire migration
                continue
        
        print(f"🎉 Successfully migrated {migrated_count} events to UTC datetime format!")
        
    except Exception as e:
        print(f"❌ Error during event datetime migration: {e}")
        raise


def convert_halifax_to_utc(date_str: str, start_time_str: str, end_time_str: str, halifax_tz):
    """Convert Halifax date/time strings to UTC datetime objects"""
    
    # Parse date and times
    date_parts = date_str.split('-')
    year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
    
    start_parts = start_time_str.split(':')
    start_hour, start_minute = int(start_parts[0]), int(start_parts[1])
    
    end_parts = end_time_str.split(':')
    end_hour, end_minute = int(end_parts[0]), int(end_parts[1])
    
    # Create Halifax datetime objects (handles DST automatically)
    start_halifax = halifax_tz.localize(datetime(year, month, day, start_hour, start_minute))
    end_halifax = halifax_tz.localize(datetime(year, month, day, end_hour, end_minute))
    
    # Convert to UTC
    start_utc = start_halifax.astimezone(timezone.utc)
    end_utc = end_halifax.astimezone(timezone.utc)
    
    return start_utc, end_utc


def migrate_events_to_datetime(events_data):
    """Helper function for testing - migrates event data"""
    halifax_tz = pytz.timezone('America/Halifax')
    migrated_events = []
    
    for event in events_data:
        start_utc, end_utc = convert_halifax_to_utc(
            event['date'], 
            event['start_time'], 
            event['end_time'], 
            halifax_tz
        )
        
        migrated_event = {
            **event,
            'start_datetime': start_utc,
            'end_datetime': end_utc
        }
        migrated_events.append(migrated_event)
    
    return migrated_events