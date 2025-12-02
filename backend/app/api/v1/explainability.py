"""
Explainability API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from loguru import logger

from app.database.db import get_db
from app.database.models import User, Message
from app.auth.security import require_permission

router = APIRouter()

class ExplainabilityResponse(BaseModel):
    message_id: str
    response: str
    explanation: Optional[str]
    reasoning_chain: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    confidence_score: float
    grounding_evidence: Optional[Dict[str, Any]]
    agents_involved: List[str]

@router.get("/message/{message_id}", response_model=ExplainabilityResponse)
async def get_message_explainability(
    message_id: str,
    current_user: User = Depends(require_permission("explain:view")),
    db: Session = Depends(get_db)
):
    """Get explainability data for a message"""

    message = db.query(Message).filter(Message.uuid == message_id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Check if user has access to this message's conversation
    if message.conversation.user_id != current_user.id:
        # Check if user is admin
        is_admin = any(role.name == 'admin' for role in current_user.roles)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

    # Gather agent logs for this message
    agent_logs = []
    for log in message.agent_logs:
        agent_logs.append({
            'agent_name': log.agent_name,
            'action': log.action,
            'reasoning': log.reasoning,
            'confidence': log.confidence,
            'execution_time': log.execution_time
        })

    return ExplainabilityResponse(
        message_id=message.uuid,
        response=message.content,
        explanation=None,  # Could extract from agent logs
        reasoning_chain=message.reasoning_chain or [],
        sources=message.sources or [],
        confidence_score=message.confidence_score or 0.0,
        grounding_evidence=message.grounding_evidence,
        agents_involved=message.agents_involved or []
    )

@router.get("/conversation/{conversation_id}/confidence")
async def get_conversation_confidence_trend(
    conversation_id: str,
    current_user: User = Depends(require_permission("explain:view")),
    db: Session = Depends(get_db)
):
    """Get confidence score trend for a conversation"""

    from app.database.models import Conversation

    conversation = db.query(Conversation).filter(Conversation.uuid == conversation_id).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id != current_user.id:
        is_admin = any(role.name == 'admin' for role in current_user.roles)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.role == 'assistant'
    ).order_by(Message.created_at).all()

    confidence_trend = [
        {
            'message_id': msg.uuid,
            'confidence_score': msg.confidence_score or 0.0,
            'timestamp': msg.created_at.isoformat(),
            'num_sources': len(msg.sources) if msg.sources else 0
        }
        for msg in messages
    ]

    avg_confidence = sum(item['confidence_score'] for item in confidence_trend) / len(confidence_trend) if confidence_trend else 0.0

    return {
        'conversation_id': conversation_id,
        'avg_confidence': avg_confidence,
        'trend': confidence_trend
    }

@router.get("/conversation/{conversation_id}")
async def get_conversation_explanations(
    conversation_id: str,
    current_user: User = Depends(require_permission("explain:view")),
    db: Session = Depends(get_db)
):
    """Get all explanations for messages in a conversation"""

    from app.database.models import Conversation

    conversation = db.query(Conversation).filter(Conversation.uuid == conversation_id).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id != current_user.id:
        is_admin = any(role.name == 'admin' for role in current_user.roles)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.role == 'assistant'
    ).order_by(Message.created_at).all()

    explanations = []
    for msg in messages:
        # Get the user message that triggered this response
        user_msg = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.role == 'user',
            Message.created_at < msg.created_at
        ).order_by(Message.created_at.desc()).first()

        explanations.append({
            'message_id': msg.uuid,
            'conversation_id': conversation_id,
            'query': user_msg.content if user_msg else '',
            'response': msg.content,
            'confidence_score': msg.confidence_score or 0.0,
            'reasoning_chain': msg.reasoning_chain or [],
            'sources': msg.sources or [],
            'grounding_evidence': msg.grounding_evidence or [],
            'agent_decisions': [],  # Could be extracted from agent_logs
            'created_at': msg.created_at.isoformat()
        })

    return explanations
