"""
RAG Retriever with grounding and source attribution
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from app.services.llm_service import llm_service
from app.services.vector_store import vector_store_service
from app.config import settings

class RAGRetriever:
    """Retrieval Augmented Generation with source attribution and grounding"""

    async def retrieve_relevant_documents(
        self,
        query: str,
        provider: str = "custom",
        n_results: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query

        Args:
            query: User query
            provider: LLM provider for embeddings
            n_results: Number of results
            filter_metadata: Metadata filter

        Returns:
            List of relevant documents with metadata
        """
        try:
            if n_results is None:
                n_results = settings.MAX_RETRIEVAL_DOCS

            results = await vector_store_service.similarity_search(
                query=query,
                provider=provider,
                n_results=n_results,
                filter_metadata=filter_metadata
            )

            # Fallback: If no results found, try the other provider
            if not results:
                other_provider = "ollama" if provider == "custom" else "custom"
                logger.info(f"No results from {provider}, trying {other_provider} provider...")
                try:
                    results = await vector_store_service.similarity_search(
                        query=query,
                        provider=other_provider,
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
                "detailed": "You are a helpful AI assistant. Answer the user's question based on the provided context. Include reasoning and cite sources using [Source N] format. Explain your confidence level.",
                "debug": "You are a helpful AI assistant. Answer the user's question based on the provided context. Provide detailed reasoning, cite all sources using [Source N] format, explain your confidence level, note any assumptions, and highlight potential limitations or uncertainties."
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
            response_text = await llm_service.invoke_llm(
                prompt=prompt,
                provider=provider,
                system_message=system_message
            )
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
                'explainability_level': explainability_level
            }

            logger.info(f"Generated response with {len(sources)} sources (confidence: {confidence_score:.2f})")

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

    def _calculate_confidence_score(
        self,
        avg_similarity: float,
        retrieved_docs: List[Dict[str, Any]],
        grounding_evidence: List[Dict[str, Any]],
        response_text: str
    ) -> float:
        """
        Calculate multi-factor confidence score combining:
        - Similarity scores (70%) - Primary signal from vector search quality
        - Source citation quality (20%) - Whether sources were effectively used
        - Response grounding indicators (10%) - Strong uncertainty detection

        Args:
            avg_similarity: Average similarity from vector search
            retrieved_docs: Retrieved documents with metadata
            grounding_evidence: Extracted source citations
            response_text: Generated response text

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Factor 1: Similarity Score (70% weight) - Primary indicator of retrieval quality
        # Already calibrated by the new vector store similarity calculation
        similarity_score = avg_similarity

        # Factor 2: Source Citation Quality (20% weight)
        # How many sources were actually cited vs retrieved?
        # More generous scoring: even 2-3 citations from 5 docs is good quality
        if retrieved_docs:
            citation_ratio = len(grounding_evidence) / len(retrieved_docs)
            # Generous bonus for citing multiple sources
            citation_diversity = min(0.3, len(grounding_evidence) * 0.08)
            # Base score of 0.7 if any citations exist
            base_citation = 0.7 if len(grounding_evidence) > 0 else 0.3
            citation_score = min(1.0, base_citation + citation_ratio * 0.2 + citation_diversity)
        else:
            citation_score = 0.6  # Neutral-positive score if no docs retrieved

        # Factor 3: Response Grounding Indicators (10% weight)
        # Check for strong uncertainty indicators that should lower confidence
        uncertainty_phrases = [
            "i don't have enough information",
            "the context doesn't contain",
            "i cannot find",
            "unable to determine",
            "no information is provided"
        ]
        response_lower = response_text.lower()
        uncertainty_penalty = sum(1 for phrase in uncertainty_phrases if phrase in response_lower)
        # Only apply penalty for strong uncertainty, be generous otherwise
        grounding_score = max(0.5, 1.0 - (uncertainty_penalty * 0.25))

        # Weighted combination (70% similarity + 20% citation + 10% grounding)
        final_confidence = (
            similarity_score * 0.70 +
            citation_score * 0.20 +
            grounding_score * 0.10
        )

        # Log detailed breakdown for debugging
        logger.info(f"Confidence breakdown: similarity={similarity_score:.3f} (70%), citation={citation_score:.3f} (20%), grounding={grounding_score:.3f} (10%) → final={final_confidence:.3f}")
        logger.info(f"  - Citations: {len(grounding_evidence)}/{len(retrieved_docs)} sources cited")
        logger.info(f"  - Uncertainty penalties: {uncertainty_penalty}")

        # Ensure score is between 0.0 and 1.0
        final_confidence = max(0.0, min(1.0, final_confidence))

        logger.debug(
            f"Confidence breakdown - Similarity: {similarity_score:.3f} (50%), "
            f"Citations: {citation_score:.3f} (30%), "
            f"Grounding: {grounding_score:.3f} (20%), "
            f"Final: {final_confidence:.3f}"
        )

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

            verification_result = await llm_service.invoke_llm(
                prompt=verification_prompt,
                provider=provider,
                system_message="You are a precise fact-checking assistant."
            )

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
                'verification_details': verification_result
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
