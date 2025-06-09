# Taskmaster AI Integration for Wrench AI

This document provides instructions for setting up and using Taskmaster AI with Wrench AI.

## Overview

Taskmaster AI is integrated with Wrench AI using the Model Context Protocol (MCP). This integration allows you to create and manage tasks directly through the MCP interface.

## Setup

### Prerequisites

- Node.js (v14 or higher)
- Python 3.8+ with `keyring` package installed
- Anthropic API key

### Storing Your API Key

The Anthropic API key is stored securely using the system keychain via the `keyring` Python package. To store your API key:

```bash
# Run the setup script and follow the prompts
./store_anthropic_key.py
```

This will guide you through storing your Anthropic API key securely in the system keychain under the service name `mcp-servers` and the account name `anthropic_api_key`.

## Running Taskmaster AI

After storing your API key, you can run Taskmaster AI using the provided script:

```bash
./taskmaster.sh
```

This script will:
1. Check if your API key is already stored in the keychain
2. If not found, prompt you to store it
3. Start Taskmaster AI with the stored key

Alternatively, you can run the Python script directly:

```bash
python run_taskmaster_keyring.py
```

## Troubleshooting

If you encounter issues:

1. Verify your API key is stored correctly:
   ```bash
   python -c "import keyring; print(bool(keyring.get_password('mcp-servers', 'anthropic_api_key')))"
   ```
   This should print `True` if the key is stored.

2. Test keychain access:
   ```bash
   python test_keychain.py
   ```
   This will try different ways to access the API key and show the results.

3. If you continue to have issues, try setting the environment variable directly:
   ```bash
   export anthropic_api_key="your_api_key_here"
   npx -y --package=task-master-ai task-master-ai
   ```

## Files

- `store_anthropic_key.py`: Script to store your Anthropic API key in the keychain
- `run_taskmaster_keyring.py`: Script to run Taskmaster AI using the stored key
- `taskmaster.sh`: Shell script that checks for the key and runs Taskmaster AI
- `test_keychain.py`: Utility to test keychain access
- `task_memory_persistence.json`: Example task definition for Taskmaster AI
- `task_expand_model_library.json`: Another example task definition

## Using Taskmaster AI

Once Taskmaster AI is running, you can interact with it through the command line or programmatically through the MCP interface. The MCP configuration in `mcp_config.json` has been set up to use the stored API key.

For more information on using Taskmaster AI, refer to the Taskmaster AI documentation.