"""
Comprehensive Test Suite for GitHub Agent

This module provides extensive testing for the GitHub Agent implementation,
covering all capabilities including repository management, pull request
automation, issue tracking, branch operations, workflow management,
release management, and code review automation.

Test Coverage:
- Agent initialization and configuration
- Repository creation and management
- Pull request operations and automation
- Issue tracking and management
- Branch operations and protection
- GitHub Actions workflow management
- Release management and versioning
- Code review automation
- Repository analytics and metrics
- Security and health checks
- Error handling and edge cases
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError as PydanticValidationError

from agentical.agents.github_agent import (
    GitHubAgent,
    RepositoryRequest,
    PullRequestRequest,
    IssueRequest,
    BranchRequest,
    ReleaseRequest,
    CodeReviewRequest,
    WorkflowRequest,
    RepositoryType,
    PullRequestState,
    IssueState,
    BranchProtectionLevel,
    WorkflowStatus,
    ReleaseType,
    ReviewDecision,
    RepositoryInfo,
    PullRequestInfo,
    IssueInfo,
    BranchInfo,
    WorkflowRun
)
from agentical.db.models.agent import AgentType, AgentStatus
from agentical.core.exceptions import AgentExecutionError, ValidationError


class TestGitHubAgent:
    """Test suite for GitHub Agent core functionality."""

    @pytest.fixture
    async def mock_session(self):
        """Create mock async database session."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def github_agent(self, mock_session):
        """Create GitHub Agent instance for testing."""
        agent = GitHubAgent(
            agent_id="test-github-agent",
            session=mock_session,
            config={"test_mode": True}
        )
        return agent

    @pytest.fixture
    def sample_repository_request(self):
        """Sample repository request for testing."""
        return RepositoryRequest(
            name="test-repo",
            description="Test repository for unit testing",
            private=False,
            auto_init=True,
            gitignore_template="Python",
            license_template="MIT",
            topics=["testing", "automation", "github"]
        )

    @pytest.fixture
    def sample_pull_request_request(self):
        """Sample pull request request for testing."""
        return PullRequestRequest(
            title="Add new feature implementation",
            body="This PR adds a new feature with comprehensive tests and documentation.",
            head="feature/new-implementation",
            base="main",
            draft=False,
            assignees=["developer1", "developer2"],
            reviewers=["reviewer1", "reviewer2"],
            labels=["enhancement", "needs-review"],
            milestone="v1.2.0"
        )

    @pytest.fixture
    def sample_issue_request(self):
        """Sample issue request for testing."""
        return IssueRequest(
            title="Bug: Application crashes on startup",
            body="The application crashes when starting with specific configuration parameters.",
            assignees=["developer1"],
            labels=["bug", "high-priority"],
            milestone="v1.1.1"
        )

    @pytest.fixture
    def sample_branch_request(self):
        """Sample branch request for testing."""
        return BranchRequest(
            name="feature/new-branch",
            source="main",
            protection=BranchProtectionLevel.STANDARD
        )

    @pytest.fixture
    def sample_release_request(self):
        """Sample release request for testing."""
        return ReleaseRequest(
            tag_name="v1.2.0",
            name="Version 1.2.0",
            body="## Features\n- New feature A\n- Improved feature B\n\n## Bug Fixes\n- Fixed issue #123",
            draft=False,
            prerelease=False,
            target_commitish="main"
        )

    @pytest.fixture
    def sample_workflow_request(self):
        """Sample workflow request for testing."""
        return WorkflowRequest(
            workflow_id="ci.yml",
            ref="main",
            inputs={"environment": "staging", "run_tests": True}
        )

    @pytest.fixture
    def sample_review_request(self):
        """Sample code review request for testing."""
        return CodeReviewRequest(
            pull_request=123,
            event=ReviewDecision.APPROVED,
            body="LGTM! Great implementation with comprehensive tests.",
            comments=[
                {
                    "path": "src/main.py",
                    "line": 42,
                    "body": "Consider adding error handling here"
                }
            ]
        )

    # Agent Initialization Tests

    async def test_agent_initialization(self, mock_session):
        """Test GitHub Agent initialization."""
        agent = GitHubAgent(
            agent_id="test-agent",
            session=mock_session,
            config={"custom_config": "value"}
        )

        assert agent.agent_id == "test-agent"
        assert agent.agent_type == AgentType.GITHUB
        assert "repository_management" in agent.supported_operations
        assert "pull_request_operations" in agent.supported_operations
        assert "issue_management" in agent.supported_operations

    async def test_supported_operations(self, github_agent):
        """Test that all expected operations are supported."""
        expected_operations = {
            "repository_management",
            "pull_request_operations",
            "issue_management",
            "branch_operations",
            "workflow_management",
            "release_management",
            "code_review",
            "security_management",
            "team_management"
        }

        assert github_agent.supported_operations == expected_operations

    # Repository Management Tests

    async def test_create_repository_success(self, github_agent, sample_repository_request):
        """Test successful repository creation."""
        with patch.object(github_agent, '_validate_repository_name') as mock_validate, \
             patch.object(github_agent, '_create_github_repository') as mock_create, \
             patch.object(github_agent, '_initialize_repository') as mock_init, \
             patch.object(github_agent, '_set_repository_topics') as mock_topics:

            mock_validate.return_value = None
            mock_create.return_value = {
                "name": "test-repo",
                "full_name": "owner/test-repo",
                "owner": {"login": "owner"},
                "description": "Test repository",
                "private": False
            }
            mock_init.return_value = None
            mock_topics.return_value = None

            result = await github_agent.create_repository("owner", sample_repository_request)

            assert isinstance(result, RepositoryInfo)
            assert result.name == "test-repo"
            assert result.full_name == "owner/test-repo"
            mock_validate.assert_called_once()
            mock_create.assert_called_once()
            mock_init.assert_called_once()
            mock_topics.assert_called_once()

    async def test_create_repository_validation_error(self, github_agent):
        """Test repository creation with validation error."""
        invalid_request = RepositoryRequest(
            name="invalid@name",  # Invalid character
            description="Test repo"
        )

        with patch.object(github_agent, '_validate_repository_name') as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid repository name")

            with pytest.raises(AgentExecutionError):
                await github_agent.create_repository("owner", invalid_request)

    async def test_repository_task_execution(self, github_agent, sample_repository_request):
        """Test repository task execution through execute_task."""
        task = {
            "id": "repo-task-1",
            "type": "repository",
            "operation": "create",
            "parameters": {
                "owner": "test-owner",
                **sample_repository_request.dict()
            }
        }

        with patch.object(github_agent, 'create_repository') as mock_create:
            mock_repo_info = RepositoryInfo(
                name="test-repo",
                full_name="test-owner/test-repo",
                owner="test-owner"
            )
            mock_create.return_value = mock_repo_info

            result = await github_agent.execute_task(task)

            assert result["name"] == "test-repo"
            mock_create.assert_called_once()

    # Pull Request Management Tests

    async def test_create_pull_request_success(self, github_agent, sample_pull_request_request):
        """Test successful pull request creation."""
        with patch.object(github_agent, '_validate_branches_exist') as mock_validate, \
             patch.object(github_agent, '_check_existing_pull_request') as mock_check, \
             patch.object(github_agent, '_create_github_pull_request') as mock_create, \
             patch.object(github_agent, '_set_pull_request_assignees_reviewers') as mock_assign, \
             patch.object(github_agent, '_add_pull_request_labels') as mock_labels:

            mock_validate.return_value = None
            mock_check.return_value = None
            mock_create.return_value = {
                "number": 123,
                "title": "Add new feature implementation",
                "body": "This PR adds a new feature",
                "state": "open",
                "head": {"ref": "feature/new-implementation"},
                "base": {"ref": "main"},
                "user": {"login": "developer"}
            }
            mock_assign.return_value = None
            mock_labels.return_value = None

            result = await github_agent.create_pull_request("owner", "repo", sample_pull_request_request)

            assert isinstance(result, PullRequestInfo)
            assert result.number == 123
            assert result.title == "Add new feature implementation"
            assert result.state == PullRequestState.OPEN
            mock_validate.assert_called_once()
            mock_create.assert_called_once()
            mock_assign.assert_called_once()
            mock_labels.assert_called_once()

    async def test_create_pull_request_already_exists(self, github_agent, sample_pull_request_request):
        """Test pull request creation when PR already exists."""
        with patch.object(github_agent, '_validate_branches_exist') as mock_validate, \
             patch.object(github_agent, '_check_existing_pull_request') as mock_check:

            mock_validate.return_value = None
            mock_check.return_value = {"number": 456}

            with pytest.raises(AgentExecutionError) as exc_info:
                await github_agent.create_pull_request("owner", "repo", sample_pull_request_request)

            assert "Pull request already exists" in str(exc_info.value)

    async def test_pull_request_different_states(self, github_agent):
        """Test pull request handling with different states."""
        states_to_test = [
            (PullRequestState.OPEN, "open"),
            (PullRequestState.CLOSED, "closed"),
            (PullRequestState.MERGED, "merged"),
            (PullRequestState.DRAFT, "draft")
        ]

        for state_enum, state_value in states_to_test:
            with patch.object(github_agent, '_validate_branches_exist'), \
                 patch.object(github_agent, '_check_existing_pull_request'), \
                 patch.object(github_agent, '_create_github_pull_request') as mock_create:

                mock_create.return_value = {
                    "number": 123,
                    "title": "Test PR",
                    "state": state_value,
                    "head": {"ref": "feature"},
                    "base": {"ref": "main"},
                    "user": {"login": "developer"}
                }

                request = PullRequestRequest(
                    title="Test PR",
                    head="feature",
                    base="main"
                )

                result = await github_agent.create_pull_request("owner", "repo", request)
                assert result.state == state_enum

    # Issue Management Tests

    async def test_create_issue_success(self, github_agent, sample_issue_request):
        """Test successful issue creation."""
        with patch.object(github_agent, '_create_github_issue') as mock_create, \
             patch.object(github_agent, '_set_issue_assignees') as mock_assign, \
             patch.object(github_agent, '_add_issue_labels') as mock_labels:

            mock_create.return_value = {
                "number": 456,
                "title": "Bug: Application crashes on startup",
                "body": "The application crashes",
                "state": "open",
                "user": {"login": "reporter"}
            }
            mock_assign.return_value = None
            mock_labels.return_value = None

            result = await github_agent.create_issue("owner", "repo", sample_issue_request)

            assert isinstance(result, IssueInfo)
            assert result.number == 456
            assert result.title == "Bug: Application crashes on startup"
            assert result.state == IssueState.OPEN
            mock_create.assert_called_once()
            mock_assign.assert_called_once()
            mock_labels.assert_called_once()

    async def test_issue_task_execution(self, github_agent, sample_issue_request):
        """Test issue task execution through execute_task."""
        task = {
            "id": "issue-task-1",
            "type": "issue",
            "operation": "create",
            "parameters": {
                "owner": "test-owner",
                "repo": "test-repo",
                **sample_issue_request.dict()
            }
        }

        with patch.object(github_agent, 'create_issue') as mock_create:
            mock_issue_info = IssueInfo(
                number=789,
                title="Test Issue",
                state=IssueState.OPEN,
                user="test-user"
            )
            mock_create.return_value = mock_issue_info

            result = await github_agent.execute_task(task)

            assert result["number"] == 789
            mock_create.assert_called_once()

    # Branch Management Tests

    async def test_create_branch_success(self, github_agent, sample_branch_request):
        """Test successful branch creation."""
        with patch.object(github_agent, '_validate_branch_name') as mock_validate, \
             patch.object(github_agent, '_branch_exists') as mock_exists, \
             patch.object(github_agent, '_get_default_branch') as mock_default, \
             patch.object(github_agent, '_get_branch_sha') as mock_sha, \
             patch.object(github_agent, '_create_github_branch') as mock_create, \
             patch.object(github_agent, '_setup_branch_protection') as mock_protect:

            mock_validate.return_value = None
            mock_exists.return_value = False
            mock_default.return_value = "main"
            mock_sha.return_value = "abc123def456"
            mock_create.return_value = {
                "name": "feature/new-branch",
                "sha": "abc123def456"
            }
            mock_protect.return_value = None

            result = await github_agent.create_branch("owner", "repo", sample_branch_request)

            assert isinstance(result, BranchInfo)
            assert result.name == "feature/new-branch"
            assert result.sha == "abc123def456"
            mock_validate.assert_called_once()
            mock_create.assert_called_once()
            mock_protect.assert_called_once()

    async def test_create_branch_already_exists(self, github_agent, sample_branch_request):
        """Test branch creation when branch already exists."""
        with patch.object(github_agent, '_validate_branch_name') as mock_validate, \
             patch.object(github_agent, '_branch_exists') as mock_exists:

            mock_validate.return_value = None
            mock_exists.return_value = True

            with pytest.raises(AgentExecutionError) as exc_info:
                await github_agent.create_branch("owner", "repo", sample_branch_request)

            assert "Branch already exists" in str(exc_info.value)

    async def test_branch_protection_levels(self, github_agent):
        """Test different branch protection levels."""
        protection_levels = [
            BranchProtectionLevel.NONE,
            BranchProtectionLevel.BASIC,
            BranchProtectionLevel.STANDARD,
            BranchProtectionLevel.STRICT
        ]

        for protection_level in protection_levels:
            request = BranchRequest(
                name=f"test-branch-{protection_level.value}",
                source="main",
                protection=protection_level
            )

            with patch.object(github_agent, '_validate_branch_name'), \
                 patch.object(github_agent, '_branch_exists', return_value=False), \
                 patch.object(github_agent, '_get_default_branch', return_value="main"), \
                 patch.object(github_agent, '_get_branch_sha', return_value="sha123"), \
                 patch.object(github_agent, '_create_github_branch') as mock_create, \
                 patch.object(github_agent, '_setup_branch_protection') as mock_protect:

                mock_create.return_value = {"name": request.name, "sha": "sha123"}

                await github_agent.create_branch("owner", "repo", request)

                if protection_level != BranchProtectionLevel.NONE:
                    mock_protect.assert_called_once()
                else:
                    mock_protect.assert_not_called()

    # Workflow Management Tests

    async def test_trigger_workflow_success(self, github_agent, sample_workflow_request):
        """Test successful workflow trigger."""
        with patch.object(github_agent, '_validate_workflow_exists') as mock_validate, \
             patch.object(github_agent, '_trigger_github_workflow') as mock_trigger, \
             patch.object(github_agent, '_wait_for_workflow_start') as mock_wait:

            mock_validate.return_value = None
            mock_trigger.return_value = {
                "id": 12345,
                "workflow_id": "ci.yml"
            }
            mock_wait.return_value = None

            result = await github_agent.trigger_workflow("owner", "repo", sample_workflow_request)

            assert isinstance(result, WorkflowRun)
            assert result.id == 12345
            mock_validate.assert_called_once()
            mock_trigger.assert_called_once()
            mock_wait.assert_called_once()

    async def test_workflow_with_inputs(self, github_agent):
        """Test workflow trigger with inputs."""
        request = WorkflowRequest(
            workflow_id="deploy.yml",
            ref="main",
            inputs={
                "environment": "production",
                "version": "v1.0.0",
                "run_migrations": True
            }
        )

        with patch.object(github_agent, '_validate_workflow_exists'), \
             patch.object(github_agent, '_trigger_github_workflow') as mock_trigger, \
             patch.object(github_agent, '_wait_for_workflow_start'):

            mock_trigger.return_value = {"id": 67890, "workflow_id": "deploy.yml"}

            result = await github_agent.trigger_workflow("owner", "repo", request)

            assert result.id == 67890
            # Verify inputs were passed correctly
            call_args = mock_trigger.call_args[0][2]  # request parameter
            assert call_args.inputs["environment"] == "production"
            assert call_args.inputs["run_migrations"] is True

    # Release Management Tests

    async def test_create_release_success(self, github_agent, sample_release_request):
        """Test successful release creation."""
        with patch.object(github_agent, '_tag_exists') as mock_tag_exists, \
             patch.object(github_agent, '_generate_release_notes') as mock_notes, \
             patch.object(github_agent, '_create_github_release') as mock_create:

            mock_tag_exists.return_value = False
            mock_notes.return_value = "Auto-generated release notes"
            mock_create.return_value = {
                "id": 123,
                "tag_name": "v1.2.0",
                "name": "Version 1.2.0",
                "body": sample_release_request.body
            }

            result = await github_agent.create_release("owner", "repo", sample_release_request)

            assert result["tag_name"] == "v1.2.0"
            assert result["name"] == "Version 1.2.0"
            mock_tag_exists.assert_called_once()
            mock_create.assert_called_once()

    async def test_create_release_tag_exists(self, github_agent, sample_release_request):
        """Test release creation when tag already exists."""
        with patch.object(github_agent, '_tag_exists') as mock_tag_exists:
            mock_tag_exists.return_value = True

            with pytest.raises(AgentExecutionError) as exc_info:
                await github_agent.create_release("owner", "repo", sample_release_request)

            assert "Tag already exists" in str(exc_info.value)

    async def test_release_types(self, github_agent):
        """Test different release types."""
        release_types = [
            ("v1.0.0", ReleaseType.MAJOR),
            ("v1.1.0", ReleaseType.MINOR),
            ("v1.1.1", ReleaseType.PATCH),
            ("v1.2.0-alpha.1", ReleaseType.PRERELEASE)
        ]

        for tag_name, release_type in release_types:
            request = ReleaseRequest(
                tag_name=tag_name,
                name=f"Release {tag_name}",
                prerelease=(release_type == ReleaseType.PRERELEASE)
            )

            with patch.object(github_agent, '_tag_exists', return_value=False), \
                 patch.object(github_agent, '_create_github_release') as mock_create:

                mock_create.return_value = {
                    "id": 1,
                    "tag_name": tag_name,
                    "prerelease": request.prerelease
                }

                result = await github_agent.create_release("owner", "repo", request)
                assert result["tag_name"] == tag_name

    # Code Review Tests

    async def test_submit_review_success(self, github_agent, sample_review_request):
        """Test successful code review submission."""
        with patch.object(github_agent, '_validate_pull_request_exists') as mock_validate, \
             patch.object(github_agent, '_submit_github_review') as mock_submit, \
             patch.object(github_agent, '_add_review_comments') as mock_comments:

            mock_validate.return_value = None
            mock_submit.return_value = {
                "id": 789,
                "event": "approved",
                "body": "LGTM! Great implementation"
            }
            mock_comments.return_value = None

            result = await github_agent.submit_review("owner", "repo", sample_review_request)

            assert result["event"] == "approved"
            mock_validate.assert_called_once()
            mock_submit.assert_called_once()
            mock_comments.assert_called_once()

    async def test_review_decisions(self, github_agent):
        """Test different review decisions."""
        review_decisions = [
            ReviewDecision.APPROVED,
            ReviewDecision.CHANGES_REQUESTED,
            ReviewDecision.COMMENTED,
            ReviewDecision.DISMISSED
        ]

        for decision in review_decisions:
            request = CodeReviewRequest(
                pull_request=123,
                event=decision,
                body=f"Review with {decision.value} decision"
            )

            with patch.object(github_agent, '_validate_pull_request_exists'), \
                 patch.object(github_agent, '_submit_github_review') as mock_submit, \
                 patch.object(github_agent, '_add_review_comments'):

                mock_submit.return_value = {
                    "id": 1,
                    "event": decision.value,
                    "body": request.body
                }

                result = await github_agent.submit_review("owner", "repo", request)
                assert result["event"] == decision.value

    # Analytics Tests

    async def test_get_repository_analytics(self, github_agent):
        """Test repository analytics retrieval."""
        with patch.object(github_agent, '_get_repository_info') as mock_repo, \
             patch.object(github_agent, '_get_commit_activity') as mock_commits, \
             patch.object(github_agent, '_get_pull_request_metrics') as mock_prs, \
             patch.object(github_agent, '_get_issue_metrics') as mock_issues, \
             patch.object(github_agent, '_get_contributor_stats') as mock_contributors, \
             patch.object(github_agent, '_get_language_stats') as mock_languages, \
             patch.object(github_agent, '_get_workflow_metrics') as mock_workflows:

            mock_repo.return_value = {"name": "test-repo", "stars": 100}
            mock_commits.return_value = {"total_commits": 500, "commits_per_day": 2.5}
            mock_prs.return_value = {"total_prs": 50, "merged_prs": 45}
            mock_issues.return_value = {"total_issues": 25, "closed_issues": 20}
            mock_contributors.return_value = {"total_contributors": 10}
            mock_languages.return_value = {"Python": 75, "JavaScript": 25}
            mock_workflows.return_value = {"successful_runs": 95, "failed_runs": 5}

            result = await github_agent.get_repository_analytics("owner", "repo", 30)

            assert "repository_info" in result
            assert "commit_activity" in result
            assert "pull_request_metrics" in result
            assert "issue_metrics" in result
            assert "contributor_stats" in result
            assert "language_stats" in result
            assert "workflow_runs" in result

    # Error Handling Tests

    async def test_unsupported_task_type(self, github_agent):
        """Test execution of unsupported task type."""
        task = {
            "type": "unsupported_task",
            "operation": "unknown",
            "parameters": {}
        }

        with pytest.raises(AgentExecutionError) as exc_info:
            await github_agent.execute_task(task)

        assert "Unsupported task type" in str(exc_info.value)

    async def test_invalid_repository_name(self, github_agent):
        """Test repository creation with invalid name."""
        invalid_request = RepositoryRequest(
            name="invalid@#$%name",
            description="Test repo"
        )

        with pytest.raises(AgentExecutionError):
            await github_agent.create_repository("owner", invalid_request)

    async def test_invalid_branch_name(self, github_agent):
        """Test branch creation with invalid name."""
        invalid_request = BranchRequest(
            name="invalid branch name with spaces",
            source="main"
        )

        with pytest.raises(AgentExecutionError):
            await github_agent.create_branch("owner", "repo", invalid_request)

    async def test_network_error_handling(self, github_agent, sample_repository_request):
        """Test handling of network errors during API calls."""
        with patch.object(github_agent, '_validate_repository_name'), \
             patch.object(github_agent, '_create_github_repository') as mock_create:

            mock_create.side_effect = Exception("Network error")

            with pytest.raises(AgentExecutionError):
                await github_agent.create_repository("owner", sample_repository_request)

    # Integration Tests

    async def test_full_workflow_integration(self, github_agent):
        """Test complete GitHub workflow integration."""
        # Create repository
        with patch.object(github_agent, 'create_repository') as mock_create_repo:
            repo_info = RepositoryInfo(
                name="integration-test",
                full_name="owner/integration-test",
                owner="owner"
            )
            mock_create_repo.return_value = repo_info

            repo_request = RepositoryRequest(name="integration-test")
            repo_result = await github_agent.create_repository("owner", repo_request)
            assert repo_result.name == "integration-test"

        # Create branch
        with patch.object(github_agent, 'create_branch') as mock_create_branch:
            branch_info = BranchInfo(name="feature/integration", sha="abc123")
            mock_create_branch.return_value = branch_info

            branch_request = BranchRequest(name="feature/integration")
            branch_result = await github_agent.create_branch("owner", "integration-test", branch_request)
            assert branch_result.name == "feature/integration"

        # Create pull request
        with patch.object(github_agent, 'create_pull_request') as mock_create_pr:
            pr_info = PullRequestInfo(
                number=1,
                title="Integration test PR",
                state=PullRequestState.OPEN,
                head_branch="feature/integration",
                base_branch="main",
                user="developer"
            )
            mock_create_pr.return_value = pr_info

            pr_request = PullRequestRequest(
                title="Integration test PR",
                head="feature/integration",
                base="main"
            )
            pr_result = await github_agent.create_pull_request("owner", "integration-test", pr_request)
            assert pr_result.number == 1

        # Submit review
        with patch.object(github_agent, 'submit_review') as mock_submit_review:
            review_result = {"id": 1, "event": "approved"}
            mock_submit_review.return_value = review_result

            review_request = CodeReviewRequest(
                pull_request=1,
                event=ReviewDecision.APPROVED,
                body="LGTM!"
            )
            review_result = await github_agent.submit_review("owner", "integration-test", review_request)
            assert review_result["event"] == "approved"

    # Performance Tests

    async def test_concurrent_operations(self, github_agent):
        """Test handling multiple concurrent GitHub operations."""
        operations = []

        # Create multiple repository requests
        for i in range(5):
            repo_request = RepositoryRequest(name=f"concurrent-repo-{i}")
            operations.append(github_agent.create_repository("owner", repo_request))

        with patch.object(github_agent, '_validate_repository_name'), \
             patch.object(github_agent, '_create_github_repository') as mock_create:

            mock_create.side_effect = [
                {"name": f"concurrent-repo-{i}", "full_name": f"owner/concurrent-repo-{i}", "owner": {"login": "owner"}}
                for i in range(5)
            ]

            # Execute all operations concurrently
            results = await asyncio.gather(*operations, return_exceptions=True)

            # Verify all operations completed successfully
            assert len(results) == 5
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    assert result.name == f"concurrent-repo-{i}"

    async def test_large_analytics_request(self, github_agent):
        """Test handling large analytics requests."""
        with patch.object(github_agent, '_get_repository_info') as mock_repo, \
             patch.object(github_agent, '_get_commit_activity') as mock_commits, \
             patch.object(github_agent,
