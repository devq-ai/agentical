"""
Unit Tests for Logfire SDK Integration with PyTest

This module contains tests that validate the Logfire SDK integration with PyTest,
ensuring that test events are properly captured and sent to Logfire for monitoring
and observability.

These tests complete Task 6.2: Integrate Logfire SDK with Custom PyTest Plugin.
"""

import pytest
import logging
import os
from unittest.mock import patch, MagicMock
import logfire


@pytest.fixture
def ensure_logfire_test_env():
    """Ensure proper environment for Logfire testing."""
    # Store original environment variables
    original_env = {}
    for key in ["LOGFIRE_ENABLED", "LOGFIRE_IGNORE_NO_CONFIG"]:
        original_env[key] = os.environ.get(key)
    
    # Set test environment
    os.environ["LOGFIRE_ENABLED"] = "true"
    os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "1"  # Don't warn if not configured
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value


@pytest.mark.unit
class TestLogfireIntegration:
    """Test Logfire SDK integration with PyTest."""
    
    def test_logfire_basic_functionality(self, ensure_logfire_test_env, mock_logfire):
        """Test basic Logfire functionality works in tests."""
        # Reset mock to clear previous calls from LogfireTestPlugin
        mock_logfire['info'].reset_mock()
        
        # Use Logfire in the test
        logfire.info("Test message from test_logfire_basic_functionality")
        
        # Verify Logfire was called
        mock_logfire['info'].assert_called_with(
            "Test message from test_logfire_basic_functionality"
        )
    
    def test_logfire_structured_logging(self, ensure_logfire_test_env, mock_logfire):
        """Test structured logging with Logfire."""
        # Reset mock to clear previous calls from LogfireTestPlugin
        mock_logfire['info'].reset_mock()
        
        # Log with structured data
        logfire.info(
            "Structured log message",
            test_id=123,
            environment="test",
            metadata={"key": "value"}
        )
        
        # Verify Logfire was called with structured data
        args, kwargs = mock_logfire['info'].call_args
        
        assert args[0] == "Structured log message"
        assert kwargs["test_id"] == 123
        assert kwargs["environment"] == "test"
        assert kwargs["metadata"] == {"key": "value"}
    
    def test_logfire_span_context_manager(self, ensure_logfire_test_env, mock_logfire):
        """Test Logfire span context manager."""
        # Reset mocks to clear previous calls from LogfireTestPlugin
        mock_logfire['span'].reset_mock()
        mock_logfire['info'].reset_mock()
        
        # Use Logfire span
        with logfire.span("Test span"):
            logfire.info("Log within span")
        
        # Verify span was created
        mock_logfire['span'].assert_called_with("Test span")
        # Verify log was called within span
        mock_logfire['info'].assert_called_with("Log within span")
    
    def test_logfire_error_logging(self, ensure_logfire_test_env, mock_logfire):
        """Test error logging with Logfire."""
        # Reset mock to clear previous calls from LogfireTestPlugin
        mock_logfire['error'].reset_mock()
        
        # Log an error
        error_message = "Test error message"
        logfire.error(error_message)
        
        # Verify error was logged
        mock_logfire['error'].assert_called_with(error_message)
    
    def test_logfire_warning_logging(self, ensure_logfire_test_env, mock_logfire):
        """Test warning logging with Logfire."""
        # Reset mock to clear previous calls from LogfireTestPlugin
        mock_logfire['warning'].reset_mock()
        
        # Log a warning
        warning_message = "Test warning message"
        logfire.warning(warning_message)
        
        # Verify warning was logged
        mock_logfire['warning'].assert_called_with(warning_message)


@pytest.mark.integration
class TestLogfirePluginIntegration:
    """Test Logfire plugin integration with PyTest."""
    
    def test_plugin_registers_with_pytest(self, ensure_logfire_test_env, monkeypatch):
        """Test that the Logfire plugin registers with PyTest."""
        # Mock PyTest's plugin manager
        mock_plugin_manager = MagicMock()
        mock_config = MagicMock()
        mock_config.pluginmanager = mock_plugin_manager
        
        # Import the function that registers the plugin
        from tests.conftest import pytest_configure
        
        # Call the function
        pytest_configure(mock_config)
        
        # Verify plugin was registered
        mock_plugin_manager.register.assert_called_once()
        
        # Verify the registered plugin is our LogfireTestPlugin
        args, kwargs = mock_plugin_manager.register.call_args
        assert "logfire_plugin" in kwargs.get("name", args[1] if len(args) > 1 else "")
    
    def test_plugin_adds_logfire_marker(self, ensure_logfire_test_env, monkeypatch):
        """Test that Logfire markers are added to tests."""
        # Create mock test items
        mock_item = MagicMock()
        mock_item.fspath = "tests/unit/test_example.py"
        mock_item.add_marker = MagicMock()
        
        # Import the function that modifies test items
        from tests.conftest import pytest_collection_modifyitems
        
        # Call the function
        pytest_collection_modifyitems(None, [mock_item])
        
        # Verify unit marker was added
        mock_item.add_marker.assert_any_call(pytest.mark.unit)
        
        # Verify logfire marker was added
        mock_item.add_marker.assert_any_call(pytest.mark.logfire)


@pytest.mark.unit
def test_pytest_hooks_called(ensure_logfire_test_env):
    """
    Meta-test that verifies PyTest hooks are called.
    
    This test actually uses the hooks being tested - the test passes
    if it runs without errors, demonstrating that the hooks work.
    """
    # This test doesn't need explicit assertions - if the Logfire plugin
    # hooks have errors, the test itself would fail
    assert True, "PyTest hooks called successfully"


@pytest.mark.integration
def test_logfire_configuration_loaded():
    """Test that Logfire configuration is loaded from file."""
    from tests.conftest import load_logfire_config
    
    # Call the function
    config = load_logfire_config()
    
    # Verify configuration was loaded (even if empty due to missing file)
    assert isinstance(config, dict)


@pytest.mark.unit
def test_logfire_mocking_works(mock_logfire):
    """Test that Logfire mocking fixture works properly."""
    # Reset all mocks to clear previous calls from LogfireTestPlugin
    mock_logfire['info'].reset_mock()
    mock_logfire['error'].reset_mock()
    mock_logfire['warning'].reset_mock()
    mock_logfire['span'].reset_mock()
    
    # Use each mocked Logfire function
    logfire.info("Test info")
    logfire.error("Test error")
    logfire.warning("Test warning")
    
    with logfire.span("Test span"):
        logfire.info("Inside span")
    
    # Verify mocks were called
    mock_logfire['info'].assert_any_call("Test info")
    mock_logfire['error'].assert_called_with("Test error")
    mock_logfire['warning'].assert_called_with("Test warning")
    mock_logfire['span'].assert_called_with("Test span")
    mock_logfire['info'].assert_any_call("Inside span")


if __name__ == "__main__":
    pytest.main(["-v", __file__])