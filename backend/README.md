# Backend Documentation

## Overview

This is an **enterprise-grade AI-powered RAG (Retrieval-Augmented Generation) system** built with FastAPI, featuring a sophisticated multi-agent architecture specialized for **renewable energy sustainability consulting**. The system combines advanced AI capabilities with enterprise features including multi-tenancy, role-based access control, and explainable AI for transparent decision-making.

## 🏗️ Architecture

### Tech Stack

- **Framework**: FastAPI 0.109.0 with Uvicorn ASGI server
- **Database**: SQLite with SQLAlchemy 2.0.25 ORM
- **Vector Store**: ChromaDB 0.4.22 for semantic search and embeddings
- **AI Framework**: LangChain 0.3+ with dual LLM provider support
- **LLM Providers**:
  - Custom API (genailab.tcs.in) with DeepSeek-V3 model
  - Ollama (local) with llama3.2 and vision support
  - Extensible architecture for OpenAI, DeepSeek API, Llama API
- **Authentication**: JWT tokens with Argon2 password hashing
- **Document Processing**: pypdf, python-docx, pandas, Pillow for OCR
- **Logging**: Loguru for structured logging
- **Resilience**: Tenacity for retry logic on LLM calls

### Core Architecture Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI API Layer                     │
│  (Auth, Chat, Documents, Reports, Council, Admin, etc.)     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                   Multi-Agent Orchestrator                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Research   │  │  Grounding   │  │ Explainability│     │
│  │    Agent     │  │    Agent     │  │    Agent      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │           Council of Agents (Voting)             │      │
│  │  Analytical │ Creative │ Critical                │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │        Energy Domain-Specific Agents             │      │
│  │  Availability │ Price Opt │ Portfolio Mix        │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                      RAG Pipeline                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Document    │  │   Vector     │  │     LLM      │     │
│  │  Processing  │→ │   Retrieval  │→ │  Generation  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                   Data & Storage Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Primary    │  │   Company    │  │   ChromaDB   │     │
│  │   Database   │  │  Databases   │  │ Collections  │     │
│  │   (SQLite)   │  │   (SQLite)   │  │  (Vectors)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- SQLite
- Ollama (optional, for local LLM)
- Access to Custom LLM API (or configure OpenAI)

### Installation

1. **Clone and navigate to backend**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize database**:
   ```bash
   python -m app.database.init_db
   ```

5. **Start server**:
   ```bash
   # From project root
   sh start.sh

   # Or directly with uvicorn
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Default Super Admin Credentials

After initialization, use these credentials:
- **Username**: `super@admin.com`
- **Password**: Check database or reset using admin scripts

## 📁 Project Structure

```
backend/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── app/
│   ├── __init__.py             # App initialization
│   ├── config.py               # Configuration management
│   ├── agents/                 # Multi-agent system
│   │   ├── base.py            # Base agent classes
│   │   ├── orchestrator.py    # Agent orchestration
│   │   ├── council.py         # Council voting system
│   │   └── specialized/       # Energy-specific agents
│   ├── api/                    # API endpoints
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── chat.py            # Chat/conversation endpoints
│   │   ├── documents.py       # Document management
│   │   ├── reports.py         # Report generation
│   │   ├── council.py         # Council evaluation
│   │   └── admin.py           # Admin management
│   ├── auth/                   # Authentication & authorization
│   │   └── security.py        # JWT, password hashing, RBAC
│   ├── database/               # Database layer
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── session.py         # Multi-tenant session management
│   │   └── init_db.py         # Database initialization
│   ├── rag/                    # RAG implementation
│   │   ├── retriever.py       # Document retrieval
│   │   ├── document_processor.py  # Document parsing
│   │   ├── text_chunker.py    # Text chunking
│   │   └── ocr_processor.py   # OCR support
│   ├── services/               # Core services
│   │   ├── llm_service.py     # LLM provider management
│   │   └── vector_store.py    # ChromaDB management
│   └── prompts/                # Prompt library
│       ├── library.py         # Prompt management
│       └── definitions.py     # Prompt definitions
├── scripts/                    # Utility scripts
│   ├── initialize_company_databases.py
│   ├── migrate_*.py           # Database migrations
│   └── generate_synthetic_data.py
├── data/                       # Application data
├── uploads/                    # Uploaded documents
├── chroma_db/                  # ChromaDB persistence
└── tests/                      # Test suite
    ├── test_api_*.py          # API tests
    └── test_*_calculation.py  # Logic tests
```

## 🔑 Core Concepts

### 1. Multi-Tenancy

The system implements **database-level multi-tenancy**:

- **Primary Database**: Stores all user accounts, authentication data
- **Company Databases**: Isolated databases per company for data segregation
- **Automatic Context Switching**: Middleware routes requests to appropriate database based on JWT token
- **Super Admin Access**: Super admins always use primary database for cross-company management

**Example Flow**:
```python
# User authenticates → JWT token issued with company_id
# Request arrives with JWT → Middleware decodes token
# Middleware sets database context to company's database
# All queries execute against company database
# Response sent → Context cleared
```

### 2. RAG (Retrieval-Augmented Generation) Pipeline

**Multi-Stage Pipeline**:

1. **Document Ingestion**:
   - Upload → Extract text → Generate metadata (summary, keywords, topics)
   - Chunk text → Generate embeddings → Store in ChromaDB + SQLite

2. **Query Processing**:
   - Extract query intent (keywords/topics)
   - Metadata-boosted retrieval from vector store
   - Multi-collection search (global + company-specific)

3. **Response Generation**:
   - Build context from retrieved documents
   - Generate response with source attribution
   - Calculate confidence scores

4. **Verification & Explanation**:
   - Grounding agent verifies factual accuracy
   - Explainability agent creates reasoning chains

### 3. Multi-Agent System

**Agent Types**:

- **ResearchAgent**: Retrieves and analyzes relevant documents
- **AnalyzerAgent**: Performs data analysis and synthesis
- **GroundingAgent**: Verifies responses against sources (prevents hallucination)
- **ExplainabilityAgent**: Generates transparent reasoning at configurable levels
- **Council Agents**: Multiple perspectives with voting mechanisms
  - Analytical (logical, factual)
  - Creative (innovative)
  - Critical (quality assurance)

**Orchestration**:
```python
# Single query → Multiple agents execute
# Each provides: response, confidence, reasoning, evidence
# Orchestrator aggregates using voting strategies
# Returns: consensus response + detailed breakdown
```

### 4. Council Voting System

**Voting Strategies**:

- **Weighted Confidence**: Aggregate by confidence scores
- **Highest Confidence**: Select best single response
- **Majority**: Most common answer wins
- **Synthesis**: LLM combines all perspectives into new response

**Debate Rounds**: Optional iterative refinement (1-5 rounds)

### 5. Role-Based Access Control (RBAC)

**Roles**:
- `super_admin`: Full system access, cross-company management
- `admin`: Company-level administration
- `analyst`: Can generate reports, chat, upload documents
- `viewer`: Read-only access

**Permissions**: Fine-grained `resource:action` format
- Examples: `documents:create`, `reports:generate`, `users:manage`

### 6. Explainable AI

**Three Explainability Levels**:

1. **Basic**: High-level summary of reasoning
2. **Detailed**: Step-by-step decision process with evidence
3. **Debug**: Complete decision tree with assumptions and confidence calculations

**Transparency Features**:
- Source attribution for all facts
- Confidence scores (0-1) for responses
- Low confidence warnings (< 0.30)
- Reasoning chains showing agent thought process
- Grounding verification scores

## 🎯 Domain Specialization: Energy Sustainability

### Energy-Specific Agents

1. **EnergyAvailabilityAgent**:
   - Analyzes renewable energy options by location
   - Evaluates solar, wind, hydro potential
   - Considers climate, geography, historical data

2. **PriceOptimizationAgent**:
   - Cost optimization for energy portfolios
   - Balances reliability vs. sustainability vs. cost
   - Market price analysis

3. **EnergyPortfolioMixAgent**:
   - Recommends optimal renewable energy portfolio
   - ESG scoring integration
   - Budget fitting and technical feasibility

### Company Energy Profiles

Tracks:
- Industry classification (ITeS, Manufacturing, Hospitality)
- Location-based constraints
- Sustainability targets (target year, renewable % increase)
- Budget parameters
- Historical consumption data ingestion

## 📚 Detailed Documentation

For in-depth information on specific components:

- **[API Documentation](app/api/README.md)**: Complete API endpoint reference with examples
- **[Agent System](app/agents/README.md)**: Multi-agent architecture and council voting
- **[RAG Implementation](app/rag/README.md)**: Document processing and retrieval details
- **[Database Architecture](app/database/README.md)**: Multi-tenant design and models
- **[Configuration Guide](CONFIGURATION.md)**: Environment variables and settings
- **[Deployment Guide](DEPLOYMENT.md)**: Production setup and scaling

## 🔐 Security Features

- **Argon2 Password Hashing**: Most secure modern hashing algorithm
- **JWT Authentication**: Signed tokens with configurable expiration
- **Database Isolation**: Physical separation of company data
- **Fine-Grained RBAC**: Permission checks on all operations
- **Input Validation**: Pydantic models validate all inputs
- **File Upload Security**: Size limits and extension validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents attacks

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api_chat.py

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_api_chat.py::test_send_message
```

## 📊 Monitoring & Observability

### Token Usage Tracking

All LLM operations track:
- Prompt tokens
- Completion tokens
- Total tokens
- Estimated cost
- Operation type
- Timestamp

Access via `/api/v1/metering/` endpoints.

### Agent Execution Logs

Detailed logs for each agent execution:
- Agent type and operation
- Inputs and outputs
- Confidence scores
- Execution time
- Token usage

Stored in `AgentLog` model, queryable via API.

### Application Logging

Structured logging with Loguru:
- Request/response logging
- Error tracking with stack traces
- Database query logging
- LLM call logging

## 🔧 Configuration

Key configuration areas:

1. **LLM Providers**: Configure Custom API, Ollama, or add new providers
2. **RAG Settings**: Chunk size, overlap, retrieval parameters
3. **Agent Behavior**: Temperature, max iterations, memory
4. **Council System**: Voting strategies, debate rounds, consensus thresholds
5. **Security**: JWT secret, token expiration, CORS origins

See [CONFIGURATION.md](CONFIGURATION.md) for complete reference.

## 🚀 Deployment

### Development

```bash
sh start.sh  # Starts on http://localhost:8000
```

### Production Considerations

- Use production ASGI server (Gunicorn + Uvicorn workers)
- Configure proper SECRET_KEY
- Set DEBUG=false
- Use PostgreSQL instead of SQLite for better concurrency
- Implement Redis caching layer
- Add load balancing
- Set up monitoring (Prometheus/Grafana)
- Implement rate limiting

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production setup.

## 🤝 Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all public functions/classes
- Keep functions focused and single-purpose

### Adding New Agents

1. Inherit from `BaseAgent` or `CouncilAgent`
2. Implement required methods
3. Register in `AGENT_REGISTRY`
4. Add tests

### Adding API Endpoints

1. Create/update router in `app/api/`
2. Add Pydantic request/response models
3. Implement permission checks
4. Add to main.py router includes
5. Test with pytest

## 📖 API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐛 Troubleshooting

### Common Issues

**Database locked errors**:
- SQLite has limited concurrency
- Consider PostgreSQL for production
- Check for long-running transactions

**ChromaDB connection errors**:
- Ensure `CHROMA_PERSIST_DIR` exists and is writable
- Check ChromaDB version compatibility

**LLM timeout errors**:
- Increase timeout in config
- Check LLM provider availability
- Review retry configuration

**JWT token errors**:
- Verify SECRET_KEY is set
- Check token expiration settings
- Ensure clock synchronization

## 📞 Support

For issues and questions:
1. Check the detailed component documentation
2. Review test files for usage examples
3. Check logs in the application directory
4. Review API documentation at `/docs`

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

Built with:
- FastAPI
- LangChain
- ChromaDB
- SQLAlchemy
- And many other excellent open-source libraries
