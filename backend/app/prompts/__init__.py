"""
Centralized Prompt Library for LLM Interactions

This package provides a centralized system for managing all prompts used across
the application including agents, RAG system, LLM services, and vision services.

Key Components:
- PromptLibrary: Singleton manager for accessing and registering prompts
- Templates: All prompt definitions organized by category
- Config: Prompt versioning and metadata configuration
"""

from .library import PromptLibrary, get_prompt_library

__all__ = ["PromptLibrary", "get_prompt_library"]
