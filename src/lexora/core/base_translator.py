"""
Base Translator - Abstract Base Class for all Translation Providers.

This follows the Strategy Pattern as defined in vibe-context.md:
- Providers: OpenAI, Gemini, Anthropic, Azure
- Base class: BaseTranslator
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, FrozenSet
from enum import Enum

from .structured_batch import StructuredBatchItem

# Canonical machine values (English) for prompts and cache identity.
TRANSLATION_TONES: FrozenSet[str] = frozenset(
    {"neutral", "formal", "casual", "literary", "academic", "marketing"}
)
TRANSLATION_DOMAINS: FrozenSet[str] = frozenset(
    {"general", "fiction", "technical", "academic", "legal", "medical", "business"}
)

DEFAULT_TRANSLATION_TONE = "neutral"
DEFAULT_TRANSLATION_DOMAIN = "general"

# EPUB neighbor-chunk context mode: prepended to the user system message (never replaces user tone/domain).
CONTEXT_CHUNK_SYSTEM_RULE = (
    "Translate only the text between TARGET_CHUNK_START and TARGET_CHUNK_END. "
    "Use neighbor context for coherence but output only the translated target chunk. "
    "Do not include labels or any extra commentary."
)


def normalize_tone(value: Optional[str]) -> str:
    v = (value or DEFAULT_TRANSLATION_TONE).strip().lower()
    if v not in TRANSLATION_TONES:
        allowed = ", ".join(sorted(TRANSLATION_TONES))
        raise ValueError(f"Invalid tone '{value}'. Allowed: {allowed}")
    return v


def normalize_domain(value: Optional[str]) -> str:
    v = (value or DEFAULT_TRANSLATION_DOMAIN).strip().lower()
    if v not in TRANSLATION_DOMAINS:
        allowed = ", ".join(sorted(TRANSLATION_DOMAINS))
        raise ValueError(f"Invalid domain '{value}'. Allowed: {allowed}")
    return v


def build_system_message(config: "TranslationConfig") -> str:
    """
    Compose the default literary translator system message with optional tone, domain,
    and free-text instruction. Defaults (neutral/general/no instruction) match the
    historical single baseline paragraph exactly.
    """
    base = (
        "You are a professional literary translator. "
        "Translate faithfully, fluently, and maintain formatting where possible. "
        "Do not add explanations or notes. Output only the translation."
    )
    parts: List[str] = [base]
    domain = normalize_domain(config.domain)
    if domain != DEFAULT_TRANSLATION_DOMAIN:
        parts.append(
            f"Subject domain: {domain}. "
            "Use terminology and conventions appropriate to this domain."
        )
    tone = normalize_tone(config.tone)
    if tone != DEFAULT_TRANSLATION_TONE:
        parts.append(f"Voice and tone: {tone}.")
    user_inst = (config.custom_instruction or "").strip()
    if user_inst:
        parts.append("Additional user instruction:\n" + user_inst)
    return "\n\n".join(parts)


def compose_neighbor_context_system_instruction(config: "TranslationConfig") -> str:
    """System message for EPUB neighbor-window mode: delimiter rules + user steering."""
    return CONTEXT_CHUNK_SYSTEM_RULE + "\n\n" + build_system_message(config)


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
    tone: Optional[str] = None
    domain: Optional[str] = None
    #: When set, ``get_system_instruction`` returns this verbatim (internal EPUB context-window path).
    system_instruction_override: Optional[str] = None


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

    def supports_structured_batch(self) -> bool:
        """Whether this provider implements translate_structured_batch for EPUB JSON batches."""
        return False

    def translate_structured_batch(
        self,
        items: List[StructuredBatchItem],
        *,
        batch_id: str,
        config: TranslationConfig,
    ) -> Tuple[Dict[str, str], Dict[str, int]]:
        """
        Translate multiple items in one request; return id -> translated text and token usage.

        Default: not implemented. Call only when supports_structured_batch() is True.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement structured batch translation"
        )

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
        if config.system_instruction_override is not None:
            return config.system_instruction_override
        return build_system_message(config)
