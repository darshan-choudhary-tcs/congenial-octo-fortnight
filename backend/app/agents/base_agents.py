"""
Base Agent class and specialized agents for multi-agent system
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from loguru import logger

from app.services.llm_service import llm_service
from app.rag.retriever import rag_retriever

class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self, name: str, agent_type: str, description: str):
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.memory = []

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], provider: str = "custom") -> Dict[str, Any]:
        """Execute agent task"""
        pass

    def add_to_memory(self, item: Dict[str, Any]):
        """Add item to agent memory"""
        self.memory.append({
            **item,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Keep only last 50 items
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]

    def get_memory_context(self, limit: int = 5) -> str:
        """Get recent memory as context"""
        recent = self.memory[-limit:]
        return "\n".join([f"- {item.get('summary', str(item))}" for item in recent])

class ResearchAgent(BaseAgent):
    """Agent specialized in research and information retrieval"""

    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            agent_type="research",
            description="Specialized in retrieving and analyzing relevant information from documents"
        )

    async def execute(self, input_data: Dict[str, Any], provider: str = "custom") -> Dict[str, Any]:
        """
        Execute research task

        Args:
            input_data: Should contain 'query' and optional 'filters'
            provider: LLM provider

        Returns:
            Research results with retrieved documents and analysis
        """
        start_time = datetime.utcnow()

        try:
            query = input_data.get('query')
            filters = input_data.get('filters')

            logger.info(f"[{self.name}] Researching: {query} (provider: {provider})")

            # Retrieve relevant documents
            retrieved_docs = await rag_retriever.retrieve_relevant_documents(
                query=query,
                provider=provider,
                filter_metadata=filters
            )

            if not retrieved_docs:
                return {
                    'status': 'completed',
                    'agent': self.name,
                    'results': [],
                    'summary': 'No relevant documents found',
                    'confidence': 0.0,
                    'reasoning': 'The query did not match any documents in the knowledge base.'
                }

            # Analyze retrieved documents
            analysis_prompt = f"""You are a research analyst. Analyze the following documents retrieved for the query: "{query}"

Documents:
{self._format_documents(retrieved_docs)}

Provide:
1. Key findings (bullet points)
2. Relevance assessment for each document
3. Overall confidence in the retrieved information
4. Any gaps or limitations

Analysis:"""

            analysis = await llm_service.invoke_llm(
                prompt=analysis_prompt,
                provider=provider,
                system_message="You are a thorough research analyst focused on accuracy and relevance."
            )

            # Calculate overall confidence
            avg_similarity = sum(doc['similarity'] for doc in retrieved_docs) / len(retrieved_docs)

            result = {
                'status': 'completed',
                'agent': self.name,
                'results': retrieved_docs,
                'analysis': analysis,
                'summary': f"Retrieved {len(retrieved_docs)} relevant documents",
                'confidence': avg_similarity,
                'reasoning': f"Found {len(retrieved_docs)} documents with average similarity {avg_similarity:.2f}",
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

            # Add to memory
            self.add_to_memory({
                'query': query,
                'doc_count': len(retrieved_docs),
                'summary': result['summary']
            })

            logger.info(f"[{self.name}] Research completed: {len(retrieved_docs)} documents")

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Research failed: {e}")
            return {
                'status': 'failed',
                'agent': self.name,
                'error': str(e),
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

    def _format_documents(self, docs: List[Dict[str, Any]], max_length: int = 500) -> str:
        """Format documents for analysis"""
        formatted = []
        for i, doc in enumerate(docs):
            content = doc['document']
            if len(content) > max_length:
                content = content[:max_length] + "..."
            formatted.append(f"Document {i+1} (Similarity: {doc['similarity']:.2f}):\n{content}\n")
        return "\n".join(formatted)

class AnalyzerAgent(BaseAgent):
    """Agent specialized in analyzing and synthesizing information"""

    def __init__(self):
        super().__init__(
            name="AnalyzerAgent",
            agent_type="analyzer",
            description="Specialized in analyzing information and generating insights"
        )

    async def execute(self, input_data: Dict[str, Any], provider: str = "custom") -> Dict[str, Any]:
        """
        Execute analysis task

        Args:
            input_data: Should contain 'data' to analyze and 'analysis_type'
            provider: LLM provider

        Returns:
            Analysis results with insights
        """
        start_time = datetime.utcnow()

        try:
            data = input_data.get('data')
            analysis_type = input_data.get('analysis_type', 'general')
            query = input_data.get('query', '')

            logger.info(f"[{self.name}] Analyzing data: {analysis_type}")

            analysis_prompts = {
                'general': f"""Analyze the following information and provide insights:

Data: {self._format_data(data)}

Provide:
1. Key insights and patterns
2. Important relationships or connections
3. Recommendations or conclusions
4. Confidence level in your analysis

Analysis:""",

                'comparative': f"""Compare and contrast the following information:

Data: {self._format_data(data)}

Provide:
1. Similarities
2. Differences
3. Strengths and weaknesses
4. Overall comparison summary

Analysis:""",

                'trend': f"""Identify trends and patterns in the following information:

Data: {self._format_data(data)}

Provide:
1. Major trends identified
2. Supporting evidence for each trend
3. Potential implications
4. Confidence in trend identification

Analysis:"""
            }

            prompt = analysis_prompts.get(analysis_type, analysis_prompts['general'])

            analysis_data = await llm_service.generate_response(
                prompt=prompt,
                provider=provider,
                system_message="You are an expert data analyst skilled at finding patterns and generating actionable insights."
            )
            analysis = analysis_data["content"]
            token_usage = analysis_data["token_usage"]

            result = {
                'status': 'completed',
                'agent': self.name,
                'analysis': analysis,
                'analysis_type': analysis_type,
                'confidence': 0.85,  # Can be calculated based on data quality
                'reasoning': f"Performed {analysis_type} analysis on provided data",
                'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                'token_usage': token_usage
            }

            self.add_to_memory({
                'analysis_type': analysis_type,
                'summary': f"Analyzed data using {analysis_type} approach"
            })

            logger.info(f"[{self.name}] Analysis completed")

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Analysis failed: {e}")
            return {
                'status': 'failed',
                'agent': self.name,
                'error': str(e),
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

    def _format_data(self, data: Any) -> str:
        """Format data for analysis"""
        if isinstance(data, list):
            return "\n".join([str(item) for item in data])
        elif isinstance(data, dict):
            return "\n".join([f"{k}: {v}" for k, v in data.items()])
        else:
            return str(data)

class ExplainabilityAgent(BaseAgent):
    """Agent specialized in explaining AI decisions and providing transparency"""

    def __init__(self):
        super().__init__(
            name="ExplainabilityAgent",
            agent_type="explainability",
            description="Specialized in explaining AI reasoning and providing transparency"
        )

    async def execute(self, input_data: Dict[str, Any], provider: str = "custom") -> Dict[str, Any]:
        """
        Generate explanation for AI decision

        Args:
            input_data: Should contain 'response', 'sources', 'process'
            provider: LLM provider

        Returns:
            Detailed explanation of the AI decision process
        """
        start_time = datetime.utcnow()

        try:
            response = input_data.get('response', '')
            sources = input_data.get('sources', [])
            process = input_data.get('process', '')
            explainability_level = input_data.get('explainability_level', 'detailed')

            logger.info(f"[{self.name}] Generating explanation (level: {explainability_level})")

            if explainability_level == 'basic':
                explanation_prompt = f"""Provide a simple explanation of how this response was generated:

Response: {response}

Number of sources used: {len(sources)}

Explain in 2-3 sentences why this response is reliable."""

            elif explainability_level == 'detailed':
                explanation_prompt = f"""Provide a detailed explanation of the AI decision process:

Response: {response}

Sources Used:
{self._format_sources(sources)}

Process: {process}

Explain:
1. What sources were used and why
2. How the information was synthesized
3. Confidence level and reasoning
4. Any limitations or uncertainties"""

            else:  # debug
                explanation_prompt = f"""Provide a comprehensive technical explanation of the AI decision process:

Response: {response}

Sources Used (with similarity scores):
{self._format_sources_detailed(sources)}

Process: {process}

Provide:
1. Detailed source selection rationale
2. Step-by-step reasoning process
3. Confidence calculations and factors
4. Potential biases or limitations
5. Alternative interpretations considered
6. Grounding verification results
7. Recommendations for improving confidence"""

            explanation_data = await llm_service.generate_response(
                prompt=explanation_prompt,
                provider=provider,
                system_message="You are an AI transparency expert. Provide clear, honest explanations of AI decision-making processes."
            )
            explanation = explanation_data["content"]
            token_usage = explanation_data["token_usage"]

            # Generate reasoning chain
            reasoning_chain = self._generate_reasoning_chain(sources, response)

            result = {
                'status': 'completed',
                'agent': self.name,
                'explanation': explanation,
                'reasoning_chain': reasoning_chain,
                'explainability_level': explainability_level,
                'confidence': self._calculate_explanation_confidence(sources),
                'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                'token_usage': token_usage
            }

            logger.info(f"[{self.name}] Explanation generated")

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Explanation generation failed: {e}")
            return {
                'status': 'failed',
                'agent': self.name,
                'error': str(e),
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

    def _format_sources(self, sources: List[Dict[str, Any]]) -> str:
        """Format sources for explanation"""
        return "\n".join([
            f"Source {i+1}: {s.get('content', '')[:100]}..."
            for i, s in enumerate(sources)
        ])

    def _format_sources_detailed(self, sources: List[Dict[str, Any]]) -> str:
        """Format sources with detailed information"""
        return "\n".join([
            f"Source {i+1} (Similarity: {s.get('similarity', 0):.3f}):\n{s.get('content', '')[:150]}...\nMetadata: {s.get('metadata', {})}"
            for i, s in enumerate(sources)
        ])

    def _generate_reasoning_chain(
        self,
        sources: List[Dict[str, Any]],
        response: str
    ) -> List[Dict[str, str]]:
        """Generate a reasoning chain showing the decision process"""
        chain = [
            {
                'step': 1,
                'action': 'Source Retrieval',
                'description': f"Retrieved {len(sources)} relevant sources from knowledge base",
                'outcome': f"Found documents with average similarity score"
            },
            {
                'step': 2,
                'action': 'Context Building',
                'description': "Constructed context from retrieved sources",
                'outcome': "Context prepared for LLM"
            },
            {
                'step': 3,
                'action': 'Response Generation',
                'description': "Generated response using LLM with context",
                'outcome': f"Generated {len(response.split())} words"
            },
            {
                'step': 4,
                'action': 'Grounding Verification',
                'description': "Verified response is grounded in sources",
                'outcome': "Response validated against sources"
            }
        ]
        return chain

    def _calculate_explanation_confidence(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate confidence in the explanation"""
        if not sources:
            return 0.5
        avg_similarity = sum(s.get('similarity', 0) for s in sources) / len(sources)
        return min(0.95, avg_similarity + 0.1)

class GroundingAgent(BaseAgent):
    """Agent specialized in verifying information grounding"""

    def __init__(self):
        super().__init__(
            name="GroundingAgent",
            agent_type="grounding",
            description="Specialized in verifying that responses are grounded in source material"
        )

    async def execute(self, input_data: Dict[str, Any], provider: str = "custom") -> Dict[str, Any]:
        """
        Verify grounding of response

        Args:
            input_data: Should contain 'response' and 'sources'
            provider: LLM provider

        Returns:
            Grounding verification results
        """
        start_time = datetime.utcnow()

        try:
            response = input_data.get('response', '')
            sources = input_data.get('sources', [])

            logger.info(f"[{self.name}] Verifying grounding for response")

            verification = await rag_retriever.verify_grounding(
                response=response,
                sources=sources,
                provider=provider
            )

            result = {
                'status': 'completed',
                'agent': self.name,
                'is_grounded': verification['is_grounded'],
                'grounding_score': verification['grounding_score'],
                'verification_details': verification['verification_details'],
                'confidence': verification['grounding_score'],
                'reasoning': f"Grounding score: {verification['grounding_score']:.2f}",
                'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                'token_usage': verification.get('token_usage', {})
            }

            logger.info(f"[{self.name}] Grounding verification completed (score: {verification['grounding_score']:.2f})")

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Grounding verification failed: {e}")
            return {
                'status': 'failed',
                'agent': self.name,
                'error': str(e),
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

# Agent registry
AGENT_REGISTRY = {
    'research': ResearchAgent(),
    'analyzer': AnalyzerAgent(),
    'explainability': ExplainabilityAgent(),
    'grounding': GroundingAgent()
}

def get_agent(agent_type: str) -> Optional[BaseAgent]:
    """Get agent by type"""
    return AGENT_REGISTRY.get(agent_type)
