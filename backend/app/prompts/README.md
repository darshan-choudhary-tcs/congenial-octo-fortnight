# Prompt Library

A centralized, version-controlled system for managing all LLM prompts across the application.

## Overview

This package provides a unified interface for accessing and managing prompts used by:
- **Multi-Agent System** (Research, Analysis, Explainability)
- **RAG System** (Generation, Grounding Verification)
- **LLM Services** (Summarization, Keywords, Topics, Content Type)
- **Vision Services** (OCR, Image Analysis)
- **Chat API** (Direct LLM Interactions)

## Quick Start

```python
from app.prompts import get_prompt_library

# Get the singleton instance
prompt_lib = get_prompt_library()

# Get a system prompt
system_msg = prompt_lib.get_system_prompt("research_analyst")

# Get a user prompt with variables
user_prompt = prompt_lib.get_prompt(
    "research_analysis",
    query="What is RAG?",
    documents="Document 1: RAG stands for..."
)

# Use with LLM service
result = await llm_service.invoke_llm(
    prompt=user_prompt,
    system_message=system_msg,
    provider="custom"
)
```

## Features

✅ **20+ Pre-defined Prompts** across 6 categories
✅ **Centralized Management** - Single source of truth
✅ **Variable Substitution** - Dynamic content injection
✅ **Usage Analytics** - Track prompt usage patterns
✅ **Custom Prompts** - Register prompts at runtime
✅ **Type Safety** - Strong typing and error handling
✅ **Comprehensive Metadata** - Full documentation per prompt

## Structure

```
backend/app/prompts/
├── __init__.py              # Package exports
├── config.py                # Configuration and metadata classes
├── library.py               # PromptLibrary manager (singleton)
├── templates.py             # All prompt definitions
├── QUICK_REFERENCE.md       # Quick lookup guide
└── README.md                # This file
```

## Prompt Categories

### 1. System Prompts (12)
Role definitions for AI behavior - no variables needed.

**Examples:**
- `research_analyst` - Research and analysis role
- `document_analyst` - Document summarization role
- `rag_assistant_detailed` - Detailed RAG with citations

### 2. Agent Prompts (7)
Multi-agent system operations.

**Examples:**
- `research_analysis` - Analyze retrieved documents
- `general_analysis` - General data analysis
- `explanation_debug` - Comprehensive technical explanation

### 3. RAG Prompts (3)
Retrieval Augmented Generation.

**Examples:**
- `rag_generation_with_sources` - Context-based answers with citations
- `grounding_verification` - Verify response grounding

### 4. LLM Service Prompts (4)
Document processing operations.

**Examples:**
- `document_summarization` - Create summaries
- `keyword_extraction` - Extract key terms
- `topic_classification` - Identify topics

### 5. Vision Prompts (2)
OCR and image analysis.

**Examples:**
- `ocr_extraction` - Extract text from images
- `image_analysis` - Analyze image content

### 6. Chat Prompts (2)
Direct LLM interactions.

**Examples:**
- `direct_llm_with_history` - Chat with context
- `direct_llm_simple` - Simple direct chat

## Documentation

📖 **[Full Documentation](../../docs/PROMPT_LIBRARY.md)** - Comprehensive guide with examples, best practices, and API reference

📋 **[Quick Reference](QUICK_REFERENCE.md)** - Fast lookup for all prompts and common patterns

## Usage Examples

### Example 1: Using Agent Prompts

```python
from app.prompts import get_prompt_library

async def analyze_research_data(query: str, documents: list):
    prompt_lib = get_prompt_library()

    # Get prompts
    system_msg = prompt_lib.get_system_prompt("research_analyst")
    analysis_prompt = prompt_lib.get_prompt(
        "research_analysis",
        query=query,
        documents=format_documents(documents)
    )

    # Execute
    result = await llm_service.invoke_llm(
        prompt=analysis_prompt,
        system_message=system_msg,
        provider="custom"
    )

    return result
```

### Example 2: Using RAG Prompts

```python
from app.prompts import get_prompt_library

async def generate_rag_response(query: str, context: str, level: str):
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

    # Get prompt
    prompt = prompt_lib.get_prompt(
        "rag_generation_with_sources",
        context=context,
        query=query,
        reasoning_detail=reasoning,
        assumptions_note=assumptions
    )

    # Generate
    result = await llm_service.generate_response(
        prompt=prompt,
        system_message=system_msg,
        provider="custom"
    )

    return result
```

### Example 3: Using LLM Service Prompts

```python
from app.prompts import get_prompt_library

async def process_document(text: str):
    prompt_lib = get_prompt_library()

    # Get prompts
    system_msg = prompt_lib.get_system_prompt("document_analyst")
    summary_prompt = prompt_lib.get_prompt("document_summarization", text=text)

    # Generate summary
    result = await llm_service.generate_response(
        prompt=summary_prompt,
        system_message=system_msg,
        provider="custom"
    )

    return result
```

## Adding New Prompts

1. **Define in `templates.py`:**

```python
AGENT_PROMPTS = {
    "my_new_prompt": {
        "template": """Analyze: {data}

Instructions:
1. Find patterns
2. Provide insights

Analysis:""",
        "metadata": PromptMetadata(
            name="my_new_prompt",
            category="agent",
            description="My new analysis prompt",
            variables=["data"],
            purpose="Analyze custom data",
            output_format="structured_text"
        )
    }
}
```

2. **Use it:**

```python
prompt = prompt_lib.get_prompt("my_new_prompt", data="sample data")
```

## API Reference

### Main Functions

- `get_prompt_library()` - Get singleton instance
- `get_prompt(name, **kwargs)` - Get prompt with variable substitution
- `get_system_prompt(name)` - Get system prompt
- `register_prompt(name, template, metadata)` - Register custom prompt
- `get_metadata(name)` - Get prompt metadata
- `list_prompts(category)` - List available prompts
- `get_usage_stats()` - Get usage analytics
- `export_prompt(name)` - Export prompt data

See [Full Documentation](../../docs/PROMPT_LIBRARY.md#api-reference) for detailed API reference.

## Best Practices

✅ **Always use the library** - Don't hardcode prompts
✅ **Provide required variables** - Check metadata for requirements
✅ **Use system prompts** - Pair with user prompts
✅ **Handle exceptions** - `ValueError` for missing vars, `KeyError` for unknown prompts
✅ **Monitor usage** - Track stats for optimization
✅ **Document custom prompts** - Add comprehensive metadata

## Error Handling

```python
try:
    prompt = prompt_lib.get_prompt("research_analysis", query="test")
except ValueError as e:
    # Missing required variable
    print(f"Missing variable: {e}")
except KeyError as e:
    # Prompt not found
    print(f"Unknown prompt: {e}")
```

## Testing

```python
# Test prompt generation
prompt = prompt_lib.get_prompt(
    "research_analysis",
    query="Test query",
    documents="Test documents"
)

print(prompt)  # Verify output

# Check metadata
metadata = prompt_lib.get_metadata("research_analysis")
print(f"Required variables: {metadata.variables}")
```

## Migration from Hardcoded Prompts

**Before:**
```python
prompt = f"Analyze this: {data}"
system = "You are an analyst"
```

**After:**
```python
prompt_lib = get_prompt_library()
prompt = prompt_lib.get_prompt("general_analysis", data=data)
system = prompt_lib.get_system_prompt("data_analyst")
```

## Troubleshooting

### Common Issues

1. **Prompt not found** - Check spelling, use `list_prompts()`
2. **Missing variables** - Check metadata with `get_metadata()`
3. **Import errors** - Ensure correct Python path

See [Full Documentation - Troubleshooting](../../docs/PROMPT_LIBRARY.md#troubleshooting) for more details.

## Version

**Current Version:** 1.0.0
**Last Updated:** December 5, 2025

## Files Modified

The following files now use the Prompt Library:

- `backend/app/agents/base_agents.py` - Agent prompts
- `backend/app/rag/retriever.py` - RAG prompts
- `backend/app/services/llm_service.py` - LLM service prompts
- `backend/app/services/vision_service.py` - Vision prompts
- `backend/app/api/v1/chat.py` - Chat prompts

## Contributing

When adding new prompts:

1. Add to appropriate category in `templates.py`
2. Include comprehensive `PromptMetadata`
3. Update documentation
4. Test thoroughly
5. Submit pull request

## License

Part of the main application - follows same licensing terms.

---

For detailed documentation, examples, and advanced usage, see [PROMPT_LIBRARY.md](../../docs/PROMPT_LIBRARY.md).
