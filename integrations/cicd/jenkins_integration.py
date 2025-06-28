"""
Jenkins Integration for Agentical Framework

This module provides comprehensive Jenkins integration capabilities,
including pipeline creation, management, monitoring, and real-time status updates
for seamless CI/CD pipeline automation within the Agentical ecosystem.

Features:
- Jenkins pipeline creation and management
- Real-time build execution monitoring
- Webhook event processing for status updates
- Artifact and log retrieval
- Advanced pipeline templates and customization
- Security and authentication management
- Integration with Agentical workflow engine
"""

import asyncio
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
import base64

import httpx
import logfire
from urllib.parse import urljoin, quote

from ...core.exceptions import (
    ExternalServiceError,
    ValidationError,
    ConfigurationError,
    AuthenticationError
)
from ...core.logging import log_operation


class JenkinsBuildStatus(Enum):
    """Jenkins build statuses."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNSTABLE = "UNSTABLE"
    ABORTED = "ABORTED"
    NOT_BUILT = "NOT_BUILT"
    RUNNING = "RUNNING"
    QUEUED = "QUEUED"


class JenkinsJobType(Enum):
    """Jenkins job types."""
    FREESTYLE = "freestyle"
    PIPELINE = "pipeline"
    MULTIBRANCH = "multibranch"
    FOLDER = "folder"


@dataclass
class JenkinsBuild:
    """Jenkins build details."""
    number: int
    job_name: str
    status: Optional[JenkinsBuildStatus]
    result: Optional[JenkinsBuildStatus]
    url: str
    timestamp: datetime
    duration: Optional[int] = None
    estimated_duration: Optional[int] = None
    building: bool = False
    description: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    console_url: Optional[str] = None


@dataclass
class JenkinsJob:
    """Jenkins job details."""
    name: str
    url: str
    job_type: JenkinsJobType
    description: Optional[str]
    buildable: bool
    builds: List[JenkinsBuild] = field(default_factory=list)
    last_build: Optional[JenkinsBuild] = None
    last_successful_build: Optional[JenkinsBuild] = None
    last_failed_build: Optional[JenkinsBuild] = None
    next_build_number: int = 1
    parameters: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class JenkinsQueue:
    """Jenkins build queue item."""
    id: int
    task_name: str
    url: str
    why: str
    blocked: bool = False
    buildable: bool = True
    stuck: bool = False
    in_queue_since: Optional[datetime] = None
    expected_build_number: Optional[int] = None


class JenkinsIntegration:
    """
    Comprehensive Jenkins integration for Agentical framework.

    Provides full lifecycle management of Jenkins pipelines including
    creation, monitoring, execution control, and artifact management with
    real-time status updates and seamless integration with Agentical agents.
    """

    def __init__(
        self,
        jenkins_url: str,
        username: str,
        api_token: str,
        verify_ssl: bool = True
    ):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.verify_ssl = verify_ssl

        # Create authentication header
        auth_string = f"{username}:{api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

        # HTTP client with authentication
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/json",
                "User-Agent": "Agentical-Framework/1.0"
            },
            timeout=30.0,
            verify=verify_ssl
        )

        # Job and build cache
        self.job_cache: Dict[str, JenkinsJob] = {}
        self.build_cache: Dict[str, JenkinsBuild] = {}

        # Event handlers
        self.event_handlers: Dict[str, List] = {}

        # Monitoring task
        self.monitoring_task: Optional[asyncio.Task] = None
        self.shutdown_requested = False

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        self.shutdown_requested = True
        if self.monitoring_task:
            self.monitoring_task.cancel()
        await self.http_client.aclose()

    async def start_monitoring(self) -> None:
        """Start background monitoring of Jenkins builds."""
        if not self.monitoring_task:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

    @log_operation("create_pipeline_job")
    async def create_pipeline_job(
        self,
        job_name: str,
        pipeline_script: str,
        description: str = None,
        parameters: List[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new Jenkins pipeline job.

        Args:
            job_name: Name of the job
            pipeline_script: Jenkinsfile content
            description: Job description
            parameters: Job parameters

        Returns:
            Job URL
        """
        with logfire.span(
            "JenkinsIntegration.create_pipeline_job",
            job_name=job_name
        ):
            try:
                # Generate job configuration XML
                config_xml = self._generate_pipeline_config(
                    pipeline_script, description, parameters or []
                )

                # Create job via Jenkins API
                url = f"{self.jenkins_url}/createItem"
                params = {"name": job_name}
                headers = {"Content-Type": "application/xml"}

                response = await self.http_client.post(
                    url,
                    params=params,
                    content=config_xml,
                    headers=headers
                )

                if response.status_code not in [200, 201]:
                    raise ExternalServiceError(
                        f"Failed to create Jenkins job: {response.status_code} {response.text}"
                    )

                job_url = f"{self.jenkins_url}/job/{quote(job_name)}"

                logfire.info(
                    "Jenkins pipeline job created",
                    job_name=job_name,
                    job_url=job_url
                )

                return job_url

            except Exception as e:
                logfire.error("Failed to create Jenkins pipeline job", error=str(e))
                raise

    @log_operation("trigger_build")
    async def trigger_build(
        self,
        job_name: str,
        parameters: Dict[str, Any] = None,
        token: str = None
    ) -> JenkinsBuild:
        """
        Trigger a Jenkins build.

        Args:
            job_name: Name of the job
            parameters: Build parameters
            token: Build token for remote triggering

        Returns:
            Build details
        """
        with logfire.span(
            "JenkinsIntegration.trigger_build",
            job_name=job_name
        ):
            try:
                # Determine build URL based on parameters
                if parameters:
                    build_url = f"{self.jenkins_url}/job/{quote(job_name)}/buildWithParameters"
                    data = parameters
                else:
                    build_url = f"{self.jenkins_url}/job/{quote(job_name)}/build"
                    data = {}

                # Add token if provided
                if token:
                    data["token"] = token

                # Trigger build
                response = await self.http_client.post(build_url, data=data)

                if response.status_code not in [200, 201, 202]:
                    raise ExternalServiceError(
                        f"Failed to trigger Jenkins build: {response.status_code} {response.text}"
                    )

                # Get queue item location from response
                queue_location = response.headers.get("Location")
                if not queue_location:
                    raise ExternalServiceError("No queue location returned from Jenkins")

                # Wait for build to start and get build number
                build_number = await self._wait_for_build_start(job_name, queue_location)

                # Get build details
                build = await self.get_build(job_name, build_number)

                logfire.info(
                    "Jenkins build triggered",
                    job_name=job_name,
                    build_number=build_number
                )

                return build

            except Exception as e:
                logfire.error("Failed to trigger Jenkins build", error=str(e))
                raise

    @log_operation("get_build")
    async def get_build(
        self,
        job_name: str,
        build_number: int
    ) -> JenkinsBuild:
        """
        Get Jenkins build details.

        Args:
            job_name: Name of the job
            build_number: Build number

        Returns:
            Build details
        """
        with logfire.span(
            "JenkinsIntegration.get_build",
            job_name=job_name,
            build_number=build_number
        ):
            try:
                cache_key = f"{job_name}#{build_number}"

                # Check cache for completed builds
                if cache_key in self.build_cache:
                    cached_build = self.build_cache[cache_key]
                    if not cached_build.building:
                        return cached_build

                # Fetch from Jenkins API
                url = f"{self.jenkins_url}/job/{quote(job_name)}/{build_number}/api/json"
                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to get Jenkins build: {response.status_code} {response.text}"
                    )

                data = response.json()
                build = self._parse_build(data, job_name)

                # Update cache
                self.build_cache[cache_key] = build

                return build

            except Exception as e:
                logfire.error("Failed to get Jenkins build", error=str(e))
                raise

    @log_operation("stop_build")
    async def stop_build(
        self,
        job_name: str,
        build_number: int
    ) -> bool:
        """
        Stop a running Jenkins build.

        Args:
            job_name: Name of the job
            build_number: Build number

        Returns:
            True if stopped successfully
        """
        with logfire.span(
            "JenkinsIntegration.stop_build",
            job_name=job_name,
            build_number=build_number
        ):
            try:
                url = f"{self.jenkins_url}/job/{quote(job_name)}/{build_number}/stop"
                response = await self.http_client.post(url)

                if response.status_code in [200, 201, 302]:
                    # Update cache
                    cache_key = f"{job_name}#{build_number}"
                    if cache_key in self.build_cache:
                        self.build_cache[cache_key].building = False
                        self.build_cache[cache_key].result = JenkinsBuildStatus.ABORTED

                    logfire.info("Jenkins build stopped", job_name=job_name, build_number=build_number)
                    return True
                else:
                    logfire.warning(
                        "Failed to stop Jenkins build",
                        job_name=job_name,
                        build_number=build_number,
                        status_code=response.status_code
                    )
                    return False

            except Exception as e:
                logfire.error("Failed to stop Jenkins build", error=str(e))
                return False

    @log_operation("get_job")
    async def get_job(self, job_name: str) -> JenkinsJob:
        """
        Get Jenkins job details.

        Args:
            job_name: Name of the job

        Returns:
            Job details
        """
        with logfire.span("JenkinsIntegration.get_job", job_name=job_name):
            try:
                # Check cache
                if job_name in self.job_cache:
                    return self.job_cache[job_name]

                # Fetch from Jenkins API
                url = f"{self.jenkins_url}/job/{quote(job_name)}/api/json"
                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to get Jenkins job: {response.status_code} {response.text}"
                    )

                data = response.json()
                job = self._parse_job(data)

                # Update cache
                self.job_cache[job_name] = job

                return job

            except Exception as e:
                logfire.error("Failed to get Jenkins job", error=str(e))
                raise

    @log_operation("list_jobs")
    async def list_jobs(self, folder: str = None) -> List[JenkinsJob]:
        """
        List Jenkins jobs.

        Args:
            folder: Optional folder name to list jobs from

        Returns:
            List of jobs
        """
        with logfire.span("JenkinsIntegration.list_jobs", folder=folder):
            try:
                if folder:
                    url = f"{self.jenkins_url}/job/{quote(folder)}/api/json"
                else:
                    url = f"{self.jenkins_url}/api/json"

                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to list Jenkins jobs: {response.status_code} {response.text}"
                    )

                data = response.json()
                jobs = []

                for job_data in data.get("jobs", []):
                    job = self._parse_job_summary(job_data)
                    jobs.append(job)
                    # Update cache
                    self.job_cache[job.name] = job

                return jobs

            except Exception as e:
                logfire.error("Failed to list Jenkins jobs", error=str(e))
                raise

    @log_operation("get_console_output")
    async def get_console_output(
        self,
        job_name: str,
        build_number: int,
        start: int = 0
    ) -> str:
        """
        Get Jenkins build console output.

        Args:
            job_name: Name of the job
            build_number: Build number
            start: Starting byte position

        Returns:
            Console output
        """
        with logfire.span(
            "JenkinsIntegration.get_console_output",
            job_name=job_name,
            build_number=build_number
        ):
            try:
                url = f"{self.jenkins_url}/job/{quote(job_name)}/{build_number}/consoleText"
                params = {"start": start} if start > 0 else {}

                response = await self.http_client.get(url, params=params)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to get console output: {response.status_code} {response.text}"
                    )

                return response.text

            except Exception as e:
                logfire.error("Failed to get Jenkins console output", error=str(e))
                raise

    @log_operation("get_artifacts")
    async def get_artifacts(
        self,
        job_name: str,
        build_number: int
    ) -> List[Dict[str, Any]]:
        """
        Get Jenkins build artifacts.

        Args:
            job_name: Name of the job
            build_number: Build number

        Returns:
            List of artifacts
        """
        with logfire.span(
            "JenkinsIntegration.get_artifacts",
            job_name=job_name,
            build_number=build_number
        ):
            try:
                url = f"{self.jenkins_url}/job/{quote(job_name)}/{build_number}/api/json"
                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to get build details: {response.status_code} {response.text}"
                    )

                data = response.json()
                artifacts = []

                for artifact_data in data.get("artifacts", []):
                    artifact = {
                        "fileName": artifact_data["fileName"],
                        "displayPath": artifact_data["displayPath"],
                        "relativePath": artifact_data["relativePath"],
                        "download_url": f"{self.jenkins_url}/job/{quote(job_name)}/{build_number}/artifact/{artifact_data['relativePath']}"
                    }
                    artifacts.append(artifact)

                return artifacts

            except Exception as e:
                logfire.error("Failed to get Jenkins build artifacts", error=str(e))
                raise

    @log_operation("download_artifact")
    async def download_artifact(
        self,
        job_name: str,
        build_number: int,
        artifact_path: str
    ) -> bytes:
        """
        Download Jenkins build artifact.

        Args:
            job_name: Name of the job
            build_number: Build number
            artifact_path: Relative path to artifact

        Returns:
            Artifact content as bytes
        """
        with logfire.span(
            "JenkinsIntegration.download_artifact",
            job_name=job_name,
            build_number=build_number,
            artifact_path=artifact_path
        ):
            try:
                url = f"{self.jenkins_url}/job/{quote(job_name)}/{build_number}/artifact/{artifact_path}"
                response = await self.http_client.get(url)

                if response.status_code != 200:
                    raise ExternalServiceError(
                        f"Failed to download artifact: {response.status_code} {response.text}"
                    )

                return response.content

            except Exception as e:
                logfire.error("Failed to download Jenkins artifact", error=str(e))
                raise

    def generate_pipeline_template(
        self,
        template_type: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Generate Jenkins pipeline (Jenkinsfile) template.

        Args:
            template_type: Type of template (ci, cd, test, etc.)
            config: Template configuration

        Returns:
            Jenkinsfile content
        """
        if template_type == "ci":
            return self._generate_ci_pipeline(config)
        elif template_type == "cd":
            return self._generate_cd_pipeline(config)
        elif template_type == "test":
            return self._generate_test_pipeline(config)
        elif template_type == "docker":
            return self._generate_docker_pipeline(config)
        else:
            raise ValidationError(f"Unknown template type: {template_type}")

    def on_event(self, event_type: str, handler) -> None:
        """Register event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    # Private methods

    async def _wait_for_build_start(self, job_name: str, queue_location: str, timeout: int = 60) -> int:
        """Wait for build to start and return build number."""
        start_time = datetime.now()

        while (datetime.now() - start_time).seconds < timeout:
            try:
                # Get queue item details
                queue_url = f"{queue_location}api/json"
                response = await self.http_client.get(queue_url)

                if response.status_code == 200:
                    queue_data = response.json()

                    # Check if build has started
                    if "executable" in queue_data:
                        build_number = queue_data["executable"]["number"]
                        return build_number

                    # Check if build is cancelled
                    if queue_data.get("cancelled", False):
                        raise ExternalServiceError("Build was cancelled")

                await asyncio.sleep(2)

            except Exception as e:
                logfire.warning(f"Error checking queue status: {str(e)}")
                await asyncio.sleep(2)

        raise ExternalServiceError("Timeout waiting for build to start")

    def _parse_build(self, data: Dict[str, Any], job_name: str) -> JenkinsBuild:
        """Parse build data from Jenkins API."""
        return JenkinsBuild(
            number=data["number"],
            job_name=job_name,
            status=JenkinsBuildStatus(data["result"]) if data.get("result") else None,
            result=JenkinsBuildStatus(data["result"]) if data.get("result") else None,
            url=data["url"],
            timestamp=datetime.fromtimestamp(data["timestamp"] / 1000),
            duration=data.get("duration"),
            estimated_duration=data.get("estimatedDuration"),
            building=data.get("building", False),
            description=data.get("description"),
            parameters={
                param["name"]: param.get("value")
                for param in data.get("actions", [])
                if param.get("_class") == "hudson.model.ParametersAction"
                for param in param.get("parameters", [])
            },
            artifacts=[
                {
                    "fileName": artifact["fileName"],
                    "relativePath": artifact["relativePath"],
                    "displayPath": artifact["displayPath"]
                }
                for artifact in data.get("artifacts", [])
            ],
            console_url=f"{data['url']}console"
        )

    def _parse_job(self, data: Dict[str, Any]) -> JenkinsJob:
        """Parse job data from Jenkins API."""
        job_type = JenkinsJobType.FREESTYLE
        if "org.jenkinsci.plugins.workflow.job.WorkflowJob" in data.get("_class", ""):
            job_type = JenkinsJobType.PIPELINE

        # Parse builds
        builds = []
        for build_data in data.get("builds", []):
            # Simplified build info for job listing
            build = JenkinsBuild(
                number=build_data["number"],
                job_name=data["name"],
                status=None,  # Will be filled when fetching full build details
                result=None,
                url=build_data["url"],
                timestamp=datetime.now(),  # Placeholder
                building=False
            )
            builds.append(build)

        return JenkinsJob(
            name=data["name"],
            url=data["url"],
            job_type=job_type,
            description=data.get("description"),
            buildable=data.get("buildable", True),
            builds=builds,
            next_build_number=data.get("nextBuildNumber", 1)
        )

    def _parse_job_summary(self, data: Dict[str, Any]) -> JenkinsJob:
        """Parse job summary data from Jenkins API."""
        job_type = JenkinsJobType.FREESTYLE
        if "workflow" in data.get("_class", "").lower():
            job_type = JenkinsJobType.PIPELINE
        elif "folder" in data.get("_class", "").lower():
            job_type = JenkinsJobType.FOLDER

        return JenkinsJob(
            name=data["name"],
            url=data["url"],
            job_type=job_type,
            description=data.get("description"),
            buildable=data.get("buildable", True)
        )

    def _generate_pipeline_config(
        self,
        pipeline_script: str,
        description: str = None,
        parameters: List[Dict[str, Any]] = None
    ) -> str:
        """Generate Jenkins pipeline job configuration XML."""
        root = ET.Element("flow-definition", plugin="workflow-job@2.40")

        if description:
            desc_elem = ET.SubElement(root, "description")
            desc_elem.text = description

        # Keep builds for 30 days
        properties = ET.SubElement(root, "properties")
        build_discarder = ET.SubElement(
            properties,
            "jenkins.model.BuildDiscarderProperty"
        )
        strategy = ET.SubElement(
            build_discarder,
            "strategy",
            {"class": "hudson.tasks.LogRotator"}
        )
        ET.SubElement(strategy, "daysToKeep").text = "30"
        ET.SubElement(strategy, "numToKeep").text = "100"

        # Parameters
        if parameters:
            params_prop = ET.SubElement(
                properties,
                "hudson.model.ParametersDefinitionProperty"
            )
            params_defs = ET.SubElement(params_prop, "parameterDefinitions")

            for param in parameters:
                if param.get("type") == "string":
                    param_def = ET.SubElement(
                        params_defs,
                        "hudson.model.StringParameterDefinition"
                    )
                    ET.SubElement(param_def, "name").text = param["name"]
                    ET.SubElement(param_def, "description").text = param.get("description", "")
                    ET.SubElement(param_def, "defaultValue").text = param.get("default", "")

        # Pipeline definition
        definition = ET.SubElement(
            root,
            "definition",
            {"class": "org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition", "plugin": "workflow-cps@2.92"}
        )
        script_elem = ET.SubElement(definition, "script")
        script_elem.text = pipeline_script
        ET.SubElement(definition, "sandbox").text = "true"

        return ET.tostring(root, encoding="unicode")

    def _generate_ci_pipeline(self, config: Dict[str, Any]) -> str:
        """Generate CI pipeline (Jenkinsfile)."""
        language = config.get("language", "python")

        if language == "python":
            return """
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh 'python -m pip install --upgrade pip'
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Lint') {
            steps {
                sh 'flake8 src/ tests/'
                sh 'black --check src/ tests/'
            }
        }

        stage('Test') {
            steps {
                sh 'pytest tests/ --cov=src/ --cov-report=xml --junitxml=test-results.xml'
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishCoverageGlobal(coberturaReportFile: 'coverage.xml')
                }
            }
        }

        stage('Build') {
            steps {
                sh 'python setup.py bdist_wheel'
            }
            post {
                success {
                    archiveArtifacts artifacts: 'dist/*.whl', fingerprint: true
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
""".strip()

        return """
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                echo 'Building...'
            }
        }
        stage('Test') {
            steps {
                echo 'Testing...'
            }
        }
    }
}
""".strip()

    def _generate_cd_pipeline(self, config: Dict[str, Any]) -> str:
        """Generate CD pipeline (Jenkinsfile)."""
        return """
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['staging', 'production'],
            description: 'Deployment environment'
        )
    }

    stages {
        stage('Build') {
            steps {
                sh 'docker build -t ${JOB_NAME}:${BUILD_NUMBER} .'
                sh 'docker tag ${JOB_NAME}:${BUILD_NUMBER} ${JOB_NAME}:latest'
            }
        }

        stage('Deploy to Staging') {
            when {
                expression { params.ENVIRONMENT == 'staging' }
            }
            steps {
                sh 'docker push ${JOB_NAME}:${BUILD_NUMBER}'
                sh 'kubectl set image deployment/${JOB_NAME} ${JOB_NAME}=${JOB_NAME}:${BUILD_NUMBER}'
            }
        }

        stage('Deploy to Production') {
            when {
                expression { params.ENVIRONMENT == 'production' }
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                sh 'docker push ${JOB_NAME}:${BUILD_NUMBER}'
                sh 'kubectl set image deployment/${JOB_NAME} ${JOB_NAME}=${JOB_NAME}:${BUILD_NUMBER} --namespace=production'
            }
        }
    }

    post {
        success {
            slackSend(
                channel: '#deployments',
                color: 'good',
                message: "Deployment successful: ${JOB_NAME} #${BUILD_NUMBER} to ${params.ENVIRONMENT}"
            )
        }
        failure {
            slackSend(
                channel: '#deployments',
                color: 'danger',
                message: "Deployment failed: ${JOB_NAME} #${BUILD_NUMBER} to ${params.ENVIRONMENT}"
            )
        }
    }
}
""".strip()

    def _generate_test_pipeline(self, config: Dict[str, Any]) -> str:
        """Generate test pipeline (Jenkinsfile)."""
        return """
pipeline {
    agent any

    stages {
        stage('Unit Tests') {
            steps {
                sh 'pytest tests/unit/ --junitxml=unit-test-results.xml'
            }
            post {
                always {
                    junit 'unit-test-results.xml'
                }
            }
        }

        stage('Integration Tests') {
            steps {
                sh 'pytest tests/integration/ --junitxml=integration-test-results.xml'
            }
            post {
                always {
                    junit 'integration-test-results.xml'
                }
            }
        }

        stage('Security Tests') {
            steps {
                sh 'safety check'
                sh 'bandit -r src/ -f json -o security-report.json'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'security-report.json'
                }
            }
        }
    }
}
""".strip()

    def _generate_docker_pipeline(self, config: Dict[str, Any]) -> str:
        """Generate Docker pipeline (Jenkinsfile)."""
        return """
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = credentials('docker-registry')
        IMAGE_NAME = "${JOB_NAME}"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Build Image') {
            steps {
                script {
                    docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                }
            }
        }

        stage('Test Image') {
            steps {
                script {
                    def image = docker.image("${IMAGE_NAME}:${IMAGE_TAG}")
                    image.inside {
                        sh 'pytest tests/'
                    }
                }
            }
        }

        stage('Security Scan') {
