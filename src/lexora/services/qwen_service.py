"""Qwen (Alibaba Cloud) service for translation."""

import os
from typing import Optional
from openai import OpenAI
from .base_service import AIService


class QwenService(AIService):
    """Qwen-based translation service via OpenAI-compatible API."""

    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-plus",
        base_url: Optional[str] = None,
    ):
        """
        Initialize Qwen service.

        Args:
            api_key: DashScope API key (defaults to QWEN_API_KEY env var)
            model: Model to use (default: qwen-plus)
            base_url: Override the default DashScope endpoint
        """
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.model = model
        self.base_url = base_url or self.BASE_URL
        self.client = None

        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

    def is_configured(self) -> bool:
        """Check if Qwen is configured."""
        return self.api_key is not None

    def translate(self, text: str, target_language: str, source_language: Optional[str] = None) -> str:
        """
        Translate text using Qwen.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (optional)

        Returns:
            str: Translated text
        """
        if not self.is_configured():
            raise ValueError("Qwen API key not configured. Set the QWEN_API_KEY environment variable.")

        source_lang_text = f" from {source_language}" if source_language else ""
        prompt = (
            f"Translate the following text{source_lang_text} to {target_language}. "
            "Preserve formatting and structure:\n\n"
            f"{text}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional translator. "
                            "Translate the text accurately while preserving its formatting and structure."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("Qwen returned no content")
            return content
        except Exception as e:
            raise RuntimeError(f"Qwen translation failed: {str(e)}")
