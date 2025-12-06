"""
Base Agent class and specialized agents for multi-agent system
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from loguru import logger

from app.services.llm_service import llm_service
from app.rag.retriever import rag_retriever
from app.prompts import get_prompt_library

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

    async def execute(self, input_data: Dict[str, Any], provider: str = "custom", user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute research task

        Args:
            input_data: Should contain 'query' and optional 'filters', 'use_metadata_boost'
            provider: LLM provider
            user_id: User ID for multi-tenant search

        Returns:
            Research results with retrieved documents and analysis
        """
        start_time = datetime.utcnow()

        try:
            query = input_data.get('query')
            filters = input_data.get('filters')
            use_metadata_boost = input_data.get('use_metadata_boost', True)  # Default to True

            logger.info(f"[{self.name}] Researching: {query} (provider: {provider}, metadata_boost: {use_metadata_boost})")

            # Retrieve relevant documents with optional metadata enhancement
            if use_metadata_boost:
                retrieval_result = await rag_retriever.retrieve_with_metadata_filter(
                    query=query,
                    provider=provider,
                    use_metadata_boost=True,
                    user_id=user_id
                )
                retrieved_docs = retrieval_result['documents']
                query_metadata = retrieval_result.get('query_metadata', {})
                metadata_boost_used = retrieval_result.get('metadata_boost_used', False)

                if metadata_boost_used:
                    logger.info(
                        f"[{self.name}] Metadata boost applied - "
                        f"Keywords: {query_metadata.get('keywords', [])}, "
                        f"Topics: {query_metadata.get('topics', [])}"
                    )
            else:
                # Standard retrieval without metadata boost
                retrieved_docs = await rag_retriever.retrieve_relevant_documents(
                    query=query,
                    provider=provider,
                    filter_metadata=filters,
                    user_id=user_id
                )
                query_metadata = {}
                metadata_boost_used = False

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
            prompt_lib = get_prompt_library()
            analysis_prompt = prompt_lib.get_prompt(
                "research_analysis",
                query=query,
                documents=self._format_documents(retrieved_docs)
            )
            system_message = prompt_lib.get_system_prompt("research_analyst")

            analysis = await llm_service.invoke_llm(
                prompt=analysis_prompt,
                provider=provider,
                system_message=system_message
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

            # Get prompts from library
            prompt_lib = get_prompt_library()
            prompt_map = {
                'general': 'general_analysis',
                'comparative': 'comparative_analysis',
                'trend': 'trend_analysis'
            }

            prompt_name = prompt_map.get(analysis_type, 'general_analysis')
            prompt = prompt_lib.get_prompt(prompt_name, data=self._format_data(data))
            system_message = prompt_lib.get_system_prompt("data_analyst")

            analysis_data = await llm_service.generate_response(
                prompt=prompt,
                provider=provider,
                system_message=system_message
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

            # Get prompts from library
            prompt_lib = get_prompt_library()

            if explainability_level == 'basic':
                explanation_prompt = prompt_lib.get_prompt(
                    "explanation_basic",
                    response=response,
                    source_count=len(sources)
                )
            elif explainability_level == 'detailed':
                explanation_prompt = prompt_lib.get_prompt(
                    "explanation_detailed",
                    response=response,
                    sources=self._format_sources(sources),
                    process=process
                )
            else:  # debug
                explanation_prompt = prompt_lib.get_prompt(
                    "explanation_debug",
                    response=response,
                    sources_detailed=self._format_sources_detailed(sources),
                    process=process
                )

            system_message = prompt_lib.get_system_prompt("transparency_expert")

            explanation_data = await llm_service.generate_response(
                prompt=explanation_prompt,
                provider=provider,
                system_message=system_message
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

class CouncilAgent(BaseAgent):
    """
    Base class for council voting agents
    Council agents evaluate queries/responses and provide votes with confidence and reasoning
    """

    def __init__(self, name: str, agent_type: str, description: str,
                 system_prompt_name: str, temperature: float = 0.7, vote_weight: float = 1.0):
        super().__init__(name, agent_type, description)
        self.system_prompt_name = system_prompt_name
        self.temperature = temperature
        self.vote_weight = vote_weight

    async def execute(self, input_data: Dict[str, Any], provider: str = "custom") -> Dict[str, Any]:
        """
        Execute council voting task

        Args:
            input_data: Should contain 'query' and optional 'context', 'retrieved_docs'
            provider: LLM provider

        Returns:
            Vote result with response, confidence, reasoning, and supporting evidence
        """
        start_time = datetime.utcnow()

        try:
            query = input_data.get('query')
            context = input_data.get('context', '')
            retrieved_docs = input_data.get('retrieved_docs', [])

            logger.info(f"[{self.name}] Evaluating query: {query[:100]}... (provider: {provider})")

            # Get prompts from library
            prompt_lib = get_prompt_library()

            # Build evaluation prompt
            prompt = self._build_evaluation_prompt(query, context, retrieved_docs, prompt_lib)
            system_message = prompt_lib.get_system_prompt(self.system_prompt_name)

            # Generate response with specific temperature
            llm = llm_service.get_llm(provider)

            # Set temperature for this specific call
            original_temp = llm.temperature if hasattr(llm, 'temperature') else 0.7
            if hasattr(llm, 'temperature'):
                llm.temperature = self.temperature

            response_data = await llm_service.generate_response(
                prompt=prompt,
                provider=provider,
                system_message=system_message
            )

            # Restore original temperature
            if hasattr(llm, 'temperature'):
                llm.temperature = original_temp

            response_content = response_data['content']
            token_usage = response_data.get('token_usage', {})

            # Parse structured response
            parsed = self._parse_response(response_content)

            # Calculate confidence score
            confidence = self._calculate_confidence(parsed, retrieved_docs)

            result = {
                'status': 'completed',
                'agent': self.name,
                'vote': {
                    'response': parsed.get('response', response_content),
                    'confidence': confidence,
                    'reasoning': parsed.get('reasoning', 'No explicit reasoning provided'),
                    'supporting_evidence': parsed.get('evidence', []),
                    'vote_weight': self.vote_weight,
                    'temperature': self.temperature
                },
                'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                'token_usage': token_usage
            }

            # Add to memory
            self.add_to_memory({
                'query': query[:100],
                'confidence': confidence,
                'summary': f"Evaluated with confidence {confidence:.2f}"
            })

            logger.info(f"[{self.name}] Vote completed (confidence: {confidence:.2f})")

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Voting failed: {e}")
            return {
                'status': 'failed',
                'agent': self.name,
                'error': str(e),
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

    def _build_evaluation_prompt(self, query: str, context: str, retrieved_docs: List[Dict], prompt_lib) -> str:
        """Build prompt for evaluation using prompt library"""
        # Build context section
        context_section = ""
        if context:
            context_section = f"\nAdditional Context:\n{context}"

        # Build documents section
        documents_section = ""
        if retrieved_docs:
            docs_text = "\n\n".join([
                f"Document {i+1} (Similarity: {doc.get('similarity', 0):.2f}):\n{doc.get('content', '')[:500]}"
                for i, doc in enumerate(retrieved_docs[:3])
            ])
            documents_section = f"\nRetrieved Documents:\n{docs_text}"

        # Get prompt from library
        return prompt_lib.get_prompt(
            "council_evaluation",
            query=query,
            context_section=context_section,
            documents_section=documents_section
        )

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse structured response from LLM"""
        sections = {
            'response': '',
            'reasoning': '',
            'evidence': [],
            'confidence_text': ''
        }

        current_section = None
        lines = response.split('\n')

        for line in lines:
            line_upper = line.strip().upper()
            if line_upper.startswith('RESPONSE:'):
                current_section = 'response'
                continue
            elif line_upper.startswith('REASONING:'):
                current_section = 'reasoning'
                continue
            elif line_upper.startswith('EVIDENCE:'):
                current_section = 'evidence'
                continue
            elif line_upper.startswith('CONFIDENCE:'):
                current_section = 'confidence_text'
                continue

            if current_section and line.strip():
                if current_section == 'evidence':
                    sections['evidence'].append(line.strip())
                else:
                    sections[current_section] += line + '\n'

        # Clean up sections
        sections['response'] = sections['response'].strip() or response
        sections['reasoning'] = sections['reasoning'].strip()

        return sections

    def _calculate_confidence(self, parsed: Dict[str, Any], retrieved_docs: List[Dict]) -> float:
        """Calculate numerical confidence score"""
        confidence_text = parsed.get('confidence_text', '').lower()

        # Base confidence from text
        if 'high' in confidence_text:
            base_confidence = 0.85
        elif 'medium' in confidence_text:
            base_confidence = 0.65
        elif 'low' in confidence_text:
            base_confidence = 0.40
        else:
            base_confidence = 0.50

        # Adjust based on document quality
        if retrieved_docs:
            avg_similarity = sum(doc.get('similarity', 0) for doc in retrieved_docs) / len(retrieved_docs)
            base_confidence = (base_confidence * 0.7) + (avg_similarity * 0.3)

        # Adjust based on reasoning length (more detailed = higher confidence)
        reasoning_length = len(parsed.get('reasoning', ''))
        if reasoning_length > 200:
            base_confidence = min(1.0, base_confidence + 0.05)

        return round(base_confidence, 3)


class AnalyticalVoter(CouncilAgent):
    """
    Council agent focused on analytical, fact-based evaluation
    Uses low temperature for consistent, logical reasoning
    """

    def __init__(self):
        super().__init__(
            name="AnalyticalVoter",
            agent_type="council_analytical",
            description="Analytical agent focused on logical reasoning and factual accuracy",
            system_prompt_name="council_analytical",
            temperature=0.3,  # Low temperature for consistency
            vote_weight=1.0
        )


class CreativeVoter(CouncilAgent):
    """
    Council agent focused on creative, holistic evaluation
    Uses higher temperature for diverse perspectives
    """

    def __init__(self):
        super().__init__(
            name="CreativeVoter",
            agent_type="council_creative",
            description="Creative agent focused on innovative thinking and broader perspectives",
            system_prompt_name="council_creative",
            temperature=0.9,  # Higher temperature for creativity
            vote_weight=1.0
        )


class CriticalVoter(CouncilAgent):
    """
    Council agent focused on critical evaluation and quality assurance
    Identifies weaknesses, biases, and potential issues
    """

    def __init__(self):
        super().__init__(
            name="CriticalVoter",
            agent_type="council_critical",
            description="Critical agent focused on identifying weaknesses and ensuring quality",
            system_prompt_name="council_critical",
            temperature=0.5,  # Medium temperature for balanced criticism
            vote_weight=1.0
        )


class EnergyAvailabilityAgent(BaseAgent):
    """Agent specialized in analyzing renewable energy availability for customer locations"""

    def __init__(self):
        super().__init__(
            name="EnergyAvailabilityAgent",
            agent_type="energy_availability",
            description="Analyzes location-based renewable energy options using historical data and weather patterns"
        )

    async def execute(self, input_data: Dict[str, Any], provider: str = "custom") -> Dict[str, Any]:
        """
        Analyze renewable energy availability for location

        Args:
            input_data: Should contain 'profile' (Profile object), 'user_id', 'weights'
            provider: LLM provider

        Returns:
            Available renewable energy options with capacity estimates
        """
        start_time = datetime.utcnow()

        try:
            profile = input_data.get('profile')
            user_id = input_data.get('user_id')
            weights = input_data.get('weights', {})

            logger.info(f"[{self.name}] Analyzing energy availability for {profile.location}, {profile.industry}")

            # Build metadata filters for ChromaDB search
            filters = {
                'location': profile.location,
                'industry': profile.industry,
                'content_type': 'renewable_energy_data'
            }

            # Retrieve renewable energy data and historical consumption patterns
            query = f"""
            Analyze renewable energy availability for {profile.location} in the {profile.industry} industry.
            Consider historical consumption patterns, weather data, and regional renewable energy potential.
            Focus on solar, wind, hydro, and biomass options with their capacity and reliability.
            """

            retrieval_result = await rag_retriever.retrieve_with_metadata_filter(
                query=query,
                provider=provider,
                use_metadata_boost=True,
                user_id=user_id
            )
            retrieved_docs = retrieval_result.get('documents', [])

            # Generate analysis using LLM with prompt from library
            prompt_lib = get_prompt_library()
            analysis_prompt = prompt_lib.get_prompt(
                "energy_availability_analysis",
                location=profile.location,
                industry=profile.industry,
                budget=profile.budget,
                documents=self._format_documents(retrieved_docs),
                weights=weights
            )
            system_message = prompt_lib.get_system_prompt("energy_availability_analyst")

            analysis_data = await llm_service.invoke_llm(
                prompt=analysis_prompt,
                provider=provider,
                system_message=system_message
            )

            # Parse analysis and extract renewable options
            renewable_options = self._extract_renewable_options(analysis_data)

            # Calculate confidence based on document relevance
            avg_similarity = sum(doc['similarity'] for doc in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0.0
            confidence = min(0.95, avg_similarity * 1.1)  # Boost slightly, cap at 0.95

            result = {
                'status': 'completed',
                'agent': self.name,
                'renewable_options': renewable_options,
                'analysis': analysis_data,
                'sources': retrieved_docs,
                'confidence': confidence,
                'reasoning': f"Analyzed {len(retrieved_docs)} documents about renewable energy in {profile.location}. "
                           f"Identified {len(renewable_options)} viable renewable energy sources.",
                'metadata': {
                    'location': profile.location,
                    'industry': profile.industry,
                    'documents_analyzed': len(retrieved_docs)
                },
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

            self.add_to_memory({
                'location': profile.location,
                'options_found': len(renewable_options),
                'summary': f"Found {len(renewable_options)} renewable options"
            })

            logger.info(f"[{self.name}] Energy availability analysis completed")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] Energy availability analysis failed: {e}")
            return {
                'status': 'failed',
                'agent': self.name,
                'error': str(e),
                'confidence': 0.0,
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

    def _format_documents(self, docs: List[Dict]) -> str:
        """Format documents for prompt"""
        formatted = []
        for i, doc in enumerate(docs, 1):
            formatted.append(f"Document {i} (Similarity: {doc['similarity']:.2f}):\n{doc['document']}")
        return "\n\n".join(formatted)

    def _extract_renewable_options(self, analysis_data: str) -> List[Dict[str, Any]]:
        """Extract structured renewable options from analysis text"""
        # Parse the analysis to extract renewable energy options
        # Use realistic differentiated profiles based on energy type characteristics
        options = []

        # Realistic profiles based on industry standards and physics
        # These vary by energy type due to fundamental differences in generation
        energy_profiles = {
            'solar': {
                'capacity_factor': 0.24,  # ~24% typical for solar (weather/night dependent)
                'reliability': 0.78,  # Good but weather-dependent
                'base_cost_kwh': 0.043,  # Decreasing costs
                'seasonal_variation': 'high'
            },
            'wind': {
                'capacity_factor': 0.38,  # ~38% typical for wind (intermittent)
                'reliability': 0.72,  # Moderate, wind-dependent
                'base_cost_kwh': 0.052,  # Moderate costs
                'seasonal_variation': 'moderate'
            },
            'hydro': {
                'capacity_factor': 0.47,  # ~47% typical for hydro
                'reliability': 0.89,  # Very reliable, water flow predictable
                'base_cost_kwh': 0.041,  # Low operating costs
                'seasonal_variation': 'low'
            }
        }

        energy_types = ['solar', 'wind', 'hydro']
        for energy_type in energy_types:
            if energy_type.lower() in analysis_data.lower():
                profile = energy_profiles.get(energy_type, {})
                options.append({
                    'type': energy_type.capitalize(),
                    'available': True,
                    'capacity_factor': profile.get('capacity_factor', 0.5),
                    'reliability_score': profile.get('reliability', 0.7),
                    'cost_per_kwh': profile.get('base_cost_kwh', 0.05),
                    'seasonal_variation': profile.get('seasonal_variation', 'moderate')
                })

        return options


class PriceOptimizationAgent(BaseAgent):
    """Agent specialized in optimizing energy mix based on pricing and budget constraints"""

    def __init__(self):
        super().__init__(
            name="PriceOptimizationAgent",
            agent_type="price_optimization",
            description="Optimizes renewable energy mix based on cost, reliability, and sustainability factors"
        )

    async def execute(self, input_data: Dict[str, Any], provider: str = "custom") -> Dict[str, Any]:
        """
        Optimize energy portfolio based on pricing

        Args:
            input_data: Should contain 'profile', 'renewable_options', 'weights', 'user_id'
            provider: LLM provider

        Returns:
            Optimized energy mix with cost breakdown
        """
        start_time = datetime.utcnow()

        try:
            profile = input_data.get('profile')
            renewable_options = input_data.get('renewable_options', [])
            weights = input_data.get('weights', {})
            user_id = input_data.get('user_id')

            logger.info(f"[{self.name}] Optimizing energy mix with budget {profile.budget}")

            # Query for pricing data from RAG
            query = f"""
            Provide pricing information for renewable energy sources in {profile.location}.
            Include cost per kWh, installation costs, maintenance costs, and market trends
            for solar, wind, hydro, and biomass energy.
            """

            retrieval_result = await rag_retriever.retrieve_with_metadata_filter(
                query=query,
                provider=provider,
                use_metadata_boost=True,
                user_id=user_id
            )
            pricing_docs = retrieval_result.get('documents', [])

            # Generate optimization analysis
            prompt_lib = get_prompt_library()
            optimization_prompt = prompt_lib.get_prompt(
                "price_optimization_analysis",
                renewable_options=renewable_options,
                budget=profile.budget,
                pricing_data=self._format_documents(pricing_docs),
                weights=weights,
                location=profile.location
            )
            system_message = prompt_lib.get_system_prompt("price_optimization_analyst")

            optimization_data = await llm_service.invoke_llm(
                prompt=optimization_prompt,
                provider=provider,
                system_message=system_message
            )

            # Extract optimized mix
            optimized_mix = self._extract_optimized_mix(optimization_data, renewable_options, profile.budget)

            # Calculate confidence
            confidence = self._calculate_optimization_confidence(pricing_docs, optimized_mix, profile.budget)

            result = {
                'status': 'completed',
                'agent': self.name,
                'optimized_mix': optimized_mix,
                'analysis': optimization_data,
                'sources': pricing_docs,
                'confidence': confidence,
                'reasoning': f"Optimized energy mix considering budget of ₹{profile.budget:,.0f} "
                           f"with {len(renewable_options)} renewable sources. "
                           f"Applied weights: cost ({weights.get('cost', 0.35):.0%}), "
                           f"reliability ({weights.get('reliability', 0.35):.0%}), "
                           f"sustainability ({weights.get('sustainability', 0.30):.0%}).",
                'metadata': {
                    'budget': profile.budget,
                    'total_cost': sum(item.get('annual_cost', 0) for item in optimized_mix),
                    'sources_analyzed': len(pricing_docs)
                },
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

            self.add_to_memory({
                'budget': profile.budget,
                'mix_items': len(optimized_mix),
                'summary': f"Optimized mix with {len(optimized_mix)} sources"
            })

            logger.info(f"[{self.name}] Price optimization completed")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] Price optimization failed: {e}")
            return {
                'status': 'failed',
                'agent': self.name,
                'error': str(e),
                'confidence': 0.0,
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

    def _format_documents(self, docs: List[Dict]) -> str:
        """Format documents for prompt"""
        formatted = []
        for i, doc in enumerate(docs, 1):
            formatted.append(f"Document {i}:\n{doc['document']}")
        return "\n\n".join(formatted)

    def _extract_optimized_mix(self, analysis_data: str, renewable_options: List[Dict], budget: float) -> List[Dict[str, Any]]:
        """Extract optimized energy mix from analysis"""
        # Use intelligent optimization based on reliability, cost, and capacity
        optimized = []

        if not renewable_options:
            return optimized

        # Calculate weighted scores for each option
        # Higher score = better overall value (reliability, cost-effectiveness, capacity)
        scored_options = []
        for option in renewable_options:
            if option.get('available'):
                reliability = option.get('reliability_score', 0.7)
                capacity = option.get('capacity_factor', 0.5)
                cost = option.get('cost_per_kwh', 0.05)

                # Normalize cost (lower is better, so invert)
                cost_score = 1.0 - min(cost / 0.10, 1.0)  # Normalize to 0-1 range

                # Weighted score: reliability (40%), capacity (35%), cost (25%)
                weighted_score = (reliability * 0.40) + (capacity * 0.35) + (cost_score * 0.25)

                scored_options.append({
                    'option': option,
                    'score': weighted_score
                })

        # Calculate percentages based on scores
        total_score = sum(item['score'] for item in scored_options)

        for item in scored_options:
            option = item['option']
            score = item['score']

            # Allocate percentage based on weighted score
            percentage = (score / total_score) * 100 if total_score > 0 else (100 / len(scored_options))

            # Calculate costs
            cost_per_kwh = option.get('cost_per_kwh', 0.05)
            portion_of_budget = budget * (percentage / 100)

            optimized.append({
                'source': option['type'],
                'percentage': round(percentage, 1),
                'annual_cost': round(portion_of_budget, 2),
                'cost_per_kwh': cost_per_kwh,
                'reliability_score': option.get('reliability_score', 0.7),
                'capacity_factor': option.get('capacity_factor', 0.5)
            })

        return optimized

    def _calculate_optimization_confidence(self, pricing_docs: List[Dict], optimized_mix: List[Dict], budget: float) -> float:
        """Calculate confidence in optimization"""
        if not pricing_docs:
            return 0.4

        avg_similarity = sum(doc['similarity'] for doc in pricing_docs) / len(pricing_docs)

        # Check if within budget
        total_cost = sum(item.get('annual_cost', 0) for item in optimized_mix)
        budget_fit = 1.0 if total_cost <= budget else max(0.5, budget / total_cost)

        confidence = (avg_similarity * 0.7 + budget_fit * 0.3)
        return min(0.95, confidence)


class EnergyPortfolioMixAgent(BaseAgent):
    """Decision agent for final energy portfolio mix based on ESG parameters"""

    def __init__(self):
        super().__init__(
            name="EnergyPortfolioMixAgent",
            agent_type="energy_portfolio_mix",
            description="Makes final portfolio decisions based on ESG targets, budget, and technical feasibility"
        )

    async def execute(self, input_data: Dict[str, Any], provider: str = "custom") -> Dict[str, Any]:
        """
        Make final portfolio decision with ESG considerations

        Args:
            input_data: Should contain 'profile', 'availability_results', 'optimization_results', 'weights'
            provider: LLM provider

        Returns:
            Final energy portfolio with ESG scoring and transition roadmap
        """
        start_time = datetime.utcnow()

        try:
            profile = input_data.get('profile')
            availability_results = input_data.get('availability_results', {})
            optimization_results = input_data.get('optimization_results', {})
            weights = input_data.get('weights', {})

            logger.info(f"[{self.name}] Making portfolio decision with ESG targets: "
                       f"KP1={profile.sustainability_target_kp1}, KP2={profile.sustainability_target_kp2}%")

            # Generate portfolio decision analysis
            prompt_lib = get_prompt_library()

            # Extract weights with defaults for template formatting
            esg_weight = weights.get('esg_score', 0.40)
            budget_weight = weights.get('budget_fit', 0.35)
            technical_weight = weights.get('technical_feasibility', 0.25)

            portfolio_prompt = prompt_lib.get_prompt(
                "portfolio_decision_analysis",
                availability_analysis=availability_results.get('analysis', ''),
                optimization_analysis=optimization_results.get('analysis', ''),
                renewable_options=availability_results.get('renewable_options', []),
                optimized_mix=optimization_results.get('optimized_mix', []),
                sustainability_target_kp1=profile.sustainability_target_kp1,
                sustainability_target_kp2=profile.sustainability_target_kp2,
                budget=profile.budget,
                esg_weight=esg_weight,
                budget_weight=budget_weight,
                technical_weight=technical_weight,
                industry=profile.industry,
                location=profile.location
            )
            system_message = prompt_lib.get_system_prompt("portfolio_decision_analyst")

            decision_data = await llm_service.invoke_llm(
                prompt=portfolio_prompt,
                provider=provider,
                system_message=system_message
            )

            # Calculate ESG scores
            esg_scores = self._calculate_esg_scores(
                optimization_results.get('optimized_mix', []),
                profile.sustainability_target_kp1,
                profile.sustainability_target_kp2
            )

            # Generate transition roadmap
            roadmap = self._generate_transition_roadmap(
                optimization_results.get('optimized_mix', []),
                profile.sustainability_target_kp1,
                profile.sustainability_target_kp2
            )

            # Calculate overall confidence with weighted components
            availability_conf = availability_results.get('confidence', 0.5)
            optimization_conf = optimization_results.get('confidence', 0.5)
            esg_fit = self._calculate_esg_fit(esg_scores, profile.sustainability_target_kp2)

            confidence = (
                availability_conf * 0.3 +
                optimization_conf * 0.3 +
                esg_fit * 0.4
            )

            # Final portfolio mix
            final_portfolio = {
                'energy_mix': optimization_results.get('optimized_mix', []),
                'esg_scores': esg_scores,
                'transition_roadmap': roadmap,
                'meets_targets': esg_scores['renewable_percentage'] >= profile.sustainability_target_kp2
            }

            result = {
                'status': 'completed',
                'agent': self.name,
                'portfolio': final_portfolio,
                'analysis': decision_data,
                'confidence': confidence,
                'reasoning': f"Portfolio decision based on weighted criteria: "
                           f"ESG score ({weights.get('esg_score', 0.40):.0%}), "
                           f"budget fit ({weights.get('budget_fit', 0.35):.0%}), "
                           f"technical feasibility ({weights.get('technical_feasibility', 0.25):.0%}). "
                           f"Target: {profile.sustainability_target_kp2}% renewable by {profile.sustainability_target_kp1}. "
                           f"Current renewable: {esg_scores['renewable_percentage']:.1f}%.",
                'metadata': {
                    'sustainability_target_kp1': profile.sustainability_target_kp1,
                    'sustainability_target_kp2': profile.sustainability_target_kp2,
                    'current_renewable_percentage': esg_scores['renewable_percentage'],
                    'meets_targets': final_portfolio['meets_targets']
                },
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

            self.add_to_memory({
                'renewable_percentage': esg_scores['renewable_percentage'],
                'meets_targets': final_portfolio['meets_targets'],
                'summary': f"Portfolio with {esg_scores['renewable_percentage']:.1f}% renewable"
            })

            logger.info(f"[{self.name}] Portfolio decision completed")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] Portfolio decision failed: {e}")
            return {
                'status': 'failed',
                'agent': self.name,
                'error': str(e),
                'confidence': 0.0,
                'execution_time': (datetime.utcnow() - start_time).total_seconds()
            }

    def _calculate_esg_scores(self, optimized_mix: List[Dict], target_year: int, target_percentage: float) -> Dict[str, Any]:
        """Calculate ESG scores for portfolio"""
        total_renewable = sum(item.get('percentage', 0) for item in optimized_mix
                             if item.get('source') in ['Solar', 'Wind', 'Hydro', 'Biomass'])

        current_year = 2025
        years_to_target = max(1, target_year - current_year)

        return {
            'renewable_percentage': total_renewable,
            'non_renewable_percentage': 100 - total_renewable,
            'sustainability_score': min(100, (total_renewable / target_percentage) * 100) if target_percentage > 0 else 0,
            'years_to_zero_non_renewable': years_to_target,
            'on_track': total_renewable >= (target_percentage * (1.0 - years_to_target * 0.1))
        }

    def _generate_transition_roadmap(self, optimized_mix: List[Dict], target_year: int, target_percentage: float) -> List[Dict[str, Any]]:
        """Generate year-by-year transition roadmap"""
        current_year = 2025
        years_to_target = max(1, target_year - current_year)

        current_renewable = sum(item.get('percentage', 0) for item in optimized_mix
                               if item.get('source') in ['Solar', 'Wind', 'Hydro', 'Biomass'])

        increment_per_year = (target_percentage - current_renewable) / years_to_target

        roadmap = []
        for i in range(years_to_target + 1):
            year = current_year + i
            renewable_pct = min(100, current_renewable + (increment_per_year * i))

            roadmap.append({
                'year': year,
                'renewable_percentage': renewable_pct,
                'milestone': f"Achieve {renewable_pct:.1f}% renewable energy"
            })

        return roadmap

    def _calculate_esg_fit(self, esg_scores: Dict, target_percentage: float) -> float:
        """Calculate how well portfolio fits ESG targets"""
        if target_percentage == 0:
            return 0.5

        renewable_pct = esg_scores.get('renewable_percentage', 0)
        fit_ratio = min(1.0, renewable_pct / target_percentage)

        # Bonus for exceeding target
        if renewable_pct > target_percentage:
            return min(0.95, 0.8 + (renewable_pct - target_percentage) / 100)

        return fit_ratio * 0.8


# Agent registry
AGENT_REGISTRY = {
    'research': ResearchAgent(),
    'analyzer': AnalyzerAgent(),
    'explainability': ExplainabilityAgent(),
    'grounding': GroundingAgent(),
    'council_analytical': AnalyticalVoter(),
    'council_creative': CreativeVoter(),
    'council_critical': CriticalVoter(),
    'energy_availability': EnergyAvailabilityAgent(),
    'price_optimization': PriceOptimizationAgent(),
    'energy_portfolio_mix': EnergyPortfolioMixAgent()
}

def get_agent(agent_type: str) -> Optional[BaseAgent]:
    """Get agent by type"""
    return AGENT_REGISTRY.get(agent_type)

def get_council_agents() -> List[CouncilAgent]:
    """Get all council voting agents"""
    return [
        AGENT_REGISTRY['council_analytical'],
        AGENT_REGISTRY['council_creative'],
        AGENT_REGISTRY['council_critical']
    ]
