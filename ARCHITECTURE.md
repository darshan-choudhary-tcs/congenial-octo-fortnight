# Project Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │    Auth    │  │     Chat     │  │   Documents/Admin   │ │
│  └────────────┘  └──────────────┘  └─────────────────────┘ │
│         │                │                      │            │
└─────────┼────────────────┼──────────────────────┼────────────┘
          │                │                      │
          ▼                ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  API Endpoints                        │   │
│  │  /auth  /chat  /documents  /agents  /explainability  │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                │                      │            │
│         ▼                ▼                      ▼            │
│  ┌──────────┐   ┌─────────────────┐   ┌─────────────┐     │
│  │   Auth   │   │  RAG Pipeline   │   │   Agents    │     │
│  │ Service  │   │  ┌───────────┐  │   │ Orchestrator│     │
│  └──────────┘   │  │ Retriever │  │   └─────────────┘     │
│                 │  └───────────┘  │          │             │
│                 │  ┌───────────┐  │          ▼             │
│                 │  │ Processor │  │   ┌─────────────┐     │
│                 │  └───────────┘  │   │  Research   │     │
│                 └─────────────────┘   │  Analyzer   │     │
│                          │            │ Explainer   │     │
│                          │            │  Grounding  │     │
│                          │            └─────────────┘     │
│                          ▼                                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │               LLM Service                           │   │
│  │  ┌──────────────┐         ┌──────────────┐        │   │
│  │  │  Custom API  │         │    Ollama    │        │   │
│  │  │  (DeepSeek)  │         │  (llama3.2)  │        │   │
│  │  └──────────────┘         └──────────────┘        │   │
│  └────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │            Vector Store (ChromaDB)                  │   │
│  │  Stores embeddings for semantic search             │   │
│  └────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │            Database (SQLite)                        │   │
│  │  Users, Roles, Documents, Conversations, Agents    │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow: RAG Query with Multi-Agent System

```
1. User submits query
   │
   ▼
2. ResearchAgent retrieves relevant documents from ChromaDB
   │
   ▼
3. RAG Retriever builds context from retrieved documents
   │
   ▼
4. LLM Service generates response using context
   │
   ▼
5. GroundingAgent verifies response against sources
   │
   ▼
6. ExplainabilityAgent generates explanation
   │
   ▼
7. Response returned with:
   - Answer text
   - Source citations
   - Confidence score
   - Reasoning chain
   - Agent logs
```

## Component Responsibilities

### Backend Components

#### 1. **Authentication & Authorization**
- JWT token-based authentication
- Role-based access control (RBAC)
- Permission checks on endpoints
- User management

#### 2. **RAG Pipeline**
- **Document Processor**: Extracts text from various formats (PDF, TXT, CSV, DOCX)
- **Text Chunker**: Splits documents into chunks with overlap
- **Retriever**: Performs semantic search and retrieves relevant context
- **Generator**: Uses LLM to generate responses with retrieved context

#### 3. **Multi-Agent System**
- **ResearchAgent**: Specializes in information retrieval
- **AnalyzerAgent**: Analyzes data and generates insights
- **ExplainabilityAgent**: Provides transparency and reasoning
- **GroundingAgent**: Verifies factual accuracy
- **Orchestrator**: Coordinates agent collaboration

#### 4. **LLM Service**
- Abstracts LLM provider details
- Supports dual providers (Custom API + Ollama)
- Handles embeddings generation
- Implements retry logic and error handling

#### 5. **Vector Store**
- ChromaDB integration
- Separate collections per LLM provider
- Semantic similarity search
- Document metadata management

#### 6. **Database Layer**
- SQLAlchemy ORM models
- User, Role, Permission management
- Document and conversation tracking
- Agent execution logging

### Frontend Components

#### 1. **Authentication**
- Login/Register pages
- Auth context provider
- Protected routes
- Token management

#### 2. **Dashboard**
- Feature navigation
- User profile display
- System status overview

#### 3. **Chat Interface** (to be completed)
- Message history
- Real-time responses
- LLM provider selection
- Source display

#### 4. **Document Management** (to be completed)
- File upload interface
- Document listing
- Processing status
- Delete operations

#### 5. **Explainability Dashboard** (to be completed)
- Confidence visualizations
- Reasoning chain display
- Source attribution
- Agent activity logs

#### 6. **Admin Panel** (to be completed)
- User management
- Role assignment
- System statistics
- Configuration

## Security Layers

```
┌─────────────────────────────────────┐
│    1. CORS Configuration            │
│    - Allowed origins validation     │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│    2. JWT Authentication            │
│    - Token validation               │
│    - Expiration checking            │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│    3. Permission Authorization      │
│    - Role-based checks              │
│    - Resource-level permissions     │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│    4. Input Validation              │
│    - Pydantic schemas               │
│    - File type/size limits          │
└─────────────────────────────────────┘
```

## AI Concepts Implementation

### 1. **Retrieval Augmented Generation (RAG)**
- **Problem**: LLMs have knowledge cutoff and can hallucinate
- **Solution**: Retrieve relevant documents and use them as context
- **Benefits**: Factual responses, source attribution, up-to-date information

### 2. **Explainable AI (XAI)**
- **Problem**: AI decisions are often black boxes
- **Solution**: Provide reasoning chains, confidence scores, and explanations
- **Benefits**: Trust, accountability, debugging, bias detection

### 3. **Grounding**
- **Problem**: AI responses may not be based on provided sources
- **Solution**: Verify that responses cite and align with source material
- **Benefits**: Reduces hallucinations, ensures factual accuracy

### 4. **Multi-Agent Collaboration**
- **Problem**: Complex tasks need specialized expertise
- **Solution**: Multiple agents with different specializations work together
- **Benefits**: Better results, modularity, scalability

## Technology Stack

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: SQLite (dev), PostgreSQL (prod recommended)
- **Vector DB**: ChromaDB
- **AI/ML**: LangChain, OpenAI API
- **Auth**: python-jose, passlib
- **Document Processing**: pypdf, python-docx, pandas

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI (shadcn/ui)
- **HTTP Client**: Axios
- **State Management**: React Context + Zustand

### Infrastructure
- **LLM Providers**:
  - Custom API (genailab.tcs.in with DeepSeek-V3)
  - Ollama (llama3.2)
- **Embeddings**:
  - OpenAI-compatible embeddings API
  - Ollama embeddings

## Scalability Considerations

### Current (Demo/Development)
- SQLite for simplicity
- In-process ChromaDB
- Synchronous processing
- Single server deployment

### Production Recommendations
- PostgreSQL/MySQL for robustness
- ChromaDB as separate service
- Background job queue (Celery + Redis)
- Horizontal scaling with load balancer
- Caching layer (Redis)
- CDN for frontend assets
- Monitoring & logging (Prometheus, Grafana)
- Rate limiting & throttling

## File Organization Best Practices

### Backend
```
app/
├── agents/          # Agent logic isolated
├── api/v1/          # Versioned API routes
├── auth/            # Auth logic centralized
├── database/        # DB models & setup
├── rag/             # RAG pipeline components
├── services/        # Reusable services
└── config.py        # Configuration management
```

### Frontend
```
app/                 # Next.js app router
├── auth/           # Auth pages
├── dashboard/      # Protected pages
├── globals.css     # Global styles
components/
├── ui/             # Reusable UI components
lib/
├── api.ts          # API client
├── auth-context.tsx # Auth state
└── utils.ts        # Helper functions
```

## Next Steps for Completion

1. **Chat Interface**: Build interactive chat UI with message history
2. **Document Upload UI**: Create document management interface
3. **Explainability Dashboard**: Visualize AI reasoning and confidence
4. **Admin Panel**: User and system management interface
5. **Testing**: Add unit and integration tests
6. **Performance**: Optimize embeddings and retrieval
7. **Monitoring**: Add logging and metrics
8. **Documentation**: API documentation and user guides
