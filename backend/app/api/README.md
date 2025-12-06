# API Documentation

## Overview

The API layer provides RESTful endpoints for all system functionality, organized into logical routers for authentication, chat, documents, reports, administration, and more. All endpoints use FastAPI for automatic validation, serialization, and interactive documentation.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require JWT authentication.

### Authentication Flow

1. **Register** or have admin create account
2. **Login** to receive JWT token
3. **Include token** in all subsequent requests:
   ```
   Authorization: Bearer <token>
   ```

### Token Structure

JWT tokens contain:
- `sub`: Username
- `exp`: Expiration timestamp
- Token is signed with `SECRET_KEY`

## API Routers

### 1. Authentication API (`/auth`)

#### POST `/api/v1/auth/register`

Register a new user account.

**Request Body**:
```json
{
  "username": "john.doe@company.com",
  "email": "john.doe@company.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "company_id": 1
}
```

**Response**:
```json
{
  "id": 5,
  "username": "john.doe@company.com",
  "email": "john.doe@company.com",
  "full_name": "John Doe",
  "company_id": 1,
  "role_id": 3,
  "is_active": true,
  "preferred_llm": "custom",
  "explainability_level": "detailed"
}
```

**Status Codes**:
- `201`: User created successfully
- `400`: Validation error or user already exists
- `403`: Registration not allowed (check if invites required)

---

#### POST `/api/v1/auth/login`

Authenticate and receive JWT token.

**Request Body**:
```json
{
  "username": "john.doe@company.com",
  "password": "SecurePass123!"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 5,
    "username": "john.doe@company.com",
    "email": "john.doe@company.com",
    "full_name": "John Doe",
    "role": {
      "id": 3,
      "name": "analyst"
    },
    "company": {
      "id": 1,
      "name": "Acme Corp"
    }
  }
}
```

**Status Codes**:
- `200`: Login successful
- `401`: Invalid credentials
- `403`: Account disabled

---

#### GET `/api/v1/auth/me`

Get current user profile.

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "id": 5,
  "username": "john.doe@company.com",
  "email": "john.doe@company.com",
  "full_name": "John Doe",
  "company_id": 1,
  "role": {
    "id": 3,
    "name": "analyst",
    "permissions": [
      {"resource": "documents", "action": "create"},
      {"resource": "reports", "action": "generate"}
    ]
  },
  "preferred_llm": "custom",
  "explainability_level": "detailed",
  "has_completed_onboarding": true
}
```

---

#### PUT `/api/v1/auth/me`

Update user preferences.

**Request Body**:
```json
{
  "preferred_llm": "ollama",
  "explainability_level": "basic",
  "full_name": "John A. Doe"
}
```

**Response**:
```json
{
  "id": 5,
  "username": "john.doe@company.com",
  "preferred_llm": "ollama",
  "explainability_level": "basic",
  "full_name": "John A. Doe"
}
```

---

#### POST `/api/v1/auth/change-password`

Change user password.

**Request Body**:
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}
```

**Response**:
```json
{
  "message": "Password updated successfully"
}
```

**Status Codes**:
- `200`: Password changed
- `400`: Invalid current password
- `422`: New password doesn't meet requirements

---

### 2. Chat API (`/chat`)

#### POST `/api/v1/chat/send`

Send a message and receive AI-powered response.

**Request Body**:
```json
{
  "conversation_id": 123,
  "message": "What are the best renewable energy options for manufacturing facilities in California?",
  "selected_document_ids": [45, 67, 89],
  "use_council": false
}
```

**Parameters**:
- `conversation_id` (optional): Continue existing conversation, or create new if omitted
- `message`: User's question/message
- `selected_document_ids` (optional): Scope retrieval to specific documents
- `use_council` (optional): Use council voting for response (default: false)

**Response**:
```json
{
  "message_id": 456,
  "conversation_id": 123,
  "response": "Based on California's climate and your manufacturing context, I recommend a hybrid approach focusing on:\n\n1. **Solar PV Systems** (60-70%): California receives excellent solar irradiance...",
  "confidence": 0.87,
  "sources": [
    {
      "document_id": 45,
      "document_name": "California Renewable Energy Report 2024.pdf",
      "chunk_id": 234,
      "relevance_score": 0.92,
      "content": "Solar energy in California has shown remarkable growth...",
      "page_number": 15
    },
    {
      "document_id": 67,
      "document_name": "Manufacturing Energy Solutions.docx",
      "chunk_id": 567,
      "relevance_score": 0.85,
      "content": "Manufacturing facilities with high daytime energy consumption..."
    }
  ],
  "reasoning_chain": [
    {
      "step": 1,
      "agent": "ResearchAgent",
      "action": "Retrieved 5 relevant documents from vector store",
      "result": "Found documents on California solar, wind, and manufacturing energy"
    },
    {
      "step": 2,
      "agent": "RAGGenerator",
      "action": "Generated response using context",
      "confidence": 0.85
    },
    {
      "step": 3,
      "agent": "GroundingAgent",
      "action": "Verified response against sources",
      "grounding_score": 0.92,
      "unsupported_claims": 0
    },
    {
      "step": 4,
      "agent": "ExplainabilityAgent",
      "action": "Generated reasoning explanation",
      "confidence": 0.87
    }
  ],
  "low_confidence_warning": false,
  "token_usage": {
    "prompt_tokens": 2456,
    "completion_tokens": 387,
    "total_tokens": 2843,
    "estimated_cost": 0.0142
  },
  "metadata": {
    "llm_provider": "custom",
    "model": "deepseek-v3",
    "processing_time_ms": 3245,
    "documents_retrieved": 5,
    "unavailable_documents": 0
  }
}
```

**Status Codes**:
- `200`: Message processed successfully
- `400`: Invalid request (e.g., conversation not found)
- `401`: Unauthorized
- `403`: Insufficient permissions
- `422`: Validation error

---

#### GET `/api/v1/chat/conversations`

List user's conversations.

**Query Parameters**:
- `skip` (default: 0): Number of records to skip
- `limit` (default: 20): Maximum records to return

**Response**:
```json
{
  "conversations": [
    {
      "id": 123,
      "title": "California Manufacturing Energy Solutions",
      "created_at": "2025-12-01T10:30:00Z",
      "updated_at": "2025-12-06T14:22:00Z",
      "message_count": 8,
      "last_message_preview": "Based on California's climate...",
      "llm_provider": "custom"
    },
    {
      "id": 122,
      "title": "Solar Panel ROI Analysis",
      "created_at": "2025-11-28T09:15:00Z",
      "updated_at": "2025-11-30T16:45:00Z",
      "message_count": 5,
      "last_message_preview": "The typical payback period...",
      "llm_provider": "ollama"
    }
  ],
  "total": 15,
  "skip": 0,
  "limit": 20
}
```

---

#### GET `/api/v1/chat/conversations/{conversation_id}`

Get conversation details with message history.

**Response**:
```json
{
  "id": 123,
  "title": "California Manufacturing Energy Solutions",
  "created_at": "2025-12-01T10:30:00Z",
  "updated_at": "2025-12-06T14:22:00Z",
  "llm_provider": "custom",
  "messages": [
    {
      "id": 450,
      "role": "user",
      "content": "What renewable energy options are best for California?",
      "timestamp": "2025-12-01T10:30:00Z"
    },
    {
      "id": 451,
      "role": "assistant",
      "content": "California has excellent potential for solar and wind...",
      "confidence": 0.89,
      "sources": [...],
      "reasoning_chain": [...],
      "timestamp": "2025-12-01T10:30:15Z"
    }
  ],
  "document_scope": [45, 67, 89],
  "total_messages": 8
}
```

---

#### DELETE `/api/v1/chat/conversations/{conversation_id}`

Delete a conversation and all associated messages.

**Response**:
```json
{
  "message": "Conversation deleted successfully"
}
```

---

#### POST `/api/v1/chat/stream`

Send message with streaming response (SSE - Server-Sent Events).

**Request Body**: Same as `/chat/send`

**Response**: Server-Sent Events stream
```
data: {"type": "token", "content": "Based"}
data: {"type": "token", "content": " on"}
data: {"type": "token", "content": " California's"}
...
data: {"type": "sources", "sources": [...]}
data: {"type": "reasoning", "chain": [...]}
data: {"type": "complete", "message_id": 456}
```

---

### 3. Documents API (`/documents`)

#### POST `/api/v1/documents/upload`

Upload and process a document.

**Request**: Multipart form data
```
file: <binary file data>
scope: "user" | "company" | "global"
```

**Supported Formats**:
- PDF (.pdf)
- Word (.docx)
- Text (.txt)
- CSV (.csv)

**Response**:
```json
{
  "id": 45,
  "filename": "Energy Report 2024.pdf",
  "original_filename": "Energy Report 2024.pdf",
  "file_path": "/uploads/energy_report_2024_abc123.pdf",
  "file_size": 2456789,
  "file_type": "application/pdf",
  "scope": "company",
  "processing_status": "processing",
  "uploaded_at": "2025-12-06T15:30:00Z",
  "metadata": {
    "page_count": 45,
    "estimated_processing_time": "30-60 seconds"
  }
}
```

**Processing Flow**:
1. File uploaded and saved
2. Text extraction begins
3. LLM generates metadata (summary, keywords, topics)
4. Text chunked into segments
5. Embeddings generated and stored in ChromaDB
6. Document marked as processed

**Status Codes**:
- `201`: Upload successful, processing started
- `400`: Invalid file format or size exceeded
- `403`: Insufficient permissions
- `413`: File too large (max 10MB)

---

#### GET `/api/v1/documents`

List user's documents.

**Query Parameters**:
- `skip` (default: 0)
- `limit` (default: 50)
- `scope` (optional): Filter by scope (user/company/global)
- `status` (optional): Filter by processing status

**Response**:
```json
{
  "documents": [
    {
      "id": 45,
      "filename": "Energy Report 2024.pdf",
      "file_size": 2456789,
      "file_type": "application/pdf",
      "scope": "company",
      "processing_status": "completed",
      "is_processed": true,
      "uploaded_at": "2025-12-06T15:30:00Z",
      "chunk_count": 87,
      "summary": "Comprehensive analysis of renewable energy trends...",
      "keywords": ["solar", "wind", "renewable", "california"],
      "topics": ["Energy Policy", "Renewable Technology"]
    }
  ],
  "total": 23,
  "skip": 0,
  "limit": 50
}
```

---

#### GET `/api/v1/documents/{document_id}`

Get detailed document information.

**Response**:
```json
{
  "id": 45,
  "filename": "Energy Report 2024.pdf",
  "original_filename": "Energy Report 2024.pdf",
  "file_path": "/uploads/energy_report_2024_abc123.pdf",
  "file_size": 2456789,
  "file_type": "application/pdf",
  "scope": "company",
  "processing_status": "completed",
  "is_processed": true,
  "uploaded_at": "2025-12-06T15:30:00Z",
  "processed_at": "2025-12-06T15:31:45Z",
  "chunk_count": 87,
  "summary": "This report provides a comprehensive analysis of renewable energy trends in California for 2024...",
  "keywords": ["solar", "wind", "renewable", "california", "manufacturing"],
  "topics": ["Energy Policy", "Renewable Technology", "Climate Action"],
  "content_type": "technical_report",
  "metadata": {
    "author": "California Energy Commission",
    "page_count": 45,
    "creation_date": "2024-11-15"
  },
  "uploaded_by": {
    "id": 5,
    "username": "john.doe@company.com",
    "full_name": "John Doe"
  }
}
```

---

#### DELETE `/api/v1/documents/{document_id}`

Delete a document and all associated data.

**Response**:
```json
{
  "message": "Document deleted successfully",
  "chunks_removed": 87,
  "embeddings_removed": 87
}
```

**Note**: Removes document from:
- File system
- Database (document + chunks)
- ChromaDB (embeddings)

---

#### POST `/api/v1/documents/{document_id}/reprocess`

Reprocess a document (regenerate metadata, chunks, embeddings).

**Response**:
```json
{
  "message": "Document reprocessing started",
  "document_id": 45,
  "estimated_time": "30-60 seconds"
}
```

**Use Cases**:
- Update metadata with improved prompts
- Re-chunk with different parameters
- Regenerate embeddings with new model

---

#### GET `/api/v1/documents/{document_id}/chunks`

View document chunks for debugging/analysis.

**Query Parameters**:
- `skip` (default: 0)
- `limit` (default: 20)

**Response**:
```json
{
  "document_id": 45,
  "document_name": "Energy Report 2024.pdf",
  "chunks": [
    {
      "id": 234,
      "chunk_index": 0,
      "content": "California's renewable energy landscape has transformed dramatically...",
      "token_count": 245,
      "page_number": 1,
      "embedding_id": "doc45_chunk0",
      "similarity_score": null
    }
  ],
  "total_chunks": 87,
  "skip": 0,
  "limit": 20
}
```

---

#### POST `/api/v1/documents/upload/historical-energy`

Special endpoint for uploading historical energy consumption CSV files.

**Request**: Multipart form data
```
file: <CSV file>
```

**Expected CSV Format**:
```csv
Date,Location,Consumption_kWh,Renewable_Percentage,Cost_USD
2024-01-01,California Plant 1,12500,35.5,1250.00
```

**Response**:
```json
{
  "document_id": 50,
  "profile_updated": true,
  "analysis": {
    "total_consumption_kwh": 4560000,
    "avg_renewable_percentage": 38.2,
    "total_cost": 456000,
    "sustainability_score": 0.72,
    "anomalies_detected": [
      {
        "date": "2024-06-15",
        "issue": "Spike in consumption",
        "severity": "medium"
      }
    ],
    "optimization_insights": [
      "Consider increasing solar capacity during summer months",
      "Peak demand occurs between 2-4 PM, ideal for solar"
    ]
  },
  "chromadb_collection": "company_1_historical_energy"
}
```

**Processing**:
1. CSV validated and parsed
2. Energy-specific metadata extracted
3. Sustainability metrics calculated
4. Anomaly detection performed
5. Optimization insights generated
6. Data stored in company-specific ChromaDB collection
7. Company profile updated with analysis

---

### 4. Council API (`/council`)

#### POST `/api/v1/council/evaluate`

Submit query for multi-agent council evaluation.

**Request Body**:
```json
{
  "query": "What is the optimal renewable energy mix for a manufacturing facility in Texas?",
  "voting_strategy": "weighted_confidence",
  "debate_rounds": 2,
  "selected_document_ids": [45, 67],
  "context": {
    "industry": "manufacturing",
    "location": "Texas",
    "budget": "moderate"
  }
}
```

**Parameters**:
- `query`: Question/problem to evaluate
- `voting_strategy`:
  - `weighted_confidence` (default): Weight by confidence scores
  - `highest_confidence`: Select best single response
  - `majority`: Most common answer
  - `synthesis`: LLM combines all responses
- `debate_rounds` (optional): 1-5 rounds of refinement
- `selected_document_ids` (optional): Scope to specific documents
- `context` (optional): Additional context for agents

**Response**:
```json
{
  "query": "What is the optimal renewable energy mix...",
  "votes": [
    {
      "agent": "analytical",
      "temperature": 0.3,
      "response": "Based on Texas's energy infrastructure and manufacturing requirements, I recommend: 1) Solar PV (45-50%): Texas has excellent solar resources... 2) Wind (30-35%): West Texas wind farms offer competitive pricing... 3) Natural Gas Bridge (15-20%): For reliability during low renewable periods...",
      "confidence": 0.88,
      "reasoning": "This recommendation prioritizes cost-effectiveness and reliability while maximizing renewable adoption. Texas's deregulated energy market provides competitive pricing...",
      "supporting_evidence": [
        "Texas leads US in wind energy production",
        "Average solar irradiance: 5.5 kWh/m²/day",
        "Manufacturing facilities require 24/7 power"
      ],
      "vote_weight": 1.0
    },
    {
      "agent": "creative",
      "temperature": 0.9,
      "response": "I propose an innovative hybrid approach combining traditional renewables with emerging technologies: 1) Solar + Storage (40%): Pair PV with lithium-ion batteries... 2) Wind (25%): Leverage Texas wind corridor... 3) Green Hydrogen (15%): Pilot project for backup... 4) Grid Services (20%): Participate in demand response...",
      "confidence": 0.76,
      "reasoning": "This forward-thinking strategy positions the facility as an energy innovator while maintaining practical reliability...",
      "supporting_evidence": [
        "Battery storage costs dropped 89% since 2010",
        "Texas has 3 active hydrogen hubs",
        "Demand response can reduce costs 10-30%"
      ],
      "vote_weight": 1.0
    },
    {
      "agent": "critical",
      "temperature": 0.5,
      "response": "After analyzing risks and constraints, I recommend a conservative renewable approach: 1) Solar (40%): Proven technology with predictable ROI... 2) Wind (30%): Established in Texas with long track record... 3) Grid Power (30%): Maintain reliability during renewable gaps...",
      "confidence": 0.85,
      "reasoning": "This approach minimizes risk while achieving renewable goals. The balanced portfolio ensures manufacturing uptime...",
      "supporting_evidence": [
        "Solar PV reliability >98% in Texas",
        "Wind capacity factor: 35-40%",
        "Grid interconnection protects against downtime"
      ],
      "vote_weight": 1.0
    }
  ],
  "consensus_response": "The council recommends a balanced renewable energy portfolio for Texas manufacturing:\n\n**Recommended Mix:**\n- Solar PV: 40-45% (leveraging Texas's excellent solar resources)\n- Wind: 30-35% (utilizing competitive West Texas wind)\n- Grid/Backup: 20-25% (ensuring 24/7 reliability)\n- Future Innovation: 5-10% (battery storage or emerging tech)\n\n**Key Rationale:**\nAll three council perspectives agree on solar and wind as primary sources, with variations in allocation and backup strategies. The analytical agent emphasizes cost-effectiveness, the creative agent pushes for innovation, and the critical agent ensures reliability. The consensus balances these priorities.\n\n**Implementation Steps:**\n1. Conduct site-specific solar/wind assessment\n2. Evaluate storage options for peak shifting\n3. Negotiate PPA terms with renewable providers\n4. Maintain grid connection for reliability\n\n**Confidence Level: 0.83** (high agreement across agents)",
  "consensus_metrics": {
    "strategy_used": "weighted_confidence",
    "consensus_level": 0.82,
    "confidence_variance": 0.0036,
    "agreement_score": 0.78,
    "avg_confidence": 0.83,
    "min_confidence": 0.76,
    "max_confidence": 0.88,
    "debate_rounds_completed": 2
  },
  "sources": [
    {
      "document_id": 45,
      "document_name": "Texas Energy Infrastructure 2024.pdf",
      "relevance_score": 0.91,
      "used_by_agents": ["analytical", "critical"]
    }
  ],
  "token_usage": {
    "total_tokens": 5234,
    "by_agent": {
      "analytical": 1678,
      "creative": 1890,
      "critical": 1666
    },
    "estimated_cost": 0.0262
  },
  "processing_time_ms": 8456,
  "metadata": {
    "debate_rounds": 2,
    "agents_participated": 3,
    "documents_retrieved": 8
  }
}
```

**Status Codes**:
- `200`: Evaluation completed successfully
- `400`: Invalid voting strategy or parameters
- `401`: Unauthorized
- `403`: Council feature not enabled or insufficient permissions
- `422`: Validation error

---

### 5. Reports API (`/reports`)

#### GET `/api/v1/reports/config`

Get current report configuration (energy analysis weights).

**Response**:
```json
{
  "energy_mix_weight": 0.4,
  "price_optimization_weight": 0.35,
  "portfolio_decision_weight": 0.25,
  "min_renewable_percentage": 60,
  "max_budget_deviation": 15,
  "sustainability_priority": "high"
}
```

---

#### PUT `/api/v1/reports/config`

Update report configuration.

**Request Body**:
```json
{
  "energy_mix_weight": 0.45,
  "price_optimization_weight": 0.30,
  "portfolio_decision_weight": 0.25
}
```

**Response**: Updated configuration

**Validation**:
- Weights must sum to 1.0
- Each weight between 0.0 and 1.0
- Requires `reports:configure` permission

---

#### POST `/api/v1/reports/generate`

Generate comprehensive energy analysis report.

**Request Body**:
```json
{
  "report_type": "energy_portfolio_analysis",
  "company_profile_id": 1,
  "parameters": {
    "location": "Texas",
    "industry": "manufacturing",
    "current_consumption_kwh": 1500000,
    "budget_usd": 500000,
    "target_renewable_percentage": 75,
    "timeline_years": 5
  },
  "include_visualizations": true
}
```

**Response**:
```json
{
  "report_id": "rpt_20251206_abc123",
  "generated_at": "2025-12-06T16:45:00Z",
  "report_type": "energy_portfolio_analysis",
  "sections": {
    "executive_summary": {
      "recommendation": "Implement a hybrid solar-wind portfolio with 70% renewable mix",
      "confidence": 0.86,
      "estimated_cost": 475000,
      "projected_savings_annual": 125000,
      "payback_period_years": 3.8,
      "carbon_reduction_tons_annual": 850
    },
    "energy_availability_analysis": {
      "agent": "EnergyAvailabilityAgent",
      "confidence": 0.89,
      "findings": {
        "solar_potential": {
          "rating": "excellent",
          "capacity_factor": 0.23,
          "recommended_capacity_kw": 800,
          "annual_generation_kwh": 1613760,
          "notes": "Texas has exceptional solar irradiance, particularly in west and south regions"
        },
        "wind_potential": {
          "rating": "excellent",
          "capacity_factor": 0.38,
          "recommended_capacity_kw": 500,
          "annual_generation_kwh": 1663200,
          "notes": "West Texas wind corridor offers some of the best wind resources in the US"
        },
        "hydro_potential": {
          "rating": "limited",
          "notes": "Limited large-scale hydro opportunities; small-scale may be viable depending on site"
        },

          "rating": "moderate",
          "notes": "Agricultural waste available in rural areas, costs may be higher"
        }
      },
      "reasoning_chain": [...]
    },
    "price_optimization_analysis": {
      "agent": "PriceOptimizationAgent",
      "confidence": 0.84,
      "findings": {
        "cost_breakdown": {
          "solar_installation": 240000,
          "wind_installation": 200000,
          "energy_storage": 25000,
          "grid_connection": 10000,
          "total": 475000
        },
        "operating_costs_annual": {
          "maintenance": 8500,
          "insurance": 3200,
          "monitoring": 1200,
          "total": 12900
        },
        "revenue_opportunities": {
          "energy_cost_savings": 125000,
          "renewable_energy_credits": 15000,
          "demand_response_programs": 8000,
          "total": 148000
        },
        "roi_metrics": {
          "net_present_value": 287500,
          "internal_rate_of_return": 0.24,
          "payback_period_years": 3.8
        }
      },
      "reasoning_chain": [...]
    },
    "portfolio_mix_recommendation": {
      "agent": "EnergyPortfolioMixAgent",
      "confidence": 0.87,
      "recommendation": {
        "solar_percentage": 45,
        "wind_percentage": 30,
        "grid_renewable_percentage": 20,
        "backup_gas_percentage": 5,
        "total_renewable_percentage": 95
      },
      "justification": "This mix optimizes for reliability, cost-effectiveness, and sustainability goals. The high renewable percentage exceeds the 75% target while maintaining operational reliability...",
      "risk_assessment": {
        "technical_risks": "low",
        "financial_risks": "low-moderate",
        "regulatory_risks": "low",
        "overall_risk": "low"
      },
      "esg_score": {
        "environmental": 0.92,
        "social": 0.78,
        "governance": 0.85,
        "overall": 0.85
      },
      "reasoning_chain": [...]
    },
    "implementation_roadmap": {
      "phase_1": {
        "timeline": "Months 1-6",
        "activities": [
          "Site assessment and feasibility study",
          "Secure financing and incentives",
          "Select equipment vendors",
          "Obtain permits and approvals"
        ],
        "estimated_cost": 50000
      },
      "phase_2": {
        "timeline": "Months 7-18",
        "activities": [
          "Install solar PV system (800 kW)",
          "Install wind turbines (500 kW)",
          "Grid interconnection",
          "Testing and commissioning"
        ],
        "estimated_cost": 425000
      },
      "phase_3": {
        "timeline": "Months 19-24",
        "activities": [
          "Monitor performance",
          "Optimize operations",
          "Train staff",
          "Pursue additional incentives"
        ],
        "estimated_cost": 10000
      }
    }
  },
  "sources": [
    {
      "document_id": 45,
      "document_name": "Texas Energy Infrastructure 2024.pdf",
      "sections_referenced": ["solar_analysis", "wind_analysis"]
    }
  ],
  "token_usage": {
    "total_tokens": 8934,
    "estimated_cost": 0.0447
  },
  "metadata": {
    "generation_time_ms": 12456,
    "agents_used": 3,
    "documents_retrieved": 12,
    "config_weights": {
      "energy_mix": 0.4,
      "price_optimization": 0.35,
      "portfolio_decision": 0.25
    }
  }
}
```

**Status Codes**:
- `200`: Report generated successfully
- `400`: Invalid parameters
- `403`: Insufficient permissions
- `404`: Company profile not found
- `422`: Validation error

---

#### GET `/api/v1/reports/saved`

List saved reports.

**Query Parameters**:
- `skip` (default: 0)
- `limit` (default: 20)
- `report_type` (optional): Filter by type

**Response**:
```json
{
  "reports": [
    {
      "id": "rpt_20251206_abc123",
      "report_type": "energy_portfolio_analysis",
      "generated_at": "2025-12-06T16:45:00Z",
      "title": "Texas Manufacturing Energy Portfolio 2025",
      "summary": "Hybrid solar-wind portfolio with 95% renewable mix",
      "confidence": 0.86,
      "saved_by": "john.doe@company.com"
    }
  ],
  "total": 8,
  "skip": 0,
  "limit": 20
}
```

---

#### POST `/api/v1/reports/save`

Save a generated report.

**Request Body**:
```json
{
  "report_data": {...},  // Full report from /generate
  "title": "Texas Manufacturing Energy Portfolio 2025",
  "tags": ["texas", "manufacturing", "solar", "wind"]
}
```

**Response**:
```json
{
  "report_id": "rpt_20251206_abc123",
  "message": "Report saved successfully"
}
```

---

#### GET `/api/v1/reports/{report_id}/export`

Export report to PDF format.

**Query Parameters**:
- `format` (default: "pdf"): Export format

**Response**: Binary PDF file with headers:
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="report_texas_energy_2025.pdf"
```

---

### 6. Admin API (`/admin`)

**Note**: Most endpoints require `super_admin` or `admin` role.

#### POST `/api/v1/admin/create-admin`

Create a new admin user (super_admin only).

**Request Body**:
```json
{
  "email": "admin@newcompany.com",
  "full_name": "Jane Admin",
  "company_id": 2
}
```

**Response**:
```json
{
  "user": {
    "id": 8,
    "username": "admin@newcompany.com",
    "email": "admin@newcompany.com",
    "full_name": "Jane Admin",
    "company_id": 2,
    "role": "admin",
    "is_active": true
  },
  "temporary_password": "SecureAutoGen123!XYZ",
  "message": "Admin user created successfully. Please share the temporary password securely."
}
```

**Note**: Auto-generates secure password. User should change on first login.

---

#### GET `/api/v1/admin/users`

List all users (filtered by company for admins).

**Query Parameters**:
- `skip` (default: 0)
- `limit` (default: 50)
- `company_id` (optional, super_admin only): Filter by company
- `role` (optional): Filter by role
- `is_active` (optional): Filter by active status

**Response**:
```json
{
  "users": [
    {
      "id": 5,
      "username": "john.doe@company.com",
      "email": "john.doe@company.com",
      "full_name": "John Doe",
      "company": {
        "id": 1,
        "name": "Acme Corp"
      },
      "role": {
        "id": 3,
        "name": "analyst"
      },
      "is_active": true,
      "last_login": "2025-12-06T14:30:00Z",
      "created_at": "2025-11-15T09:00:00Z"
    }
  ],
  "total": 23,
  "skip": 0,
  "limit": 50
}
```

---

#### GET `/api/v1/admin/users/{user_id}`

Get detailed user information.

**Response**:
```json
{
  "id": 5,
  "username": "john.doe@company.com",
  "email": "john.doe@company.com",
  "full_name": "John Doe",
  "company": {
    "id": 1,
    "name": "Acme Corp",
    "industry": "Manufacturing"
  },
  "role": {
    "id": 3,
    "name": "analyst",
    "permissions": [...]
  },
  "is_active": true,
  "preferred_llm": "custom",
  "explainability_level": "detailed",
  "has_completed_onboarding": true,
  "created_at": "2025-11-15T09:00:00Z",
  "last_login": "2025-12-06T14:30:00Z",
  "statistics": {
    "total_conversations": 15,
    "total_documents_uploaded": 23,
    "total_reports_generated": 7,
    "tokens_used": 145678
  }
}
```

---

#### PUT `/api/v1/admin/users/{user_id}`

Update user details.

**Request Body**:
```json
{
  "full_name": "John A. Doe",
  "role_id": 4,
  "is_active": true,
  "email": "john.a.doe@company.com"
}
```

**Response**: Updated user object

---

#### DELETE `/api/v1/admin/users/{user_id}`

Delete a user account.

**Response**:
```json
{
  "message": "User deleted successfully",
  "conversations_deleted": 15,
  "documents_deleted": 23
}
```

**Note**: Cascades to user's conversations, messages, documents, etc.

---

#### POST `/api/v1/admin/users/{user_id}/reset-password`

Admin password reset.

**Response**:
```json
{
  "temporary_password": "NewSecurePass789!ABC",
  "message": "Password reset successfully. Please share the temporary password securely."
}
```

---

### 7. Other APIs

#### Agents API (`/agents`)

- `GET /api/v1/agents`: List available agents
- `GET /api/v1/agents/{agent_type}`: Get agent details
- `GET /api/v1/agents/logs`: View agent execution logs

#### Explainability API (`/explainability`)

- `GET /api/v1/explainability/message/{message_id}`: Get detailed explanation for a message
- `GET /api/v1/explainability/levels`: Get available explainability levels

#### Metering API (`/metering`)

- `GET /api/v1/metering/usage`: Get token usage statistics
- `GET /api/v1/metering/costs`: Get cost estimates
- `GET /api/v1/metering/by-user`: Usage by user
- `GET /api/v1/metering/by-operation`: Usage by operation type

#### Prompts API (`/prompts`)

- `GET /api/v1/prompts`: List available prompts
- `GET /api/v1/prompts/{prompt_name}`: Get specific prompt
- `POST /api/v1/prompts`: Create custom prompt (admin)
- `PUT /api/v1/prompts/{prompt_name}`: Update prompt (admin)

#### Profile API (`/profile`)

- `GET /api/v1/profile`: Get company energy profile
- `PUT /api/v1/profile`: Update company profile
- `POST /api/v1/profile/onboarding`: Complete onboarding

---

## Common Response Patterns

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "detail": "Error message description",
  "error_code": "VALIDATION_ERROR",
  "field": "email"
}
```

### Pagination Response
```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 20,
  "has_more": true
}
```

---

## Error Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error, invalid input)
- `401`: Unauthorized (missing or invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `409`: Conflict (duplicate resource)
- `413`: Payload Too Large
- `422`: Unprocessable Entity (Pydantic validation error)
- `429`: Too Many Requests (rate limit)
- `500`: Internal Server Error
- `503`: Service Unavailable

---

## Rate Limiting

(Not currently implemented - recommendation for production)

Suggested limits:
- Authentication: 5 requests/minute
- Chat: 20 requests/minute
- Document upload: 10 requests/hour
- Report generation: 5 requests/hour
- General API: 100 requests/minute

---

## API Versioning

Current version: `v1`

Base path: `/api/v1/`

Future versions will be available at `/api/v2/`, etc., with deprecation notices.

---

## Testing the API

### Using curl

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password"}'

# Use token
TOKEN="eyJhbGciOiJIUzI1..."
curl -X GET http://localhost:8000/api/v1/chat/conversations \
  -H "Authorization: Bearer $TOKEN"
```

### Using Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Send chat message
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://localhost:8000/api/v1/chat/send",
    json={
        "message": "What are the best renewable energy options?",
        "use_council": False
    },
    headers=headers
)
print(response.json())
```

### Using Swagger UI

Navigate to http://localhost:8000/docs for interactive API testing.

---

## WebSocket Support

(Planned feature - not currently implemented)

Future support for real-time updates:
- Live chat streaming
- Document processing status
- Agent execution progress
- System notifications

---

## Best Practices

1. **Always check permissions**: Verify user has required permissions before attempting operations
2. **Handle rate limits**: Implement exponential backoff for retries
3. **Validate input**: Use Pydantic models for type safety
4. **Paginate results**: Use skip/limit for large result sets
5. **Cache tokens**: Don't request new JWT for every request
6. **Error handling**: Always check status codes and handle errors gracefully
7. **Use document scoping**: For better retrieval precision
8. **Monitor token usage**: Track costs via metering endpoints
9. **Enable explainability**: Use detailed level for important decisions
10. **Leverage council**: Use for critical decisions requiring multiple perspectives

---

## Security Considerations

1. **HTTPS only** in production
2. **Store tokens securely** (not in localStorage)
3. **Rotate secrets** regularly
4. **Validate file uploads** thoroughly
5. **Sanitize user inputs**
6. **Rate limit** authentication endpoints
7. **Log security events**
8. **Use strong passwords** (enforced by API)
9. **Implement CSRF protection**
10. **Regular security audits**

---

For more information, see:
- [Main Backend Documentation](../README.md)
- [Agent System Documentation](../agents/README.md)
- [Database Documentation](../database/README.md)
