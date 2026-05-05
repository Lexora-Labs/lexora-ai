"""Core translation components."""

from .base_translator import (
    BaseTranslator,
    TranslationConfig,
    TranslationResult,
    TranslationMode,
    BilingualAST,
    BilingualNode,
    TRANSLATION_TONES,
    TRANSLATION_DOMAINS,
    build_system_message,
    compose_neighbor_context_system_instruction,
    normalize_tone,
    normalize_domain,
)
from .translation_cache import (
    CACHE_SCHEMA_VERSION,
    CacheFingerprint,
    TranslationCache,
    build_cache_key,
    hash_glossary,
)

__all__ = [
    "BaseTranslator",
    "TranslationConfig",
    "TranslationResult",
    "TranslationMode",
    "BilingualAST",
    "BilingualNode",
    "TRANSLATION_TONES",
    "TRANSLATION_DOMAINS",
    "build_system_message",
    "compose_neighbor_context_system_instruction",
    "normalize_tone",
    "normalize_domain",
    "CACHE_SCHEMA_VERSION",
    "CacheFingerprint",
    "TranslationCache",
    "build_cache_key",
    "hash_glossary",
]
