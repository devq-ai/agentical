"""
End-to-End Tests for Agentical Framework

This module contains end-to-end tests that verify complete user workflows and
system behavior from start to finish, following DevQ.ai testing standards.

End-to-end tests should:
- Test complete user workflows and business processes
- Verify system behavior across all components
- Use realistic data and scenarios
- Test critical user journeys
- Validate system performance under realistic conditions
- Test security and authentication flows end-to-end

Test organization:
- test_user_workflows.py: Complete user interaction workflows
- test_agent_workflows.py: End-to-end agent execution scenarios
- test_business_processes.py: Critical business process validation
- test_system_integration.py: Full system integration scenarios
- test_security_flows.py: Authentication and authorization workflows
- test_performance_scenarios.py: Performance under realistic load

Test characteristics:
- Use production-like configuration when possible
- Test with realistic data volumes
- Validate complete request/response cycles
- Test error recovery and system resilience
- Monitor system resources during execution
- Verify proper logging and monitoring across all components

Usage:
    # Run all e2e tests
    pytest tests/e2e/

    # Run specific e2e test file
    pytest tests/e2e/test_user_workflows.py

    # Run with full coverage and monitoring
    pytest tests/e2e/ --cov=agentical --maxfail=1

    # Run only critical workflow tests
    pytest tests/e2e/ -m "not slow"

    # Run with parallel execution (use with caution)
    pytest tests/e2e/ -n 2

Markers:
    All tests in this directory should be marked with @pytest.mark.e2e
    Additional markers: @pytest.mark.slow, @pytest.mark.critical, @pytest.mark.security

Test Environment:
- Uses production-like configuration
- Real database connections with test data
- External service integration (with fallback mocks)
- Full Logfire observability and monitoring
- Resource usage monitoring and cleanup

Performance Expectations:
- Individual tests may take 10-60 seconds
- Full suite may take several minutes
- Resource cleanup is critical
- Proper isolation between test scenarios
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import logfire
from pathlib import Path

# Common test utilities for e2e tests
__all__ = [
    "pytest",
    "asyncio", 
    "time",
    "Mock", 
    "patch", 
    "MagicMock",
    "AsyncMock",
    "TestClient",
    "AsyncClient",
    "logfire",
    "Path"
]

# E2E test configuration
E2E_TEST_TIMEOUT = 60  # Maximum timeout for e2e tests in seconds
WORKFLOW_TIMEOUT = 120  # Maximum timeout for complex workflows
DATABASE_SETUP_TIMEOUT = 30  # Maximum time for database setup
API_BASE_URL = "http://localhost:8000"  # Base URL for API testing
EXTERNAL_SERVICE_TIMEOUT = 20  # Timeout for external service calls

# Test data configuration
TEST_DATA_DIR = Path(__file__).parent.parent / "fixtures" / "e2e_data"
SAMPLE_WORKFLOWS_DIR = TEST_DATA_DIR / "workflows"
SAMPLE_AGENTS_DIR = TEST_DATA_DIR / "agents"

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "api_response_time": 2.0,  # Maximum API response time in seconds
    "workflow_completion": 30.0,  # Maximum workflow completion time
    "agent_initialization": 5.0,  # Maximum agent initialization time
    "database_query": 1.0,  # Maximum database query time
}

# Test environment settings for e2e tests
E2E_ENVIRONMENT = {
    "ENVIRONMENT": "e2e_test",
    "DEBUG": "false",
    "TESTING": "true",
    "LOGFIRE_ENVIRONMENT": "e2e_test",
    "API_TIMEOUT": "30",
    "DATABASE_TIMEOUT": "15",
    "EXTERNAL_SERVICE_TIMEOUT": str(EXTERNAL_SERVICE_TIMEOUT)
}

# Critical test scenarios that must always pass
CRITICAL_SCENARIOS = [
    "user_authentication_flow",
    "agent_creation_and_execution", 
    "workflow_orchestration",
    "error_handling_and_recovery",
    "system_health_monitoring"
]