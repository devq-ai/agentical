"""
Security Middleware Module for Agentical

This module provides middleware components for enhancing security, input validation,
and rate limiting in the Agentical framework.

Features:
- Rate limiting with configurable limits and strategies
- Security headers for common vulnerabilities
- Request validation and sanitization
- Bot and attack protection
"""

from .rate_limiting import RateLimitMiddleware, RateLimitConfig
from .security_headers import SecurityHeadersMiddleware
from .validation import RequestValidationMiddleware
from .sanitization import sanitize_input, sanitize_html, sanitize_filename
from .bot_protection import BotProtectionMiddleware

__all__ = [
    "RateLimitMiddleware",
    "RateLimitConfig",
    "SecurityHeadersMiddleware",
    "RequestValidationMiddleware", 
    "BotProtectionMiddleware",
    "sanitize_input",
    "sanitize_html",
    "sanitize_filename",
]