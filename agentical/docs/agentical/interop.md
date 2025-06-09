# Interoperability in Agentical Framework

## Overview

The `interop` directory contains components that enable the Agentical framework to interact with external systems, frameworks, and protocols. This module ensures that Agentical can work seamlessly with other AI systems and tools in the broader ecosystem.

## Directory Structure

```
interop/
├── __init__.py             # Package initialization
├── mcp.py                  # Model Context Protocol implementation
└── a2a.py                  # Agent-to-Agent Protocol integration
```

## Core Components

### Model Context Protocol (MCP)

The `mcp.py` file implements the Model Context Protocol, which allows Agentical agents to connect to MCP servers to use their tools:

- **MCP Client**: Connect to MCP servers to use external tools
- **MCP Server**: Expose Agentical tools to other systems via MCP
- **Tool Adapters**: Convert between Agentical tools and MCP tools
- **Context Adapters**: Map between different context formats

### Agent-to-Agent (A2A) Protocol

The `a2a.py` file implements the Agent-to-Agent Protocol, which enables communication between agents built on different frameworks:

- **A2A Client**: Connect to external agents via the A2A protocol
- **A2A Server**: Expose Agentical agents to other systems
- **Message Translation**: Convert between different message formats
- **Agent Discovery**: Find and connect to external agents

## Supported Interoperability Standards

### Model Context Protocol (MCP)

The MCP implementation supports:

- **Tool Registration**: Exposing tools to MCP clients
- **Tool Invocation**: Calling tools on MCP servers
- **Tool Discovery**: Finding available tools on MCP servers
- **Context Propagation**: Maintaining context across tool calls

### Agent-to-Agent (A2A) Protocol

The A2A implementation supports:

- **Agent Communication**: Direct messaging between agents
- **Capability Advertisement**: Sharing agent capabilities
- **Task Delegation**: Assigning tasks to external agents
- **Result Integration**: Incorporating results from external agents

## Additional Interoperability Features

- **OpenAI Plugin Compatibility**: Support for OpenAI-compatible plugins
- **LangChain Integration**: Interoperability with LangChain tools and agents
- **REST API Adapters**: Connect to arbitrary REST APIs as tools
- **WebSocket Support**: Real-time communication with external systems

## Usage Example

```python
from agentical.interop.mcp import MCPClient
from agentical.interop.a2a import A2AClient

# Connect to an MCP server to use external tools
mcp_client = MCPClient(url="https://mcp-server.example.com")
tools = await mcp_client.list_tools()
result = await mcp_client.invoke_tool("web_search", {"query": "latest AI research"})

# Connect to an external agent via A2A
a2a_client = A2AClient(url="https://a2a-agent.example.com")
agent_capabilities = await a2a_client.get_capabilities()
task_result = await a2a_client.delegate_task("Summarize this article", {"url": "https://example.com/article"})
```

## Integration Points

### Integrating with MCP Servers

Agentical can act as both an MCP client and server:

- **As Client**: Connect to external MCP servers to use their tools
- **As Server**: Expose Agentical tools to other systems via MCP

### Integrating with A2A Agents

Agentical can interact with other A2A-compatible agents:

- **Direct Communication**: Send messages to external agents
- **Capability Discovery**: Find agents with required capabilities
- **Task Delegation**: Assign tasks to specialized external agents

## Best Practices

1. Validate external tools before integrating them
2. Implement timeouts for external system calls
3. Handle errors gracefully from external systems
4. Cache results when appropriate to reduce external calls
5. Document the capabilities and limitations of external integrations
6. Test interoperability with multiple systems
7. Monitor performance and reliability of external integrations

## Related Components

- **Agents**: Use interoperability features to extend capabilities
- **Tools**: Can be exposed or consumed through interop protocols
- **Workflows**: Can incorporate external agents and tools