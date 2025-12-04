# Production Deployment Guide

This guide covers deploying the RAG & Multi-Agent AI System to production environments.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Security Hardening](#security-hardening)
5. [Web Server Configuration](#web-server-configuration)
6. [Process Management](#process-management)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup Strategies](#backup-strategies)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance](#maintenance)

---

## Pre-Deployment Checklist

Before deploying to production, ensure the following:

### Security
- [ ] Change `SECRET_KEY` to a cryptographically secure random string
- [ ] Set `DEBUG = False` in production
- [ ] Configure proper CORS origins (no wildcards)
- [ ] Review and update all default passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up API rate limiting
- [ ] Review and restrict file upload permissions
- [ ] Secure environment variables (use secrets management)

### Performance
- [ ] Migrate from SQLite to PostgreSQL
- [ ] Configure connection pooling
- [ ] Set up Redis for caching (optional)
- [ ] Optimize ChromaDB persistence
- [ ] Configure proper worker counts
- [ ] Set up CDN for static files (if applicable)

### Reliability
- [ ] Set up automated backups
- [ ] Configure health checks
- [ ] Implement logging and monitoring
- [ ] Set up alerting
- [ ] Configure automatic restarts
- [ ] Test disaster recovery procedures

### Compliance
- [ ] Review data retention policies
- [ ] Ensure GDPR/privacy compliance
- [ ] Document API usage policies
- [ ] Set up audit logging
- [ ] Review license compliance

---

## Environment Setup

### 1. Server Requirements

**Minimum Specifications:**
- **CPU:** 4 cores
- **RAM:** 8GB (16GB recommended)
- **Storage:** 50GB SSD
- **OS:** Ubuntu 22.04 LTS or similar

**Recommended Specifications:**
- **CPU:** 8+ cores
- **RAM:** 32GB
- **Storage:** 200GB NVMe SSD
- **OS:** Ubuntu 22.04 LTS

### 2. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install system dependencies
sudo apt install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    redis-tools \
    nginx \
    supervisor \
    poppler-utils \
    tesseract-ocr

# Install monitoring tools
sudo apt install -y htop iotop netdata
```

### 3. Application Setup

```bash
# Create application user
sudo useradd -r -s /bin/bash -m -d /opt/rag-system rag

# Clone repository
sudo -u rag git clone <repository-url> /opt/rag-system/app
cd /opt/rag-system/app/backend

# Create virtual environment
sudo -u rag python3.10 -m venv /opt/rag-system/venv

# Install dependencies
sudo -u rag /opt/rag-system/venv/bin/pip install --upgrade pip
sudo -u rag /opt/rag-system/venv/bin/pip install -r requirements.txt

# Production dependencies
sudo -u rag /opt/rag-system/venv/bin/pip install \
    gunicorn \
    uvicorn[standard] \
    psycopg2-binary \
    sentry-sdk[fastapi]
```

### 4. Environment Configuration

```bash
# Create .env file
sudo -u rag nano /opt/rag-system/app/backend/.env
```

**Production .env:**

```bash
# Application
APP_NAME="RAG Multi-Agent System"
DEBUG=False
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["https://yourdomain.com","https://api.yourdomain.com"]

# Database - PostgreSQL
DATABASE_URL=postgresql://rag_user:SECURE_PASSWORD@localhost:5432/rag_production

# JWT - CRITICAL: Generate new secret key
SECRET_KEY="<GENERATE_CRYPTOGRAPHICALLY_SECURE_KEY_HERE>"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Custom LLM API
CUSTOM_LLM_BASE_URL=https://genailab.tcs.in
CUSTOM_LLM_MODEL=azure_ai/genailab-maas-DeepSeek-V3-0324
CUSTOM_LLM_API_KEY="YOUR_API_KEY_HERE"
CUSTOM_EMBEDDING_MODEL=azure/genailab-maas-text-embedding-3-large
CUSTOM_VISION_MODEL=azure_ai/genailab-maas-Llama-3.2-90B-Vision-Instruct

# Ollama (Optional - for local fallback)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_VISION_MODEL=llama3.2-vision

# ChromaDB
CHROMA_PERSIST_DIR=/opt/rag-system/data/chroma_db
CHROMA_COLLECTION_NAME=rag_documents

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIEVAL_DOCS=5
SIMILARITY_THRESHOLD=0.01

# Agents
MAX_AGENT_ITERATIONS=10
AGENT_TEMPERATURE=0.7
ENABLE_AGENT_MEMORY=True

# Explainability
EXPLAINABILITY_LEVEL=detailed
ENABLE_CONFIDENCE_SCORING=True
ENABLE_SOURCE_ATTRIBUTION=True
ENABLE_REASONING_CHAINS=True

# File Upload
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=[".pdf",".txt",".csv",".docx"]
UPLOAD_DIR=/opt/rag-system/data/uploads

# OCR
OCR_SUPPORTED_FORMATS=[".jpg",".jpeg",".png",".pdf",".tiff",".tif",".bmp",".webp"]
OCR_MAX_FILE_SIZE=20971520
OCR_IMAGE_MAX_DIMENSION=2048
OCR_CONFIDENCE_THRESHOLD=0.7
OCR_ENABLE_PREPROCESSING=True
OCR_PDF_DPI=300

# Monitoring (Optional - Sentry)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/rag-system/logs/app.log
```

**Generate Secure Secret Key:**

```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Create Data Directories

```bash
# Create directories
sudo -u rag mkdir -p /opt/rag-system/data/{chroma_db,uploads,backups}
sudo -u rag mkdir -p /opt/rag-system/logs

# Set permissions
sudo chmod 755 /opt/rag-system/data
sudo chmod 700 /opt/rag-system/data/uploads
sudo chmod 755 /opt/rag-system/logs
```

---

## Database Configuration

### PostgreSQL Setup

#### 1. Install PostgreSQL

```bash
# Install PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib-15 -y

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2. Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In psql:
CREATE DATABASE rag_production;
CREATE USER rag_user WITH PASSWORD 'SECURE_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE rag_production TO rag_user;

# PostgreSQL 15+ requires additional grants
\c rag_production
GRANT ALL ON SCHEMA public TO rag_user;

\q
```

#### 3. Configure PostgreSQL

Edit `/etc/postgresql/15/main/postgresql.conf`:

```ini
# Connection Settings
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h '
log_timezone = 'UTC'
```

Edit `/etc/postgresql/15/main/pg_hba.conf`:

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             rag_user                                md5
host    all             rag_user        127.0.0.1/32            md5
host    all             rag_user        ::1/128                 md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

#### 4. Initialize Database Schema

```bash
cd /opt/rag-system/app/backend

# Run database migrations (if using Alembic)
sudo -u rag /opt/rag-system/venv/bin/python -m alembic upgrade head

# Or run application to create tables
sudo -u rag /opt/rag-system/venv/bin/python main.py
# Stop after tables are created (Ctrl+C)
```

#### 5. Create Initial Admin User

```bash
# Create admin user script
sudo -u rag nano /opt/rag-system/app/backend/scripts/create_admin.py
```

**create_admin.py:**

```python
#!/usr/bin/env python3
"""Create initial admin user."""
import sys
sys.path.insert(0, '/opt/rag-system/app/backend')

from app.database.db import get_db
from app.database.models import User, Role
from app.auth.security import get_password_hash

def create_admin():
    db = next(get_db())

    # Check if admin exists
    existing_admin = db.query(User).filter(User.email == "admin@yourdomain.com").first()
    if existing_admin:
        print("Admin user already exists")
        return

    # Get admin role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        print("Admin role not found - create roles first")
        return

    # Create admin user
    admin = User(
        username="admin",
        email="admin@yourdomain.com",
        hashed_password=get_password_hash("CHANGE_THIS_PASSWORD"),
        preferred_llm="custom_api",
        explainability_level="detailed",
        is_active=True
    )
    admin.roles.append(admin_role)

    db.add(admin)
    db.commit()
    print(f"Admin user created: {admin.email}")
    print("IMPORTANT: Change the password immediately!")

if __name__ == "__main__":
    create_admin()
```

```bash
# Run script
sudo -u rag /opt/rag-system/venv/bin/python /opt/rag-system/app/backend/scripts/create_admin.py
```

### Connection Pooling

For high-traffic applications, configure connection pooling in SQLAlchemy:

**app/database/db.py:**

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # Number of persistent connections
    max_overflow=40,       # Max extra connections
    pool_timeout=30,       # Timeout for getting connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True,    # Verify connection before using
    echo=False             # Disable SQL logging in production
)
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (adjust port if needed)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL only from localhost
sudo ufw allow from 127.0.0.1 to any port 5432

# Check status
sudo ufw status
```

### 2. SSL/TLS Configuration

#### Option A: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

#### Option B: Self-Signed Certificate (Development)

```bash
# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/rag-selfsigned.key \
    -out /etc/ssl/certs/rag-selfsigned.crt
```

### 3. Rate Limiting

Install `slowapi` for rate limiting:

```bash
sudo -u rag /opt/rag-system/venv/bin/pip install slowapi
```

**app/main.py:**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@app.post("/chat/message")
@limiter.limit("10/minute")  # 10 requests per minute
async def send_message(...):
    pass
```

### 4. API Key Authentication (Optional)

For API access, implement API key authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY = "your-secure-api-key"
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

### 5. CORS Configuration

**Production CORS:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://api.yourdomain.com"
    ],  # No wildcards in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)
```

### 6. Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## Web Server Configuration

### Nginx Configuration

#### 1. Install Nginx

```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 2. Configure Reverse Proxy

Create `/etc/nginx/sites-available/rag-system`:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/m;
limit_conn_zone $binary_remote_addr zone=addr:10m;

# Upstream
upstream rag_backend {
    server 127.0.0.1:8000 fail_timeout=0;
    # Add more workers for load balancing:
    # server 127.0.0.1:8001 fail_timeout=0;
    # server 127.0.0.1:8002 fail_timeout=0;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com api.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com api.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/rag-access.log combined;
    error_log /var/log/nginx/rag-error.log warn;

    # Max body size for file uploads
    client_max_body_size 25M;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Rate limiting
    limit_req zone=api_limit burst=5 nodelay;
    limit_conn addr 10;

    # Proxy to FastAPI
    location / {
        proxy_pass http://rag_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for SSE)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/rag-system/app/backend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint (no rate limiting)
    location /health {
        limit_req off;
        limit_conn off;
        proxy_pass http://rag_backend;
        access_log off;
    }
}
```

#### 3. Enable Configuration

```bash
# Test configuration
sudo nginx -t

# Enable site
sudo ln -s /etc/nginx/sites-available/rag-system /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Reload Nginx
sudo systemctl reload nginx
```

---

## Process Management

### Option A: Systemd (Recommended)

#### 1. Create Systemd Service

Create `/etc/systemd/system/rag-system.service`:

```ini
[Unit]
Description=RAG Multi-Agent System
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=rag
Group=rag
WorkingDirectory=/opt/rag-system/app/backend
Environment="PATH=/opt/rag-system/venv/bin"
ExecStart=/opt/rag-system/venv/bin/gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile /opt/rag-system/logs/access.log \
    --error-logfile /opt/rag-system/logs/error.log \
    --log-level info \
    main:app

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=0

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Security hardening
PrivateTmp=true
NoNewPrivileges=true
ReadWritePaths=/opt/rag-system/data /opt/rag-system/logs

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable rag-system

# Start service
sudo systemctl start rag-system

# Check status
sudo systemctl status rag-system

# View logs
sudo journalctl -u rag-system -f
```

#### 3. Service Management Commands

```bash
# Start
sudo systemctl start rag-system

# Stop
sudo systemctl stop rag-system

# Restart
sudo systemctl restart rag-system

# Reload (graceful)
sudo systemctl reload rag-system

# Status
sudo systemctl status rag-system

# Logs
sudo journalctl -u rag-system --since "1 hour ago"
```

### Option B: Supervisor

#### 1. Install Supervisor

```bash
sudo apt install supervisor -y
```

#### 2. Create Supervisor Configuration

Create `/etc/supervisor/conf.d/rag-system.conf`:

```ini
[program:rag-system]
command=/opt/rag-system/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 4 --bind 127.0.0.1:8000 main:app
directory=/opt/rag-system/app/backend
user=rag
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/rag-system/logs/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/rag-system/venv/bin"
```

#### 3. Enable and Start

```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Start
sudo supervisorctl start rag-system

# Status
sudo supervisorctl status rag-system
```

### Worker Count Configuration

Calculate optimal worker count:

```bash
# Formula: (2 x CPU cores) + 1
# For 4 CPU cores: (2 x 4) + 1 = 9 workers

# Update service with calculated workers
-w 9
```

---

## Monitoring & Logging

### 1. Application Logging

**Configure structured logging in `app/main.py`:**

```python
import logging
import sys
from logging.handlers import RotatingFileHandler
import json

# JSON log formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_system")

# File handler
file_handler = RotatingFileHandler(
    "/opt/rag-system/logs/app.log",
    maxBytes=50*1024*1024,  # 50MB
    backupCount=10
)
file_handler.setFormatter(JsonFormatter())
logger.addHandler(file_handler)

# Console handler (for systemd)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(JsonFormatter())
logger.addHandler(console_handler)
```

### 2. Error Tracking with Sentry

```bash
# Install Sentry SDK
sudo -u rag /opt/rag-system/venv/bin/pip install sentry-sdk[fastapi]
```

**app/main.py:**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

if not settings.DEBUG and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        environment="production"
    )
```

### 3. Health Check Endpoint

**app/api/v1/health.py:**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services.vector_store import get_vector_store
import time

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring.

    Returns:
        - status: ok/degraded/error
        - checks: individual component health
        - timestamp: current time
    """
    checks = {}
    overall_status = "ok"

    # Database check
    try:
        db.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        overall_status = "error"

    # ChromaDB check
    try:
        vector_store = get_vector_store()
        vector_store.get_collection()
        checks["vector_store"] = "ok"
    except Exception as e:
        checks["vector_store"] = f"error: {str(e)}"
        overall_status = "degraded"

    # Disk space check
    import shutil
    disk = shutil.disk_usage("/opt/rag-system")
    disk_usage_percent = (disk.used / disk.total) * 100
    if disk_usage_percent > 90:
        checks["disk"] = f"warning: {disk_usage_percent:.1f}% used"
        overall_status = "degraded"
    else:
        checks["disk"] = f"ok: {disk_usage_percent:.1f}% used"

    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": time.time()
    }
```

### 4. Monitoring with Prometheus (Optional)

```bash
# Install prometheus client
sudo -u rag /opt/rag-system/venv/bin/pip install prometheus-fastapi-instrumentator
```

**app/main.py:**

```python
from prometheus_fastapi_instrumentator import Instrumentator

# Initialize instrumentator
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics")
```

### 5. Log Rotation

Create `/etc/logrotate.d/rag-system`:

```
/opt/rag-system/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 rag rag
    sharedscripts
    postrotate
        systemctl reload rag-system > /dev/null 2>&1 || true
    endscript
}
```

### 6. Monitoring Dashboard Setup

For a quick monitoring dashboard, use Netdata:

```bash
# Install Netdata
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Configure Netdata to monitor the application
sudo nano /etc/netdata/python.d/web_log.conf
```

Access dashboard at: http://your-server-ip:19999

---

## Backup Strategies

### 1. Database Backups

#### Automated PostgreSQL Backups

Create `/opt/rag-system/scripts/backup-database.sh`:

```bash
#!/bin/bash
# PostgreSQL backup script

# Configuration
BACKUP_DIR="/opt/rag-system/data/backups"
DB_NAME="rag_production"
DB_USER="rag_user"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup filename with timestamp
BACKUP_FILE="$BACKUP_DIR/rag_db_$(date +%Y%m%d_%H%M%S).sql.gz"

# Create backup
PGPASSWORD="YOUR_DB_PASSWORD" pg_dump \
    -U "$DB_USER" \
    -h localhost \
    -F c \
    "$DB_NAME" | gzip > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"

    # Remove old backups
    find "$BACKUP_DIR" -name "rag_db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

    # Log success
    logger -t rag-backup "Database backup completed successfully"
else
    echo "Backup failed!"
    logger -t rag-backup "Database backup FAILED"
    exit 1
fi

# Upload to remote storage (optional)
# aws s3 cp "$BACKUP_FILE" s3://your-bucket/backups/
```

Make executable and schedule:

```bash
# Make executable
sudo chmod +x /opt/rag-system/scripts/backup-database.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e -u rag
```

Add line:
```
0 2 * * * /opt/rag-system/scripts/backup-database.sh >> /opt/rag-system/logs/backup.log 2>&1
```

### 2. ChromaDB Backups

Create `/opt/rag-system/scripts/backup-chroma.sh`:

```bash
#!/bin/bash
# ChromaDB backup script

CHROMA_DIR="/opt/rag-system/data/chroma_db"
BACKUP_DIR="/opt/rag-system/data/backups"
RETENTION_DAYS=30

# Create backup
BACKUP_FILE="$BACKUP_DIR/chroma_$(date +%Y%m%d_%H%M%S).tar.gz"

tar -czf "$BACKUP_FILE" -C "$(dirname $CHROMA_DIR)" "$(basename $CHROMA_DIR)"

if [ $? -eq 0 ]; then
    echo "ChromaDB backup successful: $BACKUP_FILE"

    # Remove old backups
    find "$BACKUP_DIR" -name "chroma_*.tar.gz" -mtime +$RETENTION_DAYS -delete

    logger -t rag-backup "ChromaDB backup completed successfully"
else
    echo "ChromaDB backup failed!"
    logger -t rag-backup "ChromaDB backup FAILED"
    exit 1
fi
```

### 3. File Uploads Backup

```bash
#!/bin/bash
# Uploads backup script

UPLOADS_DIR="/opt/rag-system/data/uploads"
BACKUP_DIR="/opt/rag-system/data/backups"
RETENTION_DAYS=30

BACKUP_FILE="$BACKUP_DIR/uploads_$(date +%Y%m%d_%H%M%S).tar.gz"

tar -czf "$BACKUP_FILE" -C "$(dirname $UPLOADS_DIR)" "$(basename $UPLOADS_DIR)"

if [ $? -eq 0 ]; then
    echo "Uploads backup successful: $BACKUP_FILE"
    find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +$RETENTION_DAYS -delete
else
    echo "Uploads backup failed!"
    exit 1
fi
```

### 4. Complete Backup Script

Create `/opt/rag-system/scripts/backup-all.sh`:

```bash
#!/bin/bash
# Complete backup script

echo "Starting complete backup..."

# Run all backups
/opt/rag-system/scripts/backup-database.sh
/opt/rag-system/scripts/backup-chroma.sh
/opt/rag-system/scripts/backup-uploads.sh

# Sync to remote storage (optional)
# rsync -avz /opt/rag-system/data/backups/ user@backup-server:/backups/rag-system/

echo "Complete backup finished"
```

### 5. Restore Procedures

#### Database Restore

```bash
# Stop application
sudo systemctl stop rag-system

# Restore database
gunzip < /path/to/backup.sql.gz | \
PGPASSWORD="YOUR_DB_PASSWORD" pg_restore \
    -U rag_user \
    -h localhost \
    -d rag_production \
    --clean \
    --if-exists

# Start application
sudo systemctl start rag-system
```

#### ChromaDB Restore

```bash
# Stop application
sudo systemctl stop rag-system

# Remove existing ChromaDB
sudo -u rag rm -rf /opt/rag-system/data/chroma_db

# Extract backup
sudo -u rag tar -xzf /path/to/chroma_backup.tar.gz \
    -C /opt/rag-system/data/

# Start application
sudo systemctl start rag-system
```

---

## Scaling

### Horizontal Scaling

#### 1. Multiple Application Instances

Run multiple Gunicorn instances on different ports:

**/etc/systemd/system/rag-system@.service:**

```ini
[Unit]
Description=RAG System Instance %i
After=network.target postgresql.service

[Service]
Type=notify
User=rag
Group=rag
WorkingDirectory=/opt/rag-system/app/backend
Environment="PATH=/opt/rag-system/venv/bin"
ExecStart=/opt/rag-system/venv/bin/gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    --bind 127.0.0.1:800%i \
    --timeout 120 \
    main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start multiple instances:

```bash
sudo systemctl start rag-system@0  # Port 8000
sudo systemctl start rag-system@1  # Port 8001
sudo systemctl start rag-system@2  # Port 8002
```

Update Nginx upstream:

```nginx
upstream rag_backend {
    least_conn;  # Load balancing algorithm
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
}
```

#### 2. Database Connection Pooling

Use PgBouncer for PostgreSQL connection pooling:

```bash
# Install PgBouncer
sudo apt install pgbouncer -y

# Configure /etc/pgbouncer/pgbouncer.ini
[databases]
rag_production = host=127.0.0.1 port=5432 dbname=rag_production

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 25
```

Update application DATABASE_URL:
```
DATABASE_URL=postgresql://rag_user:password@localhost:6432/rag_production
```

#### 3. Redis for Caching (Optional)

```bash
# Install Redis
sudo apt install redis-server -y

# Configure for production
sudo nano /etc/redis/redis.conf
```

```ini
# /etc/redis/redis.conf
bind 127.0.0.1
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

Integrate Redis caching:

```python
import redis
from functools import wraps
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(ttl=300):
    """Cache decorator with TTL in seconds."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            redis_client.setex(cache_key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator
```

### Vertical Scaling

#### Optimize Resource Limits

**/etc/systemd/system/rag-system.service:**

```ini
[Service]
# Increase file descriptors
LimitNOFILE=65536

# Increase process limit
LimitNPROC=8192

# Memory limits (optional)
MemoryMax=8G
MemoryHigh=6G
```

#### PostgreSQL Tuning

Use `pg tune` for recommendations:

```bash
# Install pgtune
pip install pgtune

# Generate config
pgtune -i /etc/postgresql/15/main/postgresql.conf \
    -o /etc/postgresql/15/main/postgresql-tuned.conf \
    --memory=16GB \
    --type=web
```

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Check logs:**
```bash
sudo journalctl -u rag-system -n 100 --no-pager
```

**Common causes:**
- Port already in use
- Database connection failed
- Missing environment variables
- Permission issues

**Solutions:**
```bash
# Check if port is in use
sudo lsof -i :8000

# Test database connection
sudo -u rag psql -U rag_user -d rag_production -c "SELECT 1;"

# Verify environment
sudo -u rag /opt/rag-system/venv/bin/python -c "from app.config import settings; print(settings)"

# Fix permissions
sudo chown -R rag:rag /opt/rag-system
```

#### 2. High Memory Usage

**Monitor memory:**
```bash
# Process memory
ps aux | grep gunicorn | awk '{print $2, $4, $11}' | sort -k2 -rn

# System memory
free -h
```

**Solutions:**
- Reduce worker count
- Implement connection pooling
- Add swap space (temporary)
- Upgrade server RAM

#### 3. Slow Response Times

**Check performance:**
```bash
# Application logs
tail -f /opt/rag-system/logs/app.log

# Database queries
sudo -u postgres psql -d rag_production -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# System load
htop
```

**Solutions:**
- Add database indexes
- Optimize ChromaDB queries
- Enable Redis caching
- Scale horizontally

#### 4. Database Lock Issues

**Check locks:**
```bash
sudo -u postgres psql -d rag_production -c "
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE state != 'idle' AND query NOT LIKE '%pg_stat_activity%';"
```

**Kill stuck queries:**
```bash
sudo -u postgres psql -d rag_production -c "SELECT pg_terminate_backend(PID);"
```

#### 5. Disk Space Full

**Check disk usage:**
```bash
df -h
du -sh /opt/rag-system/* | sort -h
```

**Clean up:**
```bash
# Remove old logs
find /opt/rag-system/logs -name "*.log.*" -mtime +30 -delete

# Remove old backups
find /opt/rag-system/data/backups -mtime +30 -delete

# Clean apt cache
sudo apt clean
```

---

## Maintenance

### Regular Maintenance Tasks

#### Daily
- [ ] Check application health
- [ ] Review error logs
- [ ] Monitor disk space

#### Weekly
- [ ] Review performance metrics
- [ ] Check backup integrity
- [ ] Update OS packages

#### Monthly
- [ ] Database vacuum and analyze
- [ ] Review security updates
- [ ] Audit user activity
- [ ] Review and optimize queries

### Maintenance Scripts

#### Database Maintenance

Create `/opt/rag-system/scripts/maintain-database.sh`:

```bash
#!/bin/bash
# Database maintenance script

echo "Starting database maintenance..."

# Vacuum and analyze
sudo -u postgres psql -d rag_production -c "VACUUM ANALYZE;"

# Reindex
sudo -u postgres psql -d rag_production -c "REINDEX DATABASE rag_production;"

# Check for bloat
sudo -u postgres psql -d rag_production -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;"

echo "Database maintenance completed"
```

#### Log Cleanup

```bash
#!/bin/bash
# Clean old logs

find /opt/rag-system/logs -name "*.log.*" -mtime +30 -delete
find /var/log/nginx -name "*.log.*" -mtime +30 -delete

# Restart log rotation
logrotate -f /etc/logrotate.d/rag-system
```

### Zero-Downtime Deployment

#### Blue-Green Deployment

1. **Prepare new version:**
```bash
# Clone to new directory
git clone <repo> /opt/rag-system/app-new
cd /opt/rag-system/app-new/backend

# Install dependencies
/opt/rag-system/venv/bin/pip install -r requirements.txt
```

2. **Run database migrations:**
```bash
/opt/rag-system/venv/bin/alembic upgrade head
```

3. **Start new instances:**
```bash
sudo systemctl start rag-system-new@0
sudo systemctl start rag-system-new@1
```

4. **Update Nginx to use new instances:**
```nginx
upstream rag_backend {
    server 127.0.0.1:9000;  # New instances
    server 127.0.0.1:9001;
}
```

5. **Reload Nginx:**
```bash
sudo nginx -t && sudo nginx -s reload
```

6. **Stop old instances:**
```bash
sudo systemctl stop rag-system@0
sudo systemctl stop rag-system@1
```

7. **Switch directories:**
```bash
mv /opt/rag-system/app /opt/rag-system/app-old
mv /opt/rag-system/app-new /opt/rag-system/app
```

---

## Production Checklist

### Pre-Launch
- [ ] All security measures implemented
- [ ] SSL/TLS configured
- [ ] Backups automated and tested
- [ ] Monitoring and alerting configured
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Documentation updated

### Post-Launch
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify backup jobs running
- [ ] Test alerting system
- [ ] Review security logs
- [ ] Gather user feedback

---

## Support and Resources

- **Documentation:** `/opt/rag-system/app/backend/docs/`
- **Logs:** `/opt/rag-system/logs/`
- **Backups:** `/opt/rag-system/data/backups/`
- **Configuration:** `/opt/rag-system/app/backend/.env`

For issues:
1. Check application logs
2. Check system logs (`journalctl -u rag-system`)
3. Review monitoring dashboards
4. Consult troubleshooting section
5. Open GitHub issue with logs

---

**Last Updated:** December 2025
**Version:** 1.0
