"""Main translator module."""

from typing import Optional, List
from pathlib import Path
from .readers import FileReader, EpubReader, MobiReader, WordReader, MarkdownReader
from .services import AIService, OpenAIService, AzureOpenAIService, AzureAIFoundryService


class Translator:
    """Main translator class that coordinates file reading and translation."""

    def __init__(self, service: Optional[AIService] = None):
        """
        Initialize translator.

        Args:
            service: AI service to use for translation (defaults to OpenAI)
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
        ]
        
        for service in services:
            if service.is_configured():
                return service
        
        raise ValueError(
            "No AI service is configured. Please set one of:\n"
            "- OPENAI_API_KEY for OpenAI\n"
            "- AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT for Azure OpenAI\n"
            "- AZURE_AI_FOUNDRY_API_KEY, AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_MODEL for Azure AI Foundry"
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
        print(f"Reading {input_file}...")
        text = reader.read(input_file)

        if not text.strip():
            raise ValueError("No text content found in the file")

        # Translate the text
        print(f"Translating to {target_language}...")
        translated_text = self.service.translate(text, target_language, source_language)

        # Write the translated text
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        print(f"Translation saved to {output_file}")

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
        return self.service.translate(text, target_language, source_language)
