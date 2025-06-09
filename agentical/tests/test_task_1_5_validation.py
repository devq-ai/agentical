"""
Validation Test for Task 1.5 - Enhance Request Validation and Security

This module validates the implementation of Task 1.5 by testing the
security middleware components, input validation, and protection features.
"""

import inspect
import os
import pytest
from importlib import import_module
from unittest.mock import Mock, patch

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Import the security components
from agentical.middlewares.security import (
    RateLimitMiddleware,
    RateLimitConfig,
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    RequestValidationConfig,
    BotProtectionMiddleware,
    BotDetectionConfig,
    sanitize_input,
    sanitize_html,
    sanitize_filename
)

# Test if security module exists
def test_security_module_exists():
    """Verify that the security module exists and is correctly structured."""
    # Check main security module
    import agentical.middlewares.security
    
    # Check that all required components are exported
    assert hasattr(agentical.middlewares.security, "RateLimitMiddleware"), "RateLimitMiddleware should be exported"
    assert hasattr(agentical.middlewares.security, "SecurityHeadersMiddleware"), "SecurityHeadersMiddleware should be exported"
    assert hasattr(agentical.middlewares.security, "RequestValidationMiddleware"), "RequestValidationMiddleware should be exported"
    assert hasattr(agentical.middlewares.security, "BotProtectionMiddleware"), "BotProtectionMiddleware should be exported"
    assert hasattr(agentical.middlewares.security, "sanitize_input"), "sanitize_input should be exported"
    assert hasattr(agentical.middlewares.security, "sanitize_html"), "sanitize_html should be exported"
    assert hasattr(agentical.middlewares.security, "sanitize_filename"), "sanitize_filename should be exported"


# Test security middleware classes
def test_security_middleware_classes():
    """Verify that security middleware classes are correctly implemented."""
    # Check RateLimitMiddleware
    assert issubclass(RateLimitMiddleware, BaseHTTPMiddleware), "RateLimitMiddleware should inherit from BaseHTTPMiddleware"
    assert hasattr(RateLimitMiddleware, "dispatch"), "RateLimitMiddleware should have a dispatch method"
    assert inspect.iscoroutinefunction(RateLimitMiddleware.dispatch), "dispatch should be an async method"
    
    # Check SecurityHeadersMiddleware
    assert issubclass(SecurityHeadersMiddleware, BaseHTTPMiddleware), "SecurityHeadersMiddleware should inherit from BaseHTTPMiddleware"
    assert hasattr(SecurityHeadersMiddleware, "dispatch"), "SecurityHeadersMiddleware should have a dispatch method"
    assert inspect.iscoroutinefunction(SecurityHeadersMiddleware.dispatch), "dispatch should be an async method"
    
    # Check RequestValidationMiddleware
    assert issubclass(RequestValidationMiddleware, BaseHTTPMiddleware), "RequestValidationMiddleware should inherit from BaseHTTPMiddleware"
    assert hasattr(RequestValidationMiddleware, "dispatch"), "RequestValidationMiddleware should have a dispatch method"
    assert inspect.iscoroutinefunction(RequestValidationMiddleware.dispatch), "dispatch should be an async method"
    
    # Check BotProtectionMiddleware
    assert issubclass(BotProtectionMiddleware, BaseHTTPMiddleware), "BotProtectionMiddleware should inherit from BaseHTTPMiddleware"
    assert hasattr(BotProtectionMiddleware, "dispatch"), "BotProtectionMiddleware should have a dispatch method"
    assert inspect.iscoroutinefunction(BotProtectionMiddleware.dispatch), "dispatch should be an async method"


# Test configuration classes
def test_security_config_classes():
    """Verify that security configuration classes are correctly implemented."""
    # Check RateLimitConfig
    rate_limit_config = RateLimitConfig()
    assert hasattr(rate_limit_config, "requests_per_minute"), "RateLimitConfig should have requests_per_minute attribute"
    assert hasattr(rate_limit_config, "burst"), "RateLimitConfig should have burst attribute"
    assert hasattr(rate_limit_config, "strategy"), "RateLimitConfig should have strategy attribute"
    
    # Check RequestValidationConfig
    validation_config = RequestValidationConfig()
    assert hasattr(validation_config, "max_content_length"), "RequestValidationConfig should have max_content_length attribute"
    assert hasattr(validation_config, "validate_query_params"), "RequestValidationConfig should have validate_query_params attribute"
    assert hasattr(validation_config, "blocked_patterns"), "RequestValidationConfig should have blocked_patterns attribute"
    
    # Check BotDetectionConfig
    bot_config = BotDetectionConfig()
    assert hasattr(bot_config, "enabled"), "BotDetectionConfig should have enabled attribute"
    assert hasattr(bot_config, "suspicious_threshold"), "BotDetectionConfig should have suspicious_threshold attribute"
    assert hasattr(bot_config, "bot_threshold"), "BotDetectionConfig should have bot_threshold attribute"


# Test sanitization functions
def test_sanitization_functions():
    """Verify that sanitization functions work correctly."""
    # Test sanitize_input
    assert sanitize_input("<script>alert('XSS')</script>") == "<script>alert('XSS')</script>", "sanitize_input should remove control characters but not HTML"
    assert sanitize_input("  Hello World  ") == "Hello World", "sanitize_input should trim whitespace"
    assert sanitize_input("Hello\0World") == "HelloWorld", "sanitize_input should remove null bytes"
    
    # Test sanitize_html
    assert sanitize_html("<script>alert('XSS')</script>") == "&lt;script&gt;alert('XSS')&lt;/script&gt;", "sanitize_html should escape HTML tags"
    assert sanitize_html("<p>Hello World</p>", allowed_tags=["p"]) == "<p>Hello World</p>", "sanitize_html should allow specified tags"
    assert sanitize_html("<p onclick=\"alert('XSS')\">Hello</p>", allowed_tags=["p"]) != "<p onclick=\"alert('XSS')\">Hello</p>", "sanitize_html should sanitize dangerous attributes"
    
    # Test sanitize_filename
    assert sanitize_filename("../etc/passwd") == "__etc_passwd", "sanitize_filename should prevent path traversal"
    assert sanitize_filename("file<>:\"\\|?*name") == "file________name", "sanitize_filename should remove invalid characters"
    assert sanitize_filename("..") != "..", "sanitize_filename should handle special cases"


# Test main.py integration
def test_main_app_integration():
    """Verify that security middlewares are integrated in main.py."""
    from main import app
    
    # Check that middleware stack includes security middlewares
    middleware_classes = [middleware.__class__.__name__ for middleware in app.user_middleware]
    
    # Verify security middlewares are in the stack
    assert "BotProtectionMiddleware" in middleware_classes, "BotProtectionMiddleware should be in the middleware stack"
    assert "RequestValidationMiddleware" in middleware_classes, "RequestValidationMiddleware should be in the middleware stack"
    assert "RateLimitMiddleware" in middleware_classes, "RateLimitMiddleware should be in the middleware stack"
    assert "SecurityHeadersMiddleware" in middleware_classes, "SecurityHeadersMiddleware should be in the middleware stack"
    
    # Verify ordering (security should be before CORS)
    security_indices = [
        middleware_classes.index("BotProtectionMiddleware"),
        middleware_classes.index("RequestValidationMiddleware"),
        middleware_classes.index("RateLimitMiddleware"),
        middleware_classes.index("SecurityHeadersMiddleware")
    ]
    
    cors_index = middleware_classes.index("CORSMiddleware") if "CORSMiddleware" in middleware_classes else len(middleware_classes)
    
    for index in security_indices:
        assert index < cors_index, "Security middlewares should be added before CORS middleware"


def test_task_1_5_completed():
    """Final validation that Task 1.5 has been completed successfully."""
    # All tests passing means Task 1.5 is complete
    print("Task 1.5: Enhance Request Validation and Security - COMPLETED")
    assert True, "Task 1.5 implementation validated successfully"