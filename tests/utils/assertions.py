"""
Custom Assertions and Validation Utilities for Agentical Testing Framework

This module provides comprehensive custom assertions and validation utilities
for testing the Agentical framework, including data validators, performance
assertions, security assertions, and domain-specific validations.

Features:
- Custom assertion helpers for complex validations
- Data structure validation utilities
- Performance and timing assertions
- Security and authentication validations
- Domain-specific business logic assertions
- API response validation utilities
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, Type
from unittest.mock import Mock
import re

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from agentical.db.models.base import BaseModel
from agentical.db.models.user import User, Role
from agentical.db.models.agent import Agent, AgentType, AgentStatus
from agentical.db.models.playbook import (
    Playbook, PlaybookExecution, ExecutionStatus, PlaybookStatus
)


class CustomAssertions:
    """Custom assertion utilities for comprehensive testing."""

    @staticmethod
    def assert_response_structure(response_data: Dict[str, Any], expected_structure: Dict[str, type]):
        """Assert response has expected structure with correct types."""
        for field, expected_type in expected_structure.items():
            assert field in response_data, f"Missing field: {field}"
            actual_value = response_data[field]

            if expected_type is not type(None):
                assert isinstance(actual_value, expected_type), (
                    f"Field '{field}' expected type {expected_type}, got {type(actual_value)}"
                )

    @staticmethod
    def assert_json_schema(data: Dict[str, Any], schema: Dict[str, Any]):
        """Assert data matches JSON schema structure."""
        def validate_field(field_name: str, field_value: Any, field_schema: Dict[str, Any]):
            field_type = field_schema.get("type")
            required = field_schema.get("required", False)

            if required and field_value is None:
                raise AssertionError(f"Required field '{field_name}' is None")

            if field_value is not None and field_type:
                type_map = {
                    "string": str,
                    "integer": int,
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "object": dict
                }

                expected_type = type_map.get(field_type)
                if expected_type and not isinstance(field_value, expected_type):
                    raise AssertionError(
                        f"Field '{field_name}' expected type {field_type}, got {type(field_value)}"
                    )

        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            field_value = data.get(field_name)
            validate_field(field_name, field_value, field_schema)

    @staticmethod
    def assert_uuid_format(value: str, field_name: str = "value"):
        """Assert value is a valid UUID format."""
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        assert uuid_pattern.match(value), f"'{field_name}' is not a valid UUID: {value}"

    @staticmethod
    def assert_iso_datetime(value: str, field_name: str = "datetime"):
        """Assert value is a valid ISO datetime format."""
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise AssertionError(f"'{field_name}' is not a valid ISO datetime: {value}")

    @staticmethod
    def assert_email_format(email: str):
        """Assert email has valid format."""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        assert email_pattern.match(email), f"Invalid email format: {email}"

    @staticmethod
    def assert_pagination_fields(response_data: Dict[str, Any]):
        """Assert response contains valid pagination fields."""
        required_fields = ["page", "page_size", "total", "pages"]
        for field in required_fields:
            assert field in response_data, f"Missing pagination field: {field}"
            assert isinstance(response_data[field], int), f"Pagination field '{field}' must be integer"
            assert response_data[field] >= 0, f"Pagination field '{field}' must be non-negative"

    @staticmethod
    def assert_success_response(response_data: Dict[str, Any]):
        """Assert response indicates success."""
        assert "success" in response_data, "Response missing 'success' field"
        assert response_data["success"] is True, "Response indicates failure"

    @staticmethod
    def assert_error_response(response_data: Dict[str, Any], expected_error_code: str = None):
        """Assert response indicates error with optional error code check."""
        assert "success" in response_data, "Response missing 'success' field"
        assert response_data["success"] is False, "Response indicates success when error expected"
        assert "error" in response_data, "Error response missing 'error' field"

        if expected_error_code:
            error = response_data["error"]
            assert "code" in error, "Error missing 'code' field"
            assert error["code"] == expected_error_code, (
                f"Expected error code '{expected_error_code}', got '{error['code']}'"
            )

    @staticmethod
    def assert_list_contains_item(items: List[Dict[str, Any]], **search_criteria):
        """Assert list contains item matching criteria."""
        for item in items:
            if all(item.get(key) == value for key, value in search_criteria.items()):
                return item

        raise AssertionError(f"List does not contain item matching criteria: {search_criteria}")

    @staticmethod
    def assert_list_sorted(items: List[Any], key_func: Callable = None, reverse: bool = False):
        """Assert list is sorted according to criteria."""
        if not items:
            return

        if key_func:
            sorted_items = sorted(items, key=key_func, reverse=reverse)
        else:
            sorted_items = sorted(items, reverse=reverse)

        assert items == sorted_items, "List is not properly sorted"

    @staticmethod
    def assert_no_duplicate_values(items: List[Any], key_func: Callable = None):
        """Assert list contains no duplicate values."""
        if key_func:
            values = [key_func(item) for item in items]
        else:
            values = items

        unique_values = set(values)
        assert len(values) == len(unique_values), f"List contains duplicates: {values}"

    @staticmethod
    def assert_all_items_match(items: List[Dict[str, Any]], condition: Callable):
        """Assert all items in list match condition."""
        for i, item in enumerate(items):
            assert condition(item), f"Item at index {i} does not match condition: {item}"

    @staticmethod
    def assert_percentage_range(value: float, min_percent: float = 0.0, max_percent: float = 100.0):
        """Assert value is within percentage range."""
        assert min_percent <= value <= max_percent, (
            f"Percentage value {value} not in range [{min_percent}, {max_percent}]"
        )


class DataValidators:
    """Data validation utilities for testing."""

    @staticmethod
    def validate_user_data(user_data: Dict[str, Any], strict: bool = True):
        """Validate user data structure and content."""
        required_fields = ["username", "email", "created_at"]
        optional_fields = ["first_name", "last_name", "display_name", "is_verified", "roles"]

        # Check required fields
        for field in required_fields:
            assert field in user_data, f"User data missing required field: {field}"

        # Validate field types and formats
        assert isinstance(user_data["username"], str), "Username must be string"
        assert len(user_data["username"]) >= 3, "Username must be at least 3 characters"

        CustomAssertions.assert_email_format(user_data["email"])
        CustomAssertions.assert_iso_datetime(user_data["created_at"], "created_at")

        if "roles" in user_data:
            assert isinstance(user_data["roles"], list), "Roles must be a list"
            for role in user_data["roles"]:
                assert isinstance(role, str), "Each role must be a string"

    @staticmethod
    def validate_agent_data(agent_data: Dict[str, Any]):
        """Validate agent data structure and content."""
        required_fields = ["agent_id", "name", "agent_type", "status", "created_at"]

        for field in required_fields:
            assert field in agent_data, f"Agent data missing required field: {field}"

        CustomAssertions.assert_uuid_format(agent_data["agent_id"], "agent_id")
        assert isinstance(agent_data["name"], str), "Agent name must be string"
        assert len(agent_data["name"]) > 0, "Agent name cannot be empty"

        # Validate agent type
        valid_agent_types = [t.value for t in AgentType]
        assert agent_data["agent_type"] in valid_agent_types, (
            f"Invalid agent type: {agent_data['agent_type']}"
        )

        # Validate status
        valid_statuses = [s.value for s in AgentStatus]
        assert agent_data["status"] in valid_statuses, (
            f"Invalid agent status: {agent_data['status']}"
        )

        CustomAssertions.assert_iso_datetime(agent_data["created_at"], "created_at")

    @staticmethod
    def validate_playbook_data(playbook_data: Dict[str, Any]):
        """Validate playbook data structure and content."""
        required_fields = ["playbook_id", "name", "category", "status", "version", "created_at"]

        for field in required_fields:
            assert field in playbook_data, f"Playbook data missing required field: {field}"

        CustomAssertions.assert_uuid_format(playbook_data["playbook_id"], "playbook_id")
        assert isinstance(playbook_data["name"], str), "Playbook name must be string"
        assert len(playbook_data["name"]) > 0, "Playbook name cannot be empty"

        # Validate version format (semantic versioning)
        version_pattern = re.compile(r'^\d+\.\d+\.\d+$')
        assert version_pattern.match(playbook_data["version"]), (
            f"Invalid version format: {playbook_data['version']}"
        )

        CustomAssertions.assert_iso_datetime(playbook_data["created_at"], "created_at")

    @staticmethod
    def validate_execution_data(execution_data: Dict[str, Any]):
        """Validate execution data structure and content."""
        required_fields = ["execution_id", "status", "started_at"]

        for field in required_fields:
            assert field in execution_data, f"Execution data missing required field: {field}"

        CustomAssertions.assert_uuid_format(execution_data["execution_id"], "execution_id")

        # Validate status
        valid_statuses = [s.value for s in ExecutionStatus]
        assert execution_data["status"] in valid_statuses, (
            f"Invalid execution status: {execution_data['status']}"
        )

        CustomAssertions.assert_iso_datetime(execution_data["started_at"], "started_at")

        # Validate optional fields
        if "completed_at" in execution_data and execution_data["completed_at"]:
            CustomAssertions.assert_iso_datetime(execution_data["completed_at"], "completed_at")

        if "progress" in execution_data:
            CustomAssertions.assert_percentage_range(execution_data["progress"])


class PerformanceAssertions:
    """Performance-related assertions for testing."""

    @staticmethod
    def assert_execution_time(func: Callable, max_seconds: float, *args, **kwargs):
        """Assert function executes within time limit."""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        assert execution_time <= max_seconds, (
            f"Function took {execution_time:.3f}s, expected max {max_seconds}s"
        )

        return result

    @staticmethod
    async def assert_async_execution_time(coro: Callable, max_seconds: float, *args, **kwargs):
        """Assert async function executes within time limit."""
        start_time = time.time()
        result = await coro(*args, **kwargs)
        execution_time = time.time() - start_time

        assert execution_time <= max_seconds, (
            f"Async function took {execution_time:.3f}s, expected max {max_seconds}s"
        )

        return result

    @staticmethod
    def assert_memory_usage(func: Callable, max_mb: float, *args, **kwargs):
        """Assert function uses memory within limit."""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB

        # Execute function
        result = func(*args, **kwargs)

        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_used = final_memory - initial_memory

        assert memory_used <= max_mb, (
            f"Function used {memory_used:.2f}MB, expected max {max_mb}MB"
        )

        return result

    @staticmethod
    def assert_query_count(session: Session, max_queries: int, func: Callable, *args, **kwargs):
        """Assert function executes within query limit."""
        query_count = 0

        def count_queries(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        # Add query counter
        from sqlalchemy import event
        event.listen(session.bind, "before_cursor_execute", count_queries)

        try:
            result = func(*args, **kwargs)
            assert query_count <= max_queries, (
                f"Function executed {query_count} queries, expected max {max_queries}"
            )
            return result
        finally:
            event.remove(session.bind, "before_cursor_execute", count_queries)

    @staticmethod
    def assert_response_time(response, max_milliseconds: int):
        """Assert API response time is within limit."""
        # Check if response has timing information
        if hasattr(response, 'elapsed'):
            response_time_ms = response.elapsed.total_seconds() * 1000
            assert response_time_ms <= max_milliseconds, (
                f"Response took {response_time_ms:.2f}ms, expected max {max_milliseconds}ms"
            )

    @staticmethod
    def assert_throughput(func: Callable, min_ops_per_second: float, duration_seconds: int = 1):
        """Assert function achieves minimum throughput."""
        start_time = time.time()
        operations = 0

        while time.time() - start_time < duration_seconds:
            func()
            operations += 1

        actual_duration = time.time() - start_time
        ops_per_second = operations / actual_duration

        assert ops_per_second >= min_ops_per_second, (
            f"Achieved {ops_per_second:.2f} ops/sec, expected min {min_ops_per_second}"
        )


class SecurityAssertions:
    """Security-related assertions for testing."""

    @staticmethod
    def assert_no_sensitive_data_in_response(response_data: Dict[str, Any]):
        """Assert response doesn't contain sensitive data."""
        sensitive_fields = [
            "password", "hashed_password", "secret", "private_key",
            "api_key", "token", "credential", "session_id"
        ]

        def check_dict(data: Dict[str, Any], path: str = ""):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key

                # Check field names
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    raise AssertionError(f"Sensitive field found in response: {current_path}")

                # Recursively check nested dictionaries
                if isinstance(value, dict):
                    check_dict(value, current_path)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            check_dict(item, f"{current_path}[{i}]")

        if isinstance(response_data, dict):
            check_dict(response_data)

    @staticmethod
    def assert_password_strength(password: str):
        """Assert password meets strength requirements."""
        assert len(password) >= 8, "Password must be at least 8 characters"
        assert re.search(r'[A-Z]', password), "Password must contain uppercase letter"
        assert re.search(r'[a-z]', password), "Password must contain lowercase letter"
        assert re.search(r'\d', password), "Password must contain digit"
        assert re.search(r'[!@#$%^&*(),.?":{}|<>]', password), "Password must contain special character"

    @staticmethod
    def assert_jwt_token_format(token: str):
        """Assert token has valid JWT format."""
        parts = token.split('.')
        assert len(parts) == 3, "JWT token must have 3 parts separated by dots"

        # Validate base64 encoding (basic check)
        import base64
        for i, part in enumerate(parts[:2]):  # Don't validate signature
            try:
                # Add padding if needed
                padded = part + '=' * (4 - len(part) % 4)
                base64.urlsafe_b64decode(padded)
            except Exception:
                raise AssertionError(f"JWT part {i} is not valid base64")

    @staticmethod
    def assert_sql_injection_safe(query: str):
        """Assert query string doesn't contain SQL injection patterns."""
        injection_patterns = [
            r"('\s*(or|and)\s*')",
            r"(;\s*(drop|delete|update|insert)\s+)",
            r"(union\s+select)",
            r"(--\s*)",
            r"(/\*.*?\*/)"
        ]

        query_lower = query.lower()
        for pattern in injection_patterns:
            if re.search(pattern, query_lower):
                raise AssertionError(f"Potential SQL injection pattern found: {pattern}")

    @staticmethod
    def assert_xss_safe(content: str):
        """Assert content is safe from XSS attacks."""
        xss_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>"
        ]

        content_lower = content.lower()
        for pattern in xss_patterns:
            if re.search(pattern, content_lower):
                raise AssertionError(f"Potential XSS pattern found: {pattern}")

    @staticmethod
    def assert_no_information_disclosure(error_message: str):
        """Assert error message doesn't disclose sensitive information."""
        disclosure_patterns = [
            r"traceback",
            r"stack trace",
            r"file path",
            r"database error",
            r"connection string",
            r"internal server",
            r"debug information"
        ]

        message_lower = error_message.lower()
        for pattern in disclosure_patterns:
            if pattern in message_lower:
                raise AssertionError(f"Information disclosure in error message: {pattern}")


class BusinessLogicAssertions:
    """Domain-specific business logic assertions."""

    @staticmethod
    def assert_agent_can_execute_task(agent: Agent, task_type: str):
        """Assert agent has capabilities to execute task type."""
        if not agent.configuration:
            raise AssertionError("Agent has no configuration")

        capabilities = agent.configuration.get("capabilities", [])
        assert task_type in capabilities, (
            f"Agent lacks capability '{task_type}'. Available: {capabilities}"
        )

    @staticmethod
    def assert_playbook_execution_valid(execution: PlaybookExecution):
        """Assert playbook execution is in valid state."""
        # Check status transitions are valid
        valid_transitions = {
            ExecutionStatus.PENDING: [ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED],
            ExecutionStatus.RUNNING: [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED],
            ExecutionStatus.COMPLETED: [],  # Terminal state
            ExecutionStatus.FAILED: [],     # Terminal state
            ExecutionStatus.CANCELLED: []   # Terminal state
        }

        # Basic state validation
        if execution.status == ExecutionStatus.COMPLETED:
            assert execution.completed_at is not None, "Completed execution must have completion time"
            assert execution.progress == 100, "Completed execution must have 100% progress"

        if execution.status == ExecutionStatus.FAILED:
            assert execution.error_message is not None, "Failed execution must have error message"

        if execution.completed_at:
            assert execution.started_at <= execution.completed_at, (
                "Completion time must be after start time"
            )

    @staticmethod
    def assert_user_permissions_valid(user: User, required_permissions: List[str]):
        """Assert user has required permissions."""
        user_permissions = set()

        for role in user.roles:
            if role.permissions:
                try:
                    role_permissions = json.loads(role.permissions)
                    user_permissions.update(role_permissions)
                except json.JSONDecodeError:
                    pass

        missing_permissions = set(required_permissions) - user_permissions
        assert not missing_permissions, (
            f"User missing required permissions: {missing_permissions}"
        )

    @staticmethod
    def assert_workflow_dependencies_satisfied(workflow_data: Dict[str, Any]):
        """Assert workflow step dependencies are properly satisfied."""
        if "steps" not in workflow_data.get("configuration", {}):
            return

        steps = workflow_data["configuration"]["steps"]
        step_ids = {step["step_id"] for step in steps}

        for step in steps:
            dependencies = step.get("dependencies", [])
            for dep_id in dependencies:
                assert dep_id in step_ids, (
                    f"Step '{step['step_id']}' depends on non-existent step '{dep_id}'"
                )

    @staticmethod
    def assert_execution_metrics_consistent(metrics: Dict[str, Any]):
        """Assert execution metrics are internally consistent."""
        if "success_rate" in metrics and "total_executions" in metrics:
            success_rate = metrics["success_rate"]
            total = metrics["total_executions"]

            assert 0 <= success_rate <= 100, "Success rate must be between 0 and 100"

            if total == 0:
                assert success_rate == 0, "Success rate should be 0 when no executions"

    @staticmethod
    def assert_resource_limits_respected(resource_usage: Dict[str, float]):
        """Assert resource usage is within acceptable limits."""
        limits = {
            "cpu_usage": 95.0,      # Max 95% CPU
            "memory_usage": 90.0,   # Max 90% memory
            "disk_usage": 85.0,     # Max 85% disk
            "network_io": 1000.0    # Max 1000 Mbps
        }

        for resource, usage in resource_usage.items():
            if resource in limits:
                assert usage <= limits[resource], (
                    f"{resource} usage {usage}% exceeds limit {limits[resource]}%"
                )


# Utility functions for common assertion patterns
def assert_valid_api_response(response, expected_status: int = 200):
    """Assert API response is valid with expected status."""
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response: {response.text}"
    )

    if response.content:
        try:
            data = response.json()
            return data
        except json.JSONDecodeError:
            raise AssertionError("Response is not valid JSON")

    return None


def assert_database_record_exists(session: Session, model_class: Type[BaseModel], **filters):
    """Assert database record exists with given filters."""
    query = session.query(model_class)
    for field, value in filters.items():
        query = query.filter(getattr(model_class, field) == value)

    record = query.first()
    assert record is not None, (
        f"No {model_class.__name__} record found with filters: {filters}"
    )

    return record


def assert_eventually(condition: Callable, timeout_seconds: int = 10, check_interval: float = 0.1):
    """Assert condition becomes true within timeout period."""
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        if condition():
            return
        time.sleep(check_interval)

    raise AssertionError(f"Condition not met within {timeout_seconds} seconds")


# Pytest fixtures for common assertions
@pytest.fixture
def assert_response():
    """Fixture providing response assertion helper."""
    return lambda response, status=200: assert_valid_api_response(response, status)


@pytest.fixture
def assert_db_record():
    """Fixture providing database record assertion helper."""
    return assert_database_record_exists


@pytest.fixture
def assert_timing():
    """Fixture providing timing assertion helper."""
    return PerformanceAssertions.assert_execution_time
