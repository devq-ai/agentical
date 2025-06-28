"""
Mock Generators for External Services and APIs

This module provides comprehensive mock generators for external services,
APIs, and integrations used in the Agentical framework testing suite.

Features:
- External API response mocking
- MCP server response simulation
- Authentication service mocking
- Database operation mocking
- AI/ML service response generation
- Error condition simulation
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import random

import httpx
import pytest

from agentical.db.models.user import User, Role
from agentical.db.models.agent import Agent, AgentType, AgentStatus
from agentical.db.models.playbook import (
    Playbook, PlaybookExecution, ExecutionStatus, PlaybookStatus
)


class MockResponseGenerator:
    """Generator for realistic mock API responses."""

    @staticmethod
    def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Generate standard success response."""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4())
        }

    @staticmethod
    def error_response(
        message: str = "Error occurred",
        code: str = "GENERAL_ERROR",
        status_code: int = 500,
        details: Any = None
    ) -> Dict[str, Any]:
        """Generate standard error response."""
        response = {
            "success": False,
            "error": {
                "message": message,
                "code": code,
                "status_code": status_code
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4())
        }

        if details:
            response["error"]["details"] = details

        return response

    @staticmethod
    def paginated_response(
        items: List[Any],
        page: int = 1,
        page_size: int = 10,
        total: int = None
    ) -> Dict[str, Any]:
        """Generate paginated response."""
        total = total or len(items)
        pages = (total + page_size - 1) // page_size

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = items[start_idx:end_idx]

        return {
            "items": page_items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": pages,
                "has_next": page < pages,
                "has_prev": page > 1
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def validation_error_response(field_errors: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate validation error response in FastAPI format."""
        return {
            "detail": [
                {
                    "loc": ["body", field],
                    "msg": "; ".join(errors),
                    "type": "value_error",
                    "ctx": {"field": field}
                }
                for field, errors in field_errors.items()
            ]
        }

    @staticmethod
    def auth_token_response(
        user_id: int,
        username: str,
        roles: List[str] = None,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """Generate authentication token response."""
        return {
            "access_token": f"mock_token_{uuid.uuid4().hex[:16]}",
            "refresh_token": f"refresh_{uuid.uuid4().hex[:16]}",
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {
                "id": user_id,
                "username": username,
                "roles": roles or ["user"],
                "permissions": ["read"] + (["admin"] if "admin" in (roles or []) else [])
            }
        }

    @staticmethod
    def health_check_response(
        service_name: str,
        status: str = "healthy",
        checks: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """Generate health check response."""
        return {
            "service": service_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "uptime": "5d 12h 30m",
            "checks": checks or {
                "database": True,
                "external_apis": True,
                "memory": True,
                "disk": True
            }
        }


class MockDataGenerator:
    """Generator for realistic test data."""

    @staticmethod
    def user_data(count: int = 1, include_admin: bool = False) -> List[Dict[str, Any]]:
        """Generate mock user data."""
        users = []

        for i in range(count):
            user = {
                "id": i + 1,
                "username": f"user_{i+1}",
                "email": f"user{i+1}@test.com",
                "first_name": f"User",
                "last_name": f"{i+1}",
                "display_name": f"User {i+1}",
                "is_verified": True,
                "roles": ["user"],
                "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "last_login": datetime.utcnow().isoformat()
            }
            users.append(user)

        if include_admin:
            admin = {
                "id": count + 1,
                "username": "admin",
                "email": "admin@test.com",
                "first_name": "Admin",
                "last_name": "User",
                "display_name": "Admin User",
                "is_verified": True,
                "roles": ["admin", "user"],
                "created_at": (datetime.utcnow() - timedelta(days=count+1)).isoformat(),
                "last_login": datetime.utcnow().isoformat()
            }
            users.append(admin)

        return users

    @staticmethod
    def agent_data(count: int = 5) -> List[Dict[str, Any]]:
        """Generate mock agent data."""
        agents = []
        agent_types = ["code", "data_science", "devops", "research", "monitoring"]
        statuses = ["active", "inactive", "error"]

        for i in range(count):
            agent = {
                "agent_id": str(uuid.uuid4()),
                "name": f"agent_{i+1}",
                "description": f"Test agent {i+1} for automated testing",
                "agent_type": agent_types[i % len(agent_types)],
                "status": statuses[i % len(statuses)],
                "configuration": {
                    "capabilities": [f"capability_{i+1}"],
                    "tools": [f"tool_{i+1}"],
                    "version": "1.0.0"
                },
                "created_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            agents.append(agent)

        return agents

    @staticmethod
    def playbook_data(count: int = 3) -> List[Dict[str, Any]]:
        """Generate mock playbook data."""
        playbooks = []
        categories = ["automation", "deployment", "monitoring", "incident_response"]
        statuses = ["draft", "published", "archived"]

        for i in range(count):
            playbook = {
                "playbook_id": str(uuid.uuid4()),
                "name": f"playbook_{i+1}",
                "description": f"Test playbook {i+1} for automation",
                "category": categories[i % len(categories)],
                "status": statuses[i % len(statuses)],
                "version": f"1.{i}.0",
                "tags": [f"tag_{i+1}", "test"],
                "configuration": {
                    "steps": [
                        {
                            "step_id": f"step_{j}",
                            "name": f"Step {j+1}",
                            "type": "action",
                            "configuration": {"action": f"test_action_{j}"}
                        }
                        for j in range(3)
                    ]
                },
                "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            playbooks.append(playbook)

        return playbooks

    @staticmethod
    def execution_data(playbook_id: str, count: int = 2) -> List[Dict[str, Any]]:
        """Generate mock execution data."""
        executions = []
        statuses = ["pending", "running", "completed", "failed"]

        for i in range(count):
            execution = {
                "execution_id": str(uuid.uuid4()),
                "playbook_id": playbook_id,
                "status": statuses[i % len(statuses)],
                "started_at": (datetime.utcnow() - timedelta(hours=i+1)).isoformat(),
                "completed_at": datetime.utcnow().isoformat() if i % 2 == 0 else None,
                "progress": random.randint(0, 100),
                "configuration": {"test_execution": True},
                "input_data": {"test_input": f"value_{i}"},
                "output_data": {"test_output": f"result_{i}"} if i % 2 == 0 else None,
                "error_message": None if i % 2 == 0 else f"Test error {i}"
            }
            executions.append(execution)

        return executions

    @staticmethod
    def analytics_data() -> Dict[str, Any]:
        """Generate mock analytics data."""
        return {
            "summary": {
                "total_agents": 25,
                "active_agents": 20,
                "total_playbooks": 15,
                "total_executions": 150,
                "success_rate": 85.5
            },
            "agent_stats": {
                "by_type": {
                    "code": 8,
                    "data_science": 5,
                    "devops": 7,
                    "research": 3,
                    "monitoring": 2
                },
                "by_status": {
                    "active": 20,
                    "inactive": 3,
                    "error": 2
                }
            },
            "execution_stats": {
                "last_24h": 25,
                "last_7d": 120,
                "last_30d": 450,
                "avg_duration": 45.2,
                "success_rate": 87.3
            },
            "performance": {
                "cpu_usage": 65.2,
                "memory_usage": 78.5,
                "disk_usage": 45.8,
                "network_io": 123.4
            }
        }


class ExternalServiceMocker:
    """Mock external service integrations."""

    def __init__(self):
        self.mock_responses = {}
        self.call_counts = {}

    def mock_anthropic_api(self):
        """Mock Anthropic API responses."""
        responses = {
            "chat_completion": {
                "id": "msg_test_123",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "This is a mock response from Claude"
                    }
                ],
                "model": "claude-3-sonnet-20240229",
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 25
                }
            }
        }

        async def mock_post(url: str, **kwargs):
            self._increment_call_count("anthropic")
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = responses["chat_completion"]
            return mock_response

        return patch("httpx.AsyncClient.post", side_effect=mock_post)

    def mock_openai_api(self):
        """Mock OpenAI API responses."""
        responses = {
            "chat_completion": {
                "id": "chatcmpl-test123",
                "object": "chat.completion",
                "created": int(datetime.utcnow().timestamp()),
                "model": "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "This is a mock response from GPT-4"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            }
        }

        async def mock_post(url: str, **kwargs):
            self._increment_call_count("openai")
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = responses["chat_completion"]
            return mock_response

        return patch("httpx.AsyncClient.post", side_effect=mock_post)

    def mock_logfire_integration(self):
        """Mock Logfire integration."""
        mock_logfire = MagicMock()
        mock_logfire.span = MagicMock()
        mock_logfire.info = MagicMock()
        mock_logfire.error = MagicMock()
        mock_logfire.warning = MagicMock()
        mock_logfire.configure = MagicMock()
        mock_logfire.instrument_fastapi = MagicMock()

        return patch("logfire", mock_logfire)

    def mock_database_operations(self):
        """Mock database operations for error testing."""
        def mock_session_error():
            raise Exception("Database connection failed")

        def mock_commit_error():
            raise Exception("Database commit failed")

        return {
            "connection_error": patch("agentical.db.session.get_db", side_effect=mock_session_error),
            "commit_error": patch("sqlalchemy.orm.Session.commit", side_effect=mock_commit_error)
        }

    def mock_email_service(self):
        """Mock email service for notifications."""
        mock_email = MagicMock()
        mock_email.send_email = AsyncMock(return_value={"status": "sent", "message_id": "test_123"})
        mock_email.send_verification_email = AsyncMock(return_value=True)
        mock_email.send_password_reset = AsyncMock(return_value=True)

        return mock_email

    def _increment_call_count(self, service: str):
        """Increment call count for service."""
        self.call_counts[service] = self.call_counts.get(service, 0) + 1

    def get_call_count(self, service: str) -> int:
        """Get call count for service."""
        return self.call_counts.get(service, 0)

    def reset_call_counts(self):
        """Reset all call counts."""
        self.call_counts.clear()


class MCPServerMocker:
    """Mock MCP (Model Context Protocol) server responses."""

    def __init__(self):
        self.server_responses = self._initialize_server_responses()

    def _initialize_server_responses(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default server responses."""
        return {
            "taskmaster-ai": {
                "status": "healthy",
                "version": "1.0.0",
                "capabilities": ["task_management", "project_analysis"],
                "tools": ["get_tasks", "add_task", "update_task", "analyze_complexity"],
                "last_ping": datetime.utcnow().isoformat()
            },
            "ptolemies": {
                "status": "healthy",
                "version": "1.0.0",
                "capabilities": ["knowledge_base", "search", "retrieval"],
                "tools": ["search_knowledge", "store_document", "get_context"],
                "database_size": "597 documents",
                "last_ping": datetime.utcnow().isoformat()
            },
            "context7": {
                "status": "healthy",
                "version": "1.0.0",
                "capabilities": ["context_management", "memory", "reasoning"],
                "tools": ["store_context", "retrieve_context", "reason_about"],
                "memory_usage": "75%",
                "last_ping": datetime.utcnow().isoformat()
            },
            "bayes": {
                "status": "healthy",
                "version": "1.0.0",
                "capabilities": ["bayesian_inference", "statistical_modeling"],
                "tools": ["infer", "update_beliefs", "calculate_probability"],
                "models_loaded": 5,
                "last_ping": datetime.utcnow().isoformat()
            },
            "crawl4ai": {
                "status": "healthy",
                "version": "1.0.0",
                "capabilities": ["web_scraping", "content_extraction"],
                "tools": ["crawl_url", "extract_content", "parse_html"],
                "last_ping": datetime.utcnow().isoformat()
            }
        }

    def mock_server_health_check(self, server_name: str) -> Dict[str, Any]:
        """Mock server health check response."""
        if server_name in self.server_responses:
            return self.server_responses[server_name]
        else:
            return {
                "status": "unknown",
                "error": f"Server '{server_name}' not found"
            }

    def mock_task_management_responses(self) -> Dict[str, Any]:
        """Mock TaskMaster AI responses."""
        return {
            "get_tasks": {
                "tasks": [
                    {
                        "id": "1",
                        "title": "Test Task 1",
                        "status": "pending",
                        "priority": "high",
                        "complexity": 7,
                        "estimated_hours": 8
                    },
                    {
                        "id": "2",
                        "title": "Test Task 2",
                        "status": "in_progress",
                        "priority": "medium",
                        "complexity": 5,
                        "estimated_hours": 4
                    }
                ]
            },
            "add_task": {
                "task_id": "3",
                "status": "created",
                "message": "Task added successfully"
            },
            "analyze_complexity": {
                "complexity_score": 7,
                "factors": ["api_integration", "database_operations", "error_handling"],
                "estimated_hours": 12,
                "confidence": 0.85
            }
        }

    def mock_knowledge_base_responses(self) -> Dict[str, Any]:
        """Mock Ptolemies knowledge base responses."""
        return {
            "search_knowledge": {
                "results": [
                    {
                        "id": "doc_1",
                        "title": "API Development Best Practices",
                        "content": "Mock content about API development...",
                        "relevance": 0.92,
                        "source": "documentation"
                    },
                    {
                        "id": "doc_2",
                        "title": "Testing Strategies",
                        "content": "Mock content about testing...",
                        "relevance": 0.87,
                        "source": "documentation"
                    }
                ],
                "total_results": 15,
                "search_time": 0.023
            },
            "store_document": {
                "document_id": "doc_new",
                "status": "stored",
                "indexed": True
            }
        }

    def mock_context_management_responses(self) -> Dict[str, Any]:
        """Mock Context7 responses."""
        return {
            "store_context": {
                "context_id": str(uuid.uuid4()),
                "status": "stored",
                "memory_allocated": "2.5MB"
            },
            "retrieve_context": {
                "context": {
                    "session_id": "session_123",
                    "variables": {"key1": "value1", "key2": "value2"},
                    "history": ["action1", "action2", "action3"],
                    "metadata": {"created_at": datetime.utcnow().isoformat()}
                }
            }
        }

    def mock_all_servers(self) -> Dict[str, Any]:
        """Mock responses for all servers."""
        return {
            "health_checks": {name: self.mock_server_health_check(name)
                           for name in self.server_responses.keys()},
            "taskmaster": self.mock_task_management_responses(),
            "ptolemies": self.mock_knowledge_base_responses(),
            "context7": self.mock_context_management_responses()
        }

    def simulate_server_error(self, server_name: str, error_type: str = "connection_error"):
        """Simulate server error conditions."""
        error_responses = {
            "connection_error": {
                "status": "error",
                "error": f"Connection failed to {server_name}",
                "code": "CONNECTION_ERROR"
            },
            "timeout": {
                "status": "error",
                "error": f"Request timeout for {server_name}",
                "code": "TIMEOUT_ERROR"
            },
            "service_unavailable": {
                "status": "error",
                "error": f"Service {server_name} is unavailable",
                "code": "SERVICE_UNAVAILABLE"
            }
        }

        return error_responses.get(error_type, error_responses["connection_error"])


# Utility functions for common mocking scenarios
def mock_successful_api_call(data: Any = None):
    """Mock successful API call."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = MockResponseGenerator.success_response(data)
    return mock_response


def mock_failed_api_call(status_code: int = 500, message: str = "Internal Server Error"):
    """Mock failed API call."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = MockResponseGenerator.error_response(
        message=message,
        status_code=status_code
    )
    return mock_response


def mock_timeout_error():
    """Mock timeout error."""
    return httpx.TimeoutException("Request timeout")


def mock_connection_error():
    """Mock connection error."""
    return httpx.ConnectError("Connection failed")


# Context managers for mocking
class MockExternalServices:
    """Context manager for mocking all external services."""

    def __init__(self):
        self.service_mocker = ExternalServiceMocker()
        self.mcp_mocker = MCPServerMocker()
        self.patches = []

    def __enter__(self):
        # Mock AI services
        self.patches.append(self.service_mocker.mock_anthropic_api())
        self.patches.append(self.service_mocker.mock_openai_api())
        self.patches.append(self.service_mocker.mock_logfire_integration())

        # Start all patches
        for patch_obj in self.patches:
            patch_obj.start()

        return {
            "service_mocker": self.service_mocker,
            "mcp_mocker": self.mcp_mocker
        }

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Stop all patches
        for patch_obj in self.patches:
            patch_obj.stop()


# Decorators for common mocking scenarios
def with_mocked_external_services(func):
    """Decorator to mock external services for test function."""
    def wrapper(*args, **kwargs):
        with MockExternalServices() as mocks:
            return func(*args, mocks=mocks, **kwargs)
    return wrapper


def with_mocked_database_errors(func):
    """Decorator to mock database errors for test function."""
    def wrapper(*args, **kwargs):
        service_mocker = ExternalServiceMocker()
        with service_mocker.mock_database_operations()["connection_error"]:
            return func(*args, **kwargs)
    return wrapper
