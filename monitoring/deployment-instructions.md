# Agentical Monitoring Stack Deployment Instructions

## Overview

This deployment guide sets up a comprehensive monitoring stack for Agentical using a **hybrid approach** with **Logfire as the primary observability platform** and **Prometheus/Grafana for infrastructure monitoring**.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Logfire      │    │   Prometheus    │    │     Grafana     │
│   (Primary)     │    │ (Infrastructure)│    │ (Visualization) │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • App Metrics   │    │ • Node Metrics  │    │ • Dashboards    │
│ • Traces        │    │ • K8s Metrics   │    │ • Infrastructure│
│ • Structured    │    │ • Redis Metrics │    │ • Alerts UI     │
│   Logging       │    │ • Long-term     │    │ • Correlation   │
│ • Real-time     │    │   Storage       │    │ • SLI/SLO       │
│   Alerts        │    │ • Cost Metrics  │    │   Tracking      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                        ┌─────────▼─────────┐
                        │  AlertManager     │
                        │  (Unified         │
                        │   Alerting)       │
                        └───────────────────┘
```

## Prerequisites

1. **Kubernetes cluster** (EKS, GKE, or AKS)
2. **Helm 3.x** installed
3. **kubectl** configured for your cluster
4. **Logfire account** and API token
5. **Slack webhook** (optional, for notifications)

## Step 1: Prepare Environment

### Create Monitoring Namespace
```bash
kubectl create namespace monitoring
kubectl label namespace monitoring name=monitoring
```

### Create Secrets
```bash
# Logfire credentials
kubectl create secret generic logfire-credentials \
  --from-literal=token="pylf_v1_us_your_token_here" \
  --from-literal=project-name="agentical-production" \
  -n agentical

# Slack webhook for alerts
kubectl create secret generic alertmanager-slack \
  --from-literal=url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK" \
  -n monitoring

# Email credentials (optional)
kubectl create secret generic alertmanager-email \
  --from-literal=smtp-username="alerts@agentical.com" \
  --from-literal=smtp-password="your-app-password" \
  -n monitoring
```

## Step 2: Deploy Core Monitoring Stack

### Install Prometheus Stack
```bash
# Add Prometheus community Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values monitoring/prometheus-values.yaml \
  --wait
```

### Deploy Additional Components
```bash
# Deploy Loki, Jaeger, and monitoring utilities
kubectl apply -f monitoring/monitoring-stack-deployment.yaml
```

### Install Fluent Bit for Log Collection
```bash
# Add Fluent Helm repository
helm repo add fluent https://fluent.github.io/helm-charts
helm repo update

# Install Fluent Bit
helm install fluent-bit fluent/fluent-bit \
  --namespace logging \
  --create-namespace \
  --values monitoring/fluent-bit-values.yaml \
  --wait
```

## Step 3: Configure Application Monitoring

### Update Agentical Application
Add the Logfire monitoring configuration to your main application:

```python
# In main.py
from core.logfire_monitoring import monitoring, monitoring_lifespan

app = FastAPI(lifespan=monitoring_lifespan)

# Instrument the FastAPI app
app = monitoring.instrument_fastapi(app)
```

### Add Prometheus Metrics Endpoint
```python
# In main.py
from prometheus_client import make_asgi_app

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Add health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}
```

### Deploy Application with Monitoring
```bash
# Apply updated application deployment
kubectl apply -f k8s/deployment.yaml

# Verify metrics endpoints are accessible
kubectl port-forward -n agentical svc/agentical-api 8000:8000 &
curl http://localhost:8000/metrics
curl http://localhost:8000/health
```

## Step 4: Configure Dashboards

### Import Grafana Dashboards
```bash
# Access Grafana (default admin/admin)
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Import custom dashboard
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana-dashboards/agentical-overview.json
```

### Set Up Logfire Dashboards
1. Log into your Logfire account
2. Navigate to **Dashboards** section
3. Create custom dashboards for:
   - Agent performance metrics
   - Task completion rates
   - Error tracking
   - Response time analysis

## Step 5: Configure Alerting

### Verify AlertManager Configuration
```bash
# Check AlertManager status
kubectl get pods -n monitoring -l app.kubernetes.io/name=alertmanager

# View AlertManager configuration
kubectl port-forward -n monitoring svc/prometheus-alertmanager 9093:9093
# Visit http://localhost:9093
```

### Test Alerts
```bash
# Create a test alert
kubectl run test-pod --image=busybox --restart=Never --rm -i --tty -- \
  wget -O- "http://prometheus-alertmanager.monitoring:9093/api/v1/alerts" \
  --post-data='[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test alert"}}]' \
  --header='Content-Type: application/json'
```

## Step 6: Verify Deployment

### Check All Components
```bash
# Check monitoring namespace
kubectl get all -n monitoring

# Check logging namespace
kubectl get all -n logging

# Check application metrics
kubectl get servicemonitors -n monitoring
```

### Verify Data Flow
```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Visit http://localhost:9090/targets

# Check Grafana data sources
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Visit http://localhost:3000

# Check Loki logs
kubectl port-forward -n monitoring svc/loki 3100:3100
# Visit http://localhost:3100/ready
```

## Step 7: Access Monitoring UIs

### Port Forwarding (Development)
```bash
# Grafana Dashboard
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Access: http://localhost:3000 (admin/admin)

# Prometheus UI
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Access: http://localhost:9090

# AlertManager UI
kubectl port-forward -n monitoring svc/prometheus-alertmanager 9093:9093
# Access: http://localhost:9093

# Jaeger UI
kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
# Access: http://localhost:16686
```

### Production Access (Ingress)
```bash
# Apply ingress configuration
kubectl apply -f monitoring/monitoring-stack-deployment.yaml

# Access via configured domains:
# - https://grafana.agentical.com
# - https://jaeger.agentical.com
```

## Step 8: Configure SSL Certificates

### Install cert-manager (if not already installed)
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.13.0 \
  --set installCRDs=true
```

### Create ClusterIssuer
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@agentical.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

## Monitoring Checklist

### ✅ Application Monitoring (Logfire)
- [ ] Logfire token configured
- [ ] FastAPI instrumentation active
- [ ] Database operations tracked
- [ ] Agent execution metrics collected
- [ ] Error tracking enabled
- [ ] Custom business metrics defined

### ✅ Infrastructure Monitoring (Prometheus)
- [ ] Node Exporter collecting system metrics
- [ ] Kubernetes metrics available
- [ ] Redis metrics scraped
- [ ] SurrealDB metrics scraped
- [ ] ServiceMonitors configured
- [ ] Grafana dashboards loaded

### ✅ Logging (Fluent Bit + Loki)
- [ ] Fluent Bit DaemonSet running
- [ ] Application logs collected
- [ ] System logs collected
- [ ] Loki receiving logs
- [ ] Log retention configured

### ✅ Alerting (AlertManager)
- [ ] Alert rules configured
- [ ] Slack notifications working
- [ ] Email notifications configured
- [ ] PagerDuty integration (if needed)
- [ ] Alert routing rules active

### ✅ Tracing (Jaeger)
- [ ] Jaeger collector running
- [ ] Application sending traces
- [ ] Distributed tracing working
- [ ] Trace retention configured

## Troubleshooting

### Common Issues

#### Prometheus Not Scraping Metrics
```bash
# Check ServiceMonitor
kubectl describe servicemonitor agentical-metrics -n monitoring

# Check target endpoints
kubectl get endpoints -n agentical

# Verify metrics endpoint
kubectl exec -it deployment/agentical-api -n agentical -- curl localhost:8001/metrics
```

#### Grafana Dashboard Not Loading
```bash
# Check Grafana logs
kubectl logs -f deployment/prometheus-grafana -n monitoring

# Verify data source connection
kubectl exec -it deployment/prometheus-grafana -n monitoring -- \
  curl http://prometheus-operated:9090/api/v1/query?query=up
```

#### Alerts Not Firing
```bash
# Check AlertManager logs
kubectl logs -f statefulset/alertmanager-prometheus-alertmanager -n monitoring

# Verify alert rules
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Visit http://localhost:9090/alerts
```

#### Logs Not Appearing
```bash
# Check Fluent Bit status
kubectl get pods -n logging -l app.kubernetes.io/name=fluent-bit

# Check Fluent Bit logs
kubectl logs -f daemonset/fluent-bit -n logging

# Verify Loki is receiving logs
kubectl logs -f deployment/loki -n monitoring
```

## Performance Tuning

### Optimize Prometheus
```yaml
# In prometheus-values.yaml
prometheus:
  prometheusSpec:
    # Increase retention for production
    retention: 90d
    retentionSize: 200GB
    
    # Optimize resource allocation
    resources:
      requests:
        cpu: 1000m
        memory: 4Gi
      limits:
        cpu: 4000m
        memory: 16Gi
```

### Optimize Grafana
```yaml
# In prometheus-values.yaml
grafana:
  # Enable persistent storage
  persistence:
    enabled: true
    size: 50Gi
    
  # Optimize for performance
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 2Gi
```

## Maintenance

### Regular Tasks
```bash
# Update Helm charts
helm repo update
helm upgrade prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Clean up old metrics
kubectl exec -it prometheus-prometheus-0 -n monitoring -- \
  promtool tsdb delete-series --path=/prometheus

# Rotate logs
kubectl delete pods -l app.kubernetes.io/name=fluent-bit -n logging
```

### Backup Configuration
```bash
# Backup Grafana dashboards
kubectl get configmaps -n monitoring -o yaml > grafana-backup.yaml

# Backup Prometheus configuration
kubectl get prometheus -n monitoring -o yaml > prometheus-backup.yaml

# Backup AlertManager configuration
kubectl get alertmanager -n monitoring -o yaml > alertmanager-backup.yaml
```

This comprehensive monitoring setup provides production-ready observability for the Agentical platform with automatic alerting, log aggregation, and performance tracking.