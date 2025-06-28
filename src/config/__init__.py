"""
Configuration Module for Agentical Framework

This module provides comprehensive configuration management for the entire
Agentical framework, including agents, tools, workflows, and system settings.

Key Components:
- AgentConfigModel: Pydantic-based agent configuration with validation
- ToolConfig: Tool configuration and management
- WorkflowConfig: Workflow configuration and orchestration
- ConfigurationManager: Centralized configuration management

Features:
- Hierarchical configuration (System → Project → Agent → Runtime)
- Environment variable integration
- Configuration validation and type checking
- Dynamic configuration updates
- Configuration file management (JSON/YAML)
- Configuration templates and profiles
"""

from .agent_config import (
    ConfigurationLevel,
    AgentCapabilityType,
    AgentCapabilityConfig,
    ToolConfig,
    WorkflowStepConfig,
    WorkflowConfig,
    AgentConfigModel,
    ConfigurationManager,
    get_config_manager,
    reload_configuration
)

__all__ = [
    "ConfigurationLevel",
    "AgentCapabilityType",
    "AgentCapabilityConfig", 
    "ToolConfig",
    "WorkflowStepConfig",
    "WorkflowConfig",
    "AgentConfigModel",
    "ConfigurationManager",
    "get_config_manager",
    "reload_configuration"
]