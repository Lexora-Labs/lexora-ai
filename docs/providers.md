# Translation Providers

Lexora-AI supports multiple AI translation providers via the Strategy Pattern. All providers implement the `BaseTranslator` interface and return a standardized `TranslationResult` with Bilingual JSON AST.

---

## Quick Start

```python
from lexora.providers import (
    OpenAIProvider,
    AzureOpenAIProvider,
    AzureAIFoundryProvider,
    GeminiProvider,
    AnthropicProvider,
    QwenProvider,
)
from lexora.core import TranslationConfig

# Pick any provider
provider = OpenAIProvider()  # Uses OPENAI_API_KEY from env

config = TranslationConfig(
    source_language="en",
    target_language="vi",
)

result = provider.translate_text("Hello World", config)
print(result.translated_content)  # "Xin chào Thế giới"
print(result.bilingual_ast.to_dict())  # JSON AST
```

---

## Providers

### 1. OpenAI

Direct OpenAI API (GPT-4, GPT-4o, etc.)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |

**Supported Models:**
- `gpt-4o` (default)
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

```python
from lexora.providers import OpenAIProvider

provider = OpenAIProvider(
    api_key="sk-...",        # or use OPENAI_API_KEY env
    model="gpt-4o",          # default
    temperature=0.2,
)
```

---

### 2. Azure OpenAI

Azure-hosted OpenAI models.

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | ✅ | Azure endpoint URL |
| `AZURE_OPENAI_KEY` | ✅ | API key |
| `AZURE_OPENAI_API_KEY` | ❌ | Compatibility alias for API key |
| `AZURE_OPENAI_DEPLOYMENT` | ✅ | Deployment name |
| `AZURE_OPENAI_API_VERSION` | ❌ | API version (default: `2024-02-01`) |

**Supported Models:**
- `gpt-4o`
- `gpt-4`
- `gpt-35-turbo`

```python
from lexora.providers import AzureOpenAIProvider

provider = AzureOpenAIProvider(
    endpoint="https://your-resource.openai.azure.com",
    api_key="...",
    deployment="gpt-4o",
    api_version="2024-02-01",
    temperature=0.2,
)
```

---

### 3. Azure AI Foundry

Azure AI Foundry inference endpoint.

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_AI_FOUNDRY_API_KEY` | ✅ | API key |
| `AZURE_AI_FOUNDRY_ENDPOINT` | ✅ | Inference endpoint |
| `AZURE_AI_FOUNDRY_MODEL` | ✅ | Model name |

```python
from lexora.providers import AzureAIFoundryProvider

provider = AzureAIFoundryProvider(
    api_key="...",
    endpoint="https://your-endpoint.inference.ai.azure.com",
    model="gpt-4.1",
    temperature=0.2,
)
```

---

### 4. Google Gemini

Google's Gemini models via Google AI Studio.

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ | Google AI API key |

**Supported Models:**
- `gemini-1.5-pro` (default)
- `gemini-1.5-flash`
- `gemini-pro`

```python
from lexora.providers import GeminiProvider

provider = GeminiProvider(
    api_key="...",           # or use GOOGLE_API_KEY env
    model="gemini-1.5-pro",  # default
    temperature=0.2,
)
```

**Install SDK:**
```bash
pip install google-generativeai
```

---

### 5. Anthropic Claude

Anthropic's Claude models.

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key |

**Supported Models:**
- `claude-sonnet-4-20250514` (default)
- `claude-3-5-sonnet-20241022`
- `claude-3-opus-20240229`
- `claude-3-haiku-20240307`

```python
from lexora.providers import AnthropicProvider

provider = AnthropicProvider(
    api_key="...",           # or use ANTHROPIC_API_KEY env
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    temperature=0.2,
)
```

**Install SDK:**
```bash
pip install anthropic
```

---

### 6. Alibaba Qwen

Alibaba's Qwen (Tongyi Qianwen) models via DashScope API.

| Variable | Required | Description |
|----------|----------|-------------|
| `DASHSCOPE_API_KEY` | ✅ | DashScope API key |
| `QWEN_API_KEY` | ❌ | Alternative env var |

**Supported Models:**
- `qwen-max` (default) - Most capable
- `qwen-plus` - Balanced
- `qwen-turbo` - Fast & cheap
- `qwen-long` - Long context

```python
from lexora.providers import QwenProvider

provider = QwenProvider(
    api_key="...",           # or use DASHSCOPE_API_KEY env
    model="qwen-max",        # default
    temperature=0.2,
)
```

**API Endpoint:** `https://dashscope.aliyuncs.com/compatible-mode/v1`

**Get API Key:** https://dashscope.console.aliyun.com/

---

## Environment Variables Summary

Create a `.env` file:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Azure AI Foundry
AZURE_AI_FOUNDRY_API_KEY=...
AZURE_AI_FOUNDRY_ENDPOINT=https://your-endpoint.inference.ai.azure.com
AZURE_AI_FOUNDRY_MODEL=gpt-4.1

# Google Gemini
GOOGLE_API_KEY=...

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# Alibaba Qwen
DASHSCOPE_API_KEY=sk-...
```

---

## Common Options

All providers support these options:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temperature` | float | 0.2 | Sampling temperature (0.0-1.0) |
| `debug` | bool | False | Enable debug logging |

---

## TranslationConfig

```python
from lexora.core import TranslationConfig, TranslationMode

config = TranslationConfig(
    source_language="en",           # Source language code
    target_language="vi",           # Target language code
    mode=TranslationMode.BILINGUAL, # BILINGUAL or REPLACE
    glossary={"API": "API"},        # Term mapping
    temperature=0.2,
    custom_instruction=None,        # Override system prompt
)
```

---

## Output Format

All providers return `TranslationResult`:

```python
result = provider.translate_text("Hello", config)

# Translated text
result.translated_content  # "Xin chào"

# Bilingual JSON AST
result.bilingual_ast.to_dict()
# {
#   "version": "1.0.0",
#   "source_language": "en",
#   "target_language": "vi",
#   "nodes": [
#     {
#       "node_id": "node_0_abc123...",
#       "source_text": "Hello",
#       "translated_text": "Xin chào"
#     }
#   ]
# }

# Token usage
result.token_usage  # {"prompt_tokens": 50, "completion_tokens": 10, ...}
```

---

## Adding Custom Providers

Implement `BaseTranslator`:

```python
from lexora.core import BaseTranslator, TranslationConfig, TranslationResult

class MyCustomProvider(BaseTranslator):
    
    @property
    def provider_name(self) -> str:
        return "my_provider"
    
    def is_configured(self) -> bool:
        return True  # Check credentials
    
    def translate_text(self, text: str, config: TranslationConfig) -> TranslationResult:
        # Your implementation
        pass
    
    def translate_batch(self, texts: list, config: TranslationConfig) -> list:
        # Your implementation
        pass
```
