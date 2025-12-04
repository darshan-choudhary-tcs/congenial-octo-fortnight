# Database Schema Documentation

## Table of Contents
1. [Overview](#overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Database Models](#database-models)
4. [Relationships](#relationships)
5. [Indexes and Performance](#indexes-and-performance)
6. [Data Flow](#data-flow)
7. [Migration Strategy](#migration-strategy)
8. [Best Practices](#best-practices)

---

## Overview

The application uses a **dual-database approach**:

1. **SQLite** (Relational Database)
   - User accounts, roles, permissions
   - Document metadata
   - Conversation history and messages
   - Agent execution logs
   - Token usage tracking

2. **ChromaDB** (Vector Database)
   - Document chunk embeddings
   - Semantic search capabilities
   - Multi-collection architecture

### Technology Stack

- **ORM**: SQLAlchemy 2.0
- **Relational DB**: SQLite (development/small deployments) - Upgradeable to PostgreSQL
- **Vector DB**: ChromaDB with persistent storage
- **Migration Tool**: Alembic (for future schema migrations)

---

## Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ Conversation : "creates"
    User ||--o{ Document : "uploads"
    User }o--o{ Role : "has"
    Role }o--o{ Permission : "grants"

    Conversation ||--o{ Message : "contains"
    Conversation }o--|| User : "belongs to"

    Message ||--o{ AgentLog : "triggers"
    Message }o--|| Conversation : "part of"
    Message ||--o{ TokenUsage : "tracks"

    Document ||--o{ DocumentChunk : "contains"
    Document }o--|| User : "uploaded by"

    AgentLog }o--|| Message : "logs for"
    AgentLog ||--o| TokenUsage : "tracks"

    TokenUsage }o--|| User : "belongs to"
    TokenUsage }o--o| Conversation : "part of"
    TokenUsage }o--o| Message : "part of"
    TokenUsage }o--o| AgentLog : "tracks"

    User {
        int id PK
        string username UK
        string email UK
        string hashed_password
        string full_name
        bool is_active
        datetime created_at
        datetime updated_at
        string preferred_llm
        string explainability_level
    }

    Role {
        int id PK
        string name UK
        string description
        datetime created_at
    }

    Permission {
        int id PK
        string name UK
        string description
        string resource
        string action
    }

    Document {
        int id PK
        string uuid UK
        string filename
        string file_path
        string file_type
        int file_size
        string title
        text description
        string category
        json tags
        string scope
        text auto_summary
        json auto_keywords
        json auto_topics
        string content_type
        string summarization_model
        int summarization_tokens
        datetime summarized_at
        bool is_processed
        string processing_status
        text error_message
        int num_chunks
        int num_tokens
        datetime uploaded_at
        datetime processed_at
        int uploaded_by_id FK
    }

    DocumentChunk {
        int id PK
        string uuid UK
        int document_id FK
        text content
        int chunk_index
        int num_tokens
        int page_number
        string section
        string embedding_id
    }

    Conversation {
        int id PK
        string uuid UK
        string title
        int user_id FK
        string llm_provider
        string llm_model
        json selected_document_ids
        datetime created_at
        datetime updated_at
    }

    Message {
        int id PK
        string uuid UK
        int conversation_id FK
        string role
        text content
        json retrieved_documents
        float confidence_score
        bool low_confidence_warning
        json reasoning_chain
        json sources
        json grounding_evidence
        json agents_involved
        datetime created_at
    }

    AgentLog {
        int id PK
        string uuid UK
        int message_id FK
        string agent_name
        string agent_type
        string action
        json input_data
        json output_data
        float execution_time
        int tokens_used
        string status
        text error_message
        text reasoning
        float confidence
        datetime created_at
    }

    TokenUsage {
        int id PK
        string uuid UK
        int user_id FK
        int conversation_id FK
        int message_id FK
        int agent_log_id FK
        string provider
        string model
        string operation_type
        int prompt_tokens
        int completion_tokens
        int total_tokens
        int embedding_tokens
        float estimated_cost
        string currency
        datetime created_at
    }
```

---

## Database Models

### User Model

**Table**: `users`

**Purpose**: Stores user accounts with authentication credentials and preferences.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique user identifier |
| `username` | String | Unique, Indexed, Not Null | Unique username for login |
| `email` | String | Unique, Indexed, Not Null | User's email address |
| `hashed_password` | String | Not Null | Argon2-hashed password |
| `full_name` | String | Nullable | User's full display name |
| `is_active` | Boolean | Default: True | Account activation status |
| `created_at` | DateTime | Default: UTC now | Account creation timestamp |
| `updated_at` | DateTime | Auto-update | Last profile update timestamp |
| `preferred_llm` | String | Default: "ollama" | Preferred LLM provider (custom/ollama) |
| `explainability_level` | String | Default: "detailed" | Default explainability level (basic/detailed/debug) |

**Relationships**:
- One-to-Many with `Conversation`
- One-to-Many with `Document`
- Many-to-Many with `Role` (via `user_roles`)

**Indexes**:
- `username` (Unique)
- `email` (Unique)
- `id` (Primary Key)

---

### Role Model

**Table**: `roles`

**Purpose**: Defines user roles for RBAC (admin, analyst, viewer).

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique role identifier |
| `name` | String | Unique, Not Null | Role name (admin, analyst, viewer) |
| `description` | String | Nullable | Human-readable description |
| `created_at` | DateTime | Default: UTC now | Role creation timestamp |

**Relationships**:
- Many-to-Many with `User` (via `user_roles`)
- Many-to-Many with `Permission` (via `role_permissions`)

**Default Roles**:
1. **admin**: Full system access
2. **analyst**: Document and agent access
3. **viewer**: Read-only access

---

### Permission Model

**Table**: `permissions`

**Purpose**: Granular permissions for fine-grained access control.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique permission identifier |
| `name` | String | Unique, Not Null | Permission identifier (e.g., "documents:create") |
| `description` | String | Nullable | Human-readable description |
| `resource` | String | Nullable | Resource type (documents, agents, users, etc.) |
| `action` | String | Nullable | Action type (create, read, update, delete) |

**Relationships**:
- Many-to-Many with `Role` (via `role_permissions`)

**Standard Permissions**:
- `chat:use` - Use chat functionality
- `documents:create` - Upload documents
- `documents:read` - View documents
- `documents:update` - Modify documents
- `documents:delete` - Delete documents
- `agents:execute` - Execute agents
- `agents:read` - View agent logs
- `explain:view` - View explainability data
- `metering:read` - View token usage
- `admin:full` - Full administrative access
- `users:manage` - Manage user accounts
- `roles:manage` - Manage roles and permissions
- `system:config` - Modify system configuration

---

### Document Model

**Table**: `documents`

**Purpose**: Stores document metadata and processing status.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique document identifier |
| `uuid` | String | Unique, Default: UUID4 | Publicly-exposed document ID |
| `filename` | String | Not Null | Original filename |
| `file_path` | String | Not Null | Server file path (uploads directory) |
| `file_type` | String | Nullable | File extension (pdf, docx, txt, csv) |
| `file_size` | Integer | Nullable | File size in bytes |
| `title` | String | Nullable | Document title (defaults to filename) |
| `description` | Text | Nullable | User-provided description |
| `category` | String | Nullable | Document category |
| `tags` | JSON | Nullable | User-defined tags array |
| `scope` | String | Default: "user" | Access scope ("user" or "global") |
| `auto_summary` | Text | Nullable | LLM-generated summary (200-300 words) |
| `auto_keywords` | JSON | Nullable | Extracted keywords array (top 10) |
| `auto_topics` | JSON | Nullable | Classified topics array (5 themes) |
| `content_type` | String | Nullable | Content classification (technical/legal/financial/academic/business/medical/general) |
| `summarization_model` | String | Nullable | Model used for metadata generation |
| `summarization_tokens` | Integer | Nullable | Tokens consumed for metadata |
| `summarized_at` | DateTime | Nullable | Metadata generation timestamp |
| `is_processed` | Boolean | Default: False | Processing completion flag |
| `processing_status` | String | Default: "pending" | Status (pending/processing/completed/failed) |
| `error_message` | Text | Nullable | Error details if processing failed |
| `num_chunks` | Integer | Default: 0 | Total chunks created |
| `num_tokens` | Integer | Default: 0 | Total tokens in document |
| `uploaded_at` | DateTime | Default: UTC now | Upload timestamp |
| `processed_at` | DateTime | Nullable | Processing completion timestamp |
| `uploaded_by_id` | Integer | FK to users.id | Uploader user ID |

**Relationships**:
- Many-to-One with `User` (uploaded_by)
- One-to-Many with `DocumentChunk`

**Indexes**:
- `id` (Primary Key)
- `uuid` (Unique)
- `uploaded_by_id` (Foreign Key)

**Document Scoping**:
- **user**: Private to uploading user
- **global**: Accessible to all users (requires admin permission to create)

---

### DocumentChunk Model

**Table**: `document_chunks`

**Purpose**: Stores text chunks from documents for RAG retrieval.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique chunk identifier |
| `uuid` | String | Unique, Default: UUID4 | Publicly-exposed chunk ID |
| `document_id` | Integer | FK to documents.id | Parent document ID |
| `content` | Text | Not Null | Chunk text content |
| `chunk_index` | Integer | Nullable | Sequential chunk number |
| `num_tokens` | Integer | Nullable | Token count in chunk |
| `page_number` | Integer | Nullable | Source page number (if applicable) |
| `section` | String | Nullable | Document section name |
| `embedding_id` | String | Nullable | ChromaDB embedding reference |

**Relationships**:
- Many-to-One with `Document`

**Chunking Strategy**:
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters
- **Method**: Recursive character splitting with sentence boundary preservation

---

### Conversation Model

**Table**: `conversations`

**Purpose**: Groups messages into conversation threads.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique conversation identifier |
| `uuid` | String | Unique, Default: UUID4 | Publicly-exposed conversation ID |
| `title` | String | Nullable | Conversation title |
| `user_id` | Integer | FK to users.id | Owner user ID |
| `llm_provider` | String | Nullable | LLM provider used (custom/ollama) |
| `llm_model` | String | Nullable | Specific model name |
| `selected_document_ids` | JSON | Nullable | Array of document UUIDs to scope search |
| `created_at` | DateTime | Default: UTC now | Creation timestamp |
| `updated_at` | DateTime | Auto-update | Last message timestamp |

**Relationships**:
- Many-to-One with `User`
- One-to-Many with `Message`

**Document Scoping**:
- If `selected_document_ids` is set, only search within those documents
- If null, search all accessible documents (user + global)

---

### Message Model

**Table**: `messages`

**Purpose**: Stores individual messages in conversations with RAG context.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique message identifier |
| `uuid` | String | Unique, Default: UUID4 | Publicly-exposed message ID |
| `conversation_id` | Integer | FK to conversations.id | Parent conversation ID |
| `role` | String | Not Null | Message role (user/assistant/system) |
| `content` | Text | Not Null | Message text content |
| `retrieved_documents` | JSON | Nullable | Array of retrieved document chunks |
| `confidence_score` | Float | Nullable | Response confidence (0.0-1.0) |
| `low_confidence_warning` | Boolean | Default: False | Low confidence flag (<0.30) |
| `reasoning_chain` | JSON | Nullable | Step-by-step reasoning array |
| `sources` | JSON | Nullable | Source documents array with citations |
| `grounding_evidence` | JSON | Nullable | Grounding verification details |
| `agents_involved` | JSON | Nullable | Array of agent names that processed this message |
| `created_at` | DateTime | Default: UTC now | Message timestamp |

**Relationships**:
- Many-to-One with `Conversation`
- One-to-Many with `AgentLog`
- One-to-Many with `TokenUsage`

**JSON Field Structures**:

**retrieved_documents**:
```json
[
  {
    "document_id": "uuid",
    "chunk_id": "uuid",
    "content": "text",
    "similarity_score": 0.85,
    "page_number": 3
  }
]
```

**reasoning_chain**:
```json
[
  {
    "step": 1,
    "agent": "ResearchAgent",
    "action": "retrieve_documents",
    "reasoning": "Found 5 relevant documents...",
    "execution_time": 1.2
  }
]
```

**sources**:
```json
[
  {
    "id": "doc_uuid",
    "filename": "report.pdf",
    "title": "Q3 Report",
    "relevance_score": 0.89,
    "cited_text": "Revenue increased..."
  }
]
```

**grounding_evidence**:
```json
{
  "score": 0.85,
  "verified_claims": ["Claim 1", "Claim 2"],
  "unverified_claims": ["Claim 3"],
  "evidence": ["Claim 1 verified in Source 2, page 3"]
}
```

---

### AgentLog Model

**Table**: `agent_logs`

**Purpose**: Tracks agent execution history for auditing and explainability.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique log identifier |
| `uuid` | String | Unique, Default: UUID4 | Publicly-exposed log ID |
| `message_id` | Integer | FK to messages.id | Associated message ID |
| `agent_name` | String | Not Null | Agent name (ResearchAgent, etc.) |
| `agent_type` | String | Nullable | Agent type (research/analyzer/grounding/explainability) |
| `action` | String | Nullable | Action performed |
| `input_data` | JSON | Nullable | Agent input parameters |
| `output_data` | JSON | Nullable | Agent output results |
| `execution_time` | Float | Nullable | Execution time in seconds |
| `tokens_used` | Integer | Nullable | Tokens consumed by agent |
| `status` | String | Nullable | Execution status (success/failed/timeout) |
| `error_message` | Text | Nullable | Error details if failed |
| `reasoning` | Text | Nullable | Agent's reasoning explanation |
| `confidence` | Float | Nullable | Agent's confidence score |
| `created_at` | DateTime | Default: UTC now | Execution timestamp |

**Relationships**:
- Many-to-One with `Message`
- One-to-Many with `TokenUsage`

**Agent Types**:
- **research**: Document retrieval and search
- **analyzer**: Data analysis and insights
- **grounding**: Response verification
- **explainability**: Reasoning chain generation

---

### TokenUsage Model

**Table**: `token_usage`

**Purpose**: Comprehensive token usage metering for cost tracking.

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Auto-increment | Unique usage record identifier |
| `uuid` | String | Unique, Default: UUID4 | Publicly-exposed usage ID |
| `user_id` | Integer | FK to users.id, Not Null, Indexed | User who incurred usage |
| `conversation_id` | Integer | FK to conversations.id, Nullable, Indexed | Associated conversation |
| `message_id` | Integer | FK to messages.id, Nullable, Indexed | Associated message |
| `agent_log_id` | Integer | FK to agent_logs.id, Nullable | Associated agent log |
| `provider` | String | Not Null, Indexed | LLM provider (custom/ollama) |
| `model` | String | Not Null | Specific model name |
| `operation_type` | String | Not Null, Indexed | Operation type (chat/embedding/analysis/grounding/explanation) |
| `prompt_tokens` | Integer | Default: 0 | Input tokens consumed |
| `completion_tokens` | Integer | Default: 0 | Output tokens generated |
| `total_tokens` | Integer | Default: 0 | Sum of prompt + completion |
| `embedding_tokens` | Integer | Default: 0 | Embedding tokens consumed |
| `estimated_cost` | Float | Default: 0.0 | Calculated cost in currency |
| `currency` | String | Default: "USD" | Currency code |
| `created_at` | DateTime | Default: UTC now, Indexed | Usage timestamp |

**Relationships**:
- Many-to-One with `User`
- Many-to-One with `Conversation` (nullable)
- Many-to-One with `Message` (nullable)
- Many-to-One with `AgentLog` (nullable)

**Indexes**:
- `user_id` (Foreign Key + Index for user queries)
- `conversation_id` (Foreign Key + Index)
- `message_id` (Foreign Key + Index)
- `provider` (Index for provider breakdown)
- `operation_type` (Index for operation analytics)
- `created_at` (Index for time-series queries)

**Operation Types**:
- **chat**: Main conversation responses
- **embedding**: Document embedding generation
- **analysis**: AnalyzerAgent operations
- **grounding**: GroundingAgent verification
- **explanation**: ExplainabilityAgent reasoning

**Cost Calculation**:
```python
cost = (prompt_tokens / 1_000_000) * provider_prompt_rate + \
       (completion_tokens / 1_000_000) * provider_completion_rate
```

**Provider Pricing** (per 1M tokens):
- **custom** (DeepSeek): $0.14 prompt, $0.28 completion
- **ollama**: $0.00 (local, free)

---

### Association Tables

#### user_roles

**Purpose**: Many-to-many relationship between users and roles.

| Column | Type | Constraints |
|--------|------|-------------|
| `user_id` | Integer | PK, FK to users.id |
| `role_id` | Integer | PK, FK to roles.id |

**Composite Primary Key**: (user_id, role_id)

---

#### role_permissions

**Purpose**: Many-to-many relationship between roles and permissions.

| Column | Type | Constraints |
|--------|------|-------------|
| `role_id` | Integer | PK, FK to roles.id |
| `permission_id` | Integer | PK, FK to permissions.id |

**Composite Primary Key**: (role_id, permission_id)

---

## Relationships

### User Relationships

```python
# A user can have multiple roles
user.roles  # List[Role]

# A user can own multiple conversations
user.conversations  # List[Conversation]

# A user can upload multiple documents
user.documents  # List[Document]
```

### Conversation Relationships

```python
# A conversation belongs to one user
conversation.user  # User

# A conversation contains multiple messages
conversation.messages  # List[Message]
```

### Message Relationships

```python
# A message belongs to one conversation
message.conversation  # Conversation

# A message has multiple agent logs
message.agent_logs  # List[AgentLog]

# A message has multiple token usage records
# (accessed via back-reference)
```

### Document Relationships

```python
# A document is uploaded by one user
document.uploaded_by  # User

# A document contains multiple chunks
document.chunks  # List[DocumentChunk]
```

### Cascade Behaviors

**Delete User**:
- Deletes all user's conversations (cascade)
- Deletes all user's documents (cascade)
- Removes user-role associations

**Delete Conversation**:
- Deletes all messages in conversation (cascade)

**Delete Message**:
- Deletes all agent logs for message (cascade)

**Delete Document**:
- Deletes all document chunks (cascade)
- Removes embeddings from ChromaDB (application logic)

---

## Indexes and Performance

### Primary Indexes

All tables have an auto-incrementing integer primary key (`id`).

### UUID Indexes

All main entities have a unique `uuid` column for public API exposure (prevents sequential ID enumeration attacks).

### Foreign Key Indexes

SQLAlchemy automatically creates indexes on foreign key columns for join performance.

### Custom Indexes

**User Model**:
- `username` (Unique index for login lookups)
- `email` (Unique index for email validation)

**TokenUsage Model**:
- `user_id` (Fast user usage queries)
- `conversation_id` (Conversation-level analytics)
- `message_id` (Message-level tracking)
- `provider` (Provider breakdown queries)
- `operation_type` (Operation analytics)
- `created_at` (Time-series queries, daily aggregations)

### Query Optimization Tips

1. **Eager Loading**: Use `joinedload` for related entities to avoid N+1 queries
   ```python
   db.query(User).options(joinedload(User.roles)).all()
   ```

2. **Pagination**: Always use `skip` and `limit` for large result sets
   ```python
   db.query(Document).offset(skip).limit(limit).all()
   ```

3. **Filtered Queries**: Use indexes in WHERE clauses
   ```python
   db.query(TokenUsage).filter(TokenUsage.user_id == user_id,
                                TokenUsage.created_at >= start_date).all()
   ```

4. **Aggregations**: Use SQLAlchemy's `func` for database-level aggregations
   ```python
   db.query(func.sum(TokenUsage.total_tokens)).filter(...).scalar()
   ```

---

## Data Flow

### User Registration Flow

```
1. Create User record
2. Hash password with Argon2
3. Assign default "viewer" role (via user_roles)
4. Commit transaction
```

### Document Upload Flow

```
1. Save file to disk
2. Create Document record (processing_status="processing")
3. Extract text from file
4. Generate LLM metadata (summary, keywords, topics)
   → Create TokenUsage record
5. Chunk text into DocumentChunk records
6. Generate embeddings for each chunk
   → Create TokenUsage records
7. Store embeddings in ChromaDB
8. Update Document (processing_status="completed")
9. Commit transaction
```

### Chat Message Flow

```
1. Load/Create Conversation
2. Create user Message record (role="user")
3. Execute agents (ResearchAgent, etc.)
   → Create AgentLog records
   → Create TokenUsage records per agent
4. Generate response with RAG
   → Create TokenUsage record
5. Create assistant Message record (role="assistant")
   - Store confidence_score
   - Store reasoning_chain (from agents)
   - Store sources (from retrieval)
   - Store grounding_evidence (from GroundingAgent)
6. Commit transaction
```

### Token Usage Aggregation

```
# User-level usage
SELECT SUM(total_tokens), SUM(estimated_cost)
FROM token_usage
WHERE user_id = ?
  AND created_at BETWEEN ? AND ?
GROUP BY provider, operation_type

# System-wide usage
SELECT provider, operation_type,
       SUM(total_tokens), SUM(estimated_cost),
       COUNT(*)
FROM token_usage
WHERE created_at BETWEEN ? AND ?
GROUP BY provider, operation_type
```

---

## Migration Strategy

### Current State

- Using SQLAlchemy's `Base.metadata.create_all()` for schema creation
- No formal migration system (development phase)

### Production Migration Plan

1. **Install Alembic**:
   ```bash
   pip install alembic
   alembic init alembic
   ```

2. **Configure Alembic**:
   ```python
   # alembic/env.py
   from app.database.models import Base
   target_metadata = Base.metadata
   ```

3. **Generate Initial Migration**:
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   ```

4. **Future Schema Changes**:
   ```bash
   # Modify models.py
   alembic revision --autogenerate -m "Add new column"
   alembic upgrade head
   ```

### Migration Best Practices

- **Test migrations on staging** before production
- **Backup database** before running migrations
- **Use reversible migrations** (implement `downgrade()`)
- **Avoid data loss** (e.g., make columns nullable first, then add NOT NULL constraint)
- **Version control migrations** (commit migration files to git)

---

## Best Practices

### 1. Use UUID for Public IDs

```python
# Always expose UUIDs in APIs, not integer IDs
document.uuid  # "550e8400-e29b-41d4-a716-446655440000"
# NOT
document.id  # 42 (reveals sequence information)
```

**Why**: Prevents enumeration attacks and information leakage.

### 2. Cascade Deletes

```python
# Parent-child relationships use cascade
user = relationship("User", cascade="all, delete-orphan")
```

**Why**: Automatic cleanup of related records, maintains referential integrity.

### 3. JSON Columns for Flexibility

```python
# Use JSON for dynamic/nested data
auto_keywords = Column(JSON)  # ["keyword1", "keyword2"]
```

**Why**: Avoid creating many tables for flexible schemas. But don't overuse—use relational modeling for structured queries.

### 4. Timestamp Everything

```python
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Why**: Essential for auditing, debugging, and time-series analysis.

### 5. Soft Deletes (Future Enhancement)

```python
# Consider adding soft delete instead of hard delete
is_deleted = Column(Boolean, default=False)
deleted_at = Column(DateTime, nullable=True)
```

**Why**: Allows recovery of accidentally deleted data, maintains audit trail.

### 6. Connection Pooling

```python
# In db.py
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

**Why**: Reuse database connections for better performance.

### 7. Transaction Management

```python
# Use context managers for transactions
try:
    db.add(document)
    db.flush()  # Get document.id without committing
    # Do more work
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

**Why**: Ensures data consistency and proper error handling.

### 8. Avoid N+1 Queries

```python
# Bad: N+1 query
users = db.query(User).all()
for user in users:
    print(user.roles)  # Triggers separate query per user

# Good: Eager loading
users = db.query(User).options(joinedload(User.roles)).all()
for user in users:
    print(user.roles)  # Already loaded
```

### 9. Use Enum Types (Future Enhancement)

```python
from enum import Enum

class DocumentScope(str, Enum):
    USER = "user"
    GLOBAL = "global"

scope = Column(Enum(DocumentScope), default=DocumentScope.USER)
```

**Why**: Type safety and validation at the database level.

### 10. Database Backups

```bash
# SQLite backup
sqlite3 database.db ".backup backup.db"

# Or copy file
cp database.db database.backup.$(date +%Y%m%d).db
```

**Why**: Essential for disaster recovery and data protection.

---

## ChromaDB Integration

### Collection Naming Convention

```
rag_documents_{scope}_{provider}
```

**Examples**:
- `rag_documents_global_custom` - Global docs with Custom API embeddings
- `rag_documents_user_1_custom` - User 1's docs with Custom API
- `rag_documents_global_ollama` - Global docs with Ollama embeddings
- `rag_documents_user_1_ollama` - User 1's docs with Ollama

### Embedding Storage

Each `DocumentChunk` has an `embedding_id` that references the ChromaDB document ID.

**ChromaDB Metadata** (stored with embeddings):
```python
{
    "document_id": "uuid",
    "chunk_id": "uuid",
    "document_uuid": "doc_uuid",
    "filename": "report.pdf",
    "page_number": 3,
    "chunk_index": 5,
    "user_id": 1,
    "scope": "user"
}
```

### Synchronization

When a document is deleted:
1. Delete `Document` record (cascades to `DocumentChunk`)
2. Delete embeddings from ChromaDB collections (application logic)

```python
# In document deletion logic
for chunk in document.chunks:
    if chunk.embedding_id:
        vector_store.delete_embedding(chunk.embedding_id)
```

---

## Scaling Considerations

### SQLite Limitations

- **Concurrent Writes**: Limited (single writer)
- **Size**: Works well up to ~100GB
- **Network**: Local file only

### Migration Path to PostgreSQL

When scaling beyond single-server:

1. **Install PostgreSQL**:
   ```bash
   sudo apt install postgresql
   ```

2. **Update Connection String**:
   ```python
   # From
   DATABASE_URL = "sqlite:///./database.db"

   # To
   DATABASE_URL = "postgresql://user:pass@localhost/dbname"
   ```

3. **Migrate Data**:
   ```bash
   # Export SQLite
   sqlite3 database.db .dump > dump.sql

   # Import to PostgreSQL
   psql dbname < dump.sql
   ```

4. **Update Indexes**:
   - PostgreSQL has better index types (GIN, GiST)
   - Add indexes for JSON queries
   - Add full-text search indexes

### ChromaDB Scaling

For large-scale deployments, consider migrating to:
- **Pinecone**: Managed vector database
- **Weaviate**: Open-source, horizontally scalable
- **Qdrant**: High-performance vector search

---

## Security Considerations

### Password Storage

- **Never** store plaintext passwords
- Use **Argon2** hashing (memory-hard, GPU-resistant)
- Consider adding pepper (server-side secret)

### SQL Injection Prevention

SQLAlchemy ORM provides protection, but:
- Always use parameterized queries
- Never concatenate user input into SQL strings
- Use `.filter()` methods, not raw SQL

### UUID Exposure

- Public IDs use UUIDs to prevent enumeration
- Internal IDs (integer PKs) never exposed in API

### Data Access Control

- Check `scope` field before returning documents
- Verify user ownership or admin role
- Use permission decorators on all endpoints

---

## Troubleshooting

### Common Issues

**Issue**: "Foreign key constraint failed"
```python
# Cause: Trying to delete a user with conversations
# Solution: Cascade delete is configured, ensure it's in the relationship
user = relationship("User", cascade="all, delete-orphan")
```

**Issue**: "Table already exists"
```python
# Cause: Running create_all() multiple times
# Solution: Use Alembic for migrations, or drop tables first
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
```

**Issue**: Slow queries
```python
# Cause: Missing indexes or N+1 queries
# Solution: Add indexes and use eager loading
db.query(User).options(joinedload(User.roles)).all()
```

---

## Database Maintenance

### Regular Tasks

1. **Vacuum Database** (SQLite):
   ```bash
   sqlite3 database.db "VACUUM;"
   ```

2. **Analyze Tables** (PostgreSQL):
   ```sql
   ANALYZE;
   ```

3. **Check Integrity**:
   ```bash
   sqlite3 database.db "PRAGMA integrity_check;"
   ```

4. **Monitor Size**:
   ```bash
   du -h database.db
   ```

5. **Backup Automation**:
   ```bash
   # Cron job: daily backups
   0 2 * * * cp /path/to/database.db /backups/db_$(date +\%Y\%m\%d).db
   ```

---

## Future Enhancements

1. **Soft Deletes**: Add `is_deleted` and `deleted_at` columns
2. **Audit Trail**: Separate `audit_log` table for all changes
3. **Full-Text Search**: PostgreSQL full-text indexes on document content
4. **Partitioning**: Partition `token_usage` by date for time-series optimization
5. **Read Replicas**: PostgreSQL replication for read-heavy workloads
6. **Connection Pooling**: PgBouncer for PostgreSQL connection management
7. **Database Monitoring**: Prometheus + Grafana for query performance metrics

---

## Related Documentation

- [Architecture Overview](./ARCHITECTURE.md)
- [API Reference](./API_REFERENCE.md)
- [RAG System](./RAG_SYSTEM.md)
- [Setup Guide](./guides/SETUP.md)
