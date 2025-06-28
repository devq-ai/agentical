"""
Agent Development Toolkit

This module provides comprehensive tools for local agent development, including:
- Agent generation and scaffolding
- Development environment setup  
- Testing frameworks
- Local agent registry
- Hot reloading capabilities
- Deployment utilities

Features:
- Template-based agent generation
- Complete development environment scaffolding
- Integrated testing and validation
- Visual Studio Code integration
- Command-line development tools
"""

from .agent_generator import AgentGenerator, AgentTemplate

__all__ = [
    "AgentGenerator",
    "AgentTemplate"
]