# RAG (Retrieval-Augmented Generation) Documentation

## Overview

The RAG system implements **advanced document processing and retrieval** to ground AI responses in factual, source-attributed information. It combines semantic search with metadata filtering for precise, relevant retrieval.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Document Ingestion                         │
├──────────────────────────────────────────────────────────────┤
│  Upload → Extract → Metadata Gen → Chunk → Embed → Store    │
└────────────────┬─────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────┐
│                     Storage Layer                             │
├──────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Document  │  │   Chunks   │  │  ChromaDB  │            │
│  │   (SQLite) │  │  (SQLite)  │  │ (Vectors)  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└────────────────┬─────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────┐
│                    Query Processing                           │
├──────────────────────────────────────────────────────────────┤
│  Query → Extract Intent → Metadata-Boosted Search → Rank    │
└────────────────┬─────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────┐
│                  Response Generation                          │
├──────────────────────────────────────────────────────────────┤
│  Context Build → LLM Generate → Source Attribution          │
└──────────────────────────────────────────────────────────────┘
```

## Components

### 1. Document Processor

**Purpose**: Extract text from various document formats.

**Supported Formats**:

#### PDF Documents (`.pdf`)
- **Library**: pypdf
- **Extraction**: Page-by-page text extraction
- **Metadata**: Page numbers, page count, author, creation date
- **Limitations**: May struggle with scanned PDFs (use OCR)

```python
from app.rag.document_processor import DocumentProcessor

processor = DocumentProcessor()
result = await processor.process_pdf("path/to/document.pdf")

# Returns:
{
    "text": "Full document text...",
    "metadata": {
        "page_count": 45,
        "author": "John Doe",
        "pages": [
            {"page_number": 1, "text": "Page 1 content..."},
            {"page_number": 2, "text": "Page 2 content..."}
        ]
    }
}
```

#### Word Documents (`.docx`)
- **Library**: python-docx
- **Extraction**: Paragraph-based extraction
- **Metadata**: Paragraph count, tables, images
- **Preserves**: Basic formatting structure

```python
result = await processor.process_docx("path/to/document.docx")

# Returns:
{
    "text": "Full document text...",
    "metadata": {
        "paragraph_count": 87,
        "has_tables": true,
        "has_images": true
    }
}
```

#### Text Files (`.txt`)
- **Encoding**: UTF-8 with fallback
- **Extraction**: Direct read
- **Simple and fast**

```python
result = await processor.process_txt("path/to/document.txt")
```

#### CSV Files (`.csv`)
- **Library**: pandas
- **Processing**: Converts tabular data to searchable text
- **Includes**:
  - Column names and descriptions
  - Row samples (first 5, last 5)
  - Statistical summaries
  - Value distributions
  - Data types

```python
result = await processor.process_csv("path/to/data.csv")

# Returns:
{
    "text": "Dataset contains 5 columns: Date, Location, Consumption_kWh...\n\nSample data:\n...\n\nStatistics:\n- Average consumption: 12,500 kWh...",
    "metadata": {
        "row_count": 1000,
        "column_count": 5,
        "columns": ["Date", "Location", "Consumption_kWh", ...],
        "statistics": {...}
    }
}
```

**Energy CSV Special Processing**:

For historical energy data:
```python
result = await processor.process_energy_csv("path/to/energy_data.csv")

# Additional processing:
# - Energy-specific metadata extraction
# - Sustainability metrics calculation
# - Anomaly detection
# - Optimization insights
# - ChromaDB collection creation
```

---

### 2. Text Chunker

**Purpose**: Split documents into optimal-sized chunks for embedding and retrieval.

**Configuration**:
- **Chunk Size**: Default 1000 characters (configurable)
- **Chunk Overlap**: Default 200 characters (configurable)
- **Separators**: Hierarchical (paragraphs → sentences → words)

**Chunking Strategy**:

1. **Paragraph-First**: Prefers natural paragraph breaks
2. **Sentence-Aware**: Doesn't break mid-sentence if possible
3. **Overlap**: Maintains context across chunks
4. **Token Counting**: Tracks tokens per chunk

```python
from app.rag.text_chunker import TextChunker

chunker = TextChunker(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = chunker.chunk_text(
    text="Long document text...",
    metadata={"document_id": 45, "page_number": 1}
)

# Returns:
[
    {
        "chunk_index": 0,
        "content": "First chunk of text...",
        "token_count": 245,
        "metadata": {"document_id": 45, "page_number": 1}
    },
    {
        "chunk_index": 1,
        "content": "Second chunk with overlap from first...",
        "token_count": 238,
        "metadata": {"document_id": 45, "page_number": 1}
    }
]
```

**Chunk Size Guidelines**:
- **Small (500)**: Fast retrieval, less context, more chunks
- **Medium (1000)**: Balanced (recommended)
- **Large (2000)**: More context, slower, fewer chunks

**Overlap Guidelines**:
- **Low (100)**: Faster processing, potential context loss
- **Medium (200)**: Balanced (recommended)
- **High (400)**: Better context, more redundancy

---

### 3. OCR Processor

**Purpose**: Extract text from scanned documents and images.

**Capabilities**:
- PDF to image conversion
- Vision model-based OCR (Ollama llama3.2-vision)
- Confidence scoring
- Multi-page processing

**Configuration**:
```python
from app.rag.ocr_processor import OCRProcessor

ocr = OCRProcessor(
    ollama_base_url="http://localhost:11434",
    model="llama3.2-vision",
    confidence_threshold=0.7
)
```

**Usage**:

```python
# Process scanned PDF
result = await ocr.process_pdf("path/to/scanned.pdf")

# Returns:
{
    "text": "Extracted text from all pages...",
    "pages": [
        {
            "page_number": 1,
            "text": "Page 1 extracted text...",
            "confidence": 0.89
        }
    ],
    "avg_confidence": 0.87,
    "method": "vision_model"
}

# Process single image
result = await ocr.process_image("path/to/image.png")
```

**Confidence Threshold**:
- Pages with confidence below threshold are flagged
- User warned about potential OCR errors
- Can reprocess with different settings

**Limitations**:
- Depends on vision model quality
- Slower than native text extraction
- May struggle with handwriting or poor quality scans

---

### 4. Vector Store Service

**Purpose**: Manage ChromaDB collections for semantic search.

**Collection Strategy**:

Collections are organized by:
- **Scope**: `global`, `company_<id>`, `user_<id>`
- **Provider**: `custom`, `ollama`

**Format**: `{scope}_{provider}`

**Examples**:
- `global_custom`: Global documents with custom embeddings
- `company_1_custom`: Company 1 documents with custom embeddings
- `user_5_ollama`: User 5 documents with Ollama embeddings

**Benefits**:
- Data isolation
- Provider flexibility
- Efficient querying

**Implementation**:

```python
from app.services.vector_store import VectorStoreService

vector_store = VectorStoreService(
    chroma_persist_dir="./chroma_db",
    llm_service=llm_service
)

# Add documents
await vector_store.add_documents(
    documents=[
        {
            "id": "doc45_chunk0",
            "content": "Document text...",
            "metadata": {
                "document_id": 45,
                "chunk_index": 0,
                "keywords": ["solar", "california"],
                "topics": ["Renewable Energy"]
            }
        }
    ],
    scope="company",
    company_id=1,
    provider="custom"
)

# Search single collection
results = await vector_store.search(
    query="renewable energy in California",
    scope="company",
    company_id=1,
    provider="custom",
    n_results=5
)

# Search multiple collections
results = await vector_store.search_multi_collection(
    query="renewable energy in California",
    scopes=["global", "company"],
    company_id=1,
    provider="custom",
    n_results=5
)
```

**Metadata Filtering**:

ChromaDB supports metadata filters for precise retrieval:

```python
# Filter by keywords
results = await vector_store.search(
    query="energy solutions",
    metadata_filter={
        "keywords": {"$contains": "solar"}
    },
    scope="company",
    company_id=1
)

# Filter by multiple topics
results = await vector_store.search(
    query="sustainability report",
    metadata_filter={
        "topics": {"$in": ["Renewable Energy", "Climate Action"]}
    },
    scope="company",
    company_id=1
)
```

**Collection Management**:

```python
# Get collection info
info = await vector_store.get_collection_info(
    scope="company",
    company_id=1,
    provider="custom"
)

# Returns:
{
    "name": "company_1_custom",
    "count": 587,
    "metadata": {...}
}

# Delete collection
await vector_store.delete_collection(
    scope="company",
    company_id=1,
    provider="custom"
)
```

---

### 5. Retriever

**Purpose**: Intelligent document retrieval with metadata boosting.

**Retrieval Strategies**:

#### Standard Vector Search

Basic semantic similarity search:

```python
from app.rag.retriever import Retriever

retriever = Retriever(
    llm_service=llm_service,
    vector_store=vector_store
)

results = await retriever.retrieve(
    query="What are the best renewable energy options for California?",
    user_id=5,
    company_id=1,
    n_results=5
)
```

#### Metadata-Boosted Retrieval

Two-stage retrieval with query intent extraction:

**Stage 1: Query Analysis**
```python
# Extract keywords and topics from query
query_metadata = await retriever._extract_query_metadata(
    query="renewable energy options for California manufacturing"
)

# Returns:
{
    "keywords": ["renewable", "energy", "california", "manufacturing"],
    "topics": ["Renewable Energy", "Industrial Solutions"]
}
```

**Stage 2: Filtered Search**
```python
# Try 1: Filter by keywords
results = await retriever._search_with_metadata(
    query=query,
    keywords=["renewable", "energy", "california"],
    n_results=5
)

# If insufficient results:
# Try 2: Filter by topics
results = await retriever._search_with_metadata(
    query=query,
    topics=["Renewable Energy"],
    n_results=5
)

# If still insufficient:
# Try 3: Standard vector search (no filter)
results = await retriever.retrieve(query, n_results=5)
```

**Benefits**:
- Higher precision (retrieves more relevant documents)
- Reduced noise (filters out unrelated documents)
- Graceful fallback (always returns results)
- Better for domain-specific queries

**Example**:

```python
# Query about solar energy in California
query = "solar panel efficiency in California climate"

# Metadata-boosted retrieval:
results = await retriever.retrieve_with_metadata_boost(
    query=query,
    user_id=5,
    company_id=1,
    n_results=5
)

# Returns documents with:
# - High semantic similarity to query
# - Matching keywords: "solar", "california", "efficiency"
# - Relevant topics: "Renewable Energy", "Solar Technology"
```

---

### 6. Similarity Scoring

**Purpose**: Convert ChromaDB distance to intuitive similarity score.

**Distance Metric**: ChromaDB returns squared Euclidean distance
- **0.0**: Identical vectors
- **Larger values**: More dissimilar

**Calibration Formula**:
```python
similarity = 1 / (1 + distance * 0.1)
```

**Score Range**:
- **1.0**: Perfect match (identical)
- **0.9-0.99**: Highly similar
- **0.7-0.89**: Moderately similar
- **0.5-0.69**: Somewhat similar
- **< 0.5**: Low similarity

**Example Conversions**:
```python
distance = 0.0   → similarity = 1.0
distance = 0.5   → similarity = 0.95
distance = 1.0   → similarity = 0.91
distance = 5.0   → similarity = 0.67
distance = 10.0  → similarity = 0.50
distance = 20.0  → similarity = 0.33
```

**No Hard Threshold**:
- System returns top N most relevant results
- Confidence scoring uses similarity as one factor
- User sees similarity scores for transparency

---

### 7. Response Generation

**Purpose**: Generate contextual responses with source attribution.

**Process**:

#### 1. Context Building

```python
context = retriever._build_context(retrieved_docs)

# Format:
"""
[Source 1: California Energy Report.pdf, Page 15]
California receives 5.3-5.7 kWh/m²/day solar irradiance, making it ideal for solar installations...

[Source 2: Renewable Technology Guide.docx]
Solar panel efficiency has improved 25% in the last decade, with modern panels achieving 22-24% efficiency...
"""
```

#### 2. Prompt Construction

```python
from app.prompts.library import PromptLibrary

prompt_lib = PromptLibrary()

prompt = prompt_lib.get_prompt(
    "rag_assistant_detailed",
    query=user_query,
    context=context,
    explainability_level="detailed"
)
```

#### 3. LLM Generation

```python
response = await llm_service.generate_with_metadata(
    prompt=prompt,
    temperature=0.7
)
```

#### 4. Source Attribution

```python
sources = retriever._extract_sources(retrieved_docs, response)

# Returns:
[
    {
        "document_id": 45,
        "document_name": "California Energy Report.pdf",
        "chunk_id": 234,
        "page_number": 15,
        "content": "California receives 5.3-5.7 kWh/m²/day...",
        "relevance_score": 0.92
    }
]
```

**Full Example**:

```python
result = await retriever.generate_response(
    query="What is California's solar potential?",
    user_id=5,
    company_id=1,
    explainability_level="detailed"
)

# Returns:
{
    "response": "California has excellent solar potential with average irradiance of 5.5 kWh/m²/day...",
    "sources": [...],
    "confidence": 0.89,
    "token_usage": {...}
}
```

---

## Document Ingestion Pipeline

### Complete Flow

```python
# 1. Upload document
document = await upload_document(
    file=uploaded_file,
    user_id=5,
    company_id=1,
    scope="company"
)

# 2. Extract text
text_data = await document_processor.process(
    file_path=document.file_path,
    file_type=document.file_type
)

# 3. Generate metadata with LLM
metadata = await llm_service.generate_document_metadata(
    text=text_data["text"]
)

# Returns:
{
    "summary": "This report analyzes renewable energy trends...",
    "keywords": ["solar", "wind", "renewable", "california"],
    "topics": ["Renewable Energy", "Climate Policy"],
    "content_type": "technical_report"
}

# 4. Update document record
document.summary = metadata["summary"]
document.keywords = metadata["keywords"]
document.topics = metadata["topics"]
document.is_processed = True

# 5. Chunk text
chunks = text_chunker.chunk_text(
    text=text_data["text"],
    metadata={"document_id": document.id}
)

# 6. Generate embeddings and store
for chunk in chunks:
    # Save chunk to database
    db_chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=chunk["chunk_index"],
        content=chunk["content"],
        token_count=chunk["token_count"],
        embedding_id=f"doc{document.id}_chunk{chunk['chunk_index']}"
    )
    db.add(db_chunk)

    # Add to vector store
    await vector_store.add_documents(
        documents=[{
            "id": db_chunk.embedding_id,
            "content": chunk["content"],
            "metadata": {
                "document_id": document.id,
                "chunk_index": chunk["chunk_index"],
                "keywords": document.keywords,
                "topics": document.topics
            }
        }],
        scope="company",
        company_id=company_id,
        provider="custom"
    )

# 7. Commit to database
db.commit()

# Document ready for retrieval!
```

---

## Query Processing Pipeline

### Complete Flow

```python
# 1. User submits query
query = "What are the best renewable energy options for California?"

# 2. Validate query quality
quality = await retriever._validate_query(query)
if quality["is_gibberish"]:
    return error("Please provide a clear question")

# 3. Extract query metadata
query_metadata = await retriever._extract_query_metadata(query)
# Returns: keywords, topics

# 4. Retrieve documents (metadata-boosted)
retrieved_docs = await retriever.retrieve_with_metadata_boost(
    query=query,
    user_id=5,
    company_id=1,
    keywords=query_metadata["keywords"],
    topics=query_metadata["topics"],
    n_results=5
)

# 5. Build context from retrieved docs
context = retriever._build_context(retrieved_docs)

# 6. Generate response with LLM
response = await llm_service.generate_with_metadata(
    prompt=build_prompt(query, context),
    temperature=0.7
)

# 7. Extract source attribution
sources = retriever._extract_sources(retrieved_docs, response)

# 8. Calculate confidence
confidence = calculate_confidence(
    retrieved_docs=retrieved_docs,
    response=response,
    query_quality=quality
)

# 9. Return complete result
return {
    "response": response["content"],
    "sources": sources,
    "confidence": confidence,
    "query_metadata": query_metadata,
    "documents_retrieved": len(retrieved_docs),
    "token_usage": response["token_usage"]
}
```

---

## Multi-Collection Search

**Purpose**: Search across multiple scopes simultaneously.

**Use Cases**:
- User wants access to both global and company documents
- Search across user's personal docs + company docs
- Cross-company search (super admin only)

**Implementation**:

```python
# Search global + company collections
results = await vector_store.search_multi_collection(
    query="renewable energy trends",
    scopes=["global", "company"],
    company_id=1,
    provider="custom",
    n_results=5
)

# Behind the scenes:
# 1. Search global collection
global_results = search(collection="global_custom", query=query, n=5)

# 2. Search company collection
company_results = search(collection="company_1_custom", query=query, n=5)

# 3. Merge results
all_results = global_results + company_results

# 4. Deduplicate by document ID
unique_results = deduplicate(all_results)

# 5. Re-rank by similarity
sorted_results = sort_by_similarity(unique_results)

# 6. Return top N
return sorted_results[:n_results]
```

**Benefits**:
- Broader knowledge base
- Still respects data isolation
- Automatic deduplication
- Single unified result set

---

## Provider Fallback

**Purpose**: Ensure availability when primary LLM provider fails.

**Strategy**:

```python
try:
    # Try primary provider (custom)
    results = await vector_store.search(
        query=query,
        provider="custom",
        ...
    )
except ProviderError:
    logger.warning("Custom provider failed, trying Ollama")

    # Fallback to Ollama
    results = await vector_store.search(
        query=query,
        provider="ollama",
        ...
    )
```

**Applied To**:
- Embedding generation
- Query processing
- Metadata extraction

**Transparent to User**: System automatically handles fallback

---

## Configuration

### Environment Variables

```bash
# RAG Settings
CHUNK_SIZE=1000                    # Characters per chunk
CHUNK_OVERLAP=200                  # Overlap between chunks
MAX_RETRIEVAL_DOCS=5               # Max documents to retrieve
SIMILARITY_THRESHOLD=0.01          # Minimum similarity (not strictly enforced)

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=documents

# OCR
OCR_SUPPORTED_FORMATS=pdf,png,jpg,jpeg
OCR_MAX_FILE_SIZE=10485760        # 10MB
OCR_CONFIDENCE_THRESHOLD=0.7

# Document Processing
MAX_UPLOAD_SIZE=10485760           # 10MB
ALLOWED_EXTENSIONS=pdf,docx,txt,csv
UPLOAD_DIR=./uploads
```

### Programmatic Configuration

```python
from app.config import settings

# Override chunk size
custom_chunker = TextChunker(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP
)

# Override retrieval count
results = await retriever.retrieve(
    query=query,
    n_results=10  # Override MAX_RETRIEVAL_DOCS
)
```

---

## Performance Optimization

### 1. Collection Caching

Vector store caches collection objects in memory:

```python
# First access: Loads from disk
collection = vector_store._get_collection("company_1_custom")

# Subsequent accesses: Cached in memory
collection = vector_store._get_collection("company_1_custom")  # Fast!
```

### 2. Batch Processing

Process multiple documents efficiently:

```python
# Bad: One at a time
for doc in documents:
    await vector_store.add_documents([doc], ...)

# Good: Batch
await vector_store.add_documents(documents, ...)
```

### 3. Parallel Searches

Search multiple collections in parallel:

```python
import asyncio

# Parallel search
results = await asyncio.gather(
    vector_store.search(query, scope="global"),
    vector_store.search(query, scope="company", company_id=1),
    vector_store.search(query, scope="user", user_id=5)
)
```

### 4. Embedding Caching

tiktoken (tokenizer) has built-in caching for speed.

---

## Best Practices

### Document Upload

1. **Validate before processing**: Check file size, type
2. **Set appropriate scope**: global, company, or user
3. **Generate quality metadata**: Improves retrieval
4. **Monitor processing time**: Alert if taking too long
5. **Handle errors gracefully**: Partial failures, rollback

### Chunking

1. **Use default 1000/200**: Works well for most documents
2. **Larger chunks for technical docs**: More context needed
3. **Smaller chunks for summaries**: Quick facts
4. **Consistent chunking**: Same settings across documents

### Retrieval

1. **Use metadata boost**: Significantly improves precision
2. **Multi-collection search**: Broader results
3. **Limit results**: 5-10 typically sufficient
4. **Check similarity scores**: Low scores = poor match
5. **Provide context**: Selected documents help focus

### Response Generation

1. **Include source attribution**: Transparency
2. **Use appropriate explainability**: Match user needs
3. **Calculate confidence**: Help users assess reliability
4. **Track token usage**: Monitor costs
5. **Enable grounding**: Prevent hallucinations

---

## Troubleshooting

### No Results Retrieved

**Symptoms**: Empty or very few results

**Causes**:
- Documents not processed
- Embedding mismatch (different providers)
- Query too specific
- Metadata filter too restrictive

**Solutions**:
1. Verify documents are processed: Check `is_processed` flag
2. Check collection exists: `get_collection_info()`
3. Try without metadata filter
4. Simplify query
5. Check provider matches (custom vs ollama)

---

### Low Similarity Scores

**Symptoms**: All results have similarity < 0.5

**Causes**:
- Query-document mismatch (wrong domain)
- Poor document quality
- Embedding model limitations
- Query too vague

**Solutions**:
1. Upload more relevant documents
2. Improve query specificity
3. Use metadata boost
4. Try different provider
5. Check document summaries for relevance

---

### High Token Usage

**Symptoms**: Expensive queries

**Causes**:
- Large chunks
- Many retrieved documents
- Detailed explainability
- Metadata generation

**Solutions**:
1. Reduce chunk size
2. Limit retrieved documents (n_results)
3. Use basic explainability
4. Batch metadata generation
5. Use Ollama for embeddings (free)

---

### Processing Failures

**Symptoms**: Documents stuck in "processing" status

**Causes**:
- File corruption
- Unsupported format
- LLM timeout
- ChromaDB connection error

**Solutions**:
1. Check file integrity
2. Verify format support
3. Increase timeouts
4. Check ChromaDB status
5. Retry with error logging

---

### Duplicate Results

**Symptoms**: Same content appears multiple times

**Causes**:
- Document uploaded multiple times
- Chunks overlapping too much
- Multi-collection search without dedup

**Solutions**:
1. Delete duplicate documents
2. Reduce chunk overlap
3. Enable deduplication in multi-collection search
4. Check document IDs

---

## Testing

### Unit Tests

```python
import pytest
from app.rag.text_chunker import TextChunker

def test_text_chunking():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    text = "A" * 500
    chunks = chunker.chunk_text(text)

    assert len(chunks) > 0
    assert all(len(c["content"]) <= 120 for c in chunks)  # Allow overlap
    assert chunks[0]["chunk_index"] == 0

@pytest.mark.asyncio
async def test_document_retrieval(mock_vector_store):
    retriever = Retriever(mock_llm_service, mock_vector_store)
    results = await retriever.retrieve("test query", user_id=1, company_id=1)

    assert len(results) > 0
    assert all("similarity" in r for r in results)
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_ingestion_pipeline(test_db, llm_service, vector_store):
    # Upload document
    document = await upload_document(...)

    # Process
    await process_document(document.id, test_db, llm_service, vector_store)

    # Verify in database
    assert document.is_processed
    assert document.summary is not None

    # Verify in vector store
    results = await vector_store.search(query="test", ...)
    assert len(results) > 0
```

---

For more information, see:
- [Main Backend Documentation](../../README.md)
- [Agent System Documentation](../agents/README.md)
- [API Documentation](../api/README.md)
