"""
Configuration Integration Module

This module provides integration between the new configuration framework
and the existing Agentical infrastructure, including agents, registries,
and execution systems.

Features:
- Agent configuration injection
- Dynamic configuration updates
- Configuration-driven agent creation
- Tool configuration management
- Workflow configuration execution
"""

import logging
from typing import Dict, Any, Optional, List, Type
from pathlib import Path

import logfire

from .agent_config import (
    ConfigurationManager,
    AgentConfigModel,
    ToolConfig,
    WorkflowConfig,
    get_config_manager
)

logger = logging.getLogger(__name__)


class ConfigurationIntegrator:
    """
    Integrates configuration framework with existing Agentical infrastructure
    
    Provides seamless configuration injection and management for agents,
    tools, and workflows.
    """
    
    def __init__(self, config_manager: Optional[ConfigurationManager] = None):
        """
        Initialize configuration integrator
        
        Args:
            config_manager: Optional configuration manager instance
        """
        self.config_manager = config_manager or get_config_manager()
        
        # Integration state
        self.integrated_agents: Dict[str, Any] = {}
        self.configured_tools: Dict[str, ToolConfig] = {}
        self.active_workflows: Dict[str, WorkflowConfig] = {}
        
        logger.info("Configuration integrator initialized")
    
    def configure_agent_from_config(
        self, 
        agent_id: str, 
        agent_instance: Any,
        override_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Apply configuration to an existing agent instance
        
        Args:
            agent_id: Agent identifier
            agent_instance: Agent instance to configure
            override_config: Optional configuration overrides
        """
        with logfire.span("Configuring agent from config", agent_id=agent_id):
            # Get agent configuration
            agent_config = self.config_manager.get_agent_config(agent_id)
            
            if not agent_config:
                logger.warning(f"No configuration found for agent: {agent_id}")
                return
            
            # Apply configuration overrides
            if override_config:
                config_dict = agent_config.dict()
                config_dict.update(override_config)
                agent_config = AgentConfigModel(**config_dict)
            
            # Apply configuration to agent
            self._apply_agent_configuration(agent_instance, agent_config)
            
            # Track configured agent
            self.integrated_agents[agent_id] = {
                "instance": agent_instance,
                "config": agent_config,
                "configured_at": logfire.current_span().start_time
            }
            
            logger.info(f"Applied configuration to agent: {agent_id}")
    
    def _apply_agent_configuration(self, agent_instance: Any, config: AgentConfigModel) -> None:
        """Apply configuration settings to agent instance"""
        
        # Apply basic configuration
        if hasattr(agent_instance, 'metadata'):
            metadata = agent_instance.metadata
            metadata.name = config.name
            metadata.description = config.description
            metadata.version = config.version
            metadata.author = config.author
            metadata.tags = config.tags
        
        # Apply capability configuration
        if hasattr(agent_instance, '_configure_capabilities'):
            agent_instance._configure_capabilities(config.capabilities)
        
        # Apply tool configuration
        if hasattr(agent_instance, '_configure_tools'):
            agent_instance._configure_tools(config.tools)
        
        # Apply resource limits
        if hasattr(agent_instance, '_configure_resources'):
            agent_instance._configure_resources({
                "memory_limit_mb": config.memory_limit_mb,
                "cpu_limit_percent": config.cpu_limit_percent,
                "max_concurrent_executions": config.max_concurrent_executions
            })
        
        # Apply security configuration
        if hasattr(agent_instance, '_configure_security'):
            agent_instance._configure_security({
                "security_level": config.security_level,
                "allowed_operations": config.allowed_operations,
                "resource_quotas": config.resource_quotas
            })
        
        # Apply monitoring configuration
        if hasattr(agent_instance, '_configure_monitoring'):
            agent_instance._configure_monitoring({
                "logging_level": config.logging_level,
                "metrics_enabled": config.metrics_enabled,
                "trace_enabled": config.trace_enabled,
                "health_check_interval_seconds": config.health_check_interval_seconds
            })
    
    def create_agent_from_config(
        self, 
        agent_id: str,
        agent_registry: Any,
        override_config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create new agent instance from configuration
        
        Args:
            agent_id: Agent identifier
            agent_registry: Agent registry for creation
            override_config: Optional configuration overrides
            
        Returns:
            Configured agent instance
        """
        with logfire.span("Creating agent from config", agent_id=agent_id):
            # Get agent configuration
            agent_config = self.config_manager.get_agent_config(agent_id)
            
            if not agent_config:
                raise ValueError(f"No configuration found for agent: {agent_id}")
            
            # Apply configuration overrides
            if override_config:
                config_dict = agent_config.dict()
                config_dict.update(override_config)
                agent_config = AgentConfigModel(**config_dict)
            
            # Create agent instance
            agent_instance = agent_registry.get_or_create_agent(
                agent_id, 
                agent_config.type
            )
            
            # Apply configuration
            self._apply_agent_configuration(agent_instance, agent_config)
            
            # Track configured agent
            self.integrated_agents[agent_id] = {
                "instance": agent_instance,
                "config": agent_config,
                "configured_at": logfire.current_span().start_time
            }
            
            logger.info(f"Created and configured agent: {agent_id}")
            return agent_instance
    
    def configure_tools_from_config(self, tool_manager: Any) -> None:
        """
        Configure tools from configuration
        
        Args:
            tool_manager: Tool manager instance
        """
        with logfire.span("Configuring tools from config"):
            configured_count = 0
            
            for tool_name, tool_config in self.config_manager.tool_configs.items():
                try:
                    # Configure tool in manager
                    if hasattr(tool_manager, 'configure_tool'):
                        tool_manager.configure_tool(tool_name, tool_config)
                    
                    # Track configured tool
                    self.configured_tools[tool_name] = tool_config
                    configured_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to configure tool {tool_name}: {e}")
            
            logger.info(f"Configured {configured_count} tools from configuration")
    
    def get_workflow_execution_plan(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution plan for workflow from configuration
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow execution plan or None if not found
        """
        workflow_config = self.config_manager.get_workflow_config(workflow_id)
        
        if not workflow_config:
            return None
        
        # Build execution plan
        execution_plan = {
            "workflow_id": workflow_id,
            "name": workflow_config.name,
            "description": workflow_config.description,
            "version": workflow_config.version,
            "timeout_seconds": workflow_config.timeout_seconds,
            "parallel_execution": workflow_config.parallel_execution,
            "auto_retry": workflow_config.auto_retry,
            "max_retries": workflow_config.max_retries,
            "checkpoint_enabled": workflow_config.checkpoint_enabled,
            "rollback_on_failure": workflow_config.rollback_on_failure,
            "steps": []
        }
        
        # Process workflow steps
        for step in workflow_config.steps:
            step_plan = {
                "id": step.id,
                "name": step.name,
                "agent_type": step.agent_type,
                "operation": step.operation,
                "parameters": step.parameters,
                "timeout_seconds": step.timeout_seconds,
                "retry_attempts": step.retry_attempts,
                "parallel_execution": step.parallel_execution,
                "depends_on": step.depends_on,
                "conditions": step.conditions,
                "on_error": step.on_error,
                "fallback_step": step.fallback_step
            }
            execution_plan["steps"].append(step_plan)
        
        return execution_plan
    
    def update_agent_configuration(
        self, 
        agent_id: str, 
        config_updates: Dict[str, Any]
    ) -> bool:
        """
        Update agent configuration dynamically
        
        Args:
            agent_id: Agent identifier
            config_updates: Configuration updates to apply
            
        Returns:
            True if update successful, False otherwise
        """
        with logfire.span("Updating agent configuration", agent_id=agent_id):
            try:
                # Update configuration
                updated_config = self.config_manager.update_agent_config(
                    agent_id, 
                    config_updates
                )
                
                # Apply to existing agent instance if available
                if agent_id in self.integrated_agents:
                    agent_instance = self.integrated_agents[agent_id]["instance"]
                    self._apply_agent_configuration(agent_instance, updated_config)
                    
                    # Update tracking
                    self.integrated_agents[agent_id]["config"] = updated_config
                    self.integrated_agents[agent_id]["last_updated"] = logfire.current_span().start_time
                
                logger.info(f"Updated configuration for agent: {agent_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to update agent configuration {agent_id}: {e}")
                return False
    
    def validate_agent_configuration(self, agent_id: str) -> Dict[str, Any]:
        """
        Validate agent configuration
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Validation results
        """
        validation_result = {
            "agent_id": agent_id,
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        # Get agent configuration
        agent_config = self.config_manager.get_agent_config(agent_id)
        
        if not agent_config:
            validation_result["errors"].append("Agent configuration not found")
            return validation_result
        
        try:
            # Validate Pydantic model
            AgentConfigModel(**agent_config.dict())
            
            # Additional custom validations
            if not agent_config.capabilities:
                validation_result["warnings"].append("No capabilities defined")
            
            if not agent_config.tools and not agent_config.mcp_servers:
                validation_result["warnings"].append("No tools or MCP servers configured")
            
            if agent_config.memory_limit_mb < 512:
                validation_result["warnings"].append("Memory limit may be too low")
            
            validation_result["valid"] = True
            
        except Exception as e:
            validation_result["errors"].append(f"Configuration validation error: {str(e)}")
        
        return validation_result
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get overall integration status"""
        return {
            "configured_agents": len(self.integrated_agents),
            "configured_tools": len(self.configured_tools),
            "active_workflows": len(self.active_workflows),
            "agent_configs_available": len(self.config_manager.agent_configs),
            "tool_configs_available": len(self.config_manager.tool_configs),
            "workflow_configs_available": len(self.config_manager.workflow_configs),
            "agents": list(self.integrated_agents.keys()),
            "tools": list(self.configured_tools.keys()),
            "workflows": list(self.active_workflows.keys())
        }
    
    def export_configuration_templates(self, output_dir: Path) -> None:
        """
        Export configuration templates for common use cases
        
        Args:
            output_dir: Directory to export templates to
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        templates = {
            "basic_agent_template.json": {
                "agents": {
                    "template_agent": {
                        "name": "Template Agent",
                        "type": "generic",
                        "description": "Basic agent template",
                        "capabilities": [
                            {
                                "type": "reasoning",
                                "enabled": True,
                                "priority": 8
                            },
                            {
                                "type": "execution", 
                                "enabled": True,
                                "priority": 7
                            }
                        ],
                        "tools": [],
                        "mcp_servers": ["filesystem", "git"],
                        "tags": ["template", "basic"]
                    }
                }
            },
            "advanced_agent_template.json": {
                "agents": {
                    "advanced_template_agent": {
                        "name": "Advanced Template Agent",
                        "type": "super",
                        "description": "Advanced agent template with full capabilities",
                        "capabilities": [
                            {"type": "reasoning", "enabled": True, "priority": 10},
                            {"type": "planning", "enabled": True, "priority": 9},
                            {"type": "execution", "enabled": True, "priority": 8},
                            {"type": "learning", "enabled": True, "priority": 7},
                            {"type": "monitoring", "enabled": True, "priority": 6},
                            {"type": "integration", "enabled": True, "priority": 8}
                        ],
                        "max_concurrent_executions": 10,
                        "memory_limit_mb": 2048,
                        "tools": [],
                        "mcp_servers": ["context7-mcp", "ptolemies-mcp", "taskmaster-ai"],
                        "security_level": "strict",
                        "tags": ["template", "advanced", "production"]
                    }
                }
            },
            "workflow_template.json": {
                "workflows": {
                    "template_workflow": {
                        "name": "Template Workflow",
                        "description": "Basic workflow template",
                        "steps": [
                            {
                                "id": "step1",
                                "name": "First Step",
                                "agent_type": "generic",
                                "operation": "example_operation",
                                "parameters": {},
                                "timeout_seconds": 60.0
                            }
                        ],
                        "timeout_seconds": 300.0,
                        "tags": ["template", "basic"]
                    }
                }
            }
        }
        
        import json
        for filename, template in templates.items():
            template_file = output_dir / filename
            with open(template_file, 'w') as f:
                json.dump(template, f, indent=2, default=str)
        
        logger.info(f"Exported {len(templates)} configuration templates to {output_dir}")


# Global integrator instance
_integrator: Optional[ConfigurationIntegrator] = None


def get_configuration_integrator() -> ConfigurationIntegrator:
    """Get global configuration integrator instance"""
    global _integrator
    
    if _integrator is None:
        _integrator = ConfigurationIntegrator()
    
    return _integrator


def reload_configuration_integrator() -> ConfigurationIntegrator:
    """Reload configuration integrator"""
    global _integrator
    _integrator = None
    return get_configuration_integrator()


# Export main classes and functions
__all__ = [
    "ConfigurationIntegrator",
    "get_configuration_integrator", 
    "reload_configuration_integrator"
]