"""
Example usage of Lexora AI translation tool.

This example demonstrates how to:
1. Set up a translation provider (OpenAI, Azure OpenAI, or Azure AI Foundry)
2. Create a translator instance
3. Translate files or text
"""

from lexora import Translator
from lexora.providers import OpenAIProvider, AzureOpenAIProvider, AzureAIFoundryProvider


def example_with_openai():
    """Example using the OpenAI provider."""
    # Option 1: Use environment variable OPENAI_API_KEY
    provider = OpenAIProvider()
    
    # Option 2: Provide API key directly
    # provider = OpenAIProvider(api_key="your-api-key-here", model="gpt-4o")
    
    translator = Translator(provider=provider)
    
    # Translate a file
    translator.translate_file(
        input_file="book.epub",
        output_file="translated_book.txt",
        target_language="es",  # Spanish
        source_language="en"   # English (optional)
    )


def example_with_azure_openai():
    """Example using the Azure OpenAI provider."""
    # Use environment variables or provide directly
    provider = AzureOpenAIProvider(
        api_key="your-azure-key",
        endpoint="https://your-resource.openai.azure.com/",
        deployment="your-deployment-name"
    )
    
    translator = Translator(provider=provider)
    
    # Translate text directly
    translated = translator.translate_text(
        text="Hello, world!",
        target_language="fr"  # French
    )
    print(translated)


def example_with_azure_ai_foundry():
    """Example using the Azure AI Foundry provider."""
    provider = AzureAIFoundryProvider(
        api_key="your-foundry-key",
        endpoint="https://your-endpoint.inference.ai.azure.com",
        model="your-model-name"
    )
    
    translator = Translator(provider=provider)
    
    # Translate a markdown file
    translator.translate_file(
        input_file="README.md",
        output_file="README_translated.md",
        target_language="de"  # German
    )


def example_auto_detect_service():
    """Example with auto-detected provider from environment variables."""
    # This will automatically use the first configured provider
    # based on environment variables
    translator = Translator()
    
    # Translate a Word document
    translator.translate_file(
        input_file="document.docx",
        output_file="document_translated.txt",
        target_language="ja"  # Japanese
    )


if __name__ == "__main__":
    # Uncomment the example you want to run
    
    # example_with_openai()
    # example_with_azure_openai()
    # example_with_azure_ai_foundry()
    # example_auto_detect_service()
    
    print("See the function definitions for examples of how to use Lexora AI")
