"""
Playbook Agent Capabilities System

Enhanced agent capabilities data model for the Agentical playbook system.
This module extends the base agent capabilities to provide comprehensive
support for playbook execution, agent pool discovery, and dynamic coordination.

Features:
- Enhanced capability definitions with playbook-specific attributes
- Agent pool discovery and filtering
- Real-time capability assessment and load balancing
- Tool compatibility and workflow support mapping
- Performance metrics and health monitoring
- Dynamic capability updates and versioning
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, Field, validator
import uuid

try:
    import logfire
except ImportError:
    class MockLogfire:
        @staticmethod
        def span(name, **kwargs):
            class MockSpan:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return MockSpan()
        @staticmethod
        def info(*args, **kwargs): pass
        @staticmethod
        def error(*args, **kwargs): pass
    logfire = MockLogfire()

from .base_agent import AgentCapability as BaseAgentCapability, AgentMetadata, AgentStatus
from ..db.schemas.playbook_schema_manager import AgentCapability as SchemaAgentCapability

logger = logging.getLogger(__name__)


class PlaybookCapabilityType(str, Enum):
    """Types of playbook-specific capabilities."""
    TASK_EXECUTION = "task_execution"
    COORDINATION = "coordination"
    MONITORING = "monitoring"
    DOCUMENTATION = "documentation"
    VALIDATION = "validation"
    COMMUNICATION = "communication"
    DATA_PROCESSING = "data_processing"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"
    INTEGRATION = "integration"


class CapabilityComplexity(str, Enum):
    """Complexity levels for capabilities."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class ResourceType(str, Enum):
    """Types of resources agents can consume."""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    STORAGE = "storage"
    API_CALLS = "api_calls"
    TOKENS = "tokens"


class HealthStatus(str, Enum):
    """Agent health status for pool discovery."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class ResourceLimit:
    """Resource consumption limits for agents."""
    type: ResourceType
    max_value: float
    current_usage: float = 0.0
    warning_threshold: float = 0.8
    critical_threshold: float = 0.95
    unit: str = ""

    @property
    def usage_percentage(self) -> float:
        """Calculate current usage percentage."""
        if self.max_value == 0:
            return 0.0
        return min(self.current_usage / self.max_value, 1.0)

    @property
    def status(self) -> HealthStatus:
        """Get health status based on usage."""
        usage_pct = self.usage_percentage
        if usage_pct >= self.critical_threshold:
            return HealthStatus.CRITICAL
        elif usage_pct >= self.warning_threshold:
            return HealthStatus.WARNING
        return HealthStatus.HEALTHY


@dataclass
class PerformanceMetrics:
    """Performance metrics for agent capabilities."""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    last_execution_at: Optional[datetime] = None
    error_rate: float = 0.0
    throughput_per_hour: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions

    def update_execution(self, success: bool, execution_time: float):
        """Update metrics with new execution data."""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        # Update timing metrics
        if self.total_executions == 1:
            self.average_execution_time = execution_time
        else:
            self.average_execution_time = (
                (self.average_execution_time * (self.total_executions - 1) + execution_time) /
                self.total_executions
            )

        self.min_execution_time = min(self.min_execution_time, execution_time)
        self.max_execution_time = max(self.max_execution_time, execution_time)
        self.last_execution_at = datetime.utcnow()

        # Update error rate
        self.error_rate = self.failed_executions / self.total_executions


class PlaybookCapability(BaseModel):
    """Enhanced capability definition for playbook execution."""

    # Basic capability information
    name: str = Field(..., description="Capability name")
    display_name: str = Field(..., description="Human-readable capability name")
    description: str = Field(..., description="Detailed capability description")
    capability_type: PlaybookCapabilityType = Field(..., description="Type of capability")
    complexity: CapabilityComplexity = Field(default=CapabilityComplexity.MODERATE, description="Capability complexity")

    # Playbook-specific attributes
    supported_step_types: List[str] = Field(default_factory=list, description="Supported playbook step types")
    required_tools: List[str] = Field(default_factory=list, description="Required MCP tools")
    optional_tools: List[str] = Field(default_factory=list, description="Optional MCP tools for enhanced functionality")
    supported_workflows: List[str] = Field(default_factory=list, description="Supported workflow types")

    # Execution characteristics
    typical_execution_time: float = Field(default=30.0, description="Typical execution time in seconds")
    max_execution_time: float = Field(default=300.0, description="Maximum execution time in seconds")
    can_run_parallel: bool = Field(default=True, description="Can execute in parallel with other capabilities")
    requires_human_input: bool = Field(default=False, description="Requires human intervention")
    is_stateful: bool = Field(default=False, description="Maintains state between executions")

    # Resource requirements
    cpu_intensive: bool = Field(default=False, description="Is CPU intensive")
    memory_intensive: bool = Field(default=False, description="Is memory intensive")
    network_intensive: bool = Field(default=False, description="Is network intensive")
    estimated_tokens: int = Field(default=1000, description="Estimated token consumption")

    # Validation and testing
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="Input validation schema")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="Output format schema")
    test_cases: List[Dict[str, Any]] = Field(default_factory=list, description="Test cases for validation")

    # Dependencies and prerequisites
    depends_on_capabilities: List[str] = Field(default_factory=list, description="Required prerequisite capabilities")
    conflicts_with: List[str] = Field(default_factory=list, description="Conflicting capabilities")
    knowledge_domains: List[str] = Field(default_factory=list, description="Relevant knowledge domains")

    # Versioning and maintenance
    version: str = Field(default="1.0.0", description="Capability version")
    deprecated: bool = Field(default=False, description="Is this capability deprecated")
    replacement_capability: Optional[str] = Field(None, description="Replacement capability if deprecated")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Classification tags")


class AgentPoolEntry(BaseModel):
    """Entry in the agent pool for discovery and selection."""

    # Agent identification
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Agent type/class")
    agent_name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent description")

    # Capabilities and tools
    capabilities: List[PlaybookCapability] = Field(default_factory=list, description="Agent capabilities")
    available_tools: List[str] = Field(default_factory=list, description="Available MCP tools")
    supported_workflows: List[str] = Field(default_factory=list, description="Supported workflow types")
    specializations: List[str] = Field(default_factory=list, description="Agent specializations")

    # Capacity and performance
    max_concurrent_executions: int = Field(default=1, description="Maximum concurrent executions")
    current_load: int = Field(default=0, description="Current active executions")
    resource_limits: List[ResourceLimit] = Field(default_factory=list, description="Resource consumption limits")
    performance_metrics: Dict[str, PerformanceMetrics] = Field(default_factory=dict, description="Performance metrics by capability")

    # Health and status
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN, description="Current health status")
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow, description="Last heartbeat timestamp")
    uptime_start: datetime = Field(default_factory=datetime.utcnow, description="Agent startup time")
    error_count_24h: int = Field(default=0, description="Error count in last 24 hours")

    # Configuration
    priority: int = Field(default=5, description="Agent priority (1-10, higher is better)")
    environment: str = Field(default="production", description="Environment (development/staging/production)")
    region: str = Field(default="default", description="Deployment region")
    cost_per_execution: float = Field(default=0.0, description="Estimated cost per execution")

    # Metadata
    version: str = Field(default="1.0.0", description="Agent version")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Registration timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Agent tags")

    @property
    def load_percentage(self) -> float:
        """Calculate current load percentage."""
        if self.max_concurrent_executions == 0:
            return 100.0
        return min(self.current_load / self.max_concurrent_executions * 100, 100.0)

    @property
    def is_available(self) -> bool:
        """Check if agent is available for new executions."""
        return (
            self.health_status in [HealthStatus.HEALTHY, HealthStatus.WARNING] and
            self.current_load < self.max_concurrent_executions and
            self._is_heartbeat_recent()
        )

    @property
    def uptime_hours(self) -> float:
        """Calculate uptime in hours."""
        return (datetime.utcnow() - self.uptime_start).total_seconds() / 3600

    def _is_heartbeat_recent(self, max_age_minutes: int = 5) -> bool:
        """Check if heartbeat is recent enough."""
        max_age = timedelta(minutes=max_age_minutes)
        return (datetime.utcnow() - self.last_heartbeat) <= max_age

    def get_capability(self, capability_name: str) -> Optional[PlaybookCapability]:
        """Get capability by name."""
        for capability in self.capabilities:
            if capability.name == capability_name:
                return capability
        return None

    def has_tool(self, tool_name: str) -> bool:
        """Check if agent has access to a specific tool."""
        return tool_name in self.available_tools

    def supports_workflow(self, workflow_type: str) -> bool:
        """Check if agent supports a specific workflow type."""
        return workflow_type in self.supported_workflows or "all_types" in self.supported_workflows

    def can_execute_step(self, step_type: str, required_tools: List[str] = None) -> bool:
        """Check if agent can execute a specific step type."""
        # Check if any capability supports this step type
        supports_step = any(
            step_type in cap.supported_step_types
            for cap in self.capabilities
        )

        if not supports_step:
            return False

        # Check tool requirements
        if required_tools:
            return all(self.has_tool(tool) for tool in required_tools)

        return True


class CapabilityFilter(BaseModel):
    """Filter criteria for agent capability discovery."""

    # Basic filters
    capability_types: List[PlaybookCapabilityType] = Field(default_factory=list, description="Required capability types")
    step_types: List[str] = Field(default_factory=list, description="Required step types")
    required_tools: List[str] = Field(default_factory=list, description="Required tools")
    workflow_types: List[str] = Field(default_factory=list, description="Required workflow support")

    # Performance filters
    max_execution_time: Optional[float] = Field(None, description="Maximum execution time requirement")
    min_success_rate: float = Field(default=0.0, description="Minimum success rate requirement")
    max_error_rate: float = Field(default=1.0, description="Maximum error rate tolerance")

    # Capacity filters
    min_available_capacity: int = Field(default=1, description="Minimum available execution slots")
    max_current_load: float = Field(default=100.0, description="Maximum current load percentage")
    health_statuses: List[HealthStatus] = Field(default_factory=lambda: [HealthStatus.HEALTHY], description="Acceptable health statuses")

    # Environment filters
    environments: List[str] = Field(default_factory=list, description="Target environments")
    regions: List[str] = Field(default_factory=list, description="Target regions")
    agent_types: List[str] = Field(default_factory=list, description="Specific agent types")

    # Advanced filters
    exclude_agents: List[str] = Field(default_factory=list, description="Agent IDs to exclude")
    prefer_agents: List[str] = Field(default_factory=list, description="Preferred agent IDs")
    max_cost_per_execution: Optional[float] = Field(None, description="Maximum cost per execution")
    tags: List[str] = Field(default_factory=list, description="Required tags")


class CapabilityMatchResult(BaseModel):
    """Result of capability matching for an agent."""

    agent_id: str = Field(..., description="Agent identifier")
    match_score: float = Field(..., description="Match score (0.0 to 1.0)")
    matched_capabilities: List[str] = Field(default_factory=list, description="Names of matched capabilities")
    missing_requirements: List[str] = Field(default_factory=list, description="Missing requirements")
    performance_score: float = Field(default=0.0, description="Performance score based on metrics")
    availability_score: float = Field(default=0.0, description="Availability score based on load and health")

    # Detailed scoring breakdown
    capability_score: float = Field(default=0.0, description="How well capabilities match requirements")
    tool_score: float = Field(default=0.0, description="Tool availability score")
    workflow_score: float = Field(default=0.0, description="Workflow support score")
    load_score: float = Field(default=0.0, description="Current load score (lower load = higher score)")
    health_score: float = Field(default=0.0, description="Health status score")

    # Execution estimates
    estimated_execution_time: float = Field(default=0.0, description="Estimated execution time")
    estimated_cost: float = Field(default=0.0, description="Estimated execution cost")
    confidence_level: float = Field(default=0.0, description="Confidence in the match")

    @property
    def is_viable(self) -> bool:
        """Check if this is a viable match."""
        return (
            self.match_score >= 0.5 and
            len(self.missing_requirements) == 0 and
            self.health_score > 0.0
        )

    @property
    def recommendation_level(self) -> str:
        """Get recommendation level based on scores."""
        if self.match_score >= 0.9:
            return "excellent"
        elif self.match_score >= 0.75:
            return "good"
        elif self.match_score >= 0.5:
            return "acceptable"
        else:
            return "poor"


def create_default_capabilities() -> List[PlaybookCapability]:
    """Create default capabilities for common agent types."""
    return [
        # SuperAgent capabilities
        PlaybookCapability(
            name="meta_coordination",
            display_name="Meta Coordination",
            description="Coordinate multiple agents and complex workflows",
            capability_type=PlaybookCapabilityType.COORDINATION,
            complexity=CapabilityComplexity.EXPERT,
            supported_step_types=["agent_task", "parallel", "condition"],
            required_tools=["ptolemies-mcp", "taskmaster-ai"],
            supported_workflows=["all_types"],
            typical_execution_time=60.0,
            max_execution_time=600.0,
            can_run_parallel=True,
            is_stateful=True,
            specializations=["supervision", "orchestration", "decision_making"]
        ),

        # CodifierAgent capabilities
        PlaybookCapability(
            name="documentation_generation",
            display_name="Documentation Generation",
            description="Generate comprehensive documentation and AAR reports",
            capability_type=PlaybookCapabilityType.DOCUMENTATION,
            complexity=CapabilityComplexity.MODERATE,
            supported_step_types=["documentation", "verification"],
            required_tools=["filesystem", "git", "ptolemies-mcp"],
            supported_workflows=["sequential", "pipeline"],
            typical_execution_time=30.0,
            max_execution_time=300.0,
            specializations=["aar_generation", "knowledge_codification"]
        ),

        # IOAgent capabilities
        PlaybookCapability(
            name="system_monitoring",
            display_name="System Monitoring",
            description="Monitor system health, logs, and performance",
            capability_type=PlaybookCapabilityType.MONITORING,
            complexity=CapabilityComplexity.MODERATE,
            supported_step_types=["verification", "monitoring", "condition"],
            required_tools=["logfire-mcp", "fetch"],
            supported_workflows=["loop", "conditional", "parallel"],
            typical_execution_time=15.0,
            max_execution_time=180.0,
            can_run_parallel=True,
            specializations=["health_checks", "performance_monitoring", "alerting"]
        ),

        # PlaybookAgent capabilities
        PlaybookCapability(
            name="playbook_orchestration",
            display_name="Playbook Orchestration",
            description="Create, manage, and execute playbooks",
            capability_type=PlaybookCapabilityType.COORDINATION,
            complexity=CapabilityComplexity.COMPLEX,
            supported_step_types=["agent_task", "human_input", "condition"],
            required_tools=["taskmaster-ai", "context7-mcp"],
            supported_workflows=["all_types"],
            typical_execution_time=120.0,
            max_execution_time=1800.0,
            is_stateful=True,
            requires_human_input=True,
            specializations=["strategic_execution", "workflow_management"]
        )
    ]


def convert_to_schema_capability(pool_entry: AgentPoolEntry) -> SchemaAgentCapability:
    """Convert agent pool entry to schema manager capability format."""
    return SchemaAgentCapability(
        agent_id=pool_entry.agent_id,
        agent_type=pool_entry.agent_type,
        available_tools=pool_entry.available_tools,
        supported_workflows=pool_entry.supported_workflows,
        max_concurrent=pool_entry.max_concurrent_executions,
        specializations=pool_entry.specializations,
        resource_limits={
            limit.type.value: {
                "max_value": limit.max_value,
                "current_usage": limit.current_usage,
                "unit": limit.unit
            }
            for limit in pool_entry.resource_limits
        }
    )


def create_pool_entry_from_metadata(metadata: AgentMetadata, **kwargs) -> AgentPoolEntry:
    """Create agent pool entry from agent metadata."""
    return AgentPoolEntry(
        agent_id=metadata.id,
        agent_type=metadata.__class__.__name__.replace("Agent", "").lower(),
        agent_name=metadata.name,
        description=metadata.description,
        available_tools=metadata.available_tools,
        capabilities=create_default_capabilities(),  # Will be enhanced per agent type
        version=metadata.version,
        tags=metadata.tags,
        **kwargs
    )
