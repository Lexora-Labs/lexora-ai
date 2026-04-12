"""Compatibility shim for the legacy Azure OpenAI service API."""

from .base_service import AIService
from ..providers import AzureOpenAIProvider


class AzureOpenAIService(AzureOpenAIProvider, AIService):
    """Compatibility alias for integrations that still import AzureOpenAIService."""
