# Claude Code Configuration for Ptolemies - Advanced Knowledge Management Platform

- You are 100% honest in all statements.

## 🚀 MANDATORY MCP SERVER INITIALIZATION

### REQUIRED MCP SERVERS - MUST BE VERIFIED ON SESSION START
**CRITICAL**: Before beginning ANY work, Claude Code MUST verify connectivity and functionality of ALL MCP servers. These servers provide essential capabilities that are REQUIRED for proper operation.

#### MCP Server Connection Requirements:
1. **IMMEDIATELY** upon session start, verify ALL MCP servers are accessible
2. **USE** MCP server tools throughout the session (not Python scripts)
3. **REPORT** any MCP server connection failures before proceeding
4. **PRIORITIZE** MCP server tools over alternative implementations

#### Required MCP Servers (By Name):
- **context7** - Documentation sourcing and semantic search
- **ptolemies** - Knowledge base access and management  
- **surrealdb** - Vector database operations
- **taskmaster-ai** - Task breakdown and management
- **filesystem** - File operations
- **git** - Version control operations
- **memory** - Session persistence
- **sequentialthinking** - Complex reasoning

#### MCP Server Verification Protocol:
```bash
# Test each MCP server on session start
# Example usage through Claude interface:
"Use context7 to check status"
"Use ptolemies to list available knowledge"
"Use surrealdb to verify database connection"
"Use taskmaster-ai to verify task management"
```

#### MCP Server Usage Examples:
- **DO**: "Use context7 to search for FastAPI documentation"
- **DO**: "Use ptolemies to find authentication patterns"
- **DO**: "Use surrealdb to query vector embeddings"
- **DON'T**: Create Python scripts that try to call MCP servers directly
- **DON'T**: Implement functionality that MCP servers already provide

## 🔒 MANDATORY VERIFICATION & PRECISION PROTOCOL

### NO COMPLETION CLAIMS WITHOUT TRIPLE VERIFICATION
This protocol is **NON-NEGOTIABLE** and must be followed for every task, subtask, and deliverable.

#### VERIFICATION LEVEL 1: Evidence-Based Reality
- **NEVER** claim success without running actual verification queries
- **ALWAYS** show real data counts, not assumptions
- **DOCUMENT** actual query results in all status reports
- **VERIFY** functionality with working examples, not theoretical descriptions

#### VERIFICATION LEVEL 2: Production Environment Compliance  
- **OPERATE** only within documented production environment and tools
- **USE** specified tech stack (FastAPI, PyTest, Logfire, TaskMaster AI, Pydantic AI)
- **MEET** all documented performance targets (sub-100ms, 90% test coverage)
- **VALIDATE** against production requirements, not alternative implementations

#### VERIFICATION LEVEL 3: Public-Ready Standards
- **ENSURE** production-grade quality suitable for public release
- **DEMONSTRATE** all functionality works to documented specifications  
- **PROVIDE** complete test coverage and performance validation
- **DELIVER** systems that meet professional development standards

### Mandatory Verification Queries (Run Before Any Completion Claim):
```bash
# Database connectivity & data existence
surreal sql --conn ws://localhost:8000/rpc --user root --pass root --ns ptolemies --db knowledge --pretty <<< "SELECT count() FROM document_chunks GROUP ALL;"

# Source coverage verification  
surreal sql --conn ws://localhost:8000/rpc --user root --pass root --ns ptolemies --db knowledge --pretty <<< "SELECT source_name, count() as chunks FROM document_chunks GROUP BY source_name ORDER BY chunks DESC;"

# Quality & performance metrics
surreal sql --conn ws://localhost:8000/rpc --user root --pass root --ns ptolemies --db knowledge --pretty <<< "SELECT math::mean(quality_score) as avg_quality FROM document_chunks GROUP ALL;"

# Functionality demonstration
surreal sql --conn ws://localhost:8000/rpc --user root --pass root --ns ptolemies --db knowledge --pretty <<< "SELECT title, source_name FROM document_chunks WHERE string::contains(content, 'API') LIMIT 3;"
```

### Historical Pattern Recognition:
**PREVIOUS FAILURES DOCUMENTED:**
1. Claimed "784 pages complete" without checking actual count (found 161)
2. Stated "vector search ready" without verifying embeddings (found NONE)
3. Reported "migration complete" without testing functionality
4. Created completion reports without running verification queries

**CORRECTIVE MEASURES:**
- All completion claims MUST include verification query results
- All functionality claims MUST be demonstrated with working examples  
- All performance claims MUST show actual metrics
- All system status reports MUST reflect verified reality

## Project Information
- **Organization**: DevQ.ai
- **Project**: Ptolemies - Advanced Knowledge Management Platform
- **Repository**: /Users/dionedge/devqai/ptolemies/
- **Purpose**: 784-page technical documentation knowledge base with vector search, graph relationships, and sub-100ms query performance
- **Rules Reference**: [./rules](./rules) directory for comprehensive development guidelines

## 🚫 BRANDING RESTRICTION
**DO NOT ADD ANYTHING LIKE THIS BRANDING TO A COMMIT MESSAGE:**
```
🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 🏗️ Core Architecture Requirements (Non-Negotiable)

### Primary Framework Stack
1. **FastAPI Foundation** - Core web framework for ALL projects
2. **PyTest Build-to-Test** - REQUIRED for every subtask progression
3. **Logfire Observability** - REQUIRED for every event and operation
4. **TaskMaster AI** - REQUIRED for task/subtask generation and management
5. **Pydantic AI** - REQUIRED when agents are needed

### Development Workflow Requirements

#### PyTest Testing Protocol
- **Unit tests REQUIRED** for every subtask before progression
- **Test coverage minimum**: 90% line coverage
- **Test structure**: Unit + Integration + API tests
- **Test execution**: `pytest tests/ --cov=src/ --cov-report=html`
- **Subtask progression**: Cannot advance without passing tests

#### Logfire Monitoring Protocol
- **Every event** must be logged through Logfire
- **Every function** must have Logfire spans for observability
- **Every API endpoint** must include Logfire instrumentation
- **Every error** must be captured with context
- **Performance metrics** tracked for all operations

#### TaskMaster AI Protocol
- **Task generation**: Must break down work into manageable subtasks
- **Subtask completion**: Requires comprehensive summary including:
  - Work accomplished
  - Complexity analysis
  - Logfire analysis and metrics
  - Test results and coverage
  - Dependencies and relationships

---

## 📋 Mandatory Tool Inventory & Testing

### Core Tools (Must Verify Accessibility)

#### Pydantic AI Integration
```python
# Required for agent implementations
from pydantic_ai import Agent
import logfire

# Example agent with required Logfire integration
@logfire.instrument()
async def create_pydantic_agent():
    agent = Agent(
        'claude-3-7-sonnet-20250219',
        system_prompt="DevQ.ai agent with Logfire monitoring"
    )
    return agent
```

#### Claude Code Tools
- **filesystem**: File operations and project management
- **git**: Version control with DevQ.ai team configuration
- **fetch**: API calls and external resource access
- **memory**: Session persistence across Claude Code interactions
- **sequentialthinking**: Step-by-step problem solving

#### Zed IDE Integration
- **Terminal**: Pre-configured with DevQ.ai environment
- **MCP Servers**: TaskMaster AI and knowledge tools
- **LSP**: Python/TypeScript with proper formatting
- **Git**: Inline blame and gutter integration

### Knowledge & Planning Tools (Mandatory for Complex Tasks)

#### Context7 (Redis-backed contextual reasoning)
```bash
# Verify Context7 accessibility through MCP
# Use in Claude conversation: "Use context7 to get status"
# Expected response: Server status with Redis/OpenAI connectivity
```

**Context7 MCP Tools:**
- `context7_status` - Check server and connection status
- `store_document` - Store documentation with embeddings
- `search_documents` - Semantic similarity search
- `crawl_documentation` - Web content extraction
- `get_context` - Contextual information retrieval

#### Ptolemies Knowledge Base
```bash
# Verify Ptolemies through MCP
# Use in Claude conversation: "Use ptolemies to search for FastAPI testing patterns"
# Expected response: Relevant knowledge base entries
```

**Ptolemies MCP Tools:**
- `ptolemies_search` - Search knowledge base
- `ptolemies_list` - List available knowledge
- `ptolemies_get` - Retrieve specific entries
- `ptolemies_status` - Check knowledge base status

#### Additional Knowledge Tools
- **Bayes**: Statistical modeling and analysis
- **Crawl4AI**: Web content extraction and analysis
- **SurrealDB**: Multi-model database operations
- **Neo4j**: Graph database and relationship mapping

### Required Tool Verification Script

```bash
#!/bin/bash
# tools-verification.sh - Must pass before project work begins

echo "🔍 Verifying DevQ.ai Tool Stack..."

# Core Framework Verification
python -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
python -c "import pytest; print('✅ PyTest:', pytest.__version__)"
python -c "import logfire; print('✅ Logfire:', logfire.__version__)"
python -c "import pydantic_ai; print('✅ Pydantic AI:', pydantic_ai.__version__)"

# Database Verification
curl -s http://localhost:8000/status && echo "✅ SurrealDB accessible"
python -c "import redis; print('✅ Redis accessible"

echo "🎉 Framework verification complete!"
echo ""
echo "📡 MCP Server Verification Required:"
echo "Use these commands in Claude conversation:"
echo "  - 'Use context7 to get status'"
echo "  - 'Use ptolemies to list knowledge'"
echo "  - 'Use surrealdb to check connection'"
echo "  - 'Use taskmaster-ai to verify status'"
echo "  - 'Use filesystem to list current directory'"
echo "  - 'Use git to check repository status'"
```

---

## 🎯 Development Standards

### Code Formatting
- **Backend**: 88 character line length, Black formatter
- **Frontend**: 100 character line length, single quotes, required semicolons
- **Python**: 3.12, Black formatter, Google-style docstrings
- **TypeScript**: Strict mode, ES2022 target

### FastAPI Application Template (Required)
```python
# main.py - Standard DevQ.ai FastAPI application
from fastapi import FastAPI, HTTPException, Depends
import logfire
import pytest
from contextlib import asynccontextmanager

# Configure Logfire (REQUIRED)
logfire.configure()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logfire.info("Application starting up")
    yield
    logfire.info("Application shutting down")

app = FastAPI(
    title="Machina - MCP Registry Platform",
    description="DevQ.ai's unified MCP server registry with health monitoring and configuration management",
    version="1.0.0",
    lifespan=lifespan
)

# Enable Logfire instrumentation (REQUIRED)
logfire.instrument_fastapi(app, capture_headers=True)

@app.get("/health")
async def health_check():
    """Health check with Logfire logging."""
    with logfire.span("Health check"):
        logfire.info("Health check requested")
        return {"status": "healthy", "framework": "FastAPI + DevQ.ai stack"}
```

### PyTest Configuration Template (Required)
```python
# conftest.py - Required test configuration
import pytest
import asyncio
from fastapi.testclient import TestClient
import logfire

# Configure test logging
logfire.configure(send_to_logfire=False)  # Disable in tests

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    from main import app
    with TestClient(app) as test_client:
        yield test_client

# Required test pattern
def test_health_endpoint(client):
    """All endpoints must have tests."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Documentation Requirements
- **All public APIs** must have complete OpenAPI documentation
- **Google-style docstrings** for all Python functions
- **React components** with props and state descriptions
- **Code examples** for all non-trivial functions
- **Logfire span documentation** for observability

---

## 🔧 Database Integration Standards

### SurrealDB (Primary Multi-model Database)
```python
# Required SurrealDB integration pattern
import surrealdb
import logfire

@logfire.instrument()
async def setup_surrealdb():
    """Standard SurrealDB setup with Logfire monitoring."""
    db = surrealdb.Surreal()
    await db.connect('ws://localhost:8000/rpc')
    await db.use('ptolemies', 'knowledge')
    logfire.info("SurrealDB connected", namespace="ptolemies")
    return db
```

### Database Selection Guidelines
- **SurrealDB**: Primary choice for knowledge bases with vector search
- **PostgreSQL**: Relational data and ACID transactions
- **Redis**: Caching, session storage, and pub/sub messaging
- **Neo4j**: Knowledge graphs and complex relationship analysis

---

## 🤖 Agent Development Standards

### Pydantic AI Agent Template (Required when agents needed)
```python
from pydantic_ai import Agent
import logfire
from typing import Dict, Any

@logfire.instrument()
class DevQaiAgent:
    """Standard DevQ.ai agent with Logfire integration."""

    def __init__(self, model: str = 'claude-3-7-sonnet-20250219'):
        self.agent = Agent(
            model,
            system_prompt="""You are a DevQ.ai agent.
            Requirements:
            - Use FastAPI for all web services
            - Include PyTest for all functionality
            - Log everything through Logfire
            - Generate TaskMaster AI tasks for complex work"""
        )

    @logfire.instrument()
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process task with full observability."""
        with logfire.span("Agent task processing", task_id=task.get('id')):
            result = await self.agent.run(task['prompt'])
            logfire.info("Task completed", task_id=task.get('id'), result_length=len(str(result)))
            return result
```

### Agent Integration Requirements
- **Error handling** for all tool usage
- **Logfire monitoring** for all agent operations
- **PyTest coverage** for agent functionality
- **TaskMaster integration** for complex workflows

---

## 🧪 Quality Assurance Standards

### Component Requirements
- **Frontend components**: Must support light and dark themes
- **API endpoints**: Proper validation and error responses with Logfire logging
- **Database operations**: Connection pooling, transaction management, and monitoring
- **Agent components**: Comprehensive error handling and observability

### Default Review Checklist
- [ ] Follows FastAPI patterns and best practices
- [ ] Includes comprehensive PyTest coverage (90%+)
- [ ] Has complete Logfire instrumentation
- [ ] TaskMaster AI tasks documented and completed
- [ ] Includes appropriate error handling
- [ ] Maintains backward compatibility
- [ ] Follows security best practices
- [ ] Agent functionality (if applicable) properly integrated

---

## 🛠️ MCP Server Configuration

### Core MCP Servers (Required)
```yaml
# In .claude/settings.local.json
filesystem:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem", "."]

git:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-git"]

memory:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-memory"]

sequentialthinking:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-sequentialthinking"]

taskmaster-ai:
  command: npx
  args: ["-y", "--package=task-master-ai", "task-master-ai"]
  env:
    ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY}"
    MODEL: "claude-3-7-sonnet-20250219"
```

### Knowledge & Development Servers
```yaml
context7:
  command: python
  args: ["-m", "context7_mcp.server"]
  cwd: "./devqai/mcp/mcp-servers/context7-mcp"

ptolemies:
  command: python
  args: ["-m", "ptolemies.mcp.ptolemies_mcp"]
  cwd: "./devqai/ptolemies"

surrealdb:
  command: python
  args: ["-m", "surrealdb_mcp.server"]
  cwd: "./devqai/mcp/mcp-servers/surrealdb-mcp"
```

---

## 📋 Environment Configuration

### Required Environment Variables
```bash
# Core Configuration
DEVQAI_ROOT=/Users/dionedge/devqai
PYTHONPATH=/Users/dionedge/devqai:$PYTHONPATH

# FastAPI & Logfire
LOGFIRE_TOKEN=pylf_v1_us_...
LOGFIRE_PROJECT_NAME=machina-mcp-registry
LOGFIRE_SERVICE_NAME=machina-api

# TaskMaster AI
ANTHROPIC_API_KEY=sk-ant-...
MODEL=claude-3-7-sonnet-20250219

# Knowledge Base
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_USERNAME=root
SURREALDB_PASSWORD=root
PTOLEMIES_PATH=/Users/dionedge/devqai/ptolemies

# Context & Memory
UPSTASH_REDIS_REST_URL=your_redis_url
UPSTASH_REDIS_REST_TOKEN=your_redis_token
```

---

## 🎯 Usage Workflow

### Daily Development Process
1. **MCP Server Verification**: Verify ALL MCP servers are connected and functional
   - Use context7 status check
   - Use ptolemies list command
   - Use surrealdb connection test
   - Use taskmaster-ai verification
2. **Tool Verification**: Run tools-verification.sh
3. **Session Initialization**: Start Zed, source DevQ.ai environment
4. **Task Management**: Use TaskMaster AI for task breakdown (via MCP)
5. **Implementation**: Follow FastAPI + PyTest + Logfire pattern
6. **Testing**: Ensure 90% coverage before subtask progression
7. **Monitoring**: Review Logfire dashboards for performance
8. **Documentation**: Update comprehensive summaries

### Subtask Completion Requirements
Each subtask must include:
- ✅ **Work accomplished** - Detailed description of changes
- ✅ **Complexity analysis** - TaskMaster AI complexity scoring
- ✅ **Logfire analysis** - Performance metrics and error rates
- ✅ **Test results** - Coverage percentage and passing tests
- ✅ **Dependencies** - Impact on other tasks/subtasks

---

This configuration ensures Claude Code operates within the DevQ.ai ecosystem with all required MCP servers connected and properly integrated.

## 🔌 MCP Server Integration Protocol

### Mandatory MCP Server Usage
**CRITICAL**: MCP servers are the PRIMARY interface for extended capabilities. Always prefer MCP server tools over custom implementations.

#### MCP Server Priority Order:
1. **Knowledge Operations**: Use `context7` and `ptolemies` MCP servers
2. **Database Operations**: Use `surrealdb` MCP server  
3. **Task Management**: Use `taskmaster-ai` MCP server
4. **File Operations**: Use `filesystem` MCP server
5. **Version Control**: Use `git` MCP server

#### Example MCP-First Workflow:
```markdown
# CORRECT Approach (Using MCP Servers):
1. "Use context7 to search for authentication patterns"
2. "Use ptolemies to find related knowledge"
3. "Use surrealdb to query vector embeddings"
4. "Use taskmaster-ai to break down the implementation"

# INCORRECT Approach (Direct Python calls):
1. Creating Python scripts to call MCP servers
2. Implementing functionality that MCP servers provide
3. Using subprocess to interact with MCP tools
```

This configuration ensures Claude Code operates within the DevQ.ai ecosystem with all required tools accessible and properly integrated through MCP servers.

## Neo4j Framework References
- **@neo4j_current_framework.txt** - A key reference for graph database integration and modeling techniques