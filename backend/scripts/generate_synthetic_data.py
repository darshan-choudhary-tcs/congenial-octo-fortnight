"""
Script to generate synthetic data for demonstration
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database.db import SessionLocal
from app.database.models import Document, DocumentChunk
from app.services.vector_store import vector_store_service
from app.rag.document_processor import TextChunker
import asyncio
from loguru import logger

# Synthetic documents
SYNTHETIC_DOCUMENTS = [
    {
        "filename": "ai_concepts_guide.txt",
        "title": "Guide to AI Concepts",
        "content": """# Artificial Intelligence Concepts Guide

## Introduction to AI
Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn. Modern AI systems can perform tasks such as visual perception, speech recognition, decision-making, and language translation.

## Machine Learning
Machine Learning (ML) is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.

### Supervised Learning
In supervised learning, the algorithm learns from labeled training data and makes predictions based on that data. Examples include classification and regression tasks.

### Unsupervised Learning
Unsupervised learning involves training on unlabeled data, where the algorithm tries to learn the underlying structure. Clustering and dimensionality reduction are common applications.

## Deep Learning
Deep Learning is a subset of machine learning based on artificial neural networks. It uses multiple layers to progressively extract higher-level features from raw input.

### Neural Networks
Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes (neurons) that process information.

## Natural Language Processing
Natural Language Processing (NLP) enables computers to understand, interpret, and generate human language. Applications include chatbots, translation services, and sentiment analysis.

## Computer Vision
Computer Vision enables machines to interpret and understand visual information from the world. Applications include facial recognition, object detection, and autonomous vehicles.

## Explainable AI (XAI)
Explainable AI focuses on making AI decisions transparent and interpretable to humans. This is crucial for building trust and ensuring accountability in AI systems.

## Grounding in AI
Grounding refers to ensuring that AI responses are based on factual information from reliable sources rather than generating potentially incorrect information (hallucinations).

## Retrieval Augmented Generation (RAG)
RAG combines information retrieval with text generation, allowing AI models to generate responses grounded in retrieved documents. This improves accuracy and reduces hallucinations.
""",
        "category": "AI Concepts"
    },
    {
        "filename": "multi_agent_systems.txt",
        "title": "Multi-Agent Systems Overview",
        "content": """# Multi-Agent Systems in AI

## Introduction
Multi-agent systems involve multiple autonomous agents working together to solve complex problems. Each agent can have specialized capabilities and can communicate with other agents.

## Agent Architecture
An agent is an autonomous entity that observes its environment and acts upon it. Key components include:
- Perception: Sensing the environment
- Reasoning: Decision-making process
- Action: Executing decisions

## Types of Agents

### Reactive Agents
Reactive agents respond directly to environmental stimuli without complex reasoning. They are fast but limited in capability.

### Deliberative Agents
Deliberative agents maintain an internal model of the world and plan their actions accordingly. They can handle more complex tasks but require more computational resources.

### Hybrid Agents
Hybrid agents combine reactive and deliberative approaches, balancing responsiveness with planning capability.

## Agent Communication
Agents communicate through messages using standardized protocols. Common communication patterns include:
- Request-response
- Publish-subscribe
- Blackboard systems

## Coordination Strategies
Agents must coordinate their activities to achieve common goals:
- Task allocation
- Resource sharing
- Conflict resolution
- Negotiation protocols

## Applications
Multi-agent systems are used in:
- Autonomous vehicles
- Smart grids
- Supply chain management
- Game AI
- Distributed problem solving

## Specialized Agents
Different agents can specialize in specific tasks:
- Research agents for information gathering
- Analysis agents for data processing
- Explanation agents for transparency
- Grounding agents for fact verification
""",
        "category": "Multi-Agent Systems"
    },
    {
        "filename": "explainable_ai_principles.txt",
        "title": "Principles of Explainable AI",
        "content": """# Explainable AI (XAI) Principles

## Why Explainability Matters
As AI systems become more prevalent in critical decision-making, understanding how they reach conclusions is essential for:
- Building trust
- Ensuring accountability
- Debugging and improving models
- Meeting regulatory requirements
- Detecting bias

## Transparency vs Interpretability
Transparency refers to understanding the internal mechanics of an AI system, while interpretability focuses on understanding the relationship between inputs and outputs in human terms.

## Levels of Explainability

### Global Explainability
Explains the overall behavior of the model across all inputs. Useful for understanding general patterns and biases.

### Local Explainability
Explains specific predictions for individual instances. Critical for understanding why a particular decision was made.

### Counterfactual Explanations
Shows what would need to change in the input for the output to be different. Helps users understand decision boundaries.

## Techniques for Explainability

### Feature Importance
Identifies which input features most influence the model's predictions. Methods include SHAP values and permutation importance.

### Attention Mechanisms
In neural networks, attention weights show which parts of the input the model focuses on when making decisions.

### Rule Extraction
Converts complex models into simpler rule-based representations that humans can understand.

### Example-Based Explanations
Provides similar examples from training data to explain predictions by analogy.

## Confidence Scoring
Providing confidence scores helps users understand how certain the AI is about its predictions. Low confidence scores signal when human review may be needed.

## Source Attribution
In systems like RAG, showing which sources were used to generate a response helps verify accuracy and detect potential errors.

## Reasoning Chains
Displaying step-by-step reasoning helps users follow the AI's logic from inputs to conclusions.

## Trade-offs
More complex models often perform better but are harder to explain. Finding the right balance between performance and explainability depends on the application.

## Best Practices
- Provide multiple levels of explanation (basic, detailed, technical)
- Make explanations actionable
- Tailor explanations to the audience
- Include uncertainty and limitations
- Enable interactive exploration of explanations
""",
        "category": "Explainability"
    },
    {
        "filename": "rag_systems_guide.txt",
        "title": "Retrieval Augmented Generation Systems",
        "content": """# Retrieval Augmented Generation (RAG) Systems

## Overview
RAG systems enhance language models by retrieving relevant information from a knowledge base before generating responses. This grounds responses in factual data and reduces hallucinations.

## RAG Architecture

### Components
1. Document Store: Repository of knowledge (vector database)
2. Retriever: Finds relevant documents for a query
3. Generator: Language model that produces responses
4. Orchestrator: Coordinates the retrieval and generation process

### Workflow
1. User submits a query
2. Query is embedded into vector space
3. Similar documents are retrieved
4. Retrieved documents provide context for the generator
5. Generator produces a grounded response

## Vector Databases
Vector databases store document embeddings for efficient similarity search:
- ChromaDB
- Pinecone
- Weaviate
- Milvus

## Embedding Models
Embeddings convert text into numerical vectors that capture semantic meaning:
- OpenAI embeddings
- Sentence transformers
- Custom embeddings

## Retrieval Strategies

### Semantic Search
Uses vector similarity to find documents with similar meaning, even if exact words don't match.

### Hybrid Search
Combines semantic search with keyword matching for better results.

### Reranking
Applies a second-stage model to improve the ranking of retrieved documents.

## Chunking Strategies
Documents are split into chunks for better retrieval:
- Fixed-size chunking
- Sentence-based chunking
- Paragraph-based chunking
- Semantic chunking

## Context Window Management
Managing the amount of context provided to the generator:
- Too little context: Incomplete information
- Too much context: Information overload, higher cost

## Grounding and Verification
Ensuring generated responses are based on retrieved documents:
- Source citation
- Fact verification
- Confidence scoring
- Hallucination detection

## Challenges
- Relevance: Retrieving truly relevant documents
- Context length: Fitting retrieved information in model context window
- Latency: Balancing speed with thoroughness
- Cost: Managing API and compute costs

## Improvements
- Fine-tuning retrievers for domain-specific tasks
- Using multiple retrieval strategies
- Implementing feedback loops
- Caching frequent queries
""",
        "category": "RAG Systems"
    }
]

async def create_synthetic_documents():
    """Create synthetic documents with embeddings"""
    db = SessionLocal()

    try:
        logger.info("Creating synthetic documents...")

        for doc_data in SYNTHETIC_DOCUMENTS:
            # Check if document already exists
            existing = db.query(Document).filter(Document.filename == doc_data["filename"]).first()
            if existing:
                logger.info(f"Document already exists: {doc_data['filename']}")
                continue

            # Create document
            document = Document(
                filename=doc_data["filename"],
                file_path=f"synthetic/{doc_data['filename']}",
                file_type="txt",
                file_size=len(doc_data["content"]),
                title=doc_data["title"],
                category=doc_data["category"],
                uploaded_by_id=1,  # Admin user
                processing_status="processing"
            )
            db.add(document)
            db.flush()

            # Chunk text
            chunks = TextChunker.chunk_text(doc_data["content"])

            # Prepare for both providers
            for provider in ["custom", "ollama"]:
                try:
                    logger.info(f"Processing {doc_data['filename']} for provider: {provider}")

                    chunk_texts = [chunk['content'] for chunk in chunks]
                    chunk_metadatas = [
                        {
                            'document_id': document.uuid,
                            'document_title': document.title,
                            'chunk_index': chunk['chunk_index'],
                            'file_type': 'txt',
                            'category': doc_data['category']
                        }
                        for chunk in chunks
                    ]

                    # Add to vector store
                    chunk_ids = await vector_store_service.add_documents(
                        texts=chunk_texts,
                        metadatas=chunk_metadatas,
                        provider=provider
                    )

                    # Save chunks to database (only once)
                    if provider == "custom":
                        for chunk, chunk_id in zip(chunks, chunk_ids):
                            doc_chunk = DocumentChunk(
                                document_id=document.id,
                                content=chunk['content'],
                                chunk_index=chunk['chunk_index'],
                                num_tokens=chunk['num_tokens'],
                                embedding_id=chunk_id
                            )
                            db.add(doc_chunk)

                    logger.info(f"Added {len(chunk_ids)} chunks to {provider} vector store")

                except Exception as e:
                    logger.warning(f"Failed to process for {provider}: {e}")

            # Update document
            document.is_processed = True
            document.processing_status = "completed"
            document.num_chunks = len(chunks)
            document.num_tokens = sum(chunk['num_tokens'] for chunk in chunks)

            db.commit()
            logger.info(f"Created document: {doc_data['title']}")

        logger.info("✅ Synthetic data generation completed!")

    except Exception as e:
        logger.error(f"Failed to create synthetic documents: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_synthetic_documents())
