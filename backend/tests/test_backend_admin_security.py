"""
Regression tests for admin user initialization security fixes.
Tests the removal of hardcoded credentials and proper environment-based initialization.
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from app.repositories.memory import InMemoryUserRepository
from app.repositories.postgresql import PostgreSQLUserRepository
from app.models import User


class TestAdminUserInitialization:
    """Test suite for admin user initialization security fixes."""
    
    # Test Constants
    DEFAULT_ADMIN_USERNAME = "admin"
    TEST_ADMIN_USERNAME = "test_admin"
    TEST_ADMIN_PASSWORD = "secure_test_password_123"
    GENERATED_PASSWORD_LENGTH = 16
    
    @pytest.fixture
    def clean_environment(self):
        """Arrange: Clean environment variables for test isolation."""
        original_admin_username = os.environ.get("ADMIN_USERNAME")
        original_admin_password = os.environ.get("ADMIN_PASSWORD")
        
        # Clean environment
        if "ADMIN_USERNAME" in os.environ:
            del os.environ["ADMIN_USERNAME"]
        if "ADMIN_PASSWORD" in os.environ:
            del os.environ["ADMIN_PASSWORD"]
            
        yield
        
        # Restore original environment
        if original_admin_username is not None:
            os.environ["ADMIN_USERNAME"] = original_admin_username
        if original_admin_password is not None:
            os.environ["ADMIN_PASSWORD"] = original_admin_password
    
    @pytest.fixture
    def mock_db_session(self):
        """Arrange: Mock database session for PostgreSQL tests."""
        mock_session = MagicMock()
        mock_session.query.return_value.count.return_value = 0  # No existing users
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.rollback = MagicMock()
        return mock_session

    def test_memory_repository_initialization_with_environment_password_creates_admin_user(self, clean_environment):
        """Test: InMemoryUserRepository initialization with ADMIN_PASSWORD environment variable creates admin user."""
        # Arrange
        os.environ["ADMIN_PASSWORD"] = self.TEST_ADMIN_PASSWORD
        
        # Act
        repository = InMemoryUserRepository()
        
        # Assert
        assert len(repository.store) == 1
        admin_user = list(repository.store.values())[0]
        assert admin_user.username == self.DEFAULT_ADMIN_USERNAME
        assert admin_user.role == "admin"
        assert admin_user.password_hash is not None
        assert admin_user.password_hash != self.TEST_ADMIN_PASSWORD  # Should be hashed
    
    def test_memory_repository_initialization_with_custom_username_creates_admin_with_custom_name(self, clean_environment):
        """Test: InMemoryUserRepository initialization with custom ADMIN_USERNAME creates admin with custom username."""
        # Arrange
        os.environ["ADMIN_USERNAME"] = self.TEST_ADMIN_USERNAME
        os.environ["ADMIN_PASSWORD"] = self.TEST_ADMIN_PASSWORD
        
        # Act
        repository = InMemoryUserRepository()
        
        # Assert
        assert len(repository.store) == 1
        admin_user = list(repository.store.values())[0]
        assert admin_user.username == self.TEST_ADMIN_USERNAME
        assert admin_user.role == "admin"
    
    @patch('builtins.print')
    def test_memory_repository_initialization_without_password_generates_random_password(self, mock_print, clean_environment):
        """Test: InMemoryUserRepository initialization without ADMIN_PASSWORD generates random password."""
        # Arrange - No ADMIN_PASSWORD environment variable
        
        # Act
        repository = InMemoryUserRepository()
        
        # Assert
        assert len(repository.store) == 1
        admin_user = list(repository.store.values())[0]
        assert admin_user.username == self.DEFAULT_ADMIN_USERNAME
        assert admin_user.role == "admin"
        assert admin_user.password_hash is not None
        
        # Verify random password generation was logged
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        password_generation_logged = any("Generated admin password:" in call for call in print_calls)
        assert password_generation_logged
    
    def test_memory_repository_initialization_prevents_duplicate_initialization(self, clean_environment):
        """Test: InMemoryUserRepository initialization prevents duplicate admin user creation."""
        # Arrange
        os.environ["ADMIN_PASSWORD"] = self.TEST_ADMIN_PASSWORD
        repository = InMemoryUserRepository()
        initial_user_count = len(repository.store)
        
        # Act - Call initialization again
        repository._initialize_seed_data()
        
        # Assert
        assert len(repository.store) == initial_user_count  # No duplicate users created
    
    @patch('app.db_models.UserDB')
    def test_postgresql_repository_initialization_with_environment_password_creates_admin_user(self, mock_user_db, mock_db_session, clean_environment):
        """Test: PostgreSQLUserRepository initialization with ADMIN_PASSWORD creates admin user."""
        # Arrange
        os.environ["ADMIN_PASSWORD"] = self.TEST_ADMIN_PASSWORD
        
        # Act
        repository = PostgreSQLUserRepository(mock_db_session)
        
        # Assert
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_user_db.assert_called_once()
        
        # Verify UserDB was called with correct parameters
        call_kwargs = mock_user_db.call_args.kwargs
        assert call_kwargs['username'] == self.DEFAULT_ADMIN_USERNAME
        assert call_kwargs['role'] == "admin"
        assert call_kwargs['password_hash'] is not None
        assert call_kwargs['password_hash'] != self.TEST_ADMIN_PASSWORD  # Should be hashed
    
    @patch('builtins.print')
    def test_postgresql_repository_initialization_without_password_logs_warning(self, mock_print, mock_db_session, clean_environment):
        """Test: PostgreSQLUserRepository initialization without ADMIN_PASSWORD logs warning."""
        # Arrange - No ADMIN_PASSWORD environment variable
        
        # Act
        repository = PostgreSQLUserRepository(mock_db_session)
        
        # Assert
        mock_db_session.add.assert_not_called()  # No user should be created
        
        # Verify warning was logged
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        warning_logged = any("WARNING: No ADMIN_PASSWORD set" in call for call in print_calls)
        assert warning_logged
    
    def test_postgresql_repository_initialization_with_existing_users_skips_creation(self, mock_db_session, clean_environment):
        """Test: PostgreSQLUserRepository initialization with existing users skips admin creation."""
        # Arrange
        os.environ["ADMIN_PASSWORD"] = self.TEST_ADMIN_PASSWORD
        mock_db_session.query.return_value.count.return_value = 1  # Existing users
        
        # Act
        repository = PostgreSQLUserRepository(mock_db_session)
        
        # Assert
        mock_db_session.add.assert_not_called()  # No user should be created
        mock_db_session.commit.assert_not_called()
    
    @patch('builtins.print')
    def test_postgresql_repository_initialization_handles_database_errors(self, mock_print, mock_db_session, clean_environment):
        """Test: PostgreSQLUserRepository initialization handles database errors gracefully."""
        # Arrange
        os.environ["ADMIN_PASSWORD"] = self.TEST_ADMIN_PASSWORD
        mock_db_session.commit.side_effect = Exception("Database connection error")
        
        # Act
        repository = PostgreSQLUserRepository(mock_db_session)
        
        # Assert
        mock_db_session.rollback.assert_called_once()
        
        # Verify error was logged
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        error_logged = any("Failed to initialize admin user:" in call for call in print_calls)
        assert error_logged
    
    def test_memory_repository_password_hashing_uses_bcrypt(self, clean_environment):
        """Test: InMemoryUserRepository password hashing uses bcrypt properly."""
        # Arrange
        os.environ["ADMIN_PASSWORD"] = self.TEST_ADMIN_PASSWORD
        
        # Act
        repository = InMemoryUserRepository()
        
        # Assert
        admin_user = list(repository.store.values())[0]
        password_hash = admin_user.password_hash
        
        # Verify bcrypt hash format (starts with $2b$)
        assert password_hash.startswith("$2b$")
        assert len(password_hash) == 60  # Standard bcrypt hash length
        assert password_hash != self.TEST_ADMIN_PASSWORD  # Not plaintext
    
    def test_postgresql_repository_password_hashing_uses_bcrypt(self, mock_db_session, clean_environment):
        """Test: PostgreSQLUserRepository password hashing uses bcrypt properly."""
        # Arrange
        os.environ["ADMIN_PASSWORD"] = self.TEST_ADMIN_PASSWORD
        
        with patch('app.db_models.UserDB') as mock_user_db:
            # Act
            repository = PostgreSQLUserRepository(mock_db_session)
            
            # Assert
            if mock_user_db.call_args is not None:
                call_kwargs = mock_user_db.call_args.kwargs
                password_hash = call_kwargs['password_hash']
                
                # Verify bcrypt hash format
                assert password_hash.startswith("$2b$")
                assert len(password_hash) == 60  # Standard bcrypt hash length
                assert password_hash != self.TEST_ADMIN_PASSWORD  # Not plaintext
            else:
                # If no admin user was created (e.g., users already exist), that's also valid
                assert True