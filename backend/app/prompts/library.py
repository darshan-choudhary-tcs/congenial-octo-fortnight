"""
Prompt Library Manager

Singleton class for managing all prompts in the application.
Provides centralized access to prompt templates with variable substitution,
versioning support, and usage analytics.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
from .templates import ALL_PROMPTS
from .config import DEFAULT_SETTINGS, PromptMetadata

logger = logging.getLogger(__name__)


class PromptLibrary:
    """
    Singleton manager for accessing and managing prompt templates.

    Features:
    - Centralized prompt storage and retrieval
    - Variable substitution in templates
    - Custom prompt registration
    - Usage tracking and analytics
    - Version management support
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Ensure singleton pattern"""
        if cls._instance is None:
            cls._instance = super(PromptLibrary, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the prompt library (only once)"""
        if not PromptLibrary._initialized:
            self.prompts: Dict[str, Dict[str, Any]] = ALL_PROMPTS.copy()
            self.custom_prompts: Dict[str, Dict[str, Any]] = {}
            self.settings = DEFAULT_SETTINGS.copy()
            self.usage_stats: Dict[str, int] = {}
            self.last_access: Dict[str, datetime] = {}
            PromptLibrary._initialized = True
            logger.info(f"Prompt Library initialized with {len(self.prompts)} prompts")

    def get_prompt(
        self,
        name: str,
        version: str = "latest",
        **kwargs
    ) -> str:
        """
        Get a prompt template and substitute variables.

        Args:
            name: Name of the prompt to retrieve
            version: Version of the prompt (default: "latest")
            **kwargs: Variables to substitute in the template

        Returns:
            Formatted prompt string with variables substituted

        Raises:
            KeyError: If prompt name not found
            ValueError: If required variables are missing

        Example:
            >>> library = get_prompt_library()
            >>> prompt = library.get_prompt(
            ...     "research_analysis",
            ...     query="What is RAG?",
            ...     documents="Doc 1: RAG is..."
            ... )
        """
        # Check custom prompts first
        if name in self.custom_prompts:
            prompt_data = self.custom_prompts[name]
        elif name in self.prompts:
            prompt_data = self.prompts[name]
        else:
            raise KeyError(f"Prompt '{name}' not found in library")

        template = prompt_data["template"]
        metadata: PromptMetadata = prompt_data["metadata"]

        # Track usage
        if self.settings.get("enable_analytics", True):
            self.usage_stats[name] = self.usage_stats.get(name, 0) + 1
            self.last_access[name] = datetime.now()
            metadata.usage_count += 1

        # Substitute variables
        try:
            formatted_prompt = template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(
                f"Missing required variable '{missing_var}' for prompt '{name}'. "
                f"Required variables: {metadata.variables}"
            )

        logger.debug(f"Retrieved prompt '{name}' (version: {version})")
        return formatted_prompt

    def get_system_prompt(self, name: str) -> str:
        """
        Get a system prompt (role definition) without variable substitution.

        Args:
            name: Name of the system prompt

        Returns:
            System prompt string

        Example:
            >>> library = get_prompt_library()
            >>> system = library.get_system_prompt("research_analyst")
        """
        return self.get_prompt(name)

    def register_prompt(
        self,
        name: str,
        template: str,
        metadata: PromptMetadata,
        override: bool = False
    ) -> bool:
        """
        Register a new custom prompt.

        Args:
            name: Unique name for the prompt
            template: Prompt template string with {variables}
            metadata: PromptMetadata object with prompt information
            override: Whether to override existing prompt (default: False)

        Returns:
            True if registered successfully, False if name exists and override=False

        Example:
            >>> library = get_prompt_library()
            >>> metadata = PromptMetadata(
            ...     name="custom_analysis",
            ...     category="agent",
            ...     description="Custom analysis prompt",
            ...     variables=["data"]
            ... )
            >>> library.register_prompt(
            ...     "custom_analysis",
            ...     "Analyze: {data}",
            ...     metadata
            ... )
        """
        if name in self.custom_prompts and not override:
            logger.warning(f"Prompt '{name}' already exists. Set override=True to replace.")
            return False

        self.custom_prompts[name] = {
            "template": template,
            "metadata": metadata
        }
        logger.info(f"Registered custom prompt '{name}' in category '{metadata.category}'")
        return True

    def get_metadata(self, name: str) -> Optional[PromptMetadata]:
        """
        Get metadata for a prompt.

        Args:
            name: Name of the prompt

        Returns:
            PromptMetadata object or None if not found
        """
        if name in self.custom_prompts:
            return self.custom_prompts[name]["metadata"]
        elif name in self.prompts:
            return self.prompts[name]["metadata"]
        return None

    def list_prompts(self, category: Optional[str] = None) -> Dict[str, PromptMetadata]:
        """
        List all available prompts, optionally filtered by category.

        Args:
            category: Optional category to filter by (e.g., "agent", "rag", "llm_service")

        Returns:
            Dictionary mapping prompt names to their metadata

        Example:
            >>> library = get_prompt_library()
            >>> agent_prompts = library.list_prompts(category="agent")
        """
        all_prompts = {**self.prompts, **self.custom_prompts}

        if category:
            return {
                name: data["metadata"]
                for name, data in all_prompts.items()
                if data["metadata"].category == category
            }

        return {name: data["metadata"] for name, data in all_prompts.items()}

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for all prompts.

        Returns:
            Dictionary with usage counts and last access times
        """
        return {
            "total_prompts": len(self.prompts) + len(self.custom_prompts),
            "usage_counts": self.usage_stats.copy(),
            "last_access": {
                name: dt.isoformat()
                for name, dt in self.last_access.items()
            },
            "most_used": sorted(
                self.usage_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    def export_prompt(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Export a prompt with its metadata and template.

        Args:
            name: Name of the prompt to export

        Returns:
            Dictionary with prompt data or None if not found
        """
        prompt_data = None
        if name in self.custom_prompts:
            prompt_data = self.custom_prompts[name]
        elif name in self.prompts:
            prompt_data = self.prompts[name]

        if prompt_data:
            return {
                "name": name,
                "template": prompt_data["template"],
                "metadata": prompt_data["metadata"].to_dict()
            }
        return None

    def clear_custom_prompts(self):
        """Clear all custom registered prompts"""
        self.custom_prompts.clear()
        logger.info("Cleared all custom prompts")

    def reset(self):
        """Reset the library to initial state (mainly for testing)"""
        self.__init__()
        logger.info("Prompt Library reset to initial state")


# Singleton instance getter
_prompt_library_instance = None

def get_prompt_library() -> PromptLibrary:
    """
    Get the singleton instance of PromptLibrary.

    Returns:
        PromptLibrary singleton instance

    Example:
        >>> from app.prompts import get_prompt_library
        >>> library = get_prompt_library()
        >>> prompt = library.get_prompt("research_analysis", query="...", documents="...")
    """
    global _prompt_library_instance
    if _prompt_library_instance is None:
        _prompt_library_instance = PromptLibrary()
    return _prompt_library_instance
