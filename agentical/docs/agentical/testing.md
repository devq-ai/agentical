# Testing in Agentical Framework

## Overview

The `testing` directory contains utilities and helpers for testing the Agentical framework components. This module provides tools for unit testing, integration testing, and mocking components to ensure the reliability and correctness of the framework.

## Directory Structure

```
testing/
├── __init__.py             # Package initialization
├── test_models.py          # Test model implementations
├── fixtures.py             # Test fixtures
└── assertions.py           # Test assertions
```

## Core Components

### Test Models

The `test_models.py` file provides test implementations of LLM models:

- **TestModel**: A predictable model for testing that returns predefined responses
- **FunctionModel**: A model that focuses on testing function calling
- **FailingModel**: A model that simulates failures for error handling tests
- **DelayedModel**: A model that simulates response latency

### Test Fixtures

The `fixtures.py` file provides pytest fixtures for testing:

- **Agent Fixtures**: Pre-configured agents for testing
- **Workflow Fixtures**: Sample workflows for testing
- **Knowledge Fixtures**: Test data for the knowledge base
- **Config Fixtures**: Test configurations for various components
- **Mock Components**: Mock implementations of external dependencies

### Test Assertions

The `assertions.py` file provides custom assertions for testing:

- **Agent Assertions**: Validate agent behaviors and outputs
- **Workflow Assertions**: Verify workflow execution paths
- **Response Assertions**: Check response structure and content
- **Performance Assertions**: Verify performance characteristics

## Testing Approaches

### Agent Testing

Methods for testing agents:

- **Response Testing**: Verify agent responses to inputs
- **Tool Usage Testing**: Validate correct tool selection and usage
- **Error Handling**: Test agent behavior with invalid inputs
- **Capability Testing**: Verify agent capabilities work as expected

### Workflow Testing

Methods for testing workflows:

- **Path Testing**: Verify workflow execution paths
- **Agent Interaction Testing**: Test how agents interact in workflows
- **State Management**: Validate workflow state transitions
- **Error Propagation**: Test error handling in workflows

### Knowledge Base Testing

Methods for testing the knowledge base:

- **Storage Testing**: Verify correct storage and retrieval
- **Search Testing**: Validate search functionality
- **Embedding Testing**: Test embedding generation and similarity
- **Performance Testing**: Measure knowledge base performance

## Usage Examples

### Testing an Agent

```python
from agentical.testing import TestModel, assert_agent_response

# Create an agent with a test model
agent = create_agent(
    name="Test Agent",
    model=TestModel([
        {"role": "assistant", "content": "This is a test response"}
    ])
)

# Test the agent
async def test_agent_response():
    result = await agent.run("Test input")
    
    # Assert the response is as expected
    assert_agent_response(result, expected="This is a test response")
```

### Testing a Workflow

```python
from agentical.testing import workflow_fixture, assert_workflow_path

# Use a workflow fixture
@pytest.fixture
def test_workflow():
    return workflow_fixture("feedback_loop")

# Test the workflow
async def test_workflow_execution(test_workflow):
    result = await test_workflow.run({"input": "Test input"})
    
    # Assert the workflow followed the expected path
    assert_workflow_path(result, ["agent1", "agent2", "agent1", "complete"])
```

## Mocking External Services

The testing module provides utilities for mocking external services:

- **MockHTTPClient**: Mock HTTP responses for testing
- **MockEmbeddingService**: Simulate embedding generation
- **MockSurrealDBClient**: In-memory database for testing
- **MockWebSocket**: Test WebSocket interactions

## Testing Tools

The testing module integrates with standard Python testing tools:

- **pytest**: Primary testing framework
- **pytest-asyncio**: Support for testing async code
- **pytest-cov**: Code coverage reporting
- **dirty-equals**: Flexible assertions for complex objects
- **inline-snapshots**: Snapshot testing for responses

## Test Data Management

Approaches for managing test data:

- **Fixtures**: Predefined test data
- **Factories**: Generate test data dynamically
- **Snapshot Testing**: Compare against saved responses
- **Golden Files**: Compare against reference files

## Best Practices

1. Write tests for all core components
2. Use test models instead of real LLMs in unit tests
3. Test edge cases and error conditions
4. Use fixtures to avoid repetition
5. Mock external dependencies for isolation
6. Test asynchronous code properly
7. Use meaningful assertions for clear failures
8. Maintain test independence

## Related Components

- **Agents**: Primary subjects for testing
- **Workflows**: Complex components requiring thorough testing
- **Evaluation**: More comprehensive system evaluation