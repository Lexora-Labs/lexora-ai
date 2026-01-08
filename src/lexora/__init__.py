"""Lexora AI - eBook translation tool."""

from .translator import Translator
from .services import OpenAIService, AzureOpenAIService, AzureAIFoundryService
from .readers import EpubReader, MobiReader, WordReader, MarkdownReader

__version__ = "0.1.0"
__all__ = [
    'Translator',
    'OpenAIService',
    'AzureOpenAIService',
    'AzureAIFoundryService',
    'EpubReader',
    'MobiReader',
    'WordReader',
    'MarkdownReader',
]
