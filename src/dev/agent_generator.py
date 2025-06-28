"""
Local Agent Development Generator

This module provides tools for local agent development, including agent generation,
scaffolding, testing frameworks, and deployment utilities.

Features:
- Agent template generation
- Custom agent scaffolding
- Development environment setup
- Testing framework integration
- Local agent registry
- Hot reloading for development
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional, Type
from pathlib import Path
from datetime import datetime
import jinja2
import ast
import inspect

import logfire

logger = logging.getLogger(__name__)


class AgentTemplate:
    """Agent template for code generation"""
    
    def __init__(self, name: str, description: str, template_path: str):
        self.name = name
        self.description = description
        self.template_path = template_path
        self.variables: Dict[str, Any] = {}
        
    def set_variable(self, key: str, value: Any) -> None:
        """Set template variable"""
        self.variables[key] = value
        
    def render(self, output_path: Path) -> None:
        """Render template to output path"""
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(Path(self.template_path).parent),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        template = env.get_template(Path(self.template_path).name)
        rendered = template.render(**self.variables)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(rendered)


class AgentGenerator:
    """
    Generator for creating new agent scaffolds and development environments
    
    Provides tools for rapid agent development with best practices built-in.
    """
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        """
        Initialize agent generator
        
        Args:
            workspace_dir: Directory for agent development workspace
        """
        self.workspace_dir = workspace_dir or Path.cwd() / "agent_workspace"
        self.templates_dir = Path(__file__).parent / "templates"
        
        # Create workspace if it doesn't exist
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize templates
        self._setup_templates()
        
        logger.info(f"Agent generator initialized with workspace: {self.workspace_dir}")
    
    def _setup_templates(self) -> None:
        """Set up agent templates"""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default templates if they don't exist
        self._create_basic_agent_template()
        self._create_advanced_agent_template()
        self._create_custom_agent_template()
        
    def _create_basic_agent_template(self) -> None:
        """Create basic agent template"""
        template_content = '''"""
{{ agent_name }} - {{ description }}

Generated on {{ generation_date }}
Author: {{ author }}
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

import logfire
from pydantic import BaseModel, Field

from agentical.agents.base_agent import (
    BaseAgent,
    AgentMetadata,
    AgentCapability,
    AgentStatus,
    AgentExecutionContext,
    AgentExecutionResult
)
from agentical.core.exceptions import AgenticalError, AgentError

logger = logging.getLogger(__name__)


class {{ class_name }}(BaseAgent):
    """
    {{ description }}
    
    This agent provides:
    {% for capability in capabilities %}
    - {{ capability }}
    {% endfor %}
    """
    
    def __init__(self):
        """Initialize {{ agent_name }}"""
        metadata = AgentMetadata(
            id="{{ agent_id }}",
            name="{{ agent_name }}",
            description="{{ description }}",
            version="{{ version }}",
            capabilities=[
                {% for capability in capabilities %}
                AgentCapability(
                    name="{{ capability.lower().replace(' ', '_') }}",
                    description="{{ capability }}",
                    enabled=True
                ),
                {% endfor %}
            ],
            dependencies={{ dependencies }},
            author="{{ author }}",
            tags={{ tags }}
        )
        
        super().__init__(metadata)
        
        # Custom initialization
        self._setup_custom_capabilities()
        
        logger.info(f"Initialized {{ agent_name }}")
    
    def _setup_custom_capabilities(self) -> None:
        """Setup custom agent capabilities"""
        # TODO: Implement custom capability setup
        pass
    
    async def execute(self, operation: str, parameters: Dict[str, Any] = None) -> AgentExecutionResult:
        """
        Execute agent operation
        
        Args:
            operation: Operation to execute
            parameters: Operation parameters
            
        Returns:
            Execution result
        """
        with logfire.span("{{ class_name }} execution", operation=operation):
            start_time = datetime.utcnow()
            
            try:
                # Set execution context
                context = AgentExecutionContext(
                    agent_id=self.metadata.id,
                    operation=operation,
                    parameters=parameters or {},
                    execution_id=f"{self.metadata.id}_{datetime.utcnow().timestamp()}",
                    timestamp=start_time
                )
                
                self.current_context = context
                self.status = AgentStatus.RUNNING
                
                # Execute operation
                result = await self._execute_operation(operation, parameters or {})
                
                # Create execution result
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                execution_result = AgentExecutionResult(
                    success=True,
                    execution_id=context.execution_id,
                    agent_id=self.metadata.id,
                    operation=operation,
                    result=result,
                    execution_time=execution_time,
                    timestamp=datetime.utcnow()
                )
                
                self.execution_history.append(execution_result)
                self.status = AgentStatus.IDLE
                
                logger.info(f"{{ agent_name }} executed {operation} successfully")
                return execution_result
                
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                execution_result = AgentExecutionResult(
                    success=False,
                    execution_id=context.execution_id if 'context' in locals() else "unknown",
                    agent_id=self.metadata.id,
                    operation=operation,
                    result={},
                    error=str(e),
                    execution_time=execution_time,
                    timestamp=datetime.utcnow()
                )
                
                self.execution_history.append(execution_result)
                self.status = AgentStatus.ERROR
                
                logger.error(f"{{ agent_name }} execution failed: {e}")
                return execution_result
    
    async def _execute_operation(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute specific operation
        
        Args:
            operation: Operation to execute
            parameters: Operation parameters
            
        Returns:
            Operation result
        """
        # Map operations to methods
        operation_map = {
            {% for operation in operations %}
            "{{ operation.lower().replace(' ', '_') }}": self._{{ operation.lower().replace(' ', '_') }},
            {% endfor %}
            "health_check": self._health_check,
            "get_status": self._get_status
        }
        
        if operation not in operation_map:
            raise AgentError(f"Unknown operation: {operation}")
        
        return await operation_map[operation](parameters)
    
    {% for operation in operations %}
    async def _{{ operation.lower().replace(' ', '_') }}(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute {{ operation.lower().replace('_', ' ') }} operation
        
        Args:
            parameters: Operation parameters
            
        Returns:
            Operation result
        """
        # TODO: Implement {{ operation.lower().replace('_', ' ') }} logic
        return {
            "operation": "{{ operation.lower().replace(' ', '_') }}",
            "status": "completed",
            "message": "{{ operation }} executed successfully",
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    {% endfor %}
    async def _health_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Health check operation"""
        return {
            "agent_id": self.metadata.id,
            "agent_name": self.metadata.name,
            "status": self.status.value,
            "health": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "infrastructure": {
                "ptolemies_available": self.infrastructure.ptolemies_available,
                "mcp_servers": len(self.infrastructure.mcp_servers or {})
            }
        }
    
    async def _get_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.metadata.id,
            "agent_name": self.metadata.name,
            "status": self.status.value,
            "execution_count": len(self.execution_history),
            "last_execution": self.execution_history[-1].timestamp.isoformat() if self.execution_history else None,
            "capabilities": [cap.name for cap in self.metadata.capabilities],
            "timestamp": datetime.utcnow().isoformat()
        }
'''
        
        template_path = self.templates_dir / "basic_agent.py.j2"
        with open(template_path, 'w') as f:
            f.write(template_content)
    
    def _create_advanced_agent_template(self) -> None:
        """Create advanced agent template with more features"""
        # This would be a more complex template with additional features
        pass
    
    def _create_custom_agent_template(self) -> None:
        """Create custom agent template"""
        # This would be a highly customizable template
        pass
    
    def generate_agent(
        self,
        agent_name: str,
        agent_id: Optional[str] = None,
        description: str = "",
        capabilities: Optional[List[str]] = None,
        operations: Optional[List[str]] = None,
        template_type: str = "basic",
        author: str = "Developer",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None
    ) -> Path:
        """
        Generate a new agent from template
        
        Args:
            agent_name: Human-readable agent name
            agent_id: Unique agent identifier
            description: Agent description
            capabilities: List of agent capabilities
            operations: List of operations the agent can perform
            template_type: Type of template to use
            author: Agent author
            version: Agent version
            tags: Agent tags
            dependencies: Agent dependencies
            
        Returns:
            Path to generated agent file
        """
        with logfire.span("Generating agent", agent_name=agent_name):
            # Set defaults
            agent_id = agent_id or agent_name.lower().replace(" ", "_").replace("-", "_")
            capabilities = capabilities or ["Basic Execution", "Status Reporting"]
            operations = operations or ["execute_task", "process_request"]
            tags = tags or ["generated", "development"]
            dependencies = dependencies or []
            
            # Sanitize class name
            class_name = "".join(word.capitalize() for word in agent_name.split())
            if not class_name.endswith("Agent"):
                class_name += "Agent"
            
            # Create agent directory
            agent_dir = self.workspace_dir / agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Template variables
            template_vars = {
                "agent_name": agent_name,
                "agent_id": agent_id,
                "class_name": class_name,
                "description": description or f"Generated agent: {agent_name}",
                "capabilities": capabilities,
                "operations": operations,
                "author": author,
                "version": version,
                "tags": tags,
                "dependencies": dependencies,
                "generation_date": datetime.utcnow().isoformat()
            }
            
            # Render agent template
            template_path = self.templates_dir / f"{template_type}_agent.py.j2"
            if not template_path.exists():
                template_path = self.templates_dir / "basic_agent.py.j2"
            
            template = AgentTemplate(
                name=f"{template_type}_agent",
                description=f"{template_type} agent template",
                template_path=str(template_path)
            )
            
            for key, value in template_vars.items():
                template.set_variable(key, value)
            
            agent_file = agent_dir / f"{agent_id}.py"
            template.render(agent_file)
            
            # Generate additional files
            self._generate_agent_config(agent_dir, template_vars)
            self._generate_agent_tests(agent_dir, template_vars)
            self._generate_agent_readme(agent_dir, template_vars)
            
            logger.info(f"Generated agent: {agent_name} at {agent_file}")
            return agent_file
    
    def _generate_agent_config(self, agent_dir: Path, template_vars: Dict[str, Any]) -> None:
        """Generate agent configuration file"""
        config = {
            "agent_id": template_vars["agent_id"],
            "name": template_vars["agent_name"],
            "type": "custom",
            "description": template_vars["description"],
            "version": template_vars["version"],
            "capabilities": [
                {
                    "type": capability.lower().replace(" ", "_"),
                    "enabled": True,
                    "priority": 5
                }
                for capability in template_vars["capabilities"]
            ],
            "max_concurrent_executions": 5,
            "default_timeout_seconds": 300.0,
            "memory_limit_mb": 1024,
            "tools": [],
            "mcp_servers": ["filesystem", "git", "memory"],
            "security_level": "standard",
            "logging_level": "INFO",
            "metrics_enabled": True,
            "author": template_vars["author"],
            "tags": template_vars["tags"]
        }
        
        config_file = agent_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _generate_agent_tests(self, agent_dir: Path, template_vars: Dict[str, Any]) -> None:
        """Generate agent test file"""
        test_content = f'''"""
Tests for {template_vars["agent_name"]}

Generated on {template_vars["generation_date"]}
"""

import pytest
import asyncio
from datetime import datetime

from {template_vars["agent_id"]} import {template_vars["class_name"]}


class Test{template_vars["class_name"]}:
    """Test suite for {template_vars["class_name"]}"""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        return {template_vars["class_name"]}()
    
    def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.metadata.id == "{template_vars["agent_id"]}"
        assert agent.metadata.name == "{template_vars["agent_name"]}"
        assert len(agent.metadata.capabilities) > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, agent):
        """Test agent health check"""
        result = await agent.execute("health_check")
        
        assert result.success is True
        assert result.agent_id == "{template_vars["agent_id"]}"
        assert "health" in result.result
        assert result.result["health"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_status(self, agent):
        """Test agent status retrieval"""
        result = await agent.execute("get_status")
        
        assert result.success is True
        assert "status" in result.result
        assert "capabilities" in result.result
    
    {chr(10).join([f'''@pytest.mark.asyncio
    async def test_{op.lower().replace(" ", "_")}(self, agent):
        """Test {op.lower().replace("_", " ")} operation"""
        result = await agent.execute("{op.lower().replace(" ", "_")}", {{"test_param": "test_value"}})
        
        assert result.success is True
        assert result.operation == "{op.lower().replace(" ", "_")}"
        assert "status" in result.result''' for op in template_vars["operations"]])}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        
        test_file = agent_dir / f"test_{template_vars['agent_id']}.py"
        with open(test_file, 'w') as f:
            f.write(test_content)
    
    def _generate_agent_readme(self, agent_dir: Path, template_vars: Dict[str, Any]) -> None:
        """Generate agent README file"""
        readme_content = f'''# {template_vars["agent_name"]}

{template_vars["description"]}

## Overview

- **Agent ID**: `{template_vars["agent_id"]}`
- **Version**: {template_vars["version"]}
- **Author**: {template_vars["author"]}
- **Generated**: {template_vars["generation_date"]}

## Capabilities

{chr(10).join([f"- {capability}" for capability in template_vars["capabilities"]])}

## Operations

{chr(10).join([f"- `{op.lower().replace(' ', '_')}`: {op}" for op in template_vars["operations"]])}

## Usage

```python
from {template_vars["agent_id"]} import {template_vars["class_name"]}

# Initialize agent
agent = {template_vars["class_name"]}()

# Execute operation
result = await agent.execute("health_check")
print(result.result)
```

## Development

### Testing

```bash
# Run tests
python -m pytest test_{template_vars["agent_id"]}.py -v

# Run with coverage
python -m pytest test_{template_vars["agent_id"]}.py --cov={template_vars["agent_id"]} --cov-report=html
```

### Configuration

Agent configuration is stored in `config.json`. Modify this file to customize:

- Capabilities and permissions
- Resource limits
- Tool integrations
- Security settings

## Integration

To integrate this agent with the Agentical framework:

1. Register the agent with the agent registry
2. Configure the agent in the main application
3. Set up monitoring and logging
4. Deploy to your environment

## Tags

{", ".join(template_vars["tags"])}
'''
        
        readme_file = agent_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
    
    def create_development_environment(self, project_name: str) -> Path:
        """
        Create a complete development environment for agent development
        
        Args:
            project_name: Name of the development project
            
        Returns:
            Path to the created project directory
        """
        with logfire.span("Creating development environment", project=project_name):
            project_dir = self.workspace_dir / project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Create directory structure
            directories = [
                "agents",
                "tests", 
                "config",
                "tools",
                "workflows",
                "docs",
                "scripts"
            ]
            
            for directory in directories:
                (project_dir / directory).mkdir(exist_ok=True)
            
            # Create project files
            self._create_project_config(project_dir, project_name)
            self._create_requirements_file(project_dir)
            self._create_pytest_config(project_dir)
            self._create_project_readme(project_dir, project_name)
            self._create_development_scripts(project_dir)
            self._create_vscode_config(project_dir)
            
            logger.info(f"Created development environment: {project_dir}")
            return project_dir
    
    def _create_project_config(self, project_dir: Path, project_name: str) -> None:
        """Create project configuration files"""
        # pyproject.toml
        pyproject_content = f'''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name.lower().replace(' ', '-')}"
version = "0.1.0"
description = "Agent development project: {project_name}"
authors = [{{name = "Developer", email = "developer@example.com"}}]
dependencies = [
    "agentical>=1.0.0",
    "pydantic>=2.0.0",
    "logfire>=0.28.0",
    "httpx>=0.24.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0"
]

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=agents --cov-report=html --cov-report=term"
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.black]
line-length = 88
target-version = ["py312"]

[tool.isort]
profile = "black"
line_length = 88
'''
        
        with open(project_dir / "pyproject.toml", 'w') as f:
            f.write(pyproject_content)
        
        # .env template
        env_content = '''# Agent Development Environment Variables

# Agentical Configuration
AGENTICAL_ENV=development
DEBUG=true

# Logfire Configuration
LOGFIRE_TOKEN=your_logfire_token_here
LOGFIRE_PROJECT_NAME=agent_development
LOGFIRE_SERVICE_NAME=custom_agents

# Database Configuration
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_USERNAME=root
SURREALDB_PASSWORD=root
SURREALDB_NAMESPACE=development
SURREALDB_DATABASE=agents

# Redis Configuration
REDIS_URL=redis://localhost:6379
UPSTASH_REDIS_REST_URL=your_redis_url
UPSTASH_REDIS_REST_TOKEN=your_redis_token

# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Development Settings
PYTEST_WORKERS=auto
HOT_RELOAD=true
AUTO_SAVE_CONFIG=true
'''
        
        with open(project_dir / ".env.template", 'w') as f:
            f.write(env_content)
    
    def _create_requirements_file(self, project_dir: Path) -> None:
        """Create requirements.txt file"""
        requirements = [
            "# Agent Development Requirements",
            "",
            "# Core framework",
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.0.0",
            "logfire[fastapi]>=0.28.0",
            "",
            "# Development tools",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.9.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "",
            "# Agent development",
            "jinja2>=3.1.0",
            "httpx>=0.24.0",
            "aiofiles>=23.0.0",
            "",
            "# Optional integrations",
            "redis>=4.6.0",
            "surrealdb>=0.3.0",
            "python-dotenv>=1.0.0"
        ]
        
        with open(project_dir / "requirements.txt", 'w') as f:
            f.write('\n'.join(requirements))
    
    def _create_pytest_config(self, project_dir: Path) -> None:
        """Create pytest configuration"""
        pytest_content = '''[tool:pytest]
minversion = 7.0
addopts = -ra -q --cov=agents --cov-report=html --cov-report=term --cov-fail-under=80
testpaths = tests
asyncio_mode = auto
python_files = test_*.py
python_classes = Test*
python_functions = test_*
'''
        
        with open(project_dir / "pytest.ini", 'w') as f:
            f.write(pytest_content)
    
    def _create_project_readme(self, project_dir: Path, project_name: str) -> None:
        """Create project README"""
        readme_content = f'''# {project_name} - Agent Development Project

This is a development project for creating custom agents using the Agentical framework.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Agentical framework
- SurrealDB (optional)
- Redis (optional)

### Installation

1. Clone or create this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment template:
   ```bash
   cp .env.template .env
   ```
4. Edit `.env` with your configuration

### Development Workflow

1. **Generate a new agent:**
   ```bash
   python scripts/generate_agent.py --name "My Custom Agent" --capabilities "Data Processing,API Integration"
   ```

2. **Test your agent:**
   ```bash
   pytest tests/ -v
   ```

3. **Run agent locally:**
   ```bash
   python scripts/run_agent.py --agent my_custom_agent
   ```

## Project Structure

```
{project_name.lower().replace(' ', '_')}/
├── agents/              # Custom agent implementations
├── tests/              # Agent tests
├── config/             # Configuration files
├── tools/              # Custom tools
├── workflows/          # Workflow definitions
├── docs/               # Documentation
├── scripts/            # Development scripts
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project configuration
└── README.md           # This file
```

## Agent Development

### Creating a New Agent

Use the agent generator to create scaffolding:

```python
from agentical.dev.agent_generator import AgentGenerator

generator = AgentGenerator()
agent_file = generator.generate_agent(
    agent_name="My Custom Agent",
    description="Agent that processes data and integrates with APIs",
    capabilities=["Data Processing", "API Integration"],
    operations=["process_data", "call_api", "transform_results"]
)
```

### Testing

All agents should have comprehensive tests:

```bash
# Run all tests
pytest

# Run specific agent tests
pytest tests/test_my_custom_agent.py

# Run with coverage
pytest --cov=agents --cov-report=html
```

### Configuration

Agent configurations are stored in `config/` directory. Each agent should have:

- `config.json`: Agent configuration
- `README.md`: Agent documentation
- Test files in `tests/`

## Integration

To integrate your agents with the main Agentical framework:

1. Register agents in the agent registry
2. Configure endpoints in the API
3. Set up monitoring and logging
4. Deploy to your environment

## Best Practices

- Follow the agent template structure
- Include comprehensive tests
- Document all capabilities and operations
- Use configuration for customization
- Implement proper error handling
- Add logging and monitoring

## Support

For questions and support:

- Check the Agentical documentation
- Review example agents
- Run tests to validate setup
- Check logs for debugging

'''
        
        with open(project_dir / "README.md", 'w') as f:
            f.write(readme_content)
    
    def _create_development_scripts(self, project_dir: Path) -> None:
        """Create development scripts"""
        scripts_dir = project_dir / "scripts"
        
        # Agent generator script
        generator_script = '''#!/usr/bin/env python3
"""
Agent Generator Script

Usage: python generate_agent.py --name "Agent Name" --capabilities "Cap1,Cap2"
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agentical.dev.agent_generator import AgentGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate a new agent")
    parser.add_argument("--name", required=True, help="Agent name")
    parser.add_argument("--id", help="Agent ID (auto-generated if not provided)")
    parser.add_argument("--description", help="Agent description")
    parser.add_argument("--capabilities", help="Comma-separated capabilities")
    parser.add_argument("--operations", help="Comma-separated operations")
    parser.add_argument("--template", default="basic", help="Template type")
    parser.add_argument("--author", default="Developer", help="Agent author")
    
    args = parser.parse_args()
    
    capabilities = args.capabilities.split(",") if args.capabilities else None
    operations = args.operations.split(",") if args.operations else None
    
    generator = AgentGenerator()
    agent_file = generator.generate_agent(
        agent_name=args.name,
        agent_id=args.id,
        description=args.description,
        capabilities=capabilities,
        operations=operations,
        template_type=args.template,
        author=args.author
    )
    
    print(f"Generated agent: {agent_file}")


if __name__ == "__main__":
    main()
'''
        
        with open(scripts_dir / "generate_agent.py", 'w') as f:
            f.write(generator_script)
        
        # Agent runner script
        runner_script = '''#!/usr/bin/env python3
"""
Agent Runner Script

Usage: python run_agent.py --agent agent_id --operation health_check
"""

import argparse
import asyncio
import sys
import importlib
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "agents"))


async def main():
    parser = argparse.ArgumentParser(description="Run an agent operation")
    parser.add_argument("--agent", required=True, help="Agent ID")
    parser.add_argument("--operation", default="health_check", help="Operation to execute")
    parser.add_argument("--params", help="JSON parameters for operation")
    
    args = parser.parse_args()
    
    try:
        # Import agent module
        agent_module = importlib.import_module(args.agent)
        
        # Find agent class
        agent_class = None
        for attr_name in dir(agent_module):
            attr = getattr(agent_module, attr_name)
            if (isinstance(attr, type) and 
                hasattr(attr, '__bases__') and 
                any('BaseAgent' in str(base) for base in attr.__bases__)):
                agent_class = attr
                break
        
        if not agent_class:
            print(f"No agent class found in {args.agent}")
            return
        
        # Create and run agent
        agent = agent_class()
        
        # Parse parameters
        parameters = {}
        if args.params:
            import json
            parameters = json.loads(args.params)
        
        # Execute operation
        result = await agent.execute(args.operation, parameters)
        
        print(f"Agent: {agent.metadata.name}")
        print(f"Operation: {args.operation}")
        print(f"Success: {result.success}")
        print(f"Result: {result.result}")
        
        if not result.success:
            print(f"Error: {result.error}")
        
    except Exception as e:
        print(f"Error running agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(scripts_dir / "run_agent.py", 'w') as f:
            f.write(runner_script)
        
        # Make scripts executable
        for script in scripts_dir.glob("*.py"):
            script.chmod(0o755)
    
    def _create_vscode_config(self, project_dir: Path) -> None:
        """Create VS Code configuration"""
        vscode_dir = project_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        # Settings
        settings = {
            "python.defaultInterpreterPath": "venv/bin/python",
            "python.testing.pytestEnabled": True,
            "python.testing.pytestArgs": ["tests"],
            "python.linting.enabled": True,
            "python.linting.pylintEnabled": False,
            "python.linting.mypyEnabled": True,
            "python.formatting.provider": "black",
            "python.sortImports.args": ["--profile", "black"],
            "files.exclude": {
                "**/__pycache__": True,
                "**/.pytest_cache": True,
                "**/htmlcov": True,
                "**/.coverage": True
            }
        }
        
        with open(vscode_dir / "settings.json", 'w') as f:
            json.dump(settings, f, indent=2)
        
        # Launch configuration
        launch = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Run Agent",
                    "type": "python",
                    "request": "launch",
                    "program": "scripts/run_agent.py",
                    "args": ["--agent", "${input:agentId}", "--operation", "${input:operation}"],
                    "console": "integratedTerminal",
                    "cwd": "${workspaceFolder}"
                },
                {
                    "name": "Run Tests",
                    "type": "python",
                    "request": "launch",
                    "module": "pytest",
                    "args": ["tests/", "-v"],
                    "console": "integratedTerminal",
                    "cwd": "${workspaceFolder}"
                }
            ],
            "inputs": [
                {
                    "id": "agentId",
                    "type": "promptString",
                    "description": "Agent ID to run"
                },
                {
                    "id": "operation",
                    "type": "promptString",
                    "description": "Operation to execute",
                    "default": "health_check"
                }
            ]
        }
        
        with open(vscode_dir / "launch.json", 'w') as f:
            json.dump(launch, f, indent=2)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents in workspace"""
        agents = []
        
        for agent_dir in self.workspace_dir.iterdir():
            if agent_dir.is_dir():
                config_file = agent_dir / "config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                        
                        agents.append({
                            "agent_id": config.get("agent_id"),
                            "name": config.get("name"),
                            "description": config.get("description"),
                            "version": config.get("version"),
                            "path": str(agent_dir),
                            "capabilities": len(config.get("capabilities", [])),
                            "author": config.get("author")
                        })
                    except Exception as e:
                        logger.warning(f"Failed to load config for {agent_dir}: {e}")
        
        return agents
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an agent"""
        agent_dir = self.workspace_dir / agent_id
        
        if not agent_dir.exists():
            return None
        
        config_file = agent_dir / "config.json"
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check for additional files
            files = list(agent_dir.glob("*"))
            
            return {
                "agent_id": agent_id,
                "config": config,
                "files": [str(f.name) for f in files],
                "path": str(agent_dir),
                "has_tests": any(f.name.startswith("test_") for f in files),
                "has_readme": any(f.name.lower() == "readme.md" for f in files)
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent info for {agent_id}: {e}")
            return None


# Export main classes
__all__ = [
    "AgentTemplate",
    "AgentGenerator"
]