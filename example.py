"""
Example usage of Lexora AI translation tool.

This example demonstrates how to:
1. Set up an AI service (OpenAI, Azure OpenAI, or Azure AI Foundry)
2. Create a translator instance
3. Translate files or text
"""

from lexora import Translator
from lexora.services import OpenAIService, AzureOpenAIService, AzureAIFoundryService


def example_with_openai():
    """Example using OpenAI service."""
    # Option 1: Use environment variable OPENAI_API_KEY
    service = OpenAIService()
    
    # Option 2: Provide API key directly
    # service = OpenAIService(api_key="your-api-key-here", model="gpt-4")
    
    translator = Translator(service=service)
    
    # Translate a file
    translator.translate_file(
        input_file="book.epub",
        output_file="translated_book.txt",
        target_language="es",  # Spanish
        source_language="en"   # English (optional)
    )


def example_with_azure_openai():
    """Example using Azure OpenAI service."""
    # Use environment variables or provide directly
    service = AzureOpenAIService(
        api_key="your-azure-key",
        endpoint="https://your-resource.openai.azure.com/",
        deployment="your-deployment-name"
    )
    
    translator = Translator(service=service)
    
    # Translate text directly
    translated = translator.translate_text(
        text="Hello, world!",
        target_language="fr"  # French
    )
    print(translated)


def example_with_azure_ai_foundry():
    """Example using Azure AI Foundry service."""
    service = AzureAIFoundryService(
        api_key="your-foundry-key",
        endpoint="https://your-endpoint.inference.ai.azure.com",
        model="your-model-name"
    )
    
    translator = Translator(service=service)
    
    # Translate a markdown file
    translator.translate_file(
        input_file="README.md",
        output_file="README_translated.md",
        target_language="de"  # German
    )


def example_auto_detect_service():
    """Example with auto-detected service from environment variables."""
    # This will automatically use the first configured service
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
