# Provider API Key Setup Guide

This guide explains how to obtain and configure API keys for each supported provider in Lexora-AI.

Security notes:
- Never paste secrets into chat, tickets, or source control.
- Store keys in local `.env` only.
- Rotate keys immediately if exposed.

## OpenAI

Portal:
- https://platform.openai.com/api-keys

Steps:
1. Sign in to OpenAI Platform.
2. Open API keys.
3. Create a new secret key.
4. Copy and store it in your local `.env`.

Required env var:
- `OPENAI_API_KEY`

Example:
```env
OPENAI_API_KEY=your_openai_key
```

## Azure OpenAI

Portal:
- https://portal.azure.com

Steps:
1. Create or open your Azure OpenAI resource.
2. Open Keys and Endpoint and copy endpoint + key.
3. Create or confirm a model deployment in Azure OpenAI Studio.
4. Set endpoint, deployment, and key in `.env`.

Required env vars:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_KEY` or `AZURE_OPENAI_API_KEY`

Example:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_KEY=your_azure_openai_key
```

## Azure AI Foundry

Portal:
- https://ai.azure.com

Steps:
1. Open your Foundry project.
2. Get endpoint and API key from project/resource settings.
3. Confirm the model name used for inference.
4. Set endpoint, key, and model in `.env`.

Required env vars:
- `AZURE_AI_FOUNDRY_ENDPOINT`
- `AZURE_AI_FOUNDRY_API_KEY`
- `AZURE_AI_FOUNDRY_MODEL`

Example:
```env
AZURE_AI_FOUNDRY_ENDPOINT=https://your-foundry-endpoint/
AZURE_AI_FOUNDRY_API_KEY=your_foundry_key
AZURE_AI_FOUNDRY_MODEL=your_model_name
```

## Gemini

Portal:
- https://aistudio.google.com/app/apikey

Steps:
1. Sign in to Google AI Studio.
2. Create an API key.
3. Store key in `.env`.

Required env var:
- `GOOGLE_API_KEY`

Optional:
- `GEMINI_MODEL` — Gemini model id (default `gemini-2.0-flash`). Use if the default is unavailable in your region or account.

Example:
```env
GOOGLE_API_KEY=your_google_key
# GEMINI_MODEL=gemini-2.5-flash
```

## Anthropic

Portal:
- https://console.anthropic.com/settings/keys

Steps:
1. Sign in to Anthropic Console.
2. Create API key.
3. Store key in `.env`.

Required env var:
- `ANTHROPIC_API_KEY`

Example:
```env
ANTHROPIC_API_KEY=your_anthropic_key
```

## Qwen (DashScope)

Portal:
- https://dashscope.console.aliyun.com/

Steps:
1. Sign in to DashScope console.
2. Create an API key.
3. Store key in `.env`.

Accepted env vars:
- `DASHSCOPE_API_KEY`
- `QWEN_API_KEY`

Example:
```env
DASHSCOPE_API_KEY=your_dashscope_key
```

## One-file `.env` Template

```env
OPENAI_API_KEY=

AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_KEY=

AZURE_AI_FOUNDRY_ENDPOINT=
AZURE_AI_FOUNDRY_API_KEY=
AZURE_AI_FOUNDRY_MODEL=

GOOGLE_API_KEY=
ANTHROPIC_API_KEY=

DASHSCOPE_API_KEY=
# QWEN_API_KEY=
```

## Quick Provider Validation Commands

Run from the `lexora-ai` repo root after setting `.env`.

Use an EPUB from the IDPF sample catalog (see [testing-epub-samples.md](testing-epub-samples.md)); place it under `samples/` (for example `samples\accessible_epub_3.epub`). Replace the input path below with your file name.

```powershell
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-openai.epub --target vi --service openai --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-azure-openai.epub --target vi --service azure-openai --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-azure-foundry.epub --target vi --service azure-foundry --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-gemini.epub --target vi --service gemini --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-anthropic.epub --target vi --service anthropic --limit-docs 1
python -m lexora.cli translate .\samples\accessible_epub_3.epub .\samples\out-qwen.epub --target vi --service qwen --limit-docs 1
```
