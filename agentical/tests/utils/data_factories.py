"""
Data Factories for Agentical Tests

This module provides factory classes for generating test data for various
components of the Agentical framework. These factories help create consistent,
customizable test data for unit and integration tests.
"""

import uuid
import random
import string
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from agentical.agents import (
    AgentMetadata,
    AgentCapability,
    AgentStatus,
    AgentExecutionContext,
    AgentExecutionResult
)


class BaseDataFactory:
    """Base class for all data factories with common utilities."""
    
    @staticmethod
    def random_string(length: int = 8) -> str:
        """Generate a random string of specified length."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_email() -> str:
        """Generate a random email address."""
        domains = ["example.com", "test.org", "agentical.ai", "devq.ai"]
        username = BaseDataFactory.random_string(8).lower()
        domain = random.choice(domains)
        return f"{username}@{domain}"
    
    @staticmethod
    def random_date(start_date: Optional[datetime] = None, days_range: int = 30) -> datetime:
        """Generate a random date within a range."""
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=days_range)
        
        random_days = random.randint(0, days_range)
        return start_date + timedelta(days=random_days)
    
    @staticmethod
    def random_bool(true_probability: float = 0.5) -> bool:
        """Generate a random boolean with a specified probability of being True."""
        return random.random() < true_probability
    
    @staticmethod
    def random_choice(choices: List[Any]) -> Any:
        """Choose a random element from a list."""
        return random.choice(choices)
    
    @staticmethod
    def unique_id() -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())
    
    @staticmethod
    def random_int(min_val: int = 0, max_val: int = 100) -> int:
        """Generate a random integer within a range."""
        return random.randint(min_val, max_val)
    
    @staticmethod
    def random_float(min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Generate a random float within a range."""
        return random.uniform(min_val, max_val)


class AgentDataFactory(BaseDataFactory):
    """Factory for generating agent-related test data."""
    
    @classmethod
    def create_agent_metadata(cls, **kwargs) -> Dict[str, Any]:
        """Create test agent metadata."""
        capabilities = kwargs.pop("capabilities", None)
        if capabilities is None:
            capabilities = [cls.create_agent_capability() for _ in range(2)]
        
        default_data = {
            "id": f"test_agent_{cls.random_string(4)}",
            "name": f"Test Agent {cls.random_string(4)}",
            "description": "A test agent for unit testing",
            "version": "1.0.0",
            "capabilities": capabilities,
            "available_tools": ["memory", "text_processing", "web_search"],
            "model": "test-model",
            "system_prompts": ["You are a test agent"],
            "tags": ["test", "unit-testing"]
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_agent_capability(cls, **kwargs) -> Dict[str, Any]:
        """Create test agent capability."""
        default_data = {
            "name": f"capability_{cls.random_string(4)}",
            "description": "A test capability",
            "input_schema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                }
            },
            "required_tools": ["memory"],
            "knowledge_domains": ["general"]
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_agent_execution_context(cls, **kwargs) -> Dict[str, Any]:
        """Create test agent execution context."""
        default_data = {
            "execution_id": f"exec_{cls.unique_id()}",
            "agent_id": f"test_agent_{cls.random_string(4)}",
            "operation": "test_operation",
            "parameters": {"param1": "value1", "param2": 42},
            "knowledge_context": {},
            "knowledge_queries": 0
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_agent_execution_result(cls, success: bool = True, **kwargs) -> Dict[str, Any]:
        """Create test agent execution result."""
        default_data = {
            "success": success,
            "execution_id": f"exec_{cls.unique_id()}",
            "agent_id": f"test_agent_{cls.random_string(4)}",
            "operation": "test_operation",
            "result": {"status": "completed", "output": "Test output"} if success else None,
            "error": None if success else "Test error message",
            "execution_time": random.uniform(0.1, 2.0),
            "tools_used": ["memory", "text_processing"],
            "knowledge_queries": cls.random_int(0, 5)
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_perception_result(cls, **kwargs) -> Dict[str, Any]:
        """Create test perception result."""
        default_data = {
            "input_understood": True,
            "input_type": "text",
            "context_enriched": True,
            "additional_context": {"word_count": 42, "sentiment": "positive"},
            "confidence": 0.95,
            "requires_clarification": False,
            "classification": "question",
            "entities": [
                {"type": "person", "value": "John Doe"},
                {"type": "location", "value": "New York"}
            ]
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_decision_result(cls, **kwargs) -> Dict[str, Any]:
        """Create test decision result."""
        default_data = {
            "decision": "Execute operation test_operation",
            "reasoning": "This is a test decision reasoning",
            "confidence": 0.92,
            "alternative_decisions": [
                {"decision": "Alt 1", "confidence": 0.4},
                {"decision": "Alt 2", "confidence": 0.3}
            ],
            "tools_to_use": ["memory", "text_processing"],
            "execution_plan": {
                "steps": [
                    {"step": "process_input", "tool": "text_processing"},
                    {"step": "generate_response", "tool": "memory"}
                ]
            },
            "knowledge_references": ["ref1", "ref2"]
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_action_result(cls, success: bool = True, **kwargs) -> Dict[str, Any]:
        """Create test action result."""
        default_data = {
            "success": success,
            "action_taken": "Executed test_operation",
            "tools_used": ["memory", "text_processing"],
            "tool_results": [
                {
                    "tool_name": "memory",
                    "success": True,
                    "result": {"status": "success", "data": "Memory result"},
                    "execution_time": 0.2
                },
                {
                    "tool_name": "text_processing",
                    "success": True,
                    "result": {"status": "success", "data": "Text processing result"},
                    "execution_time": 0.1
                }
            ],
            "output": {"response": "Test response", "details": {"key": "value"}},
            "execution_time": random.uniform(0.5, 3.0)
        }
        return {**default_data, **kwargs}


class DatabaseDataFactory(BaseDataFactory):
    """Factory for generating database-related test data."""
    
    @classmethod
    def create_user(cls, **kwargs) -> Dict[str, Any]:
        """Create test user data."""
        default_data = {
            "id": cls.random_int(1, 1000),
            "username": f"user_{cls.random_string(6)}",
            "email": cls.random_email(),
            "full_name": f"Test User {cls.random_int(1, 100)}",
            "is_active": True,
            "is_superuser": False,
            "created_at": cls.random_date().isoformat(),
            "updated_at": cls.random_date().isoformat()
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_api_key(cls, **kwargs) -> Dict[str, Any]:
        """Create test API key data."""
        default_data = {
            "id": cls.random_int(1, 1000),
            "key": f"api_{cls.unique_id()}",
            "name": f"API Key {cls.random_int(1, 100)}",
            "user_id": cls.random_int(1, 1000),
            "scopes": ["read", "write"],
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "created_at": cls.random_date().isoformat()
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_agent_record(cls, **kwargs) -> Dict[str, Any]:
        """Create test agent database record."""
        default_data = {
            "id": cls.random_int(1, 1000),
            "agent_id": f"agent_{cls.random_string(6)}",
            "name": f"Database Agent {cls.random_int(1, 100)}",
            "description": "A test agent record in the database",
            "config": json.dumps({
                "model": "test-model",
                "max_tokens": 1000,
                "temperature": 0.7
            }),
            "status": "active",
            "created_by": cls.random_int(1, 1000),
            "created_at": cls.random_date().isoformat(),
            "updated_at": cls.random_date().isoformat()
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_execution_record(cls, **kwargs) -> Dict[str, Any]:
        """Create test execution record."""
        default_data = {
            "id": cls.random_int(1, 1000),
            "execution_id": f"exec_{cls.unique_id()}",
            "agent_id": cls.random_int(1, 1000),
            "operation": "test_operation",
            "parameters": json.dumps({"param1": "value1", "param2": 42}),
            "result": json.dumps({"status": "completed", "output": "Test output"}),
            "success": True,
            "execution_time": cls.random_float(0.1, 5.0),
            "created_at": cls.random_date().isoformat()
        }
        return {**default_data, **kwargs}


class KnowledgeDataFactory(BaseDataFactory):
    """Factory for generating knowledge-related test data."""
    
    @classmethod
    def create_knowledge_item(cls, **kwargs) -> Dict[str, Any]:
        """Create test knowledge item."""
        default_data = {
            "id": f"knowledge_{cls.unique_id()}",
            "title": f"Knowledge Item {cls.random_int(1, 100)}",
            "content": f"This is test knowledge content with ID {cls.random_int(1000, 9999)}.",
            "metadata": {
                "source": "test",
                "author": f"Author {cls.random_int(1, 10)}",
                "created_at": cls.random_date().isoformat(),
                "domain": "test_domain",
                "tags": ["test", "knowledge", "item"]
            },
            "embedding": [cls.random_float() for _ in range(5)],  # Simplified embedding vector
            "vector_id": f"vector_{cls.unique_id()}"
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_knowledge_query_result(cls, **kwargs) -> Dict[str, Any]:
        """Create test knowledge query result."""
        items = kwargs.pop("items", None)
        if items is None:
            items = [cls.create_knowledge_item() for _ in range(3)]
        
        default_data = {
            "query": f"Test query {cls.random_int(1, 100)}",
            "results": items,
            "total_results": len(items),
            "search_time": cls.random_float(0.01, 0.5),
            "sources": ["test_source_1", "test_source_2"],
            "query_id": f"query_{cls.unique_id()}"
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_knowledge_domain(cls, **kwargs) -> Dict[str, Any]:
        """Create test knowledge domain."""
        default_data = {
            "id": f"domain_{cls.random_string(6)}",
            "name": f"Test Domain {cls.random_int(1, 10)}",
            "description": "A test knowledge domain",
            "item_count": cls.random_int(10, 1000),
            "created_at": cls.random_date().isoformat(),
            "updated_at": cls.random_date().isoformat()
        }
        return {**default_data, **kwargs}


class WorkflowDataFactory(BaseDataFactory):
    """Factory for generating workflow-related test data."""
    
    @classmethod
    def create_workflow(cls, **kwargs) -> Dict[str, Any]:
        """Create test workflow data."""
        steps = kwargs.pop("steps", None)
        if steps is None:
            steps = [cls.create_workflow_step() for _ in range(3)]
        
        default_data = {
            "id": f"workflow_{cls.random_string(6)}",
            "name": f"Test Workflow {cls.random_int(1, 100)}",
            "description": "A test workflow for unit testing",
            "steps": steps,
            "inputs": {"input1": "string", "input2": "number"},
            "outputs": {"output1": "string", "output2": "object"},
            "created_at": cls.random_date().isoformat(),
            "updated_at": cls.random_date().isoformat(),
            "version": "1.0.0",
            "tags": ["test", "workflow"]
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_workflow_step(cls, **kwargs) -> Dict[str, Any]:
        """Create test workflow step."""
        default_data = {
            "id": f"step_{cls.random_string(6)}",
            "name": f"Step {cls.random_int(1, 10)}",
            "type": cls.random_choice(["agent", "tool", "condition", "loop"]),
            "config": {
                "agent_id": f"agent_{cls.random_string(4)}" if cls.random_bool() else None,
                "operation": f"operation_{cls.random_string(4)}",
                "parameters": {"param1": "value1", "param2": "value2"}
            },
            "inputs": {"input1": "$workflow.inputs.input1"},
            "outputs": {"output1": "$step.result"},
            "next_step": f"step_{cls.random_string(6)}" if cls.random_bool() else None,
            "condition": "$inputs.value > 10" if cls.random_bool() else None
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_workflow_execution(cls, **kwargs) -> Dict[str, Any]:
        """Create test workflow execution data."""
        default_data = {
            "id": f"execution_{cls.unique_id()}",
            "workflow_id": f"workflow_{cls.random_string(6)}",
            "status": cls.random_choice(["running", "completed", "failed", "waiting"]),
            "started_at": cls.random_date().isoformat(),
            "completed_at": cls.random_date().isoformat() if cls.random_bool(0.7) else None,
            "inputs": {"input1": "test value", "input2": 42},
            "outputs": {"output1": "result value", "output2": {"key": "value"}} if cls.random_bool(0.7) else None,
            "current_step": f"step_{cls.random_string(6)}" if cls.random_bool(0.3) else None,
            "steps_completed": cls.random_int(0, 5),
            "steps_total": cls.random_int(5, 10),
            "error": "Error message" if cls.random_bool(0.2) else None
        }
        return {**default_data, **kwargs}


class ToolDataFactory(BaseDataFactory):
    """Factory for generating tool-related test data."""
    
    @classmethod
    def create_tool_config(cls, **kwargs) -> Dict[str, Any]:
        """Create test tool configuration."""
        default_data = {
            "name": f"tool_{cls.random_string(6)}",
            "description": "A test tool for unit testing",
            "version": "1.0.0",
            "parameters": {
                "param1": {"type": "string", "description": "First parameter"},
                "param2": {"type": "number", "description": "Second parameter"}
            },
            "required_parameters": ["param1"],
            "returns": {"type": "object", "description": "Tool result"},
            "timeout": cls.random_int(5, 60),
            "rate_limit": cls.random_int(10, 100),
            "enabled": True
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_tool_execution_request(cls, **kwargs) -> Dict[str, Any]:
        """Create test tool execution request."""
        default_data = {
            "tool_name": f"tool_{cls.random_string(6)}",
            "parameters": {
                "param1": f"value_{cls.random_string(4)}",
                "param2": cls.random_int(1, 100)
            },
            "execution_id": f"exec_{cls.unique_id()}",
            "timeout": cls.random_int(5, 30),
            "async_execution": cls.random_bool(0.3)
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_tool_execution_result(cls, success: bool = True, **kwargs) -> Dict[str, Any]:
        """Create test tool execution result."""
        default_data = {
            "execution_id": f"exec_{cls.unique_id()}",
            "tool_name": f"tool_{cls.random_string(6)}",
            "success": success,
            "result": {"status": "success", "data": "Tool execution result"} if success else None,
            "error": None if success else "Tool execution failed: test error",
            "execution_time": cls.random_float(0.1, 2.0),
            "timestamp": datetime.utcnow().isoformat()
        }
        return {**default_data, **kwargs}
    
    @classmethod
    def create_mcp_server_config(cls, **kwargs) -> Dict[str, Any]:
        """Create test MCP server configuration."""
        default_data = {
            "id": f"mcp_{cls.random_string(6)}",
            "name": f"MCP Server {cls.random_int(1, 10)}",
            "url": f"http://localhost:{cls.random_int(8000, 9000)}",
            "tools": [f"tool_{cls.random_string(4)}" for _ in range(3)],
            "status": "active",
            "auth_method": cls.random_choice(["none", "basic", "token"]),
            "auth_config": {
                "username": "test_user" if cls.random_bool() else None,
                "token": f"token_{cls.random_string(16)}" if cls.random_bool() else None
            },
            "rate_limit": cls.random_int(10, 100),
            "timeout": cls.random_int(5, 30),
            "retry_config": {
                "max_retries": cls.random_int(1, 5),
                "retry_delay": cls.random_float(0.1, 1.0)
            }
        }
        return {**default_data, **kwargs}