"""
Sentiment Analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import uuid
from datetime import datetime
from loguru import logger
import pandas as pd

from app.database.db import get_db
from app.database.models import User, SentimentAnalysisResult
from app.auth.security import get_current_active_user, require_permission
from app.services.sentiment_service import get_sentiment_service
from app.config import settings

router = APIRouter()


# Pydantic models
class TextAnalysisRequest(BaseModel):
    """Request model for single text sentiment analysis"""
    text: str


class TextAnalysisResponse(BaseModel):
    """Response model for text sentiment analysis"""
    text: str
    sentiment: str
    confidence: float
    error: Optional[str] = None


class CSVAnalysisRequest(BaseModel):
    """Request model for CSV column suggestions"""
    pass


class ColumnSuggestionsResponse(BaseModel):
    """Response model for column suggestions"""
    text_columns: List[str]
    numeric_columns: List[str]
    all_columns: List[str]


class SentimentAnalysisResultResponse(BaseModel):
    """Response model for sentiment analysis results"""
    id: int
    uuid: str
    input_type: str
    created_at: datetime
    completed_at: Optional[datetime]
    status: str
    
    # CSV specific
    original_filename: Optional[str]
    text_column: Optional[str]
    sentiment_column: Optional[str]
    confidence_column: Optional[str]
    
    # Results
    results: Optional[Dict[str, Any]]
    
    # Statistics
    total_rows: Optional[int]
    positive_count: Optional[int]
    negative_count: Optional[int]
    neutral_count: Optional[int]
    average_confidence: Optional[float]
    
    error_message: Optional[str]

    class Config:
        from_attributes = True


@router.post("/analyze-text", response_model=TextAnalysisResponse)
async def analyze_text(
    request: TextAnalysisRequest,
    current_user: User = Depends(require_permission("sentiment:analyze")),
    db: Session = Depends(get_db)
):
    """
    Analyze sentiment of a single text input.
    
    Args:
        request: Text analysis request with text field
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Sentiment analysis result with label and confidence
    """
    try:
        sentiment_service = get_sentiment_service()
        result = sentiment_service.analyze_text(request.text)
        
        # Save result to database
        db_result = SentimentAnalysisResult(
            user_id=current_user.id,
            input_type="text",
            text_input=request.text[:1000],  # Store first 1000 chars
            results=result,
            status="completed",
            completed_at=datetime.utcnow()
        )
        db.add(db_result)
        db.commit()
        
        return TextAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in text sentiment analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing text: {str(e)}"
        )


@router.post("/analyze-csv", response_model=SentimentAnalysisResultResponse)
async def analyze_csv(
    file: UploadFile = File(...),
    text_column: str = Form(...),
    sentiment_column: str = Form(default="sentiment"),
    confidence_column: str = Form(default="sentiment_confidence"),
    current_user: User = Depends(require_permission("sentiment:analyze")),
    db: Session = Depends(get_db)
):
    """
    Analyze sentiment for a CSV file column.
    
    Args:
        file: Uploaded CSV file
        text_column: Name of column containing text to analyze
        sentiment_column: Name for output sentiment column
        confidence_column: Name for output confidence column
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Sentiment analysis result with statistics and file paths
    """
    # Validate file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )
    
    # Create analysis record
    analysis_uuid = str(uuid.uuid4())
    db_result = SentimentAnalysisResult(
        uuid=analysis_uuid,
        user_id=current_user.id,
        input_type="csv",
        original_filename=file.filename,
        text_column=text_column,
        sentiment_column=sentiment_column,
        confidence_column=confidence_column,
        status="processing"
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    try:
        # Save uploaded file
        file_uuid = str(uuid.uuid4())
        upload_dir = Path(settings.UPLOAD_DIR) / "sentiment"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        input_path = upload_dir / f"{file_uuid}_input.csv"
        output_path = upload_dir / f"{file_uuid}_output.csv"
        
        # Save uploaded file
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process CSV
        sentiment_service = get_sentiment_service()
        result = sentiment_service.process_csv_file(
            input_path=str(input_path),
            output_path=str(output_path),
            text_column=text_column,
            output_sentiment_column=sentiment_column,
            output_confidence_column=confidence_column
        )
        
        if not result.get("success"):
            db_result.status = "failed"
            db_result.error_message = result.get("error", "Unknown error")
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Error processing CSV")
            )
        
        # Update database record with results
        stats = result.get("statistics", {})
        db_result.original_file_path = str(input_path)
        db_result.result_file_path = str(output_path)
        db_result.results = stats
        db_result.total_rows = stats.get("total_rows", 0)
        db_result.positive_count = stats.get("positive_count", 0)
        db_result.negative_count = stats.get("negative_count", 0)
        db_result.neutral_count = stats.get("neutral_count", 0)
        db_result.average_confidence = stats.get("average_confidence", 0.0)
        db_result.status = "completed"
        db_result.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_result)
        
        return SentimentAnalysisResultResponse.from_orm(db_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in CSV sentiment analysis: {e}")
        db_result.status = "failed"
        db_result.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing CSV: {str(e)}"
        )


@router.post("/get-columns", response_model=ColumnSuggestionsResponse)
async def get_csv_columns(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("sentiment:analyze")),
):
    """
    Get column suggestions from a CSV file.
    
    Args:
        file: Uploaded CSV file
        current_user: Current authenticated user
        
    Returns:
        Column suggestions with text and numeric columns
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )
    
    try:
        # Read CSV
        content = await file.read()
        from io import BytesIO
        df = pd.read_csv(BytesIO(content))
        
        # Get column suggestions
        sentiment_service = get_sentiment_service()
        suggestions = sentiment_service.get_column_suggestions(df)
        
        return ColumnSuggestionsResponse(**suggestions)
        
    except Exception as e:
        logger.error(f"Error reading CSV columns: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading CSV file: {str(e)}"
        )


@router.get("/results", response_model=List[SentimentAnalysisResultResponse])
async def get_results(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """
    Get sentiment analysis results for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        limit: Maximum number of results to return
        offset: Number of results to skip
        
    Returns:
        List of sentiment analysis results
    """
    results = db.query(SentimentAnalysisResult).filter(
        SentimentAnalysisResult.user_id == current_user.id
    ).order_by(
        SentimentAnalysisResult.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    return [SentimentAnalysisResultResponse.from_orm(r) for r in results]


@router.get("/results/{result_uuid}", response_model=SentimentAnalysisResultResponse)
async def get_result(
    result_uuid: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific sentiment analysis result.
    
    Args:
        result_uuid: UUID of the analysis result
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Sentiment analysis result
    """
    result = db.query(SentimentAnalysisResult).filter(
        SentimentAnalysisResult.uuid == result_uuid,
        SentimentAnalysisResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    return SentimentAnalysisResultResponse.from_orm(result)


@router.get("/export/{result_uuid}")
async def export_result(
    result_uuid: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download the result CSV file with sentiment analysis.
    
    Args:
        result_uuid: UUID of the analysis result
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CSV file with sentiment columns
    """
    result = db.query(SentimentAnalysisResult).filter(
        SentimentAnalysisResult.uuid == result_uuid,
        SentimentAnalysisResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    if not result.result_file_path or not os.path.exists(result.result_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result file not found"
        )
    
    # Generate filename
    original_name = result.original_filename or "sentiment_analysis"
    filename = f"{Path(original_name).stem}_sentiment.csv"
    
    return FileResponse(
        path=result.result_file_path,
        filename=filename,
        media_type="text/csv"
    )


@router.delete("/results/{result_uuid}")
async def delete_result(
    result_uuid: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a sentiment analysis result and associated files.
    
    Args:
        result_uuid: UUID of the analysis result
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    result = db.query(SentimentAnalysisResult).filter(
        SentimentAnalysisResult.uuid == result_uuid,
        SentimentAnalysisResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    # Delete files
    try:
        if result.original_file_path and os.path.exists(result.original_file_path):
            os.remove(result.original_file_path)
        if result.result_file_path and os.path.exists(result.result_file_path):
            os.remove(result.result_file_path)
    except Exception as e:
        logger.warning(f"Error deleting files: {e}")
    
    # Delete database record
    db.delete(result)
    db.commit()
    
    return {"message": "Result deleted successfully"}
