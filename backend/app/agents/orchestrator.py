"""
Multi-Agent Orchestrator for coordinating agents
"""
from typing import Dict, Any, List, Optional, AsyncGenerator
from loguru import logger
from datetime import datetime
import asyncio

from app.agents.base_agents import get_agent, AGENT_REGISTRY
from app.rag.retriever import rag_retriever

class AgentOrchestrator:
    """Orchestrate multiple agents to solve complex tasks"""

    def __init__(self):
        self.agents = AGENT_REGISTRY
        self.execution_history = []

    async def execute_rag_with_agents(
        self,
        query: str,
        provider: str = "custom",
        explainability_level: str = "detailed",
        include_grounding: bool = True,
        user_id: Optional[int] = None,
        document_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute RAG pipeline with multi-agent support

        Args:
            query: User query
            provider: LLM provider
            explainability_level: Level of explanation
            include_grounding: Whether to verify grounding
            user_id: User ID for multi-tenant document search
            document_filter: Optional filter to scope document search to specific documents

        Returns:
            Complete response with agent logs
        """
        start_time = datetime.utcnow()
        agent_logs = []

        try:
            logger.info(f"[Orchestrator] Starting RAG with agents for query: {query[:50]}...")

            # Step 1: Research Agent - Retrieve documents with metadata boost
            research_agent = get_agent('research')
            research_input = {
                'query': query,
                'use_metadata_boost': True  # Enable intelligent metadata filtering
            }
            # Add document filter if provided (for scoped conversations)
            if document_filter:
                research_input['filter_metadata'] = document_filter

            research_result = await research_agent.execute(
                input_data=research_input,
                provider=provider,
                user_id=user_id
            )
            agent_logs.append({
                'agent': 'ResearchAgent',
                'action': 'document_retrieval',
                'result': research_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            if research_result['status'] != 'completed' or not research_result.get('results'):
                return {
                    'response': "I couldn't find relevant information to answer your question. The knowledge base may not contain documents related to this topic.",
                    'sources': [],
                    'confidence_score': 0.0,
                    'reasoning_chain': [
                        {
                            'step': 1,
                            'action': 'Document Retrieval',
                            'description': 'Searched knowledge base for relevant documents',
                            'outcome': 'No relevant documents found'
                        }
                    ],
                    'agents_involved': ['ResearchAgent'],
                    'agent_logs': agent_logs,
                    'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                    'grounding': None,
                    'explanation': 'No documents were found in the knowledge base that match your query. Please upload relevant documents or try rephrasing your question.',
                    'provider': provider,
                    'explainability_level': explainability_level
                }

            retrieved_docs = research_result['results']

            # Step 2: Generate response with RAG
            rag_result = await rag_retriever.generate_with_context(
                query=query,
                retrieved_docs=retrieved_docs,
                provider=provider,
                include_sources=True,
                explainability_level=explainability_level
            )

            response = rag_result['response']
            sources = rag_result['sources']
            confidence = rag_result['confidence_score']

            # Track token usage from RAG generation
            total_token_usage = {
                'prompt_tokens': rag_result.get('token_usage', {}).get('prompt_tokens', 0),
                'completion_tokens': rag_result.get('token_usage', {}).get('completion_tokens', 0),
                'total_tokens': rag_result.get('token_usage', {}).get('total_tokens', 0),
                'operations': [{
                    'operation': 'rag_generation',
                    'token_usage': rag_result.get('token_usage', {})
                }]
            }

            # Step 3: Grounding Agent - Verify grounding (if enabled)
            grounding_result = None
            if include_grounding:
                grounding_agent = get_agent('grounding')
                grounding_result = await grounding_agent.execute(
                    input_data={
                        'response': response,
                        'sources': sources
                    },
                    provider=provider
                )
                agent_logs.append({
                    'agent': 'GroundingAgent',
                    'action': 'grounding_verification',
                    'result': grounding_result,
                    'timestamp': datetime.utcnow().isoformat()
                })

                # Track grounding token usage
                if grounding_result and grounding_result.get('token_usage'):
                    grounding_tokens = grounding_result['token_usage']
                    total_token_usage['prompt_tokens'] += grounding_tokens.get('prompt_tokens', 0)
                    total_token_usage['completion_tokens'] += grounding_tokens.get('completion_tokens', 0)
                    total_token_usage['total_tokens'] += grounding_tokens.get('total_tokens', 0)
                    total_token_usage['operations'].append({
                        'operation': 'grounding_verification',
                        'token_usage': grounding_tokens
                    })

                # Enhance confidence with grounding score if available
                if grounding_result and grounding_result.get('status') == 'completed':
                    grounding_score = grounding_result.get('grounding_score', 0.0)
                    # Blend grounding score with existing confidence (70% original, 30% grounding)
                    confidence = confidence * 0.7 + grounding_score * 0.3
                    logger.info(f"[Orchestrator] Enhanced confidence with grounding: {confidence:.3f}")

            # Step 4: Explainability Agent - Generate explanation
            explainability_agent = get_agent('explainability')
            explainability_result = await explainability_agent.execute(
                input_data={
                    'response': response,
                    'sources': sources,
                    'process': 'RAG with multi-agent orchestration',
                    'explainability_level': explainability_level
                },
                provider=provider
            )
            agent_logs.append({
                'agent': 'ExplainabilityAgent',
                'action': 'explanation_generation',
                'result': explainability_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            # Track explainability token usage
            if explainability_result and explainability_result.get('token_usage'):
                explain_tokens = explainability_result['token_usage']
                total_token_usage['prompt_tokens'] += explain_tokens.get('prompt_tokens', 0)
                total_token_usage['completion_tokens'] += explain_tokens.get('completion_tokens', 0)
                total_token_usage['total_tokens'] += explain_tokens.get('total_tokens', 0)
                total_token_usage['operations'].append({
                    'operation': 'explanation_generation',
                    'token_usage': explain_tokens
                })

            # Check for very low confidence and add notice
            low_confidence_warning = False
            if confidence < 0.30:
                low_confidence_warning = True
                # Prepend notice to response
                notice = "⚠️ **Notice**: This response is generated by the AI without relevant content from the knowledge base. The confidence score is very low, indicating no closely matching documents were found. Consider uploading relevant documents or rephrasing your query.\n\n---\n\n"
                response = notice + response
                logger.warning(f"[Orchestrator] Very low confidence ({confidence:.3f}) - Added knowledge base notice")

            # Compile final result
            final_result = {
                'response': response,
                'sources': sources,
                'confidence_score': confidence,
                'low_confidence_warning': low_confidence_warning,
                'grounding': grounding_result if grounding_result else None,
                'explanation': explainability_result.get('explanation'),
                'reasoning_chain': explainability_result.get('reasoning_chain', []),
                'agent_logs': agent_logs,
                'agents_involved': ['ResearchAgent', 'GroundingAgent', 'ExplainabilityAgent'] if include_grounding else ['ResearchAgent', 'ExplainabilityAgent'],
                'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                'provider': provider,
                'explainability_level': explainability_level,
                'token_usage': total_token_usage
            }

            self.execution_history.append({
                'query': query,
                'timestamp': datetime.utcnow().isoformat(),
                'agents_used': final_result['agents_involved'],
                'success': True
            })

            logger.info(f"[Orchestrator] RAG completed successfully in {final_result['execution_time']:.2f}s")

            return final_result

        except Exception as e:
            logger.error(f"[Orchestrator] Execution failed: {e}")
            self.execution_history.append({
                'query': query,
                'timestamp': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e)
            })
            raise

    async def analyze_with_agents(
        self,
        query: str,
        data: Any,
        analysis_type: str = "general",
        provider: str = "custom"
    ) -> Dict[str, Any]:
        """
        Perform analysis using multiple agents

        Args:
            query: Analysis question
            data: Data to analyze
            analysis_type: Type of analysis
            provider: LLM provider

        Returns:
            Analysis results with agent logs
        """
        start_time = datetime.utcnow()
        agent_logs = []

        try:
            logger.info(f"[Orchestrator] Starting analysis: {analysis_type}")

            # Analyzer Agent
            analyzer_agent = get_agent('analyzer')
            analysis_result = await analyzer_agent.execute(
                input_data={
                    'query': query,
                    'data': data,
                    'analysis_type': analysis_type
                },
                provider=provider
            )
            agent_logs.append({
                'agent': 'AnalyzerAgent',
                'action': 'data_analysis',
                'result': analysis_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            # Explainability Agent
            explainability_agent = get_agent('explainability')
            explainability_result = await explainability_agent.execute(
                input_data={
                    'response': analysis_result.get('analysis', ''),
                    'sources': [],
                    'process': f'{analysis_type} analysis',
                    'explainability_level': 'detailed'
                },
                provider=provider
            )
            agent_logs.append({
                'agent': 'ExplainabilityAgent',
                'action': 'explanation_generation',
                'result': explainability_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            return {
                'analysis': analysis_result.get('analysis'),
                'explanation': explainability_result.get('explanation'),
                'confidence_score': analysis_result.get('confidence', 0.8),
                'agent_logs': agent_logs,
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

        except Exception as e:
            logger.error(f"[Orchestrator] Analysis failed: {e}")
            raise

    async def execute_rag_with_agents_stream(
        self,
        query: str,
        provider: str = "custom",
        explainability_level: str = "detailed",
        include_grounding: bool = True,
        user_id: Optional[int] = None,
        document_filter: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute RAG pipeline with multi-agent support, yielding status events via SSE

        Args:
            query: User query
            provider: LLM provider
            explainability_level: Level of explanation
            include_grounding: Whether to verify grounding
            user_id: User ID for multi-tenant document search
            document_filter: Optional filter to scope document search to specific documents

        Yields:
            Status events with agent progress
        """
        start_time = datetime.utcnow()
        agent_logs = []

        try:
            logger.info(f"[Orchestrator] Starting streaming RAG with agents for query: {query[:50]}...")

            # Initial status
            yield {
                'type': 'status',
                'data': {
                    'status': 'started',
                    'message': 'Starting RAG pipeline...',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            await asyncio.sleep(0.01)

            # Step 1: Research Agent - Retrieve documents
            yield {
                'type': 'agent_start',
                'data': {
                    'agent': 'ResearchAgent',
                    'action': 'document_retrieval',
                    'status': 'started',
                    'message': 'Searching knowledge base for relevant documents...',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            await asyncio.sleep(0.01)

            research_agent = get_agent('research')
            research_input = {'query': query}
            # Add document filter if provided (for scoped conversations)
            if document_filter:
                research_input['filter_metadata'] = document_filter

            research_result = await research_agent.execute(
                input_data=research_input,
                provider=provider,
                user_id=user_id
            )
            agent_logs.append({
                'agent': 'ResearchAgent',
                'action': 'document_retrieval',
                'result': research_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            yield {
                'type': 'agent_complete',
                'data': {
                    'agent': 'ResearchAgent',
                    'action': 'document_retrieval',
                    'status': 'completed',
                    'message': f"Found {len(research_result.get('results', []))} relevant documents",
                    'result': {
                        'document_count': len(research_result.get('results', [])),
                        'confidence': research_result.get('confidence', 0.0)
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            await asyncio.sleep(0.01)

            # Emit agent log event
            yield {
                'type': 'agent_log',
                'data': agent_logs[-1]
            }
            await asyncio.sleep(0.01)

            if research_result['status'] != 'completed' or not research_result.get('results'):
                no_docs_response = {
                    'response': "I couldn't find relevant information to answer your question. The knowledge base may not contain documents related to this topic.",
                    'sources': [],
                    'confidence_score': 0.0,
                    'reasoning_chain': [
                        {
                            'step': 1,
                            'action': 'Document Retrieval',
                            'description': 'Searched knowledge base for relevant documents',
                            'outcome': 'No relevant documents found'
                        }
                    ],
                    'agents_involved': ['ResearchAgent'],
                    'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                    'grounding': None,
                    'explanation': 'No documents were found in the knowledge base that match your query. Please upload relevant documents or try rephrasing your question.',
                }

                yield {
                    'type': 'complete',
                    'data': no_docs_response
                }
                return

            retrieved_docs = research_result['results']

            # Step 2: Generate response with RAG
            yield {
                'type': 'agent_start',
                'data': {
                    'agent': 'RAGGenerator',
                    'action': 'response_generation',
                    'status': 'started',
                    'message': 'Generating response from retrieved documents...',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            await asyncio.sleep(0.01)

            rag_result = await rag_retriever.generate_with_context(
                query=query,
                retrieved_docs=retrieved_docs,
                provider=provider,
                include_sources=True,
                explainability_level=explainability_level
            )

            response = rag_result['response']
            sources = rag_result['sources']
            confidence = rag_result['confidence_score']

            # Track token usage from RAG generation
            total_token_usage = {
                'prompt_tokens': rag_result.get('token_usage', {}).get('prompt_tokens', 0),
                'completion_tokens': rag_result.get('token_usage', {}).get('completion_tokens', 0),
                'total_tokens': rag_result.get('token_usage', {}).get('total_tokens', 0),
                'operations': [{
                    'operation': 'rag_generation',
                    'token_usage': rag_result.get('token_usage', {})
                }]
            }

            yield {
                'type': 'agent_complete',
                'data': {
                    'agent': 'RAGGenerator',
                    'action': 'response_generation',
                    'status': 'completed',
                    'message': 'Response generated successfully',
                    'result': {
                        'response_length': len(response),
                        'confidence': confidence
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            await asyncio.sleep(0.01)

            # Step 3: Grounding Agent - Verify grounding (if enabled)
            grounding_result = None
            agents_involved = ['ResearchAgent']

            if include_grounding:
                yield {
                    'type': 'agent_start',
                    'data': {
                        'agent': 'GroundingAgent',
                        'action': 'grounding_verification',
                        'status': 'started',
                        'message': 'Verifying response grounding in sources...',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
                await asyncio.sleep(0.01)

                grounding_agent = get_agent('grounding')
                grounding_result = await grounding_agent.execute(
                    input_data={
                        'response': response,
                        'sources': sources
                    },
                    provider=provider
                )
                agent_logs.append({
                    'agent': 'GroundingAgent',
                    'action': 'grounding_verification',
                    'result': grounding_result,
                    'timestamp': datetime.utcnow().isoformat()
                })

                # Track grounding token usage
                if grounding_result and grounding_result.get('token_usage'):
                    grounding_tokens = grounding_result['token_usage']
                    total_token_usage['prompt_tokens'] += grounding_tokens.get('prompt_tokens', 0)
                    total_token_usage['completion_tokens'] += grounding_tokens.get('completion_tokens', 0)
                    total_token_usage['total_tokens'] += grounding_tokens.get('total_tokens', 0)
                    total_token_usage['operations'].append({
                        'operation': 'grounding_verification',
                        'token_usage': grounding_tokens
                    })

                yield {
                    'type': 'agent_complete',
                    'data': {
                        'agent': 'GroundingAgent',
                        'action': 'grounding_verification',
                        'status': 'completed',
                        'message': 'Grounding verification completed',
                        'result': {
                            'is_grounded': grounding_result.get('is_grounded', False),
                            'confidence': grounding_result.get('confidence', 0.0)
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
                await asyncio.sleep(0.01)

                # Emit agent log event
                yield {
                    'type': 'agent_log',
                    'data': agent_logs[-1]
                }
                await asyncio.sleep(0.01)

                agents_involved.append('GroundingAgent')

            # Step 4: Explainability Agent - Generate explanation
            yield {
                'type': 'agent_start',
                'data': {
                    'agent': 'ExplainabilityAgent',
                    'action': 'explanation_generation',
                    'status': 'started',
                    'message': 'Generating explanation and reasoning chain...',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            await asyncio.sleep(0.01)

            explainability_agent = get_agent('explainability')
            explainability_result = await explainability_agent.execute(
                input_data={
                    'response': response,
                    'sources': sources,
                    'process': 'RAG with multi-agent orchestration',
                    'explainability_level': explainability_level
                },
                provider=provider
            )
            agent_logs.append({
                'agent': 'ExplainabilityAgent',
                'action': 'explanation_generation',
                'result': explainability_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            # Track explainability token usage
            if explainability_result and explainability_result.get('token_usage'):
                explain_tokens = explainability_result['token_usage']
                total_token_usage['prompt_tokens'] += explain_tokens.get('prompt_tokens', 0)
                total_token_usage['completion_tokens'] += explain_tokens.get('completion_tokens', 0)
                total_token_usage['total_tokens'] += explain_tokens.get('total_tokens', 0)
                total_token_usage['operations'].append({
                    'operation': 'explanation_generation',
                    'token_usage': explain_tokens
                })

            yield {
                'type': 'agent_complete',
                'data': {
                    'agent': 'ExplainabilityAgent',
                    'action': 'explanation_generation',
                    'status': 'completed',
                    'message': 'Explanation generated successfully',
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            await asyncio.sleep(0.01)

            # Emit agent log event
            yield {
                'type': 'agent_log',
                'data': agent_logs[-1]
            }
            await asyncio.sleep(0.01)

            agents_involved.append('ExplainabilityAgent')

            # Check for very low confidence and add notice
            low_confidence_warning = False
            if confidence < 0.30:
                low_confidence_warning = True
                # Prepend notice to response
                notice = "⚠️ **Notice**: This response is generated by the AI without relevant content from the knowledge base. The confidence score is very low, indicating no closely matching documents were found. Consider uploading relevant documents or rephrasing your query.\n\n---\n\n"
                response = notice + response
                logger.warning(f"[Orchestrator Stream] Very low confidence ({confidence:.3f}) - Added knowledge base notice")

            # Compile final result
            final_result = {
                'response': response,
                'sources': sources,
                'confidence_score': confidence,
                'low_confidence_warning': low_confidence_warning,
                'grounding': grounding_result if grounding_result else None,
                'explanation': explainability_result.get('explanation'),
                'reasoning_chain': explainability_result.get('reasoning_chain', []),
                'agents_involved': agents_involved,
                'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                'provider': provider,
                'explainability_level': explainability_level,
                'token_usage': total_token_usage
            }

            self.execution_history.append({
                'query': query,
                'timestamp': datetime.utcnow().isoformat(),
                'agents_used': final_result['agents_involved'],
                'success': True
            })

            logger.info(f"[Orchestrator] Streaming RAG completed successfully in {final_result['execution_time']:.2f}s")

            # Send final complete event
            yield {
                'type': 'complete',
                'data': final_result
            }

        except Exception as e:
            logger.error(f"[Orchestrator] Streaming execution failed: {e}")
            self.execution_history.append({
                'query': query,
                'timestamp': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e)
            })
            yield {
                'type': 'error',
                'data': {
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            }

    async def execute_council_voting(
        self,
        query: str,
        provider: str = "ollama",
        user_id: Optional[int] = None,
        voting_strategy: str = "weighted_confidence",
        include_synthesis: bool = True,
        debate_rounds: int = 1,
        document_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute council of agents voting using direct LLM calls (no RAG)

        Args:
            query: User query
            provider: LLM provider (ollama, custom, openai, deepseek, llama)
            user_id: User ID for tracking (not used for RAG)
            voting_strategy: Strategy for aggregating votes (weighted_confidence, highest_confidence, majority, synthesis)
            include_synthesis: Whether to synthesize all responses into final answer
            debate_rounds: Number of debate rounds (1 = no debate, >1 = iterative refinement)
            document_filter: Optional filter (not used - council uses direct LLM)

        Returns:
            Council result with aggregated response, individual votes, and consensus metrics
        """
        start_time = datetime.utcnow()
        agent_logs = []

        try:
            from app.agents.base_agents import get_council_agents
            from app.services.llm_service import llm_service

            logger.info(f"[Orchestrator] Starting council voting for query: {query[:50]}... (strategy: {voting_strategy})")

            # Execute council agents in parallel with direct LLM calls (no RAG)
            council_agents = get_council_agents()
            council_input = {
                'query': query,
                'retrieved_docs': [],  # No RAG - direct LLM calls only
                'context': ''  # No document context
            }

            # Execute all council agents concurrently
            logger.info(f"[Orchestrator] Executing {len(council_agents)} council agents in parallel")
            vote_results = await asyncio.gather(*[
                agent.execute(council_input, provider)
                for agent in council_agents
            ], return_exceptions=True)

            # Process vote results and handle any failures
            valid_votes = []
            failed_votes = []

            for i, result in enumerate(vote_results):
                agent_name = council_agents[i].name

                if isinstance(result, Exception):
                    logger.error(f"[Orchestrator] {agent_name} failed: {result}")
                    failed_votes.append({
                        'agent': agent_name,
                        'error': str(result)
                    })
                elif result.get('status') == 'completed':
                    valid_votes.append(result)
                    agent_logs.append({
                        'agent': agent_name,
                        'action': 'council_vote',
                        'result': {
                            'confidence': result['vote']['confidence'],
                            'vote_weight': result['vote']['vote_weight']
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    failed_votes.append({
                        'agent': agent_name,
                        'error': result.get('error', 'Unknown error')
                    })

            if not valid_votes:
                raise ValueError("All council agents failed to provide votes")

            logger.info(f"[Orchestrator] Received {len(valid_votes)} valid votes from council")

            # Aggregate votes based on strategy
            aggregation_result = await self._aggregate_council_votes(
                votes=valid_votes,
                strategy=voting_strategy,
                query=query,
                provider=provider,
                include_synthesis=include_synthesis
            )

            # Optional debate rounds (iterative refinement)
            debate_history = []
            if debate_rounds > 1:
                logger.info(f"[Orchestrator] Starting {debate_rounds - 1} debate rounds")
                for round_num in range(2, debate_rounds + 1):
                    debate_result = await self._execute_debate_round(
                        query=query,
                        previous_votes=valid_votes,
                        aggregated_response=aggregation_result['final_response'],
                        provider=provider,
                        round_number=round_num
                    )
                    debate_history.append(debate_result)
                    valid_votes = debate_result['votes']

                    # Re-aggregate after debate
                    aggregation_result = await self._aggregate_council_votes(
                        votes=valid_votes,
                        strategy=voting_strategy,
                        query=query,
                        provider=provider,
                        include_synthesis=include_synthesis
                    )

            # Calculate consensus metrics
            consensus_metrics = self._calculate_consensus_metrics(valid_votes)

            # Prepare final result
            total_execution_time = (datetime.utcnow() - start_time).total_seconds()

            result = {
                'response': aggregation_result['final_response'],
                'voting_strategy': voting_strategy,
                'votes': [
                    {
                        'agent': vote['agent'],
                        'response': vote['vote']['response'],
                        'confidence': vote['vote']['confidence'],
                        'reasoning': vote['vote']['reasoning'],
                        'vote_weight': vote['vote']['vote_weight'],
                        'temperature': vote['vote']['temperature']
                    }
                    for vote in valid_votes
                ],
                'consensus_metrics': consensus_metrics,
                'aggregated_confidence': aggregation_result['aggregated_confidence'],
                'synthesis_used': aggregation_result.get('synthesis_used', False),
                'sources': [],  # No RAG sources - council uses direct LLM calls
                'failed_votes': failed_votes,
                'debate_rounds': len(debate_history),
                'debate_history': debate_history if debate_history else None,
                'agents_involved': [vote['agent'] for vote in valid_votes],
                'agent_logs': agent_logs,
                'execution_time': total_execution_time,
                'token_usage': self._aggregate_token_usage(valid_votes),
                'provider': provider
            }

            # Add to execution history
            self.execution_history.append({
                'type': 'council_voting',
                'query': query[:100],
                'result': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })

            logger.info(f"[Orchestrator] Council voting completed in {total_execution_time:.2f}s "
                       f"(consensus: {consensus_metrics['consensus_level']:.2f})")

            return result

        except Exception as e:
            logger.error(f"[Orchestrator] Council voting failed: {e}")
            self.execution_history.append({
                'type': 'council_voting',
                'query': query[:100],
                'result': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            raise

    async def _aggregate_council_votes(
        self,
        votes: List[Dict[str, Any]],
        strategy: str,
        query: str,
        provider: str,
        include_synthesis: bool
    ) -> Dict[str, Any]:
        """
        Aggregate votes from council agents based on strategy
        """
        from app.services.llm_service import llm_service

        if strategy == "highest_confidence":
            # Select response with highest confidence
            best_vote = max(votes, key=lambda v: v['vote']['confidence'])
            return {
                'final_response': best_vote['vote']['response'],
                'aggregated_confidence': best_vote['vote']['confidence'],
                'strategy_used': 'highest_confidence',
                'selected_agent': best_vote['agent']
            }

        elif strategy == "weighted_confidence":
            # Weight responses by confidence scores
            total_weight = sum(v['vote']['confidence'] * v['vote']['vote_weight'] for v in votes)
            if total_weight == 0:
                avg_confidence = sum(v['vote']['confidence'] for v in votes) / len(votes)
            else:
                avg_confidence = total_weight / sum(v['vote']['vote_weight'] for v in votes)

            # Select highest confidence response
            best_vote = max(votes, key=lambda v: v['vote']['confidence'])

            if include_synthesis:
                # Synthesize all responses
                synthesis = await self._synthesize_responses(votes, query, provider)
                return {
                    'final_response': synthesis,
                    'aggregated_confidence': avg_confidence,
                    'strategy_used': 'weighted_confidence_synthesis',
                    'synthesis_used': True
                }
            else:
                return {
                    'final_response': best_vote['vote']['response'],
                    'aggregated_confidence': avg_confidence,
                    'strategy_used': 'weighted_confidence',
                    'selected_agent': best_vote['agent']
                }

        elif strategy == "synthesis":
            # Always synthesize responses
            synthesis = await self._synthesize_responses(votes, query, provider)
            avg_confidence = sum(v['vote']['confidence'] for v in votes) / len(votes)

            return {
                'final_response': synthesis,
                'aggregated_confidence': avg_confidence,
                'strategy_used': 'synthesis',
                'synthesis_used': True
            }

        elif strategy == "majority":
            # Select response closest to average confidence
            confidence_levels = [v['vote']['confidence'] for v in votes]
            avg_confidence = sum(confidence_levels) / len(confidence_levels)
            closest_vote = min(votes, key=lambda v: abs(v['vote']['confidence'] - avg_confidence))

            return {
                'final_response': closest_vote['vote']['response'],
                'aggregated_confidence': avg_confidence,
                'strategy_used': 'majority',
                'selected_agent': closest_vote['agent']
            }

        else:
            raise ValueError(f"Unknown voting strategy: {strategy}")

    async def _synthesize_responses(
        self,
        votes: List[Dict[str, Any]],
        query: str,
        provider: str
    ) -> str:
        """Synthesize multiple agent responses into a coherent final answer"""
        from app.services.llm_service import llm_service

        responses_text = "\n\n".join([
            f"Agent: {vote['agent']}\n"
            f"Confidence: {vote['vote']['confidence']:.2f}\n"
            f"Response: {vote['vote']['response']}\n"
            f"Reasoning: {vote['vote']['reasoning']}"
            for vote in votes
        ])

        synthesis_prompt = f"""You are synthesizing responses from multiple expert agents who have evaluated the same query.

Query: {query}

Agent Responses:
{responses_text}

Task: Create a comprehensive, coherent response that:
1. Integrates the best insights from all agents
2. Resolves any contradictions or differences
3. Maintains factual accuracy
4. Provides a clear, well-structured answer
5. Acknowledges areas of uncertainty if agents disagree

Synthesized Response:"""

        result = await llm_service.generate_response(
            prompt=synthesis_prompt,
            provider=provider,
            system_message="You are an expert at synthesizing multiple perspectives into coherent, high-quality responses."
        )

        return result['content']

    async def _execute_debate_round(
        self,
        query: str,
        previous_votes: List[Dict[str, Any]],
        aggregated_response: str,
        provider: str,
        round_number: int
    ) -> Dict[str, Any]:
        """Execute a debate round where agents can refine their responses"""
        from app.agents.base_agents import get_council_agents

        logger.info(f"[Orchestrator] Executing debate round {round_number}")

        # Build debate context
        debate_context = f"""Previous Round Summary:
Aggregated Response: {aggregated_response}

Other Agents' Perspectives:
{self._format_other_perspectives(previous_votes)}

Consider the other agents' viewpoints and refine your response if needed."""

        # Execute council agents again with debate context
        council_agents = get_council_agents()
        council_input = {
            'query': query,
            'context': debate_context,
            'retrieved_docs': []
        }

        refined_votes = await asyncio.gather(*[
            agent.execute(council_input, provider)
            for agent in council_agents
        ], return_exceptions=True)

        valid_votes = [
            vote for vote in refined_votes
            if not isinstance(vote, Exception) and vote.get('status') == 'completed'
        ]

        return {
            'round': round_number,
            'votes': valid_votes,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _format_other_perspectives(self, votes: List[Dict[str, Any]]) -> str:
        """Format other agents' perspectives for debate context"""
        return "\n\n".join([
            f"{vote['agent']}: {vote['vote']['response'][:300]}..."
            for vote in votes
        ])

    def _calculate_consensus_metrics(self, votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consensus metrics from council votes"""
        if not votes:
            return {
                'consensus_level': 0.0,
                'confidence_variance': 0.0,
                'agreement_score': 0.0,
                'avg_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0
            }

        confidences = [v['vote']['confidence'] for v in votes]
        avg_confidence = sum(confidences) / len(confidences)

        # Calculate variance in confidence scores (lower = more consensus)
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)

        # Consensus level: high when confidence is high and variance is low
        consensus_level = avg_confidence * (1 - min(variance, 1.0))

        # Agreement score: inverse of variance (0 to 1)
        agreement_score = max(0.0, 1.0 - variance)

        return {
            'consensus_level': round(consensus_level, 3),
            'confidence_variance': round(variance, 3),
            'agreement_score': round(agreement_score, 3),
            'avg_confidence': round(avg_confidence, 3),
            'min_confidence': round(min(confidences), 3),
            'max_confidence': round(max(confidences), 3)
        }

    def _aggregate_token_usage(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate token usage from multiple agent results"""
        total_usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'operations': []
        }

        for result in results:
            token_usage = result.get('token_usage', {})
            if token_usage:
                total_usage['prompt_tokens'] += token_usage.get('prompt_tokens', 0)
                total_usage['completion_tokens'] += token_usage.get('completion_tokens', 0)
                total_usage['total_tokens'] += token_usage.get('total_tokens', 0)
                total_usage['operations'].append({
                    'agent': result.get('agent', 'unknown'),
                    'tokens': token_usage
                })

        return total_usage

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {
            'total_agents': len(self.agents),
            'agents': [],
            'execution_history_count': len(self.execution_history)
        }

        for agent_type, agent in self.agents.items():
            status['agents'].append({
                'type': agent_type,
                'name': agent.name,
                'description': agent.description,
                'memory_size': len(agent.memory)
            })

        return status

    async def execute_energy_report(
        self,
        profile: Any,
        user_id: int,
        provider: str = "custom",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute multi-agent energy report generation

        Args:
            profile: User profile with industry, location, budget, sustainability targets
            user_id: User ID for document scoping
            provider: LLM provider
            custom_config: Optional config overrides for weights and parameters

        Returns:
            Complete report with results from all three agents
        """
        start_time = datetime.utcnow()
        agent_logs = []

        try:
            logger.info(f"[Orchestrator] Starting energy report generation for user {user_id}")

            # Merge profile report_config with custom overrides
            import json
            default_config = json.loads(profile.report_config) if profile.report_config else {}
            config = {**default_config, **(custom_config or {})}

            # Step 1: Energy Availability Agent
            logger.info("[Orchestrator] Step 1/3: Analyzing energy availability...")
            availability_agent = get_agent('energy_availability')
            availability_input = {
                'profile': profile,
                'user_id': user_id,
                'weights': config.get('energy_weights', {})
            }

            availability_result = await availability_agent.execute(
                input_data=availability_input,
                provider=provider
            )
            agent_logs.append({
                'agent': 'EnergyAvailabilityAgent',
                'step': 1,
                'result': availability_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            if availability_result['status'] != 'completed':
                logger.error(f"[Orchestrator] Energy availability analysis failed: {availability_result.get('error')}")
                return {
                    'status': 'failed',
                    'error': 'Energy availability analysis failed',
                    'agent_logs': agent_logs,
                    'execution_time': (datetime.utcnow() - start_time).total_seconds()
                }

            # Step 2: Price Optimization Agent
            logger.info("[Orchestrator] Step 2/3: Optimizing energy pricing...")
            optimization_agent = get_agent('price_optimization')
            optimization_input = {
                'profile': profile,
                'renewable_options': availability_result.get('renewable_options', []),
                'weights': config.get('price_optimization_weights', {}),
                'user_id': user_id
            }

            optimization_result = await optimization_agent.execute(
                input_data=optimization_input,
                provider=provider
            )
            agent_logs.append({
                'agent': 'PriceOptimizationAgent',
                'step': 2,
                'result': optimization_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            if optimization_result['status'] != 'completed':
                logger.error(f"[Orchestrator] Price optimization failed: {optimization_result.get('error')}")
                return {
                    'status': 'failed',
                    'error': 'Price optimization failed',
                    'agent_logs': agent_logs,
                    'execution_time': (datetime.utcnow() - start_time).total_seconds()
                }

            # Step 3: Energy Portfolio Mix Decision Agent
            logger.info("[Orchestrator] Step 3/3: Making portfolio decision...")
            portfolio_agent = get_agent('energy_portfolio_mix')
            portfolio_input = {
                'profile': profile,
                'availability_results': availability_result,
                'optimization_results': optimization_result,
                'weights': config.get('portfolio_decision_weights', {})
            }

            portfolio_result = await portfolio_agent.execute(
                input_data=portfolio_input,
                provider=provider
            )
            agent_logs.append({
                'agent': 'EnergyPortfolioMixAgent',
                'step': 3,
                'result': portfolio_result,
                'timestamp': datetime.utcnow().isoformat()
            })

            if portfolio_result['status'] != 'completed':
                logger.error(f"[Orchestrator] Portfolio decision failed: {portfolio_result.get('error')}")
                return {
                    'status': 'failed',
                    'error': 'Portfolio decision failed',
                    'agent_logs': agent_logs,
                    'execution_time': (datetime.utcnow() - start_time).total_seconds()
                }

            # Calculate overall confidence (weighted average)
            overall_confidence = (
                availability_result.get('confidence', 0) * 0.3 +
                optimization_result.get('confidence', 0) * 0.3 +
                portfolio_result.get('confidence', 0) * 0.4
            )

            # Build comprehensive reasoning chain
            reasoning_chain = [
                {
                    'step': 1,
                    'agent': 'EnergyAvailabilityAgent',
                    'action': 'Renewable Energy Analysis',
                    'description': f"Analyzed renewable energy options for {profile.location} in {profile.industry} industry",
                    'outcome': availability_result.get('reasoning', ''),
                    'confidence': availability_result.get('confidence', 0)
                },
                {
                    'step': 2,
                    'agent': 'PriceOptimizationAgent',
                    'action': 'Price Optimization',
                    'description': f"Optimized energy mix within budget of ₹{profile.budget:,.0f}",
                    'outcome': optimization_result.get('reasoning', ''),
                    'confidence': optimization_result.get('confidence', 0)
                },
                {
                    'step': 3,
                    'agent': 'EnergyPortfolioMixAgent',
                    'action': 'Portfolio Decision',
                    'description': f"Final portfolio decision considering ESG targets (KP1: {profile.sustainability_target_kp1}, KP2: {profile.sustainability_target_kp2}%)",
                    'outcome': portfolio_result.get('reasoning', ''),
                    'confidence': portfolio_result.get('confidence', 0)
                }
            ]

            # Aggregate token usage
            total_token_usage = self._aggregate_token_usage([
                availability_result,
                optimization_result,
                portfolio_result
            ])

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            report = {
                'status': 'completed',
                'report_sections': {
                    'energy_availability': availability_result,
                    'price_optimization': optimization_result,
                    'portfolio_decision': portfolio_result
                },
                'overall_confidence': overall_confidence,
                'reasoning_chain': reasoning_chain,
                'agent_logs': agent_logs,
                'agents_involved': ['EnergyAvailabilityAgent', 'PriceOptimizationAgent', 'EnergyPortfolioMixAgent'],
                'execution_time': execution_time,
                'token_usage': total_token_usage,
                'provider': provider,
                'config_used': config
            }

            logger.info(f"[Orchestrator] Energy report completed in {execution_time:.2f}s with confidence {overall_confidence:.2f}")

            return report

        except Exception as e:
            logger.error(f"[Orchestrator] Energy report generation failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'agent_logs': agent_logs,
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

    async def execute_energy_report_stream(
        self,
        profile: Any,
        user_id: int,
        provider: str = "custom",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute energy report with streaming progress updates

        Yields progress events for real-time UI updates
        """
        start_time = datetime.utcnow()

        try:
            import json
            default_config = json.loads(profile.report_config) if profile.report_config else {}
            config = {**default_config, **(custom_config or {})}

            yield {
                'type': 'report_start',
                'data': {
                    'message': 'Starting energy report generation',
                    'total_steps': 3
                }
            }

            # Step 1: Energy Availability
            yield {
                'type': 'agent_start',
                'data': {
                    'agent': 'EnergyAvailabilityAgent',
                    'step': 1,
                    'message': f'Analyzing renewable energy options for {profile.location}'
                }
            }

            availability_agent = get_agent('energy_availability')
            availability_result = await availability_agent.execute(
                input_data={
                    'profile': profile,
                    'user_id': user_id,
                    'weights': config.get('energy_weights', {})
                },
                provider=provider
            )

            yield {
                'type': 'agent_complete',
                'data': {
                    'agent': 'EnergyAvailabilityAgent',
                    'step': 1,
                    'result': availability_result
                }
            }

            if availability_result['status'] != 'completed':
                yield {
                    'type': 'error',
                    'data': {'message': 'Energy availability analysis failed', 'error': availability_result.get('error')}
                }
                return

            # Step 2: Price Optimization
            yield {
                'type': 'agent_start',
                'data': {
                    'agent': 'PriceOptimizationAgent',
                    'step': 2,
                    'message': 'Optimizing energy mix based on pricing'
                }
            }

            optimization_agent = get_agent('price_optimization')
            optimization_result = await optimization_agent.execute(
                input_data={
                    'profile': profile,
                    'renewable_options': availability_result.get('renewable_options', []),
                    'weights': config.get('price_optimization_weights', {}),
                    'user_id': user_id
                },
                provider=provider
            )

            yield {
                'type': 'agent_complete',
                'data': {
                    'agent': 'PriceOptimizationAgent',
                    'step': 2,
                    'result': optimization_result
                }
            }

            if optimization_result['status'] != 'completed':
                yield {
                    'type': 'error',
                    'data': {'message': 'Price optimization failed', 'error': optimization_result.get('error')}
                }
                return

            # Step 3: Portfolio Decision
            yield {
                'type': 'agent_start',
                'data': {
                    'agent': 'EnergyPortfolioMixAgent',
                    'step': 3,
                    'message': 'Making final portfolio decision with ESG targets'
                }
            }

            portfolio_agent = get_agent('energy_portfolio_mix')
            portfolio_result = await portfolio_agent.execute(
                input_data={
                    'profile': profile,
                    'availability_results': availability_result,
                    'optimization_results': optimization_result,
                    'weights': config.get('portfolio_decision_weights', {})
                },
                provider=provider
            )

            yield {
                'type': 'agent_complete',
                'data': {
                    'agent': 'EnergyPortfolioMixAgent',
                    'step': 3,
                    'result': portfolio_result
                }
            }

            if portfolio_result['status'] != 'completed':
                yield {
                    'type': 'error',
                    'data': {'message': 'Portfolio decision failed', 'error': portfolio_result.get('error')}
                }
                return

            # Final report
            overall_confidence = (
                availability_result.get('confidence', 0) * 0.3 +
                optimization_result.get('confidence', 0) * 0.3 +
                portfolio_result.get('confidence', 0) * 0.4
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            yield {
                'type': 'report_complete',
                'data': {
                    'status': 'completed',
                    'report_sections': {
                        'energy_availability': availability_result,
                        'price_optimization': optimization_result,
                        'portfolio_decision': portfolio_result
                    },
                    'overall_confidence': overall_confidence,
                    'execution_time': execution_time,
                    'config_used': config
                }
            }

        except Exception as e:
            logger.error(f"[Orchestrator] Energy report streaming failed: {e}")
            yield {
                'type': 'error',
                'data': {'message': str(e)}
            }

# Global orchestrator instance
orchestrator = AgentOrchestrator()
