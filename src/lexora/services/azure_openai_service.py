"""Azure OpenAI service for translation."""

import os
from typing import Optional
from openai import AzureOpenAI
from .base_service import AIService


class AzureOpenAIService(AIService):
    """Azure OpenAI-based translation service."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: str = "2024-02-15-preview"
    ):
        """
        Initialize Azure OpenAI service.

        Args:
            api_key: Azure OpenAI API key (defaults to AZURE_OPENAI_API_KEY env var)
            endpoint: Azure OpenAI endpoint (defaults to AZURE_OPENAI_ENDPOINT env var)
            deployment: Deployment name (defaults to AZURE_OPENAI_DEPLOYMENT env var)
            api_version: API version
        """
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.api_version = api_version
        self.client = None
        
        if self.api_key and self.endpoint:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )

    def is_configured(self) -> bool:
        """Check if Azure OpenAI is configured."""
        return all([self.api_key, self.endpoint, self.deployment])

    def translate(self, text: str, target_language: str, source_language: Optional[str] = None) -> str:
        """
        Translate text using Azure OpenAI.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (optional)

        Returns:
            str: Translated text
        """
        if not self.is_configured():
            raise ValueError("Azure OpenAI not fully configured (need API key, endpoint, and deployment)")

        source_lang_text = f" from {source_language}" if source_language else ""
        prompt = f"Translate the following text{source_lang_text} to {target_language}. Preserve formatting and structure:\n\n{text}"

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a professional translator. Translate the text accurately while preserving its formatting and structure."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI translation failed: {str(e)}")
