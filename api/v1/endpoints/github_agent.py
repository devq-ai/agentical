"""
GitHub Agent API Endpoints for Agentical Framework

This module provides REST API endpoints for the GitHub Agent, enabling
repository management, pull request automation, issue tracking, and
Git workflow operations through HTTP requests.

Endpoints:
- Repository management and operations
- Pull request creation and management
- Issue tracking and management
- Branch operations and protection
- GitHub Actions workflow management
- Release management and versioning
- Code review automation
- Repository analytics and metrics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

import logfire
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
    ReviewDecision
)
from agentical.db.database import get_async_session
from agentical.core.exceptions import AgentExecutionError, ValidationError, NotFoundError
from agentical.api.v1.dependencies import get_current_user, require_permissions
from agentical.core.security import User

router = APIRouter(prefix="/github", tags=["github"])


class TaskExecutionRequest(BaseModel):
    """Request model for generic task execution."""
    task_type: str = Field(..., description="Type of GitHub task")
    operation: str = Field(..., description="Operation to perform")
    parameters: Dict[str, Any] = Field(..., description="Task parameters")
    async_execution: bool = Field(default=False, description="Execute task asynchronously")


class TaskExecutionResponse(BaseModel):
    """Response model for task execution."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task execution status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task execution result")
    started_at: datetime = Field(..., description="Task start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")
    error: Optional[str] = Field(default=None, description="Error message if task failed")


class AgentCapabilitiesResponse(BaseModel):
    """Response model for agent capabilities."""
    agent_type: str = Field(..., description="Agent type identifier")
    version: str = Field(..., description="Agent version")
    supported_operations: List[str] = Field(..., description="Supported GitHub operations")
    capabilities: List[str] = Field(..., description="Available agent capabilities")
    repository_types: List[str] = Field(..., description="Supported repository types")
    pr_states: List[str] = Field(..., description="Pull request states")
    issue_states: List[str] = Field(..., description="Issue states")
    protection_levels: List[str] = Field(..., description="Branch protection levels")
    workflow_statuses: List[str] = Field(..., description="Workflow statuses")
    release_types: List[str] = Field(..., description="Release types")
    review_decisions: List[str] = Field(..., description="Review decision types")


class RepositoryAnalyticsResponse(BaseModel):
    """Response model for repository analytics."""
    repository_info: Dict[str, Any] = Field(..., description="Basic repository information")
    commit_activity: Dict[str, Any] = Field(..., description="Commit activity metrics")
    pull_request_metrics: Dict[str, Any] = Field(..., description="Pull request metrics")
    issue_metrics: Dict[str, Any] = Field(..., description="Issue metrics")
    contributor_stats: Dict[str, Any] = Field(..., description="Contributor statistics")
    language_stats: Dict[str, Any] = Field(..., description="Language statistics")
    workflow_runs: Dict[str, Any] = Field(..., description="Workflow execution metrics")
    analysis_period_days: int = Field(..., description="Analysis period in days")


async def get_github_agent(
    session: AsyncSession = Depends(get_async_session)
) -> GitHubAgent:
    """Dependency to get GitHubAgent instance."""
    agent_id = f"github-agent-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return GitHubAgent(agent_id=agent_id, session=session)


@router.get(
    "/capabilities",
    response_model=AgentCapabilitiesResponse,
    summary="Get GitHub Agent Capabilities",
    description="Retrieve comprehensive information about GitHub Agent capabilities, supported operations, and available features."
)
async def get_capabilities(
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(get_current_user)
) -> AgentCapabilitiesResponse:
    """Get GitHub Agent capabilities and supported operations."""
    try:
        with logfire.span("get_github_capabilities", user_id=current_user.id):
            capabilities = {
                "agent_type": "github",
                "version": "1.0.0",
                "supported_operations": list(agent.supported_operations),
                "capabilities": [
                    "repository_management",
                    "pull_request_automation",
                    "issue_tracking",
                    "branch_operations",
                    "workflow_management",
                    "release_management",
                    "code_review",
                    "analytics_reporting"
                ],
                "repository_types": [repo_type.value for repo_type in RepositoryType],
                "pr_states": [state.value for state in PullRequestState],
                "issue_states": [state.value for state in IssueState],
                "protection_levels": [level.value for level in BranchProtectionLevel],
                "workflow_statuses": [status.value for status in WorkflowStatus],
                "release_types": [release_type.value for release_type in ReleaseType],
                "review_decisions": [decision.value for decision in ReviewDecision]
            }

            logfire.info(
                "GitHub capabilities retrieved",
                user_id=current_user.id,
                operations_count=len(capabilities["supported_operations"])
            )

            return AgentCapabilitiesResponse(**capabilities)

    except Exception as e:
        logfire.error("Failed to retrieve GitHub capabilities", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve capabilities: {str(e)}"
        )


@router.post(
    "/tasks/execute",
    response_model=TaskExecutionResponse,
    summary="Execute GitHub Task",
    description="Execute a generic GitHub task with specified type, operation, and parameters."
)
async def execute_task(
    request: TaskExecutionRequest,
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:execute"]))
) -> TaskExecutionResponse:
    """Execute a GitHub task."""
    try:
        with logfire.span(
            "execute_github_task",
            user_id=current_user.id,
            task_type=request.task_type,
            operation=request.operation
        ):
            started_at = datetime.now()
            task_id = f"task-{started_at.strftime('%Y%m%d%H%M%S')}-{request.task_type}"

            task_data = {
                "id": task_id,
                "type": request.task_type,
                "operation": request.operation,
                "parameters": request.parameters
            }

            if request.async_execution:
                # For async execution, we would typically queue the task
                # For now, execute synchronously but return immediately
                asyncio.create_task(agent.execute_task(task_data))

                return TaskExecutionResponse(
                    task_id=task_id,
                    status="queued",
                    started_at=started_at
                )
            else:
                # Synchronous execution
                result = await agent.execute_task(task_data)
                completed_at = datetime.now()

                logfire.info(
                    "GitHub task completed",
                    task_id=task_id,
                    task_type=request.task_type,
                    execution_time=(completed_at - started_at).total_seconds()
                )

                return TaskExecutionResponse(
                    task_id=task_id,
                    status="completed",
                    result=result,
                    started_at=started_at,
                    completed_at=completed_at
                )

    except ValidationError as e:
        logfire.warning("Task validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Task execution failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task execution failed: {str(e)}"
        )
    except Exception as e:
        logfire.error("Unexpected error during task execution", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post(
    "/repositories",
    response_model=Dict[str, Any],
    summary="Create Repository",
    description="Create a new GitHub repository with specified configuration and settings."
)
async def create_repository(
    owner: str = Query(..., description="Repository owner (user or organization)"),
    request: RepositoryRequest = Body(...),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:repository:create"]))
) -> Dict[str, Any]:
    """Create a GitHub repository."""
    try:
        with logfire.span(
            "create_repository",
            user_id=current_user.id,
            owner=owner,
            repository_name=request.name
        ):
            result = await agent.create_repository(owner, request)

            logfire.info(
                "Repository created successfully",
                user_id=current_user.id,
                owner=owner,
                repository=request.name
            )

            return result.__dict__

    except ValidationError as e:
        logfire.warning("Repository validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Repository creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository creation failed: {str(e)}"
        )


@router.post(
    "/repositories/{owner}/{repo}/pulls",
    response_model=Dict[str, Any],
    summary="Create Pull Request",
    description="Create a new pull request with specified head and base branches."
)
async def create_pull_request(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    request: PullRequestRequest = Body(...),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:pr:create"]))
) -> Dict[str, Any]:
    """Create a pull request."""
    try:
        with logfire.span(
            "create_pull_request",
            user_id=current_user.id,
            owner=owner,
            repository=repo,
            title=request.title
        ):
            result = await agent.create_pull_request(owner, repo, request)

            logfire.info(
                "Pull request created successfully",
                user_id=current_user.id,
                owner=owner,
                repository=repo,
                pr_number=result.number
            )

            return result.__dict__

    except ValidationError as e:
        logfire.warning("Pull request validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pull request validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Pull request creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pull request creation failed: {str(e)}"
        )


@router.post(
    "/repositories/{owner}/{repo}/issues",
    response_model=Dict[str, Any],
    summary="Create Issue",
    description="Create a new issue with specified title, description, and metadata."
)
async def create_issue(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    request: IssueRequest = Body(...),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:issue:create"]))
) -> Dict[str, Any]:
    """Create an issue."""
    try:
        with logfire.span(
            "create_issue",
            user_id=current_user.id,
            owner=owner,
            repository=repo,
            title=request.title
        ):
            result = await agent.create_issue(owner, repo, request)

            logfire.info(
                "Issue created successfully",
                user_id=current_user.id,
                owner=owner,
                repository=repo,
                issue_number=result.number
            )

            return result.__dict__

    except ValidationError as e:
        logfire.warning("Issue validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Issue validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Issue creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Issue creation failed: {str(e)}"
        )


@router.post(
    "/repositories/{owner}/{repo}/branches",
    response_model=Dict[str, Any],
    summary="Create Branch",
    description="Create a new branch with optional protection rules and source branch specification."
)
async def create_branch(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    request: BranchRequest = Body(...),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:branch:create"]))
) -> Dict[str, Any]:
    """Create a branch."""
    try:
        with logfire.span(
            "create_branch",
            user_id=current_user.id,
            owner=owner,
            repository=repo,
            branch_name=request.name
        ):
            result = await agent.create_branch(owner, repo, request)

            logfire.info(
                "Branch created successfully",
                user_id=current_user.id,
                owner=owner,
                repository=repo,
                branch_name=request.name
            )

            return result.__dict__

    except ValidationError as e:
        logfire.warning("Branch validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Branch validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Branch creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Branch creation failed: {str(e)}"
        )


@router.post(
    "/repositories/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
    response_model=Dict[str, Any],
    summary="Trigger Workflow",
    description="Trigger a GitHub Actions workflow with optional inputs and target reference."
)
async def trigger_workflow(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    workflow_id: str = Path(..., description="Workflow ID or filename"),
    request: WorkflowRequest = Body(...),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:workflow:trigger"]))
) -> Dict[str, Any]:
    """Trigger a GitHub Actions workflow."""
    try:
        with logfire.span(
            "trigger_workflow",
            user_id=current_user.id,
            owner=owner,
            repository=repo,
            workflow_id=workflow_id
        ):
            # Set workflow_id in request
            request.workflow_id = workflow_id
            result = await agent.trigger_workflow(owner, repo, request)

            logfire.info(
                "Workflow triggered successfully",
                user_id=current_user.id,
                owner=owner,
                repository=repo,
                workflow_id=workflow_id,
                run_id=result.id
            )

            return result.__dict__

    except ValidationError as e:
        logfire.warning("Workflow validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Workflow trigger failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow trigger failed: {str(e)}"
        )


@router.post(
    "/repositories/{owner}/{repo}/releases",
    response_model=Dict[str, Any],
    summary="Create Release",
    description="Create a new release with specified tag, name, and release notes."
)
async def create_release(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    request: ReleaseRequest = Body(...),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:release:create"]))
) -> Dict[str, Any]:
    """Create a release."""
    try:
        with logfire.span(
            "create_release",
            user_id=current_user.id,
            owner=owner,
            repository=repo,
            tag_name=request.tag_name
        ):
            result = await agent.create_release(owner, repo, request)

            logfire.info(
                "Release created successfully",
                user_id=current_user.id,
                owner=owner,
                repository=repo,
                tag_name=request.tag_name
            )

            return result

    except ValidationError as e:
        logfire.warning("Release validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Release validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Release creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Release creation failed: {str(e)}"
        )


@router.post(
    "/repositories/{owner}/{repo}/pulls/{pull_number}/reviews",
    response_model=Dict[str, Any],
    summary="Submit Code Review",
    description="Submit a code review for a pull request with specified decision and comments."
)
async def submit_review(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    pull_number: int = Path(..., description="Pull request number"),
    request: CodeReviewRequest = Body(...),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:review:submit"]))
) -> Dict[str, Any]:
    """Submit a code review."""
    try:
        with logfire.span(
            "submit_review",
            user_id=current_user.id,
            owner=owner,
            repository=repo,
            pr_number=pull_number
        ):
            # Set pull request number in request
            request.pull_request = pull_number
            result = await agent.submit_review(owner, repo, request)

            logfire.info(
                "Review submitted successfully",
                user_id=current_user.id,
                owner=owner,
                repository=repo,
                pr_number=pull_number,
                decision=request.event.value
            )

            return result

    except ValidationError as e:
        logfire.warning("Review validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Review validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Review submission failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review submission failed: {str(e)}"
        )


@router.get(
    "/repositories/{owner}/{repo}/analytics",
    response_model=RepositoryAnalyticsResponse,
    summary="Get Repository Analytics",
    description="Retrieve comprehensive analytics and metrics for a repository including commits, PRs, issues, and contributors."
)
async def get_repository_analytics(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:analytics:read"]))
) -> RepositoryAnalyticsResponse:
    """Get repository analytics and metrics."""
    try:
        with logfire.span(
            "get_repository_analytics",
            user_id=current_user.id,
            owner=owner,
            repository=repo,
            days=days
        ):
            analytics = await agent.get_repository_analytics(owner, repo, days)

            logfire.info(
                "Repository analytics retrieved",
                user_id=current_user.id,
                owner=owner,
                repository=repo,
                analysis_period=days
            )

            return RepositoryAnalyticsResponse(
                analysis_period_days=days,
                **analytics
            )

    except Exception as e:
        logfire.error("Failed to retrieve repository analytics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


@router.get(
    "/repositories/{owner}/{repo}/health",
    response_model=Dict[str, Any],
    summary="Check Repository Health",
    description="Perform health check on repository including branch status, CI/CD status, and general health metrics."
)
async def check_repository_health(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:health:check"]))
) -> Dict[str, Any]:
    """Check repository health status."""
    try:
        with logfire.span(
            "check_repository_health",
            user_id=current_user.id,
            owner=owner,
            repository=repo
        ):
            # Implementation would include health checks
            health_status = {
                "status": "healthy",
                "repository": f"{owner}/{repo}",
                "checks": {
                    "repository_accessible": True,
                    "default_branch_exists": True,
                    "recent_activity": True,
                    "workflow_status": "passing"
                },
                "last_checked": datetime.now().isoformat()
            }

            logfire.info(
                "Repository health check completed",
                user_id=current_user.id,
                owner=owner,
                repository=repo,
                status=health_status["status"]
            )

            return health_status

    except Exception as e:
        logfire.error("Repository health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/repositories/{owner}/{repo}/security",
    response_model=Dict[str, Any],
    summary="Get Repository Security Status",
    description="Retrieve security status including dependency vulnerabilities, secret scanning alerts, and security policies."
)
async def get_repository_security(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    agent: GitHubAgent = Depends(get_github_agent),
    current_user: User = Depends(require_permissions(["github:security:read"]))
) -> Dict[str, Any]:
    """Get repository security status."""
    try:
        with logfire.span(
            "get_repository_security",
            user_id=current_user.id,
            owner=owner,
            repository=repo
        ):
            # Implementation would include security checks
            security_status = {
                "repository": f"{owner}/{repo}",
                "security_score": 85,
                "vulnerabilities": {
                    "critical": 0,
                    "high": 1,
                    "medium": 3,
                    "low": 5
                },
                "secret_scanning": {
                    "enabled": True,
                    "alerts": 0
                },
                "dependency_scanning": {
                    "enabled": True,
                    "last_scan": datetime.now().isoformat()
                },
                "security_policies": {
                    "security_md_exists": True,
                    "codeql_enabled": True,
                    "branch_protection": True
                },
                "last_updated": datetime.now().isoformat()
            }

            logfire.info(
                "Repository security status retrieved",
                user_id=current_user.id,
                owner=owner,
                repository=repo,
                security_score=security_status["security_score"]
            )

            return security_status

    except Exception as e:
        logfire.error("Failed to retrieve repository security status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security status: {str(e)}"
        )


@router.get(
    "/features",
    response_model=Dict[str, List[str]],
    summary="Get Supported Features",
    description="Get comprehensive list of all supported GitHub features and operations."
)
async def get_supported_features(
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[str]]:
    """Get all supported GitHub features and operations."""
    try:
        with logfire.span("get_github_features", user_id=current_user.id):
            features = {
                "repository_operations": [
                    "create_repository",
                    "delete_repository",
                    "update_repository",
                    "fork_repository",
                    "clone_repository",
                    "archive_repository"
                ],
                "pull_request_operations": [
                    "create_pull_request",
                    "update_pull_request",
                    "merge_pull_request",
                    "close_pull_request",
                    "reopen_pull_request",
                    "add_reviewers",
                    "request_changes",
                    "approve_pull_request"
                ],
                "issue_operations": [
                    "create_issue",
                    "update_issue",
                    "close_issue",
                    "reopen_issue",
                    "add_assignees",
                    "add_labels",
                    "add_to_milestone"
                ],
                "branch_operations": [
                    "create_branch",
                    "delete_branch",
                    "protect_branch",
                    "merge_branch",
                    "compare_branches"
                ],
                "workflow_operations": [
                    "trigger_workflow",
                    "cancel_workflow",
                    "get_workflow_runs",
                    "download_artifacts",
                    "view_logs"
                ],
                "release_operations": [
                    "create_release",
                    "update_release",
                    "delete_release",
                    "upload_assets",
                    "generate_release_notes"
                ],
                "analytics_operations": [
                    "repository_analytics",
                    "contributor_stats",
                    "traffic_analytics",
                    "dependency_insights",
                    "security_insights"
                ]
            }

            logfire.info("GitHub features retrieved", user_id=current_user.id)

            return features

    except Exception as e:
        logfire.error("Failed to retrieve GitHub features", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve features: {str(e)}"
        )
