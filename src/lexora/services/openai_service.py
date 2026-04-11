"""Compatibility shim for the legacy OpenAI service API."""

from .base_service import AIService
from ..providers import OpenAIProvider


class OpenAIService(OpenAIProvider, AIService):
    """Compatibility alias for integrations that still import OpenAIService."""
