"""Main translator module."""

import logging
from typing import Optional, List
from pathlib import Path
from .readers import FileReader, EpubReader, MobiReader, WordReader, MarkdownReader
from .services import AIService, OpenAIService, AzureOpenAIService, AzureAIFoundryService, QwenService

logger = logging.getLogger(__name__)


class Translator:
    """Main translator class that coordinates file reading and translation."""

    def __init__(self, service: Optional[AIService] = None):
        """
        Initialize translator.

        Args:
            service: AI service to use for translation (defaults to first configured service)
        """
        self.service = service or self._get_default_service()
        self.readers: List[FileReader] = [
            EpubReader(),
            MobiReader(),
            WordReader(),
            MarkdownReader(),
        ]

    def _get_default_service(self) -> AIService:
        """Get the first configured AI service."""
        services = [
            OpenAIService(),
            AzureOpenAIService(),
            AzureAIFoundryService(),
            QwenService(),
        ]
        
        for service in services:
            if service.is_configured():
                return service
        
        raise ValueError(
            "No AI service is configured. Please set one of:\n"
            "- OPENAI_API_KEY for OpenAI\n"
            "- AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT for Azure OpenAI\n"
            "- AZURE_AI_FOUNDRY_API_KEY, AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_MODEL for Azure AI Foundry\n"
            "- QWEN_API_KEY for Qwen (Alibaba Cloud)"
        )

    def _get_reader(self, file_path: str) -> FileReader:
        """Get the appropriate reader for a file."""
        for reader in self.readers:
            if reader.supports(file_path):
                return reader
        
        supported_formats = ['.epub', '.mobi', '.docx', '.doc', '.md']
        raise ValueError(
            f"Unsupported file format. Supported formats: {', '.join(supported_formats)}"
        )

    def translate_file(
        self,
        input_file: str,
        output_file: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> None:
        """
        Translate a file to the target language.

        Args:
            input_file: Path to input file
            output_file: Path to output file
            target_language: Target language code
            source_language: Source language code (optional)
        """
        # Check if input file exists
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Read the file
        reader = self._get_reader(input_file)
        logger.info("Reading %s...", input_file)
        text = reader.read(input_file)

        if not text.strip():
            raise ValueError("No text content found in the file")

        # Translate the text
        logger.info("Translating to %s...", target_language)
        translated_text = self.service.translate(text, target_language, source_language)

        if translated_text is None:
            raise RuntimeError("Translation service returned no content")

        # Write the translated text
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        logger.info("Translation saved to %s", output_file)

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """
        Translate raw text.

        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)

        Returns:
            str: Translated text
        """
        result = self.service.translate(text, target_language, source_language)
        if result is None:
            raise RuntimeError("Translation service returned no content")
        return result
