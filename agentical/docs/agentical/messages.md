# Messages in Agentical Framework

## Overview

The `messages` directory contains components for handling message exchange in the Agentical framework. This module provides standardized structures and utilities for managing conversations, formatting messages, and maintaining interaction history between users, agents, and workflows.

## Directory Structure

```
messages/
├── __init__.py             # Package initialization
├── models.py               # Message data models
├── history.py              # Chat history management
└── formatters.py           # Message formatting utilities
```

## Core Components

### Message Models

The `models.py` file defines the data structures for messages:

- **Message**: Base class for all message types
- **UserMessage**: Messages from users to agents
- **AgentMessage**: Messages from agents to users
- **SystemMessage**: System instructions and prompts
- **ToolMessage**: Messages related to tool calls
- **FunctionCallMessage**: Messages containing function calls
- **FunctionResultMessage**: Messages containing function results

### Chat History

The `history.py` file provides functionality for managing conversation history:

- **History**: Track and manage conversation history
- **HistoryManager**: Advanced history management with filtering and pruning
- **PersistentHistory**: Store and retrieve conversation history
- **HistoryExporter**: Export history in various formats

### Message Formatting

The `formatters.py` file contains utilities for formatting messages:

- **Template Rendering**: Format messages using templates
- **Markdown Formatting**: Format messages with Markdown
- **Code Formatting**: Format code snippets in messages
- **Message Truncation**: Truncate messages to fit model limits

## Message Structure

A standard message includes the following fields:

- **id**: Unique identifier for the message
- **role**: The role of the message sender (user, agent, system, etc.)
- **content**: The content of the message
- **timestamp**: When the message was created
- **metadata**: Additional information about the message

## Usage Examples

### Creating and Using Messages

```python
from agentical.messages.models import UserMessage, AgentMessage
from agentical.messages.history import History

# Create messages
user_message = UserMessage(content="What can you tell me about quantum computing?")
agent_message = AgentMessage(content="Quantum computing is a type of computing that uses quantum phenomena...")

# Create history
history = History()
history.add_message(user_message)
history.add_message(agent_message)

# Use history with an agent
result = await agent.run("Tell me more about qubits", history=history)
```

### Formatting Messages

```python
from agentical.messages.formatters import MarkdownFormatter

# Create a formatter
formatter = MarkdownFormatter()

# Format a message
formatted_message = formatter.format(agent_message)
```

## Message Flow

In the Agentical framework, messages flow through several stages:

1. **Creation**: Messages are created by users, agents, or the system
2. **Validation**: Messages are validated for structure and content
3. **Formatting**: Messages are formatted for the intended recipient
4. **Processing**: Messages are processed by agents or workflows
5. **Storage**: Messages are stored in the history
6. **Retrieval**: Messages are retrieved for context in future interactions

## Message Context

Messages can include context to provide additional information:

- **Previous Messages**: References to previous messages in the conversation
- **Knowledge Context**: Related information from the knowledge base
- **Tool Context**: Information about available tools
- **User Context**: Information about the user

## Best Practices

1. Use appropriate message types for different scenarios
2. Keep message history pruned to relevant information
3. Include sufficient context for agent understanding
4. Format messages appropriately for different outputs
5. Validate message content for safety and appropriateness
6. Use metadata to track message processing
7. Export histories for analysis and debugging

## Related Components

- **Agents**: Process and generate messages
- **Workflows**: Orchestrate message flow between agents
- **API**: Expose message history through endpoints
- **Tools**: Generate tool-related messages