"""
Pytest configuration for Youth Attendance testing.

This file sets up PostgreSQL database testing with Docker,
ensuring proper test isolation and TDD workflow support.
"""

import pytest
import asyncio
import subprocess
import time
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from app.database import Base
from tests.test_config import (
    get_test_database_url, 
    is_docker_available, 
    is_test_db_running,
    DOCKER_COMPOSE_FILE,
    DOCKER_SERVICE_NAME
)


def pytest_configure(config):
    """Configure pytest with custom markers and setup."""
    config.addinivalue_line(
        "markers", "requires_docker: mark test as requiring Docker PostgreSQL"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their location and requirements."""
    for item in items:
        # Mark tests that use the database as requiring docker
        if "test_db" in getattr(item, "fixturenames", []):
            item.add_marker(pytest.mark.requires_docker)
        
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up the test database for the entire test session."""
    if not is_docker_available():
        pytest.skip("Docker is not available - skipping database tests")
    
    backend_path = Path(__file__).parent  # Current directory is backend/
    compose_file_path = backend_path / DOCKER_COMPOSE_FILE
    
    if not compose_file_path.exists():
        pytest.fail(f"Docker compose file not found: {compose_file_path}")
    
    # Start the database if not running
    if not is_test_db_running():
        print(f"\n🐳 Starting test database container...")
        try:
            subprocess.run([
                "docker", "compose", "-f", str(compose_file_path), 
                "up", "-d", DOCKER_SERVICE_NAME
            ], check=True, cwd=backend_path, capture_output=True)
            
            # Wait for database to be ready
            max_retries = 30
            for attempt in range(max_retries):
                try:
                    engine = create_engine(get_test_database_url())
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    print(f"✅ Test database is ready!")
                    break
                except OperationalError:
                    if attempt < max_retries - 1:
                        print(f"⏳ Waiting for database... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(2)
                    else:
                        pytest.fail("Test database failed to start within 60 seconds")
                        
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Failed to start test database: {e}")
    else:
        print(f"✅ Test database container is already running")
    
    yield
    
    # Cleanup: Stop the database container
    print(f"\n🧹 Cleaning up test database...")
    try:
        subprocess.run([
            "docker", "compose", "-f", str(compose_file_path),
            "down", "-v"  # Remove volumes to ensure clean state
        ], check=True, cwd=backend_path, capture_output=True)
        print(f"✅ Test database cleaned up")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Failed to cleanup test database: {e}")


@pytest.fixture(scope="function")
def test_db(setup_test_database):
    """
    Create a clean database session for each test.
    
    This fixture:
    1. Creates all tables fresh for each test
    2. Provides a database session
    3. Rolls back all changes after the test
    4. Ensures test isolation
    """
    engine = create_engine(get_test_database_url())
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        # Close session and clean up
        session.close()
        
        # Drop all tables to ensure clean state
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user(test_db):
    """Create a sample user for testing."""
    from app.db_models import UserDB
    
    user = UserDB(
        username="testadmin",
        password_hash="$2b$12$test_hash",
        role="admin"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def sample_person(test_db):
    """Create a sample person for testing."""
    from app.db_models import PersonDB
    
    person = PersonDB(
        first_name="John",
        last_name="Doe",
        person_type="youth",
        grade=10,
        school_name="Test High School",
        phone_number="+1234567890"
    )
    test_db.add(person)
    test_db.commit()
    test_db.refresh(person)
    return person


# Helper functions for test utilities
def reset_test_database():
    """Reset the test database to a clean state."""
    engine = create_engine(get_test_database_url())
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_test_engine():
    """Get a SQLAlchemy engine for the test database."""
    return create_engine(get_test_database_url())