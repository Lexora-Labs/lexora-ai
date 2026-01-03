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
        from lexora.readers import MarkdownReader
        
        # Create a test markdown file
        test_file = "/tmp/test_input.md"
        if not os.path.exists(test_file):
            print(f"✗ Test file not found: {test_file}")
            return False
        
        reader = MarkdownReader()
        content = reader.read(test_file)
        
        assert len(content) > 0, "Content should not be empty"
        assert "Test Document" in content, "Content should contain the title"
        
        print(f"✓ Successfully read {len(content)} characters from markdown file")
        print("\n✓ Markdown reader test passed!")
        return True
    except Exception as e:
        print(f"\n✗ Markdown reader test failed: {e}")
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
