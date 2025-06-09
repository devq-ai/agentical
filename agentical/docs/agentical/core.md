# Core in Agentical Framework

## Overview

The `core` directory contains the foundational components of the Agentical framework. These components provide the essential infrastructure, configuration, and shared utilities that power all other parts of the system. The core module is designed to be stable, well-tested, and to change infrequently compared to other parts of the codebase.

## Directory Structure

```
core/
├── __init__.py             # Package initialization
├── config.py               # Framework configuration
├── registry.py             # Component registry
├── exceptions.py           # Exception definitions
├── dependencies.py         # Dependency management
└── utils.py                # Utility functions
```

## Core Components

### Configuration System

The `config.py` file defines the configuration system for the Agentical framework:

- Environment-based configuration using Pydantic models
- Support for `.env` files and environment variables
- Type validation and transformation of configuration values
- Sensible defaults for all settings
- Hierarchical configuration for different components

### Component Registry

The `registry.py` file implements a central registry for all components in the system:

- Registration of agents, tools, workflows, and playbooks
- Discovery of components at runtime
- Dependency resolution between components
- Factory methods for component creation
- Decorator-based registration API

### Exception Handling

The `exceptions.py` file defines a hierarchy of exceptions specific to the framework:

- Structured error information for debugging
- Clear error messages for users
- Error categorization for proper handling
- Integration with logging and monitoring

### Dependency Management

The `dependencies.py` file implements a dependency injection system:

- Type-based dependency resolution
- Lazy initialization of dependencies
- Scoped dependencies (singleton, request, etc.)
- Integration with FastAPI's dependency system
- Support for async initialization

### Utility Functions

The `utils.py` file provides common utility functions used throughout the framework:

- Text processing utilities
- Date and time handling
- Serialization and deserialization
- Validation helpers
- Async utilities

## Configuration Structure

The configuration system is based on nested Pydantic models:

```python
class Settings:
    # Environment settings
    env: str
    debug: bool
    
    # Component settings
    surrealdb: SurrealDBSettings
    llm: LLMSettings
    embedding: EmbeddingSettings
    api: APISettings
    logging: LoggingSettings
    
    # Feature settings
    max_concurrent_agents: int
    max_workflow_steps: int
    workflow_timeout: int
```

## Registry Usage

The component registry provides a central point for discovering and instantiating components:

```python
# Registering a component
@registry.register_agent("research-assistant")
class ResearchAssistantAgent(Agent):
    ...

# Getting a component
agent = registry.agents.get_instance("research-assistant")
```

## Dependency Injection

The dependency system enables components to declare their dependencies:

```python
# Declaring dependencies
class SearchTool:
    def __init__(self, http_client = Depends(HTTPClient)):
        self.http_client = http_client
    
    async def search(self, query: str):
        ...

# Resolving dependencies
search_tool = await dependency_provider.get(SearchTool)
```

## Exception Handling

The exception system provides structured error handling:

```python
try:
    result = await agent.run(query)
except AgentExecutionError as e:
    logger.error(f"Agent execution failed: {e}")
    # Handle the error appropriately
```

## Best Practices

1. Use the configuration system for all configurable values
2. Register all components with the registry
3. Use dependency injection for component dependencies
4. Use the exception hierarchy for error handling
5. Favor utility functions over reimplementing common operations

## Extending the Core

While the core components should remain stable, there are approved ways to extend them:

1. **Custom Settings**: Add new settings to the configuration system
2. **Registry Extensions**: Register custom component types
3. **Dependency Providers**: Create custom dependency providers
4. **Exception Types**: Define domain-specific exceptions

## Related Components

- **Agents**: Use the core for configuration and registration
- **Workflows**: Leverage the dependency system for component composition
- **API**: Uses core exceptions for error handling
- **Knowledge Base**: Configured through the core settings