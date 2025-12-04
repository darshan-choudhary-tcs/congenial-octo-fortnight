# Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [LLM Provider Configuration](#llm-provider-configuration)
6. [Running the Application](#running-the-application)
7. [Testing](#testing)
8. [IDE Configuration](#ide-configuration)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python**: 3.10 or higher
- **pip**: Python package manager
- **git**: Version control
- **(Optional) Ollama**: For local LLM inference

### System Requirements

- **OS**: Linux, macOS, or Windows (WSL recommended)
- **RAM**: Minimum 4GB, recommended 8GB+
- **Disk Space**: 5GB free (more if using Ollama models)
- **Internet**: Required for Custom API access

---

## Local Development Setup

### 1. Create Virtual Environment

**Using venv** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Using conda**:
```bash
conda create -n rag-backend python=3.10
conda activate rag-backend
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include**:
- FastAPI (web framework)
- SQLAlchemy (ORM)
- ChromaDB (vector database)
- LangChain (LLM orchestration)
- PyPDF, python-docx (document processing)
- Pillow, pdf2image (image processing)
- And more...

**Verify Installation**:
```bash
python -c "import fastapi, sqlalchemy, chromadb; print('All imports successful!')"
```

### 3. Install Poppler (for PDF to Image conversion)

**macOS**:
```bash
brew install poppler
```

**Ubuntu/Debian**:
```bash
sudo apt-get install poppler-utils
```

**Windows**:
Download from: http://blog.alivate.com.au/poppler-windows/

---

## Environment Configuration

### 1. Create `.env` File

```bash
cp .env.example .env  # If example exists
# OR create manually:
touch .env
```

### 2. Configure Environment Variables

Edit `.env` file:

```bash
# Application Settings
APP_NAME="RAG & Multi-Agent System"
DEBUG=True
ENVIRONMENT=development

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Database
DATABASE_URL=sqlite:///./database.db
CHROMA_DB_PATH=./chroma_db

# File Upload
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=[".pdf", ".docx", ".txt", ".csv"]

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_TOP_K=5
SIMILARITY_THRESHOLD=0.01

# LLM Providers
# Custom API (DeepSeek)
CUSTOM_API_URL=https://genailab.tcs.in/chat/completions
CUSTOM_API_KEY=your-api-key-here
CUSTOM_MODEL=deepseek-chat
CUSTOM_EMBEDDING_MODEL=text-embedding-3-large
CUSTOM_VISION_MODEL=Llama-3.2-90B-Vision-Instruct

# Ollama (Local)
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_VISION_MODEL=llama3.2-vision

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### 3. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy output to `SECRET_KEY` in `.env`

---

## Database Setup

### 1. Create Directory Structure

```bash
mkdir -p uploads chroma_db data
```

### 2. Initialize Database

The database is automatically created on first run, but you can explicitly initialize:

```python
# Run in Python shell or create init_db.py
from app.database.db import engine
from app.database.models import Base

Base.metadata.create_all(bind=engine)
print("Database initialized!")
```

Or run the application once (it will create tables automatically):

```bash
python main.py
# Press Ctrl+C after startup
```

### 3. Seed Initial Data

Create default roles and permissions:

```bash
python scripts/seed_database.py
```

**Default Users** (created on first run):
- **Admin**: username `admin`, password `admin123`
- **Analyst**: username `analyst`, password `analyst123`
- **Viewer**: username `viewer`, password `viewer123`

⚠️ **Change these passwords immediately in production!**

---

## LLM Provider Configuration

### Option 1: Custom API (Cloud)

**Step 1: Obtain API Key**
- Contact your organization's AI lab or register at provider website
- Copy API key

**Step 2: Configure in `.env`**
```bash
CUSTOM_API_KEY=sk-xxx...
```

**Step 3: Test Connection**
```bash
python -c "
from app.services.llm_service import llm_service
import asyncio

async def test():
    result = await llm_service.invoke_llm(
        prompt='Hello, world!',
        provider='custom'
    )
    print(result)

asyncio.run(test())
"
```

### Option 2: Ollama (Local)

**Step 1: Install Ollama**
```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh

# Or download from: https://ollama.ai/download
```

**Step 2: Pull Models**
```bash
# LLM model
ollama pull llama3.2

# Embedding model
ollama pull nomic-embed-text

# Vision model (optional)
ollama pull llama3.2-vision
```

**Step 3: Start Ollama Server**
```bash
ollama serve
# Should start on http://localhost:11434
```

**Step 4: Test Connection**
```bash
curl http://localhost:11434/api/tags
# Should list available models
```

### Dual Provider Setup (Recommended)

Configure both providers for flexibility:

```bash
# Custom API for production
CUSTOM_API_KEY=sk-xxx...

# Ollama for development/testing
OLLAMA_API_URL=http://localhost:11434
```

Users can switch providers via their profile preferences.

---

## Running the Application

### Development Mode

**Method 1: Using uvicorn directly**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Method 2: Using Python**
```bash
python main.py
```

**Method 3: Using the start script**
```bash
chmod +x start.sh
./start.sh
```

### Verify Application is Running

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs  # macOS
# Or navigate to http://localhost:8000/docs in browser
```

### Background Process (Production-like)

```bash
# Start in background
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# Check logs
tail -f server.log

# Stop server
pkill -f uvicorn
```

---

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_api_auth.py
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Run Specific Test Function

```bash
pytest tests/test_api_auth.py::test_register_user
```

### Test Configuration

Tests use a separate test database (`test_database.db`) automatically created and cleaned up.

**Fixtures** (in `tests/conftest.py`):
- `client`: FastAPI test client
- `test_db`: Test database session
- `test_user`: Authenticated test user
- `mock_llm`: Mocked LLM service (no API calls)

---

## IDE Configuration

### VS Code

**Recommended Extensions**:
- Python (Microsoft)
- Pylance
- Python Test Explorer
- REST Client (for API testing)

**Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

**Launch Configuration** (`.vscode/launch.json`):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

### PyCharm

**Configure Interpreter**:
1. File → Settings → Project → Python Interpreter
2. Add interpreter → Existing environment → Select `venv/bin/python`

**Configure pytest**:
1. File → Settings → Tools → Python Integrated Tools
2. Testing → Default test runner → pytest

**Run Configuration**:
1. Run → Edit Configurations → Add New → Python
2. Script path: `path/to/uvicorn`
3. Parameters: `main:app --reload`

---

## Troubleshooting

### Issue: ModuleNotFoundError

**Symptom**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Issue: Database Locked

**Symptom**:
```
sqlite3.OperationalError: database is locked
```

**Solution**:
```bash
# SQLite doesn't handle concurrent writes well
# Option 1: Restart application
pkill -f uvicorn
python main.py

# Option 2: Use PostgreSQL for production
# See DATABASE.md for migration guide
```

---

### Issue: ChromaDB Collection Not Found

**Symptom**:
```
chromadb.errors.InvalidCollectionException: Collection not found
```

**Solution**:
```bash
# Delete and recreate ChromaDB
rm -rf chroma_db/
python main.py  # Will recreate collections
```

---

### Issue: Ollama Connection Failed

**Symptom**:
```
requests.exceptions.ConnectionError: Cannot connect to Ollama
```

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Verify models are pulled
ollama list
```

---

### Issue: Custom API Authentication Failed

**Symptom**:
```
401 Unauthorized: Invalid API key
```

**Solution**:
```bash
# Verify API key in .env
cat .env | grep CUSTOM_API_KEY

# Test API key manually
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://genailab.tcs.in/chat/completions
```

---

### Issue: Port Already in Use

**Symptom**:
```
OSError: [Errno 48] Address already in use
```

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000
# Or on Windows:
netstat -ano | findstr :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

---

### Issue: File Upload Fails

**Symptom**:
```
413 Request Entity Too Large
```

**Solution**:
```bash
# Increase MAX_UPLOAD_SIZE in .env
MAX_UPLOAD_SIZE=52428800  # 50MB

# Or use nginx with larger client_max_body_size
```

---

### Issue: Slow Document Processing

**Symptom**: Document upload takes > 1 minute

**Solutions**:
```bash
# 1. Use Ollama instead of Custom API (faster for metadata)
# In user profile: Set preferred_llm = "ollama"

# 2. Skip metadata generation for large docs
# Modify documents.py to skip metadata for files > 5MB

# 3. Use smaller chunk size
CHUNK_SIZE=500
```

---

### Issue: Import Errors

**Symptom**:
```
ImportError: cannot import name 'app' from 'app'
```

**Solution**:
```bash
# Ensure you're in the backend directory
cd backend

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Verify directory structure
ls app/
# Should see: __init__.py, config.py, etc.
```

---

## Next Steps

After setup:

1. **Explore API Documentation**: http://localhost:8000/docs
2. **Upload Test Documents**: Use the `/documents/upload` endpoint
3. **Test Chat**: Send queries via `/chat/message`
4. **Review Architecture**: Read [ARCHITECTURE.md](../ARCHITECTURE.md)
5. **Configure for Production**: See [DEPLOYMENT.md](../DEPLOYMENT.md)

---

## Quick Start Script

Save as `quickstart.sh`:

```bash
#!/bin/bash

# Quick setup script
set -e

echo "🚀 Setting up RAG & Multi-Agent System..."

# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 3. Create directories
echo "📁 Creating directories..."
mkdir -p uploads chroma_db data

# 4. Create .env if not exists
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cat > .env << EOF
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
DATABASE_URL=sqlite:///./database.db
CHROMA_DB_PATH=./chroma_db
CUSTOM_API_KEY=your-key-here
OLLAMA_API_URL=http://localhost:11434
EOF
fi

# 5. Initialize database
echo "🗄️ Initializing database..."
python -c "from app.database.db import engine; from app.database.models import Base; Base.metadata.create_all(bind=engine)"

echo "✅ Setup complete!"
echo "▶️ Start the server with: python main.py"
echo "📚 View docs at: http://localhost:8000/docs"
```

**Run it**:
```bash
chmod +x quickstart.sh
./quickstart.sh
```

---

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [API Reference](../API_REFERENCE.md)
- [Configuration Guide](./CONFIGURATION.md)
- [Extending the System](./EXTENDING.md)
- [Deployment Guide](../DEPLOYMENT.md)
