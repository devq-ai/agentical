"""
Integration Tests for Health and Monitoring Endpoints

This module tests the health check and monitoring endpoints to ensure they
provide accurate information about the system's health and performance.
"""

import pytest
from fastapi import status

from tests.base_test import BaseIntegrationTest


class TestHealthEndpoints(BaseIntegrationTest):
    """Test suite for health and monitoring endpoints."""
    
    def test_health_check_endpoint(self):
        """Test the main health check endpoint returns valid data."""
        response = self.client.get("/api/v1/health")
        self.assert_api_success(response)
        
        # Verify required fields
        self.assert_field_in_response(response, "status")
        self.assert_field_in_response(response, "timestamp")
        self.assert_field_in_response(response, "version")
        self.assert_field_in_response(response, "environment")
        self.assert_field_in_response(response, "services")
        self.assert_field_in_response(response, "system")
        
        # Verify services
        data = response.json()
        assert "database" in data["services"], "Database service not found in health check"
        assert "cache" in data["services"], "Cache service not found in health check"
        assert "logfire" in data["services"], "Logfire service not found in health check"
        
        # Verify system metrics
        assert "cpu_usage" in data["system"], "CPU usage not found in system metrics"
        assert "memory_usage" in data["system"], "Memory usage not found in system metrics"
        assert "disk_usage" in data["system"], "Disk usage not found in system metrics"
        assert "uptime_seconds" in data["system"], "Uptime not found in system metrics"
    
    def test_readiness_probe(self):
        """Test the readiness probe endpoint."""
        response = self.client.get("/api/v1/health/readiness")
        self.assert_api_success(response)
        self.assert_value_in_response(response, "status", "ready")
    
    def test_liveness_probe(self):
        """Test the liveness probe endpoint."""
        response = self.client.get("/api/v1/health/liveness")
        self.assert_api_success(response)
        self.assert_value_in_response(response, "status", "alive")
    
    def test_metrics_endpoint(self):
        """Test the metrics endpoint returns valid data."""
        response = self.client.get("/api/v1/health/metrics")
        self.assert_api_success(response)
        
        # Verify required fields
        self.assert_field_in_response(response, "timestamp")
        self.assert_field_in_response(response, "metrics")
        
        # Verify metrics structure
        data = response.json()
        assert isinstance(data["metrics"], list), "Metrics should be a list"
        assert len(data["metrics"]) > 0, "Metrics list should not be empty"
        
        # Verify metric fields
        first_metric = data["metrics"][0]
        assert "name" in first_metric, "Metric should have a name"
        assert "value" in first_metric, "Metric should have a value"
        assert "timestamp" in first_metric, "Metric should have a timestamp"
    
    def test_database_health_endpoint(self):
        """Test the database health endpoint."""
        response = self.client.get("/api/v1/health/database")
        self.assert_api_success(response)
        
        # Verify required fields
        self.assert_field_in_response(response, "connection_pool")
        self.assert_field_in_response(response, "query_performance")
        
        # Verify connection pool metrics
        data = response.json()
        assert "size" in data["connection_pool"], "Connection pool size not found"
        assert "checked_out" in data["connection_pool"], "Checked out connections not found"
        assert "overflow" in data["connection_pool"], "Connection pool overflow not found"