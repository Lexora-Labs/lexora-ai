"""Compatibility shim for the legacy Azure AI Foundry service API."""

from .base_service import AIService
from ..providers import AzureAIFoundryProvider


class AzureAIFoundryService(AzureAIFoundryProvider, AIService):
    """Compatibility alias for integrations that still import AzureAIFoundryService."""
