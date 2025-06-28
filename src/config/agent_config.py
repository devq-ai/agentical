"""
Agent Configuration Framework for Agentical

This module provides comprehensive configuration management for agents, tools, and workflows
with environment variable support, validation, and dynamic configuration updates.

Features:
- Agent-specific configuration management
- Tool configuration and validation
- Workflow configuration framework
- Environment-based configuration override
- Dynamic configuration updates
- Configuration validation and defaults
- Configuration templates and profiles
"""

import os
import json
import yaml
from typing import Dict, Any, List, Optional, Union, Type, get_type_hints
from dataclasses import dataclass, field, fields
from pathlib import Path
from enum import Enum
import logging
from datetime import datetime

import logfire
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class ConfigurationLevel(str, Enum):
    """Configuration hierarchy levels"""
    SYSTEM = "system"      # System-wide defaults
    PROJECT = "project"    # Project-level overrides
    AGENT = "agent"        # Agent-specific settings
    RUNTIME = "runtime"    # Runtime overrides


class AgentCapabilityType(str, Enum):
    """Types of agent capabilities"""
    REASONING = "reasoning"
    PLANNING = "planning"
    EXECUTION = "execution"
    COMMUNICATION = "communication"
    LEARNING = "learning"
    MONITORING = "monitoring"
    INTEGRATION = "integration"


@dataclass
class AgentCapabilityConfig:
    """Configuration for a specific agent capability"""
    type: AgentCapabilityType
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10 scale
    timeout_seconds: float = 30.0
    retry_attempts: int = 3
    

@dataclass
class ToolConfig:
    """Configuration for agent tools"""
    name: str
    type: str  # "mcp", "builtin", "external", "api"
    enabled: bool = True
    
    # Tool connection settings
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    cwd: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    
    # Tool behavior settings
    timeout_seconds: float = 30.0
    retry_attempts: int = 3
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    
    # Tool permissions and security
    permissions: List[str] = field(default_factory=list)
    sandbox_enabled: bool = True
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    
    # Tool metadata
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass 
class WorkflowStepConfig:
    """Configuration for a workflow step"""
    id: str
    name: str
    agent_type: str
    operation: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Execution settings
    timeout_seconds: float = 300.0
    retry_attempts: int = 3
    parallel_execution: bool = False
    
    # Dependencies and conditions
    depends_on: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Error handling
    on_error: str = "stop"  # "stop", "continue", "retry", "fallback"
    fallback_step: Optional[str] = None


@dataclass
class WorkflowConfig:
    """Configuration for agent workflows"""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    
    # Workflow execution settings
    steps: List[WorkflowStepConfig] = field(default_factory=list)
    parallel_execution: bool = False
    timeout_seconds: float = 1800.0  # 30 minutes default
    
    # Workflow behavior
    auto_retry: bool = True
    max_retries: int = 3
    checkpoint_enabled: bool = True
    rollback_on_failure: bool = True
    
    # Monitoring and logging
    logging_level: str = "INFO"
    metrics_enabled: bool = True
    trace_enabled: bool = True
    
    # Workflow metadata
    author: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


class AgentConfigModel(BaseModel):
    """Pydantic model for agent configuration with validation"""
    
    # Basic agent information
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    type: str = Field(..., description="Agent type (generic, super, custom)")
    description: str = Field("", description="Agent description")
    version: str = Field("1.0.0", description="Agent version")
    
    # Agent capabilities
    capabilities: List[AgentCapabilityConfig] = Field(default_factory=list)
    
    # Agent behavior configuration
    max_concurrent_executions: int = Field(5, ge=1, le=100)
    default_timeout_seconds: float = Field(300.0, gt=0)
    memory_limit_mb: int = Field(1024, gt=0)
    cpu_limit_percent: int = Field(80, ge=1, le=100)
    
    # Agent tools and integrations
    tools: List[ToolConfig] = Field(default_factory=list)
    mcp_servers: List[str] = Field(default_factory=list)
    external_apis: Dict[str, str] = Field(default_factory=dict)
    
    # Agent learning and adaptation
    learning_enabled: bool = Field(True)
    experience_retention_days: int = Field(30, ge=1)
    auto_optimization: bool = Field(True)
    
    # Agent security and permissions
    security_level: str = Field("standard", pattern="^(minimal|standard|strict|maximum)$")
    allowed_operations: List[str] = Field(default_factory=list)
    resource_quotas: Dict[str, int] = Field(default_factory=dict)
    
    # Agent monitoring and observability
    logging_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    metrics_enabled: bool = Field(True)
    trace_enabled: bool = Field(True)
    health_check_interval_seconds: int = Field(60, ge=10)
    
    # Agent metadata
    author: str = Field("DevQ.ai", description="Agent author")
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @field_validator('capabilities', mode='before')
    @classmethod
    def validate_capabilities(cls, v):
        if isinstance(v, list):
            return [AgentCapabilityConfig(**item) if isinstance(item, dict) else item for item in v]
        return v
    
    @field_validator('tools', mode='before')
    @classmethod 
    def validate_tools(cls, v):
        if isinstance(v, list):
            return [ToolConfig(**item) if isinstance(item, dict) else item for item in v]
        return v
    
    @model_validator(mode='after')
    def validate_agent_config(self):
        """Validate overall agent configuration consistency"""
        # Ensure at least one capability is enabled
        if self.capabilities and not any(cap.enabled for cap in self.capabilities):
            raise ValueError("At least one capability must be enabled")
        
        # Validate resource limits
        if self.memory_limit_mb < 256:
            raise ValueError("Memory limit must be at least 256MB")
        
        return self


class ConfigurationManager:
    """
    Centralized configuration manager for agents, tools, and workflows
    
    Provides hierarchical configuration management with environment variable
    support, validation, and dynamic updates.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or Path(__file__).parent.parent.parent / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration storage
        self.agent_configs: Dict[str, AgentConfigModel] = {}
        self.tool_configs: Dict[str, ToolConfig] = {}
        self.workflow_configs: Dict[str, WorkflowConfig] = {}
        
        # Configuration hierarchy
        self.config_hierarchy: Dict[ConfigurationLevel, Dict[str, Any]] = {
            ConfigurationLevel.SYSTEM: {},
            ConfigurationLevel.PROJECT: {},
            ConfigurationLevel.AGENT: {},
            ConfigurationLevel.RUNTIME: {}
        }
        
        # Initialize with environment variables
        self._load_environment_config()
        self._load_config_files()
        
        logger.info(f"Configuration manager initialized with config directory: {self.config_dir}")
    
    def _load_environment_config(self):
        """Load configuration from environment variables"""
        with logfire.span("Loading environment configuration"):
            env_config = {}
            
            # Agent-specific environment variables
            for key, value in os.environ.items():
                if key.startswith("AGENTICAL_"):
                    config_key = key[10:].lower()  # Remove AGENTICAL_ prefix
                    env_config[config_key] = value
            
            self.config_hierarchy[ConfigurationLevel.SYSTEM] = env_config
            logger.info(f"Loaded {len(env_config)} environment configuration variables")
    
    def _load_config_files(self):
        """Load configuration from files"""
        with logfire.span("Loading configuration files"):
            config_files = {
                "agents.json": self._load_agent_configs,
                "agents.yaml": self._load_agent_configs,
                "tools.json": self._load_tool_configs,
                "tools.yaml": self._load_tool_configs,
                "workflows.json": self._load_workflow_configs,
                "workflows.yaml": self._load_workflow_configs
            }
            
            loaded_files = 0
            for filename, loader_func in config_files.items():
                config_file = self.config_dir / filename
                if config_file.exists():
                    try:
                        loader_func(config_file)
                        loaded_files += 1
                        logger.info(f"Loaded configuration from {filename}")
                    except Exception as e:
                        logger.warning(f"Failed to load {filename}: {e}")
            
            logger.info(f"Loaded {loaded_files} configuration files")
    
    def _load_agent_configs(self, config_file: Path):
        """Load agent configurations from file"""
        data = self._load_config_data(config_file)
        
        for agent_id, agent_data in data.get("agents", {}).items():
            try:
                agent_config = AgentConfigModel(id=agent_id, **agent_data)
                self.agent_configs[agent_id] = agent_config
            except Exception as e:
                logger.error(f"Failed to load agent config for {agent_id}: {e}")
    
    def _load_tool_configs(self, config_file: Path):
        """Load tool configurations from file"""
        data = self._load_config_data(config_file)
        
        for tool_name, tool_data in data.get("tools", {}).items():
            try:
                tool_config = ToolConfig(name=tool_name, **tool_data)
                self.tool_configs[tool_name] = tool_config
            except Exception as e:
                logger.error(f"Failed to load tool config for {tool_name}: {e}")
    
    def _load_workflow_configs(self, config_file: Path):
        """Load workflow configurations from file"""
        data = self._load_config_data(config_file)
        
        for workflow_id, workflow_data in data.get("workflows", {}).items():
            try:
                # Convert step data to WorkflowStepConfig objects
                steps_data = workflow_data.get("steps", [])
                steps = [WorkflowStepConfig(**step) for step in steps_data]
                workflow_data["steps"] = steps
                
                workflow_config = WorkflowConfig(id=workflow_id, **workflow_data)
                self.workflow_configs[workflow_id] = workflow_config
            except Exception as e:
                logger.error(f"Failed to load workflow config for {workflow_id}: {e}")
    
    def _load_config_data(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration data from JSON or YAML file"""
        with open(config_file, 'r') as f:
            if config_file.suffix == '.json':
                return json.load(f)
            elif config_file.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_file.suffix}")
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfigModel]:
        """Get agent configuration by ID"""
        return self.agent_configs.get(agent_id)
    
    def create_agent_config(
        self, 
        agent_id: str, 
        agent_type: str = "generic",
        **kwargs
    ) -> AgentConfigModel:
        """Create new agent configuration"""
        config_data = {
            "id": agent_id,
            "name": kwargs.get("name", agent_id.replace("_", " ").title()),
            "type": agent_type,
            **kwargs
        }
        
        agent_config = AgentConfigModel(**config_data)
        self.agent_configs[agent_id] = agent_config
        
        logger.info(f"Created agent configuration: {agent_id}")
        return agent_config
    
    def update_agent_config(self, agent_id: str, updates: Dict[str, Any]) -> AgentConfigModel:
        """Update existing agent configuration"""
        if agent_id not in self.agent_configs:
            raise ValueError(f"Agent configuration not found: {agent_id}")
        
        current_config = self.agent_configs[agent_id]
        updated_data = current_config.dict()
        updated_data.update(updates)
        updated_data["updated_at"] = datetime.utcnow()
        
        new_config = AgentConfigModel(**updated_data)
        self.agent_configs[agent_id] = new_config
        
        logger.info(f"Updated agent configuration: {agent_id}")
        return new_config
    
    def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """Get tool configuration by name"""
        return self.tool_configs.get(tool_name)
    
    def register_tool_config(self, tool_config: ToolConfig) -> None:
        """Register new tool configuration"""
        self.tool_configs[tool_config.name] = tool_config
        logger.info(f"Registered tool configuration: {tool_config.name}")
    
    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """Get workflow configuration by ID"""
        return self.workflow_configs.get(workflow_id)
    
    def register_workflow_config(self, workflow_config: WorkflowConfig) -> None:
        """Register new workflow configuration"""
        self.workflow_configs[workflow_config.id] = workflow_config
        logger.info(f"Registered workflow configuration: {workflow_config.id}")
    
    def get_hierarchical_config(
        self, 
        config_key: str, 
        agent_id: Optional[str] = None,
        default: Any = None
    ) -> Any:
        """
        Get configuration value with hierarchical lookup
        
        Searches through configuration hierarchy:
        1. Runtime overrides
        2. Agent-specific config
        3. Project-level config  
        4. System defaults
        """
        # Check runtime overrides first
        if config_key in self.config_hierarchy[ConfigurationLevel.RUNTIME]:
            return self.config_hierarchy[ConfigurationLevel.RUNTIME][config_key]
        
        # Check agent-specific config
        if agent_id and agent_id in self.agent_configs:
            agent_config = self.agent_configs[agent_id]
            if hasattr(agent_config, config_key):
                return getattr(agent_config, config_key)
        
        # Check project-level config
        if config_key in self.config_hierarchy[ConfigurationLevel.PROJECT]:
            return self.config_hierarchy[ConfigurationLevel.PROJECT][config_key]
        
        # Check system defaults
        if config_key in self.config_hierarchy[ConfigurationLevel.SYSTEM]:
            return self.config_hierarchy[ConfigurationLevel.SYSTEM][config_key]
        
        return default
    
    def set_runtime_config(self, config_key: str, value: Any) -> None:
        """Set runtime configuration override"""
        self.config_hierarchy[ConfigurationLevel.RUNTIME][config_key] = value
        logger.info(f"Set runtime config: {config_key} = {value}")
    
    def save_configurations(self) -> None:
        """Save all configurations to files"""
        with logfire.span("Saving configurations"):
            # Save agent configurations
            agents_data = {
                "agents": {
                    agent_id: config.dict() 
                    for agent_id, config in self.agent_configs.items()
                }
            }
            self._save_config_file("agents.json", agents_data)
            
            # Save tool configurations  
            tools_data = {
                "tools": {
                    tool_name: config.__dict__
                    for tool_name, config in self.tool_configs.items()
                }
            }
            self._save_config_file("tools.json", tools_data)
            
            # Save workflow configurations
            workflows_data = {
                "workflows": {
                    workflow_id: config.__dict__
                    for workflow_id, config in self.workflow_configs.items()
                }
            }
            self._save_config_file("workflows.json", workflows_data)
            
            logger.info("Saved all configurations to files")
    
    def _save_config_file(self, filename: str, data: Dict[str, Any]) -> None:
        """Save configuration data to file"""
        config_file = self.config_dir / filename
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def validate_all_configurations(self) -> Dict[str, List[str]]:
        """Validate all configurations and return validation errors"""
        validation_errors = {
            "agents": [],
            "tools": [],
            "workflows": []
        }
        
        # Validate agent configurations
        for agent_id, config in self.agent_configs.items():
            try:
                # Re-validate the Pydantic model
                AgentConfigModel(**config.dict())
            except Exception as e:
                validation_errors["agents"].append(f"{agent_id}: {str(e)}")
        
        # Validate tool configurations
        for tool_name, config in self.tool_configs.items():
            if not config.name:
                validation_errors["tools"].append(f"{tool_name}: Tool name is required")
            if not config.type:
                validation_errors["tools"].append(f"{tool_name}: Tool type is required")
        
        # Validate workflow configurations
        for workflow_id, config in self.workflow_configs.items():
            if not config.steps:
                validation_errors["workflows"].append(f"{workflow_id}: At least one step is required")
            
            # Validate step dependencies
            step_ids = {step.id for step in config.steps}
            for step in config.steps:
                for dep in step.depends_on:
                    if dep not in step_ids:
                        validation_errors["workflows"].append(
                            f"{workflow_id}: Step {step.id} depends on non-existent step {dep}"
                        )
        
        return validation_errors
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of all configurations"""
        return {
            "agent_count": len(self.agent_configs),
            "tool_count": len(self.tool_configs),
            "workflow_count": len(self.workflow_configs),
            "config_directory": str(self.config_dir),
            "agents": list(self.agent_configs.keys()),
            "tools": list(self.tool_configs.keys()),
            "workflows": list(self.workflow_configs.keys())
        }


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager instance"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    
    return _config_manager


def reload_configuration() -> ConfigurationManager:
    """Reload configuration manager"""
    global _config_manager
    _config_manager = None
    return get_config_manager()


# Export main classes and functions
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