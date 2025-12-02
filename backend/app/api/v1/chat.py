"""
Chat API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncGenerator
from loguru import logger
import json
import asyncio

from app.database.db import get_db
from app.database.models import User, Conversation, Message, AgentLog
from app.auth.security import get_current_active_user, require_permission
from app.agents.orchestrator import orchestrator

router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    provider: Optional[str] = "custom"  # custom or ollama
    include_grounding: bool = True

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    sources: List[Dict[str, Any]] = []
    confidence_score: float
    grounding: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    reasoning_chain: List[Dict[str, Any]] = []
    agents_involved: List[str] = []
    execution_time: float

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission("chat:use")),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response"""

    try:
        # Validate provider
        if chat_request.provider not in ["custom", "ollama"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider must be 'custom' or 'ollama'"
            )

        # Use user's preferred provider if not specified
        provider = chat_request.provider or current_user.preferred_llm

        # Get or create conversation
        if chat_request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.uuid == chat_request.conversation_id,
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
                title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message,
                user_id=current_user.id,
                llm_provider=provider,
                llm_model=f"{provider}_model"
            )
            db.add(conversation)
            db.flush()

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=chat_request.message
        )
        db.add(user_message)
        db.flush()

        # Execute RAG with agents
        result = await orchestrator.execute_rag_with_agents(
            query=chat_request.message,
            provider=provider,
            explainability_level=current_user.explainability_level,
            include_grounding=chat_request.include_grounding
        )

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.get('response', ''),
            retrieved_documents=[
                {
                    'id': src.get('id', ''),
                    'content': src.get('content', ''),
                    'similarity': src.get('similarity', 0.0)
                } for src in result.get('sources', [])
            ],
            confidence_score=result.get('confidence_score', 0.0),
            reasoning_chain=result.get('reasoning_chain', []),
            sources=result.get('sources', []),
            grounding_evidence=result.get('grounding'),
            agents_involved=result.get('agents_involved', [])
        )
        db.add(assistant_message)
        db.flush()

        # Save agent logs
        for log_entry in result['agent_logs']:
            agent_log = AgentLog(
                message_id=assistant_message.id,
                agent_name=log_entry['agent'],
                agent_type=log_entry.get('result', {}).get('agent', '').lower().replace('agent', ''),
                action=log_entry['action'],
                input_data={'query': chat_request.message},
                output_data=log_entry['result'],
                execution_time=log_entry.get('result', {}).get('execution_time', 0),
                status='success' if log_entry.get('result', {}).get('status') == 'completed' else 'failed',
                reasoning=log_entry.get('result', {}).get('reasoning', ''),
                confidence=log_entry.get('result', {}).get('confidence', 0.0)
            )
            db.add(agent_log)

        db.commit()

        logger.info(f"Chat message processed for user {current_user.username}")

        return ChatResponse(
            conversation_id=conversation.uuid,
            message_id=assistant_message.uuid,
            response=result.get('response', ''),
            sources=result.get('sources', []),
            confidence_score=result.get('confidence_score', 0.0),
            grounding=result.get('grounding'),
            explanation=result.get('explanation'),
            reasoning_chain=result.get('reasoning_chain', []),
            agents_involved=result.get('agents_involved', []),
            execution_time=result.get('execution_time', 0.0)
        )

    except Exception as e:
        logger.error(f"Chat message failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(require_permission("chat:history")),
    db: Session = Depends(get_db)
):
    """Get user's conversation history"""

    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()

    return [
        ConversationResponse(
            id=conv.uuid,
            title=conv.title,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            message_count=len(conv.messages)
        )
        for conv in conversations
    ]

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(require_permission("chat:history")),
    db: Session = Depends(get_db)
):
    """Get messages in a conversation"""

    conversation = db.query(Conversation).filter(
        Conversation.uuid == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).all()

    return [
        {
            'id': msg.uuid,
            'role': msg.role,
            'content': msg.content,
            'sources': msg.sources if msg.role == 'assistant' else None,
            'confidence_score': msg.confidence_score,
            'created_at': msg.created_at.isoformat()
        }
        for msg in messages
    ]

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation"""

    conversation = db.query(Conversation).filter(
        Conversation.uuid == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted successfully"}

@router.post("/message/stream")
async def send_message_stream(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission("chat:use")),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response via Server-Sent Events (SSE)"""

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events as agents execute"""
        conversation = None
        user_message = None
        assistant_message_data = {}
        agent_logs_data = []

        try:
            # Validate provider
            if chat_request.provider not in ["custom", "ollama"]:
                yield f"event: error\ndata: {json.dumps({'error': 'Provider must be custom or ollama'})}\n\n"
                return

            provider = chat_request.provider or current_user.preferred_llm

            # Send initial status
            yield f"event: status\ndata: {json.dumps({'status': 'initializing', 'message': 'Setting up conversation...'})}\n\n"
            await asyncio.sleep(0.01)  # Allow event to flush

            # Get or create conversation
            if chat_request.conversation_id:
                conversation = db.query(Conversation).filter(
                    Conversation.uuid == chat_request.conversation_id,
                    Conversation.user_id == current_user.id
                ).first()
                if not conversation:
                    yield f"event: error\ndata: {json.dumps({'error': 'Conversation not found'})}\n\n"
                    return
            else:
                conversation = Conversation(
                    title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message,
                    user_id=current_user.id,
                    llm_provider=provider,
                    llm_model=f"{provider}_model"
                )
                db.add(conversation)
                db.flush()

            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content=chat_request.message
            )
            db.add(user_message)
            db.flush()

            yield f"event: conversation\ndata: {json.dumps({'conversation_id': conversation.uuid})}\n\n"
            await asyncio.sleep(0.01)

            # Execute RAG with streaming agent status
            async for event in orchestrator.execute_rag_with_agents_stream(
                query=chat_request.message,
                provider=provider,
                explainability_level=current_user.explainability_level,
                include_grounding=chat_request.include_grounding
            ):
                event_type = event.get('type', 'status')
                event_data = event.get('data', {})

                # Store final result data for database
                if event_type == 'complete':
                    assistant_message_data = event_data
                elif event_type == 'agent_log':
                    agent_logs_data.append(event_data)

                # Send event to client
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
                await asyncio.sleep(0.01)

            # Save assistant message to database
            if assistant_message_data:
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=assistant_message_data.get('response', ''),
                    retrieved_documents=[
                        {
                            'id': src.get('id', ''),
                            'content': src.get('content', ''),
                            'similarity': src.get('similarity', 0.0)
                        } for src in assistant_message_data.get('sources', [])
                    ],
                    confidence_score=assistant_message_data.get('confidence_score', 0.0),
                    reasoning_chain=assistant_message_data.get('reasoning_chain', []),
                    sources=assistant_message_data.get('sources', []),
                    grounding_evidence=assistant_message_data.get('grounding'),
                    agents_involved=assistant_message_data.get('agents_involved', [])
                )
                db.add(assistant_message)
                db.flush()

                # Save agent logs
                for log_entry in agent_logs_data:
                    agent_log = AgentLog(
                        message_id=assistant_message.id,
                        agent_name=log_entry.get('agent', ''),
                        agent_type=log_entry.get('agent', '').lower().replace('agent', ''),
                        action=log_entry.get('action', ''),
                        input_data={'query': chat_request.message},
                        output_data=log_entry.get('result', {}),
                        execution_time=log_entry.get('result', {}).get('execution_time', 0),
                        status='success' if log_entry.get('result', {}).get('status') == 'completed' else 'failed',
                        reasoning=log_entry.get('result', {}).get('reasoning', ''),
                        confidence=log_entry.get('result', {}).get('confidence', 0.0)
                    )
                    db.add(agent_log)

                db.commit()

                # Send final message_id
                yield f"event: saved\ndata: {json.dumps({'message_id': assistant_message.uuid})}\n\n"

            yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"
            logger.info(f"SSE chat stream completed for user {current_user.username}")

        except Exception as e:
            logger.error(f"SSE chat stream failed: {e}")
            if conversation:
                db.rollback()
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )
