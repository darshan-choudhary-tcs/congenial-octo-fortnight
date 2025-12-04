# Backend Documentation

## RAG & Multi-Agent AI System

Enterprise-grade **Retrieval-Augmented Generation (RAG)** and **Multi-Agent System** for building intelligent, document-based knowledge bases with explainable AI capabilities.

---

## 🚀 Quick Start

```bash
# Clone repository
git clone <repository-url>
cd backend

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
python main.py
```

Visit **http://localhost:8000/docs** for interactive API documentation.

👉 **Detailed setup instructions**: [Setup Guide](docs/guides/SETUP.md)

---

## 📚 Documentation Index

### Core Documentation

| Document | Description |
|----------|-------------|
| **[Architecture](docs/ARCHITECTURE.md)** | System overview, design patterns, component layers, technology stack |
| **[API Reference](docs/API_REFERENCE.md)** | Complete API documentation with endpoints, schemas, and examples |
| **[Database Schema](docs/DATABASE.md)** | Database models, relationships, ER diagrams, and migrations |
| **[RAG System](docs/RAG_SYSTEM.md)** | Document processing, retrieval, confidence scoring, grounding |
| **[Agent System](docs/AGENT_SYSTEM.md)** | Multi-agent orchestration, agent types, communication patterns |

### Developer Guides

| Guide | Description |
|-------|-------------|
| **[Setup Guide](docs/guides/SETUP.md)** | Local development setup, environment configuration, testing |
| **[Configuration](docs/guides/CONFIGURATION.md)** | All configuration options explained |
| **[Authentication](docs/guides/AUTHENTICATION.md)** | JWT implementation, RBAC, permission model |
| **[Extending](docs/guides/EXTENDING.md)** | How to add agents, endpoints, document processors, LLM providers |

### Operations

| Document | Description |
|----------|-------------|
| **[Deployment](docs/DEPLOYMENT.md)** | Production deployment, security, monitoring, scaling |

---

## ✨ Key Features

### 🗂️ Document Management
- **Multi-format support**: PDF, DOCX, TXT, CSV
- **Automatic metadata generation**: LLM-powered summaries, keywords, topics
- **Smart chunking**: Recursive text splitting with overlap
- **Dual scope**: Global (shared) and user-specific documents

### 🤖 Multi-Agent System
- **ResearchAgent**: Intelligent document retrieval with metadata filtering
- **AnalyzerAgent**: Data analysis and insight generation
- **GroundingAgent**: Response verification against sources
- **ExplainabilityAgent**: Transparent reasoning chains

### 🧠 RAG Pipeline
- **Semantic search**: Vector similarity with ChromaDB
- **Metadata-enhanced retrieval**: Query keywords/topics boost relevance
- **Multi-factor confidence**: Similarity + citations + query quality + length
- **Source attribution**: [Source N] citations in responses
- **Grounding verification**: LLM-based claim checking

### 🔐 Security & Access Control
- **JWT authentication**: Secure token-based auth with expiration
- **Role-Based Access Control (RBAC)**: Admin, Analyst, Viewer roles
- **Fine-grained permissions**: 13 granular permissions
- **Document scoping**: Private vs shared documents

### 📊 Explainable AI
- **Confidence scoring**: 0-1 scale with calibrated multi-factor algorithm
- **Reasoning chains**: Step-by-step decision tracking
- **Agent logs**: Complete execution history
- **Three explainability levels**: Basic, Detailed, Debug

### 💰 Token Usage Metering
- **Comprehensive tracking**: Every LLM call logged
- **Cost estimation**: Provider-specific pricing
- **Multi-level analytics**: User, conversation, message, agent
- **Operation breakdown**: Chat, embedding, analysis, grounding, explanation

### 🖼️ OCR & Vision
- **Text extraction**: From images and PDFs
- **Vision models**: Llama-3.2-90B-Vision (Custom API) or llama3.2-vision (Ollama)
- **Batch processing**: Multiple files in one request

### 🌊 Real-Time Streaming
- **Server-Sent Events (SSE)**: Progressive response delivery
- **Agent progress tracking**: See which agent is executing
- **Token-by-token streaming**: Reduce perceived latency

### 🔄 Dual LLM Support
- **Custom API**: DeepSeek-V3 (cloud, production-ready)
- **Ollama**: Llama 3.2 (local, free, privacy-focused)
- **Runtime switching**: Users choose preferred provider

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  Authentication, Request Validation, Response Formatting     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Agent Layer                               │
│  ResearchAgent, AnalyzerAgent, GroundingAgent, etc.         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Service Layer                               │
│  LLMService, VectorStoreService, VisionService              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    RAG Layer                                 │
│  DocumentProcessor, Retriever, OCRProcessor                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Data Layer                                 │
│  SQLAlchemy Models, Database Session, ChromaDB              │
└─────────────────────────────────────────────────────────────┘
```

**Design Patterns**:
- Layered Architecture (clear separation of concerns)
- Dependency Injection (FastAPI Depends)
- Factory Pattern (Agent registry)
- Strategy Pattern (LLM provider switching)
- Orchestrator Pattern (Multi-agent coordination)

**Read more**: [Architecture Documentation](docs/ARCHITECTURE.md)

---

## 🗄️ Technology Stack

### Core Framework
- **FastAPI** (0.104.1) - Modern async web framework
- **SQLAlchemy** (2.0.23) - ORM for database
- **ChromaDB** (0.4.18) - Vector database

### LLM Integration
- **LangChain** (0.1.0) - LLM orchestration
- **OpenAI SDK** - Custom API client (DeepSeek-V3)
- **Ollama SDK** - Local LLM client

### Document Processing
- **PyPDF** (3.17.4) - PDF extraction
- **python-docx** (1.1.0) - Word documents
- **pandas** (2.1.4) - CSV processing
- **Pillow** (10.1.0) - Image manipulation
- **pdf2image** (1.16.3) - PDF to image

### Security
- **python-jose** (3.3.0) - JWT handling
- **passlib** (1.7.4) - Password hashing (Argon2)

---

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info
- `PUT /auth/me` - Update user profile
- `POST /auth/change-password` - Change password

### Chat & Messaging
- `POST /chat/message` - Send message, get AI response
- `POST /chat/stream` - Streaming response with SSE
- `GET /chat/conversations` - List user conversations
- `GET /chat/conversations/{id}` - Get conversation history
- `DELETE /chat/conversations/{id}` - Delete conversation

### Document Management
- `POST /documents/upload` - Upload document
- `GET /documents` - List documents with filtering
- `GET /documents/{id}` - Get document details
- `DELETE /documents/{id}` - Delete document
- `POST /documents/{id}/regenerate-metadata` - Regenerate metadata

### Agent Monitoring
- `GET /agents/status` - Get agent status
- `GET /agents/logs` - Get agent execution logs
- `GET /agents/logs/message/{id}` - Get logs for message

### Explainability
- `GET /explainability/message/{id}` - Get explainability data
- `GET /explainability/conversation/{id}/confidence` - Confidence trend

### Token Metering
- `GET /metering/user/{id}/usage` - User token usage
- `GET /metering/overall` - System-wide usage (admin)
- `GET /metering/conversation/{id}` - Conversation usage
- `GET /metering/cost-breakdown` - Cost breakdown (admin)

### Admin Operations
- `GET /admin/users` - List all users
- `POST /admin/users` - Create user
- `PUT /admin/users/{id}` - Update user
- `DELETE /admin/users/{id}` - Delete user
- `GET /admin/roles` - List roles
- `GET /admin/permissions` - List permissions
- `GET /admin/stats` - System statistics
- `GET /admin/llm-config` - Get LLM configuration
- `PUT /admin/llm-config` - Update LLM configuration

### Utility Functions
- `POST /utilities/ocr` - Extract text from image/PDF
- `POST /utilities/ocr/batch` - Batch OCR processing
- `POST /utilities/vision` - Analyze image with vision model

**Interactive Docs**: http://localhost:8000/docs
**Read more**: [API Reference](docs/API_REFERENCE.md)

---

## 🗃️ Database Models

- **User**: Authentication, preferences (preferred_llm, explainability_level)
- **Role**: Access control (admin, analyst, viewer)
- **Permission**: Granular rights (documents:create, agents:execute, etc.)
- **Document**: File metadata, LLM-generated summary/keywords/topics
- **DocumentChunk**: Text chunks with embeddings
- **Conversation**: Chat sessions with LLM config
- **Message**: User/assistant messages with RAG context
- **AgentLog**: Agent execution history
- **TokenUsage**: Comprehensive token metering

**Read more**: [Database Documentation](docs/DATABASE.md)

---

## 🤝 Contributing

### Development Workflow

1. **Create branch**: `git checkout -b feature/your-feature`
2. **Make changes**: Follow code style guidelines
3. **Run tests**: `pytest`
4. **Commit**: `git commit -m "Add feature X"`
5. **Push**: `git push origin feature/your-feature`
6. **Create PR**: Submit pull request for review

### Code Style

- **Formatter**: Black (line length 100)
- **Linter**: Pylint
- **Type hints**: Use where appropriate
- **Docstrings**: Google style

```bash
# Format code
black app/ tests/

# Lint
pylint app/

# Type check
mypy app/
```

### Testing Guidelines

- Write tests for new features
- Maintain >80% code coverage
- Use fixtures for common setups
- Mock external services (LLM, etc.)

**Read more**: [Setup Guide - Testing](docs/guides/SETUP.md#testing)

---

## 📦 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── agents/                # Multi-agent system
│   │   ├── base_agents.py     # Agent base class + implementations
│   │   └── orchestrator.py    # Agent orchestrator
│   ├── api/                   # API endpoints
│   │   └── v1/                # API version 1
│   │       ├── admin.py       # Admin endpoints
│   │       ├── agents.py      # Agent monitoring
│   │       ├── auth.py        # Authentication
│   │       ├── chat.py        # Chat & messaging
│   │       ├── documents.py   # Document management
│   │       ├── explainability.py  # Explainability
│   │       ├── metering.py    # Token usage
│   │       └── utilities.py   # OCR & vision
│   ├── auth/                  # Authentication & security
│   │   ├── schemas.py         # Pydantic models
│   │   └── security.py        # JWT, RBAC
│   ├── database/              # Database layer
│   │   ├── db.py              # Database session
│   │   └── models.py          # SQLAlchemy models
│   ├── rag/                   # RAG system
│   │   ├── document_processor.py  # Document extraction
│   │   ├── ocr_processor.py   # OCR processing
│   │   ├── query_validator.py # Query quality check
│   │   └── retriever.py       # Retrieval & grounding
│   └── services/              # Business logic
│       ├── llm_service.py     # LLM integration
│       ├── vector_store.py    # ChromaDB service
│       └── vision_service.py  # Vision processing
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── DATABASE.md
│   ├── RAG_SYSTEM.md
│   ├── AGENT_SYSTEM.md
│   ├── DEPLOYMENT.md
│   └── guides/
│       ├── SETUP.md
│       ├── CONFIGURATION.md
│       ├── AUTHENTICATION.md
│       └── EXTENDING.md
├── tests/                     # Test suite
│   ├── conftest.py            # Pytest fixtures
│   ├── test_api_auth.py
│   ├── test_api_chat.py
│   ├── test_api_documents.py
│   └── test_confidence_calculation.py
├── scripts/                   # Utility scripts
│   ├── generate_synthetic_data.py
│   └── migrate_*.py
├── chroma_db/                 # ChromaDB storage
├── uploads/                   # Uploaded files
├── data/                      # Data files
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── start.sh                   # Start script
├── stop.sh                    # Stop script
└── README.md                  # This file
```

---

## 🚢 Deployment

### Production Checklist

- [ ] Change default passwords
- [ ] Set strong SECRET_KEY
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure production CORS origins
- [ ] Enable HTTPS
- [ ] Set up reverse proxy (nginx)
- [ ] Configure proper logging
- [ ] Set up backup strategy
- [ ] Monitor token usage
- [ ] Set up alerting

**Read more**: [Deployment Guide](docs/DEPLOYMENT.md)

---

## 🐛 Troubleshooting

### Common Issues

**Database Locked**
```bash
# SQLite limitation - use PostgreSQL for production
rm database.db && python main.py
```

**Ollama Connection Failed**
```bash
# Start Ollama server
ollama serve
```

**Module Not Found**
```bash
# Activate virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**Read more**: [Setup Guide - Troubleshooting](docs/guides/SETUP.md#troubleshooting)

---

## 📖 Additional Resources

### External Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [LangChain Docs](https://python.langchain.com/)
- [Ollama Docs](https://ollama.ai/docs)

### API Testing
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Example Clients
- Python: See `docs/examples/python_client.py`
- JavaScript: See `docs/examples/js_client.js`
- cURL: See `docs/API_REFERENCE.md`

---

## 📝 License

[Your License Here]

---

## 🙏 Acknowledgments

Built with:
- FastAPI framework
- ChromaDB vector database
- DeepSeek-V3 and Llama 3.2 models
- And many open-source libraries

---

## 📞 Support

- **Issues**: [GitHub Issues](your-repo-url/issues)
- **Discussions**: [GitHub Discussions](your-repo-url/discussions)
- **Email**: support@your-domain.com

---

**Last Updated**: December 2025
