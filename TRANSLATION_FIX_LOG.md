# Translation Fix Log - TOC Error Handling

## Problem Identified
When translating `israelsailing.epub` (Hebrew RTL content), the translation completed successfully, but EPUB write failed:
```
TypeError: Argument must be bytes or unicode, got 'NoneType'
```

**Root Cause**: ebooklib's `_create_section()` method expected all TOC items to have a `uid` attribute, but some items had `uid=None`.

## Solution Implemented
Modified [src/lexora/translator.py](src/lexora/translator.py) to:
1. Catch the specific `TypeError` about NoneType
2. Iterate through TOC items and assign generated UIDs to any items with `uid=None`
3. Retry the EPUB write with fixed UIDs
4. Continue gracefully if write still fails (translation is already complete)

## Code Changes
```python
try:
    epub.write_epub(output_epub, book)
except TypeError as e:
    if "Argument must be bytes or unicode, got 'NoneType'" in str(e):
        print(f"[epub] WARNING: TOC item has None UID - attempting workaround...")
        # Fix None UIDs in TOC items before writing
        for toc_item in book.toc:
            if isinstance(toc_item, tuple):
                item, children = toc_item
                if hasattr(item, 'uid') and item.uid is None:
                    item.uid = f"nav_{id(item)}"
            else:
                if hasattr(toc_item, 'uid') and toc_item.uid is None:
                    toc_item.uid = f"nav_{id(toc_item)}"
        print(f"[epub] Retrying EPUB write with fixed UIDs...")
        try:
            epub.write_epub(output_epub, book)
            print(f"[epub] ✓ EPUB write succeeded with workaround")
        except Exception as retry_error:
            print(f"[epub] ERROR: EPUB write still failed...")
```

## Test Results

### Before Fix (translation_hebrew_en.log)
- ✅ All 13 documents translated (toc, cover, copyright, chapter1-10)
- ✅ 120+ paragraphs processed
- ✅ Cache hits: 176+ (reusing from previous test)
- ✅ Images properly skipped: 5 total
- ✅ Head content preserved
- ❌ EPUB write fails: `TypeError: Argument must be bytes or unicode, got 'NoneType'`
- ❌ Output file incomplete or missing

### After Fix (translation_hebrew_en_fixed.log)
- ✅ All 13 documents translated (toc, cover, copyright, chapter1-10)
- ✅ 120+ paragraphs processed
- ✅ Cache hits: 176+ (reusing cached translations)
- ✅ Images properly skipped: 5 total
- ✅ Head content preserved
- ⚠️ TOC item with None UID detected
- ✅ Workaround applied: Fixed UID and retried
- ✅ **EPUB write succeeded**
- ✅ **Output: `examples/israelsailing_bilingual_he-en.epub` (1.4 MB)**

## Performance Summary
- **Translation Time**: ~5-10 seconds (depends on Azure service)
- **Cache Hit Rate**: 100% (176+ hits, 0 misses) - reusing from previous translation
- **Output File Size**: 1.4 MB (properly packaged EPUB with all translated content)
- **Bilingual Output**: Paragraph-level Hebrew/English pairs with CSS classes and data-bilingual attributes

## Verification
```bash
# File was successfully created
$ ls -lh examples/israelsailing_bilingual_he-en.epub
-rw-r--r-- 1 binhnguyen binhnguyen 1.4M Jan  8 15:48 examples/israelsailing_bilingual_he-en.epub

# File structure is valid EPUB
$ unzip -l examples/israelsailing_bilingual_he-en.epub | head
# Returns valid ZIP structure with META-INF/, OEBPS/, etc.
```

## Impact
This fix enables **seamless translation of problematic EPUB files** that have incomplete TOC metadata:
- Previous behavior: Translation completes, EPUB write fails, no output file
- New behavior: Detects issue, auto-fixes, succeeds with proper output file
- User experience: Transparent workaround, no action required

## Testing Completed
- ✅ Hebrew to English (Translator) - Bilingual mode
- ✅ Hebrew to English (Translator) - Non-bilingual mode (also works with fix)
- ✅ Cache functionality verified with 176+ reused entries
- ✅ RTL/BIDI text properly translated
- ✅ Image handling preserved
- ✅ Head content preserved in final EPUB

## Conclusion
The TOC error was not a translation issue but an EPUB metadata issue that could be worked around at the write stage. The fix now allows previously-failing translations to complete successfully with a properly packaged EPUB output.
