"""
Translate an EPUB to Vietnamese using Azure Foundry (Azure OpenAI) GPT-4

Features:
- Bilingual output by default (original + Vietnamese side-by-side)
- Uses existing robust pipeline from azure_epub_gpt_translator
- Safe defaults: input "book.epub" → output "book_vi.epub"
- Optional offline smoke mode (no API calls) for quick testing

Prereqs:
  pip install ebooklib beautifulsoup4 lxml openai requests python-dotenv

Env variables (via .env or environment):
  AZURE_OPENAI_ENDPOINT        # Foundry/Azure OpenAI endpoint (without trailing /openai/v1)
  AZURE_OPENAI_KEY             # API key
  AZURE_OPENAI_DEPLOYMENT      # Deployment name (e.g., gpt-4, gpt-4o)
  AZURE_OPENAI_API_VERSION     # e.g., 2024-02-01 (for Azure OpenAI SDK)

Usage:
  python translate.py --input book.epub --to-lang vi
  python translate.py --offline  # offline smoke test (no API calls)
"""

import os
from pathlib import Path
import argparse
import json
from typing import List

from dotenv import load_dotenv
from ebooklib import epub
import ebooklib

# Reuse the robust pipeline utilities
from azure_epub_gpt_translator import (
    AzureGPT,
    AzureTextTranslator,
    normalize_endpoint,
    load_env_file,
    process_epub,
)


class FakeAzureGPT:
    """Offline stub for smoke testing: echoes input as the "translation".
    This allows end-to-end EPUB processing without contacting the API.
    """

    def translate_batch(self, items: List[str], src_lang: str, tgt_lang: str, glossary: dict, retry: int = 0, sleep: float = 0.0) -> List[str]:
        return items


def output_with_lang_suffix(epub_path: str, lang: str = "vi") -> str:
    p = Path(epub_path)
    return str(p.with_name(f"{p.stem}_{lang}{p.suffix}"))


def resolve_glossary_path(path: str | None) -> str | None:
    if not path:
        guess = Path("glossary.json")
        return str(guess) if guess.exists() else None
    return path if Path(path).exists() else None


def main():
    # Welcome message
    print("=" * 70)
    print("  Lexora AI")
    print("  AI-powered eBook translation tool")
    print("  https://github.com/Lexora-Labs/lexora-ai")
    print("=" * 70)
    print()
    
    ap = argparse.ArgumentParser(description="Translate EPUB using Azure Foundry GPT-4 with bilingual output")
    ap.add_argument("--env-file", default=".env", help="Optional .env file with AZURE_* variables")
    ap.add_argument("--input", default="book.epub", help="Path to source .epub (default: book.epub)")
    ap.add_argument("--output", help="Path to output .epub (default: add _vi suffix)")
    ap.add_argument("--from-lang", default="en", help="Source language code (default: en)")
    ap.add_argument("--to-lang", default="vi", help="Target language code (default: vi)")
    ap.add_argument("--no-bilingual", action="store_true", help="Disable bilingual mode (translate-only)")
    ap.add_argument("--glossary", help="Path to glossary JSON {source_term: target_term}")
    ap.add_argument("--cache", default="gpt_translation_cache.jsonl", help="Path to JSONL cache file")
    ap.add_argument("--workers", type=int, default=6, help="Concurrency for GPT calls")
    ap.add_argument("--offline", action="store_true", help="Offline smoke test (no API calls)")
    ap.add_argument("--service", choices=["gpt", "translator"], default="gpt", help="Translation service: 'gpt' (Azure OpenAI) or 'translator' (Text Translator API)")
    ap.add_argument("--limit-docs", type=int, help="Translate only the first N EPUB documents (debug)")
    ap.add_argument("--max-paragraphs", type=int, default=100, help="Max paragraphs per document in bilingual mode (to avoid timeouts)")
    ap.add_argument("--endpoint", default=os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT"))
    ap.add_argument("--key", default=os.getenv("AZURE_OPENAI_KEY"))
    ap.add_argument("--translator-endpoint", default=os.getenv("AZURE_TRANSLATOR_ENDPOINT"), help="Text Translator API endpoint (e.g., https://api.cognitive.microsofttranslator.com/)")
    ap.add_argument("--translator-key", default=os.getenv("AZURE_TRANSLATOR_KEY"), help="Text Translator API key")
    ap.add_argument("--deployment", default=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"))
    ap.add_argument("--api-version", default=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"))
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--instruction", help="Custom instruction for GPT translator (system message). Default: 'You are a professional literary translator...'")
    ap.add_argument("--translated-color", default=None, help="Color for translated text in HTML/CSS format (e.g., '#4D4D4D', 'gray', 'inherit'). Default: inherit system color")
    ap.add_argument("--translated-style", default=None, help="Inline CSS for translated text (e.g., 'font-style: italic;' or 'font-weight: bold; font-style: italic;')")
    ap.add_argument("--debug-calls", action="store_true", help="Verbose logging of Azure API calls (request/response)")
    args = ap.parse_args()

    # Load .env with python-dotenv (overrides only if not already set)
    load_dotenv(args.env_file)
    # Dev convenience: also load simple KEY=VALUE lines if present
    load_env_file(args.env_file)

    # Fill args from environment if missing
    args.endpoint = args.endpoint or os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT")
    args.key = args.key or os.getenv("AZURE_OPENAI_KEY")
    args.deployment = args.deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    args.api_version = args.api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    args.translator_endpoint = args.translator_endpoint or os.getenv("AZURE_TRANSLATOR_ENDPOINT")
    args.translator_key = args.translator_key or os.getenv("AZURE_TRANSLATOR_KEY")

    # Compute default output with _vi suffix if not provided
    if not args.output:
        args.output = output_with_lang_suffix(args.input, args.to_lang)

    # Normalize endpoint: remove accidental /openai/v1 suffixes
    args.endpoint = normalize_endpoint(args.endpoint)

    bilingual = not args.no_bilingual

    # Resolve glossary
    glossary_path = resolve_glossary_path(args.glossary)
    glossary = {}
    if glossary_path:
        try:
            with open(glossary_path, "r", encoding="utf-8") as f:
                glossary = json.load(f)
        except Exception:
            glossary = {}

    # Choose translation service
    if args.offline:
        print("[mode] Using OFFLINE stub (FakeAzureGPT): no API calls.")
        gpt = FakeAzureGPT()
    elif args.service == "translator":
        # Use Azure Text Translator API
        if not args.translator_endpoint or not args.translator_key:
            raise SystemExit("Set AZURE_TRANSLATOR_ENDPOINT, AZURE_TRANSLATOR_KEY or pass via --translator-endpoint, --translator-key")
        print(f"[mode] Using Azure Text Translator: endpoint={args.translator_endpoint}")
        gpt = AzureTextTranslator(endpoint=args.translator_endpoint, key=args.translator_key, debug=args.debug_calls)
    else:
        # Use Azure OpenAI GPT
        if not args.endpoint or not args.key or not args.deployment:
            raise SystemExit("Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_DEPLOYMENT or pass via args.")
        print(f"[mode] Using Azure OpenAI GPT: endpoint={args.endpoint}, deployment={args.deployment}, api_version={args.api_version}")
        gpt = AzureGPT(endpoint=args.endpoint, key=args.key, deployment=args.deployment,
                   api_version=args.api_version, temperature=args.temperature, debug=args.debug_calls, instruction=args.instruction)

    # End-to-end process (in-place modification of EPUB HTML items)
    process_epub(
        input_epub=args.input,
        output_epub=args.output,
        gpt=gpt,
        src_lang=args.from_lang,
        tgt_lang=args.to_lang,
        bilingual=bilingual,
        glossary=glossary,
        cache_path=args.cache,
        workers=args.workers,
        limit_docs=args.limit_docs,
        max_paragraphs=args.max_paragraphs,
        translated_color=args.translated_color,
        translated_style=args.translated_style,
    )
    print(f"✅ Done: {args.output}")


if __name__ == "__main__":
    main()