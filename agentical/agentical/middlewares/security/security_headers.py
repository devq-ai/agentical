"""
Security Headers Middleware for Agentical

This module provides middleware to add security headers to responses,
protecting against common web vulnerabilities like XSS, clickjacking,
and content type sniffing.

Features:
- Content Security Policy (CSP) for XSS protection
- X-Frame-Options for clickjacking protection
- X-Content-Type-Options for MIME sniffing protection
- Strict-Transport-Security for HTTPS enforcement
- Referrer-Policy for privacy protection
- Permissions-Policy for feature control
"""

from typing import Dict, List, Optional, Set, Union, Callable
import logging

import logfire
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# Logger setup
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses."""
    
    def __init__(
        self,
        app: ASGIApp,
        csp_directives: Optional[Dict[str, Union[str, List[str]]]] = None,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        frame_options: str = "DENY",
        content_type_options: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[Dict[str, str]] = None,
        xss_protection: bool = True,
        disable_for_paths: Optional[List[str]] = None,
    ):
        """Initialize the security headers middleware.
        
        Args:
            app: The ASGI application
            csp_directives: Content Security Policy directives
            hsts_max_age: Strict-Transport-Security max-age in seconds
            hsts_include_subdomains: Whether to include subdomains in HSTS
            hsts_preload: Whether to enable HSTS preloading
            frame_options: X-Frame-Options value (DENY, SAMEORIGIN)
            content_type_options: Whether to add X-Content-Type-Options: nosniff
            referrer_policy: Referrer-Policy value
            permissions_policy: Permissions Policy directives
            xss_protection: Whether to add X-XSS-Protection header
            disable_for_paths: List of paths to disable security headers for
        """
        super().__init__(app)
        
        # Default CSP if none provided
        self.csp_directives = csp_directives or {
            "default-src": ["'self'"],
            "img-src": ["'self'", "data:"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "script-src": ["'self'"],
            "font-src": ["'self'"],
            "object-src": ["'none'"],
            "frame-ancestors": ["'none'"],
        }
        
        # Default permissions policy if none provided
        self.permissions_policy = permissions_policy or {
            "geolocation": "self",
            "microphone": "self",
            "camera": "self",
            "payment": "self",
        }
        
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.referrer_policy = referrer_policy
        self.xss_protection = xss_protection
        self.disable_for_paths = disable_for_paths or []
    
    def _build_csp_header(self) -> str:
        """Build the Content-Security-Policy header value.
        
        Returns:
            The CSP header value as a string
        """
        directives = []
        
        for directive, sources in self.csp_directives.items():
            if isinstance(sources, str):
                directives.append(f"{directive} {sources}")
            else:
                directives.append(f"{directive} {' '.join(sources)}")
        
        return "; ".join(directives)
    
    def _build_permissions_policy_header(self) -> str:
        """Build the Permissions-Policy header value.
        
        Returns:
            The Permissions-Policy header value as a string
        """
        directives = []
        
        for feature, allowlist in self.permissions_policy.items():
            if allowlist == "":
                directives.append(f"{feature}=()")
            else:
                directives.append(f"{feature}=({allowlist})")
        
        return ", ".join(directives)
    
    def _build_hsts_header(self) -> str:
        """Build the Strict-Transport-Security header value.
        
        Returns:
            The HSTS header value as a string
        """
        hsts_parts = [f"max-age={self.hsts_max_age}"]
        
        if self.hsts_include_subdomains:
            hsts_parts.append("includeSubDomains")
        
        if self.hsts_preload:
            hsts_parts.append("preload")
        
        return "; ".join(hsts_parts)
    
    def _should_add_headers(self, request: Request) -> bool:
        """Determine if security headers should be added to the response.
        
        Args:
            request: The incoming request
            
        Returns:
            True if headers should be added, False otherwise
        """
        # Skip for excluded paths
        for path in self.disable_for_paths:
            if request.url.path.startswith(path):
                return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add security headers to the response.
        
        Args:
            request: The incoming request
            call_next: The next middleware in the chain
            
        Returns:
            The response from the application with security headers
        """
        response = await call_next(request)
        
        if not self._should_add_headers(request):
            return response
        
        with logfire.span("Add security headers"):
            # Content Security Policy
            response.headers["Content-Security-Policy"] = self._build_csp_header()
            
            # X-Frame-Options for clickjacking protection
            response.headers["X-Frame-Options"] = self.frame_options
            
            # X-Content-Type-Options to prevent MIME sniffing
            if self.content_type_options:
                response.headers["X-Content-Type-Options"] = "nosniff"
            
            # Referrer-Policy for privacy
            response.headers["Referrer-Policy"] = self.referrer_policy
            
            # Permissions-Policy for feature control
            response.headers["Permissions-Policy"] = self._build_permissions_policy_header()
            
            # Strict-Transport-Security for HTTPS enforcement
            # Only add HSTS header on HTTPS connections
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = self._build_hsts_header()
            
            # X-XSS-Protection as an additional layer of protection
            if self.xss_protection:
                response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response