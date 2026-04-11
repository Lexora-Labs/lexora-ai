"""Helpers for selecting and constructing translation providers."""

from typing import Dict, Iterable, Tuple, Type

from .anthropic_provider import AnthropicProvider
from .azure_ai_foundry_provider import AzureAIFoundryProvider
from .azure_openai_provider import AzureOpenAIProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .qwen_provider import QwenProvider
from ..core import BaseTranslator


ProviderClass = Type[BaseTranslator]

_CANONICAL_PROVIDERS: Tuple[Tuple[str, ProviderClass], ...] = (
    ("openai", OpenAIProvider),
    ("azure-openai", AzureOpenAIProvider),
    ("azure-foundry", AzureAIFoundryProvider),
    ("gemini", GeminiProvider),
    ("anthropic", AnthropicProvider),
    ("qwen", QwenProvider),
)

_ALIASES: Dict[str, str] = {
    "azure_openai": "azure-openai",
    "azure-ai-foundry": "azure-foundry",
    "azure_ai_foundry": "azure-foundry",
}


def canonical_provider_name(name: str) -> str:
    """Return the canonical CLI/library provider name."""
    normalized = name.strip().lower()
    return _ALIASES.get(normalized, normalized)


def get_provider_class(name: str) -> ProviderClass:
    """Look up a provider class by canonical or alias name."""
    canonical_name = canonical_provider_name(name)

    for provider_name, provider_class in _CANONICAL_PROVIDERS:
        if provider_name == canonical_name:
            return provider_class

    supported = ", ".join(provider_name for provider_name, _ in _CANONICAL_PROVIDERS)
    raise ValueError(f"Unsupported provider '{name}'. Supported providers: {supported}")


def create_provider(name: str, **kwargs) -> BaseTranslator:
    """Instantiate a provider by name."""
    provider_class = get_provider_class(name)
    return provider_class(**kwargs)


def iter_available_provider_names() -> Iterable[str]:
    """List canonical provider names in default resolution order."""
    for provider_name, _ in _CANONICAL_PROVIDERS:
        yield provider_name


def get_default_provider() -> BaseTranslator:
    """Return the first configured provider available in the environment."""
    configuration_errors = []

    for provider_name, provider_class in _CANONICAL_PROVIDERS:
        try:
            provider = provider_class()
        except ImportError as exc:
            configuration_errors.append(f"{provider_name}: missing dependency ({exc})")
            continue

        if provider.is_configured():
            return provider

    error_lines = [
        "No translation provider is configured. Set one of:",
        "- OPENAI_API_KEY for OpenAI",
        "- AZURE_OPENAI_KEY or AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT for Azure OpenAI",
        "- AZURE_AI_FOUNDRY_API_KEY, AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_MODEL for Azure AI Foundry",
        "- GOOGLE_API_KEY for Gemini",
        "- ANTHROPIC_API_KEY for Anthropic",
        "- DASHSCOPE_API_KEY or QWEN_API_KEY for Qwen",
    ]
    if configuration_errors:
        error_lines.append("")
        error_lines.append("Unavailable providers:")
        error_lines.extend(f"- {message}" for message in configuration_errors)

    raise ValueError("\n".join(error_lines))
