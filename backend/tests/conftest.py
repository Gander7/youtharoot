"""
Pytest configuration and shared fixtures for PostgreSQL integration tests.
"""
import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import settings

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-scoped fixture to set up and clean up test database.
    Only runs when using PostgreSQL.
    """
    if settings.DATABASE_TYPE != "postgresql":
        yield
        return
    
    # Create engine for test database
    engine = create_engine(settings.database_url)
    
    # Import models to register them with Base
    from app import db_models
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def clean_database():
    """
    Function-scoped fixture to clean database between tests.
    Only runs when using PostgreSQL.
    """
    if settings.DATABASE_TYPE != "postgresql":
        yield
        return
    
    # Clean before test
    _clean_test_database()
    
    yield
    
    # Clean after test
    _clean_test_database()

def _clean_test_database():
    """Clean all data from test database tables."""
    if settings.DATABASE_TYPE != "postgresql":
        return
    
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Start a new transaction
            trans = conn.begin()
            try:
                # Disable foreign key checks temporarily
                conn.execute(text("SET session_replication_role = replica;"))
                
                # Get all table names
                tables = [
                    "event_persons",
                    "events", 
                    "users",
                    "message_group_membership",
                    "messages",
                    "message_templates", 
                    "message_groups",
                    "persons"
                ]
                
                # Truncate all tables
                for table in tables:
                    try:
                        conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
                    except Exception as e:
                        # Table might not exist yet, ignore
                        pass
                
                # Re-enable foreign key checks
                conn.execute(text("SET session_replication_role = DEFAULT;"))
                
                # Commit the transaction
                trans.commit()
                
            except Exception as e:
                # Rollback on any error
                trans.rollback()
                print(f"Database cleaning error (rolled back): {e}")
                
    except Exception as e:
        print(f"Database cleaning connection error: {e}")
    finally:
        engine.dispose()