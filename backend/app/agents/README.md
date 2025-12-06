# Agent System Documentation

## Overview

The agent system implements a **sophisticated multi-agent architecture** that combines specialized AI agents with a council voting mechanism for high-quality, explainable responses. Each agent has specific expertise and contributes to the overall decision-making process.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                        │
│              (Coordinates all agent activities)              │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├──────────────────────────────────────────────┐
               │                                               │
┌──────────────▼─────────┐                    ┌───────────────▼──────────┐
│   Base Agents          │                    │   Council Agents          │
│                        │                    │   (Voting System)         │
├────────────────────────┤                    ├──────────────────────────┤
│ • ResearchAgent        │                    │ • AnalyticalVoter         │
│ • AnalyzerAgent        │                    │ • CreativeVoter           │
│ • GroundingAgent       │                    │ • CriticalVoter           │
│ • ExplainabilityAgent  │                    │                           │
└────────────────────────┘                    └──────────────────────────┘
               │                                               │
               └───────────────┬───────────────────────────────┘
                               │
               ┌───────────────▼───────────────┐
               │  Domain-Specific Agents       │
               ├───────────────────────────────┤
               │ • EnergyAvailabilityAgent     │
               │ • PriceOptimizationAgent      │
               │ • EnergyPortfolioMixAgent     │
               └───────────────────────────────┘
```

## Agent Registry

All agents are registered in a global `AGENT_REGISTRY` for easy access and management.

```python
from app.agents.base import get_agent

# Get specific agent
research_agent = get_agent("research")
grounding_agent = get_agent("grounding")

# Get all council agents
council_agents = get_council_agents()
```

## Base Agent Classes

### BaseAgent

Abstract base class for all agents.

**Key Attributes**:
- `agent_type`: Unique identifier for the agent
- `llm_service`: Reference to LLM service
- `temperature`: Creativity level (0.0-1.0)
- `max_iterations`: Maximum execution steps

**Key Methods**:
- `execute()`: Main execution method (must be implemented)
- `calculate_confidence()`: Compute confidence score
- `log_execution()`: Save execution details to database

**Example Implementation**:

```python
from app.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, llm_service):
        super().__init__(
            agent_type="custom",
            llm_service=llm_service,
            temperature=0.7
        )

    async def execute(self, input_data, context=None):
        """Execute agent logic"""
        # 1. Process input
        processed = await self._process(input_data)

        # 2. Generate response
        response = await self.llm_service.generate_with_metadata(
            prompt=self._build_prompt(processed),
            temperature=self.temperature
        )

        # 3. Calculate confidence
        confidence = self.calculate_confidence(response, context)

        # 4. Log execution
        await self.log_execution(
            input_data=input_data,
            output=response,
            confidence=confidence
        )

        return {
            "response": response["content"],
            "confidence": confidence,
            "metadata": response["token_usage"]
        }
```

---

## Core Agents

### 1. ResearchAgent

**Purpose**: Retrieves and analyzes relevant documents from the vector store.

**Capabilities**:
- Semantic search across document collections
- Metadata-boosted retrieval
- Relevance scoring
- Document summarization

**Execution Flow**:
1. Extract query intent (keywords, topics)
2. Search vector store with metadata filters
3. Rank results by similarity
4. Analyze retrieved documents
5. Calculate confidence based on relevance

**Confidence Calculation**:
- Based on average similarity scores of retrieved documents
- Range: 0.0 (no relevant docs) to 1.0 (highly relevant)
- Formula: `confidence = min(avg_similarity * 1.2, 1.0)`

**Example Usage**:

```python
research_agent = get_agent("research")

result = await research_agent.execute(
    query="What renewable energy options are available in California?",
    context={
        "user_id": 5,
        "company_id": 1,
        "selected_document_ids": [45, 67]
    }
)

print(f"Found {len(result['documents'])} relevant documents")
print(f"Confidence: {result['confidence']}")
print(f"Analysis: {result['analysis']}")
```

**Output Structure**:
```json
{
  "documents": [
    {
      "id": 45,
      "name": "California Energy Report.pdf",
      "content": "California has excellent solar and wind resources...",
      "similarity": 0.92,
      "metadata": {...}
    }
  ],
  "analysis": "The retrieved documents provide comprehensive coverage of California's renewable energy landscape...",
  "confidence": 0.89,
  "sources": [...],
  "token_usage": {...}
}
```

---

### 2. AnalyzerAgent

**Purpose**: Performs data analysis and synthesis on structured data.

**Capabilities**:
- Statistical analysis
- Trend identification
- Comparative analysis
- Data summarization
- Insight generation

**Analysis Types**:
- **General Analysis**: Overall patterns and trends
- **Comparative Analysis**: Compare multiple datasets
- **Trend Analysis**: Identify temporal patterns

**Confidence Calculation**:
- Fixed baseline: 0.85
- Adjusted based on data quality, completeness, sample size
- Higher confidence for larger, cleaner datasets

**Example Usage**:

```python
analyzer_agent = get_agent("analyzer")

result = await analyzer_agent.execute(
    data={
        "type": "energy_consumption",
        "records": [...],  # CSV or structured data
        "analysis_type": "trend"
    },
    context={
        "date_range": "2024-01-01 to 2024-12-31",
        "location": "California Plant 1"
    }
)

print(f"Trend: {result['trend']}")
print(f"Insights: {result['insights']}")
```

**Output Structure**:
```json
{
  "analysis_type": "trend",
  "trend": "increasing",
  "insights": [
    "Energy consumption increased 15% year-over-year",
    "Peak demand occurs in summer months",
    "Renewable percentage grew from 30% to 38%"
  ],
  "statistics": {
    "mean": 12500,
    "median": 12000,
    "std_dev": 2300
  },
  "confidence": 0.87,
  "recommendations": [...]
}
```

---

### 3. GroundingAgent

**Purpose**: Verifies responses against source documents to prevent hallucinations.

**Capabilities**:
- Fact checking against sources
- Citation verification
- Hallucination detection
- Evidence mapping
- Claim validation

**Verification Process**:
1. Parse response into individual claims
2. Check each claim against source documents
3. Identify supported vs. unsupported claims
4. Calculate grounding score
5. Flag potential hallucinations

**Grounding Score**:
- `1.0`: All claims supported by sources
- `0.5-0.99`: Most claims supported, some inference
- `< 0.5`: Significant unsupported claims (warning)

**Example Usage**:

```python
grounding_agent = get_agent("grounding")

result = await grounding_agent.execute(
    response="California has excellent solar potential with average irradiance of 5.5 kWh/m²/day...",
    sources=[
        {
            "content": "California receives 5.3-5.7 kWh/m²/day solar irradiance...",
            "document_id": 45
        }
    ],
    context={"verify_facts": True}
)

print(f"Grounding Score: {result['grounding_score']}")
print(f"Unsupported Claims: {len(result['unsupported_claims'])}")
```

**Output Structure**:
```json
{
  "grounding_score": 0.94,
  "supported_claims": [
    {
      "claim": "California has excellent solar potential",
      "evidence": "Document 45, paragraph 3",
      "confidence": 0.95
    },
    {
      "claim": "Average irradiance of 5.5 kWh/m²/day",
      "evidence": "Document 45, table 2",
      "confidence": 0.98
    }
  ],
  "unsupported_claims": [],
  "inferred_claims": [
    {
      "claim": "Suitable for large-scale solar installations",
      "reasoning": "Inferred from high irradiance values",
      "confidence": 0.80
    }
  ],
  "hallucination_risk": "low",
  "recommendations": "Response is well-grounded in source documents"
}
```

---

### 4. ExplainabilityAgent

**Purpose**: Generates transparent, human-readable explanations of AI decision-making.

**Capabilities**:
- Multi-level explanations (basic, detailed, debug)
- Reasoning chain generation
- Confidence explanation
- Assumption identification
- Source attribution

**Explainability Levels**:

1. **Basic**: High-level summary
   - What decision was made
   - Why it was made (1-2 sentences)
   - Confidence level

2. **Detailed**: Step-by-step reasoning
   - Each reasoning step explained
   - Evidence for each step
   - Confidence breakdown
   - Source attribution

3. **Debug**: Complete decision tree
   - All assumptions listed
   - Alternative paths considered
   - Uncertainty quantification
   - Full agent execution log

**Example Usage**:

```python
explainability_agent = get_agent("explainability")

result = await explainability_agent.execute(
    response="Recommend 45% solar, 30% wind for California manufacturing",
    reasoning_steps=[...],  # From previous agents
    sources=[...],
    confidence=0.87,
    level="detailed"  # or "basic", "debug"
)

print(result['explanation'])
```

**Output Structure (Detailed Level)**:
```json
{
  "explanation": "I recommended a solar-wind hybrid approach based on the following reasoning:\n\n**Step 1: Resource Assessment**\n- California has excellent solar resources (5.5 kWh/m²/day irradiance)\n- West Texas wind corridor accessible with 35-40% capacity factor\n- Evidence: Documents 45, 67\n- Confidence: 0.92\n\n**Step 2: Cost Analysis**\n- Solar LCOE: $40-50/MWh in California\n- Wind LCOE: $35-45/MWh\n- Combined cost: $42/MWh average\n- Evidence: Document 89, Table 3\n- Confidence: 0.85\n\n**Step 3: Reliability Assessment**\n- Solar + wind provides complementary generation profiles\n- Combined capacity factor: ~30%\n- Grid backup recommended for 24/7 operations\n- Confidence: 0.83\n\n**Overall Confidence: 0.87**\nBased on high-quality data from recent industry reports with strong agreement across sources.",
  "reasoning_chain": [
    {
      "step": 1,
      "title": "Resource Assessment",
      "description": "Evaluated renewable resource availability",
      "evidence": ["Document 45", "Document 67"],
      "confidence": 0.92,
      "assumptions": ["Irradiance data representative of typical years"]
    },
    {
      "step": 2,
      "title": "Cost Analysis",
      "description": "Analyzed levelized cost of energy",
      "evidence": ["Document 89"],
      "confidence": 0.85,
      "assumptions": ["2024 cost data applicable to 2025-2030"]
    }
  ],
  "confidence_factors": {
    "data_quality": 0.90,
    "source_reliability": 0.88,
    "model_certainty": 0.85,
    "overall": 0.87
  },
  "assumptions": [
    "Solar irradiance data representative of typical years",
    "Cost projections stable over 5-year period",
    "No major regulatory changes",
    "Grid interconnection available"
  ],
  "limitations": [
    "Site-specific assessment needed for final decision",
    "Local incentives not considered",
    "Storage costs not included in LCOE"
  ]
}
```

---

## Council Voting System

The council system uses **multiple AI agents with different perspectives** to evaluate queries and reach consensus.

### Council Agent Types

#### 1. AnalyticalVoter (CouncilAgent)

**Characteristics**:
- Temperature: 0.3 (low creativity, high precision)
- Focus: Logical reasoning, factual accuracy, data-driven
- Approach: Conservative, evidence-based
- Strengths: Reliability, accuracy, systematic analysis
- Use Cases: Technical decisions, data interpretation, risk assessment

**Voting Behavior**:
- Prioritizes facts over speculation
- High confidence when data is clear
- Lower confidence when data is ambiguous
- Detailed reasoning with citations

---

#### 2. CreativeVoter (CouncilAgent)

**Characteristics**:
- Temperature: 0.9 (high creativity)
- Focus: Innovation, novel solutions, outside-the-box thinking
- Approach: Forward-thinking, exploratory
- Strengths: Innovation, alternative perspectives, future trends
- Use Cases: Strategic planning, brainstorming, identifying opportunities

**Voting Behavior**:
- Proposes innovative solutions
- Considers emerging technologies
- Moderate to high confidence in novel approaches
- Expansive reasoning with possibilities

---

#### 3. CriticalVoter (CouncilAgent)

**Characteristics**:
- Temperature: 0.5 (balanced)
- Focus: Quality assurance, risk identification, validation
- Approach: Skeptical, thorough, devil's advocate
- Strengths: Risk mitigation, quality control, error detection
- Use Cases: Decision validation, risk assessment, quality review

**Voting Behavior**:
- Identifies potential issues and risks
- Questions assumptions
- Moderate confidence, highlights uncertainties
- Critical reasoning with caveats

---

### Voting Strategies

#### 1. Weighted Confidence

Aggregates responses weighted by confidence scores.

**Formula**:
```
final_response = Σ(vote_i × confidence_i × weight_i) / Σ(confidence_i × weight_i)
```

**When to Use**:
- Default strategy for most queries
- When all agents provide valuable input
- Balanced decision-making needed

**Example**:
```python
# Analytical: confidence=0.88, weight=1.0
# Creative: confidence=0.76, weight=1.0
# Critical: confidence=0.85, weight=1.0

# Result emphasizes analytical and critical perspectives
# Final confidence: 0.83 (weighted average)
```

---

#### 2. Highest Confidence

Selects the single response with highest confidence.

**When to Use**:
- Need single definitive answer
- One agent clearly more qualified for query type
- Time-sensitive decisions

**Example**:
```python
# Analytical: 0.88
# Creative: 0.76
# Critical: 0.85

# Result: Analytical agent's response selected
```

---

#### 3. Majority Vote

Most common response wins (requires similar responses).

**When to Use**:
- Binary or categorical decisions
- Seeking consensus on classification
- Multiple choice scenarios

**Example**:
```python
# Analytical: "Solar is best" (0.88)
# Creative: "Hybrid solar-wind optimal" (0.76)
# Critical: "Solar is best" (0.85)

# Result: "Solar is best" (2 votes)
```

---

#### 4. Synthesis

LLM combines all perspectives into new comprehensive response.

**When to Use**:
- Complex decisions requiring all perspectives
- Need holistic view
- Diverse viewpoints valuable

**Process**:
1. Collect all agent responses
2. Prompt synthesis LLM to combine perspectives
3. Generate unified response incorporating key points
4. Calculate consensus metrics

**Example Output**:
```
The council recommends a hybrid approach combining insights from all perspectives:

**Analytical Perspective**: Data shows solar as most cost-effective with proven ROI.

**Creative Perspective**: Consider pairing solar with emerging battery storage technology.

**Critical Perspective**: Ensure grid backup to mitigate intermittency risks.

**Synthesized Recommendation**: Implement 60% solar with 15% battery storage and 25% grid backup. This balances cost-effectiveness (analytical), innovation (creative), and reliability (critical).
```

---

### Debate Rounds

Optional iterative refinement where agents critique and improve responses.

**Process**:
1. **Round 1**: Initial votes from all agents
2. **Critique Phase**: Each agent reviews others' responses
3. **Round 2**: Revised votes incorporating feedback
4. **Repeat**: Up to 5 rounds or until consensus threshold reached

**Benefits**:
- Higher quality decisions
- Better consensus
- Identification of blind spots
- Refined reasoning

**Trade-offs**:
- Increased token usage
- Longer processing time
- May over-converge (lose diverse perspectives)

**Example Usage**:

```python
from app.agents.orchestrator import Orchestrator

orchestrator = Orchestrator(db, llm_service, vector_store)

result = await orchestrator.council_evaluate(
    query="What renewable energy mix for Texas manufacturing?",
    voting_strategy="synthesis",
    debate_rounds=2,  # Enable 2 rounds of debate
    context={...}
)

print(f"Consensus after {result['debate_rounds_completed']} rounds")
print(f"Agreement score: {result['consensus_metrics']['agreement_score']}")
```

---

### Consensus Metrics

Quantifies agreement and confidence across council agents.

**Metrics Provided**:

1. **Consensus Level** (0-1):
   - How similar are the responses?
   - 1.0 = identical, 0.0 = completely different
   - Calculated using semantic similarity

2. **Confidence Variance**:
   - Spread of confidence scores
   - Lower = more agreement on certainty
   - Higher = disagreement on confidence

3. **Agreement Score** (0-1):
   - Combined metric: consensus × (1 - confidence_variance)
   - Overall measure of council alignment

4. **Average/Min/Max Confidence**:
   - Statistical summary of agent confidence
   - Useful for understanding range

**Example Metrics**:
```json
{
  "consensus_level": 0.82,
  "confidence_variance": 0.0036,
  "agreement_score": 0.78,
  "avg_confidence": 0.83,
  "min_confidence": 0.76,
  "max_confidence": 0.88,
  "interpretation": "High agreement with consistent confidence"
}
```

**Interpretation Guide**:
- Agreement > 0.80: Strong consensus, reliable decision
- Agreement 0.60-0.80: Moderate consensus, consider all perspectives
- Agreement < 0.60: Low consensus, may need more information or human review

---

## Domain-Specific Agents

### 1. EnergyAvailabilityAgent

**Purpose**: Analyzes renewable energy resource availability by location.

**Capabilities**:
- Solar potential assessment (irradiance, capacity factor)
- Wind resource evaluation (speed, consistency, seasonal patterns)
- Hydro potential (water resources, topography)

- Geographic and climatic analysis
- Historical weather data interpretation

**Input Requirements**:
```json
{
  "location": "California",
  "industry": "manufacturing",
  "site_characteristics": {
    "area_sqm": 50000,
    "latitude": 37.7749,
    "longitude": -122.4194,
    "elevation": 100
  },
  "constraints": {
    "zoning": "industrial",
    "grid_access": true
  }
}
```

**Output Structure**:
```json
{
  "solar_potential": {
    "rating": "excellent",
    "irradiance_kwh_per_sqm_day": 5.5,
    "capacity_factor": 0.23,
    "recommended_capacity_kw": 800,
    "annual_generation_kwh": 1613760,
    "seasonal_variation": "low",
    "notes": "Excellent year-round solar with minimal cloud cover"
  },
  "wind_potential": {
    "rating": "good",
    "avg_wind_speed_mps": 6.2,
    "capacity_factor": 0.30,
    "recommended_capacity_kw": 500,
    "annual_generation_kwh": 1314000,
    "seasonal_variation": "moderate",
    "notes": "Coastal winds provide good resource, stronger in spring"
  },
  "hydro_potential": {
    "rating": "not_applicable",
    "notes": "No suitable water resources on-site"
  },

  "recommendations": [
    "Prioritize solar as primary renewable source",
    "Consider wind as secondary source",
    "Battery storage recommended for peak shifting"
  ],
  "confidence": 0.89,
  "sources": [...]
}
```

---

### 2. PriceOptimizationAgent

**Purpose**: Optimizes energy portfolio for cost while balancing reliability and sustainability.

**Capabilities**:
- LCOE (Levelized Cost of Energy) calculation
- ROI and payback period analysis
- Operating cost estimation
- Incentive and subsidy identification
- Market price analysis
- Risk-adjusted cost modeling

**Optimization Factors**:
- Capital costs (installation, equipment)
- Operating costs (maintenance, insurance)
- Energy cost savings
- Revenue opportunities (RECs, demand response)
- Financing options
- Risk premium for reliability

**Input Requirements**:
```json
{
  "portfolio_options": [
    {
      "technology": "solar",
      "capacity_kw": 800,
      "capital_cost": 240000,
      "operating_cost_annual": 4000
    },
    {
      "technology": "wind",
      "capacity_kw": 500,
      "capital_cost": 200000,
      "operating_cost_annual": 6000
    }
  ],
  "constraints": {
    "max_budget": 500000,
    "min_renewable_percentage": 60,
    "required_reliability": 0.98
  },
  "market_data": {
    "electricity_price_per_kwh": 0.12,
    "rec_price_per_mwh": 15,
    "discount_rate": 0.06
  }
}
```

**Output Structure**:
```json
{
  "optimal_portfolio": {
    "solar_capacity_kw": 700,
    "wind_capacity_kw": 400,
    "storage_capacity_kwh": 200,
    "total_cost": 475000
  },
  "financial_analysis": {
    "total_capex": 475000,
    "annual_opex": 12000,
    "annual_savings": 148000,
    "net_present_value": 287500,
    "internal_rate_of_return": 0.24,
    "payback_period_years": 3.8,
    "lifetime_savings_20yr": 2100000
  },
  "revenue_streams": {
    "energy_cost_savings": 125000,
    "renewable_energy_credits": 15000,
    "demand_response": 8000,
    "total": 148000
  },
  "risk_analysis": {
    "price_volatility_risk": "low",
    "technology_risk": "low",
    "financing_risk": "low-moderate",
    "overall_risk": "low"
  },
  "recommendations": [
    "Proceed with solar-wind hybrid",
    "Explore PACE financing to reduce upfront costs",
    "Lock in PPA rates for 10 years",
    "Add battery storage in phase 2"
  ],
  "confidence": 0.84,
  "sources": [...]
}
```

---

### 3. EnergyPortfolioMixAgent

**Purpose**: Recommends optimal renewable energy portfolio mix.

**Capabilities**:
- Multi-criteria optimization
- ESG (Environmental, Social, Governance) scoring
- Technical feasibility assessment
- Risk-return trade-off analysis
- Scenario modeling
- Sensitivity analysis

**Optimization Criteria**:
1. **Renewable Percentage**: Maximize clean energy
2. **Cost**: Minimize LCOE and total cost
3. **Reliability**: Ensure 24/7 availability
4. **ESG Score**: Maximize sustainability impact
5. **Technical Feasibility**: Practical implementation
6. **Scalability**: Future expansion potential

**Input Requirements**:
```json
{
  "target_renewable_percentage": 75,
  "budget_usd": 500000,
  "annual_consumption_kwh": 1500000,
  "location": "Texas",
  "industry": "manufacturing",
  "priority_weights": {
    "cost": 0.35,
    "reliability": 0.30,
    "sustainability": 0.25,
    "innovation": 0.10
  },
  "constraints": {
    "max_payback_period_years": 7,
    "min_capacity_factor": 0.25
  }
}
```

**Output Structure**:
```json
{
  "recommended_mix": {
    "solar_percentage": 45,
    "wind_percentage": 30,

    "hydro_percentage": 0,
    "grid_renewable_percentage": 20,
    "backup_gas_percentage": 5,
    "total_renewable_percentage": 95
  },
  "portfolio_characteristics": {
    "total_capacity_kw": 1200,
    "combined_capacity_factor": 0.28,
    "annual_generation_kwh": 2941440,
    "excess_generation_percentage": 96,
    "grid_supplementation_needed": false
  },
  "esg_score": {
    "environmental": 0.92,
    "social": 0.78,
    "governance": 0.85,
    "overall": 0.85,
    "carbon_reduction_tons_annual": 850,
    "renewable_energy_percentage": 95
  },
  "risk_assessment": {
    "technical_risks": "low",
    "financial_risks": "low-moderate",
    "regulatory_risks": "low",
    "weather_risks": "moderate",
    "overall_risk": "low",
    "risk_score": 0.23
  },
  "justification": "This portfolio optimizes across all criteria:\n- **Renewable %**: Achieves 95%, exceeding 75% target\n- **Cost**: Total cost $475k within $500k budget, payback 3.8 years\n- **Reliability**: Complementary solar-wind profiles, grid backup ensures 24/7\n- **ESG**: 0.85 score, 850 tons CO2 reduction annually\n- **Technical**: Both technologies proven in Texas climate",
  "scenario_analysis": [
    {
      "scenario": "high_solar",
      "mix": {"solar": 60, "wind": 20, "grid": 15, "backup": 5},
      "cost": 490000,
      "reliability": 0.97,
      "renewable_percentage": 95,
      "score": 0.82
    },
    {
      "scenario": "balanced",
      "mix": {"solar": 45, "wind": 30, "grid": 20, "backup": 5},
      "cost": 475000,
      "reliability": 0.98,
      "renewable_percentage": 95,
      "score": 0.87
    }
  ],
  "recommendations": [
    "Implement balanced scenario for optimal risk-return",
    "Phase installation: solar first (year 1), wind second (year 2)",
    "Add battery storage in year 3 to increase self-consumption",
    "Monitor performance and adjust mix based on actual generation"
  ],
  "confidence": 0.87,
  "sources": [...]
}
```

---

## Agent Orchestrator

The `Orchestrator` class coordinates all agent activities and implements the RAG pipeline.

### Key Methods

#### 1. `rag_generate()`

Main RAG pipeline combining research, generation, grounding, and explanation.

```python
result = await orchestrator.rag_generate(
    query="What renewable energy options for California?",
    conversation_id=123,
    user_id=5,
    company_id=1,
    selected_document_ids=[45, 67],
    use_grounding=True,
    explainability_level="detailed"
)
```

**Process**:
1. **Research**: Retrieve relevant documents
2. **Generate**: Create response with context
3. **Ground**: Verify against sources (if enabled)
4. **Explain**: Generate reasoning chain
5. **Log**: Save all execution details

---

#### 2. `council_evaluate()`

Multi-agent council evaluation with voting.

```python
result = await orchestrator.council_evaluate(
    query="Optimal energy mix for Texas manufacturing?",
    voting_strategy="synthesis",
    debate_rounds=2,
    user_id=5,
    company_id=1,
    selected_document_ids=[45, 67, 89]
)
```

**Returns**:
- All individual votes with reasoning
- Consensus response
- Consensus metrics
- Token usage breakdown
- Sources used

---

#### 3. `analyze_data()`

Data analysis pipeline using AnalyzerAgent.

```python
result = await orchestrator.analyze_data(
    data={"records": [...]},
    analysis_type="trend",
    user_id=5,
    explainability_level="detailed"
)
```

---

## Best Practices

### 1. Agent Selection

- **Single query, factual answer**: Use ResearchAgent + RAG pipeline
- **Data analysis needed**: Use AnalyzerAgent
- **Critical decision**: Use council with debate rounds
- **Need transparency**: Enable explainability (detailed level)
- **Prevent hallucination**: Enable GroundingAgent

### 2. Configuration

```python
# Conservative configuration (production)
config = {
    "temperature": 0.3,
    "use_grounding": True,
    "explainability_level": "detailed",
    "enable_council": True,
    "voting_strategy": "weighted_confidence"
}

# Exploratory configuration (research)
config = {
    "temperature": 0.8,
    "use_grounding": False,
    "explainability_level": "basic",
    "enable_council": True,
    "voting_strategy": "synthesis"
}
```

### 3. Token Optimization

- Use basic explainability for simple queries
- Disable grounding for low-risk responses
- Limit debate rounds (1-2 typically sufficient)
- Use highest_confidence strategy instead of synthesis

### 4. Error Handling

```python
try:
    result = await orchestrator.rag_generate(...)
except AgentExecutionError as e:
    logger.error(f"Agent failed: {e}")
    # Fallback to simpler approach
    result = await fallback_generation(...)
```

### 5. Monitoring

Track agent performance:
- Execution time per agent
- Token usage per agent
- Confidence score trends
- Error rates
- User satisfaction with responses

---

## Testing

### Unit Tests

```python
import pytest
from app.agents.base import ResearchAgent

@pytest.mark.asyncio
async def test_research_agent_execution(mock_llm_service, mock_vector_store):
    agent = ResearchAgent(mock_llm_service, mock_vector_store)

    result = await agent.execute(
        query="Test query",
        context={"user_id": 1, "company_id": 1}
    )

    assert result["confidence"] > 0
    assert len(result["documents"]) > 0
    assert "analysis" in result
```

### Integration Tests

Test complete orchestration:

```python
@pytest.mark.asyncio
async def test_full_rag_pipeline(test_db, llm_service, vector_store):
    orchestrator = Orchestrator(test_db, llm_service, vector_store)

    result = await orchestrator.rag_generate(
        query="Test query",
        user_id=1,
        company_id=1
    )

    assert result["response"]
    assert result["confidence"] > 0
    assert len(result["sources"]) > 0
    assert len(result["reasoning_chain"]) > 0
```

---

## Troubleshooting

### Low Confidence Scores

**Symptoms**: Consistent confidence < 0.5

**Causes**:
- Poor quality documents in vector store
- Query-document mismatch
- Insufficient context
- Ambiguous queries

**Solutions**:
1. Improve document quality and metadata
2. Use metadata-boosted retrieval
3. Provide more context in query
4. Use council for difficult queries

---

### High Token Usage

**Symptoms**: Token costs exceeding budget

**Causes**:
- Debate rounds enabled
- Synthesis voting strategy
- Detailed explainability
- All agents enabled

**Solutions**:
1. Use basic explainability for simple queries
2. Reduce debate rounds to 1
3. Use highest_confidence instead of synthesis
4. Disable grounding for low-risk queries

---

### Inconsistent Council Votes

**Symptoms**: Low consensus metrics (< 0.6)

**Causes**:
- Ambiguous query
- Insufficient information
- Multiple valid solutions
- Agent configuration issues

**Solutions**:
1. Enable debate rounds for refinement
2. Provide more context
3. Use synthesis strategy to combine perspectives
4. Check agent temperature settings

---

For more information, see:
- [Main Backend Documentation](../../README.md)
- [API Documentation](../api/README.md)
- [RAG Documentation](../rag/README.md)
