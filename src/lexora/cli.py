"""Command-line interface for Lexora AI."""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
from .translator import Translator
from .services import OpenAIService, AzureOpenAIService, AzureAIFoundryService


def main():
    """Main CLI entry point."""
    # Load environment variables from .env file if it exists
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Lexora AI - Translate eBooks using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate an EPUB file to Spanish
  lexora translate input.epub output.txt --target es

  # Translate a Word document to French with specific service
  lexora translate input.docx output.txt --target fr --service openai

  # Translate with source language specified
  lexora translate input.md output.txt --target de --source en

Supported file formats:
  - EPUB (.epub)
  - MOBI (.mobi)
  - Word (.docx, .doc)
  - Markdown (.md)

Supported AI services:
  - openai: OpenAI (requires OPENAI_API_KEY)
  - azure-openai: Azure OpenAI (requires AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT)
  - azure-foundry: Azure AI Foundry (requires AZURE_AI_FOUNDRY_API_KEY, AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_MODEL)
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Translate command
    translate_parser = subparsers.add_parser('translate', help='Translate a file')
    translate_parser.add_argument('input', help='Input file path')
    translate_parser.add_argument('output', help='Output file path')
    translate_parser.add_argument(
        '-t', '--target',
        required=True,
        help='Target language code (e.g., es, fr, de, ja, zh)'
    )
    translate_parser.add_argument(
        '-s', '--source',
        help='Source language code (optional, auto-detect if not specified)'
    )
    translate_parser.add_argument(
        '--service',
        choices=['openai', 'azure-openai', 'azure-foundry'],
        help='AI service to use (auto-detect if not specified)'
    )

    args = parser.parse_args()

    if args.command == 'translate':
        try:
            # Get the AI service
            service = None
            if args.service:
                if args.service == 'openai':
                    service = OpenAIService()
                elif args.service == 'azure-openai':
                    service = AzureOpenAIService()
                elif args.service == 'azure-foundry':
                    service = AzureAIFoundryService()
                
                if not service.is_configured():
                    print(f"Error: {args.service} is not properly configured", file=sys.stderr)
                    sys.exit(1)

            # Create translator
            translator = Translator(service=service)

            # Translate the file
            translator.translate_file(
                input_file=args.input,
                output_file=args.output,
                target_language=args.target,
                source_language=args.source
            )

            print("Translation completed successfully!")

        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
