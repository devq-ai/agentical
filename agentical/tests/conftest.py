"""
Agentical Test Configuration and Fixtures

This module provides comprehensive test configuration and fixtures for the Agentical
framework, integrating PyTest with Logfire observability and following DevQ.ai
testing standards.

Key Features:
- Logfire integration for test observability and monitoring
- Database fixtures with proper isolation and cleanup
- FastAPI test client with async support
- Custom PyTest plugin for enhanced reporting
- Test utilities and common fixtures
- Performance monitoring and resource tracking
- Comprehensive error handling and logging

Test Environment:
- Minimum 90% code coverage requirement
- Build-to-test development approach
- Proper test isolation and cleanup
- Real-time test monitoring via Logfire
"""

import os
import sys
import asyncio
import logging
import tempfile
import json
import pytest
import logfire
from pathlib import Path
from typing import Dict, Any, AsyncGenerator, Generator, List, Optional
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
import traceback
from uuid import uuid4

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure test environment variables
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["LOGFIRE_ENVIRONMENT"] = "test"

# Configure test logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Load Logfire configuration from file
def load_logfire_config():
    """Load Logfire configuration from file, with environment variable substitution."""
    config_path = project_root / ".logfire" / "test_config.json"
    if not config_path.exists():
        logger.warning(f"Logfire config file not found: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = json.loads(f.read())
        
        # Substitute environment variables
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                config[key] = os.getenv(env_var, "")
        
        return config
    except Exception as e:
        logger.warning(f"Failed to load Logfire config: {e}")
        return {}

# Configure Logfire for test observability
try:
    # Get token from environment or config
    token = os.getenv("LOGFIRE_TOKEN")
    
    # Initialize with basic config
    logfire_config = {
        "token": token,
        "project_name": os.getenv("LOGFIRE_PROJECT_NAME", "agentical-test"),
        "service_name": os.getenv("LOGFIRE_SERVICE_NAME", "agentical-test-suite"),
        "environment": "test"
    }
    
    # Update with file config if available
    file_config = load_logfire_config()
    if file_config:
        logfire_config.update(file_config)
    
    # Configure Logfire
    if token:
        logfire.configure(**logfire_config)
        logger.info("Logfire configured for test observability")
    else:
        logger.warning("Logfire token not found. Test observability disabled.")
        os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "1"
except Exception as e:
    logger.warning(f"Failed to configure Logfire: {e}")
    os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "1"


# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_agentical.db"
TEST_DATABASE_URL_MEMORY = "sqlite:///:memory:"


class LogfireTestPlugin:
    """Custom PyTest plugin for Logfire integration and enhanced test reporting.
    
    This plugin hooks into PyTest's event system to capture test execution events
    and send them to Logfire for observability and monitoring. It provides detailed
    information about test execution, including setup, teardown, and results.
    
    Features:
    - Test session start/finish tracking
    - Individual test setup/execution/teardown monitoring
    - Test outcome reporting (passed, failed, skipped)
    - Error and exception reporting
    - Test duration metrics
    - Test suite statistics
    - Marker-based test categorization
    - Coverage reporting integration
    """
    
    def __init__(self):
        self.test_start_time = None
        self.session_start_time = None
        self.test_results = []
        self.test_contexts = {}
        self.session_id = str(uuid4())
        self.enabled = os.getenv("LOGFIRE_ENABLED", "true").lower() == "true"
        self.verbose = os.getenv("LOGFIRE_TEST_VERBOSE", "false").lower() == "true"
        self.capture_logs = os.getenv("LOGFIRE_CAPTURE_LOGS", "true").lower() == "true"
        self.include_source = os.getenv("LOGFIRE_INCLUDE_SOURCE", "false").lower() == "true"
        
    def pytest_sessionstart(self, session):
        """Called when test session starts."""
        if not self.enabled:
            return
            
        self.session_start_time = datetime.now(timezone.utc)
        
        # Gather environment information
        env_info = {
            "python_version": sys.version,
            "pytest_version": pytest.__version__,
            "os_platform": sys.platform,
            "test_environment": os.getenv("ENVIRONMENT", "test"),
            "debug_mode": os.getenv("DEBUG", "false")
        }
        
        # Gather test collection information
        collection_info = {
            "total_collected": getattr(session, 'testscollected', 0),
            "session_id": self.session_id,
            "test_directory": str(project_root / "tests"),
            "timestamp": self.session_start_time.isoformat()
        }
        
        with logfire.span("Test Session Start"):
            logfire.info(
                "Starting Agentical test session",
                **collection_info,
                **env_info
            )
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Called when test session finishes."""
        if not self.enabled:
            return
            
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.session_start_time).total_seconds()
        
        # Collect session statistics
        outcomes = {
            "passed": len([r for r in self.test_results if r['outcome'] == 'passed']),
            "failed": len([r for r in self.test_results if r['outcome'] == 'failed']),
            "skipped": len([r for r in self.test_results if r['outcome'] == 'skipped']),
            "xfailed": len([r for r in self.test_results if r['outcome'] == 'xfailed']),
            "xpassed": len([r for r in self.test_results if r['outcome'] == 'xpassed']),
            "error": len([r for r in self.test_results if r['outcome'] == 'error'])
        }
        
        # Calculate pass rate
        total_executed = outcomes["passed"] + outcomes["failed"]
        pass_rate = (outcomes["passed"] / total_executed * 100) if total_executed > 0 else 0
        
        # Get coverage information if available
        coverage_info = {}
        try:
            import coverage
            cov = coverage.Coverage()
            if hasattr(cov, '_harvest_data'):
                cov._harvest_data()
                if hasattr(cov, 'get_data') and callable(cov.get_data):
                    data = cov.get_data()
                    if hasattr(data, 'summary') and callable(data.summary):
                        coverage_info["total_coverage"] = data.summary()["total_coverage"]
        except (ImportError, AttributeError):
            pass
        
        # Aggregate test durations by type
        test_types = {}
        for result in self.test_results:
            test_path = result['test_name'].split('::')[0]
            test_type = "unknown"
            if "unit" in test_path:
                test_type = "unit"
            elif "integration" in test_path:
                test_type = "integration"
            elif "e2e" in test_path:
                test_type = "e2e"
                
            if test_type not in test_types:
                test_types[test_type] = {"count": 0, "duration": 0, "passed": 0, "failed": 0}
                
            test_types[test_type]["count"] += 1
            test_types[test_type]["duration"] += result.get('duration', 0)
            if result['outcome'] == 'passed':
                test_types[test_type]["passed"] += 1
            elif result['outcome'] == 'failed':
                test_types[test_type]["failed"] += 1
        
        with logfire.span("Test Session Complete"):
            logfire.info(
                "Test session completed",
                duration=duration,
                exit_status=exitstatus,
                exit_status_desc=self._get_exit_status_description(exitstatus),
                session_id=self.session_id,
                timestamp=end_time.isoformat(),
                pass_rate=pass_rate,
                tests_passed=outcomes["passed"],
                tests_failed=outcomes["failed"],
                tests_skipped=outcomes["skipped"],
                tests_xfailed=outcomes["xfailed"],
                tests_xpassed=outcomes["xpassed"],
                tests_error=outcomes["error"],
                total_tests=len(self.test_results),
                test_types=test_types,
                **coverage_info
            )
            
            # Log detailed result summary if verbose
            if self.verbose and self.test_results:
                logfire.info(
                    "Test results summary",
                    session_id=self.session_id,
                    results=self.test_results[:100]  # Limit to avoid excessive data
                )
    
    def _get_exit_status_description(self, exitstatus):
        """Convert PyTest exit status to human-readable description."""
        status_map = {
            0: "All tests passed",
            1: "Tests failed",
            2: "Test execution interrupted",
            3: "Internal pytest error",
            4: "Usage error",
            5: "No tests collected"
        }
        return status_map.get(exitstatus, f"Unknown exit status: {exitstatus}")
    
    def pytest_runtest_setup(self, item):
        """Called before each test runs."""
        if not self.enabled:
            return
            
        self.test_start_time = datetime.now(timezone.utc)
        test_id = item.nodeid
        
        # Store test context for later reference
        self.test_contexts[test_id] = {
            "start_time": self.test_start_time,
            "markers": [mark.name for mark in item.iter_markers()],
            "name": item.name,
            "file": str(item.fspath),
            "line": item.function.__code__.co_firstlineno if hasattr(item, 'function') else None,
            "description": item.function.__doc__ if hasattr(item, 'function') else None,
            "phase": "setup"
        }
        
        # Get test source code if enabled
        if self.include_source and hasattr(item, 'function'):
            try:
                import inspect
                source = inspect.getsource(item.function)
                self.test_contexts[test_id]["source"] = source
            except Exception:
                pass
        
        with logfire.span(f"Test Setup: {item.name}"):
            logfire.info(
                "Setting up test",
                test_id=test_id,
                test_name=item.name,
                test_file=str(item.fspath),
                test_markers=[mark.name for mark in item.iter_markers()],
                session_id=self.session_id,
                test_module=item.module.__name__ if hasattr(item, 'module') else None
            )
    
    def pytest_runtest_call(self, item):
        """Called during test execution."""
        if not self.enabled:
            return
            
        test_id = item.nodeid
        if test_id in self.test_contexts:
            self.test_contexts[test_id]["phase"] = "call"
        
        # Capture function parameters if available
        params = {}
        if hasattr(item, '_obj') and hasattr(item._obj, 'funcargs'):
            for name, value in item._obj.funcargs.items():
                # Skip certain parameter types that might cause serialization issues
                if name not in ['request', 'monkeypatch', 'caplog', 'tmpdir']:
                    try:
                        # Try to get a string representation of the parameter
                        params[name] = str(value)
                    except Exception:
                        params[name] = f"<{type(value).__name__}>"
        
        with logfire.span(f"Test Execution: {item.name}"):
            logfire.info(
                "Executing test",
                test_id=test_id,
                test_name=item.name,
                test_function=item.function.__name__ if hasattr(item, 'function') else None,
                session_id=self.session_id,
                parameters=params if params else None
            )
    
    def pytest_runtest_teardown(self, item):
        """Called after each test completes."""
        if not self.enabled:
            return
            
        test_id = item.nodeid
        end_time = datetime.now(timezone.utc)
        
        if test_id in self.test_contexts:
            start_time = self.test_contexts[test_id].get("start_time", self.test_start_time)
            duration = (end_time - start_time).total_seconds()
            self.test_contexts[test_id]["duration"] = duration
            self.test_contexts[test_id]["phase"] = "teardown"
        else:
            duration = (end_time - self.test_start_time).total_seconds()
        
        with logfire.span(f"Test Teardown: {item.name}"):
            logfire.info(
                "Tearing down test",
                test_id=test_id,
                test_name=item.name,
                duration=duration,
                session_id=self.session_id,
                timestamp=end_time.isoformat()
            )
    
    def pytest_runtest_logreport(self, report):
        """Called for each test result."""
        if not self.enabled:
            return
            
        test_id = report.nodeid
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Only process the call phase for test results
        if report.when == "call":
            # Prepare the test result data
            test_result = {
                'test_id': test_id,
                'test_name': report.nodeid,
                'outcome': report.outcome,
                'duration': report.duration,
                'timestamp': timestamp,
                'session_id': self.session_id
            }
            
            # Add context information if available
            if test_id in self.test_contexts:
                test_result['markers'] = self.test_contexts[test_id].get('markers', [])
                test_result['description'] = self.test_contexts[test_id].get('description')
                
            # Add failure information if test failed
            if report.outcome == 'failed':
                error_message = str(report.longrepr)
                test_result['error'] = error_message
                
                # Extract exception type and message if possible
                try:
                    if hasattr(report, 'longrepr') and hasattr(report.longrepr, 'reprcrash'):
                        test_result['exception_type'] = report.longrepr.reprcrash.message.split(':')[0]
                        test_result['exception_line'] = report.longrepr.reprcrash.lineno
                except Exception:
                    pass
            
            # Store the test result
            self.test_results.append(test_result)
            
            # Log to Logfire with appropriate level
            with logfire.span(f"Test Result: {test_id}"):
                if report.outcome == 'passed':
                    logfire.info(
                        "Test passed",
                        test_id=test_id,
                        test_name=report.nodeid,
                        duration=report.duration,
                        session_id=self.session_id,
                        timestamp=timestamp,
                        markers=test_result.get('markers', [])
                    )
                elif report.outcome == 'failed':
                    logfire.error(
                        "Test failed",
                        test_id=test_id,
                        test_name=report.nodeid,
                        duration=report.duration,
                        error=test_result.get('error', ''),
                        exception_type=test_result.get('exception_type'),
                        exception_line=test_result.get('exception_line'),
                        session_id=self.session_id,
                        timestamp=timestamp,
                        markers=test_result.get('markers', [])
                    )
                else:
                    logfire.warning(
                        f"Test {report.outcome}",
                        test_id=test_id,
                        test_name=report.nodeid,
                        duration=report.duration,
                        session_id=self.session_id,
                        timestamp=timestamp,
                        markers=test_result.get('markers', [])
                    )
        
        # Log setup/teardown failures separately
        elif report.outcome == 'failed':
            error_message = str(report.longrepr)
            
            with logfire.span(f"Test {report.when.capitalize()} Failure: {test_id}"):
                logfire.error(
                    f"Test {report.when} failed",
                    test_id=test_id,
                    test_name=report.nodeid,
                    phase=report.when,
                    error=error_message,
                    session_id=self.session_id,
                    timestamp=timestamp
                )


    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        """Called at the end of the test session to add information to the terminal summary."""
        if not self.enabled:
            return
            
        # Get coverage data if available
        if hasattr(terminalreporter, 'coverage'):
            try:
                coverage_data = terminalreporter.coverage
                with logfire.span("Coverage Report"):
                    logfire.info(
                        "Test coverage report",
                        coverage_total=getattr(coverage_data, 'total_coverage', None),
                        coverage_missing=getattr(coverage_data, 'missing_lines', None),
                        session_id=self.session_id
                    )
            except Exception as e:
                logger.debug(f"Failed to log coverage data: {e}")
    
    def pytest_collectreport(self, report):
        """Called after collection is completed."""
        if not self.enabled:
            return
            
        if report.failed:
            with logfire.span("Collection Failure"):
                logfire.error(
                    "Test collection failed",
                    error=str(report.longrepr),
                    session_id=self.session_id
                )
    
    def pytest_exception_interact(self, node, call, report):
        """Called when an exception was raised during a test invocation."""
        if not self.enabled:
            return
            
        if report.failed:
            # Get extended traceback information
            excinfo = call.excinfo
            formatted_traceback = "".join(traceback.format_exception(
                excinfo.type, excinfo.value, excinfo.tb
            ))
            
            with logfire.span("Test Exception"):
                logfire.error(
                    "Exception during test execution",
                    test_id=node.nodeid,
                    exception_type=excinfo.typename,
                    exception_value=str(excinfo.value),
                    traceback=formatted_traceback,
                    session_id=self.session_id
                )


# Register the custom plugin
def pytest_configure(config):
    """Configure PyTest with custom plugins."""
    # Check if Logfire reporting is enabled
    enabled = os.getenv("LOGFIRE_ENABLED", "true").lower() == "true"
    
    # Register the plugin
    plugin = LogfireTestPlugin()
    config.pluginmanager.register(plugin, "logfire_plugin")
    
    # Set command-line options for the plugin
    if hasattr(config.option, 'logfire_verbose'):
        plugin.verbose = config.option.logfire_verbose
    if hasattr(config.option, 'logfire_capture_logs'):
        plugin.capture_logs = config.option.logfire_capture_logs
    if hasattr(config.option, 'logfire_include_source'):
        plugin.include_source = config.option.logfire_include_source
    
    # Register the Logfire marker
    config.addinivalue_line("markers", "logfire: mark test to be monitored by Logfire")


def pytest_addoption(parser):
    """Add Logfire-specific command line options to pytest."""
    group = parser.getgroup("logfire", "Logfire Observability")
    group.addoption(
        "--logfire-enabled",
        action="store_true",
        default=True,
        help="Enable Logfire observability for tests"
    )
    group.addoption(
        "--logfire-verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging to Logfire"
    )
    group.addoption(
        "--logfire-capture-logs",
        action="store_true",
        default=True,
        help="Capture logs during test execution"
    )
    group.addoption(
        "--logfire-include-source",
        action="store_true",
        default=False,
        help="Include test source code in Logfire logs"
    )

def pytest_collection_modifyitems(config, items):
    """Modify collected test items to add appropriate markers."""
    # Get plugin configuration
    enabled = os.getenv("LOGFIRE_ENABLED", "true").lower() == "true"
    if not enabled:
        return
        
    for item in items:
        # Auto-mark tests based on their location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add logfire marker to all tests for filtering
        item.add_marker(pytest.mark.logfire)
        
        # Mark slow tests
        if hasattr(item.function, 'pytestmark'):
            markers = [mark.name for mark in item.function.pytestmark]
            if 'slow' not in markers and 'e2e' in markers:
                item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_engine():
    """Create a test database engine for the session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Log database operations for testing
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if os.getenv("LOG_SQL_QUERIES", "false").lower() == "true":
            logger.debug(f"SQL Query: {statement}")
    
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_database_engine):
    """Create a database session for testing with proper cleanup."""
    # Import here to avoid circular imports
    try:
        from agentical.db import Base
        Base.metadata.create_all(bind=test_database_engine)
    except ImportError:
        logger.warning("Database models not found, skipping table creation")
    
    SessionLocal = sessionmaker(bind=test_database_engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        
        # Clean up database tables
        try:
            from agentical.db import Base
            Base.metadata.drop_all(bind=test_database_engine)
        except ImportError:
            pass


@pytest.fixture
async def async_db_session(test_database_engine):
    """Create an async database session for testing."""
    try:
        from agentical.db import Base, AsyncSessionLocal
        
        # Create tables
        Base.metadata.create_all(bind=test_database_engine)
        
        async with AsyncSessionLocal() as session:
            yield session
            await session.rollback()
            
        # Clean up
        Base.metadata.drop_all(bind=test_database_engine)
    except ImportError:
        logger.warning("Async database session not available")
        yield None


@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    try:
        from agentical.main import app
        
        # Override database dependency for testing
        def override_get_db():
            try:
                from agentical.db import SessionLocal
                db = SessionLocal()
                yield db
            finally:
                db.close()
        
        # Apply dependency override if available
        try:
            from agentical.main import get_db
            app.dependency_overrides[get_db] = override_get_db
        except ImportError:
            pass
        
        with TestClient(app) as client:
            yield client
            
        # Clear overrides
        app.dependency_overrides.clear()
        
    except ImportError:
        logger.warning("FastAPI app not available for testing")
        yield None


@pytest.fixture
async def async_client():
    """Create an async HTTP client for testing."""
    try:
        from agentical.main import app
        
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            yield client
    except ImportError:
        logger.warning("FastAPI app not available for async testing")
        yield None


@pytest.fixture
def mock_logfire():
    """Mock Logfire for tests that don't need real observability."""
    with patch('logfire.info') as mock_info, \
         patch('logfire.error') as mock_error, \
         patch('logfire.warning') as mock_warning, \
         patch('logfire.span') as mock_span:
        
        # Create a context manager mock for spans
        span_context = MagicMock()
        span_context.__enter__ = MagicMock(return_value=span_context)
        span_context.__exit__ = MagicMock(return_value=False)
        mock_span.return_value = span_context
        
        yield {
            'info': mock_info,
            'error': mock_error,
            'warning': mock_warning,
            'span': mock_span
        }


@pytest.fixture
def test_data_factory():
    """Factory for creating test data."""
    class TestDataFactory:
        @staticmethod
        def create_user_data(**kwargs):
            """Create test user data."""
            default_data = {
                "email": "test@example.com",
                "username": "testuser",
                "is_active": True
            }
            return {**default_data, **kwargs}
        
        @staticmethod
        def create_agent_data(**kwargs):
            """Create test agent data."""
            default_data = {
                "name": "Test Agent",
                "description": "A test agent for unit testing",
                "capabilities": ["test", "mock"],
                "config": {"max_iterations": 10}
            }
            return {**default_data, **kwargs}
        
        @staticmethod
        def create_workflow_data(**kwargs):
            """Create test workflow data."""
            default_data = {
                "name": "Test Workflow",
                "description": "A test workflow",
                "steps": [
                    {"name": "step1", "action": "test_action"},
                    {"name": "step2", "action": "another_action"}
                ]
            }
            return {**default_data, **kwargs}
    
    return TestDataFactory()


@pytest.fixture
def performance_monitor():
    """Monitor test performance and resource usage."""
    import psutil
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.process = psutil.Process()
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = self.process.memory_info().rss
            
        def stop(self):
            if self.start_time is None:
                return None
                
            duration = time.time() - self.start_time
            memory_used = self.process.memory_info().rss - self.start_memory
            
            return {
                'duration': duration,
                'memory_used_mb': memory_used / 1024 / 1024,
                'cpu_percent': self.process.cpu_percent()
            }
    
    monitor = PerformanceMonitor()
    monitor.start()
    yield monitor
    
    # Log performance metrics
    metrics = monitor.stop()
    if metrics:
        with logfire.span("Test Performance Metrics"):
            logfire.info(
                "Test performance completed",
                **metrics
            )


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_external_services():
    """Mock external services commonly used in tests."""
    with patch('httpx.AsyncClient') as mock_httpx, \
         patch('requests.get') as mock_requests_get, \
         patch('requests.post') as mock_requests_post:
        
        # Configure mock responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.text = '{"status": "success"}'
        
        mock_requests_get.return_value = mock_response
        mock_requests_post.return_value = mock_response
        
        # Configure async client mock
        mock_async_response = Mock()
        mock_async_response.status_code = 200
        mock_async_response.json = Mock(return_value={"status": "success"})
        
        mock_httpx_instance = Mock()
        mock_httpx_instance.get = Mock(return_value=mock_async_response)
        mock_httpx_instance.post = Mock(return_value=mock_async_response)
        mock_httpx.return_value.__aenter__ = Mock(return_value=mock_httpx_instance)
        mock_httpx.return_value.__aexit__ = Mock(return_value=False)
        
        yield {
            'httpx': mock_httpx,
            'requests_get': mock_requests_get,
            'requests_post': mock_requests_post,
            'async_client': mock_httpx_instance
        }


@pytest.fixture(autouse=True)
def test_environment():
    """Automatically set up test environment variables for all tests."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "DATABASE_URL": TEST_DATABASE_URL,
        "LOGFIRE_ENVIRONMENT": "test",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30"
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Custom assertion helpers
def assert_response_ok(response, expected_status=200):
    """Assert that a response is successful with optional status check."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"


def assert_valid_json(response):
    """Assert that a response contains valid JSON."""
    try:
        response.json()
    except ValueError:
        pytest.fail(f"Response does not contain valid JSON: {response.text}")


def assert_logfire_called(mock_logfire, method='info', contains=None):
    """Assert that Logfire was called with expected parameters."""
    mock_method = mock_logfire[method]
    assert mock_method.called, f"Logfire {method} was not called"
    
    if contains:
        found = False
        for call_args in mock_method.call_args_list:
            if any(contains in str(arg) for arg in call_args[0]):
                found = True
                break
        assert found, f"Logfire {method} was not called with message containing '{contains}'"


# Export common testing utilities
__all__ = [
    "pytest",
    "logfire",
    "TestClient",
    "AsyncClient",
    "Mock",
    "patch",
    "MagicMock",
    "assert_response_ok",
    "assert_valid_json", 
    "assert_logfire_called"
]