# Database Architecture Documentation

## Overview

The database layer implements a **multi-tenant architecture** with automatic context switching to ensure data isolation between companies while maintaining efficient resource usage.

## Architecture Pattern

```
┌──────────────────────────────────────────────────────────────┐
│                     Primary Database                          │
│                   (primary_database.db)                       │
├──────────────────────────────────────────────────────────────┤
│  • All user accounts                                          │
│  • Company records                                            │
│  • Roles & Permissions                                        │
│  • Super admin data                                           │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ User authenticates
                            │ JWT token issued with company_id
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                    Database Middleware                         │
│                (app/database/session.py)                       │
├───────────────────────────────────────────────────────────────┤
│  • Extracts company_id from JWT token                         │
│  • Sets database context                                      │
│  • Routes queries to appropriate database                     │
└───────────────────────────┬───────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌────────────────┐                    ┌────────────────┐
│   Company 1    │                    │   Company 2    │
│   Database     │                    │   Database     │
│ (company_1.db) │                    │ (company_2.db) │
├────────────────┤                    ├────────────────┤
│ • Documents    │                    │ • Documents    │
│ • Conversations│                    │ • Conversations│
│ • Messages     │                    │ • Messages     │
│ • Agent Logs   │                    │ • Agent Logs   │
│ • Token Usage  │                    │ • Token Usage  │
│ • Reports      │                    │ • Reports      │
│ • Profiles     │                    │ • Profiles     │
└────────────────┘                    └────────────────┘
```

## Database Context Switching

### How It Works

1. **User logs in** → JWT token generated with `username`
2. **Request arrives** with JWT token in `Authorization` header
3. **Middleware extracts token** → decodes to get `username`
4. **Queries primary database** to get user record and `company_id`
5. **Sets context** to company database:
   ```python
   set_database_context(f"company_{company_id}.db")
   ```
6. **All subsequent queries** execute against company database
7. **Request completes** → context cleared

### Special Case: Super Admins

Super admins **always use the primary database**:

```python
if user.role.name == "super_admin":
    # Use primary database
    set_database_context("primary")
else:
    # Use company database
    set_database_context(f"company_{user.company_id}")
```

### Implementation

**File**: `app/database/session.py`

```python
from contextvars import ContextVar

# Context variable to track current database
_current_database: ContextVar[str] = ContextVar("current_database", default="primary")

def set_database_context(db_name: str):
    """Set the current database context."""
    _current_database.set(db_name)

def get_database_context() -> str:
    """Get the current database context."""
    return _current_database.get()

def clear_database_context():
    """Clear the database context."""
    _current_database.set("primary")

def get_db_session(db_name: str = None):
    """Get database session for specified database."""
    if db_name is None:
        db_name = get_database_context()

    engine = _get_or_create_engine(db_name)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
```

### Database Engine Management

```python
# Engine cache to avoid recreating connections
_engines = {}

def _get_or_create_engine(db_name: str):
    """Get or create SQLAlchemy engine for database."""
    if db_name not in _engines:
        db_path = get_database_path(db_name)

        _engines[db_name] = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # For SQLite
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,     # Check connection before use
            pool_recycle=3600       # Recycle connections after 1 hour
        )

    return _engines[db_name]
```

---

## Data Models

### Primary Database Models

#### 1. User

**Purpose**: User accounts and authentication.

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)

    # Company association
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="users")

    # Role association
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")

    # User preferences
    preferred_llm = Column(String, default="custom")  # custom, ollama, openai
    explainability_level = Column(String, default="detailed")  # basic, detailed, debug

    # Onboarding
    has_completed_onboarding = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
```

**Relationships**:
- Belongs to one `Company`
- Has one `Role`
- Has many `Conversations` (in company database)
- Has many `Documents` (in company database)

---

#### 2. Company

**Purpose**: Organization/tenant records.

```python
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    industry = Column(String)  # ITeS, Manufacturing, Hospitality, etc.

    # Database reference
    database_name = Column(String, unique=True)  # e.g., "company_1.db"

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="company")
```

---

#### 3. Role

**Purpose**: User roles for RBAC.

```python
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # super_admin, admin, analyst, viewer
    description = Column(String)

    # Relationships
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
```

**Default Roles**:
- `super_admin`: Full system access
- `admin`: Company administration
- `analyst`: Can create reports, chat, upload documents
- `viewer`: Read-only access

---

#### 4. Permission

**Purpose**: Fine-grained access control.

```python
class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    resource = Column(String, nullable=False)  # documents, reports, users, etc.
    action = Column(String, nullable=False)    # create, read, update, delete, generate, etc.
    description = Column(String)

    # Relationships
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
```

**Format**: `resource:action`

**Examples**:
- `documents:create`
- `documents:read`
- `reports:generate`
- `users:manage`
- `admin:access`

---

#### 5. RolePermission

**Purpose**: Many-to-many relationship between roles and permissions.

```python
class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), primary_key=True)
```

---

### Company Database Models

These models exist in each company's database:

#### 1. Document

**Purpose**: Document metadata and processing status.

```python
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    file_type = Column(String)

    # Scope
    scope = Column(String, default="user")  # global, company, user

    # Processing
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    is_processed = Column(Boolean, default=False)

    # LLM-generated metadata
    summary = Column(Text)
    keywords = Column(JSON)  # List of keywords
    topics = Column(JSON)    # List of topics
    content_type = Column(String)  # report, article, manual, etc.

    # Ownership
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer)  # Reference to primary DB

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
```

**Processing Lifecycle**:
1. `pending`: Just uploaded
2. `processing`: Text extraction and metadata generation in progress
3. `completed`: Ready for use
4. `failed`: Processing error occurred

---

#### 2. DocumentChunk

**Purpose**: Text chunks with embedding references.

```python
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    # Chunk data
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)

    # Embedding reference
    embedding_id = Column(String, unique=True)  # ID in ChromaDB

    # Metadata
    page_number = Column(Integer)  # For PDFs

    # Relationships
    document = relationship("Document", back_populates="chunks")
```

**Note**: Actual embeddings stored in ChromaDB, not in SQLite.

---

#### 3. Conversation

**Purpose**: Chat conversation sessions.

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    title = Column(String)

    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer)

    # Configuration
    llm_provider = Column(String, default="custom")  # Which LLM used

    # Document scope (optional)
    selected_document_ids = Column(JSON)  # List of document IDs to scope retrieval

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
```

---

#### 4. Message

**Purpose**: Individual messages in conversations.

```python
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)

    # Message content
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)

    # AI metadata (for assistant messages)
    confidence = Column(Float)
    sources = Column(JSON)  # List of source documents
    reasoning_chain = Column(JSON)  # Step-by-step reasoning
    low_confidence_warning = Column(Boolean, default=False)

    # Token tracking
    token_usage = Column(JSON)  # {prompt_tokens, completion_tokens, total_tokens}

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
```

---

#### 5. AgentLog

**Purpose**: Detailed agent execution logs.

```python
class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True)

    # Agent info
    agent_type = Column(String, nullable=False)  # research, grounding, explainability, etc.
    operation = Column(String)  # retrieve, verify, explain, etc.

    # Execution data
    input_data = Column(JSON)
    output_data = Column(JSON)
    confidence = Column(Float)

    # Council voting (if applicable)
    is_council_vote = Column(Boolean, default=False)
    vote_data = Column(JSON)  # {agent, temperature, vote, confidence, reasoning}

    # Performance
    execution_time_ms = Column(Float)
    token_usage = Column(JSON)

    # Context
    message_id = Column(Integer, ForeignKey("messages.id"))
    user_id = Column(Integer)
    company_id = Column(Integer)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Use Cases**:
- Debugging agent behavior
- Performance monitoring
- Audit trail
- Training data collection

---

#### 6. TokenUsage

**Purpose**: Comprehensive token tracking and cost estimation.

```python
class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True)

    # Operation context
    operation_type = Column(String)  # chat, report_generation, document_processing, etc.
    operation_id = Column(String)    # ID of associated operation (message_id, report_id, etc.)

    # Token counts
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost estimation
    estimated_cost = Column(Float)

    # Provider info
    llm_provider = Column(String)  # custom, ollama, openai
    model_name = Column(String)

    # Context
    user_id = Column(Integer)
    company_id = Column(Integer)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Cost Calculation**:
```python
# Example for custom provider (DeepSeek-V3)
prompt_cost = prompt_tokens * 0.00001  # $0.01 per 1K tokens
completion_cost = completion_tokens * 0.00002  # $0.02 per 1K tokens
total_cost = prompt_cost + completion_cost
```

---

#### 7. Profile

**Purpose**: Company energy profile and sustainability data.

```python
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, unique=True)

    # Company info
    industry = Column(String)  # ITeS, Manufacturing, Hospitality
    location = Column(String)

    # Sustainability targets
    target_year = Column(Integer)  # KP1: Target year for renewable transition
    renewable_percentage_increase = Column(Float)  # KP2: Target % increase

    # Budget
    budget = Column(Float)

    # Historical data
    historical_data_uploaded = Column(Boolean, default=False)
    chroma_collection_name = Column(String)  # ChromaDB collection for historical data

    # Energy metrics
    total_consumption_kwh = Column(Float)
    current_renewable_percentage = Column(Float)
    sustainability_score = Column(Float)

    # Onboarding
    onboarding_completed = Column(Boolean, default=False)

    # Report configuration
    energy_mix_weight = Column(Float, default=0.4)
    price_optimization_weight = Column(Float, default=0.35)
    portfolio_decision_weight = Column(Float, default=0.25)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

#### 8. SavedReport

**Purpose**: Stored generated reports.

```python
class SavedReport(Base):
    __tablename__ = "saved_reports"

    id = Column(Integer, primary_key=True)
    report_id = Column(String, unique=True, nullable=False)

    # Report data
    report_type = Column(String)
    report_data = Column(JSON)  # Full report content
    title = Column(String)
    tags = Column(JSON)

    # Metadata
    confidence = Column(Float)
    token_usage = Column(JSON)

    # Ownership
    user_id = Column(Integer)
    company_id = Column(Integer)

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)
    saved_at = Column(DateTime, default=datetime.utcnow)
```

---

## Database Initialization

### Primary Database Setup

```python
from app.database.init_db import initialize_primary_database

# Create tables
initialize_primary_database()

# Creates:
# - users table
# - companies table
# - roles table
# - permissions table
# - role_permissions table

# Seeds with:
# - Default roles (super_admin, admin, analyst, viewer)
# - Default permissions
# - Super admin account
```

### Company Database Setup

```python
from app.database.init_db import initialize_company_database

# Create company database
initialize_company_database(company_id=1)

# Creates database: company_1.db
# With tables:
# - documents
# - document_chunks
# - conversations
# - messages
# - agent_logs
# - token_usage
# - profiles
# - saved_reports
```

---

## Database Migrations

Migration scripts in `backend/scripts/`:

### Running Migrations

```bash
# Migrate all company databases
python scripts/migrate_all_company_databases.py

# Migrate specific company
python scripts/migrate_company_database.py --company-id 1

# Reset all databases (DANGER: Deletes all data)
python scripts/reset_all_databases.py
```

### Migration Examples

#### Add New Column

**File**: `migrate_add_low_confidence_warning.py`

```python
def migrate_database(db_path):
    """Add low_confidence_warning column to messages table."""
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as conn:
        # Check if column exists
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("messages")]

        if "low_confidence_warning" not in columns:
            conn.execute(text(
                "ALTER TABLE messages ADD COLUMN low_confidence_warning BOOLEAN DEFAULT 0"
            ))
            conn.commit()
            print(f"✓ Added low_confidence_warning column")
```

#### Add New Table

**File**: `migrate_add_saved_reports.py`

```python
def migrate_database(db_path):
    """Add saved_reports table."""
    engine = create_engine(f"sqlite:///{db_path}")

    # Import model
    from app.database.models import SavedReport

    # Create table if not exists
    SavedReport.__table__.create(engine, checkfirst=True)

    print(f"✓ Created saved_reports table")
```

---

## Connection Pooling

### Configuration

```python
engine = create_engine(
    f"sqlite:///{db_path}",

    # Thread safety (SQLite specific)
    connect_args={"check_same_thread": False},

    # Connection pooling
    poolclass=StaticPool,  # For SQLite
    pool_size=20,          # Base connections
    max_overflow=40,       # Additional connections

    # Health checks
    pool_pre_ping=True,    # Verify connection before use

    # Connection recycling
    pool_recycle=3600,     # Recycle after 1 hour

    # Logging
    echo=False             # Set True for SQL logging
)
```

### Why StaticPool for SQLite?

SQLite has limited concurrency. `StaticPool` maintains a single connection that's reused, which works well for SQLite's locking model.

### Production Consideration

For PostgreSQL in production:

```python
engine = create_engine(
    postgresql_url,
    poolclass=QueuePool,  # Better for PostgreSQL
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

## Query Patterns

### Get User with Company and Role

```python
user = db.query(User).options(
    joinedload(User.company),
    joinedload(User.role).joinedload(Role.permissions)
).filter(User.username == username).first()

# Access:
print(user.company.name)
print(user.role.name)
print([p.resource for p in user.role.permissions])
```

### Get Documents with Chunks

```python
documents = db.query(Document).options(
    joinedload(Document.chunks)
).filter(
    Document.user_id == user_id,
    Document.is_processed == True
).all()

# Access:
for doc in documents:
    print(f"{doc.filename}: {len(doc.chunks)} chunks")
```

### Get Conversation with Messages

```python
conversation = db.query(Conversation).options(
    joinedload(Conversation.messages)
).filter(Conversation.id == conversation_id).first()

# Access:
for message in conversation.messages:
    print(f"{message.role}: {message.content}")
```

### Aggregate Token Usage by User

```python
from sqlalchemy import func

usage = db.query(
    func.sum(TokenUsage.total_tokens).label("total"),
    func.sum(TokenUsage.estimated_cost).label("cost")
).filter(
    TokenUsage.user_id == user_id,
    TokenUsage.created_at >= start_date
).first()

print(f"Total tokens: {usage.total}")
print(f"Total cost: ${usage.cost:.2f}")
```

---

## Best Practices

### 1. Always Use Context Manager

```python
# Bad
db = get_db_session()
user = db.query(User).first()
db.close()

# Good
with get_db_session() as db:
    user = db.query(User).first()
# Automatically closes
```

### 2. Use Transactions

```python
with get_db_session() as db:
    try:
        # Multiple operations
        user = User(...)
        db.add(user)

        document = Document(user_id=user.id, ...)
        db.add(document)

        # Commit all or nothing
        db.commit()
    except Exception as e:
        db.rollback()
        raise
```

### 3. Eager Loading for Related Data

```python
# Bad: N+1 query problem
documents = db.query(Document).all()
for doc in documents:
    print(doc.user.username)  # Separate query each time!

# Good: Eager load
documents = db.query(Document).options(
    joinedload(Document.user)
).all()
for doc in documents:
    print(doc.user.username)  # Already loaded
```

### 4. Index Important Columns

```python
class User(Base):
    __tablename__ = "users"

    username = Column(String, unique=True, nullable=False, index=True)  # Index!
    email = Column(String, unique=True, nullable=False, index=True)     # Index!
    company_id = Column(Integer, ForeignKey("companies.id"), index=True)  # Index!
```

### 5. Cascade Deletes

```python
class Document(Base):
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"  # Delete chunks when document deleted
    )
```

---

## Troubleshooting

### Database Locked Errors

**Symptom**: `sqlite3.OperationalError: database is locked`

**Causes**:
- Long-running transaction
- Concurrent writes to SQLite
- Insufficient timeout

**Solutions**:
1. Use shorter transactions
2. Add timeout: `connect_args={"timeout": 30}`
3. Consider PostgreSQL for production
4. Ensure transactions commit/rollback quickly

---

### Foreign Key Violations

**Symptom**: `FOREIGN KEY constraint failed`

**Causes**:
- Referenced record doesn't exist
- Wrong database context
- Cascade not configured

**Solutions**:
1. Verify referenced record exists
2. Check database context is correct
3. Add cascade rules to relationships
4. Enable foreign key constraints:
   ```python
   from sqlalchemy import event

   @event.listens_for(Engine, "connect")
   def set_sqlite_pragma(dbapi_conn, connection_record):
       cursor = dbapi_conn.cursor()
       cursor.execute("PRAGMA foreign_keys=ON")
       cursor.close()
   ```

---

### Context Not Set

**Symptom**: Queries return wrong data or no data

**Causes**:
- Middleware not executed
- Context not set before query
- Context cleared prematurely

**Solutions**:
1. Ensure middleware runs on all routes
2. Set context explicitly if needed:
   ```python
   set_database_context(f"company_{company_id}")
   ```
3. Debug with: `print(get_database_context())`

---

For more information, see:
- [Main Backend Documentation](../../README.md)
- [API Documentation](../api/README.md)
- [Configuration Guide](../../CONFIGURATION.md)
