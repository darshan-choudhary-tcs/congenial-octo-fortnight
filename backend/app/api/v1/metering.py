"""
Token Usage Metering API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from app.database.db import get_db
from app.database.models import User, TokenUsage, Conversation, Message
from app.auth.security import get_current_active_user, require_permission, require_role

router = APIRouter()


# Pydantic Models
class TokenUsageResponse(BaseModel):
    """Individual token usage record"""
    id: int
    user_id: int
    conversation_id: Optional[int]
    message_id: Optional[int]
    provider: str
    model: str
    operation_type: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    embedding_tokens: int
    estimated_cost: float
    currency: str
    created_at: str

    class Config:
        from_attributes = True


class UserUsageStats(BaseModel):
    """Aggregated usage statistics for a user"""
    user_id: int
    username: str
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_embedding_tokens: int
    total_cost: float
    currency: str
    operation_breakdown: Dict[str, int]  # operation_type -> token count
    provider_breakdown: Dict[str, int]  # provider -> token count
    conversation_count: int
    message_count: int
    date_range: Dict[str, str]


class OverallUsageStats(BaseModel):
    """System-wide usage statistics"""
    total_users: int
    total_tokens: int
    total_cost: float
    currency: str
    provider_breakdown: Dict[str, Any]  # provider -> {tokens, cost, requests}
    operation_breakdown: Dict[str, int]  # operation_type -> token count
    top_users: List[Dict[str, Any]]  # Top 10 users by token usage
    date_range: Dict[str, str]
    daily_usage: List[Dict[str, Any]]  # Daily aggregated usage


class CostBreakdown(BaseModel):
    """Detailed cost breakdown"""
    total_cost: float
    currency: str
    by_provider: Dict[str, float]
    by_operation: Dict[str, float]
    by_user: List[Dict[str, Any]]
    period: str


class UsageFilters(BaseModel):
    """Filters for usage queries"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    provider: Optional[str] = None
    operation_type: Optional[str] = None
    conversation_id: Optional[str] = None


# Helper Functions
def _parse_date(date_str: Optional[str], default_days_ago: int = 30) -> datetime:
    """Parse date string or return default"""
    if date_str:
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass
    return datetime.utcnow() - timedelta(days=default_days_ago)


# API Endpoints
@router.get("/me/usage", response_model=UserUsageStats)
async def get_my_usage(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get token usage statistics for the current user

    Returns aggregated token usage, costs, and breakdowns by provider and operation type.
    """
    try:
        # Parse dates
        start_dt = _parse_date(start_date, 30)
        end_dt = _parse_date(end_date, 0)

        # Build query
        query = db.query(TokenUsage).filter(
            TokenUsage.user_id == current_user.id,
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        )

        if provider:
            query = query.filter(TokenUsage.provider == provider)
        if operation_type:
            query = query.filter(TokenUsage.operation_type == operation_type)

        usage_records = query.all()

        # Aggregate statistics
        total_tokens = sum(r.total_tokens for r in usage_records)
        total_prompt_tokens = sum(r.prompt_tokens for r in usage_records)
        total_completion_tokens = sum(r.completion_tokens for r in usage_records)
        total_embedding_tokens = sum(r.embedding_tokens for r in usage_records)
        total_cost = sum(r.estimated_cost for r in usage_records)

        # Operation breakdown
        operation_breakdown = {}
        for record in usage_records:
            op = record.operation_type
            operation_breakdown[op] = operation_breakdown.get(op, 0) + record.total_tokens

        # Provider breakdown
        provider_breakdown = {}
        for record in usage_records:
            prov = record.provider
            provider_breakdown[prov] = provider_breakdown.get(prov, 0) + record.total_tokens

        # Count unique conversations and messages
        conversation_count = db.query(func.count(func.distinct(TokenUsage.conversation_id))).filter(
            TokenUsage.user_id == current_user.id,
            TokenUsage.conversation_id.isnot(None),
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).scalar() or 0

        message_count = db.query(func.count(func.distinct(TokenUsage.message_id))).filter(
            TokenUsage.user_id == current_user.id,
            TokenUsage.message_id.isnot(None),
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).scalar() or 0

        return UserUsageStats(
            user_id=current_user.id,
            username=current_user.username,
            total_tokens=total_tokens,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_embedding_tokens=total_embedding_tokens,
            total_cost=round(total_cost, 4),
            currency="USD",
            operation_breakdown=operation_breakdown,
            provider_breakdown=provider_breakdown,
            conversation_count=conversation_count,
            message_count=message_count,
            date_range={
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Failed to get user usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage statistics: {str(e)}"
        )


@router.get("/users/{user_id}/usage", response_model=UserUsageStats)
async def get_user_usage(
    user_id: int,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Get token usage statistics for a specific user (admin only)

    Provides detailed usage analytics for any user in the system.
    """
    try:
        # Get target user
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Parse dates
        start_dt = _parse_date(start_date, 30)
        end_dt = _parse_date(end_date, 0)

        # Build query
        query = db.query(TokenUsage).filter(
            TokenUsage.user_id == user_id,
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        )

        if provider:
            query = query.filter(TokenUsage.provider == provider)
        if operation_type:
            query = query.filter(TokenUsage.operation_type == operation_type)

        usage_records = query.all()

        # Aggregate statistics
        total_tokens = sum(r.total_tokens for r in usage_records)
        total_prompt_tokens = sum(r.prompt_tokens for r in usage_records)
        total_completion_tokens = sum(r.completion_tokens for r in usage_records)
        total_embedding_tokens = sum(r.embedding_tokens for r in usage_records)
        total_cost = sum(r.estimated_cost for r in usage_records)

        # Operation breakdown
        operation_breakdown = {}
        for record in usage_records:
            op = record.operation_type
            operation_breakdown[op] = operation_breakdown.get(op, 0) + record.total_tokens

        # Provider breakdown
        provider_breakdown = {}
        for record in usage_records:
            prov = record.provider
            provider_breakdown[prov] = provider_breakdown.get(prov, 0) + record.total_tokens

        # Count unique conversations and messages
        conversation_count = db.query(func.count(func.distinct(TokenUsage.conversation_id))).filter(
            TokenUsage.user_id == user_id,
            TokenUsage.conversation_id.isnot(None),
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).scalar() or 0

        message_count = db.query(func.count(func.distinct(TokenUsage.message_id))).filter(
            TokenUsage.user_id == user_id,
            TokenUsage.message_id.isnot(None),
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).scalar() or 0

        return UserUsageStats(
            user_id=target_user.id,
            username=target_user.username,
            total_tokens=total_tokens,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_embedding_tokens=total_embedding_tokens,
            total_cost=round(total_cost, 4),
            currency="USD",
            operation_breakdown=operation_breakdown,
            provider_breakdown=provider_breakdown,
            conversation_count=conversation_count,
            message_count=message_count,
            date_range={
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage statistics: {str(e)}"
        )


@router.get("/overall", response_model=OverallUsageStats)
async def get_overall_usage(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Get system-wide token usage statistics (admin only)

    Provides comprehensive usage analytics across all users and operations.
    """
    try:
        # Parse dates
        start_dt = _parse_date(start_date, 30)
        end_dt = _parse_date(end_date, 0)

        # Get all usage records in date range
        usage_records = db.query(TokenUsage).filter(
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).all()

        # Aggregate statistics
        total_tokens = sum(r.total_tokens for r in usage_records)
        total_cost = sum(r.estimated_cost for r in usage_records)

        # Provider breakdown with detailed stats
        provider_breakdown = {}
        for record in usage_records:
            prov = record.provider
            if prov not in provider_breakdown:
                provider_breakdown[prov] = {
                    "tokens": 0,
                    "cost": 0.0,
                    "requests": 0
                }
            provider_breakdown[prov]["tokens"] += record.total_tokens
            provider_breakdown[prov]["cost"] += record.estimated_cost
            provider_breakdown[prov]["requests"] += 1

        # Round costs
        for prov in provider_breakdown:
            provider_breakdown[prov]["cost"] = round(provider_breakdown[prov]["cost"], 4)

        # Operation breakdown
        operation_breakdown = {}
        for record in usage_records:
            op = record.operation_type
            operation_breakdown[op] = operation_breakdown.get(op, 0) + record.total_tokens

        # Top users by token usage
        user_usage = db.query(
            TokenUsage.user_id,
            User.username,
            func.sum(TokenUsage.total_tokens).label('total_tokens'),
            func.sum(TokenUsage.estimated_cost).label('total_cost')
        ).join(User, TokenUsage.user_id == User.id).filter(
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).group_by(TokenUsage.user_id, User.username).order_by(
            func.sum(TokenUsage.total_tokens).desc()
        ).limit(10).all()

        top_users = [
            {
                "user_id": u.user_id,
                "username": u.username,
                "total_tokens": u.total_tokens,
                "total_cost": round(u.total_cost, 4)
            }
            for u in user_usage
        ]

        # Daily usage aggregation
        daily_usage_query = db.query(
            func.date(TokenUsage.created_at).label('date'),
            func.sum(TokenUsage.total_tokens).label('tokens'),
            func.sum(TokenUsage.estimated_cost).label('cost'),
            func.count(TokenUsage.id).label('requests')
        ).filter(
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).group_by(func.date(TokenUsage.created_at)).order_by(
            func.date(TokenUsage.created_at)
        ).all()

        daily_usage = [
            {
                "date": str(d.date),
                "tokens": d.tokens,
                "cost": round(d.cost, 4),
                "requests": d.requests
            }
            for d in daily_usage_query
        ]

        # Count unique users
        total_users = db.query(func.count(func.distinct(TokenUsage.user_id))).filter(
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).scalar() or 0

        return OverallUsageStats(
            total_users=total_users,
            total_tokens=total_tokens,
            total_cost=round(total_cost, 4),
            currency="USD",
            provider_breakdown=provider_breakdown,
            operation_breakdown=operation_breakdown,
            top_users=top_users,
            date_range={
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            },
            daily_usage=daily_usage
        )

    except Exception as e:
        logger.error(f"Failed to get overall usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve overall usage statistics: {str(e)}"
        )


@router.get("/costs", response_model=CostBreakdown)
async def get_cost_breakdown(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Get detailed cost breakdown (admin only)

    Provides granular cost analysis by provider, operation, and user.
    """
    try:
        # Parse dates
        start_dt = _parse_date(start_date, 30)
        end_dt = _parse_date(end_date, 0)

        # Get all usage records in date range
        usage_records = db.query(TokenUsage).filter(
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).all()

        # Total cost
        total_cost = sum(r.estimated_cost for r in usage_records)

        # Cost by provider
        by_provider = {}
        for record in usage_records:
            prov = record.provider
            by_provider[prov] = by_provider.get(prov, 0.0) + record.estimated_cost

        # Round costs
        by_provider = {k: round(v, 4) for k, v in by_provider.items()}

        # Cost by operation
        by_operation = {}
        for record in usage_records:
            op = record.operation_type
            by_operation[op] = by_operation.get(op, 0.0) + record.estimated_cost

        # Round costs
        by_operation = {k: round(v, 4) for k, v in by_operation.items()}

        # Cost by user
        user_costs = db.query(
            TokenUsage.user_id,
            User.username,
            func.sum(TokenUsage.estimated_cost).label('total_cost'),
            func.sum(TokenUsage.total_tokens).label('total_tokens')
        ).join(User, TokenUsage.user_id == User.id).filter(
            TokenUsage.created_at >= start_dt,
            TokenUsage.created_at <= end_dt
        ).group_by(TokenUsage.user_id, User.username).order_by(
            func.sum(TokenUsage.estimated_cost).desc()
        ).limit(20).all()

        by_user = [
            {
                "user_id": u.user_id,
                "username": u.username,
                "cost": round(u.total_cost, 4),
                "tokens": u.total_tokens
            }
            for u in user_costs
        ]

        # Calculate period description
        days_diff = (end_dt - start_dt).days
        if days_diff <= 1:
            period = "Last 24 hours"
        elif days_diff <= 7:
            period = f"Last {days_diff} days"
        elif days_diff <= 30:
            period = "Last month"
        else:
            period = f"{days_diff} days"

        return CostBreakdown(
            total_cost=round(total_cost, 4),
            currency="USD",
            by_provider=by_provider,
            by_operation=by_operation,
            by_user=by_user,
            period=period
        )

    except Exception as e:
        logger.error(f"Failed to get cost breakdown: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cost breakdown: {str(e)}"
        )


@router.get("/history", response_model=List[TokenUsageResponse])
async def get_usage_history(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed token usage history for the current user

    Returns individual usage records with pagination support.
    """
    try:
        # Build query
        query = db.query(TokenUsage).filter(
            TokenUsage.user_id == current_user.id
        )

        if provider:
            query = query.filter(TokenUsage.provider == provider)
        if operation_type:
            query = query.filter(TokenUsage.operation_type == operation_type)

        # Get total count
        total = query.count()

        # Get paginated records
        records = query.order_by(TokenUsage.created_at.desc()).offset(offset).limit(limit).all()

        return [
            TokenUsageResponse(
                id=r.id,
                user_id=r.user_id,
                conversation_id=r.conversation_id,
                message_id=r.message_id,
                provider=r.provider,
                model=r.model,
                operation_type=r.operation_type,
                prompt_tokens=r.prompt_tokens,
                completion_tokens=r.completion_tokens,
                total_tokens=r.total_tokens,
                embedding_tokens=r.embedding_tokens,
                estimated_cost=r.estimated_cost,
                currency=r.currency,
                created_at=r.created_at.isoformat()
            )
            for r in records
        ]

    except Exception as e:
        logger.error(f"Failed to get usage history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage history: {str(e)}"
        )
