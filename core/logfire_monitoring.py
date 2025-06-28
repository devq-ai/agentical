# Logfire-First Monitoring Implementation for Agentical
# Comprehensive observability using Logfire as the primary monitoring solution

import os
import time
import asyncio
import psutil
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
import logfire
from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge
import structlog

class AgenticalMonitoring:
    """
    Comprehensive monitoring implementation using Logfire as primary observability platform
    with minimal Prometheus for infrastructure metrics collection.
    """
    
    def __init__(self):
        self.setup_logfire()
        self.setup_structured_logging()
        self.metrics_collectors = {}
        self._system_metrics_task = None
    
    def setup_logfire(self):
        """Configure Logfire with production-ready settings."""
        logfire.configure(
            token=os.getenv("LOGFIRE_TOKEN"),
            project_name=os.getenv("LOGFIRE_PROJECT_NAME", "agentical-production"),
            service_name=os.getenv("LOGFIRE_SERVICE_NAME", "agentical-api"),
            service_version=os.getenv("APP_VERSION", "1.0.0"),
            environment=os.getenv("ENVIRONMENT", "production"),
            # Optimize for production workloads
            sampling_rate=float(os.getenv("LOGFIRE_SAMPLING_RATE", "0.1")),
            # Enable trace correlation
            send_to_logfire=True,
            console=True if os.getenv("ENVIRONMENT") == "development" else False,
        )
        
        logfire.info(
            "Agentical monitoring initialized",
            service_name=os.getenv("LOGFIRE_SERVICE_NAME", "agentical-api"),
            environment=os.getenv("ENVIRONMENT", "production"),
            version=os.getenv("APP_VERSION", "1.0.0")
        )
    
    def setup_structured_logging(self):
        """Configure structured logging with Logfire integration."""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    def instrument_fastapi(self, app: FastAPI):
        """Instrument FastAPI application with comprehensive monitoring."""
        # Primary Logfire instrumentation
        logfire.instrument_fastapi(
            app,
            capture_headers=True,
            capture_body=True,
            excluded_urls=["/health", "/metrics", "/docs", "/openapi.json"]
        )
        
        # Add custom middleware for business metrics
        @app.middleware("http")
        async def monitoring_middleware(request: Request, call_next):
            start_time = time.time()
            
            # Create span context for the request
            with logfire.span(
                "http_request",
                method=request.method,
                url=str(request.url),
                user_agent=request.headers.get("user-agent", "unknown")
            ) as span:
                
                try:
                    response = await call_next(request)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log comprehensive request metrics
                    logfire.info(
                        "HTTP request completed",
                        method=request.method,
                        url=str(request.url),
                        status_code=response.status_code,
                        duration_ms=round(duration_ms, 2),
                        response_size=response.headers.get("content-length", 0)
                    )
                    
                    # Set span attributes
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute("http.response_size", response.headers.get("content-length", 0))
                    span.set_attribute("duration_ms", round(duration_ms, 2))
                    
                    return response
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log error with context
                    logfire.error(
                        "HTTP request failed",
                        method=request.method,
                        url=str(request.url),
                        duration_ms=round(duration_ms, 2),
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    
                    # Set span error attributes
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    span.set_attribute("error.type", type(e).__name__)
                    
                    raise
        
        return app
    
    def instrument_database(self):
        """Instrument database connections."""
        # Instrument common database libraries
        logfire.instrument_asyncpg()
        logfire.instrument_sqlalchemy()
        logfire.instrument_psycopg()
        
        logfire.info("Database instrumentation enabled")
    
    def instrument_cache(self):
        """Instrument Redis and caching operations."""
        logfire.instrument_redis()
        
        logfire.info("Cache instrumentation enabled")
    
    def instrument_http_clients(self):
        """Instrument HTTP client libraries."""
        logfire.instrument_httpx()
        logfire.instrument_requests()
        
        logfire.info("HTTP client instrumentation enabled")
    
    @logfire.instrument()
    async def track_agent_execution(
        self, 
        agent_id: str, 
        task_type: str, 
        task_data: Optional[Dict[str, Any]] = None
    ):
        """Track agent execution with comprehensive metrics."""
        with logfire.span(
            "agent_execution",
            agent_id=agent_id,
            task_type=task_type,
            task_size=len(str(task_data)) if task_data else 0
        ) as span:
            
            start_time = time.time()
            
            try:
                # Log task start
                logfire.info(
                    "Agent task started",
                    agent_id=agent_id,
                    task_type=task_type,
                    task_data_keys=list(task_data.keys()) if task_data else []
                )
                
                # Simulate agent processing (replace with actual logic)
                await asyncio.sleep(0.1)
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Log successful completion
                logfire.info(
                    "Agent task completed successfully",
                    agent_id=agent_id,
                    task_type=task_type,
                    duration_ms=round(duration_ms, 2),
                    status="success"
                )
                
                # Set span success attributes
                span.set_attribute("status", "success")
                span.set_attribute("duration_ms", round(duration_ms, 2))
                
                return {"status": "success", "duration_ms": duration_ms}
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Log error with context
                logfire.error(
                    "Agent task failed",
                    agent_id=agent_id,
                    task_type=task_type,
                    duration_ms=round(duration_ms, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    status="error"
                )
                
                # Set span error attributes
                span.set_attribute("status", "error")
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                span.set_attribute("duration_ms", round(duration_ms, 2))
                
                raise
    
    @logfire.instrument()
    def track_mcp_tool_usage(self, tool_name: str, tool_params: Dict[str, Any]):
        """Track MCP tool usage and performance."""
        with logfire.span("mcp_tool_execution", tool_name=tool_name) as span:
            
            start_time = time.time()
            
            try:
                logfire.info(
                    "MCP tool execution started",
                    tool_name=tool_name,
                    param_count=len(tool_params),
                    param_keys=list(tool_params.keys())
                )
                
                # Simulate tool execution
                time.sleep(0.05)
                
                duration_ms = (time.time() - start_time) * 1000
                
                logfire.info(
                    "MCP tool execution completed",
                    tool_name=tool_name,
                    duration_ms=round(duration_ms, 2),
                    status="success"
                )
                
                span.set_attribute("duration_ms", round(duration_ms, 2))
                span.set_attribute("status", "success")
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logfire.error(
                    "MCP tool execution failed",
                    tool_name=tool_name,
                    duration_ms=round(duration_ms, 2),
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                raise
    
    async def collect_system_metrics(self):
        """Collect system-level metrics and send to Logfire."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_stats = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            except:
                network_stats = {}
            
            # Log comprehensive system metrics
            logfire.info(
                "System metrics collected",
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                memory_total_gb=round(memory.total / (1024**3), 2),
                memory_used_gb=round(memory.used / (1024**3), 2),
                memory_percent=memory.percent,
                disk_total_gb=round(disk.total / (1024**3), 2),
                disk_used_gb=round(disk.used / (1024**3), 2),
                disk_percent=round((disk.used / disk.total) * 100, 2),
                **network_stats
            )
            
        except Exception as e:
            logfire.error(
                "Failed to collect system metrics",
                error=str(e),
                error_type=type(e).__name__
            )
    
    async def start_system_metrics_collection(self, interval: int = 30):
        """Start periodic system metrics collection."""
        async def metrics_loop():
            while True:
                await self.collect_system_metrics()
                await asyncio.sleep(interval)
        
        self._system_metrics_task = asyncio.create_task(metrics_loop())
        logfire.info(
            "System metrics collection started",
            interval_seconds=interval
        )
    
    async def stop_system_metrics_collection(self):
        """Stop system metrics collection."""
        if self._system_metrics_task:
            self._system_metrics_task.cancel()
            try:
                await self._system_metrics_task
            except asyncio.CancelledError:
                pass
            
            logfire.info("System metrics collection stopped")
    
    def create_custom_alert_rules(self):
        """Define custom alert rules for Logfire."""
        # This would be configured in Logfire dashboard
        alert_rules = {
            "high_error_rate": {
                "condition": "error_rate > 5%",
                "window": "5m",
                "severity": "critical"
            },
            "slow_response_time": {
                "condition": "p95_response_time > 2s",
                "window": "5m", 
                "severity": "warning"
            },
            "agent_task_failures": {
                "condition": "agent_failure_rate > 10%",
                "window": "10m",
                "severity": "critical"
            },
            "high_memory_usage": {
                "condition": "memory_percent > 90%",
                "window": "5m",
                "severity": "warning"
            }
        }
        
        logfire.info(
            "Alert rules configured",
            rule_count=len(alert_rules),
            rules=list(alert_rules.keys())
        )
        
        return alert_rules

# Global monitoring instance
monitoring = AgenticalMonitoring()

# Convenience functions for application use
@logfire.instrument()
async def track_agent_task(agent_id: str, task_type: str, task_data: Dict[str, Any] = None):
    """Convenience function to track agent task execution."""
    return await monitoring.track_agent_execution(agent_id, task_type, task_data)

@logfire.instrument()
def track_mcp_tool(tool_name: str, tool_params: Dict[str, Any]):
    """Convenience function to track MCP tool usage."""
    return monitoring.track_mcp_tool_usage(tool_name, tool_params)

@logfire.instrument()
def track_database_operation(operation: str, table: str, duration_ms: float, rows_affected: int = 0):
    """Track database operations."""
    logfire.info(
        "Database operation completed",
        operation=operation,
        table=table,
        duration_ms=round(duration_ms, 2),
        rows_affected=rows_affected
    )

@logfire.instrument()
def track_cache_operation(operation: str, key: str, hit: bool, duration_ms: float):
    """Track cache operations."""
    logfire.info(
        "Cache operation completed",
        operation=operation,
        cache_key=key,
        cache_hit=hit,
        duration_ms=round(duration_ms, 2)
    )

# Application lifecycle management
@asynccontextmanager
async def monitoring_lifespan(app: FastAPI):
    """Application lifespan with monitoring setup."""
    # Startup
    logfire.info("Agentical application starting up")
    
    # Instrument all components
    monitoring.instrument_database()
    monitoring.instrument_cache()
    monitoring.instrument_http_clients()
    
    # Start system metrics collection
    await monitoring.start_system_metrics_collection(interval=30)
    
    # Setup alert rules
    monitoring.create_custom_alert_rules()
    
    logfire.info("Agentical monitoring fully initialized")
    
    yield
    
    # Shutdown
    logfire.info("Agentical application shutting down")
    await monitoring.stop_system_metrics_collection()
    logfire.info("Agentical monitoring shutdown complete")