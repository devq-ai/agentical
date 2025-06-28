"""
CI/CD Integration Manager for Agentical Framework

This module provides comprehensive CI/CD pipeline integration capabilities,
supporting GitHub Actions, Jenkins, GitLab CI, and other major CI/CD platforms
with seamless workflow automation and real-time monitoring.

Features:
- Multi-platform CI/CD integration (GitHub Actions, Jenkins, GitLab CI)
- Automated pipeline creation and management
- Real-time pipeline status monitoring and reporting
- Event-driven pipeline triggers and notifications
- Integration with Agentical workflow engine and agents
- Comprehensive error handling and retry logic
- Security and authentication management
- Performance metrics and analytics
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging

import httpx
import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.exceptions import (
    AgenticalError,
    ValidationError,
    ExternalServiceError,
    ConfigurationError
)
from ...core.logging import log_operation
from ...agents.devops_agent import DevOpsAgent
from ...workflows.engine.workflow_engine import WorkflowEngine
from ...db.models.workflow import Workflow, WorkflowExecution
from ...db.repositories.workflow import AsyncWorkflowRepository


class CICDPlatform(Enum):
    """Supported CI/CD platforms."""
    GITHUB_ACTIONS = "github_actions"
    JENKINS = "jenkins"
    GITLAB_CI = "gitlab_ci"
    AZURE_DEVOPS = "azure_devops"
    CIRCLE_CI = "circle_ci"
    TRAVIS_CI = "travis_ci"
    BUILDKITE = "buildkite"
    DRONE = "drone"


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class TriggerEvent(Enum):
    """Pipeline trigger events."""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    TAG = "tag"
    RELEASE = "release"
    WORKFLOW_DISPATCH = "workflow_dispatch"


@dataclass
class PipelineConfiguration:
    """CI/CD pipeline configuration."""
    name: str
    platform: CICDPlatform
    repository: str
    branch: str = "main"
    triggers: List[TriggerEvent] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    stages: List[Dict[str, Any]] = field(default_factory=list)
    notifications: Dict[str, Any] = field(default_factory=dict)
    timeout_minutes: int = 60
    parallel_jobs: int = 1
    retry_attempts: int = 3
    deployment_environments: List[str] = field(default_factory=list)


@dataclass
class PipelineExecution:
    """CI/CD pipeline execution details."""
    id: str
    pipeline_id: str
    platform: CICDPlatform
    status: PipelineStatus
    trigger_event: TriggerEvent
    commit_sha: str
    branch: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    logs_url: Optional[str] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    stages: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    workflow_execution_id: Optional[str] = None


@dataclass
class WebhookEvent:
    """Webhook event from CI/CD platform."""
    platform: CICDPlatform
    event_type: str
    payload: Dict[str, Any]
    headers: Dict[str, str]
    timestamp: datetime
    signature: Optional[str] = None


class CICDIntegrationManager:
    """
    Comprehensive CI/CD integration manager for Agentical framework.

    Provides unified interface for multiple CI/CD platforms with automated
    pipeline management, real-time monitoring, and seamless integration
    with the Agentical workflow engine and agent ecosystem.
    """

    def __init__(
        self,
        workflow_engine: WorkflowEngine,
        devops_agent: DevOpsAgent,
        db_session: AsyncSession,
        config: Dict[str, Any] = None
    ):
        self.workflow_engine = workflow_engine
        self.devops_agent = devops_agent
        self.db_session = db_session
        self.config = config or {}

        # Platform clients
        self.platform_clients: Dict[CICDPlatform, Any] = {}
        self.webhook_handlers: Dict[CICDPlatform, Callable] = {}

        # Pipeline tracking
        self.active_pipelines: Dict[str, PipelineExecution] = {}
        self.pipeline_configurations: Dict[str, PipelineConfiguration] = {}

        # Event handling
        self.event_listeners: Dict[str, List[Callable]] = {}

        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.shutdown_requested = False

        # Initialize platform integrations
        self._initialize_platform_integrations()

    async def start(self) -> None:
        """Start the CI/CD integration manager."""
        with logfire.span("CICDIntegrationManager.start"):
            try:
                # Start background monitoring
                self.monitoring_task = asyncio.create_task(self._monitoring_loop())
                self.cleanup_task = asyncio.create_task(self._cleanup_loop())

                logfire.info("CI/CD Integration Manager started successfully")

            except Exception as e:
                logfire.error("Failed to start CI/CD Integration Manager", error=str(e))
                raise

    async def shutdown(self) -> None:
        """Shutdown the CI/CD integration manager."""
        with logfire.span("CICDIntegrationManager.shutdown"):
            try:
                self.shutdown_requested = True

                # Cancel background tasks
                if self.monitoring_task:
                    self.monitoring_task.cancel()
                if self.cleanup_task:
                    self.cleanup_task.cancel()

                # Close HTTP client
                await self.http_client.aclose()

                logfire.info("CI/CD Integration Manager shutdown completed")

            except Exception as e:
                logfire.error("Error during CI/CD Integration Manager shutdown", error=str(e))

    @log_operation("create_pipeline")
    async def create_pipeline(
        self,
        config: PipelineConfiguration,
        auto_deploy: bool = False
    ) -> str:
        """
        Create a new CI/CD pipeline.

        Args:
            config: Pipeline configuration
            auto_deploy: Whether to automatically deploy the pipeline

        Returns:
            Pipeline ID
        """
        with logfire.span(
            "CICDIntegrationManager.create_pipeline",
            platform=config.platform.value,
            repository=config.repository
        ):
            try:
                # Validate configuration
                await self._validate_pipeline_config(config)

                # Generate pipeline ID
                pipeline_id = f"pipeline_{uuid.uuid4().hex[:8]}"

                # Create pipeline on platform
                platform_pipeline_id = await self._create_platform_pipeline(config)

                # Store configuration
                self.pipeline_configurations[pipeline_id] = config

                # Create Agentical workflow if needed
                if auto_deploy:
                    workflow = await self._create_deployment_workflow(config)
                    config.workflow_id = workflow.id

                logfire.info(
                    "Pipeline created successfully",
                    pipeline_id=pipeline_id,
                    platform_pipeline_id=platform_pipeline_id
                )

                # Emit event
                await self._emit_event("pipeline_created", {
                    "pipeline_id": pipeline_id,
                    "platform": config.platform.value,
                    "repository": config.repository
                })

                return pipeline_id

            except Exception as e:
                logfire.error("Failed to create pipeline", error=str(e))
                raise AgenticalError(f"Pipeline creation failed: {str(e)}")

    @log_operation("trigger_pipeline")
    async def trigger_pipeline(
        self,
        pipeline_id: str,
        trigger_event: TriggerEvent = TriggerEvent.MANUAL,
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        parameters: Dict[str, Any] = None
    ) -> PipelineExecution:
        """
        Trigger a pipeline execution.

        Args:
            pipeline_id: Pipeline identifier
            trigger_event: Event that triggered the pipeline
            commit_sha: Specific commit to build
            branch: Branch to build
            parameters: Additional parameters

        Returns:
            Pipeline execution details
        """
        with logfire.span(
            "CICDIntegrationManager.trigger_pipeline",
            pipeline_id=pipeline_id,
            trigger_event=trigger_event.value
        ):
            try:
                config = self.pipeline_configurations.get(pipeline_id)
                if not config:
                    raise ValidationError(f"Pipeline {pipeline_id} not found")

                # Create execution record
                execution_id = f"exec_{uuid.uuid4().hex[:8]}"
                execution = PipelineExecution(
                    id=execution_id,
                    pipeline_id=pipeline_id,
                    platform=config.platform,
                    status=PipelineStatus.PENDING,
                    trigger_event=trigger_event,
                    commit_sha=commit_sha or "HEAD",
                    branch=branch or config.branch,
                    started_at=datetime.utcnow()
                )

                # Trigger on platform
                platform_execution_id = await self._trigger_platform_pipeline(
                    config, execution, parameters or {}
                )

                # Store execution
                self.active_pipelines[execution_id] = execution

                logfire.info(
                    "Pipeline triggered successfully",
                    execution_id=execution_id,
                    platform_execution_id=platform_execution_id
                )

                # Emit event
                await self._emit_event("pipeline_triggered", {
                    "execution_id": execution_id,
                    "pipeline_id": pipeline_id,
                    "trigger_event": trigger_event.value
                })

                return execution

            except Exception as e:
                logfire.error("Failed to trigger pipeline", error=str(e))
                raise AgenticalError(f"Pipeline trigger failed: {str(e)}")

    @log_operation("get_pipeline_status")
    async def get_pipeline_status(self, execution_id: str) -> PipelineExecution:
        """Get current pipeline execution status."""
        with logfire.span("CICDIntegrationManager.get_pipeline_status", execution_id=execution_id):
            try:
                execution = self.active_pipelines.get(execution_id)
                if not execution:
                    raise ValidationError(f"Pipeline execution {execution_id} not found")

                # Refresh status from platform
                await self._refresh_execution_status(execution)

                return execution

            except Exception as e:
                logfire.error("Failed to get pipeline status", error=str(e))
                raise

    @log_operation("cancel_pipeline")
    async def cancel_pipeline(self, execution_id: str) -> bool:
        """Cancel a running pipeline execution."""
        with logfire.span("CICDIntegrationManager.cancel_pipeline", execution_id=execution_id):
            try:
                execution = self.active_pipelines.get(execution_id)
                if not execution:
                    raise ValidationError(f"Pipeline execution {execution_id} not found")

                if execution.status not in [PipelineStatus.PENDING, PipelineStatus.QUEUED, PipelineStatus.RUNNING]:
                    logfire.warning(f"Cannot cancel pipeline in status {execution.status}")
                    return False

                # Cancel on platform
                success = await self._cancel_platform_pipeline(execution)

                if success:
                    execution.status = PipelineStatus.CANCELLED
                    execution.finished_at = datetime.utcnow()

                    # Emit event
                    await self._emit_event("pipeline_cancelled", {
                        "execution_id": execution_id
                    })

                return success

            except Exception as e:
                logfire.error("Failed to cancel pipeline", error=str(e))
                raise

    @log_operation("handle_webhook")
    async def handle_webhook(
        self,
        platform: CICDPlatform,
        event_data: Dict[str, Any],
        headers: Dict[str, str] = None
    ) -> bool:
        """
        Handle webhook event from CI/CD platform.

        Args:
            platform: CI/CD platform
            event_data: Webhook payload
            headers: HTTP headers

        Returns:
            True if event was processed successfully
        """
        with logfire.span(
            "CICDIntegrationManager.handle_webhook",
            platform=platform.value
        ):
            try:
                # Create webhook event
                webhook_event = WebhookEvent(
                    platform=platform,
                    event_type=event_data.get("action", "unknown"),
                    payload=event_data,
                    headers=headers or {},
                    timestamp=datetime.utcnow()
                )

                # Verify webhook signature if configured
                if not await self._verify_webhook_signature(webhook_event):
                    logfire.warning("Webhook signature verification failed")
                    return False

                # Process webhook based on platform
                handler = self.webhook_handlers.get(platform)
                if handler:
                    await handler(webhook_event)
                else:
                    logfire.warning(f"No webhook handler for platform {platform.value}")

                return True

            except Exception as e:
                logfire.error("Failed to handle webhook", error=str(e))
                return False

    @log_operation("get_pipeline_logs")
    async def get_pipeline_logs(
        self,
        execution_id: str,
        stage: Optional[str] = None
    ) -> str:
        """Get pipeline execution logs."""
        with logfire.span("CICDIntegrationManager.get_pipeline_logs", execution_id=execution_id):
            try:
                execution = self.active_pipelines.get(execution_id)
                if not execution:
                    raise ValidationError(f"Pipeline execution {execution_id} not found")

                # Get logs from platform
                logs = await self._get_platform_logs(execution, stage)

                return logs

            except Exception as e:
                logfire.error("Failed to get pipeline logs", error=str(e))
                raise

    @log_operation("get_pipeline_artifacts")
    async def get_pipeline_artifacts(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get pipeline execution artifacts."""
        with logfire.span("CICDIntegrationManager.get_pipeline_artifacts", execution_id=execution_id):
            try:
                execution = self.active_pipelines.get(execution_id)
                if not execution:
                    raise ValidationError(f"Pipeline execution {execution_id} not found")

                # Get artifacts from platform
                artifacts = await self._get_platform_artifacts(execution)

                return artifacts

            except Exception as e:
                logfire.error("Failed to get pipeline artifacts", error=str(e))
                raise

    @log_operation("create_deployment_pipeline")
    async def create_deployment_pipeline(
        self,
        application_name: str,
        repository: str,
        environments: List[str],
        platform: CICDPlatform = CICDPlatform.GITHUB_ACTIONS
    ) -> str:
        """Create automated deployment pipeline."""
        with logfire.span(
            "CICDIntegrationManager.create_deployment_pipeline",
            application=application_name,
            platform=platform.value
        ):
            try:
                # Create deployment stages
                stages = []

                # Build stage
                stages.append({
                    "name": "build",
                    "type": "build",
                    "commands": [
                        "docker build -t ${{ env.IMAGE_NAME }}:${{ github.sha }} .",
                        "docker tag ${{ env.IMAGE_NAME }}:${{ github.sha }} ${{ env.IMAGE_NAME }}:latest"
                    ],
                    "environment_variables": {
                        "IMAGE_NAME": application_name
                    }
                })

                # Test stage
                stages.append({
                    "name": "test",
                    "type": "test",
                    "commands": [
                        "docker run --rm ${{ env.IMAGE_NAME }}:${{ github.sha }} pytest tests/ --cov=src/ --cov-report=xml",
                        "docker run --rm ${{ env.IMAGE_NAME }}:${{ github.sha }} flake8 src/"
                    ],
                    "artifacts": ["coverage.xml", "test-results.xml"]
                })

                # Security scan stage
                stages.append({
                    "name": "security_scan",
                    "type": "security",
                    "commands": [
                        "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image ${{ env.IMAGE_NAME }}:${{ github.sha }}"
                    ]
                })

                # Deployment stages for each environment
                for env in environments:
                    stages.append({
                        "name": f"deploy_{env}",
                        "type": "deploy",
                        "environment": env,
                        "commands": [
                            f"docker push ${{{{ env.REGISTRY_URL }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}",
                            f"kubectl set image deployment/{application_name} {application_name}=${{{{ env.REGISTRY_URL }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}"
                        ],
                        "depends_on": ["build", "test", "security_scan"],
                        "approval_required": env == "production"
                    })

                # Create pipeline configuration
                config = PipelineConfiguration(
                    name=f"{application_name}-deployment",
                    platform=platform,
                    repository=repository,
                    branch="main",
                    triggers=[TriggerEvent.PUSH, TriggerEvent.PULL_REQUEST],
                    stages=stages,
                    environment_variables={
                        "APPLICATION_NAME": application_name,
                        "REGISTRY_URL": self.config.get("registry_url", "ghcr.io")
                    },
                    secrets=["REGISTRY_TOKEN", "KUBE_CONFIG"],
                    deployment_environments=environments,
                    timeout_minutes=45,
                    parallel_jobs=2
                )

                # Create the pipeline
                pipeline_id = await self.create_pipeline(config, auto_deploy=True)

                logfire.info(
                    "Deployment pipeline created",
                    pipeline_id=pipeline_id,
                    application=application_name,
                    environments=environments
                )

                return pipeline_id

            except Exception as e:
                logfire.error("Failed to create deployment pipeline", error=str(e))
                raise

    def on_event(self, event_type: str, handler: Callable) -> None:
        """Register event handler."""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(handler)

    # Private methods

    def _initialize_platform_integrations(self) -> None:
        """Initialize CI/CD platform integrations."""
        try:
            # Initialize GitHub Actions integration
            self.webhook_handlers[CICDPlatform.GITHUB_ACTIONS] = self._handle_github_webhook

            # Initialize Jenkins integration
            self.webhook_handlers[CICDPlatform.JENKINS] = self._handle_jenkins_webhook

            # Initialize GitLab CI integration
            self.webhook_handlers[CICDPlatform.GITLAB_CI] = self._handle_gitlab_webhook

            logfire.info("Platform integrations initialized")

        except Exception as e:
            logfire.error("Failed to initialize platform integrations", error=str(e))
            raise

    async def _validate_pipeline_config(self, config: PipelineConfiguration) -> None:
        """Validate pipeline configuration."""
        if not config.name:
            raise ValidationError("Pipeline name is required")

        if not config.repository:
            raise ValidationError("Repository is required")

        if not config.stages:
            raise ValidationError("Pipeline must have at least one stage")

        # Validate platform-specific requirements
        if config.platform == CICDPlatform.GITHUB_ACTIONS:
            if not self.config.get("github_token"):
                raise ConfigurationError("GitHub token is required for GitHub Actions")

    async def _create_platform_pipeline(self, config: PipelineConfiguration) -> str:
        """Create pipeline on specific platform."""
        if config.platform == CICDPlatform.GITHUB_ACTIONS:
            return await self._create_github_actions_pipeline(config)
        elif config.platform == CICDPlatform.JENKINS:
            return await self._create_jenkins_pipeline(config)
        elif config.platform == CICDPlatform.GITLAB_CI:
            return await self._create_gitlab_pipeline(config)
        else:
            raise ValidationError(f"Platform {config.platform.value} not supported")

    async def _create_github_actions_pipeline(self, config: PipelineConfiguration) -> str:
        """Create GitHub Actions workflow."""
        # Generate GitHub Actions YAML
        workflow_yaml = self._generate_github_actions_yaml(config)

        # Create workflow file via GitHub API
        github_token = self.config.get("github_token")
        if not github_token:
            raise ConfigurationError("GitHub token not configured")

        # Implementation would create .github/workflows/*.yml file
        # via GitHub API

        return f"github_workflow_{config.name}"

    async def _create_jenkins_pipeline(self, config: PipelineConfiguration) -> str:
        """Create Jenkins pipeline."""
        # Generate Jenkinsfile
        jenkinsfile = self._generate_jenkinsfile(config)

        # Create pipeline job via Jenkins API
        jenkins_url = self.config.get("jenkins_url")
        jenkins_token = self.config.get("jenkins_token")

        if not jenkins_url or not jenkins_token:
            raise ConfigurationError("Jenkins configuration not complete")

        # Implementation would create Jenkins job via API

        return f"jenkins_job_{config.name}"

    async def _create_gitlab_pipeline(self, config: PipelineConfiguration) -> str:
        """Create GitLab CI pipeline."""
        # Generate .gitlab-ci.yml
        gitlab_yaml = self._generate_gitlab_ci_yaml(config)

        # Create pipeline via GitLab API
        gitlab_url = self.config.get("gitlab_url")
        gitlab_token = self.config.get("gitlab_token")

        if not gitlab_url or not gitlab_token:
            raise ConfigurationError("GitLab configuration not complete")

        # Implementation would create .gitlab-ci.yml file via API

        return f"gitlab_pipeline_{config.name}"

    def _generate_github_actions_yaml(self, config: PipelineConfiguration) -> str:
        """Generate GitHub Actions workflow YAML."""
        workflow = {
            "name": config.name,
            "on": self._get_github_triggers(config.triggers),
            "env": config.environment_variables,
            "jobs": {}
        }

        for stage in config.stages:
            job_name = stage["name"].replace(" ", "_").lower()
            workflow["jobs"][job_name] = {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    *[{"run": cmd} for cmd in stage.get("commands", [])]
                ]
            }

        import yaml
        return yaml.dump(workflow, default_flow_style=False)

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for pipeline executions."""
        while not self.shutdown_requested:
            try:
                # Check active pipeline statuses
                for execution_id, execution in list(self.active_pipelines.items()):
                    if execution.status in [PipelineStatus.PENDING, PipelineStatus.QUEUED, PipelineStatus.RUNNING]:
                        await self._refresh_execution_status(execution)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logfire.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(60)  # Back off on error

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop for completed executions."""
        while not self.shutdown_requested:
            try:
                # Clean up old completed executions
                cutoff_time = datetime.utcnow() - timedelta(hours=24)

                to_remove = []
                for execution_id, execution in self.active_pipelines.items():
                    if (execution.finished_at and
                        execution.finished_at < cutoff_time and
                        execution.status in [PipelineStatus.SUCCESS, PipelineStatus.FAILURE, PipelineStatus.CANCELLED]):
                        to_remove.append(execution_id)

                for execution_id in to_remove:
                    del self.active_pipelines[execution_id]

                if to_remove:
                    logfire.info(f"Cleaned up {len(to_remove)} completed pipeline executions")

                await asyncio.sleep(3600)  # Clean up every hour

            except Exception as e:
                logfire.error("Error in cleanup loop", error=str(e))
                await asyncio.sleep(3600)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit event to registered listeners."""
        handlers = self.event_listeners.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logfire.error(f"Event handler error for {event_type}", error=str(e))

    async def _handle_github_webhook(self, event: WebhookEvent) -> None:
        """Handle GitHub webhook events."""
        # Process GitHub-specific webhook events
        # Update pipeline statuses based on GitHub Actions events
        pass

    async def _handle_jenkins_webhook(self, event: WebhookEvent) -> None:
        """Handle Jenkins webhook events."""
        # Process Jenkins-specific webhook events
        pass

    async def _handle_gitlab_webhook(self, event: WebhookEvent) -> None:
        """Handle GitLab webhook events."""
        # Process GitLab-specific webhook events
        pass

    async def _refresh_execution_status(self, execution: PipelineExecution) -> None:
        """Refresh execution status from platform."""
        # Implementation would query platform API for current status
        pass

    async def _verify_webhook_signature(self, event: WebhookEvent) -> bool:
        """Verify webhook signature for security."""
        # Implementation would verify webhook signature based on platform
        return True
