"""
Performance Monitor for Workflow Engine

This module provides comprehensive performance monitoring, metrics collection,
and optimization recommendations for the Agentical Workflow Engine.

Features:
- Real-time performance monitoring and alerting
- Resource utilization tracking and optimization
- Workflow execution analytics and insights
- Performance bottleneck detection and analysis
- SLA monitoring and compliance tracking
- Automated performance optimization recommendations
"""

import asyncio
import time
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import statistics
import json
import logging

import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.exceptions import WorkflowError, ValidationError
from ...core.logging import log_operation
from .execution_context import ExecutionContext


class MetricType(Enum):
    """Types of performance metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResourceType(Enum):
    """System resource types."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    AGENT_POOL = "agent_pool"


@dataclass
class PerformanceMetric:
    """Represents a performance metric."""
    name: str
    metric_type: MetricType
    value: Union[int, float]
    timestamp: datetime
    tags: Dict[str, str]
    unit: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type.value
        }


@dataclass
class PerformanceAlert:
    """Represents a performance alert."""
    alert_id: str
    metric_name: str
    severity: AlertSeverity
    message: str
    threshold_value: Union[int, float]
    current_value: Union[int, float]
    timestamp: datetime
    execution_id: Optional[str] = None
    workflow_id: Optional[int] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            **asdict(self),
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class ResourceUsage:
    """System resource usage snapshot."""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource usage to dictionary."""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class WorkflowPerformanceStats:
    """Performance statistics for a workflow execution."""
    execution_id: str
    workflow_id: int
    start_time: datetime
    end_time: Optional[datetime]
    total_duration: Optional[timedelta]
    step_count: int
    completed_steps: int
    failed_steps: int
    average_step_duration: float
    peak_memory_usage: float
    peak_cpu_usage: float
    agent_utilization: Dict[str, float]
    coordination_efficiency: float
    checkpoint_overhead: float
    error_rate: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            **asdict(self),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration": self.total_duration.total_seconds() if self.total_duration else None
        }


class ThresholdRule:
    """Performance threshold rule for alerting."""

    def __init__(
        self,
        metric_name: str,
        threshold_value: Union[int, float],
        comparison: str,  # "gt", "lt", "eq", "gte", "lte"
        severity: AlertSeverity,
        message_template: str,
        consecutive_violations: int = 1,
        cooldown_minutes: int = 5
    ):
        """Initialize threshold rule."""
        self.metric_name = metric_name
        self.threshold_value = threshold_value
        self.comparison = comparison
        self.severity = severity
        self.message_template = message_template
        self.consecutive_violations = consecutive_violations
        self.cooldown_minutes = cooldown_minutes

        # Tracking state
        self.current_violations = 0
        self.last_alert_time: Optional[datetime] = None

    def evaluate(self, metric_value: Union[int, float]) -> bool:
        """Evaluate if metric violates threshold."""
        violation = False

        if self.comparison == "gt":
            violation = metric_value > self.threshold_value
        elif self.comparison == "lt":
            violation = metric_value < self.threshold_value
        elif self.comparison == "gte":
            violation = metric_value >= self.threshold_value
        elif self.comparison == "lte":
            violation = metric_value <= self.threshold_value
        elif self.comparison == "eq":
            violation = metric_value == self.threshold_value

        if violation:
            self.current_violations += 1
        else:
            self.current_violations = 0

        return self.current_violations >= self.consecutive_violations

    def should_alert(self) -> bool:
        """Check if alert should be fired considering cooldown."""
        if self.last_alert_time is None:
            return True

        cooldown = timedelta(minutes=self.cooldown_minutes)
        return datetime.utcnow() - self.last_alert_time > cooldown

    def fire_alert(self) -> None:
        """Mark alert as fired."""
        self.last_alert_time = datetime.utcnow()


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for workflow engine.

    Monitors system resources, workflow performance, agent utilization,
    and provides real-time alerts and optimization recommendations.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        monitoring_interval: int = 30,  # seconds
        metric_retention_hours: int = 24,
        enable_system_monitoring: bool = True,
        enable_workflow_profiling: bool = True
    ):
        """Initialize performance monitor."""
        self.db_session = db_session
        self.monitoring_interval = monitoring_interval
        self.metric_retention_hours = metric_retention_hours
        self.enable_system_monitoring = enable_system_monitoring
        self.enable_workflow_profiling = enable_workflow_profiling

        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[PerformanceAlert] = []
        self.workflow_stats: Dict[str, WorkflowPerformanceStats] = {}

        # Resource monitoring
        self.resource_history: deque = deque(maxlen=100)
        self.baseline_metrics: Dict[str, float] = {}

        # Threshold rules
        self.threshold_rules: List[ThresholdRule] = []
        self._setup_default_thresholds()

        # Event handlers
        self.alert_handlers: List[Callable] = []
        self.metric_handlers: List[Callable] = []

        # Monitoring state
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_requested = False
        self._start_time = datetime.utcnow()

        # Performance baselines
        self.performance_baselines: Dict[str, Dict[str, float]] = {
            "execution_time": {"p50": 0, "p95": 0, "p99": 0},
            "memory_usage": {"average": 0, "peak": 0},
            "cpu_usage": {"average": 0, "peak": 0},
            "agent_efficiency": {"average": 0.8, "minimum": 0.6}
        }

        logfire.info(
            "Performance monitor initialized",
            monitoring_interval=monitoring_interval,
            metric_retention_hours=metric_retention_hours
        )

    async def start(self) -> None:
        """Start performance monitoring."""
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logfire.info("Performance monitoring started")

    async def stop(self) -> None:
        """Stop performance monitoring."""
        self._shutdown_requested = True

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logfire.info("Performance monitoring stopped")

    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
        unit: str = "",
        description: str = ""
    ) -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit=unit,
            description=description
        )

        self.metrics[name].append(metric)

        # Check threshold rules
        self._check_thresholds(name, value)

        # Emit to handlers
        for handler in self.metric_handlers:
            try:
                handler(metric)
            except Exception as e:
                logfire.error("Metric handler error", handler=str(handler), error=str(e))

        logfire.debug("Metric recorded", name=name, value=value, type=metric_type.value)

    def start_workflow_profiling(self, context: ExecutionContext) -> None:
        """Start profiling a workflow execution."""
        if not self.enable_workflow_profiling:
            return

        execution_id = context.execution.execution_id
        workflow_id = context.workflow.id

        stats = WorkflowPerformanceStats(
            execution_id=execution_id,
            workflow_id=workflow_id,
            start_time=datetime.utcnow(),
            end_time=None,
            total_duration=None,
            step_count=len(context.workflow.steps) if context.workflow.steps else 0,
            completed_steps=0,
            failed_steps=0,
            average_step_duration=0.0,
            peak_memory_usage=0.0,
            peak_cpu_usage=0.0,
            agent_utilization={},
            coordination_efficiency=0.0,
            checkpoint_overhead=0.0,
            error_rate=0.0
        )

        self.workflow_stats[execution_id] = stats

        # Record start metric
        self.record_metric(
            "workflow_started",
            1,
            MetricType.COUNTER,
            tags={"execution_id": execution_id, "workflow_id": str(workflow_id)}
        )

        logfire.info("Workflow profiling started", execution_id=execution_id)

    def update_workflow_progress(self, context: ExecutionContext) -> None:
        """Update workflow performance metrics during execution."""
        execution_id = context.execution.execution_id

        if execution_id not in self.workflow_stats:
            return

        stats = self.workflow_stats[execution_id]

        # Update basic stats
        stats.completed_steps = len(context.completed_steps)
        stats.failed_steps = len(context.failed_steps)

        if stats.completed_steps > 0:
            total_step_time = sum(
                duration.total_seconds()
                for duration in context.step_durations.values()
            )
            stats.average_step_duration = total_step_time / stats.completed_steps

        # Calculate error rate
        total_steps = stats.completed_steps + stats.failed_steps
        if total_steps > 0:
            stats.error_rate = stats.failed_steps / total_steps

        # Record progress metric
        progress = context.get_progress_percentage()
        self.record_metric(
            "workflow_progress",
            progress,
            MetricType.GAUGE,
            tags={"execution_id": execution_id}
        )

    def complete_workflow_profiling(self, context: ExecutionContext) -> WorkflowPerformanceStats:
        """Complete workflow profiling and return final stats."""
        execution_id = context.execution.execution_id

        if execution_id not in self.workflow_stats:
            # Create minimal stats if profiling wasn't started
            self.start_workflow_profiling(context)

        stats = self.workflow_stats[execution_id]
        stats.end_time = datetime.utcnow()
        stats.total_duration = stats.end_time - stats.start_time

        # Record completion metric
        self.record_metric(
            "workflow_completed",
            1,
            MetricType.COUNTER,
            tags={
                "execution_id": execution_id,
                "success": str(len(context.failed_steps) == 0),
                "duration_seconds": str(stats.total_duration.total_seconds())
            }
        )

        logfire.info(
            "Workflow profiling completed",
            execution_id=execution_id,
            duration=stats.total_duration.total_seconds(),
            error_rate=stats.error_rate
        )

        return stats

    def add_threshold_rule(self, rule: ThresholdRule) -> None:
        """Add a performance threshold rule."""
        self.threshold_rules.append(rule)
        logfire.info("Threshold rule added", metric=rule.metric_name, threshold=rule.threshold_value)

    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]) -> None:
        """Add alert handler."""
        self.alert_handlers.append(handler)

    def add_metric_handler(self, handler: Callable[[PerformanceMetric], None]) -> None:
        """Add metric handler."""
        self.metric_handlers.append(handler)

    def get_metric_statistics(self, metric_name: str, time_window: Optional[timedelta] = None) -> Dict[str, float]:
        """Get statistical summary of a metric."""
        if metric_name not in self.metrics:
            return {}

        metrics = self.metrics[metric_name]

        if time_window:
            cutoff_time = datetime.utcnow() - time_window
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]

        if not metrics:
            return {}

        values = [m.value for m in metrics]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99)
        }

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[PerformanceAlert]:
        """Get active (unresolved) alerts."""
        alerts = [alert for alert in self.alerts if not alert.resolved]

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                logfire.info("Alert resolved", alert_id=alert_id)
                return True

        return False

    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive system health summary."""
        current_resource_usage = self._collect_resource_usage()

        # Calculate average resource usage over last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_usage = [
            usage for usage in self.resource_history
            if usage.timestamp >= one_hour_ago
        ]

        avg_cpu = statistics.mean([u.cpu_percent for u in recent_usage]) if recent_usage else 0
        avg_memory = statistics.mean([u.memory_percent for u in recent_usage]) if recent_usage else 0

        # Count active alerts by severity
        active_alerts = self.get_active_alerts()
        alert_counts = defaultdict(int)
        for alert in active_alerts:
            alert_counts[alert.severity.value] += 1

        return {
            "current_resources": current_resource_usage.to_dict(),
            "average_cpu_1h": avg_cpu,
            "average_memory_1h": avg_memory,
            "active_workflows": len(self.workflow_stats),
            "total_metrics": sum(len(metrics) for metrics in self.metrics.values()),
            "active_alerts": {
                "total": len(active_alerts),
                "by_severity": dict(alert_counts)
            },
            "monitoring_uptime": (datetime.utcnow() - self._start_time).total_seconds(),
            "health_score": self._calculate_health_score()
        }

    def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Generate performance optimization recommendations."""
        recommendations = []

        # Analyze resource usage patterns
        if self.resource_history:
            recent_cpu = [u.cpu_percent for u in list(self.resource_history)[-10:]]
            recent_memory = [u.memory_percent for u in list(self.resource_history)[-10:]]

            avg_cpu = statistics.mean(recent_cpu)
            avg_memory = statistics.mean(recent_memory)

            if avg_cpu > 80:
                recommendations.append({
                    "type": "resource_optimization",
                    "priority": "high",
                    "title": "High CPU Usage Detected",
                    "description": f"Average CPU usage is {avg_cpu:.1f}%. Consider scaling horizontally or optimizing workflows.",
                    "metric": "cpu_usage",
                    "current_value": avg_cpu,
                    "recommended_action": "scale_out"
                })

            if avg_memory > 85:
                recommendations.append({
                    "type": "resource_optimization",
                    "priority": "high",
                    "title": "High Memory Usage Detected",
                    "description": f"Average memory usage is {avg_memory:.1f}%. Consider increasing memory or optimizing data structures.",
                    "metric": "memory_usage",
                    "current_value": avg_memory,
                    "recommended_action": "increase_memory"
                })

        # Analyze workflow performance
        for execution_id, stats in self.workflow_stats.items():
            if stats.error_rate > 0.1:  # More than 10% error rate
                recommendations.append({
                    "type": "workflow_optimization",
                    "priority": "medium",
                    "title": f"High Error Rate in Workflow {execution_id}",
                    "description": f"Error rate is {stats.error_rate:.1%}. Review workflow logic and error handling.",
                    "metric": "error_rate",
                    "current_value": stats.error_rate,
                    "execution_id": execution_id
                })

            if stats.average_step_duration > 300:  # Steps taking more than 5 minutes
                recommendations.append({
                    "type": "workflow_optimization",
                    "priority": "medium",
                    "title": f"Slow Step Execution in Workflow {execution_id}",
                    "description": f"Average step duration is {stats.average_step_duration:.1f} seconds. Consider optimizing step logic.",
                    "metric": "step_duration",
                    "current_value": stats.average_step_duration,
                    "execution_id": execution_id
                })

        return recommendations

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while not self._shutdown_requested:
            try:
                # Collect system metrics
                if self.enable_system_monitoring:
                    await self._collect_system_metrics()

                # Clean up old metrics
                self._cleanup_old_metrics()

                # Update performance baselines
                self._update_baselines()

                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logfire.error("Monitoring loop error", error=str(e))
                await asyncio.sleep(5)

    async def _collect_system_metrics(self) -> None:
        """Collect system resource metrics."""
        try:
            # Get resource usage
            resource_usage = self._collect_resource_usage()
            self.resource_history.append(resource_usage)

            # Record individual metrics
            self.record_metric("cpu_usage_percent", resource_usage.cpu_percent, MetricType.GAUGE, unit="%")
            self.record_metric("memory_usage_percent", resource_usage.memory_percent, MetricType.GAUGE, unit="%")
            self.record_metric("memory_used_mb", resource_usage.memory_used_mb, MetricType.GAUGE, unit="MB")
            self.record_metric("disk_usage_percent", resource_usage.disk_usage_percent, MetricType.GAUGE, unit="%")
            self.record_metric("active_connections", resource_usage.active_connections, MetricType.GAUGE)

            # Python-specific metrics
            gc_stats = gc.get_stats()
            if gc_stats:
                self.record_metric("gc_collections", sum(g['collections'] for g in gc_stats), MetricType.COUNTER)

        except Exception as e:
            logfire.error("Failed to collect system metrics", error=str(e))

    def _collect_resource_usage(self) -> ResourceUsage:
        """Collect current system resource usage."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024 * 1024 * 1024)

        # Network I/O
        network = psutil.net_io_counters()
        network_sent_mb = network.bytes_sent / (1024 * 1024)
        network_recv_mb = network.bytes_recv / (1024 * 1024)

        # Network connections
        try:
            connections = psutil.net_connections()
            active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            active_connections = 0

        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            active_connections=active_connections,
            timestamp=datetime.utcnow()
        )

    def _check_thresholds(self, metric_name: str, value: Union[int, float]) -> None:
        """Check metric value against threshold rules."""
        for rule in self.threshold_rules:
            if rule.metric_name == metric_name:
                if rule.evaluate(value) and rule.should_alert():
                    alert = PerformanceAlert(
                        alert_id=f"{metric_name}_{int(time.time())}",
                        metric_name=metric_name,
                        severity=rule.severity,
                        message=rule.message_template.format(
                            metric_name=metric_name,
                            value=value,
                            threshold=rule.threshold_value
                        ),
                        threshold_value=rule.threshold_value,
                        current_value=value,
                        timestamp=datetime.utcnow()
                    )

                    self.alerts.append(alert)
                    rule.fire_alert()

                    # Emit to handlers
                    for handler in self.alert_handlers:
                        try:
                            handler(alert)
                        except Exception as e:
                            logfire.error("Alert handler error", error=str(e))

                    logfire.warning(
                        "Performance alert triggered",
                        alert_id=alert.alert_id,
                        metric=metric_name,
                        value=value,
                        threshold=rule.threshold_value
                    )

    def _cleanup_old_metrics(self) -> None:
        """Remove old metrics beyond retention period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metric_retention_hours)

        for metric_name in self.metrics:
            # Filter out old metrics
            old_count = len(self.metrics[metric_name])
            self.metrics[metric_name] = deque(
                [m for m in self.metrics[metric_name] if m.timestamp >= cutoff_time],
                maxlen=1000
            )
            new_count = len(self.metrics[metric_name])

            if old_count > new_count:
                logfire.debug(
                    "Cleaned up old metrics",
                    metric_name=metric_name,
                    removed_count=old_count - new_count
                )

    def _update_baselines(self) -> None:
        """Update performance baselines based on historical data."""
        # Update execution time baselines
        if "workflow_execution_time" in self.metrics:
            execution_times = [m.value for m in self.metrics["workflow_execution_time"]]
            if execution_times:
                self.performance_baselines["execution_time"] = {
                    "p50": self._percentile(execution_times, 50),
                    "p95": self._percentile(execution_times, 95),
                    "p99": self._percentile(execution_times, 99)
                }

        # Update resource usage baselines
        if self.resource_history:
            cpu_values = [u.cpu_percent for u in self.resource_history]
            memory_values = [u.memory_percent for u in self.resource_history]

            self.performance_baselines["cpu_usage"] = {
                "average": statistics.mean(cpu_values),
                "peak": max(cpu_values)
            }

            self.performance_baselines["memory_usage"] = {
                "average": statistics.mean(memory_values),
                "peak": max(memory_values)
            }

    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)."""
        score = 100.0

        # Deduct points for active critical alerts
        critical_alerts = [a for a in self.get_active_alerts() if a.severity == AlertSeverity.CRITICAL]
        score -= len(critical_alerts) * 20

        # Deduct points for high error alerts
        error_alerts = [a for a in self.get_active_alerts() if a.severity == AlertSeverity.ERROR]
        score -= len(error_alerts) * 10

        # Deduct points for warning alerts
        warning_alerts = [a for a in self.get_active_alerts() if a.severity == AlertSeverity.WARNING]
        score -= len(warning_alerts) * 5

        # Consider resource utilization
        if self.resource_history:
            recent_usage = list(self.resource_history)[-5:]  # Last 5 measurements
            avg_cpu = statistics.mean([u.cpu_percent for u in recent_usage])
            avg_memory = statistics.mean([u.memory_percent for u in recent_usage])

            if avg_cpu > 90:
                score -= 15
            elif avg_cpu > 80:
                score -= 10

            if avg_memory > 90:
                score -= 15
            elif avg_memory > 80:
                score -= 10

        return max(0.0, min(100.0, score))

    def _setup_default_thresholds(self) -> None:
        """Set up default performance threshold rules."""
        default_rules = [
            ThresholdRule(
                "cpu_usage_percent", 85.0, "gt", AlertSeverity.WARNING,
                "High CPU usage: {value:.1f}% (threshold: {threshold}%)", 3, 5
            ),
            ThresholdRule(
                "cpu_usage_percent", 95.0, "gt", AlertSeverity.CRITICAL,
                "Critical CPU usage: {value:.1f}% (threshold: {threshold}%)", 2, 2
            ),
            ThresholdRule(
                "memory_usage_percent", 85.0, "gt", AlertSeverity.WARNING,
                "High memory usage: {value:.1f}% (threshold: {threshold}%)", 3, 5
            ),
            ThresholdRule(
                "memory_usage_percent", 95.0, "gt", AlertSeverity.CRITICAL,
                "Critical memory usage: {value:.1f}% (threshold: {threshold}%)", 2, 2
            ),
            ThresholdRule(
                "workflow_error_rate", 0.1, "gt", AlertSeverity.ERROR,
                "High workflow error rate: {value:.1%} (threshold: {threshold:.1%})", 1, 10
            )
        ]

        self.threshold_rules.extend(default_rules)

    @staticmethod
    def _percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = k - f

        if f == len(sorted_values) - 1:
            return sorted_values[f]

        return sorted_values[f] + c * (sorted_values[f + 1] - sorted_values[f])

    def __repr__(self) -> str:
        """String representation of performance monitor."""
        return (
            f"PerformanceMonitor(metrics={len(self.metrics)}, "
            f"active_alerts={len(self.get_active_alerts())}, "
            f"workflows={len(self.workflow_stats)})"
        )
