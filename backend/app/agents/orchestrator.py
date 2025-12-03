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
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute RAG pipeline with multi-agent support

        Args:
            query: User query
            provider: LLM provider
            explainability_level: Level of explanation
            include_grounding: Whether to verify grounding
            user_id: User ID for multi-tenant document search

        Returns:
            Complete response with agent logs
        """
        start_time = datetime.utcnow()
        agent_logs = []

        try:
            logger.info(f"[Orchestrator] Starting RAG with agents for query: {query[:50]}...")

            # Step 1: Research Agent - Retrieve documents
            research_agent = get_agent('research')
            research_result = await research_agent.execute(
                input_data={'query': query},
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
        user_id: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute RAG pipeline with multi-agent support, yielding status events via SSE

        Args:
            query: User query
            provider: LLM provider
            explainability_level: Level of explanation
            include_grounding: Whether to verify grounding
            user_id: User ID for multi-tenant document search

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
            research_result = await research_agent.execute(
                input_data={'query': query},
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

# Global orchestrator instance
orchestrator = AgentOrchestrator()
