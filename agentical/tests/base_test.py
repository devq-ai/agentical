"""
Base Test Classes for Agentical Test Suite

This module provides base test classes that can be extended for different types of tests
(unit, integration, end-to-end) with appropriate fixtures and utilities pre-configured.

Following DevQ.ai testing standards, these base classes implement common test patterns,
logging integration, and assertion helpers to ensure consistent and comprehensive testing.
"""

import asyncio
import json
import os
import pytest
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

import logfire
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from agentical.core.exceptions import AgenticalError


class BaseAgenticalTest(ABC):
    """Base class for all Agentical tests with common utilities and fixtures."""
    
    @pytest.fixture(autouse=True)
    def _setup_base_test(self, request):
        """Automatically setup base test environment."""
        self.test_name = request.node.name
        self.test_class = request.node.cls.__name__ if request.node.cls else None
        self.test_module = request.node.module.__name__
        
        with logfire.span("Test setup", 
                         test_name=self.test_name, 
                         test_class=self.test_class,
                         test_module=self.test_module):
            logfire.info("Starting test", 
                        test_name=self.test_name, 
                        test_class=self.test_class)
    
    def assert_status_code(self, response: Response, expected_status: int):
        """Assert that response has the expected status code."""
        assert response.status_code == expected_status, (
            f"Expected status code {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )
    
    def assert_json_response(self, response: Response):
        """Assert that response is valid JSON."""
        try:
            response.json()
        except Exception as e:
            pytest.fail(f"Response is not valid JSON: {e}. Response: {response.text}")
    
    def assert_field_in_response(self, response: Response, field: str):
        """Assert that field exists in JSON response."""
        data = response.json()
        assert field in data, f"Field '{field}' not found in response. Response: {data}"
    
    def assert_value_in_response(self, response: Response, field: str, expected_value: Any):
        """Assert that field has expected value in JSON response."""
        data = response.json()
        assert field in data, f"Field '{field}' not found in response. Response: {data}"
        assert data[field] == expected_value, (
            f"Expected '{field}' to be {expected_value}, got {data[field]}. Response: {data}"
        )
    
    def assert_exception_raised(self, exception_type, callable_obj, *args, **kwargs):
        """Assert that callable raises specified exception."""
        with pytest.raises(exception_type) as excinfo:
            callable_obj(*args, **kwargs)
        return excinfo.value
    
    def assert_logfire_logged(self, mock_logfire, level: str, message: str):
        """Assert that Logfire logged specified message at level."""
        calls = mock_logfire.calls_for_level(level)
        assert any(message in call.args[0] for call in calls), (
            f"Expected Logfire to log '{message}' at level '{level}', "
            f"but found only: {[call.args[0] for call in calls]}"
        )
    
    def assert_performance(self, func: Callable, max_time_ms: int, *args, **kwargs):
        """Assert that function executes within specified time."""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time_ms = (time.time() - start_time) * 1000
        
        assert execution_time_ms <= max_time_ms, (
            f"Function took {execution_time_ms:.2f}ms to execute, "
            f"which exceeds the maximum allowed time of {max_time_ms}ms"
        )
        
        return result, execution_time_ms


class BaseUnitTest(BaseAgenticalTest):
    """Base class for unit tests with appropriate fixtures and utilities."""
    
    @pytest.fixture(autouse=True)
    def _setup_unit_test(self, mock_logfire, test_data_factory):
        """Automatically setup unit test environment."""
        self.mock_logfire = mock_logfire
        self.test_data_factory = test_data_factory
    
    def assert_function_called_with(self, mock_function, *args, **kwargs):
        """Assert that mock function was called with specified arguments."""
        mock_function.assert_called_with(*args, **kwargs)
    
    def assert_function_called(self, mock_function, times: Optional[int] = None):
        """Assert that mock function was called a specific number of times."""
        if times is not None:
            assert mock_function.call_count == times, (
                f"Expected function to be called {times} times, "
                f"but was called {mock_function.call_count} times"
            )
        else:
            assert mock_function.called, "Expected function to be called, but it was not"


class BaseIntegrationTest(BaseAgenticalTest):
    """Base class for integration tests with database and API client fixtures."""
    
    @pytest.fixture(autouse=True)
    def _setup_integration_test(self, db_session, test_client, test_data_factory):
        """Automatically setup integration test environment."""
        self.db = db_session
        self.client = test_client
        self.test_data_factory = test_data_factory
    
    def assert_db_record_exists(self, model_class, **filters):
        """Assert that a database record exists matching the filters."""
        record = self.db.query(model_class).filter_by(**filters).first()
        assert record is not None, (
            f"Expected to find a {model_class.__name__} record matching filters: {filters}, "
            f"but none was found"
        )
        return record
    
    def assert_db_record_count(self, model_class, expected_count: int, **filters):
        """Assert that a specific number of database records exist matching the filters."""
        count = self.db.query(model_class).filter_by(**filters).count()
        assert count == expected_count, (
            f"Expected to find {expected_count} {model_class.__name__} records matching filters: {filters}, "
            f"but found {count}"
        )
    
    def assert_api_success(self, response: Response):
        """Assert that API response indicates success."""
        self.assert_status_code(response, 200)
        self.assert_json_response(response)
    
    def assert_api_created(self, response: Response):
        """Assert that API response indicates successful creation."""
        self.assert_status_code(response, 201)
        self.assert_json_response(response)
    
    def assert_api_error(self, response: Response, expected_status: int = 400):
        """Assert that API response indicates an error."""
        self.assert_status_code(response, expected_status)
        self.assert_json_response(response)
        self.assert_field_in_response(response, "detail")


class BaseAsyncIntegrationTest(BaseIntegrationTest):
    """Base class for async integration tests with async client and database session."""
    
    @pytest.fixture(autouse=True)
    def _setup_async_integration_test(self, async_client, async_db_session):
        """Automatically setup async integration test environment."""
        self.async_client = async_client
        self.async_db = async_db_session
    
    async def assert_async_db_record_exists(self, model_class, **filters):
        """Assert that a database record exists matching the filters (async version)."""
        query = await self.async_db.execute(model_class.__table__.select().filter_by(**filters))
        record = query.first()
        assert record is not None, (
            f"Expected to find a {model_class.__name__} record matching filters: {filters}, "
            f"but none was found"
        )
        return record
    
    async def assert_api_success_async(self, response: Response):
        """Assert that API response indicates success (async version)."""
        self.assert_status_code(response, 200)
        self.assert_json_response(response)


class BaseE2ETest(BaseAgenticalTest):
    """Base class for end-to-end tests with comprehensive test environment."""
    
    @pytest.fixture(autouse=True)
    def _setup_e2e_test(self, test_client, db_session, test_environment, test_data_factory):
        """Automatically setup end-to-end test environment."""
        self.client = test_client
        self.db = db_session
        self.test_environment = test_environment
        self.test_data_factory = test_data_factory
    
    def assert_workflow_completed(self, workflow_id: str, timeout_seconds: int = 30):
        """Assert that a workflow completes successfully within the timeout period."""
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            response = self.client.get(f"/api/v1/workflows/{workflow_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "completed":
                    return data
                elif data.get("status") == "failed":
                    pytest.fail(f"Workflow failed: {data.get('error')}")
            time.sleep(0.5)
        
        pytest.fail(f"Workflow did not complete within {timeout_seconds} seconds")
    
    def assert_agent_response_valid(self, response: Response):
        """Assert that an agent response is valid."""
        self.assert_status_code(response, 200)
        self.assert_json_response(response)
        self.assert_field_in_response(response, "agent_id")
        self.assert_field_in_response(response, "response")
        
        # Additional validation for agent response format
        data = response.json()
        assert isinstance(data["response"], dict), "Agent response should be a dictionary"
        assert "content" in data["response"], "Agent response should contain 'content'"


class BasePerformanceTest(BaseIntegrationTest):
    """Base class for performance tests with timing and resource monitoring."""
    
    @pytest.fixture(autouse=True)
    def _setup_performance_test(self, performance_monitor):
        """Automatically setup performance test environment."""
        self.performance_monitor = performance_monitor
        self.performance_monitor.start()
        yield
        self.performance_monitor.stop()
    
    def assert_response_time(self, response: Response, max_time_ms: int):
        """Assert that API response time is within acceptable limits."""
        assert hasattr(response, "elapsed"), "Response object has no elapsed time information"
        elapsed_ms = response.elapsed.total_seconds() * 1000
        assert elapsed_ms <= max_time_ms, (
            f"API response took {elapsed_ms:.2f}ms, which exceeds the maximum "
            f"allowed time of {max_time_ms}ms"
        )
    
    def assert_query_count(self, max_queries: int):
        """Assert that the number of database queries is within acceptable limits."""
        query_count = self.performance_monitor.get_query_count()
        assert query_count <= max_queries, (
            f"Test executed {query_count} database queries, which exceeds the maximum "
            f"allowed count of {max_queries}"
        )
    
    def assert_memory_usage(self, max_mb: float):
        """Assert that memory usage is within acceptable limits."""
        memory_usage_mb = self.performance_monitor.get_memory_usage_mb()
        assert memory_usage_mb <= max_mb, (
            f"Test used {memory_usage_mb:.2f}MB of memory, which exceeds the maximum "
            f"allowed usage of {max_mb}MB"
        )


# Example usage:
"""
class TestHealthEndpoints(BaseIntegrationTest):
    def test_health_check(self):
        response = self.client.get("/api/v1/health")
        self.assert_api_success(response)
        self.assert_field_in_response(response, "status")
        self.assert_field_in_response(response, "services")
        
    def test_readiness_probe(self):
        response = self.client.get("/api/v1/health/readiness")
        self.assert_api_success(response)
        self.assert_value_in_response(response, "status", "ready")
"""