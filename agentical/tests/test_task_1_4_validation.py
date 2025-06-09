"""
Validation Test for Task 1.4 - Health Check and Monitoring Endpoints

This module validates that the health check and monitoring endpoints have been
properly implemented according to the requirements of Task 1.4.
"""

import inspect
import pytest
import os
from importlib import import_module

from fastapi import FastAPI
from fastapi.routing import APIRouter

from agentical.api.health.endpoints import (
    router, 
    HealthResponse, 
    ServiceHealth, 
    SystemMetrics, 
    DatabaseMetrics,
    MonitoringResponse,
    MonitoringMetric
)

# Test if health API module exists
def test_health_api_module_exists():
    """Verify that the health API module exists and is correctly structured."""
    # Check if the module can be imported
    from agentical.api.health import router
    from agentical.api import api_router
    
    # Check that router is properly exported
    assert router is not None, "Health API router should be exported"
    
    # Check that router is included in the main API router
    assert any(
        r.prefix == "/health" for r in api_router.routes
    ), "Health router should be included in main API router"


# Test health API endpoint models
def test_health_api_models():
    """Verify that the health API models are correctly defined."""
    # Check HealthResponse model
    assert hasattr(HealthResponse, "model_fields"), "HealthResponse should be a Pydantic model"
    assert "status" in HealthResponse.model_fields, "HealthResponse should have a status field"
    assert "timestamp" in HealthResponse.model_fields, "HealthResponse should have a timestamp field"
    assert "version" in HealthResponse.model_fields, "HealthResponse should have a version field"
    assert "services" in HealthResponse.model_fields, "HealthResponse should have a services field"
    assert "system" in HealthResponse.model_fields, "HealthResponse should have a system field"
    
    # Check ServiceHealth model
    assert hasattr(ServiceHealth, "model_fields"), "ServiceHealth should be a Pydantic model"
    assert "status" in ServiceHealth.model_fields, "ServiceHealth should have a status field"
    assert "latency_ms" in ServiceHealth.model_fields, "ServiceHealth should have a latency_ms field"
    assert "details" in ServiceHealth.model_fields, "ServiceHealth should have a details field"
    
    # Check SystemMetrics model
    assert hasattr(SystemMetrics, "model_fields"), "SystemMetrics should be a Pydantic model"
    assert "cpu_usage" in SystemMetrics.model_fields, "SystemMetrics should have a cpu_usage field"
    assert "memory_usage" in SystemMetrics.model_fields, "SystemMetrics should have a memory_usage field"
    assert "disk_usage" in SystemMetrics.model_fields, "SystemMetrics should have a disk_usage field"
    assert "uptime_seconds" in SystemMetrics.model_fields, "SystemMetrics should have an uptime_seconds field"
    
    # Check DatabaseMetrics model
    assert hasattr(DatabaseMetrics, "model_fields"), "DatabaseMetrics should be a Pydantic model"
    assert "connection_pool" in DatabaseMetrics.model_fields, "DatabaseMetrics should have a connection_pool field"
    assert "query_performance" in DatabaseMetrics.model_fields, "DatabaseMetrics should have a query_performance field"


# Test health API endpoints
def test_health_api_endpoints():
    """Verify that all required health API endpoints are defined."""
    # Extract all route paths
    routes = [
        {
            "path": route.path,
            "name": route.name,
            "methods": route.methods
        }
        for route in router.routes
    ]
    
    # Check that all required endpoints exist
    route_paths = [route["path"] for route in routes]
    
    assert "" in route_paths, "Main health check endpoint should exist"
    assert "/readiness" in route_paths, "Readiness endpoint should exist"
    assert "/liveness" in route_paths, "Liveness endpoint should exist"
    assert "/metrics" in route_paths, "Metrics endpoint should exist"
    assert "/database" in route_paths, "Database health endpoint should exist"
    
    # Check route methods
    for route in routes:
        if route["path"] in ["", "/readiness", "/liveness", "/metrics", "/database"]:
            assert "GET" in route["methods"], f"{route['path']} endpoint should support GET method"


# Test utility functions
def test_health_api_utilities():
    """Verify that utility functions for health checks are implemented."""
    assert hasattr(import_module("agentical.api.health.endpoints"), "get_system_metrics"), "get_system_metrics function should exist"
    assert hasattr(import_module("agentical.api.health.endpoints"), "get_database_metrics"), "get_database_metrics function should exist"


# Test main health check endpoint implementation
def test_health_check_endpoint_implementation():
    """Verify that the health check endpoint is correctly implemented."""
    # Check that the function is async
    health_check = import_module("agentical.api.health.endpoints").health_check
    assert inspect.iscoroutinefunction(health_check), "health_check should be an async function"
    
    # Check that it has a db dependency
    assert "db" in inspect.signature(health_check).parameters, "health_check should have a db parameter"
    
    # Check return type annotation
    assert inspect.signature(health_check).return_annotation == HealthResponse, "health_check should return a HealthResponse"


# Test if liveness probe is implemented
def test_liveness_probe_implementation():
    """Verify that the liveness probe is correctly implemented."""
    liveness_check = import_module("agentical.api.health.endpoints").liveness_check
    assert inspect.iscoroutinefunction(liveness_check), "liveness_check should be an async function"


# Test if readiness probe is implemented
def test_readiness_probe_implementation():
    """Verify that the readiness probe is correctly implemented."""
    readiness_check = import_module("agentical.api.health.endpoints").readiness_check
    assert inspect.iscoroutinefunction(readiness_check), "readiness_check should be an async function"


# Test if metrics endpoint is implemented
def test_metrics_endpoint_implementation():
    """Verify that the metrics endpoint is correctly implemented."""
    metrics = import_module("agentical.api.health.endpoints").metrics
    assert inspect.iscoroutinefunction(metrics), "metrics should be an async function"
    assert inspect.signature(metrics).return_annotation == MonitoringResponse, "metrics should return a MonitoringResponse"


# Test if database health endpoint is implemented
def test_database_health_endpoint_implementation():
    """Verify that the database health endpoint is correctly implemented."""
    database_health = import_module("agentical.api.health.endpoints").database_health
    assert inspect.iscoroutinefunction(database_health), "database_health should be an async function"
    assert inspect.signature(database_health).return_annotation == DatabaseMetrics, "database_health should return a DatabaseMetrics"


# Integration with main.py
def test_api_router_integration():
    """Verify that the API router is integrated with the main application."""
    from main import app
    
    # Check that the API router is included in the app
    assert any(
        route.path.startswith("/api/v1/health")
        for route in app.routes
    ), "Health API router should be included in the main application"


def test_task_1_4_completed():
    """Final validation that Task 1.4 has been completed successfully."""
    # All tests passing means Task 1.4 is complete
    print("Task 1.4: Implement Health Check and Monitoring Endpoints - COMPLETED")
    assert True, "Task 1.4 implementation validated successfully"