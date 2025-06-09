"""
Agentical Test Suite

This package contains comprehensive tests for the Agentical framework, organized according
to DevQ.ai testing standards with PyTest and Logfire integration.

Test Structure:
- unit/: Unit tests for individual components and functions
- integration/: Integration tests for component interactions
- e2e/: End-to-end tests for complete workflows
- fixtures/: Test data and reusable fixtures

Test Categories (using pytest markers):
- @pytest.mark.unit: Individual component tests
- @pytest.mark.integration: Multi-component interaction tests
- @pytest.mark.e2e: Complete user workflow tests
- @pytest.mark.slow: Tests taking >1 second
- @pytest.mark.external: Tests requiring external services
- @pytest.mark.agent: Agent-specific functionality tests
- @pytest.mark.api: FastAPI endpoint tests
- @pytest.mark.db: Database interaction tests
- @pytest.mark.mcp: MCP server integration tests
- @pytest.mark.performance: Performance and load tests
- @pytest.mark.security: Security-related tests
- @pytest.mark.smoke: Basic smoke tests

Testing Standards:
- Minimum 90% code coverage required
- All tests must pass before task completion
- Logfire integration for test monitoring and observability
- Build-to-test development approach

Usage:
    # Run all tests
    pytest

    # Run specific test categories
    pytest -m unit
    pytest -m integration
    pytest -m "not slow"

    # Run with coverage
    pytest --cov=agentical

    # Run in parallel
    pytest -n auto
"""

import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Version for test compatibility
__version__ = "0.1.0"

# Test configuration constants
TEST_TIMEOUT = 30  # Default test timeout in seconds
MIN_COVERAGE = 90  # Minimum code coverage percentage
MAX_PARALLEL_TESTS = 4  # Maximum parallel test processes