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
from app.auth.security import require_role, get_password_hash
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
        roles = [role.name for role in user.roles]
        permissions = []
        for role in user.roles:
            permissions.extend([perm.name for perm in role.permissions])

        result.append(UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            roles=roles,
            permissions=list(set(permissions)),
            preferred_llm=user.preferred_llm,
            explainability_level=user.explainability_level
        ))

    return result

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

    roles = [role.name for role in user.roles]
    permissions = []
    for role in user.roles:
        permissions.extend([perm.name for perm in role.permissions])

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        roles=roles,
        permissions=list(set(permissions)),
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

    roles = [role.name for role in user.roles]
    permissions = []
    for role in user.roles:
        permissions.extend([perm.name for perm in role.permissions])

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        roles=roles,
        permissions=list(set(permissions)),
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

    from app.database.models import Document, Conversation, Message, AgentLog

    return {
        'total_users': db.query(User).count(),
        'active_users': db.query(User).filter(User.is_active == True).count(),
        'total_documents': db.query(Document).count(),
        'processed_documents': db.query(Document).filter(Document.is_processed == True).count(),
        'total_conversations': db.query(Conversation).count(),
        'total_messages': db.query(Message).count(),
        'total_agent_executions': db.query(AgentLog).count()
    }
