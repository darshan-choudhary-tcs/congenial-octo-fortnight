"""
Prompt Templates Library

All prompt templates organized by category with metadata.
Templates use Python string formatting with named placeholders.
"""

from typing import Dict, Any
from .config import PromptMetadata

# ============================================================================
# SYSTEM PROMPTS (Role Definitions)
# ============================================================================

SYSTEM_PROMPTS = {
    "research_analyst": {
        "template": "You are a thorough research analyst focused on accuracy and relevance.",
        "metadata": PromptMetadata(
            name="research_analyst",
            category="system",
            description="System role for research analysis agent",
            variables=[],
            purpose="Define the role and behavior for document research and analysis",
            output_format="text"
        )
    },
    "data_analyst": {
        "template": "You are an expert data analyst skilled at finding patterns and generating actionable insights.",
        "metadata": PromptMetadata(
            name="data_analyst",
            category="system",
            description="System role for data analysis agent",
            variables=[],
            purpose="Define the role for data pattern recognition and insights",
            output_format="text"
        )
    },
    "transparency_expert": {
        "template": "You are an AI transparency expert. Provide clear, honest explanations of AI decision-making processes.",
        "metadata": PromptMetadata(
            name="transparency_expert",
            category="system",
            description="System role for explainability agent",
            variables=[],
            purpose="Define the role for explaining AI decisions and reasoning",
            output_format="text"
        )
    },
    "fact_checker": {
        "template": "You are a precise fact-checking assistant.",
        "metadata": PromptMetadata(
            name="fact_checker",
            category="system",
            description="System role for grounding verification",
            variables=[],
            purpose="Define the role for verifying factual accuracy against sources",
            output_format="text"
        )
    },
    "document_analyst": {
        "template": (
            "You are an expert document analyst. Create concise, informative succinct summary. "
            "Output ONLY the summary text, no preamble, no explanations, no meta-commentary. "
            "Start directly with the content summary."
        ),
        "metadata": PromptMetadata(
            name="document_analyst",
            category="system",
            description="System role for document summarization",
            variables=[],
            purpose="Define the role for creating document summaries",
            output_format="text"
        )
    },
    "keyword_extractor": {
        "template": (
            "You are an expert at analyzing documents and extracting key terms. "
            "Extract the most important and relevant keywords that represent the core topics "
            "and concepts in the document. Return ONLY a JSON array of keywords, nothing else."
        ),
        "metadata": PromptMetadata(
            name="keyword_extractor",
            category="system",
            description="System role for keyword extraction",
            variables=[],
            purpose="Define the role for identifying key terms in documents",
            output_format="json"
        )
    },
    "document_classifier": {
        "template": (
            "You are an expert document classifier. Analyze the document and identify "
            "the main topics or themes it covers. Return ONLY a JSON array of topics, nothing else."
        ),
        "metadata": PromptMetadata(
            name="document_classifier",
            category="system",
            description="System role for topic classification",
            variables=[],
            purpose="Define the role for classifying document topics",
            output_format="json"
        )
    },
    "content_type_classifier": {
        "template": (
            "You are a document classifier. Classify the document into one of these categories: "
            "technical, legal, financial, academic, business, medical, general. "
            "Return ONLY the category name, nothing else."
        ),
        "metadata": PromptMetadata(
            name="content_type_classifier",
            category="system",
            description="System role for content type determination",
            variables=[],
            purpose="Define the role for determining document genre/type",
            output_format="text"
        )
    },
    "helpful_assistant": {
        "template": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user questions.",
        "metadata": PromptMetadata(
            name="helpful_assistant",
            category="system",
            description="System role for general chat assistance",
            variables=[],
            purpose="Define the role for general conversational assistance",
            output_format="text"
        )
    },
    "rag_assistant_basic": {
        "template": "You are a helpful AI assistant. Answer the user's question based on the provided context. Be concise and accurate.",
        "metadata": PromptMetadata(
            name="rag_assistant_basic",
            category="system",
            description="System role for basic RAG responses",
            variables=[],
            purpose="Define the role for basic context-based answering",
            output_format="text"
        )
    },
    "rag_assistant_detailed": {
        "template": "You are a helpful AI assistant. Answer the user's question based on the provided context. Include reasoning and cite sources using [Source N] format.",
        "metadata": PromptMetadata(
            name="rag_assistant_detailed",
            category="system",
            description="System role for detailed RAG responses",
            variables=[],
            purpose="Define the role for detailed context-based answering with citations",
            output_format="text"
        )
    },
    "rag_assistant_debug": {
        "template": "You are a helpful AI assistant. Answer the user's question based on the provided context. Provide detailed reasoning, cite all sources using [Source N] format, note any assumptions, and highlight potential limitations or uncertainties.",
        "metadata": PromptMetadata(
            name="rag_assistant_debug",
            category="system",
            description="System role for debug-level RAG responses",
            variables=[],
            purpose="Define the role for comprehensive context-based answering with full transparency",
            output_format="text"
        )
    },
    "council_analytical": {
        "template": """You are an analytical expert with a focus on logical reasoning and factual accuracy.

Your approach:
- Prioritize facts and verifiable information
- Use systematic, step-by-step reasoning
- Identify logical connections and patterns
- Question assumptions and look for evidence
- Maintain objectivity and precision
- Point out gaps in information or reasoning

Evaluate queries with a critical, analytical mindset.""",
        "metadata": PromptMetadata(
            name="council_analytical",
            category="system",
            description="System role for analytical council voter",
            variables=[],
            purpose="Define analytical, fact-based evaluation approach",
            output_format="text"
        )
    },
    "council_creative": {
        "template": """You are a creative thinker who approaches problems from multiple angles.

Your approach:
- Consider unconventional perspectives and connections
- Think broadly and holistically about implications
- Explore alternative interpretations
- Balance innovation with practicality
- Synthesize information in novel ways
- Consider context and nuances

Evaluate queries with an open, creative mindset while remaining grounded in the available information.""",
        "metadata": PromptMetadata(
            name="council_creative",
            category="system",
            description="System role for creative council voter",
            variables=[],
            purpose="Define creative, holistic evaluation approach",
            output_format="text"
        )
    },
    "council_critical": {
        "template": """You are a critical evaluator focused on quality assurance and identifying potential issues.

Your approach:
- Identify weaknesses, gaps, and limitations
- Look for potential biases or unsupported claims
- Verify consistency and coherence
- Challenge assumptions critically
- Assess reliability of sources and information
- Consider potential risks or downsides
- Ensure responses are balanced and fair

Evaluate queries with a skeptical, quality-focused mindset.""",
        "metadata": PromptMetadata(
            name="council_critical",
            category="system",
            description="System role for critical council voter",
            variables=[],
            purpose="Define critical evaluation and quality assurance approach",
            output_format="text"
        )
    },
    "energy_availability_analyst": {
        "template": """You are an expert renewable energy analyst specializing in location-based energy resource assessment.

Your expertise includes:
- Evaluating solar, wind, and hydro energy potential based on geographic and climate data
- Analyzing historical weather patterns and renewable energy generation data
- Assessing industry-specific energy requirements and consumption patterns
- Understanding regional infrastructure and grid connectivity
- Estimating realistic capacity factors and generation potential

When analyzing renewable energy availability:
1. CITE ALL SOURCES: Reference every document used with [Source N] format
2. BE SPECIFIC: Provide concrete capacity estimates in kWh when data is available
3. ACKNOWLEDGE LIMITATIONS: Clearly state when data is incomplete or estimates are approximate
4. GROUND IN EVIDENCE: Base all claims on retrieved documents; avoid speculation
5. CONSIDER CONTEXT: Factor in location, industry, climate, and existing infrastructure
6. ASSESS RELIABILITY: Note seasonal variations and reliability scores for each energy source

Your analysis must be data-driven, transparent, and actionable.""",
        "metadata": PromptMetadata(
            name="energy_availability_analyst",
            category="system",
            description="System role for energy availability analysis",
            variables=[],
            purpose="Define role for analyzing renewable energy availability by location",
            output_format="text"
        )
    },
    "price_optimization_analyst": {
        "template": """You are an expert in energy pricing and portfolio optimization.

Your expertise includes:
- Analyzing cost structures for renewable energy sources (CAPEX, OPEX, LCOE)
- Evaluating price trends and market dynamics in energy markets
- Optimizing energy mix based on cost, reliability, and sustainability goals
- Understanding financing options and ROI calculations for renewable investments
- Assessing grid costs, interconnection fees, and operational expenses

When optimizing energy pricing:
1. CITE PRICING DATA: Reference all cost figures with [Source N] format
2. BUDGET ALIGNMENT: Ensure recommendations fit within specified budget constraints
3. MULTI-FACTOR OPTIMIZATION: Balance cost, reliability, and sustainability per given weights
4. TRANSPARENT CALCULATIONS: Show how costs are calculated and allocated
5. ACKNOWLEDGE UNCERTAINTY: Note when prices are estimates or subject to market volatility
6. CONSIDER TOTAL COST: Include installation, operation, maintenance, and grid connection costs
7. QUANTIFY TRADE-OFFS: Explain cost-benefit trade-offs between different energy sources

Provide evidence-based, financially sound recommendations.""",
        "metadata": PromptMetadata(
            name="price_optimization_analyst",
            category="system",
            description="System role for price optimization analysis",
            variables=[],
            purpose="Define role for optimizing energy mix based on pricing",
            output_format="text"
        )
    },
    "portfolio_decision_analyst": {
        "template": """You are a strategic energy portfolio advisor focused on ESG-aligned decision making.

Your expertise includes:
- Integrating environmental, social, and governance (ESG) factors into energy decisions
- Developing transition roadmaps to achieve net-zero targets
- Balancing sustainability goals with technical feasibility and budget constraints
- Assessing regulatory compliance and carbon reduction strategies
- Creating actionable, phased implementation plans

When making portfolio decisions:
1. ESG INTEGRATION: Prioritize sustainability targets (renewable percentage, zero non-renewable year)
2. WEIGHTED DECISION-MAKING: Apply configurable weights (ESG score, budget fit, technical feasibility)
3. TIMELINE CLARITY: Provide year-by-year transition roadmap to achieve targets
4. CITE RATIONALE: Reference previous analyses and sources with [Source N] format
5. FEASIBILITY CHECK: Ensure recommendations are technically and financially achievable
6. MEASURE PROGRESS: Define clear milestones and KPIs for tracking success
7. ACKNOWLEDGE RISKS: Note potential challenges or barriers to implementation
8. CONFIDENCE TRANSPARENCY: Express confidence level and reasoning behind recommendations

Your decisions must align with sustainability commitments while remaining practical and achievable.""",
        "metadata": PromptMetadata(
            name="portfolio_decision_analyst",
            category="system",
            description="System role for energy portfolio decision-making",
            variables=[],
            purpose="Define role for making ESG-aligned portfolio decisions",
            output_format="text"
        )
    }
}

# ============================================================================
# AGENT PROMPTS
# ============================================================================

AGENT_PROMPTS = {
    "research_analysis": {
        "template": """You are a research analyst. Analyze the following documents retrieved for the query: "{query}"

Documents:
{documents}

Provide:
1. Key findings (bullet points)
2. Relevance assessment for each document
3. Overall confidence in the retrieved information
4. Any gaps or limitations

Analysis:""",
        "metadata": PromptMetadata(
            name="research_analysis",
            category="agent",
            description="Prompt for research agent to analyze retrieved documents",
            variables=["query", "documents"],
            purpose="Analyze retrieved documents and assess their relevance to user query",
            output_format="structured_text"
        )
    },
    "general_analysis": {
        "template": """Analyze the following information and provide insights:

Data: {data}

Provide:
1. Key insights and patterns
2. Important relationships or connections
3. Recommendations or conclusions

Analysis:""",
        "metadata": PromptMetadata(
            name="general_analysis",
            category="agent",
            description="Prompt for general data analysis",
            variables=["data"],
            purpose="Perform general analysis to identify insights and patterns",
            output_format="structured_text"
        )
    },
    "comparative_analysis": {
        "template": """Compare and contrast the following information:

Data: {data}

Provide:
1. Similarities
2. Differences
3. Strengths and weaknesses
4. Overall comparison summary

Analysis:""",
        "metadata": PromptMetadata(
            name="comparative_analysis",
            category="agent",
            description="Prompt for comparative analysis",
            variables=["data"],
            purpose="Compare and contrast different pieces of information",
            output_format="structured_text"
        )
    },
    "trend_analysis": {
        "template": """Identify trends and patterns in the following information:

Data: {data}

Provide:
1. Major trends identified
2. Supporting evidence for each trend
3. Potential implications
4. Confidence in trend identification

Analysis:""",
        "metadata": PromptMetadata(
            name="trend_analysis",
            category="agent",
            description="Prompt for trend analysis",
            variables=["data"],
            purpose="Identify and analyze trends in data",
            output_format="structured_text"
        )
    },
    "explanation_basic": {
        "template": """Provide a simple explanation of how this response was generated:

Response: {response}

Number of sources used: {source_count}

Explain in 2-3 sentences why this response is reliable.""",
        "metadata": PromptMetadata(
            name="explanation_basic",
            category="agent",
            description="Prompt for basic explainability",
            variables=["response", "source_count"],
            purpose="Provide simple explanation of AI reasoning",
            output_format="text"
        )
    },
    "explanation_detailed": {
        "template": """Provide a detailed explanation of the AI decision process:

Response: {response}

Sources Used:
{sources}

Process: {process}

Explain:
1. What sources were used and why
2. How the information was synthesized
3. Reasoning
4. Any limitations or uncertainties""",
        "metadata": PromptMetadata(
            name="explanation_detailed",
            category="agent",
            description="Prompt for detailed explainability",
            variables=["response", "sources", "process"],
            purpose="Provide detailed explanation of AI reasoning and source usage",
            output_format="structured_text"
        )
    },
    "explanation_debug": {
        "template": """Provide a comprehensive technical explanation of the AI decision process:

Response: {response}

Sources Used (with similarity scores):
{sources_detailed}

Process: {process}

Provide:
1. Detailed source selection rationale
2. Step-by-step reasoning process
3. Confidence calculations and factors
4. Potential biases or limitations
5. Alternative interpretations considered
6. Grounding verification results
7. Recommendations for improving confidence""",
        "metadata": PromptMetadata(
            name="explanation_debug",
            category="agent",
            description="Prompt for debug-level explainability",
            variables=["response", "sources_detailed", "process"],
            purpose="Provide comprehensive technical explanation of AI reasoning",
            output_format="structured_text"
        )
    },
    "council_evaluation": {
        "template": """Query: {query}
{context_section}
{documents_section}

Provide your response in the following structure:

RESPONSE:
[Your detailed answer to the query]

REASONING:
[Your step-by-step reasoning process]

EVIDENCE:
[Key evidence points from the documents, if any]

CONFIDENCE:
[Your confidence level: high/medium/low and why]""",
        "metadata": PromptMetadata(
            name="council_evaluation",
            category="agent",
            description="Prompt for council agent evaluation",
            variables=["query", "context_section", "documents_section"],
            purpose="Evaluate queries with structured response format",
            output_format="structured_text"
        )
    },
    "energy_availability_analysis": {
        "template": """Analyze renewable energy availability for the following location and industry:

LOCATION: {location}
INDUSTRY: {industry}
BUDGET: ₹{budget:,.0f}

ENERGY SOURCE WEIGHTS (Preferences):
{weights}

RETRIEVED DOCUMENTS:
{documents}

YOUR TASK:
Analyze the renewable energy potential for this location considering:
1. **Solar Energy**: Assess solar irradiance, panel efficiency, rooftop/ground availability
2. **Wind Energy**: Evaluate wind speeds, turbine suitability, seasonal patterns
3. **Hydro Energy**: Consider water resources, hydroelectric potential, regulatory constraints

CRITICAL: Each energy source has DIFFERENT characteristics. DO NOT assign the same reliability to all sources.
- Solar: Typically 75-85% reliability (weather/daylight dependent)
- Wind: Typically 70-80% reliability (wind pattern dependent)
- Hydro: Typically 85-95% reliability (most predictable)

For EACH viable renewable source, provide:
- **Availability**: Yes/No with confidence level
- **Estimated Annual Capacity**: In kWh (cite source data or use industry standards)
- **Reliability Score**: 0-1 scale based on consistency and seasonality (MUST BE DIFFERENT for each source)
- **Capacity Factor**: Actual output vs theoretical maximum (Solar ~24%, Wind ~38%, Hydro ~47%)
- **Key Factors**: Geographic, climatic, or infrastructure considerations
- **Limitations**: Data gaps, seasonal variations, infrastructure needs

CITE ALL SOURCES using [Source N] format.
Be specific with capacity numbers when data is available.
If no specific data available, use realistic industry-standard values based on energy type.
Acknowledge when making estimates vs. using actual data.

ANALYSIS:""",
        "metadata": PromptMetadata(
            name="energy_availability_analysis",
            category="agent",
            description="Prompt for energy availability analysis agent",
            variables=["location", "industry", "budget", "documents", "weights"],
            purpose="Analyze location-specific renewable energy availability",
            output_format="structured_text"
        )
    },
    "price_optimization_analysis": {
        "template": """Optimize the renewable energy mix for the following scenario:

LOCATION: {location}
ANNUAL BUDGET: ₹{budget:,.0f}

AVAILABLE RENEWABLE OPTIONS:
{renewable_options}

OPTIMIZATION WEIGHTS:
{weights}

PRICING DATA FROM KNOWLEDGE BASE:
{pricing_data}

YOUR TASK:
Create an optimized energy portfolio that maximizes value based on the weighted criteria:
- **Cost**: Minimize total cost within budget
- **Reliability**: Ensure consistent energy supply
- **Sustainability**: Maximize renewable percentage

Optimization weights: {weights}

CRITICAL: DO NOT allocate equal percentages (33% each) unless the data truly justifies it.
Consider real-world factors:
- Hydro typically gets higher allocation due to reliability and low cost
- Solar and Wind vary by location climate
- Diversification is important but shouldn't override cost-effectiveness

For EACH renewable source in the optimized mix, provide:
- **Source Name**: (Solar/Wind/Hydro)
- **Percentage Allocation**: % of total energy mix (MUST vary based on source characteristics)
- **Annual Cost**: ₹ (calculated from percentage × budget)
- **Cost per kWh**: ₹/kWh (realistic values: Solar ~₹0.043, Wind ~₹0.052, Hydro ~₹0.041)
- **Reliability Score**: 0-1 scale (DIFFERENT for each source)
- **Justification**: Why this allocation is optimal given the weights

ENSURE:
✓ Total annual cost ≤ ₹{budget:,.0f}
✓ Percentages sum to 100%
✓ All cost figures cited from [Source N] or based on industry standards
✓ Trade-offs explained (e.g., higher cost = better reliability)
✓ Allocations reflect weighted priorities and source characteristics

OPTIMIZED PORTFOLIO:""",
        "metadata": PromptMetadata(
            name="price_optimization_analysis",
            category="agent",
            description="Prompt for price optimization agent",
            variables=["location", "budget", "renewable_options", "pricing_data", "weights"],
            purpose="Optimize energy mix based on cost, reliability, and sustainability",
            output_format="structured_text"
        )
    },
    "portfolio_decision_analysis": {
        "template": """Make the final energy portfolio decision based on comprehensive analysis:

COMPANY PROFILE:
- Industry: {industry}
- Location: {location}
- Annual Budget: ₹{budget:,.0f}

SUSTAINABILITY TARGETS (ESG):
- KP1 (Zero Non-Renewable Year): {sustainability_target_kp1}
- KP2 (Target Renewable %): {sustainability_target_kp2}%

DECISION WEIGHTS:
- ESG Score: {esg_weight:.0%}
- Budget Fit: {budget_weight:.0%}
- Technical Feasibility: {technical_weight:.0%}

ENERGY AVAILABILITY ANALYSIS:
{availability_analysis}

AVAILABLE OPTIONS:
{renewable_options}

PRICE OPTIMIZATION RESULTS:
{optimization_analysis}

OPTIMIZED MIX:
{optimized_mix}

YOUR TASK:
Make the final portfolio decision considering all factors. Provide:

1. **FINAL ENERGY PORTFOLIO MIX**:
   For each source (Solar/Wind/Hydro):
   - Percentage allocation
   - Annual energy (kWh)
   - Annual cost (₹)

2. **ESG ASSESSMENT**:
   - Current renewable percentage: ___%
   - Gap to target ({sustainability_target_kp2}%): ___%
   - Meets sustainability targets? Yes/No
   - Carbon reduction estimate

3. **TRANSITION ROADMAP** (Year-by-Year):
   From 2025 to {sustainability_target_kp1}:
   - Year | Renewable % | Milestone Action
   - Show progressive steps to reach zero non-renewable target

4. **CONFIDENCE & REASONING**:
   - Overall confidence score (0-1)
   - Key decision factors and trade-offs
   - Risks and mitigation strategies
   - Why this portfolio best balances all weighted criteria

5. **CITATIONS**:
   Reference all sources used in analysis with [Source N]

FINAL DECISION:""",
        "metadata": PromptMetadata(
            name="portfolio_decision_analysis",
            category="agent",
            description="Prompt for portfolio decision agent",
            variables=[
                "industry", "location", "budget", "sustainability_target_kp1",
                "sustainability_target_kp2", "esg_weight", "budget_weight",
                "technical_weight", "availability_analysis", "renewable_options",
                "optimization_analysis", "optimized_mix"
            ],
            purpose="Make final ESG-aligned energy portfolio decision",
            output_format="structured_text"
        )
    }
}

# ============================================================================
# RAG PROMPTS
# ============================================================================

RAG_PROMPTS = {
    "rag_generation_with_sources": {
        "template": """Context Information:
{context}

User Question: {query}

Instructions:
1. Answer the question using ONLY the information from the context provided above
2. If the context doesn't contain enough information, acknowledge this limitation
3. Cite your sources using the [Source N] format
4. Explain your reasoning{reasoning_detail}
{assumptions_note}

Answer:""",
        "metadata": PromptMetadata(
            name="rag_generation_with_sources",
            category="rag",
            description="Main RAG prompt for generating answers with source citations",
            variables=["context", "query", "reasoning_detail", "assumptions_note"],
            purpose="Generate context-based answers with proper citations",
            output_format="text_with_citations"
        )
    },
    "rag_generation_simple": {
        "template": """Context: {context}

Question: {query}

Answer:""",
        "metadata": PromptMetadata(
            name="rag_generation_simple",
            category="rag",
            description="Simple RAG prompt without source tracking",
            variables=["context", "query"],
            purpose="Generate basic context-based answers",
            output_format="text"
        )
    },
    "grounding_verification": {
        "template": """You are a fact-checking AI. Your task is to verify if the following response is grounded in the provided sources.

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
Explanation: [brief explanation]""",
        "metadata": PromptMetadata(
            name="grounding_verification",
            category="rag",
            description="Prompt for verifying response grounding in sources",
            variables=["sources_text", "response"],
            purpose="Verify that responses are factually grounded in source material",
            output_format="structured_text"
        )
    }
}

# ============================================================================
# LLM SERVICE PROMPTS
# ============================================================================

LLM_SERVICE_PROMPTS = {
    "document_summarization": {
        "template": """Summarize the following document in 200-300 words. Include main points and key information. Write in clear, professional language. Output ONLY the summary, nothing else.

Document:
{text}

Summary:""",
        "metadata": PromptMetadata(
            name="document_summarization",
            category="llm_service",
            description="Prompt for creating document summaries",
            variables=["text"],
            purpose="Generate concise summaries of documents",
            output_format="text"
        )
    },
    "keyword_extraction": {
        "template": """Extract {max_keywords} most important keywords from this document.
Return them as a JSON array like: ["keyword1", "keyword2", "keyword3"]

Document:
{text}

Keywords (JSON array only):""",
        "metadata": PromptMetadata(
            name="keyword_extraction",
            category="llm_service",
            description="Prompt for extracting keywords from documents",
            variables=["max_keywords", "text"],
            purpose="Identify key terms and concepts in documents",
            output_format="json"
        )
    },
    "topic_classification": {
        "template": """Identify the {max_topics} main topics or themes in this document.
Return them as a JSON array like: ["topic1", "topic2", "topic3"]

Document:
{text}

Topics (JSON array only):""",
        "metadata": PromptMetadata(
            name="topic_classification",
            category="llm_service",
            description="Prompt for classifying document topics",
            variables=["max_topics", "text"],
            purpose="Identify main topics and themes in documents",
            output_format="json"
        )
    },
    "content_type_determination": {
        "template": """Classify this document into one category: technical, legal, financial, academic, business, medical, or general.

Document:
{text}

Category:""",
        "metadata": PromptMetadata(
            name="content_type_determination",
            category="llm_service",
            description="Prompt for determining document content type",
            variables=["text"],
            purpose="Classify documents by genre or type",
            output_format="text"
        )
    }
}

# ============================================================================
# VISION PROMPTS
# ============================================================================

VISION_PROMPTS = {
    "ocr_extraction": {
        "template": """Extract ALL text from this image exactly as it appears.

Instructions:
- Preserve the original layout and formatting as much as possible
- Include all visible text, numbers, symbols, and punctuation
- Maintain line breaks and spacing
- If the text is structured (tables, lists, forms), preserve that structure
- If any text is unclear or difficult to read, note it with [unclear]
- Do not add any commentary or interpretation, only the extracted text

Extracted text:""",
        "metadata": PromptMetadata(
            name="ocr_extraction",
            category="vision",
            description="Prompt for extracting text from images",
            variables=[],
            purpose="Extract and preserve text from images with original formatting",
            output_format="text"
        )
    },
    "image_analysis": {
        "template": "{analysis_prompt}",
        "metadata": PromptMetadata(
            name="image_analysis",
            category="vision",
            description="Prompt for analyzing image content",
            variables=["analysis_prompt"],
            purpose="Describe and analyze image content",
            output_format="text"
        )
    }
}

# ============================================================================
# CHAT PROMPTS
# ============================================================================

CHAT_PROMPTS = {
    "direct_llm_with_history": {
        "template": """Previous conversation context:
{conversation_history}

Current question: {message}

Please provide a helpful, accurate response based on the question.""",
        "metadata": PromptMetadata(
            name="direct_llm_with_history",
            category="chat",
            description="Prompt for direct LLM queries with conversation history",
            variables=["conversation_history", "message"],
            purpose="Generate responses with conversation context",
            output_format="text"
        )
    },
    "direct_llm_simple": {
        "template": "{message}",
        "metadata": PromptMetadata(
            name="direct_llm_simple",
            category="chat",
            description="Prompt for simple direct LLM queries",
            variables=["message"],
            purpose="Pass through user message directly",
            output_format="text"
        )
    }
}

# ============================================================================
# ENERGY METADATA PROMPTS
# ============================================================================

ENERGY_METADATA_PROMPTS = {
    "energy_consumption_summary": {
        "template": """Analyze this energy consumption data and provide a comprehensive summary in 200-300 words.

Focus on:
1. Renewable vs Non-Renewable Energy Mix: Calculate the percentage of renewable (solar, wind, hydro) versus non-renewable (coal) energy sources
2. Consumption Patterns: Identify peak consumption periods, daily/monthly trends, and seasonal variations
3. Cost Analysis: Summarize total costs, average cost per kWh, and identify any pricing anomalies or cost spikes
4. Energy Sources: Break down the contribution of each energy source (solar, wind, hydro, coal) to total consumption
5. Grid Provider: Note the grid provider and any provider-related patterns
6. Data Quality: Flag any anomalies like negative values, impossible readings (e.g., solar generation at night), or missing data

Data:
{text}

Summary (200-300 words):""",
        "metadata": PromptMetadata(
            name="energy_consumption_summary",
            category="energy_metadata",
            description="Comprehensive summary of energy consumption data with sustainability focus",
            variables=["text"],
            purpose="Generate energy-focused summaries highlighting renewable mix, consumption patterns, and costs",
            output_format="text"
        )
    },
    "energy_anomaly_detection": {
        "template": """Analyze this energy data for anomalies and data quality issues.

Identify:
1. Negative Energy Values: Any negative consumption, generation, or cost values (physics violation)
2. Impossible Conditions: Solar generation at night, wind generation without wind, etc.
3. Price Outliers: Unusually high or low prices (>2x or <0.5x normal rates)
4. Demand Spikes: Sudden consumption increases (>5000 kWh when baseline is 500-800 kWh)
5. Missing Data: NaN, null, or missing values in critical fields
6. Math Errors: Inconsistencies in calculations (e.g., total != sum of parts)

Return as JSON array of detected anomalies with format:
[{{"type": "anomaly_type", "description": "brief description", "severity": "high/medium/low"}}]

Data:
{text}

Anomalies (JSON array only):""",
        "metadata": PromptMetadata(
            name="energy_anomaly_detection",
            category="energy_metadata",
            description="Detect data quality issues and anomalies in energy consumption data",
            variables=["text"],
            purpose="Identify errors, outliers, and data integrity issues for agent awareness",
            output_format="json"
        )
    },
    "sustainability_metrics_extraction": {
        "template": """Extract key sustainability metrics from this energy consumption data.

Calculate and return as JSON:
{{
  "total_energy_kwh": float,
  "renewable_energy_kwh": float,
  "non_renewable_energy_kwh": float,
  "renewable_percentage": float,
  "total_cost_inr": float,
  "average_cost_per_kwh": float,
  "solar_kwh": float,
  "wind_kwh": float,
  "hydro_kwh": float,
  "coal_kwh": float,
  "peak_demand_kwh": float,
  "grid_providers": ["list", "of", "providers"],
  "data_period_days": int
}}

Data:
{text}

Metrics (JSON only):""",
        "metadata": PromptMetadata(
            name="sustainability_metrics_extraction",
            category="energy_metadata",
            description="Extract quantitative sustainability and energy metrics",
            variables=["text"],
            purpose="Calculate precise energy consumption, renewable mix, and cost metrics",
            output_format="json"
        )
    },
    "energy_optimization_insights": {
        "template": """Based on this energy consumption data, provide {max_insights} actionable recommendations for energy optimization and increasing renewable energy usage.

Focus on:
1. Renewable Energy Adoption: Opportunities to increase solar, wind, or hydro capacity
2. Peak Demand Management: Strategies to reduce peak consumption and associated costs
3. Cost Reduction: Ways to lower average cost per kWh through renewable sources or better grid management
4. Energy Efficiency: Patterns that suggest waste or inefficiency
5. Grid Provider Optimization: Consider switching providers or negotiating better rates

Return as JSON array:
[{{"insight": "recommendation text", "impact": "high/medium/low", "category": "renewable/cost/efficiency/grid"}}]

Data:
{text}

Recommendations (JSON array with exactly {max_insights} items):""",
        "metadata": PromptMetadata(
            name="energy_optimization_insights",
            category="energy_metadata",
            description="Generate actionable recommendations for energy optimization",
            variables=["max_insights", "text"],
            purpose="Provide strategic insights for improving sustainability based on historical patterns",
            output_format="json"
        )
    }
}

# ============================================================================
# COMBINED REGISTRY
# ============================================================================

ALL_PROMPTS = {
    **SYSTEM_PROMPTS,
    **AGENT_PROMPTS,
    **RAG_PROMPTS,
    **LLM_SERVICE_PROMPTS,
    **VISION_PROMPTS,
    **CHAT_PROMPTS,
    **ENERGY_METADATA_PROMPTS
}
