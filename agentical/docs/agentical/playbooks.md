# Playbooks in Agentical Framework

## Overview

The `playbooks` directory contains the implementation of Agentical's playbook system, which provides a declarative way to define complex AI solutions. Playbooks serve as configuration files that define objectives, success criteria, agents, tools, and workflows, allowing users to create sophisticated AI applications without writing code.

## Directory Structure

```
playbooks/
├── __init__.py             # Package initialization
├── base.py                 # Base playbook definitions
├── config.py               # Playbook configuration schemas
├── loader.py               # Playbook loading utilities
└── templates/              # Template playbooks
    ├── __init__.py
    └── ...
```

## Core Components

### Base Playbook

The `base.py` file defines the foundational playbook classes:

- **Playbook**: The core class for defining and executing playbooks
- **PlaybookResult**: Container for playbook execution results
- **PlaybookValidator**: Validates playbook configurations
- **PlaybookRegistry**: Manages available playbooks

### Configuration Schemas

The `config.py` file defines Pydantic models for playbook configuration:

- **PlaybookConfig**: Top-level configuration schema
- **AgentConfig**: Configuration for agents within a playbook
- **WorkflowConfig**: Configuration for workflows within a playbook
- **ToolConfig**: Configuration for tools within a playbook
- **ObjectiveConfig**: Configuration for playbook objectives

### Playbook Loader

The `loader.py` file provides utilities for loading playbooks:

- **FileLoader**: Load playbooks from YAML or JSON files
- **DirectoryLoader**: Discover playbooks in a directory
- **DatabaseLoader**: Load playbooks from the knowledge base
- **TemplateLoader**: Create playbooks from templates

### Playbook Templates

The `templates/` directory contains predefined playbook templates:

- **Starter templates**: Simple templates for common use cases
- **Domain-specific templates**: Templates for specific domains
- **Pattern templates**: Templates for common workflow patterns

## Playbook Structure

A typical playbook has the following structure:

- **Metadata**: Name, description, version, and other metadata
- **Objective**: The goal the playbook aims to achieve
- **Success Criteria**: How to evaluate if the objective was met
- **Agents**: The agents involved in the playbook
- **Tools**: The tools available to the agents
- **Workflows**: How agents interact to solve the problem
- **Configuration**: Additional settings for execution

## Usage Examples

### Creating a Playbook

```python
from agentical import Playbook

# Create a playbook from a configuration
playbook = Playbook.from_config({
    "name": "Research Project",
    "objective": "Research and create a comprehensive report on a topic",
    "success_criteria": [
        "Covers key aspects of the topic",
        "Includes recent developments",
        "Well-structured and coherent"
    ],
    "agents": [
        {"id": "researcher", "type": "research_agent"},
        {"id": "writer", "type": "content_writer"},
        {"id": "editor", "type": "content_editor"}
    ],
    "workflows": [
        {
            "id": "research_workflow",
            "type": "partner_feedback_loop",
            "agents": {
                "researcher": "researcher",
                "writer": "writer",
                "editor": "editor"
            }
        }
    ],
    "tools": ["web_search", "knowledge_base", "document_generator"]
})
```

### Executing a Playbook

```python
# Execute the playbook
result = await playbook.execute({
    "topic": "Sustainable energy solutions",
    "depth": "comprehensive",
    "format": "report"
})

# Access the results
print(f"Success: {result.success}")
print(f"Output: {result.output}")
```

## Playbook Templates

Agentical provides several playbook templates for common use cases:

- **Research Assistant**: Conduct research and create reports
- **Content Creator**: Generate and refine content
- **Code Developer**: Write, review, and improve code
- **Data Analyst**: Analyze and visualize data
- **Customer Support**: Respond to customer inquiries

## Advanced Features

### Dynamic Playbooks

Playbooks can adjust their behavior based on input:

- **Conditional Workflows**: Choose workflows based on input
- **Dynamic Agent Selection**: Select agents based on requirements
- **Tool Configuration**: Configure tools based on context
- **Adaptive Execution**: Adjust execution based on interim results

### Nested Playbooks

Playbooks can include other playbooks as components:

- **Playbook Composition**: Build complex playbooks from simpler ones
- **Reusable Patterns**: Define once, use many times
- **Hierarchical Execution**: Manage complexity through nesting

### Human-in-the-Loop Integration

Playbooks can incorporate human feedback:

- **Approval Points**: Define points requiring human approval
- **Feedback Collection**: Gather human input during execution
- **Review Stages**: Include explicit review phases

## Best Practices

1. Define clear objectives and success criteria
2. Use appropriate agents for specific roles
3. Structure workflows to match problem-solving patterns
4. Leverage templates for common use cases
5. Test playbooks with various inputs
6. Document playbook purpose and usage
7. Version playbooks as they evolve

## Related Components

- **Agents**: The actors defined in playbooks
- **Workflows**: The interaction patterns used in playbooks
- **Tools**: The capabilities available in playbooks
- **Knowledge Base**: Source of information for playbook execution