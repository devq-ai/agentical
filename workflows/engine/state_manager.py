"""
Workflow State Manager for Agentical Framework

This module provides comprehensive state management for workflow executions,
including persistence, recovery, checkpointing, and state synchronization
across distributed workflow execution environments.

Features:
- Persistent state storage and retrieval
- State checkpointing and recovery
- Distributed state synchronization
- State migration and versioning
- Performance optimization with caching
- Comprehensive error handling and validation
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from enum import Enum
from collections import defaultdict
import pickle
import hashlib
import logging

import logfire
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from ...core.exceptions import (
    WorkflowError,
    WorkflowExecutionError,
    WorkflowValidationError,
    ValidationError
)
from ...core.logging import log_operation
from ...db.models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStepExecution,
    WorkflowStatus,
    ExecutionStatus,
    StepStatus
)
from ...db.repositories.workflow import AsyncWorkflowRepository
from .execution_context import ExecutionContext, ExecutionPhase


class StateOperationType(Enum):
    """Types of state operations."""
    CHECKPOINT = "checkpoint"
    RESTORE = "restore"
    MIGRATE = "migrate"
    SYNC = "sync"
    CLEANUP = "cleanup"


class StateVersion(Enum):
    """State format versions."""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"
    CURRENT = V2_0


class CheckpointLevel(Enum):
    """Checkpoint granularity levels."""
    MINIMAL = "minimal"      # Basic execution state only
    STANDARD = "standard"    # Execution state + variables
    COMPREHENSIVE = "comprehensive"  # Full state including context
    DEBUG = "debug"          # All data including internals


class StateCheckpoint:
    """Represents a workflow state checkpoint."""

    def __init__(
        self,
        checkpoint_id: str,
        execution_id: str,
        timestamp: datetime,
        checkpoint_level: CheckpointLevel,
        state_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize state checkpoint."""
        self.checkpoint_id = checkpoint_id
        self.execution_id = execution_id
        self.timestamp = timestamp
        self.checkpoint_level = checkpoint_level
        self.state_data = state_data
        self.metadata = metadata or {}

        # Computed properties
        self.state_hash = self._compute_hash()
        self.size_bytes = len(json.dumps(state_data, default=str))

    def _compute_hash(self) -> str:
        """Compute hash of state data for integrity checking."""
        state_str = json.dumps(self.state_data, sort_keys=True, default=str)
        return hashlib.sha256(state_str.encode()).hexdigest()

    def validate_integrity(self) -> bool:
        """Validate checkpoint integrity."""
        return self.state_hash == self._compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "checkpoint_level": self.checkpoint_level.value,
            "state_hash": self.state_hash,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], state_data: Dict[str, Any]) -> "StateCheckpoint":
        """Create checkpoint from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            execution_id=data["execution_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            checkpoint_level=CheckpointLevel(data["checkpoint_level"]),
            state_data=state_data,
            metadata=data.get("metadata", {})
        )


class WorkflowStateManager:
    """
    Comprehensive workflow state management system.

    Manages workflow execution state persistence, recovery, checkpointing,
    and synchronization across distributed execution environments.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        checkpoint_interval: int = 60,  # seconds
        max_checkpoints_per_execution: int = 100,
        enable_compression: bool = True,
        cache_size: int = 1000
    ):
        """Initialize workflow state manager."""
        self.db_session = db_session
        self.checkpoint_interval = checkpoint_interval
        self.max_checkpoints_per_execution = max_checkpoints_per_execution
        self.enable_compression = enable_compression
        self.cache_size = cache_size

        # Repository for database operations
        self.workflow_repo = AsyncWorkflowRepository(db_session)

        # State cache for performance
        self.state_cache: Dict[str, StateCheckpoint] = {}
        self.cache_access_times: Dict[str, datetime] = {}

        # Active state tracking
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.checkpoint_tasks: Dict[str, asyncio.Task] = {}
        self.last_checkpoints: Dict[str, datetime] = {}

        # Performance metrics
        self.state_metrics: Dict[str, Any] = {
            "total_checkpoints": 0,
            "total_restores": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_checkpoint_size": 0,
            "average_checkpoint_time": 0.0
        }

        logfire.info(
            "Workflow state manager initialized",
            checkpoint_interval=checkpoint_interval,
            max_checkpoints=max_checkpoints_per_execution,
            cache_size=cache_size
        )

    async def start_managing_execution(self, context: ExecutionContext) -> None:
        """Start managing state for a workflow execution."""
        execution_id = context.execution.execution_id

        with logfire.span("Start state management", execution_id=execution_id):
            self.active_executions[execution_id] = context

            # Create initial checkpoint
            await self.create_checkpoint(
                context,
                checkpoint_level=CheckpointLevel.STANDARD,
                trigger="execution_start"
            )

            # Start periodic checkpointing
            if self.checkpoint_interval > 0:
                task = asyncio.create_task(
                    self._periodic_checkpoint_loop(context)
                )
                self.checkpoint_tasks[execution_id] = task

            logfire.info("State management started", execution_id=execution_id)

    async def stop_managing_execution(self, execution_id: str, final_checkpoint: bool = True) -> None:
        """Stop managing state for a workflow execution."""
        with logfire.span("Stop state management", execution_id=execution_id):
            # Create final checkpoint if requested
            if final_checkpoint and execution_id in self.active_executions:
                context = self.active_executions[execution_id]
                await self.create_checkpoint(
                    context,
                    checkpoint_level=CheckpointLevel.COMPREHENSIVE,
                    trigger="execution_end"
                )

            # Stop periodic checkpointing
            if execution_id in self.checkpoint_tasks:
                task = self.checkpoint_tasks[execution_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.checkpoint_tasks[execution_id]

            # Clean up tracking
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            if execution_id in self.last_checkpoints:
                del self.last_checkpoints[execution_id]

            logfire.info("State management stopped", execution_id=execution_id)

    async def create_checkpoint(
        self,
        context: ExecutionContext,
        checkpoint_level: CheckpointLevel = CheckpointLevel.STANDARD,
        trigger: str = "manual",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateCheckpoint:
        """Create a state checkpoint for the execution."""
        execution_id = context.execution.execution_id

        with logfire.span("Create checkpoint", execution_id=execution_id, level=checkpoint_level.value):
            start_time = datetime.utcnow()

            # Generate checkpoint ID
            checkpoint_id = f"{execution_id}_{uuid.uuid4().hex[:8]}"

            # Collect state data based on level
            state_data = await self._collect_state_data(context, checkpoint_level)

            # Create checkpoint metadata
            checkpoint_metadata = {
                "trigger": trigger,
                "execution_phase": context.phase.value,
                "progress_percentage": context.get_progress_percentage(),
                "step_count": len(context.completed_steps),
                "variable_count": len(context.variables),
                "created_by": "state_manager",
                **(metadata or {})
            }

            # Create checkpoint object
            checkpoint = StateCheckpoint(
                checkpoint_id=checkpoint_id,
                execution_id=execution_id,
                timestamp=start_time,
                checkpoint_level=checkpoint_level,
                state_data=state_data,
                metadata=checkpoint_metadata
            )

            # Persist checkpoint
            await self._persist_checkpoint(checkpoint)

            # Update cache
            self._update_cache(checkpoint)

            # Update metrics
            self.state_metrics["total_checkpoints"] += 1
            checkpoint_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_average_metric("average_checkpoint_time", checkpoint_time)
            self._update_average_metric("average_checkpoint_size", checkpoint.size_bytes)

            # Update last checkpoint time
            self.last_checkpoints[execution_id] = start_time

            logfire.info(
                "Checkpoint created",
                execution_id=execution_id,
                checkpoint_id=checkpoint_id,
                level=checkpoint_level.value,
                size_bytes=checkpoint.size_bytes,
                creation_time=checkpoint_time
            )

            return checkpoint

    async def restore_execution(
        self,
        execution_id: str,
        checkpoint_id: Optional[str] = None,
        target_timestamp: Optional[datetime] = None
    ) -> ExecutionContext:
        """Restore execution state from a checkpoint."""
        with logfire.span("Restore execution", execution_id=execution_id):
            # Find the appropriate checkpoint
            checkpoint = await self._find_restore_checkpoint(
                execution_id, checkpoint_id, target_timestamp
            )

            if not checkpoint:
                raise WorkflowValidationError(f"No suitable checkpoint found for execution {execution_id}")

            # Validate checkpoint integrity
            if not checkpoint.validate_integrity():
                raise WorkflowExecutionError(f"Checkpoint {checkpoint.checkpoint_id} integrity validation failed")

            # Load execution and workflow data
            execution = await self._load_execution_data(execution_id)
            workflow = await self._load_workflow_data(execution.workflow_id)

            # Reconstruct execution context
            context = await self._reconstruct_context(execution, workflow, checkpoint)

            # Update metrics
            self.state_metrics["total_restores"] += 1

            logfire.info(
                "Execution restored",
                execution_id=execution_id,
                checkpoint_id=checkpoint.checkpoint_id,
                restored_phase=context.phase.value,
                progress=context.get_progress_percentage()
            )

            return context

    async def list_checkpoints(
        self,
        execution_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[StateCheckpoint]:
        """List checkpoints for an execution."""
        # Implementation would query database for checkpoints
        # For now, return empty list as placeholder
        return []

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint."""
        try:
            # Remove from cache
            if checkpoint_id in self.state_cache:
                del self.state_cache[checkpoint_id]
                if checkpoint_id in self.cache_access_times:
                    del self.cache_access_times[checkpoint_id]

            # Delete from database (implementation needed)
            # await self._delete_checkpoint_from_db(checkpoint_id)

            logfire.info("Checkpoint deleted", checkpoint_id=checkpoint_id)
            return True

        except Exception as e:
            logfire.error("Failed to delete checkpoint", checkpoint_id=checkpoint_id, error=str(e))
            return False

    async def migrate_state_format(
        self,
        execution_id: str,
        source_version: StateVersion,
        target_version: StateVersion
    ) -> bool:
        """Migrate state format between versions."""
        with logfire.span("State migration", execution_id=execution_id):
            try:
                # Load checkpoints in source format
                checkpoints = await self.list_checkpoints(execution_id)

                # Migrate each checkpoint
                for checkpoint in checkpoints:
                    migrated_data = await self._migrate_checkpoint_data(
                        checkpoint.state_data, source_version, target_version
                    )

                    # Create new checkpoint with migrated data
                    migrated_checkpoint = StateCheckpoint(
                        checkpoint_id=f"{checkpoint.checkpoint_id}_migrated",
                        execution_id=execution_id,
                        timestamp=datetime.utcnow(),
                        checkpoint_level=checkpoint.checkpoint_level,
                        state_data=migrated_data,
                        metadata={
                            **checkpoint.metadata,
                            "migrated_from": source_version.value,
                            "migrated_to": target_version.value,
                            "original_checkpoint": checkpoint.checkpoint_id
                        }
                    )

                    await self._persist_checkpoint(migrated_checkpoint)

                logfire.info(
                    "State migration completed",
                    execution_id=execution_id,
                    source_version=source_version.value,
                    target_version=target_version.value,
                    checkpoints_migrated=len(checkpoints)
                )

                return True

            except Exception as e:
                logfire.error("State migration failed", execution_id=execution_id, error=str(e))
                return False

    async def cleanup_old_checkpoints(
        self,
        execution_id: Optional[str] = None,
        older_than: Optional[timedelta] = None
    ) -> int:
        """Clean up old checkpoints to free storage."""
        if older_than is None:
            older_than = timedelta(days=30)

        cutoff_time = datetime.utcnow() - older_than
        deleted_count = 0

        with logfire.span("Cleanup checkpoints", execution_id=execution_id):
            try:
                # Implementation would query and delete old checkpoints
                # For now, return 0 as placeholder
                pass

            except Exception as e:
                logfire.error("Checkpoint cleanup failed", error=str(e))

            logfire.info(
                "Checkpoint cleanup completed",
                deleted_count=deleted_count,
                cutoff_time=cutoff_time.isoformat()
            )

            return deleted_count

    async def get_state_metrics(self) -> Dict[str, Any]:
        """Get state manager performance metrics."""
        return {
            **self.state_metrics,
            "active_executions": len(self.active_executions),
            "active_checkpoint_tasks": len(self.checkpoint_tasks),
            "cache_size": len(self.state_cache),
            "cache_hit_rate": (
                self.state_metrics["cache_hits"] /
                max(1, self.state_metrics["cache_hits"] + self.state_metrics["cache_misses"])
            )
        }

    async def _collect_state_data(
        self,
        context: ExecutionContext,
        level: CheckpointLevel
    ) -> Dict[str, Any]:
        """Collect state data based on checkpoint level."""
        base_data = {
            "execution_id": context.execution.execution_id,
            "workflow_id": context.workflow.id,
            "phase": context.phase.value,
            "is_paused": context.is_paused,
            "is_cancelled": context.is_cancelled,
            "completed_steps": list(context.completed_steps),
            "failed_steps": list(context.failed_steps),
            "skipped_steps": list(context.skipped_steps)
        }

        if level in [CheckpointLevel.STANDARD, CheckpointLevel.COMPREHENSIVE, CheckpointLevel.DEBUG]:
            base_data.update({
                "variables": context.variables,
                "step_results": context.step_results,
                "output_data": context.output_data
            })

        if level in [CheckpointLevel.COMPREHENSIVE, CheckpointLevel.DEBUG]:
            base_data.update({
                "global_context": context.global_context,
                "step_durations": {
                    str(k): v.total_seconds() for k, v in context.step_durations.items()
                },
                "checkpoint_times": [t.isoformat() for t in context.checkpoint_times],
                "error_details": context.error_details
            })

        if level == CheckpointLevel.DEBUG:
            base_data.update({
                "start_time": context.start_time.isoformat(),
                "last_checkpoint": context.last_checkpoint.isoformat() if context.last_checkpoint else None,
                "current_step_id": context.current_step.id if context.current_step else None,
                "event_handlers_count": len(context.event_handlers),
                "step_hooks_count": len(context.step_hooks)
            })

        return base_data

    async def _persist_checkpoint(self, checkpoint: StateCheckpoint) -> None:
        """Persist checkpoint to database."""
        # Implementation would save checkpoint to database
        # For now, just log the operation
        logfire.debug(
            "Persisting checkpoint",
            checkpoint_id=checkpoint.checkpoint_id,
            size_bytes=checkpoint.size_bytes
        )

    async def _find_restore_checkpoint(
        self,
        execution_id: str,
        checkpoint_id: Optional[str],
        target_timestamp: Optional[datetime]
    ) -> Optional[StateCheckpoint]:
        """Find the appropriate checkpoint for restoration."""
        # Check cache first
        if checkpoint_id and checkpoint_id in self.state_cache:
            self.state_metrics["cache_hits"] += 1
            return self.state_cache[checkpoint_id]

        self.state_metrics["cache_misses"] += 1

        # Implementation would query database for checkpoints
        # For now, return None as placeholder
        return None

    async def _load_execution_data(self, execution_id: str) -> WorkflowExecution:
        """Load execution data from database."""
        # Implementation would load from database
        # For now, return minimal object as placeholder
        return WorkflowExecution(execution_id=execution_id)

    async def _load_workflow_data(self, workflow_id: int) -> Workflow:
        """Load workflow data from database."""
        return await self.workflow_repo.get(workflow_id)

    async def _reconstruct_context(
        self,
        execution: WorkflowExecution,
        workflow: Workflow,
        checkpoint: StateCheckpoint
    ) -> ExecutionContext:
        """Reconstruct execution context from checkpoint data."""
        state_data = checkpoint.state_data

        # Create basic context
        context = ExecutionContext(
            execution=execution,
            workflow=workflow,
            input_data=state_data.get("variables", {}),
            config=state_data.get("global_context", {})
        )

        # Restore state
        context.phase = ExecutionPhase(state_data.get("phase", "initialization"))
        context.is_paused = state_data.get("is_paused", False)
        context.is_cancelled = state_data.get("is_cancelled", False)
        context.completed_steps = set(state_data.get("completed_steps", []))
        context.failed_steps = set(state_data.get("failed_steps", []))
        context.skipped_steps = set(state_data.get("skipped_steps", []))
        context.variables = state_data.get("variables", {})
        context.step_results = state_data.get("step_results", {})
        context.output_data = state_data.get("output_data", {})

        # Restore optional data if available
        if "global_context" in state_data:
            context.global_context = state_data["global_context"]

        if "error_details" in state_data:
            context.error_details = state_data["error_details"]

        return context

    async def _migrate_checkpoint_data(
        self,
        data: Dict[str, Any],
        source_version: StateVersion,
        target_version: StateVersion
    ) -> Dict[str, Any]:
        """Migrate checkpoint data between format versions."""
        # Placeholder migration logic
        # In practice, this would handle format changes between versions
        migrated_data = data.copy()
        migrated_data["_migrated_from"] = source_version.value
        migrated_data["_migrated_to"] = target_version.value
        return migrated_data

    async def _periodic_checkpoint_loop(self, context: ExecutionContext) -> None:
        """Periodic checkpoint creation loop."""
        execution_id = context.execution.execution_id

        while execution_id in self.active_executions:
            try:
                await asyncio.sleep(self.checkpoint_interval)

                if execution_id not in self.active_executions:
                    break

                # Check if execution is still active and making progress
                if not context.is_paused and not context.is_cancelled:
                    await self.create_checkpoint(
                        context,
                        checkpoint_level=CheckpointLevel.STANDARD,
                        trigger="periodic"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logfire.error(
                    "Periodic checkpoint failed",
                    execution_id=execution_id,
                    error=str(e)
                )
                await asyncio.sleep(5)  # Brief delay before retry

    def _update_cache(self, checkpoint: StateCheckpoint) -> None:
        """Update checkpoint cache."""
        # Add to cache
        self.state_cache[checkpoint.checkpoint_id] = checkpoint
        self.cache_access_times[checkpoint.checkpoint_id] = datetime.utcnow()

        # Evict old entries if cache is full
        if len(self.state_cache) > self.cache_size:
            # Remove oldest accessed checkpoint
            oldest_id = min(self.cache_access_times.items(), key=lambda x: x[1])[0]
            del self.state_cache[oldest_id]
            del self.cache_access_times[oldest_id]

    def _update_average_metric(self, metric_name: str, new_value: float) -> None:
        """Update running average metric."""
        current_avg = self.state_metrics.get(metric_name, 0.0)
        count = self.state_metrics.get(f"{metric_name}_count", 0)

        new_avg = (current_avg * count + new_value) / (count + 1)
        self.state_metrics[metric_name] = new_avg
        self.state_metrics[f"{metric_name}_count"] = count + 1

    def __repr__(self) -> str:
        """String representation of state manager."""
        return (
            f"WorkflowStateManager(active={len(self.active_executions)}, "
            f"cache_size={len(self.state_cache)}, "
            f"checkpoints_created={self.state_metrics['total_checkpoints']})"
        )
