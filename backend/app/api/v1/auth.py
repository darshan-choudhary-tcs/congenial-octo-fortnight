"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from loguru import logger

from app.database.db import get_db, get_primary_db
from app.database.models import User, Role
from app.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    check_permission,
    format_user_response
)
from app.auth.schemas import (
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
    LoginRequest,
    ChangePasswordRequest,
    AdminSetupRequest,
    SetupCompleteResponse,
    ProfileResponse
)
from app.services.vector_store import vector_store_service
from app.config import settings
from app.database.models import Profile
from app.services.database_service import DatabaseService
from datetime import datetime
from fastapi import UploadFile, File, Form
from typing import Optional
import os
import shutil

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_primary_db)):
    """Register a new user"""

    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        company=user_data.company,
        hashed_password=get_password_hash(user_data.password),
        is_active=True
    )

    # Assign default authenticated_user role
    authenticated_user_role = db.query(Role).filter(Role.name == "authenticated_user").first()
    if authenticated_user_role:
        user.roles.append(authenticated_user_role)

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"New user registered: {user.username}")

    # Prepare response using helper
    user_data = format_user_response(user)
    return UserResponse(
        **user_data,
        created_at=user.created_at,
        preferred_llm=user.preferred_llm,
        explainability_level=user.explainability_level
    )

@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_primary_db)):
    """Login user and return JWT token with first-login flag"""

    # Find user
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    logger.info(f"User logged in: {user.username} (first_login: {user.is_first_login})")

    # Check if user is admin and needs setup
    user_roles = [role.name for role in user.roles]
    is_admin = "admin" in user_roles or "super_admin" in user_roles
    requires_setup = is_admin and user.is_first_login

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_first_login": user.is_first_login,
        "requires_setup": requires_setup
    }

@router.post("/token", response_model=Token)
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_primary_db)
):
    """OAuth2 compatible token login"""

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""

    user_data = format_user_response(current_user)
    return UserResponse(
        **user_data,
        created_at=current_user.created_at,
        preferred_llm=current_user.preferred_llm,
        explainability_level=current_user.explainability_level
    )

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""

    if user_update.email is not None:
        # Check if email is already taken
        existing = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = user_update.email

    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    if user_update.company is not None:
        current_user.company = user_update.company

    if user_update.preferred_llm is not None:
        if user_update.preferred_llm not in ["custom", "ollama"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="preferred_llm must be 'custom' or 'ollama'"
            )
        current_user.preferred_llm = user_update.preferred_llm

    if user_update.explainability_level is not None:
        if user_update.explainability_level not in ["basic", "detailed", "debug"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="explainability_level must be 'basic', 'detailed', or 'debug'"
            )
        current_user.explainability_level = user_update.explainability_level

    db.commit()
    db.refresh(current_user)

    logger.info(f"User updated: {current_user.username}")

    user_data = format_user_response(current_user)
    return UserResponse(
        **user_data,
        created_at=current_user.created_at,
        preferred_llm=current_user.preferred_llm,
        explainability_level=current_user.explainability_level
    )

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""

    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    logger.info(f"Password changed for user: {current_user.username}")

    return {"message": "Password changed successfully"}

@router.post("/complete-setup", response_model=SetupCompleteResponse)
async def complete_setup(
    industry: str = Form(...),
    location: str = Form(...),
    sustainability_target_kp1: int = Form(...),
    sustainability_target_kp2: float = Form(...),
    budget: float = Form(...),
    historical_data: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    primary_db: Session = Depends(get_primary_db)  # Use primary DB for user updates only
):
    """
    Complete first-time admin setup with company profile.
    Creates company-specific database and stores profile data in company database.
    """

    # Verify user is admin and hasn't completed setup
    user_roles = [role.name for role in current_user.roles]
    is_admin = "admin" in user_roles or "super_admin" in user_roles

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can complete setup"
        )

    if not current_user.is_first_login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup already completed"
        )

    # Validate industry
    valid_industries = ["ITeS", "Manufacturing", "Hospitality"]
    if industry not in valid_industries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Industry must be one of: {', '.join(valid_industries)}"
        )

    # Validate sustainability targets
    if sustainability_target_kp1 < 2025 or sustainability_target_kp1 > 2100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target year must be between 2025 and 2100"
        )

    if sustainability_target_kp2 < 0 or sustainability_target_kp2 > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Percentage must be between 0 and 100"
        )

    if budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget must be greater than 0"
        )

    logger.info(f"Starting setup for admin: {current_user.username}, company: {current_user.company}")

    try:
        # Handle historical data CSV upload
        historical_data_path = None
        if historical_data:
            # Validate file type
            if not historical_data.filename.endswith('.csv'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Historical data must be a CSV file"
                )

            # Save CSV file
            upload_dir = settings.UPLOAD_DIR
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, f"historical_{current_user.id}_{historical_data.filename}")
            with open(file_path, "wb") as f:
                shutil.copyfileobj(historical_data.file, f)

            historical_data_path = file_path
            logger.info(f"Historical data saved: {file_path}")

        # Prepare profile data for company database
        profile_data = {
            "industry": industry,
            "location": location,
            "sustainability_target_kp1": sustainability_target_kp1,
            "sustainability_target_kp2": sustainability_target_kp2,
            "budget": budget,
            "historical_data_path": historical_data_path
        }

        # Create company-specific database with profile
        logger.info(f"Creating company database for: {current_user.company}")

        admin_user_data = {
            "username": current_user.username,
            "email": current_user.email,
            "hashed_password": current_user.hashed_password,
            "full_name": current_user.full_name,
            "company": current_user.company
        }

        company_db_name = DatabaseService.create_company_database(
            company_name=current_user.company,
            admin_user_data=admin_user_data,
            profile_data=profile_data
        )

        logger.info(f"✓ Company database created: {company_db_name}")

        # Process historical data and renewable potential data for ChromaDB ingestion
        logger.info(f"Processing energy data for ChromaDB ingestion...")
        try:
            from app.database.db import get_session_for_db
            from app.api.v1.documents import process_profile_historical_data, process_renewable_potential_data

            company_session = get_session_for_db(company_db_name)
            total_chunks = 0

            try:
                # 1. Process historical consumption data if provided
                if historical_data_path:
                    logger.info(f"Processing historical consumption data...")
                    processing_result = await process_profile_historical_data(
                        file_path=historical_data_path,
                        user_id=current_user.id,
                        company_db=company_session,
                        provider=current_user.preferred_llm or "custom"
                    )

                    total_chunks += processing_result["chunk_count"]

                    logger.info(f"✓ Historical data processed: {processing_result['chunk_count']} chunks")
                    logger.info(f"  Renewable %: {processing_result['sustainability_metrics'].get('renewable_percentage', 'N/A')}")
                    logger.info(f"  Anomalies detected: {len(processing_result['anomalies'])}")
                    logger.info(f"  Optimization insights: {len(processing_result['optimization_insights'])}")

                # 2. Process renewable energy potential data (always available)
                logger.info(f"Processing renewable energy potential data...")
                renewable_result = await process_renewable_potential_data(
                    user_id=current_user.id,
                    company_db=company_session,
                    location=location,
                    provider=current_user.preferred_llm or "custom"
                )

                if renewable_result.get("chunk_count", 0) > 0:
                    total_chunks += renewable_result["chunk_count"]
                    logger.info(f"✓ Renewable potential data processed: {renewable_result['chunk_count']} chunks")
                    logger.info(f"  Location: {location}")
                    logger.info(f"  Data rows: {renewable_result.get('csv_rows', 'N/A')}")
                else:
                    logger.warning("Renewable potential data not found or empty")

                # Update profile with ChromaDB tracking info
                if total_chunks > 0:
                    profile = company_session.query(Profile).filter(Profile.user_id == 1).first()
                    if profile:
                        collection_name = vector_store_service.get_collection_name(
                            "company",
                            current_user.preferred_llm or "custom",
                            current_user.id
                        )
                        profile.chroma_collection_name = collection_name
                        profile.historical_data_processed_at = datetime.utcnow()
                        profile.historical_data_chunk_count = total_chunks

                    company_session.commit()
                    logger.info(f"✓ Total chunks in ChromaDB: {total_chunks}, collection: {collection_name}")

            except Exception as processing_error:
                company_session.rollback()
                logger.error(f"Energy data processing failed: {processing_error}")
                # Don't fail the entire setup, just log the error
                logger.warning("Setup will continue without complete energy data ingestion")
            finally:
                company_session.close()

        except Exception as import_error:
            logger.error(f"Failed to import processing functions: {import_error}")

        # Update user in primary database
        current_user.is_first_login = False
        current_user.setup_completed_at = datetime.utcnow()
        current_user.company_database_name = company_db_name

        primary_db.commit()

        # Retrieve profile from company database for response
        from app.database.db import get_session_for_db
        company_session = get_session_for_db(company_db_name)
        try:
            profile = company_session.query(Profile).filter(Profile.user_id == 1).first()  # Admin is first user in company DB
        finally:
            company_session.close()

        logger.info(f"✓ Setup completed for admin: {current_user.username}")

        # Return response
        return SetupCompleteResponse(
            message="Setup completed successfully! Your company database has been created.",
            profile=ProfileResponse(
                id=profile.id,
                user_id=profile.user_id,
                industry=profile.industry,
                location=profile.location,
                sustainability_target_kp1=profile.sustainability_target_kp1,
                sustainability_target_kp2=profile.sustainability_target_kp2,
                budget=profile.budget,
                historical_data_path=profile.historical_data_path,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            ),
            company_database=company_db_name
        )

    except Exception as e:
        primary_db.rollback()
        logger.error(f"Setup failed for {current_user.username}: {e}")

        # Clean up uploaded file if it exists
        if historical_data_path and os.path.exists(historical_data_path):
            os.remove(historical_data_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Setup failed: {str(e)}"
        )
