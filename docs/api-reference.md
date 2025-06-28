# Agentical Platform - API Reference

## Base URL

```
Production: https://api.agentical.com/v1
Staging: https://staging-api.agentical.com/v1
Local: http://localhost:8000/api/v1
```

## Authentication

All API endpoints require authentication using JWT tokens in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

## Rate Limiting

- **Standard tier**: 100 requests per minute
- **Premium tier**: 1000 requests per minute
- **Enterprise tier**: 10000 requests per minute

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    },
    "request_id": "req_123456789",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or expired token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Authentication Endpoints

### POST /auth/login

Authenticate user credentials and receive JWT token.

**Request:**
```json
{
  "username": "john_doe",
  "password": "secure_password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "rt_abcdef123456",
  "user": {
    "id": "users:abc123",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "permissions": ["read:agents", "write:tasks"]
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `423 Locked`: Account locked due to failed attempts
- `429 Too Many Requests`: Rate limit exceeded

### POST /auth/refresh

Refresh an expired JWT token.

**Request:**
```json
{
  "refresh_token": "rt_abcdef123456"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/logout

Invalidate current session and refresh token.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (204 No Content)**

### POST /auth/register

Register a new user account.

**Request:**
```json
{
  "username": "jane_doe",
  "email": "jane@example.com",
  "password": "secure_password123",
  "confirm_password": "secure_password123",
  "terms_accepted": true
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": "users:def456",
    "username": "jane_doe",
    "email": "jane@example.com",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z",
    "email_verified": false
  },
  "message": "Registration successful. Please check your email for verification."
}
```

---

## User Management

### GET /users/me

Get current user profile.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": "users:abc123",
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user",
  "permissions": ["read:agents", "write:tasks"],
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T12:00:00Z",
  "email_verified": true,
  "preferences": {
    "theme": "dark",
    "notifications": {
      "email": true,
      "push": false
    }
  },
  "quota": {
    "agents": {
      "used": 5,
      "limit": 10
    },
    "tasks_per_month": {
      "used": 150,
      "limit": 1000
    }
  }
}
```

### PUT /users/me

Update current user profile.

**Request:**
```json
{
  "email": "newemail@example.com",
  "preferences": {
    "theme": "light",
    "notifications": {
      "email": false,
      "push": true
    }
  }
}
```

**Response (200 OK):**
```json
{
  "id": "users:abc123",
  "username": "john_doe",
  "email": "newemail@example.com",
  "updated_at": "2024-01-01T12:30:00Z",
  "preferences": {
    "theme": "light",
    "notifications": {
      "email": false,
      "push": true
    }
  }
}
```

### POST /users/me/change-password

Change user password.

**Request:**
```json
{
  "current_password": "old_password123",
  "new_password": "new_secure_password456",
  "confirm_password": "new_secure_password456"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully",
  "password_changed_at": "2024-01-01T12:45:00Z"
}
```

---

## Agent Management

### GET /agents

List all agents with pagination and filtering.

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `size` (integer, default: 10, max: 100): Items per page
- `type` (string): Filter by agent type (`generic`, `super`, `specialized`)
- `status` (string): Filter by status (`idle`, `busy`, `error`, `offline`)
- `search` (string): Search in name and description
- `created_by` (string): Filter by creator user ID
- `sort` (string): Sort field (`name`, `created_at`, `updated_at`)
- `order` (string): Sort order (`asc`, `desc`)

**Example Request:**
```http
GET /agents?page=1&size=20&type=generic&status=idle&search=data%20analysis&sort=created_at&order=desc
```

**Response (200 OK):**
```json
{
  "agents": [
    {
      "id": "agents:abc123",
      "name": "Data Analysis Agent",
      "description": "Specialized agent for data analysis tasks",
      "type": "generic",
      "status": "idle",
      "configuration": {
        "model": "claude-3-sonnet",
        "temperature": 0.7,
        "max_tokens": 4000
      },
      "tools": ["filesystem", "python", "data_analysis"],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z",
      "created_by": "users:abc123",
      "is_active": true,
      "tags": ["data", "analysis", "python"],
      "performance_stats": {
        "total_tasks": 45,
        "completed_tasks": 42,
        "failed_tasks": 3,
        "average_duration_ms": 5200,
        "success_rate": 0.933
      }
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 5,
    "pages": 1
  },
  "filters": {
    "type": "generic",
    "status": "idle",
    "search": "data analysis"
  }
}
```

### POST /agents

Create a new agent.

**Request:**
```json
{
  "name": "Web Scraping Agent",
  "description": "Agent specialized in web scraping and data extraction",
  "type": "specialized",
  "configuration": {
    "model": "claude-3-sonnet",
    "temperature": 0.3,
    "max_tokens": 8000,
    "timeout_seconds": 300,
    "retry_attempts": 3
  },
  "tools": ["web_scraper", "html_parser", "data_extractor"],
  "tags": ["web", "scraping", "extraction"],
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": "agents:def456",
  "name": "Web Scraping Agent",
  "description": "Agent specialized in web scraping and data extraction",
  "type": "specialized",
  "status": "idle",
  "configuration": {
    "model": "claude-3-sonnet",
    "temperature": 0.3,
    "max_tokens": 8000,
    "timeout_seconds": 300,
    "retry_attempts": 3
  },
  "tools": ["web_scraper", "html_parser", "data_extractor"],
  "tags": ["web", "scraping", "extraction"],
  "created_at": "2024-01-01T13:00:00Z",
  "updated_at": "2024-01-01T13:00:00Z",
  "created_by": "users:abc123",
  "is_active": true,
  "performance_stats": {
    "total_tasks": 0,
    "completed_tasks": 0,
    "failed_tasks": 0,
    "average_duration_ms": 0,
    "success_rate": 0
  }
}
```

### GET /agents/{agent_id}

Get detailed information about a specific agent.

**Path Parameters:**
- `agent_id` (string): Agent ID

**Response (200 OK):**
```json
{
  "id": "agents:abc123",
  "name": "Data Analysis Agent",
  "description": "Specialized agent for data analysis tasks",
  "type": "generic",
  "status": "idle",
  "configuration": {
    "model": "claude-3-sonnet",
    "temperature": 0.7,
    "max_tokens": 4000,
    "timeout_seconds": 300,
    "retry_attempts": 3
  },
  "tools": ["filesystem", "python", "data_analysis"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "created_by": "users:abc123",
  "is_active": true,
  "tags": ["data", "analysis", "python"],
  "performance_stats": {
    "total_tasks": 45,
    "completed_tasks": 42,
    "failed_tasks": 3,
    "average_duration_ms": 5200,
    "success_rate": 0.933,
    "last_task_at": "2024-01-01T11:30:00Z"
  },
  "recent_tasks": [
    {
      "id": "tasks:xyz789",
      "title": "Analyze sales data",
      "status": "completed",
      "duration_ms": 4800,
      "completed_at": "2024-01-01T11:30:00Z"
    }
  ]
}
```

### PUT /agents/{agent_id}

Update an existing agent.

**Request:**
```json
{
  "name": "Advanced Data Analysis Agent",
  "description": "Enhanced agent for complex data analysis and visualization",
  "configuration": {
    "temperature": 0.5,
    "max_tokens": 6000
  },
  "tools": ["filesystem", "python", "data_analysis", "visualization"],
  "tags": ["data", "analysis", "python", "visualization"]
}
```

**Response (200 OK):** Same format as GET /agents/{agent_id}

### DELETE /agents/{agent_id}

Delete an agent. Only agents with no active tasks can be deleted.

**Response (204 No Content)**

### POST /agents/{agent_id}/activate

Activate a deactivated agent.

**Response (200 OK):**
```json
{
  "id": "agents:abc123",
  "status": "idle",
  "is_active": true,
  "activated_at": "2024-01-01T13:15:00Z"
}
```

### POST /agents/{agent_id}/deactivate

Deactivate an agent. This will prevent new tasks from being assigned.

**Response (200 OK):**
```json
{
  "id": "agents:abc123",
  "status": "offline",
  "is_active": false,
  "deactivated_at": "2024-01-01T13:20:00Z"
}
```

---

## Task Management

### POST /tasks

Create and optionally execute a new task.

**Request:**
```json
{
  "title": "Analyze Q4 Sales Data",
  "description": "Perform comprehensive analysis of Q4 sales data including trends, patterns, and forecasting",
  "type": "data_analysis",
  "priority": "high",
  "input_data": {
    "prompt": "Analyze the attached Q4 sales data and provide insights on trends, top-performing products, and revenue forecasting for Q1.",
    "files": [
      {
        "name": "q4_sales.csv",
        "url": "https://storage.agentical.com/files/q4_sales.csv",
        "type": "text/csv"
      }
    ],
    "parameters": {
      "include_visualization": true,
      "forecast_periods": 3
    }
  },
  "agent_id": "agents:abc123",
  "timeout_seconds": 600,
  "execute_immediately": true,
  "tags": ["sales", "q4", "analysis"]
}
```

**Response (201 Created):**
```json
{
  "id": "tasks:xyz789",
  "title": "Analyze Q4 Sales Data",
  "description": "Perform comprehensive analysis of Q4 sales data including trends, patterns, and forecasting",
  "type": "data_analysis",
  "priority": "high",
  "status": "running",
  "input_data": {
    "prompt": "Analyze the attached Q4 sales data...",
    "files": [...],
    "parameters": {...}
  },
  "assigned_agent": "agents:abc123",
  "created_at": "2024-01-01T14:00:00Z",
  "started_at": "2024-01-01T14:00:05Z",
  "estimated_completion": "2024-01-01T14:10:05Z",
  "tags": ["sales", "q4", "analysis"],
  "execution": {
    "id": "executions:exec123",
    "current_step": "data_processing",
    "progress_percentage": 25
  }
}
```

### GET /tasks

List tasks with pagination and filtering.

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `size` (integer, default: 10, max: 100): Items per page
- `status` (string): Filter by status (`pending`, `running`, `completed`, `failed`, `cancelled`)
- `type` (string): Filter by task type
- `priority` (string): Filter by priority (`low`, `medium`, `high`, `urgent`)
- `agent_id` (string): Filter by assigned agent
- `created_by` (string): Filter by creator
- `search` (string): Search in title and description
- `tags` (string): Filter by tags (comma-separated)
- `date_from` (string): Filter tasks created after this date (ISO 8601)
- `date_to` (string): Filter tasks created before this date (ISO 8601)
- `sort` (string): Sort field (`created_at`, `updated_at`, `priority`, `status`)
- `order` (string): Sort order (`asc`, `desc`)

**Response (200 OK):**
```json
{
  "tasks": [
    {
      "id": "tasks:xyz789",
      "title": "Analyze Q4 Sales Data",
      "type": "data_analysis",
      "priority": "high",
      "status": "completed",
      "assigned_agent": "agents:abc123",
      "created_at": "2024-01-01T14:00:00Z",
      "started_at": "2024-01-01T14:00:05Z",
      "completed_at": "2024-01-01T14:08:30Z",
      "duration_ms": 505000,
      "tags": ["sales", "q4", "analysis"],
      "success": true
    }
  ],
  "pagination": {
    "page": 1,
    "size": 10,
    "total": 25,
    "pages": 3
  },
  "summary": {
    "total_tasks": 25,
    "completed": 18,
    "running": 2,
    "failed": 3,
    "pending": 2
  }
}
```

### GET /tasks/{task_id}

Get detailed information about a specific task.

**Response (200 OK):**
```json
{
  "id": "tasks:xyz789",
  "title": "Analyze Q4 Sales Data",
  "description": "Perform comprehensive analysis of Q4 sales data including trends, patterns, and forecasting",
  "type": "data_analysis",
  "priority": "high",
  "status": "completed",
  "input_data": {
    "prompt": "Analyze the attached Q4 sales data...",
    "files": [
      {
        "name": "q4_sales.csv",
        "url": "https://storage.agentical.com/files/q4_sales.csv",
        "type": "text/csv",
        "size": 1048576
      }
    ],
    "parameters": {
      "include_visualization": true,
      "forecast_periods": 3
    }
  },
  "output_data": {
    "analysis_summary": "Q4 sales showed 15% growth compared to Q3...",
    "key_insights": [
      "Product category A led growth with 25% increase",
      "Geographic region West showed strongest performance",
      "December sales exceeded projections by 8%"
    ],
    "forecast": {
      "q1_revenue_projection": 2450000,
      "confidence_level": 0.87
    },
    "visualizations": [
      {
        "type": "chart",
        "title": "Q4 Sales Trend",
        "url": "https://storage.agentical.com/charts/q4_trend.png"
      }
    ],
    "files_generated": [
      {
        "name": "q4_analysis_report.pdf",
        "url": "https://storage.agentical.com/reports/q4_analysis.pdf",
        "type": "application/pdf",
        "size": 2097152
      }
    ]
  },
  "assigned_agent": "agents:abc123",
  "created_by": "users:abc123",
  "created_at": "2024-01-01T14:00:00Z",
  "started_at": "2024-01-01T14:00:05Z",
  "completed_at": "2024-01-01T14:08:30Z",
  "duration_ms": 505000,
  "tags": ["sales", "q4", "analysis"],
  "execution": {
    "id": "executions:exec123",
    "status": "completed",
    "steps": [
      {
        "name": "file_validation",
        "status": "completed",
        "started_at": "2024-01-01T14:00:05Z",
        "completed_at": "2024-01-01T14:00:08Z",
        "duration_ms": 3000
      },
      {
        "name": "data_processing",
        "status": "completed",
        "started_at": "2024-01-01T14:00:08Z",
        "completed_at": "2024-01-01T14:02:15Z",
        "duration_ms": 127000
      },
      {
        "name": "analysis_execution",
        "status": "completed",
        "started_at": "2024-01-01T14:02:15Z",
        "completed_at": "2024-01-01T14:07:20Z",
        "duration_ms": 305000
      },
      {
        "name": "report_generation",
        "status": "completed",
        "started_at": "2024-01-01T14:07:20Z",
        "completed_at": "2024-01-01T14:08:30Z",
        "duration_ms": 70000
      }
    ],
    "metrics": {
      "tokens_used": 15420,
      "api_calls": 8,
      "memory_peak_mb": 256,
      "cpu_time_ms": 45000
    }
  },
  "error_message": null
}
```

### PUT /tasks/{task_id}

Update task metadata (title, description, priority, tags). Only pending tasks can be modified.

**Request:**
```json
{
  "title": "Updated Q4 Sales Analysis",
  "priority": "urgent",
  "tags": ["sales", "q4", "analysis", "urgent"]
}
```

### DELETE /tasks/{task_id}

Cancel a pending or running task, or delete a completed task.

**Response (204 No Content)**

### POST /tasks/{task_id}/cancel

Cancel a running task.

**Response (200 OK):**
```json
{
  "id": "tasks:xyz789",
  "status": "cancelled",
  "cancelled_at": "2024-01-01T14:05:00Z",
  "reason": "User requested cancellation"
}
```

### POST /tasks/{task_id}/retry

Retry a failed task.

**Request:**
```json
{
  "reset_configuration": false,
  "new_agent_id": "agents:def456"
}
```

**Response (200 OK):**
```json
{
  "id": "tasks:xyz789",
  "status": "pending",
  "retry_count": 1,
  "reset_at": "2024-01-01T14:10:00Z"
}
```

---

## MCP Tool Integration

### GET /tools

List all available MCP tools.

**Query Parameters:**
- `enabled` (boolean): Filter by enabled status
- `health_status` (string): Filter by health status (`healthy`, `unhealthy`, `timeout`, `error`)
- `capability` (string): Filter by tool capability

**Response (200 OK):**
```json
{
  "tools": [
    {
      "id": "mcp_tools:filesystem",
      "name": "filesystem",
      "description": "File system operations including read, write, and directory management",
      "server_url": "http://filesystem-mcp:8080",
      "capabilities": [
        "read_file",
        "write_file",
        "list_directory",
        "create_directory",
        "delete_file"
      ],
      "configuration": {
        "max_file_size_mb": 100,
        "allowed_extensions": [".txt", ".csv", ".json", ".md"],
        "base_directory": "/workspace"
      },
      "is_enabled": true,
      "health_status": "healthy",
      "last_health_check": "2024-01-01T14:00:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z",
      "usage_stats": {
        "total_calls": 1250,
        "successful_calls": 1210,
        "failed_calls": 40,
        "average_response_ms": 150
      }
    },
    {
      "id": "mcp_tools:web_search",
      "name": "web_search",
      "description": "Web search and content retrieval capabilities",
      "server_url": "http://web-search-mcp:8080",
      "capabilities": [
        "search",
        "fetch_url",
        "extract_content"
      ],
      "configuration": {
        "search_engine": "google",
        "max_results": 20,
        "timeout_seconds": 30
      },
      "is_enabled": true,
      "health_status": "healthy",
      "last_health_check": "2024-01-01T14:00:00Z",
      "usage_stats": {
        "total_calls": 890,
        "successful_calls": 875,
        "failed_calls": 15,
        "average_response_ms": 2400
      }
    }
  ],
  "summary": {
    "total_tools": 12,
    "enabled_tools": 10,
    "healthy_tools": 9,
    "unhealthy_tools": 1
  }
}
```

### GET /tools/{tool_name}

Get detailed information about a specific tool.

**Response (200 OK):**
```json
{
  "id": "mcp_tools:filesystem",
  "name": "filesystem",
  "description": "File system operations including read, write, and directory management",
  "server_url": "http://filesystem-mcp:8080",
  "capabilities": [
    {
      "name": "read_file",
      "description": "Read contents of a file",
      "parameters": {
        "path": {
          "type": "string",
          "description": "File path to read",
          "required": true
        },
        "encoding": {
          "type": "string",
          "description": "File encoding (default: utf-8)",
          "required": false,
          "default": "utf-8"
        }
      },
      "returns": {
        "content": "string",
        "size": "integer",
        "modified": "datetime"
      }
    },
    {
      "name": "write_file",
      "description": "Write content to a file",
      "parameters": {
        "path": {
          "type": "string",
          "description": "File path to write",
          "required": true
        },
        "content": {
          "type": "string",
          "description": "Content to write",
          "required": true
        },
        "encoding": {
          "type": "string",
          "description": "File encoding (default: utf-8)",
          "required": false,
          "default": "utf-8"
        }
      },
      "returns": {
        "success": "boolean",
        "bytes_written": "integer"
      }
    }
  ],
  "configuration": {
    "max_file_size_mb": 100,
    "allowed_extensions": [".txt", ".csv", ".json", ".md"],
    "base_directory": "/workspace"
  },
  "is_enabled": true,
  "health_status": "healthy",
  "last_health_check": "2024-01-01T14:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "usage_stats": {
    "total_calls": 1250,
    "successful_calls": 1210,
    "failed_calls": 40,
    "average_response_ms": 150,
    "calls_by_function": {
      "read_file": 850,
      "write_file": 300,
      "list_directory": 100
    }
  },
  "recent_calls": [
    {
      "function": "read_file",
      "timestamp": "2024-01-01T13:58:30Z",
      "duration_ms": 120,
      "success": true
    },
    {
      "function": "write_file",
      "timestamp": "2024-01-01T13:55:15Z",
      "duration_ms": 180,
      "success": true
    }
  ]
}
```

### POST /tools/{tool_name}/execute

Execute a function on an MCP tool.

**Request:**
```json
{
  "function": "read_file",
  "parameters": {
    "path": "/workspace/data/sales_q4.csv",
    "encoding": "utf-8"
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "result": {
    "content": "Date,Product,Sales,Region\n2024-01-01,Widget A,1000,North\n...",
    "size": 15420,
    "modified": "2024-01-01T10:30:00Z"
  },
  "execution_time_ms": 125,
  "tool_call_id": "call_abc123",
  "timestamp": "2024-01-01T14:05:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "File not found: /workspace/data/sales_q4.csv",
    "tool_error": {
      "errno": 2,
      "path": "/workspace/data/sales_q4.csv"
    }
  },
  "execution_time_ms": 45,
  "tool_call_id": "call_def456",
  "timestamp": "2024-01-01T14:05:00Z"
}
```

### POST /tools/{tool_name}/health-check

Manually trigger a health check for a tool.

**Response (200 OK):**
```json
{
  "tool_name": "filesystem",
  "health_status": "healthy",
  "response_time_ms": 45,
  "checked_at": "2024-01-01T14:10:00Z",
  "details": {
    "server_reachable": true,
    "functions_available": 5,
    "configuration_valid": true
  }
}
```

### PUT /tools/{tool_name}/configuration

Update tool configuration.

**Request:**
```json
{
  "max_file_size_mb": 200,
  "allowed_extensions": [".txt", ".csv", ".json", ".md", ".py"],
  "base_directory": "/workspace"
}
```

**Response (200 OK):**
```json
{
  "tool_name": "filesystem",
  "configuration": {
    "max_file_size_mb": 200,
    "allowed_extensions": [".txt", ".csv", ".json", ".md", ".py"],
    "base_directory": "/workspace"
  },
  "updated_at": "2024-01-01T14:15:00Z"
}
```

---

## Playbook Management

### GET /playbooks

List all playbooks with filtering options.

**Query Parameters:**
- `page` (integer, default: 1): Page number
- `size` (integer, default: 10, max: 100): Items per page
- `active` (boolean): Filter by active status
- `created_by` (string): Filter by creator
- `tags` (string): Filter by tags (comma-separated)
- `search` (string): Search in name and description

**Response (200 OK):**
```json
{
  "playbooks": [
    {
      "id": "playbooks:abc123",
      "name": "Data Analysis Pipeline",
      "description": "Automated pipeline for processing and analyzing incoming data files",
      "is_active": true,
      "created_by": "users:abc123",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z",
      "tags": ["automation", "data", "analysis"],
      "execution_count": 25,
      "success_rate": 0.96,
      "average_duration_ms": 180000,
      "last_executed": "2024-01-01T13:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 10,
    "total": 8,
    "pages": 1
  }
}
```

### POST /playbooks

Create a new playbook.

**Request:**
```json
{
  "name": "Customer Report Generation",
  "description": "Automated workflow to generate monthly customer reports",
  "steps": [
    {
      "id": "step_1",
      "name": "Fetch Customer Data",
      "type": "tool_call",
      "tool": "database",
      "function": "query",
      "parameters": {
        "query": "SELECT * FROM customers WHERE created_at >= $start_date",
        "variables": {
          "start_date": "{{ variables.report_start_date }}"
        }
      },
      "output_variable": "customer_data"
    },
    {
      "id": "step_2",
      "name": "Generate Report",
      "type": "agent_task",
      "agent_id": "agents:report_agent",
      "task_type": "report_generation",
      "input": {
        "data": "{{ step_1.customer_data }}",
        "template": "monthly_customer_report",
        "format": "pdf"
      },
      "depends_on": ["step_1"]
    }
  ],
  "variables": {
    "report_start_date": {
      "type": "date",
      "description": "Start date for the report period",
      "required": true
    },
    "report_format": {
      "type": "string",
      "description": "Output format for the report",
      "default": "pdf",
      "options": ["pdf", "xlsx", "html"]
    }
  },
  "triggers": [
    {
      "type": "schedule",
      "schedule": "0 9 1 * *",
      "timezone": "UTC",
      "enabled": true
    },
    {
      "type": "webhook",
      "endpoint": "/webhooks/generate-report",
      "auth_required": true,
      "enabled": true
    }
  ],
  "tags": ["reports", "customers", "automation"]
}
```

**Response (201 Created):**
```json
{
  "id": "playbooks:def456",
  "name": "Customer Report Generation",
  "description": "Automated workflow to generate monthly customer reports",
  "steps": [...],
  "variables": {...},
  "triggers": [...],
  "tags": ["reports", "customers", "automation"],
  "is_active": true,
  "created_by": "users:abc123",
  "created_at": "2024-01-01T14:20:00Z",
  "updated_at": "2024-01-01T14:20:00Z",
  "execution_count": 0,
  "webhook_urls": [
    {
      "trigger_id": "webhook_1",
      "url": "https://api.agentical.com/v1/webhooks/generate-report?token=abc123def456"
    }
  ]
}
```

### GET /playbooks/{playbook_id}

Get detailed information about a specific playbook.

### PUT /playbooks/{playbook_id}

Update an existing playbook.

### DELETE /playbooks/{playbook_id}

Delete a playbook.

### POST /playbooks/{playbook_id}/execute

Manually execute a playbook.

**Request:**
```json
{
  "variables": {
    "report_start_date": "2024-01-01",
    "report_format": "pdf"
  },
  "execution_name": "January 2024 Report"
}
```

**Response (202 Accepted):**
```json
{
  "execution_id": "executions:exec789",
  "playbook_id": "playbooks:def456",
  "status": "running",
  "started_at": "2024-01-01T14:25:00Z",
  "variables": {
    "report_start_date": "2024-01-01",
    "report_format": "pdf"
  }
}
```

---

## Monitoring and Analytics

### GET /analytics/overview

Get platform overview statistics.

**Query Parameters:**
- `period` (string): Time period (`1h`, `24h`, `7d`, `30d`)
- `timezone` (string): Timezone for date aggregations (default: UTC)

**Response (200 OK):**
```json
{
  "period": "24h",
  "timezone": "UTC",
  "generated_at": "2024-01-01T14:30:00Z",
  "summary": {
    "total_agents": 45,
    "active_agents": 38,
    "total_tasks": 1250,
    "completed_tasks": 1180,
    "running_tasks": 12,
    "failed_tasks": 58,
    "success_rate": 0.944,
    "average_task_duration_ms": 8500
  },
  "performance": {
    "api_requests": {
      "total": 15420,
      "success_rate": 0.998,
      "average_response_ms": 120,
      "p95_response_ms": 350,
      "p99_response_ms": 850
    },
    "agent_utilization": {
      "average": 0.65,
      "peak": 0.92,
      "peak_time": "2024-01-01T10:15:00Z"
    },
    "resource_usage": {
      "cpu_average": 0.45,
      "memory_average_mb": 2048,
      "storage_used_gb": 45.2
    }
  },
  "task_distribution": {
    "by_type": {
      "data_analysis": 450,
      "text_processing": 320,
      "web_scraping": 180,
      "report_generation": 150,
      "other": 150
    },
    "by_priority": {
      "urgent": 25,
      "high": 180,
      "medium": 680,
      "low": 365
    },
    "by_status": {
      "completed": 1180,
      "running": 12,
      "failed": 58
    }
  },
  "trends": {
    "hourly_tasks": [
      {"hour": "2024-01-01T00:00:00Z", "count": 45},
      {"hour": "2024-01-01T01:00:00Z", "count": 38},
      {"hour": "2024-01-01T02:00:00Z", "count": 42}
    ],
    "success_rate_trend": [
      {"hour": "2024-01-01T00:00:00Z", "rate": 0.95},
      {"hour": "2024-01-01T01:00:00Z", "rate": 0.94},
      {"hour": "2024-01-01T02:00:00Z", "rate": 0.96}
    ]
  }
}
```

### GET /analytics/agents/{agent_id}

Get detailed analytics for a specific agent.

### GET /analytics/tools

Get MCP tool usage analytics.

### GET /health

Get system health status.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T14:35:00Z",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15,
      "connection_pool": {
        "active": 8,
        "idle": 12,
        "max": 20
      }
    },
    "cache": {
      "status": "healthy",
      "response_time_ms": 2,
      "memory_usage": {
        "used_mb": 512,
        "max_mb": 2048,
        "hit_rate": 0.94
      }
    },
    "mcp_tools": {
      "status": "healthy",
      "healthy_count": 9,
      "total_count": 10,
      "unhealthy_tools": ["slow_tool"]
    }
  },
  "metrics": {
    "cpu_usage": 0.45,
    "memory_usage_mb": 1024,
    "disk_usage_percent": 35,
    "active_connections": 150
  }
}
```

---

## WebSocket API

For real-time updates, connect to the WebSocket endpoint:

```
ws://localhost:8000/ws/v1/events
wss://api.agentical.com/ws/v1/events
```

### Authentication

Send JWT token as query parameter:
```
ws://localhost:8000/ws/v1/events?token=<jwt_token>
```

### Event Types

#### Task Status Updates
```json
{
  "type": "task_status_update",
  "data": {
    "task_id": "tasks:xyz789",
    "status": "running",
    "progress_percentage": 45,
    "current_step": "data_processing",
    "timestamp": "2024-01-01T14:40:00Z"
  }
}
```

#### Agent Status Updates
```json
{
  "type": "agent_status_update",
  "data": {
    "agent_id": "agents:abc123",
    "status": "busy",
    "current_task": "tasks:xyz789",
    "timestamp": "2024-01-01T14:40:00Z"
  }
}
```

#### System Notifications
```json
{
  "type": "system_notification",
  "data": {
    "level": "warning",
    "message": "High CPU usage detected",
    "details": {
      "cpu_usage": 0.85,
      "threshold": 0.80
    },
    "timestamp": "2024-01-01T14:40:00Z"
  }
}
```

---

## SDK and Client Libraries

### Python SDK

```python
from agentical import AgenticalClient

# Initialize client
client = AgenticalClient(
    api_key="your_api_key",
    base_url="https://api.agentical.com/v1"
)

# Create and execute a task
task = client.tasks.create(
    title="Analyze data",
    agent_id="agents:abc123",
    input_data={"prompt": "Analyze this dataset..."},
    execute_immediately=True
)

# Wait for completion
result = client.tasks.wait_for_completion(task.id, timeout=300)
print(result.output_data)
```

### JavaScript/TypeScript SDK

```typescript
import { AgenticalClient } from '@agentical/sdk';

const client = new AgenticalClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.agentical.com/v1'
});

// Create and execute task
const task = await client.tasks.create({
  title: 'Analyze data',
  agentId: 'agents:abc123',
  inputData: { prompt: 'Analyze this dataset...' },
  executeImmediately: true
});

// Wait for completion
const result = await client.tasks.waitForCompletion(task.id, { timeout: 300000 });
console.log(result.outputData);
```

This comprehensive API reference covers all major endpoints and functionality of the Agentical platform. For additional details, examples, and SDK documentation, visit the developer portal at https://docs.agentical.com.
