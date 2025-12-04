# Usage Examples

This directory contains practical, runnable examples demonstrating various features of the RAG & Multi-Agent AI System.

## Available Examples

### 1. Basic Chat Workflow ([01_basic_chat.py](01_basic_chat.py))
**What it demonstrates:**
- User authentication with JWT
- Sending chat messages
- Receiving AI responses with RAG context
- Viewing source documents
- Maintaining conversation context

**Key concepts:**
- Authentication flow
- Message API usage
- Response structure
- Conversation management

**Run:**
```bash
python docs/examples/01_basic_chat.py
```

---

### 2. Document Upload with RAG ([02_document_upload.py](02_document_upload.py))
**What it demonstrates:**
- Uploading documents to the system
- Automatic metadata generation (LLM-powered)
- Document management operations (list, get, delete)
- Querying specific documents
- Document scoping (user vs global)

**Key concepts:**
- File upload API
- Metadata generation
- Document filtering
- Scoped queries
- RAG with specific documents

**Run:**
```bash
python docs/examples/02_document_upload.py
```

---

### 3. Streaming Chat ([03_streaming_chat.py](03_streaming_chat.py))
**What it demonstrates:**
- Server-Sent Events (SSE) for real-time streaming
- Token-by-token response delivery
- Agent execution progress tracking
- Custom stream handlers

**Key concepts:**
- SSE protocol
- Streaming responses
- Event types (agent_start, token, complete)
- Real-time progress updates

**Run:**
```bash
python docs/examples/03_streaming_chat.py
```

---

### 4. Multi-Agent Orchestration ([04_agent_monitoring.py](04_agent_monitoring.py))
**What it demonstrates:**
- Agent execution lifecycle
- Agent logs and monitoring
- Grounding verification process
- Explainability features
- Reasoning chains

**Key concepts:**
- Agent orchestration
- Agent logs API
- Explainability levels
- Confidence scoring
- Grounding verification

**Run:**
```bash
python docs/examples/04_agent_monitoring.py
```

---

### 5. Token Usage Metering ([05_token_metering.py](05_token_metering.py))
**What it demonstrates:**
- Tracking token usage across operations
- Cost estimation for LLM calls
- Usage analytics (user, conversation, agent-level)
- Cost optimization strategies

**Key concepts:**
- Token metering
- Cost calculation
- Usage breakdowns
- Admin analytics
- Cost optimization

**Run:**
```bash
python docs/examples/05_token_metering.py
```

---

### 6. OCR & Vision Processing ([06_ocr_vision.py](06_ocr_vision.py))
**What it demonstrates:**
- Text extraction from images
- PDF to image OCR conversion
- Batch OCR processing
- Vision model analysis
- Structured data extraction

**Key concepts:**
- OCR API
- Batch processing
- Vision models
- Structured extraction
- Document digitization

**Run:**
```bash
python docs/examples/06_ocr_vision.py
```

---

## Setup

### Prerequisites
```bash
# Python 3.10+
python --version

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Configuration

1. **Backend must be running:**
```bash
# In backend directory
python main.py
```

2. **Update credentials** in each example:
```python
# Change these in each example file
USERNAME = "your_username@example.com"
PASSWORD = "your_password"
```

3. **Create test user** (if needed):
```bash
# Using admin account
curl -X POST http://localhost:8000/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com",
    "password": "test123",
    "role_name": "analyst"
  }'
```

---

## Common Patterns

### Authentication Pattern
```python
def authenticate(username: str, password: str) -> str:
    """Get JWT token for API access."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]

# Use in headers
headers = {"Authorization": f"Bearer {token}"}
```

### Error Handling Pattern
```python
try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
except requests.exceptions.HTTPError as e:
    print(f"Error: {e}")
    print(f"Response: {e.response.text}")
    return None
```

### Pagination Pattern
```python
def get_all_pages(token: str, endpoint: str):
    """Fetch all pages of results."""
    page = 1
    all_results = []

    while True:
        response = requests.get(
            f"{BASE_URL}/{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": page, "page_size": 50}
        )
        data = response.json()

        all_results.extend(data['items'])

        if not data['has_next']:
            break

        page += 1

    return all_results
```

---

## Integration Examples

### Python SDK
```python
# Simple Python client wrapper
class RAGClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.token = self._authenticate(username, password)

    def _authenticate(self, username: str, password: str) -> str:
        response = requests.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def chat(self, message: str, conversation_id: str = None) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = requests.post(
            f"{self.base_url}/chat/message",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def upload_document(self, file_path: str, scope: str = "user") -> dict:
        headers = {"Authorization": f"Bearer {self.token}"}

        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"scope": scope}
            response = requests.post(
                f"{self.base_url}/documents/upload",
                headers=headers,
                files=files,
                data=data
            )

        response.raise_for_status()
        return response.json()

# Usage
client = RAGClient("http://localhost:8000", "user@example.com", "password")
response = client.chat("What is machine learning?")
print(response['message']['content'])
```

### JavaScript/TypeScript SDK
```typescript
// TypeScript client example
class RAGClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async authenticate(username: string, password: string): Promise<void> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });

    const data = await response.json();
    this.token = data.access_token;
  }

  async chat(message: string, conversationId?: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/chat/message`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId
      })
    });

    return response.json();
  }

  async uploadDocument(file: File, scope: string = 'user'): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('scope', scope);

    const response = await fetch(`${this.baseUrl}/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });

    return response.json();
  }
}

// Usage
const client = new RAGClient('http://localhost:8000');
await client.authenticate('user@example.com', 'password');
const response = await client.chat('What is machine learning?');
console.log(response.message.content);
```

---

## Testing Examples

Each example can be tested individually:

```bash
# Test basic chat
python docs/examples/01_basic_chat.py

# Test with different user
USERNAME="admin@example.com" PASSWORD="admin123" python docs/examples/01_basic_chat.py
```

---

## Troubleshooting

### Connection Refused
**Problem:** `requests.exceptions.ConnectionError: Connection refused`

**Solution:**
```bash
# Ensure backend is running
cd backend
python main.py

# Check if it's accessible
curl http://localhost:8000/docs
```

### Authentication Failed
**Problem:** `401 Unauthorized`

**Solution:**
- Verify username and password
- Check if user exists in database
- Ensure user is not deactivated

### Token Expired
**Problem:** `401 Unauthorized` after some time

**Solution:**
- Re-authenticate to get new token
- Implement token refresh logic
- Increase `ACCESS_TOKEN_EXPIRE_MINUTES` in config

### Rate Limiting
**Problem:** `429 Too Many Requests`

**Solution:**
- Add delays between requests
- Implement exponential backoff
- Contact admin to increase rate limits

---

## Next Steps

- **Read the [API Reference](../API_REFERENCE.md)** for complete endpoint documentation
- **Review [Architecture](../ARCHITECTURE.md)** to understand system design
- **Check [Setup Guide](../guides/SETUP.md)** for development environment
- **See [Extending Guide](../guides/EXTENDING.md)** to add custom features

---

## Contributing

Have a useful example? Contribute it!

1. Create a new example file: `0X_feature_name.py`
2. Include comprehensive docstrings and comments
3. Add expected output section
4. Update this README
5. Submit a pull request

---

**Questions?** Check the [main documentation](../README.md) or open an issue.
