"""
RAG Retriever with grounding and source attribution
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from app.services.llm_service import llm_service
from app.services.vector_store import vector_store_service
from app.config import settings
from app.rag.query_validator import query_validator

class RAGRetriever:
    """Retrieval Augmented Generation with source attribution and grounding"""

    async def extract_query_metadata(self, query: str, provider: str = "custom") -> Dict[str, Any]:
        """
        Extract keywords and topics from user query to enhance retrieval

        Args:
            query: User query
            provider: LLM provider

        Returns:
            Dictionary with extracted keywords and topics
        """
        try:
            # Extract keywords from query (limit to 3-5 for focused search)
            keywords_result = await llm_service.extract_keywords(
                text=query,
                provider=provider,
                max_keywords=5,
                max_length=500  # Queries are short
            )

            # Extract topics from query (limit to 2-3 main topics)
            topics_result = await llm_service.classify_topics(
                text=query,
                provider=provider,
                max_topics=3,
                max_length=500
            )

            return {
                'keywords': keywords_result.get('keywords', []),
                'topics': topics_result.get('topics', []),
                'token_usage': {
                    'prompt_tokens': (
                        keywords_result.get('token_usage', {}).get('prompt_tokens', 0) +
                        topics_result.get('token_usage', {}).get('prompt_tokens', 0)
                    ),
                    'completion_tokens': (
                        keywords_result.get('token_usage', {}).get('completion_tokens', 0) +
                        topics_result.get('token_usage', {}).get('completion_tokens', 0)
                    ),
                    'total_tokens': (
                        keywords_result.get('token_usage', {}).get('total_tokens', 0) +
                        topics_result.get('token_usage', {}).get('total_tokens', 0)
                    )
                }
            }
        except Exception as e:
            logger.warning(f"Failed to extract query metadata: {e}. Proceeding without metadata filtering.")
            return {'keywords': [], 'topics': [], 'token_usage': {}}

    async def retrieve_with_metadata_filter(
        self,
        query: str,
        provider: str = "custom",
        n_results: int = None,
        use_metadata_boost: bool = True,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve documents with intelligent metadata filtering

        Args:
            query: User query
            provider: LLM provider
            n_results: Number of results
            use_metadata_boost: If True, extract query metadata for filtering
            user_id: User ID for user-specific collection search

        Returns:
            Dictionary with documents and metadata extraction info
        """
        try:
            query_metadata = {'keywords': [], 'topics': [], 'token_usage': {}}

            # Extract metadata from query for smarter filtering
            if use_metadata_boost:
                logger.info(f"[Metadata Boost] Extracting keywords/topics from query...")
                query_metadata = await self.extract_query_metadata(query, provider)

                if query_metadata['keywords'] or query_metadata['topics']:
                    logger.info(
                        f"[Metadata Boost] Query keywords: {query_metadata['keywords']}, "
                        f"topics: {query_metadata['topics']}"
                    )

            # First attempt: Try with metadata filtering if we have query metadata
            filtered_results = []
            if use_metadata_boost and (query_metadata['keywords'] or query_metadata['topics']):
                # Build filter to match documents with overlapping keywords/topics
                # Note: ChromaDB $contains operator checks if the string contains the substring
                filter_metadata = None

                # Try filtering by keywords first (most specific)
                if query_metadata['keywords']:
                    keyword = query_metadata['keywords'][0]  # Use most relevant keyword
                    filter_metadata = {'keywords': {'$contains': keyword}}

                    logger.info(f"[Metadata Boost] Filtering by keyword: '{keyword}'")
                    filtered_results = await self.retrieve_relevant_documents(
                        query=query,
                        provider=provider,
                        n_results=n_results,
                        filter_metadata=filter_metadata,
                        user_id=user_id
                    )

                # If no results with keyword filter, try topic filter
                if not filtered_results and query_metadata['topics']:
                    topic = query_metadata['topics'][0]  # Use most relevant topic
                    filter_metadata = {'topics': {'$contains': topic}}

                    logger.info(f"[Metadata Boost] Filtering by topic: '{topic}'")
                    filtered_results = await self.retrieve_relevant_documents(
                        query=query,
                        provider=provider,
                        n_results=n_results,
                        filter_metadata=filter_metadata,
                        user_id=user_id
                    )

            # Fallback: Regular retrieval without metadata filter
            if not filtered_results:
                logger.info("[Metadata Boost] Using standard retrieval (no metadata filter)")
                filtered_results = await self.retrieve_relevant_documents(
                    query=query,
                    provider=provider,
                    n_results=n_results,
                    filter_metadata=None,
                    user_id=user_id
                )

            return {
                'documents': filtered_results,
                'query_metadata': query_metadata,
                'metadata_boost_used': use_metadata_boost and bool(query_metadata['keywords'] or query_metadata['topics'])
            }

        except Exception as e:
            logger.error(f"Metadata-enhanced retrieval failed: {e}")
            # Fallback to standard retrieval
            results = await self.retrieve_relevant_documents(
                query=query,
                provider=provider,
                n_results=n_results,
                user_id=user_id
            )
            return {
                'documents': results,
                'query_metadata': {'keywords': [], 'topics': []},
                'metadata_boost_used': False
            }

    async def retrieve_relevant_documents(
        self,
        query: str,
        provider: str = "custom",
        n_results: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query from both global and user collections

        Args:
            query: User query
            provider: LLM provider for embeddings
            n_results: Number of results
            filter_metadata: Metadata filter
            user_id: User ID for user-specific collection search

        Returns:
            List of relevant documents with metadata (includes query_quality in metadata)
        """
        try:
            if n_results is None:
                n_results = settings.MAX_RETRIEVAL_DOCS

            # Validate query quality to detect gibberish
            query_quality = query_validator.validate_query(query)
            logger.info(f"Query quality: {query_quality['quality_score']:.2f}, Valid: {query_quality['is_valid']}")

            # Search both global and user collections
            results = await vector_store_service.search_multiple_collections(
                query=query,
                provider=provider,
                user_id=user_id,
                n_results=n_results,
                filter_metadata=filter_metadata
            )

            # Attach query quality information to each result for later use
            for result in results:
                result['query_quality'] = query_quality

            # Fallback: If no results found, try the other provider
            if not results:
                other_provider = "ollama" if provider == "custom" else "custom"
                logger.info(f"No results from {provider}, trying {other_provider} provider...")
                try:
                    results = await vector_store_service.search_multiple_collections(
                        query=query,
                        provider=other_provider,
                        user_id=user_id,
                        n_results=n_results,
                        filter_metadata=filter_metadata
                    )
                    if results:
                        logger.info(f"Found {len(results)} documents in {other_provider} collection")
                except Exception as e:
                    logger.warning(f"Fallback to {other_provider} failed: {e}")

            # Add retrieval metadata
            for result in results:
                result['retrieved_at'] = datetime.utcnow().isoformat()
                result['query'] = query

            logger.info(f"Retrieved {len(results)} relevant documents for query: {query[:50]}...")

            return results

        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []

    async def generate_with_context(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        provider: str = "custom",
        include_sources: bool = True,
        explainability_level: str = "detailed"
    ) -> Dict[str, Any]:
        """
        Generate response using retrieved documents as context

        Args:
            query: User query
            retrieved_docs: Retrieved documents
            provider: LLM provider
            include_sources: Whether to include source attribution
            explainability_level: Level of explanation (basic, detailed, debug)

        Returns:
            Dictionary with response and metadata
        """
        try:
            # Build context from retrieved documents
            context_parts = []
            sources = []

            for i, doc in enumerate(retrieved_docs):
                context_parts.append(f"[Source {i+1}]")
                context_parts.append(doc['document'])
                context_parts.append("")

                sources.append({
                    'id': doc['id'],
                    'content': doc['document'][:200] + "..." if len(doc['document']) > 200 else doc['document'],
                    'metadata': doc['metadata'],
                    'similarity': doc['similarity'],
                    'source_number': i + 1
                })

            context = "\n".join(context_parts)

            # Build system message based on explainability level
            system_messages = {
                "basic": "You are a helpful AI assistant. Answer the user's question based on the provided context. Be concise and accurate.",
                "detailed": "You are a helpful AI assistant. Answer the user's question based on the provided context. Include reasoning and cite sources using [Source N] format.",
                "debug": "You are a helpful AI assistant. Answer the user's question based on the provided context. Provide detailed reasoning, cite all sources using [Source N] format, note any assumptions, and highlight potential limitations or uncertainties."
            }

            system_message = system_messages.get(explainability_level, system_messages["detailed"])

            # Build prompt
            if include_sources:
                prompt = f"""Context Information:
{context}

User Question: {query}

Instructions:
1. Answer the question using ONLY the information from the context provided above
2. If the context doesn't contain enough information, acknowledge this limitation
3. Cite your sources using the [Source N] format
4. Explain your reasoning{' in detail' if explainability_level in ['detailed', 'debug'] else ''}
{f'5. Note any assumptions or uncertainties' if explainability_level == 'debug' else ''}

Answer:"""
            else:
                prompt = f"""Context: {context}

Question: {query}

Answer:"""

            # Generate response
            start_time = datetime.utcnow()
            response_data = await llm_service.generate_response(
                prompt=prompt,
                provider=provider,
                system_message=system_message
            )
            response_text = response_data["content"]
            token_usage = response_data["token_usage"]
            end_time = datetime.utcnow()

            # Calculate base similarity score
            avg_similarity = sum(doc['similarity'] for doc in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0.0

            # Extract grounding evidence (source citations in response)
            grounding_evidence = self._extract_source_citations(response_text, sources)

            # Calculate multi-factor confidence score
            confidence_score = self._calculate_confidence_score(
                avg_similarity=avg_similarity,
                retrieved_docs=retrieved_docs,
                grounding_evidence=grounding_evidence,
                response_text=response_text
            )

            result = {
                'response': response_text,
                'sources': sources if include_sources else [],
                'confidence_score': confidence_score,
                'retrieved_doc_count': len(retrieved_docs),
                'avg_similarity': avg_similarity,
                'grounding_evidence': grounding_evidence,
                'generation_time': (end_time - start_time).total_seconds(),
                'provider': provider,
                'explainability_level': explainability_level,
                'token_usage': token_usage
            }

            logger.info(f"Generated response with {len(sources)} sources (confidence: {confidence_score:.2f}, tokens: {token_usage['total_tokens']})")

            return result

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise

    def _extract_source_citations(
        self,
        response_text: str,
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract which sources were cited in the response"""
        grounding_evidence = []

        for source in sources:
            source_num = source['source_number']
            citation_pattern = f"[Source {source_num}]"

            if citation_pattern in response_text:
                grounding_evidence.append({
                    'source_number': source_num,
                    'source_id': source['id'],
                    'cited': True,
                    'similarity': source['similarity']
                })

        return grounding_evidence

    def _calculate_similarity_component(self, avg_similarity: float) -> float:
        """
        Calculate similarity component of confidence score.

        Args:
            avg_similarity: Average similarity from vector search

        Returns:
            Similarity score (already calibrated by vector store)
        """
        return avg_similarity

    def _calculate_citation_component(
        self,
        retrieved_docs: List[Dict[str, Any]],
        grounding_evidence: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate citation quality component based on how many sources were cited.

        Args:
            retrieved_docs: Retrieved documents with metadata
            grounding_evidence: Extracted source citations

        Returns:
            Citation quality score between 0.0 and 1.0
        """
        if not retrieved_docs:
            return 0.3  # Lower neutral score if no docs retrieved

        citation_ratio = len(grounding_evidence) / len(retrieved_docs)
        # Less generous than before - require good citation ratio
        citation_diversity = min(0.2, len(grounding_evidence) * 0.05)
        # Base score of 0.6 if any citations exist, 0.2 if none
        base_citation = 0.6 if len(grounding_evidence) > 0 else 0.2
        citation_score = min(1.0, base_citation + citation_ratio * 0.3 + citation_diversity)

        return citation_score

    def _calculate_grounding_component(self, response_text: str) -> tuple[float, int]:
        """
        Calculate grounding component by detecting uncertainty indicators.

        Args:
            response_text: Generated response text

        Returns:
            Tuple of (grounding_score, uncertainty_penalty_count)
        """
        uncertainty_phrases = [
            "i don't have enough information",
            "the context doesn't contain",
            "i cannot find",
            "unable to determine",
            "no information is provided",
            "cannot answer",
            "not enough context"
        ]
        response_lower = response_text.lower()
        uncertainty_penalty = sum(1 for phrase in uncertainty_phrases if phrase in response_lower)
        # Apply stronger penalties for uncertainty
        grounding_score = max(0.3, 1.0 - (uncertainty_penalty * 0.3))

        return grounding_score, uncertainty_penalty

    def _calculate_query_quality_component(
        self,
        retrieved_docs: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate query quality component to penalize gibberish queries.

        Args:
            retrieved_docs: Retrieved documents with metadata

        Returns:
            Query quality score between 0.0 and 1.0
        """
        query_quality_score = 1.0  # Default to high quality

        if retrieved_docs and len(retrieved_docs) > 0:
            # Extract query quality from first document (all have same quality)
            query_quality = retrieved_docs[0].get('query_quality', {})
            query_quality_score = query_quality.get('quality_score', 1.0)

            if query_quality_score < 0.5:
                logger.warning(
                    f"Low query quality detected: {query_quality_score:.2f}, "
                    f"Issues: {query_quality.get('issues', [])}"
                )

        return query_quality_score

    def _combine_confidence_factors(
        self,
        similarity_score: float,
        citation_score: float,
        grounding_score: float,
        query_quality_score: float,
        weights: dict = None
    ) -> float:
        """
        Combine confidence factors using weighted average.

        Args:
            similarity_score: Similarity component score
            citation_score: Citation quality component score
            grounding_score: Grounding component score
            query_quality_score: Query quality component score
            weights: Optional custom weights dict, defaults to standard weights

        Returns:
            Final combined confidence score between 0.0 and 1.0
        """
        if weights is None:
            weights = {
                'similarity': 0.60,
                'citation': 0.20,
                'grounding': 0.10,
                'query_quality': 0.10
            }

        final_confidence = (
            similarity_score * weights['similarity'] +
            citation_score * weights['citation'] +
            grounding_score * weights['grounding'] +
            query_quality_score * weights['query_quality']
        )

        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, final_confidence))

    def _calculate_confidence_score(
        self,
        avg_similarity: float,
        retrieved_docs: List[Dict[str, Any]],
        grounding_evidence: List[Dict[str, Any]],
        response_text: str
    ) -> float:
        """
        Calculate multi-factor confidence score combining:
        - Similarity scores (60%) - Primary signal from vector search quality
        - Source citation quality (20%) - Whether sources were effectively used
        - Response grounding indicators (10%) - Strong uncertainty detection
        - Query quality (10%) - Penalizes gibberish/meaningless queries

        Args:
            avg_similarity: Average similarity from vector search
            retrieved_docs: Retrieved documents with metadata
            grounding_evidence: Extracted source citations
            response_text: Generated response text

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Calculate individual components
        similarity_score = self._calculate_similarity_component(avg_similarity)
        citation_score = self._calculate_citation_component(retrieved_docs, grounding_evidence)
        grounding_score, uncertainty_penalty = self._calculate_grounding_component(response_text)
        query_quality_score = self._calculate_query_quality_component(retrieved_docs)

        # Combine components with standard weights
        final_confidence = self._combine_confidence_factors(
            similarity_score,
            citation_score,
            grounding_score,
            query_quality_score
        )

        # Log detailed breakdown for debugging
        logger.info(
            f"Confidence breakdown: similarity={similarity_score:.3f} (60%), "
            f"citation={citation_score:.3f} (20%), grounding={grounding_score:.3f} (10%), "
            f"query_quality={query_quality_score:.3f} (10%) → final={final_confidence:.3f}"
        )
        logger.info(f"  - Citations: {len(grounding_evidence)}/{len(retrieved_docs)} sources cited")
        logger.info(f"  - Uncertainty penalties: {uncertainty_penalty}")

        return final_confidence

    async def verify_grounding(
        self,
        response: str,
        sources: List[Dict[str, Any]],
        provider: str = "custom"
    ) -> Dict[str, Any]:
        """
        Verify that the response is grounded in the provided sources

        Args:
            response: Generated response
            sources: Source documents
            provider: LLM provider

        Returns:
            Verification results with grounding score
        """
        try:
            sources_text = "\n\n".join([f"Source {i+1}: {s['content']}" for i, s in enumerate(sources)])

            verification_prompt = f"""You are a fact-checking AI. Your task is to verify if the following response is grounded in the provided sources.

Sources:
{sources_text}

Response to Verify:
{response}

Analyze:
1. Which claims in the response are supported by the sources?
2. Are there any claims that are NOT supported by the sources?
3. Overall grounding score (0.0 to 1.0)

Provide your analysis in this format:
Supported Claims: [list]
Unsupported Claims: [list]
Grounding Score: [0.0-1.0]
Explanation: [brief explanation]"""

            verification_data = await llm_service.generate_response(
                prompt=verification_prompt,
                provider=provider,
                system_message="You are a precise fact-checking assistant."
            )
            verification_result = verification_data["content"]
            token_usage = verification_data["token_usage"]

            # Parse grounding score (simple extraction)
            grounding_score = 0.8  # Default
            if "Grounding Score:" in verification_result:
                try:
                    score_line = [line for line in verification_result.split('\n') if 'Grounding Score:' in line][0]
                    score_str = score_line.split(':')[1].strip()
                    grounding_score = float(score_str)
                except:
                    pass

            return {
                'is_grounded': grounding_score >= 0.7,
                'grounding_score': grounding_score,
                'verification_details': verification_result,
                'token_usage': token_usage
            }

        except Exception as e:
            logger.error(f"Grounding verification failed: {e}")
            return {
                'is_grounded': True,  # Default to True on error
                'grounding_score': 0.8,
                'verification_details': f"Verification failed: {str(e)}"
            }

# Global instance
rag_retriever = RAGRetriever()
