# Comprehensive Features Documentation

> **Complete guide to all major application features**

This document consolidates documentation for all major features in the application. For detailed implementation guides, refer to the individual feature files.

---

## 📄 Document Management

**Route:** `/dashboard/documents`
**Permissions:** `documents:read` (view), `documents:create` (upload), `documents:delete` (delete)

### Upload Flow

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Documents Page
    participant API as Backend
    participant VS as Vector Store
    participant DB as Database

    U->>UI: Select file
    U->>UI: Choose provider (Custom/Ollama)
    U->>UI: Choose scope (Personal/Global)
    UI->>UI: Validate file (type, size)

    UI->>API: POST /documents/upload
    API->>DB: Create document record
    DB-->>API: document_id

    API->>API: Extract text
    API->>API: Chunk text
    API->>VS: Generate embeddings
    VS-->>API: Store vectors

    API->>DB: Update status: completed
    API-->>UI: Success response
    UI->>U: Show success + reload list
```

### Document States

```mermaid
stateDiagram-v2
    [*] --> Pending: Upload initiated
    Pending --> Processing: Backend receives file
    Processing --> Completed: Successfully processed
    Processing --> Failed: Error occurred

    Completed --> [*]
    Failed --> [*]
```

### Key Features

- **Multi-format Support:** PDF, TXT, CSV, DOCX
- **Scope System:** Personal (user-only) or Global (admin, all users)
- **Provider Selection:** Custom API or Ollama for embeddings
- **Processing Status:** Real-time status indicators
- **Statistics Cards:** Total docs, personal/global split, chunks, total size
- **Search & Filter:** Find documents by name
- **Bulk Operations:** Select and delete multiple

### Implementation

```typescript
// Upload document
const handleUpload = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('provider', selectedProvider)

  try {
    const endpoint = scope === 'global' && hasRole('admin')
      ? documentsAPI.uploadGlobal
      : documentsAPI.upload

    const response = await endpoint(file, selectedProvider)
    showSnackbar('Document uploaded successfully!', 'success')
    fetchDocuments()  // Reload list
  } catch (error) {
    showSnackbar(error.response?.data?.detail || 'Upload failed', 'error')
  }
}
```

---

## 🔍 OCR Processing

**Route:** `/dashboard/ocr`
**Permissions:** `documents:create` (to save extracted text)

### OCR Pipeline

```mermaid
flowchart TD
    A[User uploads image/PDF] --> B{File type}
    B -->|Image| C[Single page processing]
    B -->|PDF| D{Process all pages?}

    D -->|Yes| E[Extract all pages]
    D -->|No| F[Extract first page only]

    C --> G[Vision Model]
    E --> G
    F --> G

    G --> H[Custom Azure Vision API]
    G --> I[Ollama LLaVA]

    H --> J[Extract text with prompt]
    I --> J

    J --> K[Display results]
    K --> L{User action}

    L -->|Save| M[Store in vector DB]
    L -->|Download| N[Download as .txt]
    L -->|Copy| O[Copy to clipboard]

    style G fill:#ff9800
    style M fill:#4caf50
```

### Vision Model Configuration

| Provider | Model | Features | Use Case |
|----------|-------|----------|----------|
| **Custom** | Azure Vision API | High accuracy, multilingual, table extraction | Production documents |
| **Ollama** | LLaVA | Local processing, privacy, free | Development, sensitive docs |

### Multi-Page Processing

```typescript
// Process all pages or first page only
const processOCR = async (file: File, processAllPages: boolean) => {
  const response = await documentsAPI.ocr(file, {
    provider: selectedProvider,
    prompt: customPrompt || 'Extract all text accurately',
    process_all_pages: processAllPages,
  })

  // Response structure:
  {
    pages: [
      { page_number: 1, text: '...', confidence: 0.95, tokens_used: 1200 },
      { page_number: 2, text: '...', confidence: 0.98, tokens_used: 1100 }
    ],
    total_tokens: 2300,
    processing_time: 3.5
  }
}
```

### Key Features

- **Supported Formats:** JPG, PNG, PDF, TIFF, BMP, WebP
- **Custom Prompts:** Guide extraction with specific instructions
- **Multi-page PDFs:** Process all pages or first only
- **Confidence Scores:** Per-page extraction confidence
- **Token Tracking:** Monitor API usage
- **Save Options:** Store in vector DB or download
- **Preview:** View uploaded image before processing

---

## 📊 Explainability Dashboard

**Route:** `/dashboard/explainability`
**Permissions:** `explain:view`

### Dashboard Architecture

```mermaid
graph TD
    A[Explainability Dashboard] --> B[AI Insights Tab]
    A --> C[Confidence Analysis Tab]
    A --> D[Agent Performance Tab]
    A --> E[Reasoning Chains Tab]

    B --> B1[Query History]
    B --> B2[Confidence Scores]
    B --> B3[Detailed View]

    C --> C1[Confidence Trend Chart]
    C --> C2[Score Distribution]

    D --> D1[Agent Execution Times]
    D --> D2[Success Rates]

    E --> E1[Step-by-step Reasoning]
    E --> E2[Decision Trees]

    style A fill:#2196f3
    style B fill:#4caf50
    style C fill:#ff9800
```

### Tab 1: AI Insights

Shows all chat queries with explainability data:

- Query text and response
- Confidence score with color-coded badge
- Timestamp and provider
- Low confidence warnings
- Expandable detailed view

### Tab 2: Confidence Analysis

```mermaid
graph LR
    A[Confidence Data] --> B[Line Chart]
    A --> C[Statistics]

    B --> B1[Time series]
    B --> B2[Trend line]

    C --> C1[Average score]
    C --> C2[Min/Max]
    C --> C3[Total queries]

    style B fill:#2196f3
```

**Recharts Implementation:**

```typescript
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={confidenceData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="timestamp" />
    <YAxis domain={[0, 1]} />
    <Tooltip />
    <Legend />
    <Line
      type="monotone"
      dataKey="confidence_score"
      stroke="#2196f3"
      strokeWidth={2}
    />
  </LineChart>
</ResponsiveContainer>
```

### Tab 3: Agent Performance

Bar chart showing execution metrics per agent:

- Orchestrator, Query Analyzer, Retriever, Reranker, Generator, Validator
- Average execution time in milliseconds
- Success vs failure rates
- Interactive tooltips

### Tab 4: Reasoning Chains

Step-by-step visualization of AI decision-making:

```mermaid
flowchart TD
    A[User Query] --> B[Query Analysis]
    B --> C[Intent: Information Retrieval]
    C --> D[Document Search]
    D --> E[Found 5 relevant documents]
    E --> F[Reranking]
    F --> G[Top 3 selected]
    G --> H[Response Generation]
    H --> I[Validation]
    I --> J[Confidence: 0.87]
    J --> K[Final Answer]

    style A fill:#2196f3
    style K fill:#4caf50
```

**Features:**
- Expandable step cards
- Execution time per step
- Input/output data
- Confidence at each stage
- Grounding evidence

---

## 👥 Admin Panel

**Route:** `/dashboard/admin`
**Permissions:** `admin:access` (admin role required)

### Admin Panel Structure

```mermaid
graph TD
    A[Admin Panel] --> B[User Management]
    A --> C[System Statistics]
    A --> D[LLM Configuration]
    A --> E[Token Metering]

    B --> B1[User List Table]
    B --> B2[Create User]
    B --> B3[Edit User]
    B --> B4[Delete User]

    C --> C1[Total Users]
    C --> C2[Active Users 24h]
    C --> C3[Total Conversations]
    C --> C4[Agent Executions]

    D --> D1[Provider Status]
    D --> D2[Model Configs]
    D --> D3[RAG Settings]

    E --> E1[Token Usage]
    E --> E2[Cost Calculation]

    style A fill:#f44336
```

### User Management CRUD

```mermaid
sequenceDiagram
    participant A as Admin
    participant UI as Admin Panel
    participant API as Backend
    participant DB as Database

    Note over A,DB: CREATE USER
    A->>UI: Click "Create User"
    UI->>A: Show form modal
    A->>UI: Fill form (username, email, password, roles)
    UI->>API: POST /admin/users
    API->>DB: Insert user record
    DB-->>API: Success
    API-->>UI: User created
    UI->>UI: Refresh user list

    Note over A,DB: UPDATE USER
    A->>UI: Click edit icon
    UI->>API: GET /admin/users/:id
    API-->>UI: User data
    UI->>A: Show edit form
    A->>UI: Modify roles/status
    UI->>API: PUT /admin/users/:id
    API->>DB: Update record
    DB-->>API: Success
    API-->>UI: Updated
    UI->>UI: Refresh user list

    Note over A,DB: DELETE USER
    A->>UI: Click delete icon
    UI->>A: Confirm dialog
    A->>UI: Confirm
    UI->>API: DELETE /admin/users/:id
    API->>DB: Delete record
    DB-->>API: Success
    API-->>UI: Deleted
    UI->>UI: Remove from list
```

### User Table Features

- **DataGrid Component:** Sortable, filterable columns
- **Columns:** ID, Username, Email, Full Name, Roles, Status, Last Login, Actions
- **Role Chips:** Color-coded badges (Admin=red, Analyst=orange, Viewer=green)
- **Status Toggle:** Active/Inactive switch
- **Actions:** Edit, Delete buttons
- **Export:** Download user list as CSV

### System Statistics Cards

```typescript
<Grid container spacing={3}>
  <Grid item xs={12} sm={6} md={3}>
    <StatsCard
      title="Total Users"
      value={stats.total_users}
      icon={<PeopleIcon />}
      color="primary"
    />
  </Grid>

  <Grid item xs={12} sm={6} md={3}>
    <StatsCard
      title="Active Users (24h)"
      value={stats.active_users_24h}
      icon={<PersonIcon />}
      color="success"
    />
  </Grid>

  <Grid item xs={12} sm={6} md={3}>
    <StatsCard
      title="Total Conversations"
      value={stats.total_conversations}
      icon={<ChatIcon />}
      color="info"
    />
  </Grid>

  <Grid item xs={12} sm={6} md={3}>
    <StatsCard
      title="Agent Executions"
      value={stats.total_agent_executions}
      icon={<SmartToyIcon />}
      color="warning"
    />
  </Grid>
</Grid>
```

### Token Metering

**Real-time cost tracking:**

```typescript
{
  providers: {
    custom: {
      total_tokens: 1245600,
      total_cost: 24.91,
      queries_count: 450
    },
    ollama: {
      total_tokens: 340000,
      total_cost: 0,  // Local, free
      queries_count: 120
    }
  },
  last_7_days: { tokens: 125000, cost: 2.50 },
  last_30_days: { tokens: 580000, cost: 11.60 }
}
```

### LLM Configuration Display

Read-only view of system configuration:

- **Custom Provider:** API endpoint, model name, embedding model
- **Ollama Provider:** Base URL, available models
- **Vision Models:** Azure Vision config, Ollama LLaVA
- **RAG Settings:** Chunk size, overlap, similarity threshold, top-k
- **Explainability:** Logging level, confidence thresholds

---

## 🛠️ Utilities Page

**Route:** `/dashboard/utilities`
**Purpose:** Demo/testing interface for UI components

### Tab Structure

1. **Tables Tab:** DataGrid demos with CRUD operations, CSV export
2. **Forms Tab:** Sample form with validation
3. **Charts Tab:** Line, Bar, Pie chart examples using Recharts
4. **PII Scrubbing Tab:** Text anonymization utility

### PII Scrubbing Feature

```mermaid
flowchart LR
    A[User inputs text] --> B[API Call]
    B --> C[/utilities/scrub-pii]
    C --> D[Backend detects PII]
    D --> E[Replace with placeholders]
    E --> F[Return scrubbed text]
    F --> G[Display result]

    D --> H[Detection count]
    H --> G

    style C fill:#ff9800
    style E fill:#4caf50
```

**Example:**
```
Input: "John Smith's email is john@example.com and SSN is 123-45-6789"
Output: "PERSON_1's email is EMAIL_1 and SSN is SSN_1"
Detections: 3 (1 person, 1 email, 1 SSN)
```

---

## Feature Comparison Matrix

| Feature | Permission Required | Admin Only | Supports Streaming | Uses Vector Store |
|---------|---------------------|------------|-------------------|-------------------|
| **Chat** | `chat:use` | No | Yes | Yes |
| **Documents** | `documents:read/create` | No (Global: Yes) | No | Yes |
| **OCR** | `documents:create` | No | No | Optional |
| **Explainability** | `explain:view` | No | No | No |
| **Admin Panel** | `admin:access` | Yes | No | No |
| **Utilities** | None (authenticated) | No | No | No |

---

## Cross-Feature Workflows

### Complete RAG Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant D as Documents Page
    participant C as Chat Page
    participant E as Explainability

    U->>D: Upload documents
    D->>D: Process & embed

    U->>C: Start chat
    C->>C: Select documents
    U->>C: Ask question
    C->>C: Stream answer with sources

    U->>E: View explainability
    E->>E: Show confidence & reasoning
```

### Admin Monitoring Workflow

```mermaid
flowchart TD
    A[Admin logs in] --> B[Check system stats]
    B --> C{Issues detected?}

    C -->|High token usage| D[Review token metering]
    C -->|Low confidence| E[Check explainability]
    C -->|User complaints| F[Review user list]

    D --> G[Adjust LLM provider]
    E --> H[Improve prompts]
    F --> I[Manage permissions]
```

---

## Next Steps

- **[Components Guide](../guides/COMPONENTS.md)** - Reusable UI components
- **[Development Guide](../guides/DEVELOPMENT_GUIDE.md)** - Add new features
- **[API Integration](../guides/API_INTEGRATION.md)** - Connect features to backend

---

**Last Updated:** December 4, 2025
