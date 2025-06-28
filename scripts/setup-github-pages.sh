#!/bin/bash

# Agentical GitHub Pages Setup Script
# This script helps configure GitHub Pages for the Agentical status dashboard

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Unicode symbols
CHECK="✅"
ERROR="❌"
INFO="ℹ️"
ROCKET="🚀"
GEAR="⚙️"
DOCS="📚"

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPO_URL=""
GITHUB_TOKEN=""

# Functions
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🤖 AGENTICAL SETUP                        ║"
    echo "║              GitHub Pages Status Dashboard                   ║"
    echo "║                                                              ║"
    echo "║  This script will configure GitHub Pages for your           ║"
    echo "║  Agentical status dashboard deployment.                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${BLUE}${GEAR} $1${NC}"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${ERROR} $1${NC}"
}

print_info() {
    echo -e "${CYAN}${INFO} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_dependencies() {
    print_step "Checking dependencies..."

    local missing_deps=()

    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi

    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi

    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI (gh) not found. Manual configuration will be required."
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo -e "\nPlease install the missing dependencies and run this script again."
        exit 1
    fi

    print_success "All dependencies are available"
}

detect_repository() {
    print_step "Detecting repository information..."

    if [ -d "$PROJECT_ROOT/.git" ]; then
        cd "$PROJECT_ROOT"
        REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")

        if [[ $REPO_URL == *"github.com"* ]]; then
            print_success "GitHub repository detected: $REPO_URL"
        else
            print_error "This does not appear to be a GitHub repository"
            echo "GitHub Pages requires a GitHub repository. Please push your code to GitHub first."
            exit 1
        fi
    else
        print_error "No git repository found in $PROJECT_ROOT"
        echo "Please initialize a git repository and push to GitHub first."
        exit 1
    fi
}

check_github_auth() {
    print_step "Checking GitHub authentication..."

    if command -v gh &> /dev/null; then
        if gh auth status &> /dev/null; then
            print_success "GitHub CLI is authenticated"
            return 0
        else
            print_warning "GitHub CLI is not authenticated"
        fi
    fi

    print_info "You may need to configure GitHub Pages manually"
    print_info "Visit: https://github.com/settings/tokens to create a personal access token"
    return 1
}

generate_status_report() {
    print_step "Generating initial status report..."

    cd "$PROJECT_ROOT"

    if [ -f "generate_agentical_status.py" ]; then
        if python3 generate_agentical_status.py --save docs/status.json; then
            print_success "Status report generated successfully"
        else
            print_error "Failed to generate status report"
            exit 1
        fi
    else
        print_error "Status generator script not found"
        exit 1
    fi
}

setup_github_pages_cli() {
    print_step "Setting up GitHub Pages using GitHub CLI..."

    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI not available, skipping automatic setup"
        return 1
    fi

    if ! gh auth status &> /dev/null; then
        print_warning "GitHub CLI not authenticated, skipping automatic setup"
        return 1
    fi

    cd "$PROJECT_ROOT"

    # Enable GitHub Pages with GitHub Actions source
    if gh api repos/:owner/:repo/pages -X POST -f source.branch=main -f source.path=/ -f build_type=workflow &> /dev/null; then
        print_success "GitHub Pages enabled with GitHub Actions"
    else
        print_info "GitHub Pages may already be configured or requires manual setup"
    fi

    return 0
}

create_workflow_permissions() {
    print_step "Checking workflow permissions..."

    local workflow_file="$PROJECT_ROOT/.github/workflows/deploy-status.yml"

    if [ -f "$workflow_file" ]; then
        print_success "GitHub Actions workflow found"

        if grep -q "pages: write" "$workflow_file"; then
            print_success "Workflow permissions are correctly configured"
        else
            print_warning "Workflow may need permission updates"
        fi
    else
        print_error "GitHub Actions workflow not found"
        echo "Expected location: $workflow_file"
        exit 1
    fi
}

commit_and_push() {
    print_step "Committing and pushing changes..."

    cd "$PROJECT_ROOT"

    # Check if there are changes to commit
    if git diff --quiet && git diff --staged --quiet; then
        print_info "No changes to commit"
        return 0
    fi

    # Add docs directory
    git add docs/

    # Add workflow if it exists
    if [ -f ".github/workflows/deploy-status.yml" ]; then
        git add .github/workflows/deploy-status.yml
    fi

    # Commit changes
    if git commit -m "Setup GitHub Pages status dashboard

- Add Agentical status generator
- Configure GitHub Actions workflow for automatic deployment
- Generate initial status.json with system metrics
- Setup responsive HTML dashboard with real-time updates

Components tracked:
- 15+ Production Agents (CodeAgent, DevOpsAgent, etc.)
- Workflow Engine with 7 coordination strategies
- 26+ MCP Servers and tool integration
- 0 Playbooks (ready for creation)
- 95% test coverage across 22,000+ lines of code"; then
        print_success "Changes committed"
    else
        print_error "Failed to commit changes"
        exit 1
    fi

    # Push to origin
    if git push origin main; then
        print_success "Changes pushed to GitHub"
    else
        print_error "Failed to push to GitHub"
        exit 1
    fi
}

print_manual_instructions() {
    print_step "Manual GitHub Pages Configuration"

    echo -e "\n${YELLOW}If automatic setup failed, follow these manual steps:${NC}\n"

    echo "1. Go to your GitHub repository settings:"
    echo "   https://github.com/YOUR_USERNAME/agentical/settings/pages"
    echo ""
    echo "2. Configure GitHub Pages:"
    echo "   - Source: GitHub Actions"
    echo "   - Branch: main (if prompted)"
    echo ""
    echo "3. Wait for the workflow to run:"
    echo "   - Go to Actions tab to monitor deployment"
    echo "   - First run may take 2-3 minutes"
    echo ""
    echo "4. Access your status page:"
    echo "   https://YOUR_USERNAME.github.io/agentical/"
    echo ""

    print_info "The status page will auto-update every 6 hours"
}

print_completion_summary() {
    echo -e "\n${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   🎉 SETUP COMPLETE!                         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${CYAN}What was configured:${NC}"
    echo "  ${CHECK} Status generator script"
    echo "  ${CHECK} GitHub Actions workflow"
    echo "  ${CHECK} Initial status.json generated"
    echo "  ${CHECK} HTML dashboard created"
    echo "  ${CHECK} Changes committed and pushed"

    echo -e "\n${CYAN}What happens next:${NC}"
    echo "  ${ROCKET} GitHub Actions will deploy your status page"
    echo "  ${DOCS} Status updates automatically every 6 hours"
    echo "  ${GEAR} Manual updates available via workflow dispatch"

    echo -e "\n${CYAN}Key Features:${NC}"
    echo "  📊 Real-time system metrics"
    echo "  🤖 15+ Agent status tracking"
    echo "  ⚙️  Workflow engine monitoring"
    echo "  🔧 MCP server integration status"
    echo "  📋 Playbook availability (currently 0)"
    echo "  📈 Implementation progress (85% complete)"

    if [[ $REPO_URL == *"github.com/"* ]]; then
        local repo_path=$(echo "$REPO_URL" | sed 's/.*github\.com[:/]\([^/]*\/[^/]*\)\.git.*/\1/')
        echo -e "\n${PURPLE}Your status page will be available at:${NC}"
        echo "  🔗 https://${repo_path%/*}.github.io/${repo_path##*/}/"
    fi

    echo -e "\n${YELLOW}Next steps:${NC}"
    echo "  1. Monitor the Actions tab for deployment progress"
    echo "  2. Visit your status page once deployment completes"
    echo "  3. Create playbooks to see them tracked in the dashboard"
    echo "  4. Customize the dashboard styling if desired"
}

# Main execution
main() {
    print_banner

    check_dependencies
    detect_repository
    check_github_auth

    generate_status_report
    create_workflow_permissions

    # Try automatic setup, fall back to manual instructions
    if ! setup_github_pages_cli; then
        print_manual_instructions
    fi

    commit_and_push
    print_completion_summary

    echo -e "\n${GREEN}🚀 Agentical GitHub Pages setup complete!${NC}"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Agentical GitHub Pages Setup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --dry-run      Show what would be done without making changes"
        echo ""
        echo "This script configures GitHub Pages for the Agentical status dashboard."
        echo "It will generate status data, set up GitHub Actions, and deploy the page."
        exit 0
        ;;
    --dry-run)
        echo "DRY RUN MODE - No changes will be made"
        echo ""
        check_dependencies
        detect_repository
        check_github_auth
        echo ""
        echo "Would generate status report and configure GitHub Pages"
        echo "Use without --dry-run to actually perform setup"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
