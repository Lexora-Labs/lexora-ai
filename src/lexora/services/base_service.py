"""Base AI service interface."""

from abc import ABC, abstractmethod
from typing import Optional


class AIService(ABC):
    """Abstract base class for AI translation services."""

    @abstractmethod
    def translate(self, text: str, target_language: str, source_language: Optional[str] = None) -> str:
        """
        Translate text to the target language.

        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'es', 'fr', 'de')
            source_language: Source language code (optional, auto-detect if None)

        Returns:
            str: Translated text
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the service is properly configured.

        Returns:
            bool: True if the service has necessary credentials
        """
        pass
