"""
Test configuration for PostgreSQL database testing.

This configuration uses Docker PostgreSQL for better integration testing
that matches production database behavior.
"""

import os
from typing import Optional

# Test Database Configuration
TEST_DATABASE_URL = "postgresql://test_user:test_password@localhost:5433/test_youth_attendance"

# Docker configuration
DOCKER_COMPOSE_FILE = "docker-compose.test.yml"
DOCKER_SERVICE_NAME = "test-postgres"

def get_test_database_url() -> str:
    """Get the test database URL, with environment variable override."""
    return os.getenv("TEST_DATABASE_URL", TEST_DATABASE_URL)

def is_docker_available() -> bool:
    """Check if Docker is available on the system."""
    import subprocess
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_test_db_running() -> bool:
    """Check if the test database container is running."""
    import subprocess
    try:
        result = subprocess.run([
            "docker", "ps", "--filter", f"name={DOCKER_SERVICE_NAME}", 
            "--filter", "status=running", "--quiet"
        ], capture_output=True, text=True, check=True)
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False