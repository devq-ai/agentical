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


# ================================
# Agent Pool Testing Fixtures
# ================================

@pytest.fixture
def mock_agent_pool_discovery_service():
    """Create mock agent pool discovery service."""
    from agentical.agents.pool_discovery import AgentPoolDiscoveryService

    service = Mock(spec=AgentPoolDiscoveryService)
    service.initialize = AsyncMock(return_value=True)
    service.discover_agents = AsyncMock(return_value=True)
    service.find_capable_agents = AsyncMock(return_value=[])
    service.get_agent_by_id = AsyncMock(return_value=None)
    service.get_available_agents = AsyncMock(return_value=[])
    service.update_agent_heartbeat = AsyncMock(return_value=True)
    service.update_agent_load = AsyncMock(return_value=True)
    service.register_agent_capability = AsyncMock(return_value=True)
    service.get_pool_statistics = AsyncMock(return_value={
        "total_agents": 0,
        "available_agents": 0,
        "healthy_agents": 0,
        "agents_by_type": {},
        "agents_by_health_status": {}
    })
    service.agent_pool = {}
    service.last_discovery_time = datetime.utcnow()

    return service


@pytest.fixture
def mock_capability_matcher():
    """Create mock capability matcher."""
    from agentical.agents.capability_matcher import AdvancedCapabilityMatcher

    matcher = Mock(spec=AdvancedCapabilityMatcher)
    matcher.find_best_matches = AsyncMock(return_value=[])
    matcher.calculate_match_score = AsyncMock(return_value=0.0)
    matcher.validate_requirements = AsyncMock(return_value=True)

    return matcher


@pytest.fixture
def sample_agent_pool_entries():
    """Create sample agent pool entries for testing."""
    try:
        from agentical.agents.playbook_capabilities import (
            AgentPoolEntry, PlaybookCapability, PerformanceMetrics,
            HealthStatus, PlaybookCapabilityType, CapabilityComplexity
        )

        return [
            AgentPoolEntry(
                agent_id="test_agent_001",
                agent_type="test",
                agent_name="Test Agent 1",
                description="First test agent",
                available_tools=["filesystem", "git"],
                supported_workflows=["sequential"],
                health_status=HealthStatus.HEALTHY,
                current_load=1,
                max_concurrent_executions=5,
                capabilities=[
                    PlaybookCapability(
                        name="test_capability_1",
                        display_name="Test Capability 1",
                        description="First test capability",
                        capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                        complexity=CapabilityComplexity.SIMPLE,
                        supported_step_types=["action"],
                        required_tools=["filesystem"]
                    )
                ]
            ),
            AgentPoolEntry(
                agent_id="test_agent_002",
                agent_type="worker",
                agent_name="Test Agent 2",
                description="Second test agent",
                available_tools=["memory", "fetch"],
                supported_workflows=["parallel"],
                health_status=HealthStatus.HEALTHY,
                current_load=2,
                max_concurrent_executions=3,
                capabilities=[
                    PlaybookCapability(
                        name="test_capability_2",
                        display_name="Test Capability 2",
                        description="Second test capability",
                        capability_type=PlaybookCapabilityType.DATA_PROCESSING,
                        complexity=CapabilityComplexity.MODERATE,
                        supported_step_types=["data_processing"],
                        required_tools=["memory"]
                    )
                ]
            ),
            AgentPoolEntry(
                agent_id="test_agent_003",
                agent_type="monitor",
                agent_name="Test Agent 3",
                description="Third test agent",
                available_tools=["logfire-mcp"],
                supported_workflows=["loop"],
                health_status=HealthStatus.WARNING,
                current_load=0,
                max_concurrent_executions=10,
                capabilities=[
                    PlaybookCapability(
                        name="test_capability_3",
                        display_name="Test Capability 3",
                        description="Third test capability",
                        capability_type=PlaybookCapabilityType.MONITORING,
                        complexity=CapabilityComplexity.SIMPLE,
                        supported_step_types=["monitoring"],
                        required_tools=["logfire-mcp"]
                    )
                ]
            )
        ]
    except ImportError:
        # Return empty list if dependencies not available
        return []


@pytest.fixture
def sample_capability_filters():
    """Create sample capability filters for testing."""
    try:
        from agentical.agents.playbook_capabilities import (
            CapabilityFilter, HealthStatus, PlaybookCapabilityType
        )

        return {
            "basic": CapabilityFilter(
                required_tools=["filesystem"],
                workflow_types=["sequential"],
                health_statuses=[HealthStatus.HEALTHY]
            ),
            "advanced": CapabilityFilter(
                capability_types=[PlaybookCapabilityType.DATA_PROCESSING],
                required_tools=["memory"],
                workflow_types=["parallel"],
                min_success_rate=0.9
            ),
            "monitoring": CapabilityFilter(
                capability_types=[PlaybookCapabilityType.MONITORING],
                required_tools=["logfire-mcp"],
                workflow_types=["loop"],
                health_statuses=[HealthStatus.HEALTHY, HealthStatus.WARNING]
            ),
            "empty": CapabilityFilter()
        }
    except ImportError:
        return {}


@pytest.fixture
def agent_pool_test_data(sample_agent_pool_entries):
    """Create comprehensive agent pool test data."""
    return {
        "agents": sample_agent_pool_entries,
        "agent_count": len(sample_agent_pool_entries),
        "healthy_count": len([a for a in sample_agent_pool_entries if hasattr(a, 'health_status') and a.health_status.value == 'healthy']),
        "agent_types": list(set(a.agent_type for a in sample_agent_pool_entries if hasattr(a, 'agent_type'))),
        "available_tools": list(set(tool for a in sample_agent_pool_entries if hasattr(a, 'available_tools') for tool in a.available_tools))
    }


@pytest.fixture
def mock_agent_registry():
    """Create mock agent registry for testing discovery."""
    registry = Mock()
    registry.list_agents = AsyncMock(return_value=[
        {
            "id": "registry_agent_001",
            "name": "Registry Agent 1",
            "type": "TestAgent",
            "status": "idle",
            "description": "Test agent from registry",
            "capabilities_count": 2
        },
        {
            "id": "registry_agent_002",
            "name": "Registry Agent 2",
            "type": "WorkerAgent",
            "status": "busy",
            "description": "Worker agent from registry",
            "capabilities_count": 3
        }
    ])

    # Mock individual agent metadata
    mock_agent_1 = Mock()
    mock_agent_1.metadata = Mock()
    mock_agent_1.metadata.id = "registry_agent_001"
    mock_agent_1.metadata.name = "Registry Agent 1"
    mock_agent_1.metadata.description = "Test agent from registry"
    mock_agent_1.metadata.available_tools = ["tool1", "tool2"]
    mock_agent_1.metadata.version = "1.0.0"
    mock_agent_1.metadata.tags = ["test"]

    mock_agent_2 = Mock()
    mock_agent_2.metadata = Mock()
    mock_agent_2.metadata.id = "registry_agent_002"
    mock_agent_2.metadata.name = "Registry Agent 2"
    mock_agent_2.metadata.description = "Worker agent from registry"
    mock_agent_2.metadata.available_tools = ["tool2", "tool3", "tool4"]
    mock_agent_2.metadata.version = "1.1.0"
    mock_agent_2.metadata.tags = ["worker"]

    def get_agent_side_effect(agent_id):
        if agent_id == "registry_agent_001":
            return mock_agent_1
        elif agent_id == "registry_agent_002":
            return mock_agent_2
        return None

    registry.get_agent = Mock(side_effect=get_agent_side_effect)

    return registry


# ================================
# CodeAgent Testing Fixtures
# ================================

@pytest.fixture
def mock_code_agent():
    """Create mock CodeAgent for testing."""
    try:
        from agentical.agents.code_agent import CodeAgent

        agent = Mock(spec=CodeAgent)
        agent.agent_id = "code-001"
        agent.name = "CodeAgent"
        agent.capabilities = [
            "code_generation", "code_refactoring", "code_analysis",
            "code_review", "test_generation", "documentation"
        ]
        agent.tools = [
            "git", "github", "filesystem", "dart-mcp", "jupyter-mcp"
        ]

        # Mock core methods
        agent.generate_code = AsyncMock(return_value={
            "success": True,
            "generated_code": "def sample_function(): pass",
            "tests": "def test_sample_function(): assert True",
            "documentation": "# Sample Function Documentation",
            "validation": {"syntax_valid": True}
        })

        agent.refactor_code = AsyncMock(return_value={
            "success": True,
            "refactored_code": "def improved_function(): pass",
            "changes": {"lines_modified": 1},
            "validation": {"behavior_preserved": True}
        })

        agent.analyze_code = AsyncMock(return_value={
            "success": True,
            "analysis_results": {
                "metrics": {"lines_of_code": 10, "complexity": 1},
                "quality": {"score": 85.0},
                "security": []
            },
            "recommendations": ["Add documentation"]
        })

        agent.review_code = AsyncMock(return_value={
            "success": True,
            "quality_score": 85.0,
            "findings": {"minor": [], "major": []},
            "suggestions": ["Follow naming conventions"]
        })

        agent.generate_tests = AsyncMock(return_value={
            "success": True,
            "generated_tests": {"unit": "def test_example(): pass"},
            "coverage_estimate": 90.0
        })

        agent.generate_documentation = AsyncMock(return_value={
            "success": True,
            "api_documentation": "# API Documentation",
            "inline_documentation": "# Inline docs",
            "readme": "# README"
        })

        return agent
    except ImportError:
        pytest.skip("CodeAgent not available")


@pytest.fixture
def code_generation_samples():
    """Sample code generation requests and expected outputs."""
    return {
        "python_function": {
            "request": {
                "language": "python",
                "description": "Create a function to calculate factorial",
                "function_name": "factorial",
                "include_tests": True,
                "include_docs": True
            },
            "expected_code": '''
def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)
''',
            "expected_tests": '''
import pytest

def test_factorial():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
'''
        },
        "javascript_function": {
            "request": {
                "language": "javascript",
                "description": "Create a function to validate email",
                "function_name": "validateEmail",
                "include_tests": True
            },
            "expected_code": '''
function validateEmail(email) {
    const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    return emailRegex.test(email);
}
''',
            "expected_tests": '''
describe('validateEmail', () => {
    test('valid email', () => {
        expect(validateEmail('test@example.com')).toBe(true);
    });

    test('invalid email', () => {
        expect(validateEmail('invalid-email')).toBe(false);
    });
});
'''
        }
    }


@pytest.fixture
def code_analysis_samples():
    """Sample code for analysis testing."""
    return {
        "simple_python": {
            "code": '''
def hello_world():
    print("Hello, World!")

def add_numbers(a, b):
    return a + b
''',
            "expected_metrics": {
                "lines_of_code": 5,
                "functions": 2,
                "complexity": "low"
            }
        },
        "complex_python": {
            "code": '''
def complex_function(data):
    result = []
    for item in data:
        if item is not None:
            if isinstance(item, str):
                if len(item) > 0:
                    processed = item.upper().strip()
                    if processed not in result:
                        result.append(processed)
                    else:
                        continue
                else:
                    result.append("EMPTY")
            elif isinstance(item, (int, float)):
                result.append(str(item))
            else:
                result.append("UNKNOWN")
        else:
            result.append("NULL")
    return result
''',
            "expected_metrics": {
                "lines_of_code": 18,
                "functions": 1,
                "complexity": "high",
                "nested_levels": 4
            }
        },
        "security_issues": {
            "code": '''
import os
import subprocess

def execute_command(user_input):
    os.system(f"ls {user_input}")

def sql_query(user_input):
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query
''',
            "expected_issues": [
                {"type": "command_injection", "severity": "high"},
                {"type": "sql_injection", "severity": "high"}
            ]
        }
    }


@pytest.fixture
def refactoring_scenarios():
    """Sample refactoring scenarios for testing."""
    return {
        "extract_method": {
            "original": '''
def process_data(data):
    # Complex processing logic
    result = []
    for item in data:
        if item is not None and len(str(item)) > 0:
            processed = str(item).upper().strip()
            result.append(processed)
    return result
''',
            "refactor_type": "extract_method",
            "expected": '''
def process_data(data):
    result = []
    for item in data:
        processed_item = process_item(item)
        if processed_item:
            result.append(processed_item)
    return result

def process_item(item):
    if item is not None and len(str(item)) > 0:
        return str(item).upper().strip()
    return None
'''
        },
        "improve_readability": {
            "original": '''
def calc(x,y,op):
    if op=='add':return x+y
    elif op=='sub':return x-y
    elif op=='mul':return x*y
    elif op=='div':return x/y if y!=0 else None
''',
            "refactor_type": "improve_readability",
            "expected": '''
def calculate(x, y, operation):
    """Perform basic arithmetic operations."""
    if operation == 'add':
        return x + y
    elif operation == 'subtract':
        return x - y
    elif operation == 'multiply':
        return x * y
    elif operation == 'divide':
        return x / y if y != 0 else None
    else:
        raise ValueError(f"Unsupported operation: {operation}")
'''
        }
    }


@pytest.fixture
def programming_language_configs():
    """Configuration for different programming languages."""
    return {
        "python": {
            "file_extensions": [".py"],
            "test_frameworks": ["pytest", "unittest"],
            "linters": ["pylint", "flake8", "mypy"],
            "formatters": ["black", "autopep8"],
            "package_managers": ["pip", "poetry", "conda"]
        },
        "javascript": {
            "file_extensions": [".js", ".mjs"],
            "test_frameworks": ["jest", "mocha", "cypress"],
            "linters": ["eslint", "jshint"],
            "formatters": ["prettier"],
            "package_managers": ["npm", "yarn"]
        },
        "typescript": {
            "file_extensions": [".ts", ".tsx"],
            "test_frameworks": ["jest", "mocha"],
            "linters": ["eslint", "tslint"],
            "formatters": ["prettier"],
            "package_managers": ["npm", "yarn"]
        }
    }
