# Chat Interface Feature

> **Complete guide to the real-time chat interface with streaming responses and agent orchestration**

## 📋 Table of Contents

- [Overview](#overview)
- [User Journey](#user-journey)
- [Streaming Architecture](#streaming-architecture)
- [Agent Orchestration](#agent-orchestration)
- [Document Context](#document-context)
- [Conversation Management](#conversation-management)
- [Implementation Details](#implementation-details)
- [Key Features](#key-features)

---

## Overview

The chat interface provides a real-time conversational experience with streaming responses, multi-agent orchestration visualization, document-grounded answers, and confidence scoring.

**Route:** `/dashboard/chat`
**Permission Required:** `chat:use`
**File:** `frontend/app/dashboard/chat/page.tsx`

### Core Features

```mermaid
graph TD
    A[Chat Interface] --> B[Streaming Responses]
    A --> C[Agent Visualization]
    A --> D[Document Context]
    A --> E[Conversation History]

    B --> B1[Real-time typing effect]
    B --> B2[Abort capability]

    C --> C1[Agent status cards]
    C --> C2[Execution timeline]

    D --> D1[Document selection]
    D --> D2[Source citations]

    E --> E1[Sidebar navigation]
    E --> E2[Search & filter]

    style A fill:#2196f3
    style B fill:#4caf50
    style C fill:#ff9800
```

---

## User Journey

### Complete Chat Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as Chat Page
    participant DM as Document Modal
    participant API as Backend Stream
    participant DB as Database

    U->>C: Navigate to /dashboard/chat
    C->>C: Load conversations sidebar

    U->>C: Click "New Chat"
    C->>DM: Open document selection
    U->>DM: Select relevant documents
    DM->>C: Return selected docs

    U->>C: Type message
    U->>C: Click Send

    C->>C: Add user message (optimistic)
    C->>API: POST /chat/stream (SSE)

    loop Stream Events
        API-->>C: agent_status update
        C->>C: Update agent card

        API-->>C: stream chunk
        C->>C: Append to response

        API-->>C: citation
        C->>C: Add source document

        API-->>C: confidence score
        C->>C: Update badge
    end

    API-->>C: done
    C->>DB: Save conversation
    C->>U: Show complete response
```

### First-Time User Experience

```mermaid
flowchart TD
    A[User enters chat page] --> B{Has conversations?}
    B -->|No| C[Show welcome message]
    B -->|Yes| D[Load last conversation]

    C --> E[Prompt to start new chat]
    E --> F[Click New Chat button]

    F --> G[Document Selection Modal]
    G --> H{Select documents?}
    H -->|Yes| I[Documents added to context]
    H -->|Skip| J[Use global knowledge base]

    I --> K[Show chat input]
    J --> K

    D --> K

    K --> L[User ready to chat]

    style C fill:#4caf50
    style G fill:#ff9800
```

---

## Streaming Architecture

### Server-Sent Events (SSE) Implementation

```mermaid
graph TD
    A[User sends message] --> B[Fetch API call]
    B --> C[Backend SSE stream opens]

    C --> D[ReadableStream reader]
    D --> E[TextDecoder]
    E --> F[Buffer accumulation]

    F --> G{Line complete?}
    G -->|No| F
    G -->|Yes| H[Parse JSON event]

    H --> I{Event type?}
    I -->|stream| J[Append text]
    I -->|agent_status| K[Update agent UI]
    I -->|citation| L[Add source]
    I -->|confidence| M[Update badge]
    I -->|done| N[Finalize message]

    J --> O[Update UI]
    K --> O
    L --> O
    M --> O

    O --> D
    N --> P[Close stream]

    style C fill:#2196f3
    style N fill:#4caf50
```

### Streaming Implementation Code

```typescript
const handleStreamingChat = async (message: string) => {
  const token = localStorage.getItem('token')

  // Open SSE connection
  const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      selected_documents: selectedDocumentIds,
      use_grounding: useGrounding,
      provider: preferredLLM,
    }),
  })

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  let buffer = ''
  let currentMessage = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    // Decode chunk
    buffer += decoder.decode(value, { stream: true })

    // Process complete lines
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6))
        handleStreamEvent(event)
      }
    }
  }
}
```

### Event Types

| Event Type | Purpose | Data Structure | UI Update |
|------------|---------|----------------|-----------|
| `stream` | Text chunks | `{ type, content }` | Append to message |
| `agent_status` | Agent state | `{ agent_name, status, message }` | Update agent card |
| `citation` | Source document | `{ document_id, similarity }` | Add citation chip |
| `confidence` | Confidence score | `{ score, level }` | Update confidence badge |
| `metadata` | Message metadata | `{ llm_provider, tokens }` | Store in state |
| `done` | Stream complete | `{ conversation_id, message_id }` | Finalize & save |

---

## Agent Orchestration

### Multi-Agent System Visualization

```mermaid
stateDiagram-v2
    [*] --> Orchestrator

    Orchestrator --> QueryAnalysis: Analyze query
    QueryAnalysis --> VectorSearch: Search documents
    VectorSearch --> Reranker: Rerank results
    Reranker --> Generator: Generate response
    Generator --> Validator: Validate answer
    Validator --> [*]: Return response

    QueryAnalysis --> [*]: Invalid query
    Validator --> Generator: Low confidence - retry
```

### Agent Status Display

Each agent is represented by a card showing:

```mermaid
graph LR
    A[Agent Card] --> B[Agent Name & Icon]
    A --> C[Status Indicator]
    A --> D[Status Message]
    A --> E[Execution Time]

    C --> C1[Pending: Gray]
    C --> C2[Running: Blue]
    C --> C3[Success: Green]
    C --> C4[Failed: Red]

    style A fill:#2196f3
    style C3 fill:#4caf50
    style C4 fill:#f44336
```

**Agent Roles:**

1. **Orchestrator** - Coordinates workflow
2. **Query Analyzer** - Parses user intent
3. **Document Retriever** - Searches vector store
4. **Reranker** - Scores relevance
5. **Generator** - Creates response
6. **Validator** - Checks quality

### Agent Status Updates

```typescript
// Handle agent status events
const handleAgentStatus = (event: AgentStatusEvent) => {
  setAgentStatuses(prev => ({
    ...prev,
    [event.agent_name]: {
      status: event.status,  // 'pending' | 'running' | 'success' | 'failed'
      message: event.message,
      timestamp: new Date(),
    }
  }))
}

// Render agent cards
<Box sx={{ display: 'flex', gap: 2, overflow: 'auto' }}>
  {agents.map(agent => (
    <Card key={agent.name}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {getAgentIcon(agent.name)}
          <Typography variant="h6">{agent.name}</Typography>
        </Box>

        <Chip
          label={agentStatuses[agent.name]?.status || 'pending'}
          color={getStatusColor(agentStatuses[agent.name]?.status)}
          size="small"
        />

        <Typography variant="body2">
          {agentStatuses[agent.name]?.message}
        </Typography>
      </CardContent>
    </Card>
  ))}
</Box>
```

---

## Document Context

### Document Selection Flow

```mermaid
flowchart TD
    A[Start New Conversation] --> B[Document Selection Modal]

    B --> C[Show all user documents]
    C --> D{User selects}

    D -->|Select specific| E[Add to selected list]
    D -->|Select all| F[Add all documents]
    D -->|Skip| G[No documents selected]

    E --> H[Show selected count]
    F --> H
    G --> I[Use global knowledge]

    H --> J[User confirms]
    J --> K[Store selection in state]
    K --> L[Include in first message]

    I --> L

    L --> M[Send message with context]

    style B fill:#ff9800
    style M fill:#4caf50
```

### Document Selection Modal

```typescript
<DocumentSelectionModal
  open={modalOpen}
  onClose={() => setModalOpen(false)}
  onConfirm={(selectedDocs) => {
    setSelectedDocuments(selectedDocs)
    setModalOpen(false)
  }}
/>

// Modal features:
// - Search/filter documents
// - Filter by scope (personal/global)
// - Select all/none
// - Show file type and size
// - Preview document summary
```

### Source Citations

```mermaid
graph TD
    A[Response Complete] --> B[Citations Included]
    B --> C[Document Title]
    B --> D[Similarity Score]
    B --> E[Relevant Chunk]

    C --> F[Clickable Chip]
    D --> G[Percentage Badge]
    E --> H[Expandable Section]

    F --> I[Navigate to document]
    G --> J[Visual confidence indicator]
    H --> K[Show original text]

    style B fill:#2196f3
    style F fill:#4caf50
```

**Citation Display:**

```typescript
<Box sx={{ mt: 2 }}>
  <Typography variant="caption" color="text.secondary">
    Sources:
  </Typography>

  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
    {message.sources?.map(source => (
      <Chip
        key={source.id}
        icon={<FileTextIcon />}
        label={`${source.filename} (${(source.similarity * 100).toFixed(1)}%)`}
        size="small"
        clickable
        onClick={() => viewDocument(source.id)}
      />
    ))}
  </Box>
</Box>
```

---

## Conversation Management

### Sidebar Structure

```mermaid
graph TD
    A[Conversations Sidebar] --> B[Search Bar]
    A --> C[Conversation List]

    B --> B1[Real-time filter]

    C --> C1[Today]
    C --> C2[Yesterday]
    C --> C3[Last 7 Days]
    C --> C4[Older]

    C1 --> D[Conversation Item]
    C2 --> D
    C3 --> D
    C4 --> D

    D --> E[Title Preview]
    D --> F[Timestamp]
    D --> G[Message Count]
    D --> H[Delete Button]

    style A fill:#2196f3
```

### Conversation Actions

```mermaid
flowchart TD
    A[Conversation Item] --> B{User Action}

    B -->|Click| C[Load conversation]
    B -->|Hover| D[Show delete button]
    B -->|Search| E[Filter by title]

    C --> F[Fetch messages]
    F --> G[Display in chat]

    D --> H{Click delete}
    H -->|Yes| I[Confirm dialog]
    H -->|No| A

    I -->|Confirm| J[Delete API call]
    I -->|Cancel| A

    J --> K[Remove from list]

    E --> L[Show matching only]

    style C fill:#4caf50
    style J fill:#f44336
```

### New Conversation Flow

```typescript
const startNewConversation = () => {
  // Reset state
  setConversationId(null)
  setMessages([])
  setSelectedDocuments([])

  // Open document selection
  setDocumentModalOpen(true)
}

// After first message sent:
const handleFirstMessage = async (message: string) => {
  const response = await chatAPI.sendMessage({
    message,
    selected_documents: selectedDocuments.map(d => d.id),
  })

  // Backend creates new conversation
  setConversationId(response.data.conversation_id)

  // Refresh sidebar
  fetchConversations()
}
```

---

## Implementation Details

### Component State Structure

```typescript
interface ChatPageState {
  // Conversation data
  conversationId: string | null
  conversations: Conversation[]
  messages: Message[]

  // UI state
  inputMessage: string
  isStreaming: boolean
  streamController: AbortController | null

  // Document context
  selectedDocuments: Document[]
  documentModalOpen: boolean

  // Agent visualization
  agentStatuses: Record<string, AgentStatus>

  // Settings
  useGrounding: boolean
  preferredLLM: 'custom' | 'ollama'

  // Sidebar
  sidebarOpen: boolean
  searchQuery: string
}
```

### Message Structure

```typescript
interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string

  // Metadata
  timestamp: string
  tokens_used?: number
  llm_provider?: string

  // Citations
  sources?: {
    document_id: string
    filename: string
    similarity: number
    chunk_text: string
  }[]

  // Confidence
  confidence_score?: number
  confidence_level?: 'high' | 'medium' | 'low'
  low_confidence_warning?: string

  // Agent data
  agent_logs?: {
    agent_name: string
    status: string
    execution_time: number
  }[]
}
```

---

## Key Features

### 1. Streaming Response Display

```typescript
// Accumulate streaming text
const [streamingContent, setStreamingContent] = useState('')

// On stream event
case 'stream':
  setStreamingContent(prev => prev + event.content)

// Render with typing effect
<Box sx={{ whiteSpace: 'pre-wrap' }}>
  <ReactMarkdown>{streamingContent}</ReactMarkdown>
  <Box component="span" className="blinking-cursor">|</Box>
</Box>
```

### 2. Abort Streaming

```typescript
const [abortController, setAbortController] = useState<AbortController | null>(null)

const startStreaming = () => {
  const controller = new AbortController()
  setAbortController(controller)

  fetch(url, { signal: controller.signal })
}

const stopStreaming = () => {
  abortController?.abort()
  setIsStreaming(false)
  showSnackbar('Response stopped', 'info')
}

// UI
{isStreaming && (
  <Button onClick={stopStreaming} color="error">
    Stop Generating
  </Button>
)}
```

### 3. Confidence Indicators

```mermaid
graph LR
    A[Confidence Score] --> B{Score Range}

    B -->|0.9-1.0| C[Very High - Green]
    B -->|0.8-0.9| D[High - Green]
    B -->|0.7-0.8| E[Good - Yellow]
    B -->|0.6-0.7| F[Medium - Yellow]
    B -->|< 0.6| G[Low - Red + Warning]

    C --> H[Badge Display]
    D --> H
    E --> H
    F --> H
    G --> I[Warning Alert]

    style C fill:#4caf50
    style D fill:#4caf50
    style E fill:#ff9800
    style F fill:#ff9800
    style G fill:#f44336
```

### 4. Provider Switching

```typescript
<FormControl>
  <InputLabel>LLM Provider</InputLabel>
  <Select
    value={preferredLLM}
    onChange={(e) => setPreferredLLM(e.target.value)}
  >
    <MenuItem value="custom">Custom API</MenuItem>
    <MenuItem value="ollama">Ollama Local</MenuItem>
  </Select>
</FormControl>
```

### 5. Grounding Toggle

```typescript
<FormControlLabel
  control={
    <Checkbox
      checked={useGrounding}
      onChange={(e) => setUseGrounding(e.target.checked)}
    />
  }
  label="Enable Answer Grounding Verification"
/>

// When enabled, backend validates answers against sources
// Adds grounding_confidence score to response
```

---

## Best Practices

### ✅ Do's

1. **Clean up streams on unmount**
```typescript
useEffect(() => {
  return () => {
    abortController?.abort()
  }
}, [])
```

2. **Show loading states during streaming**
```typescript
{isStreaming && <LinearProgress />}
```

3. **Handle stream errors gracefully**
```typescript
try {
  await streamResponse()
} catch (error) {
  if (error.name === 'AbortError') {
    showSnackbar('Stopped by user', 'info')
  } else {
    showSnackbar('Stream error', 'error')
  }
}
```

4. **Optimize message rendering**
```typescript
const MessageList = React.memo(({ messages }) => (
  // Only re-render when messages change
))
```

### ❌ Don'ts

- Don't forget to close ReadableStream readers
- Don't block UI during streaming
- Don't lose message context on re-render
- Don't allow multiple simultaneous streams

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Stream not starting | CORS or auth error | Check token and CORS headers |
| Partial messages | Buffer not flushed | Process remaining buffer after done |
| Memory leak | Reader not closed | Close reader in finally block |
| Agent status not updating | Event parsing error | Validate JSON structure |

---

## Next Steps

- **[Documents Feature](./DOCUMENTS.md)** - Learn about document management
- **[Explainability Feature](./EXPLAINABILITY.md)** - Understand AI transparency
- **[API Integration Guide](../guides/API_INTEGRATION.md)** - Deep dive into SSE

---

**Last Updated:** December 4, 2025
