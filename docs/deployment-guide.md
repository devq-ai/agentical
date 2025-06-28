# Agentical Platform - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Agentical platform across different environments, from local development to production-scale deployments on cloud platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Platform Deployments](#cloud-platform-deployments)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Security Configuration](#security-configuration)
8. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
9. [Scaling and Performance](#scaling-and-performance)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum Requirements (Development):**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB available space
- OS: Linux, macOS, or Windows with WSL2

**Recommended Requirements (Production):**
- CPU: 16+ cores
- RAM: 32GB+
- Storage: 500GB+ SSD
- Network: High-bandwidth connection with low latency

### Required Software

#### Local Development
- **Docker**: Version 24.0+
- **Docker Compose**: Version 2.20+
- **Python**: Version 3.11+
- **Node.js**: Version 18+
- **Git**: Latest version

#### Production Deployment
- **Kubernetes**: Version 1.28+
- **Helm**: Version 3.12+
- **kubectl**: Compatible with your Kubernetes version
- **Terraform**: Version 1.5+ (for infrastructure as code)

### External Services

#### Required
- **Container Registry**: Docker Hub, AWS ECR, or Google Container Registry
- **Domain Name**: For production deployments
- **SSL Certificates**: Let's Encrypt or commercial certificates

#### Optional but Recommended
- **Logfire Account**: For observability and monitoring
- **Slack Workspace**: For alert notifications
- **Email Service**: SMTP server for notifications
- **PagerDuty**: For critical incident management

---

## Local Development Setup

### Quick Start with Docker Compose

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/agentical.git
   cd agentical
   ```

2. **Create Environment Configuration**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration:
   ```env
   # Application Configuration
   ENVIRONMENT=development
   DEBUG=true
   SECRET_KEY=your-secret-key-here
   
   # Database Configuration
   SURREALDB_URL=ws://surrealdb:8000/rpc
   SURREALDB_USERNAME=root
   SURREALDB_PASSWORD=root
   SURREALDB_NAMESPACE=agentical
   SURREALDB_DATABASE=development
   
   # Redis Configuration
   REDIS_URL=redis://redis:6379
   
   # Monitoring (Optional)
   LOGFIRE_TOKEN=your-logfire-token
   LOGFIRE_PROJECT_NAME=agentical-development
   
   # External APIs
   ANTHROPIC_API_KEY=your-anthropic-api-key
   OPENAI_API_KEY=your-openai-api-key
   ```

3. **Start Development Environment**
   ```bash
   docker-compose up -d
   ```

4. **Verify Installation**
   ```bash
   # Check service status
   docker-compose ps
   
   # Check application health
   curl http://localhost:8000/health
   
   # Check frontend
   curl http://localhost:3000
   ```

5. **Access Services**
   - **API**: http://localhost:8000
   - **Frontend**: http://localhost:3000
   - **API Documentation**: http://localhost:8000/docs
   - **SurrealDB Studio**: http://localhost:8080

### Development Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Main API Service
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
      - "8001:8001"  # Metrics port
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - SURREALDB_URL=ws://surrealdb:8000/rpc
      - REDIS_URL=redis://redis:6379
    volumes:
      - .:/app
      - ./data:/app/data
    depends_on:
      - surrealdb
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Frontend Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - api
    restart: unless-stopped

  # SurrealDB Database
  surrealdb:
    image: surrealdb/surrealdb:latest
    command: start --log info --user root --pass root file:/data/database.db
    ports:
      - "8080:8000"  # SurrealDB Studio
    volumes:
      - surrealdb_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Development Tools
  redis-commander:
    image: rediscommander/redis-commander:latest
    ports:
      - "8081:8081"
    environment:
      - REDIS_HOSTS=local:redis:6379
    depends_on:
      - redis
    profiles:
      - tools

volumes:
  surrealdb_data:
  redis_data:

networks:
  default:
    name: agentical-dev
```

### Development Dockerfile

```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development command with hot reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## Docker Deployment

### Production Docker Images

#### API Service Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

#### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - web_static:/var/www/html:ro
    depends_on:
      - api
      - frontend
    restart: unless-stopped
    networks:
      - agentical-network

  # API Service
  api:
    image: agentical/api:${VERSION:-latest}
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - SECRET_KEY=${SECRET_KEY}
      - SURREALDB_URL=ws://surrealdb:8000/rpc
      - REDIS_URL=redis://redis:6379
      - LOGFIRE_TOKEN=${LOGFIRE_TOKEN}
    volumes:
      - api_data:/app/data
    depends_on:
      - surrealdb
      - redis
    restart: unless-stopped
    networks:
      - agentical-network
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  # Frontend Service
  frontend:
    image: agentical/frontend:${VERSION:-latest}
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    restart: unless-stopped
    networks:
      - agentical-network
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  # Database
  surrealdb:
    image: surrealdb/surrealdb:latest
    command: start --log info --user ${SURREALDB_USERNAME} --pass ${SURREALDB_PASSWORD} file:/data/database.db
    volumes:
      - surrealdb_data:/data
    restart: unless-stopped
    networks:
      - agentical-network
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

  # Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - agentical-network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - agentical-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    restart: unless-stopped
    networks:
      - agentical-network

volumes:
  surrealdb_data:
  redis_data:
  api_data:
  web_static:
  prometheus_data:
  grafana_data:

networks:
  agentical-network:
    driver: bridge
```

### Nginx Configuration

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=web:10m rate=2r/s;
    
    # Include server configurations
    include /etc/nginx/conf.d/*.conf;
}
```

```nginx
# nginx/conf.d/agentical.conf
# Upstream servers
upstream api_backend {
    least_conn;
    server api:8000 max_fails=3 fail_timeout=30s;
}

upstream frontend_backend {
    least_conn;
    server frontend:3000 max_fails=3 fail_timeout=30s;
}

# HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# Main application server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/yourdomain.com.crt;
    ssl_certificate_key /etc/nginx/ssl/yourdomain.com.key;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    
    # Modern configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # API routes
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }
    
    # WebSocket support for real-time updates
    location /ws/ {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket specific timeouts
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
    
    # Frontend routes
    location / {
        limit_req zone=web burst=10 nodelay;
        
        proxy_pass http://frontend_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://api_backend/health;
        proxy_set_header Host $host;
    }
}

# API subdomain
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration (same as above)
    ssl_certificate /etc/nginx/ssl/yourdomain.com.crt;
    ssl_certificate_key /etc/nginx/ssl/yourdomain.com.key;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Kubernetes Deployment

### Namespace and RBAC

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agentical
  labels:
    name: agentical
    app.kubernetes.io/name: agentical
    app.kubernetes.io/part-of: agentical-platform
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: agentical-api
  namespace: agentical
  labels:
    app.kubernetes.io/name: agentical-api
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: agentical
  name: agentical-api
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: agentical-api
  namespace: agentical
subjects:
- kind: ServiceAccount
  name: agentical-api
  namespace: agentical
roleRef:
  kind: Role
  name: agentical-api
  apiGroup: rbac.authorization.k8s.io
```

### ConfigMaps and Secrets

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agentical-config
  namespace: agentical
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  SURREALDB_URL: "ws://surrealdb:8000/rpc"
  SURREALDB_NAMESPACE: "agentical"
  SURREALDB_DATABASE: "production"
  REDIS_URL: "redis://redis:6379"
  LOGFIRE_PROJECT_NAME: "agentical-production"
  RATE_LIMIT_REQUESTS: "1000"
  RATE_LIMIT_WINDOW: "60"
---
apiVersion: v1
kind: Secret
metadata:
  name: agentical-secrets
  namespace: agentical
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret-key>
  SURREALDB_USERNAME: <base64-encoded-username>
  SURREALDB_PASSWORD: <base64-encoded-password>
  REDIS_PASSWORD: <base64-encoded-redis-password>
  LOGFIRE_TOKEN: <base64-encoded-logfire-token>
  ANTHROPIC_API_KEY: <base64-encoded-anthropic-key>
  OPENAI_API_KEY: <base64-encoded-openai-key>
```

### Database Deployments

```yaml
# k8s/surrealdb.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: surrealdb
  namespace: agentical
  labels:
    app.kubernetes.io/name: surrealdb
spec:
  serviceName: surrealdb
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: surrealdb
  template:
    metadata:
      labels:
        app.kubernetes.io/name: surrealdb
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
      - name: surrealdb
        image: surrealdb/surrealdb:latest
        args:
        - start
        - --log=info
        - --user=$(SURREALDB_USERNAME)
        - --pass=$(SURREALDB_PASSWORD)
        - file:/data/database.db
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: SURREALDB_USERNAME
          valueFrom:
            secretKeyRef:
              name: agentical-secrets
              key: SURREALDB_USERNAME
        - name: SURREALDB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: agentical-secrets
              key: SURREALDB_PASSWORD
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: surrealdb
  namespace: agentical
  labels:
    app.kubernetes.io/name: surrealdb
spec:
  selector:
    app.kubernetes.io/name: surrealdb
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  clusterIP: None
```

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: agentical
  labels:
    app.kubernetes.io/name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: redis
  template:
    metadata:
      labels:
        app.kubernetes.io/name: redis
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 999
        fsGroup: 999
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - --appendonly
        - "yes"
        - --requirepass
        - $(REDIS_PASSWORD)
        ports:
        - containerPort: 6379
          name: redis
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: agentical-secrets
              key: REDIS_PASSWORD
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 1Gi
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: redis-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-data
  namespace: agentical
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: agentical
  labels:
    app.kubernetes.io/name: redis
spec:
  selector:
    app.kubernetes.io/name: redis
  ports:
  - port: 6379
    targetPort: 6379
    name: redis
  type: ClusterIP
```

### Application Deployment

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentical-api
  namespace: agentical
  labels:
    app.kubernetes.io/name: agentical-api
    app.kubernetes.io/version: "1.0.0"
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app.kubernetes.io/name: agentical-api
  template:
    metadata:
      labels:
        app.kubernetes.io/name: agentical-api
        app.kubernetes.io/version: "1.0.0"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8001"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: agentical-api
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
      - name: api
        image: agentical/api:1.0.0
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 8001
          name: metrics
        envFrom:
        - configMapRef:
            name: agentical-config
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: agentical-secrets
              key: SECRET_KEY
        - name: SURREALDB_USERNAME
          valueFrom:
            secretKeyRef:
              name: agentical-secrets
              key: SURREALDB_USERNAME
        - name: SURREALDB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: agentical-secrets
              key: SURREALDB_PASSWORD
        - name: LOGFIRE_TOKEN
          valueFrom:
            secretKeyRef:
              name: agentical-secrets
              key: LOGFIRE_TOKEN
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: temp
          mountPath: /tmp
      volumes:
      - name: temp
        emptyDir:
          sizeLimit: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: agentical-api
  namespace: agentical
  labels:
    app.kubernetes.io/name: agentical-api
spec:
  selector:
    app.kubernetes.io/name: agentical-api
  ports:
  - name: http
    port: 8000
    targetPort: 8000
  - name: metrics
    port: 8001
    targetPort: 8001
  type: ClusterIP
```

### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agentical-ingress
  namespace: agentical
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Frame-Options: DENY";
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "X-XSS-Protection: 1; mode=block";
      more_set_headers "Strict-Transport-Security: max-age=31536000; includeSubDomains";
spec:
  tls:
  - hosts:
    - agentical.yourdomain.com
    - api.agentical.yourdomain.com
    secretName: agentical-tls
  rules:
  - host: agentical.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: agentical-api
            port:
              number: 8000
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: agentical-api
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agentical-frontend
            port:
              number: 3000
  - host: api.agentical.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agentical-api
            port:
              number: 8000
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agentical-api-hpa
  namespace: agentical
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agentical-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 2
        periodSeconds: 60
```

### Pod Disruption Budget

```yaml
# k8s/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: agentical-api-pdb
  namespace: agentical
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: agentical-api
  maxUnavailable: 1
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: surrealdb-pdb
  namespace: agentical
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: surrealdb
  maxUnavailable: 0
```

### Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

# Configuration
NAMESPACE="agentical"
VERSION=${1:-"latest"}
ENVIRONMENT=${2:-"production"}

echo "🚀 Deploying Agentical Platform v${VERSION} to ${ENVIRONMENT}"

# Check prerequisites
echo "📋 Checking prerequisites..."
kubectl cluster-info >/dev/null 2>&1 || { echo "❌ kubectl not configured"; exit 1; }
helm version >/dev/null 2>&1 || { echo "❌ helm not installed"; exit 1; }

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Apply secrets (should be created separately in production)
echo "🔐 Applying secrets..."
if [ "$ENVIRONMENT" = "development" ]; then
    kubectl apply -f k8s/secrets-dev.yaml
else
    echo "⚠️  Please ensure secrets are created manually in production"
fi

# Apply configurations
echo "⚙️  Applying configurations..."
kubectl apply -f k8s/configmap.yaml

# Deploy databases
echo "🗄️  Deploying databases..."
kubectl apply -f k8s/surrealdb.yaml
kubectl apply -f k8s/redis.yaml

# Wait for databases to be ready
echo "⏳ Waiting for databases..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=surrealdb -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n $NAMESPACE --timeout=300s

# Deploy applications
echo "🚀 Deploying applications..."
# Update image tags
sed -i.bak "s|image: agentical/api:.*|image: agentical/api:${VERSION}|g" k8s/api-deployment.yaml
sed -i.bak "s|image: agentical/frontend:.*|image: agentical/frontend:${VERSION}|g" k8s/frontend-deployment.yaml

kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Apply autoscaling
echo "📊 Applying autoscaling..."
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml

# Apply ingress
echo "🌐 Applying ingress..."
kubectl apply -f k8s/ingress.yaml

# Wait for deployment rollout
echo "⏳ Waiting for deployments..."
kubectl rollout status deployment/agentical-api -n $NAMESPACE --timeout=600s
kubectl rollout status deployment/agentical-frontend -n $NAMESPACE --timeout=600s

# Verify deployment
echo "✅ Verifying deployment..."
API_POD=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=agentical-api --output=jsonpath='{.items[0].metadata.name}')
kubectl exec -n $NAMESPACE $API_POD -- curl -f http://localhost:8000/health

echo "🎉 Deployment completed successfully!"
echo "📝 Next steps:"
echo "   - Configure DNS to point to your ingress"
echo "   - Verify SSL certificates"
echo "   - Check monitoring dashboards"
echo "   - Run integration tests"

# Display useful information
echo "📋 Deployment Information:"
echo "   Namespace: $NAMESPACE"
echo "   Version: $VERSION"
echo "   Environment: $ENVIRONMENT"
echo "   API URL: https://api.agentical.yourdomain.com"
echo "   Frontend URL: https://agentical.yourdomain.com"
```

This deployment guide provides comprehensive instructions for deploying Agentical across different environments. The next sections will cover cloud-specific deployments, monitoring, security, and operational procedures.
