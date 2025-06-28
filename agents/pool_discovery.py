"""
Agent Pool Discovery Service for Agentical Playbook System

This module provides comprehensive agent pool discovery, filtering, and selection
capabilities for the playbook execution system. It integrates with the existing
agent registry and enhances it with playbook-specific functionality.

Features:
- Real-time agent discovery and capability assessment
- Advanced filtering and matching algorithms
- Load balancing and performance optimization
- Health monitoring and heartbeat management
- Integration with SurrealDB for persistence
- Automatic agent registration and updates
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from collections import defaultdict
import json
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
        @staticmethod
        def warning(*args, **kwargs): pass
    logfire = MockLogfire()

from .agent_registry import AgentRegistry, get_agent_registry
from .playbook_capabilities import (
    AgentPoolEntry, PlaybookCapability, CapabilityFilter, CapabilityMatchResult,
    HealthStatus, ResourceLimit, ResourceType, PerformanceMetrics,
    create_default_capabilities, convert_to_schema_capability,
    create_pool_entry_from_metadata
)
from ..db.schemas.playbook_schema_manager import PlaybookSchemaManager, PlaybookSchemaFactory

logger = logging.getLogger(__name__)


class AgentPoolDiscoveryService:
    """
    Service for discovering and managing the agent pool for playbook execution.

    Provides advanced filtering, matching, and selection capabilities for agents
    based on playbook requirements and real-time system state.
    """

    def __init__(self, schema_manager: Optional[PlaybookSchemaManager] = None):
        """
        Initialize the agent pool discovery service.

        Args:
            schema_manager: Optional schema manager for database operations
        """
        self.agent_registry = get_agent_registry()
        self.schema_manager = schema_manager
        self.agent_pool: Dict[str, AgentPoolEntry] = {}
        self.last_discovery_time: Optional[datetime] = None
        self.discovery_interval = timedelta(minutes=1)
        self.heartbeat_timeout = timedelta(minutes=5)

        # Performance tracking
        self.discovery_metrics = {
            "total_discoveries": 0,
            "successful_matches": 0,
            "failed_matches": 0,
            "average_discovery_time": 0.0
        }

    async def initialize(self) -> bool:
        """
        Initialize the discovery service and perform initial agent discovery.

        Returns:
            bool: Success status
        """
        with logfire.span("Initialize agent pool discovery"):
            try:
                # Get schema manager if not provided
                if self.schema_manager is None:
                    self.schema_manager = await PlaybookSchemaFactory.get_manager()

                # Perform initial discovery
                success = await self.discover_agents()

                if success:
                    logfire.info("Agent pool discovery service initialized",
                               agent_count=len(self.agent_pool))
                    logger.info(f"Initialized with {len(self.agent_pool)} agents")

                return success

            except Exception as e:
                logfire.error("Failed to initialize agent pool discovery", error=str(e))
                logger.error(f"Initialization failed: {e}")
                return False

    async def discover_agents(self, force_refresh: bool = False) -> bool:
        """
        Discover available agents and update the pool.

        Args:
            force_refresh: Force refresh even if cache is recent

        Returns:
            bool: Success status
        """
        with logfire.span("Discover agents", force_refresh=force_refresh):
            start_time = datetime.utcnow()

            try:
                # Check if discovery is needed
                if not force_refresh and self._is_cache_fresh():
                    logger.debug("Agent pool cache is fresh, skipping discovery")
                    return True

                logger.info("Starting agent pool discovery")

                # Get agents from registry
                registry_agents = self.agent_registry.list_agents()

                # Get agents from database
                db_agents = []
                if self.schema_manager:
                    db_agents = await self.schema_manager.get_agent_pool(filter_healthy=False)

                # Merge and update agent pool
                updated_count = await self._update_agent_pool(registry_agents, db_agents)

                # Update discovery metrics
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                self.discovery_metrics["total_discoveries"] += 1
                self.discovery_metrics["average_discovery_time"] = (
                    (self.discovery_metrics["average_discovery_time"] * (self.discovery_metrics["total_discoveries"] - 1) + execution_time) /
                    self.discovery_metrics["total_discoveries"]
                )

                self.last_discovery_time = datetime.utcnow()

                logfire.info("Agent discovery completed",
                           agents_found=len(self.agent_pool),
                           updated_agents=updated_count,
                           execution_time=execution_time)

                return True

            except Exception as e:
                logfire.error("Agent discovery failed", error=str(e))
                logger.error(f"Agent discovery failed: {e}")
                return False

    async def find_capable_agents(
        self,
        capability_filter: CapabilityFilter,
        max_results: int = 10,
        sort_by: str = "match_score"
    ) -> List[CapabilityMatchResult]:
        """
        Find agents that match the given capability requirements.

        Args:
            capability_filter: Filter criteria for capability matching
            max_results: Maximum number of results to return
            sort_by: Sort criteria ("match_score", "performance", "availability")

        Returns:
            List of capability match results
        """
        with logfire.span("Find capable agents", filter_count=len(capability_filter.capability_types)):
            try:
                # Ensure agent pool is fresh
                await self.discover_agents()

                # Filter and score agents
                matches = []
                for agent_id, agent_entry in self.agent_pool.items():
                    if self._passes_basic_filters(agent_entry, capability_filter):
                        match_result = await self._calculate_match_score(agent_entry, capability_filter)
                        if match_result.is_viable:
                            matches.append(match_result)

                # Sort results
                if sort_by == "match_score":
                    matches.sort(key=lambda x: x.match_score, reverse=True)
                elif sort_by == "performance":
                    matches.sort(key=lambda x: x.performance_score, reverse=True)
                elif sort_by == "availability":
                    matches.sort(key=lambda x: x.availability_score, reverse=True)

                # Limit results
                results = matches[:max_results]

                logfire.info("Capability matching completed",
                           total_candidates=len(self.agent_pool),
                           viable_matches=len(matches),
                           returned_results=len(results))

                if results:
                    self.discovery_metrics["successful_matches"] += 1
                else:
                    self.discovery_metrics["failed_matches"] += 1

                return results

            except Exception as e:
                logfire.error("Capability matching failed", error=str(e))
                logger.error(f"Capability matching failed: {e}")
                self.discovery_metrics["failed_matches"] += 1
                return []

    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentPoolEntry]:
        """
        Get specific agent from the pool by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent pool entry or None if not found
        """
        await self.discover_agents()
        return self.agent_pool.get(agent_id)

    async def get_available_agents(
        self,
        health_filter: List[HealthStatus] = None,
        max_load_percentage: float = 80.0
    ) -> List[AgentPoolEntry]:
        """
        Get all currently available agents.

        Args:
            health_filter: Acceptable health statuses
            max_load_percentage: Maximum load percentage for availability

        Returns:
            List of available agent pool entries
        """
        if health_filter is None:
            health_filter = [HealthStatus.HEALTHY, HealthStatus.WARNING]

        await self.discover_agents()

        available_agents = []
        for agent_entry in self.agent_pool.values():
            if (
                agent_entry.health_status in health_filter and
                agent_entry.load_percentage <= max_load_percentage and
                agent_entry.is_available
            ):
                available_agents.append(agent_entry)

        return available_agents

    async def update_agent_heartbeat(self, agent_id: str) -> bool:
        """
        Update heartbeat for a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            bool: Success status
        """
        try:
            # Update in local pool
            if agent_id in self.agent_pool:
                self.agent_pool[agent_id].last_heartbeat = datetime.utcnow()

            # Update in database
            if self.schema_manager:
                await self.schema_manager.update_agent_heartbeat(agent_id)

            return True

        except Exception as e:
            logger.error(f"Failed to update heartbeat for {agent_id}: {e}")
            return False

    async def update_agent_load(self, agent_id: str, current_load: int) -> bool:
        """
        Update current load for a specific agent.

        Args:
            agent_id: Agent identifier
            current_load: Current number of active executions

        Returns:
            bool: Success status
        """
        try:
            if agent_id in self.agent_pool:
                self.agent_pool[agent_id].current_load = current_load
                self.agent_pool[agent_id].updated_at = datetime.utcnow()

                # Update health status based on load
                load_percentage = self.agent_pool[agent_id].load_percentage
                if load_percentage >= 95:
                    self.agent_pool[agent_id].health_status = HealthStatus.CRITICAL
                elif load_percentage >= 80:
                    self.agent_pool[agent_id].health_status = HealthStatus.WARNING
                else:
                    self.agent_pool[agent_id].health_status = HealthStatus.HEALTHY

                return True

        except Exception as e:
            logger.error(f"Failed to update load for {agent_id}: {e}")
            return False

    async def register_agent_capability(self, agent_id: str, capability: PlaybookCapability) -> bool:
        """
        Register a new capability for an agent.

        Args:
            agent_id: Agent identifier
            capability: Capability to register

        Returns:
            bool: Success status
        """
        try:
            if agent_id in self.agent_pool:
                # Check if capability already exists
                existing_cap = self.agent_pool[agent_id].get_capability(capability.name)
                if existing_cap:
                    # Update existing capability
                    capabilities = self.agent_pool[agent_id].capabilities
                    for i, cap in enumerate(capabilities):
                        if cap.name == capability.name:
                            capabilities[i] = capability
                            break
                else:
                    # Add new capability
                    self.agent_pool[agent_id].capabilities.append(capability)

                self.agent_pool[agent_id].updated_at = datetime.utcnow()

                logfire.info("Agent capability registered",
                           agent_id=agent_id,
                           capability_name=capability.name)

                return True

        except Exception as e:
            logfire.error("Failed to register agent capability",
                        agent_id=agent_id,
                        capability_name=capability.name,
                        error=str(e))
            return False

    async def get_pool_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the agent pool.

        Returns:
            Dict containing pool statistics
        """
        await self.discover_agents()

        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(self.agent_pool),
            "available_agents": 0,
            "healthy_agents": 0,
            "agents_by_type": defaultdict(int),
            "agents_by_health": defaultdict(int),
            "total_capacity": 0,
            "current_load": 0,
            "average_load_percentage": 0.0,
            "discovery_metrics": self.discovery_metrics.copy()
        }

        total_load_percentage = 0.0

        for agent_entry in self.agent_pool.values():
            # Count by availability
            if agent_entry.is_available:
                stats["available_agents"] += 1

            # Count by health
            if agent_entry.health_status == HealthStatus.HEALTHY:
                stats["healthy_agents"] += 1

            # Count by type
            stats["agents_by_type"][agent_entry.agent_type] += 1

            # Count by health status
            stats["agents_by_health"][agent_entry.health_status.value] += 1

            # Capacity and load
            stats["total_capacity"] += agent_entry.max_concurrent_executions
            stats["current_load"] += agent_entry.current_load
            total_load_percentage += agent_entry.load_percentage

        # Calculate averages
        if len(self.agent_pool) > 0:
            stats["average_load_percentage"] = total_load_percentage / len(self.agent_pool)

        return stats

    # Private helper methods

    def _is_cache_fresh(self) -> bool:
        """Check if the agent pool cache is fresh enough."""
        if self.last_discovery_time is None:
            return False
        return (datetime.utcnow() - self.last_discovery_time) < self.discovery_interval

    async def _update_agent_pool(
        self,
        registry_agents: List[Dict[str, Any]],
        db_agents: List[Dict[str, Any]]
    ) -> int:
        """Update the agent pool with discovered agents."""
        updated_count = 0

        # Process registry agents
        for agent_info in registry_agents:
            agent_id = agent_info["id"]

            if agent_id in self.agent_pool:
                # Update existing entry
                self.agent_pool[agent_id].updated_at = datetime.utcnow()
                self.agent_pool[agent_id].last_heartbeat = datetime.utcnow()
            else:
                # Create new entry
                try:
                    agent = self.agent_registry.get_agent(agent_id)
                    pool_entry = create_pool_entry_from_metadata(agent.metadata)
                    self.agent_pool[agent_id] = pool_entry
                    updated_count += 1
                except Exception as e:
                    logger.warning(f"Failed to create pool entry for {agent_id}: {e}")

        # Process database agents
        for db_agent in db_agents:
            agent_id = db_agent.get("agent_id")
            if not agent_id:
                continue

            if agent_id in self.agent_pool:
                # Update with database information
                self._update_from_db_data(self.agent_pool[agent_id], db_agent)
            else:
                # Create entry from database data
                pool_entry = self._create_from_db_data(db_agent)
                if pool_entry:
                    self.agent_pool[agent_id] = pool_entry
                    updated_count += 1

        # Remove stale agents
        current_time = datetime.utcnow()
        stale_agents = []
        for agent_id, agent_entry in self.agent_pool.items():
            if (current_time - agent_entry.last_heartbeat) > self.heartbeat_timeout:
                stale_agents.append(agent_id)

        for agent_id in stale_agents:
            del self.agent_pool[agent_id]
            logger.info(f"Removed stale agent: {agent_id}")

        return updated_count

    def _update_from_db_data(self, pool_entry: AgentPoolEntry, db_data: Dict[str, Any]):
        """Update pool entry with database data."""
        if "health_status" in db_data:
            pool_entry.health_status = HealthStatus(db_data["health_status"])

        if "last_heartbeat" in db_data:
            pool_entry.last_heartbeat = db_data["last_heartbeat"]

        if "current_load" in db_data:
            pool_entry.current_load = db_data["current_load"]

        if "performance_metrics" in db_data:
            # Update performance metrics
            metrics_data = db_data["performance_metrics"]
            if isinstance(metrics_data, dict):
                for capability_name, metrics in metrics_data.items():
                    if capability_name not in pool_entry.performance_metrics:
                        pool_entry.performance_metrics[capability_name] = PerformanceMetrics()
                    # Update metrics fields here if needed

    def _create_from_db_data(self, db_data: Dict[str, Any]) -> Optional[AgentPoolEntry]:
        """Create pool entry from database data."""
        try:
            return AgentPoolEntry(
                agent_id=db_data["agent_id"],
                agent_type=db_data.get("agent_type", "unknown"),
                agent_name=db_data.get("agent_id", "Unknown Agent"),
                description=f"Agent {db_data['agent_id']}",
                available_tools=db_data.get("available_tools", []),
                supported_workflows=db_data.get("supported_workflows", []),
                specializations=db_data.get("specializations", []),
                max_concurrent_executions=db_data.get("max_concurrent", 1),
                current_load=db_data.get("current_load", 0),
                health_status=HealthStatus(db_data.get("health_status", "unknown")),
                last_heartbeat=db_data.get("last_heartbeat", datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Failed to create pool entry from DB data: {e}")
            return None

    def _passes_basic_filters(self, agent_entry: AgentPoolEntry, filter_criteria: CapabilityFilter) -> bool:
        """Check if agent passes basic filter criteria."""
        # Health status filter
        if filter_criteria.health_statuses and agent_entry.health_status not in filter_criteria.health_statuses:
            return False

        # Load filter
        if agent_entry.load_percentage > filter_criteria.max_current_load:
            return False

        # Capacity filter
        available_capacity = agent_entry.max_concurrent_executions - agent_entry.current_load
        if available_capacity < filter_criteria.min_available_capacity:
            return False

        # Agent type filter
        if filter_criteria.agent_types and agent_entry.agent_type not in filter_criteria.agent_types:
            return False

        # Environment filter
        if filter_criteria.environments and agent_entry.environment not in filter_criteria.environments:
            return False

        # Region filter
        if filter_criteria.regions and agent_entry.region not in filter_criteria.regions:
            return False

        # Exclude filter
        if agent_entry.agent_id in filter_criteria.exclude_agents:
            return False

        return True

    async def _calculate_match_score(
        self,
        agent_entry: AgentPoolEntry,
        filter_criteria: CapabilityFilter
    ) -> CapabilityMatchResult:
        """Calculate detailed match score for an agent."""

        # Initialize result
        result = CapabilityMatchResult(
            agent_id=agent_entry.agent_id,
            match_score=0.0
        )

        # Calculate capability score
        capability_score = 0.0
        matched_capabilities = []

        if filter_criteria.capability_types:
            for cap_type in filter_criteria.capability_types:
                for capability in agent_entry.capabilities:
                    if capability.capability_type == cap_type:
                        matched_capabilities.append(capability.name)
                        capability_score += 1.0
            capability_score /= len(filter_criteria.capability_types)
        else:
            capability_score = 1.0

        # Calculate tool score
        tool_score = 1.0
        if filter_criteria.required_tools:
            available_tools = set(agent_entry.available_tools)
            required_tools = set(filter_criteria.required_tools)
            missing_tools = required_tools - available_tools

            if missing_tools:
                result.missing_requirements.extend(f"tool:{tool}" for tool in missing_tools)
                tool_score = len(required_tools - missing_tools) / len(required_tools)
            else:
                tool_score = 1.0

        # Calculate workflow score
        workflow_score = 1.0
        if filter_criteria.workflow_types:
            supported_count = sum(
                1 for wf in filter_criteria.workflow_types
                if agent_entry.supports_workflow(wf)
            )
            workflow_score = supported_count / len(filter_criteria.workflow_types)

        # Calculate load score (inverse of load percentage)
        load_score = max(0.0, 1.0 - (agent_entry.load_percentage / 100.0))

        # Calculate health score
        health_scores = {
            HealthStatus.HEALTHY: 1.0,
            HealthStatus.WARNING: 0.7,
            HealthStatus.CRITICAL: 0.3,
            HealthStatus.OFFLINE: 0.0,
            HealthStatus.UNKNOWN: 0.5
        }
        health_score = health_scores.get(agent_entry.health_status, 0.0)

        # Calculate performance score based on metrics
        performance_score = 0.8  # Default assumption
        if agent_entry.performance_metrics:
            total_success_rate = 0.0
            metric_count = 0
            for metrics in agent_entry.performance_metrics.values():
                total_success_rate += metrics.success_rate
                metric_count += 1
            if metric_count > 0:
                performance_score = total_success_rate / metric_count

        # Calculate availability score
        availability_score = (load_score + health_score) / 2

        # Apply preference boost
        preference_boost = 0.0
        if agent_entry.agent_id in filter_criteria.prefer_agents:
            preference_boost = 0.1

        # Calculate overall match score
        weights = {
            "capability": 0.3,
            "tool": 0.25,
            "workflow": 0.15,
            "performance": 0.15,
            "availability": 0.15
        }

        match_score = (
            weights["capability"] * capability_score +
            weights["tool"] * tool_score +
            weights["workflow"] * workflow_score +
            weights["performance"] * performance_score +
            weights["availability"] * availability_score +
            preference_boost
        )

        # Populate result
        result.match_score = min(match_score, 1.0)
        result.matched_capabilities = matched_capabilities
        result.capability_score = capability_score
        result.tool_score = tool_score
        result.workflow_score = workflow_score
        result.load_score = load_score
        result.health_score = health_score
        result.performance_score = performance_score
        result.availability_score = availability_score

        # Estimate execution time and cost
        if matched_capabilities and agent_entry.capabilities:
            relevant_caps = [
                cap for cap in agent_entry.capabilities
                if cap.name in matched_capabilities
            ]
            if relevant_caps:
                result.estimated_execution_time = max(cap.typical_execution_time for cap in relevant_caps)
                result.estimated_cost = agent_entry.cost_per_execution

        # Calculate confidence
        result.confidence_level = min(
            capability_score * tool_score * workflow_score * health_score,
            1.0
        )

        return result


# Global instance
_discovery_service: Optional[AgentPoolDiscoveryService] = None


async def get_discovery_service() -> AgentPoolDiscoveryService:
    """Get or create the global agent pool discovery service."""
    global _discovery_service

    if _discovery_service is None:
        _discovery_service = AgentPoolDiscoveryService()
        await _discovery_service.initialize()

    return _discovery_service


async def discover_agents_for_playbook(
    required_capabilities: List[str] = None,
    required_tools: List[str] = None,
    workflow_types: List[str] = None,
    max_results: int = 5
) -> List[CapabilityMatchResult]:
    """
    Convenience function to discover agents for playbook execution.

    Args:
        required_capabilities: List of required capability types
        required_tools: List of required MCP tools
        workflow_types: List of required workflow types
        max_results: Maximum number of results

    Returns:
        List of capability match results
    """
    service = await get_discovery_service()

    filter_criteria = CapabilityFilter(
        step_types=required_capabilities or [],
        required_tools=required_tools or [],
        workflow_types=workflow_types or [],
        health_statuses=[HealthStatus.HEALTHY, HealthStatus.WARNING]
    )

    return await service.find_capable_agents(filter_criteria, max_results)
