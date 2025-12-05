# RAG & Multi-Agent System

A comprehensive full-stack AI application featuring **Retrieval-Augmented Generation (RAG)**, **Multi-Agent Orchestration**, and **Explainable AI** capabilities. Built with FastAPI backend and Next.js frontend.

## 🌟 Features

### Core AI Capabilities
- **Retrieval Augmented Generation (RAG)**: Query knowledge base with context-aware responses
- **Multi-Agent System**: Specialized agents working together (Research, Analyzer, Explainability, Grounding)
- **Explainable AI**: Transparent reasoning chains, confidence scores, and source attribution
- **Grounding Verification**: Ensures responses are based on factual source material
- **Dual LLM Support**: Switch between Custom API (genailab.tcs.in with DeepSeek-V3) and Ollama (llama3.2)
- **Vector Search**: ChromaDB for semantic document retrieval

### Application Features
- **Role-Based Access Control (RBAC)**: Admin, Analyst, and Viewer roles with granular permissions
- **Document Management**: Upload and process PDF, TXT, CSV, DOCX files
- **Conversational AI Interface**: Interactive chat with message history
- **Agent Monitoring**: Real-time agent activity and execution logs
- **Confidence Scoring**: Quantified confidence in AI responses
- **Source Citations**: Track which documents contributed to each response

## 📁 Project Structure

```
.
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── agents/            # Multi-agent system
│   │   │   ├── base_agents.py
│   │   │   └── orchestrator.py
│   │   ├── api/v1/            # REST API endpoints
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   ├── agents.py
│   │   │   ├── admin.py
│   │   │   └── explainability.py
│   │   ├── auth/              # Authentication & Authorization
│   │   │   ├── security.py
│   │   │   └── schemas.py
│   │   ├── database/          # SQLite database models
│   │   │   ├── models.py
│   │   │   └── db.py
│   │   ├── rag/               # RAG pipeline
│   │   │   ├── document_processor.py
│   │   │   └── retriever.py
│   │   ├── services/          # Core services
│   │   │   ├── llm_service.py
│   │   │   └── vector_store.py
│   │   └── config.py
│   ├── scripts/
│   │   └── generate_synthetic_data.py
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/                   # Next.js Frontend
    ├── app/
    │   ├── auth/              # Authentication pages
    │   │   ├── login/
    │   │   └── register/
    │   └── dashboard/         # Main application
    │       ├── page.tsx
    │       └── layout.tsx
    ├── components/ui/         # Reusable UI components
    ├── lib/
    │   ├── api.ts             # API client
    │   ├── auth-context.tsx   # Authentication context
    │   └── utils.ts
    ├── package.json
    └── next.config.js
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- (Optional) Ollama for local LLM

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Create and activate virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

**⚠️ Important: LLM Provider Configuration**

Before running the application, you need to configure an LLM provider. Without this, document uploads will fail with "RBAC: access denied" error.

📖 **See [API_CONFIGURATION.md](./API_CONFIGURATION.md) for detailed setup instructions**

**Quick Setup Options**:

**Option A: Use Ollama (Recommended for development)**
```bash
brew install ollama
ollama pull llama3.2
ollama serve
# Then select "Ollama" provider in the UI
```

**Option B: Use Custom API (Requires API key)**
```bash
# Add to backend/.env
CUSTOM_LLM_API_KEY=your-genailab-api-key
```

**Important environment variables**:
```env
# Custom LLM API (Required if using Custom provider)
CUSTOM_LLM_API_KEY=your-genailab-api-key

# Ollama (Required if using Ollama provider)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Database
DATABASE_URL=sqlite:///./rag_agents.db

# JWT Secret (Change in production)
SECRET_KEY=your-secret-key-change-this-in-production
```

5. **Initialize database and create synthetic data**:
```bash
# Run the main application (creates database with default users)
python main.py

# In another terminal, generate synthetic documents
python scripts/generate_synthetic_data.py
```

6. **Start the backend server**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Configure environment**:
```bash
# .env.local is already created
# Verify the API URL points to your backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Start the development server**:
```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

## 📖 Frontend Documentation

The frontend has **comprehensive documentation** with visual diagrams covering all aspects of the application. Perfect for developers who need to understand or extend the system.

### 📚 Main Documentation
Start here: **[Frontend Documentation](./frontend/DOCUMENTATION.md)**

This serves as the entry point with:
- Technology stack overview (Next.js, TypeScript, Material-UI)
- Architecture diagrams
- Complete project structure
- Quick start guide
- Navigation to all detailed guides

### 🔑 Core Guides

| Guide | Description |
|-------|-------------|
| **[Authentication](./frontend/docs/guides/AUTHENTICATION.md)** | JWT flows, RBAC system, route protection, permissions |
| **[API Integration](./frontend/docs/guides/API_INTEGRATION.md)** | HTTP client, interceptors, SSE streaming, error handling |
| **[State Management](./frontend/docs/guides/STATE_MANAGEMENT.md)** | Context providers, Zustand store, data flow patterns |
| **[Theming & Styling](./frontend/docs/guides/THEMING_STYLING.md)** | MUI theme system, dark/light mode, responsive design |
| **[Components & Utilities](./frontend/docs/guides/COMPONENTS_UTILITIES.md)** | Reusable components reference and utility functions |
| **[Development Guide](./frontend/docs/guides/DEVELOPMENT_GUIDE.md)** | Step-by-step tutorials for extending the application |

### 🎯 Feature Documentation

| Feature | Description |
|---------|-------------|
| **[Chat Interface](./frontend/docs/features/CHAT.md)** | Deep dive into chat with streaming, agents, and citations |
| **[Features Overview](./frontend/docs/features/FEATURES_OVERVIEW.md)** | Documents, OCR, Explainability, Admin Panel, Utilities |

### 🏗️ Architecture

| Resource | Description |
|----------|-------------|
| **[Architecture Patterns](./frontend/docs/ARCHITECTURE_PATTERNS.md)** | Design patterns, code organization, best practices |

**Key Highlights:**
- 📊 **50+ Visual Diagrams**: Mermaid.js diagrams for architecture, flows, and patterns
- 💻 **100+ Code Examples**: Real-world examples from the codebase
- 📝 **4,500+ Lines**: Comprehensive coverage of every aspect
- 🎓 **Tutorial-Based**: Step-by-step guides for common tasks

Perfect for:
- ✅ First-time contributors understanding the codebase
- ✅ Developers extending features or adding pages
- ✅ Architects reviewing design patterns
- ✅ Anyone needing to understand authentication, API integration, or state management

## 👤 Default Users

The system comes with three pre-configured users:

| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| Admin | `admin` | `admin123` | Full system access |
| Analyst | `analyst1` | `analyst123` | Document & agent access |
| Viewer | `viewer1` | `viewer123` | Read-only access |

## 📚 Key AI Concepts Implemented

### 1. **Retrieval Augmented Generation (RAG)**
- Documents are chunked and embedded into vector space
- User queries retrieve relevant context
- LLM generates responses grounded in retrieved documents
- Source attribution shows which documents were used

### 2. **Multi-Agent System**
- **ResearchAgent**: Retrieves relevant documents from knowledge base
- **AnalyzerAgent**: Analyzes data and generates insights
- **ExplainabilityAgent**: Provides transparency into AI decision-making
- **GroundingAgent**: Verifies responses are based on source material

### 3. **Explainable AI (XAI)**
- **Confidence Scoring**: Quantified certainty in responses
- **Reasoning Chains**: Step-by-step decision process
- **Source Attribution**: Citations to source documents
- **Grounding Evidence**: Verification that responses are factually supported
- **Adjustable Levels**: Basic, Detailed, or Debug explanations

### 4. **Grounding**
- Prevents AI hallucinations by ensuring responses cite sources
- Verification step checks response accuracy against retrieved documents
- Confidence scores reflect quality of grounding

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user
- `PUT /api/v1/auth/me` - Update profile

### Chat
- `POST /api/v1/chat/message` - Send message (RAG + Multi-Agent)
- `GET /api/v1/chat/conversations` - List conversations
- `GET /api/v1/chat/conversations/{id}/messages` - Get messages

### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/` - List documents
- `DELETE /api/v1/documents/{id}` - Delete document

### Agents
- `GET /api/v1/agents/status` - Agent system status
- `GET /api/v1/agents/logs` - Agent execution logs

### Explainability
- `GET /api/v1/explain/message/{id}` - Get explanation for message
- `GET /api/v1/explain/conversation/{id}/confidence` - Confidence trend

### Admin
- `GET /api/v1/admin/users` - List users
- `POST /api/v1/admin/users` - Create user
- `GET /api/v1/admin/stats` - System statistics

## 🛠️ Configuration Options

### LLM Provider Selection
Users can choose between:
- **Custom API**: genailab.tcs.in with DeepSeek-V3 model
- **Ollama**: Local LLM (llama3.2)

Configure in user profile or via API:
```python
{
  "preferred_llm": "custom"  # or "ollama"
}
```

### Explainability Levels
- **Basic**: Simple explanations for end users
- **Detailed**: Comprehensive reasoning for analysts
- **Debug**: Technical details for developers

### RAG Settings
```env
CHUNK_SIZE=1000              # Document chunk size
CHUNK_OVERLAP=200            # Overlap between chunks
MAX_RETRIEVAL_DOCS=5         # Max documents retrieved
SIMILARITY_THRESHOLD=0.7     # Minimum similarity score
```

## 🧪 Testing the System

### 1. Upload Documents
- Login as `analyst1` or `admin`
- Navigate to Documents
- Upload sample PDF/TXT files
- Wait for processing to complete

### 2. Chat with RAG
- Navigate to Chat
- Ask questions about uploaded documents
- Example: "What is explainable AI?"
- View sources, confidence scores, and explanations

### 3. Monitor Agents
- Check Agents page to see execution logs
- View which agents participated in each response
- Analyze reasoning chains and confidence levels

### 4. Explainability Dashboard
- View detailed explanations for any message
- See confidence trends across conversations
- Inspect grounding verification results

## 🔒 Security

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: Bcrypt for password storage
- **Role-Based Access**: Granular permissions per resource
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **CORS Configuration**: Configurable allowed origins

## 📈 Scaling Considerations

### Current Implementation
- SQLite database (suitable for development/demo)
- In-process ChromaDB (suitable for small datasets)
- Synchronous document processing

### Production Recommendations
- Use PostgreSQL or MySQL for production database
- Deploy ChromaDB as a separate service
- Add background job queue (Celery/Redis) for document processing
- Implement response caching
- Add rate limiting
- Use production-grade web server (Gunicorn/Uvicorn workers)

## 🛠️ Database Management

### Reset All Databases

**⚠️ WARNING: This will delete ALL data!**

A comprehensive utility is provided to reset all databases and files:

```bash
# Run the interactive reset utility
./reset_all_dbs.sh

# Or directly with Python
cd backend
python scripts/reset_all_databases.py
```

**Options available:**
1. **Complete Reset** - Delete all databases, ChromaDB, uploaded files, and tokens
2. **SQLite Only** - Delete all SQLite databases (primary + company-specific)
3. **ChromaDB Only** - Delete the vector database
4. **Uploads Only** - Delete all uploaded files

**What gets deleted:**
- 📁 Primary database (`data/data_store.db`)
- 📁 Company-specific databases (`data/company_*.db`)
- 📁 ChromaDB vector store (`chroma_db/`)
- 📁 Uploaded files (`uploads/`)
- 📁 Token files (`token/`)

After reset:
- Restart the backend server
- Databases will be recreated automatically
- Default users will be restored
- Upload new documents as needed

### Reset Single Database

To reset only the primary database schema (keeps files):

```bash
cd backend
python scripts/reset_database.py
```

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.9+)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check .env file exists and has required values
- Look for port conflicts (default: 8000)

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Clear node_modules: `rm -rf node_modules && npm install`
- Verify API_URL in .env.local

### Documents not processing
- Check file size limits (default: 10MB)
- Verify file extensions are allowed (.pdf, .txt, .csv, .docx)
- Check backend logs for processing errors
- Ensure ChromaDB directory has write permissions

### LLM errors
- **Custom API**: Verify API key is correct in .env
- **Ollama**: Ensure Ollama is running (`ollama serve`)
- Check network connectivity
- Review backend logs for specific error messages

### Database Issues
- Try resetting databases with `./reset_all_dbs.sh`
- Check file permissions on data directory
- Verify SQLite is not locked by another process

## 📝 License

This project is for demonstration and educational purposes.

## 🤝 Contributing

This is a demonstration project. For production use, consider:
- Adding comprehensive test coverage
- Implementing CI/CD pipelines
- Adding monitoring and alerting
- Enhancing security measures
- Optimizing performance

## 📞 Support

For issues or questions:
1. Check API documentation at `/docs`
2. Review backend logs
3. Inspect browser console for frontend errors
4. Verify environment configuration

---

**Built with**: FastAPI, Next.js, LangChain, ChromaDB, SQLAlchemy, TypeScript, Tailwind CSS
