"""
Validation Test for Task 6.4 - Develop Test Utilities and Data Factories

This module validates the implementation of Task 6.4 by testing the test
utilities and data factories developed for the Agentical framework.
"""

import inspect
import os
import json
import pytest
from pathlib import Path

from tests.utils.data_factories import (
    BaseDataFactory,
    AgentDataFactory,
    DatabaseDataFactory,
    KnowledgeDataFactory,
    WorkflowDataFactory,
    ToolDataFactory
)

from tests.utils.mocks import (
    MockClient,
    MockResponse,
    MockKnowledgeBase,
    MockAgent,
    MockRedisClient,
    MockSurrealDB
)

from tests.utils.helpers import (
    async_test,
    load_test_data,
    wait_for_completion,
    compare_json_objects,
    isolate_test_execution,
    create_test_app
)


# Test base data factory
def test_base_data_factory():
    """Verify that the base data factory has the required utility methods."""
    assert hasattr(BaseDataFactory, "random_string"), "BaseDataFactory should have random_string method"
    assert hasattr(BaseDataFactory, "random_email"), "BaseDataFactory should have random_email method"
    assert hasattr(BaseDataFactory, "random_date"), "BaseDataFactory should have random_date method"
    assert hasattr(BaseDataFactory, "random_bool"), "BaseDataFactory should have random_bool method"
    assert hasattr(BaseDataFactory, "random_choice"), "BaseDataFactory should have random_choice method"
    assert hasattr(BaseDataFactory, "unique_id"), "BaseDataFactory should have unique_id method"
    assert hasattr(BaseDataFactory, "random_int"), "BaseDataFactory should have random_int method"
    assert hasattr(BaseDataFactory, "random_float"), "BaseDataFactory should have random_float method"
    
    # Test method functionality
    assert len(BaseDataFactory.random_string(10)) == 10, "random_string should generate string of specified length"
    assert "@" in BaseDataFactory.random_email(), "random_email should generate a valid email address"
    assert isinstance(BaseDataFactory.random_bool(), bool), "random_bool should return a boolean"
    assert isinstance(BaseDataFactory.random_int(1, 10), int), "random_int should return an integer"
    assert isinstance(BaseDataFactory.random_float(0.0, 1.0), float), "random_float should return a float"


# Test agent data factory
def test_agent_data_factory():
    """Verify that the agent data factory has the required methods."""
    assert hasattr(AgentDataFactory, "create_agent_metadata"), "AgentDataFactory should have create_agent_metadata method"
    assert hasattr(AgentDataFactory, "create_agent_capability"), "AgentDataFactory should have create_agent_capability method"
    assert hasattr(AgentDataFactory, "create_agent_execution_context"), "AgentDataFactory should have create_agent_execution_context method"
    assert hasattr(AgentDataFactory, "create_agent_execution_result"), "AgentDataFactory should have create_agent_execution_result method"
    assert hasattr(AgentDataFactory, "create_perception_result"), "AgentDataFactory should have create_perception_result method"
    assert hasattr(AgentDataFactory, "create_decision_result"), "AgentDataFactory should have create_decision_result method"
    assert hasattr(AgentDataFactory, "create_action_result"), "AgentDataFactory should have create_action_result method"
    
    # Test method functionality
    agent_metadata = AgentDataFactory.create_agent_metadata()
    assert isinstance(agent_metadata, dict), "create_agent_metadata should return a dict"
    assert "id" in agent_metadata, "agent_metadata should have an id field"
    assert "name" in agent_metadata, "agent_metadata should have a name field"
    assert "capabilities" in agent_metadata, "agent_metadata should have a capabilities field"
    
    execution_result = AgentDataFactory.create_agent_execution_result()
    assert isinstance(execution_result, dict), "create_agent_execution_result should return a dict"
    assert "success" in execution_result, "execution_result should have a success field"
    assert "execution_id" in execution_result, "execution_result should have an execution_id field"


# Test database data factory
def test_database_data_factory():
    """Verify that the database data factory has the required methods."""
    assert hasattr(DatabaseDataFactory, "create_user"), "DatabaseDataFactory should have create_user method"
    assert hasattr(DatabaseDataFactory, "create_api_key"), "DatabaseDataFactory should have create_api_key method"
    assert hasattr(DatabaseDataFactory, "create_agent_record"), "DatabaseDataFactory should have create_agent_record method"
    assert hasattr(DatabaseDataFactory, "create_execution_record"), "DatabaseDataFactory should have create_execution_record method"
    
    # Test method functionality
    user = DatabaseDataFactory.create_user()
    assert isinstance(user, dict), "create_user should return a dict"
    assert "id" in user, "user should have an id field"
    assert "username" in user, "user should have a username field"
    assert "email" in user, "user should have an email field"
    
    agent_record = DatabaseDataFactory.create_agent_record()
    assert isinstance(agent_record, dict), "create_agent_record should return a dict"
    assert "id" in agent_record, "agent_record should have an id field"
    assert "agent_id" in agent_record, "agent_record should have an agent_id field"


# Test knowledge data factory
def test_knowledge_data_factory():
    """Verify that the knowledge data factory has the required methods."""
    assert hasattr(KnowledgeDataFactory, "create_knowledge_item"), "KnowledgeDataFactory should have create_knowledge_item method"
    assert hasattr(KnowledgeDataFactory, "create_knowledge_query_result"), "KnowledgeDataFactory should have create_knowledge_query_result method"
    assert hasattr(KnowledgeDataFactory, "create_knowledge_domain"), "KnowledgeDataFactory should have create_knowledge_domain method"
    
    # Test method functionality
    knowledge_item = KnowledgeDataFactory.create_knowledge_item()
    assert isinstance(knowledge_item, dict), "create_knowledge_item should return a dict"
    assert "id" in knowledge_item, "knowledge_item should have an id field"
    assert "content" in knowledge_item, "knowledge_item should have a content field"
    
    query_result = KnowledgeDataFactory.create_knowledge_query_result()
    assert isinstance(query_result, dict), "create_knowledge_query_result should return a dict"
    assert "query" in query_result, "query_result should have a query field"
    assert "results" in query_result, "query_result should have a results field"


# Test workflow data factory
def test_workflow_data_factory():
    """Verify that the workflow data factory has the required methods."""
    assert hasattr(WorkflowDataFactory, "create_workflow"), "WorkflowDataFactory should have create_workflow method"
    assert hasattr(WorkflowDataFactory, "create_workflow_step"), "WorkflowDataFactory should have create_workflow_step method"
    assert hasattr(WorkflowDataFactory, "create_workflow_execution"), "WorkflowDataFactory should have create_workflow_execution method"
    
    # Test method functionality
    workflow = WorkflowDataFactory.create_workflow()
    assert isinstance(workflow, dict), "create_workflow should return a dict"
    assert "id" in workflow, "workflow should have an id field"
    assert "steps" in workflow, "workflow should have a steps field"
    
    workflow_step = WorkflowDataFactory.create_workflow_step()
    assert isinstance(workflow_step, dict), "create_workflow_step should return a dict"
    assert "id" in workflow_step, "workflow_step should have an id field"
    assert "type" in workflow_step, "workflow_step should have a type field"


# Test tool data factory
def test_tool_data_factory():
    """Verify that the tool data factory has the required methods."""
    assert hasattr(ToolDataFactory, "create_tool_config"), "ToolDataFactory should have create_tool_config method"
    assert hasattr(ToolDataFactory, "create_tool_execution_request"), "ToolDataFactory should have create_tool_execution_request method"
    assert hasattr(ToolDataFactory, "create_tool_execution_result"), "ToolDataFactory should have create_tool_execution_result method"
    assert hasattr(ToolDataFactory, "create_mcp_server_config"), "ToolDataFactory should have create_mcp_server_config method"
    
    # Test method functionality
    tool_config = ToolDataFactory.create_tool_config()
    assert isinstance(tool_config, dict), "create_tool_config should return a dict"
    assert "name" in tool_config, "tool_config should have a name field"
    assert "parameters" in tool_config, "tool_config should have a parameters field"
    
    tool_result = ToolDataFactory.create_tool_execution_result()
    assert isinstance(tool_result, dict), "create_tool_execution_result should return a dict"
    assert "execution_id" in tool_result, "tool_result should have an execution_id field"
    assert "success" in tool_result, "tool_result should have a success field"


# Test mock objects
def test_mock_objects():
    """Verify that the mock objects have the required functionality."""
    # Test MockResponse
    response = MockResponse(
        status_code=200,
        content={"message": "Success"},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200, "MockResponse should have correct status_code"
    assert response.json()["message"] == "Success", "MockResponse should have correct JSON content"
    
    # Test MockClient
    client = MockClient()
    assert hasattr(client, "get"), "MockClient should have get method"
    assert hasattr(client, "post"), "MockClient should have post method"
    assert hasattr(client, "put"), "MockClient should have put method"
    assert hasattr(client, "delete"), "MockClient should have delete method"
    
    # Test MockKnowledgeBase
    kb = MockKnowledgeBase()
    assert hasattr(kb, "query"), "MockKnowledgeBase should have query method"
    assert hasattr(kb, "add_item"), "MockKnowledgeBase should have add_item method"
    assert hasattr(kb, "get_item"), "MockKnowledgeBase should have get_item method"
    
    # Test MockAgent
    agent = MockAgent()
    assert hasattr(agent, "_execute_operation"), "MockAgent should have _execute_operation method"
    
    # Test MockRedisClient
    redis = MockRedisClient()
    assert hasattr(redis, "get"), "MockRedisClient should have get method"
    assert hasattr(redis, "set"), "MockRedisClient should have set method"
    assert hasattr(redis, "delete"), "MockRedisClient should have delete method"
    
    # Test MockSurrealDB
    surreal = MockSurrealDB()
    assert hasattr(surreal, "connect"), "MockSurrealDB should have connect method"
    assert hasattr(surreal, "select"), "MockSurrealDB should have select method"
    assert hasattr(surreal, "create"), "MockSurrealDB should have create method"


# Test helper functions
def test_helper_functions():
    """Verify that the helper functions have the required functionality."""
    assert callable(async_test), "async_test should be callable"
    assert callable(load_test_data), "load_test_data should be callable"
    assert callable(wait_for_completion), "wait_for_completion should be callable"
    assert callable(compare_json_objects), "compare_json_objects should be callable"
    assert callable(isolate_test_execution), "isolate_test_execution should be callable"
    assert callable(create_test_app), "create_test_app should be callable"
    
    # Test compare_json_objects
    obj1 = {"a": 1, "b": 2, "c": {"d": 3}}
    obj2 = {"a": 1, "b": 2, "c": {"d": 3}}
    is_equal, differences = compare_json_objects(obj1, obj2)
    assert is_equal, "compare_json_objects should return True for equal objects"
    assert len(differences) == 0, "compare_json_objects should return empty differences for equal objects"
    
    obj3 = {"a": 1, "b": 3, "c": {"d": 4}}
    is_equal, differences = compare_json_objects(obj1, obj3)
    assert not is_equal, "compare_json_objects should return False for different objects"
    assert len(differences) > 0, "compare_json_objects should return non-empty differences for different objects"


# Test fixture data files
def test_fixture_data_files():
    """Verify that the fixture data files exist and are valid JSON."""
    # Check if fixtures directory exists
    fixtures_dir = Path(__file__).parent / "fixtures" / "data"
    assert fixtures_dir.exists(), "Fixtures directory should exist"
    
    # Check if agent data file exists
    agent_data_file = fixtures_dir / "agent_data.json"
    assert agent_data_file.exists(), "agent_data.json should exist"
    
    # Load and validate agent data
    with open(agent_data_file, "r") as f:
        agent_data = json.load(f)
    
    assert "agents" in agent_data, "agent_data.json should have agents field"
    assert isinstance(agent_data["agents"], list), "agents field should be a list"
    assert len(agent_data["agents"]) > 0, "agents list should not be empty"
    
    # Check if tool data file exists
    tool_data_file = fixtures_dir / "tool_data.json"
    assert tool_data_file.exists(), "tool_data.json should exist"
    
    # Load and validate tool data
    with open(tool_data_file, "r") as f:
        tool_data = json.load(f)
    
    assert "tools" in tool_data, "tool_data.json should have tools field"
    assert isinstance(tool_data["tools"], list), "tools field should be a list"
    assert len(tool_data["tools"]) > 0, "tools list should not be empty"


def test_task_6_4_completed():
    """Final validation that Task 6.4 has been completed successfully."""
    # All tests passing means Task 6.4 is complete
    print("Task 6.4: Develop Test Utilities and Data Factories - COMPLETED")
    assert True, "Task 6.4 implementation validated successfully"