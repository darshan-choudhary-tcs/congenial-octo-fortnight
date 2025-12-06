"""
Reports API endpoints for energy analysis and reporting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from loguru import logger
import json

from app.database.db import get_db
from app.database.models import User, Profile
from app.auth.security import get_current_active_user, require_permission
from app.agents.orchestrator import orchestrator
from app.services.report_indexing_service import report_indexing_service

router = APIRouter()


class ReportConfigWeights(BaseModel):
    """Configurable weights for report generation"""
    energy_weights: Optional[Dict[str, float]] = None
    price_optimization_weights: Optional[Dict[str, float]] = None
    portfolio_decision_weights: Optional[Dict[str, float]] = None


class ReportRequest(BaseModel):
    """Request model for report generation"""
    provider: Optional[str] = "custom"  # LLM provider
    config_override: Optional[ReportConfigWeights] = None  # Optional weight overrides


class ReportConfigUpdate(BaseModel):
    """Model for updating report configuration"""
    energy_weights: Dict[str, float] = Field(
        ...,
        description="Weights for renewable energy sources (solar, wind, hydro)"
    )
    price_optimization_weights: Dict[str, float] = Field(
        ...,
        description="Weights for optimization criteria (cost, reliability, sustainability)"
    )
    portfolio_decision_weights: Dict[str, float] = Field(
        ...,
        description="Weights for portfolio decision (esg_score, budget_fit, technical_feasibility)"
    )
    confidence_threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    enable_fallback_options: Optional[bool] = True
    max_renewable_sources: Optional[int] = Field(4, ge=1, le=10)


class ReportConfigResponse(BaseModel):
    """Response model for report configuration"""
    config: Dict[str, Any]
    is_default: bool


class AgentResult(BaseModel):
    """Result from a single agent"""
    agent: str
    status: str
    confidence: float
    reasoning: str
    data: Dict[str, Any]


class ReportResponse(BaseModel):
    """Response model for complete report"""
    status: str
    report_sections: Dict[str, Any]
    overall_confidence: float
    reasoning_chain: List[Dict[str, Any]]
    execution_time: float
    agents_involved: List[str]


@router.get("/config", response_model=ReportConfigResponse)
async def get_report_config(
    current_user: User = Depends(require_permission("reports:view")),
    db: Session = Depends(get_db)
):
    """
    Get current report configuration for the user's profile
    """
    try:
        # Get user from company database (to get correct user_id for profile lookup)
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Get user profile using company database user_id
        profile = db.query(Profile).filter(Profile.user_id == company_user.id).first()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please complete your company profile setup in the Profile/Onboarding section before generating reports."
            )

        # Default configuration
        default_config = {
            "energy_weights": {
                "solar": 0.35,
                "wind": 0.35,
                "hydro": 0.30
            },
            "price_optimization_weights": {
                "cost": 0.35,
                "reliability": 0.35,
                "sustainability": 0.30
            },
            "portfolio_decision_weights": {
                "esg_score": 0.40,
                "budget_fit": 0.35,
                "technical_feasibility": 0.25
            },
            "confidence_threshold": 0.7,
            "enable_fallback_options": True,
            "max_renewable_sources": 4
        }

        # Check if profile has custom configuration
        if profile.report_config:
            try:
                custom_config = json.loads(profile.report_config) if isinstance(profile.report_config, str) else profile.report_config
                return {
                    "config": custom_config,
                    "is_default": False
                }
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in report_config for user {current_user.id}")

        return {
            "config": default_config,
            "is_default": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report configuration: {str(e)}"
        )


@router.put("/config", response_model=ReportConfigResponse)
async def update_report_config(
    config_update: ReportConfigUpdate,
    current_user: User = Depends(require_permission("reports:configure")),
    db: Session = Depends(get_db)
):
    """
    Update report configuration for the user's profile
    """
    try:
        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Get user profile
        profile = db.query(Profile).filter(Profile.user_id == company_user.id).first()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please complete profile setup first."
            )

        # Validate weight sums (should be close to 1.0)
        def validate_weights(weights: Dict[str, float], name: str):
            total = sum(weights.values())
            if not (0.95 <= total <= 1.05):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{name} weights must sum to approximately 1.0 (got {total:.2f})"
                )

        validate_weights(config_update.energy_weights, "Energy")
        validate_weights(config_update.price_optimization_weights, "Price optimization")
        validate_weights(config_update.portfolio_decision_weights, "Portfolio decision")

        # Build new configuration
        new_config = {
            "energy_weights": config_update.energy_weights,
            "price_optimization_weights": config_update.price_optimization_weights,
            "portfolio_decision_weights": config_update.portfolio_decision_weights,
            "confidence_threshold": config_update.confidence_threshold,
            "enable_fallback_options": config_update.enable_fallback_options,
            "max_renewable_sources": config_update.max_renewable_sources
        }

        # Update profile
        profile.report_config = json.dumps(new_config)
        db.commit()

        logger.info(f"Updated report config for user {current_user.id}")

        return {
            "config": new_config,
            "is_default": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating report config: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update report configuration: {str(e)}"
        )


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    current_user: User = Depends(require_permission("reports:generate")),
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive energy report using multi-agent system
    """
    try:
        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Get user profile
        profile = db.query(Profile).filter(Profile.user_id == company_user.id).first()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please complete your company profile setup in the Profile/Onboarding section before generating reports."
            )

        logger.info(f"Generating energy report for user {current_user.username} (company user_id={company_user.id})")

        # Prepare custom config if provided
        custom_config = None
        if request.config_override:
            custom_config = {}
            if request.config_override.energy_weights:
                custom_config['energy_weights'] = request.config_override.energy_weights
            if request.config_override.price_optimization_weights:
                custom_config['price_optimization_weights'] = request.config_override.price_optimization_weights
            if request.config_override.portfolio_decision_weights:
                custom_config['portfolio_decision_weights'] = request.config_override.portfolio_decision_weights

        # Execute report generation with orchestrator
        report = await orchestrator.execute_energy_report(
            profile=profile,
            user_id=current_user.id,
            provider=request.provider,
            custom_config=custom_config
        )

        if report['status'] != 'completed':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {report.get('error', 'Unknown error')}"
            )

        logger.info(f"Energy report completed for user {current_user.id} in {report['execution_time']:.2f}s")

        return ReportResponse(
            status=report['status'],
            report_sections=report['report_sections'],
            overall_confidence=report['overall_confidence'],
            reasoning_chain=report['reasoning_chain'],
            execution_time=report['execution_time'],
            agents_involved=report['agents_involved']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )
    """
    Generate energy report with streaming progress updates
    """
    try:
        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Get user profile
        profile = db.query(Profile).filter(Profile.user_id == company_user.id).first()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please complete your company profile setup in the Profile/Onboarding section before generating reports."
            )

        logger.info(f"Starting streaming report generation for user {current_user.username} (company user_id={company_user.id})")

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please complete your company profile setup in the Profile/Onboarding section before generating reports."
            )

        logger.info(f"Starting streaming report generation for user {current_user.id}")

        # Prepare custom config
        custom_config = None
        if request.config_override:
            custom_config = {}
            if request.config_override.energy_weights:
                custom_config['energy_weights'] = request.config_override.energy_weights
            if request.config_override.price_optimization_weights:
                custom_config['price_optimization_weights'] = request.config_override.price_optimization_weights
            if request.config_override.portfolio_decision_weights:
                custom_config['portfolio_decision_weights'] = request.config_override.portfolio_decision_weights

        async def event_generator():
            """Generate server-sent events for real-time updates"""
            try:
                async for event in orchestrator.execute_energy_report_stream(
                    profile=profile,
                    user_id=current_user.id,
                    provider=request.provider,
                    custom_config=custom_config
                ):
                    yield f"data: {json.dumps(event)}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting streaming report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start report generation: {str(e)}"
        )


@router.get("/status")
async def get_report_status(
    current_user: User = Depends(require_permission("reports:view")),
    db: Session = Depends(get_db)
):
    """
    Check if user has necessary data for report generation
    """
    try:
        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            return {
                "ready": False,
                "missing": ["user"],
                "message": "User not found in company database"
            }

        profile = db.query(Profile).filter(Profile.user_id == company_user.id).first()

        if not profile:
            return {
                "ready": False,
                "missing": ["profile"],
                "message": "Profile setup required"
            }
        profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()

        if not profile:
            return {
                "ready": False,
                "missing": ["profile"],
                "message": "Profile setup required"
            }

        missing = []
        warnings = []

        # Check required fields
        if not profile.industry:
            missing.append("industry")
        if not profile.location:
            missing.append("location")
        if not profile.budget or profile.budget <= 0:
            missing.append("budget")

        # Check optional but recommended fields
        if not profile.historical_data_path:
            warnings.append("Historical consumption data not uploaded - analysis will be limited")
        if not profile.chroma_collection_name:
            warnings.append("No documents uploaded - recommendations may be generic")

        return {
            "ready": len(missing) == 0,
            "missing": missing,
            "warnings": warnings,
            "profile": {
                "industry": profile.industry,
                "location": profile.location,
                "budget": profile.budget,
                "sustainability_target_kp1": profile.sustainability_target_kp1,
                "sustainability_target_kp2": profile.sustainability_target_kp2,
                "has_historical_data": profile.historical_data_path is not None,
                "has_documents": profile.chroma_collection_name is not None
            }
        }

    except Exception as e:
        logger.error(f"Error checking report status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check report status: {str(e)}"
        )


# ===== SAVED REPORTS ENDPOINTS =====

class SaveReportRequest(BaseModel):
    """Request model for saving a report"""
    report_name: Optional[str] = None
    report_content: Dict[str, Any]
    profile_snapshot: Dict[str, Any]
    config_snapshot: Dict[str, Any]
    overall_confidence: float
    execution_time: float
    total_tokens: int = 0
    provider: Optional[str] = "custom"  # LLM provider for RAG indexing


class SavedReportSummary(BaseModel):
    """Summary model for saved report list"""
    id: int
    report_name: Optional[str]
    report_type: str
    overall_confidence: float
    execution_time: float
    created_at: str
    industry: str
    location: str


class SavedReportDetail(BaseModel):
    """Detailed model for saved report"""
    id: int
    report_name: Optional[str]
    report_type: str
    report_content: Dict[str, Any]
    profile_snapshot: Dict[str, Any]
    config_snapshot: Dict[str, Any]
    overall_confidence: float
    execution_time: float
    total_tokens: int
    created_at: str


@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_report(
    request: SaveReportRequest,
    current_user: User = Depends(require_permission("reports:save")),
    db: Session = Depends(get_db)
):
    """
    Save a generated report for later viewing
    """
    try:
        from app.database.models import SavedReport
        from datetime import datetime

        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Create saved report
        saved_report = SavedReport(
            user_id=company_user.id,
            report_name=request.report_name,
            report_type="energy_portfolio",
            report_content=request.report_content,
            profile_snapshot=request.profile_snapshot,
            config_snapshot=request.config_snapshot,
            overall_confidence=request.overall_confidence,
            execution_time=request.execution_time,
            total_tokens=request.total_tokens,
            created_at=datetime.utcnow()
        )

        db.add(saved_report)
        db.commit()
        db.refresh(saved_report)

        logger.info(f"Report saved successfully: ID={saved_report.id}, User={company_user.username}")

        # Index report content into RAG for conversational queries
        try:
            indexing_success = await report_indexing_service.index_report(
                report_id=saved_report.id,
                report_name=request.report_name or f"Report {saved_report.id}",
                report_content=request.report_content,
                profile_snapshot=request.profile_snapshot,
                user_id=company_user.id,
                provider=request.provider
            )
            if indexing_success:
                logger.info(f"Report {saved_report.id} indexed successfully for RAG")
            else:
                logger.warning(f"Report {saved_report.id} saved but indexing failed")
        except Exception as index_error:
            logger.error(f"Failed to index report {saved_report.id}: {index_error}")
            # Don't fail the save operation if indexing fails

        return {
            "success": True,
            "report_id": saved_report.id,
            "message": "Report saved successfully"
        }

    except Exception as e:
        logger.error(f"Error saving report: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save report: {str(e)}"
        )


@router.get("/saved", response_model=List[SavedReportSummary])
async def get_saved_reports(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_permission("reports:view_saved")),
    db: Session = Depends(get_db)
):
    """
    Get list of saved reports for the current user
    """
    try:
        from app.database.models import SavedReport

        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Query saved reports
        reports = db.query(SavedReport)\
            .filter(SavedReport.user_id == company_user.id)\
            .order_by(SavedReport.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

        # Format response
        result = []
        for report in reports:
            result.append({
                "id": report.id,
                "report_name": report.report_name,
                "report_type": report.report_type,
                "overall_confidence": report.overall_confidence,
                "execution_time": report.execution_time,
                "created_at": report.created_at.isoformat(),
                "industry": report.profile_snapshot.get('industry', 'N/A'),
                "location": report.profile_snapshot.get('location', 'N/A')
            })

        return result

    except Exception as e:
        logger.error(f"Error fetching saved reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch saved reports: {str(e)}"
        )


@router.get("/saved/{report_id}", response_model=SavedReportDetail)
async def get_saved_report(
    report_id: int,
    current_user: User = Depends(require_permission("reports:view_saved")),
    db: Session = Depends(get_db)
):
    """
    Get detailed view of a specific saved report
    """
    try:
        from app.database.models import SavedReport

        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Query saved report
        report = db.query(SavedReport)\
            .filter(SavedReport.id == report_id)\
            .filter(SavedReport.user_id == company_user.id)\
            .first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        return {
            "id": report.id,
            "report_name": report.report_name,
            "report_type": report.report_type,
            "report_content": report.report_content,
            "profile_snapshot": report.profile_snapshot,
            "config_snapshot": report.config_snapshot,
            "overall_confidence": report.overall_confidence,
            "execution_time": report.execution_time,
            "total_tokens": report.total_tokens,
            "created_at": report.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching saved report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch saved report: {str(e)}"
        )


@router.delete("/saved/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_report(
    report_id: int,
    current_user: User = Depends(require_permission("reports:save")),
    db: Session = Depends(get_db)
):
    """
    Delete a saved report
    """
    try:
        from app.database.models import SavedReport

        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Query saved report
        report = db.query(SavedReport)\
            .filter(SavedReport.id == report_id)\
            .filter(SavedReport.user_id == company_user.id)\
            .first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        db.delete(report)
        db.commit()

        logger.info(f"Report deleted: ID={report_id}, User={company_user.username}")

        # Remove report from RAG index
        try:
            await report_indexing_service.remove_report_from_index(
                report_id=report_id,
                user_id=company_user.id,
                provider="custom"  # Try both providers if needed
            )
            logger.info(f"Report {report_id} removed from RAG index")
        except Exception as index_error:
            logger.error(f"Failed to remove report {report_id} from index: {index_error}")
            # Don't fail the delete operation if index removal fails

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting saved report: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete saved report: {str(e)}"
        )


@router.post("/saved/{report_id}/generate-textual-version")
async def generate_textual_version(
    report_id: int,
    current_user: User = Depends(require_permission("reports:view")),
    db: Session = Depends(get_db)
):
    """
    Generate a full verbose textual version of the report using LLM.
    This creates a comprehensive narrative document without charts or UI elements.
    """
    try:
        from app.database.models import SavedReport
        from app.services.llm_service import llm_service
        from datetime import datetime

        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Query saved report
        report = db.query(SavedReport)\
            .filter(SavedReport.id == report_id)\
            .filter(SavedReport.user_id == company_user.id)\
            .first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        # Build comprehensive prompt for textual report generation
        report_content = report.report_content
        profile_snapshot = report.profile_snapshot

        # Extract key information from report sections
        availability_section = report_content.get("availability_agent", {})
        optimization_section = report_content.get("optimization_agent", {})
        portfolio_section = report_content.get("portfolio_agent", {})

        prompt = f"""Generate a comprehensive, verbose textual report for an Energy Portfolio Analysis.
This report is for {profile_snapshot.get('industry', 'N/A')} industry located in {profile_snapshot.get('location', 'N/A')}.

Budget: ${profile_snapshot.get('budget', 0):,.0f}
Sustainability Target: {profile_snapshot.get('sustainability_target_kp2', 0)}% renewable energy by {profile_snapshot.get('sustainability_target_kp1', 'N/A')}

Overall Confidence Score: {report.overall_confidence:.1%}

Create a FULL NARRATIVE REPORT with the following sections:

[EXECUTIVE SUMMARY]
Provide a comprehensive executive summary highlighting key findings, recommendations, and strategic implications.

[COMPANY PROFILE]
Detail the company's industry, location, current energy situation, budget constraints, and sustainability goals.

[RENEWABLE ENERGY AVAILABILITY ANALYSIS]
Based on this analysis:
{json.dumps(availability_section, indent=2)}

Provide a detailed narrative covering available renewable energy sources (solar, wind, hydro), capacity factors and reliability scores for each source, location-specific considerations and constraints, seasonal variations and expected performance, and technical feasibility assessment.

[PRICE OPTIMIZATION ANALYSIS]
Based on this analysis:
{json.dumps(optimization_section, indent=2)}

Provide comprehensive details on the optimized energy mix breakdown with percentages, cost analysis for each energy source (installation, operational, maintenance), total annual costs and cost per kWh, budget utilization and financial viability, trade-offs between cost, reliability, and sustainability, and return on investment projections.

[ENERGY PORTFOLIO RECOMMENDATION]
Based on this portfolio decision:
{json.dumps(portfolio_section, indent=2)}

Provide an in-depth discussion of the final recommended energy portfolio composition, ESG scores and sustainability metrics, alignment with target goals (renewable percentage, zero non-renewable timeline), year-by-year transition roadmap with milestones, technical implementation considerations, and risk factors and mitigation strategies.

[IMPLEMENTATION ROADMAP]
Detail the step-by-step implementation plan with phase-wise deployment strategy, timeline and key milestones, resource requirements, potential challenges and solutions, and success metrics and KPIs.

[CONCLUSION AND RECOMMENDATIONS]
Summarize key takeaways and actionable recommendations for stakeholders.

CRITICAL FORMATTING RULES:
- Write ONLY in plain text - NO markdown syntax whatsoever
- Do NOT use # for headers, ** for bold, * for italics, or any markdown formatting
- Use section titles in [BRACKETS] as shown above
- Write in full paragraphs with detailed explanations
- Use professional, business-appropriate language
- Include specific numbers, percentages, and data points in the text
- Use flowing narrative prose - no bullet points, no numbered lists
- Do NOT include charts, graphs, or visual elements
- Do NOT include tables or any structured formatting
- Write as if this is a formal business report document for printing
- Be comprehensive and verbose - aim for a thorough analysis
- Separate sections with blank lines only"""

        # Generate textual version using LLM
        logger.info(f"Generating textual version for report {report_id}")

        system_message = "You are an expert energy analyst creating comprehensive business reports. Write in a professional, detailed, narrative style suitable for executive review."

        response = await llm_service.generate_response(
            prompt=prompt,
            provider=company_user.preferred_llm or "custom",
            system_message=system_message
        )

        generated_text = response["content"]

        # Store textual version in report
        textual_version_data = {
            "generated_text": generated_text,
            "edited_text": None,  # Will be populated when user edits
            "generated_at": datetime.utcnow().isoformat(),
            "edited_at": None,
            "edit_count": 0
        }

        report.textual_version = textual_version_data
        db.commit()
        db.refresh(report)

        logger.info(f"Textual version generated for report {report_id}")

        return {
            "success": True,
            "textual_version": textual_version_data,
            "report_id": report_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating textual version: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate textual version: {str(e)}"
        )


@router.put("/saved/{report_id}/textual-version")
async def update_textual_version(
    report_id: int,
    edited_text: Dict[str, str],
    current_user: User = Depends(require_permission("reports:save")),
    db: Session = Depends(get_db)
):
    """
    Update the edited textual version of the report (HITL - Human-in-the-Loop).
    Saves user's reviewed and edited version.
    """
    try:
        from app.database.models import SavedReport
        from datetime import datetime

        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Query saved report
        report = db.query(SavedReport)\
            .filter(SavedReport.id == report_id)\
            .filter(SavedReport.user_id == company_user.id)\
            .first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        if not report.textual_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Textual version has not been generated yet"
            )

        # Update edited text
        textual_data = report.textual_version
        textual_data["edited_text"] = edited_text.get("text", "")
        textual_data["edited_at"] = datetime.utcnow().isoformat()
        textual_data["edit_count"] = textual_data.get("edit_count", 0) + 1

        report.textual_version = textual_data
        db.commit()
        db.refresh(report)

        logger.info(f"Textual version updated for report {report_id} by {company_user.username}")

        return {
            "success": True,
            "textual_version": textual_data,
            "report_id": report_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating textual version: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update textual version: {str(e)}"
        )


@router.get("/saved/{report_id}/download-text")
async def download_textual_version(
    report_id: int,
    current_user: User = Depends(require_permission("reports:view")),
    db: Session = Depends(get_db)
):
    """
    Download the textual version of the report as a text file.
    Returns the edited version if available, otherwise the generated version.
    """
    try:
        from app.database.models import SavedReport
        from fastapi.responses import Response

        # Get user from company database
        company_user = db.query(User).filter(User.username == current_user.username).first()
        if not company_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in company database."
            )

        # Query saved report
        report = db.query(SavedReport)\
            .filter(SavedReport.id == report_id)\
            .filter(SavedReport.user_id == company_user.id)\
            .first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        if not report.textual_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Textual version has not been generated yet"
            )

        textual_data = report.textual_version

        # Use edited version if available, otherwise use generated version
        text_content = textual_data.get("edited_text") or textual_data.get("generated_text", "")

        if not text_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No textual content available"
            )

        # Add header with metadata
        report_name = report.report_name or f"Energy Report {report_id}"
        header = f"""{'='*80}
{report_name.upper()}
{'='*80}

Company: {company_user.company or 'N/A'}
Generated: {report.created_at.strftime('%B %d, %Y at %I:%M %p')}
Confidence Score: {report.overall_confidence:.1%}
{'Reviewed and Edited by User' if textual_data.get('edited_text') else 'AI-Generated Version'}

{'='*80}

"""

        full_content = header + text_content

        # Generate filename
        filename = f"{report_name.replace(' ', '_')}_textual_report.txt"

        logger.info(f"Textual version downloaded for report {report_id} by {company_user.username}")

        return Response(
            content=full_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading textual version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download textual version: {str(e)}"
        )


# PDF export removed - now handled client-side in frontend
