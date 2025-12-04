"""
Prompt Library Configuration

Defines metadata, versioning, and configuration for the prompt library.
"""

from typing import Dict, Any
from datetime import datetime

# Prompt version tracking
PROMPT_VERSION = "1.0.0"
LAST_UPDATED = datetime(2025, 12, 5)

# Prompt metadata structure
class PromptMetadata:
    """Metadata for a prompt template"""

    def __init__(
        self,
        name: str,
        category: str,
        description: str,
        variables: list,
        version: str = "1.0.0",
        output_format: str = "text",
        purpose: str = "",
        examples: list = None
    ):
        self.name = name
        self.category = category
        self.description = description
        self.variables = variables
        self.version = version
        self.output_format = output_format
        self.purpose = purpose
        self.examples = examples or []
        self.created_at = LAST_UPDATED
        self.usage_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "variables": self.variables,
            "version": self.version,
            "output_format": self.output_format,
            "purpose": self.purpose,
            "examples": self.examples,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count
        }

# Prompt categories
PROMPT_CATEGORIES = {
    "agent": "Agent-specific prompts for multi-agent system",
    "rag": "Retrieval Augmented Generation prompts",
    "llm_service": "LLM service prompts for document processing",
    "vision": "Vision and OCR service prompts",
    "chat": "Direct chat API prompts",
    "system": "System-level role definitions"
}

# Default prompt settings
DEFAULT_SETTINGS = {
    "enable_versioning": True,
    "enable_analytics": True,
    "default_version": "latest",
    "cache_prompts": True
}
