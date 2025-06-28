# Agentical - AI Agent Framework & Orchestration Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![VS Code Extension](https://img.shields.io/badge/VS%20Code-Extension-007ACC?style=flat&logo=visual-studio-code&logoColor=white)](https://marketplace.visualstudio.com/items?itemName=devq-ai.agentical-vscode)

**Agentical** is a comprehensive AI agent framework and orchestration platform that enables seamless multi-agent workflows, intelligent automation, and enterprise-grade CI/CD integration. Built with FastAPI, enhanced with real-time observability, and designed for production-scale deployments.

## 🎯 **Project Status: Agentical 1.0 (85% Complete)**

### **✅ Production-Ready Features**
- **15+ Specialized Agents**: Code, DevOps, GitHub, Research, Cloud, UX, Legal agents
- **Multi-Agent Orchestration**: 7 coordination strategies with real-time monitoring
- **VS Code Integration**: Full-featured extension with 15+ commands
- **CI/CD Integration**: GitHub Actions, Jenkins, GitLab CI with automated pipelines
- **Enterprise Infrastructure**: FastAPI + Logfire + PostgreSQL + Redis

### **🔄 Current Phase: Integration & Ecosystem (40% Complete)**
- ✅ **PB-006.1**: IDE Integration (VS Code Extension)
- ✅ **PB-006.2**: CI/CD Pipeline Integration (Multi-platform)
- 🔄 **Remaining**: Third-party connectors, Enterprise SSO (→ Agentical 2.0)

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.12+
- Node.js 18+ (for VS Code extension)
- Docker (optional)
- PostgreSQL or SurrealDB

### **Installation**

```bash
# Clone the repository
git clone https://github.com/devq-ai/agentical.git
cd agentical

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
cp .env.example .env
# Edit .env with your configuration

# Start the application
python main.py
```

### **VS Code Extension**
```bash
cd integrations/vscode
npm install
npm run compile
# Install extension: Ctrl+Shift+P > "Extensions: Install from VSIX"
```

### **Docker Deployment**
```bash
docker-compose up -d
```

---

## 📁 **Repository Structure**

### **🗂️ Root Directory (Essential Files Only)**
```
agentical/
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore patterns
├── .rules                        # DevQ.ai development rules
├── __init__.py                   # Python package initialization
├── CHANGELOG.md                  # Version history and changes
├── CLAUDE.md                     # Claude AI integration documentation
├── CONFIG.md                     # Configuration documentation
├── CONTRIBUTING.md               # Contribution guidelines
├── LICENSE.md                    # MIT license
├── README.md                     # This file
├── alembic.ini                   # Database migration configuration
├── main.py                       # FastAPI application entry point
├── pyproject.toml                # Python project configuration
├── pytest.ini                    # Test configuration
└── requirements.txt              # Python dependencies
```

### **🏗️ Organized Directory Structure**
```
agentical/
├── 📁 .claude/                   # Claude AI configuration
├── 📁 .github/                   # GitHub Actions workflows
├── 📁 .logfire/                  # Logfire observability credentials
├── 📁 agents/                    # AI Agent Implementations
│   ├── types/                    # Specialized agent types
│   ├── agent_registry.py         # Agent discovery and management
│   └── enhanced_base_agent.py    # Base agent architecture
│
├── 📁 api/                       # FastAPI REST API
│   └── v1/endpoints/             # API endpoint implementations
│
├── 📁 config/                    # Configuration Files
│   └── mcp-servers.json          # MCP server configuration
│
├── 📁 docker/                    # Docker Configuration
│   ├── Dockerfile                # Container build instructions
│   ├── docker-compose.yml        # Local development
│   ├── docker-compose.prod.yml   # Production deployment
│   └── docker-entrypoint.sh      # Container startup script
│
├── 📁 docs/                      # Documentation
│   ├── implementation/           # Implementation guides
│   │   ├── ADVANCED_AGENT_ECOSYSTEM_IMPLEMENTATION.md
│   │   ├── WORKFLOW_ENGINE_CORE_IMPLEMENTATION.md
│   │   └── ...
│   ├── project/                  # Project documentation
│   │   ├── PROJECT_STATUS_FINAL_1.0.md
│   │   ├── AGENTICAL_2.0_ROADMAP.md
│   │   └── ...
│   ├── status/                   # Status page documentation
│   │   ├── GITHUB_PAGES_SETUP.md
│   │   ├── STATUS_PAGE_SUMMARY.md
│   │   └── LOCAL_PREVIEW_GUIDE.md
│   ├── README.md                 # Documentation index
│   └── status.json               # Generated status data
│
├── 📁 scripts/                   # Utility Scripts
│   ├── generate_agentical_status.py  # Status page generator
│   ├── setup-github-pages.sh     # GitHub Pages setup
│   ├── serve-status-local.py     # Local development server
│   ├── create-local-preview.py   # Static preview generator
│   └── verify-status-setup.py    # Setup verification
│
├── 📁 workflows/                 # Workflow Engine & Orchestration
│   ├── engine/                   # Core workflow execution engine
│   ├── manager.py                # Workflow lifecycle management
│   └── registry.py               # Workflow discovery
│
├── 📁 core/                      # Core Framework Components
│   ├── exceptions.py             # Error handling
│   ├── logging.py                # Logfire observability
│   └── dependencies.py           # FastAPI dependencies
│
├── 📁 db/                        # Database & Persistence
│   ├── models/                   # SQLAlchemy models
│   └── repositories/             # Repository pattern
│
├── 📁 tests/                     # Comprehensive Test Suite
├── 📁 docs/                      # Documentation
├── 📁 examples/                  # Usage examples
└── main.py                       # Application entry point
```

---

## 🤖 **Agent Ecosystem**

### **Production Agents (15+)**

| Agent | Purpose | Capabilities | Status |
|-------|---------|--------------|--------|
| **CodeAgent** | Software Development | 21+ languages, testing, documentation | ✅ Production |
| **DevOpsAgent** | Infrastructure & Deployment | Multi-cloud, containers, IaC | ✅ Production |
| **GitHubAgent** | Repository Management | PRs, issues, analytics, automation | ✅ Production |
| **ResearchAgent** | Knowledge Discovery | Academic, web, competitive analysis | ✅ Production |
| **CloudAgent** | Multi-Cloud Operations | AWS, GCP, Azure cost optimization | ✅ Production |
| **UXAgent** | User Experience | Usability testing, design review | ✅ Production |
| **LegalAgent** | Legal Document Analysis | Contract review, compliance | ✅ Production |
| **DataScienceAgent** | Analytics & ML | Data processing, model training | ✅ Production |
| **SecurityAgent** | Security Analysis | Vulnerability scanning, compliance | ✅ Production |
| **TesterAgent** | Quality Assurance | Automated testing, test generation | ✅ Production |

### **Meta Agents**
- **SuperAgent**: Multi-agent coordination and orchestration
- **PlaybookAgent**: Strategic execution and workflow management
- **IOAgent**: System monitoring and observability

---

## 🔧 **Core Features**

### **Multi-Agent Orchestration**
```python
from agentical import SuperAgent, CodeAgent, DevOpsAgent

# Initialize agents
super_agent = SuperAgent()
code_agent = CodeAgent()
devops_agent = DevOpsAgent()

# Execute coordinated workflow
result = await super_agent.coordinate([
    code_agent.generate_code("FastAPI app with authentication"),
    code_agent.generate_tests("comprehensive test suite"),
    devops_agent.create_deployment_pipeline("production")
])
```

### **Workflow Engine**
```python
from agentical.workflows import WorkflowEngine

# Create and execute workflow
workflow = WorkflowEngine.create_workflow({
    "name": "CI/CD Pipeline",
    "type": "sequential",
    "steps": [
        {"agent": "code", "task": "generate_code"},
        {"agent": "devops", "task": "deploy_application"},
        {"agent": "github", "task": "create_pull_request"}
    ]
})

execution = await workflow.execute()
```

### **Real-time Monitoring**
```python
import logfire

# Observability built-in
with logfire.span("agent_execution"):
    result = await agent.execute_task(task_data)
    logfire.info("Task completed", result=result)
```

---

## 💻 **VS Code Integration**

### **Features**
- **Agent Pool Management**: Real-time agent status and monitoring
- **Code Generation**: AI-powered code generation with context awareness
- **Code Review**: Intelligent code review and optimization suggestions
- **Workflow Execution**: Direct workflow execution from IDE
- **DevOps Integration**: Deployment and infrastructure management
- **Real-time Updates**: WebSocket integration for live status updates

### **Commands**
- `Ctrl+Shift+G`: Generate code with AI
- `Ctrl+Shift+R`: Review selected code
- `Ctrl+Shift+X`: Execute workflow
- `Ctrl+Shift+D`: Open Agentical dashboard

---

## 🔄 **CI/CD Integration**

### **Supported Platforms**
- **GitHub Actions**: Workflow creation and management
- **Jenkins**: Pipeline automation and monitoring
- **GitLab CI**: Complete DevOps lifecycle
- **Azure DevOps**: Enterprise CI/CD integration
- **CircleCI, Travis CI, BuildKite**: Additional platform support

### **Features**
- **Automated Pipeline Creation**: Template-based pipeline generation
- **Real-time Monitoring**: Live pipeline status and progress tracking
- **Webhook Integration**: Event-driven status updates
- **Artifact Management**: Comprehensive artifact storage and retrieval
- **Security Scanning**: Integrated security and compliance checks

### **Example: GitHub Actions Integration**
```python
from agentical.integrations.cicd import GitHubActionsIntegration

github = GitHubActionsIntegration(token="your_token")

# Create deployment workflow
workflow_path = await github.create_workflow(
    owner="your-org",
    repo="your-repo",
    workflow_name="production-deploy",
    workflow_config={
        "name": "Production Deployment",
        "on": {"push": {"branches": ["main"]}},
        "jobs": {
            "deploy": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {"run": "docker build -t app:latest ."},
                    {"run": "kubectl apply -f k8s/"}
                ]
            }
        }
    }
)
```

---

## 📊 **API Reference**

### **Core Endpoints**

#### **Agents**
```http
GET    /api/v1/agents                    # List available agents
POST   /api/v1/agents/{id}/execute       # Execute agent task
GET    /api/v1/agents/{id}/status        # Get agent status
```

#### **Workflows**
```http
GET    /api/v1/workflows                 # List workflows
POST   /api/v1/workflows/execute         # Execute workflow
GET    /api/v1/workflows/{id}/status     # Get execution status
POST   /api/v1/workflows/{id}/cancel     # Cancel execution
```

#### **CI/CD Integration**
```http
POST   /api/v1/cicd/pipelines            # Create pipeline
POST   /api/v1/cicd/pipelines/{id}/trigger  # Trigger execution
GET    /api/v1/cicd/pipelines/{id}/logs      # Get logs
POST   /api/v1/cicd/webhooks/{platform}     # Handle webhooks
```

### **Authentication**
```bash
# API Key Authentication
curl -H "Authorization: Bearer your_api_key" \
     -H "Content-Type: application/json" \
     https://api.agentical.dev/v1/agents
```

---

## 🧪 **Testing**

### **Run Tests**
```bash
# Full test suite
pytest tests/ --cov=src/ --cov-report=html

# Specific test categories
pytest tests/agents/          # Agent tests
pytest tests/workflows/       # Workflow tests
pytest tests/integrations/    # Integration tests
```

### **Test Coverage**
- **Overall Coverage**: 95%+
- **Agent Tests**: 115+ test methods
- **Integration Tests**: API endpoints, CI/CD platforms
- **Performance Tests**: Load testing and benchmarks

---

## 📈 **Performance & Scalability**

### **Benchmarks**
- **API Response Time**: <200ms average
- **Concurrent Agents**: 20+ simultaneous executions
- **Workflow Throughput**: 100+ workflows per minute
- **System Uptime**: 99.5% availability target

### **Scaling**
- **Horizontal Scaling**: Multi-instance deployment
- **Load Balancing**: Agent pool distribution
- **Caching**: Redis-based caching for performance
- **Database**: Async PostgreSQL with connection pooling

---

## 🔒 **Security**

### **Authentication & Authorization**
- **JWT Tokens**: Secure API authentication
- **Role-Based Access**: Fine-grained permissions
- **API Rate Limiting**: DDoS protection
- **Webhook Verification**: Signature-based security

### **Data Protection**
- **Encryption**: TLS 1.3 for data in transit
- **Secret Management**: Environment-based configuration
- **Audit Logging**: Complete audit trail
- **Compliance**: SOC2, GDPR ready

---

## 🌟 **Use Cases**

### **Software Development**
```python
# Automated code generation and testing
result = await code_agent.execute({
    "task": "create_fastapi_app",
    "requirements": "user authentication, REST API, tests",
    "language": "python",
    "framework": "fastapi"
})
```

### **DevOps Automation**
```python
# Infrastructure deployment
deployment = await devops_agent.deploy_application({
    "application": "web-app",
    "environment": "production",
    "platform": "kubernetes",
    "scaling": {"min": 3, "max": 10}
})
```

### **Research & Analysis**
```python
# Market research and competitive analysis
research = await research_agent.analyze_market({
    "topic": "AI agent frameworks",
    "depth": "comprehensive",
    "sources": ["academic", "industry", "patents"]
})
```

---

## 🗺️ **Agentical 2.0 Roadmap**

### **Phase 3 Completion (Q1 2025)**
- **PB-006.3**: Third-party Service Connectors
  - Slack, Teams, Discord integrations
  - JIRA, Trello, Asana project management
  - Monitoring services (Datadog, New Relic)

- **PB-006.4**: Enterprise SSO and Permissions
  - LDAP, SAML, OAuth integration
  - Advanced RBAC and multi-tenant support

- **PB-006.5**: API Marketplace and Extensions
  - Plugin architecture for custom integrations
  - Community marketplace for agents and workflows

### **Phase 4: Advanced Features & AI (Q2 2025)**
- **PB-007.1**: Multi-modal AI Capabilities
  - Vision, audio, and document processing
  - Advanced reasoning and planning

- **PB-007.2**: Natural Language Interfaces
  - Conversational agent interaction
  - Voice command integration

- **PB-007.3**: Machine Learning Optimization
  - Automated hyperparameter tuning
  - Model performance optimization

### **Phase 5: Production & Scale (Q3-Q4 2025)**
- **PB-008.1**: Horizontal Scaling Architecture
  - Kubernetes-native deployment
  - Auto-scaling and load balancing

- **PB-008.2**: Multi-tenant Capabilities
  - Enterprise tenant isolation
  - Resource quotas and billing

- **PB-008.3**: Global Deployment
  - Multi-region support
  - CDN and edge computing

---

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/agentical.git
cd agentical

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests before committing
pytest tests/
```

### **Code Standards**
- **Python**: Black formatting, type hints required
- **TypeScript**: Strict mode, comprehensive types
- **Documentation**: Google-style docstrings
- **Testing**: 95%+ coverage requirement

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

---

## 🙏 **Acknowledgments**

- **DevQ.ai Team** for framework development
- **FastAPI** for the excellent web framework
- **Pydantic** for Logfire observability
- **Open Source Community** for inspiration and contributions

---

## 📞 **Support**

- **Documentation**: [https://docs.agentical.dev](https://docs.agentical.dev)
- **GitHub Issues**: [Report bugs or request features](https://github.com/devq-ai/agentical/issues)
- **Discord**: [Join our community](https://discord.gg/agentical)
- **Email**: support@agentical.dev

---

**Built with ❤️ by the DevQ.ai Team**

*Agentical - Orchestrating Intelligence, Automating Excellence*