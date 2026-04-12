"""Command-line interface for Lexora AI."""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from .logging_framework import build_logging_config, configure_logging
from .translator import Translator
from .providers import create_provider, iter_available_provider_names


DEFAULT_GLOBAL_CACHE_PATH = ".lexora/cache/global_translation_cache.jsonl"
DEFAULT_PER_EBOOK_CACHE_DIR = ".lexora/cache/per-ebook"


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


def _build_per_ebook_cache_path(input_file: str) -> str:
    """Build deterministic per-ebook cache path from input file identity."""
    source = Path(input_file)
    name = source.stem or "ebook"
    path_hash = hashlib.sha256(str(source.resolve()).encode("utf-8")).hexdigest()[:12]
    return str(Path(DEFAULT_PER_EBOOK_CACHE_DIR) / f"{name}-{path_hash}.jsonl")


def _resolve_cache_path(
    input_file: str,
    cache_scope: str,
    cache_path: str,
    no_cache: bool,
) -> str | None:
    """Resolve effective cache path from CLI flags."""
    if no_cache or cache_scope == "disabled":
        return None
    if cache_scope == "per-ebook":
        return _build_per_ebook_cache_path(input_file)
    return cache_path


def _clear_cache_file(path: str | None) -> str:
    """Clear cache file if present, otherwise return a safe no-op message."""
    if not path:
        return "Cache is disabled, nothing to clear"

    cache_path = Path(path)
    if not cache_path.exists():
        return f"Cache file not found, nothing to clear: {path}"

    cache_path.unlink()
    return f"Cleared cache file: {path}"


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
        '--cache-scope',
        choices=['global', 'per-ebook', 'disabled'],
        default='global',
        help='Cache scope strategy (default: global)',
    )
    translate_parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable translation cache for this run',
    )
    translate_parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear the effective cache file before translation starts',
    )
    translate_parser.add_argument(
        '--log-level',
        help='Logging level override (DEBUG, INFO, WARNING, ERROR)',
    )
    translate_parser.add_argument(
        '--log-targets',
        help='Comma-separated log sinks (console,file,azure,aws,ui)',
    )
    translate_parser.add_argument(
        '--log-file-path',
        help='Log file path/pattern for file sink (supports %DATE%, %TIME%, %DATETIME%, %LEVEL%, %RUN_ID%, %PROVIDER%, %PID%)',
    )
    translate_parser.add_argument(
        '--log-file-max-bytes',
        type=int,
        help='Max bytes before rotating file sink (default from env or 5242880)',
    )
    translate_parser.add_argument(
        '--log-file-backup-count',
        type=int,
        help='Retained rotated file count (default from env or 3)',
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
            logging_config = build_logging_config(
                level=args.log_level,
                targets=args.log_targets,
                log_file_path=args.log_file_path,
                file_max_bytes=args.log_file_max_bytes,
                file_backup_count=args.log_file_backup_count,
                provider=args.service or "auto",
            )
            logger = configure_logging(logging_config).getChild("cli")

            # Get the translation provider
            provider = None
            if args.service:
                provider = create_provider(args.service)

                if not provider.is_configured():
                    logger.error("%s is not properly configured", args.service)
                    sys.exit(1)

            # Create translator
            translator = Translator(provider=provider)
            glossary = _load_glossary(args.glossary)
            cache_path = _resolve_cache_path(
                input_file=args.input,
                cache_scope=args.cache_scope,
                cache_path=args.cache_path,
                no_cache=args.no_cache,
            )

            if args.clear_cache:
                logger.info(_clear_cache_file(cache_path))

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

            logger.info("Translation completed successfully")

        except Exception as e:
            logging.getLogger("lexora.cli").exception("Translation failed")
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
