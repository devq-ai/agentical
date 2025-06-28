"""
API Testing Helpers for Agentical Framework

This module provides comprehensive utilities for testing FastAPI endpoints,
including request builders, response validators, authentication helpers,
and endpoint testing utilities.

Features:
- Fluent API request builders
- Response validation utilities
- Authentication token management
- Endpoint testing helpers
- Mock response generators
- Error simulation utilities
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from unittest.mock import Mock, patch
import jwt

from fastapi import status
from fastapi.testclient import TestClient
import httpx
import pytest

from agentical.db.models.user import User


class APITestHelper:
    """Comprehensive API testing helper with fluent interface."""

    def __init__(self, client: TestClient):
        self.client = client
        self.base_url = "/api/v1"
        self.default_headers = {"Content-Type": "application/json"}
        self.auth_token = None

    def set_base_url(self, base_url: str):
        """Set base URL for API requests."""
        self.base_url = base_url
        return self

    def set_auth_token(self, token: str):
        """Set authentication token."""
        self.auth_token = token
        self.default_headers["Authorization"] = f"Bearer {token}"
        return self

    def clear_auth(self):
        """Clear authentication."""
        self.auth_token = None
        if "Authorization" in self.default_headers:
            del self.default_headers["Authorization"]
        return self

    def get(self, endpoint: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers, **(headers or {})}
        return self.client.get(url, params=params, headers=request_headers)

    def post(self, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers, **(headers or {})}
        return self.client.post(url, json=data, headers=request_headers)

    def put(self, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """Make PUT request."""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers, **(headers or {})}
        return self.client.put(url, json=data, headers=request_headers)

    def patch(self, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """Make PATCH request."""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers, **(headers or {})}
        return self.client.patch(url, json=data, headers=request_headers)

    def delete(self, endpoint: str, headers: Dict[str, str] = None):
        """Make DELETE request."""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers, **(headers or {})}
        return self.client.delete(url, headers=request_headers)


class RequestBuilder:
    """Builder for creating API requests with fluent interface."""

    def __init__(self, method: str, endpoint: str):
        self.method = method.upper()
        self.endpoint = endpoint
        self._headers = {"Content-Type": "application/json"}
        self._params = {}
        self._data = {}
        self._auth_token = None

    def headers(self, headers: Dict[str, str]):
        """Set request headers."""
        self._headers.update(headers)
        return self

    def header(self, key: str, value: str):
        """Set single header."""
        self._headers[key] = value
        return self

    def params(self, params: Dict[str, Any]):
        """Set query parameters."""
        self._params.update(params)
        return self

    def param(self, key: str, value: Any):
        """Set single query parameter."""
        self._params[key] = value
        return self

    def data(self, data: Dict[str, Any]):
        """Set request data."""
        self._data.update(data)
        return self

    def field(self, key: str, value: Any):
        """Set single data field."""
        self._data[key] = value
        return self

    def auth(self, token: str):
        """Set authentication token."""
        self._auth_token = token
        self._headers["Authorization"] = f"Bearer {token}"
        return self

    def execute(self, client: TestClient):
        """Execute the request."""
        method_map = {
            "GET": client.get,
            "POST": client.post,
            "PUT": client.put,
            "PATCH": client.patch,
            "DELETE": client.delete
        }

        method_func = method_map.get(self.method)
        if not method_func:
            raise ValueError(f"Unsupported HTTP method: {self.method}")

        kwargs = {"headers": self._headers}

        if self.method == "GET":
            kwargs["params"] = self._params
        else:
            if self._data:
                kwargs["json"] = self._data
            if self._params:
                kwargs["params"] = self._params

        return method_func(self.endpoint, **kwargs)


class ResponseValidator:
    """Validator for API responses with comprehensive checks."""

    def __init__(self, response):
        self.response = response
        self.data = None
        try:
            self.data = response.json() if response.content else {}
        except json.JSONDecodeError:
            self.data = {}

    def status_code(self, expected_code: int):
        """Validate status code."""
        assert self.response.status_code == expected_code, (
            f"Expected status code {expected_code}, got {self.response.status_code}. "
            f"Response: {self.response.text}"
        )
        return self

    def success(self):
        """Validate successful response (2xx)."""
        assert 200 <= self.response.status_code < 300, (
            f"Expected successful status code, got {self.response.status_code}. "
            f"Response: {self.response.text}"
        )
        return self

    def has_field(self, field_name: str):
        """Validate response has field."""
        assert field_name in self.data, f"Response missing field: {field_name}"
        return self

    def has_fields(self, *field_names: str):
        """Validate response has multiple fields."""
        for field_name in field_names:
            self.has_field(field_name)
        return self

    def field_equals(self, field_name: str, expected_value: Any):
        """Validate field equals expected value."""
        self.has_field(field_name)
        actual_value = self.data[field_name]
        assert actual_value == expected_value, (
            f"Field '{field_name}' expected {expected_value}, got {actual_value}"
        )
        return self

    def field_not_null(self, field_name: str):
        """Validate field is not null."""
        self.has_field(field_name)
        assert self.data[field_name] is not None, f"Field '{field_name}' should not be null"
        return self

    def field_type(self, field_name: str, expected_type: type):
        """Validate field type."""
        self.has_field(field_name)
        actual_value = self.data[field_name]
        assert isinstance(actual_value, expected_type), (
            f"Field '{field_name}' expected type {expected_type}, got {type(actual_value)}"
        )
        return self

    def field_length(self, field_name: str, expected_length: int):
        """Validate field length."""
        self.has_field(field_name)
        actual_value = self.data[field_name]
        assert len(actual_value) == expected_length, (
            f"Field '{field_name}' expected length {expected_length}, got {len(actual_value)}"
        )
        return self

    def field_min_length(self, field_name: str, min_length: int):
        """Validate field minimum length."""
        self.has_field(field_name)
        actual_value = self.data[field_name]
        assert len(actual_value) >= min_length, (
            f"Field '{field_name}' expected minimum length {min_length}, got {len(actual_value)}"
        )
        return self

    def field_contains(self, field_name: str, expected_item: Any):
        """Validate field contains item."""
        self.has_field(field_name)
        actual_value = self.data[field_name]
        assert expected_item in actual_value, (
            f"Field '{field_name}' should contain {expected_item}"
        )
        return self

    def is_list(self, field_name: str = None):
        """Validate response or field is a list."""
        if field_name:
            self.has_field(field_name)
            value = self.data[field_name]
        else:
            value = self.data

        assert isinstance(value, list), f"Expected list, got {type(value)}"
        return self

    def list_length(self, expected_length: int, field_name: str = None):
        """Validate list length."""
        if field_name:
            self.has_field(field_name)
            value = self.data[field_name]
        else:
            value = self.data

        assert isinstance(value, list), f"Expected list, got {type(value)}"
        assert len(value) == expected_length, (
            f"Expected list length {expected_length}, got {len(value)}"
        )
        return self

    def list_not_empty(self, field_name: str = None):
        """Validate list is not empty."""
        if field_name:
            self.has_field(field_name)
            value = self.data[field_name]
        else:
            value = self.data

        assert isinstance(value, list), f"Expected list, got {type(value)}"
        assert len(value) > 0, "List should not be empty"
        return self

    def error_message_contains(self, expected_text: str):
        """Validate error message contains text."""
        error_fields = ["detail", "message", "error"]
        found = False

        for field in error_fields:
            if field in self.data:
                if expected_text in str(self.data[field]):
                    found = True
                    break

        assert found, f"Error message should contain '{expected_text}'. Response: {self.data}"
        return self

    def pagination_fields(self):
        """Validate pagination fields are present."""
        pagination_fields = ["page", "page_size", "total", "pages"]
        for field in pagination_fields:
            self.has_field(field)
        return self

    def custom_assertion(self, assertion_func: Callable):
        """Run custom assertion function."""
        assertion_func(self.response, self.data)
        return self


class AuthenticationHelper:
    """Helper for managing authentication in tests."""

    def __init__(self, secret_key: str = "test_secret"):
        self.secret_key = secret_key
        self.algorithm = "HS256"

    def create_token(
        self,
        user_id: int,
        username: str,
        roles: List[str] = None,
        permissions: List[str] = None,
        expires_in_hours: int = 1
    ) -> str:
        """Create JWT token for testing."""
        payload = {
            "user_id": user_id,
            "username": username,
            "roles": roles or [],
            "permissions": permissions or [],
            "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
            "iat": datetime.utcnow(),
            "iss": "agentical-test"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_admin_token(self, user_id: int = 1, username: str = "admin") -> str:
        """Create admin token for testing."""
        return self.create_token(
            user_id=user_id,
            username=username,
            roles=["admin", "super_admin"],
            permissions=["admin:users", "admin:system", "user:read", "user:create"]
        )

    def create_user_token(self, user_id: int = 2, username: str = "testuser") -> str:
        """Create regular user token for testing."""
        return self.create_token(
            user_id=user_id,
            username=username,
            roles=["user"],
            permissions=["user:read"]
        )

    def create_expired_token(self, user_id: int = 1, username: str = "expired") -> str:
        """Create expired token for testing."""
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_invalid_token(self) -> str:
        """Create invalid token for testing."""
        payload = {
            "user_id": 1,
            "username": "invalid",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, "wrong_secret", algorithm=self.algorithm)

    def extract_payload(self, token: str) -> Dict[str, Any]:
        """Extract payload from token (for testing)."""
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])


class EndpointTester:
    """Comprehensive endpoint testing utility."""

    def __init__(self, client: TestClient, auth_helper: AuthenticationHelper = None):
        self.client = client
        self.api_helper = APITestHelper(client)
        self.auth_helper = auth_helper or AuthenticationHelper()

    def test_endpoint_authentication(self, endpoint: str, method: str = "GET"):
        """Test endpoint requires authentication."""
        # Test without authentication
        response = self.api_helper.get(endpoint) if method == "GET" else getattr(self.api_helper, method.lower())(endpoint)

        ResponseValidator(response).status_code(status.HTTP_401_UNAUTHORIZED)

        # Test with invalid token
        self.api_helper.set_auth_token("invalid_token")
        response = self.api_helper.get(endpoint) if method == "GET" else getattr(self.api_helper, method.lower())(endpoint)

        ResponseValidator(response).status_code(status.HTTP_401_UNAUTHORIZED)

        # Test with expired token
        expired_token = self.auth_helper.create_expired_token()
        self.api_helper.set_auth_token(expired_token)
        response = self.api_helper.get(endpoint) if method == "GET" else getattr(self.api_helper, method.lower())(endpoint)

        ResponseValidator(response).status_code(status.HTTP_401_UNAUTHORIZED)

    def test_endpoint_authorization(self, endpoint: str, required_roles: List[str], method: str = "GET"):
        """Test endpoint authorization with different roles."""
        # Test with insufficient permissions
        user_token = self.auth_helper.create_user_token()
        self.api_helper.set_auth_token(user_token)
        response = self.api_helper.get(endpoint) if method == "GET" else getattr(self.api_helper, method.lower())(endpoint)

        if "admin" in required_roles:
            ResponseValidator(response).status_code(status.HTTP_403_FORBIDDEN)

        # Test with admin permissions
        admin_token = self.auth_helper.create_admin_token()
        self.api_helper.set_auth_token(admin_token)
        response = self.api_helper.get(endpoint) if method == "GET" else getattr(self.api_helper, method.lower())(endpoint)

        # Should not be 403 (might be 200, 404, etc. depending on endpoint)
        assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_endpoint_validation(self, endpoint: str, invalid_data: Dict[str, Any], method: str = "POST"):
        """Test endpoint input validation."""
        admin_token = self.auth_helper.create_admin_token()
        self.api_helper.set_auth_token(admin_token)

        response = getattr(self.api_helper, method.lower())(endpoint, data=invalid_data)

        ResponseValidator(response).status_code(status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_endpoint_not_found(self, endpoint: str, method: str = "GET"):
        """Test endpoint returns 404 for non-existent resources."""
        admin_token = self.auth_helper.create_admin_token()
        self.api_helper.set_auth_token(admin_token)

        response = self.api_helper.get(endpoint) if method == "GET" else getattr(self.api_helper, method.lower())(endpoint)

        ResponseValidator(response).status_code(status.HTTP_404_NOT_FOUND)

    def test_crud_endpoints(
        self,
        base_endpoint: str,
        create_data: Dict[str, Any],
        update_data: Dict[str, Any],
        invalid_data: Dict[str, Any] = None
    ):
        """Test complete CRUD operations for an endpoint."""
        admin_token = self.auth_helper.create_admin_token()
        self.api_helper.set_auth_token(admin_token)

        # Test CREATE
        response = self.api_helper.post(base_endpoint, data=create_data)
        ResponseValidator(response).success()

        created_item = response.json()
        item_id = created_item.get("id") or created_item.get("agent_id") or created_item.get("playbook_id")

        # Test READ (list)
        response = self.api_helper.get(base_endpoint)
        ResponseValidator(response).success().is_list()

        # Test READ (single)
        response = self.api_helper.get(f"{base_endpoint}/{item_id}")
        ResponseValidator(response).success()

        # Test UPDATE
        response = self.api_helper.put(f"{base_endpoint}/{item_id}", data=update_data)
        ResponseValidator(response).success()

        # Test invalid data (if provided)
        if invalid_data:
            response = self.api_helper.post(base_endpoint, data=invalid_data)
            ResponseValidator(response).status_code(status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Test DELETE
        response = self.api_helper.delete(f"{base_endpoint}/{item_id}")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

        # Verify deletion
        response = self.api_helper.get(f"{base_endpoint}/{item_id}")
        ResponseValidator(response).status_code(status.HTTP_404_NOT_FOUND)


class MockResponseGenerator:
    """Generator for mock API responses."""

    @staticmethod
    def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Generate success response."""
        return {
            "success": True,
            "message": message,
            "data": data
        }

    @staticmethod
    def error_response(message: str = "Error", code: str = "ERROR", details: Any = None) -> Dict[str, Any]:
        """Generate error response."""
        response = {
            "success": False,
            "error": {
                "message": message,
                "code": code
            }
        }
        if details:
            response["error"]["details"] = details
        return response

    @staticmethod
    def paginated_response(items: List[Any], page: int = 1, page_size: int = 10, total: int = None) -> Dict[str, Any]:
        """Generate paginated response."""
        total = total or len(items)
        pages = (total + page_size - 1) // page_size

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = items[start_idx:end_idx]

        return {
            "items": page_items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": pages,
                "has_next": page < pages,
                "has_prev": page > 1
            }
        }

    @staticmethod
    def validation_error_response(field_errors: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate validation error response."""
        return {
            "detail": [
                {
                    "loc": ["body", field],
                    "msg": "; ".join(errors),
                    "type": "value_error"
                }
                for field, errors in field_errors.items()
            ]
        }


# Convenience functions
def get_request(endpoint: str) -> RequestBuilder:
    """Create GET request builder."""
    return RequestBuilder("GET", endpoint)


def post_request(endpoint: str) -> RequestBuilder:
    """Create POST request builder."""
    return RequestBuilder("POST", endpoint)


def put_request(endpoint: str) -> RequestBuilder:
    """Create PUT request builder."""
    return RequestBuilder("PUT", endpoint)


def patch_request(endpoint: str) -> RequestBuilder:
    """Create PATCH request builder."""
    return RequestBuilder("PATCH", endpoint)


def delete_request(endpoint: str) -> RequestBuilder:
    """Create DELETE request builder."""
    return RequestBuilder("DELETE", endpoint)


def validate_response(response) -> ResponseValidator:
    """Create response validator."""
    return ResponseValidator(response)


# Error simulation utilities
class ErrorSimulator:
    """Utility for simulating various error conditions."""

    @staticmethod
    def simulate_database_error():
        """Simulate database connection error."""
        return patch('agentical.db.session.get_db', side_effect=Exception("Database connection failed"))

    @staticmethod
    def simulate_auth_service_error():
        """Simulate authentication service error."""
        return patch('agentical.tools.security.auth_manager.AuthManager.authenticate',
                    side_effect=Exception("Auth service unavailable"))

    @staticmethod
    def simulate_external_api_error():
        """Simulate external API error."""
        return patch('httpx.AsyncClient.post', side_effect=Exception("External API error"))

    @staticmethod
    def simulate_timeout():
        """Simulate request timeout."""
        return patch('httpx.AsyncClient.post', side_effect=httpx.TimeoutException("Request timeout"))

    @staticmethod
    def simulate_rate_limit():
        """Simulate rate limit exceeded."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limit exceeded"}
        return patch('httpx.AsyncClient.post', return_value=mock_response)
