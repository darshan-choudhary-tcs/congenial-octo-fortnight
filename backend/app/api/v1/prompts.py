"""
Prompts API endpoints for managing and accessing the prompt library.

This module provides CRUD operations for prompts:
- Read access to all 30 built-in prompts
- Create, update, and delete custom runtime prompts
- Test prompts with variable substitution
- Usage statistics and metadata

All endpoints require super_admin role for security.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database.models import User
from app.auth.security import require_role
from app.prompts import get_prompt_library

router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class PromptResponse(BaseModel):
    """Full prompt details including metadata"""
    name: str = Field(..., description="Unique prompt identifier")
    category: str = Field(..., description="Prompt category (agent, rag, llm_service, vision, chat, system)")
    description: str = Field(..., description="Human-readable description")
    template: str = Field(..., description="Prompt template with {variables}")
    variables: List[str] = Field(..., description="Required variable names for substitution")
    version: str = Field(..., description="Version string")
    output_format: str = Field(..., description="Expected output format")
    purpose: str = Field(..., description="Purpose and use case")
    examples: List[str] = Field(default_factory=list, description="Usage examples")
    is_custom: bool = Field(..., description="Whether this is a custom runtime prompt")
    usage_count: int = Field(..., description="Number of times prompt has been used")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "research_analysis",
                "category": "agent",
                "description": "Research analysis with specific focus",
                "template": "Analyze the following query: {query}\n\nContext: {context}",
                "variables": ["query", "context"],
                "version": "1.0.0",
                "output_format": "structured_text",
                "purpose": "In-depth research and analysis",
                "examples": [],
                "is_custom": False,
                "usage_count": 42,
                "created_at": "2025-01-01T00:00:00"
            }
        }


class PromptListResponse(BaseModel):
    """List of prompts with summary information"""
    prompts: List[PromptResponse] = Field(..., description="List of prompt details")
    total: int = Field(..., description="Total number of prompts")
    categories: List[str] = Field(..., description="Available categories")
    filtered_category: Optional[str] = Field(None, description="Category filter applied (if any)")

    class Config:
        json_schema_extra = {
            "example": {
                "prompts": [],
                "total": 30,
                "categories": ["agent", "rag", "llm_service", "vision", "chat", "system"],
                "filtered_category": "agent"
            }
        }


class PromptCreate(BaseModel):
    """Schema for creating custom prompts"""
    name: str = Field(..., description="Unique prompt identifier (no spaces)", min_length=1, max_length=100)
    template: str = Field(..., description="Prompt template with {variables}", min_length=1)
    category: str = Field(..., description="Prompt category")
    description: str = Field(..., description="Human-readable description", min_length=1)
    variables: List[str] = Field(default_factory=list, description="Required variable names")
    output_format: str = Field(default="text", description="Expected output format")
    purpose: Optional[str] = Field(None, description="Purpose and use case")
    examples: List[str] = Field(default_factory=list, description="Usage examples")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "custom_analysis",
                "template": "Analyze {topic} with focus on {aspect}",
                "category": "agent",
                "description": "Custom analysis prompt",
                "variables": ["topic", "aspect"],
                "output_format": "text",
                "purpose": "Custom business analysis",
                "examples": []
            }
        }


class PromptUpdate(BaseModel):
    """Schema for updating custom prompts (all fields optional)"""
    template: Optional[str] = Field(None, description="Updated prompt template")
    category: Optional[str] = Field(None, description="Updated category")
    description: Optional[str] = Field(None, description="Updated description")
    variables: Optional[List[str]] = Field(None, description="Updated variable list")
    output_format: Optional[str] = Field(None, description="Updated output format")
    purpose: Optional[str] = Field(None, description="Updated purpose")
    examples: Optional[List[str]] = Field(None, description="Updated examples")

    class Config:
        json_schema_extra = {
            "example": {
                "template": "Updated template with {new_variable}",
                "description": "Updated description"
            }
        }


class PromptTestRequest(BaseModel):
    """Request schema for testing prompt variable substitution"""
    variables: Dict[str, str] = Field(..., description="Variable key-value pairs for substitution")

    class Config:
        json_schema_extra = {
            "example": {
                "variables": {
                    "query": "What is AI?",
                    "context": "General information about artificial intelligence"
                }
            }
        }


class PromptTestResponse(BaseModel):
    """Response schema for prompt testing"""
    formatted_prompt: str = Field(..., description="Prompt after variable substitution")
    variables_used: Dict[str, str] = Field(..., description="Variables that were substituted")
    template: str = Field(..., description="Original template")
    missing_variables: List[str] = Field(default_factory=list, description="Required variables that were not provided")

    class Config:
        json_schema_extra = {
            "example": {
                "formatted_prompt": "Analyze the following query: What is AI?\n\nContext: General information...",
                "variables_used": {
                    "query": "What is AI?",
                    "context": "General information..."
                },
                "template": "Analyze the following query: {query}\n\nContext: {context}",
                "missing_variables": []
            }
        }


class CategoryResponse(BaseModel):
    """Response schema for categories"""
    categories: List[str] = Field(..., description="Available prompt categories")
    count_by_category: Dict[str, int] = Field(..., description="Number of prompts per category")

    class Config:
        json_schema_extra = {
            "example": {
                "categories": ["agent", "rag", "llm_service", "vision", "chat", "system"],
                "count_by_category": {
                    "agent": 7,
                    "rag": 3,
                    "llm_service": 4,
                    "vision": 2,
                    "chat": 2,
                    "system": 12
                }
            }
        }


class StatsResponse(BaseModel):
    """Response schema for usage statistics"""
    total_prompts: int = Field(..., description="Total number of prompts")
    custom_prompts: int = Field(..., description="Number of custom prompts")
    built_in_prompts: int = Field(..., description="Number of built-in prompts")
    total_usage: int = Field(..., description="Sum of all usage counts")
    most_used: List[Dict[str, Any]] = Field(..., description="Top 5 most used prompts")
    by_category: Dict[str, int] = Field(..., description="Prompt count by category")

    class Config:
        json_schema_extra = {
            "example": {
                "total_prompts": 30,
                "custom_prompts": 0,
                "built_in_prompts": 30,
                "total_usage": 1250,
                "most_used": [
                    {"name": "rag_assistant_basic", "usage_count": 500}
                ],
                "by_category": {
                    "agent": 7,
                    "rag": 3
                }
            }
        }


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str = Field(..., description="Status or informational message")
    detail: Optional[str] = Field(None, description="Additional details")


# ============================================================================
# Helper Functions
# ============================================================================

def _is_built_in_prompt(name: str) -> bool:
    """Check if a prompt is built-in (from templates.py)"""
    # Built-in prompts are those defined in templates.py
    # Custom prompts are registered at runtime
    prompt_lib = get_prompt_library()

    # List of all 30 built-in prompt names
    built_in_prompts = {
        # System prompts (12)
        'research_analyst', 'data_analyst', 'transparency_expert', 'fact_checker',
        'document_analyst', 'keyword_extractor', 'document_classifier', 'content_type_classifier',
        'helpful_assistant', 'rag_assistant_basic', 'rag_assistant_detailed', 'rag_assistant_debug',
        # Agent prompts (7)
        'research_analysis', 'general_analysis', 'comparative_analysis', 'trend_analysis',
        'explanation_basic', 'explanation_detailed', 'explanation_debug',
        # RAG prompts (3)
        'rag_generation_with_sources', 'rag_generation_simple', 'grounding_verification',
        # LLM Service prompts (4)
        'document_summarization', 'keyword_extraction', 'topic_classification', 'content_type_determination',
        # Vision prompts (2)
        'ocr_extraction', 'image_analysis',
        # Chat prompts (2)
        'direct_llm_with_history', 'direct_llm_simple'
    }

    return name in built_in_prompts


def _convert_metadata_to_response(name: str, metadata: Any) -> PromptResponse:
    """Convert PromptMetadata to PromptResponse"""
    prompt_lib = get_prompt_library()

    # Get the template from the correct location
    template = ""
    if name in prompt_lib.custom_prompts:
        template = prompt_lib.custom_prompts[name]["template"]
    elif name in prompt_lib.prompts:
        template = prompt_lib.prompts[name]["template"]

    return PromptResponse(
        name=metadata.name,
        category=metadata.category,
        description=metadata.description,
        template=template,
        variables=metadata.variables,
        version=metadata.version,
        output_format=metadata.output_format,
        purpose=metadata.purpose,
        examples=metadata.examples,
        is_custom=not _is_built_in_prompt(name),
        usage_count=metadata.usage_count,
        created_at=metadata.created_at.isoformat()
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=PromptListResponse)
async def list_prompts(
    category: Optional[str] = Query(None, description="Filter by category (agent, rag, llm_service, vision, chat, system)"),
    current_user: User = Depends(require_role("super_admin"))
):
    """
    List all prompts with optional category filter.

    Returns all 30 built-in prompts plus any custom runtime prompts.
    Requires super_admin role.
    """
    prompt_lib = get_prompt_library()

    # Get all prompts
    all_prompts = prompt_lib.list_prompts(category=category)

    # Convert to response format
    prompt_responses = [
        _convert_metadata_to_response(name, metadata)
        for name, metadata in all_prompts.items()
    ]

    # Get all available categories
    all_categories_dict = prompt_lib.list_prompts()
    categories = sorted(set(meta.category for meta in all_categories_dict.values()))

    return PromptListResponse(
        prompts=prompt_responses,
        total=len(prompt_responses),
        categories=categories,
        filtered_category=category
    )


@router.get("/categories", response_model=CategoryResponse)
async def get_categories(
    current_user: User = Depends(require_role("super_admin"))
):
    """
    Get all available prompt categories with counts.

    Requires super_admin role.
    """
    prompt_lib = get_prompt_library()
    all_prompts = prompt_lib.list_prompts()

    # Count by category
    count_by_category: Dict[str, int] = {}
    for metadata in all_prompts.values():
        count_by_category[metadata.category] = count_by_category.get(metadata.category, 0) + 1

    categories = sorted(count_by_category.keys())

    return CategoryResponse(
        categories=categories,
        count_by_category=count_by_category
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    current_user: User = Depends(require_role("super_admin"))
):
    """
    Get usage statistics for all prompts.

    Requires super_admin role.
    """
    prompt_lib = get_prompt_library()
    usage_stats = prompt_lib.get_usage_stats()

    all_prompts = prompt_lib.list_prompts()

    # Count custom vs built-in
    custom_count = sum(1 for name in all_prompts.keys() if not _is_built_in_prompt(name))
    built_in_count = len(all_prompts) - custom_count

    # Get top 5 most used
    sorted_prompts = sorted(
        all_prompts.items(),
        key=lambda x: x[1].usage_count,
        reverse=True
    )[:5]

    most_used = [
        {"name": name, "usage_count": metadata.usage_count, "category": metadata.category}
        for name, metadata in sorted_prompts
    ]

    # Count by category
    by_category: Dict[str, int] = {}
    for metadata in all_prompts.values():
        by_category[metadata.category] = by_category.get(metadata.category, 0) + 1

    # Calculate total usage from all prompts
    total_usage = sum(metadata.usage_count for metadata in all_prompts.values())

    return StatsResponse(
        total_prompts=usage_stats["total_prompts"],
        custom_prompts=custom_count,
        built_in_prompts=built_in_count,
        total_usage=total_usage,
        most_used=most_used,
        by_category=by_category
    )


@router.get("/{name}", response_model=PromptResponse)
async def get_prompt(
    name: str,
    current_user: User = Depends(require_role("super_admin"))
):
    """
    Get detailed information about a specific prompt.

    Requires super_admin role.
    """
    prompt_lib = get_prompt_library()

    try:
        metadata = prompt_lib.get_metadata(name)
        if metadata is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt '{name}' not found"
            )

        return _convert_metadata_to_response(name, metadata)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving prompt: {str(e)}"
        )


@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_data: PromptCreate,
    current_user: User = Depends(require_role("super_admin"))
):
    """
    Register a new custom prompt at runtime.

    Note: Custom prompts are stored in-memory only and will be lost on restart.
    Built-in prompt names cannot be overridden unless override=True.

    Requires super_admin role.
    """
    prompt_lib = get_prompt_library()

    # Check if prompt already exists
    existing_metadata = prompt_lib.get_metadata(prompt_data.name)
    if existing_metadata is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prompt '{prompt_data.name}' already exists. Use PUT to update."
        )

    # Validate category
    valid_categories = ["agent", "rag", "llm_service", "vision", "chat", "system", "custom"]
    if prompt_data.category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )

    # Create metadata
    from app.prompts.config import PromptMetadata

    metadata = PromptMetadata(
        name=prompt_data.name,
        category=prompt_data.category,
        description=prompt_data.description,
        variables=prompt_data.variables,
        version="1.0.0",
        output_format=prompt_data.output_format,
        purpose=prompt_data.purpose or prompt_data.description,
        examples=prompt_data.examples
    )

    # Register the prompt
    try:
        success = prompt_lib.register_prompt(
            name=prompt_data.name,
            template=prompt_data.template,
            metadata=metadata,
            override=False
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to register prompt '{prompt_data.name}'"
            )

        # Return the created prompt
        created_metadata = prompt_lib.get_metadata(prompt_data.name)
        return _convert_metadata_to_response(prompt_data.name, created_metadata)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating prompt: {str(e)}"
        )


@router.put("/{name}", response_model=PromptResponse)
async def update_prompt(
    name: str,
    prompt_update: PromptUpdate,
    current_user: User = Depends(require_role("super_admin"))
):
    """
    Update an existing custom prompt.

    Built-in prompts (from templates.py) cannot be updated.
    Only custom runtime prompts can be modified.

    Requires super_admin role.
    """
    prompt_lib = get_prompt_library()

    # Check if prompt exists
    existing_metadata = prompt_lib.get_metadata(name)
    if existing_metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{name}' not found"
        )

    # Check if it's a built-in prompt
    if _is_built_in_prompt(name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot update built-in prompt '{name}'. Create a custom prompt with a different name instead."
        )

    # Get current template
    current_template = ""
    if name in prompt_lib.custom_prompts:
        current_template = prompt_lib.custom_prompts[name]["template"]
    elif name in prompt_lib.prompts:
        current_template = prompt_lib.prompts[name]["template"]

    # Update fields (only those provided)
    from app.prompts.config import PromptMetadata

    updated_metadata = PromptMetadata(
        name=name,
        category=prompt_update.category if prompt_update.category is not None else existing_metadata.category,
        description=prompt_update.description if prompt_update.description is not None else existing_metadata.description,
        variables=prompt_update.variables if prompt_update.variables is not None else existing_metadata.variables,
        version=existing_metadata.version,  # Keep version for updates
        output_format=prompt_update.output_format if prompt_update.output_format is not None else existing_metadata.output_format,
        purpose=prompt_update.purpose if prompt_update.purpose is not None else existing_metadata.purpose,
        examples=prompt_update.examples if prompt_update.examples is not None else existing_metadata.examples
    )

    new_template = prompt_update.template if prompt_update.template is not None else current_template

    # Re-register with override=True
    try:
        success = prompt_lib.register_prompt(
            name=name,
            template=new_template,
            metadata=updated_metadata,
            override=True
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update prompt '{name}'"
            )

        # Return the updated prompt
        updated_metadata_result = prompt_lib.get_metadata(name)
        return _convert_metadata_to_response(name, updated_metadata_result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating prompt: {str(e)}"
        )


@router.delete("/{name}", response_model=MessageResponse)
async def delete_prompt(
    name: str,
    current_user: User = Depends(require_role("super_admin"))
):
    """
    Delete a custom prompt.

    Built-in prompts (from templates.py) cannot be deleted.
    Only custom runtime prompts can be removed.

    Requires super_admin role.
    """
    prompt_lib = get_prompt_library()

    # Check if prompt exists
    existing_metadata = prompt_lib.get_metadata(name)
    if existing_metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{name}' not found"
        )

    # Check if it's a built-in prompt
    if _is_built_in_prompt(name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot delete built-in prompt '{name}'. Built-in prompts are read-only."
        )

    # Delete the custom prompt
    try:
        # Remove from custom prompts dictionary
        if name in prompt_lib.custom_prompts:
            del prompt_lib.custom_prompts[name]

        return MessageResponse(
            message=f"Custom prompt '{name}' deleted successfully",
            detail="This prompt has been removed from runtime memory"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting prompt: {str(e)}"
        )


@router.delete("", response_model=MessageResponse)
async def clear_custom_prompts(
    current_user: User = Depends(require_role("super_admin"))
):
    """
    Clear all custom prompts, keeping only built-in prompts.

    This removes all runtime-registered prompts while preserving
    the 30 built-in prompts from templates.py.

    Requires super_admin role.
    """
    prompt_lib = get_prompt_library()

    try:
        # Get list of custom prompts
        all_prompts = prompt_lib.list_prompts()
        custom_prompts = [name for name in all_prompts.keys() if not _is_built_in_prompt(name)]

        # Delete each custom prompt
        for name in custom_prompts:
            if name in prompt_lib.custom_prompts:
                del prompt_lib.custom_prompts[name]

        return MessageResponse(
            message=f"Cleared {len(custom_prompts)} custom prompt(s)",
            detail=f"Removed: {', '.join(custom_prompts) if custom_prompts else 'none'}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing custom prompts: {str(e)}"
        )


@router.post("/{name}/test", response_model=PromptTestResponse)
async def test_prompt(
    name: str,
    test_request: PromptTestRequest,
    current_user: User = Depends(require_role("super_admin"))
):
    """
    Test a prompt with variable substitution.

    This endpoint allows testing how a prompt will look after
    variable substitution without actually using it.

    Requires super_admin role.
    """
    prompt_lib = get_prompt_library()

    # Check if prompt exists
    metadata = prompt_lib.get_metadata(name)
    if metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{name}' not found"
        )

    # Get the template
    template = ""
    if name in prompt_lib.custom_prompts:
        template = prompt_lib.custom_prompts[name]["template"]
    elif name in prompt_lib.prompts:
        template = prompt_lib.prompts[name]["template"]

    # Check for missing variables
    required_vars = set(metadata.variables)
    provided_vars = set(test_request.variables.keys())
    missing_vars = list(required_vars - provided_vars)

    # Try to format the prompt
    try:
        formatted_prompt = prompt_lib.get_prompt(name, **test_request.variables)

        return PromptTestResponse(
            formatted_prompt=formatted_prompt,
            variables_used=test_request.variables,
            template=template,
            missing_variables=missing_vars
        )

    except (KeyError, ValueError) as e:
        # Return partial result with error information
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required variables: {', '.join(missing_vars)}" if missing_vars else str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing prompt: {str(e)}"
        )
