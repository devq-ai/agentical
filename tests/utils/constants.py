"""
Constants and Sample Data for Agentical Testing Framework

This module provides comprehensive constants, sample data, error messages,
and configuration values used throughout the Agentical testing suite.

Features:
- Test configuration constants
- Sample data for various entity types
- Standard error messages and status codes
- API endpoint constants
- Database configuration values
- Performance testing constants
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

from agentical.db.models.agent import AgentType, AgentStatus
from agentical.db.models.playbook import PlaybookCategory, PlaybookStatus, ExecutionStatus
from agentical.db.models.user import User, Role


# =============================================================================
# Test Configuration Constants
# =============================================================================

TEST_CONSTANTS = {
    # Database
    "TEST_DATABASE_URL": "sqlite:///:memory:",
    "TEST_DATABASE_ECHO": False,
    "MAX_CONNECTION_RETRIES": 3,
    "CONNECTION_TIMEOUT": 30,

    # Authentication
    "JWT_SECRET": "test_secret_key_for_testing_only",
    "JWT_ALGORITHM": "HS256",
    "JWT_EXPIRY_HOURS": 1,
    "REFRESH_TOKEN_EXPIRY_DAYS": 7,
    "PASSWORD_MIN_LENGTH": 8,

    # API Testing
    "API_BASE_URL": "/api/v1",
    "DEFAULT_PAGE_SIZE": 10,
    "MAX_PAGE_SIZE": 100,
    "REQUEST_TIMEOUT": 30,
    "MAX_RETRIES": 3,

    # Performance Testing
    "PERFORMANCE_TIMEOUT": 10.0,  # seconds
    "MEMORY_LIMIT_MB": 100,
    "CPU_LIMIT_PERCENT": 80,
    "MIN_OPS_PER_SECOND": 10,
    "LOAD_TEST_USERS": 10,
    "LOAD_TEST_DURATION": 60,

    # File Testing
    "MAX_FILE_SIZE_MB": 10,
    "TEMP_DIR": "/tmp/agentical_tests",
    "UPLOAD_DIR": "/tmp/uploads",

    # External Services
    "MOCK_EXTERNAL_APIS": True,
    "MOCK_EMAIL_SERVICE": True,
    "MOCK_MCP_SERVERS": True,
    "MOCK_AI_RESPONSES": True,
}


# =============================================================================
# Sample Data
# =============================================================================

SAMPLE_DATA = {
    # User Data
    "users": {
        "admin": {
            "username": "admin",
            "email": "admin@test.com",
            "password": "AdminPass123!",
            "first_name": "Admin",
            "last_name": "User",
            "display_name": "Administrator",
            "is_verified": True,
            "roles": ["admin", "user"]
        },
        "regular_user": {
            "username": "testuser",
            "email": "user@test.com",
            "password": "UserPass123!",
            "first_name": "Test",
            "last_name": "User",
            "display_name": "Test User",
            "is_verified": True,
            "roles": ["user"]
        },
        "unverified_user": {
            "username": "unverified",
            "email": "unverified@test.com",
            "password": "UnverifiedPass123!",
            "first_name": "Unverified",
            "last_name": "User",
            "display_name": "Unverified User",
            "is_verified": False,
            "roles": ["user"]
        }
    },

    # Agent Data
    "agents": {
        "code_agent": {
            "name": "test_code_agent",
            "description": "Test code agent for software development tasks",
            "agent_type": AgentType.CODE_AGENT,
            "status": AgentStatus.ACTIVE,
            "configuration": {
                "capabilities": ["code_generation", "code_review", "debugging"],
                "tools": ["git", "ide", "compiler"],
                "languages": ["python", "javascript", "typescript"],
                "frameworks": ["fastapi", "react", "pytest"]
            }
        },
        "data_science_agent": {
            "name": "test_data_agent",
            "description": "Test data science agent for analytics tasks",
            "agent_type": AgentType.DATA_SCIENCE_AGENT,
            "status": AgentStatus.ACTIVE,
            "configuration": {
                "capabilities": ["data_analysis", "machine_learning", "visualization"],
                "tools": ["pandas", "numpy", "sklearn", "matplotlib"],
                "specializations": ["statistics", "modeling", "reporting"]
            }
        },
        "devops_agent": {
            "name": "test_devops_agent",
            "description": "Test DevOps agent for infrastructure tasks",
            "agent_type": AgentType.DEVOPS_AGENT,
            "status": AgentStatus.ACTIVE,
            "configuration": {
                "capabilities": ["deployment", "monitoring", "scaling"],
                "tools": ["docker", "kubernetes", "terraform"],
                "cloud_providers": ["aws", "gcp", "azure"]
            }
        }
    },

    # Playbook Data
    "playbooks": {
        "automation_playbook": {
            "name": "test_automation_playbook",
            "description": "Test automation playbook for CI/CD",
            "category": PlaybookCategory.AUTOMATION,
            "status": PlaybookStatus.PUBLISHED,
            "version": "1.0.0",
            "tags": ["automation", "ci/cd", "test"],
            "configuration": {
                "steps": [
                    {
                        "step_id": "step_1",
                        "name": "Code Checkout",
                        "type": "git_clone",
                        "configuration": {"repository": "test_repo"}
                    },
                    {
                        "step_id": "step_2",
                        "name": "Run Tests",
                        "type": "test_execution",
                        "configuration": {"test_command": "pytest"}
                    },
                    {
                        "step_id": "step_3",
                        "name": "Deploy",
                        "type": "deployment",
                        "configuration": {"target": "staging"}
                    }
                ]
            }
        },
        "monitoring_playbook": {
            "name": "test_monitoring_playbook",
            "description": "Test monitoring playbook for system health",
            "category": PlaybookCategory.MONITORING,
            "status": PlaybookStatus.DRAFT,
            "version": "0.1.0",
            "tags": ["monitoring", "health", "alerts"],
            "configuration": {
                "steps": [
                    {
                        "step_id": "step_1",
                        "name": "Check System Health",
                        "type": "health_check",
                        "configuration": {"endpoints": ["api", "database"]}
                    },
                    {
                        "step_id": "step_2",
                        "name": "Send Alerts",
                        "type": "notification",
                        "configuration": {"channels": ["email", "slack"]}
                    }
                ]
            }
        }
    },

    # Execution Data
    "executions": {
        "successful_execution": {
            "status": ExecutionStatus.COMPLETED,
            "progress": 100,
            "input_data": {"test_input": "sample_value"},
            "output_data": {"test_output": "processed_value"},
            "configuration": {"execution_mode": "test"},
            "error_message": None
        },
        "failed_execution": {
            "status": ExecutionStatus.FAILED,
            "progress": 75,
            "input_data": {"test_input": "invalid_value"},
            "output_data": None,
            "configuration": {"execution_mode": "test"},
            "error_message": "Test execution failed due to invalid input"
        },
        "running_execution": {
            "status": ExecutionStatus.RUNNING,
            "progress": 45,
            "input_data": {"test_input": "processing_value"},
            "output_data": None,
            "configuration": {"execution_mode": "test"},
            "error_message": None
        }
    },

    # Analytics Data
    "analytics": {
        "agent_metrics": {
            "total_agents": 25,
            "active_agents": 20,
            "inactive_agents": 3,
            "error_agents": 2,
            "agent_utilization": 78.5,
            "avg_response_time": 1.2,
            "success_rate": 95.3
        },
        "playbook_metrics": {
            "total_playbooks": 15,
            "published_playbooks": 12,
            "draft_playbooks": 2,
            "archived_playbooks": 1,
            "execution_count": 150,
            "success_rate": 87.5
        },
        "system_metrics": {
            "cpu_usage": 65.2,
            "memory_usage": 78.5,
            "disk_usage": 45.8,
            "network_io": 123.4,
            "uptime_hours": 720,
            "error_rate": 2.1
        }
    }
}


# =============================================================================
# Error Messages
# =============================================================================

ERROR_MESSAGES = {
    # Authentication Errors
    "AUTH_REQUIRED": "Authentication required",
    "INVALID_CREDENTIALS": "Invalid username or password",
    "TOKEN_EXPIRED": "Authentication token has expired",
    "TOKEN_INVALID": "Invalid authentication token",
    "ACCOUNT_LOCKED": "Account is temporarily locked due to failed login attempts",
    "EMAIL_NOT_VERIFIED": "Email address has not been verified",
    "INSUFFICIENT_PERMISSIONS": "Insufficient permissions to perform this action",

    # Validation Errors
    "FIELD_REQUIRED": "This field is required",
    "FIELD_TOO_SHORT": "This field is too short",
    "FIELD_TOO_LONG": "This field is too long",
    "INVALID_EMAIL": "Invalid email address format",
    "INVALID_UUID": "Invalid UUID format",
    "INVALID_DATE": "Invalid date format",
    "PASSWORD_TOO_WEAK": "Password does not meet strength requirements",

    # Resource Errors
    "RESOURCE_NOT_FOUND": "The requested resource was not found",
    "RESOURCE_ALREADY_EXISTS": "A resource with this identifier already exists",
    "RESOURCE_IN_USE": "Resource is currently in use and cannot be modified",
    "RESOURCE_LIMIT_EXCEEDED": "Resource limit exceeded",

    # Database Errors
    "DATABASE_CONNECTION_FAILED": "Failed to connect to database",
    "DATABASE_QUERY_FAILED": "Database query failed",
    "DATABASE_CONSTRAINT_VIOLATION": "Database constraint violation",
    "DATABASE_TRANSACTION_FAILED": "Database transaction failed",

    # External Service Errors
    "EXTERNAL_SERVICE_UNAVAILABLE": "External service is currently unavailable",
    "EXTERNAL_API_ERROR": "Error communicating with external API",
    "TIMEOUT_ERROR": "Request timeout occurred",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded",

    # System Errors
    "INTERNAL_SERVER_ERROR": "An internal server error occurred",
    "SERVICE_UNAVAILABLE": "Service is temporarily unavailable",
    "MAINTENANCE_MODE": "System is in maintenance mode",
    "CONFIGURATION_ERROR": "System configuration error"
}


# =============================================================================
# HTTP Status Codes
# =============================================================================

STATUS_CODES = {
    # Success
    "OK": 200,
    "CREATED": 201,
    "ACCEPTED": 202,
    "NO_CONTENT": 204,

    # Client Errors
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "TOO_MANY_REQUESTS": 429,

    # Server Errors
    "INTERNAL_SERVER_ERROR": 500,
    "NOT_IMPLEMENTED": 501,
    "BAD_GATEWAY": 502,
    "SERVICE_UNAVAILABLE": 503,
    "GATEWAY_TIMEOUT": 504
}


# =============================================================================
# API Endpoints
# =============================================================================

API_ENDPOINTS = {
    # Authentication
    "AUTH_LOGIN": "/auth/login",
    "AUTH_LOGOUT": "/auth/logout",
    "AUTH_REGISTER": "/auth/register",
    "AUTH_REFRESH": "/auth/refresh",
    "AUTH_ME": "/auth/me",
    "AUTH_VERIFY_EMAIL": "/auth/verify-email",
    "AUTH_RESET_PASSWORD": "/auth/reset-password",

    # Users
    "USERS_LIST": "/users",
    "USERS_CREATE": "/users",
    "USERS_GET": "/users/{user_id}",
    "USERS_UPDATE": "/users/{user_id}",
    "USERS_DELETE": "/users/{user_id}",

    # Agents
    "AGENTS_LIST": "/agents",
    "AGENTS_CREATE": "/agents",
    "AGENTS_GET": "/agents/{agent_id}",
    "AGENTS_UPDATE": "/agents/{agent_id}",
    "AGENTS_DELETE": "/agents/{agent_id}",
    "AGENTS_EXECUTE": "/agents/{agent_id}/execute",

    # Playbooks
    "PLAYBOOKS_LIST": "/playbooks",
    "PLAYBOOKS_CREATE": "/playbooks",
    "PLAYBOOKS_GET": "/playbooks/{playbook_id}",
    "PLAYBOOKS_UPDATE": "/playbooks/{playbook_id}",
    "PLAYBOOKS_DELETE": "/playbooks/{playbook_id}",
    "PLAYBOOKS_EXECUTE": "/playbooks/{playbook_id}/execute",
    "PLAYBOOKS_EXECUTIONS": "/playbooks/{playbook_id}/executions",

    # Workflows
    "WORKFLOWS_LIST": "/workflows",
    "WORKFLOWS_CREATE": "/workflows",
    "WORKFLOWS_GET": "/workflows/{workflow_id}",
    "WORKFLOWS_UPDATE": "/workflows/{workflow_id}",
    "WORKFLOWS_DELETE": "/workflows/{workflow_id}",
    "WORKFLOWS_EXECUTE": "/workflows/{workflow_id}/execute",

    # Analytics
    "ANALYTICS_OVERVIEW": "/analytics/overview",
    "ANALYTICS_AGENTS": "/analytics/agents",
    "ANALYTICS_PLAYBOOKS": "/analytics/playbooks",
    "ANALYTICS_PERFORMANCE": "/analytics/performance",

    # Health & System
    "HEALTH_CHECK": "/health",
    "SYSTEM_STATUS": "/system/status",
    "SYSTEM_METRICS": "/system/metrics"
}


# =============================================================================
# Test Data Generators
# =============================================================================

def generate_test_user_data(username: str = None, email: str = None) -> Dict[str, Any]:
    """Generate test user data with unique values."""
    unique_id = uuid.uuid4().hex[:8]

    return {
        "username": username or f"testuser_{unique_id}",
        "email": email or f"test_{unique_id}@example.com",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": f"User{unique_id}",
        "display_name": f"Test User {unique_id}",
        "is_verified": True
    }


def generate_test_agent_data(name: str = None, agent_type: AgentType = None) -> Dict[str, Any]:
    """Generate test agent data with unique values."""
    unique_id = uuid.uuid4().hex[:8]
    agent_type = agent_type or AgentType.CODE_AGENT

    return {
        "agent_id": str(uuid.uuid4()),
        "name": name or f"test_agent_{unique_id}",
        "description": f"Test {agent_type.value} agent {unique_id}",
        "agent_type": agent_type,
        "status": AgentStatus.ACTIVE,
        "configuration": {
            "capabilities": [f"capability_{unique_id}"],
            "tools": [f"tool_{unique_id}"],
            "version": "1.0.0"
        }
    }


def generate_test_playbook_data(name: str = None, category: PlaybookCategory = None) -> Dict[str, Any]:
    """Generate test playbook data with unique values."""
    unique_id = uuid.uuid4().hex[:8]
    category = category or PlaybookCategory.AUTOMATION

    return {
        "playbook_id": str(uuid.uuid4()),
        "name": name or f"test_playbook_{unique_id}",
        "description": f"Test {category.value} playbook {unique_id}",
        "category": category,
        "status": PlaybookStatus.DRAFT,
        "version": "1.0.0",
        "tags": [f"tag_{unique_id}", "test"],
        "configuration": {
            "steps": [
                {
                    "step_id": f"step_{i}",
                    "name": f"Test Step {i}",
                    "type": "action",
                    "configuration": {"test": True}
                }
                for i in range(3)
            ]
        }
    }


def generate_test_execution_data(
    playbook_id: str,
    status: ExecutionStatus = None
) -> Dict[str, Any]:
    """Generate test execution data."""
    status = status or ExecutionStatus.PENDING
    unique_id = uuid.uuid4().hex[:8]

    execution_data = {
        "execution_id": str(uuid.uuid4()),
        "playbook_id": playbook_id,
        "status": status,
        "started_at": datetime.utcnow().isoformat(),
        "configuration": {"test_execution": True, "id": unique_id},
        "input_data": {"test_input": f"value_{unique_id}"}
    }

    if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
        execution_data["completed_at"] = (
            datetime.utcnow() + timedelta(minutes=5)
        ).isoformat()
        execution_data["progress"] = 100 if status == ExecutionStatus.COMPLETED else 75

        if status == ExecutionStatus.COMPLETED:
            execution_data["output_data"] = {"test_output": f"result_{unique_id}"}
        else:
            execution_data["error_message"] = f"Test error {unique_id}"

    return execution_data


# =============================================================================
# Mock Response Templates
# =============================================================================

MOCK_RESPONSES = {
    "success": {
        "success": True,
        "message": "Operation completed successfully",
        "timestamp": "2024-01-01T00:00:00Z"
    },

    "error": {
        "success": False,
        "error": {
            "message": "An error occurred",
            "code": "GENERAL_ERROR"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    },

    "validation_error": {
        "detail": [
            {
                "loc": ["body", "field_name"],
                "msg": "Field validation failed",
                "type": "value_error"
            }
        ]
    },

    "auth_token": {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_type": "bearer",
        "expires_in": 3600
    },

    "paginated": {
        "items": [],
        "pagination": {
            "page": 1,
            "page_size": 10,
            "total": 0,
            "pages": 0,
            "has_next": False,
            "has_prev": False
        }
    }
}


# =============================================================================
# Test Environment Configuration
# =============================================================================

TEST_ENVIRONMENT = {
    "database": {
        "url": "sqlite:///:memory:",
        "echo": False,
        "pool_pre_ping": True,
        "pool_recycle": 3600
    },

    "redis": {
        "url": "redis://localhost:6379/1",
        "decode_responses": True,
        "socket_timeout": 5
    },

    "logging": {
        "level": "DEBUG",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "disable_existing_loggers": False
    },

    "fastapi": {
        "debug": True,
        "testing": True,
        "docs_url": None,  # Disable docs in testing
        "redoc_url": None  # Disable redoc in testing
    },

    "security": {
        "secret_key": "test_secret_key_for_testing_only",
        "algorithm": "HS256",
        "access_token_expire_minutes": 60,
        "refresh_token_expire_days": 7
    }
}


# =============================================================================
# Performance Testing Constants
# =============================================================================

PERFORMANCE_BENCHMARKS = {
    "response_times": {
        "fast": 0.1,      # 100ms
        "acceptable": 0.5, # 500ms
        "slow": 1.0,      # 1 second
        "timeout": 5.0    # 5 seconds
    },

    "throughput": {
        "low": 10,        # 10 ops/sec
        "medium": 100,    # 100 ops/sec
        "high": 1000,     # 1000 ops/sec
        "extreme": 10000  # 10k ops/sec
    },

    "memory_usage": {
        "small": 10,      # 10 MB
        "medium": 50,     # 50 MB
        "large": 100,     # 100 MB
        "huge": 500       # 500 MB
    },

    "concurrent_users": {
        "single": 1,
        "light": 10,
        "moderate": 50,
        "heavy": 100,
        "extreme": 500
    }
}


# =============================================================================
# Validation Patterns
# =============================================================================

VALIDATION_PATTERNS = {
    "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "username": r"^[a-zA-Z0-9._-]{3,50}$",
    "password": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
    "version": r"^\d+\.\d+\.\d+$",
    "iso_datetime": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
    "jwt_token": r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"
}
