# Lexora AI

Lexora AI is an open-source, AI-powered eBook translation tool. It enables developers and creators to translate eBooks into multiple languages while preserving formatting and structure. Built for scalability and future innovation.

## Features

- **Multiple AI Service Support**: Connect to OpenAI, Azure OpenAI, or Azure AI Foundry
- **Multiple File Format Support**: Read and translate EPUB, MOBI, Word (.docx), and Markdown (.md) files
- **Preserve Formatting**: Maintains document structure during translation
- **Easy CLI Interface**: Simple command-line tool for quick translations
- **Python API**: Use as a library in your own projects

## Installation

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in your project directory with your API credentials:

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Or Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your_deployment_name

# Or Azure AI Foundry
AZURE_AI_FOUNDRY_API_KEY=your_azure_ai_foundry_key_here
AZURE_AI_FOUNDRY_ENDPOINT=https://your-endpoint.inference.ai.azure.com
AZURE_AI_FOUNDRY_MODEL=your_model_name
```

See `.env.example` for a template.

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

Use a specific AI service:
```bash
lexora translate input.md output.txt --target de --service azure-openai
```

### Python API

```python
from lexora import Translator
from lexora.services import OpenAIService

# Create a translator with OpenAI
service = OpenAIService(api_key="your-key")
translator = Translator(service=service)

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

## Supported AI Services

1. **OpenAI**: Uses GPT models for translation
   - Requires: `OPENAI_API_KEY`

2. **Azure OpenAI**: Azure-hosted OpenAI models
   - Requires: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`

3. **Azure AI Foundry**: Azure AI Foundry inference service
   - Requires: `AZURE_AI_FOUNDRY_API_KEY`, `AZURE_AI_FOUNDRY_ENDPOINT`, `AZURE_AI_FOUNDRY_MODEL`

## Development

Install in development mode:
```bash
pip install -e .
```

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
