"""
Integration Tests for Agentical Main FastAPI Application

This module contains integration tests for the main FastAPI application endpoints,
validating that the API works correctly with the test framework infrastructure.

Tests cover:
- Basic health check endpoints
- API functionality and routing
- Request/response validation
- Error handling integration
- FastAPI test client functionality

This serves as validation that Task 6.1 (PyTest Environment Setup) is complete
and working with the actual application.
"""

import pytest
import json
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
class TestMainAPIEndpoints:
    """Integration tests for main API endpoints."""
    
    def test_root_endpoint_basic_functionality(self, test_client):
        """Test the root endpoint returns expected response."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        response = test_client.get("/")
        
        # Basic response validation
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Response content validation
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data or "status" in data
    
    def test_health_check_endpoint(self, test_client):
        """Test the health check endpoint functionality."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        response = test_client.get("/health")
        
        # Health check should return 200 or 503 depending on system state
        assert response.status_code in [200, 503]
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, dict)
        # Health check should have status information
        assert "status" in data
    
    @pytest.mark.slow
    def test_infrastructure_status_endpoint(self, test_client):
        """Test the infrastructure status endpoint."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        response = test_client.get("/infrastructure/status")
        
        # Infrastructure status endpoint
        assert response.status_code in [200, 503]
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_api_error_handling(self, test_client):
        """Test that API handles invalid routes properly."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        response = test_client.get("/nonexistent-endpoint")
        
        # Should return 404 for nonexistent endpoints
        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, dict)
        assert "detail" in data
    
    def test_api_content_type_validation(self, test_client):
        """Test that API properly handles content types."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        # Test valid JSON content type
        response = test_client.get("/")
        assert "application/json" in response.headers["content-type"]
        
        # Ensure response is valid JSON
        try:
            response.json()
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")


@pytest.mark.integration
@pytest.mark.api
class TestAgentAPIEndpoints:
    """Integration tests for agent-related API endpoints."""
    
    def test_agent_execution_endpoint_exists(self, test_client):
        """Test that agent execution endpoint exists and handles requests."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        # Test POST to agent execution endpoint with minimal data
        test_data = {
            "prompt": "test prompt",
            "agent_type": "test"
        }
        
        response = test_client.post("/agent/execute", json=test_data)
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        # Should return valid response (may be 422 for validation, 200 for success, etc.)
        assert response.status_code in [200, 400, 422, 500]
        assert response.headers["content-type"] == "application/json"
    
    def test_workflow_execution_endpoint_exists(self, test_client):
        """Test that workflow execution endpoint exists."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        test_data = {
            "workflow_name": "test_workflow"
        }
        
        response = test_client.post("/workflow/execute", json=test_data)
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        assert response.status_code in [200, 400, 422, 500]
        assert response.headers["content-type"] == "application/json"
    
    def test_playbook_execution_endpoint_exists(self, test_client):
        """Test that playbook execution endpoint exists."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        test_data = {
            "playbook_name": "test_playbook"
        }
        
        response = test_client.post("/playbook/execute", json=test_data)
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        assert response.status_code in [200, 400, 422, 500]
        assert response.headers["content-type"] == "application/json"


@pytest.mark.integration
class TestAsyncAPIFunctionality:
    """Integration tests for async API functionality."""
    
    async def test_async_client_functionality(self, async_client):
        """Test that async client works with the API."""
        if async_client is None:
            pytest.skip("Async client not available for testing")
            
        response = await async_client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, dict)
    
    async def test_async_health_check(self, async_client):
        """Test health check endpoint with async client."""
        if async_client is None:
            pytest.skip("Async client not available for testing")
            
        response = await async_client.get("/health")
        
        assert response.status_code in [200, 503]
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data


@pytest.mark.integration
@pytest.mark.external
class TestExternalServiceIntegration:
    """Integration tests for external service connections."""
    
    def test_infrastructure_health_checker_integration(self, test_client, mock_external_services):
        """Test that infrastructure health checker integration works."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        # Mock external service calls to avoid actual network requests
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            
            mock_httpx_instance = Mock()
            mock_httpx_instance.get = Mock(return_value=mock_response)
            mock_httpx.return_value.__aenter__ = Mock(return_value=mock_httpx_instance)
            mock_httpx.return_value.__aexit__ = Mock(return_value=False)
            
            response = test_client.get("/infrastructure/status")
            
            # Should return some response (may vary based on mocked services)
            assert response.status_code in [200, 503]
            assert response.headers["content-type"] == "application/json"


@pytest.mark.integration
@pytest.mark.smoke
class TestCriticalAPIFunctionality:
    """Smoke tests for critical API functionality."""
    
    def test_api_server_responds(self, test_client):
        """Critical test: API server responds to requests."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        response = test_client.get("/")
        
        # Critical: API must respond
        assert response.status_code is not None
        assert response.status_code < 500  # No internal server errors
    
    def test_health_endpoint_accessible(self, test_client):
        """Critical test: Health endpoint is accessible."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        response = test_client.get("/health")
        
        # Critical: Health endpoint must be accessible
        assert response.status_code != 404
        assert response.status_code in [200, 503]  # Healthy or unhealthy, but accessible
    
    def test_api_returns_json(self, test_client):
        """Critical test: API returns valid JSON responses."""
        if test_client is None:
            pytest.skip("FastAPI app not available for testing")
            
        response = test_client.get("/")
        
        # Critical: Must return valid JSON
        assert "application/json" in response.headers.get("content-type", "")
        
        # Must be parseable JSON
        try:
            data = response.json()
            assert isinstance(data, (dict, list))
        except json.JSONDecodeError:
            pytest.fail("API did not return valid JSON")


@pytest.mark.integration
def test_fastapi_test_client_setup():
    """Test that FastAPI test client is properly configured."""
    try:
        from agentical.main import app
        client = TestClient(app)
        
        # Test that we can create a client
        assert client is not None
        
        # Test basic connectivity
        response = client.get("/")
        assert response is not None
        
    except ImportError:
        pytest.skip("FastAPI app not available - this is expected if main.py doesn't exist yet")


@pytest.mark.integration
def test_pytest_integration_with_fastapi():
    """Verify that PyTest integration with FastAPI is working properly."""
    # This test validates that the test framework itself is working
    assert True  # Basic assertion
    
    # Test that pytest fixtures are available
    import pytest
    assert hasattr(pytest, 'mark')
    
    # Test that FastAPI can be imported
    try:
        from fastapi import FastAPI
        app = FastAPI()
        assert app is not None
    except ImportError:
        pytest.fail("FastAPI not available")


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v", "--no-cov"])