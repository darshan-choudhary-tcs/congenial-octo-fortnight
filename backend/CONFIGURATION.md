# Configuration Guide

## Overview

This guide covers all configuration options for the backend application. Configuration is managed through environment variables using Pydantic Settings for type safety and validation.

## Configuration File

Create a `.env` file in the `backend/` directory:

```bash
# Copy example
cp .env.example .env

# Edit with your values
nano .env
```

## Environment Variables

### Application Settings

#### APP_NAME
- **Type**: String
- **Default**: `"AI-Powered RAG System"`
- **Description**: Application name displayed in logs and API docs

```bash
APP_NAME="Energy Sustainability RAG Platform"
```

#### DEBUG
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable debug mode (detailed logs, auto-reload)

```bash
DEBUG=true  # Development
DEBUG=false # Production
```

#### HOST
- **Type**: String
- **Default**: `"0.0.0.0"`
- **Description**: Server host address

```bash
HOST=0.0.0.0      # All interfaces
HOST=127.0.0.1    # Localhost only
```

#### PORT
- **Type**: Integer
- **Default**: `8000`
- **Description**: Server port

```bash
PORT=8000
```

#### CORS_ORIGINS
- **Type**: List[String]
- **Default**: `["http://localhost:3000"]`
- **Description**: Allowed CORS origins (comma-separated)

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,https://app.example.com
```

---

### Database Settings

#### DATABASE_URL
- **Type**: String
- **Default**: `"sqlite:///./primary_database.db"`
- **Description**: Primary database connection URL

```bash
# SQLite (development)
DATABASE_URL=sqlite:///./primary_database.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# MySQL
DATABASE_URL=mysql://user:password@localhost:3306/dbname
```

#### DATABASE_ECHO
- **Type**: Boolean
- **Default**: `false`
- **Description**: Log all SQL queries (debugging)

```bash
DATABASE_ECHO=true  # Development only
```

---

### JWT Authentication

#### SECRET_KEY
- **Type**: String
- **Required**: Yes
- **Description**: Secret key for JWT token signing

```bash
# Generate secure key:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-super-secret-key-change-this-in-production
```

⚠️ **IMPORTANT**: Use a strong, unique secret key in production!

#### ALGORITHM
- **Type**: String
- **Default**: `"HS256"`
- **Description**: JWT signing algorithm

```bash
ALGORITHM=HS256
```

#### ACCESS_TOKEN_EXPIRE_MINUTES
- **Type**: Integer
- **Default**: `1440` (24 hours)
- **Description**: JWT token expiration time

```bash
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
ACCESS_TOKEN_EXPIRE_MINUTES=60    # 1 hour (stricter)
```

---

### LLM Providers

#### Custom API (Primary)

##### CUSTOM_LLM_BASE_URL
- **Type**: String
- **Default**: `"https://genailab.tcs.in/openai/deployments"`
- **Description**: Base URL for custom LLM API

```bash
CUSTOM_LLM_BASE_URL=https://genailab.tcs.in/openai/deployments
```

##### CUSTOM_LLM_API_KEY
- **Type**: String
- **Required**: Yes
- **Description**: API key for custom LLM

```bash
CUSTOM_LLM_API_KEY=your-api-key-here
```

##### CUSTOM_LLM_MODEL
- **Type**: String
- **Default**: `"deepseek-v3"`
- **Description**: Model name/deployment ID

```bash
CUSTOM_LLM_MODEL=deepseek-v3
```

##### CUSTOM_LLM_TEMPERATURE
- **Type**: Float
- **Default**: `0.7`
- **Description**: Default temperature for custom LLM

```bash
CUSTOM_LLM_TEMPERATURE=0.7
```

##### CUSTOM_EMBEDDINGS_MODEL
- **Type**: String
- **Default**: `"text-embedding-ada-002"`
- **Description**: Embedding model name

```bash
CUSTOM_EMBEDDINGS_MODEL=text-embedding-ada-002
```

---

#### Ollama (Local LLM)

##### OLLAMA_BASE_URL
- **Type**: String
- **Default**: `"http://localhost:11434"`
- **Description**: Ollama server URL

```bash
OLLAMA_BASE_URL=http://localhost:11434
```

##### OLLAMA_MODEL
- **Type**: String
- **Default**: `"llama3.2"`
- **Description**: Ollama model name

```bash
OLLAMA_MODEL=llama3.2
OLLAMA_MODEL=mistral
OLLAMA_MODEL=codellama
```

##### OLLAMA_EMBEDDINGS_MODEL
- **Type**: String
- **Default**: `"nomic-embed-text"`
- **Description**: Ollama embedding model

```bash
OLLAMA_EMBEDDINGS_MODEL=nomic-embed-text
```

##### OLLAMA_VISION_MODEL
- **Type**: String
- **Default**: `"llama3.2-vision"`
- **Description**: Ollama vision model for OCR

```bash
OLLAMA_VISION_MODEL=llama3.2-vision
```

---

#### OpenAI (Future Support)

##### OPENAI_API_KEY
- **Type**: String
- **Description**: OpenAI API key

```bash
OPENAI_API_KEY=sk-...
```

##### OPENAI_MODEL
- **Type**: String
- **Default**: `"gpt-4"`
- **Description**: OpenAI model name

```bash
OPENAI_MODEL=gpt-4
OPENAI_MODEL=gpt-4-turbo
OPENAI_MODEL=gpt-3.5-turbo
```

---

### ChromaDB (Vector Store)

#### CHROMA_PERSIST_DIR
- **Type**: String
- **Default**: `"./chroma_db"`
- **Description**: Directory for ChromaDB persistence

```bash
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_PERSIST_DIR=/var/lib/chroma  # Production
```

#### CHROMA_COLLECTION_NAME
- **Type**: String
- **Default**: `"documents"`
- **Description**: Default collection name (rarely used due to scoping)

```bash
CHROMA_COLLECTION_NAME=documents
```

#### CHROMA_HOST
- **Type**: String
- **Default**: `None` (local mode)
- **Description**: ChromaDB server host (for client-server mode)

```bash
# Local mode (default)
# CHROMA_HOST=

# Client-server mode
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

---

### RAG Configuration

#### CHUNK_SIZE
- **Type**: Integer
- **Default**: `1000`
- **Description**: Characters per text chunk

```bash
CHUNK_SIZE=1000   # Balanced
CHUNK_SIZE=500    # Smaller chunks, faster retrieval
CHUNK_SIZE=2000   # Larger context, slower
```

#### CHUNK_OVERLAP
- **Type**: Integer
- **Default**: `200`
- **Description**: Overlap between chunks (characters)

```bash
CHUNK_OVERLAP=200  # Balanced
CHUNK_OVERLAP=100  # Less redundancy
CHUNK_OVERLAP=400  # More context preservation
```

#### MAX_RETRIEVAL_DOCS
- **Type**: Integer
- **Default**: `5`
- **Description**: Maximum documents to retrieve per query

```bash
MAX_RETRIEVAL_DOCS=5   # Balanced
MAX_RETRIEVAL_DOCS=10  # More context
MAX_RETRIEVAL_DOCS=3   # Faster, less context
```

#### SIMILARITY_THRESHOLD
- **Type**: Float
- **Default**: `0.01`
- **Description**: Minimum similarity score (not strictly enforced)

```bash
SIMILARITY_THRESHOLD=0.01
```

#### ENABLE_METADATA_BOOST
- **Type**: Boolean
- **Default**: `true`
- **Description**: Use metadata-boosted retrieval

```bash
ENABLE_METADATA_BOOST=true  # Recommended
ENABLE_METADATA_BOOST=false # Standard vector search only
```

---

### Agent Configuration

#### MAX_AGENT_ITERATIONS
- **Type**: Integer
- **Default**: `5`
- **Description**: Maximum iterations for agent loops

```bash
MAX_AGENT_ITERATIONS=5
```

#### AGENT_TEMPERATURE
- **Type**: Float
- **Default**: `0.7`
- **Description**: Default agent temperature

```bash
AGENT_TEMPERATURE=0.7  # Balanced
AGENT_TEMPERATURE=0.3  # Conservative
AGENT_TEMPERATURE=0.9  # Creative
```

#### ENABLE_AGENT_MEMORY
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable agent memory (future feature)

```bash
ENABLE_AGENT_MEMORY=false
```

---

### Explainability Settings

#### EXPLAINABILITY_LEVEL
- **Type**: String
- **Default**: `"detailed"`
- **Options**: `basic`, `detailed`, `debug`
- **Description**: Default explainability level

```bash
EXPLAINABILITY_LEVEL=detailed  # Recommended
EXPLAINABILITY_LEVEL=basic     # Less verbose
EXPLAINABILITY_LEVEL=debug     # Maximum detail
```

#### ENABLE_CONFIDENCE_SCORING
- **Type**: Boolean
- **Default**: `true`
- **Description**: Calculate confidence scores

```bash
ENABLE_CONFIDENCE_SCORING=true
```

#### ENABLE_SOURCE_ATTRIBUTION
- **Type**: Boolean
- **Default**: `true`
- **Description**: Attribute facts to source documents

```bash
ENABLE_SOURCE_ATTRIBUTION=true
```

#### ENABLE_REASONING_CHAINS
- **Type**: Boolean
- **Default**: `true`
- **Description**: Generate step-by-step reasoning

```bash
ENABLE_REASONING_CHAINS=true
```

#### LOW_CONFIDENCE_THRESHOLD
- **Type**: Float
- **Default**: `0.30`
- **Description**: Threshold for low confidence warnings

```bash
LOW_CONFIDENCE_THRESHOLD=0.30  # Default
LOW_CONFIDENCE_THRESHOLD=0.40  # More conservative
```

---

### Council of Agents

#### COUNCIL_ENABLED
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable council voting system

```bash
COUNCIL_ENABLED=true
```

#### COUNCIL_DEFAULT_STRATEGY
- **Type**: String
- **Default**: `"weighted_confidence"`
- **Options**: `weighted_confidence`, `highest_confidence`, `majority`, `synthesis`
- **Description**: Default voting strategy

```bash
COUNCIL_DEFAULT_STRATEGY=weighted_confidence  # Recommended
COUNCIL_DEFAULT_STRATEGY=synthesis            # Most comprehensive
```

#### COUNCIL_MAX_DEBATE_ROUNDS
- **Type**: Integer
- **Default**: `5`
- **Description**: Maximum debate rounds

```bash
COUNCIL_MAX_DEBATE_ROUNDS=5  # Maximum allowed
COUNCIL_MAX_DEBATE_ROUNDS=2  # Typical usage
```

#### COUNCIL_MIN_CONSENSUS_THRESHOLD
- **Type**: Float
- **Default**: `0.6`
- **Description**: Minimum consensus score to accept result

```bash
COUNCIL_MIN_CONSENSUS_THRESHOLD=0.6  # Moderate
COUNCIL_MIN_CONSENSUS_THRESHOLD=0.8  # Strict
```

#### Council Agent Configurations

##### Analytical Voter
```bash
COUNCIL_ANALYTICAL_TEMPERATURE=0.3    # Conservative
COUNCIL_ANALYTICAL_PROVIDER=custom    # LLM provider
COUNCIL_ANALYTICAL_WEIGHT=1.0         # Vote weight
```

##### Creative Voter
```bash
COUNCIL_CREATIVE_TEMPERATURE=0.9      # Innovative
COUNCIL_CREATIVE_PROVIDER=custom
COUNCIL_CREATIVE_WEIGHT=1.0
```

##### Critical Voter
```bash
COUNCIL_CRITICAL_TEMPERATURE=0.5      # Balanced
COUNCIL_CRITICAL_PROVIDER=custom
COUNCIL_CRITICAL_WEIGHT=1.0
```

---

### File Upload

#### MAX_UPLOAD_SIZE
- **Type**: Integer
- **Default**: `10485760` (10MB)
- **Description**: Maximum file upload size (bytes)

```bash
MAX_UPLOAD_SIZE=10485760   # 10MB
MAX_UPLOAD_SIZE=52428800   # 50MB
MAX_UPLOAD_SIZE=104857600  # 100MB
```

#### ALLOWED_EXTENSIONS
- **Type**: List[String]
- **Default**: `["pdf", "docx", "txt", "csv"]`
- **Description**: Allowed file extensions

```bash
ALLOWED_EXTENSIONS=pdf,docx,txt,csv
```

#### UPLOAD_DIR
- **Type**: String
- **Default**: `"./uploads"`
- **Description**: Directory for uploaded files

```bash
UPLOAD_DIR=./uploads
UPLOAD_DIR=/var/lib/app/uploads  # Production
```

---

### OCR Configuration

#### OCR_SUPPORTED_FORMATS
- **Type**: List[String]
- **Default**: `["pdf", "png", "jpg", "jpeg"]`
- **Description**: File formats supporting OCR

```bash
OCR_SUPPORTED_FORMATS=pdf,png,jpg,jpeg,tiff
```

#### OCR_MAX_FILE_SIZE
- **Type**: Integer
- **Default**: `10485760` (10MB)
- **Description**: Maximum file size for OCR

```bash
OCR_MAX_FILE_SIZE=10485760
```

#### OCR_CONFIDENCE_THRESHOLD
- **Type**: Float
- **Default**: `0.7`
- **Description**: Minimum OCR confidence score

```bash
OCR_CONFIDENCE_THRESHOLD=0.7  # Balanced
OCR_CONFIDENCE_THRESHOLD=0.8  # Stricter
```

---

### Logging

#### LOG_LEVEL
- **Type**: String
- **Default**: `"INFO"`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Logging verbosity

```bash
LOG_LEVEL=INFO     # Production
LOG_LEVEL=DEBUG    # Development
LOG_LEVEL=WARNING  # Minimal logging
```

#### LOG_FILE
- **Type**: String
- **Default**: `None` (console only)
- **Description**: Log file path

```bash
LOG_FILE=./logs/app.log
LOG_FILE=/var/log/app/backend.log  # Production
```

---

## Configuration Profiles

### Development

```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_ECHO=true
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Use Ollama for free local testing
PREFERRED_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Fast settings
CHUNK_SIZE=800
MAX_RETRIEVAL_DOCS=3
COUNCIL_MAX_DEBATE_ROUNDS=1
```

### Staging

```bash
# .env.staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@staging-db:5432/app
CORS_ORIGINS=https://staging.example.com

# Use custom API
PREFERRED_LLM_PROVIDER=custom
CUSTOM_LLM_BASE_URL=https://api.example.com
CUSTOM_LLM_API_KEY=staging-key

# Production-like settings
CHUNK_SIZE=1000
MAX_RETRIEVAL_DOCS=5
ENABLE_METADATA_BOOST=true
```

### Production

```bash
# .env.production
DEBUG=false
LOG_LEVEL=WARNING
LOG_FILE=/var/log/app/backend.log

# Production database
DATABASE_URL=postgresql://user:pass@prod-db:5432/app

# Security
SECRET_KEY=<strong-randomly-generated-key>
ACCESS_TOKEN_EXPIRE_MINUTES=60  # Shorter for security
CORS_ORIGINS=https://app.example.com

# Production LLM
CUSTOM_LLM_BASE_URL=https://api.example.com
CUSTOM_LLM_API_KEY=<production-key>

# Optimized settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIEVAL_DOCS=5
ENABLE_METADATA_BOOST=true
COUNCIL_MAX_DEBATE_ROUNDS=2

# Paths
UPLOAD_DIR=/var/lib/app/uploads
CHROMA_PERSIST_DIR=/var/lib/app/chroma_db
```

---

## Validation

The application validates configuration on startup using Pydantic:

```python
from app.config import settings

# Validation errors will be raised immediately
print(settings.CUSTOM_LLM_API_KEY)  # Must be set
print(settings.CHUNK_SIZE)           # Must be positive integer
```

Common validation errors:

```
ValidationError: CUSTOM_LLM_API_KEY is required
ValidationError: CHUNK_SIZE must be greater than 0
ValidationError: COUNCIL_MIN_CONSENSUS_THRESHOLD must be between 0 and 1
```

---

## Dynamic Configuration

Some settings can be overridden at runtime:

### User Preferences

Users can configure per their profile:

```python
user.preferred_llm = "ollama"          # Override LLM provider
user.explainability_level = "basic"    # Override explainability
```

### API Parameters

Many settings can be overridden per request:

```python
# Chat with custom settings
response = await chat.send(
    message="...",
    temperature=0.9,              # Override default
    explainability_level="debug", # Override user preference
    use_council=True,             # Enable council
    voting_strategy="synthesis"   # Override default strategy
)
```

### Report Configuration

Report generation weights can be configured per company:

```python
profile.energy_mix_weight = 0.45
profile.price_optimization_weight = 0.30
profile.portfolio_decision_weight = 0.25
```

---

## Configuration Best Practices

1. **Use Environment Variables**: Never hardcode secrets
2. **Separate by Environment**: Different .env for dev/staging/prod
3. **Strong SECRET_KEY**: Generate with `secrets.token_urlsafe(32)`
4. **Secure Token Expiration**: Shorter in production (60-120 min)
5. **Enable HTTPS Only**: In production
6. **Restrict CORS Origins**: Only allow trusted domains
7. **Monitor Token Usage**: Track costs with appropriate logging
8. **Backup Configuration**: Keep .env.example updated
9. **Rotate Secrets**: Change API keys and secrets periodically
10. **Use PostgreSQL**: In production (not SQLite)

---

## Troubleshooting

### Configuration Not Loading

**Check**:
1. `.env` file exists in correct directory
2. File is readable (permissions)
3. No syntax errors in .env
4. Environment variables have correct names (case-sensitive)

### LLM Provider Errors

**Check**:
1. API keys are set and valid
2. Base URLs are correct
3. Models exist and are accessible
4. Network connectivity
5. Rate limits not exceeded

### Database Connection Errors

**Check**:
1. DATABASE_URL format is correct
2. Database server is running
3. Credentials are valid
4. Network connectivity
5. Database exists

### ChromaDB Errors

**Check**:
1. CHROMA_PERSIST_DIR exists and is writable
2. Sufficient disk space
3. No permission issues
4. ChromaDB server running (if client-server mode)

---

## Environment Variable Reference

Quick reference of all environment variables:

```bash
# Application
APP_NAME=string
DEBUG=boolean
HOST=string
PORT=integer
CORS_ORIGINS=comma-separated-list

# Database
DATABASE_URL=string
DATABASE_ECHO=boolean

# JWT
SECRET_KEY=string (required)
ALGORITHM=string
ACCESS_TOKEN_EXPIRE_MINUTES=integer

# Custom LLM
CUSTOM_LLM_BASE_URL=string
CUSTOM_LLM_API_KEY=string (required)
CUSTOM_LLM_MODEL=string
CUSTOM_LLM_TEMPERATURE=float
CUSTOM_EMBEDDINGS_MODEL=string

# Ollama
OLLAMA_BASE_URL=string
OLLAMA_MODEL=string
OLLAMA_EMBEDDINGS_MODEL=string
OLLAMA_VISION_MODEL=string

# OpenAI (future)
OPENAI_API_KEY=string
OPENAI_MODEL=string

# ChromaDB
CHROMA_PERSIST_DIR=string
CHROMA_COLLECTION_NAME=string
CHROMA_HOST=string
CHROMA_PORT=integer

# RAG
CHUNK_SIZE=integer
CHUNK_OVERLAP=integer
MAX_RETRIEVAL_DOCS=integer
SIMILARITY_THRESHOLD=float
ENABLE_METADATA_BOOST=boolean

# Agents
MAX_AGENT_ITERATIONS=integer
AGENT_TEMPERATURE=float
ENABLE_AGENT_MEMORY=boolean

# Explainability
EXPLAINABILITY_LEVEL=string
ENABLE_CONFIDENCE_SCORING=boolean
ENABLE_SOURCE_ATTRIBUTION=boolean
ENABLE_REASONING_CHAINS=boolean
LOW_CONFIDENCE_THRESHOLD=float

# Council
COUNCIL_ENABLED=boolean
COUNCIL_DEFAULT_STRATEGY=string
COUNCIL_MAX_DEBATE_ROUNDS=integer
COUNCIL_MIN_CONSENSUS_THRESHOLD=float
COUNCIL_ANALYTICAL_TEMPERATURE=float
COUNCIL_ANALYTICAL_PROVIDER=string
COUNCIL_ANALYTICAL_WEIGHT=float
COUNCIL_CREATIVE_TEMPERATURE=float
COUNCIL_CREATIVE_PROVIDER=string
COUNCIL_CREATIVE_WEIGHT=float
COUNCIL_CRITICAL_TEMPERATURE=float
COUNCIL_CRITICAL_PROVIDER=string
COUNCIL_CRITICAL_WEIGHT=float

# File Upload
MAX_UPLOAD_SIZE=integer
ALLOWED_EXTENSIONS=comma-separated-list
UPLOAD_DIR=string

# OCR
OCR_SUPPORTED_FORMATS=comma-separated-list
OCR_MAX_FILE_SIZE=integer
OCR_CONFIDENCE_THRESHOLD=float

# Logging
LOG_LEVEL=string
LOG_FILE=string
```

---

For more information, see:
- [Main Backend Documentation](README.md)
- [Deployment Guide](DEPLOYMENT.md)
- [API Documentation](app/api/README.md)
