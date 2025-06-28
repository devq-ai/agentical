# Agentical Testing Framework Documentation

## Overview

The Agentical testing framework provides comprehensive testing infrastructure for the multi-agent system, including unit tests, integration tests, performance tests, and security tests. Built on PyTest with extensive utilities for database testing, API testing, and performance monitoring.

## Framework Architecture

### Core Components

1. **Global Configuration** (`conftest.py`)
   - Database session management
   - Authentication fixtures
   - Test data factories
   - Mock service configurations

2. **Testing Utilities** (`tests/utils/`)
   - Test builders for data creation
   - API testing helpers
   - Database testing utilities
   - Mock generators
   - Custom assertions
   - Performance testing tools

3. **Test Categories**
   - Unit tests for individual components
   - Integration tests for component interactions
   - API tests for endpoint validation
   - Performance tests for optimization
   - Security tests for vulnerability assessment

## Quick Start

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests only
pytest -m api                     # API tests only
pytest -m performance             # Performance tests only
pytest -m security                # Security tests only

# Run tests with coverage
pytest --cov=agentical --cov-report=html

# Run tests in parallel
pytest -n auto                    # Automatic CPU detection
pytest -n 4                       # 4 parallel workers
```

### Test Markers

Use markers to categorize and filter tests:

```python
@pytest.mark.unit
def test_user_creation():
    """Unit test for user creation."""
    pass

@pytest.mark.integration
def test_agent_workflow_integration():
    """Integration test for agent-workflow interaction."""
    pass

@pytest.mark.api
def test_login_endpoint():
    """API test for login endpoint."""
    pass

@pytest.mark.performance
def test_database_query_performance():
    """Performance test for database queries."""
    pass

@pytest.mark.security
def test_authentication_security():
    """Security test for authentication system."""
    pass
```

## Testing Utilities Guide

### 1. Database Testing

#### Database Session Management

```python
def test_user_creation(db_session):
    """Test using database session."""
    user = User(username="test", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None

def test_with_sample_data(db_with_data):
    """Test using pre-populated database."""
    users = db_with_data.query(User).all()
    assert len(users) >= 2  # admin and regular user
```

#### Database Helper Utilities

```python
def test_database_operations(db_session):
    """Test using database helper utilities."""
    from tests.utils.db_helpers import DatabaseTestHelper
    
    db_helper = DatabaseTestHelper(db_session)
    
    # Create test data
    user = db_helper.create_user("testuser", "test@example.com")
    agent = db_helper.create_agent("test_agent", AgentType.CODE_AGENT)
    
    # Validate data
    assert db_helper.count_records(User) == 1
    assert db_helper.find_by_id(User, user.id) == user
    
    # Clean up automatically handled by fixture
```

#### Data Factories and Builders

```python
def test_user_builder():
    """Test using user builder pattern."""
    from tests.utils.test_builders import UserBuilder
    
    user = (UserBuilder()
            .username("john_doe")
            .email("john@example.com")
            .name("John", "Doe")
            .admin(True)
            .verified(True)
            .build())
    
    assert user.username == "john_doe"
    assert user.is_admin == True
    assert user.is_verified == True

def test_agent_builder():
    """Test using agent builder pattern."""
    from tests.utils.test_builders import AgentBuilder
    
    agent = (AgentBuilder()
             .name("code_assistant")
             .agent_type(AgentType.CODE_AGENT)
             .status(AgentStatus.ACTIVE)
             .add_capability("code_generation")
             .add_tool("git")
             .build())
    
    assert agent.name == "code_assistant"
    assert "code_generation" in agent.configuration["capabilities"]
```

### 2. API Testing

#### API Test Helper

```python
def test_api_endpoints(client):
    """Test using API helper utilities."""
    from tests.utils.api_helpers import APITestHelper
    
    api = APITestHelper(client)
    
    # Set authentication
    api.set_auth_token("valid_jwt_token")
    
    # Make requests
    response = api.get("/agents")
    assert response.status_code == 200
    
    response = api.post("/agents", data={
        "name": "test_agent",
        "agent_type": "code"
    })
    assert response.status_code == 201
```

#### Request Builder Pattern

```python
def test_request_builder(client):
    """Test using request builder pattern."""
    from tests.utils.api_helpers import post_request, validate_response
    
    response = (post_request("/auth/login")
                .field("username", "testuser")
                .field("password", "password123")
                .header("Content-Type", "application/json")
                .execute(client))
    
    # Validate response
    data = validate_response(response, 200)
    assert data["access_token"] is not None
```

#### Response Validation

```python
def test_response_validation(client):
    """Test using response validation utilities."""
    from tests.utils.api_helpers import ResponseValidator
    
    response = client.get("/api/v1/agents")
    
    (ResponseValidator(response)
     .success()
     .is_list()
     .list_not_empty()
     .has_field("pagination")
     .pagination_fields())
```

### 3. Authentication Testing

#### Authentication Helper

```python
def test_authentication():
    """Test using authentication helper."""
    from tests.utils.api_helpers import AuthenticationHelper
    
    auth = AuthenticationHelper()
    
    # Create tokens
    admin_token = auth.create_admin_token()
    user_token = auth.create_user_token()
    expired_token = auth.create_expired_token()
    
    # Extract payload
    payload = auth.extract_payload(user_token)
    assert payload["username"] == "testuser"
```

#### Security Context Testing

```python
def test_security_context(security_context_admin):
    """Test using security context fixtures."""
    from agentical.core.security import Permission
    
    # Test permissions
    assert security_context_admin.has_permission(Permission.ADMIN_USERS)
    assert security_context_admin.is_admin()
    assert not security_context_admin.is_super_admin()
```

### 4. Mock Testing

#### External Service Mocking

```python
def test_external_services():
    """Test using external service mocks."""
    from tests.utils.mock_generators import ExternalServiceMocker
    
    mocker = ExternalServiceMocker()
    
    with mocker.mock_anthropic_api():
        # Test code that calls Anthropic API
        result = call_ai_service("test prompt")
        assert result["content"] is not None
    
    # Check call counts
    assert mocker.get_call_count("anthropic") == 1
```

#### MCP Server Mocking

```python
def test_mcp_servers():
    """Test using MCP server mocks."""
    from tests.utils.mock_generators import MCPServerMocker
    
    mcp_mocker = MCPServerMocker()
    
    # Mock health check
    health = mcp_mocker.mock_server_health_check("taskmaster-ai")
    assert health["status"] == "healthy"
    
    # Mock task management
    responses = mcp_mocker.mock_task_management_responses()
    tasks = responses["get_tasks"]["tasks"]
    assert len(tasks) >= 2
```

### 5. Performance Testing

#### Performance Measurement

```python
def test_function_performance():
    """Test function performance measurement."""
    from tests.utils.performance import PerformanceTestHelper
    
    helper = PerformanceTestHelper()
    
    def expensive_operation():
        return sum(i * i for i in range(10000))
    
    metrics = helper.measure_function_performance(
        expensive_operation,
        iterations=100,
        warmup_iterations=10
    )
    
    assert metrics.operations_per_second > 100
    assert metrics.execution_time < 0.1
    assert metrics.success_rate == 100.0
```

#### Load Testing

```python
def test_load_testing(client):
    """Test load testing capabilities."""
    from tests.utils.performance import LoadTestRunner
    
    runner = LoadTestRunner(client)
    
    def api_call():
        response = client.get("/health")
        assert response.status_code == 200
    
    results = runner.run_load_test(
        test_function=api_call,
        concurrent_users=10,
        duration_seconds=30
    )
    
    assert results["success_rate"] > 95.0
    assert results["avg_response_time"] < 1.0
```

#### Benchmarking

```python
def test_benchmarking():
    """Test benchmarking capabilities."""
    from tests.utils.performance import BenchmarkSuite
    
    suite = BenchmarkSuite()
    
    # Register benchmarks
    suite.register_benchmark("database_query", lambda: query_users())
    suite.register_benchmark("api_call", lambda: call_api_endpoint())
    
    # Run benchmarks
    results = suite.run_all_benchmarks(iterations=100)
    
    # Set baseline for regression testing
    suite.set_baseline(results)
    
    # Compare future runs
    new_results = suite.run_all_benchmarks(iterations=100)
    comparisons = suite.compare_to_baseline(new_results, tolerance_percent=10.0)
    
    for name, comparison in comparisons.items():
        assert comparison["status"] != "failed", f"Performance regression in {name}"
```

### 6. Custom Assertions

#### Data Validation

```python
def test_custom_assertions():
    """Test using custom assertion utilities."""
    from tests.utils.assertions import DataValidators, CustomAssertions
    
    # Validate user data
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }
    DataValidators.validate_user_data(user_data)
    
    # Validate UUID format
    uuid_value = "550e8400-e29b-41d4-a716-446655440000"
    CustomAssertions.assert_uuid_format(uuid_value)
    
    # Validate response structure
    response = {"id": 1, "name": "test", "active": True}
    CustomAssertions.assert_response_structure(response, {
        "id": int,
        "name": str,
        "active": bool
    })
```

#### Business Logic Assertions

```python
def test_business_logic_assertions():
    """Test business logic specific assertions."""
    from tests.utils.assertions import BusinessLogicAssertions
    
    # Test agent capabilities
    agent = create_test_agent()
    BusinessLogicAssertions.assert_agent_can_execute_task(agent, "code_generation")
    
    # Test user permissions
    user = create_test_user()
    BusinessLogicAssertions.assert_user_permissions_valid(user, ["user:read"])
    
    # Test execution validity
    execution = create_test_execution()
    BusinessLogicAssertions.assert_playbook_execution_valid(execution)
```

### 7. Security Testing

#### Security Assertions

```python
def test_security_assertions():
    """Test security-specific assertions."""
    from tests.utils.assertions import SecurityAssertions
    
    # Test password strength
    SecurityAssertions.assert_password_strength("StrongPass123!")
    
    # Test JWT format
    jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.hash"
    SecurityAssertions.assert_jwt_token_format(jwt_token)
    
    # Test response doesn't contain sensitive data
    response_data = {"username": "test", "email": "test@example.com"}
    SecurityAssertions.assert_no_sensitive_data_in_response(response_data)
    
    # Test SQL injection safety
    query = "SELECT * FROM users WHERE name = ?"
    SecurityAssertions.assert_sql_injection_safe(query)
```

## Test Organization

### Directory Structure

```
tests/
├── conftest.py                 # Global fixtures and configuration
├── utils/                      # Testing utilities
│   ├── __init__.py
│   ├── test_builders.py        # Data builders and factories
│   ├── api_helpers.py          # API testing utilities
│   ├── db_helpers.py           # Database testing utilities
│   ├── mock_generators.py     # Mock response generators
│   ├── assertions.py           # Custom assertion utilities
│   ├── performance.py          # Performance testing tools
│   └── constants.py            # Test constants and sample data
├── unit/                       # Unit tests
│   ├── test_models.py          # Database model tests
│   ├── test_services.py        # Service layer tests
│   └── test_utilities.py       # Utility function tests
├── integration/                # Integration tests
│   ├── test_agent_workflow.py  # Agent-workflow integration
│   ├── test_database_ops.py    # Database operation tests
│   └── test_external_apis.py   # External API integration
├── api/                        # API endpoint tests
│   ├── test_auth.py            # Authentication endpoints
│   ├── test_agents.py          # Agent management endpoints
│   ├── test_playbooks.py       # Playbook management endpoints
│   └── test_workflows.py       # Workflow management endpoints
├── performance/                # Performance tests
│   ├── test_load.py            # Load testing scenarios
│   ├── test_benchmarks.py      # Performance benchmarks
│   └── test_stress.py          # Stress testing scenarios
└── security/                   # Security tests
    ├── test_authentication.py  # Authentication security
    ├── test_authorization.py   # Authorization security
    └── test_input_validation.py # Input validation security
```

### Test Naming Conventions

- **Test files**: `test_*.py`
- **Test classes**: `Test*` (e.g., `TestUserAPI`)
- **Test functions**: `test_*` (e.g., `test_user_creation`)
- **Fixture files**: `conftest.py`

### Test Documentation

Each test should include:

```python
def test_user_registration():
    """
    Test user registration endpoint.
    
    Scenarios:
    - Valid registration data should create user
    - Duplicate username should return 409
    - Invalid email should return 422
    - Weak password should return 422
    """
    pass
```

## Configuration

### PyTest Configuration (`pytest.ini`)

```ini
[pytest]
minversion = 6.0
addopts = 
    -ra
    --strict-markers
    --strict-config
    --cov=agentical
    --cov-report=term-missing
    --cov-report=html:reports/coverage
    --cov-fail-under=90
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    performance: Performance tests
    security: Security tests
    slow: Slow running tests
```

### Environment Variables

Set up test environment variables in `.env.test`:

```bash
# Test Database
DATABASE_URL=sqlite:///:memory:
TEST_DATABASE_ECHO=false

# Authentication
JWT_SECRET=test_secret_key_for_testing_only
JWT_ALGORITHM=HS256

# External Services
MOCK_EXTERNAL_APIS=true
ANTHROPIC_API_KEY=test_key
OPENAI_API_KEY=test_key

# Logging
LOG_LEVEL=DEBUG
TESTING=true
```

## Best Practices

### 1. Test Independence

- Each test should be independent and not rely on other tests
- Use fixtures for setup and teardown
- Clean up resources after each test

```python
def test_independent_operation(db_session):
    """Each test is independent."""
    # Setup
    user = create_test_user()
    
    # Test
    result = perform_operation(user)
    
    # Assert
    assert result.success
    
    # Cleanup handled by fixture
```

### 2. Test Data Management

- Use factories and builders for test data creation
- Keep test data minimal and focused
- Use realistic but safe test data

```python
def test_with_factory_data():
    """Use factories for clean test data."""
    user = UserFactory.create_user(
        username="testuser",
        email="test@example.com",
        is_verified=True
    )
    
    assert user.username == "testuser"
```

### 3. Mocking External Dependencies

- Mock external APIs and services
- Use dependency injection for testability
- Verify mock interactions when relevant

```python
@patch('external_service.call_api')
def test_external_service_integration(mock_api):
    """Mock external dependencies."""
    mock_api.return_value = {"status": "success"}
    
    result = service_that_calls_api()
    
    assert result.success
    mock_api.assert_called_once()
```

### 4. Performance Testing

- Include performance tests for critical paths
- Set realistic performance thresholds
- Monitor performance trends over time

```python
@pytest.mark.performance
def test_database_query_performance():
    """Ensure queries perform within acceptable limits."""
    with performance_monitoring():
        results = expensive_database_query()
    
    assert len(results) > 0
    # Performance assertions handled by monitoring context
```

### 5. Security Testing

- Test authentication and authorization
- Validate input sanitization
- Check for common vulnerabilities

```python
@pytest.mark.security
def test_sql_injection_protection():
    """Ensure SQL injection protection."""
    malicious_input = "'; DROP TABLE users; --"
    
    with pytest.raises(ValidationError):
        unsafe_query_function(malicious_input)
```

## Continuous Integration

### GitHub Actions Configuration

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e .[dev]
    
    - name: Run tests
      run: |
        pytest --cov=agentical --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Coverage Requirements

- **Minimum Coverage**: 90% line coverage
- **Branch Coverage**: 85% minimum
- **Critical Paths**: 100% coverage required

### Quality Gates

Tests must pass these quality gates:

1. **All tests passing**: Zero test failures
2. **Coverage threshold**: Minimum 90% line coverage
3. **Performance benchmarks**: No significant regressions
4. **Security scans**: Zero high/critical vulnerabilities
5. **Code quality**: Linting and formatting checks

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure test database is properly configured
   - Check database session fixtures
   - Verify test isolation

2. **Authentication Failures**
   - Check JWT secret configuration
   - Verify token generation and validation
   - Ensure proper test user setup

3. **Mock Configuration Issues**
   - Verify mock setup and teardown
   - Check mock return values
   - Ensure proper patch locations

4. **Performance Test Fluctuations**
   - Run tests multiple times for stability
   - Consider system load factors
   - Adjust thresholds for CI environments

### Debug Mode

Run tests in debug mode for troubleshooting:

```bash
# Verbose output
pytest -v

# Debug output
pytest -s --log-cli-level=DEBUG

# Stop on first failure
pytest -x

# Run specific test
pytest tests/unit/test_models.py::test_user_creation -v
```

## Contributing

### Adding New Tests

1. Choose appropriate test category (unit/integration/api/performance/security)
2. Use existing utilities and fixtures
3. Follow naming conventions
4. Include comprehensive documentation
5. Ensure tests are independent and isolated

### Extending Testing Utilities

1. Add new utilities to appropriate module in `tests/utils/`
2. Include comprehensive docstrings
3. Add corresponding fixtures if needed
4. Update this documentation

### Performance Testing Guidelines

1. Set realistic thresholds based on requirements
2. Include both load and stress testing scenarios
3. Monitor trends over time
4. Consider environment factors in CI

---

## Summary

The Agentical testing framework provides comprehensive testing capabilities covering:

- **Unit Testing**: Individual component validation
- **Integration Testing**: Component interaction verification
- **API Testing**: Endpoint functionality and security
- **Performance Testing**: Load, stress, and benchmark testing
- **Security Testing**: Authentication, authorization, and vulnerability testing

With extensive utilities for data generation, mocking, assertions, and performance monitoring, the framework enables thorough testing of the multi-agent system while maintaining high code quality and reliability standards.

For questions or issues with the testing framework, refer to the project documentation or contact the development team.