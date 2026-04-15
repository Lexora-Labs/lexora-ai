"""
Azure AI Foundry translation provider.

Implements BaseTranslator for Azure AI Foundry inference endpoints.
"""

import os
import time
import hashlib
import logging
from typing import List, Optional, Dict, Any, Tuple

from lexora.core.base_translator import (
    BaseTranslator,
    TranslationConfig,
    TranslationResult,
    BilingualAST,
    BilingualNode,
)
from lexora.core.structured_batch import (
    StructuredBatchItem,
    build_structured_batch_user_payload,
    parse_structured_batch_response,
    validate_and_extract_translations,
)

try:
    from openai import OpenAI

    AZURE_AI_FOUNDRY_AVAILABLE = True
except ImportError:
    OpenAI = None
    AZURE_AI_FOUNDRY_AVAILABLE = False


class AzureAIFoundryProvider(BaseTranslator):
    """Azure AI Foundry provider using the OpenAI SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        debug: bool = False,
    ):
        if not AZURE_AI_FOUNDRY_AVAILABLE:
            raise ImportError(
                "openai package not installed. "
                "Run: pip install openai"
            )

        self._api_key = api_key or os.getenv("AZURE_AI_FOUNDRY_API_KEY")
        endpoint_env = endpoint or os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
        self._endpoint = endpoint_env.rstrip("/") if endpoint_env else None
        self._model = model or os.getenv("AZURE_AI_FOUNDRY_MODEL")
        self._temperature = temperature
        self._debug = debug
        self._client: Optional[OpenAI] = None
        self._logger = logging.getLogger("lexora.providers.azure_ai_foundry")

    @property
    def provider_name(self) -> str:
        return "azure-foundry"

    def supports_structured_batch(self) -> bool:
        return True

    def is_configured(self) -> bool:
        return bool(self._api_key and self._endpoint and self._model)

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "Azure AI Foundry is not configured. Set "
                    "AZURE_AI_FOUNDRY_API_KEY, AZURE_AI_FOUNDRY_ENDPOINT, "
                    "and AZURE_AI_FOUNDRY_MODEL environment variables."
                )

            self._client = OpenAI(
                base_url=self._endpoint,
                api_key=self._api_key,
            )

        return self._client

    def translate_text(
        self,
        text: str,
        config: TranslationConfig,
    ) -> TranslationResult:
        results = self.translate_batch([text], config)
        return results[0] if results else TranslationResult(
            translated_content=text,
            bilingual_ast=None,
        )

    def translate_batch(
        self,
        texts: List[str],
        config: TranslationConfig,
        retry: int = 3,
        sleep: float = 1.0,
    ) -> List[TranslationResult]:
        client = self._get_client()
        results: List[TranslationResult] = []
        system_msg = self.get_system_instruction(config)

        total_tokens: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        for idx, text in enumerate(texts):
            prompt = self.build_prompt(text, config)
            translated = self._call_api_with_retry(
                client, system_msg, prompt, text, retry, sleep, total_tokens
            )

            node = BilingualNode(
                node_id=self._generate_node_id(text, idx),
                source_text=text,
                translated_text=translated,
            )

            result = TranslationResult(
                translated_content=translated,
                bilingual_ast=BilingualAST(
                    source_language=config.source_language or "",
                    target_language=config.target_language,
                    nodes=[node],
                ),
                token_usage=dict(total_tokens),
            )
            results.append(result)

        return results

    def _structured_system_message(self, config: TranslationConfig) -> str:
        base = self.get_system_instruction(config)
        return (
            f"{base}\n\n"
            "You receive JSON describing translation items. "
            'Respond with a single JSON object only, shape: '
            '{"items":[{"id":"<same as input id>","translated_text":"<translation>"}]} '
            "with exactly one entry per input item, identical ids, no markdown fences, no commentary."
        )

    def translate_structured_batch(
        self,
        items: List[StructuredBatchItem],
        *,
        batch_id: str,
        config: TranslationConfig,
    ) -> Tuple[Dict[str, str], Dict[str, int]]:
        if not items:
            return {}, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        client = self._get_client()
        user_body = build_structured_batch_user_payload(
            source_lang=config.source_language,
            target_lang=config.target_language,
            batch_id=batch_id,
            items=items,
        )
        system_msg = self._structured_system_message(config)
        usage: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        expected_ids = [it.id for it in items]
        source_by_id = {it.id: it.text for it in items}

        last_error: Optional[Exception] = None
        for attempt in range(2):
            user_content = user_body
            if attempt == 1:
                user_content = (
                    user_body
                    + "\n\nYour previous reply was invalid. Output only valid JSON matching "
                    'the contract: {"items":[{"id":"...","translated_text":"..."}]} '
                    "with the same ids as the input items."
                )
            try:
                response = client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=self._temperature,
                    response_format={"type": "json_object"},
                )
                raw = self._extract_text(response).strip()
                self._accumulate_usage(response, usage)

                parsed = parse_structured_batch_response(raw)
                out = validate_and_extract_translations(
                    expected_ids=expected_ids,
                    parsed=parsed,
                    source_by_id=source_by_id,
                )
                return out, usage
            except Exception as exc:
                last_error = exc
                if self._debug:
                    self._logger.debug(
                        "provider.structured_batch.retry provider=azure_ai_foundry batch_id=%s attempt=%s",
                        batch_id,
                        attempt + 1,
                    )

        assert last_error is not None
        raise last_error

    def _call_api_with_retry(
        self,
        client: OpenAI,
        system_msg: str,
        prompt: str,
        text: str,
        retry: int,
        sleep: float,
        total_tokens: Dict[str, int],
    ) -> str:
        for attempt in range(retry):
            try:
                if self._debug:
                    self._logger.debug(
                        "provider.request.started provider=azure_ai_foundry model=%s chars=%s attempt=%s",
                        self._model,
                        len(text),
                        attempt + 1,
                    )

                t0 = time.time()
                response = client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self._temperature,
                )

                translated = self._extract_text(response).strip()
                self._accumulate_usage(response, total_tokens)

                if self._debug:
                    self._logger.debug(
                        "provider.request.completed provider=azure_ai_foundry model=%s chars=%s elapsed_ms=%s",
                        self._model,
                        len(translated),
                        round((time.time() - t0) * 1000),
                    )

                return translated or text

            except Exception as e:
                if self._debug:
                    self._logger.exception(
                        "provider.request.failed provider=azure_ai_foundry model=%s error_type=%s",
                        self._model,
                        type(e).__name__,
                    )

                error_str = str(e).lower()
                if "content" in error_str and ("filter" in error_str or "safety" in error_str):
                    if self._debug:
                        self._logger.warning(
                            "provider.request.blocked provider=azure_ai_foundry model=%s reason=content_filter",
                            self._model,
                        )
                    return text
                    
                if "resource not found" in error_str or "404" in error_str:
                    if self._debug:
                        self._logger.warning(
                            "provider.request.endpoint_hint provider=azure_ai_foundry endpoint=%s hint=append_/v1_or_/models",
                            self._endpoint,
                        )
                    if attempt == retry - 1:
                        raise ValueError(f"Azure AI Foundry resource not found at {self._endpoint}. Check your endpoint URL (may need /v1 or /models appended). Error: {e}")

                time.sleep(sleep * (attempt + 1))
                if attempt == retry - 1:
                    raise

        return text

    def _extract_text(self, response: Any) -> str:
        choice = response.choices[0]
        message = getattr(choice, "message", None)
        content = getattr(message, "content", "")

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            chunks: List[str] = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                else:
                    maybe_text = getattr(item, "text", None) or getattr(item, "content", None)
                    if maybe_text:
                        chunks.append(str(maybe_text))
            return "".join(chunks)

        return str(content or "")

    def _accumulate_usage(self, response: Any, total_tokens: Dict[str, int]) -> None:
        usage = getattr(response, "usage", None)
        if not usage:
            return

        total_tokens["prompt_tokens"] += (
            getattr(usage, "prompt_tokens", 0)
            or getattr(usage, "input_tokens", 0)
            or 0
        )
        total_tokens["completion_tokens"] += (
            getattr(usage, "completion_tokens", 0)
            or getattr(usage, "output_tokens", 0)
            or 0
        )
        total_tokens["total_tokens"] += (
            getattr(usage, "total_tokens", 0)
            or (
                total_tokens["prompt_tokens"] + total_tokens["completion_tokens"]
            )
        )

    def _generate_node_id(self, text: str, index: int) -> str:
        content_hash = hashlib.sha256(
            f"{index}:{text[:100]}".encode("utf-8")
        ).hexdigest()[:12]
        return f"node_{index}_{content_hash}"
