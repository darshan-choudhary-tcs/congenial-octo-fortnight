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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    message = relationship("Message", back_populates="agent_logs")
