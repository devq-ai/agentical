# Taskmaster AI Integration in Wrenchai

## Overview

Taskmaster AI has been integrated into the Wrenchai project as an MCP (Model Context Protocol) server. This allows you to create, manage, and track tasks directly through the MCP interface.

## Configuration Status

The Taskmaster AI MCP server has been configured in `mcp_config.json` with the following settings:

- Using Claude 3.7 Sonnet (claude-3-7-sonnet-20250219) as the AI model
- Maximum tokens: 64,000
- Temperature: 0.2
- Default subtasks: 5
- Default priority: medium

## Setting Up Your API Keys

To use Taskmaster AI, you need to set up your API keys:

### Using Secrets Manager (Recommended)

```bash
# Store your Anthropic API key (required)
secrets-manager store anthropic_api_key --service mcp-servers
```

The Secrets Manager will prompt you to enter your API key securely.

### Using Direct Environment Variables

If you prefer, you can set the environment variable directly:

```bash
export anthropic_api_key="YOUR_ANTHROPIC_API_KEY"
```

## Starting Taskmaster AI

Once your API key is set up, you can start Taskmaster AI with:

```bash
./run_taskmaster.sh
```

This script will automatically retrieve your API key from the Secrets Manager and start the server.

## Using Taskmaster AI in Your Code

Taskmaster AI can be used in your Python code through the MCP client. Here's an example:

```python
from pydantic_ai.mcp import Runnable

class MyAgent(Runnable):
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
        subtasks = await self.execute_mcp_function(
            "taskmaster-ai",
            "generateSubtasks",
            {"taskId": task_id}
        )
        
        return subtasks
```

For more information, see the full documentation in `TASKMASTER_AI.md`.

## Files Added

- `mcp_config.json`: Updated with Taskmaster AI configuration
- `run_taskmaster.sh`: Script to start the Taskmaster AI MCP server
- `start_taskmaster.py`: Python helper for running the Taskmaster AI server
- `TASKMASTER_AI.md`: Full documentation