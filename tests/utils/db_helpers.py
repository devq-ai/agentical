"""
Database Testing Helpers for Agentical Framework

This module provides comprehensive utilities for database testing,
including transaction management, data seeding, model validation,
and database state management for testing scenarios.

Features:
- Database transaction management
- Test data seeding and cleanup
- Model validation utilities
- Database state snapshots
- Query performance testing
- Relationship testing helpers
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Type, Union, Callable
from contextlib import contextmanager
from unittest.mock import Mock, patch

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
import pytest

from agentical.db.models.base import BaseModel, Base
from agentical.db.models.user import User, Role
from agentical.db.models.agent import Agent, AgentType, AgentStatus
from agentical.db.models.playbook import (
    Playbook, PlaybookStep, PlaybookExecution, PlaybookStatus,
    ExecutionStatus, StepType, StepStatus, PlaybookCategory
)
from agentical.db.models.workflow import Workflow, WorkflowExecution, WorkflowStep


class DatabaseTestHelper:
    """Comprehensive database testing helper."""

    def __init__(self, session: Session):
        self.session = session
        self._snapshots = {}
        self._created_objects = []

    def create_and_save(self, model_instance: BaseModel) -> BaseModel:
        """Create and save model instance, tracking for cleanup."""
        self.session.add(model_instance)
        self.session.commit()
        self.session.refresh(model_instance)
        self._created_objects.append(model_instance)
        return model_instance

    def create_user(
        self,
        username: str = None,
        email: str = None,
        is_admin: bool = False,
        **kwargs
    ) -> User:
        """Create test user with default values."""
        username = username or f"user_{uuid.uuid4().hex[:8]}"
        email = email or f"{username}@test.com"

        user = User(
            username=username,
            email=email,
            hashed_password="$2b$12$test_hash",
            first_name=kwargs.get("first_name", "Test"),
            last_name=kwargs.get("last_name", "User"),
            display_name=kwargs.get("display_name", f"{username} User"),
            is_verified=kwargs.get("is_verified", True),
            created_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ["first_name", "last_name", "display_name", "is_verified"]}
        )

        if is_admin:
            admin_role = self.get_or_create_role("admin", "Administrator role")
            user.roles = [admin_role]

        return self.create_and_save(user)

    def create_role(self, name: str, description: str = None, permissions: List[str] = None) -> Role:
        """Create test role."""
        import json
        role = Role(
            name=name,
            description=description or f"{name} role",
            permissions=json.dumps(permissions or [])
        )
        return self.create_and_save(role)

    def get_or_create_role(self, name: str, description: str = None) -> Role:
        """Get existing role or create new one."""
        role = self.session.query(Role).filter(Role.name == name).first()
        if not role:
            role = self.create_role(name, description)
        return role

    def create_agent(
        self,
        name: str = None,
        agent_type: AgentType = AgentType.CODE_AGENT,
        status: AgentStatus = AgentStatus.ACTIVE,
        **kwargs
    ) -> Agent:
        """Create test agent."""
        name = name or f"agent_{uuid.uuid4().hex[:8]}"

        agent = Agent(
            agent_id=str(uuid.uuid4()),
            name=name,
            description=kwargs.get("description", f"Test {agent_type.value} agent"),
            agent_type=agent_type,
            status=status,
            configuration=kwargs.get("configuration", {}),
            created_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ["description", "configuration"]}
        )

        return self.create_and_save(agent)

    def create_playbook(
        self,
        name: str = None,
        category: PlaybookCategory = PlaybookCategory.AUTOMATION,
        status: PlaybookStatus = PlaybookStatus.DRAFT,
        **kwargs
    ) -> Playbook:
        """Create test playbook."""
        name = name or f"playbook_{uuid.uuid4().hex[:8]}"

        playbook = Playbook(
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

        return self.create_and_save(playbook)

    def create_playbook_execution(
        self,
        playbook: Playbook,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        **kwargs
    ) -> PlaybookExecution:
        """Create test playbook execution."""
        execution = PlaybookExecution(
            execution_id=str(uuid.uuid4()),
            playbook_id=playbook.playbook_id,
            status=status,
            started_at=kwargs.get("started_at", datetime.utcnow()),
            configuration=kwargs.get("configuration", {}),
            **{k: v for k, v in kwargs.items() if k not in ["started_at", "configuration"]}
        )

        return self.create_and_save(execution)

    def create_workflow(
        self,
        name: str = None,
        workflow_type: str = "sequential",
        **kwargs
    ) -> Workflow:
        """Create test workflow."""
        name = name or f"workflow_{uuid.uuid4().hex[:8]}"

        workflow = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=kwargs.get("description", f"Test {workflow_type} workflow"),
            workflow_type=workflow_type,
            configuration=kwargs.get("configuration", {}),
            created_at=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k not in ["description", "configuration"]}
        )

        return self.create_and_save(workflow)

    def count_records(self, model_class: Type[BaseModel]) -> int:
        """Count records in table."""
        return self.session.query(model_class).count()

    def find_by_id(self, model_class: Type[BaseModel], record_id: Union[int, str]) -> Optional[BaseModel]:
        """Find record by ID."""
        if hasattr(model_class, 'id'):
            return self.session.query(model_class).filter(model_class.id == record_id).first()
        elif hasattr(model_class, 'agent_id'):
            return self.session.query(model_class).filter(model_class.agent_id == record_id).first()
        elif hasattr(model_class, 'playbook_id'):
            return self.session.query(model_class).filter(model_class.playbook_id == record_id).first()
        elif hasattr(model_class, 'workflow_id'):
            return self.session.query(model_class).filter(model_class.workflow_id == record_id).first()
        else:
            raise ValueError(f"Cannot determine ID field for {model_class}")

    def delete_all(self, model_class: Type[BaseModel]):
        """Delete all records from table."""
        self.session.query(model_class).delete()
        self.session.commit()

    def cleanup_created_objects(self):
        """Clean up all objects created during test."""
        for obj in reversed(self._created_objects):
            try:
                self.session.delete(obj)
            except SQLAlchemyError:
                pass  # Object might already be deleted

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()

        self._created_objects.clear()

    def take_snapshot(self, name: str, tables: List[Type[BaseModel]] = None):
        """Take snapshot of database state."""
        if tables is None:
            tables = [User, Role, Agent, Playbook, PlaybookExecution, Workflow]

        snapshot = {}
        for table in tables:
            records = self.session.query(table).all()
            snapshot[table.__name__] = [self._serialize_record(record) for record in records]

        self._snapshots[name] = snapshot

    def restore_snapshot(self, name: str):
        """Restore database to snapshot state."""
        if name not in self._snapshots:
            raise ValueError(f"Snapshot '{name}' not found")

        snapshot = self._snapshots[name]

        # Clear current data
        for table_name in snapshot.keys():
            table_class = self._get_table_class(table_name)
            self.session.query(table_class).delete()

        # Restore snapshot data
        for table_name, records in snapshot.items():
            table_class = self._get_table_class(table_name)
            for record_data in records:
                record = table_class(**record_data)
                self.session.add(record)

        self.session.commit()

    def _serialize_record(self, record: BaseModel) -> Dict[str, Any]:
        """Serialize database record to dictionary."""
        data = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            if isinstance(value, datetime):
                data[column.name] = value.isoformat()
            elif isinstance(value, (dict, list)):
                data[column.name] = value
            else:
                data[column.name] = value
        return data

    def _get_table_class(self, table_name: str) -> Type[BaseModel]:
        """Get table class by name."""
        table_map = {
            "User": User,
            "Role": Role,
            "Agent": Agent,
            "Playbook": Playbook,
            "PlaybookExecution": PlaybookExecution,
            "Workflow": Workflow
        }
        return table_map[table_name]

    def assert_record_exists(self, model_class: Type[BaseModel], **filter_kwargs):
        """Assert that record exists with given filters."""
        query = self.session.query(model_class)
        for field, value in filter_kwargs.items():
            query = query.filter(getattr(model_class, field) == value)

        record = query.first()
        assert record is not None, f"Record not found in {model_class.__name__} with filters: {filter_kwargs}"
        return record

    def assert_record_count(self, model_class: Type[BaseModel], expected_count: int):
        """Assert record count in table."""
        actual_count = self.count_records(model_class)
        assert actual_count == expected_count, (
            f"Expected {expected_count} records in {model_class.__name__}, found {actual_count}"
        )

    def assert_no_records(self, model_class: Type[BaseModel]):
        """Assert no records exist in table."""
        self.assert_record_count(model_class, 0)


class TransactionManager:
    """Database transaction management for testing."""

    def __init__(self, session: Session):
        self.session = session
        self._savepoints = []

    @contextmanager
    def transaction(self):
        """Context manager for database transaction."""
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    @contextmanager
    def savepoint(self, name: str = None):
        """Context manager for database savepoint."""
        name = name or f"sp_{len(self._savepoints)}"
        savepoint = self.session.begin_nested()
        self._savepoints.append((name, savepoint))

        try:
            yield self.session
        except Exception:
            savepoint.rollback()
            raise
        finally:
            if self._savepoints and self._savepoints[-1][0] == name:
                self._savepoints.pop()

    def rollback_to_savepoint(self, name: str = None):
        """Rollback to specific savepoint."""
        if name is None and self._savepoints:
            _, savepoint = self._savepoints[-1]
            savepoint.rollback()
        else:
            for sp_name, savepoint in reversed(self._savepoints):
                if sp_name == name:
                    savepoint.rollback()
                    break

    def commit(self):
        """Commit current transaction."""
        self.session.commit()

    def rollback(self):
        """Rollback current transaction."""
        self.session.rollback()


class DataSeeder:
    """Database seeding utility for test data."""

    def __init__(self, db_helper: DatabaseTestHelper):
        self.db_helper = db_helper

    def seed_basic_data(self):
        """Seed basic test data."""
        # Create roles
        admin_role = self.db_helper.get_or_create_role(
            "admin",
            "Administrator role",
            ["admin:users", "admin:system", "user:read", "user:create"]
        )
        user_role = self.db_helper.get_or_create_role(
            "user",
            "Regular user role",
            ["user:read"]
        )

        # Create users
        admin_user = self.db_helper.create_user(
            username="admin",
            email="admin@test.com",
            is_admin=True
        )

        regular_user = self.db_helper.create_user(
            username="testuser",
            email="user@test.com"
        )
        regular_user.roles = [user_role]
        self.db_helper.session.commit()

        return {
            "admin_role": admin_role,
            "user_role": user_role,
            "admin_user": admin_user,
            "regular_user": regular_user
        }

    def seed_agent_data(self, count: int = 5):
        """Seed agent test data."""
        agents = []
        agent_types = list(AgentType)

        for i in range(count):
            agent_type = agent_types[i % len(agent_types)]
            agent = self.db_helper.create_agent(
                name=f"test_agent_{i}",
                agent_type=agent_type,
                status=AgentStatus.ACTIVE,
                configuration={
                    "test_config": f"value_{i}",
                    "capabilities": [f"capability_{i}"]
                }
            )
            agents.append(agent)

        return agents

    def seed_playbook_data(self, count: int = 3):
        """Seed playbook test data."""
        playbooks = []
        categories = list(PlaybookCategory)

        for i in range(count):
            category = categories[i % len(categories)]
            playbook = self.db_helper.create_playbook(
                name=f"test_playbook_{i}",
                category=category,
                status=PlaybookStatus.PUBLISHED,
                configuration={
                    "steps": [
                        {
                            "step_id": f"step_{j}",
                            "name": f"Step {j}",
                            "type": "action",
                            "configuration": {}
                        }
                        for j in range(3)
                    ]
                }
            )
            playbooks.append(playbook)

        return playbooks

    def seed_execution_data(self, playbooks: List[Playbook] = None):
        """Seed execution test data."""
        if not playbooks:
            playbooks = self.seed_playbook_data(2)

        executions = []
        statuses = list(ExecutionStatus)

        for i, playbook in enumerate(playbooks):
            for j in range(2):  # 2 executions per playbook
                status = statuses[(i + j) % len(statuses)]
                execution = self.db_helper.create_playbook_execution(
                    playbook=playbook,
                    status=status,
                    started_at=datetime.utcnow() - timedelta(hours=i+j),
                    configuration={"test_execution": True}
                )
                executions.append(execution)

        return executions

    def seed_workflow_data(self, count: int = 3):
        """Seed workflow test data."""
        workflows = []
        workflow_types = ["sequential", "parallel", "conditional"]

        for i in range(count):
            workflow_type = workflow_types[i % len(workflow_types)]
            workflow = self.db_helper.create_workflow(
                name=f"test_workflow_{i}",
                workflow_type=workflow_type,
                configuration={
                    "steps": [
                        {
                            "step_id": f"step_{j}",
                            "name": f"Workflow Step {j}",
                            "type": "task",
                            "configuration": {}
                        }
                        for j in range(2)
                    ]
                }
            )
            workflows.append(workflow)

        return workflows

    def seed_comprehensive_data(self):
        """Seed comprehensive test data for integration tests."""
        data = {}

        # Basic data
        data.update(self.seed_basic_data())

        # Agents
        data["agents"] = self.seed_agent_data(10)

        # Playbooks
        data["playbooks"] = self.seed_playbook_data(5)

        # Executions
        data["executions"] = self.seed_execution_data(data["playbooks"])

        # Workflows
        data["workflows"] = self.seed_workflow_data(5)

        return data


class ModelValidator:
    """Model validation utilities for testing."""

    @staticmethod
    def validate_user(user: User, expected_data: Dict[str, Any] = None):
        """Validate user model instance."""
        assert user.username is not None
        assert user.email is not None
        assert "@" in user.email
        assert user.hashed_password is not None
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

        if expected_data:
            for field, expected_value in expected_data.items():
                actual_value = getattr(user, field)
                assert actual_value == expected_value, (
                    f"User.{field} expected {expected_value}, got {actual_value}"
                )

    @staticmethod
    def validate_agent(agent: Agent, expected_data: Dict[str, Any] = None):
        """Validate agent model instance."""
        assert agent.agent_id is not None
        assert agent.name is not None
        assert agent.agent_type is not None
        assert isinstance(agent.agent_type, AgentType)
        assert agent.status is not None
        assert isinstance(agent.status, AgentStatus)
        assert agent.created_at is not None
        assert isinstance(agent.created_at, datetime)

        if expected_data:
            for field, expected_value in expected_data.items():
                actual_value = getattr(agent, field)
                assert actual_value == expected_value, (
                    f"Agent.{field} expected {expected_value}, got {actual_value}"
                )

    @staticmethod
    def validate_playbook(playbook: Playbook, expected_data: Dict[str, Any] = None):
        """Validate playbook model instance."""
        assert playbook.playbook_id is not None
        assert playbook.name is not None
        assert playbook.category is not None
        assert isinstance(playbook.category, PlaybookCategory)
        assert playbook.status is not None
        assert isinstance(playbook.status, PlaybookStatus)
        assert playbook.created_at is not None
        assert isinstance(playbook.created_at, datetime)

        if expected_data:
            for field, expected_value in expected_data.items():
                actual_value = getattr(playbook, field)
                assert actual_value == expected_value, (
                    f"Playbook.{field} expected {expected_value}, got {actual_value}"
                )

    @staticmethod
    def validate_relationships(instance: BaseModel, relationships: Dict[str, Any]):
        """Validate model relationships."""
        for relationship_name, expected_data in relationships.items():
            actual_relationship = getattr(instance, relationship_name)

            if expected_data is None:
                assert actual_relationship is None
            elif isinstance(expected_data, list):
                assert len(actual_relationship) == len(expected_data)
            else:
                assert actual_relationship is not None


class DatabasePerformanceHelper:
    """Helper for database performance testing."""

    def __init__(self, session: Session):
        self.session = session
        self._query_count = 0
        self._query_times = []

    def start_monitoring(self):
        """Start monitoring database queries."""
        self._query_count = 0
        self._query_times = []

        @event.listens_for(self.session.bind, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = datetime.utcnow()

        @event.listens_for(self.session.bind, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            end_time = datetime.utcnow()
            duration = (end_time - context._query_start_time).total_seconds()
            self._query_count += 1
            self._query_times.append(duration)

    def get_query_count(self) -> int:
        """Get number of queries executed."""
        return self._query_count

    def get_average_query_time(self) -> float:
        """Get average query execution time."""
        if not self._query_times:
            return 0.0
        return sum(self._query_times) / len(self._query_times)

    def get_slowest_query_time(self) -> float:
        """Get slowest query execution time."""
        return max(self._query_times) if self._query_times else 0.0

    def assert_max_queries(self, max_queries: int):
        """Assert maximum number of queries."""
        assert self._query_count <= max_queries, (
            f"Expected maximum {max_queries} queries, executed {self._query_count}"
        )

    def assert_max_query_time(self, max_time_seconds: float):
        """Assert maximum query execution time."""
        slowest = self.get_slowest_query_time()
        assert slowest <= max_time_seconds, (
            f"Slowest query took {slowest}s, expected maximum {max_time_seconds}s"
        )


# Utility functions
def create_test_database_session(database_url: str = "sqlite:///:memory:") -> Session:
    """Create test database session."""
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        poolclass=StaticPool if "sqlite" in database_url else None,
        echo=False
    )

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@contextmanager
def isolated_database_test():
    """Context manager for isolated database test."""
    session = create_test_database_session()
    db_helper = DatabaseTestHelper(session)

    try:
        yield db_helper
    finally:
        db_helper.cleanup_created_objects()
        session.close()


def assert_database_state_unchanged(session: Session, model_classes: List[Type[BaseModel]] = None):
    """Assert database state is unchanged after operation."""
    if model_classes is None:
        model_classes = [User, Role, Agent, Playbook, PlaybookExecution, Workflow]

    initial_counts = {}
    for model_class in model_classes:
        initial_counts[model_class] = session.query(model_class).count()

    def check_state():
        for model_class in model_classes:
            current_count = session.query(model_class).count()
            initial_count = initial_counts[model_class]
            assert current_count == initial_count, (
                f"{model_class.__name__} count changed from {initial_count} to {current_count}"
            )

    return check_state
