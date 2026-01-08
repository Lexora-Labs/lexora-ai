"""
Lexora AI - AI-Powered eBook Translator

An open-source EPUB translation tool powered by Azure OpenAI GPT.
"""

__version__ = "0.1.0"

from .translator import (
    AzureGPT,
    AzureTextTranslator,
    process_epub,
    Cache,
)

__all__ = [
    "AzureGPT",
    "AzureTextTranslator",
    "process_epub",
    "Cache",
]
