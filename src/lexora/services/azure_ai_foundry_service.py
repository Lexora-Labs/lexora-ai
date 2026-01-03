"""Azure AI Foundry service for translation."""

import os
from typing import Optional
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from .base_service import AIService


class AzureAIFoundryService(AIService):
    """Azure AI Foundry-based translation service."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Azure AI Foundry service.

        Args:
            api_key: Azure AI Foundry API key (defaults to AZURE_AI_FOUNDRY_API_KEY env var)
            endpoint: Azure AI Foundry endpoint (defaults to AZURE_AI_FOUNDRY_ENDPOINT env var)
            model: Model name (defaults to AZURE_AI_FOUNDRY_MODEL env var)
        """
        self.api_key = api_key or os.getenv("AZURE_AI_FOUNDRY_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
        self.model = model or os.getenv("AZURE_AI_FOUNDRY_MODEL")
        self.client = None
        
        if self.api_key and self.endpoint:
            self.client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key)
            )

    def is_configured(self) -> bool:
        """Check if Azure AI Foundry is configured."""
        return all([self.api_key, self.endpoint, self.model])

    def translate(self, text: str, target_language: str, source_language: Optional[str] = None) -> str:
        """
        Translate text using Azure AI Foundry.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (optional)

        Returns:
            str: Translated text
        """
        if not self.is_configured():
            raise ValueError("Azure AI Foundry not fully configured (need API key, endpoint, and model)")

        source_lang_text = f" from {source_language}" if source_language else ""
        prompt = f"Translate the following text{source_lang_text} to {target_language}. Preserve formatting and structure:\n\n{text}"

        try:
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You are a professional translator. Translate the text accurately while preserving its formatting and structure."),
                    UserMessage(content=prompt)
                ],
                model=self.model,
                temperature=0.3,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Azure AI Foundry translation failed: {str(e)}")
