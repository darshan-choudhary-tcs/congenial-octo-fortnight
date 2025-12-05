# Prompts API Documentation

Complete API reference for managing and accessing the prompt library system.

## Overview

The Prompts API provides CRUD operations for all 30 built-in prompts and custom runtime prompts. All endpoints require **admin role** for security.

### Base URL
```
http://localhost:8000/api/v1/prompts
```

### Authentication
All endpoints require Bearer token authentication with admin role:
```
Authorization: Bearer <your_token>
```

---

## Prompt Library Structure

### Built-in Prompts (30 total)

#### System Prompts (12)
Role definitions for AI behavior:
- `research_analyst` - Research and analysis role
- `data_analyst` - Data analysis role
- `transparency_expert` - AI transparency/explainability role
- `fact_checker` - Fact-checking and grounding role
- `document_analyst` - Document summarization role
- `keyword_extractor` - Keyword extraction role
- `document_classifier` - Topic classification role
- `content_type_classifier` - Content type determination role
- `helpful_assistant` - General chat assistance
- `rag_assistant_basic` - Basic RAG responses
- `rag_assistant_detailed` - Detailed RAG with citations
- `rag_assistant_debug` - Debug-level RAG with full transparency

#### Agent Prompts (7)
Multi-agent system operations:
- `research_analysis` - In-depth research with specific focus
- `general_analysis` - General analytical responses
- `comparative_analysis` - Comparative analysis between topics
- `trend_analysis` - Trend identification and analysis
- `explanation_basic` - Basic explanation generation
- `explanation_detailed` - Detailed explanation with reasoning
- `explanation_debug` - Debug-level explanation with full process

#### RAG Prompts (3)
Retrieval Augmented Generation:
- `rag_generation_with_sources` - Generate response with source attribution
- `rag_generation_simple` - Simple RAG response
- `grounding_verification` - Verify grounding with sources

#### LLM Service Prompts (4)
Document processing:
- `document_summarization` - Summarize documents
- `keyword_extraction` - Extract keywords from text
- `topic_classification` - Classify topics
- `content_type_determination` - Determine content type

#### Vision Prompts (2)
OCR and image analysis:
- `ocr_extraction` - Extract text from images
- `image_analysis` - Analyze image content

#### Chat Prompts (2)
Direct LLM interactions:
- `direct_llm_with_history` - Chat with conversation history
- `direct_llm_simple` - Simple direct LLM query

---

## API Endpoints

### 1. List All Prompts

Get all prompts with optional category filter.

**Endpoint:** `GET /prompts`

**Query Parameters:**
- `category` (optional): Filter by category (`agent`, `rag`, `llm_service`, `vision`, `chat`, `system`)

**Response:** `200 OK`
```json
{
  "prompts": [
    {
      "name": "research_analyst",
      "category": "system",
      "description": "Research analyst role definition",
      "template": "You are a research analyst...",
      "variables": [],
      "version": "1.0.0",
      "output_format": "text",
      "purpose": "Research analysis role",
      "examples": [],
      "is_custom": false,
      "usage_count": 42,
      "created_at": "2025-01-01T00:00:00"
    }
  ],
  "total": 30,
  "categories": ["agent", "rag", "llm_service", "vision", "chat", "system"],
  "filtered_category": null
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/prompts" \
  -H "Authorization: Bearer <token>"

# Filter by category
curl -X GET "http://localhost:8000/api/v1/prompts?category=agent" \
  -H "Authorization: Bearer <token>"
```

---

### 2. Get Prompt Details

Get detailed information about a specific prompt.

**Endpoint:** `GET /prompts/{name}`

**Path Parameters:**
- `name` (required): Unique prompt identifier

**Response:** `200 OK`
```json
{
  "name": "research_analysis",
  "category": "agent",
  "description": "Research analysis with specific focus",
  "template": "Analyze the following query: {query}\n\nContext: {context}",
  "variables": ["query", "context"],
  "version": "1.0.0",
  "output_format": "structured_text",
  "purpose": "In-depth research and analysis",
  "examples": [],
  "is_custom": false,
  "usage_count": 15,
  "created_at": "2025-01-01T00:00:00"
}
```

**Error Responses:**
- `404 Not Found` - Prompt not found

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/prompts/research_analyst" \
  -H "Authorization: Bearer <token>"
```

---

### 3. Get Categories

Get all available prompt categories with counts.

**Endpoint:** `GET /prompts/categories`

**Response:** `200 OK`
```json
{
  "categories": ["agent", "rag", "llm_service", "vision", "chat", "system"],
  "count_by_category": {
    "agent": 7,
    "rag": 3,
    "llm_service": 4,
    "vision": 2,
    "chat": 2,
    "system": 12
  }
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/prompts/categories" \
  -H "Authorization: Bearer <token>"
```

---

### 4. Get Usage Statistics

Get usage statistics for all prompts.

**Endpoint:** `GET /prompts/stats`

**Response:** `200 OK`
```json
{
  "total_prompts": 30,
  "custom_prompts": 0,
  "built_in_prompts": 30,
  "total_usage": 1250,
  "most_used": [
    {
      "name": "rag_assistant_basic",
      "usage_count": 500,
      "category": "system"
    }
  ],
  "by_category": {
    "agent": 7,
    "rag": 3,
    "llm_service": 4,
    "vision": 2,
    "chat": 2,
    "system": 12
  }
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/prompts/stats" \
  -H "Authorization: Bearer <token>"
```

---

### 5. Create Custom Prompt

Register a new custom prompt at runtime.

**Endpoint:** `POST /prompts`

**Request Body:**
```json
{
  "name": "custom_analysis",
  "template": "Analyze {topic} with focus on {aspect}",
  "category": "custom",
  "description": "Custom analysis prompt",
  "variables": ["topic", "aspect"],
  "output_format": "text",
  "purpose": "Custom business analysis",
  "examples": []
}
```

**Response:** `201 Created`
```json
{
  "name": "custom_analysis",
  "category": "custom",
  "description": "Custom analysis prompt",
  "template": "Analyze {topic} with focus on {aspect}",
  "variables": ["topic", "aspect"],
  "version": "1.0.0",
  "output_format": "text",
  "purpose": "Custom business analysis",
  "examples": [],
  "is_custom": true,
  "usage_count": 0,
  "created_at": "2025-12-05T10:30:00"
}
```

**Error Responses:**
- `400 Bad Request` - Prompt already exists or invalid data
- `403 Forbidden` - Not admin user

**Notes:**
- Custom prompts are stored in-memory only and lost on restart
- Built-in prompt names cannot be used unless updating with `override=True`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/prompts" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_custom_prompt",
    "template": "Analyze: {data}",
    "category": "custom",
    "description": "My custom prompt",
    "variables": ["data"],
    "output_format": "text"
  }'
```

---

### 6. Update Custom Prompt

Update an existing custom prompt. Built-in prompts cannot be updated.

**Endpoint:** `PUT /prompts/{name}`

**Path Parameters:**
- `name` (required): Prompt identifier

**Request Body:** (all fields optional)
```json
{
  "template": "Updated template with {new_variable}",
  "description": "Updated description",
  "variables": ["new_variable"],
  "category": "custom",
  "output_format": "json",
  "purpose": "Updated purpose"
}
```

**Response:** `200 OK`
```json
{
  "name": "custom_analysis",
  "category": "custom",
  "description": "Updated description",
  "template": "Updated template with {new_variable}",
  "variables": ["new_variable"],
  "version": "1.0.0",
  "output_format": "json",
  "purpose": "Updated purpose",
  "examples": [],
  "is_custom": true,
  "usage_count": 5,
  "created_at": "2025-12-05T10:30:00"
}
```

**Error Responses:**
- `403 Forbidden` - Attempting to update built-in prompt
- `404 Not Found` - Prompt not found

**Example:**
```bash
curl -X PUT "http://localhost:8000/api/v1/prompts/my_custom_prompt" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated custom prompt description"
  }'
```

---

### 7. Delete Custom Prompt

Delete a custom prompt. Built-in prompts cannot be deleted.

**Endpoint:** `DELETE /prompts/{name}`

**Path Parameters:**
- `name` (required): Prompt identifier

**Response:** `200 OK`
```json
{
  "message": "Custom prompt 'custom_analysis' deleted successfully",
  "detail": "This prompt has been removed from runtime memory"
}
```

**Error Responses:**
- `403 Forbidden` - Attempting to delete built-in prompt
- `404 Not Found` - Prompt not found

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/prompts/my_custom_prompt" \
  -H "Authorization: Bearer <token>"
```

---

### 8. Clear All Custom Prompts

Clear all custom prompts, keeping only built-in prompts.

**Endpoint:** `DELETE /prompts`

**Response:** `200 OK`
```json
{
  "message": "Cleared 3 custom prompt(s)",
  "detail": "Removed: custom_analysis, my_custom_prompt, test_prompt"
}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/prompts" \
  -H "Authorization: Bearer <token>"
```

---

### 9. Test Prompt

Test a prompt with variable substitution without actually using it.

**Endpoint:** `POST /prompts/{name}/test`

**Path Parameters:**
- `name` (required): Prompt identifier

**Request Body:**
```json
{
  "variables": {
    "query": "What is AI?",
    "context": "General information about artificial intelligence"
  }
}
```

**Response:** `200 OK`
```json
{
  "formatted_prompt": "Analyze the following query: What is AI?\n\nContext: General information about artificial intelligence",
  "variables_used": {
    "query": "What is AI?",
    "context": "General information about artificial intelligence"
  },
  "template": "Analyze the following query: {query}\n\nContext: {context}",
  "missing_variables": []
}
```

**Error Responses:**
- `400 Bad Request` - Missing required variables
- `404 Not Found` - Prompt not found

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/prompts/research_analysis/test" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "query": "Explain quantum computing",
      "context": "Recent advances in quantum technology"
    }
  }'
```

---

## Common Response Schemas

### PromptResponse
```typescript
{
  name: string;              // Unique identifier
  category: string;          // Category name
  description: string;       // Human-readable description
  template: string;          // Template with {variables}
  variables: string[];       // Required variable names
  version: string;           // Version string
  output_format: string;     // Expected output format
  purpose: string;           // Purpose and use case
  examples: string[];        // Usage examples
  is_custom: boolean;        // True if custom, false if built-in
  usage_count: number;       // Number of times used
  created_at: string;        // ISO 8601 timestamp
}
```

### Error Response
```typescript
{
  detail: string;            // Error message
}
```

---

## Authentication

### Getting a Token

1. **Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password"
```

2. **Use Token:**
```bash
curl -X GET "http://localhost:8000/api/v1/prompts" \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Best Practices

### 1. Read-Only Access to Built-in Prompts
Built-in prompts (from `templates.py`) are protected:
- ✅ Can be read via GET endpoints
- ❌ Cannot be updated or deleted
- 💡 Create custom prompts with different names instead

### 2. Custom Prompt Management
Custom prompts are runtime-only:
- ⚠️ Lost on server restart
- 💡 Consider persisting important prompts externally
- 💡 Use descriptive names to avoid conflicts

### 3. Variable Testing
Always test prompts before using in production:
- Use the `/test` endpoint to verify variable substitution
- Ensure all required variables are provided
- Check formatted output meets expectations

### 4. Category Organization
Use meaningful categories for custom prompts:
- `custom` - General custom prompts
- Reuse existing categories if applicable
- Keep consistent with built-in categorization

---

## Integration Examples

### Python
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
token = "your_access_token"
headers = {"Authorization": f"Bearer {token}"}

# List all agent prompts
response = requests.get(
    f"{BASE_URL}/prompts?category=agent",
    headers=headers
)
prompts = response.json()

# Get specific prompt
response = requests.get(
    f"{BASE_URL}/prompts/research_analysis",
    headers=headers
)
prompt = response.json()

# Create custom prompt
prompt_data = {
    "name": "sales_analysis",
    "template": "Analyze sales data for {product} in {region}",
    "category": "custom",
    "description": "Sales analysis prompt",
    "variables": ["product", "region"],
    "output_format": "json"
}
response = requests.post(
    f"{BASE_URL}/prompts",
    headers=headers,
    json=prompt_data
)
```

### JavaScript/TypeScript
```typescript
const BASE_URL = "http://localhost:8000/api/v1";
const token = "your_access_token";

// List all prompts
const response = await fetch(`${BASE_URL}/prompts`, {
  headers: { "Authorization": `Bearer ${token}` }
});
const data = await response.json();

// Create custom prompt
const promptData = {
  name: "marketing_analysis",
  template: "Analyze marketing campaign: {campaign_name}",
  category: "custom",
  description: "Marketing analysis prompt",
  variables: ["campaign_name"],
  output_format: "text"
};

const createResponse = await fetch(`${BASE_URL}/prompts`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify(promptData)
});
```

---

## Testing

A comprehensive test suite is available at `backend/test_prompts_api.py`.

### Running Tests
```bash
# Ensure backend is running
cd backend
python test_prompts_api.py
```

### Test Coverage
- ✅ List prompts (all and filtered)
- ✅ Get categories and statistics
- ✅ Get specific prompt details
- ✅ Create custom prompts
- ✅ Update custom prompts
- ✅ Test prompt variable substitution
- ✅ Delete custom prompts
- ✅ Protection of built-in prompts

---

## Rate Limits & Performance

- No rate limiting currently implemented
- In-memory operations are fast (<10ms typical)
- Consider caching prompt lists in client applications
- Usage statistics updated on each prompt retrieval

---

## Troubleshooting

### 401 Unauthorized
- Token expired or invalid
- Re-authenticate to get new token

### 403 Forbidden
- User lacks admin role
- Cannot modify built-in prompts

### 404 Not Found
- Prompt name doesn't exist
- Check spelling and case sensitivity

### 400 Bad Request
- Missing required fields
- Invalid variable substitution
- Prompt name already exists

---

## Support

For issues or questions:
- Check backend logs in `backend/`
- Review prompt library docs in `backend/app/prompts/README.md`
- Test with provided test script

---

## Version History

### v1.0.0 (2025-12-05)
- Initial release
- Full CRUD operations for prompts
- Support for 30 built-in prompts
- Runtime custom prompt management
- Admin-only access control
- Variable testing endpoint
