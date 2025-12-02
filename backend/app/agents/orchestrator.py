"""
Multi-Agent Orchestrator for coordinating agents
"""
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime

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
        include_grounding: bool = True
    ) -> Dict[str, Any]:
        """
        Execute RAG pipeline with multi-agent support

        Args:
            query: User query
            provider: LLM provider
            explainability_level: Level of explanation
            include_grounding: Whether to verify grounding

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
                provider=provider
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

            # Compile final result
            final_result = {
                'response': response,
                'sources': sources,
                'confidence_score': confidence,
                'grounding': grounding_result if grounding_result else None,
                'explanation': explainability_result.get('explanation'),
                'reasoning_chain': explainability_result.get('reasoning_chain', []),
                'agent_logs': agent_logs,
                'agents_involved': ['ResearchAgent', 'GroundingAgent', 'ExplainabilityAgent'] if include_grounding else ['ResearchAgent', 'ExplainabilityAgent'],
                'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                'provider': provider,
                'explainability_level': explainability_level
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
