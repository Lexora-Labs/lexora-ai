"""
Google Gemini Translation Provider.

Implements BaseTranslator for Google Gemini models.
"""

import os
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

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

# Gemini structured output schema (matches validate_and_extract_translations contract).
_STRUCTURED_BATCH_RESPONSE_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "translated_text": {"type": "string"},
                },
                "required": ["id", "translated_text"],
            },
        }
    },
    "required": ["items"],
}

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    genai_types = None


class GeminiProvider(BaseTranslator):
    """
    Google Gemini Translation Provider.

    Uses the ``google-genai`` SDK against the Generative Language API.
    Default model tracks Google’s current ``generateContent`` IDs (older
    ``gemini-1.5-*`` names often return 404 on v1beta); override with
    ``GEMINI_MODEL`` / ``GOOGLE_GEMINI_MODEL`` or the ``model`` argument.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        debug: bool = False,
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google AI API key (or GOOGLE_API_KEY env var)
            model: Model id (e.g. ``gemini-2.0-flash``, ``gemini-2.5-flash``).
                If omitted, uses ``GEMINI_MODEL``, ``GOOGLE_GEMINI_MODEL``, then
                ``gemini-2.0-flash``.
            temperature: Sampling temperature
            debug: Enable debug logging
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )

        self._api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._model_name = (
            model
            or os.getenv("GEMINI_MODEL")
            or os.getenv("GOOGLE_GEMINI_MODEL")
            or "gemini-2.0-flash"
        )
        self._temperature = temperature
        self._debug = debug
        self._client = None
        self._logger = logging.getLogger("lexora.providers.gemini")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def supports_structured_batch(self) -> bool:
        return True

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self):
        if self._client is None:
            if not self.is_configured():
                raise ValueError(
                    "Gemini is not configured. Set GOOGLE_API_KEY environment variable."
                )
            self._client = genai.Client(api_key=self._api_key)
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
        system_instruction = self.get_system_instruction(config)
        
        total_tokens: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        
        for idx, text in enumerate(texts):
            prompt = self.build_prompt(text, config)
            full_prompt = f"{system_instruction}\n\n{prompt}"
            
            translated = self._call_api_with_retry(
                client, full_prompt, text, retry, sleep, total_tokens
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
                response = client.models.generate_content(
                    model=self._model_name,
                    contents=user_content,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_msg,
                        temperature=self._temperature,
                        response_mime_type="application/json",
                        response_json_schema=_STRUCTURED_BATCH_RESPONSE_JSON_SCHEMA,
                    ),
                )
                raw = (getattr(response, "text", None) or "").strip()
                if not raw:
                    candidates = getattr(response, "candidates", None) or []
                    first_candidate = candidates[0] if candidates else None
                    content = getattr(first_candidate, "content", None)
                    parts = getattr(content, "parts", None) or []
                    text_parts = [
                        getattr(part, "text", "")
                        for part in parts
                        if getattr(part, "text", None)
                    ]
                    raw = "".join(text_parts).strip()
                if not raw:
                    raise ValueError("gemini_empty_structured_response")

                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    um = response.usage_metadata
                    usage["prompt_tokens"] = int(
                        getattr(um, "prompt_token_count", 0) or 0
                    )
                    usage["completion_tokens"] = int(
                        getattr(um, "candidates_token_count", 0) or 0
                    )
                    usage["total_tokens"] = int(
                        getattr(um, "total_token_count", 0)
                        or (usage["prompt_tokens"] + usage["completion_tokens"])
                    )

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
                        "provider.structured_batch.retry provider=gemini batch_id=%s attempt=%s",
                        batch_id,
                        attempt + 1,
                    )

        assert last_error is not None
        raise last_error

    def _call_api_with_retry(
        self,
        client,
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
                        "provider.request.started provider=gemini model=%s chars=%s attempt=%s",
                        self._model_name,
                        len(text),
                        attempt + 1,
                    )
                
                t0 = time.time()
                response = client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        temperature=self._temperature,
                    ),
                )

                translated = (getattr(response, "text", None) or "").strip()
                if not translated:
                    candidates = getattr(response, "candidates", None) or []
                    first_candidate = candidates[0] if candidates else None
                    content = getattr(first_candidate, "content", None)
                    parts = getattr(content, "parts", None) or []
                    text_parts = [
                        getattr(part, "text", "")
                        for part in parts
                        if getattr(part, "text", None)
                    ]
                    translated = "".join(text_parts).strip()
                if not translated:
                    translated = text
                
                # Track token usage if available
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    total_tokens["prompt_tokens"] += getattr(usage, 'prompt_token_count', 0)
                    total_tokens["completion_tokens"] += getattr(usage, 'candidates_token_count', 0)
                    total_tokens["total_tokens"] += getattr(usage, 'total_token_count', 0)
                
                if self._debug:
                    self._logger.debug(
                        "provider.request.completed provider=gemini model=%s chars=%s elapsed_ms=%s",
                        self._model_name,
                        len(translated),
                        round((time.time() - t0) * 1000),
                    )
                
                return translated
                
            except Exception as e:
                if self._debug:
                    self._logger.exception(
                        "provider.request.failed provider=gemini model=%s error_type=%s",
                        self._model_name,
                        type(e).__name__,
                    )
                
                # Handle safety blocks
                if "blocked" in str(e).lower() or "safety" in str(e).lower():
                    if self._debug:
                        self._logger.warning(
                            "provider.request.blocked provider=gemini model=%s reason=safety_filter",
                            self._model_name,
                        )
                    return text
                
                time.sleep(sleep * (attempt + 1))
                if attempt == retry - 1:
                    raise
        
        return text

    def _generate_node_id(self, text: str, index: int) -> str:
        content_hash = hashlib.sha256(
            f"{index}:{text[:100]}".encode("utf-8")
        ).hexdigest()[:12]
        return f"node_{index}_{content_hash}"
