"""
Vector Store Service using ChromaDB
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from loguru import logger
import uuid
import math

from app.config import settings
from app.services.llm_service import llm_service

class VectorStoreService:
    """Service for managing ChromaDB vector store"""

    def __init__(self):
        self.client = None
        self.collections = {}
        self._initialize_chroma()

    def _initialize_chroma(self):
        """Initialize ChromaDB client"""
        try:
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB initialized at {settings.CHROMA_PERSIST_DIR}")

            # Get or create default collection for each provider
            self._get_or_create_collection("custom")
            self._get_or_create_collection("ollama")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def _get_or_create_collection(self, provider: str):
        """Get or create a collection for a specific provider"""
        collection_name = f"{settings.CHROMA_COLLECTION_NAME}_{provider}"

        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"provider": provider}
            )
            self.collections[provider] = collection
            logger.info(f"Collection '{collection_name}' ready")
            return collection

        except Exception as e:
            logger.error(f"Failed to get/create collection {collection_name}: {e}")
            raise

    def get_collection(self, provider: str = "custom"):
        """Get collection for specific provider"""
        if provider not in self.collections:
            self._get_or_create_collection(provider)
        return self.collections[provider]

    async def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        provider: str = "custom"
    ) -> List[str]:
        """
        Add documents to vector store

        Args:
            texts: List of text chunks
            metadatas: List of metadata dictionaries
            ids: Optional list of IDs
            provider: LLM provider to use for embeddings

        Returns:
            List of document IDs
        """
        try:
            collection = self.get_collection(provider)

            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(len(texts))]

            # Get embeddings
            embeddings = await llm_service.get_embeddings_for_documents(texts, provider)

            # Add to collection
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Added {len(texts)} documents to {provider} collection")
            return ids

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    async def similarity_search(
        self,
        query: str,
        provider: str = "custom",
        n_results: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search

        Args:
            query: Query text
            provider: LLM provider to use
            n_results: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of results with documents, metadatas, distances
        """
        try:
            collection = self.get_collection(provider)

            if n_results is None:
                n_results = settings.MAX_RETRIEVAL_DOCS

            # Get query embedding
            query_embedding = await llm_service.get_embeddings_for_text(query, provider)

            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )

            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                distance = results['distances'][0][i]
                # ChromaDB uses squared euclidean distance
                # For high-dimensional embeddings (768-1536 dim), we need calibrated normalization
                # Typical distance ranges: 0-2 (very similar), 2-10 (relevant), 10-20 (less relevant), >20 (not relevant)
                similarity = self._calculate_calibrated_similarity(distance)

                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': distance,
                    'similarity': similarity
                })

            # Sort by similarity (highest first)
            formatted_results.sort(key=lambda x: x['similarity'], reverse=True)

            # Log all results before filtering
            logger.info(f"Raw search results: {len(formatted_results)} documents")
            for r in formatted_results:
                logger.info(f"  - Doc {r['id'][:8]}... similarity: {r['similarity']:.4f}, distance: {r['distance']:.3f}")

            # For high-dimensional vectors (like 768-dim), distances can be very large
            # Just return top N results instead of using threshold
            # The top results are still the most relevant even if absolute scores are low
            logger.info(f"Returning top {len(formatted_results)} documents (sorted by relevance)")
            return formatted_results

            # # Filter by similarity threshold  - DISABLED for now due to high-dimensional vector issues
            # # If we have very few results (< 3), just return them all to avoid over-filtering
            # if len(formatted_results) <= 3:
            #     logger.info(f"Returning all {len(formatted_results)} documents (small result set)")
            #     return formatted_results

            # filtered_results = [
            #     r for r in formatted_results
            #     if r['similarity'] >= settings.SIMILARITY_THRESHOLD
            # ]

            # logger.info(f"Found {len(filtered_results)} relevant documents after filtering (threshold: {settings.SIMILARITY_THRESHOLD})")
            # return filtered_results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise

    def _calculate_calibrated_similarity(self, distance: float) -> float:
        """
        Calculate calibrated similarity score from squared Euclidean distance.
        Optimized for high-dimensional embeddings (768-1536 dimensions).

        ChromaDB returns SQUARED Euclidean distances, resulting in larger values (200-500+).
        Distance ranges and their typical meanings (based on observed data):
        - 0.0 - 150.0:   Nearly identical / Very high similarity (0.85 - 1.0)
        - 150.0 - 250.0: Highly relevant / High similarity (0.70 - 0.85)
        - 250.0 - 350.0: Moderately relevant / Good similarity (0.55 - 0.70)
        - 350.0 - 450.0: Somewhat relevant / Fair similarity (0.40 - 0.55)
        - > 450.0:       Low relevance / Low similarity (0.0 - 0.40)

        Args:
            distance: Squared Euclidean distance from ChromaDB

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if distance < 0:
            return 1.0  # Handle edge case

        # Piecewise linear mapping calibrated for SQUARED Euclidean distances (actual observed range: 200-500+)
        # ChromaDB appears to return squared distances, not regular Euclidean
        if distance <= 150.0:
            # Very similar: map [0, 150] -> [1.0, 0.85]
            return 1.0 - (distance / 150.0) * 0.15
        elif distance <= 250.0:
            # Highly relevant: map [150, 250] -> [0.85, 0.70]
            return 0.85 - ((distance - 150.0) / 100.0) * 0.15
        elif distance <= 350.0:
            # Moderately relevant: map [250, 350] -> [0.70, 0.55]
            return 0.70 - ((distance - 250.0) / 100.0) * 0.15
        elif distance <= 450.0:
            # Somewhat relevant: map [350, 450] -> [0.55, 0.40]
            return 0.55 - ((distance - 350.0) / 100.0) * 0.15
        else:
            # Low relevance: exponential decay for distances > 450
            # map [450, infinity] -> [0.40, 0.0]
            return max(0.0, 0.40 * math.exp(-(distance - 450.0) / 200.0))

    async def get_document_by_id(
        self,
        doc_id: str,
        provider: str = "custom"
    ) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            collection = self.get_collection(provider)
            result = collection.get(ids=[doc_id])

            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'document': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None

    async def delete_documents(
        self,
        ids: List[str],
        provider: str = "custom"
    ) -> bool:
        """Delete documents by IDs"""
        try:
            collection = self.get_collection(provider)
            collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from {provider} collection")
            return True

        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False

    async def delete_by_metadata(
        self,
        filter_metadata: Dict[str, Any],
        provider: str = "custom"
    ) -> bool:
        """Delete documents by metadata filter"""
        try:
            collection = self.get_collection(provider)
            collection.delete(where=filter_metadata)
            logger.info(f"Deleted documents matching {filter_metadata} from {provider} collection")
            return True

        except Exception as e:
            logger.error(f"Failed to delete documents by metadata: {e}")
            return False

    def get_collection_stats(self, provider: str = "custom") -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection = self.get_collection(provider)
            count = collection.count()

            return {
                "provider": provider,
                "collection_name": collection.name,
                "document_count": count,
                "metadata": collection.metadata
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}

    def reset_collection(self, provider: str = "custom") -> bool:
        """Reset/clear a collection"""
        try:
            collection_name = f"{settings.CHROMA_COLLECTION_NAME}_{provider}"
            self.client.delete_collection(name=collection_name)
            self._get_or_create_collection(provider)
            logger.info(f"Reset collection for {provider}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False

# Global instance
vector_store_service = VectorStoreService()
