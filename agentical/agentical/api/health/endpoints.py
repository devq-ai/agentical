"""
Health and Monitoring API Endpoints

This module provides comprehensive health check and monitoring endpoints for the
Agentical framework, following DevQ.ai best practices for observability.
"""

from datetime import datetime
import platform
import os
import psutil
import time
from typing import Dict, Any, List, Optional

import logfire
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from agentical.core.exceptions import AgenticalError
from agentical.db.init import get_db, engine
from agentical.db.profiler import get_query_statistics
from agentical.db.cache.redis_client import get_redis_client, check_redis_connection
from sqlalchemy.orm import Session

# Create router with prefix and tags
router = APIRouter(
    prefix="/health",
    tags=["health", "monitoring"]
)

# Health check response models
class ServiceHealth(BaseModel):
    """Individual service health details"""
    status: str = Field(..., description="Service health status (healthy, degraded, unavailable)")
    latency_ms: Optional[int] = Field(None, description="Service response latency in milliseconds")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed service metrics")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last check")


class SystemMetrics(BaseModel):
    """System performance metrics"""
    cpu_usage: float = Field(..., description="Current CPU usage percentage")
    memory_usage: Dict[str, float] = Field(..., description="Memory usage statistics")
    disk_usage: Dict[str, float] = Field(..., description="Disk usage statistics")
    uptime_seconds: int = Field(..., description="Application uptime in seconds")


class DatabaseMetrics(BaseModel):
    """Database performance metrics"""
    connection_pool: Dict[str, int] = Field(..., description="Database connection pool statistics")
    query_performance: Dict[str, Any] = Field(..., description="Query performance statistics")
    cache_hit_ratio: Optional[float] = Field(None, description="Cache hit ratio percentage")


class HealthResponse(BaseModel):
    """Comprehensive health check response"""
    status: str = Field(..., description="Overall health status (healthy, degraded, unavailable)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current server time")
    version: str = Field("1.0.0", description="API version")
    environment: str = Field(..., description="Current deployment environment")
    services: Dict[str, ServiceHealth] = Field(..., description="Service health details")
    system: SystemMetrics = Field(..., description="System performance metrics")
    database: Optional[DatabaseMetrics] = Field(None, description="Database performance metrics")


class MonitoringMetric(BaseModel):
    """Individual monitoring metric"""
    name: str = Field(..., description="Metric name")
    value: Any = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Measurement unit")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MonitoringResponse(BaseModel):
    """Monitoring data response"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: List[MonitoringMetric] = Field(..., description="List of monitoring metrics")


# Application start time for uptime calculation
APPLICATION_START_TIME = time.time()


async def get_system_metrics() -> SystemMetrics:
    """Collect system performance metrics"""
    with logfire.span("Get system metrics"):
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_metrics = {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent
        }
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_metrics = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent": disk.percent
        }
        
        # Calculate uptime
        uptime_seconds = int(time.time() - APPLICATION_START_TIME)
        
        return SystemMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory_metrics,
            disk_usage=disk_metrics,
            uptime_seconds=uptime_seconds
        )


async def get_database_metrics(db: Session) -> DatabaseMetrics:
    """Collect database performance metrics"""
    with logfire.span("Get database metrics"):
        try:
            # Get connection pool statistics
            pool_metrics = {
                "size": engine.pool.size(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
            }
            
            # Get query performance metrics
            query_stats = get_query_statistics()
            
            # Get cache metrics if available
            cache_hit_ratio = None
            try:
                redis_client = get_redis_client()
                if await check_redis_connection(redis_client):
                    # Get cache statistics from Redis
                    cache_info = await redis_client.info()
                    hits = int(cache_info.get('keyspace_hits', 0))
                    misses = int(cache_info.get('keyspace_misses', 0))
                    total = hits + misses
                    cache_hit_ratio = (hits / total) * 100 if total > 0 else 0
            except Exception as e:
                logfire.warning("Failed to get cache metrics", error=str(e))
            
            return DatabaseMetrics(
                connection_pool=pool_metrics,
                query_performance=query_stats,
                cache_hit_ratio=cache_hit_ratio
            )
        except Exception as e:
            logfire.error("Error retrieving database metrics", error=str(e))
            raise AgenticalError(f"Database metrics error: {str(e)}")


@router.get(
    "",
    response_model=HealthResponse,
    summary="Comprehensive health check",
    description="Get the health status of all components in the Agentical framework"
)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Comprehensive health check endpoint for all Agentical components"""
    with logfire.span("Health check endpoint"):
        start_time = time.time()
        
        try:
            # Collect service health information
            services = {}
            
            # Check database health
            db_latency_start = time.time()
            try:
                # Execute a simple query to check database connectivity
                db.execute("SELECT 1").fetchall()
                db_status = "healthy"
                db_details = {"connection": "established"}
            except Exception as e:
                db_status = "unavailable"
                db_details = {"error": str(e)}
                logfire.error("Database health check failed", error=str(e))
            
            db_latency_ms = int((time.time() - db_latency_start) * 1000)
            services["database"] = ServiceHealth(
                status=db_status,
                latency_ms=db_latency_ms,
                details=db_details
            )
            
            # Check Redis cache health
            cache_latency_start = time.time()
            try:
                redis_client = get_redis_client()
                redis_ok = await check_redis_connection(redis_client)
                cache_status = "healthy" if redis_ok else "degraded"
                cache_details = {"connection": "established" if redis_ok else "degraded"}
            except Exception as e:
                cache_status = "unavailable"
                cache_details = {"error": str(e)}
                logfire.error("Redis health check failed", error=str(e))
            
            cache_latency_ms = int((time.time() - cache_latency_start) * 1000)
            services["cache"] = ServiceHealth(
                status=cache_status,
                latency_ms=cache_latency_ms,
                details=cache_details
            )
            
            # Check Logfire health
            logfire_status = "healthy"  # If we got this far, Logfire is working
            services["logfire"] = ServiceHealth(
                status=logfire_status,
                latency_ms=0,
                details={"instrumentation": "active"}
            )
            
            # Get system metrics
            system_metrics = await get_system_metrics()
            
            # Get database metrics if database is healthy
            db_metrics = None
            if services["database"].status == "healthy":
                db_metrics = await get_database_metrics(db)
            
            # Determine overall status
            critical_services = ["database", "logfire"]
            critical_healthy = all(
                services[service].status == "healthy"
                for service in critical_services
                if service in services
            )
            
            overall_status = "healthy" if critical_healthy else "degraded"
            
            # Get environment
            environment = os.getenv("ENVIRONMENT", "development")
            
            # Create and return health response
            health_response = HealthResponse(
                status=overall_status,
                environment=environment,
                services=services,
                system=system_metrics,
                database=db_metrics
            )
            
            # Log health check results
            logfire.info(
                "Health check completed",
                status=overall_status,
                duration_ms=int((time.time() - start_time) * 1000),
                db_status=services["database"].status,
                cache_status=services["cache"].status
            )
            
            return health_response
        except Exception as e:
            logfire.error("Health check failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Health check failed: {str(e)}"
            )


@router.get(
    "/readiness",
    response_model=Dict[str, str],
    summary="Readiness probe",
    description="Simple readiness check for Kubernetes health probes"
)
async def readiness_check() -> Dict[str, str]:
    """Lightweight readiness check for Kubernetes probes"""
    with logfire.span("Readiness check"):
        return {"status": "ready"}


@router.get(
    "/liveness",
    response_model=Dict[str, str],
    summary="Liveness probe",
    description="Simple liveness check for Kubernetes health probes"
)
async def liveness_check() -> Dict[str, str]:
    """Lightweight liveness check for Kubernetes probes"""
    with logfire.span("Liveness check"):
        return {"status": "alive"}


@router.get(
    "/metrics",
    response_model=MonitoringResponse,
    summary="System metrics",
    description="Get system and application performance metrics"
)
async def metrics(db: Session = Depends(get_db)) -> MonitoringResponse:
    """Get detailed system and application metrics"""
    with logfire.span("Metrics endpoint"):
        metrics_list = []
        
        # System information
        metrics_list.append(MonitoringMetric(
            name="system.python.version",
            value=platform.python_version(),
            unit="version"
        ))
        
        metrics_list.append(MonitoringMetric(
            name="system.os",
            value=f"{platform.system()} {platform.release()}"
        ))
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        metrics_list.append(MonitoringMetric(
            name="system.cpu.usage",
            value=cpu_percent,
            unit="percent"
        ))
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics_list.append(MonitoringMetric(
            name="system.memory.total",
            value=round(memory.total / (1024**3), 2),
            unit="GB"
        ))
        
        metrics_list.append(MonitoringMetric(
            name="system.memory.used",
            value=round(memory.used / (1024**3), 2),
            unit="GB"
        ))
        
        metrics_list.append(MonitoringMetric(
            name="system.memory.percent",
            value=memory.percent,
            unit="percent"
        ))
        
        # Application metrics
        metrics_list.append(MonitoringMetric(
            name="app.uptime",
            value=int(time.time() - APPLICATION_START_TIME),
            unit="seconds"
        ))
        
        # Database metrics
        try:
            # Check connection pool
            metrics_list.append(MonitoringMetric(
                name="db.pool.size",
                value=engine.pool.size(),
                unit="connections"
            ))
            
            metrics_list.append(MonitoringMetric(
                name="db.pool.checked_out",
                value=engine.pool.checkedout(),
                unit="connections"
            ))
            
            # Get average query time
            query_stats = get_query_statistics()
            if query_stats and "average_time_ms" in query_stats:
                metrics_list.append(MonitoringMetric(
                    name="db.query.avg_time",
                    value=query_stats["average_time_ms"],
                    unit="ms"
                ))
        except Exception as e:
            logfire.error("Error collecting database metrics", error=str(e))
        
        # Redis cache metrics
        try:
            redis_client = get_redis_client()
            if await check_redis_connection(redis_client):
                info = await redis_client.info()
                
                metrics_list.append(MonitoringMetric(
                    name="cache.used_memory",
                    value=round(int(info.get("used_memory", 0)) / (1024**2), 2),
                    unit="MB"
                ))
                
                hits = int(info.get("keyspace_hits", 0))
                misses = int(info.get("keyspace_misses", 0))
                total = hits + misses
                
                if total > 0:
                    hit_ratio = (hits / total) * 100
                    metrics_list.append(MonitoringMetric(
                        name="cache.hit_ratio",
                        value=round(hit_ratio, 2),
                        unit="percent"
                    ))
        except Exception as e:
            logfire.error("Error collecting Redis metrics", error=str(e))
        
        return MonitoringResponse(metrics=metrics_list)


@router.get(
    "/database",
    response_model=DatabaseMetrics,
    summary="Database health",
    description="Get detailed database health and performance metrics"
)
async def database_health(db: Session = Depends(get_db)) -> DatabaseMetrics:
    """Get detailed database health and performance metrics"""
    with logfire.span("Database health check"):
        try:
            return await get_database_metrics(db)
        except Exception as e:
            logfire.error("Database health check failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database health check failed: {str(e)}"
            )