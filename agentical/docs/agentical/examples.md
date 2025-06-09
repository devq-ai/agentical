# Examples in Agentical Framework

## Overview

The `examples` directory contains sample implementations and tutorials that demonstrate how to use the Agentical framework. These examples serve as both documentation and practical starting points for developers building applications with Agentical.

## Directory Structure

```
examples/
├── agents/                  # Example agents
├── workflows/               # Example workflows
├── playbooks/               # Example playbooks
├── knowledge/               # Example knowledge base usage
├── api/                     # Example API usage
└── tutorials/               # Tutorials
```

## Core Components

### Agent Examples

The `agents/` directory contains examples of different agent implementations:

- **Basic Agents**: Simple agent implementations to get started
- **Specialized Agents**: Domain-specific agent examples
- **Custom Capability Agents**: Agents with custom capabilities
- **Multi-modal Agents**: Agents that handle images, audio, etc.

### Workflow Examples

The `workflows/` directory showcases different workflow patterns:

- **Parallel Workflows**: Examples of concurrent agent execution
- **Feedback Loops**: Self and partner feedback workflow examples
- **Conditional Workflows**: Examples with branching logic
- **Agent-versus-Agent**: Competitive workflow examples
- **Human-in-the-Loop**: Examples incorporating human feedback

### Playbook Examples

The `playbooks/` directory contains sample playbook configurations:

- **Basic Playbooks**: Simple playbook configurations
- **Complex Playbooks**: Multi-workflow playbook examples
- **Domain-specific Playbooks**: Playbooks for specific use cases
- **Customized Playbooks**: Examples of extending playbooks

### Knowledge Base Examples

The `knowledge/` directory shows how to use the knowledge base:

- **Knowledge Storage**: Examples of storing information
- **Semantic Search**: Demonstrations of search capabilities
- **Knowledge Integration**: Using knowledge in agents and workflows
- **Custom Embedding**: Examples of custom embedding models

### API Examples

The `api/` directory demonstrates how to use the API:

- **REST Client**: Examples of calling the REST API
- **WebSocket Client**: Examples of using streaming endpoints
- **API Integration**: Integrating Agentical into applications
- **Authentication**: Examples of API authentication

### Tutorials

The `tutorials/` directory contains step-by-step guides:

- **Getting Started**: Quick start guide for new users
- **Building Agents**: Tutorial on creating custom agents
- **Creating Workflows**: Guide to designing effective workflows
- **Knowledge Base Setup**: Tutorial on setting up and populating the knowledge base
- **API Integration**: Guide to integrating with the API

## Example Applications

Complete example applications that demonstrate real-world use cases:

### 1. Research Assistant

A complete research assistant application that:
- Searches for information
- Retrieves relevant knowledge
- Generates comprehensive reports
- Includes citations and references

### 2. Code Developer

A code development assistant that:
- Generates code based on requirements
- Reviews and improves existing code
- Explains code functionality
- Answers programming questions

### 3. Content Creator

A content creation system that:
- Generates articles and blog posts
- Edits and improves content
- Creates SEO-friendly titles and descriptions
- Suggests images and media

### 4. Customer Support Bot

A customer support system that:
- Answers customer questions
- Retrieves relevant product information
- Escalates complex issues to humans
- Follows up with customers

## Running the Examples

Most examples can be run directly with:

```bash
python -m agentical.examples.<example_path>
```

For example:

```bash
# Run the basic agent example
python -m agentical.examples.agents.basic_agent

# Run the feedback loop workflow example
python -m agentical.examples.workflows.feedback_loop
```

## Using Examples as Templates

The examples are designed to be used as templates for your own implementations:

1. Copy the relevant example
2. Modify it to suit your needs
3. Extend it with additional functionality
4. Integrate it into your application

## Best Practices

1. Start with the simplest example that matches your use case
2. Read the code comments for implementation details
3. Try modifying examples to understand how they work
4. Use the tutorials for guided learning
5. Reference the API documentation alongside examples
6. Experiment with different configurations

## Related Documentation

- **API Reference**: Detailed documentation of the framework API
- **Tutorials**: Step-by-step guides for building with Agentical
- **Concepts**: Explanations of core concepts and principles