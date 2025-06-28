"""
Test Data Builders for Agentical Testing Framework

This module provides builder pattern implementations for creating test data
with fluent interfaces and default values for comprehensive testing scenarios.

Features:
- Fluent builder interfaces for all major entities
- Realistic default values for testing
- Chainable methods for easy customization
- Integration with database sessions
- Support for complex relationships
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field

from agentical.db.models.user import User, Role
from agentical.db.models.agent import Agent, AgentType, AgentStatus
from agentical.db.models.playbook import (
    Playbook, PlaybookStep, PlaybookExecution, PlaybookStatus,
    ExecutionStatus, StepType, StepStatus, PlaybookCategory
)
from agentical.db.models.workflow import Workflow, WorkflowExecution, WorkflowStep


class UserBuilder:
    """Builder for creating test users with fluent interface."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset builder to default state."""
        self._username = f"user_{uuid.uuid4().hex[:8]}"
        self._email = f"{self._username}@test.com"
        self._password = "$2b$12$test_hash"
        self._first_name = "Test"
        self._last_name = "User"
        self._display_name = None
        self._is_verified = True
        self._is_admin = False
        self._roles = []
        self._created_at = datetime.utcnow()
        self._last_login = None
        self._account_locked = False
        self._failed_attempts = 0
        return self

    def username(self, username: str):
        """Set username."""
        self._username = username
        return self

    def email(self, email: str):
        """Set email address."""
        self._email = email
        return self

    def password(self, password: str):
        """Set password hash."""
        self._password = password
        return self

    def name(self, first_name: str, last_name: str = None):
        """Set first and last name."""
        self._first_name = first_name
        if last_name:
            self._last_name = last_name
        return self

    def display_name(self, display_name: str):
        """Set display name."""
        self._display_name = display_name
        return self

    def verified(self, is_verified: bool = True):
        """Set verification status."""
        self._is_verified = is_verified
        return self

    def admin(self, is_admin: bool = True):
        """Set admin status."""
        self._is_admin = is_admin
        return self

    def with_roles(self, *roles: Union[str, Role]):
        """Add roles to user."""
        for role in roles:
            if isinstance(role, str):
                role_obj = Role(name=role, description=f"{role} role")
                self._roles.append(role_obj)
            else:
                self._roles.append(role)
        return self

    def created_at(self, created_at: datetime):
        """Set creation timestamp."""
        self._created_at = created_at
        return self

    def last_login(self, last_login: datetime):
        """Set last login timestamp."""
        self._last_login = last_login
        return self

    def locked(self, is_locked: bool = True, failed_attempts: int = 5):
        """Set account locked status."""
        self._account_locked = is_locked
        self._failed_attempts = failed_attempts
        return self

    def build(self) -> User:
        """Build the user instance."""
        display_name = self._display_name or f"{self._first_name} {self._last_name}"

        user = User(
            username=self._username,
            email=self._email,
            hashed_password=self._password,
            first_name=self._first_name,
            last_name=self._last_name,
            display_name=display_name,
            is_verified=self._is_verified,
            created_at=self._created_at,
            last_login=self._last_login,
            account_locked=self._account_locked,
            failed_login_attempts=self._failed_attempts
        )

        # Add roles
        if self._is_admin and not any(role.name == "admin" for role in self._roles):
            admin_role = Role(name="admin", description="Administrator role")
            self._roles.append(admin_role)

        user.roles = self._roles
        return user


class AgentBuilder:
    """Builder for creating test agents with fluent interface."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset builder to default state."""
        self._agent_id = str(uuid.uuid4())
        self._name = f"agent_{uuid.uuid4().hex[:8]}"
        self._description = "Test agent for automated testing"
        self._agent_type = AgentType.CODE_AGENT
        self._status = AgentStatus.ACTIVE
        self._configuration = {}
        self._capabilities = ["test_capability"]
        self._tools = []
        self._created_at = datetime.utcnow()
        self._updated_at = None
        self._version = "1.0.0"
        self._owner_id = None
        return self

    def agent_id(self, agent_id: str):
        """Set agent ID."""
        self._agent_id = agent_id
        return self

    def name(self, name: str):
        """Set agent name."""
        self._name = name
        return self

    def description(self, description: str):
        """Set agent description."""
        self._description = description
        return self

    def agent_type(self, agent_type: AgentType):
        """Set agent type."""
        self._agent_type = agent_type
        return self

    def status(self, status: AgentStatus):
        """Set agent status."""
        self._status = status
        return self

    def configuration(self, config: Dict[str, Any]):
        """Set agent configuration."""
        self._configuration = config
        return self

    def add_capability(self, capability: str):
        """Add capability to agent."""
        if capability not in self._capabilities:
            self._capabilities.append(capability)
        return self

    def with_capabilities(self, *capabilities: str):
        """Set agent capabilities."""
        self._capabilities = list(capabilities)
        return self

    def add_tool(self, tool: str):
        """Add tool to agent."""
        if tool not in self._tools:
            self._tools.append(tool)
        return self

    def with_tools(self, *tools: str):
        """Set agent tools."""
        self._tools = list(tools)
        return self

    def version(self, version: str):
        """Set agent version."""
        self._version = version
        return self

    def owner(self, owner_id: int):
        """Set agent owner."""
        self._owner_id = owner_id
        return self

    def created_at(self, created_at: datetime):
        """Set creation timestamp."""
        self._created_at = created_at
        return self

    def updated_at(self, updated_at: datetime):
        """Set update timestamp."""
        self._updated_at = updated_at
        return self

    def build(self) -> Agent:
        """Build the agent instance."""
        config = self._configuration.copy()
        config.update({
            "capabilities": self._capabilities,
            "tools": self._tools,
            "version": self._version
        })

        return Agent(
            agent_id=self._agent_id,
            name=self._name,
            description=self._description,
            agent_type=self._agent_type,
            status=self._status,
            configuration=config,
            created_at=self._created_at,
            updated_at=self._updated_at,
            owner_id=self._owner_id
        )


class PlaybookBuilder:
    """Builder for creating test playbooks with fluent interface."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset builder to default state."""
        self._playbook_id = str(uuid.uuid4())
        self._name = f"playbook_{uuid.uuid4().hex[:8]}"
        self._description = "Test playbook for automated testing"
        self._category = PlaybookCategory.AUTOMATION
        self._status = PlaybookStatus.DRAFT
        self._version = "1.0.0"
        self._tags = ["test"]
        self._configuration = {}
        self._steps = []
        self._variables = {}
        self._created_at = datetime.utcnow()
        self._updated_at = None
        self._author_id = None
        return self

    def playbook_id(self, playbook_id: str):
        """Set playbook ID."""
        self._playbook_id = playbook_id
        return self

    def name(self, name: str):
        """Set playbook name."""
        self._name = name
        return self

    def description(self, description: str):
        """Set playbook description."""
        self._description = description
        return self

    def category(self, category: PlaybookCategory):
        """Set playbook category."""
        self._category = category
        return self

    def status(self, status: PlaybookStatus):
        """Set playbook status."""
        self._status = status
        return self

    def version(self, version: str):
        """Set playbook version."""
        self._version = version
        return self

    def add_tag(self, tag: str):
        """Add tag to playbook."""
        if tag not in self._tags:
            self._tags.append(tag)
        return self

    def with_tags(self, *tags: str):
        """Set playbook tags."""
        self._tags = list(tags)
        return self

    def configuration(self, config: Dict[str, Any]):
        """Set playbook configuration."""
        self._configuration = config
        return self

    def add_step(self, step_type: StepType, name: str, configuration: Dict[str, Any] = None):
        """Add step to playbook."""
        step = {
            "step_id": str(uuid.uuid4()),
            "name": name,
            "step_type": step_type,
            "configuration": configuration or {},
            "order": len(self._steps) + 1
        }
        self._steps.append(step)
        return self

    def with_steps(self, steps: List[Dict[str, Any]]):
        """Set playbook steps."""
        self._steps = steps
        return self

    def add_variable(self, name: str, value: Any, variable_type: str = "string"):
        """Add variable to playbook."""
        self._variables[name] = {
            "value": value,
            "type": variable_type
        }
        return self

    def with_variables(self, variables: Dict[str, Any]):
        """Set playbook variables."""
        self._variables = variables
        return self

    def author(self, author_id: int):
        """Set playbook author."""
        self._author_id = author_id
        return self

    def created_at(self, created_at: datetime):
        """Set creation timestamp."""
        self._created_at = created_at
        return self

    def updated_at(self, updated_at: datetime):
        """Set update timestamp."""
        self._updated_at = updated_at
        return self

    def build(self) -> Playbook:
        """Build the playbook instance."""
        config = self._configuration.copy()
        config.update({
            "steps": self._steps,
            "variables": self._variables
        })

        return Playbook(
            playbook_id=self._playbook_id,
            name=self._name,
            description=self._description,
            category=self._category,
            status=self._status,
            version=self._version,
            tags=self._tags,
            configuration=config,
            created_at=self._created_at,
            updated_at=self._updated_at,
            author_id=self._author_id
        )


class WorkflowBuilder:
    """Builder for creating test workflows with fluent interface."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset builder to default state."""
        self._workflow_id = str(uuid.uuid4())
        self._name = f"workflow_{uuid.uuid4().hex[:8]}"
        self._description = "Test workflow for automated testing"
        self._workflow_type = "sequential"
        self._configuration = {}
        self._steps = []
        self._triggers = []
        self._created_at = datetime.utcnow()
        self._updated_at = None
        self._author_id = None
        self._is_active = True
        return self

    def workflow_id(self, workflow_id: str):
        """Set workflow ID."""
        self._workflow_id = workflow_id
        return self

    def name(self, name: str):
        """Set workflow name."""
        self._name = name
        return self

    def description(self, description: str):
        """Set workflow description."""
        self._description = description
        return self

    def workflow_type(self, workflow_type: str):
        """Set workflow type."""
        self._workflow_type = workflow_type
        return self

    def configuration(self, config: Dict[str, Any]):
        """Set workflow configuration."""
        self._configuration = config
        return self

    def add_step(self, name: str, step_type: str, configuration: Dict[str, Any] = None):
        """Add step to workflow."""
        step = {
            "step_id": str(uuid.uuid4()),
            "name": name,
            "step_type": step_type,
            "configuration": configuration or {},
            "order": len(self._steps) + 1
        }
        self._steps.append(step)
        return self

    def with_steps(self, steps: List[Dict[str, Any]]):
        """Set workflow steps."""
        self._steps = steps
        return self

    def add_trigger(self, trigger_type: str, configuration: Dict[str, Any] = None):
        """Add trigger to workflow."""
        trigger = {
            "trigger_id": str(uuid.uuid4()),
            "trigger_type": trigger_type,
            "configuration": configuration or {}
        }
        self._triggers.append(trigger)
        return self

    def with_triggers(self, triggers: List[Dict[str, Any]]):
        """Set workflow triggers."""
        self._triggers = triggers
        return self

    def author(self, author_id: int):
        """Set workflow author."""
        self._author_id = author_id
        return self

    def active(self, is_active: bool = True):
        """Set workflow active status."""
        self._is_active = is_active
        return self

    def created_at(self, created_at: datetime):
        """Set creation timestamp."""
        self._created_at = created_at
        return self

    def updated_at(self, updated_at: datetime):
        """Set update timestamp."""
        self._updated_at = updated_at
        return self

    def build(self) -> Workflow:
        """Build the workflow instance."""
        config = self._configuration.copy()
        config.update({
            "steps": self._steps,
            "triggers": self._triggers
        })

        return Workflow(
            workflow_id=self._workflow_id,
            name=self._name,
            description=self._description,
            workflow_type=self._workflow_type,
            configuration=config,
            created_at=self._created_at,
            updated_at=self._updated_at,
            author_id=self._author_id,
            is_active=self._is_active
        )


class ExecutionBuilder:
    """Builder for creating test executions with fluent interface."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset builder to default state."""
        self._execution_id = str(uuid.uuid4())
        self._playbook_id = None
        self._workflow_id = None
        self._status = ExecutionStatus.PENDING
        self._started_at = None
        self._completed_at = None
        self._configuration = {}
        self._input_data = {}
        self._output_data = {}
        self._error_message = None
        self._progress = 0
        self._step_executions = []
        self._triggered_by = None
        return self

    def execution_id(self, execution_id: str):
        """Set execution ID."""
        self._execution_id = execution_id
        return self

    def playbook(self, playbook_id: str):
        """Set playbook ID."""
        self._playbook_id = playbook_id
        return self

    def workflow(self, workflow_id: str):
        """Set workflow ID."""
        self._workflow_id = workflow_id
        return self

    def status(self, status: ExecutionStatus):
        """Set execution status."""
        self._status = status
        return self

    def started_at(self, started_at: datetime):
        """Set start timestamp."""
        self._started_at = started_at
        return self

    def completed_at(self, completed_at: datetime):
        """Set completion timestamp."""
        self._completed_at = completed_at
        return self

    def configuration(self, config: Dict[str, Any]):
        """Set execution configuration."""
        self._configuration = config
        return self

    def input_data(self, input_data: Dict[str, Any]):
        """Set input data."""
        self._input_data = input_data
        return self

    def output_data(self, output_data: Dict[str, Any]):
        """Set output data."""
        self._output_data = output_data
        return self

    def error_message(self, error_message: str):
        """Set error message."""
        self._error_message = error_message
        return self

    def progress(self, progress: int):
        """Set execution progress (0-100)."""
        self._progress = max(0, min(100, progress))
        return self

    def triggered_by(self, triggered_by: str):
        """Set who/what triggered the execution."""
        self._triggered_by = triggered_by
        return self

    def add_step_execution(self, step_id: str, status: StepStatus, started_at: datetime = None):
        """Add step execution."""
        step_execution = {
            "step_execution_id": str(uuid.uuid4()),
            "step_id": step_id,
            "status": status,
            "started_at": started_at or datetime.utcnow(),
            "completed_at": None if status in [StepStatus.PENDING, StepStatus.RUNNING] else datetime.utcnow()
        }
        self._step_executions.append(step_execution)
        return self

    def build_playbook_execution(self) -> PlaybookExecution:
        """Build playbook execution instance."""
        if not self._playbook_id:
            raise ValueError("Playbook ID is required for playbook execution")

        return PlaybookExecution(
            execution_id=self._execution_id,
            playbook_id=self._playbook_id,
            status=self._status,
            started_at=self._started_at,
            completed_at=self._completed_at,
            configuration=self._configuration,
            input_data=self._input_data,
            output_data=self._output_data,
            error_message=self._error_message,
            progress=self._progress,
            triggered_by=self._triggered_by
        )

    def build_workflow_execution(self) -> WorkflowExecution:
        """Build workflow execution instance."""
        if not self._workflow_id:
            raise ValueError("Workflow ID is required for workflow execution")

        return WorkflowExecution(
            execution_id=self._execution_id,
            workflow_id=self._workflow_id,
            status=self._status,
            started_at=self._started_at,
            completed_at=self._completed_at,
            configuration=self._configuration,
            input_data=self._input_data,
            output_data=self._output_data,
            error_message=self._error_message,
            progress=self._progress,
            triggered_by=self._triggered_by
        )


# Convenience functions for common scenarios
def create_test_user(username: str = None, is_admin: bool = False) -> User:
    """Create a simple test user."""
    builder = UserBuilder()
    if username:
        builder.username(username)
    if is_admin:
        builder.admin(True)
    return builder.build()


def create_test_agent(name: str = None, agent_type: AgentType = AgentType.CODE_AGENT) -> Agent:
    """Create a simple test agent."""
    builder = AgentBuilder()
    if name:
        builder.name(name)
    builder.agent_type(agent_type)
    return builder.build()


def create_test_playbook(name: str = None, category: PlaybookCategory = PlaybookCategory.AUTOMATION) -> Playbook:
    """Create a simple test playbook."""
    builder = PlaybookBuilder()
    if name:
        builder.name(name)
    builder.category(category)
    return builder.build()


def create_test_workflow(name: str = None, workflow_type: str = "sequential") -> Workflow:
    """Create a simple test workflow."""
    builder = WorkflowBuilder()
    if name:
        builder.name(name)
    builder.workflow_type(workflow_type)
    return builder.build()
