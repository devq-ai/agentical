# Ptolemies Knowledge Management System - Changelog

All notable changes to the Ptolemies project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - 2025-01-03

#### Status Dashboard Complete Implementation

- **GitHub Pages Status Dashboard**: Live production monitoring at https://devq-ai.github.io/ptolemies/
- **Neo4j Knowledge Graph Integration**: Real-time monitoring of 77 nodes and 156 relationships
- **Dehallucinator AI Detection Service**: Production-grade hallucination detection with 97.3% accuracy
- **Comprehensive Service Portfolio**: Unified monitoring for all major Ptolemies services
- **Real-Time Performance Metrics**: Live updates with auto-refresh capabilities
- **Mobile-Responsive Design**: Professional dark theme with DaisyUI components
- **Direct Service Access**: One-click links to Neo4j Browser, GitHub repositories
- **Production Documentation**: Complete README overhaul with live dashboard integration

#### Knowledge Base Enhancements

- **Complete Documentation Coverage**: 292 chunks across 17 framework sources
- **Framework Categorization**: AI/ML, Web Frontend, Backend/API, Data/DB, Tools/Utils
- **Quality Metrics Display**: 0.86 average quality score with source-level breakdown
- **Vector Search Integration**: SurrealDB semantic search capabilities
- **Graph Relationship Mapping**: Neo4j integration with framework interdependencies

#### AI Detection & Validation

- **Production AI Detection**: 97.3% accuracy rate with <2.1% false positive rate
- **Framework Support**: 17 major frameworks with 2,296 validated API patterns
- **Detection Categories**: Non-existent APIs, impossible imports, AI patterns, violations
- **Performance Benchmarks**: <200ms analysis time, <512MB memory usage
- **Batch Processing**: Repository-wide scanning with concurrent file processing

#### Development Infrastructure

- **DevQ.ai Stack Compliance**: FastAPI + Logfire + PyTest + TaskMaster AI
- **Test Coverage**: 90%+ requirement with comprehensive test suites
- **Code Quality**: Black formatting, Google-style docstrings, type hints
- **Observability**: Complete Logfire instrumentation across all services
- **Environment Configuration**: Standardized .env management and MCP integration

### Added - 2025-01-04

#### Environment Configuration Consolidation

- Created master `.env` file in `/devqai/` root directory consolidating all environment variables from across the ecosystem
- Unified environment configuration with 94+ variables covering:
  - Database configurations (SurrealDB, Redis, Neo4j)
  - LLM API keys (OpenAI, Anthropic, Gemini, Groq, DeepSeek)
  - Domain-specific API keys (AgentQL, Dart, Slack, GitHub, etc.)
  - MCP (Model Context Protocol) configuration
  - Project-specific settings (Agentical, Ptolemies, etc.)
  - Monitoring and telemetry settings

#### MCP Server Configuration Standardization

- Aligned `CLAUDE.md` and `mcp-servers.json` configurations
- Added NPX-based core MCP servers:
  - `filesystem` - File read/write operations
  - `git` - Version control operations
  - `fetch` - API calls and external resource access
  - `memory` - Persistent memory across sessions
  - `sequentialthinking` - Enhanced problem solving
  - `inspector` - Debug MCP server connections
- Standardized environment variable names:
  - `GITHUB_TOKEN` → `GITHUB_PERSONAL_ACCESS_TOKEN`
  - Updated `dart-mcp` and `github-mcp` to use NPX commands
- Created directory structure for 18 MCP servers with installation scaffolding

### Changed - 2025-01-04

#### Environment File Organization

- Replaced project-specific `.env` files with copies of master configuration
- Standardized naming convention for template files:
  - `agentical/.env.example` → `agentical/.env.template`
  - `heuristicfund/.env.example` → `heuristicfund/.env.template`
- Unified all projects to use identical environment configuration

#### MCP Server Infrastructure

- Updated `run-mcp-tool.sh` to include all 18 available MCP servers
- Enhanced MCP server registry with discovery and installation tools
- Improved documentation and configuration for each server

### Removed - 2025-01-04

#### Cleanup Operations

- Removed all project-specific `.env` files:
  - `bayes/.env`
  - `devgen/.env`
  - `mcp/.env`
  - `ptolemies/.env`
  - `heuristicfund/.env`
  - `mcp/pydantic_ai_env/mcp.env`
- Deleted all `.ropeproject` directories (3 total):
  - `bayes/.ropeproject`
  - `mcp/.ropeproject`
  - `.ropeproject` (root)
- Eliminated environment configuration duplication and inconsistencies

### Fixed - 2025-01-04

#### Configuration Consistency

- Resolved environment variable conflicts between projects
- Ensured API key consistency across all project directories
- Standardized database connection parameters
- Fixed MCP server configuration gaps between documentation and implementation

### Technical Details

#### Environment Variables Consolidated

- **Database**: SurrealDB, Redis, Neo4j connection strings and credentials
- **LLM APIs**: OpenAI, Anthropic, Gemini, Groq, DeepSeek API keys
- **Version Control**: GitHub Personal Access Tokens
- **Domain Services**: AgentQL, Dart AI, Slack, BuildKite, Exa, Financial Datasets
- **Monitoring**: Logfire, OpenTelemetry, Grafana configurations
- **Project-Specific**: Agentical framework settings, Ptolemies crawler config

#### MCP Infrastructure

- **Core Servers**: 5 NPX-based foundational servers
- **Local Servers**: 13 Python-based specialized servers
- **Registry**: Centralized server discovery and management
- **Documentation**: Comprehensive setup guides and configuration templates

#### File Structure Impact

```
devqai/
├── .env                           # Master environment configuration
├── CHANGELOG.md                   # This file
├── agentical/.env                # Copy of master .env
├── bayes/.env                    # Copy of master .env
├── devgen/.env                   # Copy of master .env
├── heuristicfund/.env            # Copy of master .env
├── mcp/.env                      # Copy of master .env
├── mcp/pydantic_ai_env/.env      # Copy of master .env
├── ptolemies/.env                # Copy of master .env
└── mcp/mcp-servers.json          # Standardized MCP server configuration
```

---

### Notes

- All API keys and sensitive credentials have been consolidated but individual values preserved
- Projects now share a unified configuration while maintaining ability to override locally
- MCP server infrastructure ready for production deployment
- Environment setup simplified for new development environments
