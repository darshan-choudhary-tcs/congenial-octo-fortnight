"""
Utilities API endpoints
Provides utility functions like PII scrubbing
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import scrubadub

from app.auth.security import get_current_active_user
from app.database.models import User

router = APIRouter()

class PIIRequest(BaseModel):
    text: str
    locale: Optional[str] = "en_US"

class PIIResponse(BaseModel):
    original_text: str
    scrubbed_text: str
    detections: int

@router.post("/scrub-pii", response_model=PIIResponse)
async def scrub_pii(
    request: PIIRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Scrub PII (Personally Identifiable Information) from text
    Uses scrubadub library to detect and mask sensitive information
    """
    try:
        # Initialize scrubber with detectors
        scrubber = scrubadub.Scrubber()

        # Add additional detectors if needed
        # scrubber.add_detector(scrubadub.detectors.EmailDetector)
        # scrubber.add_detector(scrubadub.detectors.PhoneDetector)

        # Scrub the text (locale not needed in scrubadub 2.0)
        scrubbed_text = scrubber.clean(request.text)

        # Count detections
        filth_list = list(scrubber.iter_filth(request.text))
        detections_count = len(filth_list)

        return PIIResponse(
            original_text=request.text,
            scrubbed_text=scrubbed_text,
            detections=detections_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scrubbing PII: {str(e)}"
        )

@router.post("/scrub-pii-advanced", response_model=PIIResponse)
async def scrub_pii_advanced(
    request: PIIRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Advanced PII scrubbing with custom patterns
    """
    try:
        # Initialize scrubber with additional detectors
        scrubber = scrubadub.Scrubber()

        # Try to add SpaCy detector if available
        try:
            import scrubadub.detectors.spacy
            scrubber.add_detector(scrubadub.detectors.spacy.SpacyEntityDetector)
        except (ImportError, AttributeError):
            pass  # SpaCy detector not available

        # Scrub the text (locale not needed in scrubadub 2.0)
        scrubbed_text = scrubber.clean(request.text)

        # Count detections
        filth_list = list(scrubber.iter_filth(request.text))
        detections_count = len(filth_list)

        return PIIResponse(
            original_text=request.text,
            scrubbed_text=scrubbed_text,
            detections=detections_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scrubbing PII: {str(e)}"
        )
