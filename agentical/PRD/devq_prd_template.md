# {PROJECT_NAME}: Product Requirements Document

**Version**: 1.0  
**Date**: {DATE}  
**Project**: {PROJECT_NAME}  
**Location**: `/Users/dionedge/devqai/{project_name}`

---

## 🎯 Executive Summary

{PROJECT_NAME} is a {brief_description} built on DevQ.ai's proven five-component stack: FastAPI foundation, Logfire observability, PyTest build-to-test development, TaskMaster AI project management, and comprehensive MCP server integration.

### Key Value Propositions

- **DevQ.ai Standard Stack**: FastAPI + Logfire + PyTest + TaskMaster AI + MCP integration
- **{UNIQUE_VALUE_1}**: {description}
- **{UNIQUE_VALUE_2}**: {description}
- **Enterprise Ready**: Logfire observability, production monitoring, scalable architecture
- **AI-Assisted Development**: Rich MCP ecosystem for enhanced productivity

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Functional Requirements](#-functional-requirements)
3. [Technical Architecture](#-technical-architecture)
4. [API Specifications](#-api-specifications)
5. [User Interface Requirements](#-user-interface-requirements)
6. [Performance Requirements](#-performance-requirements)
7. [Security & Compliance](#-security--compliance)
8. [Deployment & Operations](#-deployment--operations)
9. [Success Criteria](#-success-criteria)
10. [Development Roadmap](#-development-roadmap)

---

## 🎯 Project Overview

### Vision Statement
*"{PROJECT_VISION_STATEMENT}"*

### Target Users

#### Primary Users
- **{USER_TYPE_1}**: {use_cases}
- **{USER_TYPE_2}**: {use_cases}
- **{USER_TYPE_3}**: {use_cases}

#### Secondary Users
- **{USER_TYPE_4}**: {use_cases}
- **AI/ML Engineers**: Integration via MCP protocol and automated workflows

### Business Objectives

#### Quantifiable Goals
- **Adoption**: {target} active users within {timeframe}
- **Performance**: {performance_target}
- **Reliability**: 99.9% uptime for core services
- **Satisfaction**: >4.7/5 user rating

#### Strategic Outcomes
- {STRATEGIC_OUTCOME_1}
- {STRATEGIC_OUTCOME_2}
- {STRATEGIC_OUTCOME_3}

---

## ⚙️ Functional Requirements

### Core Application Features

#### FR-001: {CORE_FEATURE_1}
- **Priority**: High
- **Description**: {detailed_description}
- **Acceptance Criteria**:
  - {criteria_1}
  - {criteria_2}
  - {criteria_3}

#### FR-002: {CORE_FEATURE_2}
- **Priority**: High
- **Description**: {detailed_description}
- **Acceptance Criteria**:
  - {criteria_1}
  - {criteria_2}
  - {criteria_3}

### MCP Server Integration (Required)

#### FR-003: Standard MCP Protocol
- **Priority**: High
- **Description**: Full compliance with Model Context Protocol specification
- **Acceptance Criteria**:
  - JSON-RPC 2.0 message format
  - Standard tool registration and discovery
  - Error handling and status codes
  - Session management capabilities

#### FR-004: Domain-Specific MCP Tools
- **Priority**: High
- **Description**: Expose {domain} capabilities through MCP tools
- **Acceptance Criteria**:
  - `{tool_1}`: {description}
  - `{tool_2}`: {description}
  - `{tool_3}`: {description}
  - Real-time progress monitoring via WebSocket

### API & Integration Layer

#### FR-005: FastAPI Foundation
- **Priority**: High
- **Description**: RESTful API built with FastAPI for all core operations
- **Acceptance Criteria**:
  - OpenAPI/Swagger documentation
  - Input validation with Pydantic
  - Proper error handling and HTTP status codes
  - Rate limiting and security middleware

#### FR-006: Logfire Observability
- **Priority**: High
- **Description**: Comprehensive observability and monitoring
- **Acceptance Criteria**:
  - Automatic FastAPI instrumentation
  - Structured logging with context
  - Performance metrics and traces
  - Error tracking and alerting

---

## 🏗️ Technical Architecture

### DevQ.ai Standard Stack

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web/Panel UI │    │   MCP Server    │    │  CLI Interface  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Dashboard     │    │ • Tool Registry │    │ • Batch Jobs    │
│ • User Interface│    │ • Session Mgmt  │    │ • Automation    │
│ • Visualization │    │ • Real-time API │    │ • TaskMaster AI │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────────────────────────────┐
         │              {PROJECT} Core Engine            │
         ├───────────────────────────────────────────────┤
         │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
         │ │ FastAPI     │ │ Business    │ │ Data        │ │
         │ │ Foundation  │ │ Logic       │ │ Processing  │ │
         │ └─────────────┘ └─────────────┘ └─────────────┘ │
         │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
         │ │ Logfire     │ │ PyTest      │ │ {DOMAIN}    │ │
         │ │ Monitoring  │ │ Testing     │ │ Engine      │ │
         │ └─────────────┘ └─────────────┘ └─────────────┘ │
         └───────────────────────────────────────────────┘
                                 │
         ┌───────────────────────────────────────────────┐
         │               Integration Layer               │
         ├───────────────────────────────────────────────┤
         │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
         │ │ SurrealDB   │ │ Logfire     │ │ MCP Server  │ │
         │ │ Storage     │ │ Monitoring  │ │ Registry    │ │
         │ └─────────────┘ └─────────────┘ └─────────────┘ │
         └───────────────────────────────────────────────┘
```

### Technology Stack (Fixed)

#### Core Components (Required)
- **Language**: Python 3.11+
- **Web Framework**: FastAPI 0.104.0+
- **Observability**: Logfire 0.28.0+
- **Testing**: PyTest 7.4.0+
- **Task Management**: TaskMaster AI (MCP integration)

#### Data & Storage
- **Database**: SurrealDB (multi-model capabilities)
- **Cache**: Redis (session state, real-time data)
- **File Storage**: Local filesystem + optional cloud storage

#### Development & Monitoring
- **Code Quality**: Black, isort, mypy, ruff
- **Documentation**: MkDocs with Material theme
- **CI/CD**: GitHub Actions
- **Containerization**: Docker + Docker Compose

### Required Configuration Files

#### Project Structure (Standard)
```
{project_name}/
├── .claude/
│   └── settings.local.json      # Claude Code permissions and MCP discovery
├── .git/
│   └── config                   # Git configuration with DevQ.ai team settings
├── .logfire/
│   └── logfire_credentials.json # Logfire observability credentials
├── .zed/
│   └── settings.json            # Zed IDE configuration with MCP servers
├── mcp/
│   └── mcp-servers.json         # MCP server registry definitions
├── src/                         # Source code directory
├── tests/                       # PyTest test suite
├── .env                         # Environment variables
├── .gitignore                   # Git ignore patterns (DevQ.ai standard)
├── .rules                       # Development rules and guidelines
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Container orchestration
└── main.py                      # FastAPI application entry point
```

### Data Models

#### Core Entities
```python
# Define your domain-specific models here
@dataclass
class {DomainModel}:
    """Core domain entity"""
    id: str
    name: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

# Standard DevQ.ai patterns
class BaseResponse(BaseModel):
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, bool]
```

---

## 🔌 API Specifications

### MCP Tools Interface (Required)

#### Tool: {primary_tool}
```json
{
  "name": "{primary_tool}",
  "description": "{tool_description}",
  "inputSchema": {
    "type": "object",
    "properties": {
      "{param_1}": {
        "type": "string",
        "description": "{param_description}"
      },
      "{param_2}": {
        "type": "object",
        "properties": {
          "{nested_param}": {"type": "string"}
        }
      }
    },
    "required": ["{param_1}"]
  }
}
```

### FastAPI Endpoints (Standard)

#### Core Operations
- `POST /api/v1/{resource}` - Create resource
- `GET /api/v1/{resource}/{id}` - Get resource by ID
- `PUT /api/v1/{resource}/{id}` - Update resource
- `DELETE /api/v1/{resource}/{id}` - Delete resource
- `GET /api/v1/{resource}` - List resources with pagination

#### System Endpoints (Required)
- `GET /health` - Health check with dependency status
- `GET /api/v1/metrics` - Prometheus-compatible metrics
- `GET /api/v1/docs` - Interactive API documentation
- `GET /api/v1/openapi.json` - OpenAPI specification

#### MCP Integration Endpoints
- `POST /mcp/tools` - Register MCP tools
- `GET /mcp/capabilities` - List available MCP capabilities
- `WebSocket /mcp/ws` - Real-time MCP communication

---

## 🎨 User Interface Requirements

### {Choose appropriate UI framework based on project needs}

#### Option A: Panel Dashboard (For Data/Analytics Applications)
```python
# Panel-based interface for data-heavy applications
import panel as pn

main_dashboard = pn.template.FastListTemplate(
    title="{PROJECT_NAME}",
    sidebar=[navigation_panel, filters_panel],
    main=[
        pn.Row(primary_view, secondary_view),
        pn.Row(metrics_panel, actions_panel)
    ]
)
```

#### Option B: FastAPI + Frontend Framework (For Web Applications)
- **Frontend**: React/Vue.js/Svelte (specify based on requirements)
- **API Integration**: Axios/Fetch for REST API calls
- **Real-time**: WebSocket for live updates
- **Styling**: Tailwind CSS or component library

### Design System (DevQ.ai Standard)

#### Color Palette
- **Primary**: {project_primary_color}
- **Secondary**: {project_secondary_color}
- **Success**: #10B981 (Emerald)
- **Warning**: #F59E0B (Amber)
- **Error**: #EF4444 (Red)
- **Info**: #3B82F6 (Blue)

#### Typography
- **Headers**: Inter, 600 weight
- **Body**: Inter, 400 weight
- **Code**: JetBrains Mono, 400 weight

---

## ⚡ Performance Requirements

### API Performance (Required)
- **Response Time**: <100ms for CRUD operations (95th percentile)
- **Throughput**: Support 1000+ requests/second
- **Concurrent Users**: 100+ simultaneous users
- **Database Queries**: <50ms for standard operations

### MCP Performance
- **Tool Response Time**: <200ms for simple operations
- **WebSocket Latency**: <50ms for real-time updates
- **Session Management**: Support 50+ concurrent MCP sessions

### System Resources
- **Memory Usage**: <2GB for standard operations
- **CPU Utilization**: 80%+ efficiency on multi-core systems
- **Storage**: Efficient data storage with SurrealDB optimization

---

## 🔒 Security & Compliance

### Authentication & Authorization (Standard)
- **API Authentication**: JWT tokens with configurable expiry
- **Role-Based Access Control**: Admin, User, Viewer roles minimum
- **MCP Security**: Session-based authentication for tool access
- **Rate Limiting**: Configurable limits per endpoint and user

### Data Protection (Required)
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Input Validation**: Pydantic models for all API inputs
- **SQL Injection**: SQLAlchemy ORM protection
- **CORS**: Configurable origin policies

### Monitoring & Audit (Logfire Integration)
- **Access Logs**: All API and MCP tool usage
- **Error Tracking**: Comprehensive error capture and analysis
- **Performance Monitoring**: Request tracing and bottleneck identification
- **Security Events**: Failed authentication and suspicious activity

---

## 🚀 Deployment & Operations

### Container Configuration (Standard)

#### Dockerfile Template
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./src /app/src
WORKDIR /app

# Configure runtime
ENV PYTHONPATH=/app/src
ENV {PROJECT}_ENV=production

EXPOSE 8000
CMD ["uvicorn", "{project}.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose (Required Services)
```yaml
version: '3.8'

services:
  {project}-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SURREALDB_URL=ws://surrealdb:8000/rpc
      - REDIS_URL=redis://redis:6379
      - LOGFIRE_TOKEN=${LOGFIRE_TOKEN}
    depends_on:
      - surrealdb
      - redis

  surrealdb:
    image: surrealdb/surrealdb:latest
    ports:
      - "8001:8000"
    command: start --log info --user root --pass root memory
    volumes:
      - surrealdb_data:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  surrealdb_data:
  redis_data:
```

### Health Monitoring (Required)
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": __version__,
        "checks": {
            "database": await check_surrealdb_connection(),
            "redis": await check_redis_connection(),
            "logfire": check_logfire_connection(),
            "mcp_servers": await check_mcp_servers()
        }
    }
    
    if not all(checks["checks"].values()):
        checks["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=checks)
    
    return checks
```

---

## 🎯 Success Criteria

### Functional Acceptance Criteria

#### AC-001: DevQ.ai Stack Integration
- ✅ FastAPI application runs correctly
- ✅ Logfire observability operational
- ✅ PyTest suite passes with >90% coverage
- ✅ MCP server responds to tool calls
- ✅ TaskMaster AI integration functional

#### AC-002: Core Functionality
- ✅ All {domain-specific} operations work correctly
- ✅ API endpoints respond within performance targets
- ✅ Data persistence and retrieval working
- ✅ User interface renders and functions properly

#### AC-003: Production Readiness
- ✅ Docker deployment successful
- ✅ Health checks operational
- ✅ Monitoring dashboards configured
- ✅ Error handling comprehensive
- ✅ Security measures implemented

### Quality Metrics (Standard)

#### Code Quality
- **Test Coverage**: >90% line coverage
- **Type Safety**: Full type hints, mypy compliance
- **Code Style**: Black, isort, ruff compliance
- **Documentation**: 100% API documentation

#### Performance Benchmarks
- **API Response Time**: <100ms (95th percentile)
- **MCP Tool Response**: <200ms average
- **Memory Usage**: <2GB peak
- **Error Rate**: <0.1% of requests

---

## 🗓️ Development Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Theme**: Core Infrastructure & DevQ.ai Stack Setup

#### Week 1: Project Initialization
- ✅ Repository setup with DevQ.ai template
- ✅ Standard configuration files (.env, .rules, etc.)
- ✅ FastAPI application structure
- ✅ Logfire integration and configuration
- ✅ Basic health check endpoints

#### Week 2: Core Infrastructure
- ✅ SurrealDB integration and models
- ✅ PyTest test framework setup
- ✅ MCP server basic structure
- ✅ Docker containerization
- ✅ CI/CD pipeline configuration

### Phase 2: Core Features (Weeks 3-6)
**Theme**: Essential {Domain} Functionality

#### Week 3: Core Domain Logic
- ✅ {Primary feature 1} implementation
- ✅ Database schema and migrations
- ✅ API endpoints for core operations
- ✅ Basic error handling and validation

#### Week 4: MCP Integration
- ✅ MCP tool definitions and implementations
- ✅ Real-time communication via WebSocket
- ✅ Session management and authentication
- ✅ Tool registration and discovery

#### Week 5: User Interface
- ✅ {UI framework} setup and configuration
- ✅ Primary user workflows
- ✅ Real-time updates and interaction
- ✅ Basic styling and responsive design

#### Week 6: Testing & Quality
- ✅ Comprehensive test suite
- ✅ Integration testing
- ✅ Performance optimization
- ✅ Security audit and fixes

### Phase 3: Advanced Features (Weeks 7-10)
**Theme**: Enhanced Functionality & Polish

#### Week 7: {Advanced Feature 1}
- ✅ {Specific implementation details}
- ✅ Performance optimization
- ✅ Additional test coverage

#### Week 8: {Advanced Feature 2}
- ✅ {Specific implementation details}
- ✅ Integration with existing features
- ✅ User experience improvements

#### Week 9: Production Hardening
- ✅ Comprehensive error handling
- ✅ Monitoring and alerting setup
- ✅ Backup and recovery procedures
- ✅ Security enhancements

#### Week 10: Documentation & Launch
- ✅ Complete API documentation
- ✅ User guides and tutorials
- ✅ Deployment documentation
- ✅ Final testing and validation

### Phase 4: Future Enhancements (Post-Launch)
**Theme**: Continuous Improvement & Feature Expansion

#### Immediate Post-Launch (Weeks 11-12)
- Bug fixes and stability improvements
- User feedback integration
- Performance monitoring and optimization
- Community support setup

#### Future Roadmap (Months 3-6)
- {Future enhancement 1}
- {Future enhancement 2}
- Integration with additional MCP servers
- Advanced analytics and reporting

---

## 📚 Appendices

### Appendix A: Environment Variables Template

```bash
# Core Application
{PROJECT}_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Database Configuration
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_USERNAME=root
SURREALDB_PASSWORD=root
SURREALDB_NAMESPACE={project}
SURREALDB_DATABASE=main

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Logfire Configuration
LOGFIRE_TOKEN=your_logfire_token_here
LOGFIRE_PROJECT_NAME={project_name}
LOGFIRE_SERVICE_NAME={project_name}-api
LOGFIRE_ENVIRONMENT=development

# MCP Configuration
MCP_SERVER_NAME={project}-mcp-server
MCP_SERVER_VERSION=1.0.0
MCP_BIND_ADDRESS=127.0.0.1:8000

# TaskMaster AI
ANTHROPIC_API_KEY=your_anthropic_key_here
MODEL=claude-3-7-sonnet-20250219
MAX_TOKENS=64000
```

### Appendix B: MCP Server Registry Template

```json
{
  "mcp_servers": {
    "{project}-mcp": {
      "command": "python",
      "args": ["-m", "{project}_mcp.server"],
      "description": "{Project} MCP server with {domain} capabilities",
      "env": {
        "SURREALDB_URL": "${SURREALDB_URL}",
        "LOGFIRE_TOKEN": "${LOGFIRE_TOKEN}"
      }
    }
  }
}
```

### Appendix C: Standard Dependencies Template

```txt
# FastAPI Foundation
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0

# Logfire Observability
logfire[fastapi]>=0.28.0

# Testing Framework
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.25.0

# Database & Storage
surrealdb>=0.3.0
redis>=4.6.0

# Development Tools
black>=23.9.0
isort>=5.12.0
mypy>=1.6.0
ruff>=0.0.280

# MCP & AI Integration
# Add MCP-specific dependencies here

# Domain-Specific Dependencies
# Add your domain-specific packages here
```

---

## 📞 Support & Contact

### Development Team
- **Project Lead**: {Team Lead Name}
- **Architecture**: DevQ.ai Engineering Team
- **Backend Development**: Python/FastAPI Engineers
- **Frontend Development**: {Frontend Framework} Specialists
- **DevOps**: Infrastructure Engineers

### Community Resources
- **Documentation**: https://{project}.devq.ai/docs
- **GitHub Repository**: https://github.com/devqai/{project}
- **Issue Tracker**: https://github.com/devqai/{project}/issues
- **Discord Server**: https://discord.gg/devqai

### Enterprise Support
- **Email**: enterprise@devq.ai
- **Slack**: devqai-enterprise.slack.com
- **SLA**: 24/7 support for critical issues

---

*{PROJECT_NAME} - Built with DevQ.ai Standard Stack*  
*Copyright © 2025 DevQ.ai - All Rights Reserved*