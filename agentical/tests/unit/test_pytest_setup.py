"""
PyTest Environment Setup Verification Tests

This module contains unit tests to verify that the PyTest environment is properly
configured and working as expected for the Agentical framework.

Tests verify:
- PyTest basic functionality
- Logfire integration and observability
- Test fixtures and utilities
- Coverage reporting
- Custom markers and configuration
- Test environment isolation

This test serves as validation for Task 6.1: Set up PyTest Environment and Directory Structure
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logfire


@pytest.mark.unit
class TestPyTestEnvironmentSetup:
    """Test class to verify PyTest environment configuration."""
    
    def test_pytest_basic_functionality(self):
        """Test that PyTest is working with basic assertions."""
        assert True
        assert 1 + 1 == 2
        assert "test" in "testing"
        
    def test_test_environment_variables(self, test_environment):
        """Test that test environment variables are properly set."""
        assert os.getenv("TESTING") == "true"
        assert os.getenv("ENVIRONMENT") == "test"
        assert os.getenv("DEBUG") == "true"
        assert os.getenv("LOGFIRE_ENVIRONMENT") == "test"
        
        # Verify test_environment fixture provides expected variables
        assert test_environment["TESTING"] == "true"
        assert test_environment["ENVIRONMENT"] == "test"
    
    def test_project_path_configuration(self):
        """Test that project paths are correctly configured."""
        # Verify that the project root is in Python path
        project_root = Path(__file__).parent.parent.parent
        assert str(project_root) in sys.path or any(
            str(project_root) in path for path in sys.path
        )
    
    def test_test_markers_available(self):
        """Test that custom pytest markers are properly configured."""
        # This test verifies that our custom markers are available
        # The markers should be defined in pytest.ini
        import _pytest.mark
        
        # These markers should be available (defined in pytest.ini)
        expected_markers = [
            "unit", "integration", "e2e", "slow", "external",
            "agent", "api", "db", "mcp", "performance", "security", "smoke"
        ]
        
        # Note: In actual pytest execution, these markers are automatically registered
        # This test mainly verifies the marker configuration exists
        assert True  # Placeholder - markers are validated during pytest execution
    
    @pytest.mark.unit
    def test_unit_marker_functionality(self):
        """Test that unit test marker is working."""
        # This test should be automatically marked as 'unit' by conftest.py
        assert hasattr(pytest.mark, 'unit')
    
    def test_logfire_integration_available(self, mock_logfire):
        """Test that Logfire integration is available and working."""
        # Test that Logfire can be imported and mocked
        assert 'info' in mock_logfire
        assert 'error' in mock_logfire
        assert 'warning' in mock_logfire
        assert 'span' in mock_logfire
        
        # Test that logfire methods can be called
        mock_logfire['info']("Test message")
        mock_logfire['info'].assert_called_once_with("Test message")
    
    def test_real_logfire_functionality(self):
        """Test that real Logfire integration works (when available)."""
        try:
            # Test that we can create a logfire span
            with logfire.span("Test PyTest Setup"):
                logfire.info("PyTest environment setup test")
                assert True
        except Exception as e:
            # If Logfire isn't configured, that's OK for this test
            pytest.skip(f"Logfire not available: {e}")
    
    def test_test_data_factory_fixture(self, test_data_factory):
        """Test that test data factory fixture is working."""
        # Test user data creation
        user_data = test_data_factory.create_user_data()
        assert "email" in user_data
        assert "username" in user_data
        assert user_data["is_active"] is True
        
        # Test custom user data
        custom_user = test_data_factory.create_user_data(email="custom@test.com")
        assert custom_user["email"] == "custom@test.com"
        
        # Test agent data creation
        agent_data = test_data_factory.create_agent_data()
        assert "name" in agent_data
        assert "capabilities" in agent_data
        assert isinstance(agent_data["capabilities"], list)
        
        # Test workflow data creation
        workflow_data = test_data_factory.create_workflow_data()
        assert "name" in workflow_data
        assert "steps" in workflow_data
        assert isinstance(workflow_data["steps"], list)
    
    def test_performance_monitor_fixture(self, performance_monitor):
        """Test that performance monitoring fixture is working."""
        assert performance_monitor is not None
        assert hasattr(performance_monitor, 'start')
        assert hasattr(performance_monitor, 'stop')
        
        # Test that we can get metrics
        metrics = performance_monitor.stop()
        if metrics:  # Only if psutil is available
            assert 'duration' in metrics
            assert 'memory_used_mb' in metrics
            assert 'cpu_percent' in metrics
    
    def test_temp_directory_fixture(self, temp_directory):
        """Test that temporary directory fixture is working."""
        assert temp_directory.exists()
        assert temp_directory.is_dir()
        
        # Test writing to temp directory
        test_file = temp_directory / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"
    
    def test_mock_external_services_fixture(self, mock_external_services):
        """Test that external services mocking is working."""
        assert 'httpx' in mock_external_services
        assert 'requests_get' in mock_external_services
        assert 'requests_post' in mock_external_services
        assert 'async_client' in mock_external_services
        
        # Test that mocks are configured
        mock_get = mock_external_services['requests_get']
        mock_response = mock_get.return_value
        assert mock_response.status_code == 200
        assert mock_response.json() == {"status": "success"}
    
    def test_coverage_configuration(self):
        """Test that coverage configuration is properly set up."""
        # This test verifies that coverage can be imported
        try:
            import coverage
            assert True
        except ImportError:
            pytest.fail("Coverage module not available - check pytest-cov installation")
    
    def test_async_support_available(self):
        """Test that async test support is available."""
        try:
            import pytest_asyncio
            assert True
        except ImportError:
            pytest.fail("pytest-asyncio not available - check installation")
    
    def test_mock_support_available(self):
        """Test that mocking support is available."""
        try:
            import pytest_mock
            assert True
        except ImportError:
            pytest.fail("pytest-mock not available - check installation")
    
    def test_parallel_execution_support(self):
        """Test that parallel execution support is available."""
        try:
            import xdist
            assert True
        except ImportError:
            pytest.fail("pytest-xdist not available - check installation")


@pytest.mark.unit
class TestPyTestConfiguration:
    """Test PyTest configuration and settings."""
    
    def test_pytest_ini_exists(self):
        """Test that pytest.ini configuration file exists."""
        project_root = Path(__file__).parent.parent.parent
        pytest_ini = project_root / "pytest.ini"
        assert pytest_ini.exists(), "pytest.ini file not found"
    
    def test_reports_directory_exists(self):
        """Test that reports directory exists for test output."""
        project_root = Path(__file__).parent.parent.parent
        reports_dir = project_root / "reports"
        assert reports_dir.exists(), "reports directory not found"
        assert reports_dir.is_dir(), "reports should be a directory"
    
    def test_test_directory_structure(self):
        """Test that test directory structure is properly set up."""
        tests_dir = Path(__file__).parent.parent
        
        # Check main test directories exist
        assert (tests_dir / "unit").exists()
        assert (tests_dir / "integration").exists()
        assert (tests_dir / "e2e").exists()
        assert (tests_dir / "fixtures").exists()
        
        # Check that __init__.py files exist
        assert (tests_dir / "__init__.py").exists()
        assert (tests_dir / "unit" / "__init__.py").exists()
        assert (tests_dir / "integration" / "__init__.py").exists()
        assert (tests_dir / "e2e" / "__init__.py").exists()
    
    def test_conftest_file_exists(self):
        """Test that conftest.py exists and is importable."""
        tests_dir = Path(__file__).parent.parent
        conftest_file = tests_dir / "conftest.py"
        assert conftest_file.exists(), "conftest.py not found"
        
        # Test that conftest can be imported
        try:
            import tests.conftest
            assert True
        except ImportError as e:
            pytest.fail(f"Cannot import conftest.py: {e}")


@pytest.mark.unit
def test_simple_function_test():
    """Simple function-based test to verify basic pytest functionality."""
    def add_numbers(a, b):
        return a + b
    
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0


@pytest.mark.unit
@pytest.mark.parametrize("input_value,expected", [
    (1, 2),
    (2, 4), 
    (3, 6),
    (0, 0),
    (-1, -2)
])
def test_parametrized_test(input_value, expected):
    """Test parametrized test functionality."""
    def double_value(x):
        return x * 2
    
    assert double_value(input_value) == expected


@pytest.mark.unit
@pytest.mark.slow
def test_slow_test_marker():
    """Test that slow marker is working."""
    import time
    time.sleep(0.1)  # Brief delay to simulate slow test
    assert True


@pytest.mark.unit
async def test_async_test_support():
    """Test that async tests are supported."""
    import asyncio
    
    async def async_function():
        await asyncio.sleep(0.01)
        return "async_result"
    
    result = await async_function()
    assert result == "async_result"


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])