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

2. Install the package in editable mode:
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

2. Uncomment and populate the variables for the service(s) you wish to use:

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
- [docs/providers.md](docs/providers.md): Provider setup and configuration details.
- [docs/translation-logic.md](docs/translation-logic.md): Canonical translation pipeline logic and EPUB flow.
- [docs/todo-list.md](docs/todo-list.md): Planned translation pipeline improvements.

## Development

Install in development mode:
```bash
pip install -e .
```

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
