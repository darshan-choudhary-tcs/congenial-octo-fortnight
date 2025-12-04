"""
Admin API endpoints for user and role management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from loguru import logger

from app.database.db import get_db
from app.database.models import User, Role, Permission
from app.auth.security import require_role, get_password_hash, format_user_response
from app.auth.schemas import UserResponse, RoleResponse

router = APIRouter()

class UserCreateAdmin(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    roles: List[str] = []

class UserUpdateAdmin(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""

    users = db.query(User).all()

    result = []
    for user in users:
        user_data = format_user_response(user)
        result.append(UserResponse(
            **user_data,
            created_at=user.created_at,
            preferred_llm=user.preferred_llm,
            explainability_level=user.explainability_level
        ))

    return result

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID (admin only)"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = format_user_response(user)
    return UserResponse(
        **user_data,
        created_at=user.created_at,
        preferred_llm=user.preferred_llm,
        explainability_level=user.explainability_level
    )

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_data: UserCreateAdmin,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""

    # Check duplicates
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        is_active=True
    )

    # Assign roles
    for role_name in user_data.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            user.roles.append(role)

    db.add(user)
    db.commit()
    db.refresh(user)

    user_data = format_user_response(user)
    return UserResponse(
        **user_data,
        created_at=user.created_at,
        preferred_llm=user.preferred_llm,
        explainability_level=user.explainability_level
    )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_admin(
    user_id: int,
    user_update: UserUpdateAdmin,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.email is not None:
        user.email = user_update.email
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    if user_update.roles is not None:
        user.roles = []
        for role_name in user_update.roles:
            role = db.query(Role).filter(Role.name == role_name).first()
            if role:
                user.roles.append(role)

    db.commit()
    db.refresh(user)

    user_data = format_user_response(user)
    return UserResponse(
        **user_data,
        created_at=user.created_at,
        preferred_llm=user.preferred_llm,
        explainability_level=user.explainability_level
    )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """List all roles (admin only)"""

    roles = db.query(Role).all()

    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[perm.name for perm in role.permissions]
        )
        for role in roles
    ]

@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Get system statistics (admin only)"""

    from app.database.models import Document, Conversation, Message, AgentLog, TokenUsage
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Calculate date ranges
    now = datetime.utcnow()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)

    # Token usage statistics
    total_tokens = db.query(func.sum(TokenUsage.total_tokens)).scalar() or 0
    total_cost = db.query(func.sum(TokenUsage.estimated_cost)).scalar() or 0.0

    tokens_last_30_days = db.query(func.sum(TokenUsage.total_tokens)).filter(
        TokenUsage.created_at >= last_30_days
    ).scalar() or 0

    tokens_last_7_days = db.query(func.sum(TokenUsage.total_tokens)).filter(
        TokenUsage.created_at >= last_7_days
    ).scalar() or 0

    cost_last_30_days = db.query(func.sum(TokenUsage.estimated_cost)).filter(
        TokenUsage.created_at >= last_30_days
    ).scalar() or 0.0

    # Provider breakdown
    provider_stats = db.query(
        TokenUsage.provider,
        func.sum(TokenUsage.total_tokens).label('tokens'),
        func.count(TokenUsage.id).label('requests')
    ).group_by(TokenUsage.provider).all()

    provider_breakdown = {
        stat.provider: {
            'tokens': stat.tokens,
            'requests': stat.requests
        }
        for stat in provider_stats
    }

    return {
        'total_users': db.query(User).count(),
        'active_users': db.query(User).filter(User.is_active == True).count(),
        'total_documents': db.query(Document).count(),
        'processed_documents': db.query(Document).filter(Document.is_processed == True).count(),
        'total_conversations': db.query(Conversation).count(),
        'total_messages': db.query(Message).count(),
        'total_agent_executions': db.query(AgentLog).count(),
        'token_usage': {
            'total_tokens': total_tokens,
            'total_cost': round(total_cost, 4),
            'tokens_last_30_days': tokens_last_30_days,
            'tokens_last_7_days': tokens_last_7_days,
            'cost_last_30_days': round(cost_last_30_days, 4),
            'provider_breakdown': provider_breakdown,
            'currency': 'USD'
        }
    }

def mask_api_key(key: str) -> str:
    """Mask API key for security - show first 3 and last 3 characters"""
    if not key or len(key) < 8:
        return "***********"
    return f"{key[:3]}...{key[-3:]}"

@router.get("/llm-config")
async def get_llm_config(
    current_user: User = Depends(require_role("admin"))
):
    """Get LLM and Vision configuration (admin only) with sensitive values masked"""

    from app.config import settings
    from app.services.llm_service import llm_service
    from app.services.vision_service import vision_service

    # Get vision provider availability
    vision_status = vision_service.check_provider_availability()

    return {
        "llm": {
            "custom_base_url": settings.CUSTOM_LLM_BASE_URL,
            "custom_model": settings.CUSTOM_LLM_MODEL,
            "custom_api_key": mask_api_key(settings.CUSTOM_LLM_API_KEY),
            "custom_embedding_model": settings.CUSTOM_EMBEDDING_MODEL,
            "ollama_base_url": settings.OLLAMA_BASE_URL,
            "ollama_model": settings.OLLAMA_MODEL,
            "ollama_embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
        },
        "vision": {
            "custom_vision_model": settings.CUSTOM_VISION_MODEL,
            "custom_vision_base_url": settings.CUSTOM_LLM_BASE_URL,
            "custom_vision_timeout": 180,
            "ollama_vision_model": settings.OLLAMA_VISION_MODEL,
            "ollama_vision_base_url": settings.OLLAMA_BASE_URL,
            "ollama_vision_timeout": 300,
        },
        "ocr": {
            "supported_formats": settings.OCR_SUPPORTED_FORMATS,
            "max_file_size": settings.OCR_MAX_FILE_SIZE,
            "max_file_size_mb": round(settings.OCR_MAX_FILE_SIZE / (1024 * 1024), 2),
            "image_max_dimension": settings.OCR_IMAGE_MAX_DIMENSION,
            "confidence_threshold": settings.OCR_CONFIDENCE_THRESHOLD,
            "enable_preprocessing": settings.OCR_ENABLE_PREPROCESSING,
            "pdf_dpi": settings.OCR_PDF_DPI,
        },
        "agent": {
            "temperature": settings.AGENT_TEMPERATURE,
            "max_iterations": settings.MAX_AGENT_ITERATIONS,
            "enable_memory": settings.ENABLE_AGENT_MEMORY,
        },
        "rag": {
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "max_retrieval_docs": settings.MAX_RETRIEVAL_DOCS,
            "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        },
        "explainability": {
            "explainability_level": settings.EXPLAINABILITY_LEVEL,
            "enable_confidence_scoring": settings.ENABLE_CONFIDENCE_SCORING,
            "enable_source_attribution": settings.ENABLE_SOURCE_ATTRIBUTION,
            "enable_reasoning_chains": settings.ENABLE_REASONING_CHAINS,
        },
        "provider_status": {
            "custom_available": llm_service.custom_client is not None,
            "ollama_available": llm_service.ollama_client is not None,
            "custom_vision_available": vision_status["custom_vision_available"],
            "ollama_vision_available": vision_status["ollama_vision_available"],
        }
    }
