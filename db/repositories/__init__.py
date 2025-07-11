"""
Database Repositories Package

This package contains repository implementations for database operations in the
Agentical framework, following the repository pattern to abstract data access logic
from business logic.

Features:
- Repository pattern implementation
- Type-safe CRUD operations
- Optimized query performance
- Caching for frequently accessed data
- Integration with Logfire observability
"""

from agentical.db.repositories.base import (
    BaseRepository,
    AsyncBaseRepository
)

from agentical.db.repositories.user import (
    UserRepository,
    AsyncUserRepository
)

from agentical.db.repositories.agent import (
    AgentRepository,
    AsyncAgentRepository
)

from agentical.db.repositories.tool import (
    ToolRepository,
    AsyncToolRepository
)

from agentical.db.repositories.workflow import (
    WorkflowRepository,
    AsyncWorkflowRepository
)

from agentical.db.repositories.task import (
    TaskRepository,
    AsyncTaskRepository
)

from agentical.db.repositories.playbook import (
    PlaybookRepository,
    AsyncPlaybookRepository
)

# Export all repositories for easy imports
__all__ = [
    # Base repositories
    "BaseRepository",
    "AsyncBaseRepository",

    # User repositories
    "UserRepository",
    "AsyncUserRepository",

    # Agent repositories
    "AgentRepository",
    "AsyncAgentRepository",

    # Tool repositories
    "ToolRepository",
    "AsyncToolRepository",

    # Workflow repositories
    "WorkflowRepository",
    "AsyncWorkflowRepository",

    # Task repositories
    "TaskRepository",
    "AsyncTaskRepository",

    # Playbook repositories
    "PlaybookRepository",
    "AsyncPlaybookRepository",
]
