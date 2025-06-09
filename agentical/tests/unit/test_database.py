"""
Database Unit Tests

This module contains unit tests for the database module, verifying correct
implementation of database operations, models, repositories, and optimization
features.

Tests cover:
- Database connection and initialization
- Model CRUD operations
- Repository pattern functionality
- Connection pooling and performance
- Caching and query optimization
- Error handling and recovery
"""

import os
import pytest
import logging
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from agentical.db import (
    Base, engine, SessionLocal, get_db, get_db_dependency,
    optimize_query, initialize_database, check_database_connection
)
from agentical.db.models import (
    BaseModel, User, Role
)
from agentical.db.repositories import (
    BaseRepository, UserRepository
)
from agentical.db.cache import (
    get_from_cache, set_in_cache, invalidate_cache, cached
)
from agentical.db.profiler import (
    profile_query, profile_sqlalchemy_query, QueryProfile
)

# Configure test database URL for isolated testing
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Create an isolated test database session."""
    # Create test engine and tables
    test_engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(test_engine)
    
    # Create session
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(test_engine)


@pytest.fixture
def user_repository(db_session):
    """Create a UserRepository with test session."""
    return UserRepository(db_session)


@pytest.mark.unit
class TestDatabaseConnection:
    """Test database connection and configuration."""
    
    def test_engine_configuration(self):
        """Test that database engine is properly configured."""
        assert engine is not None
        assert engine.pool is not None
        
        # Check for connection pooling
        if hasattr(engine.pool, '__class__'):
            assert issubclass(engine.pool.__class__, QueuePool), "Connection pooling should be enabled"
    
    def test_session_factory(self):
        """Test that session factory creates sessions."""
        session = SessionLocal()
        try:
            assert session is not None
            # Check that session is bound to engine
            assert session.bind is not None
        finally:
            session.close()
    
    def test_db_context_manager(self):
        """Test the database context manager."""
        with get_db() as db:
            assert db is not None
            # Test that session is usable
            assert db.query(User).count() == 0
    
    def test_db_dependency(self):
        """Test the database dependency for FastAPI."""
        # Get dependency function
        dependency = get_db_dependency()
        
        # Create generator from dependency
        db_gen = dependency()
        
        # Get session from generator
        db = next(db_gen)
        try:
            assert db is not None
            # Test that session is usable
            assert db.query(User).count() == 0
        finally:
            # Close session (simulating FastAPI dependency cleanup)
            try:
                next(db_gen)
            except StopIteration:
                pass


@pytest.mark.unit
class TestDatabaseModels:
    """Test database models and their functionality."""
    
    def test_base_model_fields(self):
        """Test that BaseModel has expected fields."""
        # Check model fields
        assert hasattr(BaseModel, 'id')
        assert hasattr(BaseModel, 'uuid')
        assert hasattr(BaseModel, 'created_at')
        assert hasattr(BaseModel, 'updated_at')
        assert hasattr(BaseModel, 'is_active')
    
    def test_user_model(self, db_session):
        """Test User model functionality."""
        # Create user
        user = User(
            username="testuser",
            email="test@example.com"
        )
        user.password = "password123"  # Test password hashing
        db_session.add(user)
        db_session.commit()
        
        # Verify user was created
        assert user.id is not None
        assert user.uuid is not None
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.is_active is True
        
        # Test password verification
        assert user.verify_password("password123") is True
        assert user.verify_password("wrongpassword") is False
        
        # Test to_dict method
        user_dict = user.to_dict()
        assert "id" in user_dict
        assert "uuid" in user_dict
        assert "username" in user_dict
        assert "email" in user_dict
        assert "hashed_password" not in user_dict  # Sensitive field should be excluded
    
    def test_role_model(self, db_session):
        """Test Role model functionality."""
        # Create role
        role = Role(
            name="admin",
            description="Administrator role",
            permissions='["admin", "read", "write"]'
        )
        db_session.add(role)
        db_session.commit()
        
        # Verify role was created
        assert role.id is not None
        assert role.name == "admin"
        assert role.description == "Administrator role"
        
        # Test permission_set property
        assert "admin" in role.permission_set
        assert "read" in role.permission_set
        assert "write" in role.permission_set
    
    def test_user_role_relationship(self, db_session):
        """Test relationship between User and Role."""
        # Create role
        role = Role(
            name="user",
            description="Regular user",
            permissions='["read"]'
        )
        db_session.add(role)
        
        # Create user
        user = User(
            username="testuser",
            email="test@example.com"
        )
        user.password = "password123"
        
        # Add role to user
        user.roles.append(role)
        db_session.add(user)
        db_session.commit()
        
        # Verify relationship
        assert len(user.roles) == 1
        assert user.roles[0].name == "user"
        assert len(role.users) == 1
        assert role.users[0].username == "testuser"
        
        # Test has_role method
        assert user.has_role("user") is True
        assert user.has_role("admin") is False
        
        # Test has_permission method
        assert user.has_permission("read") is True
        assert user.has_permission("write") is False


@pytest.mark.unit
class TestRepositoryPattern:
    """Test the repository pattern implementation."""
    
    def test_base_repository(self, db_session):
        """Test BaseRepository functionality."""
        # Create repository
        repo = BaseRepository(User, db_session)
        
        # Test create
        user_data = {
            "username": "repouser",
            "email": "repo@example.com"
        }
        user = repo.create(user_data)
        assert user.id is not None
        assert user.username == "repouser"
        
        # Test get
        retrieved_user = repo.get(user.id)
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        
        # Test get_by_uuid
        retrieved_user = repo.get_by_uuid(user.uuid)
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        
        # Test get_all
        all_users = repo.get_all()
        assert len(all_users) == 1
        assert all_users[0].id == user.id
        
        # Test update
        updated_data = {"username": "updateduser"}
        updated_user = repo.update(user.id, updated_data)
        assert updated_user.username == "updateduser"
        
        # Test find
        found_users = repo.find({"email": "repo@example.com"})
        assert len(found_users) == 1
        assert found_users[0].id == user.id
        
        # Test find_one
        found_user = repo.find_one({"email": "repo@example.com"})
        assert found_user is not None
        assert found_user.id == user.id
        
        # Test count
        count = repo.count({"email": "repo@example.com"})
        assert count == 1
        
        # Test delete
        deleted = repo.delete(user.id)
        assert deleted is True
        
        # Test soft delete
        assert repo.get(user.id).is_active is False
        
        # Test hard delete
        repo.hard_delete(user.id)
        assert repo.get(user.id) is None
    
    def test_user_repository(self, user_repository, db_session):
        """Test UserRepository functionality."""
        # Create user
        user = user_repository.create_user(
            {"username": "userrepotest", "email": "userrepo@example.com"},
            "password123"
        )
        assert user.id is not None
        
        # Test get_by_username
        retrieved_user = user_repository.get_by_username("userrepotest")
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        
        # Test get_by_email
        retrieved_user = user_repository.get_by_email("userrepo@example.com")
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        
        # Test authenticate
        auth_user = user_repository.authenticate("userrepotest", "password123")
        assert auth_user is not None
        assert auth_user.id == user.id
        
        # Test failed authentication
        auth_user = user_repository.authenticate("userrepotest", "wrongpassword")
        assert auth_user is None
        
        # Test password change
        changed = user_repository.change_password(user.id, "password123", "newpassword123")
        assert changed is True
        
        # Verify password was changed
        auth_user = user_repository.authenticate("userrepotest", "newpassword123")
        assert auth_user is not None
        
        # Test password reset
        token = user_repository.request_password_reset("userrepo@example.com")
        assert token is not None
        
        reset = user_repository.reset_password("userrepo@example.com", token, "resetpassword123")
        assert reset is True
        
        # Verify password was reset
        auth_user = user_repository.authenticate("userrepotest", "resetpassword123")
        assert auth_user is not None


@pytest.mark.unit
class TestQueryOptimization:
    """Test query optimization features."""
    
    def test_optimize_query(self):
        """Test query optimization function."""
        # Create mock query
        query = MagicMock()
        query.execution_options = MagicMock(return_value=query)
        
        # Test with no hints
        result = optimize_query(query)
        assert result is query
        query.execution_options.assert_not_called()
        
        # Test with hints
        hints = {"query_type": "SELECT"}
        result = optimize_query(query, hints)
        assert result is query
        query.execution_options.assert_called_once_with(query_type="SELECT")
    
    def test_profile_query_context_manager(self):
        """Test profile_query context manager."""
        query = "SELECT * FROM user"
        
        with profile_query(query) as profile:
            # Simulate some work
            pass
        
        assert isinstance(profile, QueryProfile)
        assert profile.query == query
        assert profile.end_time is not None
        assert profile.execution_time > 0
        assert profile.query_type == "SELECT"
    
    def test_profile_sqlalchemy_query_decorator(self):
        """Test profile_sqlalchemy_query decorator."""
        # Create decorated function
        @profile_sqlalchemy_query
        def test_func(query_obj):
            return "result"
        
        # Create mock query object
        query_obj = MagicMock()
        query_obj.statement = MagicMock()
        query_obj.statement.compile = MagicMock()
        query_obj.session = MagicMock()
        query_obj.session.bind = MagicMock()
        query_obj.session.bind.dialect = MagicMock()
        
        # Call function
        result = test_func(query_obj)
        
        # Verify result
        assert result == "result"
        query_obj.statement.compile.assert_called_once()


@pytest.mark.unit
class TestCaching:
    """Test caching functionality."""
    
    def test_cache_operations(self):
        """Test basic cache operations."""
        # Set value in cache
        key = "test_key"
        value = {"data": "test_value"}
        set_in_cache(key, value)
        
        # Get value from cache
        hit, retrieved_value = get_from_cache(key)
        assert hit is True
        assert retrieved_value == value
        
        # Get non-existent value
        hit, retrieved_value = get_from_cache("nonexistent_key")
        assert hit is False
        assert retrieved_value is None
        
        # Invalidate cache
        invalidate_cache(key)
        hit, retrieved_value = get_from_cache(key)
        assert hit is False
        assert retrieved_value is None
    
    def test_cached_decorator(self):
        """Test cached decorator."""
        call_count = 0
        
        @cached(ttl=10)
        def test_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"
        
        # First call should execute function
        result1 = test_function("test")
        assert result1 == "result_test"
        assert call_count == 1
        
        # Second call with same parameter should use cache
        result2 = test_function("test")
        assert result2 == "result_test"
        assert call_count == 1  # Still 1 because function wasn't called again
        
        # Call with different parameter should execute function
        result3 = test_function("different")
        assert result3 == "result_different"
        assert call_count == 2


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in database operations."""
    
    def test_transaction_rollback(self, db_session):
        """Test transaction rollback on error."""
        # Create user
        user = User(username="errortest", email="error@example.com")
        user.password = "password123"
        db_session.add(user)
        db_session.commit()
        
        # Try to create another user with same username (should fail)
        duplicate_user = User(username="errortest", email="another@example.com")
        duplicate_user.password = "password456"
        db_session.add(duplicate_user)
        
        try:
            db_session.commit()
            pytest.fail("Expected IntegrityError")
        except SQLAlchemyError:
            # Error should trigger rollback
            db_session.rollback()
        
        # Verify only one user exists
        count = db_session.query(User).filter(User.username == "errortest").count()
        assert count == 1
    
    def test_repository_error_handling(self, user_repository, db_session):
        """Test error handling in repository methods."""
        # Create user
        user = user_repository.create_user(
            {"username": "repoerrortest", "email": "repoerror@example.com"},
            "password123"
        )
        
        # Create a duplicate user that will cause an error
        with patch.object(db_session, 'commit', side_effect=SQLAlchemyError("Test error")):
            with patch.object(db_session, 'rollback') as mock_rollback:
                try:
                    user_repository.create_user(
                        {"username": "repoerrortest", "email": "duplicate@example.com"},
                        "password456"
                    )
                    pytest.fail("Expected SQLAlchemyError")
                except SQLAlchemyError:
                    # Verify rollback was called
                    mock_rollback.assert_called_once()


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database functionality."""
    
    def test_initialize_database(self):
        """Test database initialization."""
        # Mock engine to avoid affecting real database
        with patch("agentical.db.engine") as mock_engine:
            # Mock metadata creation
            with patch.object(Base.metadata, "create_all") as mock_create_all:
                # Call initialize function
                initialize_database(drop_all=False)
                
                # Verify tables were created
                mock_create_all.assert_called_once_with(bind=mock_engine)
    
    def test_check_database_connection(self):
        """Test database connection check."""
        # Mock session to avoid real database connection
        with patch("agentical.db.get_db") as mock_get_db:
            # Mock session context
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            # Call connection check
            result = check_database_connection()
            
            # Verify connection was checked
            assert result is True
            mock_session.execute.assert_called_once()
            
            # Test failure case
            mock_session.execute.side_effect = SQLAlchemyError("Connection error")
            result = check_database_connection()
            assert result is False


if __name__ == "__main__":
    pytest.main(["-v", __file__])