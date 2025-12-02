"""
Agent management and monitoring API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from loguru import logger

from app.database.db import get_db
from app.database.models import User, AgentLog
from app.auth.security import require_permission
from app.agents.orchestrator import orchestrator

router = APIRouter()

class AgentStatusResponse(BaseModel):
    total_agents: int
    agents: List[Dict[str, Any]]
    execution_history_count: int

@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(
    current_user: User = Depends(require_permission("agents:read"))
):
    """Get status of all agents"""

    status = orchestrator.get_agent_status()

    return AgentStatusResponse(**status)

@router.get("/logs")
async def get_agent_logs(
    limit: int = 50,
    current_user: User = Depends(require_permission("agents:read")),
    db: Session = Depends(get_db)
):
    """Get recent agent execution logs"""

    logs = db.query(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit).all()

    return [
        {
            'id': log.uuid,
            'agent_name': log.agent_name,
            'agent_type': log.agent_type,
            'action': log.action,
            'status': log.status,
            'confidence': log.confidence,
            'execution_time': log.execution_time,
            'reasoning': log.reasoning,
            'created_at': log.created_at.isoformat()
        }
        for log in logs
    ]

@router.get("/logs/message/{message_id}")
async def get_message_agent_logs(
    message_id: str,
    current_user: User = Depends(require_permission("agents:read")),
    db: Session = Depends(get_db)
):
    """Get agent logs for a specific message"""

    from app.database.models import Message

    message = db.query(Message).filter(Message.uuid == message_id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    logs = db.query(AgentLog).filter(AgentLog.message_id == message.id).all()

    return [
        {
            'id': log.uuid,
            'agent_name': log.agent_name,
            'agent_type': log.agent_type,
            'action': log.action,
            'input_data': log.input_data,
            'output_data': log.output_data,
            'status': log.status,
            'confidence': log.confidence,
            'execution_time': log.execution_time,
            'reasoning': log.reasoning,
            'created_at': log.created_at.isoformat()
        }
        for log in logs
    ]
