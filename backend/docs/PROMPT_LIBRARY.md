# Prompt Library Documentation

## Overview

The **Prompt Library** is a centralized system for managing all LLM prompts used throughout the application. It provides a consistent, maintainable, and version-controlled approach to prompt engineering across agents, RAG systems, LLM services, vision services, and chat APIs.

## Table of Contents

1. [Architecture](#architecture)
2. [Installation & Setup](#installation--setup)
3. [Quick Start](#quick-start)
4. [Prompt Categories](#prompt-categories)
5. [Usage Examples](#usage-examples)
6. [Adding New Prompts](#adding-new-prompts)
7. [Versioning Strategy](#versioning-strategy)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

---

## Architecture

### Components

```
backend/app/prompts/
├── __init__.py          # Package initialization and exports
├── config.py            # Configuration and metadata
├── library.py           # PromptLibrary manager class
└── templates.py         # All prompt templates organized by category
```

### Design Patterns

- **Singleton Pattern**: Single `PromptLibrary` instance throughout the application
- **Template Method**: Prompts use Python f-string formatting with named placeholders
- **Registry Pattern**: All prompts registered in a central dictionary
- **Metadata Pattern**: Each prompt includes descriptive metadata

### Key Features

✅ **Centralized Management** - All prompts in one location
✅ **Variable Substitution** - Dynamic content injection with validation
✅ **Usage Analytics** - Track prompt usage and access patterns
✅ **Custom Prompts** - Register custom prompts at runtime
✅ **Metadata Rich** - Complete documentation for each prompt
✅ **Type Safety** - Strong typing with error handling

---

## Installation & Setup

The Prompt Library is automatically initialized when the application starts. No additional setup is required.

### Importing

```python
from app.prompts import get_prompt_library

# Get the singleton instance
prompt_lib = get_prompt_library()
```

---

## Quick Start

### Basic Usage

```python
from app.prompts import get_prompt_library

# Get the library instance
prompt_lib = get_prompt_library()

# Get a simple system prompt (no variables)
system_prompt = prompt_lib.get_system_prompt("research_analyst")
# Returns: "You are a thorough research analyst focused on accuracy and relevance."

# Get a prompt with variables
analysis_prompt = prompt_lib.get_prompt(
    "research_analysis",
    query="What is RAG?",
    documents="Doc 1: RAG stands for..."
)
# Returns: Fully formatted prompt with variables substituted
```

### Integration Example

```python
from app.prompts import get_prompt_library
from app.services.llm_service import llm_service

async def analyze_documents(query: str, documents: list):
    prompt_lib = get_prompt_library()

    # Get prompts from library
    system_msg = prompt_lib.get_system_prompt("research_analyst")
    user_prompt = prompt_lib.get_prompt(
        "research_analysis",
        query=query,
        documents=format_docs(documents)
    )

    # Use with LLM service
    result = await llm_service.generate_response(
        prompt=user_prompt,
        system_message=system_msg,
        provider="custom"
    )

    return result
```

---

## Prompt Categories

### 1. System Prompts (Role Definitions)

Define the AI's role and behavior. No variables needed.

| Prompt Name | Description | Category |
|------------|-------------|----------|
| `research_analyst` | Research and analysis role | system |
| `data_analyst` | Data pattern recognition role | system |
| `transparency_expert` | AI explainability role | system |
| `fact_checker` | Fact-checking role | system |
| `document_analyst` | Document summarization role | system |
| `keyword_extractor` | Keyword extraction role | system |
| `document_classifier` | Topic classification role | system |
| `content_type_classifier` | Content type determination role | system |
| `helpful_assistant` | General chat assistance role | system |
| `rag_assistant_basic` | Basic RAG responses | system |
| `rag_assistant_detailed` | Detailed RAG with citations | system |
| `rag_assistant_debug` | Debug-level RAG with full transparency | system |

### 2. Agent Prompts

Multi-agent system prompts for research, analysis, and explainability.

| Prompt Name | Variables | Purpose |
|------------|-----------|---------|
| `research_analysis` | `query`, `documents` | Analyze retrieved documents |
| `general_analysis` | `data` | Perform general data analysis |
| `comparative_analysis` | `data` | Compare and contrast information |
| `trend_analysis` | `data` | Identify trends and patterns |
| `explanation_basic` | `response`, `source_count` | Simple explanation of AI reasoning |
| `explanation_detailed` | `response`, `sources`, `process` | Detailed explanation with source usage |
| `explanation_debug` | `response`, `sources_detailed`, `process` | Comprehensive technical explanation |

### 3. RAG Prompts

Retrieval Augmented Generation prompts.

| Prompt Name | Variables | Purpose |
|------------|-----------|---------|
| `rag_generation_with_sources` | `context`, `query`, `reasoning_detail`, `assumptions_note` | Generate context-based answers with citations |
| `rag_generation_simple` | `context`, `query` | Basic context-based answering |
| `grounding_verification` | `sources_text`, `response` | Verify response grounding in sources |

### 4. LLM Service Prompts

Document processing prompts.

| Prompt Name | Variables | Purpose |
|------------|-----------|---------|
| `document_summarization` | `text` | Create document summaries |
| `keyword_extraction` | `max_keywords`, `text` | Extract key terms |
| `topic_classification` | `max_topics`, `text` | Identify document topics |
| `content_type_determination` | `text` | Determine document genre |

### 5. Vision Prompts

OCR and image analysis prompts.

| Prompt Name | Variables | Purpose |
|------------|-----------|---------|
| `ocr_extraction` | None | Extract text from images |
| `image_analysis` | `analysis_prompt` | Analyze image content |

### 6. Chat Prompts

Direct LLM interaction prompts.

| Prompt Name | Variables | Purpose |
|------------|-----------|---------|
| `direct_llm_with_history` | `conversation_history`, `message` | Chat with conversation context |
| `direct_llm_simple` | `message` | Simple direct chat |

---

## Usage Examples

### Example 1: Research Agent

```python
from app.prompts import get_prompt_library

async def execute_research(query: str, retrieved_docs: list, provider: str):
    prompt_lib = get_prompt_library()

    # Format documents for the prompt
    formatted_docs = format_documents(retrieved_docs)

    # Get prompts
    system_msg = prompt_lib.get_system_prompt("research_analyst")
    analysis_prompt = prompt_lib.get_prompt(
        "research_analysis",
        query=query,
        documents=formatted_docs
    )

    # Execute with LLM
    analysis = await llm_service.invoke_llm(
        prompt=analysis_prompt,
        provider=provider,
        system_message=system_msg
    )

    return analysis
```

### Example 2: RAG Generation

```python
from app.prompts import get_prompt_library

async def generate_rag_response(query: str, context: str, explainability_level: str):
    prompt_lib = get_prompt_library()

    # Get system message based on explainability level
    system_prompt_map = {
        "basic": "rag_assistant_basic",
        "detailed": "rag_assistant_detailed",
        "debug": "rag_assistant_debug"
    }

    system_prompt_name = system_prompt_map.get(explainability_level, "rag_assistant_detailed")
    system_msg = prompt_lib.get_system_prompt(system_prompt_name)

    # Build dynamic prompt elements
    reasoning_detail = ' in detail' if explainability_level in ['detailed', 'debug'] else ''
    assumptions_note = '5. Note any assumptions or uncertainties' if explainability_level == 'debug' else ''

    # Get prompt
    prompt = prompt_lib.get_prompt(
        "rag_generation_with_sources",
        context=context,
        query=query,
        reasoning_detail=reasoning_detail,
        assumptions_note=assumptions_note
    )

    # Generate response
    result = await llm_service.generate_response(
        prompt=prompt,
        provider="custom",
        system_message=system_msg
    )

    return result
```

### Example 3: Document Summarization

```python
from app.prompts import get_prompt_library

async def summarize_document(text: str, provider: str):
    prompt_lib = get_prompt_library()

    # Get prompts from library
    system_msg = prompt_lib.get_system_prompt("document_analyst")
    prompt = prompt_lib.get_prompt("document_summarization", text=text)

    # Generate summary
    result = await llm_service.generate_response(
        prompt=prompt,
        provider=provider,
        system_message=system_msg
    )

    return result["summary"]
```

### Example 4: Grounding Verification

```python
from app.prompts import get_prompt_library

async def verify_grounding(response: str, sources: list, provider: str):
    prompt_lib = get_prompt_library()

    # Format sources
    sources_text = format_sources_for_verification(sources)

    # Get prompts
    system_msg = prompt_lib.get_system_prompt("fact_checker")
    verification_prompt = prompt_lib.get_prompt(
        "grounding_verification",
        sources_text=sources_text,
        response=response
    )

    # Verify
    result = await llm_service.generate_response(
        prompt=verification_prompt,
        provider=provider,
        system_message=system_msg
    )

    return result
```

---

## Adding New Prompts

### Step 1: Define Prompt Template

Edit `backend/app/prompts/templates.py`:

```python
# Add to appropriate category dictionary
AGENT_PROMPTS = {
    # ... existing prompts ...

    "custom_analysis": {
        "template": """Analyze the following data and provide insights:

Data: {data}

Focus Areas:
{focus_areas}

Provide:
1. Key findings
2. Actionable recommendations
3. Risk assessment

Analysis:""",
        "metadata": PromptMetadata(
            name="custom_analysis",
            category="agent",
            description="Custom analysis prompt with focus areas",
            variables=["data", "focus_areas"],
            purpose="Perform focused analysis on specific data",
            output_format="structured_text",
            version="1.0.0"
        )
    }
}
```

### Step 2: Register in Combined Registry

Ensure your category dictionary is included in `ALL_PROMPTS`:

```python
ALL_PROMPTS = {
    **SYSTEM_PROMPTS,
    **AGENT_PROMPTS,  # Your new prompt is here
    **RAG_PROMPTS,
    **LLM_SERVICE_PROMPTS,
    **VISION_PROMPTS,
    **CHAT_PROMPTS
}
```

### Step 3: Use Your New Prompt

```python
from app.prompts import get_prompt_library

prompt_lib = get_prompt_library()
prompt = prompt_lib.get_prompt(
    "custom_analysis",
    data="Sales data for Q1...",
    focus_areas="Revenue growth\nCustomer acquisition\nMarket trends"
)
```

### Registering Custom Prompts at Runtime

```python
from app.prompts import get_prompt_library
from app.prompts.config import PromptMetadata

prompt_lib = get_prompt_library()

# Create metadata
metadata = PromptMetadata(
    name="runtime_custom",
    category="custom",
    description="Runtime-registered custom prompt",
    variables=["input_data"],
    purpose="Handle special case analysis",
    output_format="json"
)

# Register prompt
prompt_lib.register_prompt(
    name="runtime_custom",
    template="Process this data: {input_data}\n\nResult:",
    metadata=metadata,
    override=False  # Set to True to replace existing prompts
)

# Use it
result = prompt_lib.get_prompt("runtime_custom", input_data="Sample data...")
```

---

## Versioning Strategy

### Current Approach

- **Version 1.0.0**: Initial prompt library implementation
- Each prompt includes a `version` field in its metadata
- Default version is "latest"

### Future Versioning

To implement prompt versioning:

1. **Naming Convention**: Use `prompt_name_v1`, `prompt_name_v2`
2. **Version Parameter**: Pass `version="v2"` to `get_prompt()`
3. **A/B Testing**: Track performance by version using usage analytics

```python
# Example future usage
prompt_v1 = prompt_lib.get_prompt("research_analysis", version="v1", ...)
prompt_v2 = prompt_lib.get_prompt("research_analysis", version="v2", ...)
```

### Version Tracking

```python
# Get prompt metadata to see version
metadata = prompt_lib.get_metadata("research_analysis")
print(f"Version: {metadata.version}")
print(f"Created: {metadata.created_at}")
print(f"Usage count: {metadata.usage_count}")
```

---

## Best Practices

### 1. Always Use the Library

❌ **Don't**: Hardcode prompts in your code
```python
prompt = f"Analyze this: {data}"
```

✅ **Do**: Use the prompt library
```python
prompt = prompt_lib.get_prompt("general_analysis", data=data)
```

### 2. Handle Missing Variables

The library validates required variables:

```python
try:
    prompt = prompt_lib.get_prompt("research_analysis", query="What is AI?")
    # Missing 'documents' variable
except ValueError as e:
    print(f"Error: {e}")
    # Error: Missing required variable 'documents' for prompt 'research_analysis'
```

### 3. Use System Prompts Consistently

```python
# Always pair system prompts with user prompts
system_msg = prompt_lib.get_system_prompt("data_analyst")
user_prompt = prompt_lib.get_prompt("trend_analysis", data=data)

result = await llm_service.generate_response(
    prompt=user_prompt,
    system_message=system_msg,
    provider="custom"
)
```

### 4. Document Your Custom Prompts

Always provide comprehensive metadata:

```python
metadata = PromptMetadata(
    name="my_prompt",
    category="custom",
    description="Clear description of what this prompt does",
    variables=["var1", "var2"],
    purpose="Specific use case and context",
    output_format="Expected output format",
    examples=["Example usage 1", "Example usage 2"]
)
```

### 5. Monitor Prompt Performance

```python
# Get usage statistics
stats = prompt_lib.get_usage_stats()

print(f"Total prompts: {stats['total_prompts']}")
print(f"Most used prompts: {stats['most_used']}")

# Export specific prompt for analysis
prompt_data = prompt_lib.export_prompt("research_analysis")
```

### 6. Test Prompts Before Deploying

```python
# Test with sample data
test_query = "Sample query"
test_docs = "Sample documents"

prompt = prompt_lib.get_prompt(
    "research_analysis",
    query=test_query,
    documents=test_docs
)

print("Generated prompt:")
print(prompt)
# Verify the output looks correct before using in production
```

### 7. Keep Prompts Atomic

Each prompt should serve **one clear purpose**:

- ✅ Good: `document_summarization` - Creates summaries
- ✅ Good: `keyword_extraction` - Extracts keywords
- ❌ Bad: `document_analysis_and_keywords` - Does too much

---

## API Reference

### PromptLibrary Class

#### `get_prompt(name: str, version: str = "latest", **kwargs) -> str`

Get a prompt template with variable substitution.

**Parameters:**
- `name` (str): Name of the prompt
- `version` (str): Version (default: "latest")
- `**kwargs`: Variables to substitute in the template

**Returns:** Formatted prompt string

**Raises:**
- `KeyError`: If prompt name not found
- `ValueError`: If required variables are missing

**Example:**
```python
prompt = prompt_lib.get_prompt(
    "research_analysis",
    query="What is AI?",
    documents="Doc 1: AI is..."
)
```

#### `get_system_prompt(name: str) -> str`

Get a system prompt (role definition) without variable substitution.

**Parameters:**
- `name` (str): Name of the system prompt

**Returns:** System prompt string

**Example:**
```python
system_msg = prompt_lib.get_system_prompt("research_analyst")
```

#### `register_prompt(name: str, template: str, metadata: PromptMetadata, override: bool = False) -> bool`

Register a new custom prompt.

**Parameters:**
- `name` (str): Unique name for the prompt
- `template` (str): Prompt template with {variables}
- `metadata` (PromptMetadata): Metadata object
- `override` (bool): Whether to override existing (default: False)

**Returns:** True if registered, False if name exists and override=False

**Example:**
```python
metadata = PromptMetadata(
    name="custom",
    category="agent",
    description="Custom prompt",
    variables=["data"]
)

success = prompt_lib.register_prompt(
    "custom",
    "Analyze: {data}",
    metadata
)
```

#### `get_metadata(name: str) -> Optional[PromptMetadata]`

Get metadata for a prompt.

**Parameters:**
- `name` (str): Name of the prompt

**Returns:** PromptMetadata object or None

#### `list_prompts(category: Optional[str] = None) -> Dict[str, PromptMetadata]`

List all available prompts, optionally filtered by category.

**Parameters:**
- `category` (str, optional): Filter by category

**Returns:** Dictionary mapping prompt names to metadata

**Example:**
```python
# List all agent prompts
agent_prompts = prompt_lib.list_prompts(category="agent")

# List all prompts
all_prompts = prompt_lib.list_prompts()
```

#### `get_usage_stats() -> Dict[str, Any]`

Get usage statistics for all prompts.

**Returns:** Dictionary with usage counts and analytics

**Example:**
```python
stats = prompt_lib.get_usage_stats()
print(stats["most_used"])  # Top 10 most used prompts
```

#### `export_prompt(name: str) -> Optional[Dict[str, Any]]`

Export a prompt with its metadata and template.

**Parameters:**
- `name` (str): Name of the prompt

**Returns:** Dictionary with prompt data or None

---

## Troubleshooting

### Issue: "Prompt not found"

**Error:** `KeyError: Prompt 'my_prompt' not found in library`

**Solution:**
1. Check the prompt name spelling
2. Verify the prompt exists in `templates.py`
3. List available prompts: `prompt_lib.list_prompts()`

### Issue: "Missing required variable"

**Error:** `ValueError: Missing required variable 'documents' for prompt 'research_analysis'`

**Solution:**
1. Check the prompt metadata for required variables
2. Ensure all variables are provided in `get_prompt()` call

```python
metadata = prompt_lib.get_metadata("research_analysis")
print(f"Required variables: {metadata.variables}")
```

### Issue: Import errors

**Error:** `ModuleNotFoundError: No module named 'app.prompts'`

**Solution:**
1. Ensure you're running from the correct directory
2. Check Python path includes the backend directory
3. Verify all `__init__.py` files exist

### Issue: Prompt formatting issues

**Problem:** Variables not being substituted correctly

**Solution:**
1. Use named placeholders: `{variable_name}`
2. Don't use f-strings when defining templates
3. Pass variables as keyword arguments

```python
# ✅ Correct
template = "Analyze: {data}"
prompt = prompt_lib.get_prompt("my_prompt", data="sample")

# ❌ Wrong
template = f"Analyze: {data}"  # Don't use f-strings in templates
```

---

## Performance Considerations

### Caching

The PromptLibrary uses a singleton pattern, so prompts are loaded once and reused throughout the application lifecycle.

### Memory Usage

- All prompts are stored in memory
- Typical memory footprint: < 1 MB
- Usage analytics adds minimal overhead

### Recommendations

- Use the library for all prompts (don't duplicate)
- Monitor usage stats to identify optimization opportunities
- Consider prompt length when dealing with token limits

---

## Migration Guide

### Migrating Existing Code

**Before:**
```python
prompt = f"""Analyze the following documents for: "{query}"

Documents:
{format_docs(docs)}

Provide key findings..."""

system = "You are a research analyst..."
```

**After:**
```python
prompt_lib = get_prompt_library()

prompt = prompt_lib.get_prompt(
    "research_analysis",
    query=query,
    documents=format_docs(docs)
)

system = prompt_lib.get_system_prompt("research_analyst")
```

### Benefits of Migration

✅ Centralized prompt management
✅ Easier A/B testing and optimization
✅ Version control and history tracking
✅ Consistent prompt engineering patterns
✅ Usage analytics and monitoring
✅ Better code maintainability

---

## Contributing

### Adding New Prompts

1. Define the prompt in `templates.py`
2. Add comprehensive metadata
3. Update this documentation
4. Test thoroughly with sample data
5. Submit a pull request

### Prompt Engineering Guidelines

1. **Be Specific**: Clear, unambiguous instructions
2. **Use Structure**: Numbered lists, clear sections
3. **Include Examples**: When helpful for the model
4. **Set Constraints**: "ONLY return...", "Do not..."
5. **Request Format**: Specify expected output format
6. **Test Variations**: Try different phrasings

---

## Support

For questions or issues:

1. Check this documentation
2. Review the [Troubleshooting](#troubleshooting) section
3. Examine prompt templates in `backend/app/prompts/templates.py`
4. Contact the development team

---

## Changelog

### Version 1.0.0 (December 5, 2025)

- Initial prompt library implementation
- 20+ prompts across 6 categories
- Singleton pattern with usage analytics
- Comprehensive documentation
- Full integration with agents, RAG, LLM services, vision, and chat APIs

---

## License

This prompt library is part of the internal application and follows the same licensing terms.
