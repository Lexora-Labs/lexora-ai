"""
Base Translator - Abstract Base Class for all Translation Providers.

This follows the Strategy Pattern as defined in vibe-context.md:
- Providers: OpenAI, Gemini, Anthropic, Azure
- Base class: BaseTranslator
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class TranslationMode(Enum):
    """Translation output mode."""
    REPLACE = "replace"       # Replace original with translation
    BILINGUAL = "bilingual"   # Keep both original and translated


@dataclass
class BilingualNode:
    """
    Single node in the Bilingual Reader JSON AST.
    
    This is the Data Contract for bilingual output as per vibe-context.md:
    - Source Text
    - Translated Text  
    - Node ID
    """
    node_id: str
    source_text: str
    translated_text: str
    tag_name: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class BilingualAST:
    """
    Bilingual Reader JSON AST - Complete translation output.
    
    Used for:
    - Bilingual reader
    - Future UI
    """
    version: str = "1.0.0"
    source_language: str = ""
    target_language: str = ""
    nodes: List[BilingualNode] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        return {
            "version": self.version,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "source_text": n.source_text,
                    "translated_text": n.translated_text,
                    "tag_name": n.tag_name,
                    "attributes": n.attributes,
                }
                for n in self.nodes
            ],
            "metadata": self.metadata,
        }


@dataclass
class TranslationResult:
    """
    Result of a translation operation.
    
    Contains both:
    - Output 1: Compiled content (translated HTML/content)
    - Output 2: Bilingual Reader JSON AST
    """
    translated_content: str
    bilingual_ast: Optional[BilingualAST] = None
    token_usage: Dict[str, int] = field(default_factory=dict)
    cost_estimate: float = 0.0


@dataclass
class TranslationConfig:
    """Configuration for translation operations."""
    source_language: Optional[str] = None
    target_language: str = "vi"
    mode: TranslationMode = TranslationMode.BILINGUAL
    glossary: Dict[str, str] = field(default_factory=dict)
    temperature: float = 0.2
    max_tokens: Optional[int] = None
    custom_instruction: Optional[str] = None


class BaseTranslator(ABC):
    """
    Abstract Base Class for Translation Providers.
    
    All providers (OpenAI, Azure, Gemini, Anthropic) must implement this interface.
    
    Architecture:
    - Stateless: No session storage, no global state
    - Pure functions: Pipeline must be pure
    - Provider-agnostic: Swap providers without changing business logic
    """

    @abstractmethod
    def translate_text(
        self,
        text: str,
        config: TranslationConfig,
    ) -> TranslationResult:
        """
        Translate a single text string.
        
        Args:
            text: Source text to translate
            config: Translation configuration
            
        Returns:
            TranslationResult with translated content and optional AST
        """
        pass

    @abstractmethod
    def translate_batch(
        self,
        texts: List[str],
        config: TranslationConfig,
    ) -> List[TranslationResult]:
        """
        Translate a batch of text strings.
        
        Args:
            texts: List of source texts to translate
            config: Translation configuration
            
        Returns:
            List of TranslationResult objects
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the provider is properly configured with credentials.
        
        Returns:
            True if ready to use, False otherwise
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider (e.g., 'azure_openai', 'openai')."""
        pass

    def build_prompt(
        self,
        text: str,
        config: TranslationConfig,
    ) -> str:
        """
        Build the translation prompt with glossary support.
        
        Override in subclass for custom prompt engineering.
        """
        glossary_block = ""
        if config.glossary:
            glossary_lines = [f"- {k} → {v}" for k, v in config.glossary.items()]
            glossary_block = (
                f"\n\nGlossary (must use these translations):\n"
                + "\n".join(glossary_lines)
            )

        source_clause = f" from {config.source_language}" if config.source_language else ""

        return (
            f"Translate the following text{source_clause} "
            f"to {config.target_language}.{glossary_block}\n\n"
            f"Text:\n{text}"
        )

    def get_system_instruction(self, config: TranslationConfig) -> str:
        """
        Get the system instruction for the translation model.
        
        Override in subclass for provider-specific instructions.
        """
        if config.custom_instruction:
            return config.custom_instruction
            
        return (
            "You are a professional literary translator. "
            "Translate faithfully, fluently, and maintain formatting where possible. "
            "Do not add explanations or notes. Output only the translation."
        )
