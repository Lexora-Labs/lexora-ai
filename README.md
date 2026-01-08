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

## Configuration

Create a `.env` file in your project directory with your API credentials:

```bash
# Azure OpenAI (required for GPT translation)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_api_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure Text Translator (optional - alternative to GPT)
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com/
AZURE_TRANSLATOR_KEY=your_translator_key_here
```

See `.env.example` for a template.

## Usage

### Basic Translation

Translate an EPUB to Vietnamese:
```bash
lexora translate input.epub --to-lang vi
```

The output will be saved as `input_vi.epub` by default.

Translate to Spanish with custom output:
```bash
lexora translate book.epub book_spanish.epub --to-lang es
```

### Advanced Options

**Apply custom styling to translated text:**
```bash
lexora translate book.epub --to-lang vi \
  --translated-color gray \
  --translated-style "font-style: italic;"
```

**Custom translation instructions:**
```bash
lexora translate book.epub --to-lang es \
  --instruction "Translate maintaining literary style. Use formal Spanish."
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
