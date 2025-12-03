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

    def get_collection_name(self, scope: str, provider: str, user_id: Optional[int] = None) -> str:
        """Generate collection name based on scope and user"""
        if scope == "global":
            return f"{settings.CHROMA_COLLECTION_NAME}_global_{provider}"
        elif scope == "user" and user_id:
            return f"{settings.CHROMA_COLLECTION_NAME}_user_{user_id}_{provider}"
        else:
            # Fallback to old naming for backward compatibility
            return f"{settings.CHROMA_COLLECTION_NAME}_{provider}"

    def _get_or_create_collection(self, provider: str, scope: str = "global", user_id: Optional[int] = None):
        """Get or create a collection for a specific provider and scope"""
        collection_name = self.get_collection_name(scope, provider, user_id)

        try:
            # Build metadata - ChromaDB doesn't accept None values
            metadata = {"provider": provider, "scope": scope}
            if user_id is not None:
                metadata["user_id"] = str(user_id)  # Convert to string for ChromaDB

            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=metadata
            )
            # Cache key includes scope and user_id for proper isolation
            cache_key = f"{provider}_{scope}_{user_id or 'global'}"
            self.collections[cache_key] = collection
            logger.info(f"Collection '{collection_name}' ready (scope: {scope}, user: {user_id or 'global'})")
            return collection

        except Exception as e:
            logger.error(f"Failed to get/create collection {collection_name}: {e}")
            raise

    def get_collection(self, provider: str = "custom", scope: str = "user", user_id: Optional[int] = None):
        """Get collection for specific provider, scope, and user"""
        cache_key = f"{provider}_{scope}_{user_id or 'global'}"
        if cache_key not in self.collections:
            self._get_or_create_collection(provider, scope, user_id)
        return self.collections[cache_key]

    async def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        provider: str = "custom",
        scope: str = "user",
        user_id: Optional[int] = None
    ) -> List[str]:
        """
        Add documents to vector store

        Args:
            texts: List of text chunks
            metadatas: List of metadata dictionaries
            ids: Optional list of IDs
            provider: LLM provider to use for embeddings
            scope: 'global' or 'user'
            user_id: User ID (required for user scope)

        Returns:
            List of document IDs
        """
        try:
            collection = self.get_collection(provider, scope, user_id)

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

            logger.info(f"Added {len(texts)} documents to {provider} collection (scope: {scope}, user: {user_id or 'global'})")
            return ids

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    async def similarity_search(
        self,
        query: str,
        provider: str = "custom",
        n_results: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        scope: str = "user",
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search

        Args:
            query: Query text
            provider: LLM provider to use
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            scope: 'global' or 'user'
            user_id: User ID (required for user scope)

        Returns:
            List of results with documents, metadatas, distances
        """
        try:
            collection = self.get_collection(provider, scope, user_id)

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

    async def search_multiple_collections(
        self,
        query: str,
        provider: str = "custom",
        user_id: Optional[int] = None,
        n_results: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search both global and user collections, merge and rank results

        Args:
            query: Query text
            provider: LLM provider to use
            user_id: User ID for user-specific collection
            n_results: Total number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            Merged and sorted list of results
        """
        try:
            if n_results is None:
                n_results = settings.MAX_RETRIEVAL_DOCS

            # Search global collection
            global_results = []
            try:
                global_results = await self.similarity_search(
                    query=query,
                    provider=provider,
                    n_results=n_results,
                    filter_metadata=filter_metadata,
                    scope="global",
                    user_id=None
                )
                logger.info(f"Found {len(global_results)} results in global collection")
            except Exception as e:
                logger.warning(f"Global collection search failed (may not exist yet): {e}")

            # Search user collection if user_id provided
            user_results = []
            if user_id:
                try:
                    user_results = await self.similarity_search(
                        query=query,
                        provider=provider,
                        n_results=n_results,
                        filter_metadata=filter_metadata,
                        scope="user",
                        user_id=user_id
                    )
                    logger.info(f"Found {len(user_results)} results in user collection")
                except Exception as e:
                    logger.warning(f"User collection search failed (may not exist yet): {e}")

            # Merge results
            all_results = global_results + user_results

            if not all_results:
                return []

            # Sort by similarity (highest first) and take top n_results
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            merged_results = all_results[:n_results]

            logger.info(f"Merged results: {len(merged_results)} total (from {len(global_results)} global + {len(user_results)} user)")

            return merged_results

        except Exception as e:
            logger.error(f"Multi-collection search failed: {e}")
            return []

    async def get_document_by_id(
        self,
        doc_id: str,
        provider: str = "custom",
        scope: str = "user",
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            collection = self.get_collection(provider, scope, user_id)
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
        provider: str = "custom",
        scope: str = "user",
        user_id: Optional[int] = None
    ) -> bool:
        """Delete documents by IDs"""
        try:
            collection = self.get_collection(provider, scope, user_id)
            collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from {provider} collection (scope: {scope}, user: {user_id or 'global'})")
            return True

        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False

    async def delete_by_metadata(
        self,
        filter_metadata: Dict[str, Any],
        provider: str = "custom",
        scope: str = "user",
        user_id: Optional[int] = None
    ) -> bool:
        """Delete documents by metadata filter"""
        try:
            collection = self.get_collection(provider, scope, user_id)
            collection.delete(where=filter_metadata)
            logger.info(f"Deleted documents matching {filter_metadata} from {provider} collection (scope: {scope}, user: {user_id or 'global'})")
            return True

        except Exception as e:
            logger.error(f"Failed to delete documents by metadata: {e}")
            return False

    def get_collection_stats(self, provider: str = "custom", scope: str = "user", user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection = self.get_collection(provider, scope, user_id)
            count = collection.count()

            return {
                "provider": provider,
                "collection_name": collection.name,
                "document_count": count,
                "metadata": collection.metadata,
                "scope": scope,
                "user_id": user_id
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
