# CLI in Agentical Framework

## Overview

The `cli` directory contains the command-line interface implementation for the Agentical framework. The CLI provides a set of commands for interacting with agents, workflows, playbooks, and the knowledge base from the terminal, enabling both interactive use and scripting.

## Directory Structure

```
cli/
├── __init__.py             # Package initialization
├── commands.py             # CLI command definitions
├── knowledge.py            # Knowledge base CLI commands
└── scripts/                # CLI scripts
```

## Core Components

### Main CLI Application

The CLI is built using Typer, a modern library for building command-line applications in Python. The main CLI application is defined in `commands.py` and provides a set of commands for interacting with the Agentical framework.

### Knowledge Management Commands

The `knowledge.py` file contains specialized commands for managing the knowledge base, including importing, exporting, and searching knowledge.

### Scripts

The `scripts/` directory contains standalone scripts that can be run directly from the command line for specific tasks.

## Key Commands

### Agent Commands

- `agentical agent list`: List available agents
- `agentical agent run <agent-id>`: Run an agent interactively
- `agentical agent info <agent-id>`: Show details about an agent

### Workflow Commands

- `agentical workflow list`: List available workflows
- `agentical workflow run <workflow-id>`: Run a workflow
- `agentical workflow info <workflow-id>`: Show details about a workflow

### Playbook Commands

- `agentical playbook list`: List available playbooks
- `agentical playbook run <playbook-id>`: Run a playbook
- `agentical playbook create`: Create a new playbook

### Knowledge Commands

- `agentical knowledge search <query>`: Search the knowledge base
- `agentical knowledge import <file>`: Import knowledge from a file
- `agentical knowledge export <output-file>`: Export knowledge to a file

### Server Command

- `agentical serve`: Start the Agentical API server

## Interactive Mode

The CLI supports an interactive mode for running agents and workflows:

```
$ agentical agent run research-assistant --interactive
```

In interactive mode, the CLI will start a chat session with the agent, allowing for a conversation with real-time responses.

## Configuration

The CLI can be configured through:

1. Command-line arguments
2. Environment variables
3. Configuration files

The configuration precedence is: command-line arguments > environment variables > configuration files.

## Output Formats

The CLI supports multiple output formats:

- Human-readable text (default)
- JSON
- YAML
- Table

Example:

```
$ agentical agent list --format json
```

## Scripting Support

The CLI is designed to be easily used in scripts:

```bash
#!/bin/bash
# Example script that uses the Agentical CLI

# Run a workflow and capture the output
result=$(agentical workflow run research-workflow --input-file research-topic.json --format json)

# Process the result
echo "$result" | jq .summary
```

## Logging and Verbosity

The CLI supports different verbosity levels:

- `--quiet` or `-q`: Only show errors
- `--verbose` or `-v`: Show detailed information
- `--debug`: Show debug information

## Authentication

For operations that require authentication, the CLI supports:

- API key authentication
- Token-based authentication
- Interactive login

## Best Practices

1. Use the `--help` option to see available commands and options
2. Use the `--format json` option for scripting
3. Set up configuration files for common settings
4. Use the interactive mode for exploration
5. Create scripts for repetitive tasks

## Related Components

- **API**: The HTTP API that the CLI interacts with
- **Agents**: The agent functionality accessed via the CLI
- **Workflows**: The workflow functionality accessed via the CLI
- **Knowledge Base**: The knowledge base functionality accessed via the CLI