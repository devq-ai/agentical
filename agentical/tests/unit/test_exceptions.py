"""
Unit Tests for Agentical Exception Handling System

This module contains unit tests for the Agentical exception handling system,
verifying that exceptions behave correctly and produce expected responses
when integrated with FastAPI.

Tests cover:
- Exception initialization and properties
- Error response serialization
- Exception hierarchies and inheritance
- FastAPI integration and response formatting
- Logfire logging integration
"""

import pytest
import logging
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, Request, status
from fastapi.testclient import TestClient

from agentical.core.exceptions import (
    AgenticalError,
    ClientError,
    ServerError,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    BadRequestError,
    ConflictError,
    DatabaseError,
    ExternalServiceError,
    ConfigurationError,
    ServiceUnavailableError,
    TimeoutError,
    AgentError,
    AgentInitializationError,
    AgentExecutionError,
    AgentNotFoundError,
    WorkflowError,
    WorkflowNotFoundError,
    WorkflowExecutionError,
    PlaybookError,
    KnowledgeError,
    setup_exception_handlers
)


@pytest.mark.unit
class TestExceptionBase:
    """Test the base AgenticalError class and core functionality."""
    
    def test_base_exception_initialization(self):
        """Test that base exception can be initialized with default values."""
        exc = AgenticalError()
        
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "internal_error"
        assert exc.message == "An internal error occurred"
        assert isinstance(exc.details, dict)
        assert isinstance(exc.context, dict)
        assert exc.error_id is not None
        
    def test_exception_with_custom_message(self):
        """Test that exception can be initialized with a custom message."""
        custom_message = "Custom error message"
        exc = AgenticalError(message=custom_message)
        
        assert exc.message == custom_message
        assert str(exc) == custom_message
        
    def test_exception_with_custom_status_code(self):
        """Test that exception can be initialized with a custom status code."""
        custom_status = status.HTTP_418_IM_A_TEAPOT
        exc = AgenticalError(status_code=custom_status)
        
        assert exc.status_code == custom_status
        
    def test_exception_with_custom_error_code(self):
        """Test that exception can be initialized with a custom error code."""
        custom_code = "custom_error_code"
        exc = AgenticalError(error_code=custom_code)
        
        assert exc.error_code == custom_code
        
    def test_exception_with_details(self):
        """Test that exception can be initialized with details."""
        details = {"key": "value", "nested": {"data": True}}
        exc = AgenticalError(details=details)
        
        assert exc.details == details
        
    def test_exception_with_context(self):
        """Test that exception can be initialized with context."""
        context = {"location": "test", "operation": "unit_test"}
        exc = AgenticalError(context=context)
        
        assert exc.context == context
        
    def test_exception_with_custom_error_id(self):
        """Test that exception can be initialized with a custom error ID."""
        error_id = "test-error-id-12345"
        exc = AgenticalError(error_id=error_id)
        
        assert exc.error_id == error_id
        
    def test_to_dict_method(self):
        """Test that to_dict method returns correctly formatted dictionary."""
        exc = AgenticalError(
            message="Test error",
            error_code="test_error",
            details={"test": True}
        )
        
        result = exc.to_dict()
        
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "test_error"
        assert result["message"] == "Test error"
        assert "error_id" in result
        assert result["status_code"] == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "details" in result
        assert result["details"]["test"] is True
        
    def test_log_error_method(self, mock_logfire):
        """Test that log_error method logs to Logfire with correct data."""
        exc = AgenticalError(
            message="Test error",
            details={"test": True},
            context={"location": "test_function"}
        )
        
        # Mock request
        mock_request = MagicMock()
        mock_request.url.path = "/test/path"
        mock_request.method = "GET"
        mock_request.client.host = "127.0.0.1"
        
        exc.log_error(mock_request)
        
        # Verify Logfire error was called with correct parameters
        mock_logfire["error"].assert_called_once()
        args, kwargs = mock_logfire["error"].call_args
        
        assert args[0] == "Test error"  # First arg is the message
        assert "error_id" in kwargs
        assert "error_code" in kwargs
        assert "status_code" in kwargs
        assert "details" in kwargs
        assert "context" in kwargs
        assert "request_path" in kwargs
        assert "request_method" in kwargs
        assert "client_ip" in kwargs
        
        assert kwargs["details"]["test"] is True
        assert kwargs["context"]["location"] == "test_function"
        assert kwargs["request_path"] == "/test/path"
        assert kwargs["request_method"] == "GET"
        assert kwargs["client_ip"] == "127.0.0.1"


@pytest.mark.unit
class TestExceptionHierarchy:
    """Test the exception hierarchy and inheritance."""
    
    def test_client_error_inheritance(self):
        """Test that client errors inherit correctly from AgenticalError."""
        exc = ClientError()
        
        assert isinstance(exc, AgenticalError)
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_server_error_inheritance(self):
        """Test that server errors inherit correctly from AgenticalError."""
        exc = ServerError()
        
        assert isinstance(exc, AgenticalError)
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def test_not_found_error(self):
        """Test NotFoundError properties and inheritance."""
        exc = NotFoundError(message="Resource not found")
        
        assert isinstance(exc, ClientError)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "not_found"
        assert exc.message == "Resource not found"
        
    def test_validation_error(self):
        """Test ValidationError properties and inheritance."""
        exc = ValidationError(message="Validation failed")
        
        assert isinstance(exc, ClientError)
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.error_code == "validation_error"
        
    def test_authentication_error(self):
        """Test AuthenticationError properties and inheritance."""
        exc = AuthenticationError()
        
        assert isinstance(exc, ClientError)
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.error_code == "authentication_error"
        
    def test_authorization_error(self):
        """Test AuthorizationError properties and inheritance."""
        exc = AuthorizationError()
        
        assert isinstance(exc, ClientError)
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.error_code == "authorization_error"
        
    def test_database_error(self):
        """Test DatabaseError properties and inheritance."""
        exc = DatabaseError()
        
        assert isinstance(exc, ServerError)
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "database_error"
        
    def test_external_service_error(self):
        """Test ExternalServiceError properties and inheritance."""
        exc = ExternalServiceError(
            service_name="test-service",
            response_status=500,
            response_body="Internal server error"
        )
        
        assert isinstance(exc, ServerError)
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.error_code == "external_service_error"
        assert exc.details["service_name"] == "test-service"
        assert exc.details["response_status"] == 500
        assert exc.details["response_body"] == "Internal server error"


@pytest.mark.unit
class TestAgentExceptions:
    """Test agent-specific exceptions."""
    
    def test_agent_error_inheritance(self):
        """Test that agent errors inherit correctly."""
        exc = AgentError()
        
        assert isinstance(exc, AgenticalError)
        assert exc.error_code == "agent_error"
        
    def test_agent_initialization_error(self):
        """Test AgentInitializationError properties."""
        exc = AgentInitializationError(message="Could not initialize agent")
        
        assert isinstance(exc, AgentError)
        assert exc.error_code == "agent_initialization_error"
        assert exc.message == "Could not initialize agent"
        
    def test_agent_execution_error(self):
        """Test AgentExecutionError properties."""
        exc = AgentExecutionError()
        
        assert isinstance(exc, AgentError)
        assert exc.error_code == "agent_execution_error"
        
    def test_agent_not_found_error(self):
        """Test AgentNotFoundError properties and multiple inheritance."""
        exc = AgentNotFoundError()
        
        assert isinstance(exc, AgentError)
        assert isinstance(exc, NotFoundError)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "agent_not_found"


@pytest.mark.unit
class TestWorkflowExceptions:
    """Test workflow-specific exceptions."""
    
    def test_workflow_error_inheritance(self):
        """Test that workflow errors inherit correctly."""
        exc = WorkflowError()
        
        assert isinstance(exc, AgenticalError)
        assert exc.error_code == "workflow_error"
        
    def test_workflow_not_found_error(self):
        """Test WorkflowNotFoundError properties and inheritance."""
        exc = WorkflowNotFoundError()
        
        assert isinstance(exc, WorkflowError)
        assert isinstance(exc, NotFoundError)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "workflow_not_found"
        
    def test_workflow_execution_error(self):
        """Test WorkflowExecutionError properties."""
        exc = WorkflowExecutionError(
            message="Workflow execution failed",
            details={"step": "processing", "reason": "timeout"}
        )
        
        assert isinstance(exc, WorkflowError)
        assert exc.error_code == "workflow_execution_error"
        assert exc.message == "Workflow execution failed"
        assert exc.details["step"] == "processing"
        assert exc.details["reason"] == "timeout"


@pytest.mark.unit
class TestPlaybookExceptions:
    """Test playbook-specific exceptions."""
    
    def test_playbook_error_inheritance(self):
        """Test that playbook errors inherit correctly."""
        exc = PlaybookError()
        
        assert isinstance(exc, AgenticalError)
        assert exc.error_code == "playbook_error"


@pytest.mark.unit
class TestKnowledgeExceptions:
    """Test knowledge-specific exceptions."""
    
    def test_knowledge_error_inheritance(self):
        """Test that knowledge errors inherit correctly."""
        exc = KnowledgeError()
        
        assert isinstance(exc, AgenticalError)
        assert exc.error_code == "knowledge_error"


@pytest.mark.integration
class TestExceptionHandlers:
    """Test exception handlers integration with FastAPI."""
    
    def setup_method(self):
        """Set up test application with routes that raise exceptions."""
        self.app = FastAPI()
        setup_exception_handlers(self.app)
        
        @self.app.get("/test/agentical-error")
        async def raise_agentical_error():
            raise AgenticalError(message="Test AgenticalError")
        
        @self.app.get("/test/not-found")
        async def raise_not_found():
            raise NotFoundError(message="Resource not found")
        
        @self.app.get("/test/validation-error")
        async def raise_validation_error():
            raise ValidationError(
                message="Validation failed",
                details={"errors": [{"field": "name", "message": "Required"}]}
            )
        
        @self.app.get("/test/server-error")
        async def raise_server_error():
            raise ServerError(message="Server error occurred")
        
        @self.app.get("/test/unhandled-error")
        async def raise_unhandled():
            # This will trigger the general exception handler
            raise ValueError("Unhandled exception")
        
        self.client = TestClient(self.app)
    
    def test_agentical_error_handler(self):
        """Test that AgenticalError is handled correctly."""
        with patch('logfire.error') as mock_logfire_error:
            response = self.client.get("/test/agentical-error")
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["error"] == "internal_error"
            assert data["message"] == "Test AgenticalError"
            assert "error_id" in data
            
            # Verify Logfire was called
            mock_logfire_error.assert_called_once()
    
    def test_not_found_error_handler(self):
        """Test that NotFoundError is handled correctly."""
        with patch('logfire.error') as mock_logfire_error:
            response = self.client.get("/test/not-found")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] == "not_found"
            assert data["message"] == "Resource not found"
            
            # Verify Logfire was called
            mock_logfire_error.assert_called_once()
    
    def test_validation_error_handler(self):
        """Test that ValidationError is handled correctly."""
        with patch('logfire.error') as mock_logfire_error:
            response = self.client.get("/test/validation-error")
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            assert data["error"] == "validation_error"
            assert "details" in data
            assert "errors" in data["details"]
            
            # Verify Logfire was called
            mock_logfire_error.assert_called_once()
    
    def test_server_error_handler(self):
        """Test that ServerError is handled correctly."""
        with patch('logfire.error') as mock_logfire_error:
            response = self.client.get("/test/server-error")
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["error"] == "server_error"
            assert data["message"] == "Server error occurred"
            
            # Verify Logfire was called
            mock_logfire_error.assert_called_once()
    
    def test_unhandled_exception_handler(self):
        """Test that unhandled exceptions are properly handled."""
        with patch('logfire.error') as mock_logfire_error:
            response = self.client.get("/test/unhandled-error")
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["error"] == "internal_server_error"
            assert "error_id" in data
            
            # Verify Logfire was called with traceback
            mock_logfire_error.assert_called_once()
            args, kwargs = mock_logfire_error.call_args
            assert args[0] == "Unhandled exception"
            assert "traceback" in kwargs


if __name__ == "__main__":
    pytest.main(["-v", __file__])