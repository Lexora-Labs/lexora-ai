"""Command-line interface for Lexora AI."""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from .translator import Translator
from .providers import create_provider, iter_available_provider_names


DEFAULT_GLOBAL_CACHE_PATH = ".lexora/cache/global_translation_cache.jsonl"


def _load_glossary(glossary_path: str):
    """Load glossary JSON from file if provided."""
    if not glossary_path:
        return {}

    path = Path(glossary_path)
    if not path.exists():
        raise ValueError(f"Glossary file not found: {glossary_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load glossary JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Glossary JSON must be an object: {\"term\": \"translation\"}")

    return {str(k): str(v) for k, v in data.items()}


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

  # Translate a Word document to French with a specific provider
  lexora translate input.docx output.txt --target fr --service openai

  # Translate with source language specified
  lexora translate input.md output.txt --target de --source en

    # Translate EPUB in bilingual mode with glossary
    lexora translate input.epub output.epub --target vi --mode bilingual --glossary glossary.json

Supported file formats:
  - EPUB (.epub)
  - MOBI (.mobi)
  - Word (.docx, .doc)
  - Markdown (.md)

Supported AI providers:
  - openai: OpenAI (requires OPENAI_API_KEY)
  - azure-openai: Azure OpenAI (requires AZURE_OPENAI_KEY or AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT)
  - azure-foundry: Azure AI Foundry (requires AZURE_AI_FOUNDRY_API_KEY, AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_MODEL)
  - gemini: Google Gemini (requires GOOGLE_API_KEY)
  - anthropic: Anthropic Claude (requires ANTHROPIC_API_KEY)
  - qwen: Alibaba Qwen (requires DASHSCOPE_API_KEY or QWEN_API_KEY)
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
        choices=list(iter_available_provider_names()),
        help='Translation provider to use (auto-detect if not specified)'
    )
    translate_parser.add_argument(
        '--mode',
        choices=['replace', 'bilingual'],
        default='replace',
        help='Output mode: replace text or keep original + translated text (default: replace)'
    )
    translate_parser.add_argument(
        '--glossary',
        help='Path to glossary JSON object {"source_term": "target_term"}'
    )
    translate_parser.add_argument(
        '--cache-path',
        default=DEFAULT_GLOBAL_CACHE_PATH,
        help=(
            'Global translation cache JSONL path '
            f'(default: {DEFAULT_GLOBAL_CACHE_PATH})'
        ),
    )
    translate_parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable translation cache for this run',
    )
    translate_parser.add_argument(
        '--limit-docs',
        type=int,
        help='Translate only the first N EPUB document items after range filtering (debug)',
    )
    translate_parser.add_argument(
        '--start-doc',
        type=int,
        help='1-based start index of EPUB document range to translate',
    )
    translate_parser.add_argument(
        '--end-doc',
        type=int,
        help='1-based end index (inclusive) of EPUB document range to translate',
    )

    args = parser.parse_args()

    if args.command == 'translate':
        try:
            # Get the translation provider
            provider = None
            if args.service:
                provider = create_provider(args.service)

                if not provider.is_configured():
                    print(f"Error: {args.service} is not properly configured", file=sys.stderr)
                    sys.exit(1)

            # Create translator
            translator = Translator(provider=provider)
            glossary = _load_glossary(args.glossary)
            cache_path = None if args.no_cache else args.cache_path

            if args.limit_docs is not None and args.limit_docs < 0:
                raise ValueError("--limit-docs must be >= 0")
            if args.start_doc is not None and args.start_doc < 1:
                raise ValueError("--start-doc must be >= 1")
            if args.end_doc is not None and args.end_doc < 1:
                raise ValueError("--end-doc must be >= 1")
            if args.start_doc is not None and args.end_doc is not None and args.start_doc > args.end_doc:
                raise ValueError("--start-doc cannot be greater than --end-doc")

            # Translate the file
            translator.translate_file(
                input_file=args.input,
                output_file=args.output,
                target_language=args.target,
                source_language=args.source,
                mode=args.mode,
                glossary=glossary,
                cache_path=cache_path,
                limit_docs=args.limit_docs,
                start_doc=args.start_doc,
                end_doc=args.end_doc,
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
