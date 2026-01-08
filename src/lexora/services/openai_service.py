"""OpenAI service for translation."""

import os
from typing import Optional
from openai import OpenAI
from .base_service import AIService


class OpenAIService(AIService):
    """OpenAI-based translation service."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize OpenAI service.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def is_configured(self) -> bool:
        """Check if OpenAI is configured."""
        return self.api_key is not None

    def translate(self, text: str, target_language: str, source_language: Optional[str] = None) -> str:
        """
        Translate text using OpenAI.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (optional)

        Returns:
            str: Translated text
        """
        if not self.is_configured():
            raise ValueError("OpenAI API key not configured")

        source_lang_text = f" from {source_language}" if source_language else ""
        prompt = f"Translate the following text{source_lang_text} to {target_language}. Preserve formatting and structure:\n\n{text}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator. Translate the text accurately while preserving its formatting and structure."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI translation failed: {str(e)}")
