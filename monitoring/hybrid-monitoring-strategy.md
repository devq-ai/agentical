# Hybrid Monitoring Strategy: Logfire + Prometheus/Grafana

## Overview

Agentical uses a hybrid monitoring approach combining **Logfire** for application observability and **Prometheus/Grafana** for infrastructure monitoring, providing comprehensive coverage while leveraging each tool's strengths.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Logfire       │    │  Prometheus     │    │    Grafana      │
│  (Application)  │    │ (Infrastructure)│    │ (Visualization) │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • FastAPI APM   │    │ • Node Metrics  │    │ • Infra Dashboards│
│ • Trace Data    │    │ • K8s Metrics   │    │ • Custom Panels │
│ • Custom Metrics│    │ • Redis Metrics │    │ • Alerting UI   │
│ • Logs + Context│    │ • DB Metrics    │    │ • Trend Analysis│
│ • Real-time     │    │ • Long-term     │    │ • SLI/SLO       │
│   Dashboards    │    │   Storage       │    │   Tracking      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Monitoring Responsibilities

### 🔥 Logfire Handles
- **Application Performance**: Request latency, throughput, error rates
- **Business Metrics**: Agent task completion, success rates, queue depths
- **Distributed Tracing**: End-to-end request flow across services
- **Structured Logging**: Correlated logs with trace context
- **Real-time Alerts**: Application-level performance issues
- **Development Debugging**: Rich context for troubleshooting

### 📊 Prometheus/Grafana Handles
- **Infrastructure Health**: CPU, memory, disk, network usage
- **Kubernetes Monitoring**: Pod status, resource utilization, scaling events
- **Database Performance**: Connection pools, query performance, replication lag
- **Cache Performance**: Redis hit/miss rates, memory usage, evictions
- **Long-term Trends**: Capacity planning and historical analysis
- **Infrastructure Alerts**: Resource exhaustion, service failures

## Implementation

### 1. Logfire Configuration (Primary APM)

```python
# core/monitoring.py
import logfire
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Configure Logfire with enhanced settings
logfire.configure(
    token=os.getenv("LOGFIRE_TOKEN"),
    project_name="agentical-production",
    service_name="agentical-api",
    service_version="1.0.0",
    environment=os.getenv("ENVIRONMENT", "production"),
    # Enhanced sampling for high-volume scenarios
    sampling_rate=0.1 if os.getenv("ENVIRONMENT") == "production" else 1.0
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logfire.info("Agentical API starting up")
    yield
    # Shutdown
    logfire.info("Agentical API shutting down")

app = FastAPI(lifespan=lifespan)

# Automatic instrumentation
logfire.instrument_fastapi(app, capture_headers=True)
logfire.instrument_asyncpg()
logfire.instrument_redis()
logfire.instrument_httpx()

# Custom metrics for business logic
class AgentMetrics:
    @staticmethod
    @logfire.instrument()
    async def track_agent_execution(agent_id: str, task_type: str):
        with logfire.span("agent_execution", agent_id=agent_id, task_type=task_type) as span:
            start_time = time.time()
            try:
                # Agent execution logic here
                duration = time.time() - start_time
                span.set_attribute("duration_ms", duration * 1000)
                span.set_attribute("status", "success")
                
                # Custom metric
                logfire.info(
                    "Agent task completed",
                    agent_id=agent_id,
                    task_type=task_type,
                    duration_ms=duration * 1000,
                    status="success"
                )
            except Exception as e:
                span.set_attribute("status", "error")
                span.set_attribute("error", str(e))
                logfire.error(
                    "Agent task failed",
                    agent_id=agent_id,
                    task_type=task_type,
                    error=str(e)
                )
                raise
```

### 2. Prometheus Metrics (Infrastructure)

```python
# core/prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Infrastructure metrics
REQUEST_COUNT = Counter(
    'agentical_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'agentical_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'agentical_active_connections',
    'Number of active connections'
)

DATABASE_CONNECTIONS = Gauge(
    'agentical_database_connections',
    'Database connection pool status',
    ['pool_name', 'status']
)

REDIS_OPERATIONS = Counter(
    'agentical_redis_operations_total',
    'Redis operations',
    ['operation', 'status']
)

# Middleware for Prometheus metrics
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)
    
    return response

# Start Prometheus metrics server
start_http_server(8001)  # Metrics available at :8001/metrics
```

### 3. Kubernetes ServiceMonitor for Prometheus

```yaml
# monitoring/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: agentical-metrics
  namespace: agentical
  labels:
    app.kubernetes.io/name: agentical
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: agentical
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
  namespaceSelector:
    matchNames:
    - agentical
```

### 4. Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Agentical Infrastructure Overview",
    "panels": [
      {
        "title": "Application Performance (Logfire)",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(agentical_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Infrastructure Health (Prometheus)",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{namespace=\"agentical\"}[5m])",
            "legendFormat": "CPU Usage"
          },
          {
            "expr": "container_memory_usage_bytes{namespace=\"agentical\"} / 1024 / 1024",
            "legendFormat": "Memory Usage (MB)"
          }
        ]
      }
    ]
  }
}
```

## Alert Rules

### Logfire Alerts (Application)
- **High Error Rate**: >5% error rate over 5 minutes
- **Slow Response Time**: P95 latency >2 seconds
- **Agent Task Failures**: >10% task failure rate
- **Database Query Slow**: >1 second average query time

### Prometheus Alerts (Infrastructure)
- **High CPU Usage**: >80% CPU utilization for 10 minutes
- **Memory Pressure**: >90% memory usage for 5 minutes
- **Pod Restart**: Frequent pod restarts (>3 in 10 minutes)
- **Storage Space**: <10% disk space remaining

## Benefits of Hybrid Approach

### ✅ Advantages
1. **Best of Both Worlds**: Application insights + infrastructure monitoring
2. **Cost Optimization**: Logfire for high-value APM, Prometheus for bulk metrics
3. **Reduced Vendor Lock-in**: Prometheus is open-source backup
4. **Developer Experience**: Logfire provides rich debugging context
5. **Operations Team**: Grafana provides familiar infrastructure dashboards

### ⚠️ Considerations
1. **Complexity**: Managing two monitoring systems
2. **Alert Fatigue**: Need careful alert rule coordination
3. **Data Correlation**: Some manual correlation between systems
4. **Learning Curve**: Teams need to understand both tools

## Recommended Alerts Matrix

| Alert Type | Severity | Logfire | Prometheus | Action |
|------------|----------|---------|------------|---------|
| Application Error Rate >5% | Critical | ✅ | | Page on-call |
| Response Time >2s | Warning | ✅ | | Investigate performance |
| Infrastructure CPU >80% | Warning | | ✅ | Scale resources |
| Pod Restart Loop | Critical | | ✅ | Check application logs |
| Database Connection Issues | Critical | ✅ | ✅ | Check DB and connectivity |

## Migration Path

If you want to **simplify to Logfire-only** in the future:

```python
# Enhanced Logfire setup for infrastructure metrics
import psutil
import logfire

# Custom infrastructure metrics via Logfire
def collect_system_metrics():
    logfire.info(
        "System metrics",
        cpu_percent=psutil.cpu_percent(),
        memory_percent=psutil.virtual_memory().percent,
        disk_usage=psutil.disk_usage('/').percent
    )

# Schedule system metrics collection
import asyncio
async def metrics_collector():
    while True:
        collect_system_metrics()
        await asyncio.sleep(30)  # Every 30 seconds
```

This hybrid approach gives you the **best monitoring coverage** while maintaining **cost efficiency** and **operational flexibility**.