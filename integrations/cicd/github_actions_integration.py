"""
GitHub Actions Integration for Agentical Framework

This module provides comprehensive GitHub Actions integration capabilities,
including workflow creation, management, monitoring, and real-time status updates
for seamless CI/CD pipeline automation within the Agentical ecosystem.

Features:
- GitHub Actions workflow creation and management
- Real-time workflow execution monitoring
- Webhook event processing for status updates
- Artifact and log retrieval
- Advanced workflow templates and customization
- Security and authentication management
- Integration with Agentical workflow engine
"""

import asyncio
import json
import yaml
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field

import httpx
import logfire
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ...core.exceptions import (
    ExternalServiceError,
    ValidationError,
    ConfigurationError,
    AuthenticationError
)
from ...core.logging import log_operation


class GitHubWorkflowStatus(Enum):
    """GitHub Actions workflow statuses."""
    REQUESTED = "requested"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"


class GitHubWorkflowConclusion(Enum):
    """GitHub Actions workflow conclusions."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"


@dataclass
class GitHubWorkflowRun:
    """GitHub Actions workflow run details."""
    id: int
    name: str
    status: GitHubWorkflowStatus
    conclusion: Optional[GitHubWorkflowConclusion]
    workflow_id: int
    head_branch: str
    head_sha: str
    run_number: int
    event: str
    created_at: datetime
    updated_at: datetime
    run_started_at: Optional[datetime] = None
    html_url: Optional[str] = None
    jobs_url: Optional[str] = None
    logs_url: Optional[str] = None
    artifacts_url: Optional[str] = None
    cancel_url: Optional[str] = None
    rerun_url: Optional[str] = None


@dataclass
class GitHubWorkflowJob:
    """GitHub Actions workflow job details."""
    id: int
    run_id: int
    name: str
    status: GitHubWorkflowStatus
    conclusion: Optional[GitHubWorkflowConclusion]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    html_url: str
    steps: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GitHubArtifact:
    """GitHub Actions artifact details."""
    id: int
    name: str
    size_in_bytes: int
    created_at: datetime
    expired: bool
    expires_at: Optional[datetime]
    archive_download_url: str


class GitHubActionsIntegration:
    """
    Comprehensive GitHub Actions integration for Agentical framework.

    Provides full lifecycle management of GitHub Actions workflows including
    creation, monitoring, execution control, and artifact management with
    real-time status updates and seamless integration with Agentical agents.
    """

    def __init__(
        self,
        github_token: str,
        webhook_secret: Optional[str] = None,
        api_url: str = "https://api.github.com"
    ):
        self.github_token = github_token
        self.webhook_secret = webhook_secret
        self.api_url = api_url.rstrip('/')

        # HTTP client with authentication
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Agentical-Framework/1.0"
            },
            timeout=30.0
        )

        # Workflow cache
        self.workflow_cache: Dict[str, Dict[str, Any]] = {}
        self.run_cache: Dict[int, GitHubWorkflowRun] = {}

        # Event handlers
        self.event_handlers: Dict[str, List] = {}

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self.http_client.aclose()

    @log_operation("create_workflow")
    async def create_workflow(
        self,
        owner: str,
        repo: str,
        workflow_name: str,
        workflow_config: Dict[str, Any],
        commit_message: str = None
    ) -> str:
        """
        Create a new GitHub Actions workflow.

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_name: Name of the workflow file
            workflow_config: Workflow configuration
            commit_message: Commit message for workflow file

        Returns:
            Path to created workflow file
        """
        with logfire.span(
            "GitHubActionsIntegration.create_workflow",
            owner=owner,
            repo=repo,
            workflow_name=workflow_name
        ):
            try:
                # Generate workflow YAML
                workflow_yaml = yaml.dump(workflow_config, default_flow_style=False)

                # Determine workflow file path
                workflow_filename = f"{workflow_name}.yml"
                if not workflow_filename.startswith('.github/workflows/'):
                    workflow_path = f".github/workflows/{workflow_filename}"
                else:
                    workflow_path = workflow_filename

                # Check if workflow already exists
                existing_workflow = await self._get_file_content(owner, repo, workflow_path)

                # Prepare commit data
                commit_data = {
                    "message": commit_message or f"Add {workflow_name} workflow",
                    "content": base64.b64encode(workflow_yaml.encode()).decode(),
                    "branch": "main"
                }

                if existing_workflow:
                    # Update existing workflow
                    commit_data["sha"] = existing_workflow["sha"]
                    url = f"{self.api_url}/repos/{owner}/{repo}/contents/{workflow_path}"
                    response = await self.http_client.put(url, json=commit_data)
                else:
                    # Create new workflow
                    url = f"{self.api_url}/repos/{owner}/{repo}/contents/{workflow_path}"
                    response = await self.http_client.put(url, json=commit_data)

                if response.status_code not in [200, 201]:
                    raise ExternalServiceError(
                        f"Failed to create workflow: {response.status_code} {response.text}"
                    )

                result = response.json()
                logfire.info(
                    "GitHub Actions workflow created",
                    path=workflow_path,
                    sha=result["content"]["sha"]
                )

                return workflow_path

            except Exception as e:
                logfire.error("Failed to create GitHub Actions workflow", error=str(e))
                raise

    @log_operation("trigger_workflow")
    async def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: Union[str, int],
        ref: str = "main",
        inputs: Dict[str, Any] = None
    ) -> GitHubWorkflowRun:
        """
        Trigger a workflow dispatch event.

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or filename
            ref: Git reference (branch/tag)
            inputs: Workflow inputs

        Returns:
            Workflow run details
        """
        with logfire.span(
            "GitHubActionsIntegration.trigger_workflow",
            owner=owner,
            repo=repo,
            workflow_id=str(workflow_id)
        ):
            try:
                # Prepare dispatch data
                dispatch_data = {
                    "ref": ref,
                    "inputs": inputs or {}
                }

                # Trigger workflow
                url = f"{self.api_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
                response = await self.http_client.post(url, json=dispatch_data)

                if response.status_code != 204:
                    raise ExternalServiceError(
                        f"Failed to trigger workflow: {response.status_code} {response.text}"
                    )

                # Get the latest run for this workflow
                await asyncio.sleep(2)  # Brief delay for GitHub to process
                runs = await self.list_workflow_runs(owner, repo, workflow_id, per_page=1)

                if not runs:
                    raise ExternalServiceError("No workflow run found after trigger")

                workflow_run = runs[0]
                self.run_cache[workflow_run.id] = workflow_run

                logfire.info(
                    "GitHub Actions workflow triggered",
                    run_id=workflow_run.id,
                    run_number=workflow_run.run_number
                )

                return workflow_run

            except Exception as e:
                logfire.error("Failed to trigger GitHub Actions workflow", error=str(e))
                raise

    @log_operation("get_workflow_run")
    async def get_workflow_run(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> GitHubWorkflowRun:
        """
        Get workflow run details.

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            Workflow run details
        """
        with logfire.span(
            "GitHubActionsIntegration.get_workflow_run",
            owner=owner,
            repo=repo,
            run_id=run_id
        ):
            try:
                # Check cache first
                if run_id in self.run_cache:
                    cached_run = self.run_cache[run_id]
                    # Refresh if status indicates it might have changed
                    if cached_run.status in [GitHubWorkflowStatus.QUEUED, GitHubWorkflowStatus.IN_PROGRESS]:
                        pass  # Continue to refresh
                    else:
                        return cached_run

                # Fetch from GitHub API
                url = f"{self.api_url}/repos/{owner}/{repo}/actions/runs/{run_id}"
                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to get workflow run: {response.status_code} {response.text}"
                    )

                data = response.json()
                workflow_run = self._parse_workflow_run(data)

                # Update cache
                self.run_cache[run_id] = workflow_run

                return workflow_run

            except Exception as e:
                logfire.error("Failed to get GitHub Actions workflow run", error=str(e))
                raise

    @log_operation("list_workflow_runs")
    async def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: Optional[Union[str, int]] = None,
        status: Optional[GitHubWorkflowStatus] = None,
        per_page: int = 30,
        page: int = 1
    ) -> List[GitHubWorkflowRun]:
        """
        List workflow runs.

        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Optional workflow ID filter
            status: Optional status filter
            per_page: Results per page
            page: Page number

        Returns:
            List of workflow runs
        """
        with logfire.span(
            "GitHubActionsIntegration.list_workflow_runs",
            owner=owner,
            repo=repo
        ):
            try:
                # Build URL and parameters
                if workflow_id:
                    url = f"{self.api_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
                else:
                    url = f"{self.api_url}/repos/{owner}/{repo}/actions/runs"

                params = {
                    "per_page": per_page,
                    "page": page
                }

                if status:
                    params["status"] = status.value

                # Fetch from GitHub API
                response = await self.http_client.get(url, params=params)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to list workflow runs: {response.status_code} {response.text}"
                    )

                data = response.json()
                workflow_runs = [
                    self._parse_workflow_run(run_data)
                    for run_data in data["workflow_runs"]
                ]

                # Update cache
                for run in workflow_runs:
                    self.run_cache[run.id] = run

                return workflow_runs

            except Exception as e:
                logfire.error("Failed to list GitHub Actions workflow runs", error=str(e))
                raise

    @log_operation("cancel_workflow_run")
    async def cancel_workflow_run(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> bool:
        """
        Cancel a workflow run.

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            True if cancelled successfully
        """
        with logfire.span(
            "GitHubActionsIntegration.cancel_workflow_run",
            owner=owner,
            repo=repo,
            run_id=run_id
        ):
            try:
                url = f"{self.api_url}/repos/{owner}/{repo}/actions/runs/{run_id}/cancel"
                response = await self.http_client.post(url)

                if response.status_code == 202:
                    # Update cache
                    if run_id in self.run_cache:
                        self.run_cache[run_id].status = GitHubWorkflowStatus.COMPLETED
                        self.run_cache[run_id].conclusion = GitHubWorkflowConclusion.CANCELLED

                    logfire.info("GitHub Actions workflow run cancelled", run_id=run_id)
                    return True
                else:
                    logfire.warning(
                        "Failed to cancel workflow run",
                        run_id=run_id,
                        status_code=response.status_code
                    )
                    return False

            except Exception as e:
                logfire.error("Failed to cancel GitHub Actions workflow run", error=str(e))
                return False

    @log_operation("get_workflow_jobs")
    async def get_workflow_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> List[GitHubWorkflowJob]:
        """
        Get jobs for a workflow run.

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            List of workflow jobs
        """
        with logfire.span(
            "GitHubActionsIntegration.get_workflow_jobs",
            owner=owner,
            repo=repo,
            run_id=run_id
        ):
            try:
                url = f"{self.api_url}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to get workflow jobs: {response.status_code} {response.text}"
                    )

                data = response.json()
                jobs = [self._parse_workflow_job(job_data) for job_data in data["jobs"]]

                return jobs

            except Exception as e:
                logfire.error("Failed to get GitHub Actions workflow jobs", error=str(e))
                raise

    @log_operation("get_workflow_logs")
    async def get_workflow_logs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        job_id: Optional[int] = None
    ) -> str:
        """
        Download workflow run logs.

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID
            job_id: Optional specific job ID

        Returns:
            Log content as string
        """
        with logfire.span(
            "GitHubActionsIntegration.get_workflow_logs",
            owner=owner,
            repo=repo,
            run_id=run_id
        ):
            try:
                if job_id:
                    url = f"{self.api_url}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
                else:
                    url = f"{self.api_url}/repos/{owner}/{repo}/actions/runs/{run_id}/logs"

                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to get workflow logs: {response.status_code} {response.text}"
                    )

                # GitHub returns logs as plain text
                return response.text

            except Exception as e:
                logfire.error("Failed to get GitHub Actions workflow logs", error=str(e))
                raise

    @log_operation("list_workflow_artifacts")
    async def list_workflow_artifacts(
        self,
        owner: str,
        repo: str,
        run_id: int
    ) -> List[GitHubArtifact]:
        """
        List artifacts for a workflow run.

        Args:
            owner: Repository owner
            repo: Repository name
            run_id: Workflow run ID

        Returns:
            List of artifacts
        """
        with logfire.span(
            "GitHubActionsIntegration.list_workflow_artifacts",
            owner=owner,
            repo=repo,
            run_id=run_id
        ):
            try:
                url = f"{self.api_url}/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to list artifacts: {response.status_code} {response.text}"
                    )

                data = response.json()
                artifacts = [self._parse_artifact(artifact_data) for artifact_data in data["artifacts"]]

                return artifacts

            except Exception as e:
                logfire.error("Failed to list GitHub Actions workflow artifacts", error=str(e))
                raise

    @log_operation("download_artifact")
    async def download_artifact(
        self,
        owner: str,
        repo: str,
        artifact_id: int
    ) -> bytes:
        """
        Download workflow artifact.

        Args:
            owner: Repository owner
            repo: Repository name
            artifact_id: Artifact ID

        Returns:
            Artifact content as bytes
        """
        with logfire.span(
            "GitHubActionsIntegration.download_artifact",
            owner=owner,
            repo=repo,
            artifact_id=artifact_id
        ):
            try:
                url = f"{self.api_url}/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"
                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to download artifact: {response.status_code} {response.text}"
                    )

                return response.content

            except Exception as e:
                logfire.error("Failed to download GitHub Actions artifact", error=str(e))
                raise

    async def handle_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> bool:
        """
        Handle GitHub webhook event.

        Args:
            payload: Webhook payload
            headers: HTTP headers

        Returns:
            True if processed successfully
        """
        with logfire.span("GitHubActionsIntegration.handle_webhook"):
            try:
                # Verify webhook signature if secret is configured
                if self.webhook_secret:
                    if not self._verify_webhook_signature(payload, headers):
                        logfire.warning("GitHub webhook signature verification failed")
                        return False

                # Extract event information
                event_type = headers.get("X-GitHub-Event", "unknown")
                action = payload.get("action")

                # Handle workflow run events
                if event_type == "workflow_run":
                    await self._handle_workflow_run_event(payload)
                elif event_type == "workflow_job":
                    await self._handle_workflow_job_event(payload)
                else:
                    logfire.debug(f"Unhandled GitHub webhook event: {event_type}")

                return True

            except Exception as e:
                logfire.error("Failed to handle GitHub webhook", error=str(e))
                return False

    def generate_workflow_template(
        self,
        template_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate workflow template based on type and configuration.

        Args:
            template_type: Type of template (ci, cd, test, security, etc.)
            config: Template configuration

        Returns:
            Workflow configuration dictionary
        """
        if template_type == "ci":
            return self._generate_ci_template(config)
        elif template_type == "cd":
            return self._generate_cd_template(config)
        elif template_type == "test":
            return self._generate_test_template(config)
        elif template_type == "security":
            return self._generate_security_template(config)
        elif template_type == "docker":
            return self._generate_docker_template(config)
        else:
            raise ValidationError(f"Unknown template type: {template_type}")

    def on_event(self, event_type: str, handler) -> None:
        """Register event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    # Private methods

    async def _get_file_content(self, owner: str, repo: str, path: str) -> Optional[Dict[str, Any]]:
        """Get file content from repository."""
        try:
            url = f"{self.api_url}/repos/{owner}/{repo}/contents/{path}"
            response = await self.http_client.get(url)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise ExternalServiceError(f"Failed to get file content: {response.status_code}")
        except Exception:
            return None

    def _parse_workflow_run(self, data: Dict[str, Any]) -> GitHubWorkflowRun:
        """Parse workflow run data from GitHub API."""
        return GitHubWorkflowRun(
            id=data["id"],
            name=data["name"],
            status=GitHubWorkflowStatus(data["status"]),
            conclusion=GitHubWorkflowConclusion(data["conclusion"]) if data["conclusion"] else None,
            workflow_id=data["workflow_id"],
            head_branch=data["head_branch"],
            head_sha=data["head_sha"],
            run_number=data["run_number"],
            event=data["event"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            run_started_at=datetime.fromisoformat(data["run_started_at"].replace("Z", "+00:00")) if data.get("run_started_at") else None,
            html_url=data["html_url"],
            jobs_url=data["jobs_url"],
            logs_url=data["logs_url"],
            artifacts_url=data["artifacts_url"],
            cancel_url=data["cancel_url"],
            rerun_url=data["rerun_url"]
        )

    def _parse_workflow_job(self, data: Dict[str, Any]) -> GitHubWorkflowJob:
        """Parse workflow job data from GitHub API."""
        return GitHubWorkflowJob(
            id=data["id"],
            run_id=data["run_id"],
            name=data["name"],
            status=GitHubWorkflowStatus(data["status"]),
            conclusion=GitHubWorkflowConclusion(data["conclusion"]) if data["conclusion"] else None,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            started_at=datetime.fromisoformat(data["started_at"].replace("Z", "+00:00")) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00")) if data.get("completed_at") else None,
            html_url=data["html_url"],
            steps=data.get("steps", [])
        )

    def _parse_artifact(self, data: Dict[str, Any]) -> GitHubArtifact:
        """Parse artifact data from GitHub API."""
        return GitHubArtifact(
            id=data["id"],
            name=data["name"],
            size_in_bytes=data["size_in_bytes"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            expired=data["expired"],
            expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")) if data.get("expires_at") else None,
            archive_download_url=data["archive_download_url"]
        )

    def _verify_webhook_signature(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Verify GitHub webhook signature."""
        signature = headers.get("X-Hub-Signature-256")
        if not signature:
            return False

        # Implementation would verify HMAC signature
        # This is a simplified version
        return True

    async def _handle_workflow_run_event(self, payload: Dict[str, Any]) -> None:
        """Handle workflow run webhook event."""
        action = payload.get("action")
        workflow_run_data = payload.get("workflow_run", {})

        if not workflow_run_data:
            return

        # Parse and cache workflow run
        workflow_run = self._parse_workflow_run(workflow_run_data)
        self.run_cache[workflow_run.id] = workflow_run

        # Emit event to handlers
        await self._emit_event(f"workflow_run_{action}", {
            "workflow_run": workflow_run,
            "action": action,
            "repository": payload.get("repository", {})
        })

    async def _handle_workflow_job_event(self, payload: Dict[str, Any]) -> None:
        """Handle workflow job webhook event."""
        action = payload.get("action")
        workflow_job_data = payload.get("workflow_job", {})

        if not workflow_job_data:
            return

        # Parse workflow job
        workflow_job = self._parse_workflow_job(workflow_job_data)

        # Emit event to handlers
        await self._emit_event(f"workflow_job_{action}", {
            "workflow_job": workflow_job,
            "action": action,
            "repository": payload.get("repository", {})
        })

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit event to registered handlers."""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logfire.error(f"Event handler error for {event_type}", error=str(e))

    def _generate_ci_template(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CI workflow template."""
        language = config.get("language", "python")

        workflow = {
            "name": "Continuous Integration",
            "on": {
                "push": {"branches": ["main", "develop"]},
                "pull_request": {"branches": ["main"]}
            },
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "strategy": {
                        "matrix": {
                            "python-version": ["3.9", "3.10", "3.11"]
                        }
                    },
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {"python-version": "${{ matrix.python-version }}"}
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -r requirements.txt"
                        },
                        {
                            "name": "Run tests",
                            "run": "pytest tests/ --cov=src/ --cov-report=xml"
                        },
                        {
                            "name": "Upload coverage",
                            "uses": "codecov/codecov-action@v3"
                        }
                    ]
                }
            }
        }

        return workflow

    def _generate_cd_template(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CD workflow template."""
        return {
            "name": "Continuous Deployment",
            "on": {
                "push": {"branches": ["main"]},
                "release": {"types": ["created"]}
            },
            "jobs": {
                "deploy": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Build Docker image",
                            "run": "docker build -t ${{ github.repository }}:${{ github.sha }} ."
                        },
                        {
                            "name": "Deploy to staging",
                            "run": "echo 'Deploying to staging environment'"
                        }
                    ]
                }
            }
        }

    def _generate_test_template(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test workflow template."""
        return {
            "name": "Test Suite",
            "on": ["push", "pull_request"],
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Run unit tests",
                            "run": "pytest tests/unit/"
                        },
                        {
                            "name": "Run integration tests",
                            "run": "pytest tests/integration/"
                        }
                    ]
                }
            }
        }

    def _generate_security_template(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security workflow template."""
        return {
            "name": "Security Scan",
            "on": ["push", "pull_request"],
            "jobs": {
                "security": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@
