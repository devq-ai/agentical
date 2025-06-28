#!/usr/bin/env python3
"""
Agentical Status Setup Verification Script

This script verifies that the GitHub Pages status dashboard setup is working correctly
by testing all components and providing detailed diagnostics.

Usage:
    python scripts/verify-status-setup.py
    python scripts/verify-status-setup.py --verbose
    python scripts/verify-status-setup.py --fix-issues
"""

import json
import sys
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Tuple
import time

class StatusSetupVerifier:
    """Verify Agentical status page setup and components."""

    def __init__(self, verbose: bool = False, fix_issues: bool = False):
        self.verbose = verbose
        self.fix_issues = fix_issues
        self.project_root = Path(__file__).parent.parent
        self.issues_found = []
        self.checks_passed = []

    def log(self, message: str, level: str = "INFO"):
        """Log message with level indicator."""
        if level == "ERROR":
            print(f"❌ {message}")
            self.issues_found.append(message)
        elif level == "SUCCESS":
            print(f"✅ {message}")
            self.checks_passed.append(message)
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "INFO" and self.verbose:
            print(f"ℹ️  {message}")
        elif level == "HEADER":
            print(f"\n🔍 {message}")

    def check_file_exists(self, file_path: Path, description: str) -> bool:
        """Check if a required file exists."""
        if file_path.exists():
            self.log(f"{description} exists: {file_path}", "SUCCESS")
            return True
        else:
            self.log(f"{description} missing: {file_path}", "ERROR")
            return False

    def check_python_dependencies(self) -> bool:
        """Check Python dependencies for status generation."""
        self.log("Checking Python dependencies", "HEADER")

        try:
            import json
            import datetime
            import platform
            self.log("Required Python modules available", "SUCCESS")
            return True
        except ImportError as e:
            self.log(f"Missing Python dependency: {e}", "ERROR")
            return False

    def check_project_structure(self) -> bool:
        """Verify project structure for status generation."""
        self.log("Checking project structure", "HEADER")

        required_dirs = [
            ("agents", "Agent implementations directory"),
            ("workflows", "Workflow engine directory"),
            ("tools", "Tools and MCP integration directory"),
            ("docs", "Documentation and status output directory"),
            (".github/workflows", "GitHub Actions workflows directory")
        ]

        all_good = True
        for dir_name, description in required_dirs:
            dir_path = self.project_root / dir_name
            if not self.check_file_exists(dir_path, description):
                all_good = False
                if self.fix_issues and dir_name == "docs":
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.log(f"Created missing directory: {dir_path}", "SUCCESS")
                    all_good = True

        return all_good

    def check_required_files(self) -> bool:
        """Check for required files."""
        self.log("Checking required files", "HEADER")

        required_files = [
            ("scripts/generate_agentical_status.py", "Status generator script"),
            (".github/workflows/deploy-status.yml", "GitHub Actions workflow"),
            ("scripts/setup-github-pages.sh", "Setup script"),
            ("docs/status/GITHUB_PAGES_SETUP.md", "Setup documentation")
        ]

        all_good = True
        for file_name, description in required_files:
            file_path = self.project_root / file_name
            if not self.check_file_exists(file_path, description):
                all_good = False

        return all_good

    def test_status_generation(self) -> bool:
        """Test the status generation script."""
        self.log("Testing status generation", "HEADER")

        generator_script = self.project_root / "scripts/generate_agentical_status.py"

        if not generator_script.exists():
            self.log("Status generator script not found", "ERROR")
            return False

        try:
            # Test status generation to temporary file
            temp_status = self.project_root / "temp_status.json"

            result = subprocess.run([
                sys.executable, str(generator_script),
                "--save", str(temp_status)
            ], capture_output=True, text=True, cwd=self.project_root)

            if result.returncode == 0:
                self.log("Status generation script runs successfully", "SUCCESS")

                # Validate generated JSON
                if temp_status.exists():
                    try:
                        with open(temp_status, 'r') as f:
                            status_data = json.load(f)

                        # Check required fields
                        required_fields = ["system", "agents", "workflows", "tools", "playbooks"]
                        missing_fields = [field for field in required_fields if field not in status_data]

                        if missing_fields:
                            self.log(f"Generated status missing fields: {missing_fields}", "ERROR")
                            return False

                        self.log("Status JSON structure is valid", "SUCCESS")

                        # Check specific metrics
                        if status_data.get("agents", {}).get("total_agents", 0) > 0:
                            self.log(f"Agents detected: {status_data['agents']['total_agents']}", "SUCCESS")
                        else:
                            self.log("No agents detected in status", "WARNING")

                        if status_data.get("tools", {}).get("mcp_servers", {}).get("total_available", 0) > 0:
                            self.log(f"MCP servers detected: {status_data['tools']['mcp_servers']['total_available']}", "SUCCESS")
                        else:
                            self.log("No MCP servers detected", "WARNING")

                        # Clean up temp file
                        temp_status.unlink()
                        return True

                    except json.JSONDecodeError as e:
                        self.log(f"Generated JSON is invalid: {e}", "ERROR")
                        return False
                    finally:
                        if temp_status.exists():
                            temp_status.unlink()
                else:
                    self.log("Status file was not generated", "ERROR")
                    return False
            else:
                self.log(f"Status generation failed: {result.stderr}", "ERROR")
                return False

        except Exception as e:
            self.log(f"Error testing status generation: {e}", "ERROR")
            return False

    def check_workflow_configuration(self) -> bool:
        """Check GitHub Actions workflow configuration."""
        self.log("Checking workflow configuration", "HEADER")

        workflow_file = self.project_root / ".github/workflows/deploy-status.yml"

        if not workflow_file.exists():
            self.log("GitHub Actions workflow file not found", "ERROR")
            return False

        try:
            with open(workflow_file, 'r') as f:
                workflow_content = f.read()

            # Check for required components
            required_components = [
                ("pages: write", "Pages write permission"),
                ("actions/checkout@v4", "Checkout action"),
                ("actions/setup-python@v4", "Python setup"),
                ("actions/configure-pages@v4", "Pages configuration"),
                ("actions/deploy-pages@v4", "Pages deployment"),
                ("generate_agentical_status.py", "Status generation command")
            ]

            all_good = True
            for component, description in required_components:
                if component in workflow_content:
                    self.log(f"Workflow has {description}", "SUCCESS")
                else:
                    self.log(f"Workflow missing {description}", "ERROR")
                    all_good = False

            # Check schedule configuration
            if "schedule:" in workflow_content and "cron:" in workflow_content:
                self.log("Automatic update schedule configured", "SUCCESS")
            else:
                self.log("No automatic update schedule found", "WARNING")

            return all_good

        except Exception as e:
            self.log(f"Error reading workflow file: {e}", "ERROR")
            return False

    def check_git_repository(self) -> bool:
        """Check git repository status."""
        self.log("Checking git repository", "HEADER")

        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True, text=True, cwd=self.project_root
            )

            if result.returncode != 0:
                self.log("Not in a git repository", "ERROR")
                return False

            self.log("Git repository detected", "SUCCESS")

            # Check for remote origin
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, cwd=self.project_root
            )

            if result.returncode == 0:
                remote_url = result.stdout.strip()
                if "github.com" in remote_url:
                    self.log(f"GitHub remote configured: {remote_url}", "SUCCESS")
                    return True
                else:
                    self.log(f"Remote is not GitHub: {remote_url}", "WARNING")
                    return False
            else:
                self.log("No remote origin configured", "ERROR")
                return False

        except Exception as e:
            self.log(f"Error checking git repository: {e}", "ERROR")
            return False

    def check_github_pages_config(self) -> bool:
        """Check if GitHub Pages could be configured."""
        self.log("Checking GitHub Pages readiness", "HEADER")

        try:
            # Check if GitHub CLI is available
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True, text=True
            )

            if result.returncode == 0:
                self.log("GitHub CLI available", "SUCCESS")

                # Check authentication
                result = subprocess.run(
                    ["gh", "auth", "status"],
                    capture_output=True, text=True
                )

                if result.returncode == 0:
                    self.log("GitHub CLI authenticated", "SUCCESS")
                    return True
                else:
                    self.log("GitHub CLI not authenticated", "WARNING")
                    self.log("Run 'gh auth login' to authenticate", "INFO")
                    return False
            else:
                self.log("GitHub CLI not available", "WARNING")
                self.log("Install GitHub CLI for automatic Pages setup", "INFO")
                return False

        except FileNotFoundError:
            self.log("GitHub CLI not installed", "WARNING")
            return False

    def check_docs_directory(self) -> bool:
        """Check docs directory and contents."""
        self.log("Checking docs directory", "HEADER")

        docs_dir = self.project_root / "docs"

        if not docs_dir.exists():
            self.log("Docs directory does not exist", "ERROR")
            if self.fix_issues:
                docs_dir.mkdir(parents=True, exist_ok=True)
                self.log("Created docs directory", "SUCCESS")
                return True
            return False

        self.log("Docs directory exists", "SUCCESS")

        # Check for status.json
        status_file = docs_dir / "status.json"
        if status_file.exists():
            self.log("Existing status.json found", "SUCCESS")

            try:
                with open(status_file, 'r') as f:
                    status_data = json.load(f)

                # Check timestamp
                if "timestamp" in status_data:
                    self.log(f"Status last updated: {status_data['timestamp']}", "SUCCESS")
                else:
                    self.log("Status file missing timestamp", "WARNING")

            except json.JSONDecodeError:
                self.log("Existing status.json is invalid", "ERROR")
                return False
        else:
            self.log("No status.json found in docs directory", "WARNING")

        return True

    def run_comprehensive_test(self) -> bool:
        """Run comprehensive verification test."""
        self.log("AGENTICAL STATUS SETUP VERIFICATION", "HEADER")
        print("=" * 50)

        tests = [
            ("Python Dependencies", self.check_python_dependencies),
            ("Project Structure", self.check_project_structure),
            ("Required Files", self.check_required_files),
            ("Status Generation", self.test_status_generation),
            ("Workflow Configuration", self.check_workflow_configuration),
            ("Git Repository", self.check_git_repository),
            ("GitHub Pages Readiness", self.check_github_pages_config),
            ("Docs Directory", self.check_docs_directory)
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log(f"Test {test_name} failed with exception: {e}", "ERROR")

        # Summary
        print(f"\n{'='*50}")
        print(f"VERIFICATION SUMMARY")
        print(f"{'='*50}")

        if passed_tests == total_tests:
            print(f"🎉 ALL TESTS PASSED ({passed_tests}/{total_tests})")
            print("\n✅ Your Agentical status page setup is ready!")
            print("   Run: ./scripts/setup-github-pages.sh")
            return True
        else:
            print(f"⚠️  SOME TESTS FAILED ({passed_tests}/{total_tests})")
            print(f"\n❌ Issues found: {len(self.issues_found)}")
            for issue in self.issues_found:
                print(f"   • {issue}")

            if self.fix_issues:
                print(f"\n🔧 Attempted to fix issues automatically")
            else:
                print(f"\n💡 Run with --fix-issues to attempt automatic fixes")

            return False

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Verify Agentical status page setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/verify-status-setup.py
  python scripts/verify-status-setup.py --verbose
  python scripts/verify-status-setup.py --fix-issues
        """
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--fix-issues',
        action='store_true',
        help='Attempt to automatically fix issues'
    )

    args = parser.parse_args()

    try:
        verifier = StatusSetupVerifier(
            verbose=args.verbose,
            fix_issues=args.fix_issues
        )

        success = verifier.run_comprehensive_test()

        if success:
            print("\n🚀 Next steps:")
            print("   1. Run: ./scripts/setup-github-pages.sh")
            print("   2. Monitor GitHub Actions for deployment")
            print("   3. Access your status page once deployed")
            return 0
        else:
            print("\n🔧 Please fix the issues above and run verification again")
            return 1

    except KeyboardInterrupt:
        print("\n\n⏸️  Verification interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
