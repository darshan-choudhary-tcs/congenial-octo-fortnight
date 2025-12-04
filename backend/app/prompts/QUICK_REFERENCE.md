# Prompt Library Quick Reference

## Quick Import

```python
from app.prompts import get_prompt_library

prompt_lib = get_prompt_library()
```

## All Available Prompts

### System Prompts (No Variables)

```python
# Research & Analysis
prompt_lib.get_system_prompt("research_analyst")
prompt_lib.get_system_prompt("data_analyst")
prompt_lib.get_system_prompt("transparency_expert")
prompt_lib.get_system_prompt("fact_checker")

# Document Processing
prompt_lib.get_system_prompt("document_analyst")
prompt_lib.get_system_prompt("keyword_extractor")
prompt_lib.get_system_prompt("document_classifier")
prompt_lib.get_system_prompt("content_type_classifier")

# Chat & RAG
prompt_lib.get_system_prompt("helpful_assistant")
prompt_lib.get_system_prompt("rag_assistant_basic")
prompt_lib.get_system_prompt("rag_assistant_detailed")
prompt_lib.get_system_prompt("rag_assistant_debug")
```

### Agent Prompts

```python
# Research Analysis
prompt_lib.get_prompt("research_analysis",
    query="user query",
    documents="formatted documents"
)

# Data Analysis (choose one)
prompt_lib.get_prompt("general_analysis", data="data to analyze")
prompt_lib.get_prompt("comparative_analysis", data="data to compare")
prompt_lib.get_prompt("trend_analysis", data="data for trends")

# Explainability (choose level)
prompt_lib.get_prompt("explanation_basic",
    response="AI response",
    source_count=5
)

prompt_lib.get_prompt("explanation_detailed",
    response="AI response",
    sources="formatted sources",
    process="process description"
)

prompt_lib.get_prompt("explanation_debug",
    response="AI response",
    sources_detailed="detailed sources with scores",
    process="process description"
)
```

### RAG Prompts

```python
# RAG Generation with Sources
prompt_lib.get_prompt("rag_generation_with_sources",
    context="retrieved context",
    query="user query",
    reasoning_detail=" in detail",  # or ""
    assumptions_note="5. Note any assumptions"  # or ""
)

# Simple RAG
prompt_lib.get_prompt("rag_generation_simple",
    context="context",
    query="query"
)

# Grounding Verification
prompt_lib.get_prompt("grounding_verification",
    sources_text="formatted sources",
    response="response to verify"
)
```

### LLM Service Prompts

```python
# Document Summarization
prompt_lib.get_prompt("document_summarization", text="document text")

# Keyword Extraction
prompt_lib.get_prompt("keyword_extraction",
    max_keywords=10,
    text="document text"
)

# Topic Classification
prompt_lib.get_prompt("topic_classification",
    max_topics=5,
    text="document text"
)

# Content Type Determination
prompt_lib.get_prompt("content_type_determination", text="document text")
```

### Vision Prompts

```python
# OCR Extraction
prompt_lib.get_prompt("ocr_extraction")  # No variables

# Image Analysis
prompt_lib.get_prompt("image_analysis",
    analysis_prompt="Describe the image"
)
```

### Chat Prompts

```python
# Direct LLM with History
prompt_lib.get_prompt("direct_llm_with_history",
    conversation_history="past messages",
    message="current message"
)

# Simple Direct LLM
prompt_lib.get_prompt("direct_llm_simple", message="user message")
```

## Common Patterns

### Pattern 1: Agent Execution

```python
prompt_lib = get_prompt_library()

system_msg = prompt_lib.get_system_prompt("research_analyst")
user_prompt = prompt_lib.get_prompt("research_analysis", query=q, documents=docs)

result = await llm_service.invoke_llm(
    prompt=user_prompt,
    system_message=system_msg,
    provider="custom"
)
```

### Pattern 2: RAG with Explainability Levels

```python
prompt_lib = get_prompt_library()

# Map explainability level to system prompt
system_map = {
    "basic": "rag_assistant_basic",
    "detailed": "rag_assistant_detailed",
    "debug": "rag_assistant_debug"
}

system_msg = prompt_lib.get_system_prompt(system_map[level])

# Build conditional elements
reasoning = ' in detail' if level in ['detailed', 'debug'] else ''
assumptions = '5. Note assumptions' if level == 'debug' else ''

prompt = prompt_lib.get_prompt(
    "rag_generation_with_sources",
    context=ctx,
    query=q,
    reasoning_detail=reasoning,
    assumptions_note=assumptions
)
```

### Pattern 3: Document Processing

```python
prompt_lib = get_prompt_library()

# Parallel processing
system_msg = prompt_lib.get_system_prompt("document_analyst")
summary_prompt = prompt_lib.get_prompt("document_summarization", text=text)
keyword_prompt = prompt_lib.get_prompt("keyword_extraction", max_keywords=10, text=text)

# Execute both
summary = await llm_service.generate_response(prompt=summary_prompt, ...)
keywords = await llm_service.generate_response(prompt=keyword_prompt, ...)
```

## Utility Functions

```python
# List all prompts in a category
agent_prompts = prompt_lib.list_prompts(category="agent")

# Get prompt metadata
metadata = prompt_lib.get_metadata("research_analysis")
print(metadata.variables)  # ['query', 'documents']

# Get usage statistics
stats = prompt_lib.get_usage_stats()
print(stats["most_used"])

# Export a prompt
data = prompt_lib.export_prompt("research_analysis")
print(data["template"])
```

## Error Handling

```python
try:
    prompt = prompt_lib.get_prompt("research_analysis", query="test")
except ValueError as e:
    # Missing required variable 'documents'
    print(f"Error: {e}")

try:
    prompt = prompt_lib.get_prompt("nonexistent_prompt")
except KeyError as e:
    # Prompt not found
    print(f"Error: {e}")
```

## Custom Prompts at Runtime

```python
from app.prompts.config import PromptMetadata

metadata = PromptMetadata(
    name="my_custom_prompt",
    category="custom",
    description="My custom prompt",
    variables=["input"],
    purpose="Special analysis"
)

prompt_lib.register_prompt(
    name="my_custom_prompt",
    template="Process: {input}\n\nResult:",
    metadata=metadata
)

# Use it
result = prompt_lib.get_prompt("my_custom_prompt", input="data")
```

## Categories Reference

| Category | Prompt Count | Use Case |
|----------|--------------|----------|
| `system` | 12 | Role definitions (no variables) |
| `agent` | 7 | Multi-agent system operations |
| `rag` | 3 | Retrieval augmented generation |
| `llm_service` | 4 | Document processing |
| `vision` | 2 | OCR and image analysis |
| `chat` | 2 | Direct LLM interactions |

## Best Practices Checklist

- ✅ Always use `get_prompt_library()` instead of hardcoding
- ✅ Pair system prompts with user prompts
- ✅ Handle `ValueError` for missing variables
- ✅ Handle `KeyError` for unknown prompt names
- ✅ Provide all required variables (check metadata)
- ✅ Use appropriate explainability level for RAG
- ✅ Monitor usage stats for optimization

## File Locations

```
backend/app/prompts/
├── __init__.py          # Import here
├── config.py            # PromptMetadata class
├── library.py           # PromptLibrary class
└── templates.py         # All prompt definitions
```

## Documentation

- **Full Documentation**: `backend/docs/PROMPT_LIBRARY.md`
- **This Quick Reference**: `backend/app/prompts/QUICK_REFERENCE.md`
- **Examples**: See documentation for detailed usage examples

---

**Last Updated**: December 5, 2025
**Version**: 1.0.0
