# Taskmaster AI Setup with Secrets Manager

This guide explains how to set up Taskmaster AI using environment variables securely retrieved from your keychain via secrets-manager.

## Available Scripts

### `create_taskmaster_env.py`

This script generates a `.env` file for Taskmaster AI by retrieving secret API keys from your macOS Keychain:

- Retrieves `anthropic_api_key` and `gemini_api_key` from the keychain
- Sets up default Taskmaster configuration values
- Creates a `.env` file in the current directory

```bash
./create_taskmaster_env.py
```

### `taskmaster_with_env.sh`

This script provides an all-in-one solution:

1. Runs `create_taskmaster_env.py` to generate the `.env` file
2. Starts Taskmaster AI which will automatically use the environment variables from the `.env` file

```bash
./taskmaster_with_env.sh
```

## Environment Variables

Taskmaster AI uses the following environment variables:

| Variable | Description | Source |
|----------|-------------|--------|
| `anthropic_api_key` | API key for Claude AI | Retrieved from keychain |
| `gemini_api_key` | API key for Google Gemini | Retrieved from keychain |
| `MODEL` | AI model to use | Set to "claude-3-7-sonnet-20250219" |
| `MAX_TOKENS` | Maximum token limit | Set to "64000" |
| `TEMPERATURE` | Temperature setting | Set to "0.2" |
| `DEFAULT_SUBTASKS` | Default number of subtasks | Set to "5" |
| `DEFAULT_PRIORITY` | Default priority level | Set to "medium" |

## Troubleshooting

If you encounter issues retrieving API keys from the keychain:

1. Verify your keys are correctly stored in the keychain:
   - The Anthropic key should be stored as an internet password for "https://api.anthropic.com" with account "Bearer"
   - The Gemini key should be stored with service "mcp-servers" and account "gemini_api_key"

2. Try manually setting the environment variables:
   ```bash
   export anthropic_api_key="your_key_here"
   export gemini_api_key="your_key_here"
   npx -y --package=task-master-ai task-master-ai
   ```