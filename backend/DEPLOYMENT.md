# Deployment Guide

## Overview

This guide covers deploying the AI-powered RAG backend to production environments. The application is designed for scalability, reliability, and security in enterprise settings.

## Prerequisites

### System Requirements

**Minimum**:
- CPU: 4 cores
- RAM: 8GB
- Disk: 50GB SSD
- OS: Ubuntu 20.04+ / RHEL 8+ / macOS 10.15+

**Recommended**:
- CPU: 8+ cores
- RAM: 16GB+
- Disk: 100GB+ SSD (more for document storage)
- OS: Ubuntu 22.04 LTS

### Software Requirements

- Python 3.9+
- PostgreSQL 13+ (production database)
- Redis 6+ (caching, optional but recommended)
- Nginx (reverse proxy)
- SSL certificates
- Ollama (optional, for local LLM)

---

## Deployment Options

### 1. Traditional Server Deployment

Deploy directly on a Linux server with systemd.

### 2. Docker Deployment

Containerized deployment with Docker Compose.

### 3. Kubernetes Deployment

Scalable deployment with Kubernetes orchestration.

### 4. Cloud Platforms

Deploy on AWS, Azure, GCP, or other cloud providers.

---

## Traditional Server Deployment

### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.9 python3.9-venv python3-pip \
    postgresql postgresql-contrib nginx git supervisor

# Create application user
sudo useradd -m -s /bin/bash appuser
sudo su - appuser
```

### Step 2: Clone and Setup Application

```bash
# Clone repository
cd /opt
sudo git clone <repository-url> app
sudo chown -R appuser:appuser /opt/app

# Switch to app user
sudo su - appuser
cd /opt/app/backend

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure PostgreSQL

```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
psql
```

```sql
CREATE DATABASE production_db;
CREATE USER appuser WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE production_db TO appuser;
\q
```

```bash
# Configure PostgreSQL for remote connections (if needed)
sudo nano /etc/postgresql/13/main/postgresql.conf
# Set: listen_addresses = '*'

sudo nano /etc/postgresql/13/main/pg_hba.conf
# Add: host production_db appuser 0.0.0.0/0 md5

sudo systemctl restart postgresql
```

### Step 4: Configure Application

```bash
# Create production .env file
cd /opt/app/backend
nano .env
```

```bash
# Production Configuration
DEBUG=false
LOG_LEVEL=WARNING
LOG_FILE=/var/log/app/backend.log

# Database
DATABASE_URL=postgresql://appuser:secure_password@localhost:5432/production_db

# Security
SECRET_KEY=<generate-with-secrets-token_urlsafe>
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=https://app.yourdomain.com

# LLM
CUSTOM_LLM_BASE_URL=https://api.example.com
CUSTOM_LLM_API_KEY=<your-production-key>
CUSTOM_LLM_MODEL=deepseek-v3

# Storage
UPLOAD_DIR=/var/lib/app/uploads
CHROMA_PERSIST_DIR=/var/lib/app/chroma_db

# Server
HOST=127.0.0.1
PORT=8000
```

```bash
# Create directories
sudo mkdir -p /var/lib/app/uploads /var/lib/app/chroma_db /var/log/app
sudo chown -R appuser:appuser /var/lib/app /var/log/app
```

### Step 5: Initialize Database

```bash
cd /opt/app/backend
source venv/bin/activate

# Run migrations
python scripts/initialize_company_databases.py

# Create super admin
python -c "
from app.database.session import get_db_session
from app.database.models import User, Role
from app.auth.security import get_password_hash

with get_db_session() as db:
    role = db.query(Role).filter(Role.name == 'super_admin').first()
    user = User(
        username='admin@yourdomain.com',
        email='admin@yourdomain.com',
        hashed_password=get_password_hash('ChangeThisPassword123!'),
        full_name='Super Admin',
        role_id=role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
"
```

### Step 6: Setup Gunicorn with Systemd

```bash
# Create systemd service
sudo nano /etc/systemd/system/backend.service
```

```ini
[Unit]
Description=AI RAG Backend Service
After=network.target postgresql.service

[Service]
Type=notify
User=appuser
Group=appuser
WorkingDirectory=/opt/app/backend
Environment="PATH=/opt/app/backend/venv/bin"
ExecStart=/opt/app/backend/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 300 \
    --access-logfile /var/log/app/access.log \
    --error-logfile /var/log/app/error.log \
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable backend
sudo systemctl start backend
sudo systemctl status backend
```

### Step 7: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/backend
```

```nginx
upstream backend_server {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # File Upload Size
    client_max_body_size 100M;

    # Timeouts
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;

    location / {
        proxy_pass http://backend_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for future streaming)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://backend_server/health;
        access_log off;
    }

    # Static files (if any)
    location /static {
        alias /opt/app/backend/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal is configured by default
sudo certbot renew --dry-run
```

### Step 9: Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## Docker Deployment

### Dockerfile

**File**: `backend/Dockerfile`

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p /app/uploads /app/chroma_db /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["gunicorn", "main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300"]
```

### Docker Compose

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: backend_postgres
    environment:
      POSTGRES_DB: production_db
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: backend_redis
    volumes:
      - redis_data:/data
    networks:
      - backend_network
    restart: unless-stopped
    command: redis-server --appendonly yes

  backend:
    build: ./backend
    container_name: backend_app
    environment:
      DATABASE_URL: postgresql://appuser:${DB_PASSWORD}@postgres:5432/production_db
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      CUSTOM_LLM_API_KEY: ${CUSTOM_LLM_API_KEY}
      DEBUG: "false"
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/chroma_db:/app/chroma_db
      - ./backend/logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - backend_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: backend_nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    networks:
      - backend_network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  backend_network:
    driver: bridge
```

### Deployment Commands

```bash
# Create .env file
cat > .env << EOF
DB_PASSWORD=secure_db_password
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
CUSTOM_LLM_API_KEY=your_api_key
EOF

# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Stop
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Kubernetes Deployment

### Kubernetes Manifests

**File**: `k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  labels:
    app: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: secret-key
        - name: CUSTOM_LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: llm-api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
        - name: chroma-db
          mountPath: /app/chroma_db
      volumes:
      - name: uploads
        persistentVolumeClaim:
          claimName: uploads-pvc
      - name: chroma-db
        persistentVolumeClaim:
          claimName: chroma-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
stringData:
  database-url: "postgresql://user:pass@postgres:5432/db"
  secret-key: "your-secret-key"
  llm-api-key: "your-llm-key"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: uploads-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 50Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: chroma-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 20Gi
```

### Deploy to Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/backend-deployment

# Scale
kubectl scale deployment/backend-deployment --replicas=5
```

---

## Performance Optimization

### 1. Database Optimization

**PostgreSQL Configuration** (`postgresql.conf`):

```ini
# Connection pooling
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

**Indexes**:

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_company_id ON documents(company_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_agent_logs_user_id ON agent_logs(user_id);
CREATE INDEX idx_token_usage_user_id ON token_usage(user_id);
```

### 2. Caching with Redis

**Install Redis client**:

```bash
pip install redis aioredis
```

**Implement caching**:

```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_result(ttl=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            redis_client.setex(cache_key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl=1800)
async def expensive_query(...):
    ...
```

### 3. Connection Pooling

**Gunicorn workers**:

```bash
# Calculate workers: (2 x CPU cores) + 1
gunicorn main:app \
    --workers 9 \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-connections 1000 \
    --max-requests 10000 \
    --max-requests-jitter 1000
```

### 4. CDN for Static Assets

Use CDN for uploaded documents (if public):

```python
# Configure S3 or CloudFlare for uploads
UPLOAD_URL_PREFIX = "https://cdn.yourdomain.com/uploads/"
```

---

## Monitoring & Observability

### 1. Application Monitoring

**Prometheus + Grafana**:

```bash
# Install prometheus-fastapi-instrumentator
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add metrics endpoint
Instrumentator().instrument(app).expose(app)
```

### 2. Logging

**Structured logging with Loguru**:

```python
from loguru import logger

logger.add(
    "/var/log/app/backend.log",
    rotation="500 MB",
    retention="10 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)
```

### 3. Error Tracking

**Sentry integration**:

```bash
pip install sentry-sdk
```

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)
```

### 4. Health Checks

**Enhanced health endpoint**:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "chromadb": check_chromadb_connection(),
        "llm_provider": check_llm_availability()
    }
```

---

## Security Hardening

### 1. Environment Security

```bash
# Secure .env file
chmod 600 .env
chown appuser:appuser .env

# Use secrets management
# AWS: Secrets Manager
# Azure: Key Vault
# GCP: Secret Manager
```

### 2. Network Security

```bash
# Restrict PostgreSQL access
# Edit pg_hba.conf to allow only app server

# Use private networks
# Backend ← → Database (private)
# Backend ← → Redis (private)
# Backend ← Public (via reverse proxy only)
```

### 3. Rate Limiting

**Implement with slowapi**:

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

### 4. Input Validation

All inputs validated with Pydantic models (already implemented).

### 5. SQL Injection Protection

Using SQLAlchemy ORM (already protected).

---

## Backup & Disaster Recovery

### 1. Database Backups

```bash
# Automated PostgreSQL backups
#!/bin/bash
# /opt/scripts/backup_db.sh

BACKUP_DIR="/var/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql.gz"

# Create backup
pg_dump -U appuser production_db | gzip > $BACKUP_FILE

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE s3://your-bucket/backups/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete
```

```bash
# Add to crontab
crontab -e
# Daily at 2 AM
0 2 * * * /opt/scripts/backup_db.sh
```

### 2. File Backups

```bash
# Backup uploads and ChromaDB
rsync -avz /var/lib/app/ backup-server:/backups/app/
```

### 3. Restore Procedure

```bash
# Restore database
gunzip < backup_20251206_020000.sql.gz | psql -U appuser production_db

# Restore files
rsync -avz backup-server:/backups/app/ /var/lib/app/
```

---

## Scaling Strategies

### Horizontal Scaling

1. **Load Balancer**: Nginx, HAProxy, or cloud load balancer
2. **Multiple App Instances**: Run behind load balancer
3. **Shared Storage**: NFS or S3 for uploads/ChromaDB
4. **Database Read Replicas**: For read-heavy workloads

### Vertical Scaling

1. **Increase Resources**: More CPU, RAM
2. **Optimize Queries**: Add indexes, optimize SQLAlchemy queries
3. **Connection Pooling**: Tune pool sizes

### Microservices Architecture (Future)

1. **Separate Services**:
   - Authentication service
   - Document processing service
   - RAG/Chat service
   - Report generation service
   - Admin service

2. **Message Queue**: RabbitMQ or Kafka for async tasks
3. **API Gateway**: Kong or AWS API Gateway

---

## Troubleshooting

### Common Issues

**Application won't start**:
- Check logs: `journalctl -u backend -f`
- Verify .env configuration
- Check database connectivity
- Ensure ports not in use

**High memory usage**:
- Reduce Gunicorn workers
- Optimize chunk sizes
- Implement caching
- Check for memory leaks

**Slow response times**:
- Check database query performance
- Add indexes
- Enable caching
- Optimize LLM calls
- Scale horizontally

**Database connection errors**:
- Check connection pool size
- Verify credentials
- Check network connectivity
- Look for locked transactions

---

## Maintenance

### Regular Tasks

**Daily**:
- Monitor error logs
- Check disk space
- Review performance metrics

**Weekly**:
- Review security logs
- Check backup integrity
- Update dependencies (if needed)

**Monthly**:
- Security patches
- Performance optimization review
- Capacity planning
- Clean old logs

---

For more information, see:
- [Main Backend Documentation](README.md)
- [Configuration Guide](CONFIGURATION.md)
- [API Documentation](app/api/README.md)
