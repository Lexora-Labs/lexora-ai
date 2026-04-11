"""Core translation components."""

from .base_translator import (
    BaseTranslator,
    TranslationConfig,
    TranslationResult,
    TranslationMode,
    BilingualAST,
    BilingualNode,
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
    "CACHE_SCHEMA_VERSION",
    "CacheFingerprint",
    "TranslationCache",
    "build_cache_key",
    "hash_glossary",
]
