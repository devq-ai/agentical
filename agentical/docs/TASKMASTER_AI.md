# Taskmaster AI Integration

This document provides information on how to use the Taskmaster AI integration in this project.

## Overview

Taskmaster AI is a task management system for AI-driven development that has been integrated with Wrenchai as an MCP (Model Context Protocol) server. This allows you to create, manage, and track tasks directly through the MCP interface.

## Setup

### Prerequisites

- Node.js (v14 or higher recommended)
- Anthropic API key (for Claude)
- Gemini API key (optional, for Google AI)

### Configuration

Taskmaster AI is configured in the `mcp_config.json` file with the following environment variables:

- `anthropic_api_key`: Your Anthropic API key (required)
- `gemini_api_key`: Your Gemini API key (optional)
- `MODEL`: The Claude model to use (default: claude-3-7-sonnet-20250219)
- `PERPLEXITY_MODEL`: The Perplexity model to use (default: sonar-pro)
- `MAX_TOKENS`: Maximum tokens to use (default: 64000)
- `TEMPERATURE`: Temperature for generation (default: 0.2)
- `DEFAULT_SUBTASKS`: Default number of subtasks (default: 5)
- `DEFAULT_PRIORITY`: Default priority for tasks (default: medium)

### Set Up API Keys

You can set up your API keys using the Secrets Manager:

```bash
# Store the Anthropic API key (required)
secrets-manager store anthropic_api_key --service mcp-servers

# Store the Gemini API key (optional)
secrets-manager store gemini_api_key --service mcp-servers
```

The Secrets Manager will prompt you to enter your API key securely. Alternatively, you can set up the API keys directly in your environment:

```bash
export anthropic_api_key="YOUR_ANTHROPIC_API_KEY"
export gemini_api_key="YOUR_GEMINI_API_KEY"
```

## Starting Taskmaster AI

You can start Taskmaster AI using the provided script:

```bash
./run_taskmaster.sh
```

This script will:
1. Attempt to retrieve the API keys from the Secrets Manager
2. Fall back to direct keychain access if Secrets Manager is not available
3. Use environment variables if they're already set
4. Start the Taskmaster AI MCP server with the configured settings

## Using Taskmaster AI through MCP

Taskmaster AI is used through the MCP (Model Context Protocol) interface. You can interact with it in your Python code using the MCP client:

```python
from core.tools.mcp_client import get_mcp_manager
from pydantic_ai.mcp import Runnable

class YourAgent(Runnable):
    async def run(self):
        # Create a task
        task = await self.execute_mcp_function(
            "taskmaster-ai",
            "createTask",
            {
                "name": "Implement Feature X",
                "description": "Add Feature X to the project",
                "priority": "high"
            }
        )
        
        # Get task details
        task_id = task["id"]
        task_details = await self.execute_mcp_function(
            "taskmaster-ai",
            "getTask",
            {"taskId": task_id}
        )
        
        # Generate subtasks
        subtasks = await self.execute_mcp_function(
            "taskmaster-ai",
            "generateSubtasks",
            {"taskId": task_id}
        )
        
        return subtasks
```

### Running with MCP Servers

To use Taskmaster AI in your agent, you need to run it with the MCP server:

```python
async def main():
    # Get MCP manager
    manager = get_mcp_manager("mcp_config.json")
    
    # Get Taskmaster AI server
    server = manager.get_server_from_config("taskmaster-ai")
    
    # Create your agent
    agent = YourAgent()
    
    # Run with MCP server
    async with agent.run_mcp_servers(server):
        result = await agent.run()
        return result
```

## Available MCP Functions

Taskmaster AI provides several MCP functions:

- `version`: Get the Taskmaster AI version
- `createTask`: Create a new task
- `getTask`: Get details of a task
- `updateTask`: Update a task
- `deleteTask`: Delete a task
- `generateSubtasks`: Generate subtasks for a task
- `listTasks`: List all tasks

Each function takes specific parameters. See the test script for examples.

## Troubleshooting

If you encounter issues with Taskmaster AI:

1. Check that your API keys are correctly set in the Secrets Manager:
   ```bash
   secrets-manager get anthropic_api_key
   ```

2. Make sure Node.js is installed (v14 or higher):
   ```bash
   node --version
   ```

3. Check the logs when starting the server:
   ```bash
   ./run_taskmaster.sh
   ```

4. If the Secrets Manager is not working, you can set the API key directly:
   ```bash
   export anthropic_api_key="YOUR_ANTHROPIC_API_KEY"
   ./run_taskmaster.sh
   ```