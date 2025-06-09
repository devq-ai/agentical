"""
Integration Tests for Agentical Framework

This module contains integration tests that verify component interactions and
system behavior across multiple modules, following DevQ.ai testing standards.

Integration tests should:
- Test interactions between multiple components
- Verify data flow across system boundaries
- Test API endpoints with real database interactions
- Use test databases and controlled external services
- Validate system behavior under realistic conditions

Test organization:
- test_api_endpoints.py: FastAPI endpoint integration tests
- test_database.py: Database operation tests
- test_agent_integration.py: Agent interaction with other components
- test_external_services.py: External service integration tests
- test_workflow_engine.py: Workflow coordination tests
- test_mcp_integration.py: MCP server integration tests

Test patterns:
- Use test database fixtures for data isolation
- Mock external services when appropriate
- Test error handling across component boundaries
- Verify proper logging and monitoring integration
- Test authentication and authorization flows

Usage:
    # Run all integration tests
    pytest tests/integration/

    # Run specific integration test file
    pytest tests/integration/test_api_endpoints.py

    # Run with coverage and Logfire monitoring
    pytest tests/integration/ --cov=agentical

    # Run excluding slow tests
    pytest tests/integration/ -m "not slow"

Markers:
    All tests in this directory should be marked with @pytest.mark.integration
    Additional markers as needed: @pytest.mark.api, @pytest.mark.db, etc.

Test Environment:
- Uses test database configuration
- Isolated test data with proper cleanup
- Controlled external service mocking
- Logfire integration for test observability
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Common test utilities for integration tests
__all__ = [
    "pytest",
    "asyncio",
    "Mock", 
    "patch", 
    "MagicMock",
    "AsyncMock",
    "TestClient",
    "AsyncClient",
    "create_engine",
    "sessionmaker"
]

# Integration test configuration
INTEGRATION_TEST_TIMEOUT = 30  # Maximum timeout for integration tests in seconds
TEST_DATABASE_URL = "sqlite:///./test_agentical.db"
API_TEST_HOST = "http://testserver"
EXTERNAL_SERVICE_TIMEOUT = 10  # Timeout for external service calls in tests

# Test environment settings
TEST_ENVIRONMENT = {
    "ENVIRONMENT": "test",
    "DEBUG": "true",
    "DATABASE_URL": TEST_DATABASE_URL,
    "LOGFIRE_ENVIRONMENT": "test",
    "TESTING": "true"
}