"""
Multi-Agent Coordinator for Workflow Engine

This module provides the core multi-agent coordination capabilities for the Agentical
Workflow Engine, enabling sophisticated orchestration of multiple agents working
together on complex workflows.

Features:
- Multi-agent task distribution and coordination
- Agent pool management and load balancing
- Real-time agent health monitoring and failover
- Parallel and sequential agent execution patterns
- Inter-agent communication and data sharing
- Resource management and conflict resolution
- Performance optimization and scaling
- Comprehensive error handling and recovery
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from enum import Enum
from collections import defaultdict, deque
import json
import logging

import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.exceptions import (
    WorkflowExecutionError,
    WorkflowValidationError,
    AgentError,
    ValidationError
)
from ...core.logging import log_operation
from ...db.models.workflow import (
    WorkflowStep,
    WorkflowStepExecution,
    StepType,
    StepStatus
)
from ...db.models.agent import Agent, AgentStatus
from ...agents.agent_registry import AgentRegistry
from ...agents.pool_discovery import AgentPoolDiscovery
from ...agents.capability_matcher import CapabilityMatcher
from .execution_context import ExecutionContext


class CoordinationStrategy(Enum):
    """Agent coordination strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    SCATTER_GATHER = "scatter_gather"
    CONSENSUS = "consensus"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"


class AgentState(Enum):
    """Agent execution state within coordinator."""
    IDLE = "idle"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """Task priority levels for agent assignment."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class AgentTask:
    """Represents a task assigned to an agent."""

    def __init__(
        self,
        task_id: str,
        agent_id: str,
        step_id: int,
        task_type: str,
        input_data: Dict[str, Any],
        config: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_seconds: Optional[int] = None,
        retry_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize agent task."""
        self.task_id = task_id
        self.agent_id = agent_id
        self.step_id = step_id
        self.task_type = task_type
        self.input_data = input_data
        self.config = config
        self.priority = priority
        self.timeout_seconds = timeout_seconds or 300
        self.retry_config = retry_config or {"max_attempts": 3, "backoff_factor": 2}

        # Execution tracking
        self.state = AgentState.ASSIGNED
        self.assigned_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.attempts = 0
        self.execution_context: Dict[str, Any] = {}

    def start_execution(self) -> None:
        """Mark task as started."""
        self.state = AgentState.EXECUTING
        self.started_at = datetime.utcnow()
        self.attempts += 1

    def complete_execution(self, result: Any) -> None:
        """Mark task as completed."""
        self.state = AgentState.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

    def fail_execution(self, error: str) -> None:
        """Mark task as failed."""
        self.state = AgentState.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        max_attempts = self.retry_config.get("max_attempts", 3)
        return self.attempts < max_attempts and self.state == AgentState.FAILED

    def get_execution_time(self) -> Optional[timedelta]:
        """Get task execution time."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "step_id": self.step_id,
            "task_type": self.task_type,
            "state": self.state.value,
            "priority": self.priority.value,
            "attempts": self.attempts,
            "assigned_at": self.assigned_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time": self.get_execution_time().total_seconds() if self.get_execution_time() else None,
            "has_result": self.result is not None,
            "has_error": self.error is not None,
            "can_retry": self.can_retry()
        }


class AgentCoordinationGroup:
    """Manages a group of agents working together."""

    def __init__(
        self,
        group_id: str,
        strategy: CoordinationStrategy,
        agents: List[str],
        config: Dict[str, Any]
    ):
        """Initialize coordination group."""
        self.group_id = group_id
        self.strategy = strategy
        self.agents = agents
        self.config = config

        # Group state
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[AgentTask] = []
        self.failed_tasks: List[AgentTask] = []
        self.shared_context: Dict[str, Any] = {}
        self.message_queue: deque = deque()

        # Coordination state
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.leader_agent: Optional[str] = None

        # Set leader for hierarchical coordination
        if strategy == CoordinationStrategy.HIERARCHICAL and agents:
            self.leader_agent = agents[0]

    def add_task(self, task: AgentTask) -> None:
        """Add task to the group."""
        self.active_tasks[task.task_id] = task

    def complete_task(self, task_id: str, result: Any) -> None:
        """Mark task as completed."""
        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)
            task.complete_execution(result)
            self.completed_tasks.append(task)

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)
            task.fail_execution(error)
            self.failed_tasks.append(task)

    def get_progress(self) -> Dict[str, Any]:
        """Get group progress metrics."""
        total_tasks = len(self.active_tasks) + len(self.completed_tasks) + len(self.failed_tasks)
        completed_count = len(self.completed_tasks)

        return {
            "group_id": self.group_id,
            "strategy": self.strategy.value,
            "total_tasks": total_tasks,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": completed_count,
            "failed_tasks": len(self.failed_tasks),
            "progress_percentage": (completed_count / total_tasks * 100) if total_tasks > 0 else 0,
            "is_active": self.is_active,
            "leader_agent": self.leader_agent
        }


class MultiAgentCoordinator:
    """
    Core multi-agent coordination engine for workflow execution.

    Manages multiple agents working together on complex workflows, providing
    sophisticated coordination strategies, load balancing, and error handling.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        agent_registry: AgentRegistry,
        max_concurrent_agents: int = 20,
        enable_load_balancing: bool = True,
        heartbeat_interval: int = 30
    ):
        """Initialize multi-agent coordinator."""
        self.db_session = db_session
        self.agent_registry = agent_registry
        self.max_concurrent_agents = max_concurrent_agents
        self.enable_load_balancing = enable_load_balancing
        self.heartbeat_interval = heartbeat_interval

        # Core components
        self.pool_discovery = AgentPoolDiscovery(db_session)
        self.capability_matcher = CapabilityMatcher(db_session)

        # Coordination state
        self.active_agents: Dict[str, Agent] = {}
        self.agent_tasks: Dict[str, List[AgentTask]] = defaultdict(list)
        self.coordination_groups: Dict[str, AgentCoordinationGroup] = {}
        self.task_queue: deque = deque()

        # Performance tracking
        self.agent_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.coordination_stats: Dict[str, Any] = {
            "total_tasks_executed": 0,
            "total_agents_used": 0,
            "average_task_duration": 0.0,
            "success_rate": 0.0,
            "load_balancing_events": 0
        }

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_requested = False

        logfire.info(
            "Multi-agent coordinator initialized",
            max_concurrent_agents=max_concurrent_agents,
            enable_load_balancing=enable_load_balancing
        )

    async def start(self) -> None:
        """Start the coordinator and monitoring systems."""
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logfire.info("Multi-agent coordinator started")

    async def shutdown(self) -> None:
        """Shutdown the coordinator gracefully."""
        self._shutdown_requested = True

        # Cancel all active tasks
        for agent_id, tasks in self.agent_tasks.items():
            for task in tasks:
                if task.state == AgentState.EXECUTING:
                    task.fail_execution("Coordinator shutdown")

        # Stop monitoring
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logfire.info("Multi-agent coordinator shutdown complete")

    async def execute_multi_agent_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
        strategy: CoordinationStrategy = CoordinationStrategy.PARALLEL
    ) -> Any:
        """
        Execute a workflow step using multiple agents.

        Args:
            step: Workflow step to execute
            context: Execution context
            strategy: Coordination strategy to use

        Returns:
            Execution result
        """
        with logfire.span(
            "Multi-agent step execution",
            step_id=step.id,
            strategy=strategy.value,
            execution_id=context.execution.execution_id
        ):
            # Parse step configuration
            step_config = step.configuration or {}
            agent_requirements = step_config.get("agent_requirements", {})
            parallelism = step_config.get("parallelism", 1)
            timeout_seconds = step_config.get("timeout_seconds", 300)

            # Find suitable agents
            agents = await self._select_agents_for_step(step, context, agent_requirements)
            if not agents:
                raise WorkflowExecutionError(f"No suitable agents found for step {step.id}")

            # Create coordination group
            group_id = f"step_{step.id}_{uuid.uuid4().hex[:8]}"
            agent_ids = [agent.id for agent in agents]

            coordination_group = AgentCoordinationGroup(
                group_id=group_id,
                strategy=strategy,
                agents=agent_ids,
                config=step_config
            )
            self.coordination_groups[group_id] = coordination_group

            try:
                # Execute based on strategy
                if strategy == CoordinationStrategy.PARALLEL:
                    result = await self._execute_parallel_coordination(
                        coordination_group, step, context, agents, timeout_seconds
                    )
                elif strategy == CoordinationStrategy.SEQUENTIAL:
                    result = await self._execute_sequential_coordination(
                        coordination_group, step, context, agents, timeout_seconds
                    )
                elif strategy == CoordinationStrategy.PIPELINE:
                    result = await self._execute_pipeline_coordination(
                        coordination_group, step, context, agents, timeout_seconds
                    )
                elif strategy == CoordinationStrategy.SCATTER_GATHER:
                    result = await self._execute_scatter_gather_coordination(
                        coordination_group, step, context, agents, timeout_seconds
                    )
                elif strategy == CoordinationStrategy.CONSENSUS:
                    result = await self._execute_consensus_coordination(
                        coordination_group, step, context, agents, timeout_seconds
                    )
                elif strategy == CoordinationStrategy.HIERARCHICAL:
                    result = await self._execute_hierarchical_coordination(
                        coordination_group, step, context, agents, timeout_seconds
                    )
                else:
                    raise WorkflowValidationError(f"Unsupported coordination strategy: {strategy.value}")

                # Emit success event
                await self._emit_event("step_completed", {
                    "step_id": step.id,
                    "group_id": group_id,
                    "strategy": strategy.value,
                    "agents_used": len(agents),
                    "result_size": len(str(result)) if result else 0
                })

                return result

            except Exception as e:
                # Emit failure event
                await self._emit_event("step_failed", {
                    "step_id": step.id,
                    "group_id": group_id,
                    "strategy": strategy.value,
                    "error": str(e)
                })
                raise

            finally:
                # Cleanup coordination group
                if group_id in self.coordination_groups:
                    del self.coordination_groups[group_id]

    async def _select_agents_for_step(
        self,
        step: WorkflowStep,
        context: ExecutionContext,
        requirements: Dict[str, Any]
    ) -> List[Agent]:
        """Select appropriate agents for a workflow step."""
        with logfire.span("Agent selection", step_id=step.id):
            # Get required capabilities
            required_capabilities = requirements.get("capabilities", [])
            required_count = requirements.get("count", 1)
            max_count = requirements.get("max_count", 5)

            # Discover available agents
            available_agents = await self.pool_discovery.discover_agents(
                capabilities=required_capabilities,
                min_performance_score=requirements.get("min_performance_score", 0.7),
                exclude_busy=True
            )

            if not available_agents:
                logfire.warning(
                    "No agents found for step",
                    step_id=step.id,
                    required_capabilities=required_capabilities
                )
                return []

            # Apply load balancing if enabled
            if self.enable_load_balancing:
                available_agents = await self._apply_load_balancing(available_agents)

            # Select optimal agents
            selected_count = min(max(required_count, 1), max_count, len(available_agents))
            selected_agents = available_agents[:selected_count]

            logfire.info(
                "Agents selected for step",
                step_id=step.id,
                selected_count=len(selected_agents),
                available_count=len(available_agents),
                agent_ids=[agent.id for agent in selected_agents]
            )

            return selected_agents

    async def _execute_parallel_coordination(
        self,
        group: AgentCoordinationGroup,
        step: WorkflowStep,
        context: ExecutionContext,
        agents: List[Agent],
        timeout_seconds: int
    ) -> Any:
        """Execute agents in parallel."""
        with logfire.span("Parallel coordination", group_id=group.group_id):
            # Create tasks for each agent
            tasks = []
            for i, agent in enumerate(agents):
                task_id = f"{group.group_id}_task_{i}"

                agent_task = AgentTask(
                    task_id=task_id,
                    agent_id=agent.id,
                    step_id=step.id,
                    task_type=step.step_type.value,
                    input_data=context.variables,
                    config=step.configuration or {},
                    timeout_seconds=timeout_seconds
                )

                group.add_task(agent_task)
                task_coroutine = self._execute_agent_task(agent, agent_task, context)
                tasks.append(task_coroutine)

            # Execute all tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            successful_results = []
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append(str(result))
                    group.fail_task(f"{group.group_id}_task_{i}", str(result))
                else:
                    successful_results.append(result)
                    group.complete_task(f"{group.group_id}_task_{i}", result)

            # Return combined results
            if errors and not successful_results:
                raise WorkflowExecutionError(f"All parallel agents failed: {'; '.join(errors)}")

            return {
                "results": successful_results,
                "errors": errors,
                "success_count": len(successful_results),
                "total_count": len(agents)
            }

    async def _execute_sequential_coordination(
        self,
        group: AgentCoordinationGroup,
        step: WorkflowStep,
        context: ExecutionContext,
        agents: List[Agent],
        timeout_seconds: int
    ) -> Any:
        """Execute agents sequentially."""
        with logfire.span("Sequential coordination", group_id=group.group_id):
            results = []

            for i, agent in enumerate(agents):
                task_id = f"{group.group_id}_task_{i}"

                agent_task = AgentTask(
                    task_id=task_id,
                    agent_id=agent.id,
                    step_id=step.id,
                    task_type=step.step_type.value,
                    input_data=context.variables,
                    config=step.configuration or {},
                    timeout_seconds=timeout_seconds
                )

                group.add_task(agent_task)

                try:
                    result = await self._execute_agent_task(agent, agent_task, context)
                    results.append(result)
                    group.complete_task(task_id, result)

                    # Update context with result for next agent
                    context.set_variable(f"agent_{i}_result", result)

                except Exception as e:
                    group.fail_task(task_id, str(e))
                    raise WorkflowExecutionError(f"Sequential agent {i} failed: {str(e)}")

            return {
                "results": results,
                "final_result": results[-1] if results else None,
                "agent_count": len(agents)
            }

    async def _execute_pipeline_coordination(
        self,
        group: AgentCoordinationGroup,
        step: WorkflowStep,
        context: ExecutionContext,
        agents: List[Agent],
        timeout_seconds: int
    ) -> Any:
        """Execute agents in pipeline mode."""
        with logfire.span("Pipeline coordination", group_id=group.group_id):
            current_data = context.variables

            for i, agent in enumerate(agents):
                task_id = f"{group.group_id}_task_{i}"

                agent_task = AgentTask(
                    task_id=task_id,
                    agent_id=agent.id,
                    step_id=step.id,
                    task_type=step.step_type.value,
                    input_data=current_data,
                    config=step.configuration or {},
                    timeout_seconds=timeout_seconds
                )

                group.add_task(agent_task)

                try:
                    result = await self._execute_agent_task(agent, agent_task, context)
                    group.complete_task(task_id, result)

                    # Pass result as input to next agent
                    if isinstance(result, dict):
                        current_data.update(result)
                    else:
                        current_data[f"stage_{i}_output"] = result

                except Exception as e:
                    group.fail_task(task_id, str(e))
                    raise WorkflowExecutionError(f"Pipeline stage {i} failed: {str(e)}")

            return current_data

    async def _execute_scatter_gather_coordination(
        self,
        group: AgentCoordinationGroup,
        step: WorkflowStep,
        context: ExecutionContext,
        agents: List[Agent],
        timeout_seconds: int
    ) -> Any:
        """Execute scatter-gather pattern."""
        with logfire.span("Scatter-gather coordination", group_id=group.group_id):
            # Scatter: Divide input data among agents
            input_data = context.variables
            data_chunks = self._scatter_data(input_data, len(agents))

            # Execute agents in parallel with different data chunks
            tasks = []
            for i, (agent, chunk) in enumerate(zip(agents, data_chunks)):
                task_id = f"{group.group_id}_task_{i}"

                agent_task = AgentTask(
                    task_id=task_id,
                    agent_id=agent.id,
                    step_id=step.id,
                    task_type=step.step_type.value,
                    input_data=chunk,
                    config=step.configuration or {},
                    timeout_seconds=timeout_seconds
                )

                group.add_task(agent_task)
                task_coroutine = self._execute_agent_task(agent, agent_task, context)
                tasks.append(task_coroutine)

            # Gather: Collect and combine results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            gathered_result = self._gather_results(results)

            # Mark tasks as completed
            for i, result in enumerate(results):
                task_id = f"{group.group_id}_task_{i}"
                if isinstance(result, Exception):
                    group.fail_task(task_id, str(result))
                else:
                    group.complete_task(task_id, result)

            return gathered_result

    async def _execute_consensus_coordination(
        self,
        group: AgentCoordinationGroup,
        step: WorkflowStep,
        context: ExecutionContext,
        agents: List[Agent],
        timeout_seconds: int
    ) -> Any:
        """Execute consensus-based coordination."""
        with logfire.span("Consensus coordination", group_id=group.group_id):
            # Execute all agents in parallel
            tasks = []
            for i, agent in enumerate(agents):
                task_id = f"{group.group_id}_task_{i}"

                agent_task = AgentTask(
                    task_id=task_id,
                    agent_id=agent.id,
                    step_id=step.id,
                    task_type=step.step_type.value,
                    input_data=context.variables,
                    config=step.configuration or {},
                    timeout_seconds=timeout_seconds
                )

                group.add_task(agent_task)
                task_coroutine = self._execute_agent_task(agent, agent_task, context)
                tasks.append(task_coroutine)

            # Get all results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter successful results
            successful_results = []
            for i, result in enumerate(results):
                task_id = f"{group.group_id}_task_{i}"
                if isinstance(result, Exception):
                    group.fail_task(task_id, str(result))
                else:
                    successful_results.append(result)
                    group.complete_task(task_id, result)

            # Apply consensus algorithm
            consensus_result = self._apply_consensus(successful_results)

            return {
                "consensus_result": consensus_result,
                "individual_results": successful_results,
                "consensus_confidence": len(successful_results) / len(agents)
            }

    async def _execute_hierarchical_coordination(
        self,
        group: AgentCoordinationGroup,
        step: WorkflowStep,
        context: ExecutionContext,
        agents: List[Agent],
        timeout_seconds: int
    ) -> Any:
        """Execute hierarchical coordination with leader."""
        with logfire.span("Hierarchical coordination", group_id=group.group_id):
            leader_agent = agents[0]
            worker_agents = agents[1:]

            # Execute workers first
            worker_results = []
            for i, agent in enumerate(worker_agents):
                task_id = f"{group.group_id}_worker_{i}"

                agent_task = AgentTask(
                    task_id=task_id,
                    agent_id=agent.id,
                    step_id=step.id,
                    task_type=step.step_type.value,
                    input_data=context.variables,
                    config=step.configuration or {},
                    timeout_seconds=timeout_seconds
                )

                group.add_task(agent_task)

                try:
                    result = await self._execute_agent_task(agent, agent_task, context)
                    worker_results.append(result)
                    group.complete_task(task_id, result)
                except Exception as e:
                    group.fail_task(task_id, str(e))
                    logfire.warning(f"Worker agent {i} failed: {str(e)}")

            # Leader consolidates worker results
            leader_task_id = f"{group.group_id}_leader"
            leader_input = context.variables.copy()
            leader_input["worker_results"] = worker_results

            leader_task = AgentTask(
                task_id=leader_task_id,
                agent_id=leader_agent.id,
                step_id=step.id,
                task_type=step.step_type.value,
                input_data=leader_input,
                config=step.configuration or {},
                timeout_seconds=timeout_seconds
            )

            group.add_task(leader_task)

            try:
                final_result = await self._execute_agent_task(leader_agent, leader_task, context)
                group.complete_task(leader_task_id, final_result)

                return {
                    "final_result": final_result,
                    "worker_results": worker_results,
                    "leader_id": leader_agent.id,
                    "worker_count": len(worker_agents)
                }
            except Exception as e:
                group.fail_task(leader_task_id, str(e))
                raise WorkflowExecutionError(f"Leader agent failed: {str(e)}")

    async def _execute_agent_task(
        self,
        agent: Agent,
        task: AgentTask,
        context: ExecutionContext
    ) -> Any:
        """Execute a single agent task."""
        with logfire.span(
            "Agent task execution",
            agent_id=agent.id,
            task_id=task.task_id,
            step_id=task.step_id
        ):
            task.start_execution()

            try:
                # Get agent instance from registry
                agent_instance = await self.agent_registry.get_agent(agent.id)
                if not agent_instance:
                    raise AgentError(f"Agent {agent.id} not found in registry")

                # Execute the task
                result = await agent_instance.execute_task(
                    task_type=task.task_type,
                    input_data=task.input_data,
                    config=task.config,
                    timeout_seconds=task.timeout_seconds
                )

                # Update metrics
                execution_time = task.get_execution_time()
                if execution_time:
                    self._update_agent_metrics(agent.id, execution_time.total_seconds(), True)

                task.complete_execution(result)

                logfire.info(
                    "Agent task completed",
                    agent_id=agent.id,
                    task_id=task.task_id,
                    execution_time=execution_time.total_seconds() if execution_time else None
                )

                return result

            except Exception as e:
                # Update metrics
                execution_time = task.get_execution_time()
                if execution_time:
                    self._update_agent_metrics(agent.id, execution_time.total_seconds(), False)

                task.fail_execution(str(e))

                logfire.error(
                    "Agent task failed",
                    agent_id=agent.id,
                    task_id=task.task_id,
                    error=str(e)
                )

                raise

    def _scatter_data(self, data: Dict[str, Any], chunk_count: int) -> List[Dict[str, Any]]:
        """Scatter input data into chunks for parallel processing."""
        if chunk_count <= 1:
            return [data]

        chunks = []
        items = list(data.items())
        chunk_size = max(1, len(items) // chunk_count)

        for i in range(0, len(items), chunk_size):
            chunk = dict(items[i:i + chunk_size])
            chunks.append(chunk)

        # Ensure we have exactly chunk_count chunks
        while len(chunks) < chunk_count:
            chunks.append({})

        return chunks[:chunk_count]

    def _gather_results(self, results: List[Any]) -> Dict[str, Any]:
        """Gather and combine results from multiple agents."""
        gathered = {
            "combined_results": [],
            "result_count": 0,
            "successful_results": []
        }

        for result in results:
            if not isinstance(result, Exception):
                gathered["combined_results"].append(result)
                gathered["successful_results"].append(result)
                gathered["result_count"] += 1

        # Try to merge dictionary results
        if gathered["successful_results"]:
            merged_dict = {}
            for result in gathered["successful_results"]:
                if isinstance(result, dict):
                    merged_dict.update(result)

            if merged_dict:
                gathered["merged_data"] = merged_dict

        return gathered

    def _apply_consensus(self, results: List[Any]) -> Any:
        """Apply consensus algorithm to multiple results."""
        if not results:
            return None

        if len(results) == 1:
            return results[0]

        # For now, use simple majority consensus
        # In practice, this would implement more sophisticated algorithms

        # Count occurrences of each result
        result_counts = defaultdict(int)
        for result in results:
            result_str = json.dumps(result, sort_keys=True, default=str)
            result_counts[result_str] += 1

        # Return most common result
        if result_counts:
            most_common = max(result_counts.items(), key=lambda x: x[1])
            return json.loads(most_common[0])

        return results[0]

    async def _apply_load_balancing(self, agents: List[Agent]) -> List[Agent]:
        """Apply load balancing to agent selection."""
        if not self.enable_load_balancing:
            return agents

        # Sort agents by current load (fewer active tasks = higher priority)
        agent_loads = []
        for agent in agents:
            active_tasks = len(self.agent_tasks.get(agent.id, []))
            performance_score = self.agent_metrics.get(agent.id, {}).get("success_rate", 1.0)

            # Calculate load score (lower is better)
            load_score = active_tasks / (performance_score + 0.1)
            agent_loads.append((agent, load_score))

        # Sort by load score
        agent_loads.sort(key=lambda x: x[1])

        self.coordination_stats["load_balancing_events"] += 1

        return [agent for agent, _ in agent_loads]

    def _update_agent_metrics(self, agent_id: str, execution_time: float, success: bool) -> None:
        """Update performance metrics for an agent."""
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "success_rate": 0.0,
                "last_updated": datetime.utcnow()
            }

        metrics = self.agent_metrics[agent_id]
        metrics["total_tasks"] += 1
        metrics["total_execution_time"] += execution_time

        if success:
            metrics["successful_tasks"] += 1

        metrics["average_execution_time"] = metrics["total_execution_time"] / metrics["total_tasks"]
        metrics["success_rate"] = metrics["successful_tasks"] / metrics["total_tasks"]
        metrics["last_updated"] = datetime.utcnow()

        # Update global stats
        self.coordination_stats["total_tasks_executed"] += 1
        if success:
            total_successful = sum(
                m["successful_tasks"] for m in self.agent_metrics.values()
            )
            self.coordination_stats["success_rate"] = (
                total_successful / self.coordination_stats["total_tasks_executed"]
            )

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for agent health and performance."""
        while not self._shutdown_requested:
            try:
                await self._check_agent_health()
                await self._cleanup_completed_tasks()
                await self._emit_metrics()

                await asyncio.sleep(self.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logfire.error("Monitoring loop error", error=str(e))
                await asyncio.sleep(5)

    async def _check_agent_health(self) -> None:
        """Check health of active agents."""
        for agent_id in list(self.active_agents.keys()):
            try:
                agent_instance = await self.agent_registry.get_agent(agent_id)
                if not agent_instance or not await agent_instance.health_check():
                    # Remove unhealthy agent
                    if agent_id in self.active_agents:
                        del self.active_agents[agent_id]

                    # Fail any active tasks for this agent
                    for task in self.agent_tasks.get(agent_id, []):
                        if task.state == AgentState.EXECUTING:
                            task.fail_execution("Agent health check failed")

                    logfire.warning("Agent failed health check", agent_id=agent_id)

            except Exception as e:
                logfire.error("Health check error", agent_id=agent_id, error=str(e))

    async def _cleanup_completed_tasks(self) -> None:
        """Clean up completed tasks from memory."""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)

        for agent_id, tasks in self.agent_tasks.items():
            self.agent_tasks[agent_id] = [
                task for task in tasks
                if task.state in [AgentState.ASSIGNED, AgentState.EXECUTING] or
                (task.completed_at and task.completed_at > cutoff_time)
            ]

    async def _emit_metrics(self) -> None:
        """Emit coordination metrics."""
        total_agents = len(self.active_agents)
        total_groups = len(self.coordination_groups)

        active_tasks = sum(
            len([t for t in tasks if t.state == AgentState.EXECUTING])
            for tasks in self.agent_tasks.values()
        )

        logfire.info(
            "Coordination metrics",
            total_agents=total_agents,
            total_groups=total_groups,
            active_tasks=active_tasks,
            coordination_stats=self.coordination_stats
        )

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit coordination events to registered handlers."""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                logfire.error(
                    "Event handler error",
                    event_type=event_type,
                    handler=handler.__name__,
                    error=str(e)
                )

    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add event handler for coordination events."""
        self.event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: Callable) -> None:
        """Remove event handler."""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass

    def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get comprehensive coordination metrics."""
        return {
            "coordinator_stats": self.coordination_stats.copy(),
            "active_agents_count": len(self.active_agents),
            "active_groups_count": len(self.coordination_groups),
            "total_agent_metrics": len(self.agent_metrics),
            "agent_performance": {
                agent_id: metrics.copy()
                for agent_id, metrics in self.agent_metrics.items()
            }
        }

    def get_active_coordination_groups(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active coordination groups."""
        return {
            group_id: group.get_progress()
            for group_id, group in self.coordination_groups.items()
        }

    async def cancel_coordination_group(self, group_id: str) -> bool:
        """Cancel an active coordination group."""
        if group_id not in self.coordination_groups:
            return False

        group = self.coordination_groups[group_id]

        # Cancel all active tasks in the group
        for task in group.active_tasks.values():
            if task.state == AgentState.EXECUTING:
                task.fail_execution("Group cancelled")

        # Mark group as inactive
        group.is_active = False

        logfire.info("Coordination group cancelled", group_id=group_id)
        return True

    def __repr__(self) -> str:
        """String representation of coordinator."""
        return (
            f"MultiAgentCoordinator(agents={len(self.active_agents)}, "
            f"groups={len(self.coordination_groups)}, "
            f"total_tasks={self.coordination_stats['total_tasks_executed']})"
        )
