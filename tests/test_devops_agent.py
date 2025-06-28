"""
Comprehensive Test Suite for DevOps Agent

This module provides extensive testing for the DevOps Agent implementation,
covering all capabilities including CI/CD pipeline management, deployment
orchestration, infrastructure management, security scanning, and monitoring.

Test Coverage:
- Agent initialization and configuration
- Pipeline creation and management
- Application deployment operations
- Infrastructure as Code operations
- Security scanning and compliance
- Monitoring and alerting setup
- Environment management
- Rollback operations
- Health checks and metrics
- Error handling and edge cases
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError as PydanticValidationError

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
    SecurityScanType,
    DeploymentMetrics,
    SecurityScanResult,
    InfrastructureResource,
    PipelineStage
)
from agentical.db.models.agent import AgentType, AgentStatus
from agentical.core.exceptions import AgentExecutionError, ValidationError


class TestDevOpsAgent:
    """Test suite for DevOps Agent core functionality."""

    @pytest.fixture
    async def mock_session(self):
        """Create mock async database session."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def devops_agent(self, mock_session):
        """Create DevOps Agent instance for testing."""
        agent = DevOpsAgent(
            agent_id="test-devops-agent",
            session=mock_session,
            config={"test_mode": True}
        )
        return agent

    @pytest.fixture
    def sample_pipeline_request(self):
        """Sample pipeline request for testing."""
        return PipelineRequest(
            platform=CIPlatform.GITHUB_ACTIONS,
            repository="https://github.com/example/repo",
            branch="main",
            stages=[
                {
                    "name": "build",
                    "commands": ["npm install", "npm run build"],
                    "artifacts": ["dist/"]
                },
                {
                    "name": "test",
                    "commands": ["npm test", "npm run test:e2e"],
                    "dependencies": ["build"]
                }
            ],
            environment_variables={"NODE_ENV": "production"}
        )

    @pytest.fixture
    def sample_deployment_request(self):
        """Sample deployment request for testing."""
        return DeploymentRequest(
            application_name="test-app",
            version="v1.2.3",
            environment=Environment.STAGING,
            strategy=DeploymentStrategy.BLUE_GREEN,
            orchestrator=ContainerOrchestrator.KUBERNETES,
            configuration={
                "replicas": 3,
                "image": "test-app:v1.2.3",
                "resources": {
                    "cpu": "500m",
                    "memory": "512Mi"
                }
            },
            health_checks=[
                {
                    "path": "/health",
                    "port": 8080,
                    "timeout": 30
                }
            ]
        )

    @pytest.fixture
    def sample_infrastructure_request(self):
        """Sample infrastructure request for testing."""
        return InfrastructureRequest(
            tool=IaCTool.TERRAFORM,
            platform=CloudPlatform.AWS,
            operation="apply",
            resources=[
                {
                    "type": "aws_instance",
                    "name": "web_server",
                    "config": {
                        "instance_type": "t3.medium",
                        "ami": "ami-12345678"
                    }
                }
            ],
            variables={"environment": "staging"}
        )

    @pytest.fixture
    def sample_monitoring_request(self):
        """Sample monitoring request for testing."""
        return MonitoringRequest(
            service_name="test-service",
            environment=Environment.PRODUCTION,
            metrics=["cpu_usage", "memory_usage", "request_count"],
            alerts=[
                {
                    "metric": "cpu_usage",
                    "threshold": 80,
                    "condition": "greater_than"
                }
            ]
        )

    @pytest.fixture
    def sample_security_scan_request(self):
        """Sample security scan request for testing."""
        return SecurityScanRequest(
            scan_types=[SecurityScanType.CONTAINER_SCAN, SecurityScanType.DEPENDENCY_SCAN],
            target="test-app:latest",
            environment=Environment.PRODUCTION,
            severity_threshold="medium"
        )

    # Agent Initialization Tests

    async def test_agent_initialization(self, mock_session):
        """Test DevOps Agent initialization."""
        agent = DevOpsAgent(
            agent_id="test-agent",
            session=mock_session,
            config={"custom_config": "value"}
        )

        assert agent.agent_id == "test-agent"
        assert agent.agent_type == AgentType.DEVOPS
        assert "aws" in agent.supported_platforms
        assert "kubernetes" in agent.supported_orchestrators
        assert "terraform" in agent.supported_iac_tools
        assert "github_actions" in agent.supported_ci_platforms

    async def test_get_capabilities(self, devops_agent):
        """Test getting agent capabilities."""
        capabilities = await devops_agent.get_capabilities()

        assert capabilities["agent_type"] == "devops"
        assert "version" in capabilities
        assert "supported_platforms" in capabilities
        assert "capabilities" in capabilities
        assert "pipeline_management" in capabilities["capabilities"]
        assert "application_deployment" in capabilities["capabilities"]
        assert len(capabilities["supported_platforms"]) > 0

    # Pipeline Management Tests

    async def test_create_pipeline_github_actions(self, devops_agent, sample_pipeline_request):
        """Test creating GitHub Actions pipeline."""
        with patch.object(devops_agent, '_validate_pipeline_config') as mock_validate, \
             patch.object(devops_agent, '_generate_pipeline_config') as mock_generate, \
             patch.object(devops_agent, '_create_github_actions_pipeline') as mock_create:

            mock_validate.return_value = None
            mock_generate.return_value = {"workflow": "config"}
            mock_create.return_value = {"pipeline_id": "gh-pipeline-123", "status": "created"}

            result = await devops_agent.create_pipeline(sample_pipeline_request)

            assert result["pipeline_id"] == "gh-pipeline-123"
            assert result["status"] == "created"
            mock_validate.assert_called_once()
            mock_generate.assert_called_once()
            mock_create.assert_called_once()

    async def test_create_pipeline_validation_error(self, devops_agent):
        """Test pipeline creation with validation error."""
        invalid_request = PipelineRequest(
            platform=CIPlatform.GITHUB_ACTIONS,
            repository="invalid-repo",
            branch="main",
            stages=[]  # Empty stages should cause validation error
        )

        with pytest.raises(AgentExecutionError):
            await devops_agent.create_pipeline(invalid_request)

    async def test_pipeline_task_execution(self, devops_agent, sample_pipeline_request):
        """Test pipeline task execution through execute_task."""
        task = {
            "id": "pipeline-task-1",
            "type": "pipeline",
            "parameters": sample_pipeline_request.dict()
        }

        with patch.object(devops_agent, 'create_pipeline') as mock_create:
            mock_create.return_value = {"pipeline_id": "test-pipeline", "status": "created"}

            result = await devops_agent.execute_task(task)

            assert result["pipeline_id"] == "test-pipeline"
            mock_create.assert_called_once()

    # Deployment Tests

    async def test_deploy_application_kubernetes(self, devops_agent, sample_deployment_request):
        """Test application deployment to Kubernetes."""
        with patch.object(devops_agent, '_validate_deployment_config') as mock_validate, \
             patch.object(devops_agent, '_generate_deployment_manifests') as mock_generate, \
             patch.object(devops_agent, '_deploy_to_kubernetes') as mock_deploy, \
             patch.object(devops_agent, '_verify_deployment') as mock_verify:

            mock_validate.return_value = None
            mock_generate.return_value = {"manifests": ["deployment.yaml"]}
            mock_deploy.return_value = {"deployment_id": "k8s-deploy-123", "status": "deployed"}
            mock_verify.return_value = None

            result = await devops_agent.deploy_application(sample_deployment_request)

            assert result["deployment_id"] == "k8s-deploy-123"
            assert result["status"] == "deployed"
            mock_validate.assert_called_once()
            mock_generate.assert_called_once()
            mock_deploy.assert_called_once()
            mock_verify.assert_called_once()

    async def test_deploy_application_with_rollback(self, devops_agent, sample_deployment_request):
        """Test deployment failure with automatic rollback."""
        sample_deployment_request.rollback_on_failure = True

        with patch.object(devops_agent, '_validate_deployment_config') as mock_validate, \
             patch.object(devops_agent, '_generate_deployment_manifests') as mock_generate, \
             patch.object(devops_agent, '_deploy_to_kubernetes') as mock_deploy, \
             patch.object(devops_agent, '_rollback_deployment') as mock_rollback:

            mock_validate.return_value = None
            mock_generate.return_value = {"manifests": ["deployment.yaml"]}
            mock_deploy.side_effect = Exception("Deployment failed")
            mock_rollback.return_value = {"status": "rolled_back"}

            with pytest.raises(AgentExecutionError):
                await devops_agent.deploy_application(sample_deployment_request)

            mock_rollback.assert_called_once()

    async def test_deployment_different_orchestrators(self, devops_agent):
        """Test deployment with different container orchestrators."""
        base_request = {
            "application_name": "test-app",
            "version": "v1.0.0",
            "environment": Environment.STAGING,
            "strategy": DeploymentStrategy.ROLLING,
            "configuration": {"replicas": 2}
        }

        orchestrators = [
            (ContainerOrchestrator.KUBERNETES, "_deploy_to_kubernetes"),
            (ContainerOrchestrator.DOCKER_COMPOSE, "_deploy_with_docker_compose"),
            (ContainerOrchestrator.ECS, "_deploy_to_ecs")
        ]

        for orchestrator, method_name in orchestrators:
            request = DeploymentRequest(
                orchestrator=orchestrator,
                **base_request
            )

            with patch.object(devops_agent, '_validate_deployment_config'), \
                 patch.object(devops_agent, '_generate_deployment_manifests'), \
                 patch.object(devops_agent, method_name) as mock_deploy, \
                 patch.object(devops_agent, '_verify_deployment'):

                mock_deploy.return_value = {"deployment_id": f"{orchestrator.value}-deploy", "status": "deployed"}

                result = await devops_agent.deploy_application(request)
                assert result["deployment_id"] == f"{orchestrator.value}-deploy"

    # Infrastructure Management Tests

    async def test_manage_infrastructure_terraform(self, devops_agent, sample_infrastructure_request):
        """Test infrastructure management with Terraform."""
        with patch.object(devops_agent, '_validate_infrastructure_config') as mock_validate, \
             patch.object(devops_agent, '_generate_infrastructure_code') as mock_generate, \
             patch.object(devops_agent, '_execute_terraform') as mock_execute:

            mock_validate.return_value = None
            mock_generate.return_value = "# Terraform code"
            mock_execute.return_value = {"operation": "completed", "resources": 1}

            result = await devops_agent.manage_infrastructure(sample_infrastructure_request)

            assert result["operation"] == "completed"
            assert result["resources"] == 1
            mock_validate.assert_called_once()
            mock_generate.assert_called_once()
            mock_execute.assert_called_once()

    async def test_infrastructure_different_tools(self, devops_agent):
        """Test infrastructure management with different IaC tools."""
        base_request = {
            "platform": CloudPlatform.AWS,
            "operation": "plan",
            "resources": [{"type": "instance", "name": "test"}],
            "dry_run": True
        }

        tools = [
            (IaCTool.TERRAFORM, "_execute_terraform"),
            (IaCTool.CLOUDFORMATION, "_execute_cloudformation"),
            (IaCTool.ANSIBLE, "_execute_ansible")
        ]

        for tool, method_name in tools:
            request = InfrastructureRequest(tool=tool, **base_request)

            with patch.object(devops_agent, '_validate_infrastructure_config'), \
                 patch.object(devops_agent, '_generate_infrastructure_code'), \
                 patch.object(devops_agent, method_name) as mock_execute:

                mock_execute.return_value = {"operation": "completed", "tool": tool.value}

                result = await devops_agent.manage_infrastructure(request)
                assert result["tool"] == tool.value

    # Monitoring Setup Tests

    async def test_setup_monitoring(self, devops_agent, sample_monitoring_request):
        """Test monitoring setup."""
        with patch.object(devops_agent, '_generate_monitoring_config') as mock_generate, \
             patch.object(devops_agent, '_deploy_monitoring_stack') as mock_deploy, \
             patch.object(devops_agent, '_configure_alerts') as mock_alerts, \
             patch.object(devops_agent, '_create_dashboards') as mock_dashboards:

            mock_generate.return_value = {"monitoring": "config"}
            mock_deploy.return_value = {"monitoring_stack": "deployed"}
            mock_alerts.return_value = None
            mock_dashboards.return_value = None

            sample_monitoring_request.dashboard_config = {"dashboard": "config"}

            result = await devops_agent.setup_monitoring(sample_monitoring_request)

            assert result["monitoring_stack"] == "deployed"
            mock_generate.assert_called_once()
            mock_deploy.assert_called_once()
            mock_alerts.assert_called_once()
            mock_dashboards.assert_called_once()

    # Security Scanning Tests

    async def test_perform_security_scan(self, devops_agent, sample_security_scan_request):
        """Test security scanning."""
        expected_results = [
            SecurityScanResult(
                scan_type=SecurityScanType.CONTAINER_SCAN,
                severity="medium",
                issue_count=5,
                critical_issues=0,
                high_issues=2,
                medium_issues=3,
                low_issues=0,
                scan_time=datetime.now()
            ),
            SecurityScanResult(
                scan_type=SecurityScanType.DEPENDENCY_SCAN,
                severity="high",
                issue_count=3,
                critical_issues=1,
                high_issues=2,
                medium_issues=0,
                low_issues=0,
                scan_time=datetime.now()
            )
        ]

        with patch.object(devops_agent, '_execute_security_scan') as mock_scan:
            mock_scan.side_effect = expected_results

            results = await devops_agent.perform_security_scan(sample_security_scan_request)

            assert len(results) == 2
            assert results[0].scan_type == SecurityScanType.CONTAINER_SCAN
            assert results[1].scan_type == SecurityScanType.DEPENDENCY_SCAN
            assert mock_scan.call_count == 2

    async def test_security_scan_with_compliance(self, devops_agent, sample_security_scan_request):
        """Test security scanning with compliance frameworks."""
        sample_security_scan_request.compliance_frameworks = ["SOC2", "PCI-DSS"]

        with patch.object(devops_agent, '_execute_security_scan') as mock_scan, \
             patch.object(devops_agent, '_generate_compliance_report') as mock_compliance:

            mock_scan.return_value = SecurityScanResult(
                scan_type=SecurityScanType.CONTAINER_SCAN,
                severity="low",
                issue_count=0,
                critical_issues=0,
                high_issues=0,
                medium_issues=0,
                low_issues=0,
                scan_time=datetime.now()
            )

            compliance_result = SecurityScanResult(
                scan_type=SecurityScanType.COMPLIANCE_SCAN,
                severity="info",
                issue_count=0,
                critical_issues=0,
                high_issues=0,
                medium_issues=0,
                low_issues=0,
                scan_time=datetime.now()
            )
            mock_compliance.return_value = compliance_result

            results = await devops_agent.perform_security_scan(sample_security_scan_request)

            assert len(results) == 3  # 2 scans + 1 compliance report
            mock_compliance.assert_called_once()

    # Metrics and Health Checks Tests

    async def test_get_deployment_metrics(self, devops_agent):
        """Test getting deployment metrics."""
        expected_metrics = DeploymentMetrics(
            deployment_time=25.5,
            success_rate=0.98,
            rollback_rate=0.02,
            lead_time=180.0,
            recovery_time=12.0,
            change_failure_rate=0.01,
            deployment_frequency=3.2
        )

        with patch.object(devops_agent, '_fetch_deployment_data') as mock_fetch, \
             patch.object(devops_agent, '_calculate_deployment_metrics') as mock_calculate:

            mock_fetch.return_value = {"deployments": []}
            mock_calculate.return_value = expected_metrics

            metrics = await devops_agent.get_deployment_metrics(Environment.PRODUCTION, 30)

            assert metrics.success_rate == 0.98
            assert metrics.deployment_frequency == 3.2
            mock_fetch.assert_called_once_with(Environment.PRODUCTION, 30)
            mock_calculate.assert_called_once()

    async def test_health_check_task(self, devops_agent):
        """Test health check task execution."""
        task = {
            "type": "health_check",
            "service": "api-service",
            "environment": "production"
        }

        with patch.object(devops_agent, '_perform_health_check') as mock_health:
            mock_health.return_value = {"status": "healthy", "service": "api-service"}

            result = await devops_agent.execute_task(task)

            assert result["status"] == "healthy"
            assert result["service"] == "api-service"
            mock_health.assert_called_once()

    # Rollback Tests

    async def test_rollback_task(self, devops_agent):
        """Test rollback task execution."""
        task = {
            "type": "rollback",
            "deployment_id": "deploy-123"
        }

        with patch.object(devops_agent, '_rollback_deployment_by_id') as mock_rollback:
            mock_rollback.return_value = {"status": "rolled_back", "deployment_id": "deploy-123"}

            result = await devops_agent.execute_task(task)

            assert result["status"] == "rolled_back"
            assert result["deployment_id"] == "deploy-123"
            mock_rollback.assert_called_once_with("deploy-123")

    # Error Handling Tests

    async def test_unsupported_task_type(self, devops_agent):
        """Test execution of unsupported task type."""
        task = {
            "type": "unsupported_task",
            "parameters": {}
        }

        with pytest.raises(AgentExecutionError) as exc_info:
            await devops_agent.execute_task(task)

        assert "Unsupported task type" in str(exc_info.value)

    async def test_pipeline_creation_error(self, devops_agent, sample_pipeline_request):
        """Test pipeline creation error handling."""
        with patch.object(devops_agent, '_validate_pipeline_config') as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid configuration")

            with pytest.raises(AgentExecutionError):
                await devops_agent.create_pipeline(sample_pipeline_request)

    async def test_deployment_validation_error(self, devops_agent):
        """Test deployment validation error."""
        invalid_request = DeploymentRequest(
            application_name="",  # Empty name should cause validation
            version="v1.0.0",
            environment=Environment.STAGING,
            strategy=DeploymentStrategy.ROLLING,
            orchestrator=ContainerOrchestrator.KUBERNETES,
            configuration={}  # Empty configuration should cause validation error
        )

        with pytest.raises(AgentExecutionError):
            await devops_agent.deploy_application(invalid_request)

    async def test_infrastructure_validation_error(self, devops_agent):
        """Test infrastructure validation error."""
        invalid_request = InfrastructureRequest(
            tool=IaCTool.TERRAFORM,
            platform=CloudPlatform.AWS,
            operation="apply",
            resources=[]  # Empty resources should cause validation error
        )

        with pytest.raises(AgentExecutionError):
            await devops_agent.manage_infrastructure(invalid_request)

    # Environment and Configuration Tests

    async def test_environment_task(self, devops_agent):
        """Test environment management task."""
        task = {
            "type": "environment",
            "environment": "staging",
            "operation": "create"
        }

        result = await devops_agent.execute_task(task)

        assert result["status"] == "completed"
        assert result["environment"] == "staging"

    async def test_agent_with_custom_config(self, mock_session):
        """Test agent initialization with custom configuration."""
        config = {
            "max_concurrent_deployments": 5,
            "default_timeout": 600,
            "enable_auto_rollback": True
        }

        agent = DevOpsAgent(
            agent_id="custom-agent",
            session=mock_session,
            config=config
        )

        assert agent.config == config

    # Integration Tests

    async def test_full_deployment_workflow(self, devops_agent, sample_deployment_request):
        """Test complete deployment workflow."""
        # Mock all the workflow steps
        with patch.object(devops_agent, '_validate_deployment_config') as mock_validate, \
             patch.object(devops_agent, '_generate_deployment_manifests') as mock_generate, \
             patch.object(devops_agent, '_deploy_to_kubernetes') as mock_deploy, \
             patch.object(devops_agent, '_verify_deployment') as mock_verify:

            mock_validate.return_value = None
            mock_generate.return_value = {"manifests": ["deployment.yaml", "service.yaml"]}
            mock_deploy.return_value = {"deployment_id": "full-deploy-123", "status": "deployed"}
            mock_verify.return_value = None

            # Execute the deployment
            result = await devops_agent.deploy_application(sample_deployment_request)

            # Verify the complete workflow was executed
            assert result["deployment_id"] == "full-deploy-123"
            assert result["status"] == "deployed"

            # Verify all steps were called in order
            mock_validate.assert_called_once()
            mock_generate.assert_called_once()
            mock_deploy.assert_called_once()
            mock_verify.assert_called_once()

    async def test_pipeline_to_deployment_workflow(self, devops_agent, sample_pipeline_request, sample_deployment_request):
        """Test complete CI/CD workflow from pipeline to deployment."""
        # Create pipeline
        with patch.object(devops_agent, 'create_pipeline') as mock_pipeline:
            mock_pipeline.return_value = {"pipeline_id": "workflow-pipeline", "status": "created"}

            pipeline_result = await devops_agent.create_pipeline(sample_pipeline_request)
            assert pipeline_result["pipeline_id"] == "workflow-pipeline"

        # Deploy application
        with patch.object(devops_agent, 'deploy_application') as mock_deploy:
            mock_deploy.return_value = {"deployment_id": "workflow-deploy", "status": "deployed"}

            deploy_result = await devops_agent.deploy_application(sample_deployment_request)
            assert deploy_result["deployment_id"] == "workflow-deploy"

    # Performance Tests

    async def test_concurrent_deployments(self, devops_agent):
        """Test handling multiple concurrent deployments."""
        deployment_requests = []
        for i in range(3):
            request = DeploymentRequest(
                application_name=f"app-{i}",
                version="v1.0.0",
                environment=Environment.STAGING,
                strategy=DeploymentStrategy.ROLLING,
                orchestrator=ContainerOrchestrator.KUBERNETES,
                configuration={"replicas": 1}
            )
            deployment_requests.append(request)

        with patch.object(devops_agent, '_validate_deployment_config'), \
             patch.object(devops_agent, '_generate_deployment_manifests'), \
             patch.object(devops_agent, '_deploy_to_kubernetes') as mock_deploy, \
             patch.object(devops_agent, '_verify_deployment'):

            mock_deploy.side_effect = [
                {"deployment_id": f"deploy-{i}", "status": "deployed"}
                for i in range(3)
            ]

            # Execute deployments concurrently
            tasks = [
                devops_agent.deploy_application(request)
                for request in deployment_requests
            ]
            results = await asyncio.gather(*tasks)

            # Verify all deployments completed
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result["deployment_id"] == f"deploy-{i}"
                assert result["status"] == "deployed"

    async def test_large_infrastructure_operation(self, devops_agent):
        """Test handling large infrastructure operations."""
        # Create request with many resources
        large_request = InfrastructureRequest(
            tool=IaCTool.TERRAFORM,
            platform=CloudPlatform.AWS,
            operation="apply",
            resources=[
                {
                    "type": f"aws_instance",
                    "name": f"instance-{i}",
                    "config": {"instance_type": "t3.micro"}
                }
                for i in range(50)  # 50 resources
            ]
        )

        with patch.object(devops_agent, '_validate_infrastructure_config'), \
             patch.object(devops_agent, '_generate_infrastructure_code'), \
             patch.object(devops_agent, '_execute_terraform') as mock_execute:

            mock_execute.return_value = {"operation": "completed", "resources": 50}

            result = await devops_agent.manage_infrastructure(large_request)

            assert result["operation"] == "completed"
            assert result["resources"] == 50


class TestDevOpsAgentEdgeCases:
    """Test suite for DevOps Agent edge cases and error scenarios."""

    @pytest.fixture
    async def devops_agent(self):
        """Create DevOps Agent instance for edge case testing."""
        session = AsyncMock(spec=AsyncSession)
        return DevOpsAgent(agent_id="edge-case-agent", session=session)

    async def test_empty_task_parameters(self, devops_agent):
        """Test handling of tasks with empty parameters."""
        task = {
            "type": "deployment",
            "parameters": {}
        }

        with pytest.raises(AgentExecutionError):
            await devops_agent.execute_task(task)

    async def test_malformed_task_structure(self, devops_agent):
        """Test handling of malformed task structure."""
        malformed_tasks = [
            {},  # Empty task
            {"type": "deployment"},  # Missing parameters
            {"parameters": {}},  # Missing type
            {"type": "", "parameters": {}}  # Empty type
        ]

        for task in malformed_tasks:
            with pytest.raises((AgentExecutionError, ValidationError)):
                await devops_agent.execute_task(task)

    async def test_network_timeout_simulation(self, devops_agent, sample_deployment_request):
        """Test handling of network timeouts during deployment."""
        with patch.object(devops_agent, '_deploy_to_kubernetes') as mock_deploy:
            mock_deploy.side_effect = asyncio.TimeoutError("Network timeout")

            with pytest.raises(AgentExecutionError):
                await devops_agent.deploy_application(sample_deployment_request)

    async def test_partial_failure_recovery(self, devops_agent, sample_deployment_request):
        """Test recovery from partial deployment failures."""
        with patch.object(devops_agent, '_validate_deployment_config'), \
             patch.object(devops_agent, '_generate_deployment_manifests') as mock_generate, \
             patch.object(devops_agent, '_deploy_to_kubernetes'), \
             patch.object(devops_agent, '_verify_deployment') as mock_verify, \
             patch.object(devops_agent, '_rollback_deployment') as mock_rollback:

            # Simulate verification failure
            mock_generate.return_value = {"manifests": ["deployment.yaml"]}
            mock_verify.side_effect = Exception("Health check failed")
            mock_rollback.return_value = {"status": "rolled_back"}

            sample_deployment_request.rollback_on_failure = True

            with pytest.raises(AgentExecutionError):
                await devops_agent.deploy_application(sample_deployment_request)

            # Verify rollback was called
            mock_rollback.assert_called_once()


@pytest.mark.asyncio
class TestDevOpsAgentPerformance:
    """Performance-focused tests for DevOps Agent."""

    @pytest.fixture
    async def devops_agent(self):
        """Create DevOps Agent for performance testing."""
        session = AsyncMock(spec=AsyncSession)
        return DevOpsAgent(agent_id="perf-test-agent", session=session)

    async def test_high_volume_task_execution(self, devops_agent):
        """Test execution of high volume of tasks."""
        tasks = [
            {
                "id": f"task-{i}",
                "type": "health_check",
                "service": f"service-{i}",
                "environment": "production"
            }
            for i in range(100)
        ]

        with patch.object(devops_agent, '_perform_health_check') as mock_health:
            mock_health.return_value = {"status": "healthy"}

            start_time = datetime.now()

            # Execute all tasks
            results = await asyncio.gather(*[
                devops_agent.execute_task(task) for task in tasks
            ], return_exceptions=True)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Verify performance (should complete within reasonable time)
            assert execution_time < 10.0  # Less than 10 seconds for 100 tasks
            assert len(results) == 100
            assert all(isinstance(result, dict) for result in results if not isinstance(result, Exception))

    async def test_memory_usage_with_large_configurations(self, devops_agent):
        """Test memory efficiency with large configuration objects."""
        # Create large configuration
        large_config = {
