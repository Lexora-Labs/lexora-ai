"""Legacy compatibility shims around the provider-based translation API."""

from .base_service import AIService
from .openai_service import OpenAIService
from .azure_openai_service import AzureOpenAIService
from .azure_ai_foundry_service import AzureAIFoundryService

__all__ = [
    'AIService',
    'OpenAIService',
    'AzureOpenAIService',
    'AzureAIFoundryService',
]
