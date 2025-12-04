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
from app.database.models import User, Conversation, Message, AgentLog, TokenUsage, Document
from app.auth.security import get_current_active_user, require_permission
from app.agents.orchestrator import orchestrator
from app.config import settings

router = APIRouter()

# Token pricing configuration (per 1M tokens)
TOKEN_PRICING = {
    "custom": {
        "prompt": 0.14,  # DeepSeek pricing: $0.14 per 1M prompt tokens
        "completion": 0.28  # DeepSeek pricing: $0.28 per 1M completion tokens
    },
    "ollama": {
        "prompt": 0.0,  # Local model - free
        "completion": 0.0
    }
}

def _calculate_token_cost(provider: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate the estimated cost for token usage"""
    pricing = TOKEN_PRICING.get(provider, TOKEN_PRICING["custom"])
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
    return round(prompt_cost + completion_cost, 6)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    provider: Optional[str] = "custom"  # custom or ollama
    include_grounding: bool = True
    selected_document_ids: Optional[List[str]] = None  # Document UUIDs to scope search

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    sources: List[Dict[str, Any]] = []
    confidence_score: float
    low_confidence_warning: bool = False
    grounding: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    reasoning_chain: List[Dict[str, Any]] = []
    agents_involved: List[str] = []
    execution_time: float
    unavailable_documents_count: Optional[int] = 0
    unavailable_documents: Optional[List[str]] = []

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
                llm_model=f"{provider}_model",
                selected_document_ids=chat_request.selected_document_ids
            )
            db.add(conversation)
            db.flush()

        # Validate selected documents and implement graceful degradation
        document_filter = None
        unavailable_count = 0
        unavailable_docs = []

        if conversation.selected_document_ids:
            # Query which selected documents still exist
            available_documents = db.query(Document).filter(
                Document.uuid.in_(conversation.selected_document_ids)
            ).all()

            available_doc_ids = [doc.uuid for doc in available_documents]

            # Identify unavailable documents
            unavailable_doc_ids = set(conversation.selected_document_ids) - set(available_doc_ids)

            if unavailable_doc_ids:
                # Get filenames of unavailable documents from the missing IDs
                unavailable_count = len(unavailable_doc_ids)
                unavailable_docs = list(unavailable_doc_ids)
                logger.warning(f"Conversation {conversation.uuid}: {unavailable_count} documents no longer available")

            # Build document filter with available documents only
            if available_doc_ids:
                document_filter = {'document_id': {'$in': available_doc_ids}}
                logger.info(f"Scoping conversation to {len(available_doc_ids)} documents")
            else:
                logger.warning(f"All selected documents deleted, falling back to all documents")

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=chat_request.message
        )
        db.add(user_message)
        db.flush()

        # Execute RAG with agents (with document filter if documents are selected)
        result = await orchestrator.execute_rag_with_agents(
            query=chat_request.message,
            provider=provider,
            explainability_level=current_user.explainability_level,
            include_grounding=chat_request.include_grounding,
            user_id=current_user.id,
            document_filter=document_filter
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
            low_confidence_warning=result.get('low_confidence_warning', False),
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

        db.flush()

        # Save token usage records
        token_usage_data = result.get('token_usage', {})
        if token_usage_data and token_usage_data.get('operations'):
            # Get model name based on provider
            model_name = settings.CUSTOM_LLM_MODEL if provider == "custom" else settings.OLLAMA_MODEL

            for operation in token_usage_data['operations']:
                op_tokens = operation.get('token_usage', {})
                if op_tokens.get('total_tokens', 0) > 0:
                    # Calculate cost (placeholder - adjust based on actual pricing)
                    cost = _calculate_token_cost(
                        provider=provider,
                        prompt_tokens=op_tokens.get('prompt_tokens', 0),
                        completion_tokens=op_tokens.get('completion_tokens', 0)
                    )

                    token_usage = TokenUsage(
                        user_id=current_user.id,
                        conversation_id=conversation.id,
                        message_id=assistant_message.id,
                        provider=provider,
                        model=model_name,
                        operation_type=operation['operation'],
                        prompt_tokens=op_tokens.get('prompt_tokens', 0),
                        completion_tokens=op_tokens.get('completion_tokens', 0),
                        total_tokens=op_tokens.get('total_tokens', 0),
                        embedding_tokens=op_tokens.get('embedding_tokens', 0),
                        estimated_cost=cost,
                        currency="USD"
                    )
                    db.add(token_usage)

        db.commit()

        logger.info(f"Chat message processed for user {current_user.username}")

        return ChatResponse(
            conversation_id=conversation.uuid,
            message_id=assistant_message.uuid,
            response=result.get('response', ''),
            sources=result.get('sources', []),
            confidence_score=result.get('confidence_score', 0.0),
            low_confidence_warning=result.get('low_confidence_warning', False),
            grounding=result.get('grounding'),
            explanation=result.get('explanation'),
            reasoning_chain=result.get('reasoning_chain', []),
            agents_involved=result.get('agents_involved', []),
            execution_time=result.get('execution_time', 0.0),
            unavailable_documents_count=unavailable_count,
            unavailable_documents=unavailable_docs
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
            'low_confidence_warning': msg.low_confidence_warning if msg.role == 'assistant' else False,
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

@router.get("/conversations/{conversation_id}/documents")
async def get_conversation_documents(
    conversation_id: str,
    current_user: User = Depends(require_permission("chat:history")),
    db: Session = Depends(get_db)
):
    """Get documents associated with a conversation"""

    conversation = db.query(Conversation).filter(
        Conversation.uuid == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if not conversation.selected_document_ids:
        return {
            'selected_document_ids': [],
            'documents': [],
            'available_count': 0,
            'unavailable_count': 0
        }

    # Fetch documents that still exist
    available_documents = db.query(Document).filter(
        Document.uuid.in_(conversation.selected_document_ids)
    ).all()

    available_doc_ids = [doc.uuid for doc in available_documents]
    unavailable_doc_ids = set(conversation.selected_document_ids) - set(available_doc_ids)

    return {
        'selected_document_ids': conversation.selected_document_ids,
        'documents': [
            {
                'id': doc.uuid,
                'filename': doc.filename,
                'title': doc.title,
                'file_type': doc.file_type,
                'scope': doc.scope or 'user',
                'uploaded_at': doc.uploaded_at.isoformat()
            }
            for doc in available_documents
        ],
        'available_count': len(available_documents),
        'unavailable_count': len(unavailable_doc_ids),
        'unavailable_document_ids': list(unavailable_doc_ids)
    }

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
                    llm_model=f"{provider}_model",
                    selected_document_ids=chat_request.selected_document_ids
                )
                db.add(conversation)
                db.flush()

            # Validate selected documents and implement graceful degradation
            document_filter = None
            unavailable_count = 0
            unavailable_docs = []

            if conversation.selected_document_ids:
                # Query which selected documents still exist
                available_documents = db.query(Document).filter(
                    Document.uuid.in_(conversation.selected_document_ids)
                ).all()

                available_doc_ids = [doc.uuid for doc in available_documents]

                # Identify unavailable documents
                unavailable_doc_ids = set(conversation.selected_document_ids) - set(available_doc_ids)

                if unavailable_doc_ids:
                    # Track unavailable documents for graceful degradation
                    unavailable_count = len(unavailable_doc_ids)
                    unavailable_docs = list(unavailable_doc_ids)
                    logger.warning(f"Conversation {conversation.uuid}: {unavailable_count} documents no longer available")

                # Build document filter with available documents only
                if available_doc_ids:
                    document_filter = {'document_id': {'$in': available_doc_ids}}
                    logger.info(f"Scoping conversation to {len(available_doc_ids)} documents")
                else:
                    logger.warning(f"All selected documents deleted, falling back to all documents")

            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content=chat_request.message
            )
            db.add(user_message)
            db.flush()

            yield f"event: conversation\ndata: {json.dumps({'conversation_id': conversation.uuid, 'unavailable_documents_count': unavailable_count, 'unavailable_documents': unavailable_docs})}\n\n"
            await asyncio.sleep(0.01)

            # Execute RAG with streaming agent status (with document filter if documents are selected)
            async for event in orchestrator.execute_rag_with_agents_stream(
                query=chat_request.message,
                provider=provider,
                explainability_level=current_user.explainability_level,
                include_grounding=chat_request.include_grounding,
                user_id=current_user.id,
                document_filter=document_filter
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
                    low_confidence_warning=assistant_message_data.get('low_confidence_warning', False),
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

                db.flush()

                # Save token usage records from streaming response
                token_usage_data = assistant_message_data.get('token_usage', {})
                if token_usage_data and token_usage_data.get('operations'):
                    # Get model name based on provider
                    model_name = settings.CUSTOM_LLM_MODEL if provider == "custom" else settings.OLLAMA_MODEL

                    for operation in token_usage_data['operations']:
                        op_tokens = operation.get('token_usage', {})
                        if op_tokens.get('total_tokens', 0) > 0:
                            # Calculate cost
                            cost = _calculate_token_cost(
                                provider=provider,
                                prompt_tokens=op_tokens.get('prompt_tokens', 0),
                                completion_tokens=op_tokens.get('completion_tokens', 0)
                            )

                            token_usage = TokenUsage(
                                user_id=current_user.id,
                                conversation_id=conversation.id,
                                message_id=assistant_message.id,
                                provider=provider,
                                model=model_name,
                                operation_type=operation['operation'],
                                prompt_tokens=op_tokens.get('prompt_tokens', 0),
                                completion_tokens=op_tokens.get('completion_tokens', 0),
                                total_tokens=op_tokens.get('total_tokens', 0),
                                embedding_tokens=op_tokens.get('embedding_tokens', 0),
                                estimated_cost=cost,
                                currency="USD"
                            )
                            db.add(token_usage)

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

@router.post("/message/direct", response_model=ChatResponse)
async def send_message_direct(
    chat_request: ChatRequest,
    current_user: User = Depends(require_permission("chat:use")),
    db: Session = Depends(get_db)
):
    """
    Send message directly to LLM bypassing RAG (knowledge base).
    Used for low-confidence follow-up queries when user wants direct LLM response.
    """
    import time
    from app.services.llm_service import llm_service

    try:
        # Validate provider
        if chat_request.provider not in ["custom", "ollama"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider must be 'custom' or 'ollama'"
            )

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

        # Get recent conversation history for context (last 5 messages)
        recent_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(6).all()  # 6 to include current user message

        recent_messages.reverse()  # Oldest to newest

        # Build conversation context
        conversation_history = []
        for msg in recent_messages[:-1]:  # Exclude the current user message
            conversation_history.append(f"{msg.role.capitalize()}: {msg.content}")

        # Build prompt with context
        if conversation_history:
            prompt = f"""Previous conversation context:
{chr(10).join(conversation_history[-5:])}

Current question: {chat_request.message}

Please provide a helpful, accurate response based on the question."""
        else:
            prompt = chat_request.message

        # Record start time
        start_time = time.time()

        # Call LLM directly (bypassing RAG)
        logger.info(f"Direct LLM query for user {current_user.username} (bypassing RAG)")
        llm_result = await llm_service.generate_response(
            prompt=prompt,
            provider=provider,
            system_message="You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user questions."
        )

        # Extract response and token usage
        response_content = llm_result.get('content', '')
        token_usage = llm_result.get('token_usage', {})

        execution_time = time.time() - start_time

        # Save assistant message (marked as direct LLM, no RAG)
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_content,
            retrieved_documents=[],  # No documents retrieved
            confidence_score=1.0,  # Max confidence for direct LLM
            low_confidence_warning=False,  # Not applicable for direct queries
            reasoning_chain=[{
                'step': 'direct_llm_query',
                'description': 'Response generated directly by LLM without knowledge base search',
                'bypass_rag': True
            }],
            sources=[],  # No sources from knowledge base
            grounding_evidence=None,  # No grounding check needed
            agents_involved=['DirectLLM']
        )
        db.add(assistant_message)
        db.flush()

        # Save agent log for direct query
        agent_log = AgentLog(
            message_id=assistant_message.id,
            agent_name='DirectLLM',
            agent_type='direct_llm',
            action='generate_response',
            input_data={'query': chat_request.message, 'bypass_rag': True},
            output_data={'response': response_content, 'execution_time': execution_time},
            execution_time=execution_time,
            status='success',
            reasoning='Direct LLM response without knowledge base search',
            confidence=1.0
        )
        db.add(agent_log)

        # Save token usage
        if token_usage.get('total_tokens', 0) > 0:
            model_name = settings.CUSTOM_LLM_MODEL if provider == "custom" else settings.OLLAMA_MODEL

            cost = _calculate_token_cost(
                provider=provider,
                prompt_tokens=token_usage.get('prompt_tokens', 0),
                completion_tokens=token_usage.get('completion_tokens', 0)
            )

            token_usage_record = TokenUsage(
                user_id=current_user.id,
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                provider=provider,
                model=model_name,
                operation_type='direct_llm_query',
                prompt_tokens=token_usage.get('prompt_tokens', 0),
                completion_tokens=token_usage.get('completion_tokens', 0),
                total_tokens=token_usage.get('total_tokens', 0),
                embedding_tokens=0,
                estimated_cost=cost,
                currency="USD"
            )
            db.add(token_usage_record)

        db.commit()

        logger.info(f"Direct LLM query completed in {execution_time:.2f}s")

        return ChatResponse(
            conversation_id=conversation.uuid,
            message_id=assistant_message.uuid,
            response=response_content,
            sources=[],  # No sources for direct LLM
            confidence_score=1.0,
            low_confidence_warning=False,
            grounding=None,
            explanation="Response generated directly by LLM without knowledge base search",
            reasoning_chain=[{
                'step': 'direct_llm_query',
                'description': 'Direct LLM response bypassing RAG system',
                'bypass_rag': True
            }],
            agents_involved=['DirectLLM'],
            execution_time=execution_time
        )

    except Exception as e:
        logger.error(f"Direct LLM query failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process direct LLM query: {str(e)}"
        )
