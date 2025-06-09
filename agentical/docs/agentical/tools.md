# Tools in Agentical Framework

## Overview

The `tools` directory contains implementations of tools that agents can use to perform specific tasks in the Agentical framework. Tools extend agent capabilities by providing access to external systems, data processing functions, and specialized operations that go beyond the core language model capabilities.

## Directory Structure

```
tools/
├── __init__.py             # Package initialization
├── base.py                 # Base tool classes
├── registry.py             # Tool discovery and registration
├── decorators.py           # Tool decorators
└── implementations/        # Concrete tool implementations
    ├── __init__.py
    ├── io/                 # I/O tools
    ├── web/                # Web tools
    ├── data/               # Data processing tools
    ├── knowledge/          # Knowledge-related tools
    │   ├── __init__.py
    │   ├── query.py        # Knowledge base query tools
    │   ├── retrieve.py     # Knowledge retrieval tools
    │   └── store.py        # Knowledge storage tools
    └── ...
```

## Core Components

### Base Tool Classes

The `base.py` file defines the fundamental tool abstractions:

- **Tool**: Base class for all tools in the framework
- **AsyncTool**: Base class for asynchronous tools
- **SyncTool**: Base class for synchronous tools
- **ToolResult**: Container for tool execution results
- **ToolContext**: Context object for tool execution

### Tool Registry

The `registry.py` file implements a registry for discovering and managing tools:

- **ToolRegistry**: Central registry for all tools
- **ToolCategory**: Classification of tools by purpose
- **ToolMetadata**: Information about tool capabilities
- **ToolDiscovery**: Automatic discovery of available tools

### Tool Decorators

The `decorators.py` file provides decorators for defining and registering tools:

- **@tool**: Register a function as a tool
- **@tool_with_context**: Register a function as a tool with access to context
- **@tool_category**: Assign a tool to a category
- **@tool_metadata**: Add metadata to a tool

## Tool Categories

### I/O Tools

The `implementations/io/` directory contains tools for file and data I/O:

- **FileReader**: Read content from files
- **FileWriter**: Write content to files
- **DirectoryLister**: List files in a directory
- **JSONParser**: Parse JSON data
- **CSVParser**: Parse CSV data

### Web Tools

The `implementations/web/` directory contains tools for web interaction:

- **WebSearch**: Search the web for information
- **WebBrowser**: Browse web pages and extract content
- **APIClient**: Make requests to external APIs
- **WebScraper**: Extract data from web pages
- **RSSReader**: Read RSS feeds

### Data Processing Tools

The `implementations/data/` directory contains tools for data manipulation:

- **DataTransformer**: Transform data between formats
- **DataFilter**: Filter data based on criteria
- **DataSorter**: Sort data collections
- **DataAggregator**: Aggregate data from multiple sources
- **DataVisualizer**: Generate data visualizations

### Knowledge Tools

The `implementations/knowledge/` directory contains tools for knowledge base interaction:

- **KnowledgeQuery**: Query the knowledge base
- **KnowledgeRetriever**: Retrieve information from the knowledge base
- **KnowledgeStore**: Store information in the knowledge base
- **KnowledgeSearch**: Search the knowledge base semantically

## Tool Integration with Agents

Tools are integrated with agents in several ways:

- **Direct Registration**: Tools can be registered directly with an agent
- **Capability-based Discovery**: Agents can discover tools based on capabilities
- **Dynamic Loading**: Tools can be loaded at runtime based on needs
- **Tool Chains**: Tools can be composed into chains for complex operations

## Usage Examples

### Defining a Tool

```python
from agentical.tools.base import AsyncTool
from agentical.core.registry import register_tool

@register_tool("web_search")
class WebSearchTool(AsyncTool):
    """Tool for searching the web."""
    
    async def execute(self, query: str, limit: int = 5) -> dict:
        """
        Search the web for information.
        
        Args:
            query: The search query
            limit: Maximum number of results
            
        Returns:
            Dictionary containing search results
        """
        # Implementation details...
        return {"results": [...]}
```

### Using a Tool with an Agent

```python
from agentical import create_agent

# Create an agent with tools
agent = create_agent(
    name="Research Assistant",
    system_prompts=["You are a helpful research assistant."],
    tools=["web_search", "knowledge_retrieve"]
)

# Run the agent (tools will be available to the agent)
result = await agent.run("Research quantum computing advances")
```

## Tool Development

### Creating a New Tool

To create a new tool:

1. Subclass an appropriate base tool class
2. Implement the required methods (execute for AsyncTool)
3. Register the tool with the registry
4. Document the tool's purpose, parameters, and returns

### Tool Testing

Best practices for testing tools:

- Test tool functionality in isolation
- Mock external dependencies
- Test error handling and edge cases
- Validate tool output structure
- Measure performance characteristics

## Tool Security

Security considerations for tools:

- **Permission Management**: Control which tools agents can access
- **Resource Limits**: Prevent excessive resource usage
- **Input Validation**: Validate all inputs before processing
- **Output Sanitization**: Ensure safe output from tools
- **Rate Limiting**: Prevent abuse of external services

## Best Practices

1. Make tools focused and single-purpose
2. Document tool parameters and return values clearly
3. Handle errors gracefully and provide useful error messages
4. Consider performance implications, especially for I/O operations
5. Cache results when appropriate
6. Follow the principle of least privilege
7. Make tools composable with other tools

## Related Components

- **Agents**: Use tools to extend their capabilities
- **Workflows**: Coordinate tool usage across multiple agents
- **Knowledge Base**: Source of information for knowledge tools