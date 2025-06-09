# Tests in Agentical Framework

## Overview

The `tests` directory contains comprehensive test suites for the Agentical framework. These tests ensure the reliability, correctness, and quality of the framework's components through a combination of unit tests, integration tests, and end-to-end tests. A robust testing strategy is essential for maintaining confidence in the framework's behavior and preventing regressions.

## Directory Structure

```
tests/
├── __init__.py             # Package initialization
├── unit/                   # Unit tests
│   ├── __init__.py
│   ├── test_agents/        # Tests for agents
│   ├── test_workflows/     # Tests for workflows
│   ├── test_tools/         # Tests for tools
│   ├── test_playbooks/     # Tests for playbooks
│   ├── test_knowledge/     # Tests for knowledge base
│   └── test_api/           # Tests for API
├── integration/            # Integration tests
│   ├── __init__.py
│   └── ...
└── fixtures/               # Test fixtures
    ├── __init__.py
    ├── knowledge/          # Knowledge base fixtures
    └── ...
```

## Core Components

### Unit Tests

The `unit/` directory contains tests for individual components:

- **Agent Tests**: Verify agent behavior, tool usage, and capability implementation
- **Workflow Tests**: Ensure workflow patterns function as expected
- **Tool Tests**: Validate tool functionality and error handling
- **Playbook Tests**: Test playbook configuration and execution
- **Knowledge Base Tests**: Verify knowledge storage, retrieval, and searching
- **API Tests**: Test API endpoints and request handling

### Integration Tests

The `integration/` directory contains tests that verify component interactions:

- **Agent-Workflow Integration**: Test agent interactions within workflows
- **API-Backend Integration**: Verify API integration with core components
- **Tool Chain Tests**: Validate sequences of tool operations
- **Knowledge-Agent Integration**: Test agent use of knowledge base

### Test Fixtures

The `fixtures/` directory provides reusable test data and setup:

- **Mock Data**: Sample data for testing
- **Test Configurations**: Predefined configurations for testing
- **Mock Responses**: Predefined responses for external services
- **Environment Setup**: Utilities for setting up test environments

## Testing Approaches

### Test-Driven Development

The framework encourages test-driven development (TDD):

1. Write tests first to define expected behavior
2. Implement features to satisfy tests
3. Refactor while maintaining passing tests

### Mocking and Stubbing

The tests use several mocking approaches:

- **LLM Mocking**: Replacing real LLM calls with predictable responses
- **External Service Mocking**: Simulating external API behavior
- **Database Mocking**: In-memory database for testing
- **Time Mocking**: Controlling time-dependent operations

### Parameterized Testing

Parameterized tests to cover multiple scenarios:

- **Input Variations**: Testing with different inputs
- **Configuration Variations**: Testing with different settings
- **Error Conditions**: Testing various error scenarios
- **Edge Cases**: Testing boundary conditions

## Testing Tools

The testing infrastructure leverages several tools:

- **pytest**: Primary testing framework
- **pytest-asyncio**: Testing async code
- **pytest-cov**: Code coverage reporting
- **pytest-mock**: Mocking utilities
- **async-timeout**: Handling async timeouts
- **dirty-equals**: Flexible assertions for complex objects

## Running Tests

Tests can be run at different levels:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run specific test module
pytest tests/unit/test_agents/test_capabilities.py

# Run with coverage reporting
pytest --cov=agentical

# Run tests matching a pattern
pytest -k "agent and capability"
```

## Continuous Integration

Tests are integrated into the CI/CD pipeline:

- **Pre-commit Checks**: Basic tests run before commit
- **Pull Request Validation**: Complete test suite runs on PRs
- **Scheduled Tests**: Regular testing of the main branch
- **Performance Tests**: Scheduled performance benchmark tests

## Best Practices

1. Write tests for all new features and bug fixes
2. Maintain high test coverage for critical components
3. Use appropriate mocking to isolate components
4. Structure tests clearly with setup, execution, and assertion phases
5. Test both success and failure scenarios
6. Keep tests fast to encourage frequent running
7. Use fixtures to reduce test setup duplication
8. Document test requirements and assumptions

## Related Components

- **Agents**: Tested for behavior and capability implementation
- **Workflows**: Verified for correct execution and state management
- **Tools**: Validated for functionality and error handling
- **API**: Tested for correct request handling and responses