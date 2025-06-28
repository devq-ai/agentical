# Agentical Framework Capabilities

**Comprehensive documentation of tools, workflows, agents, and capabilities available in the Agentical framework**

*Last Updated: June 28, 2025*  
*Version: 1.0.0*  
*Framework Version: Agentical v1.0.0*

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Tools Catalog](#tools-catalog)
3. [Workflow Types](#workflow-types)
4. [Created Agents](#created-agents)
5. [Planned Agents](#planned-agents)
6. [Integration Capabilities](#integration-capabilities)
7. [Performance & Scaling](#performance--scaling)

---

## 🎯 Overview

The Agentical framework provides a comprehensive ecosystem of AI agents, tools, and workflows built on:

- **Base Architecture**: Pydantic AI + FastAPI foundation
- **Observability**: Logfire integration for comprehensive monitoring
- **Tool Integration**: Model Context Protocol (MCP) for seamless tool access
- **Database**: SurrealDB for multi-model data storage
- **Knowledge Base**: Ptolemies integration with 597+ production documents
- **Agent Model**: Perception-Decision-Action-Reflection pattern

### Framework Statistics
- **26 MCP Servers**: Core and specialized tools
- **50+ Tool Types**: Categorized by domain and function
- **10 Workflow Types**: Standard and advanced orchestration patterns
- **4 Production Agents**: Fully implemented and deployed
- **15 Planned Agents**: Specialized domain agents in development

---

## 🛠️ Tools Catalog

### Core MCP Servers (NPX-based)

| Tool Name | Source | Requirements | Description |
|-----------|--------|--------------|-------------|
| **filesystem** | `@modelcontextprotocol/server-filesystem` | Node.js, NPX | File read/write operations for project directory |
| **git** | `@modelcontextprotocol/server-git` | Node.js, Git | Version control operations, commits, branch management |
| **fetch** | `@modelcontextprotocol/server-fetch` | Node.js, HTTP | API calls and external resource access |
| **memory** | `@modelcontextprotocol/server-memory` | Node.js | Persistent memory across Claude Code sessions |
| **sequentialthinking** | `@modelcontextprotocol/server-sequentialthinking` | Node.js | Enhanced step-by-step problem solving |
| **github** | `@modelcontextprotocol/server-github` | GitHub API token | Repository management, issues, pull requests |
| **inspector** | `@modelcontextprotocol/inspector` | Node.js | Debug MCP server connections |

### DevQ.ai Python Servers

| Tool Name | Source | Requirements | Description |
|-----------|--------|--------------|-------------|
| **taskmaster-ai** | `../machina/mcp/mcp-servers/task-master` | Anthropic API | TaskMaster AI project management and task tracking |
| **ptolemies-mcp** | `../ptolemies` | SurrealDB | Knowledge base integration with 597 documents |
| **context7-mcp** | `../machina/mcp/mcp-servers/context7-mcp` | Redis | Advanced contextual reasoning with memory |
| **crawl4ai-mcp** | `../machina/mcp/mcp-servers/crawl4ai-mcp` | Python | Web scraping and content extraction |
| **surrealdb-mcp** | `../machina/mcp/mcp-servers/surrealdb-mcp` | SurrealDB | Multi-model database operations |
| **logfire-mcp** | `../machina/mcp/mcp-servers/logfire-mcp` | Logfire token | Observability and monitoring integration |
| **magic-mcp** | `../machina/mcp/mcp-servers/magic-mcp` | Python | Magic utilities and helper functions |

### Specialized Development Servers

| Tool Name | Source | Requirements | Description |
|-----------|--------|--------------|-------------|
| **dart-mcp** | `dart-mcp-server` | Dart token | Smart code assistance and development |
| **agentql-mcp** | `agentql_mcp.server` | Python | Web automation and query tool |
| **browser-tools-mcp** | `browser_tools_mcp.server` | Python | Browser automation and interaction |
| **jupyter-mcp** | `jupyter_mcp.server` | Jupyter | Notebook execution and management |
| **shadcn-ui-mcp-server** | `shadcn_ui_mcp.server` | Python | Shadcn/UI component library integration |
| **registry-mcp** | `registry_mcp.server` | Python | MCP server registry management |

### External Service Integrations

| Tool Name | Source | Requirements | Description |
|-----------|--------|--------------|-------------|
| **calendar-mcp** | `calendar_mcp.server` | Google Calendar API | Event management and scheduling |
| **stripe-mcp** | `stripe_mcp.server` | Stripe API key | Payment processing integration |

### Scientific Computing & Solvers

| Tool Name | Source | Requirements | Description |
|-----------|--------|--------------|-------------|
| **bayes-mcp** | `bayes_mcp.server` | Python | Bayesian inference and probabilistic modeling |
| **solver-z3-mcp** | `solver_z3_mcp.server` | Z3 solver | Theorem prover and SMT solver |
| **solver-pysat-mcp** | `solver_pysat_mcp.server` | PySAT | Boolean satisfiability solver |

### AI/ML Internal Tools

| Tool Name | Source | Requirements | Description |
|-----------|--------|--------------|-------------|
| **vector_store** | `agentical.tools.ai_ml` | FAISS/Pinecone | Vector database for embeddings and similarity search |
| **llm_router** | `agentical.tools.ai_ml` | Multiple LLM APIs | Multi-provider language model routing |
| **model_evaluator** | `agentical.tools.ai_ml` | ML frameworks | AI model evaluation and benchmarking |
| **batch_process** | `agentical.tools.ai_ml` | Python | Large-scale data processing |
| **csv_parser** | `agentical.tools.ai_ml` | Pandas | Advanced CSV parsing with validation |
| **pdf_processor** | `agentical.tools.ai_ml` | OCR libraries | PDF text extraction and analysis |
| **image_analyzer** | `agentical.tools.ai_ml` | Computer vision | Image analysis capabilities |

### Tool Categories

#### Development Tools
- `filesystem`, `git`, `github`, `jupyter`, `shadcn_ui`, `magic`, `dart`

#### Data Analysis  
- `ptolemies`, `context7`, `bayes`, `crawl4ai`, `vector_store`, `csv_parser`

#### External Services
- `fetch`, `calendar`, `stripe`, `github`

#### Scientific Computing
- `solver_z3`, `solver_pysat`, `bayes`, `model_evaluator`

#### Infrastructure
- `memory`, `surrealdb`, `logfire`, `sequentialthinking`, `registry`

---

## 🔄 Workflow Types

### Standard Workflow Types

| Workflow Type | Description | Use Cases |
|---------------|-------------|-----------|
| **sequential** | Linear step-by-step execution | Simple automation, data pipelines |
| **parallel** | Concurrent execution of independent steps | Batch processing, multi-agent coordination |
| **conditional** | Branching logic based on conditions | Decision trees, adaptive workflows |
| **loop** | Iterative execution with break conditions | Data processing, optimization loops |
| **pipeline** | Data transformation pipeline | ETL processes, ML pipelines |

### Advanced Workflow Types

| Workflow Type | Description | Use Cases |
|---------------|-------------|-----------|
| **agent_feedback** | Agent-to-agent communication loops | Multi-agent collaboration |
| **handoff** | Task transfer between agents | Specialized task routing |
| **human_loop** | Human-in-the-loop decision points | Approval workflows, manual validation |
| **self_feedback** | Agent self-reflection and improvement | Learning systems, optimization |
| **versus** | Competitive agent execution | A/B testing, competitive analysis |

### Step Types

| Step Type | Description | Parameters |
|-----------|-------------|------------|
| **agent_task** | Execute task using specific agent | `agent_id`, `task_parameters` |
| **tool_execution** | Direct tool execution | `tool_name`, `tool_parameters` |
| **condition** | Conditional branching | `condition_expression`, `true_path`, `false_path` |
| **loop** | Iterative execution | `condition`, `max_iterations`, `break_condition` |
| **parallel** | Concurrent step execution | `steps[]`, `wait_for_all` |
| **wait** | Delay or wait for condition | `duration`, `condition` |
| **webhook** | External webhook call | `url`, `method`, `payload` |
| **script** | Custom script execution | `script_content`, `language` |
| **human_input** | Request human intervention | `prompt`, `input_type`, `validation` |
| **data_transform** | Data transformation step | `input_schema`, `output_schema`, `transform_logic` |

---

## 🤖 Created Agents

### 1. SuperAgent
- **Type**: `super`
- **Purpose**: Meta-coordinator for complex multi-agent workflows
- **Status**: ✅ Production Ready
- **Tools**: All 26 MCP servers, Ptolemies knowledge base
- **Workflows**: All types, specializing in `agent_feedback`, `handoff`
- **Capabilities**:
  - Multi-agent orchestration
  - Customer interface coordination
  - Tool routing and selection
  - Knowledge orchestration via Ptolemies
  - Complex multimodal operations
- **Performance**: 10 concurrent executions, 2GB memory limit

### 2. CodifierAgent  
- **Type**: `codifier`
- **Purpose**: Documentation, logging, and knowledge codification
- **Status**: ✅ Production Ready
- **Tools**: `filesystem`, `git`, `ptolemies-mcp`, `magic-mcp`
- **Workflows**: `sequential`, `pipeline`, `self_feedback`
- **Capabilities**:
  - API documentation generation
  - Code documentation and comments
  - Process documentation and runbooks
  - Knowledge base management
  - Content standardization
  - Information architecture
- **Document Types**: API docs, technical specs, user manuals, changelogs

### 3. IOAgent
- **Type**: `io` 
- **Purpose**: Inspection, observation, and monitoring
- **Status**: ✅ Production Ready
- **Tools**: `logfire-mcp`, `memory`, `fetch`, `surrealdb-mcp`
- **Workflows**: `loop`, `conditional`, `parallel`
- **Capabilities**:
  - System monitoring and health checks
  - Application performance observation
  - Infrastructure inspection
  - Log monitoring and alerting
  - Real-time data collection
  - Anomaly detection
- **Monitoring Scopes**: System, application, network, database, security

### 4. PlaybookAgent
- **Type**: `playbook`
- **Purpose**: Strategic execution and playbook management
- **Status**: ✅ Production Ready  
- **Tools**: `taskmaster-ai`, `context7-mcp`, `sequentialthinking`
- **Workflows**: All types, especially `human_loop`, `conditional`
- **Capabilities**:
  - Playbook creation and management
  - Strategic execution planning
  - Workflow orchestration
  - Step-by-step validation
  - Dynamic adaptation
  - Multi-agent orchestration
- **Execution Modes**: Sequential, parallel, conditional, interactive, automated

### 5. CodeAgent
- **Type**: `code`
- **Purpose**: Software development and programming tasks
- **Status**: ✅ Production Ready
- **Tools**: `git`, `github`, `filesystem`, `dart-mcp`, `jupyter-mcp`, `browser-tools-mcp`, `magic-mcp`, `sequentialthinking`
- **Workflows**: `sequential`, `parallel`, `self_feedback`, `conditional`
- **Capabilities**:
  - Multi-language code generation with framework support
  - Advanced code refactoring and optimization
  - Automated code review and quality assessment
  - Test generation with high coverage targets
  - Comprehensive documentation generation
  - Security vulnerability detection and recommendations
  - Performance bottleneck identification
  - Code complexity analysis and metrics
  - Design pattern application and best practices
- **Supported Languages**: 20+ programming languages including Python, JavaScript, TypeScript, Java, C#, C++, Rust, Go, and more
- **Integration**: Full Git workflow support, IDE integration ready, CI/CD pipeline compatible

---

## 📋 Planned Agents

### Development & DevOps Agents

#### 1. CodeAgent
- **Type**: `code`
- **Purpose**: Software development and programming tasks
- **Status**: ✅ Production Ready
- **Tools**: `git`, `github`, `filesystem`, `dart-mcp`, `jupyter-mcp`, `browser-tools-mcp`, `magic-mcp`, `sequentialthinking`
- **Workflows**: `sequential`, `parallel`, `self_feedback`, `conditional`
- **Capabilities**:
  - Multi-language code generation (Python, JavaScript, TypeScript, Java, etc.)
  - Intelligent code refactoring and optimization
  - Automated code review with actionable feedback
  - Comprehensive test suite generation
  - API and inline documentation generation
  - Security vulnerability scanning
  - Performance analysis and optimization
  - Git workflow automation
  - Design pattern application
  - Legacy code modernization
- **Supported Languages**: Python, JavaScript, TypeScript, Java, C#, C++, Rust, Go, PHP, Ruby, Swift, Kotlin, Scala, R, SQL, HTML, CSS, Shell, YAML, JSON, Markdown
- **Performance**: 5 concurrent executions, 1GB memory limit

#### 2. DevOpsAgent
- **Type**: `devops`
- **Purpose**: Infrastructure, deployment, and operations
- **Status**: ⏳ Planned
- **Planned Tools**: `fetch`, `logfire-mcp`, `surrealdb-mcp`, external cloud APIs
- **Planned Workflows**: `pipeline`, `conditional`, `loop`
- **Planned Capabilities**:
  - CI/CD pipeline management
  - Infrastructure provisioning
  - Container orchestration
  - Monitoring and alerting
  - Incident response
  - Capacity planning

#### 3. TesterAgent
- **Type**: `tester`
- **Purpose**: Testing, QA, and validation tasks
- **Status**: ⏳ Planned
- **Planned Tools**: `browser-tools-mcp`, `github`, `jupyter-mcp`
- **Planned Workflows**: `parallel`, `loop`, `conditional`
- **Planned Capabilities**:
  - Automated test generation
  - Test execution coordination
  - Performance testing
  - Security testing
  - API testing
  - User interface testing

### Data & Analytics Agents

#### 4. DataScienceAgent
- **Type**: `data_science`
- **Purpose**: Data analysis, ML, and statistical tasks
- **Status**: ⏳ Planned
- **Planned Tools**: `vector_store`, `model_evaluator`, `csv_parser`, `jupyter-mcp`
- **Planned Workflows**: `pipeline`, `loop`, `parallel`
- **Planned Capabilities**:
  - Data preprocessing and cleaning
  - Statistical analysis
  - Machine learning model training
  - Feature engineering
  - Model evaluation and validation
  - Visualization generation

#### 5. DbaAgent
- **Type**: `dba`
- **Purpose**: Database administration and optimization
- **Status**: ⏳ Planned
- **Planned Tools**: `surrealdb-mcp`, `logfire-mcp`, `memory`
- **Planned Workflows**: `conditional`, `loop`, `pipeline`
- **Planned Capabilities**:
  - Query optimization
  - Performance monitoring
  - Index management
  - Backup and recovery
  - Security auditing
  - Capacity planning

#### 6. ResearchAgent
- **Type**: `research`
- **Purpose**: Research, analysis, and knowledge synthesis
- **Status**: ⏳ Planned
- **Planned Tools**: `ptolemies-mcp`, `crawl4ai-mcp`, `fetch`, `bayes-mcp`
- **Planned Workflows**: `sequential`, `pipeline`, `self_feedback`
- **Planned Capabilities**:
  - Literature review and analysis
  - Data collection and synthesis
  - Hypothesis generation
  - Knowledge graph construction
  - Citation management
  - Report generation

### Cloud & Infrastructure Agents

#### 7. GcpAgent
- **Type**: `gcp`
- **Purpose**: Google Cloud Platform services and management
- **Status**: ⏳ Planned
- **Planned Tools**: `fetch`, `logfire-mcp`, Google Cloud APIs
- **Planned Workflows**: `conditional`, `pipeline`, `parallel`
- **Planned Capabilities**:
  - Resource provisioning
  - Service management
  - Cost optimization
  - Security configuration
  - Monitoring setup
  - Compliance checking

#### 8. PulumiAgent
- **Type**: `pulumi`
- **Purpose**: Infrastructure as code with Pulumi
- **Status**: ⏳ Planned
- **Planned Tools**: `git`, `filesystem`, Pulumi APIs
- **Planned Workflows**: `pipeline`, `conditional`, `sequential`
- **Planned Capabilities**:
  - Infrastructure definition
  - Deployment orchestration
  - State management
  - Resource tracking
  - Cost analysis
  - Compliance validation

### Security & Compliance Agents

#### 9. InfoSecAgent
- **Type**: `infosec`
- **Purpose**: Security analysis and threat assessment
- **Status**: ⏳ Planned
- **Planned Tools**: `fetch`, `logfire-mcp`, security scanning tools
- **Planned Workflows**: `parallel`, `conditional`, `loop`
- **Planned Capabilities**:
  - Vulnerability scanning
  - Penetration testing
  - Threat assessment
  - Security auditing
  - Compliance checking
  - Incident response

#### 10. LegalAgent
- **Type**: `legal`
- **Purpose**: Legal document analysis and compliance
- **Status**: ⏳ Planned
- **Planned Tools**: `pdf_processor`, `ptolemies-mcp`, `fetch`
- **Planned Workflows**: `sequential`, `pipeline`, `human_loop`
- **Planned Capabilities**:
  - Contract analysis
  - Compliance monitoring
  - Risk assessment
  - Document review
  - Legal research
  - Regulatory tracking

### User Experience & Testing Agents

#### 11. UxAgent
- **Type**: `ux`
- **Purpose**: User experience design and analysis
- **Status**: ⏳ Planned
- **Planned Tools**: `browser-tools-mcp`, `image_analyzer`, `fetch`
- **Planned Workflows**: `human_loop`, `sequential`, `parallel`
- **Planned Capabilities**:
  - User interface analysis
  - Accessibility testing
  - Performance analysis
  - User journey mapping
  - A/B testing coordination
  - Design optimization

#### 12. UatAgent
- **Type**: `uat`
- **Purpose**: User acceptance testing coordination
- **Status**: ⏳ Planned
- **Planned Tools**: `browser-tools-mcp`, `taskmaster-ai`, `github`
- **Planned Workflows**: `human_loop`, `parallel`, `conditional`
- **Planned Capabilities**:
  - Test case management
  - User coordination
  - Feedback collection
  - Defect tracking
  - Acceptance criteria validation
  - Release coordination

### External Integration Agents

#### 13. GitHubAgent
- **Type**: `github`
- **Purpose**: GitHub operations and repository management
- **Status**: ⏳ Planned
- **Planned Tools**: `github`, `git`, `filesystem`
- **Planned Workflows**: `conditional`, `parallel`, `sequential`
- **Planned Capabilities**:
  - Repository management
  - Pull request automation
  - Issue tracking
  - Release management
  - Code review coordination
  - CI/CD integration

#### 14. TokenAgent
- **Type**: `token`
- **Purpose**: Token management and analysis
- **Status**: ⏳ Planned
- **Planned Tools**: `fetch`, blockchain APIs, `logfire-mcp`
- **Planned Workflows**: `loop`, `conditional`, `parallel`
- **Planned Capabilities**:
  - Token analysis
  - Transaction monitoring
  - Wallet management
  - DeFi integration
  - Compliance tracking
  - Risk assessment

---

## 🔗 Integration Capabilities

### Agent-to-Agent Communication
- **Registry System**: Centralized agent discovery and coordination
- **Message Passing**: Structured communication between agents
- **Shared Memory**: Context preservation across agent interactions
- **Event System**: Pub/sub for agent coordination

### Tool Integration Patterns
- **MCP Protocol**: Standardized tool access via Model Context Protocol
- **Dynamic Discovery**: Runtime tool discovery and registration
- **Tool Chaining**: Sequential tool execution with data passing
- **Parallel Execution**: Concurrent tool operations for performance

### Database Integration
- **SurrealDB**: Multi-model database for complex data relationships
- **Vector Storage**: Embeddings and similarity search capabilities
- **Knowledge Graph**: Structured knowledge representation
- **Time Series**: Performance and monitoring data storage

### External Service Integration
- **API Gateway**: Unified external service access
- **Authentication**: OAuth, API key, and token management
- **Rate Limiting**: Service-specific rate limiting and quota management
- **Circuit Breakers**: Fault tolerance for external dependencies

---

## 📊 Performance & Scaling

### Agent Performance Metrics

| Agent Type | Max Concurrent | Memory Limit | CPU Limit | Timeout |
|------------|----------------|--------------|-----------|---------|
| SuperAgent | 10 | 2GB | 90% | 600s |
| CodifierAgent | 5 | 1GB | 80% | 300s |
| IOAgent | 8 | 1GB | 70% | 180s |
| PlaybookAgent | 6 | 1.5GB | 85% | 450s |

### Tool Performance Thresholds
- **Execution Warning**: 30 seconds
- **Execution Critical**: 120 seconds  
- **Success Rate Warning**: 85%
- **Success Rate Critical**: 70%
- **Concurrent Usage Warning**: 80%
- **Concurrent Usage Critical**: 95%

### Scaling Configuration
- **Max Concurrent Workflows**: 10
- **Max MCP Connections**: 20
- **Tool Cache TTL**: 30 minutes
- **Health Check Interval**: 30 seconds
- **Auto-Reconnect**: Enabled

### Resource Management
- **Memory Management**: Automatic cleanup and optimization
- **Connection Pooling**: Efficient resource utilization
- **Load Balancing**: Intelligent distribution across agents
- **Fault Tolerance**: Graceful degradation and recovery

---

## 🎯 Future Roadmap

### Short Term (Q3 2025)
- Complete implementation of all 15 planned agents
- Enhanced workflow orchestration capabilities
- Advanced tool chaining and composition
- Improved observability and monitoring

### Medium Term (Q4 2025 - Q1 2026)
- Multi-tenant agent isolation
- Advanced security and compliance features
- Real-time collaboration capabilities
- Enhanced learning and adaptation

### Long Term (Q2 2026+)
- Distributed agent deployment
- Advanced AI reasoning capabilities
- Enterprise-grade security features
- Industry-specific agent specializations

---

*For detailed implementation guides, API references, and examples, refer to the [technical documentation](docs/technical-documentation.md) and [API reference](docs/api-reference.md).*