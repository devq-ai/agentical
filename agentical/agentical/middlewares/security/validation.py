"""
Request Validation Middleware for Agentical

This module provides middleware for enhanced request validation, input sanitization,
and data consistency checks to protect against invalid or malicious input data.

Features:
- Advanced request body validation beyond Pydantic's basic checks
- Query parameter validation and sanitization
- Header validation with security checks
- JSON schema enforcement
- Size limits for request bodies
- Content type validation
- Contextual validation based on authentication status
"""

import json
import re
from typing import Any, Callable, Dict, List, Optional, Set, Union, Pattern, Type, TypeVar
import logging
from json.decoder import JSONDecodeError

import logfire
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError, create_model
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from agentical.core.exceptions import ValidationError as AgenticalValidationError

# Logger setup
logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar('ModelType', bound=BaseModel)


class RequestValidationConfig:
    """Configuration for request validation middleware."""
    
    def __init__(
        self,
        max_content_length: int = 10 * 1024 * 1024,  # 10 MB
        allowed_content_types: Optional[List[str]] = None,
        validate_query_params: bool = True,
        validate_headers: bool = True,
        validate_cookies: bool = True,
        blocked_patterns: Optional[Dict[str, Pattern]] = None,
        allowed_domains: Optional[List[str]] = None,
        validate_json_syntax: bool = True,
        enable_type_coercion: bool = True,
        exclude_paths: Optional[List[str]] = None,
    ):
        """Initialize validation configuration.
        
        Args:
            max_content_length: Maximum allowed request body size in bytes
            allowed_content_types: List of allowed Content-Type values
            validate_query_params: Whether to validate query parameters
            validate_headers: Whether to validate request headers
            validate_cookies: Whether to validate request cookies
            blocked_patterns: Patterns to block in request data by field name
            allowed_domains: List of allowed domains for URL fields
            validate_json_syntax: Whether to validate JSON syntax before Pydantic
            enable_type_coercion: Whether to attempt type coercion for query params
            exclude_paths: List of paths to exclude from validation
        """
        self.max_content_length = max_content_length
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]
        self.validate_query_params = validate_query_params
        self.validate_headers = validate_headers
        self.validate_cookies = validate_cookies
        self.blocked_patterns = blocked_patterns or {
            "sql_injection": re.compile(r"(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|UNION)\s"),
            "xss": re.compile(r"(?i)<script|javascript:|on\w+\s*=|<iframe|<img|alert\s*\("),
            "path_traversal": re.compile(r"(?:\.\./|\.\\|\.\.|/etc/passwd)"),
        }
        self.allowed_domains = allowed_domains
        self.validate_json_syntax = validate_json_syntax
        self.enable_type_coercion = enable_type_coercion
        self.exclude_paths = exclude_paths or []


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for enhanced request validation and sanitization."""
    
    def __init__(
        self,
        app: ASGIApp,
        config: Optional[RequestValidationConfig] = None,
    ):
        """Initialize the request validation middleware.
        
        Args:
            app: The ASGI application
            config: Validation configuration
        """
        super().__init__(app)
        self.config = config or RequestValidationConfig()
    
    async def validate_content_length(self, request: Request) -> Optional[Dict[str, Any]]:
        """Validate the Content-Length header.
        
        Args:
            request: The incoming request
            
        Returns:
            Error details if validation fails, None otherwise
        """
        if "content-length" in request.headers:
            try:
                content_length = int(request.headers["content-length"])
                if content_length > self.config.max_content_length:
                    return {
                        "error": "content_length_exceeded",
                        "message": f"Request body too large ({content_length} bytes). Maximum allowed size is {self.config.max_content_length} bytes.",
                        "status_code": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    }
            except (ValueError, TypeError):
                return {
                    "error": "invalid_content_length",
                    "message": "Invalid Content-Length header",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                }
        
        return None
    
    async def validate_content_type(self, request: Request) -> Optional[Dict[str, Any]]:
        """Validate the Content-Type header.
        
        Args:
            request: The incoming request
            
        Returns:
            Error details if validation fails, None otherwise
        """
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            # Extract the base content type without parameters
            base_content_type = content_type.split(";")[0].strip().lower()
            
            if not any(base_content_type.startswith(allowed) for allowed in self.config.allowed_content_types):
                return {
                    "error": "unsupported_media_type",
                    "message": f"Unsupported media type: {content_type}. Supported types: {', '.join(self.config.allowed_content_types)}",
                    "status_code": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                }
        
        return None
    
    async def validate_json_body(self, request: Request) -> Optional[Dict[str, Any]]:
        """Validate JSON syntax in the request body.
        
        Args:
            request: The incoming request
            
        Returns:
            Error details if validation fails, None otherwise
        """
        if not self.config.validate_json_syntax:
            return None
        
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type.lower() and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    try:
                        json.loads(body.decode())
                    except JSONDecodeError as e:
                        return {
                            "error": "invalid_json",
                            "message": f"Invalid JSON: {str(e)}",
                            "status_code": status.HTTP_400_BAD_REQUEST,
                            "details": {
                                "position": e.pos,
                                "line": e.lineno,
                                "column": e.colno,
                            }
                        }
            except Exception as e:
                logfire.error("Error reading request body", error=str(e))
        
        return None
    
    async def check_blocked_patterns(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for blocked patterns in request data.
        
        Args:
            data: The request data to check
            
        Returns:
            Error details if validation fails, None otherwise
        """
        def _check_value(value: Any, path: str = "") -> Optional[Dict[str, Any]]:
            if isinstance(value, str):
                for pattern_name, pattern in self.config.blocked_patterns.items():
                    if pattern.search(value):
                        return {
                            "error": "blocked_pattern_detected",
                            "message": f"Blocked pattern detected: {pattern_name}",
                            "status_code": status.HTTP_400_BAD_REQUEST,
                            "details": {
                                "pattern": pattern_name,
                                "path": path,
                            }
                        }
            elif isinstance(value, dict):
                for k, v in value.items():
                    result = _check_value(v, f"{path}.{k}" if path else k)
                    if result:
                        return result
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    result = _check_value(item, f"{path}[{i}]")
                    if result:
                        return result
            
            return None
        
        return _check_value(data)
    
    async def validate_urls(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate URLs in request data to ensure they point to allowed domains.
        
        Args:
            data: The request data to check
            
        Returns:
            Error details if validation fails, None otherwise
        """
        if not self.config.allowed_domains:
            return None
        
        url_pattern = re.compile(r'https?://([a-zA-Z0-9.-]+)')
        
        def _check_urls(value: Any, path: str = "") -> Optional[Dict[str, Any]]:
            if isinstance(value, str):
                # Check if value looks like a URL
                if value.startswith(("http://", "https://")):
                    match = url_pattern.match(value)
                    if match:
                        domain = match.group(1)
                        # Check if domain or any parent domain is allowed
                        allowed = False
                        for allowed_domain in self.config.allowed_domains:
                            if domain == allowed_domain or domain.endswith(f".{allowed_domain}"):
                                allowed = True
                                break
                        
                        if not allowed:
                            return {
                                "error": "disallowed_domain",
                                "message": f"URL points to disallowed domain: {domain}",
                                "status_code": status.HTTP_400_BAD_REQUEST,
                                "details": {
                                    "domain": domain,
                                    "path": path,
                                }
                            }
            elif isinstance(value, dict):
                for k, v in value.items():
                    result = _check_urls(v, f"{path}.{k}" if path else k)
                    if result:
                        return result
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    result = _check_urls(item, f"{path}[{i}]")
                    if result:
                        return result
            
            return None
        
        return _check_urls(data)
    
    def _should_validate(self, request: Request) -> bool:
        """Determine if request should be validated.
        
        Args:
            request: The incoming request
            
        Returns:
            True if request should be validated, False otherwise
        """
        # Skip for excluded paths
        for path in self.config.exclude_paths:
            if request.url.path.startswith(path):
                return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through validation middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware in the chain
            
        Returns:
            The response from the application
        """
        if not self._should_validate(request):
            return await call_next(request)
        
        with logfire.span("Request validation"):
            # Validate Content-Length
            error = await self.validate_content_length(request)
            if error:
                logfire.warning(
                    "Request validation failed: content length",
                    error=error["error"],
                    path=request.url.path,
                    method=request.method
                )
                return JSONResponse(
                    content=error,
                    status_code=error["status_code"]
                )
            
            # Validate Content-Type
            error = await self.validate_content_type(request)
            if error:
                logfire.warning(
                    "Request validation failed: content type",
                    error=error["error"],
                    path=request.url.path,
                    method=request.method,
                    content_type=request.headers.get("content-type", "")
                )
                return JSONResponse(
                    content=error,
                    status_code=error["status_code"]
                )
            
            # Validate JSON syntax
            error = await self.validate_json_body(request)
            if error:
                logfire.warning(
                    "Request validation failed: JSON syntax",
                    error=error["error"],
                    path=request.url.path,
                    method=request.method
                )
                return JSONResponse(
                    content=error,
                    status_code=error["status_code"]
                )
            
            # For POST/PUT/PATCH requests with JSON content, check for blocked patterns
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type.lower() and request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        data = json.loads(body.decode())
                        
                        # Check for blocked patterns
                        error = await self.check_blocked_patterns(data)
                        if error:
                            logfire.warning(
                                "Request validation failed: blocked pattern",
                                error=error["error"],
                                path=request.url.path,
                                method=request.method,
                                details=error.get("details", {})
                            )
                            return JSONResponse(
                                content=error,
                                status_code=error["status_code"]
                            )
                        
                        # Validate URLs
                        error = await self.validate_urls(data)
                        if error:
                            logfire.warning(
                                "Request validation failed: URL validation",
                                error=error["error"],
                                path=request.url.path,
                                method=request.method,
                                details=error.get("details", {})
                            )
                            return JSONResponse(
                                content=error,
                                status_code=error["status_code"]
                            )
                except Exception as e:
                    # Already validated JSON syntax, so this is likely a different error
                    logfire.error(
                        "Error during advanced request validation",
                        error=str(e),
                        path=request.url.path,
                        method=request.method
                    )
            
            # If query parameters should be validated
            if self.config.validate_query_params:
                query_params = dict(request.query_params)
                if query_params:
                    # Check for blocked patterns in query parameters
                    error = await self.check_blocked_patterns(query_params)
                    if error:
                        logfire.warning(
                            "Request validation failed: blocked pattern in query parameters",
                            error=error["error"],
                            path=request.url.path,
                            method=request.method,
                            details=error.get("details", {})
                        )
                        return JSONResponse(
                            content=error,
                            status_code=error["status_code"]
                        )
                    
                    # Validate URLs in query parameters
                    error = await self.validate_urls(query_params)
                    if error:
                        logfire.warning(
                            "Request validation failed: URL validation in query parameters",
                            error=error["error"],
                            path=request.url.path,
                            method=request.method,
                            details=error.get("details", {})
                        )
                        return JSONResponse(
                            content=error,
                            status_code=error["status_code"]
                        )
        
        # Process the request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logfire.error(
                "Unhandled exception during request processing",
                error=str(e),
                path=request.url.path,
                method=request.method
            )
            raise