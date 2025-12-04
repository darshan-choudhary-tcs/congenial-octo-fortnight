"""
Council of Agents API endpoints for multi-LLM consensus
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from loguru import logger
from datetime import datetime

from app.database.db import get_db
from app.database.models import User, Conversation, Message, AgentLog, TokenUsage, Document
from app.auth.security import get_current_active_user, require_permission
from app.agents.orchestrator import orchestrator
from app.config import settings

router = APIRouter()

# Token pricing configuration (per 1M tokens)
TOKEN_PRICING = {
    "custom": {
        "prompt": 0.14,
        "completion": 0.28
    },
    "ollama": {
        "prompt": 0.0,
        "completion": 0.0
    }
}

def _calculate_token_cost(provider: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate the estimated cost for token usage"""
    pricing = TOKEN_PRICING.get(provider, TOKEN_PRICING["custom"])
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
    return round(prompt_cost + completion_cost, 6)


class CouncilRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query to evaluate with council of agents")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID to continue")
    provider: Optional[str] = Field("custom", description="LLM provider: custom or ollama")
    voting_strategy: Optional[str] = Field("weighted_confidence", description="Voting strategy: weighted_confidence, highest_confidence, majority, synthesis")
    include_synthesis: Optional[bool] = Field(True, description="Whether to synthesize all responses")
    debate_rounds: Optional[int] = Field(1, description="Number of debate rounds (1 = no debate)")
    selected_document_ids: Optional[List[str]] = Field(None, description="Document UUIDs to scope search")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the key findings about climate change?",
                "provider": "custom",
                "voting_strategy": "weighted_confidence",
                "include_synthesis": True,
                "debate_rounds": 1
            }
        }


class VoteDetail(BaseModel):
    agent: str
    response: str
    confidence: float
    reasoning: str
    vote_weight: float
    temperature: float


class ConsensusMetrics(BaseModel):
    consensus_level: float
    confidence_variance: float
    agreement_score: float
    avg_confidence: float
    min_confidence: float
    max_confidence: float


class CouncilResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    voting_strategy: str
    votes: List[VoteDetail]
    consensus_metrics: ConsensusMetrics
    aggregated_confidence: float
    synthesis_used: bool
    sources: List[Dict[str, Any]] = []
    failed_votes: List[Dict[str, Any]] = []
    debate_rounds: int
    agents_involved: List[str]
    execution_time: float
    token_usage: Dict[str, Any]
    provider: str

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "message_id": "660e8400-e29b-41d4-a716-446655440001",
                "response": "Based on consensus from multiple agents...",
                "voting_strategy": "weighted_confidence",
                "votes": [
                    {
                        "agent": "AnalyticalVoter",
                        "response": "Climate change analysis...",
                        "confidence": 0.85,
                        "reasoning": "Based on scientific evidence...",
                        "vote_weight": 1.0,
                        "temperature": 0.3
                    }
                ],
                "consensus_metrics": {
                    "consensus_level": 0.82,
                    "confidence_variance": 0.05,
                    "agreement_score": 0.95,
                    "avg_confidence": 0.83,
                    "min_confidence": 0.78,
                    "max_confidence": 0.88
                },
                "aggregated_confidence": 0.83,
                "synthesis_used": True,
                "sources": [],
                "failed_votes": [],
                "debate_rounds": 1,
                "agents_involved": ["AnalyticalVoter", "CreativeVoter", "CriticalVoter"],
                "execution_time": 5.2,
                "token_usage": {"total_tokens": 3500},
                "provider": "custom"
            }
        }


@router.post("/evaluate", response_model=CouncilResponse)
async def evaluate_with_council(
    council_request: CouncilRequest,
    current_user: User = Depends(require_permission("chat:use")),
    db: Session = Depends(get_db)
):
    """
    Evaluate a query using council of agents for improved response quality
    
    This endpoint uses multiple specialized AI agents that vote on the best response,
    providing higher quality outputs through multi-perspective evaluation.
    """
    
    try:
        # Validate provider
        if council_request.provider not in ["custom", "ollama"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid provider. Use 'custom' or 'ollama'"
            )
        
        # Validate voting strategy
        valid_strategies = ["weighted_confidence", "highest_confidence", "majority", "synthesis"]
        if council_request.voting_strategy not in valid_strategies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid voting strategy. Use one of: {', '.join(valid_strategies)}"
            )
        
        # Validate debate rounds
        if council_request.debate_rounds < 1 or council_request.debate_rounds > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debate rounds must be between 1 and 5"
            )
        
        # Get or create conversation
        conversation = None
        if council_request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.uuid == council_request.conversation_id,
                Conversation.user_id == current_user.id
            ).first()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            # Create new conversation
            conversation = Conversation(
                title=f"Council: {council_request.query[:50]}...",
                user_id=current_user.id,
                llm_provider=council_request.provider,
                llm_model="council_multi_agent"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # Validate selected documents and build filter
        document_filter = None
        unavailable_docs = []
        unavailable_count = 0
        
        if council_request.selected_document_ids:
            # Get user's documents
            available_docs = db.query(Document).filter(
                Document.uuid.in_(council_request.selected_document_ids),
                Document.uploaded_by_id == current_user.id,
                Document.is_processed == True
            ).all()
            
            available_doc_uuids = [doc.uuid for doc in available_docs]
            unavailable_docs = [
                doc_id for doc_id in council_request.selected_document_ids 
                if doc_id not in available_doc_uuids
            ]
            unavailable_count = len(unavailable_docs)
            
            if available_doc_uuids:
                document_filter = {'document_ids': available_doc_uuids}
                conversation.selected_document_ids = available_doc_uuids
                db.commit()
        
        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=council_request.query
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Execute council voting
        logger.info(f"[Council API] User {current_user.username} executing council voting with strategy: {council_request.voting_strategy}")
        
        council_result = await orchestrator.execute_council_voting(
            query=council_request.query,
            provider=council_request.provider,
            user_id=current_user.id,
            voting_strategy=council_request.voting_strategy,
            include_synthesis=council_request.include_synthesis,
            debate_rounds=council_request.debate_rounds,
            document_filter=document_filter
        )
        
        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=council_result['response'],
            retrieved_documents=council_result.get('sources', []),
            confidence_score=council_result['aggregated_confidence'],
            low_confidence_warning=council_result['aggregated_confidence'] < 0.5,
            reasoning_chain=[
                {
                    'step': i + 1,
                    'agent': vote['agent'],
                    'confidence': vote['confidence'],
                    'reasoning': vote['reasoning'][:200]  # Truncate for storage
                }
                for i, vote in enumerate(council_result['votes'])
            ],
            sources=council_result.get('sources', []),
            agents_involved=council_result['agents_involved']
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        # Save agent logs
        for agent_log_data in council_result.get('agent_logs', []):
            agent_log = AgentLog(
                message_id=assistant_message.id,
                agent_name=agent_log_data['agent'],
                agent_type=agent_log_data.get('action', 'council_vote'),
                action=agent_log_data['action'],
                input_data={'query': council_request.query},
                output_data=agent_log_data.get('result', {}),
                status='success',
                created_at=datetime.fromisoformat(agent_log_data['timestamp'])
            )
            db.add(agent_log)
        
        # Save individual vote logs with council-specific data
        for vote in council_result['votes']:
            vote_log = AgentLog(
                message_id=assistant_message.id,
                agent_name=vote['agent'],
                agent_type=f"council_{vote['agent'].lower().replace('voter', '')}",
                action='council_vote',
                input_data={'query': council_request.query},
                output_data={'response': vote['response'][:500]},  # Truncate
                status='success',
                reasoning=vote['reasoning'],
                confidence=vote['confidence'],
                vote_data={
                    'response': vote['response'],
                    'reasoning': vote['reasoning'],
                    'vote_weight': vote['vote_weight'],
                    'temperature': vote['temperature']
                },
                vote_weight=vote['vote_weight'],
                consensus_score=council_result['consensus_metrics']['consensus_level']
            )
            db.add(vote_log)
        
        db.commit()
        
        # Track token usage
        token_usage_data = council_result.get('token_usage', {})
        if token_usage_data.get('total_tokens', 0) > 0:
            estimated_cost = _calculate_token_cost(
                council_request.provider,
                token_usage_data.get('prompt_tokens', 0),
                token_usage_data.get('completion_tokens', 0)
            )
            
            token_usage = TokenUsage(
                user_id=current_user.id,
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                provider=council_request.provider,
                model="council_multi_agent",
                operation_type="council_voting",
                prompt_tokens=token_usage_data.get('prompt_tokens', 0),
                completion_tokens=token_usage_data.get('completion_tokens', 0),
                total_tokens=token_usage_data.get('total_tokens', 0),
                estimated_cost=estimated_cost,
                currency="USD"
            )
            db.add(token_usage)
            db.commit()
        
        # Prepare response
        response = CouncilResponse(
            conversation_id=conversation.uuid,
            message_id=assistant_message.uuid,
            response=council_result['response'],
            voting_strategy=council_result['voting_strategy'],
            votes=[
                VoteDetail(
                    agent=vote['agent'],
                    response=vote['response'],
                    confidence=vote['confidence'],
                    reasoning=vote['reasoning'],
                    vote_weight=vote['vote_weight'],
                    temperature=vote['temperature']
                )
                for vote in council_result['votes']
            ],
            consensus_metrics=ConsensusMetrics(**council_result['consensus_metrics']),
            aggregated_confidence=council_result['aggregated_confidence'],
            synthesis_used=council_result['synthesis_used'],
            sources=council_result.get('sources', []),
            failed_votes=council_result.get('failed_votes', []),
            debate_rounds=council_result['debate_rounds'],
            agents_involved=council_result['agents_involved'],
            execution_time=council_result['execution_time'],
            token_usage=token_usage_data,
            provider=council_request.provider
        )
        
        logger.info(f"[Council API] Council voting completed successfully (consensus: {council_result['consensus_metrics']['consensus_level']:.2f})")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Council API] Error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Council evaluation failed: {str(e)}"
        )


@router.get("/strategies")
async def get_voting_strategies(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available voting strategies and their descriptions
    """
    return {
        "strategies": [
            {
                "name": "weighted_confidence",
                "description": "Weights responses by confidence scores and optionally synthesizes them",
                "recommended": True
            },
            {
                "name": "highest_confidence",
                "description": "Selects the response with the highest confidence score",
                "recommended": False
            },
            {
                "name": "synthesis",
                "description": "Always synthesizes all responses into a comprehensive answer",
                "recommended": True
            },
            {
                "name": "majority",
                "description": "Selects response closest to average confidence",
                "recommended": False
            }
        ],
        "default_strategy": "weighted_confidence",
        "debate_rounds_supported": True,
        "max_debate_rounds": 5
    }


@router.get("/agents")
async def get_council_agents(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get information about council agents
    """
    return {
        "agents": [
            {
                "name": "AnalyticalVoter",
                "type": "council_analytical",
                "description": "Analytical agent focused on logical reasoning and factual accuracy",
                "temperature": 0.3,
                "vote_weight": 1.0,
                "approach": "Prioritizes facts, systematic reasoning, and verifiable information"
            },
            {
                "name": "CreativeVoter",
                "type": "council_creative",
                "description": "Creative agent focused on innovative thinking and broader perspectives",
                "temperature": 0.9,
                "vote_weight": 1.0,
                "approach": "Considers unconventional perspectives and holistic connections"
            },
            {
                "name": "CriticalVoter",
                "type": "council_critical",
                "description": "Critical agent focused on identifying weaknesses and ensuring quality",
                "temperature": 0.5,
                "vote_weight": 1.0,
                "approach": "Identifies gaps, biases, and potential issues with skeptical mindset"
            }
        ],
        "total_agents": 3,
        "parallel_execution": True
    }
