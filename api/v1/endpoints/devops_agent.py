"""
DevOps Agent API Endpoints for Agentical Framework

This module provides REST API endpoints for the DevOps Agent, enabling
infrastructure management, CI/CD automation, deployment orchestration,
and DevOps workflow operations through HTTP requests.

Endpoints:
- Pipeline management and automation
- Application deployment operations
- Infrastructure as Code operations
- Monitoring and alerting setup
- Security scanning and compliance
- Environment management
- Rollback operations
- Health checks and metrics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

import logfire
from agentical.agents.devops_agent import (
    DevOpsAgent,
    PipelineRequest,
    DeploymentRequest,
    InfrastructureRequest,
    MonitoringRequest,
    SecurityScanRequest,
    CloudPlatform,
    ContainerOrchestrator,
    IaCTool,
    CIPlatform,
    DeploymentStrategy,
    Environment,
    SecurityScanType
)
from agentical.db.database import get_async_session
from agentical.core.exceptions import AgentExecutionError, ValidationError, NotFoundError
from agentical.api.v1.dependencies import get_current_user, require_permissions
from agentical.core.security import User

router = APIRouter(prefix="/devops", tags=["devops"])


class TaskExecutionRequest(BaseModel):
    """Request model for generic task execution."""
    task_type: str = Field(..., description="Type of DevOps task")
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
    supported_platforms: List[str] = Field(..., description="Supported cloud platforms")
    supported_orchestrators: List[str] = Field(..., description="Supported container orchestrators")
    supported_iac_tools: List[str] = Field(..., description="Supported Infrastructure as Code tools")
    supported_ci_platforms: List[str] = Field(..., description="Supported CI/CD platforms")
    capabilities: List[str] = Field(..., description="Available agent capabilities")
    deployment_strategies: List[str] = Field(..., description="Supported deployment strategies")
    security_scan_types: List[str] = Field(..., description="Available security scan types")
    environments: List[str] = Field(..., description="Supported environments")


class DeploymentMetricsResponse(BaseModel):
    """Response model for deployment metrics."""
    environment: str = Field(..., description="Target environment")
    time_period_days: int = Field(..., description="Analysis time period in days")
    deployment_time: float = Field(..., description="Average deployment time in minutes")
    success_rate: float = Field(..., description="Deployment success rate (0-1)")
    rollback_rate: float = Field(..., description="Rollback rate (0-1)")
    lead_time: float = Field(..., description="Lead time in hours")
    recovery_time: float = Field(..., description="Mean recovery time in minutes")
    change_failure_rate: float = Field(..., description="Change failure rate (0-1)")
    deployment_frequency: float = Field(..., description="Deployments per day")


async def get_devops_agent(
    session: AsyncSession = Depends(get_async_session)
) -> DevOpsAgent:
    """Dependency to get DevOpsAgent instance."""
    agent_id = f"devops-agent-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return DevOpsAgent(agent_id=agent_id, session=session)


@router.get(
    "/capabilities",
    response_model=AgentCapabilitiesResponse,
    summary="Get DevOps Agent Capabilities",
    description="Retrieve comprehensive information about DevOps Agent capabilities, supported platforms, and available operations."
)
async def get_capabilities(
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(get_current_user)
) -> AgentCapabilitiesResponse:
    """Get DevOps Agent capabilities and supported operations."""
    try:
        with logfire.span("get_devops_capabilities", user_id=current_user.id):
            capabilities = await agent.get_capabilities()

            logfire.info(
                "DevOps capabilities retrieved",
                user_id=current_user.id,
                capabilities_count=len(capabilities.get("capabilities", []))
            )

            return AgentCapabilitiesResponse(**capabilities)

    except Exception as e:
        logfire.error("Failed to retrieve DevOps capabilities", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve capabilities: {str(e)}"
        )


@router.post(
    "/tasks/execute",
    response_model=TaskExecutionResponse,
    summary="Execute DevOps Task",
    description="Execute a generic DevOps task with specified type and parameters."
)
async def execute_task(
    request: TaskExecutionRequest,
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(require_permissions(["devops:execute"]))
) -> TaskExecutionResponse:
    """Execute a DevOps task."""
    try:
        with logfire.span(
            "execute_devops_task",
            user_id=current_user.id,
            task_type=request.task_type
        ):
            started_at = datetime.now()
            task_id = f"task-{started_at.strftime('%Y%m%d%H%M%S')}-{request.task_type}"

            task_data = {
                "id": task_id,
                "type": request.task_type,
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
                    "DevOps task completed",
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
    "/pipelines",
    response_model=Dict[str, Any],
    summary="Create CI/CD Pipeline",
    description="Create or update a CI/CD pipeline for automated build, test, and deployment processes."
)
async def create_pipeline(
    request: PipelineRequest,
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(require_permissions(["devops:pipeline:create"]))
) -> Dict[str, Any]:
    """Create a CI/CD pipeline."""
    try:
        with logfire.span(
            "create_pipeline",
            user_id=current_user.id,
            platform=request.platform.value,
            repository=request.repository
        ):
            result = await agent.create_pipeline(request)

            logfire.info(
                "Pipeline created successfully",
                user_id=current_user.id,
                platform=request.platform.value,
                pipeline_id=result.get("pipeline_id")
            )

            return result

    except ValidationError as e:
        logfire.warning("Pipeline validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pipeline validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Pipeline creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline creation failed: {str(e)}"
        )


@router.post(
    "/deployments",
    response_model=Dict[str, Any],
    summary="Deploy Application",
    description="Deploy an application using specified deployment strategy and container orchestrator."
)
async def deploy_application(
    request: DeploymentRequest,
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(require_permissions(["devops:deployment:create"]))
) -> Dict[str, Any]:
    """Deploy an application."""
    try:
        with logfire.span(
            "deploy_application",
            user_id=current_user.id,
            application=request.application_name,
            environment=request.environment.value
        ):
            result = await agent.deploy_application(request)

            logfire.info(
                "Application deployed successfully",
                user_id=current_user.id,
                application=request.application_name,
                deployment_id=result.get("deployment_id")
            )

            return result

    except ValidationError as e:
        logfire.warning("Deployment validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deployment validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Deployment failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}"
        )


@router.post(
    "/infrastructure",
    response_model=Dict[str, Any],
    summary="Manage Infrastructure",
    description="Manage cloud infrastructure using Infrastructure as Code tools like Terraform, CloudFormation, or Ansible."
)
async def manage_infrastructure(
    request: InfrastructureRequest,
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(require_permissions(["devops:infrastructure:manage"]))
) -> Dict[str, Any]:
    """Manage infrastructure using IaC tools."""
    try:
        with logfire.span(
            "manage_infrastructure",
            user_id=current_user.id,
            tool=request.tool.value,
            operation=request.operation
        ):
            result = await agent.manage_infrastructure(request)

            logfire.info(
                "Infrastructure operation completed",
                user_id=current_user.id,
                tool=request.tool.value,
                operation=request.operation
            )

            return result

    except ValidationError as e:
        logfire.warning("Infrastructure validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Infrastructure validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Infrastructure operation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Infrastructure operation failed: {str(e)}"
        )


@router.post(
    "/monitoring",
    response_model=Dict[str, Any],
    summary="Setup Monitoring",
    description="Set up monitoring, alerting, and dashboards for services and infrastructure."
)
async def setup_monitoring(
    request: MonitoringRequest,
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(require_permissions(["devops:monitoring:setup"]))
) -> Dict[str, Any]:
    """Set up monitoring and alerting."""
    try:
        with logfire.span(
            "setup_monitoring",
            user_id=current_user.id,
            service=request.service_name,
            environment=request.environment.value
        ):
            result = await agent.setup_monitoring(request)

            logfire.info(
                "Monitoring setup completed",
                user_id=current_user.id,
                service=request.service_name,
                metrics_count=len(request.metrics)
            )

            return result

    except ValidationError as e:
        logfire.warning("Monitoring validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Monitoring validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Monitoring setup failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monitoring setup failed: {str(e)}"
        )


@router.post(
    "/security/scan",
    response_model=List[Dict[str, Any]],
    summary="Perform Security Scan",
    description="Perform comprehensive security scanning including container, dependency, secret, and compliance scans."
)
async def perform_security_scan(
    request: SecurityScanRequest,
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(require_permissions(["devops:security:scan"]))
) -> List[Dict[str, Any]]:
    """Perform security scans."""
    try:
        with logfire.span(
            "perform_security_scan",
            user_id=current_user.id,
            target=request.target,
            scan_types=[scan.value for scan in request.scan_types]
        ):
            results = await agent.perform_security_scan(request)

            # Convert SecurityScanResult objects to dictionaries
            scan_results = [
                {
                    "scan_type": result.scan_type.value,
                    "severity": result.severity,
                    "issue_count": result.issue_count,
                    "critical_issues": result.critical_issues,
                    "high_issues": result.high_issues,
                    "medium_issues": result.medium_issues,
                    "low_issues": result.low_issues,
                    "scan_time": result.scan_time.isoformat(),
                    "report_url": result.report_url,
                    "recommendations": result.recommendations
                }
                for result in results
            ]

            logfire.info(
                "Security scans completed",
                user_id=current_user.id,
                target=request.target,
                total_scans=len(scan_results)
            )

            return scan_results

    except ValidationError as e:
        logfire.warning("Security scan validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security scan validation failed: {str(e)}"
        )
    except AgentExecutionError as e:
        logfire.error("Security scan failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security scan failed: {str(e)}"
        )


@router.get(
    "/metrics/deployment",
    response_model=DeploymentMetricsResponse,
    summary="Get Deployment Metrics",
    description="Retrieve deployment metrics including success rate, lead time, and DORA metrics for specified environment."
)
async def get_deployment_metrics(
    environment: Environment = Query(..., description="Target environment for metrics"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(require_permissions(["devops:metrics:read"]))
) -> DeploymentMetricsResponse:
    """Get deployment metrics for specified environment."""
    try:
        with logfire.span(
            "get_deployment_metrics",
            user_id=current_user.id,
            environment=environment.value,
            days=days
        ):
            metrics = await agent.get_deployment_metrics(environment, days)

            logfire.info(
                "Deployment metrics retrieved",
                user_id=current_user.id,
                environment=environment.value,
                success_rate=metrics.success_rate
            )

            return DeploymentMetricsResponse(
                environment=environment.value,
                time_period_days=days,
                deployment_time=metrics.deployment_time,
                success_rate=metrics.success_rate,
                rollback_rate=metrics.rollback_rate,
                lead_time=metrics.lead_time,
                recovery_time=metrics.recovery_time,
                change_failure_rate=metrics.change_failure_rate,
                deployment_frequency=metrics.deployment_frequency
            )

    except Exception as e:
        logfire.error("Failed to retrieve deployment metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.post(
    "/deployments/{deployment_id}/rollback",
    response_model=Dict[str, Any],
    summary="Rollback Deployment",
    description="Rollback a specific deployment to the previous stable version."
)
async def rollback_deployment(
    deployment_id: str = Path(..., description="Deployment ID to rollback"),
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(require_permissions(["devops:deployment:rollback"]))
) -> Dict[str, Any]:
    """Rollback a specific deployment."""
    try:
        with logfire.span(
            "rollback_deployment",
            user_id=current_user.id,
            deployment_id=deployment_id
        ):
            task_data = {
                "type": "rollback",
                "deployment_id": deployment_id
            }

            result = await agent.execute_task(task_data)

            logfire.info(
                "Deployment rollback completed",
                user_id=current_user.id,
                deployment_id=deployment_id
            )

            return result

    except NotFoundError as e:
        logfire.warning("Deployment not found for rollback", deployment_id=deployment_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment not found: {deployment_id}"
        )
    except AgentExecutionError as e:
        logfire.error("Rollback failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}"
        )


@router.get(
    "/health/{service_name}",
    response_model=Dict[str, Any],
    summary="Check Service Health",
    description="Perform health check on a specific service in the specified environment."
)
async def check_service_health(
    service_name: str = Path(..., description="Service name to check"),
    environment: Environment = Query(..., description="Target environment"),
    agent: DevOpsAgent = Depends(get_devops_agent),
    current_user: User = Depends(require_permissions(["devops:health:check"]))
) -> Dict[str, Any]:
    """Check health of a specific service."""
    try:
        with logfire.span(
            "check_service_health",
            user_id=current_user.id,
            service=service_name,
            environment=environment.value
        ):
            task_data = {
                "type": "health_check",
                "service": service_name,
                "environment": environment.value
            }

            result = await agent.execute_task(task_data)

            logfire.info(
                "Health check completed",
                user_id=current_user.id,
                service=service_name,
                status=result.get("status")
            )

            return result

    except Exception as e:
        logfire.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/platforms",
    response_model=Dict[str, List[str]],
    summary="Get Supported Platforms",
    description="Get comprehensive list of all supported platforms, tools, and technologies."
)
async def get_supported_platforms(
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[str]]:
    """Get all supported platforms and tools."""
    try:
        with logfire.span("get_supported_platforms", user_id=current_user.id):
            platforms = {
                "cloud_platforms": [platform.value for platform in CloudPlatform],
                "container_orchestrators": [orch.value for orch in ContainerOrchestrator],
                "iac_tools": [tool.value for tool in IaCTool],
                "ci_platforms": [platform.value for platform in CIPlatform],
                "deployment_strategies": [strategy.value for strategy in DeploymentStrategy],
                "environments": [env.value for env in Environment],
                "security_scan_types": [scan.value for scan in SecurityScanType]
            }

            logfire.info("Supported platforms retrieved", user_id=current_user.id)

            return platforms

    except Exception as e:
        logfire.error("Failed to retrieve supported platforms", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve platforms: {str(e)}"
        )
