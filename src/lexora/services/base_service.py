"""Compatibility shim for the legacy service API."""

from abc import ABC, abstractmethod
from typing import Optional
from ..core import TranslationConfig, TranslationResult


class AIService(ABC):
    """Compatibility layer that forwards to the provider architecture."""

    def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
    ) -> str:
        """Translate text using the canonical provider contract."""
        config = TranslationConfig(
            source_language=source_language,
            target_language=target_language,
        )
        return self.translate_text(text, config).translated_content

    @abstractmethod
    def translate_text(self, text: str, config: TranslationConfig) -> TranslationResult:
        """Provider-style translation contract."""
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        raise NotImplementedError
