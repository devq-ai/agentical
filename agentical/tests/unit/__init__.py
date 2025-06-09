"""
Unit Tests for Agentical Framework

This module contains unit tests that test individual components and functions
in isolation, following the DevQ.ai testing standards.

Unit tests should:
- Test single functions or methods in isolation
- Use mocks for external dependencies
- Run quickly (< 1 second each)
- Have high code coverage
- Test edge cases and error conditions

Test organization:
- test_agents.py: Agent class and functionality tests
- test_api.py: FastAPI endpoint unit tests
- test_models.py: Pydantic model tests
- test_utils.py: Utility function tests
- test_services.py: Service layer tests

Usage:
    # Run all unit tests
    pytest tests/unit/

    # Run specific unit test file
    pytest tests/unit/test_agents.py

    # Run with coverage
    pytest tests/unit/ --cov=agentical

Markers:
    All tests in this directory should be marked with @pytest.mark.unit
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Common test utilities for unit tests
__all__ = [
    "pytest",
    "Mock", 
    "patch", 
    "MagicMock",
    "TestClient"
]

# Unit test configuration
UNIT_TEST_TIMEOUT = 5  # Maximum timeout for unit tests in seconds