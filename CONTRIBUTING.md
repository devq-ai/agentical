# Contributing to Ptolemies Knowledge Management System

Thank you for your interest in contributing to Ptolemies! We're excited to work with you and appreciate your help in making this knowledge management system better.

**Ptolemies** is DevQ.ai's advanced knowledge management and analytics platform featuring real-time monitoring, AI detection, and comprehensive documentation processing.

🚀 **[Live Status Dashboard](https://devq-ai.github.io/ptolemies/)** - View current system status and metrics

## 🤝 Our Collaborative Approach

We're a **PR-friendly team** that values collaboration:

- ✅ **We review PRs quickly** - Usually within hours, not days
- ✅ **We're super reactive** - Expect fast feedback and engagement
- ✅ **We sometimes take over PRs** - If your contribution is valuable but needs cleanup, we might jump in to help finish it
- ✅ **We're open to all contributions** - From bug fixes to major features

**We don't mind AI-generated code**, but we do expect you to:

- ✅ **Review and understand** what the AI generated
- ✅ **Test the code thoroughly** before submitting
- ✅ **Ensure it's well-written** and follows our patterns
- ❌ **Don't submit "AI slop"** - untested, unreviewed AI output

> **Why this matters**: We spend significant time reviewing PRs. Help us help you by submitting quality contributions that save everyone time!

## 🚀 Quick Start for Contributors

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/ptolemies.git
cd ptolemies
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
```

### 2. Create a Feature Branch

**Important**: Always target the `main` branch for Ptolemies:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes

Follow our development guidelines below and ensure compliance with DevQ.ai standards:

- Use **FastAPI** for all web services
- Include **PyTest** with 90%+ coverage
- Add **Logfire** instrumentation for all operations
- Integrate **TaskMaster AI** for complex workflows
- **Knowledge Base**: Maintain 292+ documentation chunks
- **AI Detection**: Preserve 97.3%+ accuracy standards
- **Graph Database**: Ensure Neo4j integration consistency

### 4. Test Everything Yourself

**Before submitting your PR**, ensure:

```bash
# Run all tests with coverage
pytest tests/ --cov=src/ --cov-report=html --cov-fail-under=90

# Check formatting with Black
black --check src/ tests/

# Fix formatting if needed
black src/ tests/

# Run linting
ruff check src/ tests/

# Type checking
mypy src/
```

### 5. Create a Changeset

**Required for most changes**:

```bash
# For Python projects, we manually create changelog entries
echo "## [Version] - $(date +%Y-%m-%d)" >> CHANGELOG.md
echo "- Your change description" >> CHANGELOG.md
```

See the [Changelog Guidelines](#changelog-guidelines) below for details.

### 6. Submit Your PR

- Target the `main` branch
- Write a clear description
- Reference any related issues
- Include status dashboard impact assessment

## 📋 Development Guidelines

### Branch Strategy

- **`main`**: Production-ready code - **target this for PRs**
- **Feature branches**: `feature/description` or `fix/description`
- **Status branch**: `status` for GitHub Pages deployment (automated)

### Code Quality Standards (DevQ.ai Requirements)

1. **FastAPI Foundation** - All web services must use FastAPI
2. **PyTest Build-to-Test** - 90%+ coverage required before merging
3. **Logfire Observability** - Every operation must be instrumented
4. **TaskMaster AI Integration** - Use for task breakdown and management
5. **Pydantic AI** - Required for agent implementations
6. **Google-style docstrings** for all Python functions
7. **Black formatting** with 88 character line length
8. **Type hints** required for all function signatures

### Testing Requirements

Your PR **must pass all CI checks**:

- ✅ **Unit tests**: `pytest tests/ --cov-fail-under=90`
- ✅ **Integration tests**: `pytest tests/integration/`
- ✅ **Format check**: `black --check src/ tests/`
- ✅ **Linting**: `ruff check src/ tests/`
- ✅ **Type checking**: `mypy src/`
- ✅ **Security scan**: `bandit -r src/`

**Test your changes locally first** - this saves review time and shows you care about quality.

## 📦 Changelog Guidelines

We maintain a CHANGELOG.md file to track all notable changes to the project.

### When to Update the Changelog

**Always update for**:

- ✅ New features
- ✅ Bug fixes
- ✅ Breaking changes
- ✅ Performance improvements
- ✅ User-facing documentation updates
- ✅ Dependency updates that affect functionality
- ✅ **Knowledge base enhancements**
- ✅ **AI detection improvements**
- ✅ **Graph database schema changes**
- ✅ **Status dashboard updates**
- ✅ **TaskMaster AI workflow additions**

**Skip changelog for**:

- ❌ Internal documentation only
- ❌ Test-only changes
- ❌ Code formatting/linting
- ❌ Development tooling that doesn't affect users

### How to Update the Changelog

1. **Add your entry to CHANGELOG.md**:

   ```markdown
   ## [Unreleased]

   ### Added

   - Neo4j graph monitoring with 77 nodes and 156 relationships
   - AI hallucination detection with 97.3% accuracy
   - Real-time status dashboard with GitHub Pages integration

   ### Fixed

   - FastAPI endpoint validation for knowledge base queries
   - Vector search performance optimization

   ### Changed

   - Enhanced documentation processing to 292 chunks
   - Upgraded status monitoring with live metrics
   ```

2. **Follow semantic versioning**:

   - **Major**: Breaking changes
   - **Minor**: New features
   - **Patch**: Bug fixes, docs, performance improvements

3. **Include TaskMaster AI task reference** (if applicable):

   ```markdown
   ### Added

   - Neo4j status integration [TaskMaster: TASK-11.3]
   - Dehallucinator service monitoring [TaskMaster: TASK-11.6]
   ```

### Commit Message Format

Follow conventional commits:

```bash
# Format: <type>(<scope>): <subject>

# Examples:
feat(dashboard): add Neo4j graph monitoring with real-time metrics
fix(detection): improve AI hallucination accuracy to 97.3%
test(knowledge): add 95% coverage for knowledge base processing
docs(readme): update production status and live dashboard links
```

## 🔧 Development Setup

### Prerequisites

- Python 3.12+
- pip or poetry
- Docker (for SurrealDB and Redis)
- Node.js 18+ (for MCP servers)

### Environment Setup

1. **Copy environment template**:

   ```bash
   cp .env.example .env
   ```

2. **Add required API keys and configuration**:

   ```bash
   # Core Configuration
   PROJECT_NAME=ptolemies
   PROJECT_VERSION=2.1.0
   STATUS_DASHBOARD_URL=https://devq-ai.github.io/ptolemies/

   # FastAPI & Logfire (REQUIRED)
   LOGFIRE_TOKEN=pylf_v1_us_...
   LOGFIRE_PROJECT_NAME=ptolemies
   LOGFIRE_SERVICE_NAME=ptolemies-api

   # TaskMaster AI (REQUIRED)
   ANTHROPIC_API_KEY=sk-ant-...
   MODEL=claude-3-7-sonnet-20250219

   # Neo4j Graph Database (REQUIRED)
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=ptolemies
   NEO4J_BROWSER_URL=http://localhost:7475

   # SurrealDB Vector Database (REQUIRED)
   SURREALDB_URL=ws://localhost:8000/rpc
   SURREALDB_USERNAME=root
   SURREALDB_PASSWORD=root

   # AI Detection Service
   DEHALLUCINATOR_ACCURACY_RATE=97.3
   DEHALLUCINATOR_FRAMEWORKS_SUPPORTED=17
   ```

3. **Start required services**:

   ```bash
   # Start SurrealDB
   docker run --rm -p 8000:8000 surrealdb/surrealdb:latest start

   # Start Neo4j
   docker run --rm -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/ptolemies \
     neo4j:latest

   # Start Redis (if using local)
   docker run --rm -p 6379:6379 redis:alpine
   ```

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=src/ --cov-report=html --cov-fail-under=90

# Run tests in watch mode
pytest-watch

# Run specific test file
pytest tests/test_knowledge_base.py -v

# Run integration tests only
pytest tests/integration/ -v

# Run AI detection tests
pytest tests/test_dehallucinator.py -v

# Run with Logfire monitoring (for debugging)
LOGFIRE_SEND_TO_LOGFIRE=true pytest tests/

# Generate coverage report
pytest tests/ --cov=src/ --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Code Formatting & Quality

We use Black for formatting and Ruff for linting:

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/

# Lint code
ruff check src/ tests/

# Fix linting issues
ruff check --fix src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/

# All quality checks (run before PR)
make quality  # or ./scripts/quality-check.sh
```

## 📝 PR Guidelines

### Before Submitting

- [ ] **Target the `main` branch**
- [ ] **Test everything locally** with 90%+ coverage
- [ ] **Run the full test suite** including integration tests
- [ ] **Check code formatting** with Black and Ruff
- [ ] **Type check** with mypy
- [ ] **Update CHANGELOG.md** (if needed)
- [ ] **Verify Logfire instrumentation** is in place
- [ ] **Check TaskMaster AI integration** for complex features
- [ ] **Test status dashboard integration** (if applicable)
- [ ] **Verify Neo4j/SurrealDB compatibility** (if applicable)
- [ ] **Check AI detection accuracy** (if applicable)
- [ ] **Re-read your changes** - ensure they're clean and well-thought-out

### PR Description Template

```markdown
## Description

Brief description of what this PR does.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Knowledge base enhancement
- [ ] AI detection improvement
- [ ] Graph database update
- [ ] Status dashboard feature
- [ ] TaskMaster AI workflow

## DevQ.ai Compliance Checklist

- [ ] Uses FastAPI for web services
- [ ] Has 90%+ test coverage
- [ ] Includes Logfire instrumentation
- [ ] Integrates TaskMaster AI (if applicable)
- [ ] Maintains knowledge base quality (292+ chunks)
- [ ] Preserves AI detection accuracy (97.3%+)
- [ ] Compatible with Neo4j graph schema
- [ ] Follows Black formatting (88 char limit)
- [ ] Has Google-style docstrings
- [ ] Includes type hints

## Ptolemies-Specific Checklist

- [ ] Knowledge base changes maintain 0.86+ quality score
- [ ] Graph database changes preserve 77 nodes structure
- [ ] AI detection changes maintain 17 framework support
- [ ] Status dashboard reflects new metrics (if applicable)
- [ ] Documentation chunks remain at 292+ total

## Testing

- [ ] I have tested this locally
- [ ] All existing tests pass
- [ ] I have added tests achieving 90%+ coverage
- [ ] Integration tests pass
- [ ] Logfire monitoring verified
- [ ] Knowledge base tests pass (if applicable)
- [ ] AI detection accuracy maintained (if applicable)
- [ ] Graph database queries work (if applicable)
- [ ] Status dashboard displays correctly (if applicable)

## Changelog

- [ ] I have updated CHANGELOG.md
- [ ] TaskMaster AI task reference included (if applicable)

## Additional Notes

Any additional context or notes for reviewers.
```

### What We Look For

✅ **Good PRs**:

- Clear, focused changes aligned with DevQ.ai standards
- 90%+ test coverage with PyTest
- Comprehensive Logfire instrumentation
- TaskMaster AI integration for complex workflows
- Proper type hints and Google-style docstrings
- Black-formatted code (88 char limit)
- Updated CHANGELOG.md with proper versioning
- Self-reviewed code

❌ **Avoid**:

- Massive PRs that change everything
- Code without 90%+ test coverage
- Missing Logfire instrumentation
- Non-FastAPI web services
- Missing type hints or docstrings
- Formatting issues (not Black-compliant)
- Missing changelog entries for user-facing changes
- AI-generated code that wasn't reviewed and tested

## 🏗️ Project Structure

```
ptolemies/
├── src/                   # Main source code
│   ├── api/              # FastAPI endpoints and routers
│   ├── core/             # Core utilities and shared code
│   ├── models/           # Pydantic models and schemas
│   ├── services/         # Business logic and services
│   └── search/           # Vector search and semantic queries
├── dehallucinator/        # AI hallucination detection service
├── neo4j/                # Graph database setup and queries
├── surrealdb/            # Vector database and storage
├── status-page/          # GitHub Pages status dashboard
│   ├── src/              # SvelteKit dashboard application
│   └── static/           # Static assets
├── tests/                 # Test files (90%+ coverage required)
│   ├── unit/             # Unit tests for individual components
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── crawler/              # Documentation crawling system
├── scripts/              # Development and deployment scripts
├── docs/                 # Documentation and reports
├── mcp/                  # MCP server implementations
└── .github/              # GitHub Actions workflows
```

### Key Areas for Contribution

- **Knowledge Base**: `src/search/` - Vector search and semantic processing
- **AI Detection**: `dehallucinator/` - Hallucination detection algorithms
- **Graph Database**: `neo4j/` - Knowledge graph and relationships
- **Status Dashboard**: `status-page/` - Real-time monitoring interface
- **API Endpoints**: `src/api/` - FastAPI routers and endpoints
- **Documentation Processing**: `crawler/` - Knowledge base crawling
- **Service Logic**: `src/services/` - Core business logic
- **Testing**: `tests/` - Comprehensive test coverage
- **MCP Servers**: `mcp/` - Model Context Protocol servers

## 🐛 Reporting Issues

### Bug Reports

Include:

- Ptolemies version (current: 2.1.0)
- Python version (3.12+ required)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
- Logfire trace ID (if available)
- Knowledge base state (if applicable)
- Neo4j/SurrealDB status (if applicable)
- Status dashboard screenshot (if applicable)
- Test coverage report (if applicable)

### Feature Requests

Include:

- Clear description of the feature
- Use case/motivation
- How it fits within Ptolemies knowledge management system
- Impact on status dashboard metrics
- Proposed implementation approach
- Whether it requires:
  - Knowledge base schema changes
  - AI detection algorithm updates
  - Graph database modifications
  - Status dashboard enhancements
  - TaskMaster AI workflows
  - FastAPI endpoints
  - Logfire monitoring enhancements
- Willingness to contribute

## 💬 Getting Help

- **Live Status**: [Ptolemies Dashboard](https://devq-ai.github.io/ptolemies/)
- **Issues**: [GitHub Issues](https://github.com/devq-ai/ptolemies/issues)
- **Discussions**: [GitHub Discussions](https://github.com/devq-ai/ptolemies/discussions)
- **Documentation**: [DevQ.ai Docs](https://docs.devq.ai)
- **Discord**: [Join DevQ.ai community](https://discord.gg/devqai)

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## 🚀 DevQ.ai Ecosystem Tools

When contributing, you have access to these powerful tools:

### Core Development Stack

- **FastAPI**: Web framework for all services
- **PyTest**: Testing with 90%+ coverage requirement
- **Logfire**: Observability and monitoring
- **TaskMaster AI**: Task decomposition and management
- **Pydantic AI**: Agent development framework

### Knowledge & Context Tools

- **Ptolemies Knowledge Base**: 292 documentation chunks with vector search
- **Neo4j Graph Database**: 77 nodes with framework relationships
- **AI Detection Service**: 97.3% accuracy across 17 frameworks
- **SurrealDB Vector Storage**: Semantic search capabilities
- **Context7**: Redis-backed contextual reasoning

### Development Workflow

1. **Verify tools**: Run `./scripts/tools-verification.sh`
2. **Plan with TaskMaster**: Break down complex work
3. **Implement with FastAPI**: Follow standardized patterns
4. **Test with PyTest**: Achieve 90%+ coverage
5. **Monitor with Logfire**: Full observability
6. **Document thoroughly**: Google-style docstrings

---

**Thank you for contributing to Ptolemies!**

Your contributions help advance the DevQ.ai knowledge management ecosystem and make AI-driven development more powerful and accessible. Visit our [live status dashboard](https://devq-ai.github.io/ptolemies/) to see the impact of your work in real-time!
