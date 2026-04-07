"""Test script to verify the basic functionality of Lexora AI."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from lexora import Translator
        print("✓ Translator imported")
        
        from lexora.services import OpenAIService, AzureOpenAIService, AzureAIFoundryService
        print("✓ Services imported")
        
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


def test_service_configuration():
    """Test AI service configuration detection."""
    print("\nTesting AI service configuration...")
    
    try:
        from lexora.services import OpenAIService, AzureOpenAIService, AzureAIFoundryService
        
        # These should not raise errors even without configuration
        openai_service = OpenAIService()
        azure_openai_service = AzureOpenAIService()
        azure_foundry_service = AzureAIFoundryService()
        
        # Check configuration status (should be False without env vars)
        print(f"  OpenAI configured: {openai_service.is_configured()}")
        print(f"  Azure OpenAI configured: {azure_openai_service.is_configured()}")
        print(f"  Azure AI Foundry configured: {azure_foundry_service.is_configured()}")
        
        print("\n✓ Service initialization tests passed!")
        return True
    except Exception as e:
        print(f"\n✗ Service configuration test failed: {e}")
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


def main():
    """Run all tests."""
    print("=" * 60)
    print("Lexora AI - Basic Functionality Tests")
    print("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Format Detection", test_reader_supports()))
    results.append(("Service Configuration", test_service_configuration()))
    results.append(("Markdown Reader", test_markdown_reader()))
    results.append(("Theme System", test_theme_system()))
    
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
