"""
OpenAI Translation Provider.

Implements BaseTranslator for OpenAI GPT models (direct API, not Azure).
"""

import os
import time
import hashlib
import logging
from typing import List, Optional, Dict, Tuple

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
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


class OpenAIProvider(BaseTranslator):
    """
    OpenAI GPT Translation Provider.
    
    Features:
    - Uses OpenAI Python SDK
    - Supports GPT-4, GPT-4o, GPT-3.5-turbo
    - Glossary-aware translation
    - Returns Bilingual AST
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.2,
        debug: bool = False,
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (or OPENAI_API_KEY env var)
            model: Model name (gpt-4o, gpt-4, gpt-3.5-turbo)
            temperature: Sampling temperature
            debug: Enable debug logging
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            )
        
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model = model
        self._temperature = temperature
        self._debug = debug
        self._client: Optional[OpenAI] = None
        self._logger = logging.getLogger("lexora.providers.openai")

    @property
    def provider_name(self) -> str:
        return "openai"

    def supports_structured_batch(self) -> bool:
        return True

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "OpenAI is not configured. Set OPENAI_API_KEY environment variable."
                )
            self._client = OpenAI(api_key=self._api_key)
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
                    temperature=self._temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_content},
                    ],
                )
                raw = (response.choices[0].message.content or "").strip()
                if response.usage:
                    usage["prompt_tokens"] = response.usage.prompt_tokens or 0
                    usage["completion_tokens"] = response.usage.completion_tokens or 0
                    usage["total_tokens"] = response.usage.total_tokens or 0

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
                        "provider.structured_batch.retry provider=openai batch_id=%s attempt=%s",
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
                        "provider.request.started provider=openai model=%s chars=%s attempt=%s",
                        self._model,
                        len(text),
                        attempt + 1,
                    )
                
                t0 = time.time()
                response = client.chat.completions.create(
                    model=self._model,
                    temperature=self._temperature,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                )
                
                translated = response.choices[0].message.content.strip()
                
                if response.usage:
                    total_tokens["prompt_tokens"] += response.usage.prompt_tokens or 0
                    total_tokens["completion_tokens"] += response.usage.completion_tokens or 0
                    total_tokens["total_tokens"] += response.usage.total_tokens or 0
                
                if self._debug:
                    self._logger.debug(
                        "provider.request.completed provider=openai model=%s chars=%s elapsed_ms=%s",
                        self._model,
                        len(translated),
                        round((time.time() - t0) * 1000),
                    )
                
                return translated
                
            except Exception as e:
                if self._debug:
                    self._logger.exception(
                        "provider.request.failed provider=openai model=%s error_type=%s",
                        self._model,
                        type(e).__name__,
                    )
                time.sleep(sleep * (attempt + 1))
                if attempt == retry - 1:
                    raise
        
        return text

    def _generate_node_id(self, text: str, index: int) -> str:
        content_hash = hashlib.sha256(
            f"{index}:{text[:100]}".encode("utf-8")
        ).hexdigest()[:12]
        return f"node_{index}_{content_hash}"
