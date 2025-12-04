# API Reference Documentation

## Table of Contents
1. [Authentication](#authentication)
2. [Chat & Messaging](#chat--messaging)
3. [Document Management](#document-management)
4. [Agent Monitoring](#agent-monitoring)
5. [Explainability](#explainability)
6. [Token Metering](#token-metering)
7. [Admin Operations](#admin-operations)
8. [Utility Functions](#utility-functions)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```bash
Authorization: Bearer <jwt_token>
```

### POST /auth/register

Register a new user account.

**Authentication**: Not required

**Request Body**:
```json
{
  "username": "string (required, unique)",
  "email": "string (required, valid email, unique)",
  "password": "string (required, min 8 characters)",
  "full_name": "string (optional)"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "roles": ["viewer"],
  "permissions": ["chat:use", "documents:read"],
  "created_at": "2025-12-04T10:30:00",
  "preferred_llm": "custom",
  "explainability_level": "basic"
}
```

**Errors**:
- `400 Bad Request`: Username or email already exists
- `422 Unprocessable Entity`: Invalid input format

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepass123",
    "full_name": "John Doe"
  }'
```

---

### POST /auth/login

Authenticate and receive JWT token.

**Authentication**: Not required

**Request Body**:
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "roles": ["analyst"],
    "permissions": ["chat:use", "documents:create", "agents:execute"]
  }
}
```

**Errors**:
- `401 Unauthorized`: Invalid credentials
- `400 Bad Request`: Inactive user

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepass123"
  }'
```

---

### GET /auth/me

Get current user information.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "roles": ["analyst"],
  "permissions": ["chat:use", "documents:create", "agents:execute"],
  "created_at": "2025-12-01T10:00:00",
  "preferred_llm": "custom",
  "explainability_level": "detailed"
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

---

### PUT /auth/me

Update current user profile.

**Authentication**: Required

**Request Body**:
```json
{
  "full_name": "string (optional)",
  "email": "string (optional)",
  "preferred_llm": "custom|ollama (optional)",
  "explainability_level": "basic|detailed|debug (optional)"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "newemail@example.com",
  "full_name": "John M. Doe",
  "preferred_llm": "ollama",
  "explainability_level": "debug"
}
```

---

### POST /auth/change-password

Change user password.

**Authentication**: Required

**Request Body**:
```json
{
  "current_password": "string (required)",
  "new_password": "string (required, min 8 characters)"
}
```

**Response** (200 OK):
```json
{
  "message": "Password updated successfully"
}
```

**Errors**:
- `400 Bad Request`: Incorrect current password

---

## Chat & Messaging

### POST /chat/message

Send a message and receive AI response.

**Authentication**: Required
**Permission**: `chat:use`

**Request Body**:
```json
{
  "message": "string (required, min 1 character)",
  "conversation_id": "uuid (optional, creates new if omitted)",
  "provider": "custom|ollama (optional, default: user's preference)",
  "include_grounding": "boolean (optional, default: true)",
  "selected_document_ids": ["uuid1", "uuid2"] // optional, scope search to specific docs
}
```

**Response** (200 OK):
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "660e8400-e29b-41d4-a716-446655440001",
  "response": "Based on the provided documents, the answer is... [Source 1]",
  "sources": [
    {
      "id": "doc_uuid",
      "filename": "report.pdf",
      "chunk_text": "Relevant excerpt from the document...",
      "page_number": 3,
      "relevance_score": 0.89
    }
  ],
  "confidence_score": 0.82,
  "low_confidence_warning": false,
  "grounding": {
    "score": 0.85,
    "verified_claims": 4,
    "unverified_claims": 1,
    "evidence": ["Claim 1 verified in Source 2", "..."]
  },
  "explanation": "The response was generated by...",
  "reasoning_chain": [
    {
      "step": 1,
      "agent": "ResearchAgent",
      "action": "Retrieved 5 relevant documents",
      "reasoning": "Found documents matching query keywords..."
    },
    {
      "step": 2,
      "agent": "GroundingAgent",
      "action": "Verified response accuracy",
      "reasoning": "All claims supported by sources"
    }
  ],
  "agents_involved": ["ResearchAgent", "GroundingAgent", "ExplainabilityAgent"],
  "execution_time": 3.45,
  "unavailable_documents_count": 1,
  "unavailable_documents": ["deleted_doc.pdf"]
}
```

**Errors**:
- `400 Bad Request`: Invalid provider or empty message
- `404 Not Found`: Conversation not found
- `403 Forbidden`: No permission to access conversation

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key findings in the Q3 report?",
    "provider": "custom",
    "include_grounding": true
  }'
```

---

### POST /chat/stream

Send a message with streaming response (Server-Sent Events).

**Authentication**: Required
**Permission**: `chat:use`

**Request Body**: Same as `/chat/message`

**Response** (200 OK - text/event-stream):
```
event: agent_start
data: {"agent": "ResearchAgent", "status": "started"}

event: agent_complete
data: {"agent": "ResearchAgent", "status": "completed", "execution_time": 1.2}

event: token
data: {"content": "Based on the "}

event: token
data: {"content": "Q3 report..."}

event: complete
data: {
  "conversation_id": "...",
  "message_id": "...",
  "confidence_score": 0.82,
  "sources": [...]
}

event: done
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize the report"}' \
  --no-buffer
```

---

### GET /chat/conversations

List user's conversations.

**Authentication**: Required

**Query Parameters**:
- `skip`: int (default: 0) - Pagination offset
- `limit`: int (default: 20, max: 100) - Results per page

**Response** (200 OK):
```json
{
  "conversations": [
    {
      "id": "conversation_uuid",
      "title": "Q3 Financial Analysis",
      "created_at": "2025-12-01T10:00:00",
      "updated_at": "2025-12-04T15:30:00",
      "message_count": 15
    }
  ],
  "total": 50,
  "skip": 0,
  "limit": 20
}
```

---

### GET /chat/conversations/{conversation_id}

Get conversation details with message history.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "id": "conversation_uuid",
  "title": "Q3 Financial Analysis",
  "provider": "custom",
  "created_at": "2025-12-01T10:00:00",
  "messages": [
    {
      "id": "message_uuid",
      "role": "user",
      "content": "What are the key findings?",
      "created_at": "2025-12-01T10:00:00"
    },
    {
      "id": "message_uuid_2",
      "role": "assistant",
      "content": "The key findings are...",
      "confidence_score": 0.85,
      "sources": [...],
      "created_at": "2025-12-01T10:00:05"
    }
  ],
  "selected_documents": [
    {
      "id": "doc_uuid",
      "filename": "q3_report.pdf",
      "title": "Q3 Financial Report"
    }
  ]
}
```

---

### DELETE /chat/conversations/{conversation_id}

Delete a conversation and all its messages.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "message": "Conversation deleted successfully"
}
```

---

### PUT /chat/conversations/{conversation_id}

Update conversation metadata.

**Authentication**: Required

**Request Body**:
```json
{
  "title": "string (optional)",
  "selected_document_ids": ["uuid1", "uuid2"] // optional
}
```

**Response** (200 OK):
```json
{
  "id": "conversation_uuid",
  "title": "Updated Title",
  "selected_documents": [...]
}
```

---

## Document Management

### POST /documents/upload

Upload a new document.

**Authentication**: Required
**Permission**: `documents:create`

**Request** (multipart/form-data):
```
file: File (required) - PDF, DOCX, TXT, or CSV
scope: string (optional, default: "user") - "user" or "global"
provider: string (optional, default: "custom") - LLM for metadata generation
title: string (optional) - Custom document title
description: string (optional) - Document description
category: string (optional) - Document category
```

**Response** (201 Created):
```json
{
  "id": "document_uuid",
  "filename": "financial_report.pdf",
  "title": "Q3 Financial Report",
  "description": "Quarterly financial analysis",
  "file_type": "pdf",
  "file_size": 1048576,
  "category": "financial",
  "scope": "user",
  "processing_status": "completed",
  "summary": "This document provides a comprehensive analysis of...",
  "keywords": ["revenue", "expenses", "profit", "growth", "analysis"],
  "topics": ["Financial Analysis", "Quarterly Report", "Business Performance"],
  "content_type": "financial",
  "chunk_count": 45,
  "uploaded_by": "john_doe",
  "created_at": "2025-12-04T10:30:00"
}
```

**Supported File Types**:
- `.pdf` - PDF documents
- `.docx` - Microsoft Word documents
- `.txt` - Plain text files
- `.csv` - Comma-separated values

**File Limits**:
- Maximum size: 10MB (configurable)

**Errors**:
- `400 Bad Request`: Invalid file type or size exceeded
- `500 Internal Server Error`: Processing failed

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/report.pdf" \
  -F "scope=user" \
  -F "title=Q3 Report" \
  -F "category=financial"
```

---

### GET /documents

List documents with filtering and pagination.

**Authentication**: Required
**Permission**: `documents:read`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 20, max: 100)
- `scope`: "user" | "global" | "all" (default: "all")
- `search`: string (optional) - Search in title, filename, keywords
- `category`: string (optional) - Filter by category
- `content_type`: string (optional) - Filter by content type

**Response** (200 OK):
```json
{
  "documents": [
    {
      "id": "doc_uuid",
      "filename": "report.pdf",
      "title": "Q3 Financial Report",
      "file_type": "pdf",
      "file_size": 1048576,
      "category": "financial",
      "scope": "user",
      "summary": "Brief summary...",
      "keywords": ["revenue", "expenses"],
      "topics": ["Financial Analysis"],
      "content_type": "financial",
      "chunk_count": 45,
      "uploaded_by": "john_doe",
      "created_at": "2025-12-04T10:30:00"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents?scope=user&category=financial&limit=10" \
  -H "Authorization: Bearer <token>"
```

---

### GET /documents/{document_id}

Get detailed document information.

**Authentication**: Required
**Permission**: `documents:read`

**Response** (200 OK):
```json
{
  "id": "doc_uuid",
  "filename": "report.pdf",
  "title": "Q3 Financial Report",
  "description": "Detailed analysis",
  "file_type": "pdf",
  "file_size": 1048576,
  "file_path": "/uploads/uuid.pdf",
  "category": "financial",
  "scope": "user",
  "processing_status": "completed",
  "summary": "Comprehensive quarterly financial analysis...",
  "keywords": ["revenue", "expenses", "profit", "growth"],
  "topics": ["Financial Analysis", "Business Performance"],
  "content_type": "financial",
  "chunk_count": 45,
  "uploaded_by": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe"
  },
  "created_at": "2025-12-04T10:30:00",
  "updated_at": "2025-12-04T10:35:00"
}
```

---

### DELETE /documents/{document_id}

Delete a document and all associated chunks/embeddings.

**Authentication**: Required
**Permission**: `documents:delete`

**Authorization Rules**:
- Users can delete their own documents
- Admins can delete any document
- Global documents require admin permission

**Response** (200 OK):
```json
{
  "message": "Document deleted successfully"
}
```

**Errors**:
- `404 Not Found`: Document doesn't exist
- `403 Forbidden`: Insufficient permissions

---

### POST /documents/{document_id}/regenerate-metadata

Regenerate LLM-based metadata (summary, keywords, topics) for a document.

**Authentication**: Required
**Permission**: `documents:update`

**Request Body**:
```json
{
  "provider": "custom|ollama (optional, default: custom)"
}
```

**Response** (200 OK):
```json
{
  "id": "doc_uuid",
  "summary": "Updated summary...",
  "keywords": ["new", "keywords"],
  "topics": ["Updated Topics"],
  "content_type": "technical"
}
```

---

### GET /documents/stats

Get document statistics.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "total_documents": 150,
  "user_documents": 100,
  "global_documents": 50,
  "by_type": {
    "pdf": 80,
    "docx": 40,
    "txt": 20,
    "csv": 10
  },
  "by_category": {
    "financial": 60,
    "technical": 50,
    "legal": 40
  },
  "total_size_bytes": 104857600,
  "total_chunks": 5000
}
```

---

## Agent Monitoring

### GET /agents/status

Get status of all available agents.

**Authentication**: Required
**Permission**: `agents:read`

**Response** (200 OK):
```json
{
  "total_agents": 4,
  "agents": [
    {
      "name": "ResearchAgent",
      "type": "research",
      "status": "active",
      "description": "Retrieves relevant documents using semantic search",
      "capabilities": ["document_retrieval", "metadata_filtering"]
    },
    {
      "name": "AnalyzerAgent",
      "type": "analyzer",
      "status": "active",
      "description": "Performs data analysis and generates insights",
      "capabilities": ["general_analysis", "comparative_analysis", "trend_analysis"]
    },
    {
      "name": "GroundingAgent",
      "type": "grounding",
      "status": "active",
      "description": "Verifies response accuracy against source documents",
      "capabilities": ["claim_verification", "grounding_scoring"]
    },
    {
      "name": "ExplainabilityAgent",
      "type": "explainability",
      "status": "active",
      "description": "Generates transparent reasoning chains and explanations",
      "capabilities": ["reasoning_generation", "transparency_reporting"]
    }
  ],
  "execution_history_count": 1250
}
```

---

### GET /agents/logs

Get recent agent execution logs.

**Authentication**: Required
**Permission**: `agents:read`

**Query Parameters**:
- `limit`: int (default: 50, max: 500)

**Response** (200 OK):
```json
[
  {
    "id": "log_uuid",
    "agent_name": "ResearchAgent",
    "agent_type": "research",
    "action": "retrieve_documents",
    "status": "success",
    "confidence": 0.85,
    "execution_time": 1.23,
    "reasoning": "Retrieved 5 relevant documents based on semantic similarity",
    "created_at": "2025-12-04T15:30:00"
  }
]
```

---

### GET /agents/logs/message/{message_id}

Get all agent logs for a specific message.

**Authentication**: Required
**Permission**: `agents:read`

**Response** (200 OK):
```json
[
  {
    "id": "log_uuid_1",
    "agent_name": "ResearchAgent",
    "agent_type": "research",
    "action": "retrieve_documents",
    "input_data": {"query": "What are the findings?"},
    "output_data": {"documents": [...]},
    "status": "success",
    "confidence": 0.85,
    "execution_time": 1.2,
    "reasoning": "Found relevant documents",
    "created_at": "2025-12-04T15:30:00"
  },
  {
    "id": "log_uuid_2",
    "agent_name": "GroundingAgent",
    "agent_type": "grounding",
    "action": "verify_response",
    "status": "success",
    "confidence": 0.88,
    "execution_time": 0.8,
    "reasoning": "All claims verified against sources",
    "created_at": "2025-12-04T15:30:02"
  }
]
```

---

## Explainability

### GET /explainability/message/{message_id}

Get comprehensive explainability data for a message.

**Authentication**: Required
**Permission**: `explain:view`

**Response** (200 OK):
```json
{
  "message_id": "message_uuid",
  "response": "Based on the Q3 report...",
  "explanation": "The response was generated by first retrieving relevant documents...",
  "reasoning_chain": [
    {
      "step": 1,
      "agent": "ResearchAgent",
      "action": "Document retrieval",
      "reasoning": "Searched ChromaDB using semantic similarity...",
      "documents_found": 5,
      "execution_time": 1.2
    },
    {
      "step": 2,
      "agent": "Generator",
      "action": "Response generation",
      "reasoning": "Synthesized information from retrieved documents...",
      "tokens_used": 1500
    },
    {
      "step": 3,
      "agent": "GroundingAgent",
      "action": "Verification",
      "reasoning": "Verified 4 claims against source documents...",
      "grounding_score": 0.88
    }
  ],
  "sources": [
    {
      "id": "doc_uuid",
      "filename": "q3_report.pdf",
      "relevance_score": 0.92,
      "used_in_response": true,
      "cited_text": "Revenue increased by 15%..."
    }
  ],
  "confidence_score": 0.85,
  "grounding_evidence": {
    "score": 0.88,
    "verified_claims": ["Revenue increased", "Expenses decreased"],
    "unverified_claims": ["Market share grew"],
    "evidence": ["Claim 1 verified in Source 2, page 3", "..."]
  },
  "agents_involved": ["ResearchAgent", "GroundingAgent", "ExplainabilityAgent"]
}
```

---

### GET /explainability/conversation/{conversation_id}/confidence

Get confidence score trend for a conversation.

**Authentication**: Required
**Permission**: `explain:view`

**Response** (200 OK):
```json
{
  "conversation_id": "conversation_uuid",
  "average_confidence": 0.82,
  "confidence_trend": [
    {
      "message_id": "msg_uuid_1",
      "message_number": 1,
      "confidence_score": 0.75,
      "timestamp": "2025-12-04T10:00:00"
    },
    {
      "message_id": "msg_uuid_2",
      "message_number": 2,
      "confidence_score": 0.89,
      "timestamp": "2025-12-04T10:05:00"
    }
  ],
  "low_confidence_messages": 2,
  "high_confidence_messages": 8
}
```

---

### GET /explainability/confidence/global

Get system-wide confidence statistics.

**Authentication**: Required
**Permission**: `explain:view` + `admin` role

**Query Parameters**:
- `start_date`: ISO date (optional)
- `end_date`: ISO date (optional)

**Response** (200 OK):
```json
{
  "total_messages": 5000,
  "average_confidence": 0.81,
  "confidence_distribution": {
    "0.0-0.3": 250,
    "0.3-0.5": 500,
    "0.5-0.7": 1500,
    "0.7-0.9": 2250,
    "0.9-1.0": 500
  },
  "by_provider": {
    "custom": {"average": 0.83, "count": 3000},
    "ollama": {"average": 0.78, "count": 2000}
  },
  "date_range": {
    "start": "2025-11-01",
    "end": "2025-12-04"
  }
}
```

---

## Token Metering

### GET /metering/user/{user_id}/usage

Get token usage statistics for a specific user.

**Authentication**: Required
**Permission**: `metering:read` (own data) or `admin` role (any user)

**Query Parameters**:
- `start_date`: ISO date (optional)
- `end_date`: ISO date (optional)

**Response** (200 OK):
```json
{
  "user_id": 1,
  "username": "john_doe",
  "total_tokens": 1500000,
  "total_prompt_tokens": 900000,
  "total_completion_tokens": 500000,
  "total_embedding_tokens": 100000,
  "total_cost": 42.50,
  "currency": "USD",
  "operation_breakdown": {
    "chat": 800000,
    "embedding": 500000,
    "analysis": 100000,
    "grounding": 50000,
    "explanation": 50000
  },
  "provider_breakdown": {
    "custom": 1200000,
    "ollama": 300000
  },
  "conversation_count": 50,
  "message_count": 250,
  "date_range": {
    "start": "2025-11-01",
    "end": "2025-12-04"
  }
}
```

---

### GET /metering/overall

Get system-wide token usage statistics.

**Authentication**: Required
**Permission**: `admin` role

**Query Parameters**:
- `start_date`: ISO date (optional)
- `end_date`: ISO date (optional)

**Response** (200 OK):
```json
{
  "total_users": 100,
  "total_tokens": 50000000,
  "total_cost": 1500.00,
  "currency": "USD",
  "provider_breakdown": {
    "custom": {
      "tokens": 40000000,
      "cost": 1400.00,
      "requests": 5000
    },
    "ollama": {
      "tokens": 10000000,
      "cost": 0.00,
      "requests": 2000
    }
  },
  "operation_breakdown": {
    "chat": 30000000,
    "embedding": 15000000,
    "analysis": 3000000,
    "grounding": 1000000,
    "explanation": 1000000
  },
  "top_users": [
    {
      "user_id": 5,
      "username": "power_user",
      "total_tokens": 5000000,
      "cost": 150.00
    }
  ],
  "date_range": {
    "start": "2025-11-01",
    "end": "2025-12-04"
  },
  "daily_usage": [
    {
      "date": "2025-12-01",
      "tokens": 500000,
      "cost": 15.00
    },
    {
      "date": "2025-12-02",
      "tokens": 550000,
      "cost": 16.50
    }
  ]
}
```

---

### GET /metering/conversation/{conversation_id}

Get token usage for a specific conversation.

**Authentication**: Required
**Permission**: `metering:read`

**Response** (200 OK):
```json
{
  "conversation_id": "conversation_uuid",
  "total_tokens": 50000,
  "total_prompt_tokens": 30000,
  "total_completion_tokens": 18000,
  "total_embedding_tokens": 2000,
  "total_cost": 1.50,
  "currency": "USD",
  "message_count": 20,
  "by_message": [
    {
      "message_id": "msg_uuid",
      "message_number": 1,
      "tokens": 2500,
      "cost": 0.08,
      "timestamp": "2025-12-04T10:00:00"
    }
  ],
  "by_operation": {
    "chat": 40000,
    "grounding": 5000,
    "explanation": 5000
  }
}
```

---

### GET /metering/cost-breakdown

Get detailed cost breakdown.

**Authentication**: Required
**Permission**: `admin` role

**Query Parameters**:
- `start_date`: ISO date (optional)
- `end_date`: ISO date (optional)
- `period`: "daily" | "weekly" | "monthly" (default: "daily")

**Response** (200 OK):
```json
{
  "total_cost": 1500.00,
  "currency": "USD",
  "by_provider": {
    "custom": 1400.00,
    "ollama": 0.00
  },
  "by_operation": {
    "chat": 900.00,
    "embedding": 450.00,
    "analysis": 90.00,
    "grounding": 30.00,
    "explanation": 30.00
  },
  "by_user": [
    {
      "user_id": 5,
      "username": "power_user",
      "cost": 150.00,
      "percentage": 10.0
    }
  ],
  "period": "monthly"
}
```

---

## Admin Operations

### GET /admin/users

List all users (admin only).

**Authentication**: Required
**Permission**: `admin` role

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "roles": ["analyst"],
    "permissions": ["chat:use", "documents:create"],
    "created_at": "2025-12-01T10:00:00",
    "preferred_llm": "custom",
    "explainability_level": "detailed"
  }
]
```

---

### POST /admin/users

Create a new user (admin only).

**Authentication**: Required
**Permission**: `admin` role

**Request Body**:
```json
{
  "username": "string (required)",
  "email": "string (required)",
  "password": "string (required)",
  "full_name": "string (optional)",
  "roles": ["role1", "role2"] // optional, default: ["viewer"]
}
```

**Response** (201 Created):
```json
{
  "id": 10,
  "username": "new_user",
  "email": "new@example.com",
  "roles": ["analyst"],
  "created_at": "2025-12-04T16:00:00"
}
```

---

### PUT /admin/users/{user_id}

Update a user (admin only).

**Authentication**: Required
**Permission**: `admin` role

**Request Body**:
```json
{
  "email": "string (optional)",
  "full_name": "string (optional)",
  "is_active": "boolean (optional)",
  "roles": ["role1", "role2"] // optional
}
```

**Response** (200 OK):
```json
{
  "id": 10,
  "username": "user",
  "email": "updated@example.com",
  "is_active": false,
  "roles": ["viewer"]
}
```

---

### DELETE /admin/users/{user_id}

Delete a user (admin only).

**Authentication**: Required
**Permission**: `admin` role

**Response** (200 OK):
```json
{
  "message": "User deleted successfully"
}
```

---

### GET /admin/roles

List all roles with permissions.

**Authentication**: Required
**Permission**: `admin` role

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "name": "admin",
    "description": "Full system access",
    "permissions": [
      "chat:use", "documents:create", "documents:read",
      "documents:update", "documents:delete", "agents:execute",
      "agents:read", "explain:view", "metering:read",
      "admin:full"
    ]
  }
]
```

---

### GET /admin/permissions

List all available permissions.

**Authentication**: Required
**Permission**: `admin` role

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "name": "chat:use",
    "description": "Use chat functionality"
  },
  {
    "id": 2,
    "name": "documents:create",
    "description": "Upload documents"
  }
]
```

---

### GET /admin/stats

Get system statistics (admin only).

**Authentication**: Required
**Permission**: `admin` role

**Response** (200 OK):
```json
{
  "users": {
    "total": 100,
    "active": 85,
    "inactive": 15
  },
  "documents": {
    "total": 500,
    "by_scope": {"user": 350, "global": 150},
    "total_size_bytes": 524288000
  },
  "conversations": {
    "total": 1000,
    "total_messages": 15000
  },
  "tokens": {
    "total_usage": 50000000,
    "total_cost": 1500.00
  },
  "agents": {
    "total_executions": 5000,
    "average_execution_time": 2.5
  }
}
```

---

### GET /admin/llm-config

Get current LLM configuration.

**Authentication**: Required
**Permission**: `admin` role

**Response** (200 OK):
```json
{
  "providers": {
    "custom": {
      "api_url": "https://genailab.tcs.in/chat/completions",
      "api_key": "key***123",  // masked
      "model": "deepseek-chat",
      "embedding_model": "text-embedding-3-large",
      "vision_model": "Llama-3.2-90B-Vision-Instruct"
    },
    "ollama": {
      "api_url": "http://localhost:11434",
      "model": "llama3.2",
      "embedding_model": "nomic-embed-text",
      "vision_model": "llama3.2-vision"
    }
  },
  "default_provider": "custom",
  "token_pricing": {
    "custom": {"prompt": 0.14, "completion": 0.28},
    "ollama": {"prompt": 0.0, "completion": 0.0}
  }
}
```

---

### PUT /admin/llm-config

Update LLM configuration (admin only).

**Authentication**: Required
**Permission**: `admin` role

**Request Body**:
```json
{
  "provider": "custom|ollama",
  "api_key": "string (optional)",
  "api_url": "string (optional)",
  "model": "string (optional)",
  "embedding_model": "string (optional)"
}
```

**Response** (200 OK):
```json
{
  "message": "LLM configuration updated successfully"
}
```

---

## Utility Functions

### POST /utilities/ocr

Extract text from image or PDF using OCR.

**Authentication**: Required
**Permission**: `chat:use`

**Request** (multipart/form-data):
```
file: File (required) - Image (JPG, PNG, TIFF, BMP, WEBP) or PDF
provider: string (optional, default: "custom") - "custom" or "ollama"
```

**Response** (200 OK):
```json
{
  "extracted_text": "This is the text extracted from the image...",
  "confidence": 0.92,
  "page_count": 1,
  "provider": "custom",
  "processing_time": 2.3
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/utilities/ocr \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/image.png" \
  -F "provider=custom"
```

---

### POST /utilities/ocr/batch

Process multiple images/PDFs in batch.

**Authentication**: Required
**Permission**: `chat:use`

**Request** (multipart/form-data):
```
files: File[] (required, multiple files)
provider: string (optional)
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "filename": "image1.png",
      "extracted_text": "Text from image 1...",
      "confidence": 0.92,
      "success": true
    },
    {
      "filename": "image2.png",
      "extracted_text": "Text from image 2...",
      "confidence": 0.88,
      "success": true
    }
  ],
  "total_processed": 2,
  "total_failed": 0,
  "total_time": 4.5
}
```

---

### POST /utilities/vision

Analyze image with vision model.

**Authentication**: Required
**Permission**: `chat:use`

**Request** (multipart/form-data):
```
file: File (required)
prompt: string (required) - What to analyze in the image
provider: string (optional)
```

**Response** (200 OK):
```json
{
  "analysis": "The image shows a bar chart with quarterly revenue data...",
  "confidence": 0.89,
  "provider": "custom"
}
```

---

## Error Handling

### Standard Error Response Format

All errors follow this structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "OPTIONAL_ERROR_CODE",
  "field": "optional_field_name"
}
```

### HTTP Status Codes

- **200 OK**: Request succeeded
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid input or business logic violation
- **401 Unauthorized**: Authentication required or token invalid
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource doesn't exist
- **422 Unprocessable Entity**: Validation error (Pydantic)
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected server error

### Common Error Scenarios

**Invalid Token**:
```json
{
  "detail": "Could not validate credentials"
}
```

**Permission Denied**:
```json
{
  "detail": "You don't have permission to perform this action. Required permission: documents:create"
}
```

**Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Resource Not Found**:
```json
{
  "detail": "Document not found"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. Future versions may include:

- **Per-user limits**: X requests per minute
- **IP-based limits**: Y requests per hour
- **Token budget limits**: Prevent runaway costs

### Recommended Implementation

```python
# Future rate limiting headers
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1701691200
```

---

## Pagination

List endpoints support cursor-based pagination:

**Request**:
```
GET /api/v1/documents?skip=20&limit=10
```

**Response**:
```json
{
  "documents": [...],
  "total": 150,
  "skip": 20,
  "limit": 10,
  "has_more": true
}
```

---

## Filtering & Sorting

Many list endpoints support filtering:

**Example**:
```
GET /api/v1/documents?scope=global&category=financial&search=revenue
```

**Sorting** (where available):
```
GET /api/v1/conversations?sort_by=updated_at&sort_order=desc
```

---

## Webhooks (Future Feature)

Future versions may support webhooks for:

- Document processing completed
- Conversation created
- Token budget threshold reached
- Agent execution errors

---

## API Versioning

The API uses URL-based versioning:

```
/api/v1/...  ← Current version
/api/v2/...  ← Future version
```

Breaking changes will increment the major version. The current version (v1) will be supported for at least 6 months after v2 release.

---

## OpenAPI / Swagger Documentation

Interactive API documentation is available at:

```
http://localhost:8000/docs      ← Swagger UI
http://localhost:8000/redoc     ← ReDoc
http://localhost:8000/openapi.json ← OpenAPI schema
```

---

## Best Practices

### 1. Always Include Authorization Header

```bash
curl -H "Authorization: Bearer <token>" ...
```

### 2. Handle Errors Gracefully

```javascript
try {
  const response = await fetch('/api/v1/chat/message', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({message: 'Hello'})
  });

  if (!response.ok) {
    const error = await response.json();
    console.error('API Error:', error.detail);
  }
} catch (err) {
  console.error('Network error:', err);
}
```

### 3. Use Streaming for Better UX

```javascript
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: {...},
  body: JSON.stringify({message: 'Explain this'})
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  // Process SSE events
}
```

### 4. Implement Retry Logic

```python
import time

def api_call_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # Exponential backoff
```

### 5. Cache Tokens Securely

- Store JWT tokens in httpOnly cookies or secure storage
- Never expose tokens in URLs
- Implement token refresh mechanism

---

## SDK Examples

### Python SDK Example

```python
import requests

class RAGClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}

    def send_message(self, message, conversation_id=None):
        response = requests.post(
            f'{self.base_url}/chat/message',
            headers=self.headers,
            json={
                'message': message,
                'conversation_id': conversation_id
            }
        )
        response.raise_for_status()
        return response.json()

    def upload_document(self, file_path, scope='user'):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'scope': scope}
            response = requests.post(
                f'{self.base_url}/documents/upload',
                headers=self.headers,
                files=files,
                data=data
            )
        response.raise_for_status()
        return response.json()

# Usage
client = RAGClient('http://localhost:8000/api/v1', 'your_token')
result = client.send_message('What are the findings?')
print(result['response'])
```

### JavaScript/TypeScript SDK Example

```typescript
class RAGClient {
  constructor(private baseUrl: string, private token: string) {}

  private async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    return response.json();
  }

  async sendMessage(message: string, conversationId?: string) {
    return this.request('/chat/message', {
      method: 'POST',
      body: JSON.stringify({message, conversation_id: conversationId})
    });
  }

  async uploadDocument(file: File, scope: 'user' | 'global' = 'user') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('scope', scope);

    return this.request('/documents/upload', {
      method: 'POST',
      body: formData,
      headers: {}  // Let browser set Content-Type for FormData
    });
  }
}

// Usage
const client = new RAGClient('http://localhost:8000/api/v1', token);
const result = await client.sendMessage('Summarize the report');
```

---

## Changelog

### v1.0.0 (Current)
- Initial API release
- Authentication with JWT
- Document management with RAG
- Multi-agent orchestration
- Explainability features
- Token usage metering
- OCR and vision utilities

---

For more details, see:
- [Architecture Documentation](./ARCHITECTURE.md)
- [Database Schema](./DATABASE.md)
- [RAG System](./RAG_SYSTEM.md)
- [Agent System](./AGENT_SYSTEM.md)
- [Setup Guide](./guides/SETUP.md)
