"""
Agents Package for Agentical Framework

This package provides the agent infrastructure for the Agentical framework,
including base agent classes, concrete agent implementations, and agent
management utilities.

The agent system is based on a perception-decision-action model, where agents:
1. Perceive inputs and context (perception phase)
2. Make decisions based on their understanding (decision phase)
3. Take actions through tool usage (action phase)
4. Reflect on their performance (reflection phase)
"""

from .base_agent import (
    BaseAgent,
    AgentMetadata,
    AgentCapability,
    AgentStatus,
    AgentExecutionContext,
    AgentExecutionResult,
    InfrastructureConnections
)

from .generic_agent import (
    GenericAgent,
    PerceptionResult,
    DecisionResult,
    ActionResult,
    ToolExecutionResult
)

from .agent_registry import (
    AgentRegistry,
    get_agent_registry
)

# Custom Agents (Task 4.4)
from .codifier_agent import CodifierAgent
from .io_agent import IOAgent
from .playbook_agent import PlaybookAgent
from .super_agent import SuperAgent
from .code_agent import CodeAgent
from .devops_agent import DevOpsAgent
from .github_agent import GitHubAgent

# Re-export for convenience
agent_registry = get_agent_registry()

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentMetadata",
    "AgentCapability",
    "AgentStatus",
    "AgentExecutionContext",
    "AgentExecutionResult",
    "InfrastructureConnections",

    # Concrete implementations
    "GenericAgent",
    "PerceptionResult",
    "DecisionResult",
    "ActionResult",
    "ToolExecutionResult",

    # Custom Agents (Task 4.4)
    "CodifierAgent",
    "IOAgent",
    "PlaybookAgent",
    "SuperAgent",
    "CodeAgent",
    "DevOpsAgent",
    "GitHubAgent",

    # Registry
    "AgentRegistry",
    "get_agent_registry",
    "agent_registry"
]
