# Agents in Agentical Framework

## Overview

The `agents` directory contains the core agent implementation for the Agentical framework. Agents are the primary actors in the system, designed to perform specific tasks using large language models (LLMs) with defined capabilities.

## Directory Structure

```
agents/
├── __init__.py             # Package initialization
├── base.py                 # Base agent classes and protocols
├── registry.py             # Agent registration and discovery
├── capabilities/           # Capability interfaces
│   ├── __init__.py
│   ├── code.py             # Code-related capabilities
│   ├── content.py          # Content generation capabilities
│   └── ...
├── mixins/                 # Optional agent extensions
│   ├── __init__.py
│   ├── memory.py           # Memory enhancement mixins
│   └── ...
└── implementations/        # Concrete agent implementations
    ├── __init__.py
    ├── general.py          # General-purpose agents
    └── specialized.py      # Specialized agents
```

## Core Components

### Agent Class

The base `Agent` class serves as a container for:

- **System prompts**: Instructions for the LLM
- **Function tools**: Functions that the LLM may call
- **Structured output type**: The expected output structure
- **Model settings**: Configuration for the underlying LLM

### Capabilities

Capabilities define what an agent can do through Protocol classes:

- `TextGenerationCapability`: For generating text content
- `CodeGenerationCapability`: For generating code
- `CodeReviewCapability`: For reviewing code
- `KnowledgeRetrievalCapability`: For retrieving information
- And others...

### Mixins

Mixins provide reusable functionality that can be added to agents:

- `MemoryMixin`: Adds conversation memory to agents
- `ReflectionMixin`: Adds self-reflection capabilities
- `PlanningMixin`: Adds planning capabilities

### Implementations

Concrete agent implementations ready for use:

- General-purpose agents for common tasks
- Specialized agents for specific domains
- Custom agents for particular use cases

## Usage Example

```python
from agentical import create_agent
from agentical.agents.capabilities import TextGenerationCapability

# Create a simple agent
agent = create_agent(
    name="Research Assistant",
    description="An agent that helps with research tasks",
    system_prompts=["You are a helpful research assistant."],
    tools=["web_search", "knowledge_retrieve"],
    model="gpt-4"
)

# Run the agent
result = await agent.run("What are the latest developments in quantum computing?")
print(result.output)
```

## Extension Points

1. **New Capabilities**: Add new Protocol classes in the `capabilities/` directory
2. **Custom Mixins**: Create new mixins in the `mixins/` directory
3. **Specialized Agents**: Implement new agent types in the `implementations/` directory

## Key Concepts

### Hybrid Agent-Workflow Compatibility

Agents expose capabilities that workflows can check to ensure compatibility. This hybrid approach allows:

- Reusing agents across multiple workflows
- Specializing agents for specific use cases
- Creating a clear contract between agents and workflows

### Tool Registration

Agents can use tools registered through:

- The `@agent.tool` decorator for tools that need agent context
- The `@agent.tool_plain` decorator for tools that don't need context
- Direct registration via the `register_tool` method

### Message Handling

Agents maintain a message history that can be accessed for:

- Continuing conversations
- Understanding agent reasoning
- Debugging agent behavior

## Best Practices

1. Define clear capabilities for each agent
2. Use mixins to share functionality between agents
3. Keep system prompts focused and concise
4. Test agents with a variety of inputs
5. Document agent capabilities and limitations
6. Use structured outputs when possible
7. Leverage the registry for agent discovery

## Related Components

- **Workflows**: Define how agents interact
- **Tools**: Provide functionality to agents
- **Knowledge Base**: Source of information for agents