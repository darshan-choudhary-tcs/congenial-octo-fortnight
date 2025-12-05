"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Optional
import secrets
import string
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from loguru import logger

from app.config import settings
from app.database.db import get_db, get_primary_db, set_user_db_context, clear_user_db_context
from app.database.models import User

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def generate_secure_password(length: int = 16) -> str:
    """
    Generate a secure random password

    Args:
        length: Length of password (default: 16)

    Returns:
        Randomly generated secure password
    """
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]

    # Fill the rest with random characters from all sets
    all_chars = lowercase + uppercase + digits + special
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Shuffle to avoid predictable patterns
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)

    return ''.join(password_list)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_primary_db)  # Always use primary DB to fetch user
) -> User:
    """
    Get current authenticated user and set database context.

    This function:
    1. Always queries the primary database to get user information
    2. Sets the database context based on user's company database
    3. Super admins always use primary database
    4. Regular admins and users use their company database
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Set database context based on user role and company database
    user_roles = [role.name for role in user.roles]

    if "super_admin" in user_roles:
        # Super admins always use primary database
        clear_user_db_context()
    elif user.company_database_name:
        # Regular admins and users use their company database
        set_user_db_context(user.company_database_name)
        logger.info(f"User {user.username} connected to company database: {user.company_database_name}")
    else:
        # Fallback to primary database if no company database assigned
        clear_user_db_context()

    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission"""
    for role in user.roles:
        for perm in role.permissions:
            if perm.name == permission:
                return True
    return False

def require_permission(permission: str):
    """Dependency to require specific permission"""
    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        return current_user
    return permission_checker

def require_role(role_name: str):
    """Dependency to require specific role"""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        user_roles = [role.name for role in current_user.roles]
        if role_name not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role_name}"
            )
        return current_user
    return role_checker

def require_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to require super_admin role"""
    user_roles = [role.name for role in current_user.roles]
    if "super_admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required"
        )
    return current_user

def require_admin_or_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to require admin or super_admin role"""
    user_roles = [role.name for role in current_user.roles]
    if "super_admin" not in user_roles and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Super Admin access required"
        )
    return current_user

def format_user_response(user: User) -> dict:
    """Format user data with roles and permissions for API responses

    Args:
        user: User model instance

    Returns:
        Dictionary with user data, roles, and unique permissions
    """
    roles = [role.name for role in user.roles]
    permissions = list(set(
        perm.name
        for role in user.roles
        for perm in role.permissions
    ))

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "company": user.company,
        "is_active": user.is_active,
        "roles": roles,
        "permissions": permissions
    }
