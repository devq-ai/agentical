# Agentical Architecture

## Overview

Agentical is an agentic framework built on Pydantic AI, designed to create AI systems through a composition of agents, workflows, tools, and playbooks. This document explains the core architecture decisions and design patterns that underpin the framework.

## Architectural Principles

1. **Separation of Concerns**: Agents, workflows, tools, and playbooks are decoupled to allow independent development and testing.
2. **Capability-Based Design**: Agents expose capabilities that workflows can leverage, creating a hybrid approach to agent-workflow compatibility.
3. **Type Safety**: Leveraging Pydantic for robust type validation throughout the system.
4. **Extensibility**: The framework is designed to be easily extended with new agents, tools, workflows, and knowledge sources.
5. **Observability**: Comprehensive monitoring and evaluation are built into the framework.

## Core Components

### Agents

Agents are the primary actors in the system, designed to perform specific tasks. The agent architecture follows a hybrid approach:

- **Base Capabilities**: All agents implement a core set of capabilities like text generation.
- **Specialized Extensions**: Agents can be extended with specialized capabilities through mixins and implementations.
- **Tool Integration**: Agents can use tools to interact with external systems or perform specific functions.

Each agent has:
- **System Prompts**: Instructions for the LLM
- **Function Tools**: Functions the LLM may call
- **Structured Output Type**: The expected output structure
- **Model Settings**: Configuration for the underlying LLM

### Workflows

Workflows define how agents interact to solve problems. The framework supports multiple workflow patterns:

- **Work-in-Parallel**: Multiple agents working concurrently
- **Self-Feedback Loop**: Agent improves output through iteration
- **Partner-Feedback Loop**: Agents collaborate by refining each other's work
- **Conditional Process**: Workflow with conditional branching
- **Agent-versus-Agent**: Competitive agent interactions
- **Handoff Pattern**: Sequential workflow with clear transitions
- **Human-in-the-Loop**: Workflow requiring user approval/input

Complex workflows leverage Pydantic-Graph for state machine-based execution with type-safe transitions.

### Tools

Tools are reusable components that agents can use to perform specific tasks:

- **IO Tools**: File system operations, reading/writing data
- **Web Tools**: Web searches, API calls, web scraping
- **Knowledge Tools**: Knowledge base queries, information retrieval
- **Data Tools**: Data processing, transformation, analysis

Tools are registered with agents and can be accessed during execution.

### Playbooks

Playbooks are configuration files that define:

- **Objective**: What the system aims to accomplish
- **Success Criteria**: How to evaluate success
- **Agents**: Which agents to use
- **Tools**: Which tools to make available
- **Workflows**: How agents should interact

Playbooks can be defined in YAML, JSON, or through a Python API.

### Knowledge Base

The knowledge base, powered by SurrealDB, serves as both:

- **System Resource**: Storing configuration, historical runs, and system data
- **Agent Tool**: Providing agents with domain-specific knowledge

It supports vector embeddings for semantic search, allowing agents to retrieve relevant information.

## API Layer

The API layer, built on FastAPI, provides:

- **REST Endpoints**: For managing agents, workflows, and playbooks
- **WebSockets**: For streaming agent responses
- **Background Tasks**: For long-running workflows
- **Webhooks**: For human-in-the-loop interactions

## Integration Points

Agentical integrates with several external systems:

- **LLM Providers**: OpenAI, Anthropic, etc.
- **Embedding Providers**: For vector embeddings
- **SurrealDB**: For knowledge storage
- **Logfire**: For monitoring and observability
- **MCP Protocol**: For tool interoperability
- **A2A Protocol**: For agent interoperability

## Deployment Architecture

Agentical can be deployed in various configurations:

- **Single Instance**: All components running in a single process
- **Microservices**: Components deployed as separate services
- **Serverless**: Components deployed as serverless functions
- **Hybrid**: Mix of deployment models based on requirements

## Data Flow

1. **Input Processing**: User requests or scheduled tasks trigger playbook execution
2. **Workflow Execution**: The workflow orchestrates agent interactions
3. **Agent Execution**: Agents process inputs and generate outputs
4. **Tool Usage**: Agents use tools to perform specific tasks
5. **Knowledge Retrieval**: Agents query the knowledge base for information
6. **Result Aggregation**: Results from agents are combined according to the workflow
7. **Output Generation**: Final results are returned to the user

## Security Considerations

- **API Authentication**: Secure API access through token-based authentication
- **Tool Permissions**: Limit agent access to tools based on capabilities
- **Data Validation**: Validate all inputs and outputs through Pydantic models
- **Audit Logging**: Log all agent actions for accountability

## Performance Considerations

- **Caching**: Cache expensive operations like embeddings and LLM calls
- **Batching**: Batch multiple requests to external services when possible
- **Async Processing**: Use async/await for non-blocking I/O operations
- **Horizontal Scaling**: Deploy multiple instances for high availability

## Evolution Strategy

The Agentical architecture is designed to evolve over time:

1. **Core Stability**: Maintain a stable core API while adding features
2. **Extension Points**: Provide clear extension points for customization
3. **Versioned Components**: Version components independently when possible
4. **Backward Compatibility**: Maintain backward compatibility for existing playbooks

This architecture provides a solid foundation for building complex AI systems while maintaining flexibility, reliability, and observability.