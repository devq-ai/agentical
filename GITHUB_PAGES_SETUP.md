# GitHub Pages Setup for Agentical Status Dashboard

This guide will help you set up a live status dashboard for your Agentical AI Agent Framework using GitHub Pages. The dashboard provides real-time monitoring of agents, workflows, tools, and system metrics.

## 🎯 Overview

The Agentical Status Dashboard provides:

- **Real-time System Status**: Framework health and performance metrics
- **Agent Monitoring**: Track all 15+ production agents and their capabilities
- **Workflow Engine Status**: Coordination strategies and concurrent processing
- **Tool Integration**: Monitor 26+ MCP servers and tool categories
- **Playbook Tracking**: Available playbooks (currently 0, ready for creation)
- **Implementation Metrics**: Code quality, test coverage, and deployment status

## 🚀 Quick Setup (Automated)

### Prerequisites

1. **GitHub Repository**: Your Agentical code must be in a GitHub repository
2. **Python 3.9+**: Required for status generation
3. **Git**: For committing and pushing changes
4. **GitHub CLI** (optional): For automatic Pages configuration

### One-Command Setup

```bash
# Run the automated setup script
./scripts/setup-github-pages.sh
```

The script will:
- ✅ Generate initial status report
- ✅ Configure GitHub Actions workflow
- ✅ Set up GitHub Pages (if GitHub CLI is authenticated)
- ✅ Commit and push changes
- ✅ Provide access URL

## 🔍 Local Preview (Before Pushing)

You can preview the status dashboard locally before pushing to GitHub:

### Option 1: Live Development Server (Recommended)

```bash
# Start local server with auto-refresh
python scripts/serve-status-local.py

# Custom port
python scripts/serve-status-local.py --port 8080

# Disable auto-refresh
python scripts/serve-status-local.py --no-auto-refresh
```

**Features:**
- Live at `http://localhost:8000`
- Auto-refresh every 30 seconds
- Fresh data generation on each request
- Development mode indicator

### Option 2: Static HTML Preview

```bash
# Generate static HTML file
python scripts/create-local-preview.py

# Open automatically in browser
python scripts/create-local-preview.py --open

# Custom output file
python scripts/create-local-preview.py --output my-preview.html
```

**Features:**
- Standalone HTML file
- Embedded status data
- No server required
- Perfect for sharing previews

## 📋 Manual Setup

If you prefer manual configuration or the automated script fails:

### Step 1: Generate Status Data

```bash
# Create initial status report
python generate_agentical_status.py --save docs/status.json
```

### Step 2: Enable GitHub Pages

1. Go to your repository settings:
   ```
   https://github.com/YOUR_USERNAME/agentical/settings/pages
   ```

2. Configure GitHub Pages:
   - **Source**: GitHub Actions
   - **Branch**: main (if prompted)

### Step 3: Commit and Push

```bash
# Add and commit the docs directory
git add docs/
git add .github/workflows/deploy-status.yml
git commit -m "Setup GitHub Pages status dashboard"
git push origin main
```

### Step 4: Monitor Deployment

1. Go to the **Actions** tab in your repository
2. Watch the "Deploy Agentical Status Page" workflow
3. Wait for deployment to complete (2-3 minutes)

## 🔧 Configuration

### Environment Variables

No environment variables are required for the basic setup. The status generator automatically detects:

- Agent configurations from `/agents/` directory
- Workflow capabilities from `/workflows/` directory  
- Tool integrations from `/tools/` directory
- MCP server configurations from `mcp-servers.json`

### Customizing Update Frequency

Edit `.github/workflows/deploy-status.yml` to change the update schedule:

```yaml
schedule:
  # Current: Every 6 hours
  - cron: '0 */6 * * *'
  
  # Examples:
  # Every hour: '0 * * * *'
  # Every 30 minutes: '*/30 * * * *'
  # Daily at midnight: '0 0 * * *'
```

### Custom Styling

The dashboard uses a cyberpunk dark theme with DevQ.ai colors:

- **Primary**: `#FF10F0` (Neon Pink)
- **Success**: `#39FF14` (Neon Green)  
- **Info**: `#00FFFF` (Neon Cyan)
- **Background**: Dark gradient with subtle transparency

To customize, edit the CSS in `.github/workflows/deploy-status.yml`.

## 📊 Dashboard Features

### 🎛️ System Overview
- Framework version and architecture
- Production readiness status
- Test coverage and quality grades
- Performance metrics

### 🤖 Agent Ecosystem
- **15 Production Agents**:
  - CodeAgent (21+ languages, testing, documentation)
  - DevOpsAgent (multi-cloud, containers, IaC)
  - GitHubAgent (repository management, PRs, analytics)
  - ResearchAgent (academic, web, competitive analysis)
  - CloudAgent (AWS, GCP, Azure cost optimization)
  - UXAgent (usability testing, design review)
  - LegalAgent (contract review, compliance)
  - DataScienceAgent (analytics, ML workflows)
  - SecurityAgent (vulnerability scanning)
  - TesterAgent (automated testing, QA)
  - And 5 more specialized agents

### ⚙️ Workflow Engine
- **7 Coordination Strategies**: parallel, sequential, pipeline, hierarchical, conditional, loop, dynamic
- **Multi-Agent Orchestration**: 20+ concurrent agents supported
- **State Management**: Persistent with multi-level checkpointing
- **Real-time Optimization**: Performance monitoring and health scoring

### 🔧 Tools & MCP Integration
- **26+ MCP Servers**: Complete tool ecosystem
- **6 Tool Categories**: Development, data analysis, external services, scientific computing, infrastructure, custom
- **4 Execution Modes**: sync, async, batch, stream
- **Performance Configuration**: 50 max concurrent executions, auto-reconnect

### 📋 Playbooks
- **Current Count**: 0 (ready for creation)
- **Engine Status**: Production ready
- **Editor Interface**: Available
- **Database Schema**: Deployed

### 📈 Implementation Metrics
- **22,000+ Lines of Code**: Production implementation
- **95% Test Coverage**: Comprehensive testing
- **65 API Endpoints**: Full REST API
- **40 Integration Points**: External services and platforms

## 🔄 Automation Features

### Automatic Updates

The status page automatically updates:

1. **Every 6 hours**: Scheduled refresh
2. **On push to main**: Immediate update
3. **On pull requests**: Preview generation
4. **Manual trigger**: Via GitHub Actions

### Real-time Dashboard

The web dashboard includes:

- **Auto-refresh**: Every 5 minutes
- **Loading states**: Smooth user experience
- **Error handling**: Graceful failure recovery
- **Responsive design**: Mobile and desktop friendly

## 🌐 Accessing Your Dashboard

Once deployed, your status page will be available at:

```
https://YOUR_USERNAME.github.io/agentical/
```

### Direct JSON Access

Raw status data is available at:

```
https://YOUR_USERNAME.github.io/agentical/status.json
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. GitHub Pages Not Found (404)

**Solution**: 
- Check that GitHub Pages is enabled in repository settings
- Verify the workflow completed successfully in Actions tab
- Wait 5-10 minutes for DNS propagation

#### 2. Status Generation Fails

**Solution**:
```bash
# Check Python dependencies
pip install -r requirements.txt

# Test status generation locally
python generate_agentical_status.py --print

# Check for missing files
ls -la agents/ workflows/ tools/
```

#### 3. Workflow Permission Errors

**Solution**:
- Ensure the workflow has `pages: write` permission
- Check that GitHub Actions is enabled for the repository
- Verify the repository has GitHub Pages enabled

#### 4. Outdated Status Data

**Solution**:
- Manually trigger the workflow in GitHub Actions
- Check the workflow schedule configuration
- Verify no errors in recent workflow runs

### Manual Status Update

To manually update the status:

```bash
# Generate new status
python generate_agentical_status.py --save docs/status.json

# Commit and push
git add docs/status.json
git commit -m "Update status data"
git push origin main
```

### Reset GitHub Pages

If you need to start over:

1. Disable GitHub Pages in repository settings
2. Delete the `docs/` directory
3. Remove the workflow file
4. Re-run the setup process

## 📚 Advanced Configuration

### Custom Metrics

Add custom metrics by modifying `generate_agentical_status.py`:

```python
def get_custom_metrics(self) -> Dict[str, Any]:
    return {
        "custom_agent_count": self.count_custom_agents(),
        "performance_score": self.calculate_performance(),
        "integration_health": self.check_integrations()
    }
```

### Multiple Environments

Track different environments (dev, staging, prod):

1. Create separate workflow files for each environment
2. Modify the status generator to detect environment
3. Deploy to different GitHub Pages sites or subdirectories

### API Integration

The status JSON can be consumed by external monitoring tools:

```javascript
// Fetch status from external application
const response = await fetch('https://username.github.io/agentical/status.json');
const status = await response.json();

// Use status data for monitoring
if (status.agents.total_agents < 15) {
    alert('Agent count below expected threshold');
}
```

## 🎯 Next Steps

After setting up your status dashboard:

1. **Monitor Regularly**: Check the dashboard for system health
2. **Create Playbooks**: Add playbooks to see them tracked
3. **Customize Styling**: Modify the dashboard appearance
4. **Set Up Alerts**: Use the JSON API for monitoring integration
5. **Share Status**: Use the public URL for team visibility

## 📞 Support

For issues with the status dashboard:

1. **Check the troubleshooting section** above
2. **Review GitHub Actions logs** for deployment errors
3. **Test status generation locally** for data issues
4. **Verify GitHub Pages configuration** in repository settings

The status dashboard provides comprehensive visibility into your Agentical framework, helping you monitor system health, track development progress, and maintain production readiness.

---

**Generated by**: Agentical GitHub Pages Setup Guide  
**Framework**: Agentical v1.0.0  
**Maintained by**: DevQ.ai Team