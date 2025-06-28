"""
CI/CD Integration API Endpoints for Agentical Framework

This module provides REST API endpoints for CI/CD pipeline integration,
supporting GitHub Actions, Jenkins, GitLab CI, and other major CI/CD platforms
with comprehensive pipeline management and real-time monitoring capabilities.

Features:
- Pipeline creation and management endpoints
- Real-time pipeline execution monitoring
- Webhook endpoints for status updates
- Artifact and log retrieval
- Platform-specific integration endpoints
- Security and authentication
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

import logfire

from ....core.dependencies import get_db_session, get_current_user
from ....core.exceptions import (
    ValidationError,
    ExternalServiceError,
    NotFoundError
)
from ....integrations.cicd.cicd_integration_manager import (
    CICDIntegrationManager,
    CICDPlatform,
    PipelineConfiguration,
    PipelineExecution,
    TriggerEvent,
    PipelineStatus
)
from ....integrations.cicd.github_actions_integration import GitHubActionsIntegration
from ....integrations.cicd.jenkins_integration import JenkinsIntegration
from ....agents.devops_agent import DevOpsAgent
from ....workflows.engine.workflow_engine import WorkflowEngine

# Initialize router
router = APIRouter(prefix="/cicd", tags=["CI/CD Integration"])

# Request/Response Models

class PipelineCreateRequest(BaseModel):
    """Request model for creating a CI/CD pipeline."""
    name: str = Field(..., description="Pipeline name")
    platform: str = Field(..., description="CI/CD platform (github_actions, jenkins, gitlab_ci)")
    repository: str = Field(..., description="Repository URL or name")
    branch: str = Field(default="main", description="Default branch")
    triggers: List[str] = Field(default=["push"], description="Pipeline triggers")
    environment_variables: Dict[str, str] = Field(default={}, description="Environment variables")
    secrets: List[str] = Field(default=[], description="Required secrets")
    stages: List[Dict[str, Any]] = Field(..., description="Pipeline stages configuration")
    notifications: Dict[str, Any] = Field(default={}, description="Notification settings")
    timeout_minutes: int = Field(default=60, description="Pipeline timeout in minutes")
    parallel_jobs: int = Field(default=1, description="Number of parallel jobs")
    retry_attempts: int = Field(default=3, description="Retry attempts on failure")
    deployment_environments: List[str] = Field(default=[], description="Deployment environments")

    @validator("platform")
    def validate_platform(cls, v):
        valid_platforms = [platform.value for platform in CICDPlatform]
        if v not in valid_platforms:
            raise ValueError(f"Platform must be one of: {valid_platforms}")
        return v

class PipelineTriggerRequest(BaseModel):
    """Request model for triggering a pipeline."""
    trigger_event: str = Field(default="manual", description="Trigger event type")
    commit_sha: Optional[str] = Field(None, description="Specific commit SHA")
    branch: Optional[str] = Field(None, description="Branch to build")
    parameters: Dict[str, Any] = Field(default={}, description="Pipeline parameters")

class PipelineResponse(BaseModel):
    """Response model for pipeline operations."""
    pipeline_id: str
    name: str
    platform: str
    repository: str
    branch: str
    status: str
    created_at: datetime
    updated_at: datetime

class PipelineExecutionResponse(BaseModel):
    """Response model for pipeline execution."""
    execution_id: str
    pipeline_id: str
    platform: str
    status: str
    trigger_event: str
    commit_sha: str
    branch: str
    started_at: datetime
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]
    logs_url: Optional[str]
    artifacts: List[Dict[str, Any]]
    stages: List[Dict[str, Any]]
    error_message: Optional[str]

class GitHubActionsWorkflowRequest(BaseModel):
    """Request model for GitHub Actions workflow creation."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    workflow_name: str = Field(..., description="Workflow name")
    workflow_config: Dict[str, Any] = Field(..., description="Workflow configuration")
    commit_message: Optional[str] = Field(None, description="Commit message")

class JenkinsPipelineRequest(BaseModel):
    """Request model for Jenkins pipeline creation."""
    job_name: str = Field(..., description="Jenkins job name")
    pipeline_script: str = Field(..., description="Jenkinsfile content")
    description: Optional[str] = Field(None, description="Job description")
    parameters: List[Dict[str, Any]] = Field(default=[], description="Job parameters")

class WebhookEventRequest(BaseModel):
    """Request model for webhook events."""
    platform: str = Field(..., description="CI/CD platform")
    event_data: Dict[str, Any] = Field(..., description="Webhook payload")
    signature: Optional[str] = Field(None, description="Webhook signature")

# Global CI/CD integration manager instance
cicd_manager: Optional[CICDIntegrationManager] = None

async def get_cicd_manager(
    db_session: AsyncSession = Depends(get_db_session)
) -> CICDIntegrationManager:
    """Get CI/CD integration manager instance."""
    global cicd_manager
    if not cicd_manager:
        # Initialize with required dependencies
        workflow_engine = WorkflowEngine(db_session)
        devops_agent = DevOpsAgent("devops_agent", "DevOps Agent")
        cicd_manager = CICDIntegrationManager(
            workflow_engine=workflow_engine,
            devops_agent=devops_agent,
            db_session=db_session
        )
        await cicd_manager.start()
    return cicd_manager

# API Endpoints

@router.post("/pipelines", response_model=PipelineResponse)
async def create_pipeline(
    request: PipelineCreateRequest,
    background_tasks: BackgroundTasks,
    cicd_manager: CICDIntegrationManager = Depends(get_cicd_manager),
    current_user = Depends(get_current_user)
):
    """
    Create a new CI/CD pipeline.

    Creates a pipeline configuration and optionally deploys it to the specified
    CI/CD platform with automated setup and configuration.
    """
    with logfire.span("create_pipeline", platform=request.platform, repository=request.repository):
        try:
            # Convert request to pipeline configuration
            config = PipelineConfiguration(
                name=request.name,
                platform=CICDPlatform(request.platform),
                repository=request.repository,
                branch=request.branch,
                triggers=[TriggerEvent(t) for t in request.triggers],
                environment_variables=request.environment_variables,
                secrets=request.secrets,
                stages=request.stages,
                notifications=request.notifications,
                timeout_minutes=request.timeout_minutes,
                parallel_jobs=request.parallel_jobs,
                retry_attempts=request.retry_attempts,
                deployment_environments=request.deployment_environments
            )

            # Create pipeline
            pipeline_id = await cicd_manager.create_pipeline(config, auto_deploy=True)

            # Return response
            return PipelineResponse(
                pipeline_id=pipeline_id,
                name=config.name,
                platform=config.platform.value,
                repository=config.repository,
                branch=config.branch,
                status="created",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

        except ValidationError as e:
            logfire.error("Pipeline creation validation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation error: {str(e)}"
            )
        except ExternalServiceError as e:
            logfire.error("External service error during pipeline creation", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"External service error: {str(e)}"
            )
        except Exception as e:
            logfire.error("Unexpected error during pipeline creation", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

@router.post("/pipelines/{pipeline_id}/trigger", response_model=PipelineExecutionResponse)
async def trigger_pipeline(
    pipeline_id: str,
    request: PipelineTriggerRequest,
    cicd_manager: CICDIntegrationManager = Depends(get_cicd_manager),
    current_user = Depends(get_current_user)
):
    """
    Trigger a pipeline execution.

    Initiates a new execution of the specified pipeline with optional
    parameters and custom trigger settings.
    """
    with logfire.span("trigger_pipeline", pipeline_id=pipeline_id):
        try:
            # Trigger pipeline execution
            execution = await cicd_manager.trigger_pipeline(
                pipeline_id=pipeline_id,
                trigger_event=TriggerEvent(request.trigger_event),
                commit_sha=request.commit_sha,
                branch=request.branch,
                parameters=request.parameters
            )

            return PipelineExecutionResponse(
                execution_id=execution.id,
                pipeline_id=execution.pipeline_id,
                platform=execution.platform.value,
                status=execution.status.value,
                trigger_event=execution.trigger_event.value,
                commit_sha=execution.commit_sha,
                branch=execution.branch,
                started_at=execution.started_at,
                finished_at=execution.finished_at,
                duration_seconds=execution.duration_seconds,
                logs_url=execution.logs_url,
                artifacts=execution.artifacts,
                stages=execution.stages,
                error_message=execution.error_message
            )

        except NotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to trigger pipeline", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to trigger pipeline"
            )

@router.get("/pipelines/{pipeline_id}/executions/{execution_id}", response_model=PipelineExecutionResponse)
async def get_pipeline_execution(
    pipeline_id: str,
    execution_id: str,
    cicd_manager: CICDIntegrationManager = Depends(get_cicd_manager),
    current_user = Depends(get_current_user)
):
    """
    Get pipeline execution details.

    Returns detailed information about a specific pipeline execution including
    status, logs, artifacts, and performance metrics.
    """
    with logfire.span("get_pipeline_execution", execution_id=execution_id):
        try:
            execution = await cicd_manager.get_pipeline_status(execution_id)

            return PipelineExecutionResponse(
                execution_id=execution.id,
                pipeline_id=execution.pipeline_id,
                platform=execution.platform.value,
                status=execution.status.value,
                trigger_event=execution.trigger_event.value,
                commit_sha=execution.commit_sha,
                branch=execution.branch,
                started_at=execution.started_at,
                finished_at=execution.finished_at,
                duration_seconds=execution.duration_seconds,
                logs_url=execution.logs_url,
                artifacts=execution.artifacts,
                stages=execution.stages,
                error_message=execution.error_message
            )

        except NotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to get pipeline execution", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get pipeline execution"
            )

@router.post("/pipelines/{pipeline_id}/executions/{execution_id}/cancel")
async def cancel_pipeline_execution(
    pipeline_id: str,
    execution_id: str,
    cicd_manager: CICDIntegrationManager = Depends(get_cicd_manager),
    current_user = Depends(get_current_user)
):
    """
    Cancel a running pipeline execution.

    Stops a currently running pipeline execution and performs necessary
    cleanup operations.
    """
    with logfire.span("cancel_pipeline_execution", execution_id=execution_id):
        try:
            success = await cicd_manager.cancel_pipeline(execution_id)

            if success:
                return {"message": "Pipeline execution cancelled successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to cancel pipeline execution"
                )

        except NotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to cancel pipeline execution", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel pipeline execution"
            )

@router.get("/pipelines/{pipeline_id}/executions/{execution_id}/logs")
async def get_pipeline_logs(
    pipeline_id: str,
    execution_id: str,
    stage: Optional[str] = None,
    cicd_manager: CICDIntegrationManager = Depends(get_cicd_manager),
    current_user = Depends(get_current_user)
):
    """
    Get pipeline execution logs.

    Returns the complete or partial logs for a pipeline execution,
    optionally filtered by stage.
    """
    with logfire.span("get_pipeline_logs", execution_id=execution_id):
        try:
            logs = await cicd_manager.get_pipeline_logs(execution_id, stage)

            return {
                "execution_id": execution_id,
                "stage": stage,
                "logs": logs,
                "timestamp": datetime.utcnow()
            }

        except NotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to get pipeline logs", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get pipeline logs"
            )

@router.get("/pipelines/{pipeline_id}/executions/{execution_id}/artifacts")
async def get_pipeline_artifacts(
    pipeline_id: str,
    execution_id: str,
    cicd_manager: CICDIntegrationManager = Depends(get_cicd_manager),
    current_user = Depends(get_current_user)
):
    """
    Get pipeline execution artifacts.

    Returns a list of artifacts generated by the pipeline execution
    with download URLs and metadata.
    """
    with logfire.span("get_pipeline_artifacts", execution_id=execution_id):
        try:
            artifacts = await cicd_manager.get_pipeline_artifacts(execution_id)

            return {
                "execution_id": execution_id,
                "artifacts": artifacts,
                "timestamp": datetime.utcnow()
            }

        except NotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to get pipeline artifacts", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get pipeline artifacts"
            )

@router.post("/deployment-pipelines")
async def create_deployment_pipeline(
    application_name: str,
    repository: str,
    environments: List[str],
    platform: str = "github_actions",
    cicd_manager: CICDIntegrationManager = Depends(get_cicd_manager),
    current_user = Depends(get_current_user)
):
    """
    Create an automated deployment pipeline.

    Creates a comprehensive deployment pipeline with build, test, security scan,
    and deployment stages for multiple environments.
    """
    with logfire.span("create_deployment_pipeline", application=application_name):
        try:
            pipeline_id = await cicd_manager.create_deployment_pipeline(
                application_name=application_name,
                repository=repository,
                environments=environments,
                platform=CICDPlatform(platform)
            )

            return {
                "pipeline_id": pipeline_id,
                "application_name": application_name,
                "environments": environments,
                "platform": platform,
                "message": "Deployment pipeline created successfully"
            }

        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to create deployment pipeline", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create deployment pipeline"
            )

# GitHub Actions specific endpoints

@router.post("/github-actions/workflows")
async def create_github_actions_workflow(
    request: GitHubActionsWorkflowRequest,
    current_user = Depends(get_current_user)
):
    """
    Create a GitHub Actions workflow.

    Creates a new GitHub Actions workflow file in the specified repository
    with the provided configuration.
    """
    with logfire.span("create_github_actions_workflow", repo=f"{request.owner}/{request.repo}"):
        try:
            # Initialize GitHub Actions integration
            github_token = "your_github_token"  # Should come from configuration
            github_integration = GitHubActionsIntegration(github_token)

            # Create workflow
            workflow_path = await github_integration.create_workflow(
                owner=request.owner,
                repo=request.repo,
                workflow_name=request.workflow_name,
                workflow_config=request.workflow_config,
                commit_message=request.commit_message
            )

            await github_integration.close()

            return {
                "workflow_path": workflow_path,
                "repository": f"{request.owner}/{request.repo}",
                "message": "GitHub Actions workflow created successfully"
            }

        except ExternalServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to create GitHub Actions workflow", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create GitHub Actions workflow"
            )

@router.post("/github-actions/workflows/{owner}/{repo}/{workflow_id}/trigger")
async def trigger_github_actions_workflow(
    owner: str,
    repo: str,
    workflow_id: str,
    ref: str = "main",
    inputs: Dict[str, Any] = {},
    current_user = Depends(get_current_user)
):
    """
    Trigger a GitHub Actions workflow dispatch.

    Manually triggers a workflow that supports workflow_dispatch events
    with optional inputs.
    """
    with logfire.span("trigger_github_actions_workflow", workflow_id=workflow_id):
        try:
            # Initialize GitHub Actions integration
            github_token = "your_github_token"  # Should come from configuration
            github_integration = GitHubActionsIntegration(github_token)

            # Trigger workflow
            workflow_run = await github_integration.trigger_workflow(
                owner=owner,
                repo=repo,
                workflow_id=workflow_id,
                ref=ref,
                inputs=inputs
            )

            await github_integration.close()

            return {
                "run_id": workflow_run.id,
                "run_number": workflow_run.run_number,
                "status": workflow_run.status.value,
                "html_url": workflow_run.html_url,
                "message": "GitHub Actions workflow triggered successfully"
            }

        except ExternalServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to trigger GitHub Actions workflow", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to trigger GitHub Actions workflow"
            )

# Jenkins specific endpoints

@router.post("/jenkins/pipelines")
async def create_jenkins_pipeline(
    request: JenkinsPipelineRequest,
    current_user = Depends(get_current_user)
):
    """
    Create a Jenkins pipeline job.

    Creates a new Jenkins pipeline job with the specified Jenkinsfile
    and configuration.
    """
    with logfire.span("create_jenkins_pipeline", job_name=request.job_name):
        try:
            # Initialize Jenkins integration
            jenkins_integration = JenkinsIntegration(
                jenkins_url="your_jenkins_url",  # Should come from configuration
                username="your_username",
                api_token="your_api_token"
            )

            # Create pipeline job
            job_url = await jenkins_integration.create_pipeline_job(
                job_name=request.job_name,
                pipeline_script=request.pipeline_script,
                description=request.description,
                parameters=request.parameters
            )

            await jenkins_integration.close()

            return {
                "job_name": request.job_name,
                "job_url": job_url,
                "message": "Jenkins pipeline created successfully"
            }

        except ExternalServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to create Jenkins pipeline", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create Jenkins pipeline"
            )

@router.post("/jenkins/jobs/{job_name}/trigger")
async def trigger_jenkins_build(
    job_name: str,
    parameters: Dict[str, Any] = {},
    token: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    Trigger a Jenkins build.

    Initiates a new build for the specified Jenkins job with optional
    parameters and build token.
    """
    with logfire.span("trigger_jenkins_build", job_name=job_name):
        try:
            # Initialize Jenkins integration
            jenkins_integration = JenkinsIntegration(
                jenkins_url="your_jenkins_url",  # Should come from configuration
                username="your_username",
                api_token="your_api_token"
            )

            # Trigger build
            build = await jenkins_integration.trigger_build(
                job_name=job_name,
                parameters=parameters,
                token=token
            )

            await jenkins_integration.close()

            return {
                "job_name": job_name,
                "build_number": build.number,
                "build_url": build.url,
                "status": build.status.value if build.status else "RUNNING",
                "message": "Jenkins build triggered successfully"
            }

        except ExternalServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to trigger Jenkins build", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to trigger Jenkins build"
            )

# Webhook endpoints

@router.post("/webhooks/{platform}")
async def handle_webhook(
    platform: str,
    request: Request,
    background_tasks: BackgroundTasks,
    cicd_manager: CICDIntegrationManager = Depends(get_cicd_manager)
):
    """
    Handle webhook events from CI/CD platforms.

    Processes webhook events from various CI/CD platforms to update
    pipeline statuses and trigger automated workflows.
    """
    with logfire.span("handle_webhook", platform=platform):
        try:
            # Get request body and headers
            body = await request.body()
            headers = dict(request.headers)

            # Parse JSON payload
            try:
                event_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON payload"
                )

            # Validate platform
            try:
                cicd_platform = CICDPlatform(platform)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported platform: {platform}"
                )

            # Process webhook in background
            background_tasks.add_task(
                cicd_manager.handle_webhook,
                cicd_platform,
                event_data,
                headers
            )

            return {"message": "Webhook received and processed"}

        except HTTPException:
            raise
        except Exception as e:
            logfire.error("Failed to handle webhook", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process webhook"
            )

# Template endpoints

@router.get("/templates/{platform}/{template_type}")
async def get_pipeline_template(
    platform: str,
    template_type: str,
    language: Optional[str] = None,
    framework: Optional[str] = None
):
    """
    Get a pipeline template for the specified platform and type.

    Returns a pre-configured pipeline template that can be customized
    and used to create new pipelines.
    """
    with logfire.span("get_pipeline_template", platform=platform, template_type=template_type):
        try:
            config = {
                "language": language or "python",
                "framework": framework
            }

            if platform == "github_actions":
                github_integration = GitHubActionsIntegration("dummy_token")
                template = github_integration.generate_workflow_template(template_type, config)
            elif platform == "jenkins":
                jenkins_integration = JenkinsIntegration("dummy_url", "dummy_user", "dummy_token")
                template = jenkins_integration.generate_pipeline_template(template_type, config)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported platform: {platform}"
                )

            return {
                "platform": platform,
                "template_type": template_type,
                "language": language,
                "framework": framework,
                "template": template
            }

        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logfire.error("Failed to get pipeline template", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get pipeline template"
            )

# Status and monitoring endpoints

@router.get("/status")
async def get_cicd_status(
    cicd_manager: CICDIntegrationManager = Depends(get_cicd_manager)
):
    """
    Get CI/CD integration status.

    Returns the current status of the CI/CD integration system including
    active pipelines, platform connectivity, and system health.
    """
    with logfire.span("get_cicd_status"):
        try:
            # Get active pipelines count
            active_pipelines = len(cicd_manager.active_pipelines)

            # Get configured platforms
            configured_platforms = list(cicd_manager.platform_clients.keys())

            return {
                "status": "operational",
                "active_pipelines": active_pipelines,
                "configured_platforms": [p.value for p in configured_platforms],
                "total_pipeline_configurations": len(cicd_manager.pipeline_configurations),
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logfire.error("Failed to get CI/CD status", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get CI/CD status"
            )
