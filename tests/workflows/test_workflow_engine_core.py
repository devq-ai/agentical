"""
Comprehensive Test Suite for Workflow Engine Core (PB-005.1)

This module provides comprehensive testing for the workflow engine core components
including multi-agent coordination, state management, and performance monitoring.

Test Coverage:
- Multi-agent coordination strategies
- Workflow state persistence and recovery
- Performance monitoring and metrics
- Error handling and recovery mechanisms
- Integration between core components
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import the modules under test
from agentical.workflows.engine.workflow_engine import WorkflowEngine, WorkflowEngineFactory
from agentical.workflows.engine.multi_agent_coordinator import (
    MultiAgentCoordinator, CoordinationStrategy, AgentTask, TaskPriority, AgentState
)
from agentical.workflows.engine.state_manager import (
    WorkflowStateManager, StateCheckpoint, CheckpointLevel, StateVersion
)
from agentical.workflows.engine.performance_monitor import (
    PerformanceMonitor, MetricType, AlertSeverity, ThresholdRule
)
from agentical.workflows.engine.execution_context import ExecutionContext, ExecutionPhase

# Import models and exceptions
from agentical.db.models.workflow import (
    Workflow, WorkflowExecution, WorkflowStep, WorkflowType,
    WorkflowStatus, ExecutionStatus, StepType, StepStatus
)
from agentical.db.models.agent import Agent, AgentStatus
from agentical.core.exceptions import WorkflowExecutionError, WorkflowValidationError


@pytest.fixture
async def mock_db_session():
    """Mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
async def mock_agent_registry():
    """Mock agent registry."""
    registry = Mock()
    registry.get_agent = AsyncMock()
    registry.list_agents = AsyncMock()
    return registry


@pytest.fixture
def sample_workflow():
    """Create a sample workflow for testing."""
    workflow = Workflow(
        id=1,
        name="Test Workflow",
        description="A test workflow for unit testing",
        workflow_type=WorkflowType.MULTI_AGENT,
        status=WorkflowStatus.ACTIVE,
        configuration={"timeout_seconds": 300}
    )

    # Add sample steps
    step1 = WorkflowStep(
        id=1,
        workflow_id=1,
        name="Step 1",
        step_type=StepType.AGENT_TASK,
        step_order=1,
        configuration={
            "multi_agent": True,
            "coordination_strategy": "parallel",
            "agent_requirements": {
                "capabilities": ["code_generation"],
                "count": 2
            }
        }
    )

    step2 = WorkflowStep(
        id=2,
        workflow_id=1,
        name="Step 2",
        step_type=StepType.CONDITION,
        step_order=2,
        depends_on="[1]",
        configuration={"condition": "step_1_result.success == true"}
    )

    workflow.steps = [step1, step2]
    return workflow


@pytest.fixture
def sample_execution():
    """Create a sample workflow execution for testing."""
    return WorkflowExecution(
        execution_id=f"test_{uuid.uuid4().hex[:8]}",
        workflow_id=1,
        status=ExecutionStatus.PENDING,
        input_data={"test_input": "value"},
        context_data={}
    )


@pytest.fixture
def sample_agents():
    """Create sample agents for testing."""
    return [
        Agent(
            id="agent_1",
            name="Test Agent 1",
            agent_type="code_agent",
            status=AgentStatus.ACTIVE,
            capabilities={"code_generation": 0.9, "testing": 0.8}
        ),
        Agent(
            id="agent_2",
            name="Test Agent 2",
            agent_type="devops_agent",
            status=AgentStatus.ACTIVE,
            capabilities={"deployment": 0.95, "monitoring": 0.85}
        )
    ]


class TestMultiAgentCoordinator:
    """Test cases for MultiAgentCoordinator."""

    @pytest.fixture
    async def coordinator(self, mock_db_session, mock_agent_registry):
        """Create coordinator instance for testing."""
        coordinator = MultiAgentCoordinator(
            db_session=mock_db_session,
            agent_registry=mock_agent_registry,
            max_concurrent_agents=5,
            enable_load_balancing=True
        )
        await coordinator.start()
        yield coordinator
        await coordinator.shutdown()

    @pytest.mark.asyncio
    async def test_parallel_coordination(self, coordinator, sample_workflow, sample_execution, sample_agents):
        """Test parallel agent coordination strategy."""
        # Mock agent selection
        coordinator._select_agents_for_step = AsyncMock(return_value=sample_agents)

        # Mock agent execution
        async def mock_execute_agent_task(agent, task, context):
            return {"agent_id": agent.id, "result": "success"}

        coordinator._execute_agent_task = mock_execute_agent_task

        # Create execution context
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={"test": "data"},
            config={}
        )

        # Execute parallel coordination
        step = sample_workflow.steps[0]
        result = await coordinator.execute_multi_agent_step(
            step=step,
            context=context,
            strategy=CoordinationStrategy.PARALLEL
        )

        # Verify results
        assert result is not None
        assert "results" in result
        assert len(result["results"]) == 2
        assert result["success_count"] == 2
        assert result["total_count"] == 2

    @pytest.mark.asyncio
    async def test_sequential_coordination(self, coordinator, sample_workflow, sample_execution, sample_agents):
        """Test sequential agent coordination strategy."""
        # Mock agent selection
        coordinator._select_agents_for_step = AsyncMock(return_value=sample_agents)

        # Mock agent execution with sequential results
        execution_order = []

        async def mock_execute_agent_task(agent, task, context):
            execution_order.append(agent.id)
            return {"agent_id": agent.id, "step": len(execution_order)}

        coordinator._execute_agent_task = mock_execute_agent_task

        # Create execution context
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={"test": "data"},
            config={}
        )

        # Execute sequential coordination
        step = sample_workflow.steps[0]
        result = await coordinator.execute_multi_agent_step(
            step=step,
            context=context,
            strategy=CoordinationStrategy.SEQUENTIAL
        )

        # Verify sequential execution
        assert result is not None
        assert "results" in result
        assert len(result["results"]) == 2
        assert execution_order == ["agent_1", "agent_2"]
        assert result["agent_count"] == 2

    @pytest.mark.asyncio
    async def test_pipeline_coordination(self, coordinator, sample_workflow, sample_execution, sample_agents):
        """Test pipeline agent coordination strategy."""
        # Mock agent selection
        coordinator._select_agents_for_step = AsyncMock(return_value=sample_agents)

        # Mock agent execution with pipeline data flow
        async def mock_execute_agent_task(agent, task, context):
            input_data = task.input_data
            # Each agent adds to the pipeline
            output = input_data.copy()
            output[f"{agent.id}_processed"] = True
            return output

        coordinator._execute_agent_task = mock_execute_agent_task

        # Create execution context
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={"initial_data": "test"},
            config={}
        )

        # Execute pipeline coordination
        step = sample_workflow.steps[0]
        result = await coordinator.execute_multi_agent_step(
            step=step,
            context=context,
            strategy=CoordinationStrategy.PIPELINE
        )

        # Verify pipeline results
        assert result is not None
        assert "initial_data" in result
        assert "agent_1_processed" in result
        assert "agent_2_processed" in result

    @pytest.mark.asyncio
    async def test_scatter_gather_coordination(self, coordinator, sample_workflow, sample_execution, sample_agents):
        """Test scatter-gather agent coordination strategy."""
        # Mock agent selection
        coordinator._select_agents_for_step = AsyncMock(return_value=sample_agents)

        # Mock agent execution
        async def mock_execute_agent_task(agent, task, context):
            # Each agent processes its chunk
            return {"agent_id": agent.id, "processed_items": len(task.input_data)}

        coordinator._execute_agent_task = mock_execute_agent_task

        # Create execution context with data to scatter
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={
                "item1": "data1",
                "item2": "data2",
                "item3": "data3",
                "item4": "data4"
            },
            config={}
        )

        # Execute scatter-gather coordination
        step = sample_workflow.steps[0]
        result = await coordinator.execute_multi_agent_step(
            step=step,
            context=context,
            strategy=CoordinationStrategy.SCATTER_GATHER
        )

        # Verify scatter-gather results
        assert result is not None
        assert "combined_results" in result
        assert result["result_count"] == 2

    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, coordinator, sample_workflow, sample_execution, sample_agents):
        """Test handling of agent failures during coordination."""
        # Mock agent selection
        coordinator._select_agents_for_step = AsyncMock(return_value=sample_agents)

        # Mock agent execution with one failure
        async def mock_execute_agent_task(agent, task, context):
            if agent.id == "agent_1":
                raise Exception("Agent 1 failed")
            return {"agent_id": agent.id, "result": "success"}

        coordinator._execute_agent_task = mock_execute_agent_task

        # Create execution context
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={"test": "data"},
            config={}
        )

        # Execute parallel coordination with failure
        step = sample_workflow.steps[0]
        result = await coordinator.execute_multi_agent_step(
            step=step,
            context=context,
            strategy=CoordinationStrategy.PARALLEL
        )

        # Verify failure handling
        assert result is not None
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert len(result["results"]) == 1
        assert result["success_count"] == 1

    def test_agent_task_lifecycle(self):
        """Test AgentTask lifecycle management."""
        task = AgentTask(
            task_id="test_task",
            agent_id="agent_1",
            step_id=1,
            task_type="code_generation",
            input_data={"code": "print('hello')"},
            config={},
            priority=TaskPriority.HIGH
        )

        # Test initial state
        assert task.state == AgentState.ASSIGNED
        assert task.attempts == 0
        assert task.result is None

        # Test execution start
        task.start_execution()
        assert task.state == AgentState.EXECUTING
        assert task.attempts == 1
        assert task.started_at is not None

        # Test successful completion
        task.complete_execution({"status": "success"})
        assert task.state == AgentState.COMPLETED
        assert task.result is not None
        assert task.completed_at is not None

        # Test execution time calculation
        execution_time = task.get_execution_time()
        assert execution_time is not None
        assert execution_time.total_seconds() >= 0

    def test_agent_task_retry_logic(self):
        """Test agent task retry logic."""
        task = AgentTask(
            task_id="test_task",
            agent_id="agent_1",
            step_id=1,
            task_type="code_generation",
            input_data={},
            config={},
            retry_config={"max_attempts": 3}
        )

        # Test retry eligibility
        assert task.can_retry() == False  # Not failed yet

        # Fail the task
        task.start_execution()
        task.fail_execution("Network error")
        assert task.can_retry() == True
        assert task.attempts == 1

        # Try again
        task.start_execution()
        task.fail_execution("Timeout")
        assert task.can_retry() == True
        assert task.attempts == 2

        # Final attempt
        task.start_execution()
        task.fail_execution("Fatal error")
        assert task.can_retry() == False
        assert task.attempts == 3


class TestWorkflowStateManager:
    """Test cases for WorkflowStateManager."""

    @pytest.fixture
    async def state_manager(self, mock_db_session):
        """Create state manager instance for testing."""
        return WorkflowStateManager(
            db_session=mock_db_session,
            checkpoint_interval=10,  # Fast for testing
            max_checkpoints_per_execution=5,
            enable_compression=False  # Disable for testing
        )

    @pytest.mark.asyncio
    async def test_checkpoint_creation(self, state_manager, sample_workflow, sample_execution):
        """Test checkpoint creation functionality."""
        # Create execution context
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={"test": "data"},
            config={}
        )

        # Update context state
        context.set_variable("step1_result", "success")
        context.mark_step_completed(1)
        context.set_phase(ExecutionPhase.EXECUTION)

        # Create checkpoint
        checkpoint = await state_manager.create_checkpoint(
            context=context,
            checkpoint_level=CheckpointLevel.STANDARD,
            trigger="manual_test"
        )

        # Verify checkpoint
        assert checkpoint is not None
        assert checkpoint.execution_id == sample_execution.execution_id
        assert checkpoint.checkpoint_level == CheckpointLevel.STANDARD
        assert "variables" in checkpoint.state_data
        assert "completed_steps" in checkpoint.state_data
        assert checkpoint.state_data["variables"]["step1_result"] == "success"
        assert 1 in checkpoint.state_data["completed_steps"]

    @pytest.mark.asyncio
    async def test_checkpoint_integrity(self, state_manager, sample_workflow, sample_execution):
        """Test checkpoint integrity validation."""
        # Create execution context
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={"test": "data"},
            config={}
        )

        # Create checkpoint
        checkpoint = await state_manager.create_checkpoint(context)

        # Verify integrity
        assert checkpoint.validate_integrity() == True

        # Corrupt checkpoint data
        checkpoint.state_data["corrupted"] = "data"
        assert checkpoint.validate_integrity() == False

    @pytest.mark.asyncio
    async def test_execution_state_management(self, state_manager, sample_workflow, sample_execution):
        """Test execution state management lifecycle."""
        # Create execution context
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={"initial": "data"},
            config={}
        )

        # Start managing execution
        await state_manager.start_managing_execution(context)
        assert sample_execution.execution_id in state_manager.active_executions

        # Update execution state
        context.set_variable("progress", 50)
        context.mark_step_completed(1)

        # Create manual checkpoint
        checkpoint = await state_manager.create_checkpoint(
            context=context,
            trigger="progress_update"
        )

        # Stop managing execution
        await state_manager.stop_managing_execution(
            sample_execution.execution_id,
            final_checkpoint=True
        )
        assert sample_execution.execution_id not in state_manager.active_executions

    def test_checkpoint_levels(self, sample_workflow, sample_execution):
        """Test different checkpoint levels."""
        # Create execution context
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={"test": "data"},
            config={"debug": True}
        )

        # Test minimal checkpoint
        minimal_checkpoint = StateCheckpoint(
            checkpoint_id="minimal_test",
            execution_id=sample_execution.execution_id,
            timestamp=datetime.utcnow(),
            checkpoint_level=CheckpointLevel.MINIMAL,
            state_data={"basic": "data"}
        )

        assert minimal_checkpoint.checkpoint_level == CheckpointLevel.MINIMAL
        assert minimal_checkpoint.size_bytes > 0

        # Test comprehensive checkpoint
        comprehensive_checkpoint = StateCheckpoint(
            checkpoint_id="comprehensive_test",
            execution_id=sample_execution.execution_id,
            timestamp=datetime.utcnow(),
            checkpoint_level=CheckpointLevel.COMPREHENSIVE,
            state_data={
                "variables": context.variables,
                "global_context": context.global_context,
                "step_results": context.step_results
            }
        )

        assert comprehensive_checkpoint.checkpoint_level == CheckpointLevel.COMPREHENSIVE
        assert comprehensive_checkpoint.size_bytes > minimal_checkpoint.size_bytes


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor."""

    @pytest.fixture
    async def performance_monitor(self, mock_db_session):
        """Create performance monitor instance for testing."""
        monitor = PerformanceMonitor(
            db_session=mock_db_session,
            monitoring_interval=5,  # Fast for testing
            metric_retention_hours=1,
            enable_system_monitoring=True,
            enable_workflow_profiling=True
        )
        await monitor.start()
        yield monitor
        await monitor.stop()

    @pytest.mark.asyncio
    async def test_metric_recording(self, performance_monitor):
        """Test basic metric recording functionality."""
        # Record various metric types
        performance_monitor.record_metric("cpu_usage", 75.5, MetricType.GAUGE, unit="%")
        performance_monitor.record_metric("requests_total", 100, MetricType.COUNTER)
        performance_monitor.record_metric("response_time", 250, MetricType.TIMER, unit="ms")

        # Verify metrics were recorded
        assert "cpu_usage" in performance_monitor.metrics
        assert "requests_total" in performance_monitor.metrics
        assert "response_time" in performance_monitor.metrics

        # Check metric values
        cpu_metrics = list(performance_monitor.metrics["cpu_usage"])
        assert len(cpu_metrics) == 1
        assert cpu_metrics[0].value == 75.5
        assert cpu_metrics[0].unit == "%"

    @pytest.mark.asyncio
    async def test_workflow_profiling(self, performance_monitor, sample_workflow, sample_execution):
        """Test workflow performance profiling."""
        # Create execution context
        context = ExecutionContext(
            execution=sample_execution,
            workflow=sample_workflow,
            input_data={"test": "data"},
            config={}
        )

        # Start profiling
        performance_monitor.start_workflow_profiling(context)
        assert sample_execution.execution_id in performance_monitor.workflow_stats

        # Simulate workflow progress
        context.mark_step_completed(1, timedelta(seconds=5))
        performance_monitor.update_workflow_progress(context)

        # Complete profiling
        stats = performance_monitor.complete_workflow_profiling(context)

        # Verify profiling results
        assert stats.execution_id == sample_execution.execution_id
        assert stats.completed_steps == 1
        assert stats.average_step_duration == 5.0
        assert stats.end_time is not None

    @pytest.mark.asyncio
    async def test_threshold_alerting(self, performance_monitor):
        """Test performance threshold alerting."""
        # Add custom threshold rule
        rule = ThresholdRule(
            metric_name="test_metric",
            threshold_value=80.0,
            comparison="gt",
            severity=AlertSeverity.WARNING,
            message_template="Test metric too high: {value}",
            consecutive_violations=2
        )
        performance_monitor.add_threshold_rule(rule)

        # Record metrics below threshold
        performance_monitor.record_metric("test_metric", 70.0)
        assert len(performance_monitor.get_active_alerts()) == 0

        # Record first violation
        performance_monitor.record_metric("test_metric", 85.0)
        assert len(performance_monitor.get_active_alerts()) == 0  # Need 2 consecutive

        # Record second violation - should trigger alert
        performance_monitor.record_metric("test_metric", 90.0)
        active_alerts = performance_monitor.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].severity == AlertSeverity.WARNING

    def test_metric_statistics(self, performance_monitor):
        """Test metric statistical calculations."""
        # Record multiple values
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for value in values:
            performance_monitor.record_metric("test_stats", value)

        # Get statistics
        stats = performance_monitor.get_metric_statistics("test_stats")

        # Verify statistics
        assert stats["count"] == 10
        assert stats["min"] == 10
        assert stats["max"] == 100
        assert stats["mean"] == 55.0
        assert stats["median"] == 55.0
        assert stats["p95"] == 95.0

    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, performance_monitor):
        """Test system health monitoring."""
        # Record some system metrics
        performance_monitor.record_metric("cpu_usage_percent", 60.0)
        performance_monitor.record_metric("memory_usage_percent", 70.0)
        performance_monitor.record_metric("active_connections", 25)

        # Get health summary
        health_summary = performance_monitor.get_system_health_summary()

        # Verify health summary structure
        assert "current_resources" in health_summary
        assert "active_workflows" in health_summary
        assert "total_metrics" in health_summary
        assert "active_alerts" in health_summary
        assert "health_score" in health_summary

        # Health score should be reasonable
        assert 0 <= health_summary["health_score"] <= 100

    def test_performance_recommendations(self, performance_monitor):
        """Test performance optimization recommendations."""
        # Simulate high resource usage
        for _ in range(5):
            performance_monitor.record_metric("cpu_usage_percent", 95.0)
            performance_monitor.record_metric("memory_usage_percent", 90.0)

        # Get recommendations
        recommendations = performance_monitor.get_performance_recommendations()

        # Should have CPU and memory recommendations
        assert len(recommendations) >= 1
        cpu_recommendations = [r for r in recommendations if r["metric"] == "cpu_usage"]
        memory_recommendations = [r for r in recommendations if r["metric"] == "memory_usage"]

        # Verify recommendation structure
        if cpu_recommendations:
            rec = cpu_recommendations[0]
            assert rec["type"] == "resource_optimization"
            assert rec["priority"] in ["high", "medium", "low"]
            assert "title" in rec
            assert "description" in rec


class TestWorkflowEngine:
    """Integration tests for WorkflowEngine."""

    @pytest.fixture
    async def workflow_engine(self, mock_db_session, mock_agent_registry):
        """Create workflow engine instance for testing."""
        with patch('agentical.agents.agent_registry.get_agent_registry', return_value=mock_agent_registry):
            engine = WorkflowEngine(
                db_session=mock_db_session,
                max_concurrent_workflows=3,
                default_timeout_minutes=5,
                enable_monitoring=True
            )
            await engine.start()
            yield engine
            await engine.shutdown()

    @pytest.mark.asyncio
    async def test_workflow_execution_lifecycle(self, workflow_engine, sample_workflow, sample_agents):
        """Test complete workflow execution lifecycle."""
        # Mock workflow repository
        workflow_engine.workflow_repo.get = AsyncMock(return_value=sample_workflow)
        workflow_engine.workflow_repo.create_execution = AsyncMock(
            return_value=WorkflowExecution(
                execution_id=f"test_{uuid.uuid4().hex[:8]}",
                workflow_id=sample_workflow.id,
                status=ExecutionStatus.PENDING
            )
        )

        # Mock agent coordination
        async def mock_execute_multi_agent_step(step, context, strategy):
            return {"step_result": f"completed_{step.id}"}

        workflow_engine.multi_agent_coordinator.execute_multi_agent_step = mock_execute_multi_agent_step

        # Execute workflow
        execution = await workflow_engine.execute_workflow(
            workflow_id=sample_workflow.id,
            input_data={"test_input": "value"}
        )

        # Verify execution started
        assert execution is not None
        assert execution.execution_id in workflow_engine._active_executions

        # Wait a moment for execution to process
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_workflow_pause_resume(self, workflow_engine, sample_workflow):
        """Test workflow pause and resume functionality."""
        # Mock workflow repository
        workflow_engine.workflow_repo.get = AsyncMock(return_value=sample_workflow)
        execution = WorkflowExecution(
            execution_id=f"test_{uuid.uuid4().hex[:8]}",
            workflow_id=sample_workflow.id,
            status=ExecutionStatus.RUNNING
        )
        workflow_engine.workflow_repo.create_execution = AsyncMock(return_value=execution)
        workflow_engine.workflow_repo.update_execution = AsyncMock()

        # Add execution to active list
        context = ExecutionContext(
            execution=execution,
            workflow=sample_workflow,
            input_data={},
            config={}
        )
        workflow_engine._execution_contexts[execution.execution_id] = context
        workflow_engine._active_executions[execution.execution_id] = execution

        # Test pause
        success = await workflow_engine.pause_execution(execution.execution_id)
        assert success == True
        assert context.is_paused == True

        # Test resume
        success = await workflow_engine.resume_execution(execution.execution_id)
        assert success == True
        assert context.is_paused == False

    @pytest.mark.asyncio
    async def test_performance_metrics_integration(self, workflow_engine):
        """Test integration with performance monitoring."""
        # Get performance metrics
        metrics = await workflow_engine.get_performance_metrics()

        # Verify metrics structure
        assert "system_health" in metrics
        assert "coordination_metrics" in metrics
        assert "state_metrics" in metrics
        assert "recommendations" in metrics

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, workflow_engine, sample_workflow):
        """Test error handling and recovery mechanisms."""
        # Mock workflow repository to simulate error
        workflow_engine.workflow_repo.get = AsyncMock(side_effect=Exception("Database error"))

        # Attempt to execute workflow
        with pytest.raises(Exception):
            await workflow_engine.execute_workflow(
                workflow_id=sample_workflow.id,
                input_data={}
            )

        # Verify engine remains stable
        assert len(workflow_engine._active_executions) == 0

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, workflow_engine, sample_workflow):
        """Test concurrent workflow execution handling."""
        # Mock workflow repository
        workflow_engine.workflow_repo.get = AsyncMock(return_value=sample_workflow)

        def create_execution(*args, **kwargs):
            return WorkflowExecution(
                execution_id=f"test_{uuid.uuid4().hex[:8]}",
                workflow_id=sample_workflow.id,
                status=ExecutionStatus.PENDING
            )

        workflow_engine.workflow_repo.create_execution = AsyncMock(side_effect=create_execution)

        # Mock multi-agent step execution
        workflow_engine.multi_agent_coordinator.execute_multi_agent_step = AsyncMock(
            return_value={"result": "success"}
        )

        # Start multiple concurrent executions
        executions = []
        for i in range(3):
            execution = await workflow_engine.execute_workflow(
                workflow_id=sample_workflow.id,
                input_data={"execution_number": i}
            )
            executions.append(execution)

        # Verify all executions started
        assert len(executions) == 3
        assert len(workflow_engine._active_executions) == 3

        # Verify each execution has unique ID
        execution_ids = [e.execution_id for e in executions]
        assert len(set(execution_ids)) == 3


class TestWorkflowEngineFactory:
    """Test cases for WorkflowEngineFactory."""

    def test_engine_creation(self):
        """Test workflow engine factory creation."""
        factory = WorkflowEngineFactory()

        # Mock database session
        mock_session = Mock()

        # Create engine
        engine = factory.create_engine(
            db_session=mock_session,
            max_concurrent_workflows=5,
            enable_monitoring=True
        )

        # Verify engine configuration
        assert engine is not None
        assert engine.max_concurrent_workflows == 5
        assert engine.enable_monitoring == True
        assert engine.db_session == mock_session


# Integration test scenarios
class TestWorkflowEngineIntegration:
    """Integration test scenarios for complete workflow engine functionality."""

    @pytest.mark.asyncio
    async def test_complete_multi_agent_workflow_scenario(self, mock_db_session, mock_agent_registry, sample_agents):
        """Test complete multi-agent workflow execution scenario."""
        # Setup mocks
        mock_agent_registry.get_agent = AsyncMock(side_effect=lambda agent_id: next(
            (agent for agent in sample_agents if agent.id == agent_id), None
        ))

        # Create workflow engine
        with patch('agentical.agents.agent_registry.get_agent_registry', return_value=mock_agent_registry):
            engine = WorkflowEngine(
                db_session=mock_db_session,
                max_concurrent_workflows=2,
                enable_monitoring=True
            )
            await engine.start()

            try:
                # Create complex workflow
                complex_workflow = Workflow(
                    id=2,
                    name="Complex Multi-Agent Workflow",
                    description="Integration test workflow",
                    workflow_type=WorkflowType.MULTI_AGENT,
                    status=WorkflowStatus.ACTIVE,
                    configuration={"timeout_seconds": 600}
                )

                # Add complex steps
                step1 = WorkflowStep(
                    id=1,
                    workflow_id=2,
                    name="Data Collection",
                    step_type=StepType.AGENT_TASK,
                    step_order=1,
                    configuration={
                        "multi_agent": True,
                        "coordination_strategy": "scatter_gather",
                        "agent_requirements": {
                            "capabilities": ["data_processing"],
                            "count": 2
                        }
                    }
                )

                step2 = WorkflowStep(
                    id=2,
                    workflow_id=2,
                    name="Analysis",
                    step_type=StepType.AGENT_TASK,
                    step_order=2,
                    depends_on="[1]",
                    configuration={
                        "multi_agent": True,
                        "coordination_strategy": "parallel",
                        "agent_requirements": {
                            "capabilities": ["analysis"],
                            "count": 2
                        }
                    }
                )

                step3 = WorkflowStep(
                    id=3,
                    workflow_id=2,
                    name="Report Generation",
                    step_type=StepType.AGENT_TASK,
                    step_order=3,
                    depends_on="[2]",
                    configuration={
                        "multi_agent": False,
                        "agent_requirements": {
                            "capabilities": ["reporting"],
                            "count": 1
                        }
                    }
                )

                complex_workflow.steps = [step1, step2, step3]

                # Mock workflow repository
                engine.workflow_repo.get = AsyncMock(return_value=complex_workflow)
                engine.workflow_repo.create_execution = AsyncMock(
                    return_value=WorkflowExecution(
                        execution_id=f"integration_{uuid.uuid4().hex[:8]}",
                        workflow_id=complex_workflow.id,
                        status=ExecutionStatus.PENDING
                    )
                )
                engine.workflow_repo.update_execution = AsyncMock()

                # Mock pool discovery for agent selection
                engine.multi_agent_coordinator.pool_discovery.discover_agents = AsyncMock(
                    return_value=sample_agents
                )

                # Mock agent instance execution
                mock_agent_instance = Mock()
                mock_agent_instance.execute_task = AsyncMock(
                    return_value={"status": "success", "data": "processed"}
                )
                mock_agent_instance.health_check = AsyncMock(return_value=True)
                mock_agent_registry.get_agent = AsyncMock(return_value=mock_agent_instance)

                # Execute the complex workflow
                execution = await engine.execute_workflow(
                    workflow_id=complex_workflow.id,
                    input_data={"data_source": "test_data", "format": "json"}
                )

                # Verify execution started
                assert execution is not None
                assert execution.execution_id in engine._active_executions

                # Let execution run briefly
                await asyncio.sleep(0.5)

                # Verify performance monitoring
                performance_metrics = await engine.get_performance_metrics()
                assert "system_health" in performance_metrics
                assert performance_metrics["system_health"]["active_workflows"] >= 0

                # Verify state management
                state_metrics = await engine.get_state_metrics()
                assert "active_executions" in state_metrics

                # Verify coordination metrics
                coordination_metrics = engine.get_coordination_metrics()
                assert "coordinator_stats" in coordination_metrics

            finally:
                await engine.shutdown()

    @pytest.mark.asyncio
    async def test_workflow_recovery_scenario(self, mock_db_session, mock_agent_registry):
        """Test workflow recovery from checkpoint scenario."""
        # Create workflow engine
        with patch('agentical.agents.agent_registry.get_agent_registry', return_value=mock_agent_registry):
            engine = WorkflowEngine(
                db_session=mock_db_session,
                enable_monitoring=True
            )

            # Create test workflow
            workflow = Workflow(
                id=3,
                name="Recovery Test Workflow",
                workflow_type=WorkflowType.SEQUENTIAL,
                status=WorkflowStatus.ACTIVE
            )

            execution = WorkflowExecution(
                execution_id="recovery_test_123",
                workflow_id=3,
                status=ExecutionStatus.RUNNING
            )

            # Create execution context
            context = ExecutionContext(
                execution=execution,
                workflow=workflow,
                input_data={"recovery": "test"},
                config={}
            )

            # Simulate partial execution
            context.set_variable("step1_complete", True)
            context.mark_step_completed(1)
            context.set_phase(ExecutionPhase.EXECUTION)

            # Create checkpoint
            checkpoint = await engine.state_manager.create_checkpoint(
                context=context,
                checkpoint_level=CheckpointLevel.COMPREHENSIVE,
                trigger="test_recovery"
            )

            # Verify checkpoint was created
            assert checkpoint is not None
            assert checkpoint.execution_id == execution.execution_id

            # Test checkpoint integrity
            assert checkpoint.validate_integrity() == True

            await engine.shutdown()

    @pytest.mark.asyncio
    async def test_performance_optimization_scenario(self, mock_db_session, mock_agent_registry):
        """Test performance optimization and alerting scenario."""
        # Create workflow engine with aggressive monitoring
        with patch('agentical.agents.agent_registry.get_agent_registry', return_value=mock_agent_registry):
            engine = WorkflowEngine(
                db_session=mock_db_session,
                enable_monitoring=True
            )
            await engine.start()

            try:
                # Simulate high resource usage
                monitor = engine.performance_monitor

                # Record high CPU usage to trigger alerts
                for i in range(5):
                    monitor.record_metric("cpu_usage_percent", 95.0 + i)
                    monitor.record_metric("memory_usage_percent", 90.0 + i)

                # Get active alerts
                alerts = monitor.get_active_alerts()
                assert len(alerts) >= 0  # May have alerts based on thresholds

                # Get performance recommendations
                recommendations = monitor.get_performance_recommendations()
                assert isinstance(recommendations, list)

                # Test health score calculation
                health_summary = monitor.get_system_health_summary()
                assert "health_score" in health_summary
                assert 0 <= health_summary["health_score"] <= 100

                # Test metric statistics
                cpu_stats = monitor.get_metric_statistics("cpu_usage_percent")
                if cpu_stats:
                    assert "mean" in cpu_stats
                    assert "max" in cpu_stats
                    assert cpu_stats["max"] >= 95.0

            finally:
                await engine.shutdown()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
