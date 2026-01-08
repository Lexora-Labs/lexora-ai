# Lexora AI - AI-Powered eBook Translator

Lexora AI is an open-source EPUB translation tool powered by Azure OpenAI GPT. It translates eBooks while preserving all formatting, structure, and styling - including bold, italic, links, and nested HTML elements.

## Features

- **Bilingual Output**: Side-by-side original and translated text in the same EPUB
- **Format Preservation**: Maintains all HTML formatting (bold, italic, links, nested structures)
- **Smart Caching**: Resume interrupted translations with JSONL-based cache
- **Timeout Protection**: 300-second timeout with configurable paragraph limits
- **Custom Styling**: Apply colors and CSS to translated text
- **CSS Classes**: Automatic "original" and "translated" classes for flexible styling
- **Multiple Services**: Azure OpenAI GPT or Azure Text Translator API
- **Glossary Support**: Provide custom term translations via JSON
- **Concurrent Processing**: Multi-threaded translation for faster processing

## Installation

Install the package in your virtual environment:

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

After installation, the `lexora` command will be available in your virtual environment.

## Translation Services

Lexora AI supports two Azure translation services:

### 1. Azure OpenAI GPT (Default)
Best for high-quality literary translations with context awareness and custom instructions.

**Pros:**
- Superior translation quality
- Context-aware translations
- Custom instructions support
- Maintains literary style and tone
- Better handling of idioms and cultural references

**Cons:**
- Higher API costs
- Slower processing
- Rate limits may apply

**Setup:**
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_api_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01
```

### 2. Azure Text Translator
Fast and cost-effective for general purpose translations.

**Pros:**
- Fast translation speed
- Lower API costs
- High throughput
- Reliable and consistent

**Cons:**
- Less context-aware than GPT
- May not preserve literary nuances
- No custom instruction support

**Setup:**
```bash
AZURE_TRANSLATOR_ENDPOINT=https://your-region.api.cognitive.microsofttranslator.com/
AZURE_TRANSLATOR_KEY=your_translator_key_here
```

## Configuration

Create a `.env` file in your project directory with your API credentials. Choose one or both services:

```bash
# Option 1: Azure OpenAI GPT (recommended for books)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_api_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01

# Option 2: Azure Text Translator (faster, more economical)
AZURE_TRANSLATOR_ENDPOINT=https://your-region.api.cognitive.microsofttranslator.com/
AZURE_TRANSLATOR_KEY=your_translator_key_here
```

See `.env.example` for a template.

## Usage

### Basic Translation

**Using Azure OpenAI GPT (default):**
```bash
lexora translate input.epub --to-lang vi
```
Output: `input_bilingual_en-vi.epub`

**Using Azure Text Translator:**
```bash
lexora translate input.epub --to-lang vi --service translator
```
Output: `input_bilingual_en-vi.epub`

**Non-bilingual mode (translation only):**
```bash
lexora translate book.epub --to-lang es --no-bilingual
```
Output: `book_es.epub`

**Custom output filename:**
```bash
lexora translate book.epub book_spanish.epub --to-lang es
```
Output: `book_spanish.epub`

### Advanced Options

**Apply custom styling to translated text:**
```bash
lexora translate book.epub --to-lang vi \
  --translated-color gray \
  --translated-style "font-style: italic;"
```

**Custom translation instructions (GPT only):**
```bash
lexora translate book.epub --to-lang es \
  --service gpt \
  --instruction "Translate maintaining literary style. Use formal Spanish."
```

**Fast translation with Azure Translator:**
```bash
lexora translate book.epub --to-lang vi \
  --service translator \
  --workers 8
```

**Control processing limits:**
```bash
lexora translate book.epub --to-lang vi \
  --max-paragraphs 50 \
  --limit-docs 5 \
  --workers 4
```

**Use glossary for specific terms:**
```bash
# Create glossary.json: {"source term": "target term"}
lexora translate book.epub --to-lang vi --glossary glossary.json
```

**Offline testing (no API calls):**
```bash
lexora translate book.epub --offline
```

### Command-Line Options

```bash
lexora translate <input.epub> [output.epub] [options]
```

| Option | Description | Default |
|--------|-------------|---------|
| `input` | Path to source EPUB file (positional) | Required |
| `output` | Path to output EPUB file (positional, optional) | Auto-generated with language suffix |
| `--from-lang` | Source language code | `en` |
| `--to-lang` | Target language code | `vi` |
| `--service` | Translation service: `gpt` or `translator` | `gpt` |
| `--translated-color` | CSS color for translated text | `inherit` |
| `--translated-style` | Inline CSS for translated text | None |
| `--instruction` | Custom system instruction for GPT | Default professional translator prompt |
| `--max-paragraphs` | Max paragraphs per document (timeout protection) | `100` |
| `--limit-docs` | Translate only first N documents (debug) | None |
| `--workers` | Concurrent translation threads | `6` |
| `--cache` | Path to JSONL cache file | `gpt_translation_cache.jsonl` |
| `--glossary` | Path to glossary JSON file | `glossary.json` (if exists) |
| `--no-bilingual` | Disable bilingual mode (translation only) | Bilingual enabled |
| `--offline` | Offline mode (no API calls) | False |

## Output Format

The translated EPUB contains bilingual content with original and translated paragraphs side-by-side:

```html
<!-- Original paragraph -->
<p class="original" data-bilingual="original">
  This is the <span class="italic">original</span> text with <strong>formatting</strong>.
</p>

<!-- Translated paragraph -->
<p class="translated" data-bilingual="translated">
  Este es el <span class="italic">texto original</span> con <strong>formato</strong>.
</p>
```

### CSS Styling

Use the automatic CSS classes to style original and translated text differently:

```css
/* Hide original text */
.original {
  display: none;
}

/* Style translated text */
.translated {
  color: #333;
  font-style: italic;
}
```

## Cache Management

Translations are cached in JSONL format for resumability:

```bash
# Default cache
gpt_translation_cache.jsonl

# Custom cache for full book translation
lexora translate book.epub --to-lang vi --cache book_full.jsonl
```

Each cache entry stores:
- Content hash (SHA256)
- Original text
- Target language
- Translated text

To clear cache: delete the `.jsonl` file.

## Limitations

- **EPUB only**: Currently supports only EPUB format (no MOBI, PDF, DOCX)
- **Paragraph-level translation**: Translates complete paragraphs (p, li, h1-h6, blockquote)
- **Image captions**: Paragraphs containing images are skipped to avoid timeouts
- **Large documents**: Use `--max-paragraphs` to limit processing and avoid timeouts

## Troubleshooting

**Timeout errors on large documents:**
```bash
lexora translate book.epub --to-lang vi --max-paragraphs 50
```

**API rate limiting:**
```bash
lexora translate book.epub --to-lang vi --workers 2
```

**TOC/Navigation errors (TypeError: Argument must be bytes or unicode):**
- Some EPUB files have incomplete table of contents metadata
- This causes `ebooklib` to fail when writing the navigation structure
- The translation completes successfully, but the EPUB write fails
- Known issue with certain RTL/BIDI EPUBs like `israelsailing.epub`
- Workaround: The HTML content is translated correctly; the issue is only with the final EPUB packaging

**Missing head content (title, CSS):**
- The tool automatically preserves `<head>` content via ZIP rewriting

**Empty translated paragraphs:**
- Fixed by deep copy implementation - all nested structures preserved

## Development

This project uses a virtual environment. To work with the source:

```bash
# Activate virtual environment
source bin/activate  # Linux/Mac
.\Scripts\activate   # Windows

# Install in development mode
pip install -e .

# Run directly
lexora translate book.epub --to-lang vi

# Or run the module directly
python -m lexora.cli translate book.epub --to-lang vi
```

## Testing

### Example Files

The `examples/` folder contains sample EPUB files for testing and demonstration purposes. These files are sourced from the [EPUB 3 Sample Documents](https://idpf.github.io/epub3-samples/30/samples.html) repository maintained by IDPF, ensuring no legal issues with usage.

**Available test files:**

1. **sample1.epub** - "The Geography of Bliss"
   - Tests: Basic bilingual translation, paragraph-level processing
   - Content: Literary narrative with standard formatting

2. **sample2.epub** - "Sway"
   - Tests: Multi-document structure, table of contents, copyright pages
   - Content: Book with complex structure and metadata

3. **georgia.epub** - Encyclopedia Britannica Entry
   - Tests: Reference/encyclopedia content, formal writing style
   - Content: Structured academic text with definitions and facts

4. **israelsailing.epub** - BIDI and Hebrew Text
   - Tests: Right-to-left (RTL) text, bidirectional content, page-progression-direction
   - Content: Hebrew text with RTL layout support
   - Note: Tests RTL language handling and mixed text direction
   - Known Issue: May fail at EPUB write stage due to incomplete TOC metadata (translation completes successfully)

**Running tests:**

```bash
# Test basic bilingual translation
lexora translate examples/sample1.epub --to-lang vi

# Test with Azure Translator service
lexora translate examples/sample2.epub --to-lang es --service translator

# Test RTL content handling
lexora translate examples/israelsailing.epub --to-lang en --from-lang he

# Test encyclopedia/reference content
lexora translate examples/georgia.epub --to-lang fr --service gpt
```

## Project Structure

```
booktranslator_env/
├── src/
│   └── lexora/
│       ├── __init__.py       # Package initialization
│       ├── cli.py            # Command-line interface
│       └── translator.py     # Core translation engine
├── setup.py                  # Package configuration
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
├── .gitignore               # Git ignore rules
└── README.md                # Documentation
```

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Repository

https://github.com/Lexora-Labs/lexora-ai
