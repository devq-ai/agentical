"""
Tests for Agent/Tool/Workflow Configuration Framework

This module provides comprehensive tests for the new configuration framework,
including validation, integration, and functionality tests.
"""

import os
import json
import tempfile
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import Mock, patch

# Import configuration framework
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.agent_config import (
    ConfigurationManager,
    AgentConfigModel,
    ToolConfig,
    WorkflowConfig,
    WorkflowStepConfig,
    AgentCapabilityConfig,
    AgentCapabilityType,
    ConfigurationLevel
)
from config.integration import ConfigurationIntegrator


class TestAgentConfigModel:
    """Test AgentConfigModel validation and functionality"""
    
    def test_basic_agent_config_creation(self):
        """Test creating basic agent configuration"""
        config = AgentConfigModel(
            id="test_agent",
            name="Test Agent",
            type="generic",
            description="Test agent for validation"
        )
        
        assert config.id == "test_agent"
        assert config.name == "Test Agent"
        assert config.type == "generic"
        assert config.description == "Test agent for validation"
        assert config.version == "1.0.0"
        assert config.author == "DevQ.ai"
        assert isinstance(config.created_at, datetime)
    
    def test_agent_config_with_capabilities(self):
        """Test agent configuration with capabilities"""
        capabilities = [
            AgentCapabilityConfig(
                type=AgentCapabilityType.REASONING,
                enabled=True,
                priority=8
            ),
            AgentCapabilityConfig(
                type=AgentCapabilityType.EXECUTION,
                enabled=True,
                priority=7
            )
        ]
        
        config = AgentConfigModel(
            id="test_agent",
            name="Test Agent",
            type="generic",
            capabilities=capabilities
        )
        
        assert len(config.capabilities) == 2
        assert config.capabilities[0].type == AgentCapabilityType.REASONING
        assert config.capabilities[1].type == AgentCapabilityType.EXECUTION
    
    def test_agent_config_validation_errors(self):
        """Test agent configuration validation errors"""
        with pytest.raises(ValueError):
            AgentConfigModel(
                id="test_agent",
                name="Test Agent",
                type="generic",
                memory_limit_mb=100  # Too low, should fail validation
            )
    
    def test_tool_config_creation(self):
        """Test tool configuration creation"""
        tool_config = ToolConfig(
            name="test_tool",
            type="mcp",
            command="python",
            args=["-m", "test_module"],
            description="Test tool configuration"
        )
        
        assert tool_config.name == "test_tool"
        assert tool_config.type == "mcp"
        assert tool_config.command == "python"
        assert tool_config.args == ["-m", "test_module"]
        assert tool_config.enabled is True


class TestWorkflowConfig:
    """Test workflow configuration functionality"""
    
    def test_workflow_step_creation(self):
        """Test workflow step configuration"""
        step = WorkflowStepConfig(
            id="test_step",
            name="Test Step",
            agent_type="generic",
            operation="test_operation",
            parameters={"param1": "value1"}
        )
        
        assert step.id == "test_step"
        assert step.name == "Test Step"
        assert step.agent_type == "generic"
        assert step.operation == "test_operation"
        assert step.parameters == {"param1": "value1"}
    
    def test_workflow_config_creation(self):
        """Test complete workflow configuration"""
        steps = [
            WorkflowStepConfig(
                id="step1",
                name="First Step",
                agent_type="generic",
                operation="operation1"
            ),
            WorkflowStepConfig(
                id="step2",
                name="Second Step",
                agent_type="super",
                operation="operation2",
                depends_on=["step1"]
            )
        ]
        
        workflow = WorkflowConfig(
            id="test_workflow",
            name="Test Workflow",
            description="Test workflow configuration",
            steps=steps
        )
        
        assert workflow.id == "test_workflow"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 2
        assert workflow.steps[1].depends_on == ["step1"]


class TestConfigurationManager:
    """Test configuration manager functionality"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_configuration_manager_initialization(self, temp_config_dir):
        """Test configuration manager initialization"""
        manager = ConfigurationManager(config_dir=temp_config_dir)
        
        assert manager.config_dir == temp_config_dir
        assert isinstance(manager.agent_configs, dict)
        assert isinstance(manager.tool_configs, dict)
        assert isinstance(manager.workflow_configs, dict)
    
    def test_create_agent_config(self, temp_config_dir):
        """Test creating agent configuration"""
        manager = ConfigurationManager(config_dir=temp_config_dir)
        
        config = manager.create_agent_config(
            agent_id="test_agent",
            agent_type="generic",
            name="Test Agent",
            description="Test agent creation"
        )
        
        assert config.id == "test_agent"
        assert config.type == "generic"
        assert config.name == "Test Agent"
        assert "test_agent" in manager.agent_configs
    
    def test_update_agent_config(self, temp_config_dir):
        """Test updating agent configuration"""
        manager = ConfigurationManager(config_dir=temp_config_dir)
        
        # Create initial config
        manager.create_agent_config(
            agent_id="test_agent",
            agent_type="generic"
        )
        
        # Update config
        updated_config = manager.update_agent_config(
            "test_agent",
            {"description": "Updated description", "memory_limit_mb": 2048}
        )
        
        assert updated_config.description == "Updated description"
        assert updated_config.memory_limit_mb == 2048
    
    def test_hierarchical_config_lookup(self, temp_config_dir):
        """Test hierarchical configuration lookup"""
        manager = ConfigurationManager(config_dir=temp_config_dir)
        
        # Set different levels of configuration
        manager.config_hierarchy[ConfigurationLevel.SYSTEM]["test_key"] = "system_value"
        manager.config_hierarchy[ConfigurationLevel.PROJECT]["test_key"] = "project_value"
        manager.config_hierarchy[ConfigurationLevel.RUNTIME]["test_key"] = "runtime_value"
        
        # Runtime should take precedence
        value = manager.get_hierarchical_config("test_key")
        assert value == "runtime_value"
        
        # Remove runtime, should get project value
        del manager.config_hierarchy[ConfigurationLevel.RUNTIME]["test_key"]
        value = manager.get_hierarchical_config("test_key")
        assert value == "project_value"
    
    def test_configuration_file_loading(self, temp_config_dir):
        """Test loading configuration from files"""
        # Create test agent configuration file
        agents_config = {
            "agents": {
                "file_agent": {
                    "name": "File Agent",
                    "type": "generic",
                    "description": "Agent loaded from file",
                    "capabilities": [
                        {
                            "type": "reasoning",
                            "enabled": True,
                            "priority": 8
                        }
                    ]
                }
            }
        }
        
        agents_file = temp_config_dir / "agents.json"
        with open(agents_file, 'w') as f:
            json.dump(agents_config, f)
        
        # Initialize manager (should load the file)
        manager = ConfigurationManager(config_dir=temp_config_dir)
        
        # Check that agent was loaded
        assert "file_agent" in manager.agent_configs
        config = manager.get_agent_config("file_agent")
        assert config.name == "File Agent"
        assert config.description == "Agent loaded from file"
        assert len(config.capabilities) == 1
    
    def test_configuration_validation(self, temp_config_dir):
        """Test configuration validation"""
        manager = ConfigurationManager(config_dir=temp_config_dir)
        
        # Create valid configuration
        manager.create_agent_config(
            agent_id="valid_agent",
            agent_type="generic"
        )
        
        # Validate all configurations
        validation_errors = manager.validate_all_configurations()
        
        assert "agents" in validation_errors
        assert "tools" in validation_errors
        assert "workflows" in validation_errors
        assert len(validation_errors["agents"]) == 0  # Should be no errors


class TestConfigurationIntegrator:
    """Test configuration integrator functionality"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing"""
        agent = Mock()
        agent.metadata = Mock()
        agent.metadata.name = "Test Agent"
        agent.metadata.description = "Test Description"
        return agent
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_integrator_initialization(self, temp_config_dir):
        """Test configuration integrator initialization"""
        config_manager = ConfigurationManager(config_dir=temp_config_dir)
        integrator = ConfigurationIntegrator(config_manager=config_manager)
        
        assert integrator.config_manager == config_manager
        assert isinstance(integrator.integrated_agents, dict)
        assert isinstance(integrator.configured_tools, dict)
    
    def test_configure_agent_from_config(self, temp_config_dir, mock_agent):
        """Test configuring agent from configuration"""
        config_manager = ConfigurationManager(config_dir=temp_config_dir)
        integrator = ConfigurationIntegrator(config_manager=config_manager)
        
        # Create agent configuration
        config_manager.create_agent_config(
            agent_id="test_agent",
            agent_type="generic",
            name="Configured Agent",
            description="Agent configured from config"
        )
        
        # Configure agent
        integrator.configure_agent_from_config("test_agent", mock_agent)
        
        # Check that agent was configured
        assert "test_agent" in integrator.integrated_agents
        assert mock_agent.metadata.name == "Configured Agent"
        assert mock_agent.metadata.description == "Agent configured from config"
    
    def test_workflow_execution_plan(self, temp_config_dir):
        """Test workflow execution plan generation"""
        config_manager = ConfigurationManager(config_dir=temp_config_dir)
        integrator = ConfigurationIntegrator(config_manager=config_manager)
        
        # Create workflow configuration
        steps = [
            WorkflowStepConfig(
                id="step1",
                name="First Step",
                agent_type="generic",
                operation="operation1"
            )
        ]
        
        workflow_config = WorkflowConfig(
            id="test_workflow",
            name="Test Workflow",
            description="Test workflow",
            steps=steps
        )
        
        config_manager.register_workflow_config(workflow_config)
        
        # Get execution plan
        execution_plan = integrator.get_workflow_execution_plan("test_workflow")
        
        assert execution_plan is not None
        assert execution_plan["workflow_id"] == "test_workflow"
        assert execution_plan["name"] == "Test Workflow"
        assert len(execution_plan["steps"]) == 1
        assert execution_plan["steps"][0]["id"] == "step1"
    
    def test_agent_configuration_validation(self, temp_config_dir):
        """Test agent configuration validation"""
        config_manager = ConfigurationManager(config_dir=temp_config_dir)
        integrator = ConfigurationIntegrator(config_manager=config_manager)
        
        # Create valid agent configuration
        config_manager.create_agent_config(
            agent_id="valid_agent",
            agent_type="generic"
        )
        
        # Validate configuration
        validation_result = integrator.validate_agent_configuration("valid_agent")
        
        assert validation_result["agent_id"] == "valid_agent"
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0
    
    def test_integration_status(self, temp_config_dir):
        """Test integration status reporting"""
        config_manager = ConfigurationManager(config_dir=temp_config_dir)
        integrator = ConfigurationIntegrator(config_manager=config_manager)
        
        # Create some configurations
        config_manager.create_agent_config("agent1", "generic")
        config_manager.create_agent_config("agent2", "super")
        
        # Get integration status
        status = integrator.get_integration_status()
        
        assert "configured_agents" in status
        assert "agent_configs_available" in status
        assert status["agent_configs_available"] == 2
        assert "agents" in status


class TestConfigurationFrameworkIntegration:
    """Integration tests for the complete configuration framework"""
    
    def test_end_to_end_configuration_flow(self):
        """Test complete configuration flow from creation to execution"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Initialize manager
            manager = ConfigurationManager(config_dir=config_dir)
            
            # Create agent configuration
            agent_config = manager.create_agent_config(
                agent_id="e2e_agent",
                agent_type="generic",
                name="End-to-End Agent",
                description="Complete configuration test"
            )
            
            # Create tool configuration
            tool_config = ToolConfig(
                name="e2e_tool",
                type="mcp",
                command="python",
                args=["-m", "test_tool"],
                description="End-to-end tool"
            )
            manager.register_tool_config(tool_config)
            
            # Create workflow configuration
            workflow_steps = [
                WorkflowStepConfig(
                    id="test_step",
                    name="Test Step",
                    agent_type="generic",
                    operation="test_operation"
                )
            ]
            
            workflow_config = WorkflowConfig(
                id="e2e_workflow",
                name="End-to-End Workflow",
                description="Complete workflow test",
                steps=workflow_steps
            )
            manager.register_workflow_config(workflow_config)
            
            # Initialize integrator
            integrator = ConfigurationIntegrator(config_manager=manager)
            
            # Get execution plan
            execution_plan = integrator.get_workflow_execution_plan("e2e_workflow")
            
            # Validate all configurations
            validation_errors = manager.validate_all_configurations()
            
            # Assertions
            assert agent_config.id == "e2e_agent"
            assert tool_config.name == "e2e_tool"
            assert workflow_config.id == "e2e_workflow"
            assert execution_plan is not None
            assert len(validation_errors["agents"]) == 0
            assert len(validation_errors["tools"]) == 0
            assert len(validation_errors["workflows"]) == 0
            
            # Save configurations
            manager.save_configurations()
            
            # Verify files were created
            assert (config_dir / "agents.json").exists()
            assert (config_dir / "tools.json").exists()
            assert (config_dir / "workflows.json").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])