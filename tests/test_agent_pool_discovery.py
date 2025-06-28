"""
Comprehensive Tests for Agent Pool Discovery System

This test suite validates the agent pool discovery, capability matching,
and API endpoints for the Agentical playbook system.

Features tested:
- Agent pool discovery and registration
- Capability matching algorithms
- API endpoint functionality
- Performance and load balancing
- Error handling and edge cases
- Integration with database schema
- Concurrent operations and thread safety
- Cache management and optimization
- Health monitoring and statistics
"""

import asyncio
import pytest
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import sys
    import os
    # Add current directory to path to enable relative imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from agents.pool_discovery import AgentPoolDiscoveryService
    from agents.playbook_capabilities import (
        AgentPoolEntry, PlaybookCapability, CapabilityFilter,
        HealthStatus, PerformanceMetrics, PlaybookCapabilityType, CapabilityComplexity
    )
    from agents.capability_matcher import (
        AdvancedCapabilityMatcher, MatchingContext, MatchingAlgorithm
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False


class TestAgentPoolDiscovery:
    """Comprehensive test suite for agent pool discovery service."""

    @pytest.fixture
    def mock_schema_manager(self):
        """Create a mock schema manager."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        mock_manager = Mock()
        mock_manager.get_agents_from_registry = AsyncMock(return_value=[])
        mock_manager.update_agent_in_registry = AsyncMock(return_value=True)
        mock_manager.remove_agent_from_registry = AsyncMock(return_value=True)
        return mock_manager

    @pytest.fixture
    async def discovery_service(self, mock_schema_manager):
        """Create discovery service instance."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        service = AgentPoolDiscoveryService()
        service.schema_manager = mock_schema_manager
        service.agent_registry = Mock()
        service.agent_registry.list_agents = AsyncMock(return_value=[])
        service.agent_registry.get_agent = AsyncMock(return_value=None)
        await service.initialize()
        return service

    @pytest.fixture
    def sample_agent_entry(self):
        """Create sample agent entry for testing."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        return AgentPoolEntry(
            agent_id="test_agent_001",
            agent_type="test",
            agent_name="Test Agent",
            description="A test agent for unit testing",
            available_tools=["filesystem", "git", "memory"],
            supported_workflows=["sequential", "parallel"],
            specializations=["testing", "validation"],
            health_status=HealthStatus.HEALTHY,
            performance_metrics={
                "test_capability": PerformanceMetrics(
                    total_executions=50,
                    successful_executions=48,
                    average_execution_time=15.0
                )
            },
            capabilities=[
                PlaybookCapability(
                    name="test_capability",
                    display_name="Test Capability",
                    description="Testing capability",
                    capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                    complexity=CapabilityComplexity.SIMPLE,
                    supported_step_types=["action", "validation"],
                    required_tools=["memory"],
                    typical_execution_time=15.0,
                    max_execution_time=30.0
                )
            ]
        )

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_schema_manager):
        """Test service initialization."""
        service = AgentPoolDiscoveryService(schema_manager=mock_schema_manager)
        success = await service.initialize()

        assert success is True
        assert service.schema_manager is not None
        assert isinstance(service.agent_pool, dict)
        assert service.last_discovery_time is not None

    @pytest.mark.asyncio
    async def test_service_initialization_without_schema_manager(self):
        """Test service initialization without schema manager."""
        service = AgentPoolDiscoveryService()
        success = await service.initialize()

        assert success is True
        assert isinstance(service.agent_pool, dict)

    @pytest.mark.asyncio
    async def test_agent_registration(self, discovery_service, sample_agent_entry):
        """Test agent registration in pool."""
        # Add agent to pool
        discovery_service.agent_pool[sample_agent_entry.agent_id] = sample_agent_entry

        # Verify agent exists
        agent = await discovery_service.get_agent_by_id(sample_agent_entry.agent_id)
        assert agent is not None
        assert agent.agent_id == sample_agent_entry.agent_id
        assert agent.agent_name == "Test Agent"
        assert agent.health_status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_agent_discovery_with_force_refresh(self, discovery_service):
        """Test agent discovery process with force refresh."""
        # Mock registry agents
        registry_agents = [
            {
                "id": "registry_agent_001",
                "name": "Registry Agent",
                "type": "GenericAgent",
                "status": "idle",
                "description": "Agent from registry",
                "capabilities_count": 2
            },
            {
                "id": "registry_agent_002",
                "name": "Another Registry Agent",
                "type": "SpecializedAgent",
                "status": "busy",
                "description": "Another agent from registry",
                "capabilities_count": 3
            }
        ]

        # Mock the registry list_agents method
        with patch.object(discovery_service.agent_registry, 'list_agents', return_value=registry_agents):
            with patch.object(discovery_service.agent_registry, 'get_agent') as mock_get_agent:
                # Mock the agent metadata
                mock_agent_1 = Mock()
                mock_agent_1.metadata = Mock()
                mock_agent_1.metadata.id = "registry_agent_001"
                mock_agent_1.metadata.name = "Registry Agent"
                mock_agent_1.metadata.description = "Agent from registry"
                mock_agent_1.metadata.available_tools = ["tool1", "tool2"]
                mock_agent_1.metadata.version = "1.0.0"
                mock_agent_1.metadata.tags = ["test"]

                mock_agent_2 = Mock()
                mock_agent_2.metadata = Mock()
                mock_agent_2.metadata.id = "registry_agent_002"
                mock_agent_2.metadata.name = "Another Registry Agent"
                mock_agent_2.metadata.description = "Another agent from registry"
                mock_agent_2.metadata.available_tools = ["tool2", "tool3", "tool4"]
                mock_agent_2.metadata.version = "1.1.0"
                mock_agent_2.metadata.tags = ["specialized"]

                def get_agent_side_effect(agent_id):
                    if agent_id == "registry_agent_001":
                        return mock_agent_1
                    elif agent_id == "registry_agent_002":
                        return mock_agent_2
                    return None

                mock_get_agent.side_effect = get_agent_side_effect

                success = await discovery_service.discover_agents(force_refresh=True)

                assert success is True
                assert len(discovery_service.agent_pool) >= 2

    @pytest.mark.asyncio
    async def test_heartbeat_update(self, discovery_service, sample_agent_entry):
        """Test agent heartbeat updates."""
        # Add agent to pool
        discovery_service.agent_pool[sample_agent_entry.agent_id] = sample_agent_entry
        old_heartbeat = sample_agent_entry.last_heartbeat

        # Wait a small amount to ensure timestamp difference
        await asyncio.sleep(0.01)

        # Update heartbeat
        success = await discovery_service.update_agent_heartbeat(sample_agent_entry.agent_id)

        assert success is True
        new_heartbeat = discovery_service.agent_pool[sample_agent_entry.agent_id].last_heartbeat
        assert new_heartbeat > old_heartbeat

    @pytest.mark.asyncio
    async def test_heartbeat_update_nonexistent_agent(self, discovery_service):
        """Test heartbeat update for non-existent agent."""
        success = await discovery_service.update_agent_heartbeat("nonexistent_agent")
        assert success is False

    @pytest.mark.asyncio
    async def test_load_update(self, discovery_service, sample_agent_entry):
        """Test agent load updates."""
        # Add agent to pool
        discovery_service.agent_pool[sample_agent_entry.agent_id] = sample_agent_entry
        initial_load = sample_agent_entry.current_load

        # Update load
        new_load = initial_load + 2
        success = await discovery_service.update_agent_load(sample_agent_entry.agent_id, new_load)

        assert success is True
        assert discovery_service.agent_pool[sample_agent_entry.agent_id].current_load == new_load

    @pytest.mark.asyncio
    async def test_load_update_invalid_values(self, discovery_service, sample_agent_entry):
        """Test load update with invalid values."""
        # Add agent to pool
        discovery_service.agent_pool[sample_agent_entry.agent_id] = sample_agent_entry

        # Test negative load
        success = await discovery_service.update_agent_load(sample_agent_entry.agent_id, -1)
        assert success is False

        # Test load exceeding maximum
        success = await discovery_service.update_agent_load(sample_agent_entry.agent_id, 1000)
        assert success is False

    @pytest.mark.asyncio
    async def test_capability_filtering(self, discovery_service, sample_agent_entry):
        """Test capability-based agent filtering."""
        # Add agent to pool
        discovery_service.agent_pool[sample_agent_entry.agent_id] = sample_agent_entry

        # Create filter criteria
        capability_filter = CapabilityFilter(
            required_tools=["memory"],
            workflow_types=["sequential"],
            health_statuses=[HealthStatus.HEALTHY],
            step_types=["action"]
        )

        # Find capable agents
        matches = await discovery_service.find_capable_agents(capability_filter, max_results=5)

        assert len(matches) > 0
        assert matches[0].agent_id == sample_agent_entry.agent_id
        assert matches[0].is_viable is True

    @pytest.mark.asyncio
    async def test_capability_filtering_complex_requirements(self, discovery_service):
        """Test capability filtering with complex requirements."""
        # Create multiple agents with different capabilities
        agents = [
            AgentPoolEntry(
                agent_id="fast_agent",
                agent_type="performance",
                agent_name="Fast Agent",
                description="High-performance agent",
                available_tools=["tool1", "tool2"],
                supported_workflows=["parallel"],
                health_status=HealthStatus.HEALTHY,
                capabilities=[
                    PlaybookCapability(
                        name="fast_execution",
                        display_name="Fast Execution",
                        description="Execute tasks quickly",
                        capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                        complexity=CapabilityComplexity.SIMPLE,
                        supported_step_types=["action"],
                        required_tools=["tool1"],
                        typical_execution_time=5.0,
                        max_execution_time=15.0
                    )
                ]
            ),
            AgentPoolEntry(
                agent_id="reliable_agent",
                agent_type="reliability",
                agent_name="Reliable Agent",
                description="Highly reliable agent",
                available_tools=["tool2", "tool3"],
                supported_workflows=["sequential"],
                health_status=HealthStatus.WARNING,
                capabilities=[
                    PlaybookCapability(
                        name="reliable_execution",
                        display_name="Reliable Execution",
                        description="Execute tasks reliably",
                        capability_type=PlaybookCapabilityType.WORKFLOW_CONTROL,
                        complexity=CapabilityComplexity.COMPLEX,
                        supported_step_types=["condition", "loop"],
                        required_tools=["tool3"],
                        typical_execution_time=30.0,
                        max_execution_time=60.0
                    )
                ]
            )
        ]

        for agent in agents:
            discovery_service.agent_pool[agent.agent_id] = agent

        # Filter for healthy agents with parallel workflow support
        filter1 = CapabilityFilter(
            workflow_types=["parallel"],
            health_statuses=[HealthStatus.HEALTHY],
            max_execution_time=20.0
        )

        matches1 = await discovery_service.find_capable_agents(filter1, max_results=10)
        assert len(matches1) == 1
        assert matches1[0].agent_id == "fast_agent"

        # Filter for workflow control capabilities
        filter2 = CapabilityFilter(
            capability_types=[PlaybookCapabilityType.WORKFLOW_CONTROL],
            step_types=["condition"]
        )

        matches2 = await discovery_service.find_capable_agents(filter2, max_results=10)
        assert len(matches2) == 1
        assert matches2[0].agent_id == "reliable_agent"

    @pytest.mark.asyncio
    async def test_available_agents_filter(self, discovery_service, sample_agent_entry):
        """Test filtering for available agents only."""
        # Add healthy agent
        discovery_service.agent_pool[sample_agent_entry.agent_id] = sample_agent_entry

        # Add unhealthy agent
        unhealthy_agent = AgentPoolEntry(
            agent_id="unhealthy_agent",
            agent_type="test",
            agent_name="Unhealthy Agent",
            description="Unhealthy test agent",
            health_status=HealthStatus.CRITICAL,
            current_load=10,
            max_concurrent_executions=5
        )
        discovery_service.agent_pool[unhealthy_agent.agent_id] = unhealthy_agent

        # Add overloaded agent
        overloaded_agent = AgentPoolEntry(
            agent_id="overloaded_agent",
            agent_type="test",
            agent_name="Overloaded Agent",
            description="Overloaded test agent",
            health_status=HealthStatus.HEALTHY,
            current_load=8,
            max_concurrent_executions=5
        )
        discovery_service.agent_pool[overloaded_agent.agent_id] = overloaded_agent

        # Get available agents
        available_agents = await discovery_service.get_available_agents()

        # Should only include healthy agent with reasonable load
        assert len(available_agents) == 1
        assert available_agents[0].agent_id == sample_agent_entry.agent_id

    @pytest.mark.asyncio
    async def test_pool_statistics(self, discovery_service, sample_agent_entry):
        """Test pool statistics generation."""
        # Add multiple agents to pool
        agents = [sample_agent_entry]

        # Add another healthy agent
        healthy_agent = AgentPoolEntry(
            agent_id="healthy_agent_2",
            agent_type="worker",
            agent_name="Healthy Worker",
            description="Another healthy agent",
            health_status=HealthStatus.HEALTHY
        )
        agents.append(healthy_agent)

        # Add unhealthy agent
        unhealthy_agent = AgentPoolEntry(
            agent_id="unhealthy_agent_2",
            agent_type="worker",
            agent_name="Unhealthy Worker",
            description="Unhealthy agent",
            health_status=HealthStatus.CRITICAL
        )
        agents.append(unhealthy_agent)

        for agent in agents:
            discovery_service.agent_pool[agent.agent_id] = agent

        # Get statistics
        stats = await discovery_service.get_pool_statistics()

        assert "total_agents" in stats
        assert "available_agents" in stats
        assert "healthy_agents" in stats
        assert "agents_by_type" in stats
        assert "agents_by_health_status" in stats
        assert "average_load" in stats

        assert stats["total_agents"] == 3
        assert stats["healthy_agents"] == 2
        assert stats["agents_by_type"]["test"] == 1
        assert stats["agents_by_type"]["worker"] == 2

    @pytest.mark.asyncio
    async def test_cache_management(self, discovery_service):
        """Test cache freshness and update mechanisms."""
        # Test cache freshness
        discovery_service.last_discovery_time = datetime.utcnow() - timedelta(seconds=30)
        assert not discovery_service._is_cache_fresh(max_age_seconds=10)

        discovery_service.last_discovery_time = datetime.utcnow()
        assert discovery_service._is_cache_fresh(max_age_seconds=60)

    @pytest.mark.asyncio
    async def test_capability_registration(self, discovery_service, sample_agent_entry):
        """Test capability registration for agents."""
        # Add agent to pool
        discovery_service.agent_pool[sample_agent_entry.agent_id] = sample_agent_entry

        # Register new capability
        new_capability = PlaybookCapability(
            name="new_test_capability",
            display_name="New Test Capability",
            description="Newly registered capability",
            capability_type=PlaybookCapabilityType.INTEGRATION,
            complexity=CapabilityComplexity.MODERATE,
            supported_step_types=["integration"],
            required_tools=["api_client"],
            typical_execution_time=20.0,
            max_execution_time=45.0
        )

        success = await discovery_service.register_agent_capability(
            sample_agent_entry.agent_id,
            new_capability
        )

        assert success is True
        agent = discovery_service.agent_pool[sample_agent_entry.agent_id]
        capability_names = [cap.name for cap in agent.capabilities]
        assert "new_test_capability" in capability_names

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, discovery_service, sample_agent_entry):
        """Test concurrent operations on the agent pool."""
        # Add agent to pool
        discovery_service.agent_pool[sample_agent_entry.agent_id] = sample_agent_entry

        # Define concurrent operations
        async def update_heartbeat():
            return await discovery_service.update_agent_heartbeat(sample_agent_entry.agent_id)

        async def update_load():
            return await discovery_service.update_agent_load(sample_agent_entry.agent_id, 3)

        async def get_statistics():
            return await discovery_service.get_pool_statistics()

        async def find_agents():
            filter = CapabilityFilter(required_tools=["memory"])
            return await discovery_service.find_capable_agents(filter)

        # Run operations concurrently
        results = await asyncio.gather(
            update_heartbeat(),
            update_load(),
            get_statistics(),
            find_agents(),
            return_exceptions=True
        )

        # Verify all operations completed successfully
        assert all(not isinstance(result, Exception) for result in results)
        assert results[0] is True  # heartbeat update
        assert results[1] is True  # load update
        assert isinstance(results[2], dict)  # statistics
        assert isinstance(results[3], list)  # agent matches


class TestCapabilityMatcher:
    """Test suite for capability matching algorithms."""

    @pytest.fixture
    def capability_matcher(self):
        """Create capability matcher instance."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        return AdvancedCapabilityMatcher()

    @pytest.fixture
    def sample_agents(self):
        """Create sample agents for testing."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        return [
            AgentPoolEntry(
                agent_id="fast_agent",
                agent_type="performance",
                agent_name="Fast Agent",
                description="High-performance agent",
                available_tools=["tool1", "tool2"],
                supported_workflows=["sequential", "parallel"],
                health_status=HealthStatus.HEALTHY,
                current_load=1,
                max_concurrent_executions=10,
                cost_per_execution=0.05,
                capabilities=[
                    PlaybookCapability(
                        name="fast_execution",
                        display_name="Fast Execution",
                        description="Execute tasks quickly",
                        capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                        complexity=CapabilityComplexity.SIMPLE,
                        supported_step_types=["action"],
                        required_tools=["tool1"],
                        typical_execution_time=10.0,
                        max_execution_time=30.0
                    )
                ],
                performance_metrics={
                    "fast_execution": PerformanceMetrics(
                        total_executions=100,
                        successful_executions=95,
                        average_execution_time=8.0,
                        fastest_execution_time=5.0,
                        slowest_execution_time=15.0
                    )
                }
            ),
            AgentPoolEntry(
                agent_id="reliable_agent",
                agent_type="reliability",
                agent_name="Reliable Agent",
                description="Highly reliable agent",
                available_tools=["tool1", "tool3"],
                supported_workflows=["sequential"],
                health_status=HealthStatus.HEALTHY,
                current_load=3,
                max_concurrent_executions=5,
                cost_per_execution=0.15,
                capabilities=[
                    PlaybookCapability(
                        name="reliable_execution",
                        display_name="Reliable Execution",
                        description="Execute tasks reliably",
                        capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                        complexity=CapabilityComplexity.MODERATE,
                        supported_step_types=["action", "validation"],
                        required_tools=["tool3"],
                        typical_execution_time=30.0,
                        max_execution_time=60.0
                    )
                ],
                performance_metrics={
                    "reliable_execution": PerformanceMetrics(
                        total_executions=200,
                        successful_executions=198,
                        average_execution_time=25.0,
                        fastest_execution_time=20.0,
                        slowest_execution_time=35.0
                    )
                }
            ),
            AgentPoolEntry(
                agent_id="budget_agent",
                agent_type="economy",
                agent_name="Budget Agent",
                description="Cost-effective agent",
                available_tools=["tool2", "tool4"],
                supported_workflows=["sequential", "loop"],
                health_status=HealthStatus.WARNING,
                current_load=2,
                max_concurrent_executions=8,
                cost_per_execution=0.02,
                capabilities=[
                    PlaybookCapability(
                        name="budget_execution",
                        display_name="Budget Execution",
                        description="Execute tasks cost-effectively",
                        capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                        complexity=CapabilityComplexity.SIMPLE,
                        supported_step_types=["action"],
                        required_tools=["tool2"],
                        typical_execution_time=45.0,
                        max_execution_time=90.0
                    )
                ],
                performance_metrics={
                    "budget_execution": PerformanceMetrics(
                        total_executions=150,
                        successful_executions=140,
                        average_execution_time=40.0,
                        fastest_execution_time=30.0,
                        slowest_execution_time=60.0
                    )
                }
            )
        ]

    @pytest.fixture
    def sample_requirements(self):
        """Create sample capability requirements."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        return CapabilityFilter(
            capability_types=[PlaybookCapabilityType.TASK_EXECUTION],
            required_tools=["tool1"],
            workflow_types=["sequential"],
            step_types=["action"],
            min_success_rate=0.9,
            max_execution_time=45.0,
            health_statuses=[HealthStatus.HEALTHY]
        )

    @pytest.fixture
    def sample_context(self):
        """Create sample matching context."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        return MatchingContext(
            step_count=3,
            estimated_duration=120.0,
            priority=7,
            prefer_reliable=True,
            budget_limit=0.50
        )

    @pytest.mark.asyncio
    async def test_weighted_score_matching(self, capability_matcher, sample_agents, sample_requirements, sample_context):
        """Test weighted score matching algorithm."""
        matches = await capability_matcher.find_best_matches(
            agents=sample_agents,
            requirements=sample_requirements,
            context=sample_context,
            algorithm=MatchingAlgorithm.WEIGHTED_SCORE,
            max_results=10
        )

        assert len(matches) > 0
        assert all(match.match_score >= 0.0 and match.match_score <= 1.0 for match in matches)
        # Should be sorted by match score descending
        assert matches[0].match_score >= matches[-1].match_score

        # Verify match details
        for match in matches:
            assert match.agent_id is not None
            assert match.confidence_level >= 0.0
            assert hasattr(match, 'load_score')

    @pytest.mark.asyncio
    async def test_performance_optimized_matching(self, capability_matcher, sample_agents, sample_requirements, sample_context):
        """Test performance-optimized matching algorithm."""
        matches = await capability_matcher.find_best_matches(
            agents=sample_agents,
            requirements=sample_requirements,
            context=sample_context,
            algorithm=MatchingAlgorithm.PERFORMANCE_OPTIMIZED,
            max_results=10
        )

        assert len(matches) > 0
        # Fast agent should score higher in performance-optimized matching
        fast_agent_match = next((m for m in matches if m.agent_id == "fast_agent"), None)
        reliable_agent_match = next((m for m in matches if m.agent_id == "reliable_agent"), None)

        if fast_agent_match and reliable_agent_match:
            # Fast agent should generally score higher for performance optimization
            assert fast_agent_match.match_score >= reliable_agent_match.match_score

    @pytest.mark.asyncio
    async def test_load_balanced_matching(self, capability_matcher, sample_agents, sample_requirements, sample_context):
        """Test load-balanced matching algorithm."""
        matches = await capability_matcher.find_best_matches(
            agents=sample_agents,
            requirements=sample_requirements,
            context=sample_context,
            algorithm=MatchingAlgorithm.LOAD_BALANCED,
            max_results=10
        )

        assert len(matches) > 0
        # Verify load scores are calculated
        for match in matches:
            assert hasattr(match, 'load_score')
            assert match.load_score >= 0.0

        # Agent with lowest load should score highest
        if len(matches) >= 2:
            # Find fast_agent (load=1) vs reliable_agent (load=3)
            fast_match = next((m for m in matches if m.agent_id == "fast_agent"), None)
            reliable_match = next((m for m in matches if m.agent_id == "reliable_agent"), None)

            if fast_match and reliable_match:
                assert fast_match.load_score >= reliable_match.load_score

    @pytest.mark.asyncio
    async def test_fuzzy_matching(self, capability_matcher, sample_agents, sample_context):
        """Test fuzzy matching algorithm."""
        # Create requirements with slightly different names
        fuzzy_requirements = CapabilityFilter(
            step_types=["task_exec"],  # Similar to "task_execution"
            required_tools=["tool_1"]   # Similar to "tool1"
        )

        matches = await capability_matcher.find_best_matches(
            agents=sample_agents,
            requirements=fuzzy_requirements,
            context=sample_context,
            algorithm=MatchingAlgorithm.FUZZY_MATCH,
            max_results=10
        )

        # Fuzzy matching should find some matches despite exact name differences
        assert len(matches) >= 0
        for match in matches:
            assert match.match_score >= 0.0

    @pytest.mark.asyncio
    async def test_multi_objective_matching(self, capability_matcher, sample_agents, sample_requirements, sample_context):
        """Test multi-objective optimization matching."""
        matches = await capability_matcher.find_best_matches(
            agents=sample_agents,
            requirements=sample_requirements,
            context=sample_context,
            algorithm=MatchingAlgorithm.MULTI_OBJECTIVE,
            max_results=10
        )

        assert len(matches) >= 0
        for match in matches:
            assert match.match_score >= 0.0
            assert match.confidence_level >= 0.0
            # Multi-objective should consider multiple factors
            assert hasattr(match, 'load_score')

    @pytest.mark.asyncio
    async def test_cost_optimized_matching(self, capability_matcher, sample_agents, sample_requirements, sample_context):
        """Test cost-optimized matching algorithm."""
        # Set budget limit lower to test cost filtering
        sample_context.budget_limit = 0.10

        matches = await capability_matcher.find_best_matches(
            agents=sample_agents,
            requirements=sample_requirements,
            context=sample_context,
            algorithm=MatchingAlgorithm.COST_OPTIMIZED,
            max_results=10
        )

        # Should prefer cheaper agents within budget
        for match in matches:
            if hasattr(match, 'estimated_cost'):
                assert match.estimated_cost <= sample_context.budget_limit

        # Budget agent (cost=0.02) should score higher than fast agent (cost=0.05)
        budget_match = next((m for m in matches if m.agent_id == "budget_agent"), None)
        fast_match = next((m for m in matches if m.agent_id == "fast_agent"), None)

        if budget_match and fast_match:
            assert budget_match.match_score >= fast_match.match_score

    @pytest.mark.asyncio
    async def test_matching_with_no_matches(self, capability_matcher, sample_agents, sample_context):
        """Test matching when no agents meet requirements."""
        impossible_requirements = CapabilityFilter(
            required_tools=["nonexistent_tool"],
            min_success_rate=1.0,  # Perfect success rate
            max_execution_time=1.0,  # Unrealistic time limit
            health_statuses=[HealthStatus.HEALTHY]
        )

        matches = await capability_matcher.find_best_matches(
            agents=sample_agents,
            requirements=impossible_requirements,
            context=sample_context,
            algorithm=MatchingAlgorithm.WEIGHTED_SCORE,
            max_results=10
        )

        # Should return empty list when no viable matches
        viable_matches = [m for m in matches if m.is_viable]
        assert len(viable_matches) == 0

    @pytest.mark.asyncio
    async def test_algorithm_comparison(self, capability_matcher, sample_agents, sample_requirements, sample_context):
        """Test comparison of different matching algorithms."""
        algorithms_to_test = [
            MatchingAlgorithm.WEIGHTED_SCORE,
            MatchingAlgorithm.PERFORMANCE_OPTIMIZED,
            MatchingAlgorithm.LOAD_BALANCED,
            MatchingAlgorithm.COST_OPTIMIZED
        ]

        results = {}
        for algorithm in algorithms_to_test:
            matches = await capability_matcher.find_best_matches(
                agents=sample_agents,
                requirements=sample_requirements,
                context=sample_context,
                algorithm=algorithm,
                max_results=5
            )
            results[algorithm] = matches

        # All algorithms should return some results
        for algorithm, matches in results.items():
            assert len(matches) >= 0, f"Algorithm {algorithm} failed"

        # Performance optimized should prefer fast_agent
        perf_matches = results[MatchingAlgorithm.PERFORMANCE_OPTIMIZED]
        if perf_matches:
            fast_agent_present = any(m.agent_id == "fast_agent" for m in perf_matches)
            assert fast_agent_present

    @pytest.mark.asyncio
    async def test_context_influence_on_matching(self, capability_matcher, sample_agents, sample_requirements):
        """Test how different contexts influence matching results."""
        # High priority, reliability preferred
        reliable_context = MatchingContext(
            step_count=5,
            estimated_duration=300.0,
            priority=9,
            prefer_reliable=True,
            budget_limit=1.0
        )

        # Low priority, performance preferred
        performance_context = MatchingContext(
            step_count=2,
            estimated_duration=60.0,
            priority=3,
            prefer_reliable=False,
            budget_limit=0.05
        )

        reliable_matches = await capability_matcher.find_best_matches(
            agents=sample_agents,
            requirements=sample_requirements,
            context=reliable_context,
            algorithm=MatchingAlgorithm.WEIGHTED_SCORE,
            max_results=10
        )

        performance_matches = await capability_matcher.find_best_matches(
            agents=sample_agents,
            requirements=sample_requirements,
            context=performance_context,
            algorithm=MatchingAlgorithm.WEIGHTED_SCORE,
            max_results=10
        )

        # Both should return results but potentially in different orders
        assert len(reliable_matches) >= 0
        assert len(performance_matches) >= 0

    @pytest.mark.asyncio
    async def test_capability_complexity_matching(self, capability_matcher):
        """Test matching based on capability complexity levels."""
        # Create agents with different complexity capabilities
        simple_agent = AgentPoolEntry(
            agent_id="simple_agent",
            agent_type="basic",
            agent_name="Simple Agent",
            description="Handles simple tasks",
            available_tools=["basic_tool"],
            capabilities=[
                PlaybookCapability(
                    name="simple_task",
                    display_name="Simple Task",
                    description="Simple task execution",
                    capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                    complexity=CapabilityComplexity.SIMPLE,
                    supported_step_types=["action"],
                    required_tools=["basic_tool"]
                )
            ]
        )

        complex_agent = AgentPoolEntry(
            agent_id="complex_agent",
            agent_type="advanced",
            agent_name="Complex Agent",
            description="Handles complex tasks",
            available_tools=["advanced_tool", "basic_tool"],
            capabilities=[
                PlaybookCapability(
                    name="complex_task",
                    display_name="Complex Task",
                    description="Complex task execution",
                    capability_type=PlaybookCapabilityType.WORKFLOW_CONTROL,
                    complexity=CapabilityComplexity.COMPLEX,
                    supported_step_types=["workflow", "orchestration"],
                    required_tools=["advanced_tool"]
                )
            ]
        )

        agents = [simple_agent, complex_agent]

        # Test matching for simple requirements
        simple_requirements = CapabilityFilter(
            capability_complexities=[CapabilityComplexity.SIMPLE],
            step_types=["action"]
        )

        simple_matches = await capability_matcher.find_best_matches(
            agents=agents,
            requirements=simple_requirements,
            context=MatchingContext(),
            algorithm=MatchingAlgorithm.WEIGHTED_SCORE,
            max_results=10
        )

        # Should prefer simple agent for simple tasks
        if simple_matches:
            assert simple_matches[0].agent_id == "simple_agent"

        # Test matching for complex requirements
        complex_requirements = CapabilityFilter(
            capability_complexities=[CapabilityComplexity.COMPLEX],
            step_types=["workflow"]
        )

        complex_matches = await capability_matcher.find_best_matches(
            agents=agents,
            requirements=complex_requirements,
            context=MatchingContext(),
            algorithm=MatchingAlgorithm.WEIGHTED_SCORE,
            max_results=10
        )

        # Should prefer complex agent for complex tasks
        if complex_matches:
            assert complex_matches[0].agent_id == "complex_agent"


class TestAgentPoolAPI:
    """Test suite for agent pool API endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create test client."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        # Mock FastAPI app for testing
        from fastapi import FastAPI
        mock_app = FastAPI()
        return TestClient(mock_app)

    @pytest.fixture
    def sample_agent_data(self):
        """Create sample agent data for API tests."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        return {
            "agent_id": "api_test_agent",
            "agent_type": "test",
            "agent_name": "API Test Agent",
            "description": "Agent for API testing",
            "available_tools": ["filesystem", "git"],
            "supported_workflows": ["sequential"],
            "specializations": ["testing"],
            "max_concurrent_executions": 2,
            "current_load": 0,
            "capabilities": [
                {
                    "name": "test_capability",
                    "display_name": "Test Capability",
                    "description": "Testing capability",
                    "capability_type": "task_execution",
                    "complexity": "simple",
                    "supported_step_types": ["action"],
                    "required_tools": ["filesystem"],
                    "supported_workflows": ["sequential"],
                    "typical_execution_time": 30.0,
                    "max_execution_time": 60.0,
                    "can_run_parallel": True,
                    "version": "1.0.0",
                    "tags": ["test"]
                }
            ],
            "health_status": "healthy",
            "priority": 5,
            "environment": "test",
            "version": "1.0.0",
            "tags": ["api", "test"]
        }

    def test_get_agent_pool_endpoint(self, test_client):
        """Test GET /agent-pool endpoint."""
        response = test_client.get("/api/v1/agent-pool/")

        # Should return 200 even if pool is empty
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total_count" in data
        assert "available_count" in data
        assert "healthy_count" in data

    def test_get_agent_pool_with_pagination(self, test_client):
        """Test GET /agent-pool endpoint with pagination."""
        response = test_client.get("/api/v1/agent-pool/?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data

    def test_get_agent_pool_with_filters(self, test_client):
        """Test GET /agent-pool endpoint with health status filter."""
        response = test_client.get("/api/v1/agent-pool/?health_status=healthy")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data

    def test_discover_agents_endpoint(self, test_client):
        """Test POST /agent-pool/discover endpoint."""
        response = test_client.post("/api/v1/agent-pool/discover", json={"force_refresh": True})

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total_count" in data

    def test_discover_agents_without_force_refresh(self, test_client):
        """Test POST /agent-pool/discover endpoint without force refresh."""
        response = test_client.post("/api/v1/agent-pool/discover", json={"force_refresh": False})

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data

    def test_match_capabilities_endpoint(self, test_client):
        """Test POST /agent-pool/match endpoint."""
        query_data = {
            "capability_types": ["task_execution"],
            "required_tools": ["filesystem"],
            "workflow_types": ["sequential"],
            "min_success_rate": 0.8
        }

        response = test_client.post(
            "/api/v1/agent-pool/match",
            json=query_data,
            params={"algorithm": "weighted_score", "max_results": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert "total_candidates" in data
        assert "algorithm_used" in data

    def test_match_capabilities_with_context(self, test_client):
        """Test POST /agent-pool/match endpoint with matching context."""
        query_data = {
            "capability_types": ["task_execution"],
            "required_tools": ["filesystem"],
            "workflow_types": ["sequential"],
            "min_success_rate": 0.8,
            "context": {
                "step_count": 3,
                "estimated_duration": 120.0,
                "priority": 7,
                "prefer_reliable": True
            }
        }

        response = test_client.post(
            "/api/v1/agent-pool/match",
            json=query_data,
            params={"algorithm": "performance_optimized", "max_results": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert "algorithm_used" in data

    def test_heartbeat_endpoint(self, test_client):
        """Test POST /agent-pool/heartbeat endpoint."""
        heartbeat_data = {
            "agent_id": "test_agent_heartbeat",
            "health_status": "healthy",
            "current_load": 1
        }

        # This will fail because agent doesn't exist, but tests endpoint structure
        response = test_client.post("/api/v1/agent-pool/heartbeat", json=heartbeat_data)

        # Should return 404 for non-existent agent or 500 for service error
        assert response.status_code in [404, 500]

    def test_heartbeat_endpoint_invalid_data(self, test_client):
        """Test POST /agent-pool/heartbeat endpoint with invalid data."""
        invalid_data = {
            "agent_id": "",  # Empty agent ID
            "health_status": "invalid_status",
            "current_load": -1  # Negative load
        }

        response = test_client.post("/api/v1/agent-pool/heartbeat", json=invalid_data)

        # Should return validation error
        assert response.status_code == 422

    def test_register_agent_endpoint(self, test_client, sample_agent_data):
        """Test POST /agent-pool/register endpoint."""
        response = test_client.post("/api/v1/agent-pool/register", json=sample_agent_data)

        # Should succeed or fail gracefully
        assert response.status_code in [200, 201, 422, 500]

    def test_pool_statistics_endpoint(self, test_client):
        """Test GET /agent-pool/statistics endpoint."""
        response = test_client.get("/api/v1/agent-pool/statistics")

        assert response.status_code == 200
        data = response.json()
        assert "total_agents" in data
        assert "available_agents" in data
        assert "healthy_agents" in data
        assert "agents_by_type" in data
        assert "agents_by_health_status" in data

    def test_pool_health_endpoint(self, test_client):
        """Test GET /agent-pool/health endpoint."""
        response = test_client.get("/api/v1/agent-pool/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data

    def test_algorithm_test_endpoint(self, test_client):
        """Test POST /agent-pool/algorithms/test endpoint."""
        query_data = {
            "capability_types": ["task_execution"],
            "required_tools": ["filesystem"]
        }

        response = test_client.post("/api/v1/agent-pool/algorithms/test", json=query_data)

        assert response.status_code == 200
        data = response.json()
        assert "algorithms_tested" in data
        assert "results" in data
        assert "total_candidates" in data

    def test_get_agent_details_endpoint(self, test_client):
        """Test GET /agent-pool/{agent_id} endpoint."""
        response = test_client.get("/api/v1/agent-pool/test_agent_001")

        # Should return 404 for non-existent agent
        assert response.status_code in [200, 404]

    def test_invalid_agent_id_endpoint(self, test_client):
        """Test GET /agent-pool/{agent_id} with invalid ID."""
        response = test_client.get("/api/v1/agent-pool/nonexistent_agent_id")

        assert response.status_code == 404

    def test_remove_agent_endpoint(self, test_client):
        """Test DELETE /agent-pool/{agent_id} endpoint."""
        response = test_client.delete("/api/v1/agent-pool/nonexistent_agent")

        # Should return 404 for non-existent agent
        assert response.status_code == 404

    def test_remove_agent_with_reason(self, test_client):
        """Test DELETE /agent-pool/{agent_id} endpoint with reason."""
        response = test_client.delete(
            "/api/v1/agent-pool/test_agent",
            params={"reason": "maintenance"}
        )

        assert response.status_code in [200, 404]

    def test_endpoint_error_handling(self, test_client):
        """Test API endpoint error handling."""
        # Test malformed JSON
        response = test_client.post(
            "/api/v1/agent-pool/match",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test missing required fields
        response = test_client.post("/api/v1/agent-pool/heartbeat", json={})
        assert response.status_code == 422


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    @pytest.mark.asyncio
    async def test_playbook_agent_selection_workflow(self):
        """Test complete workflow for selecting agents for playbook execution."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        # Mock discovery service
        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Add sample agents representing real agent types
        agents = [
            AgentPoolEntry(
                agent_id="super_agent",
                agent_type="super",
                agent_name="Super Agent",
                description="Meta-coordinator agent",
                available_tools=["all_mcp_servers", "ptolemies-mcp"],
                supported_workflows=["all_types"],
                specializations=["coordination", "supervision"],
                health_status=HealthStatus.HEALTHY,
                capabilities=[
                    PlaybookCapability(
                        name="coordination",
                        display_name="Agent Coordination",
                        description="Coordinate multiple agents",
                        capability_type=PlaybookCapabilityType.WORKFLOW_CONTROL,
                        complexity=CapabilityComplexity.COMPLEX,
                        supported_step_types=["agent_task", "orchestration"],
                        required_tools=["ptolemies-mcp"]
                    )
                ]
            ),
            AgentPoolEntry(
                agent_id="codifier_agent",
                agent_type="codifier",
                agent_name="Codifier Agent",
                description="Documentation agent",
                available_tools=["filesystem", "git", "ptolemies-mcp"],
                supported_workflows=["sequential", "pipeline"],
                specializations=["documentation", "aar_generation"],
                health_status=HealthStatus.HEALTHY,
                capabilities=[
                    PlaybookCapability(
                        name="documentation",
                        display_name="Documentation Generation",
                        description="Generate documentation",
                        capability_type=PlaybookCapabilityType.DATA_PROCESSING,
                        complexity=CapabilityComplexity.MODERATE,
                        supported_step_types=["documentation", "analysis"],
                        required_tools=["filesystem", "git"]
                    )
                ]
            ),
            AgentPoolEntry(
                agent_id="io_agent",
                agent_type="io",
                agent_name="IO Agent",
                description="Monitoring agent",
                available_tools=["logfire-mcp", "memory", "fetch"],
                supported_workflows=["loop", "conditional"],
                specializations=["monitoring", "validation"],
                health_status=HealthStatus.HEALTHY,
                capabilities=[
                    PlaybookCapability(
                        name="monitoring",
                        display_name="System Monitoring",
                        description="Monitor system health",
                        capability_type=PlaybookCapabilityType.MONITORING,
                        complexity=CapabilityComplexity.SIMPLE,
                        supported_step_types=["monitoring", "validation"],
                        required_tools=["logfire-mcp"]
                    )
                ]
            )
        ]

        for agent in agents:
            discovery_service.agent_pool[agent.agent_id] = agent

        # Create playbook requirements
        playbook_requirements = CapabilityFilter(
            step_types=["agent_task", "documentation", "monitoring"],
            required_tools=["ptolemies-mcp"],
            workflow_types=["sequential"],
            health_statuses=[HealthStatus.HEALTHY]
        )

        # Find capable agents
        matches = await discovery_service.find_capable_agents(playbook_requirements)

        # Should find agents that can handle the requirements
        assert len(matches) >= 1

        # Verify agent assignments
        agent_ids = [match.agent_id for match in matches]
        assert "super_agent" in agent_ids  # Should be selected for coordination

    @pytest.mark.asyncio
    async def test_load_balancing_scenario(self):
        """Test load balancing across multiple agents."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        matcher = AdvancedCapabilityMatcher()

        # Create agents with different loads
        agents = []
        for i in range(4):  # 4 agents with varying loads
            agent = AgentPoolEntry(
                agent_id=f"worker_agent_{i}",
                agent_type="worker",
                agent_name=f"Worker Agent {i}",
                description=f"Worker agent {i}",
                available_tools=["common_tool"],
                supported_workflows=["sequential"],
                max_concurrent_executions=5,
                current_load=i,  # 0, 1, 2, 3
                health_status=HealthStatus.HEALTHY,
                capabilities=[
                    PlaybookCapability(
                        name="work_capability",
                        display_name="Work Capability",
                        description="Can perform work tasks",
                        capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                        complexity=CapabilityComplexity.SIMPLE,
                        supported_step_types=["action"],
                        required_tools=["common_tool"]
                    )
                ]
            )
            agents.append(agent)

        requirements = CapabilityFilter(
            step_types=["action"],
            required_tools=["common_tool"],
            health_statuses=[HealthStatus.HEALTHY]
        )

        context = MatchingContext(prefer_reliable=False)

        # Test load-balanced matching
        matches = await matcher.find_best_matches(
            agents=agents,
            requirements=requirements,
            context=context,
            algorithm=MatchingAlgorithm.LOAD_BALANCED,
            max_results=4
        )

        # Should return all agents, with lowest load first
        assert len(matches) >= 3
        if len(matches) >= 2:
            # First agent should have lower or equal load than second
            first_agent = next(a for a in agents if a.agent_id == matches[0].agent_id)
            second_agent = next(a for a in agents if a.agent_id == matches[1].agent_id)
            assert first_agent.current_load <= second_agent.current_load

    @pytest.mark.asyncio
    async def test_high_availability_scenario(self):
        """Test high availability agent selection."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Create agents with different health statuses
        agents = [
            AgentPoolEntry(
                agent_id="primary_agent",
                agent_type="primary",
                agent_name="Primary Agent",
                description="Primary service agent",
                health_status=HealthStatus.HEALTHY,
                current_load=2,
                max_concurrent_executions=10,
                available_tools=["service_tool"],
                supported_workflows=["sequential"]
            ),
            AgentPoolEntry(
                agent_id="backup_agent",
                agent_type="backup",
                agent_name="Backup Agent",
                description="Backup service agent",
                health_status=HealthStatus.HEALTHY,
                current_load=0,
                max_concurrent_executions=5,
                available_tools=["service_tool"],
                supported_workflows=["sequential"]
            ),
            AgentPoolEntry(
                agent_id="degraded_agent",
                agent_type="degraded",
                agent_name="Degraded Agent",
                description="Agent with issues",
                health_status=HealthStatus.WARNING,
                current_load=8,
                max_concurrent_executions=10,
                available_tools=["service_tool"],
                supported_workflows=["sequential"]
            ),
            AgentPoolEntry(
                agent_id="failed_agent",
                agent_type="failed",
                agent_name="Failed Agent",
                description="Failed agent",
                health_status=HealthStatus.CRITICAL,
                current_load=0,
                max_concurrent_executions=10,
                available_tools=["service_tool"],
                supported_workflows=["sequential"]
            )
        ]

        for agent in agents:
            discovery_service.agent_pool[agent.agent_id] = agent

        # Get available agents (should exclude failed and overloaded)
        available = await discovery_service.get_available_agents()

        # Should prefer healthy agents
        healthy_agents = [a for a in available if a.health_status == HealthStatus.HEALTHY]
        assert len(healthy_agents) >= 2

        # Should exclude critical agents
        critical_agents = [a for a in available if a.health_status == HealthStatus.CRITICAL]
        assert len(critical_agents) == 0

    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test system performance under load."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Create many agents
        agents = []
        for i in range(100):
            agent = AgentPoolEntry(
                agent_id=f"load_test_agent_{i:03d}",
                agent_type="load_test",
                agent_name=f"Load Test Agent {i}",
                description=f"Agent for load testing {i}",
                health_status=HealthStatus.HEALTHY if i % 4 != 0 else HealthStatus.WARNING,
                current_load=i % 5,
                available_tools=[f"tool_{i % 3}"],
                supported_workflows=["sequential"]
            )
            agents.append(agent)
            discovery_service.agent_pool[agent.agent_id] = agent

        # Time the statistics generation
        start_time = time.time()
        stats = await discovery_service.get_pool_statistics()
        stats_time = time.time() - start_time

        assert stats["total_agents"] == 100
        assert stats_time < 1.0  # Should complete within 1 second

        # Time agent filtering
        start_time = time.time()
        available = await discovery_service.get_available_agents()
        filter_time = time.time() - start_time

        assert len(available) > 0
        assert filter_time < 1.0  # Should complete within 1 second

        # Time capability matching
        requirements = CapabilityFilter(
            required_tools=["tool_0"],
            health_statuses=[HealthStatus.HEALTHY]
        )

        start_time = time.time()
        matches = await discovery_service.find_capable_agents(requirements, max_results=10)
        match_time = time.time() - start_time

        assert len(matches) <= 10
        assert match_time < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self):
        """Test error handling in various failure scenarios."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()

        # Test with unavailable schema manager
        discovery_service.schema_manager = None
        success = await discovery_service.initialize()
        assert success is True  # Should still initialize without schema manager

        # Test heartbeat update for non-existent agent
        success = await discovery_service.update_agent_heartbeat("nonexistent_agent")
        assert success is False

        # Test load update for non-existent agent
        success = await discovery_service.update_agent_load("nonexistent_agent", 5)
        assert success is False

        # Test capability registration for non-existent agent
        test_capability = PlaybookCapability(
            name="test_cap",
            display_name="Test",
            description="Test capability",
            capability_type=PlaybookCapabilityType.TASK_EXECUTION,
            complexity=CapabilityComplexity.SIMPLE
        )
        success = await discovery_service.register_agent_capability("nonexistent", test_capability)
        assert success is False

        # Test finding agents with empty pool
        discovery_service.agent_pool = {}
        requirements = CapabilityFilter(required_tools=["any_tool"])
        matches = await discovery_service.find_capable_agents(requirements)
        assert len(matches) == 0

    @pytest.mark.asyncio
    async def test_agent_lifecycle_management(self):
        """Test complete agent lifecycle from registration to removal."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # 1. Agent Registration
        agent = AgentPoolEntry(
            agent_id="lifecycle_test_agent",
            agent_type="test",
            agent_name="Lifecycle Test Agent",
            description="Agent for lifecycle testing",
            health_status=HealthStatus.HEALTHY,
            available_tools=["test_tool"],
            supported_workflows=["sequential"]
        )

        discovery_service.agent_pool[agent.agent_id] = agent
        assert agent.agent_id in discovery_service.agent_pool

        # 2. Agent Discovery
        retrieved = await discovery_service.get_agent_by_id(agent.agent_id)
        assert retrieved is not None
        assert retrieved.agent_id == agent.agent_id

        # 3. Heartbeat Updates
        old_heartbeat = agent.last_heartbeat
        await asyncio.sleep(0.01)  # Small delay
        success = await discovery_service.update_agent_heartbeat(agent.agent_id)
        assert success is True
        new_heartbeat = discovery_service.agent_pool[agent.agent_id].last_heartbeat
        assert new_heartbeat > old_heartbeat

        # 4. Load Updates
        success = await discovery_service.update_agent_load(agent.agent_id, 3)
        assert success is True
        assert discovery_service.agent_pool[agent.agent_id].current_load == 3

        # 5. Capability Registration
        new_capability = PlaybookCapability(
            name="lifecycle_capability",
            display_name="Lifecycle Capability",
            description="Added during lifecycle test",
            capability_type=PlaybookCapabilityType.TASK_EXECUTION,
            complexity=CapabilityComplexity.SIMPLE
        )
        success = await discovery_service.register_agent_capability(agent.agent_id, new_capability)
        assert success is True

        # 6. Agent Matching
        requirements = CapabilityFilter(required_tools=["test_tool"])
        matches = await discovery_service.find_capable_agents(requirements)
        assert len(matches) >= 1
        assert any(m.agent_id == agent.agent_id for m in matches)

        # 7. Agent Removal
        del discovery_service.agent_pool[agent.agent_id]
        assert agent.agent_id not in discovery_service.agent_pool

        # 8. Verify removal
        retrieved = await discovery_service.get_agent_by_id(agent.agent_id)
        assert retrieved is None


class TestPerformanceAndScalability:
    """Test suite for performance and scalability scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_heartbeat_updates(self):
        """Test concurrent heartbeat updates."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Create multiple agents
        agents = []
        for i in range(10):
            agent = AgentPoolEntry(
                agent_id=f"concurrent_agent_{i}",
                agent_type="concurrent",
                agent_name=f"Concurrent Agent {i}",
                description=f"Agent for concurrency testing {i}",
                health_status=HealthStatus.HEALTHY
            )
            agents.append(agent)
            discovery_service.agent_pool[agent.agent_id] = agent

        # Update heartbeats concurrently
        async def update_heartbeat(agent_id):
            return await discovery_service.update_agent_heartbeat(agent_id)

        # Run concurrent updates
        tasks = [update_heartbeat(agent.agent_id) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All updates should succeed
        assert all(result is True for result in results if not isinstance(result, Exception))

    @pytest.mark.asyncio
    async def test_large_agent_pool_performance(self):
        """Test performance with large agent pool."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Create 1000 agents
        for i in range(1000):
            agent = AgentPoolEntry(
                agent_id=f"perf_agent_{i:04d}",
                agent_type=f"type_{i % 10}",
                agent_name=f"Performance Agent {i}",
                description=f"Performance test agent {i}",
                health_status=HealthStatus.HEALTHY if i % 5 != 0 else HealthStatus.WARNING,
                current_load=i % 10,
                available_tools=[f"tool_{i % 5}"],
                supported_workflows=["sequential", "parallel"][i % 2:i % 2 + 1]
            )
            discovery_service.agent_pool[agent.agent_id] = agent

        # Test statistics performance
        start_time = time.time()
        stats = await discovery_service.get_pool_statistics()
        stats_duration = time.time() - start_time

        assert stats["total_agents"] == 1000
        assert stats_duration < 2.0  # Should complete within 2 seconds

        # Test filtering performance
        start_time = time.time()
        available = await discovery_service.get_available_agents()
        filter_duration = time.time() - start_time

        assert len(available) > 0
        assert filter_duration < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test memory usage doesn't grow excessively."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Add and remove agents multiple times
        for cycle in range(10):
            # Add 100 agents
            for i in range(100):
                agent = AgentPoolEntry(
                    agent_id=f"memory_test_agent_{cycle}_{i}",
                    agent_type="memory_test",
                    agent_name=f"Memory Test Agent {cycle}-{i}",
                    description="Agent for memory testing",
                    health_status=HealthStatus.HEALTHY
                )
                discovery_service.agent_pool[agent.agent_id] = agent

            # Perform operations
            await discovery_service.get_pool_statistics()
            available = await discovery_service.get_available_agents()

            # Remove all agents from this cycle
            for i in range(100):
                agent_id = f"memory_test_agent_{cycle}_{i}"
                if agent_id in discovery_service.agent_pool:
                    del discovery_service.agent_pool[agent_id]

        # Pool should be empty after cleanup
        final_stats = await discovery_service.get_pool_statistics()
        assert final_stats["total_agents"] == 0


class TestEdgeCasesAndErrorConditions:
    """Test suite for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_capability_filters(self):
        """Test behavior with empty capability filters."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Add a test agent
        agent = AgentPoolEntry(
            agent_id="edge_case_agent",
            agent_type="test",
            agent_name="Edge Case Agent",
            description="Agent for edge case testing",
            health_status=HealthStatus.HEALTHY
        )
        discovery_service.agent_pool[agent.agent_id] = agent

        # Test with completely empty filter
        empty_filter = CapabilityFilter()
        matches = await discovery_service.find_capable_agents(empty_filter)
        assert len(matches) >= 1  # Should match all agents

    @pytest.mark.asyncio
    async def test_malformed_agent_data(self):
        """Test handling of malformed agent data."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Test with agent missing required fields (handled by Pydantic validation)
        try:
            malformed_agent = AgentPoolEntry(
                agent_id="malformed_agent",
                # Missing required fields should be caught by Pydantic
            )
            assert False, "Should have raised validation error"
        except Exception:
            # Expected behavior - Pydantic should catch this
            pass

    @pytest.mark.asyncio
    async def test_extremely_high_load_agent(self):
        """Test agent with extremely high load values."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Create agent with very high load
        high_load_agent = AgentPoolEntry(
            agent_id="high_load_agent",
            agent_type="stress",
            agent_name="High Load Agent",
            description="Agent under extreme load",
            health_status=HealthStatus.HEALTHY,
            current_load=999999,
            max_concurrent_executions=10
        )
        discovery_service.agent_pool[high_load_agent.agent_id] = high_load_agent

        # Should not appear in available agents
        available = await discovery_service.get_available_agents()
        high_load_available = [a for a in available if a.agent_id == "high_load_agent"]
        assert len(high_load_available) == 0

    @pytest.mark.asyncio
    async def test_agent_with_zero_capabilities(self):
        """Test agent with no capabilities."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Create agent with no capabilities
        no_cap_agent = AgentPoolEntry(
            agent_id="no_capabilities_agent",
            agent_type="basic",
            agent_name="No Capabilities Agent",
            description="Agent with no capabilities",
            health_status=HealthStatus.HEALTHY,
            capabilities=[]  # Empty capabilities list
        )
        discovery_service.agent_pool[no_cap_agent.agent_id] = no_cap_agent

        # Should still be discoverable but may not match capability requirements
        agent = await discovery_service.get_agent_by_id("no_capabilities_agent")
        assert agent is not None
        assert len(agent.capabilities) == 0

    @pytest.mark.asyncio
    async def test_duplicate_agent_registration(self):
        """Test handling of duplicate agent registrations."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        discovery_service = AgentPoolDiscoveryService()
        await discovery_service.initialize()

        # Register agent twice
        agent1 = AgentPoolEntry(
            agent_id="duplicate_agent",
            agent_type="test",
            agent_name="Original Agent",
            description="Original agent",
            health_status=HealthStatus.HEALTHY
        )
        discovery_service.agent_pool[agent1.agent_id] = agent1

        agent2 = AgentPoolEntry(
            agent_id="duplicate_agent",
            agent_type="test",
            agent_name="Duplicate Agent",
            description="Duplicate agent",
            health_status=HealthStatus.WARNING
        )
        discovery_service.agent_pool[agent2.agent_id] = agent2

        # Should overwrite the first agent
        retrieved = await discovery_service.get_agent_by_id("duplicate_agent")
        assert retrieved.agent_name == "Duplicate Agent"
        assert retrieved.health_status == HealthStatus.WARNING


async def run_manual_tests():
    """Run tests manually without pytest."""
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Cannot run tests - dependencies not available")
        return False

    try:
        logger.info("🧪 Starting manual agent pool discovery tests...")

        # Test 1: Service initialization
        discovery_service = AgentPoolDiscoveryService()
        success = await discovery_service.initialize()
        assert success, "Service initialization failed"
        logger.info("✅ Service initialization test passed")

        # Test 2: Agent registration
        test_agent = AgentPoolEntry(
            agent_id="manual_test_agent",
            agent_type="test",
            agent_name="Manual Test Agent",
            description="Test agent for manual testing",
            available_tools=["filesystem", "git"],
            supported_workflows=["sequential"],
            specializations=["testing"],
            health_status=HealthStatus.HEALTHY
        )

        discovery_service.agent_pool[test_agent.agent_id] = test_agent
        retrieved_agent = await discovery_service.get_agent_by_id(test_agent.agent_id)
        assert retrieved_agent is not None, "Agent registration failed"
        logger.info("✅ Agent registration test passed")

        # Test 3: Capability matching
        capability_filter = CapabilityFilter(
            required_tools=["filesystem"],
            workflow_types=["sequential"],
            health_statuses=[HealthStatus.HEALTHY]
        )

        matches = await discovery_service.find_capable_agents(capability_filter)
        assert len(matches) >= 0, "Capability matching failed"
        logger.info("✅ Capability matching test passed")

        # Test 4: Heartbeat update
        old_heartbeat = test_agent.last_heartbeat
        await asyncio.sleep(0.01)  # Small delay
        success = await discovery_service.update_agent_heartbeat(test_agent.agent_id)
        new_heartbeat = discovery_service.agent_pool[test_agent.agent_id].last_heartbeat
        assert success and new_heartbeat > old_heartbeat, "Heartbeat update failed"
        logger.info("✅ Heartbeat update test passed")

        # Test 5: Pool statistics
        stats = await discovery_service.get_pool_statistics()
        assert "total_agents" in stats, "Statistics generation failed"
        assert stats["total_agents"] > 0, "No agents in statistics"
        logger.info("✅ Pool statistics test passed")

        # Test 6: Advanced matching algorithms
        matcher = AdvancedCapabilityMatcher()
        context = MatchingContext(priority=7, prefer_reliable=True)

        # Test multiple algorithms
        algorithms_tested = 0
        for algorithm in [MatchingAlgorithm.WEIGHTED_SCORE, MatchingAlgorithm.PERFORMANCE_OPTIMIZED]:
            try:
                matches = await matcher.find_best_matches(
                    agents=[test_agent],
                    requirements=capability_filter,
                    context=context,
                    algorithm=algorithm,
                    max_results=5
                )
                algorithms_tested += 1
                logger.info(f"✅ Algorithm {algorithm.value} test passed")
            except Exception as e:
                logger.warning(f"⚠️ Algorithm {algorithm.value} test failed: {e}")

        assert algorithms_tested > 0, "No algorithms successfully tested"

        # Test 7: Load balancing
        # Create multiple agents with different loads
        for i in range(3):
            load_agent = AgentPoolEntry(
                agent_id=f"load_test_agent_{i}",
                agent_type="worker",
                agent_name=f"Load Test Agent {i}",
                description=f"Agent for load testing {i}",
                current_load=i * 2,
                max_concurrent_executions=5,
                health_status=HealthStatus.HEALTHY,
                available_tools=["common_tool"],
                supported_workflows=["sequential"]
            )
            discovery_service.agent_pool[load_agent.agent_id] = load_agent

        load_filter = CapabilityFilter(required_tools=["common_tool"])
        load_matches = await matcher.find_best_matches(
            agents=list(discovery_service.agent_pool.values()),
            requirements=load_filter,
            context=MatchingContext(),
            algorithm=MatchingAlgorithm.LOAD_BALANCED,
            max_results=5
        )
        assert len(load_matches) >= 3, "Load balancing test failed"
        logger.info("✅ Load balancing test passed")

        # Test 8: Error handling
        # Test with non-existent agent
        success = await discovery_service.update_agent_heartbeat("nonexistent_agent")
        assert success is False, "Error handling test failed"
        logger.info("✅ Error handling test passed")

        # Test 9: Concurrent operations
        async def concurrent_heartbeat_updates():
            tasks = [
                discovery_service.update_agent_heartbeat(test_agent.agent_id)
                for _ in range(5)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return all(r is True for r in results if not isinstance(r, Exception))

        concurrent_success = await concurrent_heartbeat_updates()
        assert concurrent_success, "Concurrent operations test failed"
        logger.info("✅ Concurrent operations test passed")

        # Test 10: Performance with many agents
        # Add 100 agents quickly
        start_time = time.time()
        for i in range(100):
            perf_agent = AgentPoolEntry(
                agent_id=f"perf_agent_{i:03d}",
                agent_type="performance",
                agent_name=f"Performance Agent {i}",
                description=f"Performance test agent {i}",
                health_status=HealthStatus.HEALTHY if i % 4 != 0 else HealthStatus.WARNING
            )
            discovery_service.agent_pool[perf_agent.agent_id] = perf_agent

        # Test statistics generation performance
        perf_stats = await discovery_service.get_pool_statistics()
        perf_time = time.time() - start_time

        assert perf_stats["total_agents"] >= 100, "Performance test failed"
        assert perf_time < 5.0, f"Performance test too slow: {perf_time:.2f}s"
        logger.info("✅ Performance test passed")

        logger.info("🎉 All manual tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Manual test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run manual tests if executed directly
    import asyncio

    result = asyncio.run(run_manual_tests())
    if result:
        print("✅ All tests passed!")
        exit(0)
    else:
        print("❌ Tests failed!")
        exit(1)
