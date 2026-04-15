# Lexora AI

Lexora AI is an open-source, AI-powered eBook translation tool. It enables developers and creators to translate eBooks into multiple languages while preserving formatting and structure. Built for scalability and future innovation.

## Features

- **Provider-Based AI Support**: Plug in OpenAI, Azure OpenAI, Azure AI Foundry, Gemini, Anthropic, or Qwen
- **Multiple File Format Support**: Read and translate EPUB, MOBI, Word (.docx), and Markdown (.md) files
- **Preserve Formatting**: Maintains document structure during translation
- **Easy CLI Interface**: Simple command-line tool for quick translations
- **Python API**: Use as a library in your own projects

## Installation

1. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On Mac/Linux:
source .venv/bin/activate
```

1. Install the package in editable mode:

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Configuration

Lexora AI supports `.env` files for securely managing your configuration and API keys. The CLI automatically loads credentials from a `.env` file in your working directory.

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

1. Uncomment and populate the variables for the service(s) you wish to use:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Azure OpenAI Configuration
AZURE_OPENAI_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your_deployment_name

# Azure AI Foundry Configuration
AZURE_AI_FOUNDRY_API_KEY=your_azure_ai_foundry_key_here
AZURE_AI_FOUNDRY_ENDPOINT=https://your-endpoint.inference.ai.azure.com
AZURE_AI_FOUNDRY_MODEL=your_model_name

# Refer to .env.example for Google Gemini, Anthropic Claude, and Alibaba Qwen settings.
```

See `.env.example` for the complete list of supported providers and optional UI configurations.

## Test inputs (sample EPUBs)

For manual runs and regression tests, use **IDPF EPUB 3 reference samples** instead of commercial or personal books, to respect copyright and keep a clear license story.

- **Catalog:** [EPUB 3 Samples (IDPF)](https://idpf.github.io/epub3-samples/30/samples.html)
- **Local folder:** put downloaded `.epub` files in the repository `**samples/`** directory (see `samples/README.md`).
- **Default first test:** `samples/accessible_epub_3.epub` (*Accessible EPUB 3*); details in [docs/testing-epub-samples.md](docs/testing-epub-samples.md).
- **Details:** [docs/testing-epub-samples.md](docs/testing-epub-samples.md) (licensing notes, `*.epub` gitignore behavior, example commands).

## Usage

### Command Line

Translate an EPUB file to Spanish:

```bash
lexora translate input.epub output.txt --target es
```

Translate a Word document to French:

```bash
lexora translate document.docx translated.txt --target fr
```

Specify source and target languages:

```bash
lexora translate book.epub spanish_book.txt --source en --target es
```

Use a specific AI provider:

```bash
lexora translate input.md output.txt --target de --service azure-openai
```

Translate using global cache (default) with explicit path:

```bash
lexora translate input.epub output.epub --target vi --cache-path .lexora/cache/global_translation_cache.jsonl
```

Translate using per-ebook cache isolation:

```bash
lexora translate input.epub output.epub --target vi --cache-scope per-ebook
```

Disable cache for a single run:

```bash
lexora translate input.epub output.epub --target vi --no-cache
```

Clear effective cache file before translation starts:

```bash
lexora translate input.epub output.epub --target vi --clear-cache
```

Fast test run on first 3 EPUB documents:

```bash
lexora translate input.epub output.epub --target vi --limit-docs 3
```

Run a specific EPUB document range (1-based inclusive):

```bash
lexora translate input.epub output.epub --target vi --start-doc 5 --end-doc 8
```

EPUB only — structured JSON batches (fewer round-trips; OpenAI, Azure AI Foundry, Gemini):

```bash
lexora translate samples/accessible_epub_3.epub out.epub --target vi --service openai --structured-epub-batch --limit-docs 1
lexora translate samples/accessible_epub_3.epub out.epub --target vi --service gemini --structured-epub-batch --limit-docs 1
```

Valid options for the `--service` parameter:

- `openai`
- `azure-openai`
- `azure-foundry`
- `gemini`
- `anthropic`
- `qwen`

### Python API

```python
from lexora import Translator
from lexora.providers import OpenAIProvider

# Create a translator with OpenAI
provider = OpenAIProvider(api_key="your-key")
translator = Translator(provider=provider)

# Translate a file
translator.translate_file(
    input_file="book.epub",
    output_file="translated.txt",
    target_language="es",
    source_language="en"
)

# Or translate text directly
translated = translator.translate_text(
    text="Hello, world!",
    target_language="es"
)
print(translated)
```

## Supported File Formats

- **EPUB** (`.epub`): Electronic publication format
- **MOBI** (`.mobi`): Mobipocket eBook format
- **Word** (`.docx`, `.doc`): Microsoft Word documents
- **Markdown** (`.md`): Markdown text files

## Supported AI Providers

1. **OpenAI**: Uses GPT models for translation
  - Requires: `OPENAI_API_KEY`
2. **Azure OpenAI**: Azure-hosted OpenAI models
  - Requires: `AZURE_OPENAI_KEY` or `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`
3. **Azure AI Foundry**: Azure AI Foundry inference service
  - Requires: `AZURE_AI_FOUNDRY_API_KEY`, `AZURE_AI_FOUNDRY_ENDPOINT`, `AZURE_AI_FOUNDRY_MODEL`
4. **Gemini**: Google Gemini models
  - Requires: `GOOGLE_API_KEY`
5. **Anthropic**: Claude models
  - Requires: `ANTHROPIC_API_KEY`
6. **Qwen**: Alibaba Qwen models
  - Requires: `DASHSCOPE_API_KEY` or `QWEN_API_KEY`

## Docs Index

- [docs/vibe-context.md](docs/vibe-context.md): Core engineering context, guardrails, and architecture rules.
- [docs/testing-epub-samples.md](docs/testing-epub-samples.md): IDPF sample EPUBs for testing, `samples/` folder, and license/git notes.
- [docs/providers.md](docs/providers.md): Provider setup and configuration details.
- [docs/translation-logic.md](docs/translation-logic.md): Canonical translation pipeline logic and EPUB flow.
- [docs/epub-structured-batch-translation-design.md](docs/epub-structured-batch-translation-design.md): Structure-preserving JSON batch translation design (EPUB cost/latency).
- [docs/epub-structured-batch-translation-plan.md](docs/epub-structured-batch-translation-plan.md): Task plan and phases (**LAI-T-032**–**LAI-T-035**).
- [docs/track-a-cli-core-mvp-plan.md](docs/track-a-cli-core-mvp-plan.md): 2-week execution plan for translation-core and CLI-first hardening.
- [docs/translation-run-contract.md](docs/translation-run-contract.md): Frozen run/report contract for CLI and future UI integration.
- [docs/logging-framework.md](docs/logging-framework.md): Planned centralized logging architecture and sink model.
- [docs/todo-list.md](docs/todo-list.md): Planned translation pipeline improvements.

## Development

Install in development mode:

```bash
pip install -e .
```

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0) - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.