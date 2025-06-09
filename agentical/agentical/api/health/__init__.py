"""
Health and Monitoring API endpoints for Agentical

This module provides health check, monitoring, and observability endpoints
for the Agentical framework, enabling infrastructure monitoring and status reporting.
"""

from .endpoints import router

__all__ = ["router"]