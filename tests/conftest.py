"""
Global PyTest Configuration and Fixtures for Agentical

This module provides comprehensive global fixtures and configuration for testing
the Agentical framework, including database setup, authentication, mocking,
and test data factories.

Features:
- Database test fixtures with automatic cleanup
- Authentication and security testing utilities
- Mock service configurations
- Test data factories and builders
- Async testing support
- Performance testing utilities
- Integration test helpers
"""

import asyncio
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, MagicMock
import json

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
import httpx

# Import Agentical components
from agentical.main import app
from agentical.db.session import get_db
from agentical.db.models.base import Base
from agentical.db.models.user import User, Role
from agentical.db.models.agent import Agent, AgentType, AgentStatus
from agentical.db.models.playbook import (
    Playbook, PlaybookStep, PlaybookExecution, PlaybookStatus,
    ExecutionStatus, StepType, StepStatus, PlaybookCategory
)
from agentical.db.models.workflow import Workflow, WorkflowExecution, WorkflowStep
from agentical.core.security import SecurityContext, SystemRole
from agentical.tools.security.auth_manager import AuthManager
from agentical.core.encryption import EncryptionManager
from agentical.core.security_config import SecurityPolicyConfig


# ================================
# Database Testing Configuration
# ================================

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine with in-memory SQLite."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session(test_session_factory):
    """Create test database session with automatic cleanup."""
    session = test_session_factory()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def db_with_data(db_session):
    """Database session with sample test data."""
    # Create default roles
    admin_role = Role(
        name="admin",
        description="Administrator role",
        permissions='["admin:users", "admin:system", "user:read", "user:create"]'
    )
    user_role = Role(
        name="user",
        description="Regular user role",
        permissions='["user:read"]'
    )

    db_session.add_all([admin_role, user_role])
    db_session.commit()

    # Create test users
    admin_user = User(
        username="admin",
        email="admin@test.com",
        hashed_password="$2b$12$test_admin_hash",
        first_name="Admin",
        last_name="User",
        display_name="Admin User",
        is_verified=True,
        created_at=datetime.utcnow()
    )
    admin_user.roles = [admin_role]

    regular_user = User(
        username="testuser",
        email="user@test.com",
        hashed_password="$2b$12$test_user_hash",
        first_name="Test",
        last_name="User",
        display_name="Test User",
        is_verified=True,
        created_at=datetime.utcnow()
    )
    regular_user.roles = [user_role]

    db_session.add_all([admin_user, regular_user])
    db_session.commit()

    yield db_session


@pytest.fixture
def override_get_db(db_session):
    """Override get_db dependency for testing."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    return _override_get_db


# ================================
# FastAPI Testing Configuration
# ================================

@pytest.fixture
def client(override_get_db):
    """Test client with database override."""
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(override_get_db):
    """Async test client with database override."""
    app.dependency_overrides[get_db] = override_get_db

    async with httpx.AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client

    app.dependency_overrides.clear()


# ================================
# Authentication & Security Fixtures
# ================================

@pytest.fixture
def mock_auth_manager():
    """Mock authentication manager for testing."""
    auth_manager = Mock(spec=AuthManager)
    auth_manager.authenticate = AsyncMock()
    auth_manager.create_user = AsyncMock()
    auth_manager.revoke_session = AsyncMock()
    auth_manager.health_check = AsyncMock()
    auth_manager._refresh_jwt_token = AsyncMock()
    return auth_manager


@pytest.fixture
def valid_jwt_token():
    """Generate valid JWT token for testing."""
    import jwt
    payload = {
        "user_id": 1,
        "username": "testuser",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Authentication headers for API testing."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def admin_auth_headers():
    """Admin authentication headers."""
    import jwt
    payload = {
        "user_id": 1,
        "username": "admin",
        "roles": ["admin"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, "test_secret", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def security_context_user(db_with_data):
    """Security context for regular user."""
    user = db_with_data.query(User).filter(User.username == "testuser").first()
    return SecurityContext(user)


@pytest.fixture
def security_context_admin(db_with_data):
    """Security context for admin user."""
    admin = db_with_data.query(User).filter(User.username == "admin").first()
    return SecurityContext(admin)


@pytest.fixture
def mock_encryption_manager():
    """Mock encryption manager for testing."""
    manager = Mock(spec=EncryptionManager)
    manager.encrypt_field = Mock(return_value={
        "value": "encrypted_data",
        "metadata": {"encrypted": True, "algorithm": "test"}
    })
    manager.decrypt_field = Mock(return_value="decrypted_data")
    return manager


# ================================
# Test Data Factories
# ================================

class UserFactory:
    """Factory for creating test users."""

    @staticmethod
    def create_user(
        username: str = None,
        email: str = None,
        is_admin: bool = False,
        is_verified: bool = True,
        **kwargs
    ) -> User:
        """Create a test user with default values."""
        username = username or f"user_{uuid.uuid4().hex[:8]}"
        email = email or f"{username}@test.com"

        user = User(
            username=username,
            email=email,
            hashed_password="$2b$12$test_hash",
            first_name=kwargs.get("first_name", "Test"),
            last_name=kwargs.get("last_name", "User"),
            display_name=kwargs.get("display_name", f"{username} User"),
            is_verified=is_verified,
            created_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ["first_name", "last_name", "display_name"]}
        )

        if is_admin:
            admin_role = Role(name="admin", description="Admin role")
            user.roles = [admin_role]

        return user


class AgentFactory:
    """Factory for creating test agents."""

    @staticmethod
    def create_agent(
        agent_type: AgentType = AgentType.CODE_AGENT,
        name: str = None,
        status: AgentStatus = AgentStatus.ACTIVE,
        **kwargs
    ) -> Agent:
        """Create a test agent with default values."""
        name = name or f"agent_{uuid.uuid4().hex[:8]}"

        return Agent(
            agent_id=str(uuid.uuid4()),
            name=name,
            description=kwargs.get("description", f"Test {agent_type.value} agent"),
            agent_type=agent_type,
            status=status,
            configuration=kwargs.get("configuration", {}),
            created_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ["description", "configuration"]}
        )


class PlaybookFactory:
    """Factory for creating test playbooks."""

    @staticmethod
    def create_playbook(
        name: str = None,
        category: PlaybookCategory = PlaybookCategory.AUTOMATION,
        status: PlaybookStatus = PlaybookStatus.DRAFT,
        **kwargs
    ) -> Playbook:
        """Create a test playbook with default values."""
        name = name or f"playbook_{uuid.uuid4().hex[:8]}"

        return Playbook(
            playbook_id=str(uuid.uuid4()),
            name=name,
            description=kwargs.get("description", f"Test {category.value} playbook"),
            category=category,
            status=status,
            version=kwargs.get("version", "1.0.0"),
            tags=kwargs.get("tags", ["test"]),
            configuration=kwargs.get("configuration", {}),
            created_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ["description", "version", "tags", "configuration"]}
        )

    @staticmethod
    def create_playbook_execution(
        playbook: Playbook,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        **kwargs
    ) -> PlaybookExecution:
        """Create a test playbook execution."""
        return PlaybookExecution(
            execution_id=str(uuid.uuid4()),
            playbook_id=playbook.playbook_id,
            status=status,
            started_at=kwargs.get("started_at", datetime.utcnow()),
            configuration=kwargs.get("configuration", {}),
            **{k: v for k, v in kwargs.items() if k not in ["started_at", "configuration"]}
        )


class WorkflowFactory:
    """Factory for creating test workflows."""

    @staticmethod
    def create_workflow(
        name: str = None,
        workflow_type: str = "sequential",
        **kwargs
    ) -> Workflow:
        """Create a test workflow with default values."""
        name = name or f"workflow_{uuid.uuid4().hex[:8]}"

        return Workflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=kwargs.get("description", f"Test {workflow_type} workflow"),
            workflow_type=workflow_type,
            configuration=kwargs.get("configuration", {}),
            created_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ["description", "configuration"]}
        )


@pytest.fixture
def user_factory():
    """User factory fixture."""
    return UserFactory


@pytest.fixture
def agent_factory():
    """Agent factory fixture."""
    return AgentFactory


@pytest.fixture
def playbook_factory():
    """Playbook factory fixture."""
    return PlaybookFactory


@pytest.fixture
def workflow_factory():
    """Workflow factory fixture."""
    return WorkflowFactory


# ================================
# Mock Service Configurations
# ================================

@pytest.fixture
def mock_logfire():
    """Mock Logfire integration."""
    with pytest.MonkeyPatch().context() as m:
        mock_logfire = MagicMock()
        mock_logfire.span = MagicMock()
        mock_logfire.info = MagicMock()
        mock_logfire.error = MagicMock()
        mock_logfire.warning = MagicMock()
        m.setattr("logfire", mock_logfire)
        yield mock_logfire


@pytest.fixture
def mock_mcp_servers():
    """Mock MCP server responses."""
    return {
        "taskmaster-ai": {
            "status": "healthy",
            "version": "1.0.0",
            "capabilities": ["task_management", "project_analysis"]
        },
        "ptolemies": {
            "status": "healthy",
            "version": "1.0.0",
            "capabilities": ["knowledge_base", "search"]
        },
        "context7": {
            "status": "healthy",
            "version": "1.0.0",
            "capabilities": ["context_management", "memory"]
        }
    }


@pytest.fixture
def mock_external_apis():
    """Mock external API responses."""
    return {
        "anthropic": {
            "model": "claude-3-sonnet",
            "response": "Mocked AI response",
            "status": "success"
        },
        "openai": {
            "model": "gpt-4",
            "response": "Mocked OpenAI response",
            "status": "success"
        }
    }


# ================================
# Performance Testing Utilities
# ================================

@pytest.fixture
def performance_timer():
    """Timer utility for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()
            return self.duration

        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


@pytest.fixture
def memory_tracker():
    """Memory usage tracking utility."""
    import psutil
    import os

    class MemoryTracker:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.initial_memory = None
            self.peak_memory = None

        def start(self):
            self.initial_memory = self.process.memory_info().rss
            self.peak_memory = self.initial_memory

        def update(self):
            current_memory = self.process.memory_info().rss
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory

        @property
        def memory_delta(self):
            if self.initial_memory and self.peak_memory:
                return self.peak_memory - self.initial_memory
            return None

    return MemoryTracker()


# ================================
# Integration Test Utilities
# ================================

@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    return {
        "database_url": "sqlite:///:memory:",
        "test_mode": True,
        "external_services_enabled": False,
        "mock_ai_responses": True,
        "log_level": "DEBUG"
    }


@pytest.fixture
def temp_file_manager():
    """Temporary file management for tests."""
    temp_files = []

    def create_temp_file(content: str = "", suffix: str = ".txt") -> str:
        """Create a temporary file and track it for cleanup."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            temp_files.append(f.name)
            return f.name

    yield create_temp_file

    # Cleanup
    for file_path in temp_files:
        try:
            os.unlink(file_path)
        except OSError:
            pass


# ================================
# Async Testing Support
# ================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_db_session(test_session_factory):
    """Async database session for async tests."""
    session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ================================
# Test Environment Configuration
# ================================

@pytest.fixture(autouse=True)
def test_environment_setup(monkeypatch):
    """Set up test environment variables."""
    test_env_vars = {
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "TESTING": "true",
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "test_secret_key_for_testing_only",
        "LOGFIRE_TOKEN": "test_logfire_token",
        "ANTHROPIC_API_KEY": "test_anthropic_key"
    }

    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def cleanup_test_data():
    """Cleanup test data after tests."""
    cleanup_tasks = []

    def add_cleanup(task):
        cleanup_tasks.append(task)

    yield add_cleanup

    # Execute cleanup tasks
    for task in cleanup_tasks:
        try:
            if asyncio.iscoroutinefunction(task):
                asyncio.run(task())
            else:
                task()
        except Exception as e:
            print(f"Cleanup task failed: {e}")


# ================================
# Parameterized Test Data
# ================================

@pytest.fixture(params=[
    AgentType.CODE_AGENT,
    AgentType.DATA_SCIENCE_AGENT,
    AgentType.DEVOPS_AGENT,
    AgentType.RESEARCH_AGENT
])
def agent_type_param(request):
    """Parameterized agent types for testing."""
    return request.param


@pytest.fixture(params=[
    PlaybookCategory.AUTOMATION,
    PlaybookCategory.DEPLOYMENT,
    PlaybookCategory.MONITORING,
    PlaybookCategory.INCIDENT_RESPONSE
])
def playbook_category_param(request):
    """Parameterized playbook categories for testing."""
    return request.param


@pytest.fixture(params=[
    ExecutionStatus.PENDING,
    ExecutionStatus.RUNNING,
    ExecutionStatus.COMPLETED,
    ExecutionStatus.FAILED
])
def execution_status_param(request):
    """Parameterized execution statuses for testing."""
    return request.param


# ================================
# Test Markers and Utilities
# ================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests - test individual components in isolation")
    config.addinivalue_line("markers", "integration: Integration tests - test component interactions")
    config.addinivalue_line("markers", "e2e: End-to-end tests - test complete user workflows")
    config.addinivalue_line("markers", "slow: Slow running tests (>1 second)")
    config.addinivalue_line("markers", "external: Tests requiring external services")
    config.addinivalue_line("markers", "agent: Tests specific to agent functionality")
    config.addinivalue_line("markers", "api: Tests for FastAPI endpoints")
    config.addinivalue_line("markers", "db: Tests requiring database access")
    config.addinivalue_line("markers", "mcp: Tests for MCP server integration")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "security: Security-related tests")
    config.addinivalue_line("markers", "smoke: Basic smoke tests for critical functionality")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test file location
        if "test_api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "test_performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        if "test_security" in str(item.fspath) or "test_auth" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        if "agent" in str(item.fspath):
            item.add_marker(pytest.mark.agent)
        if "db" in str(item.fspath) or "database" in str(item.fspath):
            item.add_marker(pytest.mark.db)


# ================================
# Test Reporting and Analysis
# ================================

@pytest.fixture
def test_metrics_collector():
    """Collect test execution metrics."""
    metrics = {
        "start_time": None,
        "end_time": None,
        "memory_usage": [],
        "api_calls": [],
        "database_queries": []
    }

    def start_collection():
        metrics["start_time"] = datetime.utcnow()

    def stop_collection():
        metrics["end_time"] = datetime.utcnow()
        return metrics

    def add_metric(category: str, data: Any):
        if category not in metrics:
            metrics[category] = []
        metrics[category].append({
            "timestamp": datetime.utcnow(),
            "data": data
        })

    collector = type('MetricsCollector', (), {
        'start': start_collection,
        'stop': stop_collection,
        'add': add_metric,
        'metrics': metrics
    })()

    return collector
