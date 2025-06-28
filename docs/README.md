# Agentical Documentation & Status Page

This directory contains the documentation and status page for the Agentical AI Agent Framework.

## 📊 Live Status Page

The Agentical system status is automatically updated and deployed to GitHub Pages:

**🔗 [Live Status Dashboard](https://devq-ai.github.io/agentical/)**

## 📋 Contents

- `status.json` - Real-time system status data (auto-generated)
- `index.html` - Status dashboard webpage (auto-generated)
- `README.md` - This documentation file

## 🤖 Automated Status Generation

The status page is automatically updated every 6 hours and on every push to the main branch using GitHub Actions.

### Manual Status Generation

To manually generate the status report:

```bash
# Generate and save to docs/status.json
python generate_agentical_status.py --save docs/status.json

# Print to console
python generate_agentical_status.py --print

# Save to custom location
python generate_agentical_status.py --output /path/to/custom/status.json
```

## 📈 Status Data Structure

The `status.json` file contains comprehensive system information:

### System Overview
- Framework version and status
- Architecture details
- Performance metrics
- Test coverage

### Agent Ecosystem
- **15+ Production Agents**: CodeAgent, DevOpsAgent, GitHubAgent, etc.
- **100+ Capabilities**: Across all specialized agents
- **Grade A Quality**: All agents production-ready

### Workflow Engine
- **7 Coordination Strategies**: parallel, sequential, pipeline, etc.
- **8 Core Features**: Multi-agent coordination, state management, etc.
- **20+ Concurrent Agents**: Supported simultaneously

### Tools & MCP Integration
- **26+ MCP Servers**: Full toolkit integration
- **6 Tool Categories**: Development, data analysis, external services, etc.
- **4 Execution Modes**: sync, async, batch, stream

### Playbooks
- **0 Available Playbooks**: Ready for creation
- **Production Engine**: Fully implemented
- **Editor Interface**: Available for playbook creation

### Implementation Metrics
- **22,000+ Lines of Code**: Production-ready implementation
- **95% Test Coverage**: Comprehensive testing
- **65 API Endpoints**: Full REST API
- **40 Integration Points**: External services and platforms

## ⚙️ GitHub Pages Setup

### Prerequisites

1. **Enable GitHub Pages** in repository settings:
   - Go to `Settings` → `Pages`
   - Source: `GitHub Actions`
   - Branch: `main`

2. **Required Permissions** (automatically configured in workflow):
   - `contents: read`
   - `pages: write`
   - `id-token: write`

### Automatic Deployment

The GitHub Actions workflow (`.github/workflows/deploy-status.yml`) automatically:

1. **Generates** fresh status data from the codebase
2. **Creates** the HTML dashboard
3. **Deploys** to GitHub Pages

### Deployment Triggers

- **Push to main**: Immediate update
- **Pull request**: Preview generation
- **Schedule**: Every 6 hours (automatic refresh)
- **Manual**: Via workflow dispatch

## 🎨 Dashboard Features

### Visual Elements
- **Dark Theme**: Modern cyberpunk aesthetic
- **Real-time Metrics**: Key performance indicators
- **Component Cards**: Organized system information
- **Responsive Design**: Mobile and desktop friendly

### Color Scheme (DevQ.ai Palette)
- **Primary**: `#FF10F0` (Neon Pink)
- **Success**: `#39FF14` (Neon Green)
- **Info**: `#00FFFF` (Neon Cyan)
- **Accent**: `#1B03A3` (Neon Blue)

### Interactive Features
- **Auto-refresh**: Every 5 minutes
- **JSON Access**: Direct link to raw data
- **GitHub Link**: Repository access
- **Loading States**: Smooth user experience

## 🔧 Customization

### Adding New Metrics

1. **Update Generator**: Modify `generate_agentical_status.py`
   ```python
   def get_custom_metrics(self) -> Dict[str, Any]:
       return {
           "new_metric": "value",
           "custom_data": self.calculate_custom_data()
       }
   ```

2. **Update HTML**: Modify the status rendering in the workflow
3. **Test Locally**: Run generator and verify JSON structure

### Styling Changes

The HTML template in the GitHub Actions workflow can be customized:
- Update CSS variables for colors
- Modify grid layouts
- Add new component cards
- Enhance interactive features

## 📝 Status Categories

### 🚀 System
- Framework version and architecture
- Performance and uptime metrics
- Quality grades and completion status

### 🤖 Agents
- Total count and production readiness
- Specialized agent capabilities
- Category organization

### ⚙️ Workflows
- Engine status and features
- Coordination strategies
- Concurrent processing capabilities

### 🔧 Tools
- MCP server integration
- Tool categories and execution modes
- Performance configuration

### 📋 Playbooks
- Available playbook count
- Engine and editor status
- Creation readiness

### 📊 Metrics
- Code statistics and quality
- Test coverage and API endpoints
- Integration points and documentation

### 🚀 Deployment
- Infrastructure status
- Database and monitoring setup
- Testing and API configuration

## 🔍 Monitoring

The status page provides real-time insights into:

- **Agent Health**: All 15+ agents operational
- **Workflow Performance**: Real-time orchestration metrics
- **Tool Integration**: 26+ MCP servers status
- **System Quality**: 95% test coverage maintenance
- **Production Readiness**: 85% overall completion

## 📚 Related Documentation

- [Agentical Framework Documentation](../README.md)
- [Agent Implementation Guide](../ADVANCED_AGENT_ECOSYSTEM_IMPLEMENTATION.md)
- [Workflow Engine Documentation](../WORKFLOW_ENGINE_CORE_IMPLEMENTATION.md)
- [Project Status Reports](../PROJECT_STATUS_FINAL_1.0.md)

---

**Generated by**: Agentical Status Generator v1.0.0  
**Last Updated**: Auto-updated every 6 hours  
**Maintained by**: DevQ.ai Team