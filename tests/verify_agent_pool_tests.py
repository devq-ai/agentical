#!/usr/bin/env python3
"""
Simplified Test Verification for Agent Pool Discovery System

This script provides a minimal test verification for the agent pool discovery
system without external dependencies, focusing on core functionality.
"""

import asyncio
import sys
import os
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("🔍 Verifying Agent Pool Discovery Tests...")

def test_imports():
    """Test that all required modules can be imported."""
    try:
        from agents.pool_discovery import AgentPoolDiscoveryService
        from agents.playbook_capabilities import (
            AgentPoolEntry, PlaybookCapability, CapabilityFilter,
            HealthStatus, PlaybookCapabilityType, CapabilityComplexity
        )
        from agents.capability_matcher import (
            AdvancedCapabilityMatcher, MatchingContext, MatchingAlgorithm
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_service_initialization():
    """Test basic service initialization."""
    try:
        from agents.pool_discovery import AgentPoolDiscoveryService

        service = AgentPoolDiscoveryService()
        service.agent_registry = Mock()
        service.agent_registry.list_agents = AsyncMock(return_value=[])

        success = await service.initialize()
        assert success is True
        assert hasattr(service, 'agent_pool')
        assert isinstance(service.agent_pool, dict)

        print("✅ Service initialization test passed")
        return True
    except Exception as e:
        print(f"❌ Service initialization test failed: {e}")
        return False

async def test_agent_registration():
    """Test agent registration functionality."""
    try:
        from agents.pool_discovery import AgentPoolDiscoveryService
        from agents.playbook_capabilities import AgentPoolEntry, HealthStatus

        service = AgentPoolDiscoveryService()
        service.agent_registry = Mock()
        service.agent_registry.list_agents = AsyncMock(return_value=[])
        await service.initialize()

        # Create test agent
        test_agent = AgentPoolEntry(
            agent_id="test_verify_agent",
            agent_type="test",
            agent_name="Test Verification Agent",
            description="Agent for verification testing",
            health_status=HealthStatus.HEALTHY,
            available_tools=["memory", "filesystem"],
            supported_workflows=["sequential"]
        )

        # Register agent
        service.agent_pool[test_agent.agent_id] = test_agent

        # Verify registration
        retrieved = await service.get_agent_by_id(test_agent.agent_id)
        assert retrieved is not None
        assert retrieved.agent_id == test_agent.agent_id
        assert retrieved.agent_name == "Test Verification Agent"

        print("✅ Agent registration test passed")
        return True
    except Exception as e:
        print(f"❌ Agent registration test failed: {e}")
        return False

async def test_heartbeat_updates():
    """Test heartbeat update functionality."""
    try:
        from agents.pool_discovery import AgentPoolDiscoveryService
        from agents.playbook_capabilities import AgentPoolEntry, HealthStatus

        service = AgentPoolDiscoveryService()
        service.agent_registry = Mock()
        service.agent_registry.list_agents = AsyncMock(return_value=[])
        await service.initialize()

        # Create and register test agent
        test_agent = AgentPoolEntry(
            agent_id="heartbeat_test_agent",
            agent_type="test",
            agent_name="Heartbeat Test Agent",
            description="Agent for heartbeat testing",
            health_status=HealthStatus.HEALTHY
        )
        service.agent_pool[test_agent.agent_id] = test_agent

        # Get initial heartbeat
        initial_heartbeat = test_agent.last_heartbeat

        # Wait a moment and update heartbeat
        await asyncio.sleep(0.01)
        success = await service.update_agent_heartbeat(test_agent.agent_id)

        # Verify update
        assert success is True
        updated_agent = service.agent_pool[test_agent.agent_id]
        assert updated_agent.last_heartbeat > initial_heartbeat

        print("✅ Heartbeat update test passed")
        return True
    except Exception as e:
        print(f"❌ Heartbeat update test failed: {e}")
        return False

async def test_capability_filtering():
    """Test capability filtering functionality."""
    try:
        from agents.pool_discovery import AgentPoolDiscoveryService
        from agents.playbook_capabilities import (
            AgentPoolEntry, CapabilityFilter, HealthStatus,
            PlaybookCapability, PlaybookCapabilityType, CapabilityComplexity
        )

        service = AgentPoolDiscoveryService()
        service.agent_registry = Mock()
        service.agent_registry.list_agents = AsyncMock(return_value=[])
        await service.initialize()

        # Create test agent with capabilities
        test_capability = PlaybookCapability(
            name="test_capability",
            display_name="Test Capability",
            description="A test capability",
            capability_type=PlaybookCapabilityType.TASK_EXECUTION,
            complexity=CapabilityComplexity.SIMPLE,
            supported_step_types=["action"],
            required_tools=["memory"]
        )

        test_agent = AgentPoolEntry(
            agent_id="capability_test_agent",
            agent_type="test",
            agent_name="Capability Test Agent",
            description="Agent for capability testing",
            health_status=HealthStatus.HEALTHY,
            available_tools=["memory", "filesystem"],
            supported_workflows=["sequential"],
            capabilities=[test_capability]
        )
        service.agent_pool[test_agent.agent_id] = test_agent

        # Create filter
        capability_filter = CapabilityFilter(
            required_tools=["memory"],
            workflow_types=["sequential"],
            health_statuses=[HealthStatus.HEALTHY]
        )

        # Find capable agents
        matches = await service.find_capable_agents(capability_filter, max_results=5)

        # Verify results
        assert len(matches) > 0
        assert matches[0].agent_id == test_agent.agent_id
        assert matches[0].is_viable is True

        print("✅ Capability filtering test passed")
        return True
    except Exception as e:
        print(f"❌ Capability filtering test failed: {e}")
        return False

async def test_pool_statistics():
    """Test pool statistics generation."""
    try:
        from agents.pool_discovery import AgentPoolDiscoveryService
        from agents.playbook_capabilities import AgentPoolEntry, HealthStatus

        service = AgentPoolDiscoveryService()
        service.agent_registry = Mock()
        service.agent_registry.list_agents = AsyncMock(return_value=[])
        await service.initialize()

        # Add multiple test agents
        for i in range(3):
            agent = AgentPoolEntry(
                agent_id=f"stats_test_agent_{i}",
                agent_type="test" if i < 2 else "worker",
                agent_name=f"Stats Test Agent {i}",
                description=f"Agent {i} for statistics testing",
                health_status=HealthStatus.HEALTHY if i < 2 else HealthStatus.WARNING
            )
            service.agent_pool[agent.agent_id] = agent

        # Get statistics
        stats = await service.get_pool_statistics()

        # Verify statistics
        assert "total_agents" in stats
        assert "available_agents" in stats
        assert "healthy_agents" in stats
        assert "agents_by_type" in stats
        assert "agents_by_health_status" in stats

        assert stats["total_agents"] == 3
        assert stats["healthy_agents"] == 2
        assert stats["agents_by_type"]["test"] == 2
        assert stats["agents_by_type"]["worker"] == 1

        print("✅ Pool statistics test passed")
        return True
    except Exception as e:
        print(f"❌ Pool statistics test failed: {e}")
        return False

async def test_capability_matcher():
    """Test capability matcher functionality."""
    try:
        from agents.capability_matcher import (
            AdvancedCapabilityMatcher, MatchingContext, MatchingAlgorithm
        )
        from agents.playbook_capabilities import (
            AgentPoolEntry, CapabilityFilter, HealthStatus,
            PlaybookCapability, PlaybookCapabilityType, CapabilityComplexity
        )

        matcher = AdvancedCapabilityMatcher()

        # Create test agents
        test_capability = PlaybookCapability(
            name="matcher_test_capability",
            display_name="Matcher Test Capability",
            description="Capability for matcher testing",
            capability_type=PlaybookCapabilityType.TASK_EXECUTION,
            complexity=CapabilityComplexity.SIMPLE,
            supported_step_types=["action"],
            required_tools=["test_tool"]
        )

        agents = [
            AgentPoolEntry(
                agent_id="matcher_agent_1",
                agent_type="test",
                agent_name="Matcher Agent 1",
                description="First matcher test agent",
                health_status=HealthStatus.HEALTHY,
                current_load=1,
                available_tools=["test_tool"],
                capabilities=[test_capability]
            ),
            AgentPoolEntry(
                agent_id="matcher_agent_2",
                agent_type="test",
                agent_name="Matcher Agent 2",
                description="Second matcher test agent",
                health_status=HealthStatus.HEALTHY,
                current_load=3,
                available_tools=["test_tool"],
                capabilities=[test_capability]
            )
        ]

        # Create requirements and context
        requirements = CapabilityFilter(
            required_tools=["test_tool"],
            health_statuses=[HealthStatus.HEALTHY]
        )
        context = MatchingContext()

        # Test matching
        matches = await matcher.find_best_matches(
            agents=agents,
            requirements=requirements,
            context=context,
            algorithm=MatchingAlgorithm.WEIGHTED_SCORE,
            max_results=5
        )

        # Verify results
        assert len(matches) > 0
        assert all(match.match_score >= 0.0 for match in matches)
        assert all(match.match_score <= 1.0 for match in matches)

        print("✅ Capability matcher test passed")
        return True
    except Exception as e:
        print(f"❌ Capability matcher test failed: {e}")
        return False

async def test_load_balancing():
    """Test load balancing functionality."""
    try:
        from agents.capability_matcher import (
            AdvancedCapabilityMatcher, MatchingContext, MatchingAlgorithm
        )
        from agents.playbook_capabilities import (
            AgentPoolEntry, CapabilityFilter, HealthStatus,
            PlaybookCapability, PlaybookCapabilityType, CapabilityComplexity
        )

        matcher = AdvancedCapabilityMatcher()

        # Create agents with different loads
        agents = []
        for i in range(3):
            capability = PlaybookCapability(
                name=f"load_test_capability_{i}",
                display_name=f"Load Test Capability {i}",
                description=f"Capability {i} for load testing",
                capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                complexity=CapabilityComplexity.SIMPLE,
                supported_step_types=["action"],
                required_tools=["common_tool"]
            )

            agent = AgentPoolEntry(
                agent_id=f"load_agent_{i}",
                agent_type="worker",
                agent_name=f"Load Agent {i}",
                description=f"Agent {i} for load testing",
                health_status=HealthStatus.HEALTHY,
                current_load=i * 2,  # 0, 2, 4
                max_concurrent_executions=5,
                available_tools=["common_tool"],
                capabilities=[capability]
            )
            agents.append(agent)

        requirements = CapabilityFilter(
            required_tools=["common_tool"],
            health_statuses=[HealthStatus.HEALTHY]
        )
        context = MatchingContext()

        # Test load-balanced matching
        matches = await matcher.find_best_matches(
            agents=agents,
            requirements=requirements,
            context=context,
            algorithm=MatchingAlgorithm.LOAD_BALANCED,
            max_results=3
        )

        # Verify load balancing (agent with lowest load should be first)
        assert len(matches) >= 2
        if len(matches) >= 2:
            first_agent = next(a for a in agents if a.agent_id == matches[0].agent_id)
            second_agent = next(a for a in agents if a.agent_id == matches[1].agent_id)
            assert first_agent.current_load <= second_agent.current_load

        print("✅ Load balancing test passed")
        return True
    except Exception as e:
        print(f"❌ Load balancing test failed: {e}")
        return False

async def test_error_handling():
    """Test error handling scenarios."""
    try:
        from agents.pool_discovery import AgentPoolDiscoveryService

        service = AgentPoolDiscoveryService()
        service.agent_registry = Mock()
        service.agent_registry.list_agents = AsyncMock(return_value=[])
        await service.initialize()

        # Test heartbeat update for non-existent agent
        success = await service.update_agent_heartbeat("nonexistent_agent")
        assert success is False

        # Test load update for non-existent agent
        success = await service.update_agent_load("nonexistent_agent", 5)
        assert success is False

        # Test getting non-existent agent
        agent = await service.get_agent_by_id("nonexistent_agent")
        assert agent is None

        print("✅ Error handling test passed")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def run_verification_tests():
    """Run all verification tests."""
    print("\n" + "="*60)
    print("AGENT POOL DISCOVERY TEST VERIFICATION")
    print("="*60)

    start_time = time.time()

    tests = [
        ("Import Test", test_imports),
        ("Service Initialization", test_service_initialization),
        ("Agent Registration", test_agent_registration),
        ("Heartbeat Updates", test_heartbeat_updates),
        ("Capability Filtering", test_capability_filtering),
        ("Pool Statistics", test_pool_statistics),
        ("Capability Matcher", test_capability_matcher),
        ("Load Balancing", test_load_balancing),
        ("Error Handling", test_error_handling)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1

    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {passed / (passed + failed) * 100:.1f}%")
    print(f"Duration: {duration:.2f}s")
    print("="*60)

    if failed == 0:
        print("🎉 All verification tests passed!")
        return True
    else:
        print(f"⚠️ {failed} test(s) failed")
        return False

def main():
    """Main entry point."""
    try:
        result = asyncio.run(run_verification_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
