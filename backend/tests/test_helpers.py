"""
Test helper utilities for API testing with authentication.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import User
from app.auth import get_current_user
from app.database import init_database
from app.repositories import init_repositories


def create_test_user(username: str = "test_admin", role: str = "admin", user_id: int = 999) -> User:
    """Create a test user object for mocking."""
    return User(
        id=user_id,
        username=username,
        password_hash="test_hash",  # Not used in mocking
        role=role,
        created_at=None
    )


def mock_current_user():
    """Mock function to replace get_current_user dependency."""
    return create_test_user()


def mock_current_admin():
    """Mock function to replace get_current_admin_user dependency.""" 
    return create_test_user(role="admin")


class AuthenticatedTestClient:
    """Test client with authentication dependency mocking."""
    
    def __init__(self, test_app=None):
        self.app = test_app or app
        self.client = None
        self.auth_enabled = False
        self.repos_initialized = False
    
    def _ensure_repositories_initialized(self):
        """Ensure repositories are initialized for testing."""
        if not self.repos_initialized:
            init_database()
            init_repositories()
            self.repos_initialized = True
    
    def enable_auth_override(self):
        """Enable authentication dependency override."""
        if not self.auth_enabled:
            # Override the authentication dependency
            self.app.dependency_overrides[get_current_user] = mock_current_user
            self.auth_enabled = True
        
        # Ensure repositories are initialized
        self._ensure_repositories_initialized()
            
        # Create new client with overridden dependencies
        self.client = TestClient(self.app)
        return self.client
    
    def disable_auth_override(self):
        """Disable authentication dependency override."""
        if self.auth_enabled:
            # Remove the override
            if get_current_user in self.app.dependency_overrides:
                del self.app.dependency_overrides[get_current_user]
            self.auth_enabled = False
        
        # Create new client without overrides
        self.client = TestClient(self.app)
        return self.client
    
    def get_client(self) -> TestClient:
        """Get the test client (with or without auth override)."""
        if self.client is None:
            self._ensure_repositories_initialized()
            self.client = TestClient(self.app)
        return self.client


# Global test client instance
_test_client = None


def get_test_client() -> AuthenticatedTestClient:
    """Get or create the global test client."""
    global _test_client
    if _test_client is None:
        _test_client = AuthenticatedTestClient()
    return _test_client


# Pytest fixtures for authentication testing
@pytest.fixture
def auth_client():
    """Pytest fixture that provides an authenticated test client."""
    test_client = get_test_client()
    client = test_client.enable_auth_override()
    yield client
    test_client.disable_auth_override()


@pytest.fixture  
def unauth_client():
    """Pytest fixture that provides an unauthenticated test client."""
    test_client = get_test_client()
    client = test_client.disable_auth_override()
    yield client


# Convenience functions for direct use
def get_authenticated_client() -> TestClient:
    """Get a test client with authentication mocked."""
    test_client = get_test_client()
    return test_client.enable_auth_override()


def get_unauthenticated_client() -> TestClient:
    """Get a test client without authentication."""
    test_client = get_test_client()
    return test_client.disable_auth_override()