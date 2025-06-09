# API in Agentical Framework

## Overview

The `api` directory contains the FastAPI implementation for exposing Agentical's functionality through HTTP endpoints. This API layer enables applications to interact with agents, workflows, playbooks, and the knowledge base through a well-defined REST interface with additional WebSocket support for streaming responses.

## Directory Structure

```
api/
├── __init__.py             # Package initialization
├── app.py                  # FastAPI application setup
├── routes/                 # API routes
│   ├── __init__.py
│   ├── agents.py           # Agent management endpoints
│   ├── workflows.py        # Workflow management endpoints
│   ├── playbooks.py        # Playbook management endpoints
│   ├── runs.py             # Run execution endpoints
│   ├── tools.py            # Tool management endpoints
│   ├── knowledge.py        # Knowledge base endpoints
│   └── webhooks.py         # Webhook endpoints for human-in-the-loop
├── models/                 # API data models
│   ├── __init__.py
│   ├── requests.py         # Request models
│   └── responses.py        # Response models
├── websockets/             # WebSocket handlers
│   ├── __init__.py
│   └── streams.py          # Streaming handlers
├── dependencies/           # FastAPI dependencies
│   ├── __init__.py
│   ├── auth.py             # Authentication dependencies
│   ├── knowledge.py        # Knowledge base dependencies
│   └── rate_limit.py       # Rate limiting dependencies
├── middleware/             # FastAPI middleware
│   ├── __init__.py
│   └── telemetry.py        # Telemetry middleware
└── background/             # Background tasks
    ├── __init__.py
    └── workers.py          # Background workers
```

## Core Components

### FastAPI Application

The `app.py` file sets up the FastAPI application with:

- CORS configuration
- Middleware setup
- Router registration
- Application lifecycle management

### Routes

API routes are organized by resource type:

- **Agents**: Endpoints for managing and running agents
- **Workflows**: Endpoints for managing and executing workflows
- **Playbooks**: Endpoints for configuring and running playbooks
- **Runs**: Endpoints for tracking and managing execution runs
- **Tools**: Endpoints for discovering and managing tools
- **Knowledge**: Endpoints for interacting with the knowledge base
- **Webhooks**: Endpoints for human-in-the-loop interactions

### Models

Pydantic models for API requests and responses:

- **Request Models**: Define the expected structure of API requests
- **Response Models**: Define the structure of API responses

### WebSockets

Support for real-time communication:

- **Streaming**: Handlers for streaming agent and workflow responses

### Dependencies

Reusable components for dependency injection:

- **Authentication**: User authentication and authorization
- **Knowledge**: Knowledge base client injection
- **Rate Limiting**: Request rate limiting

### Middleware

Middleware components for request processing:

- **Telemetry**: Request logging and performance tracking

### Background Tasks

Support for long-running operations:

- **Workers**: Background task workers for async processing

## Key API Endpoints

### Agent Endpoints

- `POST /api/agents/run`: Run an agent with the provided input
- `GET /api/agents`: List available agents
- `GET /api/agents/{agent_id}`: Get agent details
- `WS /api/agents/run/{run_id}/stream`: Stream agent results

### Workflow Endpoints

- `POST /api/workflows/run`: Run a workflow with the provided input
- `GET /api/workflows`: List available workflows
- `GET /api/workflows/{workflow_id}`: Get workflow details
- `WS /api/workflows/run/{run_id}/stream`: Stream workflow results

### Playbook Endpoints

- `POST /api/playbooks/execute`: Execute a playbook
- `GET /api/playbooks`: List available playbooks
- `GET /api/playbooks/{playbook_id}`: Get playbook details
- `POST /api/playbooks`: Create a new playbook

### Knowledge Endpoints

- `POST /api/knowledge/items`: Create a new knowledge item
- `GET /api/knowledge/items/{item_id}`: Get knowledge item details
- `POST /api/knowledge/search`: Search the knowledge base

### Human-in-the-Loop Endpoints

- `POST /api/webhooks/human-input/{run_id}`: Submit human input for a workflow

## Authentication

The API supports multiple authentication methods:

- API key authentication
- JWT token authentication
- OAuth2 authentication (optional)

## Streaming Support

For long-running operations, the API provides WebSocket endpoints to stream results in real-time:

- Chunked responses from LLM models
- Step-by-step workflow execution updates
- Progress updates for long-running operations

## Background Processing

Long-running operations are handled asynchronously:

- Tasks are queued for background processing
- Clients receive a run ID for tracking
- Results can be polled or streamed via WebSockets

## OpenAPI Documentation

The API automatically generates OpenAPI documentation with:

- Detailed endpoint descriptions
- Request and response schemas
- Example requests and responses
- Authentication requirements

## Best Practices

1. Use appropriate HTTP methods (GET, POST, PUT, DELETE)
2. Return appropriate status codes
3. Implement proper error handling
4. Document all endpoints with meaningful descriptions
5. Use background tasks for long-running operations
6. Implement rate limiting for public endpoints
7. Provide WebSocket alternatives for streaming responses

## Related Components

- **Agents**: Core functionality exposed through the API
- **Workflows**: Orchestration logic accessed via endpoints
- **Knowledge Base**: Data source for many operations