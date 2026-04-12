"""Lexora AI - eBook translation tool."""

from .core import BaseTranslator, BilingualAST, BilingualNode, TranslationConfig, TranslationMode, TranslationResult
from .providers import (
    AnthropicProvider,
    AzureAIFoundryProvider,
    AzureOpenAIProvider,
    GeminiProvider,
    OpenAIProvider,
    QwenProvider,
    create_provider,
    get_default_provider,
)
from .translator import Translator
from .services import OpenAIService, AzureOpenAIService, AzureAIFoundryService
from .readers import EpubReader, MobiReader, WordReader, MarkdownReader

__version__ = "0.1.0"
__all__ = [
    'Translator',
    'BaseTranslator',
    'TranslationConfig',
    'TranslationMode',
    'TranslationResult',
    'BilingualAST',
    'BilingualNode',
    'create_provider',
    'get_default_provider',
    'OpenAIProvider',
    'AzureOpenAIProvider',
    'AzureAIFoundryProvider',
    'GeminiProvider',
    'AnthropicProvider',
    'QwenProvider',
    'OpenAIService',
    'AzureOpenAIService',
    'AzureAIFoundryService',
    'EpubReader',
    'MobiReader',
    'WordReader',
    'MarkdownReader',
]
