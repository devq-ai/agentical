"""
Resource Monitor for Agentical

Comprehensive resource monitoring and management system for tracking
memory usage, CPU utilization, and system performance metrics.

Features:
- Real-time resource monitoring
- Memory leak detection
- Performance alerting
- Resource usage optimization
- System health checks
"""

import asyncio
import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import gc

import logfire

# Optional imports for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)


@dataclass
class ResourceThresholds:
    """Resource usage thresholds for monitoring"""
    memory_warning_mb: float = 512.0
    memory_critical_mb: float = 1024.0
    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0
    disk_warning_percent: float = 85.0
    disk_critical_percent: float = 95.0
    response_time_warning_ms: float = 200.0
    response_time_critical_ms: float = 500.0


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time"""
    timestamp: datetime
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    cpu_percent: float = 0.0
    disk_percent: float = 0.0
    active_connections: int = 0
    active_tasks: int = 0
    response_time_ms: float = 0.0
    gc_collections: Dict[str, int] = field(default_factory=dict)


class ResourceMonitor:
    """System resource monitoring and management"""
    
    def __init__(self, thresholds: ResourceThresholds = None, 
                 monitoring_interval: float = 10.0):
        self.thresholds = thresholds or ResourceThresholds()
        self.monitoring_interval = monitoring_interval
        
        # Resource history
        self.snapshots = deque(maxlen=360)  # Keep 1 hour of data at 10s intervals
        self.alerts: List[Dict[str, Any]] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.process = None
        
        # Performance tracking
        self.start_time = datetime.utcnow()
        self.total_operations = 0
        self.failed_operations = 0
        
        # Initialize process monitoring if available
        if PSUTIL_AVAILABLE:
            try:
                self.process = psutil.Process()
            except Exception as e:
                logger.warning(f"Failed to initialize process monitoring: {e}")
        
        logger.info("Resource monitor initialized")
    
    async def start_monitoring(self):
        """Start continuous resource monitoring"""
        if self.monitoring_active:
            logger.warning("Resource monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logfire.info("Resource monitoring started", 
                    interval=self.monitoring_interval)
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logfire.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                snapshot = await self._take_snapshot()
                self.snapshots.append(snapshot)
                
                # Check for threshold violations
                await self._check_thresholds(snapshot)
                
                # Log metrics to Logfire
                logfire.info("Resource snapshot",
                           memory_mb=snapshot.memory_mb,
                           cpu_percent=snapshot.cpu_percent,
                           active_tasks=snapshot.active_tasks)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _take_snapshot(self) -> ResourceSnapshot:
        """Take a snapshot of current resource usage"""
        snapshot = ResourceSnapshot(timestamp=datetime.utcnow())
        
        try:
            if self.process and PSUTIL_AVAILABLE:
                # Memory information
                memory_info = self.process.memory_info()
                snapshot.memory_mb = memory_info.rss / 1024 / 1024
                
                try:
                    snapshot.memory_percent = self.process.memory_percent()
                except Exception:
                    snapshot.memory_percent = 0.0
                
                # CPU information
                try:
                    snapshot.cpu_percent = self.process.cpu_percent()
                except Exception:
                    snapshot.cpu_percent = 0.0
                
                # Connection information
                try:
                    connections = self.process.connections()
                    snapshot.active_connections = len(connections)
                except Exception:
                    snapshot.active_connections = 0
            
            # System-wide disk usage
            if PSUTIL_AVAILABLE:
                try:
                    disk_usage = psutil.disk_usage('/')
                    snapshot.disk_percent = (disk_usage.used / disk_usage.total) * 100
                except Exception:
                    snapshot.disk_percent = 0.0
            
            # Garbage collection statistics
            snapshot.gc_collections = {
                f"gen_{i}": gc.get_stats()[i]['collections'] 
                for i in range(len(gc.get_stats()))
            }
            
            # Task information (if available)
            try:
                current_task = asyncio.current_task()
                if current_task:
                    all_tasks = asyncio.all_tasks()
                    snapshot.active_tasks = len([t for t in all_tasks if not t.done()])
            except Exception:
                snapshot.active_tasks = 0
            
        except Exception as e:
            logger.error(f"Error taking resource snapshot: {e}")
        
        return snapshot
    
    async def _check_thresholds(self, snapshot: ResourceSnapshot):
        """Check resource thresholds and generate alerts"""
        alerts = []
        
        # Memory threshold checks
        if snapshot.memory_mb > self.thresholds.memory_critical_mb:
            alerts.append({
                "type": "memory",
                "level": "critical", 
                "message": f"Memory usage critical: {snapshot.memory_mb:.1f}MB",
                "value": snapshot.memory_mb,
                "threshold": self.thresholds.memory_critical_mb
            })
        elif snapshot.memory_mb > self.thresholds.memory_warning_mb:
            alerts.append({
                "type": "memory",
                "level": "warning",
                "message": f"Memory usage high: {snapshot.memory_mb:.1f}MB", 
                "value": snapshot.memory_mb,
                "threshold": self.thresholds.memory_warning_mb
            })
        
        # CPU threshold checks
        if snapshot.cpu_percent > self.thresholds.cpu_critical_percent:
            alerts.append({
                "type": "cpu",
                "level": "critical",
                "message": f"CPU usage critical: {snapshot.cpu_percent:.1f}%",
                "value": snapshot.cpu_percent,
                "threshold": self.thresholds.cpu_critical_percent
            })
        elif snapshot.cpu_percent > self.thresholds.cpu_warning_percent:
            alerts.append({
                "type": "cpu", 
                "level": "warning",
                "message": f"CPU usage high: {snapshot.cpu_percent:.1f}%",
                "value": snapshot.cpu_percent,
                "threshold": self.thresholds.cpu_warning_percent
            })
        
        # Disk threshold checks
        if snapshot.disk_percent > self.thresholds.disk_critical_percent:
            alerts.append({
                "type": "disk",
                "level": "critical",
                "message": f"Disk usage critical: {snapshot.disk_percent:.1f}%",
                "value": snapshot.disk_percent,
                "threshold": self.thresholds.disk_critical_percent
            })
        elif snapshot.disk_percent > self.thresholds.disk_warning_percent:
            alerts.append({
                "type": "disk",
                "level": "warning", 
                "message": f"Disk usage high: {snapshot.disk_percent:.1f}%",
                "value": snapshot.disk_percent,
                "threshold": self.thresholds.disk_warning_percent
            })
        
        # Process alerts
        for alert in alerts:
            alert["timestamp"] = snapshot.timestamp.isoformat()
            self.alerts.append(alert)
            
            # Log to Logfire
            logfire.warning("Resource threshold violation",
                          alert_type=alert["type"],
                          level=alert["level"],
                          message=alert["message"])
        
        # Trigger automatic optimization if critical
        critical_alerts = [a for a in alerts if a["level"] == "critical"]
        if critical_alerts:
            await self._trigger_optimization()
    
    async def _trigger_optimization(self):
        """Trigger automatic resource optimization"""
        logfire.info("Triggering automatic resource optimization")
        
        try:
            # Force garbage collection
            collected = gc.collect()
            logfire.info("Garbage collection triggered", objects_collected=collected)
            
            # Additional optimization strategies could be added here:
            # - Clear caches
            # - Reduce concurrent operations
            # - Close idle connections
            
        except Exception as e:
            logger.error(f"Resource optimization failed: {e}")
    
    def get_current_usage(self) -> Dict[str, Any]:
        """Get current resource usage"""
        if not self.snapshots:
            return {"error": "No snapshots available"}
        
        latest = self.snapshots[-1]
        
        return {
            "memory_mb": latest.memory_mb,
            "memory_percent": latest.memory_percent,
            "cpu_percent": latest.cpu_percent,
            "disk_percent": latest.disk_percent,
            "active_connections": latest.active_connections,
            "active_tasks": latest.active_tasks,
            "timestamp": latest.timestamp.isoformat()
        }
    
    def get_usage_trends(self, duration_minutes: int = 30) -> Dict[str, Any]:
        """Get resource usage trends over specified duration"""
        if not self.snapshots:
            return {"error": "No snapshots available"}
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=duration_minutes)
        recent_snapshots = [
            s for s in self.snapshots 
            if s.timestamp >= cutoff_time
        ]
        
        if not recent_snapshots:
            return {"error": "No recent snapshots available"}
        
        # Calculate trends
        memory_values = [s.memory_mb for s in recent_snapshots]
        cpu_values = [s.cpu_percent for s in recent_snapshots]
        
        return {
            "duration_minutes": duration_minutes,
            "snapshot_count": len(recent_snapshots),
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "average": sum(memory_values) / len(memory_values) if memory_values else 0,
                "peak": max(memory_values) if memory_values else 0,
                "trend": "increasing" if len(memory_values) > 1 and memory_values[-1] > memory_values[0] else "stable"
            },
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "peak": max(cpu_values) if cpu_values else 0,
                "trend": "increasing" if len(cpu_values) > 1 and cpu_values[-1] > cpu_values[0] else "stable"
            }
        }
    
    def get_alerts(self, level: str = None) -> List[Dict[str, Any]]:
        """Get resource alerts, optionally filtered by level"""
        if level:
            return [a for a in self.alerts if a["level"] == level]
        return self.alerts.copy()
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        uptime = datetime.utcnow() - self.start_time
        
        current_usage = self.get_current_usage()
        trends = self.get_usage_trends()
        
        success_rate = (
            (self.total_operations - self.failed_operations) / self.total_operations * 100
            if self.total_operations > 0 else 100
        )
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_operations": self.total_operations,
            "failed_operations": self.failed_operations,
            "success_rate": success_rate,
            "current_usage": current_usage,
            "usage_trends": trends,
            "alert_counts": {
                "critical": len([a for a in self.alerts if a["level"] == "critical"]),
                "warning": len([a for a in self.alerts if a["level"] == "warning"])
            },
            "monitoring_active": self.monitoring_active,
            "psutil_available": PSUTIL_AVAILABLE
        }
    
    def track_operation(self, success: bool = True):
        """Track an operation for performance metrics"""
        self.total_operations += 1
        if not success:
            self.failed_operations += 1


class MemoryLeakDetector:
    """Detect potential memory leaks"""
    
    def __init__(self, check_interval: float = 60.0):
        self.check_interval = check_interval
        self.memory_history = deque(maxlen=60)  # 1 hour of data
        self.leak_threshold_mb = 100  # Alert if memory grows by 100MB consistently
        
    async def start_detection(self):
        """Start memory leak detection"""
        while True:
            try:
                if PSUTIL_AVAILABLE:
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    self.memory_history.append({
                        "timestamp": datetime.utcnow(),
                        "memory_mb": memory_mb
                    })
                    
                    # Check for memory leak pattern
                    if len(self.memory_history) >= 10:
                        await self._check_memory_leak()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Memory leak detection error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_memory_leak(self):
        """Check for memory leak patterns"""
        if len(self.memory_history) < 10:
            return
        
        # Calculate memory growth trend
        recent_memories = [h["memory_mb"] for h in list(self.memory_history)[-10:]]
        oldest_memory = recent_memories[0]
        newest_memory = recent_memories[-1]
        
        growth = newest_memory - oldest_memory
        
        if growth > self.leak_threshold_mb:
            logfire.warning("Potential memory leak detected",
                          memory_growth_mb=growth,
                          oldest_memory=oldest_memory,
                          newest_memory=newest_memory)


# Global resource monitor
_global_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """Get or create global resource monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ResourceMonitor()
    return _global_monitor


async def start_resource_monitoring():
    """Start global resource monitoring"""
    monitor = get_resource_monitor()
    await monitor.start_monitoring()


async def stop_resource_monitoring():
    """Stop global resource monitoring"""
    monitor = get_resource_monitor()
    await monitor.stop_monitoring()


def get_resource_stats() -> Dict[str, Any]:
    """Get current resource statistics"""
    monitor = get_resource_monitor()
    return monitor.get_performance_summary()