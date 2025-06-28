# Local Preview Guide for Agentical Status Dashboard

## 🎯 Overview

This guide shows you how to preview your Agentical status dashboard locally before deploying to GitHub Pages. You have multiple options depending on your needs.

## 🚀 Quick Start Options

### Option 1: Live Development Server (Recommended)

```bash
# Start local server with auto-refresh
python scripts/serve-status-local.py
```

- **URL**: `http://localhost:8000`
- **Auto-refresh**: Every 30 seconds
- **Live data**: Fresh generation on each request
- **Best for**: Active development and testing

### Option 2: Static HTML Preview

```bash
# Generate standalone HTML file
python scripts/create-local-preview.py --open
```

- **Output**: `agentical-status-preview.html`
- **Embedded data**: Status frozen at generation time
- **No server**: Open directly in browser
- **Best for**: Quick previews and sharing

### Option 3: Simple Python Server

```bash
# Generate status and serve docs directory
python generate_agentical_status.py --save docs/status.json
cd docs
python -m http.server 8000
```

- **URL**: `http://localhost:8000`
- **Manual refresh**: Regenerate status.json as needed
- **Best for**: Basic static serving

## 🔧 Development Server Features

### Basic Usage

```bash
# Default: port 8000, auto-refresh enabled
python scripts/serve-status-local.py

# Custom port
python scripts/serve-status-local.py --port 8080

# Disable auto-refresh
python scripts/serve-status-local.py --no-auto-refresh

# Don't auto-open browser
python scripts/serve-status-local.py --no-browser
```

### What You Get

- **🔄 Auto-refresh**: Status updates every 30 seconds
- **📊 Live Data**: Fresh metrics from your codebase
- **🎨 Full Dashboard**: Complete visual experience
- **🛠️ Dev Mode**: Clear indicators this is local development
- **📱 Responsive**: Works on mobile and desktop

### Development Workflow

1. **Start Server**: `python scripts/serve-status-local.py`
2. **Make Changes**: Edit agents, workflows, or tools
3. **See Updates**: Automatic refresh shows changes
4. **Test Features**: Verify everything works correctly
5. **Deploy**: Push to GitHub when satisfied

## 📋 Static Preview Features

### Basic Usage

```bash
# Generate preview file
python scripts/create-local-preview.py

# Auto-open in browser
python scripts/create-local-preview.py --open

# Custom filename
python scripts/create-local-preview.py --output my-dashboard.html
```

### What You Get

- **📄 Standalone File**: No server required
- **🔗 Shareable**: Send to team members
- **📊 Embedded Data**: All metrics included
- **🎨 Full Styling**: Complete visual design
- **📱 Responsive**: Works everywhere

### Use Cases

- **Quick Preview**: Check layout and data
- **Team Sharing**: Send HTML file to colleagues
- **Offline Viewing**: No internet required
- **Documentation**: Include in project docs

## 🎨 Dashboard Features Preview

Both preview methods show the complete dashboard:

### 📊 Metrics Overview
- **15+ Production Agents**: All specialized agents
- **26+ MCP Servers**: Complete tool ecosystem
- **0 Playbooks**: Ready for creation
- **95% Test Coverage**: Quality metrics

### 🎯 Visual Components
- **Dark Cyberpunk Theme**: DevQ.ai branding
- **Color Palette**: Neon pink, green, cyan
- **Responsive Grid**: Adapts to screen size
- **Interactive Cards**: Hover effects and animations

### 📈 Real-time Data
- **Agent Status**: All 15 agents with capabilities
- **Workflow Engine**: 7 coordination strategies
- **Tool Integration**: MCP server status
- **Implementation Progress**: 85% completion

## 🔍 Troubleshooting

### Port Already in Use

```bash
# Try different port
python scripts/serve-status-local.py --port 8001

# Check what's using the port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Status Generation Fails

```bash
# Test status generator
python generate_agentical_status.py --print

# Check dependencies
python scripts/verify-status-setup.py

# Fix common issues
python scripts/verify-status-setup.py --fix-issues
```

### Browser Issues

```bash
# Clear browser cache
# Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)

# Try different browser
# Disable browser extensions if needed

# Check JavaScript console for errors
```

### File Not Found Errors

```bash
# Ensure you're in project root
cd /path/to/agentical

# Verify file structure
python scripts/verify-status-setup.py

# Check required files exist
ls -la generate_agentical_status.py
ls -la scripts/serve-status-local.py
```

## 🚀 Advanced Usage

### Custom Development Workflow

```bash
# Terminal 1: Start development server
python scripts/serve-status-local.py --port 8000

# Terminal 2: Watch for changes (optional)
# Use your preferred file watcher to trigger actions

# Browser: http://localhost:8000
# Auto-refreshes show your changes
```

### Comparing Versions

```bash
# Generate current version
python scripts/create-local-preview.py --output current.html

# Make changes to your code

# Generate new version
python scripts/create-local-preview.py --output updated.html

# Compare side by side in browser tabs
```

### Integration Testing

```bash
# Start local server
python scripts/serve-status-local.py --port 8000

# Test API endpoint
curl http://localhost:8000/status.json | jq .

# Verify specific metrics
curl -s http://localhost:8000/status.json | jq '.agents.total_agents'
```

## 📝 Best Practices

### Before GitHub Deployment

1. **✅ Local Preview**: Always preview locally first
2. **🔍 Data Validation**: Check all metrics are correct
3. **🎨 Visual Review**: Verify styling and layout
4. **📱 Mobile Test**: Check responsive design
5. **🚀 Deploy**: Push to GitHub when satisfied

### Development Tips

- **Use Development Server**: For active development
- **Generate Static**: For quick checks
- **Test Frequently**: Preview changes early
- **Verify Data**: Ensure metrics are accurate
- **Check Responsiveness**: Test different screen sizes

### Sharing Previews

- **Static HTML**: Best for sharing with team
- **Screenshots**: Quick visual communication
- **Screen Recording**: Show interactive features
- **JSON Export**: Share raw data if needed

## 🎯 Next Steps

After previewing locally:

1. **Satisfied with Preview?** → Run GitHub Pages setup
2. **Need Changes?** → Modify code and preview again  
3. **Ready to Deploy?** → Use `./scripts/setup-github-pages.sh`
4. **Want to Share?** → Send static HTML file

## 📚 Related Documentation

- [GitHub Pages Setup Guide](GITHUB_PAGES_SETUP.md)
- [Status Generator Documentation](docs/README.md)
- [Verification Guide](scripts/verify-status-setup.py --help)

---

**Local Preview**: ✅ Ready to use  
**Multiple Options**: Development server, static HTML, simple serving  
**Full Features**: Complete dashboard experience locally  
**Perfect for**: Testing before deployment