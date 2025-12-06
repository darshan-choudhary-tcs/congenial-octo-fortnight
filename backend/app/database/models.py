"""
SQLAlchemy Database Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    company = Column(String)  # Company/Organization name
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Onboarding fields
    is_first_login = Column(Boolean, default=True)
    setup_completed_at = Column(DateTime, nullable=True)
    company_database_name = Column(String, nullable=True)

    # Preferences
    preferred_llm = Column(String, default="ollama")  # custom or ollama
    explainability_level = Column(String, default="detailed")  # basic, detailed, debug

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="uploaded_by", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # admin, analyst, viewer
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    resource = Column(String)  # documents, agents, users, etc.
    action = Column(String)  # create, read, update, delete

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)  # pdf, txt, csv, docx
    file_size = Column(Integer)

    # Metadata
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    tags = Column(JSON)
    scope = Column(String, default="user")  # 'global' or 'user'

    # LLM-generated metadata
    auto_summary = Column(Text)  # AI-generated summary (200-300 words)
    auto_keywords = Column(JSON)  # Extracted keywords list
    auto_topics = Column(JSON)  # Classified topics list
    content_type = Column(String)  # Document content type (technical, legal, etc.)
    summarization_model = Column(String)  # Model used for metadata generation
    summarization_tokens = Column(Integer)  # Tokens used for summarization
    summarized_at = Column(DateTime)  # When metadata was generated

    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)

    # Statistics
    num_chunks = Column(Integer, default=0)
    num_tokens = Column(Integer, default=0)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    # Foreign keys
    uploaded_by_id = Column(Integer, ForeignKey('users.id'))

    # Relationships
    uploaded_by = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(Integer, ForeignKey('documents.id'))

    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer)
    num_tokens = Column(Integer)

    # Metadata
    page_number = Column(Integer)
    section = Column(String)

    # Embedding reference (stored in ChromaDB)
    embedding_id = Column(String)  # Reference to ChromaDB

    # Relationships
    document = relationship("Document", back_populates="chunks")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))

    # LLM configuration used
    llm_provider = Column(String)  # custom or ollama
    llm_model = Column(String)

    # Document scope for conversation
    selected_document_ids = Column(JSON)  # List of document UUIDs to search in this conversation

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(Integer, ForeignKey('conversations.id'))

    # Content
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # RAG context
    retrieved_documents = Column(JSON)  # List of document chunks used

    # Explainability data
    confidence_score = Column(Float)
    low_confidence_warning = Column(Boolean, default=False)
    reasoning_chain = Column(JSON)
    sources = Column(JSON)
    grounding_evidence = Column(JSON)

    # Agent involvement
    agents_involved = Column(JSON)  # List of agents that contributed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    agent_logs = relationship("AgentLog", back_populates="message", cascade="all, delete-orphan")

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(Integer, ForeignKey('messages.id'))

    # Agent details
    agent_name = Column(String, nullable=False)
    agent_type = Column(String)  # research, analyzer, summarizer, grounding, explainability

    # Execution details
    action = Column(String)
    input_data = Column(JSON)
    output_data = Column(JSON)

    # Performance
    execution_time = Column(Float)  # in seconds
    tokens_used = Column(Integer)

    # Status
    status = Column(String)  # success, failed, timeout
    error_message = Column(Text)

    # Explainability
    reasoning = Column(Text)
    confidence = Column(Float)

    # Council of Agents voting data
    vote_data = Column(JSON)  # Full vote details: {response, reasoning, evidence, vote_weight, temperature}
    vote_weight = Column(Float)  # Weight of this agent's vote
    consensus_score = Column(Float)  # Consensus level among all agents

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    message = relationship("Message", back_populates="agent_logs")

class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))

    # Relations
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=True, index=True)
    message_id = Column(Integer, ForeignKey('messages.id'), nullable=True, index=True)
    agent_log_id = Column(Integer, ForeignKey('agent_logs.id'), nullable=True)

    # LLM Configuration
    provider = Column(String, nullable=False, index=True)  # custom, ollama
    model = Column(String, nullable=False)
    operation_type = Column(String, nullable=False, index=True)  # chat, embedding, analysis, grounding, explanation

    # Token Counts
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    embedding_tokens = Column(Integer, default=0)

    # Cost Tracking
    estimated_cost = Column(Float, default=0.0)
    currency = Column(String, default="USD")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")
    conversation = relationship("Conversation")
    message = relationship("Message")
    agent_log = relationship("AgentLog")

class Profile(Base):
    __tablename__ = "profile"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)  # One profile per user/company

    # Company Information
    industry = Column(String, nullable=False)  # ITeS, Manufacturing, Hospitality
    location = Column(String, nullable=False)

    # Sustainability Targets
    sustainability_target_kp1 = Column(Integer, nullable=False)  # Target Year for Zero Non-renewable
    sustainability_target_kp2 = Column(Float, nullable=False)  # Percentage increase in renewable mix

    # Historical Data
    historical_data_path = Column(String, nullable=True)  # Path to uploaded CSV file

    # ChromaDB Collection Tracking
    chroma_collection_name = Column(String, nullable=True)  # Company-scoped ChromaDB collection name
    historical_data_processed_at = Column(DateTime, nullable=True)  # When historical data was ingested
    historical_data_chunk_count = Column(Integer, nullable=True, default=0)  # Number of chunks in ChromaDB

    # Budget
    budget = Column(Float, nullable=False)

    # Report Configuration (JSON)
    # Stores configurable parameters for energy report generation
    # Schema: {
    #   energy_weights: {solar, wind, hydro},
    #   price_optimization_weights: {cost, reliability, sustainability},
    #   portfolio_decision_weights: {esg_score, budget_fit, technical_feasibility},
    #   confidence_threshold, enable_fallback_options, max_renewable_sources
    # }
    report_config = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SavedReport(Base):
    __tablename__ = "saved_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # Report Metadata
    report_name = Column(String, nullable=True)  # Optional user-defined name
    report_type = Column(String, default="energy_portfolio")  # Future: different report types

    # Report Content (JSON)
    # Stores the complete generated report data
    # Schema: {
    #   availability_agent: {results, reasoning, confidence, sources},
    #   optimization_agent: {results, reasoning, confidence, sources},
    #   portfolio_agent: {results, reasoning, confidence, sources, portfolio, esg_scores, transition_roadmap},
    #   overall_confidence, reasoning_chain, execution_metadata
    # }
    report_content = Column(JSON, nullable=False)

    # Profile Snapshot (JSON)
    # Snapshot of profile data at time of report generation
    profile_snapshot = Column(JSON, nullable=False)

    # Report Configuration Snapshot (JSON)
    # Snapshot of report_config used for this generation
    config_snapshot = Column(JSON, nullable=False)

    # Execution Metadata
    overall_confidence = Column(Float, nullable=False)  # Overall report confidence score (0-1)
    execution_time = Column(Float, nullable=False)  # Total execution time in seconds
    total_tokens = Column(Integer, default=0)  # Total tokens used across all agents

    # Textual Version (JSON)
    # Stores LLM-generated narrative report and user edits
    # Schema: {
    #   generated_text: "Full narrative report...",
    #   edited_text: "User-reviewed version...",
    #   generated_at: timestamp,
    #   edited_at: timestamp,
    #   edit_count: int
    # }
    textual_version = Column(JSON, nullable=True)  # HITL textual report with edits

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
