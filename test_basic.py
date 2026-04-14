"""Test script to verify the basic functionality of Lexora AI."""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def _build_fake_provider():
    from lexora.core import BaseTranslator, TranslationConfig, TranslationResult

    class FakeProvider(BaseTranslator):
        @property
        def provider_name(self) -> str:
            return "fake"

        def is_configured(self) -> bool:
            return True

        def translate_text(self, text: str, config: TranslationConfig) -> TranslationResult:
            translated = f"[{config.target_language}] {text}"
            return TranslationResult(translated_content=translated, bilingual_ast=None)

        def translate_batch(self, texts: list, config: TranslationConfig) -> list:
            return [self.translate_text(text, config) for text in texts]

    return FakeProvider()

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from lexora import Translator
        print("✓ Translator imported")
        
        from lexora.providers import (
            OpenAIProvider,
            AzureOpenAIProvider,
            AzureAIFoundryProvider,
            GeminiProvider,
            AnthropicProvider,
            QwenProvider,
        )
        print("✓ Providers imported")
        
        from lexora.readers import EpubReader, MobiReader, WordReader, MarkdownReader
        print("✓ Readers imported")
        
        print("\n✓ All imports successful!")
        return True
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reader_supports():
    """Test file format detection."""
    print("\nTesting file format detection...")
    
    try:
        from lexora.readers import EpubReader, MobiReader, WordReader, MarkdownReader
        
        epub_reader = EpubReader()
        assert epub_reader.supports("book.epub") == True
        assert epub_reader.supports("book.mobi") == False
        print("✓ EPUB reader detection works")
        
        mobi_reader = MobiReader()
        assert mobi_reader.supports("book.mobi") == True
        assert mobi_reader.supports("book.epub") == False
        print("✓ MOBI reader detection works")
        
        word_reader = WordReader()
        assert word_reader.supports("doc.docx") == True
        assert word_reader.supports("doc.doc") == True
        assert word_reader.supports("doc.pdf") == False
        print("✓ Word reader detection works")
        
        md_reader = MarkdownReader()
        assert md_reader.supports("README.md") == True
        assert md_reader.supports("README.txt") == False
        print("✓ Markdown reader detection works")
        
        print("\n✓ All format detection tests passed!")
        return True
    except Exception as e:
        print(f"\n✗ Format detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_configuration():
    """Test AI provider configuration detection."""
    print("\nTesting AI provider configuration...")
    
    try:
        from lexora.providers import (
            OpenAIProvider,
            AzureOpenAIProvider,
            AzureAIFoundryProvider,
        )
        
        # These should not raise errors even without configuration
        openai_provider = OpenAIProvider()
        azure_openai_provider = AzureOpenAIProvider()
        azure_foundry_provider = AzureAIFoundryProvider()
        
        # Check configuration status (should be False without env vars)
        print(f"  OpenAI configured: {openai_provider.is_configured()}")
        print(f"  Azure OpenAI configured: {azure_openai_provider.is_configured()}")
        print(f"  Azure AI Foundry configured: {azure_foundry_provider.is_configured()}")
        
        print("\n✓ Provider initialization tests passed!")
        return True
    except Exception as e:
        print(f"\n✗ Provider configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_translator_with_provider():
    """Test Translator against the canonical provider interface."""
    print("\nTesting Translator with BaseTranslator provider...")

    try:
        from lexora import Translator

        translator = Translator(provider=_build_fake_provider())
        translated = translator.translate_text(
            text="Hello, world!",
            target_language="es",
        )

        assert translated == "[es] Hello, world!"
        print("✓ Translator uses BaseTranslator providers correctly")
        return True
    except Exception as e:
        print(f"\n✗ Translator/provider integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_markdown_reader():
    """Test reading a markdown file."""
    print("\nTesting Markdown reader...")
    
    try:
        import tempfile
        from lexora.readers import MarkdownReader
        
        # Create a temporary test markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            test_file = f.name
            f.write("# Test Document\n\nThis is a test.")
        
        try:
            reader = MarkdownReader()
            content = reader.read(test_file)
            
            assert len(content) > 0, "Content should not be empty"
            assert "Test Document" in content, "Content should contain the title"
            
            print(f"✓ Successfully read {len(content)} characters from markdown file")
            print("\n✓ Markdown reader test passed!")
            return True
        finally:
            # Clean up the temporary file
            if os.path.exists(test_file):
                os.unlink(test_file)
    except Exception as e:
        print(f"\n✗ Markdown reader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_theme_system():
    """Test the centralized theme system."""
    print("\nTesting theme system...")

    try:
        import flet as ft
        from lexora.ui.theme import (
            Colors,
            DARK_PALETTE,
            LIGHT_PALETTE,
            apply_theme,
            cycle_theme_mode,
            theme_mode_icon,
            theme_mode_label,
            get_palette,
        )

        # --- Palette values ---
        assert DARK_PALETTE.BACKGROUND == "#0F172A", "Dark background mismatch"
        assert LIGHT_PALETTE.BACKGROUND == "#F0F4F8", "Light background mismatch"
        print("✓ Dark / light palettes have correct values")

        # --- get_palette ---
        assert get_palette(ft.ThemeMode.DARK) is DARK_PALETTE
        assert get_palette(ft.ThemeMode.LIGHT) is LIGHT_PALETTE
        assert get_palette(ft.ThemeMode.SYSTEM) is DARK_PALETTE  # default
        print("✓ get_palette() returns correct palette for each ThemeMode")

        # --- Colors singleton reflects dark palette by default ---
        assert Colors.BACKGROUND == DARK_PALETTE.BACKGROUND
        assert Colors.PRIMARY == DARK_PALETTE.PRIMARY
        print("✓ Colors singleton initialised to dark palette")

        # --- update_from_palette switches colors ---
        Colors.update_from_palette(LIGHT_PALETTE)
        assert Colors.BACKGROUND == LIGHT_PALETTE.BACKGROUND
        assert Colors.PRIMARY == LIGHT_PALETTE.PRIMARY
        Colors.update_from_palette(DARK_PALETTE)  # restore
        assert Colors.BACKGROUND == DARK_PALETTE.BACKGROUND
        print("✓ Colors.update_from_palette() switches palette in-place")

        # --- cycle_theme_mode ---
        assert cycle_theme_mode(ft.ThemeMode.DARK) == ft.ThemeMode.LIGHT
        assert cycle_theme_mode(ft.ThemeMode.LIGHT) == ft.ThemeMode.SYSTEM
        assert cycle_theme_mode(ft.ThemeMode.SYSTEM) == ft.ThemeMode.DARK
        print("✓ cycle_theme_mode() cycles DARK→LIGHT→SYSTEM→DARK")

        # --- theme_mode_icon ---
        assert theme_mode_icon(ft.ThemeMode.DARK) == ft.icons.DARK_MODE
        assert theme_mode_icon(ft.ThemeMode.LIGHT) == ft.icons.LIGHT_MODE
        assert theme_mode_icon(ft.ThemeMode.SYSTEM) == ft.icons.BRIGHTNESS_AUTO
        print("✓ theme_mode_icon() returns correct icon for each mode")

        # --- theme_mode_label ---
        assert theme_mode_label(ft.ThemeMode.DARK) == "Dark"
        assert theme_mode_label(ft.ThemeMode.LIGHT) == "Light"
        assert theme_mode_label(ft.ThemeMode.SYSTEM) == "System"
        print("✓ theme_mode_label() returns correct label for each mode")

        # --- Thread safety: _lock exists and is a Lock ---
        import threading
        assert isinstance(Colors._lock, type(threading.Lock())), \
            "Colors._lock is not a threading.Lock"
        print("✓ Colors._lock is a threading.Lock (thread-safe)")

        print("\n✓ Theme system tests passed!")
        return True

    except Exception as e:
        print(f"\n✗ Theme system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_translation_cache_key_stability():
    """Test cache key stability and fingerprint isolation behavior."""
    print("\nTesting translation cache key stability...")

    try:
        from lexora.core import CacheFingerprint, build_cache_key, hash_glossary

        fp1 = CacheFingerprint(
            source_language="en",
            target_language="vi",
            provider_name="openai",
            provider_model="gpt-4o",
            glossary_hash=hash_glossary({"hello": "xin chao"}),
            instruction_hash="abc",
            chunking_version="sentence-aware-v1",
            pipeline_version="epub-node-v1",
        )
        fp2 = CacheFingerprint(
            source_language="en",
            target_language="vi",
            provider_name="openai",
            provider_model="gpt-4o",
            glossary_hash=hash_glossary({"hello": "xin chao"}),
            instruction_hash="abc",
            chunking_version="sentence-aware-v1",
            pipeline_version="epub-node-v1",
        )

        content = "Hello, world!"
        key1 = build_cache_key(content, fp1)
        key1_repeat = build_cache_key(content, fp1)
        key2 = build_cache_key(content, fp2)

        assert key1 == key1_repeat, "Cache key must be deterministic"
        assert key1 == key2, "Display mode should not affect translation cache key"
        print("✓ Cache key stability and mode-agnostic reuse work")
        return True

    except Exception as e:
        print(f"\n✗ Translation cache key test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_cache_scope_and_clear_cache():
    """Test CLI cache scope resolution and clear-cache helper behavior."""
    print("\nTesting CLI cache scope and clear-cache helper...")

    try:
        import tempfile
        from lexora.cli import _resolve_cache_path, _clear_cache_file

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "book.epub")
            with open(input_file, "w", encoding="utf-8") as f:
                f.write("stub")

            global_path = _resolve_cache_path(
                input_file=input_file,
                cache_scope="global",
                cache_path=".lexora/cache/global_translation_cache.jsonl",
                no_cache=False,
            )
            per_ebook_path = _resolve_cache_path(
                input_file=input_file,
                cache_scope="per-ebook",
                cache_path=".lexora/cache/global_translation_cache.jsonl",
                no_cache=False,
            )
            disabled_path = _resolve_cache_path(
                input_file=input_file,
                cache_scope="disabled",
                cache_path=".lexora/cache/global_translation_cache.jsonl",
                no_cache=False,
            )

            assert global_path.endswith("global_translation_cache.jsonl")
            assert per_ebook_path is not None and "/per-ebook/" in per_ebook_path.replace("\\", "/")
            assert disabled_path is None

            cache_file = os.path.join(temp_dir, "cache.jsonl")
            with open(cache_file, "w", encoding="utf-8") as cache_out:
                cache_out.write('{"key":"k","translated_text":"v"}\n')

            cleared = _clear_cache_file(cache_file)
            assert "Cleared cache file" in cleared
            assert not os.path.exists(cache_file)

            missing = _clear_cache_file(cache_file)
            assert "not found" in missing

            disabled = _clear_cache_file(None)
            assert "disabled" in disabled

        print("✓ CLI cache scope and clear-cache helper work")
        return True
    except Exception as e:
        print(f"\n✗ CLI cache scope/clear-cache test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_record_compatibility_filtering():
    """Test cache loader skips incompatible schema/pipeline records."""
    print("\nTesting cache record compatibility filtering...")

    try:
        import tempfile
        from lexora.core import CacheFingerprint, TranslationCache, build_cache_key, hash_glossary

        fp = CacheFingerprint(
            source_language="en",
            target_language="vi",
            provider_name="openai",
            provider_model="gpt-4o",
            glossary_hash=hash_glossary({"book": "sach"}),
            instruction_hash="abc",
            chunking_version="sentence-aware-v1",
            pipeline_version="epub-node-v1",
        )
        content = "Hello, world!"
        compatible_key = build_cache_key(content, fp)

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "compat-cache.jsonl")
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "schema_version": "0.9",
                    "key": compatible_key,
                    "translated_text": "OLD",
                    "fingerprint": {"pipeline_version": "epub-node-v1"},
                }) + "\n")
                f.write(json.dumps({
                    "schema_version": "1.0",
                    "key": compatible_key,
                    "translated_text": "OLD_PIPELINE",
                    "fingerprint": {"pipeline_version": "epub-node-v0"},
                }) + "\n")
                f.write(json.dumps({
                    "schema_version": "1.0",
                    "key": compatible_key,
                    "translated_text": "NEW",
                    "fingerprint": {"pipeline_version": "epub-node-v1"},
                }) + "\n")

            cache = TranslationCache(cache_path)
            assert cache.get(content, fp) == "NEW", "Compatible cache record should be loaded"

        print("✓ Cache compatibility filtering works")
        return True
    except Exception as e:
        print(f"\n✗ Cache compatibility filtering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logging_target_parsing_and_fallback():
    """Test logging target parsing and fallback defaults."""
    print("\nTesting logging target parsing...")

    try:
        from lexora.logging_framework import parse_log_targets

        assert parse_log_targets(None) == ["console"]
        assert parse_log_targets("") == ["console"]
        assert parse_log_targets("console,file") == ["console", "file"]
        assert parse_log_targets(" console , aws , ui ") == ["console", "aws", "ui"]

        print("✓ Logging target parsing works")
        return True
    except Exception as e:
        print(f"\n✗ Logging target parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_sink_buffer_and_min_level():
    """Test UI sink stores bounded events and applies min-level filtering."""
    print("\nTesting UI sink buffering and level filter...")

    try:
        import logging
        from lexora.logging_framework import (
            build_logging_config,
            clear_ui_log_events,
            configure_logging,
            get_ui_log_events,
        )

        clear_ui_log_events()
        config = build_logging_config(
            level="DEBUG",
            targets="ui",
        )
        config["ui_buffer_size"] = 2
        config["ui_min_level"] = "INFO"

        logger = configure_logging(config).getChild("test.ui")
        logger.debug("debug should be filtered")
        logger.info("info one")
        logger.warning("warn two")
        logger.error("error three")

        events = get_ui_log_events()
        assert len(events) == 2, "UI buffer must keep only latest bounded events"
        assert events[0]["level"] == "WARNING"
        assert events[1]["level"] == "ERROR"

        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            handler.close()
            root_logger.removeHandler(handler)
        root_logger.filters.clear()

        print("✓ UI sink buffering and min-level filtering work")
        return True
    except Exception as e:
        print(f"\n✗ UI sink buffering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_structured_event_record_fields():
    """Test structured logging extras are stored in UI events."""
    print("\nTesting structured event field capture...")

    try:
        import logging
        from lexora.logging_framework import (
            build_logging_config,
            clear_ui_log_events,
            configure_logging,
            get_ui_log_events,
        )

        clear_ui_log_events()
        config = build_logging_config(level="INFO", targets="ui", provider="openai", run_id="testrun01")
        logger = configure_logging(config).getChild("test.structured")
        logger.info(
            "translation.epub.started",
            extra={
                "event": "translation.epub.started",
                "fields": {"doc_total": 3, "chunks": 12},
            },
        )

        events = get_ui_log_events()
        assert events, "Expected one structured UI event"
        event = events[-1]
        assert event["event"] == "translation.epub.started"
        assert event["fields"]["doc_total"] == 3
        assert event["provider"] == "openai"
        assert event["run_id"] == "testrun01"

        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            handler.close()
            root_logger.removeHandler(handler)
        root_logger.filters.clear()

        print("✓ Structured event fields captured in UI sink")
        return True
    except Exception as e:
        print(f"\n✗ Structured event capture test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_sink_incremental_fetch():
    """Test incremental UI sink reads by event id cursor."""
    print("\nTesting incremental UI sink fetch...")

    try:
        import logging
        from lexora.logging_framework import (
            build_logging_config,
            clear_ui_log_events,
            configure_logging,
            get_ui_log_events_since,
        )

        clear_ui_log_events()
        config = build_logging_config(level="INFO", targets="ui")
        logger = configure_logging(config).getChild("test.incremental")

        logger.info("first event")
        first_batch = get_ui_log_events_since(0)
        assert len(first_batch) == 1, "Expected first incremental fetch to return one event"
        first_id = int(first_batch[0]["id"])

        logger.info("second event")
        second_batch = get_ui_log_events_since(first_id)
        assert len(second_batch) == 1, "Expected second incremental fetch to return one new event"
        assert "second event" in second_batch[0]["message"]

        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            handler.close()
            root_logger.removeHandler(handler)
        root_logger.filters.clear()

        print("✓ Incremental UI sink fetch works")
        return True
    except Exception as e:
        print(f"\n✗ Incremental UI sink fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rotating_file_sink_utf8_output():
    """Test file sink creates UTF-8 logs with date token filename pattern."""
    print("\nTesting rotating file sink UTF-8 output...")

    try:
        import logging
        import tempfile
        from pathlib import Path
        from lexora.logging_framework import build_logging_config, configure_logging

        with tempfile.TemporaryDirectory() as temp_dir:
            pattern = str(Path(temp_dir) / "lexora-%DATE%.log")
            config = build_logging_config(
                level="INFO",
                targets="file",
                log_file_path=pattern,
                file_max_bytes=1024,
                file_backup_count=1,
            )

            logger = configure_logging(config).getChild("test")
            logger.info("UTF-8 smoke: xin chao")

            log_files = list(Path(temp_dir).glob("lexora-*.log"))
            assert log_files, "Expected at least one log file"

            content = log_files[0].read_text(encoding="utf-8")
            assert "UTF-8 smoke: xin chao" in content

            # Ensure file handlers are closed before temporary directory cleanup on Windows.
            root_logger = logging.getLogger()
            for handler in list(root_logger.handlers):
                handler.close()
                root_logger.removeHandler(handler)

        print("✓ Rotating file sink UTF-8 output works")
        return True
    except Exception as e:
        print(f"\n✗ Rotating file sink test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rotating_file_sink_datetime_token():
    """Test file sink resolves %DATETIME% token in log filename."""
    print("\nTesting rotating file sink DATETIME token...")

    try:
        import logging
        import tempfile
        from pathlib import Path
        from lexora.logging_framework import build_logging_config, configure_logging

        with tempfile.TemporaryDirectory() as temp_dir:
            pattern = str(Path(temp_dir) / "lexora-%DATETIME%.log")
            config = build_logging_config(
                level="INFO",
                targets="file",
                log_file_path=pattern,
                file_max_bytes=1024,
                file_backup_count=1,
            )

            logger = configure_logging(config).getChild("test")
            logger.info("DATETIME token smoke")

            log_files = list(Path(temp_dir).glob("lexora-*.log"))
            assert log_files, "Expected at least one log file"
            assert "%DATETIME%" not in log_files[0].name, "Token should be resolved in file name"

            # Ensure file handlers are closed before temporary directory cleanup on Windows.
            root_logger = logging.getLogger()
            for handler in list(root_logger.handlers):
                handler.close()
                root_logger.removeHandler(handler)

        print("✓ Rotating file sink DATETIME token works")
        return True
    except Exception as e:
        print(f"\n✗ Rotating file sink DATETIME token test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logging_config_retention_overrides():
    """Test CLI-style retention overrides are preserved in resolved config."""
    print("\nTesting logging retention override config...")

    try:
        from lexora.logging_framework import build_logging_config

        config = build_logging_config(
            level="INFO",
            targets="file",
            log_file_path="logs/lexora-%DATE%.log",
            file_max_bytes=2048,
            file_backup_count=7,
        )

        assert config["file_max_bytes"] == 2048
        assert config["file_backup_count"] == 7
        print("✓ Logging retention overrides work")
        return True
    except Exception as e:
        print(f"\n✗ Logging retention override test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unknown_log_target_fallback_to_console():
    """Test unknown sink target does not break logging initialization."""
    print("\nTesting unknown log target fallback...")

    try:
        import logging
        from lexora.logging_framework import configure_logging

        logger = configure_logging(
            {
                "level": "INFO",
                "targets": ["not-a-sink"],
                "log_file_path": "logs/lexora-%DATE%.log",
                "file_max_bytes": 1024,
                "file_backup_count": 1,
            }
        ).getChild("test")
        logger.info("fallback smoke")

        root_logger = logging.getLogger()
        assert root_logger.handlers, "Fallback console handler should be present"

        # Ensure handlers are closed for clean test process state.
        for handler in list(root_logger.handlers):
            handler.close()
            root_logger.removeHandler(handler)

        print("✓ Unknown target fallback works")
        return True
    except Exception as e:
        print(f"\n✗ Unknown target fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _check_epub_node_replacement_strips_raw_html_fragments() -> bool:
    """Test EPUB replacement path strips provider HTML fragments to plain text."""
    print("\nTesting EPUB node replacement HTML-fragment sanitization...")

    try:
        from lexora.readers import EpubReader

        reader = EpubReader()
        html = "<html><body><p>Hello world</p></body></html>"
        soup, nodes = reader.extract_translatable_nodes(html)
        assert nodes, "Expected translatable text nodes"

        updated = reader.replace_translatable_nodes(
            soup,
            nodes,
            ["<p>Xin chao <strong>the gioi</strong></p>"],
        )
        normalized = " ".join(updated.split())

        assert "<strong>" not in updated, "Raw HTML tags should not be rendered as text"
        assert "&lt;p&gt;" not in updated, "Escaped raw HTML tags should not appear in EPUB text nodes"
        assert "Xin chao the gioi" in normalized

        print("✓ EPUB node replacement sanitizes raw HTML fragments")
        return True
    except Exception as e:
        print(f"\n✗ EPUB node replacement sanitization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_epub_node_replacement_strips_raw_html_fragments():
    """Pytest entrypoint for EPUB replacement sanitization regression."""
    assert _check_epub_node_replacement_strips_raw_html_fragments()


def test_rotating_file_sink_extended_tokens():
    """Test file sink resolves LEVEL/RUN_ID/PROVIDER/PID tokens in filename."""
    print("\nTesting rotating file sink extended tokens...")

    try:
        import logging
        import os
        import tempfile
        from pathlib import Path
        from lexora.logging_framework import build_logging_config, configure_logging

        with tempfile.TemporaryDirectory() as temp_dir:
            run_id = "runabc12"
            pattern = str(Path(temp_dir) / "lexora-%PROVIDER%-%RUN_ID%-%LEVEL%-%PID%.log")
            config = build_logging_config(
                level="warning",
                targets="file",
                log_file_path=pattern,
                file_max_bytes=1024,
                file_backup_count=1,
                provider="azure-foundry",
                run_id=run_id,
            )

            logger = configure_logging(config).getChild("test")
            logger.warning("extended token smoke")

            log_files = list(Path(temp_dir).glob("lexora-*.log"))
            assert log_files, "Expected at least one log file"
            name = log_files[0].name
            assert "%PROVIDER%" not in name
            assert "%RUN_ID%" not in name
            assert "%LEVEL%" not in name
            assert "%PID%" not in name
            assert "azure-foundry" in name
            assert run_id in name
            assert "WARNING" in name
            assert str(os.getpid()) in name

            # Ensure file handlers are closed before temporary directory cleanup on Windows.
            root_logger = logging.getLogger()
            for handler in list(root_logger.handlers):
                handler.close()
                root_logger.removeHandler(handler)

        print("✓ Rotating file sink extended tokens work")
        return True
    except Exception as e:
        print(f"\n✗ Rotating file sink extended token test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Lexora AI - Basic Functionality Tests")
    print("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Format Detection", test_reader_supports()))
    results.append(("Provider Configuration", test_provider_configuration()))
    results.append(("Translator Provider", test_translator_with_provider()))
    results.append(("Markdown Reader", test_markdown_reader()))
    results.append(("Theme System", test_theme_system()))
    results.append(("Translation Cache Key", test_translation_cache_key_stability()))
    results.append(("CLI Cache Scope/Clear", test_cli_cache_scope_and_clear_cache()))
    results.append(("Cache Compatibility", test_cache_record_compatibility_filtering()))
    results.append(("Logging Target Parsing", test_logging_target_parsing_and_fallback()))
    results.append(("UI Sink Buffer/Level", test_ui_sink_buffer_and_min_level()))
    results.append(("Structured Event Capture", test_structured_event_record_fields()))
    results.append(("UI Sink Incremental Fetch", test_ui_sink_incremental_fetch()))
    results.append(("Rotating File Sink", test_rotating_file_sink_utf8_output()))
    results.append(("Rotating File Sink DATETIME", test_rotating_file_sink_datetime_token()))
    results.append(("Logging Retention Overrides", test_logging_config_retention_overrides()))
    results.append(("Unknown Target Fallback", test_unknown_log_target_fallback_to_console()))
    results.append(("Rotating File Sink Extended Tokens", test_rotating_file_sink_extended_tokens()))
    results.append(("EPUB Node Replacement Sanitization", _check_epub_node_replacement_strips_raw_html_fragments()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
