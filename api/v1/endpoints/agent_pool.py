"""
Agent Pool API Endpoints for Agentical Playbook System

This module provides FastAPI endpoints for agent pool discovery, capability
matching, and agent management for the playbook execution system.

Features:
- Agent pool discovery and listing
- Advanced capability matching with multiple algorithms
- Agent health monitoring and heartbeat management
- Performance metrics and statistics
- Real-time agent status updates
- Integration with playbook execution requirements
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, Body, Path
from pydantic import BaseModel, Field, validator
import logfire

from agentical.agents.pool_discovery import AgentPoolDiscoveryService, get_discovery_service
from agentical.agents.playbook_capabilities import (
    AgentPoolEntry, PlaybookCapability, CapabilityFilter, CapabilityMatchResult,
    HealthStatus, PerformanceMetrics, PlaybookCapabilityType, CapabilityComplexity
)
from agentical.agents.capability_matcher import (
    AdvancedCapabilityMatcher, MatchingContext, MatchingAlgorithm,
    OptimizationObjective, get_capability_matcher, find_best_agent_matches
)
from agentical.core.exceptions import AgenticalError, AgentNotFoundError

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agent-pool", tags=["agent-pool"])


# Request/Response Models

class AgentPoolQueryRequest(BaseModel):
    """Request model for agent pool queries."""

    capability_types: List[PlaybookCapabilityType] = Field(default_factory=list, description="Required capability types")
    step_types: List[str] = Field(default_factory=list, description="Required step types")
    required_tools: List[str] = Field(default_factory=list, description="Required MCP tools")
    workflow_types: List[str] = Field(default_factory=list, description="Required workflow types")

    # Performance filters
    max_execution_time: Optional[float] = Field(None, description="Maximum execution time requirement")
    min_success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum success rate requirement")
    max_error_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Maximum error rate tolerance")

    # Capacity filters
    min_available_capacity: int = Field(default=1, ge=1, description="Minimum available execution slots")
    max_current_load: float = Field(default=100.0, ge=0.0, le=100.0, description="Maximum current load percentage")
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


class MatchingContextRequest(BaseModel):
    """Request model for matching context."""

    playbook_id: Optional[str] = Field(None, description="Playbook identifier")
    step_count: int = Field(default=1, ge=1, description="Number of steps")
    estimated_duration: float = Field(default=300.0, gt=0, description="Estimated duration in seconds")
    priority: int = Field(default=5, ge=1, le=10, description="Priority level (1-10)")
    deadline: Optional[datetime] = Field(None, description="Execution deadline")
    budget_limit: Optional[float] = Field(None, description="Budget limit")
    prefer_reliable: bool = Field(default=True, description="Prefer reliable agents")
    allow_parallel: bool = Field(default=True, description="Allow parallel execution")
    environment: str = Field(default="production", description="Target environment")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")


class AgentPoolResponse(BaseModel):
    """Response model for agent pool information."""

    agents: List[AgentPoolEntry]
    total_count: int
    available_count: int
    healthy_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CapabilityMatchResponse(BaseModel):
    """Response model for capability matching results."""

    matches: List[CapabilityMatchResult]
    total_candidates: int
    algorithm_used: MatchingAlgorithm
    execution_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentHeartbeatRequest(BaseModel):
    """Request model for agent heartbeat updates."""

    agent_id: str = Field(..., description="Agent identifier")
    health_status: HealthStatus = Field(default=HealthStatus.HEALTHY, description="Current health status")
    current_load: int = Field(default=0, ge=0, description="Current execution load")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")


class AgentRegistrationRequest(BaseModel):
    """Request model for agent registration."""

    agent_pool_entry: AgentPoolEntry


class PoolStatisticsResponse(BaseModel):
    """Response model for pool statistics."""

    timestamp: datetime
    total_agents: int
    available_agents: int
    healthy_agents: int
    agents_by_type: Dict[str, int]
    agents_by_health: Dict[str, int]
    total_capacity: int
    current_load: int
    average_load_percentage: float
    discovery_metrics: Dict[str, Any]


# Dependency functions

async def get_pool_service() -> AgentPoolDiscoveryService:
    """Dependency to get the agent pool discovery service."""
    try:
        return await get_discovery_service()
    except Exception as e:
        logger.error(f"Failed to get pool discovery service: {e}")
        raise HTTPException(status_code=500, detail="Agent pool service unavailable")


async def get_matcher_service() -> AdvancedCapabilityMatcher:
    """Dependency to get the capability matcher service."""
    try:
        return get_capability_matcher()
    except Exception as e:
        logger.error(f"Failed to get capability matcher: {e}")
        raise HTTPException(status_code=500, detail="Capability matcher service unavailable")


# API Endpoints

@router.get("/", response_model=AgentPoolResponse)
async def get_agent_pool(
    include_offline: bool = Query(default=False, description="Include offline agents"),
    max_load_percentage: float = Query(default=80.0, ge=0.0, le=100.0, description="Maximum load percentage"),
    health_filter: Optional[str] = Query(default=None, description="Health status filter (healthy,warning,critical)"),
    pool_service: AgentPoolDiscoveryService = Depends(get_pool_service)
):
    """
    Get the current agent pool with optional filtering.

    Returns all agents in the pool with their current status, capabilities,
    and performance metrics.
    """
    with logfire.span("Get agent pool", include_offline=include_offline):
        try:
            # Parse health filter
            health_statuses = None
            if health_filter:
                status_names = [s.strip().upper() for s in health_filter.split(',')]
                health_statuses = [HealthStatus(name.lower()) for name in status_names if name]

            # Get available agents
            if include_offline:
                await pool_service.discover_agents(force_refresh=True)
                agents = list(pool_service.agent_pool.values())
            else:
                agents = await pool_service.get_available_agents(
                    health_filter=health_statuses,
                    max_load_percentage=max_load_percentage
                )

            # Calculate counts
            available_count = sum(1 for agent in agents if agent.is_available)
            healthy_count = sum(1 for agent in agents if agent.health_status == HealthStatus.HEALTHY)

            return AgentPoolResponse(
                agents=agents,
                total_count=len(agents),
                available_count=available_count,
                healthy_count=healthy_count
            )

        except Exception as e:
            logfire.error("Failed to get agent pool", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to retrieve agent pool: {str(e)}")


@router.get("/{agent_id}", response_model=AgentPoolEntry)
async def get_agent_details(
    agent_id: str = Path(..., description="Agent identifier"),
    pool_service: AgentPoolDiscoveryService = Depends(get_pool_service)
):
    """
    Get detailed information about a specific agent.

    Returns comprehensive agent information including capabilities,
    performance metrics, and current status.
    """
    with logfire.span("Get agent details", agent_id=agent_id):
        try:
            agent = await pool_service.get_agent_by_id(agent_id)

            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

            return agent

        except HTTPException:
            raise
        except Exception as e:
            logfire.error("Failed to get agent details", agent_id=agent_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to retrieve agent details: {str(e)}")


@router.post("/discover", response_model=AgentPoolResponse)
async def discover_agents(
    force_refresh: bool = Body(default=False, description="Force refresh of agent pool"),
    pool_service: AgentPoolDiscoveryService = Depends(get_pool_service)
):
    """
    Trigger agent discovery and return updated pool.

    Forces a refresh of the agent pool by querying all available
    agent sources and updating capability information.
    """
    with logfire.span("Discover agents", force_refresh=force_refresh):
        try:
            success = await pool_service.discover_agents(force_refresh=force_refresh)

            if not success:
                raise HTTPException(status_code=500, detail="Agent discovery failed")

            agents = list(pool_service.agent_pool.values())
            available_count = sum(1 for agent in agents if agent.is_available)
            healthy_count = sum(1 for agent in agents if agent.health_status == HealthStatus.HEALTHY)

            return AgentPoolResponse(
                agents=agents,
                total_count=len(agents),
                available_count=available_count,
                healthy_count=healthy_count
            )

        except HTTPException:
            raise
        except Exception as e:
            logfire.error("Failed to discover agents", error=str(e))
            raise HTTPException(status_code=500, detail=f"Agent discovery failed: {str(e)}")


@router.post("/match", response_model=CapabilityMatchResponse)
async def match_capabilities(
    query: AgentPoolQueryRequest,
    context: Optional[MatchingContextRequest] = None,
    algorithm: MatchingAlgorithm = Query(default=MatchingAlgorithm.WEIGHTED_SCORE, description="Matching algorithm"),
    max_results: int = Query(default=10, ge=1, le=50, description="Maximum results to return"),
    pool_service: AgentPoolDiscoveryService = Depends(get_pool_service),
    matcher_service: AdvancedCapabilityMatcher = Depends(get_matcher_service)
):
    """
    Find agents that match specific capability requirements.

    Uses advanced matching algorithms to find the best agents for
    a given set of requirements and context.
    """
    with logfire.span("Match capabilities", algorithm=algorithm.value):
        start_time = datetime.utcnow()

        try:
            # Convert request models to internal models
            capability_filter = CapabilityFilter(
                capability_types=query.capability_types,
                step_types=query.step_types,
                required_tools=query.required_tools,
                workflow_types=query.workflow_types,
                max_execution_time=query.max_execution_time,
                min_success_rate=query.min_success_rate,
                max_error_rate=query.max_error_rate,
                min_available_capacity=query.min_available_capacity,
                max_current_load=query.max_current_load,
                health_statuses=query.health_statuses,
                environments=query.environments,
                regions=query.regions,
                agent_types=query.agent_types,
                exclude_agents=query.exclude_agents,
                prefer_agents=query.prefer_agents,
                max_cost_per_execution=query.max_cost_per_execution,
                tags=query.tags
            )

            matching_context = MatchingContext()
            if context:
                matching_context = MatchingContext(
                    playbook_id=context.playbook_id,
                    step_count=context.step_count,
                    estimated_duration=context.estimated_duration,
                    priority=context.priority,
                    deadline=context.deadline,
                    budget_limit=context.budget_limit,
                    prefer_reliable=context.prefer_reliable,
                    allow_parallel=context.allow_parallel,
                    environment=context.environment,
                    user_preferences=context.user_preferences
                )

            # Get available agents
            agents = list(pool_service.agent_pool.values())

            # Find matches
            matches = await matcher_service.find_best_matches(
                agents=agents,
                requirements=capability_filter,
                context=matching_context,
                algorithm=algorithm,
                max_results=max_results
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return CapabilityMatchResponse(
                matches=matches,
                total_candidates=len(agents),
                algorithm_used=algorithm,
                execution_time_ms=execution_time
            )

        except Exception as e:
            logfire.error("Failed to match capabilities", error=str(e))
            raise HTTPException(status_code=500, detail=f"Capability matching failed: {str(e)}")


@router.post("/heartbeat")
async def update_heartbeat(
    heartbeat: AgentHeartbeatRequest,
    pool_service: AgentPoolDiscoveryService = Depends(get_pool_service)
):
    """
    Update agent heartbeat and status information.

    Allows agents to report their current health, load, and
    performance metrics to maintain accurate pool state.
    """
    with logfire.span("Update agent heartbeat", agent_id=heartbeat.agent_id):
        try:
            # Update heartbeat
            success = await pool_service.update_agent_heartbeat(heartbeat.agent_id)

            if not success:
                raise HTTPException(status_code=404, detail=f"Agent not found: {heartbeat.agent_id}")

            # Update load if provided
            await pool_service.update_agent_load(heartbeat.agent_id, heartbeat.current_load)

            # Update health status in pool
            if heartbeat.agent_id in pool_service.agent_pool:
                pool_service.agent_pool[heartbeat.agent_id].health_status = heartbeat.health_status
                pool_service.agent_pool[heartbeat.agent_id].updated_at = datetime.utcnow()

            return {"status": "success", "agent_id": heartbeat.agent_id, "timestamp": datetime.utcnow()}

        except HTTPException:
            raise
        except Exception as e:
            logfire.error("Failed to update heartbeat", agent_id=heartbeat.agent_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"Heartbeat update failed: {str(e)}")


@router.post("/register")
async def register_agent(
    registration: AgentRegistrationRequest,
    pool_service: AgentPoolDiscoveryService = Depends(get_pool_service)
):
    """
    Register a new agent in the pool.

    Adds a new agent to the pool with its capabilities and
    configuration information.
    """
    with logfire.span("Register agent", agent_id=registration.agent_pool_entry.agent_id):
        try:
            agent_entry = registration.agent_pool_entry

            # Add to pool
            pool_service.agent_pool[agent_entry.agent_id] = agent_entry

            # Register in database if schema manager available
            if pool_service.schema_manager:
                from agentical.db.schemas.playbook_schema_manager import convert_to_schema_capability
                schema_capability = convert_to_schema_capability(agent_entry)
                await pool_service.schema_manager.register_agent_capability(schema_capability)

            logfire.info("Agent registered successfully", agent_id=agent_entry.agent_id)

            return {
                "status": "success",
                "agent_id": agent_entry.agent_id,
                "message": "Agent registered successfully",
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logfire.error("Failed to register agent", error=str(e))
            raise HTTPException(status_code=500, detail=f"Agent registration failed: {str(e)}")


@router.get("/statistics", response_model=PoolStatisticsResponse)
async def get_pool_statistics(
    pool_service: AgentPoolDiscoveryService = Depends(get_pool_service)
):
    """
    Get comprehensive statistics about the agent pool.

    Returns detailed metrics about agent distribution, health,
    capacity utilization, and performance.
    """
    with logfire.span("Get pool statistics"):
        try:
            stats = await pool_service.get_pool_statistics()

            return PoolStatisticsResponse(**stats)

        except Exception as e:
            logfire.error("Failed to get pool statistics", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


@router.delete("/{agent_id}")
async def remove_agent(
    agent_id: str = Path(..., description="Agent identifier"),
    pool_service: AgentPoolDiscoveryService = Depends(get_pool_service)
):
    """
    Remove an agent from the pool.

    Removes an agent from the active pool, typically used when
    an agent is being decommissioned or is permanently offline.
    """
    with logfire.span("Remove agent", agent_id=agent_id):
        try:
            if agent_id not in pool_service.agent_pool:
                raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

            # Remove from pool
            del pool_service.agent_pool[agent_id]

            logfire.info("Agent removed from pool", agent_id=agent_id)

            return {
                "status": "success",
                "agent_id": agent_id,
                "message": "Agent removed successfully",
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            raise
        except Exception as e:
            logfire.error("Failed to remove agent", agent_id=agent_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"Agent removal failed: {str(e)}")


@router.post("/algorithms/test")
async def test_matching_algorithms(
    query: AgentPoolQueryRequest,
    context: Optional[MatchingContextRequest] = None,
    pool_service: AgentPoolDiscoveryService = Depends(get_pool_service),
    matcher_service: AdvancedCapabilityMatcher = Depends(get_matcher_service)
):
    """
    Test all matching algorithms and compare results.

    Useful for evaluating different matching approaches and
    understanding how algorithms perform for specific requirements.
    """
    with logfire.span("Test matching algorithms"):
        try:
            # Convert request models
            capability_filter = CapabilityFilter(
                capability_types=query.capability_types,
                step_types=query.step_types,
                required_tools=query.required_tools,
                workflow_types=query.workflow_types,
                health_statuses=query.health_statuses
            )

            matching_context = MatchingContext()
            if context:
                matching_context = MatchingContext(
                    step_count=context.step_count,
                    estimated_duration=context.estimated_duration,
                    priority=context.priority
                )

            agents = list(pool_service.agent_pool.values())
            results = {}

            # Test each algorithm
            for algorithm in MatchingAlgorithm:
                start_time = datetime.utcnow()

                matches = await matcher_service.find_best_matches(
                    agents=agents,
                    requirements=capability_filter,
                    context=matching_context,
                    algorithm=algorithm,
                    max_results=5
                )

                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                results[algorithm.value] = {
                    "matches": matches,
                    "execution_time_ms": execution_time,
                    "match_count": len(matches),
                    "top_score": matches[0].match_score if matches else 0.0
                }

            return {
                "algorithms_tested": len(results),
                "total_candidates": len(agents),
                "results": results,
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logfire.error("Failed to test matching algorithms", error=str(e))
            raise HTTPException(status_code=500, detail=f"Algorithm testing failed: {str(e)}")


# Health check endpoint
@router.get("/health")
async def pool_health_check():
    """
    Health check endpoint for the agent pool service.

    Returns the current health status of the agent pool
    discovery service and its dependencies.
    """
    try:
        pool_service = await get_discovery_service()
        matcher_service = get_capability_matcher()

        # Basic service checks
        pool_healthy = len(pool_service.agent_pool) >= 0  # Service is responsive
        matcher_healthy = matcher_service is not None

        # Get quick statistics
        total_agents = len(pool_service.agent_pool)
        healthy_agents = sum(
            1 for agent in pool_service.agent_pool.values()
            if agent.health_status == HealthStatus.HEALTHY
        )

        overall_health = "healthy" if pool_healthy and matcher_healthy else "degraded"

        return {
            "status": overall_health,
            "timestamp": datetime.utcnow(),
            "services": {
                "pool_discovery": "healthy" if pool_healthy else "unhealthy",
                "capability_matcher": "healthy" if matcher_healthy else "unhealthy"
            },
            "statistics": {
                "total_agents": total_agents,
                "healthy_agents": healthy_agents,
                "last_discovery": pool_service.last_discovery_time
            }
        }

    except Exception as e:
        logger.error(f"Pool health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }
